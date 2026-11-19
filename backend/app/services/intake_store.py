"""Append-only, hash-chained pre-MDT intake session persistence."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from app import run_store
from app.clinical_fields import CLINICAL_FIELD_REGISTRY, CLINICAL_FIELD_REGISTRY_VERSION
from app.schemas import SyntheticCase
from app.services.intake_screening import screen_case_intake

_ZERO_HASH = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _connect():
    run_store.initialize_database()
    connection = sqlite3.connect(run_store.DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS intake_sessions (
            session_id TEXT PRIMARY KEY,
            current_case_json TEXT NOT NULL,
            current_case_sha256 TEXT NOT NULL,
            declined_domains_json TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('SCREENING', 'ACCEPTED_WITH_GAPS')),
            registry_version TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            accepted_at TEXT
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS intake_events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            sequence_number INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            case_snapshot_json TEXT NOT NULL,
            case_snapshot_sha256 TEXT NOT NULL,
            previous_event_sha256 TEXT NOT NULL,
            event_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(session_id, sequence_number),
            FOREIGN KEY(session_id) REFERENCES intake_sessions(session_id) ON DELETE CASCADE
        )
    """)
    return connection


def _event_hash(
    *, event_id: str, session_id: str, sequence_number: int, event_type: str,
    payload_json: str, case_snapshot_sha256: str, previous_event_sha256: str,
    created_at: str,
) -> str:
    return _digest(_canonical_json({
        "event_id": event_id,
        "session_id": session_id,
        "sequence_number": sequence_number,
        "event_type": event_type,
        "payload_json": payload_json,
        "case_snapshot_sha256": case_snapshot_sha256,
        "previous_event_sha256": previous_event_sha256,
        "created_at": created_at,
    }))


