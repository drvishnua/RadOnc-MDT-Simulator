"""Regression tests for the immutable canonical clinical field registry."""
from dataclasses import FrozenInstanceError

import pytest

from app.clinical_fields import (
    AGE,
    CLINICAL_FIELD_REGISTRY,
    CLINICAL_FIELD_REGISTRY_VERSION,
    HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION,
    CLINICAL_FIELD_REGISTRY_V1,
    CLINICAL_M_STAGE,
    PATHOLOGICAL_T_STAGE,
    CLINICAL_N_STAGE,
    CLINICAL_T_STAGE,
    SEX,
    SITE,
    STAGE,
    T,
    N,
    M,
    build_registry_prompt_payload,
    clinical_field_registry_sha256,
    normalize_clinical_tnm_component,
    normalize_pathological_tnm_component,
)
from app.schemas import SyntheticCase
from app.services.case_integrity import build_case_prompt_context


def _case(**overrides):
    values = {
        "scenario_title": "Synthetic canonical registry test",
        "case_summary": "Fictional case. No additional clinical findings are supplied.",
    }
    values.update(overrides)
    return SyntheticCase(**values)


def test_registry_is_immutable_and_field_ids_are_stable():
    with pytest.raises(TypeError):
        CLINICAL_FIELD_REGISTRY["age_years"] = CLINICAL_FIELD_REGISTRY["age_years"]
    with pytest.raises(FrozenInstanceError):
        CLINICAL_FIELD_REGISTRY["age_years"].label = "Repurposed field"

    assert CLINICAL_FIELD_REGISTRY_VERSION == "2.0.0"
    assert HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION == "1.0.0"
    assert (T, N, M, AGE, SEX, SITE, STAGE) == (
        "clinical_t_stage",
        "clinical_n_stage",
        "clinical_m_stage",
        "age_years",
        "sex_at_birth",
        "primary_site",
        "stage_group",
    )


def test_registry_covers_every_synthetic_case_value_field():
    metadata_fields = {
        "clinical_field_states",
        "clinical_field_provenance",
        "clinical_field_conflicts",
    }
    assert set(CLINICAL_FIELD_REGISTRY) == set(SyntheticCase.model_fields) - metadata_fields


def test_v2_registry_is_additive_and_v1_definitions_remain_inspectable():
    assert set(CLINICAL_FIELD_REGISTRY_V1).issubset(CLINICAL_FIELD_REGISTRY)
    assert CLINICAL_FIELD_REGISTRY_V1[CLINICAL_T_STAGE].description == (
        "Clinical primary-tumour TNM component; staging system and edition must be supplied separately before interpretation."
    )
    assert "pathological_t_stage" not in CLINICAL_FIELD_REGISTRY_V1
    assert "pathological_t_stage" in CLINICAL_FIELD_REGISTRY
    with pytest.raises(TypeError):
        CLINICAL_FIELD_REGISTRY["new_field"] = CLINICAL_FIELD_REGISTRY[CLINICAL_T_STAGE]


def test_v1_historical_payload_and_v2_payload_are_distinct_and_hash_addressed():
    v1 = build_registry_prompt_payload(HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION)
    v2 = build_registry_prompt_payload()
    assert v1["version"] == "1.0.0"
    assert "sha256" not in v1
    assert v2["version"] == "2.0.0"
    assert v2["sha256"] == clinical_field_registry_sha256()
    assert v2["fields"] != v1["fields"]
    assert all("validation_rule" in field and "source_requirement" in field for field in v2["fields"])


def test_tnm_component_aliases_normalize_without_losing_clinical_semantics():
    assert normalize_clinical_tnm_component(CLINICAL_T_STAGE, "1") == "T1"
    assert normalize_clinical_tnm_component(CLINICAL_T_STAGE, "T1") == "T1"
    assert normalize_clinical_tnm_component(CLINICAL_T_STAGE, "cT1a") == "T1A"
    assert normalize_clinical_tnm_component(CLINICAL_N_STAGE, "N0") == "N0"
    assert normalize_clinical_tnm_component(CLINICAL_M_STAGE, "M0") == "M0"


