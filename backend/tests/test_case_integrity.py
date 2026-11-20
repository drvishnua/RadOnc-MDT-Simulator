import pytest

from app.schemas import InvestigationRecord, SyntheticCase
from app.services.case_integrity import (
    audit_unverified_case_claims,
    build_case_prompt_context,
    build_case_report_title,
    build_case_validation_warnings,
    build_source_case_facts,
    is_empty_challenge_placeholder,
    redact_flagged_tnm_values,
)


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


def test_prompt_redaction_replaces_only_stage_components_named_by_the_audit_flag():
    flag = "Audit warning: unsupported R1 staging assertion cT1N0M0."
    original = (
        "R1 recorded cT1N0M0. Separate T1 N0 M0 tokens are also visible. "
        "A distinct T2 value is not part of this audit flag."
    )
    redacted = redact_flagged_tnm_values(original, [flag])
    assert redacted.count("[flagged unsupported staging assertion]") == 4
    assert "cT1N0M0" not in redacted
    assert "T1" not in redacted
    assert "N0" not in redacted
    assert "M0" not in redacted
    assert "T2" in redacted
    assert original.count("cT1N0M0") == 1
    assert "T1" in original and "N0" in original and "M0" in original


def test_prompt_redaction_is_noop_without_a_matching_audit_flag():
    original = "The synthetic source mentions cT1N0M0 and T2."
    assert redact_flagged_tnm_values(original, []) == original
    assert redact_flagged_tnm_values(original, ["Unsupported T3 assertion."]) == original



def test_prompt_redaction_preserves_unflagged_components_in_a_combined_tnm_value():
    original = "The supplied case has cT2N0M1. The unsupported nodal component is not established."
    redacted = redact_flagged_tnm_values(
        original,
        ["Audit flag: unsupported N0 assertion in the R1 note."],
    )
    assert redacted == (
        "The supplied case has cT2[flagged unsupported staging assertion]M1. "
        "The unsupported nodal component is not established."
    )


def test_empty_structured_fields_are_marked_not_reported_not_absent():
    context = build_case_prompt_context(_case())
    assert context["field_status"]["relevant_comorbidities"]["status"] == "not_reported"
    assert context["field_status"]["prior_treatment"]["status"] == "not_reported"
    assert any("confirmed absent or negative" in item for item in context["interpretation_rules"])


def test_lesion_measurement_does_not_establish_t_stage():
    context = build_case_prompt_context(_case())
    rules = " ".join(context["interpretation_rules"]).casefold()
    assert "lesion's size" in rules
    assert "never infer a t category from lesion size" in rules
    assert "infer nodal/metastatic status from missing data" in rules


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


def test_explicitly_nonconfirmatory_n0_m0_mentions_are_not_positive_stage_assertions():
    case = _case(clinical_n_stage=None, clinical_m_stage=None)
    qualified = audit_unverified_case_claims(case, {
        "uncertainty_notes": [
            "Anatomical subsite does not confirm N0/M0.",
            "The available case data do not establish N0 or M0.",
        ]
    })
    assert not any("N-stage value" in item for item in qualified)
    assert not any("M-stage value" in item for item in qualified)

    positive = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical record documents N0. The clinical record documents M0."
    })
    assert any("N-stage value" in item for item in positive)
    assert any("M-stage value" in item for item in positive)


def test_generated_audit_metadata_is_not_reaudited_as_narrative():
    case = _case(clinical_n_stage=None, clinical_m_stage=None)
    flags = audit_unverified_case_claims(case, {
        "case_data_integrity_flags": [
            "Generated narrative contains N-stage value(s) N0, but clinical_n_stage is not supplied.",
            "Generated narrative contains M-stage value(s) M0, but clinical_m_stage is not supplied.",
        ],
        "source_reference_integrity_flags": [
            "Reference R2:MO-99 was not supplied."
        ],
    })
    assert flags == []


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
    assert "prior treatment as absent" in flags


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


def test_explicitly_rejected_tnm_inferences_are_not_flagged():
    case = _case()
    payload = {
        "risk_flags": [
            "A 1x1 cm lesion does not equate to T1 disease.",
            "T1 cannot be inferred from lesion size.",
            "N0 cannot be inferred from missing nodal information.",
            "Do not infer M0 from an unreported metastatic work-up.",
        ]
    }
    assert audit_unverified_case_claims(case, payload) == []


def test_broader_explicit_tnm_negation_and_hypothetical_forms_remain_unflagged():
    case = _case()
    payload = {
        "risk_flags": [
            "A 1x1 cm lesion does not automatically define T1 or N0/M0 status.",
            "A 1x1 cm mass does not constitute confirmed T1 staging.",
            "Lesion size is not equivalent to T1.",
            "Assess whether lesion size and subsite suggest T1a or T1b.",
            "The lesion may be T1a or T1b depending on subsite involvement, but this is not confirmed.",
            "Review guidelines for T1/T2 glottic SCC with missing nodal/metastatic status.",
        ]
    }
    assert audit_unverified_case_claims(case, payload) == []


def test_qualified_tnm_list_connectors_accept_normalised_whitespace():
    case = _case()
    flags = audit_unverified_case_claims(case, {
        "risk_flags": [
            "Do not infer T1   OR   N0   /   M0 from lesion size or missing staging investigations."
        ]
    })
    assert flags == []


def test_rejected_tnm_inference_does_not_hide_a_separate_asserted_tnm_group():
    case = _case()
    flags = " ".join(audit_unverified_case_claims(case, {
        "risk_flags": [
            "T1 cannot be inferred from lesion size and the case is cT2N1M0."
        ]
    })).casefold()

    assert "t-stage value(s) t2" in flags
    assert "n-stage value(s) n1" in flags
    assert "m-stage value(s) m0" in flags


def test_tnm_like_classification_remains_flagged_as_unsupported_staging():
    case = _case()
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The model labels the lesion T1-like."
    })).casefold()

    assert "t-stage value(s) t1" in flags


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


def test_tnm_references_are_qualified_when_guidelines_are_explicitly_conditional():
    case = _case()
    qualified_references = [
        "Review NCCN guidelines for T1/T2 glottic SCC once staging is confirmed.",
        "Review standard-of-care guidelines for cT1 glottic SCC once staging data is provided.",
        "Refer to standard of care for T1 glottic cancer pending full workup.",
        "A 1x1 cm lesion involving vocal cord does not automatically equal T1.",
        "The 1x1 cm growth cannot be converted to T1 without formal staging confirmation.",
    ]
    for wording in qualified_references:
        flags = audit_unverified_case_claims(case, {
            "discussion_options": [wording],
            "uncertainty_notes": [wording],
        })
        assert not any("t-stage" in item for item in flags), (wording, flags)

    # Positive control: the same unreported stage asserted as the patient's
    # actual staging remains a quality-gate failure.
    positive = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has cT1N0M0 glottic SCC."
    })
    joined = " ".join(positive).casefold()
    assert "t-stage value" in joined
    assert "n-stage value" in joined
    assert "m-stage value" in joined


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
            "The absence of data means suitability for either option is unknown; it does not imply one is contraindicated or that the other is indicated.",
        ]
    })
    assert not any("treatment safety/indication" in item for item in conditional)

    # Negation must not suppress a separate positive claim after a clause boundary.
    contrastive = audit_unverified_case_claims(case, {
        "risk_flags": [
            "The absence of data does not imply chemotherapy is contraindicated; however, surgery is contraindicated."
        ]
    })
    assert any("treatment safety/indication" in item for item in contrastive)


def test_missing_information_does_not_support_neither_or_no_option_indication_claims():
    case = _case(
        case_summary="Fictional case with incomplete staging; MRI and fitness are not reported.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        stage_group=None,
        performance_status=None,
    )
    flags = audit_unverified_case_claims(case, {
        "source_opinion_responses": [
            {
                "comparison": (
                    "Without established staging or fitness, neither option is indicated."
                )
            }
        ]
    })
    assert any("treatment safety/indication" in item for item in flags)

    exact_live_r3_phrase = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "All reviewed peers acknowledge that neither option is indicated without documented "
            "staging, imaging, fitness, or resectability data."
        )
    })
    assert any("treatment safety/indication" in item for item in exact_live_r3_phrase)

    no_option_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": "No treatment pathway is appropriate."
    })
    assert any("treatment safety/indication" in item for item in no_option_flags)

    uncertainty = audit_unverified_case_claims(case, {
        "source_opinion_responses": [
            {
                "comparison": (
                    "The available record does not establish whether either option is indicated; "
                    "appropriateness cannot be determined."
                )
            }
        ]
    })
    assert not any("treatment safety/indication" in item for item in uncertainty)


def test_attributed_peer_absence_of_indication_claim_is_not_a_negative_clinical_finding():
    case = _case(
        case_summary=(
            "Fictional incomplete case. The surgical note favours a surgery-led assessment first, "
            "conditional on complete local staging; the medical oncology note favours discussing "
            "a preoperative multimodality sequence, conditional on MRI staging and fitness assessment. "
            "Neither note supplies the missing investigations or establishes a final plan."
        ),
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        stage_group=None,
        performance_status=None,
    )
    for attributed_statement in (
        "Neither source claims a specific treatment sequence is indicated despite the missing prerequisites.",
        "Neither peer claims an option is indicated despite the absence of staging or fitness data.",
        "Neither peer claims that chemotherapy is contraindicated.",
    ):
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": attributed_statement
        })
        assert not any("treatment safety/indication" in item for item in flags)

    direct_negative_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "Neither option is indicated because the required investigations are missing."
        )
    })
    assert any("treatment safety/indication" in item for item in direct_negative_flags)

    r3_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "No pathway is indicated because the required investigations are missing."
        )
    })
    assert any("treatment safety/indication" in item for item in r3_flags)

    safe_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The supplied information does not establish whether either source option is indicated "
            "or appropriate; indication and suitability remain undetermined."
        )
    })
    assert not any("treatment safety/indication" in item for item in safe_flags)


def test_negated_peer_statement_about_contraindication_is_not_a_clinical_assertion():
    case = _case(
        case_summary="Fictional incomplete case; staging and fitness are not supplied.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        stage_group=None,
        performance_status=None,
    )
    saved_mo07_wording = (
        "No peer proposes a definitive treatment pathway as indicated, "
        "nor do any claim that an option is contraindicated based on missing data alone."
    )
    flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": saved_mo07_wording
    })
    assert not any("treatment safety/indication" in item for item in flags)


def test_negated_peer_statement_does_not_hide_a_separate_positive_contraindication_claim():
    case = _case(
        case_summary="Fictional incomplete case; staging and fitness are not supplied.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        stage_group=None,
        performance_status=None,
    )
    text = (
        "No peer proposes a definitive treatment pathway as indicated, "
        "nor do any claim that an option is contraindicated based on missing data alone; "
        "however, surgery is contraindicated."
    )
    flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": text
    })
    assert any("treatment safety/indication" in item for item in flags)


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


