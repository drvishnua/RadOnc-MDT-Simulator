"""Regression tests for the immutable canonical clinical field registry."""
from dataclasses import FrozenInstanceError
import hashlib

import pytest
from pydantic import ValidationError

from app.clinical_fields import (
    AGE,
    CLINICAL_FIELD_REGISTRY,
    CLINICAL_FIELD_ALIASES,
    CLINICAL_FIELD_ALIASES_V1,
    CLINICAL_FIELD_REGISTRY_VERSION,
    HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION,
    CLINICAL_FIELD_REGISTRY_V1,
    CLINICAL_M_STAGE,
    PATHOLOGICAL_T_STAGE,
    PATHOLOGICAL_N_STAGE,
    PATHOLOGICAL_M_STAGE,
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
    normalize_stage_group_token,
)
from app.schemas import ClinicalFieldProvenance, SyntheticCase
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
    assert normalize_clinical_tnm_component(CLINICAL_T_STAGE, "ycT1a") == "YCT1A"
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


def test_clinical_list_values_preserve_original_whitespace():
    original = "  first-degree relative with cancer  "
    case = _case(
        family_history=[original],
        relevant_comorbidities=["  hypertension  "],
        known_unknowns=["  staging edition not reported  "],
    )

    assert case.family_history == [original]
    assert case.relevant_comorbidities == ["  hypertension  "]
    assert case.known_unknowns == ["  staging edition not reported  "]
    assert case.model_dump(mode="json")["family_history"] == [original]


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



def test_stage_group_normalizer_is_lexical_and_does_not_assign_stage_type():
    assert normalize_stage_group_token("Stage II") == "2"
    assert normalize_stage_group_token("clinical stage group IIA") == "2A"
    assert normalize_stage_group_token("pathological stage 2B") == "2B"
    with pytest.raises(ValueError, match="Unrecognised stage-group syntax"):
        normalize_stage_group_token("Stage V")


def test_context_keeps_clinical_and_pathological_stage_groups_separate():
    case = _case(
        clinical_stage_group="IIA",
        pathological_stage_group="pathological stage III",
    )
    context = build_case_prompt_context(case)
    values = context["canonical_field_values"]
    assert values["clinical_stage_group"]["canonical_comparison_value"] == "2A"
    assert values["pathological_stage_group"]["canonical_comparison_value"] == "3"
    assert values["clinical_stage_group"]["raw_value"] == "IIA"
    assert values["pathological_stage_group"]["raw_value"] == "pathological stage III"


def test_context_remains_json_serializable_with_typed_investigations_and_dates():
    case = _case(
        diagnosis_date="2026-11-20",
        investigation_records=[{
            "investigation_name": "MRI",
            "result_summary": "No result text provided.",
            "status": "PENDING",
            "performed_on": "2026-11-20",
        }],
    )
    context = build_case_prompt_context(case)
    import json
    encoded = json.dumps(context, ensure_ascii=False)
    assert "2026-11-20" in encoded
    assert "investigation_name" in encoded
    assert context["field_status"]["age_years"]["status"] == "not_reported"


def test_field_status_legacy_aliases_are_preserved_for_unannotated_values():
    case = _case(age_years=70, relevant_comorbidities=["diabetes"])
    context = build_case_prompt_context(case)
    assert context["field_status"]["age_years"]["status"] == "provided"
    assert context["field_status"]["relevant_comorbidities"]["status"] == "reported"
    assert context["canonical_field_values"]["age_years"]["status"] == "PRESENT"



def test_case_model_persists_hash_bound_user_input_provenance_for_supplied_fields():
    case = _case(
        age_years=70,
        clinical_t_stage="T1",
        investigation_records=[{
            "investigation_name": "MRI",
            "result_summary": "Report summary supplied by the user.",
            "status": "COMPLETED",
            "reported_on": "2026-11-20",
        }],
    )
    age_source = case.clinical_field_provenance["age_years"][0]
    t_source = case.clinical_field_provenance["clinical_t_stage"][0]
    investigation_source = case.clinical_field_provenance["investigation_records"][0]

    assert age_source.source_reference == "SyntheticCase.age_years"
    assert age_source.verification_status == "user_supplied_not_independently_verified"
    assert age_source.source_sha256
    assert t_source.source_excerpt == "T1"
    assert investigation_source.source_type == "STRUCTURED_CASE_INPUT"
    assert investigation_source.source_sha256



def test_model_facing_case_snapshot_redacts_conflicting_flat_value_but_preserves_candidates():
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
    context = build_case_prompt_context(case)

    # The in-memory/original case remains unchanged for immutable persistence.
    assert case.model_dump(mode="json")["age_years"] == 70
    # The prompt receives no arbitrarily selected flat value.
    assert context["case_snapshot"]["age_years"] is None
    assert context["field_status"]["age_years"]["value"] is None
    field = context["canonical_field_values"]["age_years"]
    assert field["state"] == "CONFLICTING"
    assert field["raw_value"] is None
    assert [item["raw_value"] for item in field["conflict_candidates"]] == [70, 72]
    assert "age_years" in context["case_snapshot_redacted_conflicting_fields"]
    assert "persisted immutable case snapshot is unchanged" in context["case_snapshot_projection_note"]