def test_tnm_normalizer_rejects_pathological_or_wrong_component_values():
    with pytest.raises(ValueError, match="Pathological staging"):
        normalize_clinical_tnm_component(CLINICAL_T_STAGE, "pT1")
    with pytest.raises(ValueError, match="requires a N-component"):
        normalize_clinical_tnm_component(CLINICAL_N_STAGE, "T1")
    with pytest.raises(ValueError):
        normalize_clinical_tnm_component(CLINICAL_T_STAGE, "T1N0M0")


def test_shared_case_context_includes_registry_hash_and_canonical_tnm_but_preserves_raw_values():
    context = build_case_prompt_context(_case(clinical_t_stage="1", clinical_n_stage="N0"))

    assert context["clinical_field_registry_version"] == CLINICAL_FIELD_REGISTRY_VERSION
    assert context["clinical_field_registry"]["version"] == CLINICAL_FIELD_REGISTRY_VERSION
    assert context["clinical_field_registry_sha256"] == clinical_field_registry_sha256()
    assert context["canonical_field_values"][CLINICAL_T_STAGE]["raw_value"] == "1"
    assert context["canonical_field_values"][CLINICAL_T_STAGE]["canonical_comparison_value"] == "T1"
    assert context["canonical_field_values"][CLINICAL_N_STAGE]["canonical_comparison_value"] == "N0"
    assert context["canonical_field_values"][CLINICAL_T_STAGE]["provenance"][0]["verification_status"] == "user_supplied_not_independently_verified"
    assert any("T/N/M lexical normalization is not clinical staging validation" in rule for rule in context["interpretation_rules"])


def test_unknown_and_empty_lists_are_not_converted_to_negative_findings():
    context = build_case_prompt_context(_case())

    assert context["canonical_field_values"]["clinical_n_stage"]["state"] == "NOT_REPORTED"
    assert context["canonical_field_values"]["relevant_comorbidities"]["state"] == "NOT_REPORTED"
    assert context["canonical_field_values"]["relevant_comorbidities"]["raw_value"] == []
    comorbidity_definition = next(
        item for item in context["clinical_field_registry"]["fields"]
        if item["field_id"] == "relevant_comorbidities"
    )
    assert "CONFIRMED_ABSENT" in comorbidity_definition["allowed_states"]
    assert any("UNKNOWN, NOT_REPORTED, NOT_ASSESSED" in rule for rule in context["interpretation_rules"])


def test_pathological_stage_prefix_is_flagged_and_raw_source_is_preserved():
    context = build_case_prompt_context(_case(clinical_t_stage="pT1"))
    item = context["canonical_field_values"][CLINICAL_T_STAGE]

    assert item["raw_value"] == "pT1"
    assert item["canonical_comparison_value"] is None
    assert "Pathological staging" in item["normalization_warning"]
    assert context["tnm_normalization_warnings"]



def test_pathological_tnm_normalization_retains_pathological_namespace():
    assert normalize_pathological_tnm_component(PATHOLOGICAL_T_STAGE, "pT1") == "PT1"
    assert normalize_pathological_tnm_component(PATHOLOGICAL_T_STAGE, "ypT1a") == "YPT1A"
    with pytest.raises(ValueError, match="p or yp prefix"):
        normalize_pathological_tnm_component(PATHOLOGICAL_T_STAGE, "cT1")


@pytest.mark.parametrize(
    ("field_id", "value"),
    [
        (CLINICAL_T_STAGE, "T5"),
        (CLINICAL_N_STAGE, "N4"),
        (CLINICAL_M_STAGE, "M2"),
    ],
)
def test_tnm_normalizer_rejects_out_of_range_lexical_components(field_id, value):
    with pytest.raises(ValueError, match="Unrecognised"):
        normalize_clinical_tnm_component(field_id, value)


