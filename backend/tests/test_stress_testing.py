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


def test_stress_cases_keep_case_specific_oracles_separate_from_case_facts():
    cases = {item["case_id"]: item for item in load_stress_cases()}
    assert "no_unsupported_tnm" in cases["MDT-002"]["oracle_checks"]
    assert "preserve_attributed_opinions" in cases["MDT-006"]["oracle_checks"]
    assert "no_fabricated_patient_preference" in cases["MDT-007"]["oracle_checks"]
    assert "oracle_checks" not in cases["MDT-002"]["case"].model_dump()



def test_case_audit_hard_fails_invalid_source_reference_flags():
    cases = {item["case_id"]: item for item in load_stress_cases()}
    case = cases["MDT-006"]["case"]
    rounds = {
        2: [{
            "agent_id": "RO-01",
            "status": "completed",
            "result": {
                "source_reference_integrity_flags": [
                    "R1:RO-99 was cited but was not supplied to this role."
                ]
            },
        }]
    }
    findings = audit_case_outputs("MDT-006", case, rounds, {})
    assert any(
        item["severity"] == "hard_fail"
        and item["source"] == "R2:RO-01"
        and "RO-99" in item["finding"]
        for item in findings
    )


def test_case_audit_does_not_silently_pass_unimplemented_oracles():
    cases = {item["case_id"]: item for item in load_stress_cases()}
    case = cases["MDT-006"]["case"]
    findings = audit_case_outputs(
        "MDT-006",
        case,
        {},
        {"consensus_status": "insufficient_information"},
        cases["MDT-006"]["oracle_checks"],
    )
    pending = [item for item in findings if item["source"] == "STRESS_ORACLE"]
    assert {item["finding"].rsplit(": ", 1)[-1].rstrip(".") for item in pending} == {
        "preserve_attributed_opinions",
        "no_false_consensus",
        "retain_conditions",
    }
    assert all(item["severity"] == "major" for item in pending)


def test_case_audit_ignores_source_reference_flags_on_failed_rows():
    cases = {item["case_id"]: item for item in load_stress_cases()}
    case = cases["MDT-006"]["case"]
    rounds = {
        3: [{
            "agent_id": "RO-01",
            "status": "failed",
            "result": {
                "source_reference_integrity_flags": ["stale output must not be audited"]
            },
        }]
    }
    findings = audit_case_outputs("MDT-006", case, rounds, {})
    assert not any("stale output" in item["finding"] for item in findings)