def test_supported_biopsy_histology_paraphrase_is_not_flagged_as_an_investigation_result():
    case = _case(
        histology="adenocarcinoma",
        pathology_summary=None,
        case_summary="Fictional case. Biopsy reports rectal adenocarcinoma.",
    )
    flags = audit_unverified_case_claims(case, {
        "perspective_summary": (
            "The biopsy confirms adenocarcinoma but staging fields are unreported."
        )
    })
    assert not any("imaging/investigation result" in item for item in flags)


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

def test_attribution_detector_recognises_specialty_notes_that_favour_distinct_options():
    from app.services.case_integrity import case_summary_has_attributed_opinions

    case_summary = (
        "Fictional educational scenario. The referral includes two provisional opinions: "
        "the colorectal surgical note favours proceeding to a surgical assessment first, "
        "conditional on complete local staging and resectability review; "
        "the medical oncology note favours discussing a preoperative multimodality sequence, "
        "conditional on MRI staging, metastatic work-up and fitness assessment. "
        "Neither note establishes a final plan."
    )
    assert case_summary_has_attributed_opinions(case_summary)
    assert case_summary_has_attributed_opinions(
        "The colorectal surgical note favors a surgical assessment first, conditional on staging."
    )
    assert case_summary_has_attributed_opinions(
        "The medical oncology note favours discussing a preoperative sequence."
    )
    assert not case_summary_has_attributed_opinions(
        "The colorectal imaging report shows a lesion; the medical record lists staging details."
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


def test_unreported_positive_comorbidity_claim_is_flagged():
    case = _case(
        case_summary="Synthetic case. Comorbidity history is not reported.",
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has diabetes mellitus."
    })
    assert any("relevant_comorbidities" in item for item in flags)


def test_matching_structured_positive_comorbidity_claim_is_supported():
    case = _case(relevant_comorbidities=["Diabetes mellitus"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has diabetes mellitus."
    })
    assert not any("relevant_comorbidities" in item for item in flags)


def test_unknown_comorbidity_state_blocks_positive_case_summary_fallback():
    statement = "The patient has diabetes mellitus."
    case = _case(
        case_summary="Synthetic case. " + statement,
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement
    })
    assert any("relevant_comorbidities" in item and "UNKNOWN" in item for item in flags)


def test_unreported_positive_prior_treatment_claim_is_flagged():
    case = _case(
        case_summary="Synthetic case. Prior treatment history is not reported.",
        prior_treatment=[],
        clinical_field_states={"prior_treatment": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient previously received radiotherapy."
    })
    assert any("prior_treatment" in item for item in flags)


def test_matching_structured_positive_prior_treatment_claim_is_supported():
    case = _case(prior_treatment=["Prior radiotherapy"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient previously received radiotherapy."
    })
    assert not any("prior_treatment" in item for item in flags)


def test_unreported_positive_family_history_claim_is_flagged():
    statement = "The patient's mother had breast cancer."
    case = _case(
        case_summary="Synthetic case. Family history is not reported.",
        family_history=[],
        clinical_field_states={"family_history": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement
    })
    assert any("family_history" in item for item in flags)


def test_unreported_positive_allergy_claim_is_flagged():
    case = _case(
        case_summary="Synthetic case. Allergy history is not reported.",
        known_allergies=[],
        clinical_field_states={"known_allergies": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has a penicillin allergy."
    })
    assert any("known_allergies" in item for item in flags)


def test_unreported_positive_current_medication_claim_is_flagged():
    case = _case(
        case_summary="Synthetic case. Current medications are not reported.",
        current_medications=[],
        clinical_field_states={"current_medications": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is currently taking metformin."
    })
    assert any("current_medications" in item for item in flags)


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
def test_negative_n_and_m_assertions_are_supported_by_structured_n0_m0():
    case = _case(clinical_n_stage="N0", clinical_m_stage="M0")
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is node-negative with no distant metastases."
    })
    assert not any("node-negative status" in item for item in flags)
    assert not any("absence of metastatic disease" in item for item in flags)


def test_negative_n_and_m_assertions_explicitly_present_in_case_summary_are_not_relabelled():
    case = _case(
        clinical_n_stage=None,
        clinical_m_stage=None,
        case_summary="Referral record documents node-negative status and no distant metastases.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The record states node-negative status and no distant metastases."
    })
    assert not any("node-negative status" in item for item in flags)
    assert not any("absence of metastatic disease" in item for item in flags)

def test_populated_histology_does_not_silently_accept_a_conflicting_generated_diagnosis():
    case = _case(histology="scc", pathology_summary="Biopsy: squamous cell carcinoma.")
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathology confirms squamous cell carcinoma."
    })
    assert not any("histological diagnosis" in item for item in matching)
    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathology confirms adenocarcinoma."
    })
    assert any("histological diagnosis" in item for item in conflicting)


def test_populated_pathology_summary_does_not_silently_accept_conflicting_biomarker_claims():
    case = _case(pathology_summary="p16 negative, grade 2.")
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is p16 negative, grade 2."
    })
    assert not any("pathology/biomarker" in item for item in matching)
    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is p16 positive, grade 2."
    })
    assert any("pathology/biomarker" in item for item in conflicting)


def test_populated_imaging_summary_does_not_silently_accept_a_conflicting_generated_result():
    case = _case(imaging_summary="MRI shows no suspicious cervical nodes.")
    matching = audit_unverified_case_claims(case, {
        "provisional_conclusion": "MRI shows no suspicious cervical nodes."
    })
    assert not any("imaging/investigation" in item for item in matching)
    conflicting = audit_unverified_case_claims(case, {
        "provisional_conclusion": "MRI demonstrates a suspicious cervical node."
    })
    assert any("imaging/investigation" in item for item in conflicting)


def test_positive_treatment_suitability_is_flagged_but_conditional_candidate_language_is_not():
    case = _case()
    assert any("treatment-suitability/eligibility" in item for item in audit_unverified_case_claims(
        case, {"provisional_conclusion": "The patient is a suitable candidate for surgery."}
    ))
    assert not any("treatment-suitability/eligibility" in item for item in audit_unverified_case_claims(
        case, {"risk_flags": ["The patient may be a candidate for surgery pending imaging and fitness review."]}
    ))


def test_structured_patient_goal_without_patient_prefix_supports_matching_preference_statement():
    case = _case(patient_goals=["prefers surgery"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient prefers surgery."
    })
    assert not any("patient preference/decision" in item for item in flags)

def test_conditional_suitability_language_does_not_hide_an_unrelated_unsupported_nodal_claim():
    case = _case()
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            "The patient may be a candidate for surgery and is node-negative."
        )
    })
    assert any("node-negative status" in item for item in flags)
    assert not any("treatment-suitability/eligibility" in item for item in flags)


def test_negated_prerequisite_classification_is_not_a_categorical_unmet_claim():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging and fitness are not supplied."],
    )
    safe_statements = [
        "The peer conclusions identify the missing prerequisites without converting them into unmet conditions.",
        "Do not convert missing prerequisites into unmet conditions.",
        "Missing prerequisites are not being treated as unmet.",
        "The record does not establish that the prerequisites are unmet.",
        "The staging prerequisites must not be converted into unmet conditions.",
        "The peer conclusions identify the missing prerequisites (complete local staging, MRI staging, metastatic work-up, fitness assessment) without providing negative findings.",
        "The prerequisites are unknown due to missing case data, rather than treating them as unmet or absent.",
        "The peer records preserve uncertainty rather than converting them into categorical claims of unmet or absent conditions.",
    ]
    for statement in safe_statements:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement
        })
        assert not any("prerequisite(s) as unmet/not met" in item for item in flags), statement




def test_explicit_denial_of_negative_prerequisite_status_is_not_flagged():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging and fitness are not supplied."],
    )
    explicitly_unknown = [
        "The prerequisite status is unknown, not unmet.",
        "Prerequisites are unknown rather than unmet.",
        "The prerequisite remains unknown instead of unfulfilled.",
        "The fitness prerequisite is not failed.",
        "The investigation status is not negative.",
        "The prerequisite status is unknown rather than met or unmet.",
    ]
    for statement in explicitly_unknown:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement,
        })
        assert not any("prerequisite(s) as unmet/not met" in item for item in flags), statement

    # These are actual negative-status assertions and must continue to block.
    unqualified = [
        "The prerequisites remain unmet.",
        "The prerequisites have not been met.",
        "The fitness prerequisite failed.",
    ]
    for statement in unqualified:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement,
        })
        assert any("prerequisite(s) as unmet/not met" in item for item in flags), statement





def test_unknown_rather_than_met_or_unmet_does_not_hide_a_separate_unmet_assertion():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging and fitness are not supplied."],
    )
    safe_only = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The prerequisite status is unknown rather than met or unmet."
        )
    })
    assert not any("prerequisite(s) as unmet/not met" in item for item in safe_only)

    # This is the safe contrast emitted by the live hosted model: "negative"
    # is explicitly rejected as a finding, not asserted as the status.
    live_model_wording = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The prerequisite status is unknown because results are not supplied, "
            "rather than absent or negative."
        )
    })
    assert not any(
        "prerequisite(s) as unmet/not met" in item for item in live_model_wording
    )

    # The exception must not suppress a separate categorical assertion.
    mixed_negative = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The prerequisite status is unknown because results are not supplied, "
            "rather than absent or negative; the fitness prerequisite remains unmet."
        )
    })
    assert any(
        "prerequisite(s) as unmet/not met" in item for item in mixed_negative
    )
    assert "prerequisite remains unmet" in " ".join(mixed_negative).casefold()

    mixed = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The prerequisite status is unknown rather than met or unmet; "
            "the fitness prerequisite remains unmet."
        )
    })
    joined = " ".join(mixed).casefold()
    assert "prerequisite remains unmet" in joined


def test_server_bound_peer_excerpt_is_not_a_role_authored_prerequisite_assertion():
    case = _case(
        case_summary="Fictional case; local staging is not supplied.",
        known_unknowns=["Local staging is not supplied."],
    )
    quoted_only = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The supplied case does not establish a pathway.",
        "source_opinion_reviews": [{
            "source_excerpt": "A source option is conditional on staging.",
            "evidence_excerpt": "The peer response calls the prerequisites unmet.",
            "model_reported_evidence_excerpt": "The peer response calls the prerequisites unmet.",
        }],
    })
    assert not any("prerequisite(s) as unmet/not met" in item for item in quoted_only)

    authored = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": "The prerequisites remain unmet.",
        "source_opinion_reviews": [{
            "evidence_excerpt": "The peer response calls the prerequisites unmet.",
        }],
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in authored)



def test_categorical_unmet_prerequisite_claims_remain_flagged():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging and fitness are not supplied."],
    )
    unsafe_statements = [
        "The prerequisites remain unmet.",
        "The prerequisites are unmet.",
        "The prerequisites have not been met.",
        "The fitness prerequisite failed.",
    ]
    for statement in unsafe_statements:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement
        })
        assert any("prerequisite(s) as unmet/not met" in item for item in flags), statement


