from collections import Counter

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SyntheticCase

client = TestClient(app)


def test_health_endpoint_is_educational_only() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "education_simulation_only"


def test_fictional_case_validation_accepts_minimal_case() -> None:
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
    assert body["mode"] == "fictional_educational_case"
    assert any("Age is not supplied" in warning for warning in body["warnings"])


def test_synthetic_case_validation_accepts_full_structured_case() -> None:
    response = client.post(
        "/api/cases/validate",
        json={
            "scenario_title": "Synthetic structured rectal case",
            "case_summary": "Fictional case for complete structured-field validation.",
            "age_years": 60,
            "sex_at_birth": "Female",
            "primary_site": "Rectum",
            "histology": "Adenocarcinoma",
            "clinical_t_stage": "cT2",
            "clinical_n_stage": "cN1",
            "clinical_m_stage": "cM1",
            "stage_group": "IVA",
            "performance_status": "ECOG 1",
            "pathology_summary": "Synthetic biopsy summary.",
            "imaging_summary": "Synthetic imaging summary.",
            "relevant_comorbidities": ["Hypertension"],
            "prior_treatment": ["Diagnostic biopsy"],
            "patient_goals": ["Preserve function"],
            "social_context": ["Lives independently"],
            "resource_context": ["MRI available"],
            "known_unknowns": ["Further review of imaging is pending"],
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


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


def test_single_agent_assessment_rejects_unlinked_case_payload(monkeypatch) -> None:
    def unexpected_generation(*args, **kwargs):
        raise AssertionError("Unlinked case payload must be rejected before inference.")

    monkeypatch.setattr("app.main.generate_agent_assessment", unexpected_generation)
    response = client.post(
        "/api/agents/RO-01/assess",
        json={
            "round_number": 1,
            "case": {
                "scenario_title": "Synthetic test case",
                "case_summary": "A fictional case for API endpoint testing only.",
            },
        },
    )
    assert response.status_code == 409
    assert "unlinked case" in response.json()["detail"]


def test_legacy_batch_run_rejects_unlinked_case_payload(monkeypatch) -> None:
    from app.services import run_store

    def unexpected_create_run(*args, **kwargs):
        raise AssertionError("Unlinked case payload must be rejected before persistence.")

    monkeypatch.setattr(run_store, "create_run", unexpected_create_run)
    response = client.post(
        "/api/runs",
        json={
            "case": {
                "scenario_title": "Synthetic direct-run case",
                "case_summary": "A fictional case that must not bypass accepted intake.",
            }
        },
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "unlinked case payloads are disabled" in detail
    assert "accept the pre-MDT intake" in detail
    assert "immutable patient case version" in detail



def test_single_agent_assessment_rejects_unknown_profile() -> None:
    response = client.post(
        "/api/agents/XX-99/assess",
        json={
            "round_number": 1,
            "case": {
                "scenario_title": "Synthetic test case",
                "case_summary": "A fictional case for API endpoint testing only.",
            },
        },
    )
    assert response.status_code == 404


def test_single_agent_assessment_rejects_identifying_case_fields() -> None:
    response = client.post(
        "/api/agents/RO-01/assess",
        json={
            "round_number": 1,
            "case": {
                "scenario_title": "Synthetic test case",
                "case_summary": "A fictional case for API endpoint testing only.",
                "patient_name": "Must be rejected",
            },
        },
    )
    assert response.status_code == 422


def test_cors_allows_patient_delete_preflight_from_local_vite_origin() -> None:
    response = client.options(
        "/api/patients/test-patient-id",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    allowed_methods = response.headers["access-control-allow-methods"]
    assert "DELETE" in allowed_methods


def test_pre_mdt_intake_screen_endpoint_returns_questions_and_preserves_case():
    case = {
        "scenario_title": "Synthetic intake endpoint case",
        "case_summary": "Fictional case summary for intake endpoint testing.",
        "relevant_comorbidities": [],
        "prior_treatment": [],
    }
    response = client.post("/api/cases/screen-intake", json={"case": case})
    assert response.status_code == 200
    body = response.json()
    assert body["case_snapshot"] == SyntheticCase.model_validate(case).model_dump(exclude_none=True)
    assert body["ready_to_accept_with_gaps"] is True
    assert any(item["field_id"] == "relevant_comorbidities" for item in body["gaps"])
    assert body["questions"]


def test_pre_mdt_intake_screen_endpoint_records_declined_domain_as_gap():
    case = {
        "scenario_title": "Synthetic intake endpoint case",
        "case_summary": "Fictional case summary for intake endpoint testing.",
    }
    response = client.post(
        "/api/cases/screen-intake",
        json={"case": case, "declined_domains": ["patient_preferences"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert {"domain": "patient_preferences", "field_id": "patient_goals", "status": "DECLINED"} in body["gaps"]
    assert "patient_preferences" not in {item["domain"] for item in body["questions"]}


def test_pre_mdt_intake_screen_endpoint_rejects_unknown_declined_domain():
    response = client.post(
        "/api/cases/screen-intake",
        json={
            "case": {
                "scenario_title": "Synthetic intake endpoint case",
                "case_summary": "Fictional case summary for intake endpoint testing.",
            },
            "declined_domains": ["unknown_domain"],
        },
    )
    assert response.status_code == 422


def test_persisted_intake_api_records_answer_and_explicit_acceptance(monkeypatch, tmp_path):
    from app.services import run_store

    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "intake-api.sqlite3")
    created = client.post(
        "/api/intakes",
        json={
            "case": {
                "scenario_title": "Synthetic persisted intake API case",
                "case_summary": "Fictional case used to exercise the intake API.",
            }
        },
    )
    assert created.status_code == 200
    session = created.json()
    session_id = session["session_id"]
    assert session["state"] == "SCREENING"
    assert session["event_count"] >= 1

    answer = client.post(
        f"/api/intakes/{session_id}/events",
        json={
            "event_type": "ANSWER",
            "field_id": "age_years",
            "value": 63,
            "source_text": "User supplied age 63.",
        },
    )
    assert answer.status_code == 200
    assert answer.json()["case"]["age_years"] == 63
    assert answer.json()["events"][-1]["event_type"] == "ANSWER"

    accepted = client.post(
        f"/api/intakes/{session_id}/accept",
        json={"confirmed": True},
    )
    assert accepted.status_code == 200
    assert accepted.json()["state"] == "ACCEPTED_WITH_GAPS"
    assert accepted.json()["screening"]["gaps"]

    rejected_change = client.post(
        f"/api/intakes/{session_id}/events",
        json={"event_type": "CORRECTION", "field_id": "age_years", "value": 64},
    )
    assert rejected_change.status_code == 422


def test_persisted_intake_api_requires_explicit_acceptance(monkeypatch, tmp_path):
    from app.services import run_store

    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "intake-api-accept.sqlite3")
    created = client.post(
        "/api/intakes",
        json={
            "case": {
                "scenario_title": "Synthetic intake acceptance case",
                "case_summary": "Fictional case used to verify explicit acceptance.",
            }
        },
    )
    session_id = created.json()["session_id"]
    response = client.post(
        f"/api/intakes/{session_id}/accept",
        json={"confirmed": False},
    )
    assert response.status_code == 409
