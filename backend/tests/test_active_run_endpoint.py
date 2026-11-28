"""Tests for GET /api/runs/active endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SyntheticCase
from app.services import run_store

client = TestClient(app)


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "active_runs.sqlite3")
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()


def _make_case(title: str = "Synthetic active-run case") -> SyntheticCase:
    return SyntheticCase(
        scenario_title=title,
        case_summary="Fictional radiation oncology training case for active-run endpoint testing.",
        age_years=62,
        primary_site="Oropharynx",
        histology="Squamous cell carcinoma",
        known_unknowns=["p16 status not reported"],
    )


def test_active_run_empty_database(isolated_db) -> None:
    response = client.get("/api/runs/active")
    assert response.status_code == 200
    assert response.json() == {"active": False, "run": None}


def test_active_run_ignores_inactive_runs(isolated_db) -> None:
    run = run_store.create_run(_make_case())
    run_store.mark_run_status(run["run_id"], "completed")

    response = client.get("/api/runs/active")
    assert response.status_code == 200
    assert response.json() == {"active": False, "run": None}


@pytest.mark.parametrize("status", ["queued", "running", "paused"])
def test_active_run_discovers_r1_active_or_paused_run(isolated_db, status: str) -> None:
    run = run_store.create_run(_make_case())
    if status != "queued":
        run_store.mark_run_status(run["run_id"], status)

    response = client.get("/api/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is True
    assert body["run"]["run_id"] == run["run_id"]
    assert body["run"]["status"] == status


def test_active_run_discovers_active_latest_round_when_r1_completed(isolated_db) -> None:
    run = run_store.create_run(_make_case())
    run_id = run["run_id"]
    run_store.mark_run_status(run_id, "completed")
    with run_store._connect() as db:
        run_store._ensure_round_tables(db)
        db.execute(
            """
            INSERT INTO round_runs (run_id, round_number, status, total_agents, created_at, updated_at)
            VALUES (?, 2, 'running', 45, ?, ?)
            """,
            (run_id, run["created_at"], run["updated_at"]),
        )

    response = client.get("/api/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is True
    assert body["run"]["run_id"] == run_id
    assert body["run"]["status"] == "completed"
    assert body["run"]["round_status"]["2"] == "running"


def test_active_run_returns_latest_active_run(isolated_db) -> None:
    older = run_store.create_run(_make_case("Older paused case"))
    run_store.mark_run_status(older["run_id"], "paused")

    newer = run_store.create_run(_make_case("Newer running case"))
    run_store.mark_run_status(newer["run_id"], "running")

    response = client.get("/api/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is True
    assert body["run"]["run_id"] == newer["run_id"]