def test_v2_case_includes_additive_clinical_context_and_warns_when_staging_metadata_is_missing():
    case = _case(
        primary_site="lung",
        anatomical_subsite="upper lobe",
        laterality="RIGHT",
        histology="adenocarcinoma",
        histological_grade="G2",
        clinical_t_stage="T1",
        pathological_t_stage="pT1",
        performance_status="1",
        performance_status_scale="ECOG",
        family_history=["first-degree relative with cancer"],
        patient_willingness="not yet discussed",
    )
    context = build_case_prompt_context(case)
    fields = context["canonical_field_values"]
    assert fields["anatomical_subsite"]["raw_value"] == "upper lobe"
    assert fields["laterality"]["canonical_comparison_value"] == "RIGHT"
    assert fields["pathological_t_stage"]["canonical_comparison_value"] == "PT1"
    assert fields["clinical_t_stage"]["canonical_comparison_value"] == "T1"
    assert any("staging system" in warning and "staging edition" in warning for warning in context["staging_context_warnings"])


def test_field_states_distinguish_unknown_pending_declined_and_not_applicable():
    case = _case(
        clinical_n_stage=None,
        clinical_m_stage=None,
        patient_willingness=None,
        clinical_field_states={
            "clinical_n_stage": "UNKNOWN",
            "clinical_m_stage": "PENDING",
            "patient_goals": "DECLINED",
            "performance_status": "NOT_ASSESSED",
        },
    )
    values = build_case_prompt_context(case)["canonical_field_values"]
    assert values["clinical_n_stage"]["state"] == "UNKNOWN"
    assert values["clinical_m_stage"]["state"] == "PENDING"
    assert values["patient_goals"]["state"] == "DECLINED"
    assert values["performance_status"]["state"] == "NOT_ASSESSED"
    assert values["clinical_n_stage"]["canonical_comparison_value"] is None


def test_confirmed_absence_requires_explicit_source_provenance():
    with pytest.raises(ValueError, match="requires explicit source provenance"):
        _case(
            relevant_comorbidities=[],
            clinical_field_states={"relevant_comorbidities": "CONFIRMED_ABSENT"},
        )
    case = _case(
        relevant_comorbidities=[],
        clinical_field_states={"relevant_comorbidities": "CONFIRMED_ABSENT"},
        clinical_field_provenance={
            "relevant_comorbidities": [{
                "source_type": "CLINICIAN_NOTE",
                "source_reference": "synthetic-note-01",
                "source_excerpt": "No relevant comorbidities documented in this synthetic source.",
            }]
        },
    )
    value = build_case_prompt_context(case)["canonical_field_values"]["relevant_comorbidities"]
    assert value["state"] == "CONFIRMED_ABSENT"
    assert value["canonical_comparison_value"] is None
    assert value["provenance"][0]["source_reference"] == "synthetic-note-01"


def test_conflicting_field_values_are_preserved_without_selecting_a_value():
    case = _case(
        age_years=70,
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts={
            "age_years": [
                {
                    "raw_value": 70,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "note-a",
                        "source_excerpt": "Age recorded as 70 years.",
                    },
                },
                {
                    "raw_value": 72,
                    "provenance": {
                        "source_type": "PATIENT_REPORT",
                        "source_reference": "patient-report-b",
                        "source_excerpt": "Patient reports age as 72 years.",
                    },
                },
            ]
        },
    )
    value = build_case_prompt_context(case)["canonical_field_values"]["age_years"]
    assert value["state"] == "CONFLICTING"
    assert value["canonical_comparison_value"] is None
    assert [item["raw_value"] for item in value["conflict_candidates"]] == [70, 72]


def test_conflicting_state_without_two_distinct_source_values_is_rejected():
    with pytest.raises(ValueError, match="two source-specific conflict values"):
        _case(
            age_years=70,
            clinical_field_states={"age_years": "CONFLICTING"},
            clinical_field_conflicts={
                "age_years": [{
                    "raw_value": 70,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "note-a",
                        "source_excerpt": "Age recorded as 70 years.",
                    },
                }]
            },
        )


def test_source_excerpt_hash_must_match_preserved_text():
    with pytest.raises(ValueError, match="does not match"):
        _case(
            clinical_field_states={"relevant_comorbidities": "CONFIRMED_ABSENT"},
            clinical_field_provenance={
                "relevant_comorbidities": [{
                    "source_type": "CLINICIAN_NOTE",
                    "source_reference": "note-a",
                    "source_excerpt": "No comorbidities.",
                    "source_sha256": "0" * 64,
                }]
            },
        )