def test_unrelated_uncertainty_does_not_hide_an_unmet_prerequisite_assertion():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging is not supplied."],
    )
    for statement in (
        "The imaging result is unknown and the fitness prerequisite remains unmet.",
        "The case summary is provisional and the fitness prerequisite remains unmet.",
    ):
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement
        })
        assert any("prerequisite(s) as unmet/not met" in item for item in flags), statement


def test_negated_prerequisite_wording_does_not_hide_a_separate_unmet_claim():
    case = _case(
        case_summary="Fictional case; prerequisite status has not been assessed.",
        known_unknowns=["Clinical staging and fitness are not supplied."],
    )
    flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The staging prerequisites must not be converted into unmet conditions; "
            "however, the fitness prerequisite remains unmet."
        )
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in flags)
    assert "prerequisite remains unmet" in " ".join(flags).casefold()
    assert "staging prerequisites must not be converted" not in " ".join(flags).casefold()

    contrastive_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The prerequisites are unknown due to missing case data, rather than treating them as unmet; "
            "however, the fitness prerequisite remains unmet."
        )
    })
    joined = " ".join(contrastive_flags).casefold()
    assert "prerequisite remains unmet" in joined
    assert "prerequisites are unknown" not in joined


def test_explicit_suitability_followed_by_pending_prerequisites_is_not_unconditional_eligibility():
    case = _case()
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            "The patient is a suitable candidate for surgery pending MRI and fitness review."
        )
    })
    assert not any("treatment-suitability/eligibility" in item for item in flags)



def test_attribution_note_register_assigns_exact_stable_ids_to_competing_favour_opinions():
    from app.services.case_integrity import extract_attributed_note_opinions

    summary = (
        "Fictional educational scenario. The referral includes two provisional opinions: "
        "the colorectal surgical note favours proceeding to a surgical assessment first, "
        "conditional on complete local staging and resectability review; "
        "the medical oncology note favours discussing a preoperative multimodality sequence, "
        "conditional on MRI staging, metastatic work-up and fitness assessment. "
        "Neither note supplies the missing investigations or establishes a final plan."
    )

    opinions = extract_attributed_note_opinions(summary)

    assert [item["source_id"] for item in opinions] == [
        "CASE:case_summary#1",
        "CASE:case_summary#2",
    ]
    assert opinions[0]["source_excerpt"] == (
        "the colorectal surgical note favours proceeding to a surgical assessment first, "
        "conditional on complete local staging and resectability review"
    )
    assert opinions[1]["source_excerpt"] == (
        "the medical oncology note favours discussing a preoperative multimodality sequence, "
        "conditional on MRI staging, metastatic work-up and fitness assessment."
    )
    assert all(item["source_excerpt"] in summary for item in opinions)


def test_attribution_note_register_extracts_service_note_opinion_spans_with_punctuation():
    from app.services.case_integrity import extract_attributed_note_opinions

    summary = (
        "Fictional case. ENT service note proposes a surgery-led assessment, conditional on complete staging. "
        "Cardiology service note proposes a separate preoperative sequence, conditional on MRI review."
    )

    opinions = extract_attributed_note_opinions(summary)

    assert opinions == [
        {
            "source_id": "CASE:case_summary#1",
            "source_excerpt": "ENT service note proposes a surgery-led assessment, conditional on complete staging.",
        },
        {
            "source_id": "CASE:case_summary#2",
            "source_excerpt": "Cardiology service note proposes a separate preoperative sequence, conditional on MRI review.",
        },
    ]


def test_case_integrity_normalises_whitespace_runs_before_regex_audits():
    from app.services.case_integrity import _collapse_horizontal_whitespace

    horizontal = "Age" + (" " * 5000) + ":" + (" " * 3000) + "76"
    multiline = horizontal + "\nECOG" + (" " * 6000) + "performance" + (" " * 4000) + "status: 2"
    normalised = _collapse_horizontal_whitespace(multiline)
    assert normalised == "Age : 76\nECOG performance status: 2"
    assert normalised.count("\n") == 1

    case = _case(age_years=75, performance_status=None)
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": multiline,
    })).casefold()
    assert "age(s)" in flags
    assert "performance-status score" in flags




def test_conditionality_cannot_be_described_as_unmet_when_prerequisite_status_is_unknown():
    case = _case(
        case_summary="Fictional case; MRI and staging assessments are not supplied.",
        known_unknowns=["MRI and staging assessments are not supplied."],
    )
    unsafe = [
        "The conditionality remains unmet by the supplied record.",
        "The conditional option remains unmet pending MRI and staging.",
    ]
    for statement in unsafe:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement,
        })
        assert any("prerequisite(s) as unmet/not met" in item for item in flags), statement

    safe = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The option remains conditional while MRI and staging status are unknown."
        ),
    })
    assert not any("prerequisite(s) as unmet/not met" in item for item in safe)



def test_not_a_conclusion_that_prerequisites_are_unfulfilled_is_not_a_finding():
    case = _case(
        case_summary="Fictional case; local staging and fitness assessment are not supplied.",
        known_unknowns=["Local staging and fitness assessment are not supplied."],
    )
    safe = (
        "This is a representation omission in that peer record, not a conclusion "
        "that the clinical prerequisites are fulfilled or unfulfilled."
    )
    safe_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": safe,
    })
    assert not any("prerequisite(s) as unmet/not met" in item for item in safe_flags)

    unsafe_flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": (
            "The clinical prerequisites are unfulfilled because the assessments are not supplied."
        ),
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in unsafe_flags)


def test_neither_prerequisite_is_met_is_flagged_but_qualified_uncertainty_is_not():
    case = _case(
        case_summary="Fictional record; prerequisite assessments are not supplied.",
        known_unknowns=["The relevant prerequisite assessments are not supplied."],
    )
    unsafe = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": "Neither prerequisite is met in the record."
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in unsafe)

    safe_statements = [
        "The record does not establish that neither prerequisite is met.",
        "It remains unclear whether neither of the two prerequisites is met.",
    ]
    for statement in safe_statements:
        flags = audit_unverified_case_claims(case, {
            "response_to_other_perspectives": statement
        })
        assert not any("prerequisite(s) as unmet/not met" in item for item in flags), statement


def test_source_labelled_none_prefix_with_explanation_is_still_an_empty_challenge():
    placeholder = (
        "[Sources: CASE:case_summary#2; R2:RO-01] None; the peer explicitly "
        "acknowledges that indication cannot be determined due to missing prerequisite data."
    )
    assert is_empty_challenge_placeholder(placeholder)
    assert not is_empty_challenge_placeholder(
        "[Sources: CASE:case_summary#2; R2:RO-01] None of the supplied records "
        "establishes a whole-MDT consensus."
    )



def test_negated_peer_report_of_met_or_failed_status_is_not_flagged():
    case = _case(
        case_summary="Fictional record; prerequisite assessments are not supplied.",
        known_unknowns=["The relevant prerequisite assessments are not supplied."],
    )
    statement = (
        "Since neither source asserts that prerequisites are met or failed "
        "(only that they are not supplied)."
    )
    flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": statement
    })
    assert not any("prerequisite(s) as unmet/not met" in item for item in flags)

    direct_assertion = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": "The prerequisites are met or failed."
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in direct_assertion)


def test_negated_peer_report_exception_does_not_hide_a_separate_clause_assertion():
    case = _case(
        case_summary="Fictional record; prerequisite assessments are not supplied.",
        known_unknowns=["The relevant prerequisite assessments are not supplied."],
    )
    statement = (
        "Neither source asserts that prerequisites are met or failed; "
        "the fitness prerequisite remains unmet."
    )
    flags = audit_unverified_case_claims(case, {
        "response_to_other_perspectives": statement
    })
    assert any("prerequisite(s) as unmet/not met" in item for item in flags)

def _case_field_label(field: str) -> str:
    return {
        "current_medications": "Current medications",
        "known_allergies": "Known allergies",
        "relevant_investigations": "Relevant investigations",
        "relevant_comorbidities": "Relevant comorbidities",
        "prior_treatment": "Prior treatment",
        "patient_goals": "Patient goals",
        "social_context": "Social context",
        "resource_context": "Resource context",
        "known_unknowns": "Known unknowns",
    }[field]


def test_every_structured_list_field_has_explicit_status_and_source_fact_provenance():
    fields = {
        "current_medications": ["Medication A"],
        "known_allergies": ["Allergy B"],
        "relevant_investigations": ["Investigation C"],
        "relevant_comorbidities": ["Comorbidity D"],
        "prior_treatment": ["Treatment E"],
        "patient_goals": ["Goal F"],
        "social_context": ["Context G"],
        "resource_context": ["Resource H"],
        "known_unknowns": ["Unknown I"],
    }
    case = _case(**fields)

    context = build_case_prompt_context(case)
    facts = build_source_case_facts(case)
    joined_facts = " ".join(facts)

    for field, values in fields.items():
        assert context["field_status"][field]["status"] == "reported"
        assert context["field_status"][field]["value"] == values
        assert f"{_case_field_label(field)}: {values[0]}" in joined_facts


def test_every_empty_structured_list_field_is_explicitly_not_reported():
    case = _case(
        current_medications=[],
        known_allergies=[],
        relevant_investigations=[],
        relevant_comorbidities=[],
        prior_treatment=[],
        patient_goals=[],
        social_context=[],
        resource_context=[],
        known_unknowns=[],
    )
    context = build_case_prompt_context(case)
    for field in (
        "current_medications",
        "known_allergies",
        "relevant_investigations",
        "relevant_comorbidities",
        "prior_treatment",
        "patient_goals",
        "social_context",
        "resource_context",
        "known_unknowns",
    ):
        assert context["field_status"][field]["status"] == "not_reported"
        assert context["field_status"][field]["value"] is None


def test_every_scalar_case_field_has_explicit_provided_status_and_verbatim_value():
    fields = {
        "age_years": 62,
        "sex_at_birth": "female",
        "primary_site": "left breast",
        "histology": "invasive ductal carcinoma",
        "clinical_t_stage": "cT2",
        "clinical_n_stage": "cN1",
        "clinical_m_stage": "cM0",
        "stage_group": "IIB",
        "performance_status": "ECOG 1",
        "pathology_summary": "Synthetic pathology text, verbatim.",
        "imaging_summary": "Synthetic imaging text, verbatim.",
    }
    case = _case(**fields)
    context = build_case_prompt_context(case)

    for field, value in fields.items():
        assert context["field_status"][field]["status"] == "provided"
        assert context["field_status"][field]["value"] == value

    assert context["field_status"]["case_summary"] == {
        "label": "User-provided free-text case summary",
        "status": "provided_verbatim_unparsed",
        "value": case.case_summary,
    }
    assert context["case_snapshot"]["case_summary"] == case.case_summary


def test_every_missing_scalar_case_field_is_explicitly_not_reported():
    fields = {
        "age_years": None,
        "sex_at_birth": None,
        "primary_site": None,
        "histology": None,
        "clinical_t_stage": None,
        "clinical_n_stage": None,
        "clinical_m_stage": None,
        "stage_group": None,
        "performance_status": None,
        "pathology_summary": None,
        "imaging_summary": None,
    }
    context = build_case_prompt_context(_case(**fields))

    for field in fields:
        assert context["field_status"][field]["status"] == "not_reported"
        assert context["field_status"][field]["value"] is None

