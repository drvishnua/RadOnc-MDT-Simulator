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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
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
            """
        )


def create_run(case: SyntheticCase) -> dict[str, Any]:
    initialize_database()
    run_id = str(uuid.uuid4())
    now = _now()
    with _connect() as db:
        db.execute(
            """
            INSERT INTO simulation_runs
            (run_id, case_json, status, total_agents, current_agent_id, created_at, updated_at)
            VALUES (?, ?, 'queued', ?, NULL, ?, ?)
            """,
            (run_id, case.model_dump_json(exclude_none=True), len(AGENT_PROFILES), now, now),
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
            SET status = 'running', error_message = NULL, started_at = ?, completed_at = NULL
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
            SET status = 'queued', started_at = NULL, error_message = NULL
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
            UPDATE agent_round_results SET status = 'running', error_message = ?,
                started_at = ?, completed_at = NULL
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
            UPDATE agent_round_results SET status = 'failed', error_message = ?,
                completed_at = ?, duration_seconds = ?
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
            SET status = 'queued', error_message = NULL, started_at = NULL,
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