def _append_event(
    db: sqlite3.Connection, *, session_id: str, event_type: str,
    payload: dict[str, Any], case_json: str, case_sha256: str,
) -> dict[str, Any]:
    previous = db.execute(
        "SELECT sequence_number, event_sha256 FROM intake_events "
        "WHERE session_id = ? ORDER BY sequence_number DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    sequence = int(previous["sequence_number"]) + 1 if previous else 1
    previous_hash = str(previous["event_sha256"]) if previous else _ZERO_HASH
    event_id = str(uuid.uuid4())
    created_at = _now()
    payload_json = _canonical_json(payload)
    event_hash = _event_hash(
        event_id=event_id, session_id=session_id, sequence_number=sequence,
        event_type=event_type, payload_json=payload_json,
        case_snapshot_sha256=case_sha256,
        previous_event_sha256=previous_hash, created_at=created_at,
    )
    db.execute(
        """INSERT INTO intake_events
        (event_id, session_id, sequence_number, event_type, payload_json,
         case_snapshot_json, case_snapshot_sha256, previous_event_sha256,
         event_sha256, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, session_id, sequence, event_type, payload_json, case_json,
         case_sha256, previous_hash, event_hash, created_at),
    )
    return {
        "event_id": event_id, "sequence_number": sequence, "event_type": event_type,
        "payload": payload, "case_snapshot_sha256": case_sha256,
        "previous_event_sha256": previous_hash, "event_sha256": event_hash,
        "created_at": created_at,
    }


def create_intake_session(case: SyntheticCase) -> dict[str, Any]:
    case_json = case.model_dump_json(exclude_none=True)
    case_sha = _digest(case_json)
    session_id = str(uuid.uuid4())
    now = _now()
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            """INSERT INTO intake_sessions
            (session_id, current_case_json, current_case_sha256, declined_domains_json,
             state, registry_version, event_count, created_at, updated_at)
            VALUES (?, ?, ?, '[]', 'SCREENING', ?, 0, ?, ?)""",
            (session_id, case_json, case_sha, CLINICAL_FIELD_REGISTRY_VERSION, now, now),
        )
        _append_event(
            db, session_id=session_id, event_type="CASE_CREATED",
            payload={"case_snapshot_sha256": case_sha,
                     "registry_version": CLINICAL_FIELD_REGISTRY_VERSION},
            case_json=case_json, case_sha256=case_sha,
        )
        db.execute(
            "UPDATE intake_sessions SET event_count = 1 WHERE session_id = ?",
            (session_id,),
        )
    return get_intake_session(session_id)


def _verified_events(db: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        "SELECT * FROM intake_events WHERE session_id = ? ORDER BY sequence_number",
        (session_id,),
    ).fetchall()
    previous_hash = _ZERO_HASH
    events: list[dict[str, Any]] = []
    for expected_sequence, row in enumerate(rows, start=1):
        payload_json = str(row["payload_json"])
        expected_hash = _event_hash(
            event_id=row["event_id"], session_id=session_id,
            sequence_number=int(row["sequence_number"]), event_type=row["event_type"],
            payload_json=payload_json,
            case_snapshot_sha256=row["case_snapshot_sha256"],
            previous_event_sha256=row["previous_event_sha256"],
            created_at=row["created_at"],
        )
        snapshot = str(row["case_snapshot_json"])
        if (
            int(row["sequence_number"]) != expected_sequence
            or row["previous_event_sha256"] != previous_hash
            or _digest(snapshot) != row["case_snapshot_sha256"]
            or expected_hash != row["event_sha256"]
        ):
            raise ValueError("Intake event-chain or case-snapshot integrity verification failed.")
        previous_hash = expected_hash
        events.append({
            "event_id": row["event_id"],
            "sequence_number": expected_sequence,
            "event_type": row["event_type"],
            "payload": json.loads(payload_json),
            "case_snapshot_sha256": row["case_snapshot_sha256"],
            "previous_event_sha256": row["previous_event_sha256"],
            "event_sha256": expected_hash,
            "created_at": row["created_at"],
        })
    return events


def get_intake_session(session_id: str) -> dict[str, Any]:
    with _connect() as db:
        session = db.execute(
            "SELECT * FROM intake_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise KeyError(session_id)
        events = _verified_events(db, session_id)
        if len(events) != int(session["event_count"]):
            raise ValueError("Intake session event count does not match its audit history.")
        case = SyntheticCase.model_validate(json.loads(session["current_case_json"]))
        if _digest(session["current_case_json"]) != session["current_case_sha256"]:
            raise ValueError("Current intake case snapshot hash verification failed.")
        declined = json.loads(session["declined_domains_json"])
        screening = screen_case_intake(case, declined_domains=declined)
        return {
            "session_id": session_id,
            "state": session["state"],
            "registry_version": session["registry_version"],
            "case": case.model_dump(exclude_none=True),
            "case_snapshot_sha256": session["current_case_sha256"],
            "declined_domains": declined,
            "screening": screening,
            "events": events,
            "event_count": len(events),
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "accepted_at": session["accepted_at"],
        }


def record_intake_event(
    session_id: str, *, event_type: str, field_id: str | None = None,
    value: Any = None, domain: str | None = None, source_text: str | None = None,
) -> dict[str, Any]:
    if event_type not in {"ANSWER", "CORRECTION", "DECLINE_DOMAIN"}:
        raise ValueError("Unsupported intake event type.")
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        session = db.execute(
            "SELECT * FROM intake_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise KeyError(session_id)
        if session["state"] != "SCREENING":
            raise ValueError("Accepted intake sessions are immutable; create a new case version to amend.")
        case_data = json.loads(session["current_case_json"])
        declined = set(json.loads(session["declined_domains_json"]))
        payload: dict[str, Any] = {"source_text": source_text}
        case_json = str(session["current_case_json"])
        case_sha = str(session["current_case_sha256"])

        if event_type in {"ANSWER", "CORRECTION"}:
            if not isinstance(field_id, str) or field_id not in CLINICAL_FIELD_REGISTRY:
                raise ValueError("A registered clinical field_id is required.")
            current_value = case_data.get(field_id)
            current_reported = current_value not in (None, "") and current_value != []
            if event_type == "ANSWER" and current_reported:
                raise ValueError("Field already has a value; use CORRECTION to preserve the change history.")
            if event_type == "CORRECTION" and not current_reported:
                raise ValueError("Cannot correct a field that has no previously recorded value.")
            before_sha = case_sha
            case_data[field_id] = value
            updated_case = SyntheticCase.model_validate(case_data)
            case_json = updated_case.model_dump_json(exclude_none=True)
            case_sha = _digest(case_json)
            payload.update({
                "field_id": field_id, "raw_value": value,
                "prior_case_snapshot_sha256": before_sha,
                "new_case_snapshot_sha256": case_sha,
            })
        else:
            if not isinstance(domain, str) or not domain.strip():
                raise ValueError("A screening domain is required.")
            screening = screen_case_intake(SyntheticCase.model_validate(case_data))
            known_domains = {item["domain"] for item in screening["domains"]}
            if domain not in known_domains:
                raise ValueError("Unknown intake screening domain.")
            declined.add(domain)
            payload["domain"] = domain

        declined_json = _canonical_json(sorted(declined))
        event = _append_event(
            db, session_id=session_id, event_type=event_type, payload=payload,
            case_json=case_json, case_sha256=case_sha,
        )
        db.execute(
            """UPDATE intake_sessions SET current_case_json = ?, current_case_sha256 = ?,
            declined_domains_json = ?, event_count = event_count + 1, updated_at = ?
            WHERE session_id = ?""",
            (case_json, case_sha, declined_json, _now(), session_id),
        )
    return get_intake_session(session_id)


def accept_intake_with_gaps(session_id: str, *, confirmed: bool) -> dict[str, Any]:
    if confirmed is not True:
        raise ValueError("Explicit confirmation is required to accept an intake with outstanding gaps.")
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        session = db.execute(
            "SELECT * FROM intake_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise KeyError(session_id)
        if session["state"] != "SCREENING":
            raise ValueError("Intake session has already been accepted.")
        case_json = str(session["current_case_json"])
        case_sha = str(session["current_case_sha256"])
        declined = json.loads(session["declined_domains_json"])
        case = SyntheticCase.model_validate(json.loads(case_json))
        screening = screen_case_intake(case, declined_domains=declined)
        _append_event(
            db, session_id=session_id, event_type="ACCEPTED_WITH_GAPS",
            payload={
                "explicit_user_confirmation": True,
                "remaining_gap_count": len(screening["gaps"]),
                "case_snapshot_sha256": case_sha,
            },
            case_json=case_json, case_sha256=case_sha,
        )
        db.execute(
            """UPDATE intake_sessions SET state = 'ACCEPTED_WITH_GAPS',
            event_count = event_count + 1, accepted_at = ?, updated_at = ?
            WHERE session_id = ?""",
            (_now(), _now(), session_id),
        )
    return get_intake_session(session_id)