def test_all_empty_structured_list_fields_are_reported_as_not_reported_in_validation_warnings():
    case = _case(
        current_medications=[],
        known_allergies=[],
        relevant_investigations=[],
        relevant_comorbidities=[],
        prior_treatment=[],
        patient_goals=[],
        social_context=[],
        resource_context=[],
        known_unknowns=[],
    )

    warnings = " ".join(build_case_validation_warnings(case)).casefold()

    for field in (
        "current_medications",
        "known_allergies",
        "relevant_investigations",
        "relevant_comorbidities",
        "prior_treatment",
        "patient_goals",
        "social_context",
        "resource_context",
        "known_unknowns",
    ):
        assert field in warnings
    assert "not confirmed negatives" in warnings



def test_opposing_source_laterality_is_flagged_and_carried_without_resolution():
    summary = (
        "Fictional educational case. Source A records left laterality for the primary lesion. "
        "Source B records right laterality for the primary lesion."
    )
    case = _case(case_summary=summary)

    warnings = build_case_validation_warnings(case)
    context = build_case_prompt_context(case)
    generated_flags = audit_unverified_case_claims(
        case,
        {"provisional_conclusion": "The laterality remains unresolved pending source verification."},
    )

    conflict_warning = next(
        item for item in warnings if "opposing laterality statements" in item
    )
    assert conflict_warning in context["source_integrity_warnings"]
    assert conflict_warning in generated_flags
    assert context["case_snapshot"]["case_summary"] == summary
    assert case.case_summary == summary
    assert "No source is selected" in conflict_warning


def test_opposite_laterality_is_flagged_but_matching_or_unattributed_values_are_not():
    opposite = _case(
        case_summary=(
            "Fictional case. Source A records left laterality. "
            "Source B records right laterality."
        )
    )
    assert any(
        "opposing laterality statements" in item
        for item in build_case_validation_warnings(opposite)
    )

    matching = _case(
        case_summary=(
            "Fictional case. Source A records left laterality. "
            "Source B records left laterality."
        )
    )
    assert not any(
        "opposing laterality statements" in item
        for item in build_case_validation_warnings(matching)
    )

    unattributed = _case(
        case_summary="Fictional case. Left and right are hypothetical alternatives."
    )
    assert not any(
        "opposing laterality statements" in item
        for item in build_case_validation_warnings(unattributed)
    )



def test_pathological_tnm_in_case_summary_does_not_support_clinical_tnm_claims():
    case = _case(
        case_summary="Synthetic case; pathology reports pT1N0M0.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage is T1N0M0."
    })).casefold()
    assert "t-stage value(s) t1" in flags
    assert "n-stage value(s) n0" in flags
    assert "m-stage value(s) m0" in flags


def test_structured_pathological_stage_cannot_support_clinical_stage_claim():
    case = _case(
        clinical_t_stage=None,
        pathological_t_stage="pT1",
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The tumour is T1."
    })).casefold()
    assert "t-stage value(s) t1" in flags


def test_structured_clinical_stage_cannot_support_pathological_stage_claim():
    case = _case(
        clinical_t_stage="T1",
        pathological_t_stage=None,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathological tumour category is pT1."
    })).casefold()
    assert "unsupported pathological t-stage value(s)" in flags


def test_prefix_on_combined_pathological_tnm_applies_to_all_components():
    case = _case(
        case_summary="Synthetic case; pathological staging documented as pT2N1M0.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Clinical staging is T2N1M0."
    })).casefold()
    assert "t-stage value(s) t2" in flags
    assert "n-stage value(s) n1" in flags
    assert "m-stage value(s) m0" in flags


def test_conflicting_clinical_stage_field_cannot_become_supporting_evidence():
    case = _case(
        clinical_t_stage="T1",
        clinical_field_states={"clinical_t_stage": "CONFLICTING"},
        clinical_field_conflicts={
            "clinical_t_stage": [
                {
                    "raw_value": "T1",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "stage-note-a",
                        "source_excerpt": "Clinical T component recorded as T1.",
                    },
                },
                {
                    "raw_value": "T2",
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "stage-report-b",
                        "source_excerpt": "Clinical T component recorded as T2.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T stage is T1."
    })).casefold()
    assert "t-stage value(s) t1" in flags



def test_pathological_stage_group_cannot_support_clinical_stage_group_claim():
    case = _case(
        clinical_stage_group=None,
        pathological_stage_group="III",
        stage_group=None,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is III."
    })).casefold()
    assert "unsupported or type-conflicting stage group" in flags


def test_clinical_stage_group_cannot_support_pathological_stage_group_claim():
    case = _case(
        clinical_stage_group="IIA",
        pathological_stage_group=None,
        stage_group=None,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathological stage group is IIA."
    })).casefold()
    assert "unsupported or type-conflicting stage group" in flags


def test_typed_stage_group_supports_same_type_and_parent_stage_without_substage_inference():
    case = _case(
        clinical_stage_group="IIA",
        pathological_stage_group=None,
        stage_group=None,
    )
    parent = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is II."
    })
    exact = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is IIA."
    })
    unsupported_substage = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is IIB."
    })
    assert not any("stage group" in item.casefold() for item in parent)
    assert not any("stage group" in item.casefold() for item in exact)
    assert any("stage group" in item.casefold() for item in unsupported_substage)


def test_conflicting_stage_group_state_cannot_support_generated_stage_group():
    case = _case(
        clinical_stage_group="II",
        clinical_field_states={"clinical_stage_group": "CONFLICTING"},
        clinical_field_conflicts={
            "clinical_stage_group": [
                {
                    "raw_value": "II",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "stage-a",
                        "source_excerpt": "Clinical stage group II.",
                    },
                },
                {
                    "raw_value": "III",
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "stage-b",
                        "source_excerpt": "Clinical stage group III.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is II."
    })).casefold()
    assert "unsupported or type-conflicting stage group" in flags



def test_conflicting_age_value_cannot_support_generated_age_claim():
    case = _case(
        age_years=70,
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts={
            "age_years": [
                {
                    "raw_value": 70,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "age-note-a",
                        "source_excerpt": "Age recorded as 70 years.",
                    },
                },
                {
                    "raw_value": 72,
                    "provenance": {
                        "source_type": "PATIENT_REPORT",
                        "source_reference": "age-report-b",
                        "source_excerpt": "Patient reports age as 72 years.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is 70 years old."
    })).casefold()
    assert "conflicting source values" in flags


def test_conflicting_sex_at_birth_cannot_support_generated_sex_descriptor():
    case = _case(
        sex_at_birth="male",
        clinical_field_states={"sex_at_birth": "CONFLICTING"},
        clinical_field_conflicts={
            "sex_at_birth": [
                {
                    "raw_value": "male",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "sex-note-a",
                        "source_excerpt": "Sex at birth recorded as male.",
                    },
                },
                {
                    "raw_value": "female",
                    "provenance": {
                        "source_type": "MEDICAL_RECORD",
                        "source_reference": "sex-record-b",
                        "source_excerpt": "Sex at birth recorded as female.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient is male."
    })).casefold()
    assert "conflicting source values" in flags


def test_conflicting_performance_status_or_scale_cannot_support_generated_score():
    case = _case(
        performance_status="1",
        performance_status_scale="ECOG",
        clinical_field_states={
            "performance_status": "CONFLICTING",
            "performance_status_scale": "CONFLICTING",
        },
        clinical_field_conflicts={
            "performance_status": [
                {
                    "raw_value": "1",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "ps-note-a",
                        "source_excerpt": "ECOG performance status 1.",
                    },
                },
                {
                    "raw_value": "2",
                    "provenance": {
                        "source_type": "MEDICAL_RECORD",
                        "source_reference": "ps-record-b",
                        "source_excerpt": "ECOG performance status 2.",
                    },
                },
            ],
            "performance_status_scale": [
                {
                    "raw_value": "ECOG",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "ps-scale-a",
                        "source_excerpt": "Performance scale: ECOG.",
                    },
                },
                {
                    "raw_value": "WHO",
                    "provenance": {
                        "source_type": "MEDICAL_RECORD",
                        "source_reference": "ps-scale-b",
                        "source_excerpt": "Performance scale: WHO.",
                    },
                },
            ],
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Performance status is ECOG 1."
    })).casefold()
    assert "conflicting source values" in flags


def test_performance_status_score_without_a_named_scale_is_not_accepted_as_verified():
    case = _case(performance_status="1", performance_status_scale=None)
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Performance status is ECOG 1."
    })).casefold()
    assert "scale is absent" in flags


def test_conflicting_histology_cannot_support_generated_histology_claim():
    case = _case(
        histology="scc",
        clinical_field_states={"histology": "CONFLICTING"},
        clinical_field_conflicts={
            "histology": [
                {
                    "raw_value": "scc",
                    "provenance": {
                        "source_type": "PATHOLOGY_REPORT",
                        "source_reference": "path-a",
                        "source_excerpt": "Squamous cell carcinoma.",
                    },
                },
                {
                    "raw_value": "adenocarcinoma",
                    "provenance": {
                        "source_type": "PATHOLOGY_REPORT",
                        "source_reference": "path-b",
                        "source_excerpt": "Adenocarcinoma.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Histology is squamous cell carcinoma."
    })).casefold()
    assert "not supported" in flags


def test_conflicting_comorbidity_list_cannot_support_negative_comorbidity_claim():
    case = _case(
        relevant_comorbidities=["diabetes"],
        clinical_field_states={"relevant_comorbidities": "CONFLICTING"},
        clinical_field_conflicts={
            "relevant_comorbidities": [
                {
                    "raw_value": ["diabetes"],
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "comorbidity-a",
                        "source_excerpt": "Diabetes recorded.",
                    },
                },
                {
                    "raw_value": [],
                    "provenance": {
                        "source_type": "PATIENT_REPORT",
                        "source_reference": "comorbidity-b",
                        "source_excerpt": "Patient reports no known comorbidities.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has no known comorbidities."
    })).casefold()
    assert "absence is not explicitly supported" in flags


def test_confirmed_absent_comorbidity_requires_and_uses_explicit_provenance():
    case = _case(
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "CONFIRMED_ABSENT"},
        clinical_field_provenance={
            "relevant_comorbidities": [{
                "source_type": "CLINICIAN_NOTE",
                "source_reference": "comorbidity-confirmation",
                "source_excerpt": "No known comorbidities.",
            }]
        },
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has no known comorbidities."
    })
    assert not any("absence is not explicitly supported" in item for item in flags)


def test_unknown_comorbidity_state_does_not_use_flat_or_empty_list_as_negative_evidence():
    case = _case(
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "UNKNOWN"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has no known comorbidities."
    })).casefold()
    assert "absence is not explicitly supported" in flags


