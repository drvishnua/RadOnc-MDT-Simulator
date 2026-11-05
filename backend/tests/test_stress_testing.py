import json

import pytest

from app.services.stress_testing import audit_case_outputs, load_stress_cases


def test_stress_case_library_loads_six_valid_synthetic_cases():
    cases = load_stress_cases()
    assert [item["case_id"] for item in cases] == [
        "MDT-002", "MDT-003", "MDT-004", "MDT-005", "MDT-006", "MDT-007"
    ]
    assert all(item["case"].scenario_title.startswith("Synthetic") for item in cases)
    assert all(item["case"].case_summary for item in cases)


def test_stress_case_loader_rejects_duplicate_ids_and_invalid_case_schema(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps({
        "schema_version": "1.0", "synthetic_only": True,
        "cases": [
            {"case_id": "MDT-001", "scenario_title": "Synthetic one", "case_summary": "Fictional case summary long enough."},
            {"case_id": "MDT-001", "scenario_title": "Synthetic two", "case_summary": "Another fictional case summary."}
        ]
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_stress_cases(path)


def test_case_audit_flags_unsupported_stage_for_incomplete_glottic_case():
    cases = {item["case_id"]: item for item in load_stress_cases()}
    case = cases["MDT-002"]["case"]
    rounds = {1: [{"agent_id": "RO-01", "status": "completed", "assessment": {
        "provisional_conclusion": "This is T1N0 glottic carcinoma."
    }}]}
    findings = audit_case_outputs("MDT-002", case, rounds, {"chair_conclusion": "No stage can be confirmed."})
    assert any(item["severity"] == "hard_fail" for item in findings)
