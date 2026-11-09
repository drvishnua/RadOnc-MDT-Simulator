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


def test_lesion_measurement_does_not_establish_t_stage():
    context = build_case_prompt_context(_case())
    rules = " ".join(context["interpretation_rules"]).casefold()
    assert "lesion's size" in rules
    assert "never convert a 1x1 cm measurement into t1" in rules


def test_attributed_opinion_detector_requires_an_explicit_speaker_and_opinion_verb():
    from app.services.case_integrity import case_summary_has_attributed_opinions

    assert case_summary_has_attributed_opinions(
        "The surgeon recommends a surgery-led assessment, conditional on MRI."
    )
    assert case_summary_has_attributed_opinions(
        "According to the cardiologist, the preoperative sequence should be considered."
    )
    assert not case_summary_has_attributed_opinions(
        "dm\\nshtn\\nsmoker\\n1x1 cm growth involving right vocal cord."
    )


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



def test_uncertain_m_stage_reference_about_exclusion_is_not_flagged():
    case = _case()
    payload = {
        "risk_flags": [
            "The available record does not permit exclusion of M1 disease.",
            "M1 status remains unknown and cannot be assumed.",
        ]
    }
    assert audit_unverified_case_claims(case, payload) == []


def test_unqualified_m1_assertion_is_still_flagged():
    case = _case()
    flags = audit_unverified_case_claims(case, {"provisional_conclusion": "The patient has M1 disease."})
    assert any("M-stage" in item for item in flags)


def test_unreported_performance_status_is_flagged_but_question_or_source_record_is_not():
    case = _case()
    assert any("performance-status" in item for item in audit_unverified_case_claims(
        case, {"provisional_conclusion": "The patient has ECOG 0."}
    ))
    assert audit_unverified_case_claims(
        case, {"risk_flags": ["ECOG 0 is not documented and must not be assumed."]}
    ) == []
    source_case = _case(case_summary="Synthetic case; ECOG 1 documented in referral text.")
    assert not any("performance-status" in item for item in audit_unverified_case_claims(
        source_case, {"provisional_conclusion": "The recorded ECOG 1 is noted."}
    ))


def test_unreported_node_and_metastatic_negative_assertions_are_flagged():
    flags = " ".join(audit_unverified_case_claims(_case(), {
        "provisional_conclusion": "The patient is node-negative with no distant metastases."
    })).casefold()
    assert "node-negative" in flags
    assert "absence of metastatic disease" in flags
    assert audit_unverified_case_claims(_case(), {
        "risk_flags": ["Nodal status is unknown; M0 cannot be assumed."]
    }) == []


def test_resectability_assertion_is_flagged_but_conditional_assessment_is_not():
    case = _case()
    assert any("resectability status" in item for item in audit_unverified_case_claims(
        case, {"provisional_conclusion": "The tumour is resectable."}
    ))
    assert not any("resectability status" in item for item in audit_unverified_case_claims(
        case, {"risk_flags": ["Resectability requires formal review and cannot be assumed."]}
    ))


def test_definitive_treatment_safety_claims_are_flagged_but_conditional_risks_are_not():
    case = _case()
    flags = audit_unverified_case_claims(case, {
        "substantive_challenges": [
            "Initiating chemotherapy is contraindicated.",
            "Proceeding to surgery is unsafe.",
            "Neoadjuvant therapy is not indicated.",
        ]
    })
    assert any("treatment safety/indication" in item for item in flags)

    conditional = audit_unverified_case_claims(case, {
        "risk_flags": [
            "Starting treatment without staging may be unsafe.",
            "The case does not establish whether any option may be contraindicated.",
        ]
    })
    assert not any("treatment safety/indication" in item for item in conditional)


def test_unreported_histology_and_pathology_markers_are_flagged():
    case = _case(histology=None, pathology_summary=None)
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Biopsy confirms squamous cell carcinoma, p16 positive, grade 2."
    })).casefold()
    assert "histological diagnosis" in flags
    assert "pathology/biomarker finding" in flags