def test_conflicting_prior_treatment_list_cannot_support_no_prior_treatment_claim():
    case = _case(
        prior_treatment=["radiotherapy"],
        clinical_field_states={"prior_treatment": "CONFLICTING"},
        clinical_field_conflicts={
            "prior_treatment": [
                {
                    "raw_value": ["radiotherapy"],
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "treatment-a",
                        "source_excerpt": "Prior radiotherapy recorded.",
                    },
                },
                {
                    "raw_value": [],
                    "provenance": {
                        "source_type": "PATIENT_REPORT",
                        "source_reference": "treatment-b",
                        "source_excerpt": "Patient reports no prior treatment.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has received no prior treatment."
    })).casefold()
    assert "absence is not explicitly supported" in flags



def test_conflicting_stage_group_state_cannot_be_supported_by_the_matching_free_text_summary():
    case = _case(
        case_summary="Referral summary records clinical stage group II.",
        clinical_stage_group="II",
        clinical_field_states={"clinical_stage_group": "CONFLICTING"},
        clinical_field_conflicts={
            "clinical_stage_group": [
                {
                    "raw_value": "II",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "stage-note-a",
                        "source_excerpt": "Clinical stage group II.",
                    },
                },
                {
                    "raw_value": "III",
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "stage-note-b",
                        "source_excerpt": "Clinical stage group III.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is II."
    })).casefold()
    assert "unsupported or type-conflicting stage group" in flags

def test_invalid_structured_tnm_value_is_not_presented_as_a_conflict():
    case = _case(
        clinical_t_stage="T1",
        clinical_field_states={"clinical_t_stage": "INVALID"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The supplied case establishes clinical T1 disease."
    })).casefold()

    assert "clinical_t_stage" in flags
    assert "invalid" in flags
    assert "cannot support" in flags
    assert "conflict with structured clinical_t_stage" not in flags

def test_invalid_case_summary_is_not_used_as_supporting_evidence():
    case = _case(
        case_summary=(
            "Synthetic case: cT1N0M0, 64-year-old male; "
            "no known comorbidities and no prior treatment."
        ),
        age_years=None,
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        sex_at_birth=None,
        relevant_comorbidities=[],
        prior_treatment=[],
        clinical_field_states={"case_summary": "INVALID"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            "The patient has cT1N0M0, is a 64-year-old male, "
            "has no known comorbidities and received no prior treatment."
        )
    })).casefold()

    assert "t-stage value" in flags
    assert "n-stage value" in flags
    assert "m-stage value" in flags
    assert "assigns an age" in flags
    assert "sex/gender descriptor" in flags
    assert "comorbidities as absent" in flags
    assert "prior treatment as absent" in flags


def test_invalid_case_summary_is_labelled_invalid_in_prompt_projection():
    case = _case(
        case_summary="Synthetic case summary retained for audit only.",
        clinical_field_states={"case_summary": "INVALID"},
    )

    context = build_case_prompt_context(case)

    assert context["field_status"]["case_summary"]["status"] == "invalid"
    assert context["field_status"]["case_summary"]["value"] == case.case_summary
    assert context["canonical_field_values"]["case_summary"]["state"] == "INVALID"
    assert context["canonical_field_values"]["case_summary"]["canonical_comparison_value"] is None


def test_conflicting_case_summary_is_not_exposed_as_a_selected_prompt_value():
    case = _case(
        case_summary="Synthetic case summary: right-sided primary.",
        clinical_field_states={"case_summary": "CONFLICTING"},
        clinical_field_conflicts={
            "case_summary": [
                {
                    "raw_value": "Synthetic case summary: right-sided primary.",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "summary-a",
                        "source_excerpt": "Primary is right-sided.",
                    },
                },
                {
                    "raw_value": "Synthetic case summary: left-sided primary.",
                    "provenance": {
                        "source_type": "MEDICAL_RECORD",
                        "source_reference": "summary-b",
                        "source_excerpt": "Primary is left-sided.",
                    },
                },
            ]
        },
    )

    context = build_case_prompt_context(case)

    assert "case_summary" in context["case_snapshot_redacted_conflicting_fields"]
    assert context["case_snapshot"]["case_summary"] is None
    assert context["field_status"]["case_summary"]["status"] == "conflicting"
    assert context["field_status"]["case_summary"]["value"] is None
    assert context["canonical_field_values"]["case_summary"]["raw_value"] is None
    assert len(context["canonical_field_values"]["case_summary"]["conflict_candidates"]) == 2

@pytest.mark.parametrize(
    ("field_id", "summary", "generated", "label"),
    [
        (
            "known_allergies",
            "No known allergies.",
            "The patient has no known allergies.",
            "allerg",
        ),
        (
            "current_medications",
            "No current medications.",
            "The patient is taking no current medications.",
            "medication",
        ),
        (
            "family_history",
            "No known family history of cancer.",
            "The patient has no known family history of cancer.",
            "family history",
        ),
    ],
)
def test_unknown_negativeable_list_state_does_not_use_summary_as_absence_evidence(
    field_id, summary, generated, label
):
    case = _case(
        case_summary=summary,
        **{field_id: []},
        clinical_field_states={field_id: "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated,
    })).casefold()

    assert label in flags
    assert "absence is not explicitly supported" in flags


@pytest.mark.parametrize(
    ("field_id", "positive_value", "summary", "generated", "label"),
    [
        (
            "known_allergies",
            "penicillin",
            "No known allergies.",
            "The patient has no known allergies.",
            "allerg",
        ),
        (
            "current_medications",
            "metformin",
            "No current medications.",
            "The patient is taking no current medications.",
            "medication",
        ),
        (
            "relevant_comorbidities",
            "diabetes",
            "No known comorbidities.",
            "The patient has no known comorbidities.",
            "comorbidit",
        ),
        (
            "prior_treatment",
            "radiotherapy",
            "No prior treatment.",
            "The patient has received no prior treatment.",
            "prior treatment",
        ),
        (
            "family_history",
            "maternal breast cancer",
            "No known family history of cancer.",
            "The patient has no known family history of cancer.",
            "family history",
        ),
    ],
)
def test_positive_negativeable_list_value_overrides_contradictory_summary_absence(
    field_id, positive_value, summary, generated, label
):
    case = _case(
        case_summary=summary,
        **{field_id: [positive_value]},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated,
    })).casefold()

    assert label in flags
    assert "absence is not explicitly supported" in flags

@pytest.mark.parametrize(
    ("field_id", "summary", "generated"),
    [
        (
            "patient_willingness",
            "Referral text: the patient agrees to surgery.",
            "The patient agrees to surgery.",
        ),
        (
            "patient_consent_status",
            "Referral text: the patient has consented to participate in this educational scenario.",
            "The patient has consented to participate in this educational scenario.",
        ),
    ],
)
def test_unknown_willingness_or_consent_state_cannot_use_case_summary(
    field_id, summary, generated
):
    case = _case(
        case_summary=summary,
        clinical_field_states={field_id: "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated,
    })).casefold()

    if field_id == "patient_consent_status":
        assert "educational-scenario consent status" in flags
    else:
        assert "patient preference/decision" in flags


def test_structured_patient_willingness_supports_matching_decision_statement():
    case = _case(patient_willingness="agrees to surgery")

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient agrees to surgery.",
    })

    assert not any("patient preference/decision" in item for item in flags)


def test_given_patient_consent_status_supports_matching_educational_scenario_consent():
    case = _case(patient_consent_status="GIVEN")

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has consented to participate in this educational scenario.",
    })

    assert not any("educational-scenario consent status" in item for item in flags)


def test_educational_consent_status_is_not_a_proxy_for_treatment_consent():
    case = _case(patient_consent_status="GIVEN")

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has consented to surgery.",
    })).casefold()

    assert "treatment-specific consent" in flags


def test_declined_patient_consent_status_does_not_support_consent_given_claim():
    case = _case(patient_consent_status="DECLINED")

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has consented to participate in this educational scenario.",
    })).casefold()

    assert "educational-scenario consent status" in flags


def test_declined_patient_consent_status_supports_matching_decline_statement():
    case = _case(patient_consent_status="DECLINED")

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient declined consent to participate in this educational scenario.",
    })

    assert not any("educational-scenario consent status" in item for item in flags)

def test_structured_laterality_flags_contradictory_generated_primary_side():
    case = _case(laterality="LEFT")

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary tumour is right-sided.",
    })).casefold()

    assert "laterality" in flags
    assert "left" in flags
    assert "right" in flags


def test_structured_laterality_supports_matching_generated_primary_side():
    case = _case(laterality="RIGHT")

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary tumour is right-sided.",
    })

    assert not any("laterality" in item.casefold() for item in flags)


def test_unknown_laterality_cannot_use_case_summary_as_selected_side():
    case = _case(
        laterality=None,
        case_summary="Fictional referral: the primary tumour is right-sided.",
        clinical_field_states={"laterality": "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary tumour is right-sided.",
    })).casefold()

    assert "laterality" in flags
    assert "unknown" in flags


def test_conflicting_laterality_cannot_support_either_single_primary_side():
    case = _case(
        laterality=None,
        clinical_field_states={"laterality": "CONFLICTING"},
        clinical_field_conflicts={
            "laterality": [
                {
                    "raw_value": "LEFT",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "laterality-a",
                        "source_excerpt": "Primary laterality is left.",
                    },
                },
                {
                    "raw_value": "RIGHT",
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "laterality-b",
                        "source_excerpt": "Primary laterality is right.",
                    },
                },
            ]
        },
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary tumour is left-sided.",
    })).casefold()

    assert "laterality" in flags
    assert "conflicting" in flags


def test_laterality_can_fall_back_to_case_summary_only_when_state_is_not_explicit():
    case = _case(
        laterality=None,
        case_summary="Fictional referral: the primary tumour is right-sided.",
    )

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary tumour is right-sided.",
    })

    assert not any("laterality" in item.casefold() for item in flags)

def test_structured_histological_grade_supports_matching_grade_claim():
    case = _case(
        histological_grade="G2",
        case_summary="Synthetic case; a separate structured histological grade is supplied.",
        pathology_summary=None,
    )

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is histological grade G2.",
    })

    assert not any("pathology/biomarker" in item for item in flags)


def test_structured_histological_grade_overrides_conflicting_free_text_grade():
    case = _case(
        histological_grade="G2",
        case_summary="Synthetic referral describes histological grade G3.",
        pathology_summary=None,
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is histological grade G3.",
    })).casefold()

    assert "histological grade" in flags
    assert "g3" in flags


def test_unknown_histological_grade_cannot_use_case_summary_as_selected_grade():
    case = _case(
        histological_grade=None,
        case_summary="Synthetic referral describes histological grade G2.",
        pathology_summary=None,
        clinical_field_states={"histological_grade": "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is histological grade G2.",
    })).casefold()

    assert "histological grade" in flags


def test_conflicting_histological_grade_cannot_select_matching_summary_grade():
    case = _case(
        histological_grade=None,
        case_summary="Synthetic referral describes histological grade G2.",
        pathology_summary=None,
        clinical_field_states={"histological_grade": "CONFLICTING"},
        clinical_field_conflicts={
            "histological_grade": [
                {
                    "raw_value": "G2",
                    "provenance": {
                        "source_type": "PATHOLOGY_REPORT",
                        "source_reference": "grade-a",
                        "source_excerpt": "Histological grade G2.",
                    },
                },
                {
                    "raw_value": "G3",
                    "provenance": {
                        "source_type": "PATHOLOGY_REPORT",
                        "source_reference": "grade-b",
                        "source_excerpt": "Histological grade G3.",
                    },
                },
            ]
        },
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The biopsy is histological grade G2.",
    })).casefold()

    assert "histological grade" in flags