def test_explicit_provenance_and_conflict_sources_get_hashes_when_omitted():
    """Every retained source excerpt must be hash-addressed without implying verification."""
    t_excerpt = "Synthetic pathology report states a recorded clinical T token."
    age_a_excerpt = "Synthetic clinician note records age as 70 years."
    age_b_excerpt = "Synthetic patient report records age as 72 years."

    case = _case(
        clinical_t_stage="T1",
        age_years=70,
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_provenance={
            "clinical_t_stage": [{
                "source_type": "PATHOLOGY_REPORT",
                "source_reference": "synthetic-pathology-01",
                "source_excerpt": t_excerpt,
            }]
        },
        clinical_field_conflicts={
            "age_years": [
                {
                    "raw_value": 70,
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "synthetic-age-note",
                        "source_excerpt": age_a_excerpt,
                    },
                },
                {
                    "raw_value": 72,
                    "provenance": {
                        "source_type": "PATIENT_REPORT",
                        "source_reference": "synthetic-age-report",
                        "source_excerpt": age_b_excerpt,
                    },
                },
            ]
        },
    )

    t_source = case.clinical_field_provenance["clinical_t_stage"][0]
    conflict_sources = [
        item.provenance
        for item in case.clinical_field_conflicts["age_years"]
    ]

    assert t_source.source_sha256 == hashlib.sha256(t_excerpt.encode("utf-8")).hexdigest()
    assert [item.source_sha256 for item in conflict_sources] == [
        hashlib.sha256(age_a_excerpt.encode("utf-8")).hexdigest(),
        hashlib.sha256(age_b_excerpt.encode("utf-8")).hexdigest(),
    ]
    assert t_source.verification_status == "user_supplied_not_independently_verified"
    assert all(
        item.verification_status == "user_supplied_not_independently_verified"
        for item in conflict_sources
    )

def test_explicit_provenance_record_cannot_be_mutated_after_hashing():
    source = ClinicalFieldProvenance(
        source_type="CLINICIAN_NOTE",
        source_reference="synthetic-note-immutable",
        source_excerpt="Original source excerpt remains preserved.",
    )
    original_hash = hashlib.sha256(source.source_excerpt.encode("utf-8")).hexdigest()

    assert source.source_sha256 == original_hash
    with pytest.raises(ValidationError, match="Instance is frozen"):
        source.source_excerpt = "Altered source excerpt with stale hash."
    assert source.source_excerpt == "Original source excerpt remains preserved."
    assert source.source_sha256 == original_hash

def test_provenance_excerpt_preserves_exact_whitespace_before_hashing():
    excerpt = "\n  Original source wording with preserved spacing.  \t"
    source = ClinicalFieldProvenance(
        source_type=" CLINICIAN_NOTE ",
        source_reference=" synthetic-whitespace-note ",
        source_excerpt=excerpt,
    )

    assert source.source_excerpt == excerpt
    assert source.source_sha256 == hashlib.sha256(excerpt.encode("utf-8")).hexdigest()

def test_provenance_rejects_whitespace_only_excerpt_without_trimming_real_excerpt():
    with pytest.raises(ValidationError, match="non-whitespace source text"):
        ClinicalFieldProvenance(
            source_type="CLINICIAN_NOTE",
            source_reference="synthetic-blank-note",
            source_excerpt=" \n  \t ",
        )

@pytest.mark.parametrize(
    ("field_id", "value"),
    [
        (PATHOLOGICAL_T_STAGE, "T1"),
        (PATHOLOGICAL_N_STAGE, "N0"),
        (PATHOLOGICAL_M_STAGE, "M0"),
    ],
)
def test_pathological_tnm_requires_explicit_p_or_yp_prefix(field_id, value):
    with pytest.raises(ValueError, match="explicit p or yp prefix"):
        normalize_pathological_tnm_component(field_id, value)

@pytest.mark.parametrize(
    ("registry", "alias_lookup"),
    [
        (CLINICAL_FIELD_REGISTRY_V1, CLINICAL_FIELD_ALIASES_V1),
        (CLINICAL_FIELD_REGISTRY, CLINICAL_FIELD_ALIASES),
    ],
)
def test_registry_aliases_are_unique_and_resolve_to_declared_field(registry, alias_lookup):
    declared_aliases = [
        (alias, definition.field_id)
        for definition in registry.values()
        for alias in definition.aliases
    ]
    alias_names = [alias for alias, _ in declared_aliases]

    # A duplicate alias would be silently overwritten by the mapping-comprehension
    # used to build the read-only lookup; reject ambiguity before it reaches a prompt.
    assert len(alias_names) == len(set(alias_names))
    expected_lookup = {alias: field_id for alias, field_id in declared_aliases}
    assert dict(alias_lookup) == expected_lookup
    assert set(alias_lookup.values()).issubset(set(registry))

