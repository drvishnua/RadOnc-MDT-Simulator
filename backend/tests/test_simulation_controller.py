"""Unit tests for SimulationController and simulation lifecycle endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.simulation_controller import get_simulation_controller

client = TestClient(app)


def test_simulation_controller_pause_resume_stop(monkeypatch):
    from app.services import run_store
    monkeypatch.setattr(run_store, "mark_run_status", lambda r_id, s: None)
    monkeypatch.setattr(run_store, "mark_queued_agents_stopped", lambda r_id, round_number=None: None)
    controller = get_simulation_controller()
    run_id = "test-run-ctrl-123"

    # Initial state
    assert not controller.is_simulation_paused(run_id)
    assert not controller.is_simulation_stopped(run_id)

    # Pause
    controller.pause_simulation(run_id)
    assert controller.is_simulation_paused(run_id)

    # Resume
    controller.resume_simulation(run_id)
    assert not controller.is_simulation_paused(run_id)

    # Stop
    controller.stop_simulation(run_id)
    assert controller.is_simulation_stopped(run_id)


def test_round_and_agent_pause_stop(monkeypatch):
    from app.services import run_store
    monkeypatch.setattr(run_store, "mark_round_status", lambda r_id, r_num, s: None)
    monkeypatch.setattr(run_store, "mark_agent_status", lambda r_id, r_num, a_id, s: None)
    monkeypatch.setattr(run_store, "mark_queued_agents_stopped", lambda r_id, round_number=None: None)
    controller = get_simulation_controller()
    run_id = "test-run-round-456"

    # Round controls
    assert not controller.is_round_paused(run_id, 2)
    assert not controller.is_round_stopped(run_id, 2)

    controller.pause_round(run_id, 2)
    assert controller.is_round_paused(run_id, 2)

    controller.resume_round(run_id, 2)
    assert not controller.is_round_paused(run_id, 2)

    controller.stop_round(run_id, 2)
    assert controller.is_round_stopped(run_id, 2)

    # Agent controls
    assert not controller.is_agent_stopped(run_id, 3, "RO-01")
    controller.stop_agent(run_id, 3, "RO-01")
    assert controller.is_agent_stopped(run_id, 3, "RO-01")


def test_api_simulation_lifecycle_endpoints(monkeypatch):
    run_id = "test-api-lifecycle-789"

    # Mock run_store.get_run to return valid dict
    from app.services import run_store
    monkeypatch.setattr(run_store, "get_run", lambda r_id: {"run_id": r_id, "status": "running"})
    monkeypatch.setattr(run_store, "mark_run_status", lambda r_id, s: None)
    monkeypatch.setattr(run_store, "mark_round_status", lambda r_id, r_num, s: None)
    monkeypatch.setattr(run_store, "mark_agent_status", lambda r_id, r_num, a_id, s: None)
    monkeypatch.setattr(run_store, "mark_queued_agents_stopped", lambda r_id, round_number=None: None)

    # Pause simulation
    res = client.post(f"/api/runs/{run_id}/pause")
    assert res.status_code == 200
    assert res.json()["status"] == "paused"

    # Unpause simulation
    res = client.post(f"/api/runs/{run_id}/unpause")
    assert res.status_code == 200
    assert res.json()["status"] == "resumed"

    # Stop simulation
    res = client.post(f"/api/runs/{run_id}/stop")
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"

    # Pause specific round
    res = client.post(f"/api/runs/{run_id}/rounds/2/pause")
    assert res.status_code == 200
    assert res.json()["status"] == "paused"

    # Unpause specific round
    res = client.post(f"/api/runs/{run_id}/rounds/2/unpause")
    assert res.status_code == 200
    assert res.json()["status"] == "resumed"

    # Stop specific round
    res = client.post(f"/api/runs/{run_id}/rounds/2/stop")
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"

    # Pause specific round 1 routes to simulation
    res = client.post(f"/api/runs/{run_id}/rounds/1/pause")
    assert res.status_code == 200
    assert res.json()["status"] == "paused"

    # Unpause specific round 1
    res = client.post(f"/api/runs/{run_id}/rounds/1/unpause")
    assert res.status_code == 200
    assert res.json()["status"] == "resumed"

    # Stop specific round 1
    res = client.post(f"/api/runs/{run_id}/rounds/1/stop")
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"


def test_clear_stopped_agent(monkeypatch):
    from app.services import run_store
    monkeypatch.setattr(run_store, "get_run", lambda r_id: {"run_id": r_id, "status": "running"})
    monkeypatch.setattr(run_store, "mark_round_status", lambda r_id, r_num, s: None)
    monkeypatch.setattr(run_store, "mark_agent_status", lambda r_id, r_num, a_id, s: None)
    controller = get_simulation_controller()
    run_id = "test-clear-agent-999"

    controller.stop_agent(run_id, 1, "RO-01")
    assert controller.is_agent_stopped(run_id, 1, "RO-01")

    controller.clear_stopped_agent(run_id, 1, "RO-01")
    assert not controller.is_agent_stopped(run_id, 1, "RO-01")

    # Stop specific agent
    res = client.post(f"/api/runs/{run_id}/rounds/2/agents/RO-01/stop")
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"


def test_restart_clears_stopped_flags_and_enforces_concurrency_and_validation(monkeypatch):
    from app import main as app_main
    from app.services import run_store

    run_id = "test-restart-guards-101"
    controller = get_simulation_controller()

    monkeypatch.setattr(run_store, "get_run", lambda r_id: {"run_id": r_id, "status": "stopped"})
    monkeypatch.setattr(run_store, "mark_run_status", lambda r_id, s: None)
    monkeypatch.setattr(run_store, "mark_round_status", lambda r_id, r_num, s: None)
    monkeypatch.setattr(run_store, "mark_queued_agents_stopped", lambda r_id, round_number=None: None)
    monkeypatch.setattr(run_store, "restart_simulation", lambda r_id: None)
    monkeypatch.setattr(run_store, "restart_round", lambda r_id, r_num: None)
    monkeypatch.setattr(run_store, "restart_agent", lambda r_id, r_num, a_id: None)
    monkeypatch.setattr(app_main, "run_independent_assessments", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_main, "run_mdt_round", lambda *args, **kwargs: None)

    # Stop whole simulation, then restart -> stopped flag must be cleared
    monkeypatch.setattr(app_main, "batch_is_running", lambda: False)
    monkeypatch.setattr(app_main, "round_is_running", lambda: False)
    controller.stop_simulation(run_id)
    assert controller.is_simulation_stopped(run_id)
    assert controller.is_round_stopped(run_id, 2)

    res = client.post(f"/api/runs/{run_id}/restart")
    assert res.status_code == 200
    assert not controller.is_simulation_stopped(run_id)
    assert not controller.is_round_stopped(run_id, 2)

    # Stop round 3, then restart round 3 -> stopped flag for round 3 cleared
    controller.stop_round(run_id, 3)
    assert controller.is_round_stopped(run_id, 3)
    res = client.post(f"/api/runs/{run_id}/rounds/3/restart")
    assert res.status_code == 200
    assert not controller.is_round_stopped(run_id, 3)

    # Invalid round numbers rejected with 422
    assert client.post(f"/api/runs/{run_id}/rounds/0/pause").status_code == 422
    assert client.post(f"/api/runs/{run_id}/rounds/5/stop").status_code == 422

    # Concurrent execution blocked with 409 when another batch/round is active
    monkeypatch.setattr(app_main, "batch_is_running", lambda: True)
    assert client.post(f"/api/runs/{run_id}/restart").status_code == 409
    assert client.post(f"/api/runs/{run_id}/rounds/2/restart").status_code == 409
    assert client.post(f"/api/runs/{run_id}/rounds/2/agents/RO-01/run").status_code == 409
    assert (
        client.post(
            f"/api/runs/{run_id}/rounds/2/run-selected",
            json={"agent_ids": ["RO-01"]},
        ).status_code
        == 409
    )


def test_round_control_returns_404_for_missing_run(monkeypatch, tmp_path):
    from app.services import run_store

    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "missing_check.sqlite3")
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()

    res = client.post("/api/runs/does-not-exist/rounds/2/stop")
    assert res.status_code == 404
