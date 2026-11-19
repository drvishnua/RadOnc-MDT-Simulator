from app.schemas import SyntheticCase
from app.services.intake_screening import screen_case_intake


def make_case(**updates):
    values = {
        "scenario_title": "Synthetic intake case",
        "case_summary": "A fictional case summary supplied for educational screening.",
    }
    values.update(updates)
    return SyntheticCase(**values)


def test_screening_identifies_gaps_without_fabricating_values():
    case = make_case()
    result = screen_case_intake(case)
    assert result["ready_to_accept_with_gaps"] is True
    assert {gap["field_id"] for gap in result["gaps"]} >= {
        "age_years", "clinical_n_stage", "performance_status", "patient_goals"
    }
    assert result["case_snapshot"] == case.model_dump(exclude_none=True)
    assert all("normal" not in question["question"].lower() for question in result["questions"])


def test_explicit_decline_suppresses_question_but_retains_unknown_gap():
    case = make_case()
    result = screen_case_intake(case, declined_domains=["patient_preferences"])
    domain = next(item for item in result["domains"] if item["domain"] == "patient_preferences")
    assert domain["status"] == "DECLINED"
    assert domain["missing_fields"] == ["patient_goals"]
    assert "patient_preferences" not in {item["domain"] for item in result["questions"]}
    assert {"domain": "patient_preferences", "field_id": "patient_goals", "status": "DECLINED"} in result["gaps"]


def test_empty_lists_are_not_interpreted_as_confirmed_absence():
    result = screen_case_intake(make_case(relevant_comorbidities=[], prior_treatment=[]))
    assert any(gap["field_id"] == "relevant_comorbidities" for gap in result["gaps"])
    assert any(gap["field_id"] == "prior_treatment" for gap in result["gaps"])


def test_unknown_decline_domain_is_rejected():
    import pytest
    with pytest.raises(ValueError, match="Unknown declined"):
        screen_case_intake(make_case(), declined_domains=["stage_is_fine"])
