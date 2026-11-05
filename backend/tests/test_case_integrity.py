from app.schemas import SyntheticCase
from app.services.case_integrity import audit_unverified_case_claims, build_case_prompt_context, build_case_report_title, build_case_validation_warnings, build_source_case_facts


def _case(**overrides):
    values = {
        "scenario_title": "Synthetic glottic case",
        "case_summary": "dm\nshtn\nsmoker\n\n1x1 cm growth involving right vocal cord and anterior commissure",
        "age_years": 75,
        "primary_site": "ca glottis",
        "histology": "scc",
        "relevant_comorbidities": [],
        "prior_treatment": [],
        "patient_goals": [],
        "social_context": [],
        "resource_context": [],
    }
    values.update(overrides)
    return SyntheticCase(**values)


def test_empty_structured_fields_are_marked_not_reported_not_absent():
    context = build_case_prompt_context(_case())
    assert context["field_status"]["relevant_comorbidities"]["status"] == "not_reported"
    assert context["field_status"]["prior_treatment"]["status"] == "not_reported"
    assert any("confirmed absent or negative" in item for item in context["interpretation_rules"])


def test_source_case_facts_are_built_from_snapshot_not_model_generated_facts():
    facts = build_source_case_facts(_case())
    joined = " ".join(facts)
    assert "dm" in joined and "shtn" in joined
    assert "Age (years): 75" in joined
    assert "T1N0" not in joined
    assert "male" not in joined.casefold()


def test_validation_warns_when_free_text_and_structured_fields_conflict():
    joined = " ".join(build_case_validation_warnings(_case())).casefold()
    assert "diabetes/dm" in joined
    assert "hypertension/htn" in joined
    assert "not confirmed negatives" in joined
    assert "clinical t stage is not supplied" in joined


def test_unverified_stage_and_sex_claims_are_flagged_but_qualified_mentions_are_not():
    case = _case()
    flags = audit_unverified_case_claims(case, {"provisional_conclusion": "This 75-year-old male has T1N0 glottic SCC."})
    joined = " ".join(flags).casefold()
    assert "t-stage" in joined and "n-stage" in joined and "sex/gender" in joined
    qualified = audit_unverified_case_claims(case, {"provisional_conclusion": "T1N0 is not confirmed and must not be assumed; sex is not reported."})
    assert qualified == []


def test_hypothetical_stage_examples_and_missing_prior_records_are_not_false_positive_claims():
    case = _case()
    payload = {
        "risk_flags": [
            "Assuming T1 or N0 from the limited description would be unsafe.",
            "For example, a hypothetical T1N0 case cannot be inferred.",
            "No prior treatment data or records are supplied for review.",
        ]
    }
    assert audit_unverified_case_claims(case, payload) == []


def test_unqualified_stage_and_prior_treatment_absence_claims_remain_flagged():
    case = _case()
    payload = {
        "provisional_conclusion": (
            "The tumour is T1N0. The patient has received no prior treatment."
        )
    }
    flags = " ".join(audit_unverified_case_claims(case, payload)).casefold()
    assert "t-stage" in flags
    assert "n-stage" in flags
    assert "prior-treatment" in flags


def test_report_title_never_adds_unprovided_stage():
    assert build_case_report_title(_case()) == "MDT Chair Synthesis: ca glottis — scc"


def test_sex_explicitly_reported_in_raw_case_text_is_not_flagged_as_invented():
    case = _case(case_summary="Synthetic case: 75-year-old man with a glottic lesion.")
    flags = audit_unverified_case_claims(
        case,
        {"provisional_conclusion": "This male patient requires further staging clarification."},
    )
    assert not any("sex/gender" in flag for flag in flags)