def test_conflict_candidates_are_immutable_and_keep_json_shape():
    """Conflicting raw values and their nested JSON containers remain source-faithful."""
    first_raw = [{
        "investigation_name": "MRI",
        "result_summary": "Synthetic MRI source excerpt.",
        "status": "COMPLETED",
    }]
    second_raw = [{
        "investigation_name": "CT",
        "result_summary": "Synthetic CT source excerpt.",
        "status": "COMPLETED",
    }]
    case = _case(
        clinical_field_states={"investigation_records": "CONFLICTING"},
        clinical_field_conflicts={
            "investigation_records": [
                {
                    "raw_value": first_raw,
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "synthetic-mri-report",
                        "source_excerpt": "Synthetic MRI source excerpt.",
                    },
                },
                {
                    "raw_value": second_raw,
                    "provenance": {
                        "source_type": "IMAGING_REPORT",
                        "source_reference": "synthetic-ct-report",
                        "source_excerpt": "Synthetic CT source excerpt.",
                    },
                },
            ]
        },
    )

    first_candidate = case.clinical_field_conflicts["investigation_records"][0]
    with pytest.raises(ValidationError, match="frozen"):
        first_candidate.raw_value = []

    with pytest.raises((AttributeError, TypeError)):
        first_candidate.raw_value.append({"investigation_name": "US"})

    with pytest.raises(TypeError):
        first_candidate.raw_value[0]["result_summary"] = "Altered after validation."

    # JSON serialization remains an ordinary object/list shape and preserves
    # the original competing source values for the model-facing audit context.
    serialized = case.model_dump(mode="json")["clinical_field_conflicts"]["investigation_records"]
    assert [item["raw_value"] for item in serialized] == [first_raw, second_raw]
    context_candidates = build_case_prompt_context(case)["canonical_field_values"][
        "investigation_records"
    ]["conflict_candidates"]
    assert [item["raw_value"] for item in context_candidates] == [first_raw, second_raw]

def test_invalid_state_requires_raw_value_without_canonicalizing_it():
    with pytest.raises(ValueError, match="INVALID requires a supplied raw value"):
        _case(
            clinical_t_stage=None,
            clinical_field_states={"clinical_t_stage": "INVALID"},
        )

    case = _case(
        clinical_t_stage="T9",
        clinical_field_states={"clinical_t_stage": "INVALID"},
    )
    field = build_case_prompt_context(case)["canonical_field_values"]["clinical_t_stage"]
    assert field["state"] == "INVALID"
    assert field["raw_value"] == "T9"
    assert field["canonical_comparison_value"] is None
    assert field["provenance"][0]["verification_status"] == (
        "user_supplied_not_independently_verified"
    )
    assert any(
        "INVALID means a supplied raw value failed validation" in rule
        and "do not treat it as a valid clinical fact" in rule
        for rule in build_case_prompt_context(case)["interpretation_rules"]
    )

def test_conflicting_values_require_distinct_source_excerpt_provenance():
    same_source = {
        "source_type": "CLINICIAN_NOTE",
        "source_reference": "synthetic-single-source",
        "source_excerpt": "The same source excerpt is attached to both conflicting candidates.",
    }
    with pytest.raises(ValueError, match="distinct source-specific provenance records"):
        _case(
            age_years=70,
            clinical_field_states={"age_years": "CONFLICTING"},
            clinical_field_conflicts={
                "age_years": [
                    {"raw_value": 70, "provenance": same_source},
                    {"raw_value": 72, "provenance": same_source},
                ]
            },
        )

def test_confirmed_absent_is_limited_to_explicitly_negativeable_fields():
    negativeable_fields = {
        "current_medications",
        "known_allergies",
        "relevant_comorbidities",
        "prior_treatment",
        "family_history",
    }

    actual_fields = {
        field_id
        for field_id, definition in CLINICAL_FIELD_REGISTRY.items()
        if "CONFIRMED_ABSENT" in definition.allowed_states
    }

    assert actual_fields == negativeable_fields


@pytest.mark.parametrize(
    "field_id",
    [
        "relevant_investigations",
        "patient_goals",
        "patient_preferences",
        "family_caregiver_context",
        "social_context",
        "resource_context",
        "known_unknowns",
        "investigation_records",
    ],
)
def test_non_negativeable_list_fields_reject_confirmed_absent(field_id):
    with pytest.raises(ValidationError, match="does not allow clinical data state"):
        _case(clinical_field_states={field_id: "CONFIRMED_ABSENT"})

