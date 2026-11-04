from collections import Counter

from fastapi.testclient import TestClient

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES
from app.main import app
from app.services import batch_runner, run_store

client = TestClient(app)


def _fake_assessment(profile, case, round_number):
    return AgentAssessment(
        agent_id=profile["agent_id"],
        round_number=round_number,
        position="conditional",
        provisional_conclusion="A provisional educational conclusion is conditional because important case details remain unknown.",
        preferred_educational_option="No option can be preferred until the outstanding details are clarified.",
        perspective_summary=f"Independent educational assessment from {profile['name']} for a synthetic case.",
        confidence=0.5,
        evidence_gaps=["No evidence retrieval source is connected in this test."],
    )


def _case_payload():
    return {
        "scenario_title": "Synthetic HN batch test",
        "case_summary": "Fictional head-and-neck case used only for automated batch-run testing.",
        "age_years": 59,
        "primary_site": "Oropharynx",
        "histology": "Squamous cell carcinoma",
    }


def test_batch_run_executes_all_45_agents_independently(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "batch.sqlite3")
    calls = []

    async def fake_generate(profile, case, round_number):
        calls.append((profile["agent_id"], case.model_dump_json(), round_number))
        return _fake_assessment(profile, case, round_number)

    monkeypatch.setattr(batch_runner, "generate_agent_assessment", fake_generate)
    response = client.post("/api/runs", json={"case": _case_payload()})

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "completed"
    assert run["total_agents"] == 45
    assert run["completed_count"] == 45
    assert run["failed_count"] == 0
    assert run["progress_percent"] == 100.0
    assert len(calls) == 45
    assert len({call[0] for call in calls}) == 45
    assert len({call[1] for call in calls}) == 1
    assert {call[2] for call in calls} == {1}

    results_response = client.get(f"/api/runs/{run_id}/results")
    assert results_response.status_code == 200
    results = results_response.json()["results"]
    assert len(results) == 45
    assert all(item["status"] == "completed" for item in results)
    assert all(item["assessment"]["not_a_treatment_instruction"] is True for item in results)
    assert all(item["assessment"]["provisional_conclusion"] for item in results)


def test_batch_continues_after_failure_and_resume_runs_only_failed_agent(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "resume.sqlite3")
    calls = Counter()
    fail_first_ro01 = {"enabled": True}

    async def fake_generate(profile, case, round_number):
        calls[profile["agent_id"]] += 1
        if profile["agent_id"] == "RO-01" and fail_first_ro01["enabled"]:
            fail_first_ro01["enabled"] = False
            raise RuntimeError("intentional test failure")
        return _fake_assessment(profile, case, round_number)

    monkeypatch.setattr(batch_runner, "generate_agent_assessment", fake_generate)
    response = client.post("/api/runs", json={"case": _case_payload()})

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "completed_with_errors"
    assert run["completed_count"] == 44
    assert run["failed_count"] == 1
    assert calls["RO-01"] == 1
    assert all(calls[p["agent_id"]] == 1 for p in AGENT_PROFILES if p["agent_id"] != "RO-01")

    resume_response = client.post(f"/api/runs/{run_id}/resume")
    assert resume_response.status_code == 200
    resumed = client.get(f"/api/runs/{run_id}").json()
    assert resumed["status"] == "completed"
    assert resumed["completed_count"] == 45
    assert resumed["failed_count"] == 0
    assert calls["RO-01"] == 2
    assert all(calls[p["agent_id"]] == 1 for p in AGENT_PROFILES if p["agent_id"] != "RO-01")


def test_batch_status_for_unknown_run_returns_404(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "missing.sqlite3")
    response = client.get("/api/runs/not-a-real-run")
    assert response.status_code == 404
