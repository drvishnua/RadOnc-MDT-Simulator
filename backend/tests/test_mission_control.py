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

def test_mission_control_role_details_show_all_expected_roles_and_only_metadata(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control-roles.sqlite3")
    run_id = _create_run()

    response = client.get(f"/api/mission-control/{run_id}/rounds/1/roles")

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["expected_role_count"] == 45
    assert body["persisted_role_count"] == 45
    assert body["missing_role_record_count"] == 0
    assert len(body["roles"]) == 45
    first = body["roles"][0]
    assert first["agent_id"] == "RO-01"
    assert first["agent_name"]
    assert first["category_label"] == "Radiation Oncology"
    assert first["status"] == "queued"
    assert first["started_at"] is None
    assert first["completed_at"] is None
    assert first["duration_seconds"] is None

    serialized = response.text
    assert "Fictional case text must not be exposed" not in serialized
    assert "assessment_json" not in serialized
    assert "result_json" not in serialized
    assert "error_message" not in serialized
    assert "provisional_conclusion" not in serialized


def test_mission_control_role_details_distinguish_not_started_from_missing_rows(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control-not-started.sqlite3")
    run_id = _create_run()

    r2 = client.get(f"/api/mission-control/{run_id}/rounds/2/roles").json()
    r4 = client.get(f"/api/mission-control/{run_id}/rounds/4/roles").json()
    assert r2["expected_role_count"] == 45
    assert r2["status_counts"] == {"not_started": 45}
    assert r4["expected_role_count"] == 1
    assert r4["roles"][0]["agent_id"] == "SG-07"
    assert r4["status_counts"] == {"not_started": 1}

    with run_store._connect() as db:
        db.execute(
            "UPDATE agent_run_results SET status = 'completed' WHERE run_id = ?",
            (run_id,),
        )
        db.execute(
            "UPDATE simulation_runs SET status = 'completed' WHERE run_id = ?",
            (run_id,),
        )
    run_store.create_round_job(run_id, 2)
    with run_store._connect() as db:
        db.execute(
            "DELETE FROM agent_round_results WHERE run_id = ? AND round_number = 2 AND agent_id = 'RO-02'",
            (run_id,),
        )
    result = client.get(f"/api/mission-control/{run_id}/rounds/2/roles").json()
    assert result["status_counts"]["missing_record"] == 1
    assert result["roles"][1]["agent_id"] == "RO-02"
    assert result["roles"][1]["status"] == "missing_record"


def test_mission_control_role_details_preserve_saved_failure_and_timing_without_error_text(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control-timing.sqlite3")
    run_id = _create_run()
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
            SET status = 'failed', error_message = 'private synthetic failure detail',
                started_at = '2026-11-16T10:00:00+00:00',
                completed_at = '2026-11-16T10:00:03+00:00',
                duration_seconds = 3.0
            WHERE run_id = ? AND round_number = 2 AND agent_id = 'RO-01'
            """,
            (run_id,),
        )
    response = client.get(f"/api/mission-control/{run_id}/rounds/2/roles")
    assert response.status_code == 200
    role = response.json()["roles"][0]
    assert role["status"] == "failed"
    assert role["started_at"] == "2026-11-16T10:00:00+00:00"
    assert role["completed_at"] == "2026-11-16T10:00:03+00:00"
    assert role["duration_seconds"] == 3.0
    assert "private synthetic failure detail" not in response.text
    assert "error_message" not in response.text


def test_mission_control_role_details_return_only_the_chair_in_round_four(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mission-control-chair.sqlite3")
    run_id = _create_run()
    with run_store._connect() as db:
        db.execute("UPDATE agent_run_results SET status = 'completed' WHERE run_id = ?", (run_id,))
        db.execute("UPDATE simulation_runs SET status = 'completed' WHERE run_id = ?", (run_id,))
    run_store.create_round_job(run_id, 2)
    with run_store._connect() as db:
        db.execute(
            "UPDATE agent_round_results SET status = 'completed' WHERE run_id = ? AND round_number = 2",
            (run_id,),
        )
        db.execute(
            "UPDATE round_runs SET status = 'completed' WHERE run_id = ? AND round_number = 2",
            (run_id,),
        )
    run_store.create_round_job(run_id, 3)
    with run_store._connect() as db:
        db.execute(
            "UPDATE agent_round_results SET status = 'completed' WHERE run_id = ? AND round_number = 3",
            (run_id,),
        )
        db.execute(
            "UPDATE round_runs SET status = 'completed' WHERE run_id = ? AND round_number = 3",
            (run_id,),
        )
    run_store.create_round_job(run_id, 4)
    response = client.get(f"/api/mission-control/{run_id}/rounds/4/roles")
    assert response.status_code == 200
    body = response.json()
    assert body["expected_role_count"] == 1
    assert [role["agent_id"] for role in body["roles"]] == ["SG-07"]
    assert body["roles"][0]["category_label"] == "Final MDT report"


def test_mission_control_role_details_validate_round_and_run() -> None:
    assert client.get("/api/mission-control/not-a-run/rounds/1/roles").status_code == 404
    assert client.get("/api/mission-control/not-a-run/rounds/0/roles").status_code == 422
    assert client.get("/api/mission-control/not-a-run/rounds/5/roles").status_code == 422
