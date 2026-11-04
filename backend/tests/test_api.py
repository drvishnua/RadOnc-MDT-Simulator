from collections import Counter

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_is_educational_only() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "education_simulation_only"


def test_synthetic_case_validation_accepts_minimal_case() -> None:
    response = client.post(
        "/api/cases/validate",
        json={
            "scenario_title": "Synthetic oropharyngeal case",
            "case_summary": "Synthetic training case for API schema validation only.",
            "primary_site": "Oropharynx",
            "histology": "Squamous cell carcinoma",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["mode"] == "synthetic_educational_case"
    assert any("Age is not supplied" in warning for warning in body["warnings"])


def test_case_schema_rejects_identifying_extra_fields() -> None:
    response = client.post(
        "/api/cases/validate",
        json={
            "scenario_title": "Synthetic case",
            "case_summary": "Synthetic training case with no identifying information.",
            "patient_name": "Must be rejected",
        },
    )
    assert response.status_code == 422


def test_case_schema_rejects_blank_list_items() -> None:
    response = client.post(
        "/api/cases/validate",
        json={
            "scenario_title": "Synthetic case",
            "case_summary": "Synthetic training case with no identifying information.",
            "patient_goals": ["", "Preserve swallowing"],
        },
    )
    assert response.status_code == 422


def test_runtime_endpoint_returns_ollama_status(monkeypatch) -> None:
    async def fake_status() -> dict[str, object]:
        return {
            "reachable": True,
            "version": "test",
            "configured_model": "qwen3.5:4b",
            "configured_model_installed": True,
            "models": ["qwen3.5:4b"],
        }

    monkeypatch.setattr("app.main.get_ollama_status", fake_status)
    response = client.get("/api/runtime")
    assert response.status_code == 200
    assert response.json()["ollama"]["reachable"] is True


def test_agent_endpoint_returns_all_45_unique_profiles() -> None:
    response = client.get("/api/agents")
    assert response.status_code == 200
    body = response.json()
    agents = body["agents"]
    assert body["expected_agent_count"] == 45
    assert body["returned_agent_count"] == 45
    assert body["all_roles_required"] is True
    assert len({agent["agent_id"] for agent in agents}) == 45

    category_counts = Counter(agent["category"] for agent in agents)
    assert category_counts == {
        "radiation_oncology": 9,
        "medical_oncology": 8,
        "surgical_oncology": 8,
        "diagnostic_supportive": 3,
        "patient_perspective": 6,
        "system_governance": 8,
        "family_social_vulnerability": 3,
    }


def test_cors_allows_local_vite_origin() -> None:
    response = client.options(
        "/api/agents",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_cors_does_not_allow_arbitrary_origins() -> None:
    response = client.options(
        "/api/agents",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