def test_unreported_investigation_results_are_flagged_but_requested_tests_are_not():
    case = _case(imaging_summary=None)
    assert any("imaging/investigation result" in item for item in audit_unverified_case_claims(
        case, {"provisional_conclusion": "MRI shows a suspicious cervical node."}
    ))
    assert not any("imaging/investigation result" in item for item in audit_unverified_case_claims(
        case, {"unknowns": ["MRI staging is required; no imaging result is supplied."]}
    ))


def test_undocumented_patient_preference_is_flagged_but_elicitation_is_not():
    case = _case(patient_goals=[])
    assert any("patient preference/decision" in item for item in audit_unverified_case_claims(
        case, {"provisional_conclusion": "The patient prefers surgery."}
    ))
    assert not any("patient preference/decision" in item for item in audit_unverified_case_claims(
        case, {"unknowns": ["The patient's preferences should be elicited."]}
    ))
    assert not any("patient preference/decision" in item for item in audit_unverified_case_claims(
        case, {"unknowns": ["Obtain explicit patient consent regarding potential treatment sequences."]}
    ))
    assert not any("patient preference/decision" in item for item in audit_unverified_case_claims(
        case, {"governance": ["Patient consent must be obtained before any real-world decision."]}
    ))


def test_clause_local_qualifier_does_not_hide_a_separate_unsupported_assertion():
    flags = audit_unverified_case_claims(_case(), {
        "provisional_conclusion": "M0 is not confirmed. The patient is node-negative."
    })
    assert any("node-negative" in item for item in flags)


def test_clinical_questions_are_not_treated_as_assertions():
    case = _case()
    assert audit_unverified_case_claims(case, {
        "unknowns": ["Is ECOG 0 documented?", "Could the tumour be T1N0?"]
    }) == []


def test_patient_preferences_wording_is_not_misread_as_a_patient_choice():
    case = _case(patient_goals=[])
    assert not any("patient preference/decision" in item for item in audit_unverified_case_claims(
        case, {"unknowns": ["The patient's preferences should be elicited."]}
    ))



def test_unreported_age_and_stage_group_assertions_are_flagged():
    case = _case(age_years=None, stage_group=None)
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "This 62-year-old patient has Stage IIIA disease."
    })).casefold()
    assert "assigns an age" in flags
    assert "assigns a stage group" in flags


def test_age_and_stage_group_in_source_summary_are_not_mislabelled_as_invented():
    case = _case(
        age_years=None,
        stage_group=None,
        case_summary="A 62-year-old patient with documented Stage IIIA disease.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The 62-year-old patient has Stage IIIA disease."
    })
    assert not any("assigns an age" in item for item in flags)
    assert not any("assigns a stage group" in item for item in flags)


def test_qualified_age_and_stage_group_uncertainty_is_not_flagged():
    case = _case(age_years=None, stage_group=None)
    flags = audit_unverified_case_claims(case, {
        "risk_flags": [
            "Age is not reported and must not be assumed.",
            "Stage IIIA is hypothetical and cannot be inferred.",
        ]
    })
    assert not any("assigns an age" in item for item in flags)
    assert not any("assigns a stage group" in item for item in flags)


def test_validation_warns_on_explicit_age_sex_and_stage_discrepancies():
    case = _case(
        age_years=75,
        sex_at_birth="male",
        clinical_t_stage="T2",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        stage_group="Stage II",
        case_summary="A 68-year-old woman with cT3N1M0 disease, Stage III.",
    )
    joined = " ".join(build_case_validation_warnings(case)).casefold()
    assert "structured age_years" in joined
    assert "sex_at_birth conflicts" in joined
    assert "t stage conflicts" in joined
    assert "n stage conflicts" in joined
    assert "stage_group conflicts" in joined



