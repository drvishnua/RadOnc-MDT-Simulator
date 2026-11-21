"""Tests for the /api/runs/{run_id}/rounds/{round_number}/quality-audit endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SyntheticCase
from app.services import run_store

client = TestClient(app)


def test_quality_audit_endpoint_returns_404_for_unknown_run():
    response = client.get("/api/runs/nonexistent-run-id/rounds/1/quality-audit")
    assert response.status_code == 404


def test_quality_audit_endpoint_returns_audit_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "test.db")
    run_store.initialize_database()

    case = SyntheticCase(
        scenario_title="Larynx T1N0M0",
        case_summary="Patient with hoarseness and biopsy confirmed squamous cell carcinoma.",
        primary_site="Larynx",
        histology="SCC",
    )
    run = run_store.create_run(case)
    run_id = run["run_id"]

    # When no audit has been performed yet
    resp_empty = client.get(f"/api/runs/{run_id}/rounds/1/quality-audit")
    assert resp_empty.status_code == 200
    data_empty = resp_empty.json()
    assert data_empty["has_audit"] is False
    assert data_empty["quality_audit"] is None

    # When an audit is persisted
    audit_data = {
        "run_id": run_id,
        "round_number": 1,
        "reasoning_depth_flags": {},
        "role_differentiation": {"valid": True, "flags": []},
        "total_flags": 0,
    }
    run_store.save_round_quality_audit(run_id, 1, audit_data)

    resp = client.get(f"/api/runs/{run_id}/rounds/1/quality-audit")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_audit"] is True
    assert data["quality_audit"]["total_flags"] == 0
    assert data["quality_audit"]["role_differentiation"]["valid"] is True
