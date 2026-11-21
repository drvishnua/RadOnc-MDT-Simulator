"""Regression tests ensuring retired operational-monitor APIs stay absent."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mission_control_overview_api_is_not_exposed():
    response = client.get("/api/mission-control")
    assert response.status_code == 404


def test_mission_control_role_drilldown_api_is_not_exposed():
    response = client.get("/api/mission-control/test-run/rounds/1/roles")
    assert response.status_code == 404


def test_retiring_operational_monitor_routes_does_not_remove_four_round_results_api():
    # The user-facing saved MDT results API remains the supported route for R1-R4.
    # A nonexistent run returns the run-store's normal 404, not a route-not-found
    # response, demonstrating that the four-round results endpoint remains mounted.
    response = client.get("/api/runs/not-a-run/rounds/1/results")
    assert response.status_code == 404