def test_age_assertion_uses_numeric_equivalence_across_wording():
    case = _case(age_years=None, case_summary="Referral summary: 68-year-old patient.")
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is aged 68 and needs further assessment."
    })
    assert not any("assigns an age" in item for item in flags)


def test_stage_group_uses_exact_roman_numeric_equivalence():
    case = _case(
        stage_group="Stage III",
        case_summary="Case summary: stage group 3 disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "stage_group conflicts" not in warnings


def test_stage_group_does_not_confuse_stage_ii_with_stage_iii():
    case = _case(
        stage_group="Stage II",
        case_summary="Case summary documents Stage III disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "stage_group conflicts" in warnings


def test_combined_ctnm_notation_is_parsed_for_each_component():
    case = _case(
        clinical_t_stage="T2",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        case_summary="Case summary records cT3N1M0 disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "t stage conflicts" in warnings
    assert "n stage conflicts" in warnings
    assert "m stage conflicts" not in warnings


def test_matching_combined_ctnm_notation_does_not_generate_discrepancy():
    case = _case(
        clinical_t_stage="T3",
        clinical_n_stage="N1",
        clinical_m_stage="M0",
        case_summary="Case summary records cT3N1M0 disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "t stage conflicts" not in warnings
    assert "n stage conflicts" not in warnings
    assert "m stage conflicts" not in warnings



def test_parent_stage_group_is_compatible_with_documented_substage():
    case = _case(
        stage_group="Stage III",
        case_summary="Case summary documents Stage IIIA disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "stage_group conflicts" not in warnings


def test_different_stage_group_substages_are_flagged():
    case = _case(
        stage_group="Stage IIIA",
        case_summary="Case summary documents Stage IIIB disease.",
    )
    warnings = " ".join(build_case_validation_warnings(case)).casefold()
    assert "stage_group conflicts" in warnings


def test_generated_parent_stage_is_supported_by_source_substage():
    case = _case(
        age_years=None,
        stage_group=None,
        case_summary="Documented Stage IIIA disease.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has Stage III disease."
    })
    assert not any("assigns a stage group" in item for item in flags)


def test_generated_substage_is_not_inferred_from_parent_stage():
    case = _case(
        age_years=None,
        stage_group=None,
        case_summary="Documented Stage III disease.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has Stage IIIA disease."
    })
    assert any("assigns a stage group" in item for item in flags)



def test_qualifier_for_one_claim_does_not_hide_a_later_claim_after_comma_or_contrast():
    case = _case()
    comma_example = audit_unverified_case_claims(case, {
        "provisional_conclusion": "M0 is not confirmed, but the patient is node-negative."
    })
    assert any("node-negative status" in item for item in comma_example)

    contrast_example = audit_unverified_case_claims(case, {
        "provisional_conclusion": "M1 cannot be assumed but there are no distant metastases."
    })
    assert any("absence of metastatic disease" in item for item in contrast_example)



def test_comma_separated_question_remains_a_question_not_an_assertion():
    flags = audit_unverified_case_claims(_case(), {
        "risk_flags": ["Could this be T1, or should the team obtain further staging?"]
    })
    assert flags == []



def test_missing_site_and_histology_title_uses_neutral_incomplete_label():
    case = _case(primary_site=None, histology=None)
    assert build_case_report_title(case) == "MDT Chair Synthesis: Case details not supplied"

def test_attribution_detector_does_not_mistake_imaging_narrative_for_a_named_speaker():
    from app.services.case_integrity import case_summary_has_attributed_opinions

    assert not case_summary_has_attributed_opinions(
        "CT scan demonstrates a lesion involving the right vocal cord."
    )
    assert not case_summary_has_attributed_opinions(
        "According to the scan, the lesion involves the right vocal cord."
    )
    assert not case_summary_has_attributed_opinions(
        "According to the radiology report, further review is required."
    )


def test_attribution_detector_recognises_explicit_named_speakers_conservatively():
    from app.services.case_integrity import case_summary_has_attributed_opinions

    assert case_summary_has_attributed_opinions(
        "Dr Arun Kumar recommends a specialist review."
    )
    assert case_summary_has_attributed_opinions(
        "According to Dr Arun Kumar, the opinion remains conditional."
    )


def test_attribution_detector_recognises_explicit_department_service_notes():
    from app.services.case_integrity import case_summary_has_attributed_opinions

    assert case_summary_has_attributed_opinions(
        "Neurology service note proposes a specialist assessment first."
    )
    assert case_summary_has_attributed_opinions(
        "Cardiology service note proposes a separate preoperative sequence."
    )

def test_generated_tnm_values_are_checked_against_supplied_structured_stages():
    case = _case(
        clinical_t_stage="T2",
        clinical_n_stage="N1",
        clinical_m_stage="M0",
        case_summary="Structured staging fields are recorded separately for this regression.",
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The case is cT1N0M0."
    })).casefold()

    assert "t-stage value" in flags and "t2" in flags
    assert "n-stage value" in flags and "n1" in flags
    assert "m-stage value" not in flags


def test_generated_tnm_components_may_be_repeated_only_when_present_in_source_summary():
    case = _case(
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        case_summary="Referral summary documents cT2N1M0 disease.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The referral records cT2N1M0."
    })
    assert not any("stage value" in item for item in flags)

    unsupported = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has cT3N0M1 disease."
    })).casefold()
    assert "t-stage value" in unsupported
    assert "n-stage value" in unsupported
    assert "m-stage value" in unsupported