def test_structured_primary_site_flags_contradictory_generated_site():
    case = _case(
        primary_site="lung",
        case_summary="Synthetic case narrative; the primary site is separately structured.",
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary site is breast.",
    })).casefold()

    assert "primary_site" in flags
    assert "lung" in flags
    assert "breast" in flags


def test_structured_primary_site_supports_matching_generated_site():
    case = _case(
        primary_site="lung",
        case_summary="Synthetic case narrative; the primary site is separately structured.",
    )

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary site is lung.",
    })

    assert not any("primary_site" in item for item in flags)


def test_unknown_primary_site_cannot_use_case_summary_as_selected_site():
    case = _case(
        primary_site=None,
        case_summary="Referral text: the primary site is breast.",
        clinical_field_states={"primary_site": "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary site is breast.",
    })).casefold()

    assert "primary_site" in flags
    assert "unknown" in flags


def test_conflicting_primary_site_cannot_select_matching_summary_site():
    case = _case(
        primary_site=None,
        case_summary="Referral text: the primary site is breast.",
        clinical_field_states={"primary_site": "CONFLICTING"},
        clinical_field_conflicts={
            "primary_site": [
                {
                    "raw_value": "lung",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "site-a",
                        "source_excerpt": "Primary site is lung.",
                    },
                },
                {
                    "raw_value": "breast",
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "site-b",
                        "source_excerpt": "Primary site is breast.",
                    },
                },
            ]
        },
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary site is breast.",
    })).casefold()

    assert "primary_site" in flags
    assert "conflicting" in flags


def test_primary_site_can_fall_back_to_summary_only_without_explicit_state():
    case = _case(
        primary_site=None,
        case_summary="Referral text: the primary site is glottis.",
    )

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The primary site is glottis.",
    })

    assert not any("primary_site" in item for item in flags)


@pytest.mark.parametrize(
    ("field_id", "case_values", "known_unknown", "generated_claim"),
    [
        (
            "primary_site",
            {"primary_site": "lung"},
            "The primary site has not been confirmed.",
            "The primary site is lung.",
        ),
        (
            "anatomical_subsite",
            {"anatomical_subsite": "upper lobe"},
            "The anatomical subsite has not been reported.",
            "The anatomical subsite is upper lobe.",
        ),
        (
            "laterality",
            {"laterality": "LEFT"},
            "Tumour laterality remains unknown.",
            "The primary tumour is left-sided.",
        ),
    ],
)
def test_known_unknown_for_anatomical_field_blocks_matching_structured_claim(
    field_id, case_values, known_unknown, generated_claim
):
    case = _case(
        case_summary="Referral narrative; anatomical detail is recorded in a separate structured field.",
        known_unknowns=[known_unknown],
        **case_values,
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated_claim,
    })).casefold()

    assert field_id in flags
    assert "known_unknowns" in flags
    assert "unresolved" in flags or "not been" in flags


def test_unknown_anatomical_subsite_cannot_use_case_summary_as_selected_subsite():
    case = _case(
        anatomical_subsite=None,
        case_summary="Referral text: the anatomical subsite is upper lobe.",
        clinical_field_states={"anatomical_subsite": "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The anatomical subsite is upper lobe.",
    })).casefold()

    assert "anatomical_subsite" in flags
    assert "unknown" in flags


def test_structured_anatomical_subsite_flags_contradictory_generated_subsite():
    case = _case(
        anatomical_subsite="upper lobe",
        case_summary="Synthetic case; the subsite is supplied separately.",
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The anatomical subsite is lower lobe.",
    })).casefold()

    assert "anatomical_subsite" in flags
    assert "upper lobe" in flags
    assert "lower lobe" in flags

def test_clinical_stage_group_is_not_presented_as_validated_without_site_system_edition():
    case = _case(
        primary_site=None,
        clinical_stage_group="IIA",
        staging_system=None,
        staging_edition=None,
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has clinical stage group IIA disease.",
    })).casefold()

    assert "staging context" in flags
    assert "primary site" in flags
    assert "staging system" in flags
    assert "staging edition" in flags


def test_explicit_unknown_staging_system_cannot_validate_clinical_stage_group():
    case = _case(
        primary_site="lung",
        clinical_stage_group="IIA",
        staging_system=None,
        staging_edition="8",
        clinical_field_states={"staging_system": "UNKNOWN"},
    )

    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has clinical stage group IIA disease.",
    })).casefold()

    assert "staging context" in flags
    assert "staging system" in flags
    assert "unknown" in flags


def test_clinical_stage_group_with_explicit_site_system_and_edition_has_context():
    case = _case(
        primary_site="lung",
        clinical_stage_group="IIA",
        staging_system="AJCC",
        staging_edition="8",
    )

    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has clinical stage group IIA disease.",
    })

    assert not any("staging context" in item.casefold() for item in flags)

def test_unreported_diagnosis_date_assertion_is_flagged():
    case = _case(
        diagnosis_date=None,
        case_summary="Synthetic case with no diagnosis date recorded.",
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The diagnosis date was 2024-02-11.",
    })
    assert any("diagnosis_date" in item for item in flags)


def test_generated_diagnosis_date_must_match_the_structured_value():
    case = _case(diagnosis_date="2024-02-10")
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The diagnosis date was 2024-02-11.",
    })
    assert any("diagnosis_date" in item for item in flags)


def test_matching_structured_diagnosis_date_is_not_flagged():
    case = _case(diagnosis_date="2024-02-10")
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The diagnosis date was 2024-02-10.",
    })
    assert not any("diagnosis_date" in item for item in flags)


def test_explicit_unknown_diagnosis_date_cannot_use_summary_fallback():
    case = _case(
        case_summary="Synthetic case. Diagnosis date: 2024-02-10.",
        diagnosis_date=None,
        clinical_field_states={"diagnosis_date": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The diagnosis date was 2024-02-10.",
    })
    assert any("diagnosis_date" in item and "UNKNOWN" in item for item in flags)


def test_unreported_family_caregiver_support_assertion_is_flagged():
    case = _case(
        case_summary="Synthetic case; family and caregiver arrangements are not recorded.",
        family_caregiver_context=[],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "A caregiver is available to support the patient.",
    })
    assert any("family_caregiver_context" in item for item in flags)


