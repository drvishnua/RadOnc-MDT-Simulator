"""Regression tests for the immutable canonical clinical field registry."""
from dataclasses import FrozenInstanceError

import pytest

from app.clinical_fields import (
    AGE,
    CLINICAL_FIELD_REGISTRY,
    CLINICAL_FIELD_REGISTRY_VERSION,
    CLINICAL_M_STAGE,
    CLINICAL_N_STAGE,
    CLINICAL_T_STAGE,
    SEX,
    SITE,
    STAGE,
    T,
    N,
    M,
    build_registry_prompt_payload,
    normalize_clinical_tnm_component,
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

    assert CLINICAL_FIELD_REGISTRY_VERSION == "1.0.0"
    assert (T, N, M, AGE, SEX, SITE, STAGE) == (
        "clinical_t_stage",
        "clinical_n_stage",
        "clinical_m_stage",
        "age_years",
        "sex_at_birth",
        "primary_site",
        "stage_group",
    )


def test_registry_covers_every_synthetic_case_field():
    assert set(CLINICAL_FIELD_REGISTRY) == set(SyntheticCase.model_fields)


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


def test_shared_case_context_includes_registry_and_canonical_tnm_but_preserves_raw_values():
    context = build_case_prompt_context(_case(clinical_t_stage="1", clinical_n_stage="N0"))

    assert context["clinical_field_registry_version"] == CLINICAL_FIELD_REGISTRY_VERSION
    assert context["clinical_field_registry"]["version"] == CLINICAL_FIELD_REGISTRY_VERSION
    assert context["canonical_field_values"][CLINICAL_T_STAGE]["raw_value"] == "1"
    assert context["canonical_field_values"][CLINICAL_T_STAGE]["canonical_comparison_value"] == "T1"
    assert context["canonical_field_values"][CLINICAL_N_STAGE]["canonical_comparison_value"] == "N0"
    assert any("clinical T component" in rule and "canonical comparison value" in rule for rule in context["interpretation_rules"])


def test_unknown_and_empty_lists_are_not_converted_to_negative_findings():
    context = build_case_prompt_context(_case())

    assert context["canonical_field_values"]["clinical_n_stage"]["status"] == "NOT_REPORTED"
    assert context["canonical_field_values"]["relevant_comorbidities"]["status"] == "NOT_REPORTED"
    assert context["canonical_field_values"]["relevant_comorbidities"]["raw_value"] == []
    assert "CONFIRMED_ABSENT" in context["clinical_field_registry"]["fields"][0]["allowed_states"]
    assert "not_reported means unknown/not supplied" in context["interpretation_rules"][0]


def test_pathological_stage_prefix_is_flagged_and_raw_source_is_preserved():
    context = build_case_prompt_context(_case(clinical_t_stage="pT1"))
    item = context["canonical_field_values"][CLINICAL_T_STAGE]

    assert item["raw_value"] == "pT1"
    assert item["canonical_comparison_value"] is None
    assert "Pathological staging" in item["normalization_warning"]
    assert context["tnm_normalization_warnings"]