def test_generated_stage_group_is_checked_against_structured_group_without_inventing_substage():
    case = _case(
        stage_group="Stage III",
        case_summary="Structured stage group supplied separately.",
    )
    unsupported = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has Stage IIIA disease."
    })
    assert any("conflict with structured stage_group" in item for item in unsupported)

    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has Stage III disease."
    })
    assert not any("stage group" in item for item in matching)


def test_patient_preference_audit_detects_conflict_with_structured_patient_goals():
    case = _case(patient_goals=["The patient prefers surgery."])
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient prefers surgery."
    })
    assert not any("patient preference/decision" in item for item in matching)

    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient prefers chemotherapy."
    })
    assert any("patient_goals" in item for item in conflicting)


def test_patient_preference_audit_accepts_preference_explicitly_recorded_in_case_summary():
    case = _case(
        patient_goals=[],
        case_summary="Referral text: the patient prefers surgery after discussion.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient prefers surgery after discussion."
    })
    assert not any("patient preference/decision" in item for item in flags)

def test_generated_sex_descriptor_is_checked_against_structured_sex():
    case = _case(sex_at_birth="female")
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The female patient requires further assessment."
    })
    assert not any("sex/gender" in item for item in matching)

    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The male patient requires further assessment."
    })
    assert any("conflict with structured sex_at_birth" in item for item in conflicting)


def test_generated_performance_status_is_checked_against_structured_score():
    case = _case(performance_status="ECOG 1")
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has ECOG 1."
    })
    assert not any("performance-status" in item for item in matching)

    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has ECOG 2."
    })
    assert any("conflict with structured performance_status" in item for item in conflicting)


def test_negative_n_and_m_claims_conflict_with_structured_positive_stages():
    case = _case(clinical_n_stage="N1", clinical_m_stage="M1")
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is node-negative with no distant metastases."
    })).casefold()
    assert "node-negative status" in flags
    assert "absence of metastatic disease" in flags


def test_comorbidity_and_prior_treatment_absence_claims_are_checked_against_supplied_lists():
    case = _case(
        relevant_comorbidities=["Diabetes mellitus"],
        prior_treatment=["Prior radiotherapy"],
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has no comorbidities and has received no prior treatment."
    })).casefold()
    assert "comorbidities as absent" in flags
    assert "prior treatment as absent" in flags