def test_unknown_family_caregiver_state_cannot_use_summary_fallback():
    statement = "A caregiver is available to support the patient."
    case = _case(
        case_summary="Synthetic case. " + statement,
        family_caregiver_context=[],
        clinical_field_states={"family_caregiver_context": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("family_caregiver_context" in item and "UNKNOWN" in item for item in flags)


def test_reported_family_caregiver_support_can_support_matching_claim():
    statement = "A caregiver is available to support the patient."
    case = _case(family_caregiver_context=[statement])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("family_caregiver_context" in item for item in flags)

@pytest.mark.parametrize("status", ["PENDING", "NOT_AVAILABLE", "DECLINED"])
def test_noncompleted_investigation_record_cannot_support_a_finding(status):
    statement = "CT chest shows a 9 mm pulmonary nodule."
    record = InvestigationRecord(
        investigation_name="CT chest",
        result_summary="A 9 mm pulmonary nodule is described.",
        status=status,
        source_excerpt=statement,
    )
    case = _case(
        investigation_records=[record],
        clinical_field_states={"investigation_records": "PRESENT"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("investigation_records" in item for item in flags)


def test_completed_investigation_record_can_support_its_matching_finding():
    statement = "CT chest shows a 9 mm pulmonary nodule."
    record = InvestigationRecord(
        investigation_name="CT chest",
        result_summary="A 9 mm pulmonary nodule is described.",
        status="COMPLETED",
        source_excerpt=statement,
    )
    case = _case(
        investigation_records=[record],
        clinical_field_states={"investigation_records": "PRESENT"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("investigation_records" in item for item in flags)


def test_unknown_investigation_records_state_cannot_support_a_finding():
    statement = "CT chest shows a 9 mm pulmonary nodule."
    case = _case(
        case_summary="Synthetic case. " + statement,
        investigation_records=[],
        clinical_field_states={"investigation_records": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("investigation_records" in item and "UNKNOWN" in item for item in flags)

def test_unknown_pathological_tnm_fields_cannot_use_matching_case_summary_fallback():
    case = _case(
        case_summary="Synthetic pathology report records pT2N1M0.",
        pathological_t_stage=None,
        pathological_n_stage=None,
        pathological_m_stage=None,
        clinical_field_states={
            "pathological_t_stage": "UNKNOWN",
            "pathological_n_stage": "UNKNOWN",
            "pathological_m_stage": "UNKNOWN",
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "Pathological staging is pT2N1M0.",
    })).casefold()
    assert "pathological_t_stage" in flags
    assert "pathological_n_stage" in flags
    assert "pathological_m_stage" in flags


def test_unknown_pathological_stage_group_cannot_use_matching_case_summary_fallback():
    case = _case(
        case_summary="Synthetic pathology report records pathological stage group III.",
        stage_group=None,
        clinical_stage_group=None,
        pathological_stage_group=None,
        clinical_field_states={"pathological_stage_group": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathological stage group is III.",
    })
    assert any("unsupported or type-conflicting stage group" in item for item in flags)


def test_unknown_staging_edition_blocks_clinical_stage_group_context():
    case = _case(
        primary_site="lung",
        clinical_stage_group="IIA",
        staging_system="AJCC",
        staging_edition=None,
        clinical_field_states={"staging_edition": "UNKNOWN"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has clinical stage group IIA disease.",
    })).casefold()
    assert "staging context" in flags
    assert "staging edition" in flags
    assert "unknown" in flags

def test_unknown_social_context_cannot_support_generated_living_arrangement():
    statement = "The patient lives with a spouse."
    case = _case(
        case_summary="Referral text: " + statement,
        social_context=[],
        clinical_field_states={"social_context": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("social_context" in item for item in flags)


def test_structured_social_context_supports_matching_living_arrangement():
    case = _case(social_context=["Lives with a spouse"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient lives with a spouse.",
    })
    assert not any("social_context" in item for item in flags)


def test_social_context_may_use_summary_fallback_only_without_explicit_state():
    statement = "The patient lives with a spouse."
    case = _case(case_summary="Referral text: " + statement)
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("social_context" in item for item in flags)


def test_unknown_resource_context_cannot_support_generated_financial_constraint():
    statement = "The patient has financial constraints."
    case = _case(
        case_summary="Referral text: " + statement,
        resource_context=[],
        clinical_field_states={"resource_context": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("resource_context" in item for item in flags)


def test_structured_resource_context_supports_matching_financial_constraint():
    case = _case(resource_context=["Financial constraints"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has financial constraints.",
    })
    assert not any("resource_context" in item for item in flags)


def test_resource_context_may_use_summary_fallback_only_without_explicit_state():
    statement = "The patient has financial constraints."
    case = _case(case_summary="Referral text: " + statement)
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("resource_context" in item for item in flags)

def test_present_social_context_does_not_support_a_different_living_arrangement():
    case = _case(social_context=["Lives with a daughter"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient lives with a spouse.",
    })
    assert any("social_context" in item for item in flags)


def test_not_reported_social_context_cannot_fall_back_to_positive_summary_claim():
    statement = "The patient lives with a spouse."
    case = _case(
        case_summary="Referral text: " + statement,
        social_context=[],
        clinical_field_states={"social_context": "NOT_REPORTED"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("social_context" in item and "NOT_REPORTED" in item for item in flags)


def test_present_resource_context_does_not_support_a_different_constraint():
    case = _case(resource_context=["Financial constraints"])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has transport barriers.",
    })
    assert any("resource_context" in item for item in flags)


def test_not_reported_resource_context_cannot_fall_back_to_positive_summary_claim():
    statement = "The patient has financial constraints."
    case = _case(
        case_summary="Referral text: " + statement,
        resource_context=[],
        clinical_field_states={"resource_context": "NOT_REPORTED"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("resource_context" in item and "NOT_REPORTED" in item for item in flags)

def test_confirmed_absent_comorbidity_cannot_support_a_positive_summary_claim():
    statement = "The patient has diabetes mellitus."
    case = _case(
        case_summary="Referral text: " + statement,
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "CONFIRMED_ABSENT"},
        clinical_field_provenance={
            "relevant_comorbidities": [{
                "source_type": "CLINICIAN_NOTE",
                "source_reference": "comorbidity-absence",
                "source_excerpt": "No known comorbidities.",
            }]
        },
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any(
        "relevant_comorbidities" in item and "CONFIRMED_ABSENT" in item
        for item in flags
    )

def test_unknown_patient_willingness_blocks_direct_willingness_claim_in_case_summary():
    statement = "The patient is willing to undergo surgery."
    case = _case(
        case_summary="Referral text: " + statement,
        patient_willingness=None,
        clinical_field_states={"patient_willingness": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("patient_willingness" in item or "patient preference/decision" in item for item in flags)


def test_patient_goal_cannot_substitute_for_explicit_patient_willingness():
    statement = "The patient is willing to undergo surgery."
    case = _case(
        patient_goals=["is willing to undergo surgery"],
        patient_willingness=None,
        clinical_field_states={"patient_willingness": "UNKNOWN"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("patient_willingness" in item or "patient preference/decision" in item for item in flags)

def test_known_unknown_willingness_blocks_matching_case_summary_fallback():
    statement = "The patient is willing to undergo surgery."
    case = _case(
        case_summary="Referral text: " + statement,
        patient_willingness=None,
        known_unknowns=["Patient willingness has not been established."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("patient_willingness" in item for item in flags)


def test_known_unknown_treatment_consent_blocks_matching_case_summary_fallback():
    statement = "The patient has consented to surgery."
    case = _case(
        case_summary="Referral text: " + statement,
        known_unknowns=["Treatment-specific informed consent has not been documented."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("treatment-specific consent" in item for item in flags)


def test_unrelated_known_unknown_does_not_block_matching_treatment_consent_source():
    statement = "The patient has consented to surgery."
    case = _case(
        case_summary="Referral text: " + statement,
        known_unknowns=["The staging system and edition are not supplied."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("treatment-specific consent" in item for item in flags)

@pytest.mark.parametrize(
    ("status", "statement"),
    [
        (
            "NOT_ASKED",
            "The patient's consent to participate in this educational scenario has not been asked.",
        ),
        (
            "PENDING",
            "The patient's consent to participate in this educational scenario is pending.",
        ),
        (
            "WITHDRAWN",
            "The patient withdrew consent to participate in this educational scenario.",
        ),
    ],
)
def test_not_asked_pending_and_withdrawn_consent_statuses_support_only_matching_statements(
    status, statement
):
    case = _case(patient_consent_status=status)
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert not any("educational-scenario consent status" in item for item in flags)


@pytest.mark.parametrize(
    ("status", "statement"),
    [
        (
            "NOT_ASKED",
            "The patient has consented to participate in this educational scenario.",
        ),
        (
            "PENDING",
            "The patient has consented to participate in this educational scenario.",
        ),
        (
            "WITHDRAWN",
            "The patient has consented to participate in this educational scenario.",
        ),
    ],
)
def test_not_asked_pending_and_withdrawn_consent_do_not_support_consent_given(
    status, statement
):
    case = _case(patient_consent_status=status)
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })).casefold()
    assert "educational-scenario consent status" in flags

@pytest.mark.parametrize(
    ("field_id", "component", "source_token", "generated_token"),
    [
        ("pathological_t_stage", "T", "pT2", "pT3"),
        ("pathological_n_stage", "N", "pN1", "pN2"),
        ("pathological_m_stage", "M", "pM1", "pM0"),
    ],
)
@pytest.mark.parametrize(
    "state",
    ["UNKNOWN", "NOT_REPORTED", "NOT_ASSESSED", "PENDING", "DECLINED", "NOT_APPLICABLE"],
)
def test_each_nonpresent_pathological_tnm_state_blocks_matching_summary_and_names_state(
    field_id, component, source_token, generated_token, state
):
    case = _case(
        case_summary=f"Synthetic pathology text records {source_token}.",
        **{field_id: None},
        clinical_field_states={field_id: state},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The pathological {component} component is {source_token}."
        ),
    })).casefold()
    assert field_id in flags
    assert f"marked {state.casefold()}" in flags


@pytest.mark.parametrize(
    ("field_id", "component", "invalid_raw", "generated_token"),
    [
        ("pathological_t_stage", "T", "pT9", "pT2"),
        ("pathological_n_stage", "N", "pN4", "pN1"),
        ("pathological_m_stage", "M", "pM2", "pM1"),
    ],
)
def test_invalid_pathological_tnm_raw_value_is_preserved_but_never_supports_claim(
    field_id, component, invalid_raw, generated_token
):
    case = _case(
        **{field_id: invalid_raw},
        clinical_field_states={field_id: "INVALID"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The pathological {component} component is {generated_token}."
        ),
    })).casefold()
    assert field_id in flags
    assert "marked invalid" in flags
    assert getattr(case, field_id) == invalid_raw


@pytest.mark.parametrize(
    ("field_id", "component", "first_raw", "second_raw"),
    [
        ("pathological_t_stage", "T", "pT1", "pT2"),
        ("pathological_n_stage", "N", "pN0", "pN1"),
        ("pathological_m_stage", "M", "pM0", "pM1"),
    ],
)
def test_conflicting_pathological_tnm_values_remain_unselected_for_generated_claim(
    field_id, component, first_raw, second_raw
):
    case = _case(
        **{field_id: first_raw},
        clinical_field_states={field_id: "CONFLICTING"},
        clinical_field_conflicts={
            field_id: [
                {
                    "raw_value": first_raw,
                    "provenance": {
                        "source_type": "PATHOLOGY_REPORT",
                        "source_reference": f"{field_id}-report-a",
                        "source_excerpt": f"Pathology report A records {first_raw}.",
                    },
                },
                {
                    "raw_value": second_raw,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": f"{field_id}-note-b",
                        "source_excerpt": f"Clinician note B records {second_raw}.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The pathological {component} component is {first_raw}."
        ),
    })).casefold()
    assert field_id in flags
    assert "unresolved conflicting source values" in flags
    assert getattr(case, field_id) == first_raw


@pytest.mark.parametrize(
    ("field_id", "component", "supported_token", "unsupported_token"),
    [
        ("pathological_t_stage", "T", "pT2", "pT3"),
        ("pathological_n_stage", "N", "pN1", "pN2"),
        ("pathological_m_stage", "M", "pM1", "pM0"),
    ],
)
def test_present_pathological_tnm_supports_only_its_matching_structured_component(
    field_id, component, supported_token, unsupported_token
):
    case = _case(
        case_summary=f"Synthetic summary contains conflicting free text {unsupported_token}.",
        **{field_id: supported_token},
        clinical_field_states={field_id: "PRESENT"},
        clinical_field_provenance={
            field_id: [{
                "source_type": "PATHOLOGY_REPORT",
                "source_reference": f"{field_id}-structured-report",
                "source_excerpt": f"Pathology report records {supported_token}.",
            }]
        },
    )
    supported = audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The pathological {component} component is {supported_token}."
        ),
    })
    mismatched = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The pathological {component} component is {unsupported_token}."
        ),
    })).casefold()
    assert not any(field_id in item for item in supported)
    assert field_id in mismatched
    canonical_unsupported = f"p:{component}{unsupported_token[-1]}".casefold()
    assert canonical_unsupported in mismatched
    assert getattr(case, field_id) == supported_token

@pytest.mark.parametrize(
    ("state", "field_id", "component", "source_token", "generated_token"),
    [
        (state, field_id, component, source_token, generated_token)
        for state in (
            "UNKNOWN",
            "NOT_REPORTED",
            "NOT_ASSESSED",
            "PENDING",
            "DECLINED",
            "NOT_APPLICABLE",
        )
        for field_id, component, source_token, generated_token in (
            ("clinical_t_stage", "T", "cT2", "cT3"),
            ("clinical_n_stage", "N", "cN1", "cN2"),
            ("clinical_m_stage", "M", "cM0", "cM1"),
        )
    ],
)
def test_each_nonpresent_clinical_tnm_state_blocks_matching_summary_and_names_state(
    state, field_id, component, source_token, generated_token
):
    case = _case(
        case_summary=f"Synthetic clinical staging summary records {source_token}.",
        **{field_id: None},
        clinical_field_states={field_id: state},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The clinical {component} component is {source_token}."
        ),
    })).casefold()
    assert field_id in flags
    assert f"marked {state.casefold()}" in flags
    assert "case-summary fallback" in flags


@pytest.mark.parametrize(
    ("field_id", "component", "invalid_raw", "generated_token"),
    [
        ("clinical_t_stage", "T", "T9", "cT2"),
        ("clinical_n_stage", "N", "N4", "cN1"),
        ("clinical_m_stage", "M", "M2", "cM1"),
    ],
)
def test_invalid_clinical_tnm_raw_value_is_preserved_but_never_supports_claim(
    field_id, component, invalid_raw, generated_token
):
    case = _case(
        **{field_id: invalid_raw},
        clinical_field_states={field_id: "INVALID"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The clinical {component} component is {generated_token}."
        ),
    })).casefold()
    assert field_id in flags
    assert "marked invalid" in flags
    assert getattr(case, field_id) == invalid_raw


@pytest.mark.parametrize(
    ("field_id", "component", "first_raw", "second_raw"),
    [
        ("clinical_t_stage", "T", "T1", "T2"),
        ("clinical_n_stage", "N", "N0", "N1"),
        ("clinical_m_stage", "M", "M0", "M1"),
    ],
)
def test_conflicting_clinical_tnm_values_remain_unselected_for_generated_claim(
    field_id, component, first_raw, second_raw
):
    case = _case(
        **{field_id: first_raw},
        clinical_field_states={field_id: "CONFLICTING"},
        clinical_field_conflicts={
            field_id: [
                {
                    "raw_value": first_raw,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": f"{field_id}-clinical-source-a",
                        "source_excerpt": f"Clinical report A records {first_raw}.",
                    },
                },
                {
                    "raw_value": second_raw,
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": f"{field_id}-clinical-source-b",
                        "source_excerpt": f"Clinical report B records {second_raw}.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The clinical {component} component is {first_raw}."
        ),
    })).casefold()
    assert field_id in flags
    assert "unresolved conflicting source values" in flags
    assert getattr(case, field_id) == first_raw


@pytest.mark.parametrize(
    ("field_id", "component", "supported_token", "unsupported_token"),
    [
        ("clinical_t_stage", "T", "T2", "T3"),
        ("clinical_n_stage", "N", "N1", "N2"),
        ("clinical_m_stage", "M", "M0", "M1"),
    ],
)
def test_present_clinical_tnm_supports_only_its_matching_structured_component(
    field_id, component, supported_token, unsupported_token
):
    case = _case(
        case_summary=f"Synthetic summary contains conflicting free text c{unsupported_token}.",
        **{field_id: supported_token},
        clinical_field_states={field_id: "PRESENT"},
        clinical_field_provenance={
            field_id: [{
                "source_type": "CLINICIAN_NOTE",
                "source_reference": f"{field_id}-clinical-structured-source",
                "source_excerpt": f"Clinical record documents {supported_token}.",
            }]
        },
    )
    supported = audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The clinical {component} component is c{supported_token}."
        ),
    })
    mismatched = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": (
            f"The clinical {component} component is c{unsupported_token}."
        ),
    })).casefold()
    assert not any(field_id in item for item in supported)
    assert field_id in mismatched
    assert f"{component.casefold()}{unsupported_token[-1]}" in mismatched
    assert getattr(case, field_id) == supported_token

