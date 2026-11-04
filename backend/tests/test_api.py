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
