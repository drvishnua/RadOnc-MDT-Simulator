from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SyntheticCase
from app.services import run_store

client = TestClient(app)


def _create_run() -> str:
    case = SyntheticCase(
        scenario_title="Synthetic Mission Control test",
        case_summary="Fictional case text must not be exposed by the overview endpoint.",
        primary_site="Oropharynx",
        histology="Squamous cell carcinoma",
    )
    return run_store.create_run(case)["run_id"]


def test_mission_control_is_read_only_and_does_not_expose_case_or_agent_prose(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control.sqlite3")
    run_id = _create_run()

    response = client.get("/api/mission-control")

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["total_runs"] == 1
    assert body["count"] == 1
    run = body["runs"][0]
    assert run["run_id"] == run_id
    assert len(run["case_snapshot_sha256"]) == 64
    assert [round_item["round_number"] for round_item in run["rounds"]] == [1, 2, 3, 4]

    r1, r2, r3, r4 = run["rounds"]
    assert r1["status"] == "queued"
    assert r1["total_agents"] == 45
    assert r1["queued_count"] == 45
    assert r1["completed_count"] == 0
    assert r2["status"] == r3["status"] == r4["status"] == "not_started"
    assert [r2["total_agents"], r3["total_agents"], r4["total_agents"]] == [45, 45, 1]

    serialized = response.text
    assert "Fictional case text must not be exposed" not in serialized
    assert "scenario_title" not in serialized
    assert "case_summary" not in serialized
    assert "assessment" not in serialized
    assert "error_message" not in serialized


def test_mission_control_reflects_saved_role_statuses_and_keeps_failures_visible(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control-rounds.sqlite3")
    run_id = _create_run()

    # Establish a valid persisted R1 prerequisite before creating R2.
    with run_store._connect() as db:
        db.execute(
            "UPDATE agent_run_results SET status = 'completed', assessment_json = '{}' WHERE run_id = ?",
            (run_id,),
        )
        db.execute(
            "UPDATE simulation_runs SET status = 'completed' WHERE run_id = ?",
            (run_id,),
        )
    run_store.create_round_job(run_id, 2)

    with run_store._connect() as db:
        db.execute(
            """
            UPDATE agent_round_results
            SET status = 'completed', result_json = '{}'
            WHERE run_id = ? AND round_number = 2 AND agent_id = 'RO-01'
            """,
            (run_id,),
        )
        db.execute(
            """
            UPDATE agent_round_results
            SET status = 'running'
            WHERE run_id = ? AND round_number = 2 AND agent_id = 'RO-02'
            """,
            (run_id,),
        )
        db.execute(
            """
            UPDATE agent_round_results
            SET status = 'failed', error_message = 'synthetic test failure'
            WHERE run_id = ? AND round_number = 2 AND agent_id = 'RO-03'
            """,
            (run_id,),
        )
        db.execute(
            """
            UPDATE round_runs
            SET status = 'running', current_agent_id = 'RO-02'
            WHERE run_id = ? AND round_number = 2
            """,
            (run_id,),
        )

    response = client.get("/api/mission-control?limit=1")

    assert response.status_code == 200
    body = response.json()
    assert body["active_run_count"] == 1
    run = body["runs"][0]
    r1, r2, r3, r4 = run["rounds"]
    assert r1["completed_count"] == 45
    assert r1["failed_count"] == 0
    assert r2["status"] == "running"
    assert r2["current_agent_id"] == "RO-02"
    assert r2["completed_count"] == 1
    assert r2["running_count"] == 1
    assert r2["failed_count"] == 1
    assert r2["queued_count"] == 42
    assert r2["progress_percent"] == 4.4
    assert r3["status"] == r4["status"] == "not_started"
    assert body["failed_run_count"] == 1


def test_mission_control_validates_requested_history_limit() -> None:
    assert client.get("/api/mission-control?limit=0").status_code == 422
    assert client.get("/api/mission-control?limit=51").status_code == 422