@pytest.mark.parametrize(
    ("state", "field_id", "summary_statement", "generated_statement"),
    [
        (state, field_id, summary_statement, generated_statement)
        for state in (
            "UNKNOWN",
            "NOT_REPORTED",
            "NOT_ASSESSED",
            "PENDING",
            "DECLINED",
            "NOT_APPLICABLE",
        )
        for field_id, summary_statement, generated_statement in (
            (
                "stage_group",
                "Synthetic case summary records stage group III.",
                "The stage group is III.",
            ),
            (
                "clinical_stage_group",
                "Synthetic case summary records clinical stage group III.",
                "The clinical stage group is III.",
            ),
            (
                "pathological_stage_group",
                "Synthetic pathology summary records pathological stage group III.",
                "The pathological stage group is III.",
            ),
        )
    ],
)
def test_each_nonpresent_typed_stage_group_state_blocks_summary_and_names_state(
    state, field_id, summary_statement, generated_statement
):
    case = _case(
        case_summary=summary_statement,
        **{field_id: None},
        clinical_field_states={field_id: state},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated_statement,
    })).casefold()
    assert field_id in flags
    assert f"marked {state.casefold()}" in flags
    assert "case-summary fallback" in flags


@pytest.mark.parametrize(
    ("field_id", "invalid_raw", "generated_statement"),
    [
        ("stage_group", "Stage V", "The stage group is III."),
        ("clinical_stage_group", "Stage V", "The clinical stage group is III."),
        ("pathological_stage_group", "Stage V", "The pathological stage group is III."),
    ],
)
def test_invalid_typed_stage_group_raw_value_is_preserved_but_not_used(
    field_id, invalid_raw, generated_statement
):
    case = _case(
        **{field_id: invalid_raw},
        clinical_field_states={field_id: "INVALID"},
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated_statement,
    })).casefold()
    assert field_id in flags
    assert "invalid" in flags
    assert getattr(case, field_id) == invalid_raw


@pytest.mark.parametrize(
    ("field_id", "generated_statement", "first_value", "second_value"),
    [
        (
            "stage_group",
            "The stage group is II.",
            "II",
            "III",
        ),
        (
            "clinical_stage_group",
            "The clinical stage group is II.",
            "II",
            "III",
        ),
        (
            "pathological_stage_group",
            "The pathological stage group is II.",
            "II",
            "III",
        ),
    ],
)
def test_conflicting_typed_stage_group_sources_remain_unselected(
    field_id, generated_statement, first_value, second_value
):
    kind = {
        "stage_group": "untyped",
        "clinical_stage_group": "clinical",
        "pathological_stage_group": "pathological",
    }[field_id]
    case = _case(
        **{field_id: first_value},
        clinical_field_states={field_id: "CONFLICTING"},
        clinical_field_conflicts={
            field_id: [
                {
                    "raw_value": first_value,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": f"{field_id}-source-a",
                        "source_excerpt": f"{kind} source A records stage group {first_value}.",
                    },
                },
                {
                    "raw_value": second_value,
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": f"{field_id}-source-b",
                        "source_excerpt": f"{kind} source B records stage group {second_value}.",
                    },
                },
            ]
        },
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": generated_statement,
    })).casefold()
    assert field_id in flags
    assert "conflicting source values" in flags
    assert getattr(case, field_id) == first_value


@pytest.mark.parametrize(
    ("field_id", "supported_statement", "mismatched_statement", "supported_value"),
    [
        (
            "stage_group",
            "The stage group is III.",
            "The stage group is II.",
            "III",
        ),
        (
            "clinical_stage_group",
            "The clinical stage group is III.",
            "The clinical stage group is II.",
            "III",
        ),
        (
            "pathological_stage_group",
            "The pathological stage group is III.",
            "The pathological stage group is II.",
            "III",
        ),
    ],
)
def test_present_typed_stage_group_supports_only_its_matching_value(
    field_id, supported_statement, mismatched_statement, supported_value
):
    case = _case(
        **{field_id: supported_value},
        clinical_field_states={field_id: "PRESENT"},
        clinical_field_provenance={
            field_id: [{
                "source_type": "CLINICIAN_NOTE",
                "source_reference": f"{field_id}-present-source",
                "source_excerpt": f"Source record documents {supported_value}.",
            }]
        },
    )
    supported = audit_unverified_case_claims(case, {
        "provisional_conclusion": supported_statement,
    })
    mismatched = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": mismatched_statement,
    })).casefold()
    assert not any("stage group" in item.casefold() for item in supported)
    assert "stage group" in mismatched
    assert field_id in mismatched
    assert getattr(case, field_id) == supported_value

def test_known_unknown_clinical_t_stage_blocks_matching_case_summary_claim():
    case = _case(
        case_summary="Synthetic source summary records clinical cT2 disease.",
        clinical_t_stage=None,
        known_unknowns=["Clinical T stage is not reported."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T component is cT2.",
    })
    assert any("clinical_t_stage" in item and "known_unknowns" in item for item in flags)


def test_known_unknown_pathological_n_stage_blocks_matching_case_summary_claim():
    case = _case(
        case_summary="Synthetic pathology summary records pN1 disease.",
        pathological_n_stage=None,
        known_unknowns=["Pathological N component remains unresolved."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The pathological N component is pN1.",
    })
    assert any("pathological_n_stage" in item and "known_unknowns" in item for item in flags)


def test_known_unknown_clinical_stage_group_blocks_matching_case_summary_claim():
    case = _case(
        case_summary="Synthetic referral records clinical stage group III.",
        clinical_stage_group=None,
        known_unknowns=["Clinical stage group has not been confirmed."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical stage group is III.",
    })
    assert any("clinical_stage_group" in item and "known_unknowns" in item for item in flags)


def test_known_unknown_staging_edition_blocks_structured_value_from_validating_group():
    case = _case(
        primary_site="lung",
        clinical_stage_group="IIIA",
        staging_system="AJCC",
        staging_edition="8",
        known_unknowns=["The staging edition has not been verified."],
    )
    flags = " ".join(audit_unverified_case_claims(case, {
        "provisional_conclusion": "The patient has clinical stage group IIIA disease.",
    })).casefold()
    assert "staging edition" in flags
    assert "known_unknowns" in flags


def test_known_unknown_comorbidity_history_blocks_matching_summary_positive_claim():
    statement = "The patient has diabetes mellitus."
    case = _case(
        case_summary="Referral summary: " + statement,
        relevant_comorbidities=[],
        known_unknowns=["Relevant comorbidity history is not reported."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("relevant_comorbidities" in item and "known_unknowns" in item for item in flags)


def test_unrelated_known_unknown_does_not_block_supported_clinical_t_stage():
    case = _case(
        case_summary="Synthetic source summary records clinical cT2 disease.",
        clinical_t_stage=None,
        known_unknowns=["Diagnosis date has not been reported."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T component is cT2.",
    })
    assert not any("clinical_t_stage" in item for item in flags)


def test_not_unknown_wording_does_not_mark_a_field_unresolved():
    case = _case(
        case_summary="Synthetic source summary records clinical cT2 disease.",
        clinical_t_stage=None,
        known_unknowns=["Clinical T stage is not unknown."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T component is cT2.",
    })
    assert not any("clinical_t_stage" in item for item in flags)


def test_known_unknown_mapping_is_clause_local():
    case = _case(
        case_summary="Synthetic source summary records clinical cT2 disease.",
        clinical_t_stage=None,
        known_unknowns=["Clinical T stage is documented, but diagnosis date is not reported."],
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T component is cT2.",
    })
    assert not any("clinical_t_stage" in item for item in flags)


def test_known_unknowns_list_maps_patient_willingness_to_its_matching_field():
    statement = "The patient is willing to undergo surgery."
    case = _case(
        case_summary="Referral text: " + statement,
        patient_willingness=None,
        known_unknowns=["Patient willingness has not been established."],
        clinical_field_states={"known_unknowns": "PRESENT"},
    )
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": statement,
    })
    assert any("patient_willingness" in item for item in flags)


def test_non_present_known_unknowns_state_is_not_used_as_gap_evidence_even_if_memory_is_corrupt():
    case = _case(
        case_summary="Synthetic source summary records clinical cT2 disease.",
        clinical_t_stage=None,
        known_unknowns=[],
        clinical_field_states={"known_unknowns": "UNKNOWN"},
    )
    # Simulate a corrupted/historical in-memory object that bypassed current
    # Pydantic validation. Audit logic must still refuse non-PRESENT list data.
    object.__setattr__(case, "known_unknowns", ["Clinical T stage is not reported."])
    flags = audit_unverified_case_claims(case, {
        "provisional_conclusion": "The clinical T component is cT2.",
    })
    assert not any("clinical_t_stage" in item for item in flags)


def test_non_empty_known_unknowns_list_cannot_be_marked_unknown():
    with pytest.raises(ValueError, match="cannot carry a supplied value while marked UNKNOWN"):
        _case(
            known_unknowns=["Clinical T stage is not reported."],
            clinical_field_states={"known_unknowns": "UNKNOWN"},
        )

