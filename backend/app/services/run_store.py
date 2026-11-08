"""SQLite-backed persistence for resumable independent agent runs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase

BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "data" / "simulation_runs.sqlite3"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect():
    """Open a short-lived SQLite connection and always close it."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id TEXT PRIMARY KEY,
                case_json TEXT NOT NULL,
                status TEXT NOT NULL,
                total_agents INTEGER NOT NULL,
                current_agent_id TEXT,
                patient_id TEXT,
                case_version_id TEXT,
                case_version_number INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS synthetic_patients (
                patient_id TEXT PRIMARY KEY,
                patient_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Keep allocations after deletion; training IDs are never reissued.
            CREATE TABLE IF NOT EXISTS patient_registry_numbers (
                registry_number INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS patient_case_versions (
                case_version_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                patient_name TEXT,
                version_number INTEGER NOT NULL CHECK(version_number > 0),
                case_json TEXT NOT NULL,
                case_snapshot_sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(patient_id, version_number),
                FOREIGN KEY (patient_id) REFERENCES synthetic_patients(patient_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS patient_case_assessments (
                assessment_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                case_version_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                assessment_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES synthetic_patients(patient_id) ON DELETE CASCADE,
                FOREIGN KEY (case_version_id) REFERENCES patient_case_versions(case_version_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS agent_run_results (
                run_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                category_label TEXT NOT NULL,
                status TEXT NOT NULL,
                assessment_json TEXT,
                error_message TEXT,
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                PRIMARY KEY (run_id, agent_id),
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_agent_run_results_run_status
            ON agent_run_results(run_id, status);

            CREATE INDEX IF NOT EXISTS idx_patient_case_versions_patient
            ON patient_case_versions(patient_id, version_number DESC);
            CREATE INDEX IF NOT EXISTS idx_patient_assessments_version
            ON patient_case_assessments(case_version_id, created_at DESC);
            """
        )
        # Additive migration for databases created before patient-linked simulations.
        run_columns = {row["name"] for row in db.execute("PRAGMA table_info(simulation_runs)")}
        for column, sql_type in (
            ("patient_id", "TEXT"),
            ("case_version_id", "TEXT"),
            ("case_version_number", "INTEGER"),
        ):
            if column not in run_columns:
                db.execute(f"ALTER TABLE simulation_runs ADD COLUMN {column} {sql_type}")
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_simulation_runs_patient "
            "ON simulation_runs(patient_id, created_at DESC)"
        )
        patient_columns = {row["name"] for row in db.execute("PRAGMA table_info(synthetic_patients)")}
        if "patient_name" not in patient_columns:
            db.execute("ALTER TABLE synthetic_patients ADD COLUMN patient_name TEXT")
        version_columns = {row["name"] for row in db.execute("PRAGMA table_info(patient_case_versions)")}
        if "patient_name" not in version_columns:
            db.execute("ALTER TABLE patient_case_versions ADD COLUMN patient_name TEXT")
        # Only insert genuinely missing allocations: INSERT OR IGNORE would still
        # advance SQLite AUTOINCREMENT for conflicts on every initialization.
        db.execute(
            """INSERT INTO patient_registry_numbers(patient_id, created_at)
            SELECT p.patient_id, p.created_at FROM synthetic_patients AS p
            WHERE NOT EXISTS (
                SELECT 1 FROM patient_registry_numbers AS n WHERE n.patient_id = p.patient_id
            ) ORDER BY p.created_at, p.patient_id"""
        )
        # Migrate names written into case JSON by the short-lived earlier schema.
        legacy_profiles = db.execute(
            """SELECT p.patient_id, p.patient_name, v.case_json
            FROM synthetic_patients AS p
            LEFT JOIN patient_case_versions AS v ON v.case_version_id = (
                SELECT latest.case_version_id FROM patient_case_versions AS latest
                WHERE latest.patient_id = p.patient_id
                ORDER BY latest.version_number DESC LIMIT 1
            )"""
        ).fetchall()
        for profile in legacy_profiles:
            if not profile["patient_name"] and profile["case_json"]:
                legacy_case = json.loads(profile["case_json"])
                legacy_name = legacy_case.get("patient_name")
                if isinstance(legacy_name, str) and legacy_name.strip():
                    db.execute(
                        "UPDATE synthetic_patients SET patient_name = ? WHERE patient_id = ?",
                        (legacy_name.strip(), profile["patient_id"]),
                    )

        # Backfill version-specific display names without changing the original
        # case JSON or its hash. Embedded legacy names are the strongest source;
        # versions without one receive the current registry name as best available.
        version_profiles = db.execute(
            """SELECT v.case_version_id, v.case_json, p.patient_name AS registry_name
            FROM patient_case_versions AS v
            JOIN synthetic_patients AS p ON p.patient_id = v.patient_id
            WHERE v.patient_name IS NULL OR TRIM(v.patient_name) = ''"""
        ).fetchall()
        for version in version_profiles:
            version_case = json.loads(version["case_json"])
            embedded_name = version_case.get("patient_name")
            version_name = (
                embedded_name.strip()
                if isinstance(embedded_name, str) and embedded_name.strip()
                else (version["registry_name"] or "").strip()
            )
            if version_name:
                db.execute(
                    "UPDATE patient_case_versions SET patient_name = ? WHERE case_version_id = ?",
                    (version_name, version["case_version_id"]),
                )


def _case_json_and_hash(case: SyntheticCase) -> tuple[str, str]:
    case_json = case.model_dump_json(exclude_none=True)
    return case_json, hashlib.sha256(case_json.encode("utf-8")).hexdigest()


def create_patient(patient_name: str, case: SyntheticCase) -> dict[str, Any]:
    """Create a fictional training patient and immutable case version 1 atomically."""
    initialize_database()
    patient_id = str(uuid.uuid4())
    case_version_id = str(uuid.uuid4())
    now = _now()
    case_json, digest = _case_json_and_hash(case)
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "INSERT INTO synthetic_patients(patient_id, patient_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (patient_id, patient_name, now, now),
        )
        db.execute(
            "INSERT INTO patient_registry_numbers(patient_id, created_at) VALUES (?, ?)",
            (patient_id, now),
        )
        db.execute(
            """INSERT INTO patient_case_versions
            (case_version_id, patient_id, patient_name, version_number, case_json, case_snapshot_sha256, created_at)
            VALUES (?, ?, ?, 1, ?, ?, ?)""",
            (case_version_id, patient_id, patient_name, case_json, digest, now),
        )
    return get_patient(patient_id)


def create_case_version(patient_id: str, patient_name: str, case: SyntheticCase) -> dict[str, Any]:
    """Update registry name and append an immutable case version atomically."""
    initialize_database()
    case_version_id = str(uuid.uuid4())
    now = _now()
    case_json, digest = _case_json_and_hash(case)
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        patient = db.execute(
            "SELECT patient_id FROM synthetic_patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise KeyError(patient_id)
        version_number = db.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version "
            "FROM patient_case_versions WHERE patient_id = ?", (patient_id,)
        ).fetchone()["next_version"]
        db.execute(
            """INSERT INTO patient_case_versions
            (case_version_id, patient_id, patient_name, version_number, case_json, case_snapshot_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (case_version_id, patient_id, patient_name, version_number, case_json, digest, now),
        )
        db.execute(
            "UPDATE synthetic_patients SET patient_name = ?, updated_at = ? WHERE patient_id = ?",
            (patient_name, now, patient_id),
        )
    return get_patient(patient_id)


def _version_record(row: sqlite3.Row) -> dict[str, Any]:
    case_json = str(row["case_json"])
    digest = hashlib.sha256(case_json.encode("utf-8")).hexdigest()
    if digest != row["case_snapshot_sha256"]:
        raise ValueError("Saved case-version hash verification failed.")
    case_data = json.loads(case_json)
    # Earlier registry prototype versions embedded the display name in the case JSON.
    # Keep its original bytes/hash for audit, but exclude the name from all agent payloads.
    case_data.pop("patient_name", None)
    case = SyntheticCase.model_validate(case_data)
    return {
        "case_version_id": row["case_version_id"],
        "patient_id": row["patient_id"],
        "patient_name": row["patient_name"],
        "version_number": row["version_number"],
        "case_snapshot_sha256": digest,
        "created_at": row["created_at"],
        "case": case.model_dump(exclude_none=True),
    }


def get_patient_case_version(patient_id: str, case_version_id: str) -> dict[str, Any]:
    initialize_database()
    with _connect() as db:
        row = db.execute(
            """SELECT * FROM patient_case_versions
            WHERE patient_id = ? AND case_version_id = ?""",
            (patient_id, case_version_id),
        ).fetchone()
    if row is None:
        raise KeyError((patient_id, case_version_id))
    return _version_record(row)


def get_patient(patient_id: str) -> dict[str, Any]:
    initialize_database()
    with _connect() as db:
        patient = db.execute(
            "SELECT * FROM synthetic_patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise KeyError(patient_id)
        registry_row = db.execute(
            "SELECT registry_number FROM patient_registry_numbers WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
        version_rows = db.execute(
            "SELECT * FROM patient_case_versions WHERE patient_id = ? ORDER BY version_number DESC",
            (patient_id,),
        ).fetchall()
        run_ids = [row["run_id"] for row in db.execute(
            "SELECT run_id FROM simulation_runs WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()]
    return {
        "patient_id": patient["patient_id"],
        "patient_identifier": f"RAD-{int(registry_row['registry_number']):06d}" if registry_row else None,
        "patient_name": patient["patient_name"],
        "created_at": patient["created_at"],
        "updated_at": patient["updated_at"],
        "versions": [_version_record(row) for row in version_rows],
        "runs": [get_run(run_id) for run_id in run_ids],
    }


def list_patients() -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as db:
        patient_ids = [row["patient_id"] for row in db.execute(
            "SELECT patient_id FROM synthetic_patients ORDER BY updated_at DESC, patient_id"
        ).fetchall()]
    patients = []
    for patient_id in patient_ids:
        detail = get_patient(patient_id)
        latest = detail["versions"][0] if detail["versions"] else None
        patients.append({
            "patient_id": detail["patient_id"],
            "patient_identifier": detail["patient_identifier"],
            "patient_name": detail["patient_name"],
            "age_years": latest["case"].get("age_years") if latest else None,
            "stage_group": latest["case"].get("stage_group") if latest else None,
            "created_at": detail["created_at"],
            "updated_at": detail["updated_at"],
            "version_count": len(detail["versions"]),
            "simulation_count": len(detail["runs"]),
            "latest_case_version_id": latest["case_version_id"] if latest else None,
            "latest_version_number": latest["version_number"] if latest else None,
            "scenario_title": latest["case"]["scenario_title"] if latest else "No saved case",
        })
    return patients


def delete_patient(patient_id: str) -> None:
    """Delete a training record and linked simulation outputs; never recycle its serial."""
    initialize_database()
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT patient_id FROM synthetic_patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if existing is None:
            raise KeyError(patient_id)
        run_ids = [row["run_id"] for row in db.execute(
            "SELECT run_id FROM simulation_runs WHERE patient_id = ?", (patient_id,)
        ).fetchall()]
        for run_id in run_ids:
            db.execute("DELETE FROM simulation_runs WHERE run_id = ?", (run_id,))
        db.execute("DELETE FROM synthetic_patients WHERE patient_id = ?", (patient_id,))


def create_run_for_case_version(patient_id: str, case_version_id: str) -> dict[str, Any]:
    """Create a run only from the stored, hash-verified patient case version."""
    version = get_patient_case_version(patient_id, case_version_id)
    case = SyntheticCase.model_validate(version["case"])
    return create_run(
        case,
        patient_id=patient_id,
        case_version_id=case_version_id,
        case_version_number=version["version_number"],
    )


def save_patient_assessment(
    patient_id: str, case_version_id: str, agent_id: str, round_number: int,
    assessment_json: str,
) -> dict[str, Any]:
    get_patient_case_version(patient_id, case_version_id)
    record_id = str(uuid.uuid4())
    created_at = _now()
    with _connect() as db:
        db.execute(
            """INSERT INTO patient_case_assessments
            (assessment_id, patient_id, case_version_id, agent_id, round_number, assessment_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (record_id, patient_id, case_version_id, agent_id, round_number, assessment_json, created_at),
        )
    return {
        "assessment_id": record_id, "patient_id": patient_id,
        "case_version_id": case_version_id, "agent_id": agent_id,
        "round_number": round_number, "created_at": created_at,
        "assessment": json.loads(assessment_json),
    }


def list_patient_assessments(patient_id: str, case_version_id: str) -> list[dict[str, Any]]:
    get_patient_case_version(patient_id, case_version_id)
    with _connect() as db:
        rows = db.execute(
            """SELECT * FROM patient_case_assessments
            WHERE patient_id = ? AND case_version_id = ? ORDER BY created_at DESC, rowid DESC""",
            (patient_id, case_version_id),
        ).fetchall()
    return [{
        "assessment_id": row["assessment_id"], "patient_id": row["patient_id"],
        "case_version_id": row["case_version_id"], "agent_id": row["agent_id"],
        "round_number": row["round_number"], "created_at": row["created_at"],
        "assessment": json.loads(row["assessment_json"]),
    } for row in rows]


def create_run(case: SyntheticCase, *, patient_id: str | None = None,
               case_version_id: str | None = None,
               case_version_number: int | None = None) -> dict[str, Any]:
    initialize_database()
    run_id = str(uuid.uuid4())
    now = _now()
    case_json, _ = _case_json_and_hash(case)
    with _connect() as db:
        db.execute(
            """
            INSERT INTO simulation_runs
            (run_id, case_json, status, total_agents, current_agent_id,
             patient_id, case_version_id, case_version_number, created_at, updated_at)
            VALUES (?, ?, 'queued', ?, NULL, ?, ?, ?, ?, ?)
            """,
            (run_id, case_json, len(AGENT_PROFILES), patient_id, case_version_id,
             case_version_number, now, now),
        )
        db.executemany(
            """
            INSERT INTO agent_run_results
            (run_id, agent_id, agent_name, category_label, status)
            VALUES (?, ?, ?, ?, 'queued')
            """,
            [
                (run_id, p["agent_id"], p["name"], p["category_label"])
                for p in AGENT_PROFILES
            ],
        )
    return get_run(run_id)


def get_case_json(run_id: str) -> str:
    """Return the exact serialized case snapshot captured when the run was created."""
    with _connect() as db:
        row = db.execute(
            "SELECT case_json FROM simulation_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
    if row is None:
        raise KeyError(run_id)
    return str(row["case_json"])


def get_case(run_id: str) -> SyntheticCase:
    return SyntheticCase.model_validate_json(get_case_json(run_id))


def get_run(run_id: str) -> dict[str, Any]:
    initialize_database()
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM simulation_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(run_id)
        counts = {
            item["status"]: item["count"]
            for item in db.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM agent_run_results WHERE run_id = ? GROUP BY status
                """,
                (run_id,),
            ).fetchall()
        }

    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    queued = counts.get("queued", 0)
    running = counts.get("running", 0)
    total = row["total_agents"]
    finished = completed + failed
    return {
        "run_id": row["run_id"],
        "patient_id": row["patient_id"],
        "case_version_id": row["case_version_id"],
        "case_version_number": row["case_version_number"],
        "status": row["status"],
        "total_agents": total,
        "completed_count": completed,
        "failed_count": failed,
        "queued_count": queued,
        "running_count": running,
        "finished_count": finished,
        "progress_percent": round((finished / total) * 100, 1) if total else 0,
        "current_agent_id": row["current_agent_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "case_snapshot_sha256": hashlib.sha256(row["case_json"].encode("utf-8")).hexdigest(),
        "all_agents_required": True,
        "independent_assessments": True,
    }


def list_results(run_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as db:
        exists = db.execute(
            "SELECT 1 FROM simulation_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if exists is None:
            raise KeyError(run_id)
        rows = db.execute(
            """
            SELECT * FROM agent_run_results
            WHERE run_id = ?
            ORDER BY rowid ASC
            """,
            (run_id,),
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        assessment = (
            json.loads(row["assessment_json"]) if row["assessment_json"] else None
        )
        results.append(
            {
                "agent_id": row["agent_id"],
                "agent_name": row["agent_name"],
                "category_label": row["category_label"],
                "status": row["status"],
                "assessment": assessment,
                "error_message": row["error_message"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "duration_seconds": row["duration_seconds"],
            }
        )
    return results


def mark_run_running(run_id: str) -> None:
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE simulation_runs SET status = 'running', updated_at = ?
            WHERE run_id = ?
            """,
            (now, run_id),
        )


def mark_agent_running(run_id: str, agent_id: str) -> None:
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE agent_run_results
            SET status = 'running', assessment_json = NULL, error_message = NULL,
                started_at = ?, completed_at = NULL
            WHERE run_id = ? AND agent_id = ? AND status != 'completed'
            """,
            (now, run_id, agent_id),
        )
        db.execute(
            """
            UPDATE simulation_runs
            SET current_agent_id = ?, updated_at = ?
            WHERE run_id = ?
            """,
            (agent_id, now, run_id),
        )


def save_agent_success(
    run_id: str, agent_id: str, assessment_json: str, duration_seconds: float
) -> None:
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE agent_run_results
            SET status = 'completed', assessment_json = ?, error_message = NULL,
                completed_at = ?, duration_seconds = ?
            WHERE run_id = ? AND agent_id = ?
            """,
            (assessment_json, now, duration_seconds, run_id, agent_id),
        )
        db.execute(
            "UPDATE simulation_runs SET updated_at = ? WHERE run_id = ?",
            (now, run_id),
        )


def save_agent_failure(
    run_id: str, agent_id: str, error_message: str, duration_seconds: float
) -> None:
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE agent_run_results
            SET status = 'failed', assessment_json = NULL, error_message = ?,
                completed_at = ?, duration_seconds = ?
            WHERE run_id = ? AND agent_id = ?
            """,
            (error_message[:500], now, duration_seconds, run_id, agent_id),
        )
        db.execute(
            "UPDATE simulation_runs SET updated_at = ? WHERE run_id = ?",
            (now, run_id),
        )


def mark_run_finished(run_id: str) -> None:
    summary = get_run(run_id)
    if summary["queued_count"] or summary["running_count"]:
        status = "queued"
    elif summary["failed_count"]:
        status = "completed_with_errors"
    else:
        status = "completed"
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE simulation_runs
            SET status = ?, current_agent_id = NULL, updated_at = ?
            WHERE run_id = ?
            """,
            (status, now, run_id),
        )


def reset_interrupted_agents(run_id: str) -> None:
    """Return an interrupted in-progress agent to queued while preserving successes."""
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE agent_run_results
            SET status = 'queued', assessment_json = NULL, started_at = NULL, error_message = NULL
            WHERE run_id = ? AND status = 'running'
            """,
            (run_id,),
        )
        db.execute(
            """
            UPDATE simulation_runs SET status = 'queued', current_agent_id = NULL, updated_at = ?
            WHERE run_id = ?
            """,
            (now, run_id),
        )



def _ensure_round_tables(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS round_runs (
            run_id TEXT NOT NULL,
            round_number INTEGER NOT NULL,
            status TEXT NOT NULL,
            total_agents INTEGER NOT NULL,
            current_agent_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (run_id, round_number),
            FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_round_results (
            run_id TEXT NOT NULL,
            round_number INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            category_label TEXT NOT NULL,
            status TEXT NOT NULL,
            result_json TEXT,
            error_message TEXT,
            started_at TEXT,
            completed_at TEXT,
            duration_seconds REAL,
            PRIMARY KEY (run_id, round_number, agent_id),
            FOREIGN KEY (run_id, round_number)
                REFERENCES round_runs(run_id, round_number) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_agent_round_results_status
        ON agent_round_results(run_id, round_number, status);
        """
    )


def create_round_job(run_id: str, round_number: int) -> dict[str, Any]:
    """Create a round only when the preceding required stage is fully complete."""
    if round_number not in (2, 3, 4):
        raise ValueError("Only rounds 2, 3, and 4 can be advanced here.")
    get_run(run_id)
    if round_number == 2:
        first = get_run(run_id)
        if first["completed_count"] != first["total_agents"] or first["failed_count"]:
            raise ValueError("Round 1 must have all 45 successful independent assessments.")
        total = len(AGENT_PROFILES)
        profiles = AGENT_PROFILES
    elif round_number == 3:
        try:
            previous = get_round_summary(run_id, 2)
        except KeyError as exc:
            raise ValueError("Round 2 must be completed before Round 3.") from exc
        if previous["status"] != "completed":
            raise ValueError("Round 2 must be completed before Round 3.")
        total = len(AGENT_PROFILES)
        profiles = AGENT_PROFILES
    else:
        try:
            previous = get_round_summary(run_id, 3)
        except KeyError as exc:
            raise ValueError("Round 3 must be completed before Round 4.") from exc
        if previous["status"] != "completed":
            raise ValueError("Round 3 must be completed before Round 4.")
        total = 1
        chair = next(p for p in AGENT_PROFILES if p["agent_id"] == "SG-07")
        profiles = [{**chair, "category_label": "Final MDT report"}]

    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        existing = db.execute(
            "SELECT status FROM round_runs WHERE run_id = ? AND round_number = ?",
            (run_id, round_number),
        ).fetchone()
        if existing:
            raise ValueError(
                f"Round {round_number} already exists with status {existing['status']}; use its resume endpoint if it has errors."
            )
        db.execute(
            """
            INSERT INTO round_runs
            (run_id, round_number, status, total_agents, current_agent_id, created_at, updated_at)
            VALUES (?, ?, 'queued', ?, NULL, ?, ?)
            ON CONFLICT(run_id, round_number) DO UPDATE SET
                status = 'queued', total_agents = excluded.total_agents,
                current_agent_id = NULL, created_at = excluded.created_at,
                updated_at = excluded.updated_at
            """,
            (run_id, round_number, total, now, now),
        )
        db.execute(
            "DELETE FROM agent_round_results WHERE run_id = ? AND round_number = ?",
            (run_id, round_number),
        )
        db.executemany(
            """
            INSERT INTO agent_round_results
            (run_id, round_number, agent_id, agent_name, category_label, status)
            VALUES (?, ?, ?, ?, ?, 'queued')
            """,
            [
                (run_id, round_number, p["agent_id"], p["name"], p["category_label"])
                for p in profiles
            ],
        )
    return get_round_summary(run_id, round_number)


def get_round_summary(run_id: str, round_number: int) -> dict[str, Any]:
    with _connect() as db:
        _ensure_round_tables(db)
        row = db.execute(
            "SELECT * FROM round_runs WHERE run_id = ? AND round_number = ?",
            (run_id, round_number),
        ).fetchone()
        if row is None:
            raise KeyError((run_id, round_number))
        counts = {
            item["status"]: item["count"]
            for item in db.execute(
                """
                SELECT status, COUNT(*) AS count FROM agent_round_results
                WHERE run_id = ? AND round_number = ? GROUP BY status
                """,
                (run_id, round_number),
            ).fetchall()
        }
    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    queued = counts.get("queued", 0)
    running = counts.get("running", 0)
    total = row["total_agents"]
    finished = completed + failed
    return {
        "run_id": row["run_id"],
        "round_number": row["round_number"],
        "status": row["status"],
        "total_agents": total,
        "completed_count": completed,
        "failed_count": failed,
        "queued_count": queued,
        "running_count": running,
        "finished_count": finished,
        "progress_percent": round(finished * 100 / total, 1) if total else 0,
        "current_agent_id": row["current_agent_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_round_results(run_id: str, round_number: int) -> list[dict[str, Any]]:
    with _connect() as db:
        _ensure_round_tables(db)
        rows = db.execute(
            """
            SELECT * FROM agent_round_results
            WHERE run_id = ? AND round_number = ? ORDER BY rowid
            """,
            (run_id, round_number),
        ).fetchall()
        if not rows and not db.execute(
            "SELECT 1 FROM round_runs WHERE run_id = ? AND round_number = ?",
            (run_id, round_number),
        ).fetchone():
            raise KeyError((run_id, round_number))
    return [
        {
            "agent_id": row["agent_id"],
            "agent_name": row["agent_name"],
            "category_label": row["category_label"],
            "status": row["status"],
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error_message": row["error_message"],
            "duration_seconds": row["duration_seconds"],
        }
        for row in rows
    ]


def get_round_result(run_id: str, round_number: int, agent_id: str) -> dict[str, Any] | None:
    with _connect() as db:
        _ensure_round_tables(db)
        row = db.execute(
            """
            SELECT result_json FROM agent_round_results
            WHERE run_id = ? AND round_number = ? AND agent_id = ? AND status = 'completed'
            """,
            (run_id, round_number, agent_id),
        ).fetchone()
    return json.loads(row["result_json"]) if row and row["result_json"] else None


def mark_round_running(run_id: str, round_number: int) -> None:
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            "UPDATE round_runs SET status = 'running', updated_at = ? WHERE run_id = ? AND round_number = ?",
            (now, run_id, round_number),
        )


def mark_round_agent_running(run_id: str, round_number: int, agent_id: str) -> None:
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            """
            UPDATE agent_round_results SET status = 'running', result_json = NULL,
                error_message = ?, started_at = ?, completed_at = NULL
            WHERE run_id = ? AND round_number = ? AND agent_id = ?
            """,
            (None, now, run_id, round_number, agent_id),
        )
        db.execute(
            "UPDATE round_runs SET current_agent_id = ?, updated_at = ? WHERE run_id = ? AND round_number = ?",
            (agent_id, now, run_id, round_number),
        )


def save_round_success(
    run_id: str, round_number: int, agent_id: str, result_json: str, duration_seconds: float
) -> None:
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            """
            UPDATE agent_round_results SET status = 'completed', result_json = ?,
                error_message = NULL, completed_at = ?, duration_seconds = ?
            WHERE run_id = ? AND round_number = ? AND agent_id = ?
            """,
            (result_json, now, duration_seconds, run_id, round_number, agent_id),
        )
        db.execute(
            "UPDATE round_runs SET updated_at = ? WHERE run_id = ? AND round_number = ?",
            (now, run_id, round_number),
        )


def save_round_failure(
    run_id: str, round_number: int, agent_id: str, error_message: str, duration_seconds: float
) -> None:
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            """
            UPDATE agent_round_results SET status = 'failed', result_json = NULL,
                error_message = ?, completed_at = ?, duration_seconds = ?
            WHERE run_id = ? AND round_number = ? AND agent_id = ?
            """,
            (error_message[:500], now, duration_seconds, run_id, round_number, agent_id),
        )
        db.execute(
            "UPDATE round_runs SET updated_at = ? WHERE run_id = ? AND round_number = ?",
            (now, run_id, round_number),
        )


def mark_round_finished(run_id: str, round_number: int) -> None:
    summary = get_round_summary(run_id, round_number)
    if summary["queued_count"] or summary["running_count"]:
        status = "queued"
    elif summary["failed_count"]:
        status = "completed_with_errors"
    else:
        status = "completed"
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            """
            UPDATE round_runs SET status = ?, current_agent_id = NULL, updated_at = ?
            WHERE run_id = ? AND round_number = ?
            """,
            (status, now, run_id, round_number),
        )
        # Keep the parent run timestamp current through all four rounds.
        if round_number == 4 and status in {"completed", "completed_with_errors"}:
            overall_status = "completed" if status == "completed" else "completed_with_errors"
            db.execute(
                "UPDATE simulation_runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (overall_status, now, run_id),
            )
        else:
            db.execute("UPDATE simulation_runs SET updated_at = ? WHERE run_id = ?", (now, run_id))


def reset_failed_round_agents(run_id: str, round_number: int) -> None:
    now = _now()
    with _connect() as db:
        _ensure_round_tables(db)
        db.execute(
            """
            UPDATE agent_round_results
            SET status = 'queued', result_json = NULL, error_message = NULL, started_at = NULL,
                completed_at = NULL, duration_seconds = NULL
            WHERE run_id = ? AND round_number = ? AND status IN ('failed', 'running')
            """,
            (run_id, round_number),
        )
        db.execute(
            """
            UPDATE round_runs SET status = 'queued', current_agent_id = NULL, updated_at = ?
            WHERE run_id = ? AND round_number = ?
            """,
            (now, run_id, round_number),
        )


def get_final_report(run_id: str) -> dict[str, Any] | None:
    result = get_round_result(run_id, 4, "SG-07")
    return result

def reset_failed_agents(run_id: str) -> None:
    now = _now()
    with _connect() as db:
        db.execute(
            """
            UPDATE agent_run_results
            SET status = 'queued', error_message = NULL, started_at = NULL,
                completed_at = NULL, duration_seconds = NULL
            WHERE run_id = ? AND status = 'failed'
            """,
            (run_id,),
        )
        db.execute(
            """
            UPDATE simulation_runs SET status = 'queued', current_agent_id = NULL, updated_at = ?
            WHERE run_id = ?
            """,
            (now, run_id),
        )
