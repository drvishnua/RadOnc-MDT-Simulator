"""Immutable, versioned clinical field identifiers and safe terminology helpers.

Registry v1.0.0 is retained unchanged for historical inspection. Registry v2.0.0
is additive and is the only registry accepted for new or resumed model runs.
A registry definition is a data contract, not evidence that a patient value exists.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Final, Literal


HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION: Final[str] = "1.0.0"
CLINICAL_FIELD_REGISTRY_VERSION: Final[str] = "2.0.0"
LEGACY_FIELD_REGISTRY_VERSION: Final[str] = "legacy-unversioned"

# Stable field IDs. Existing IDs are never renamed or repurposed. Additions are
# introduced only in a new registry version.
SCENARIO_TITLE: Final[str] = "scenario_title"
CASE_SUMMARY: Final[str] = "case_summary"
AGE_YEARS: Final[str] = "age_years"
SEX_AT_BIRTH: Final[str] = "sex_at_birth"
PRIMARY_SITE: Final[str] = "primary_site"
HISTOLOGY: Final[str] = "histology"
CLINICAL_T_STAGE: Final[str] = "clinical_t_stage"
CLINICAL_N_STAGE: Final[str] = "clinical_n_stage"
CLINICAL_M_STAGE: Final[str] = "clinical_m_stage"
STAGE_GROUP: Final[str] = "stage_group"
PERFORMANCE_STATUS: Final[str] = "performance_status"
PATHOLOGY_SUMMARY: Final[str] = "pathology_summary"
IMAGING_SUMMARY: Final[str] = "imaging_summary"
CURRENT_MEDICATIONS: Final[str] = "current_medications"
KNOWN_ALLERGIES: Final[str] = "known_allergies"
RELEVANT_INVESTIGATIONS: Final[str] = "relevant_investigations"
RELEVANT_COMORBIDITIES: Final[str] = "relevant_comorbidities"
PRIOR_TREATMENT: Final[str] = "prior_treatment"
PATIENT_GOALS: Final[str] = "patient_goals"
SOCIAL_CONTEXT: Final[str] = "social_context"
RESOURCE_CONTEXT: Final[str] = "resource_context"
KNOWN_UNKNOWNS: Final[str] = "known_unknowns"

# Additive v2 identifiers. Existing IDs above retain their exact meanings.
ANATOMICAL_SUBSITE: Final[str] = "anatomical_subsite"
LATERALITY: Final[str] = "laterality"
HISTOLOGICAL_GRADE: Final[str] = "histological_grade"
PATHOLOGICAL_T_STAGE: Final[str] = "pathological_t_stage"
PATHOLOGICAL_N_STAGE: Final[str] = "pathological_n_stage"
PATHOLOGICAL_M_STAGE: Final[str] = "pathological_m_stage"
CLINICAL_STAGE_GROUP: Final[str] = "clinical_stage_group"
PATHOLOGICAL_STAGE_GROUP: Final[str] = "pathological_stage_group"
STAGING_SYSTEM: Final[str] = "staging_system"
STAGING_EDITION: Final[str] = "staging_edition"
PERFORMANCE_STATUS_SCALE: Final[str] = "performance_status_scale"
DIAGNOSIS_DATE: Final[str] = "diagnosis_date"
INVESTIGATION_RECORDS: Final[str] = "investigation_records"
FAMILY_HISTORY: Final[str] = "family_history"
FAMILY_CAREGIVER_CONTEXT: Final[str] = "family_caregiver_context"
PATIENT_PREFERENCES: Final[str] = "patient_preferences"
PATIENT_WILLINGNESS: Final[str] = "patient_willingness"
PATIENT_CONSENT_STATUS: Final[str] = "patient_consent_status"

# Short, stable aliases for common clinical concepts. These are field aliases,
# not permission to infer a patient-specific value.
T: Final[str] = CLINICAL_T_STAGE
N: Final[str] = CLINICAL_N_STAGE
M: Final[str] = CLINICAL_M_STAGE
AGE: Final[str] = AGE_YEARS
SEX: Final[str] = SEX_AT_BIRTH
SITE: Final[str] = PRIMARY_SITE
STAGE: Final[str] = STAGE_GROUP

DataState = Literal[
    "PRESENT",
    "CONFIRMED_ABSENT",
    "UNKNOWN",
    "NOT_REPORTED",
    "NOT_ASSESSED",
    "PENDING",
    "DECLINED",
    "NOT_APPLICABLE",
    "CONFLICTING",
    "INVALID",
]

_LEGACY_DATA_STATES: Final[tuple[str, ...]] = (
    "PRESENT",
    "CONFIRMED_ABSENT",
    "UNKNOWN",
    "NOT_REPORTED",
    "NOT_ASSESSED",
    "NOT_APPLICABLE",
    "CONFLICTING",
)
_COMMON_DATA_STATES: Final[tuple[str, ...]] = (
    "PRESENT",
    "UNKNOWN",
    "NOT_REPORTED",
    "NOT_ASSESSED",
    "PENDING",
    "DECLINED",
    "NOT_APPLICABLE",
    "CONFLICTING",
    "INVALID",
)
_LIST_DATA_STATES: Final[tuple[str, ...]] = (
    "PRESENT",
    "CONFIRMED_ABSENT",
    "UNKNOWN",
    "NOT_REPORTED",
    "NOT_ASSESSED",
    "PENDING",
    "DECLINED",
    "NOT_APPLICABLE",
    "CONFLICTING",
    "INVALID",
)


@dataclass(frozen=True, slots=True)
class ClinicalFieldDefinition:
    field_id: str
    label: str
    value_type: str
    description: str
    aliases: tuple[str, ...] = ()
    # The default is deliberately the v1 state vocabulary. V2 definitions set
    # their state vocabulary explicitly when constructing the new registry.
    allowed_states: tuple[str, ...] = _LEGACY_DATA_STATES
    unit: str | None = None
    allowed_values: tuple[str, ...] = ()
    validation_rule: str = "preserve_raw_validate_declared_type"
    source_requirement: str = "retain_source_and_provenance_status"
    applicability: str = "case_specific; do_not_infer"
    semantic_kind: str = "FACT"


# Immutable v1 definitions. Do not edit or repurpose this tuple; new fields and
# metadata belong to the separately versioned v2 registry below.
_DEFINITIONS = (
    ClinicalFieldDefinition(SCENARIO_TITLE, "Scenario title", "string", "Fictional case label."),
    ClinicalFieldDefinition(CASE_SUMMARY, "Case summary", "free_text", "Verbatim user-provided case narrative; not silently parsed into confirmed facts."),
    ClinicalFieldDefinition(AGE_YEARS, "Age (years)", "integer", "Explicitly recorded age in completed years.", ("AGE", "AGE_YEARS")),
    ClinicalFieldDefinition(SEX_AT_BIRTH, "Sex at birth", "string", "Explicitly recorded sex at birth; do not infer from pronouns or diagnosis.", ("SEX", "SEX_AT_BIRTH")),
    ClinicalFieldDefinition(PRIMARY_SITE, "Primary site", "string", "Explicitly recorded primary anatomical site.", ("SITE", "PRIMARY_SITE")),
    ClinicalFieldDefinition(HISTOLOGY, "Histology", "string", "Explicitly recorded histological diagnosis."),
    ClinicalFieldDefinition(CLINICAL_T_STAGE, "Clinical T component", "string", "Clinical primary-tumour TNM component; staging system and edition must be supplied separately before interpretation.", ("T", "CT", "CLINICAL_T_STAGE")),
    ClinicalFieldDefinition(CLINICAL_N_STAGE, "Clinical N component", "string", "Clinical regional-node TNM component; staging system and edition must be supplied separately before interpretation.", ("N", "CN", "CLINICAL_N_STAGE")),
    ClinicalFieldDefinition(CLINICAL_M_STAGE, "Clinical M component", "string", "Clinical distant-metastasis TNM component; staging system and edition must be supplied separately before interpretation.", ("M", "CM", "CLINICAL_M_STAGE")),
    ClinicalFieldDefinition(STAGE_GROUP, "Stage group", "string", "Recorded stage group; do not derive from incomplete components.", ("STAGE", "STAGE_GROUP")),
    ClinicalFieldDefinition(PERFORMANCE_STATUS, "Performance status", "string", "Explicitly recorded performance-status scale and value; do not infer."),
    ClinicalFieldDefinition(PATHOLOGY_SUMMARY, "Pathology summary", "free_text", "Recorded pathology narrative with source provenance."),
    ClinicalFieldDefinition(IMAGING_SUMMARY, "Imaging summary", "free_text", "Recorded imaging narrative with source provenance."),
    ClinicalFieldDefinition(CURRENT_MEDICATIONS, "Current medications", "string_list", "Reported medication list; an empty list is not a confirmed negative."),
    ClinicalFieldDefinition(KNOWN_ALLERGIES, "Known allergies", "string_list", "Reported allergy list; an empty list is not a confirmed negative."),
    ClinicalFieldDefinition(RELEVANT_INVESTIGATIONS, "Relevant investigations", "string_list", "Reported investigations and findings; missing entries are not normal results."),
    ClinicalFieldDefinition(RELEVANT_COMORBIDITIES, "Relevant comorbidities", "string_list", "Reported comorbidities; an empty list is not a confirmed absence."),
    ClinicalFieldDefinition(PRIOR_TREATMENT, "Prior treatment", "string_list", "Reported prior treatment; an empty list is not a confirmed absence."),
    ClinicalFieldDefinition(PATIENT_GOALS, "Patient goals", "string_list", "Patient-stated goals and preferences; do not infer willingness."),
    ClinicalFieldDefinition(SOCIAL_CONTEXT, "Social context", "string_list", "Reported social and family context; do not infer."),
    ClinicalFieldDefinition(RESOURCE_CONTEXT, "Resource context", "string_list", "Reported resource and access context."),
    ClinicalFieldDefinition(KNOWN_UNKNOWNS, "Known unknowns", "string_list", "Explicitly recorded unresolved information gaps."),
)

CLINICAL_FIELD_REGISTRY_V1: Final = MappingProxyType(
    {definition.field_id: definition for definition in _DEFINITIONS}
)
CLINICAL_FIELD_ALIASES_V1: Final = MappingProxyType(
    {
        alias: definition.field_id
        for definition in _DEFINITIONS
        for alias in definition.aliases
    }
)

_ADDITIONAL_DEFINITIONS = (
    ClinicalFieldDefinition(ANATOMICAL_SUBSITE, "Anatomical subsite", "string", "Explicitly recorded anatomical subsite; site-specific staging rules must be checked before interpretation."),
    ClinicalFieldDefinition(LATERALITY, "Laterality", "enum", "Explicitly recorded side; preserve conflicting source statements.", allowed_values=("LEFT", "RIGHT", "BILATERAL", "MIDLINE", "NOT_LATERALIZED")),
    ClinicalFieldDefinition(HISTOLOGICAL_GRADE, "Histological grade", "string", "Recorded grade using the histology-specific grading convention; do not infer or translate across systems."),
    ClinicalFieldDefinition(PATHOLOGICAL_T_STAGE, "Pathological T component", "string", "Pathological primary-tumour component; never use as clinical T evidence."),
    ClinicalFieldDefinition(PATHOLOGICAL_N_STAGE, "Pathological N component", "string", "Pathological regional-node component; never use as clinical N evidence."),
    ClinicalFieldDefinition(PATHOLOGICAL_M_STAGE, "Pathological M component", "string", "Pathological distant-metastasis component; never use as clinical M evidence."),
    ClinicalFieldDefinition(CLINICAL_STAGE_GROUP, "Clinical stage group", "string", "Explicitly recorded clinical stage group; requires site, staging system and edition context."),
    ClinicalFieldDefinition(PATHOLOGICAL_STAGE_GROUP, "Pathological stage group", "string", "Explicitly recorded pathological stage group; never substitute for clinical stage group."),
    ClinicalFieldDefinition(STAGING_SYSTEM, "Staging system", "string", "Named staging system used for the supplied stage value; do not infer from site or year."),
    ClinicalFieldDefinition(STAGING_EDITION, "Staging edition", "string", "Explicit edition/version of the staging system; do not infer or silently upgrade."),
    ClinicalFieldDefinition(PERFORMANCE_STATUS_SCALE, "Performance-status scale", "string", "Named scale for the recorded performance-status value; do not infer ECOG/WHO/Karnofsky equivalence."),
    ClinicalFieldDefinition(DIAGNOSIS_DATE, "Diagnosis date", "date", "Explicitly recorded diagnosis date; preserve source and avoid inferring an exact date from relative wording."),
    ClinicalFieldDefinition(INVESTIGATION_RECORDS, "Investigation records", "object_list", "Typed investigation records with test, finding, date and source; absent records are not normal findings."),
    ClinicalFieldDefinition(FAMILY_HISTORY, "Family history", "string_list", "Reported family history; an empty list is not a confirmed negative."),
    ClinicalFieldDefinition(FAMILY_CAREGIVER_CONTEXT, "Family/caregiver context", "string_list", "Reported family and caregiver context; do not infer availability or support."),
    ClinicalFieldDefinition(PATIENT_PREFERENCES, "Patient preferences", "string_list", "Patient-stated preferences; distinguish recorded statements from clinician interpretation."),
    ClinicalFieldDefinition(PATIENT_WILLINGNESS, "Patient willingness", "string", "Explicitly recorded willingness or refusal; never infer consent or willingness."),
    ClinicalFieldDefinition(PATIENT_CONSENT_STATUS, "Patient consent status", "enum", "Explicit consent status for the described educational scenario; not a proxy for treatment consent.", allowed_values=("NOT_ASKED", "PENDING", "GIVEN", "DECLINED", "WITHDRAWN")),
)

# Units and validation rule identifiers are metadata, not clinical thresholds.
_UNITS: Final = MappingProxyType({
    AGE_YEARS: "years",
    DIAGNOSIS_DATE: "date",
})
_VALIDATION_RULES: Final = MappingProxyType({
    AGE_YEARS: "integer_0_to_120",
    LATERALITY: "closed_enum",
    DIAGNOSIS_DATE: "iso_date",
    CLINICAL_T_STAGE: "clinical_tnm_lexical_only",
    CLINICAL_N_STAGE: "clinical_tnm_lexical_only",
    CLINICAL_M_STAGE: "clinical_tnm_lexical_only",
    PATHOLOGICAL_T_STAGE: "pathological_tnm_lexical_only",
    PATHOLOGICAL_N_STAGE: "pathological_tnm_lexical_only",
    PATHOLOGICAL_M_STAGE: "pathological_tnm_lexical_only",
    STAGING_SYSTEM: "explicit_identifier_no_inference",
    STAGING_EDITION: "explicit_edition_no_inference",
})
_NEGATIVEABLE_LIST_FIELDS: Final = frozenset({
    CURRENT_MEDICATIONS,
    KNOWN_ALLERGIES,
    RELEVANT_COMORBIDITIES,
    PRIOR_TREATMENT,
    FAMILY_HISTORY,
})
_PROVENANCE_REQUIRED_FIELDS: Final = frozenset({
    CLINICAL_T_STAGE, CLINICAL_N_STAGE, CLINICAL_M_STAGE,
    PATHOLOGICAL_T_STAGE, PATHOLOGICAL_N_STAGE, PATHOLOGICAL_M_STAGE,
    STAGE_GROUP, CLINICAL_STAGE_GROUP, PATHOLOGICAL_STAGE_GROUP,
    HISTOLOGY, HISTOLOGICAL_GRADE, PRIMARY_SITE, ANATOMICAL_SUBSITE,
    LATERALITY, PERFORMANCE_STATUS,
})

def _build_v2_definition(definition: ClinicalFieldDefinition) -> ClinicalFieldDefinition:
    states = _LIST_DATA_STATES if definition.field_id in _NEGATIVEABLE_LIST_FIELDS or definition.value_type in {"string_list", "object_list"} else _COMMON_DATA_STATES
    return replace(
        definition,
        allowed_states=states,
        unit=_UNITS.get(definition.field_id),
        validation_rule=_VALIDATION_RULES.get(definition.field_id, "preserve_raw_validate_declared_type"),
        source_requirement=(
            "explicit_source_required_for_state_or_interpretation"
            if definition.field_id in _PROVENANCE_REQUIRED_FIELDS
            else "retain_source_when_available; mark_unverified_if_missing"
        ),
    )

_V2_DEFINITIONS = tuple(_build_v2_definition(item) for item in (*_DEFINITIONS, *_ADDITIONAL_DEFINITIONS))
CLINICAL_FIELD_REGISTRY_V2: Final = MappingProxyType(
    {definition.field_id: definition for definition in _V2_DEFINITIONS}
)
CLINICAL_FIELD_REGISTRY: Final = CLINICAL_FIELD_REGISTRY_V2
CLINICAL_FIELD_ALIASES: Final = MappingProxyType({
    alias: definition.field_id
    for definition in _V2_DEFINITIONS
    for alias in definition.aliases
})
CLINICAL_CASE_VALUE_FIELDS: Final = tuple(CLINICAL_FIELD_REGISTRY)
_TNM_FIELD_PREFIX: Final = MappingProxyType({
    CLINICAL_T_STAGE: "T",
    CLINICAL_N_STAGE: "N",
    CLINICAL_M_STAGE: "M",
    PATHOLOGICAL_T_STAGE: "T",
    PATHOLOGICAL_N_STAGE: "N",
    PATHOLOGICAL_M_STAGE: "M",
})
_TNM_COMPONENT_PATTERNS: Final = MappingProxyType({
    "T": re.compile(r"^(?:IS|X|0|[1-4][A-D]?)$", re.IGNORECASE),
    "N": re.compile(r"^(?:X|0|[1-3])$", re.IGNORECASE),
    "M": re.compile(r"^(?:X|0|1)$", re.IGNORECASE),
})
_TNM_VALUE_PATTERN = re.compile(
    r"^(?:(?P<prefix>YP|YC|P|C)\s*)?(?P<component>[TNM])?\s*(?P<value>[A-Z0-9][A-Z0-9./+_-]*)$",
    re.IGNORECASE,
)


def normalize_clinical_tnm_component(field_id: str, raw_value: str) -> str:
    """Return a lexical clinical component (e.g. '1' and 'T1' -> 'T1').

    This is not stage validation. Clinical prefixes are tolerated because the
    target field itself is clinical; pathological prefixes are rejected. Site,
    subsite, staging system and edition remain necessary for interpretation.
    The original raw source value must always be retained separately.
    """
    if field_id not in {CLINICAL_T_STAGE, CLINICAL_N_STAGE, CLINICAL_M_STAGE}:
        raise ValueError(f"Unsupported clinical TNM field: {field_id}")
    expected = _TNM_FIELD_PREFIX[field_id]
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError("TNM component must be a non-empty string.")
    match = _TNM_VALUE_PATTERN.fullmatch(raw_value.strip())
    if match is None:
        raise ValueError(f"Unrecognised TNM component syntax: {raw_value!r}")
    prefix = (match.group("prefix") or "").upper()
    component = (match.group("component") or expected).upper()
    value = match.group("value").upper()
    if prefix in {"P", "YP"}:
        raise ValueError("Pathological staging cannot be normalized into a clinical field.")
    if component != expected:
        raise ValueError(f"{field_id} requires a {expected}-component, not {component}.")
    if not _TNM_COMPONENT_PATTERNS[expected].fullmatch(value):
        raise ValueError(f"Unrecognised {expected}-component value: {raw_value!r}")
    return ("YC" if prefix == "YC" else "") + expected + value


def normalize_stage_group_token(raw_value: str) -> str:
    """Return a lexical stage-group key while retaining the original raw value.

    This does not infer clinical versus pathological class or validate a site,
    staging system or edition. The caller must keep those dimensions separate.
    """
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError("Stage-group token must be a non-empty string.")
    value = raw_value.strip().upper()
    value = re.sub(r"^(?:CLINICAL|PATHOLOGICAL)\s+", "", value)
    value = re.sub(r"^STAGE(?:\s+GROUP)?\s*", "", value)
    value = re.sub(r"^(?:IS|WAS|OF)\s+", "", value)
    value = re.sub(r"^[:=]\s*", "", value)
    match = re.fullmatch(r"(IV|III|II|I|[1-4])([ABC])?", value)
    if match is None:
        raise ValueError(f"Unrecognised stage-group syntax: {raw_value!r}")
    roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4}
    number = roman_values.get(match.group(1), int(match.group(1)) if match.group(1).isdigit() else None)
    if number is None:
        raise ValueError(f"Unrecognised stage-group syntax: {raw_value!r}")
    return f"{number}{match.group(2) or ''}"


def normalize_pathological_tnm_component(field_id: str, raw_value: str) -> str:
    """Normalize a pathological TNM token while retaining p/yp provenance class."""
    if field_id not in {PATHOLOGICAL_T_STAGE, PATHOLOGICAL_N_STAGE, PATHOLOGICAL_M_STAGE}:
        raise ValueError(f"Unsupported pathological TNM field: {field_id}")
    expected = _TNM_FIELD_PREFIX[field_id]
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError("Pathological TNM component must be a non-empty string.")
    match = _TNM_VALUE_PATTERN.fullmatch(raw_value.strip())
    if match is None:
        raise ValueError(f"Unrecognised pathological TNM component syntax: {raw_value!r}")
    prefix = (match.group("prefix") or "").upper()
    component = (match.group("component") or expected).upper()
    value = match.group("value").upper()
    if prefix not in {"P", "YP"}:
        raise ValueError("A pathological TNM component requires an explicit p or yp prefix.")
    if component != expected:
        raise ValueError(f"{field_id} requires a {expected}-component, not {component}.")
    if not _TNM_COMPONENT_PATTERNS[expected].fullmatch(value):
        raise ValueError(f"Unrecognised pathological {expected}-component value: {raw_value!r}")
    return prefix + expected + value


def require_supported_registry_version(version: str) -> None:
    """Fail closed when a run requests a registry other than the active contract.

    Historical v1 definitions remain available for inspection, but this build
    does not silently resume a v1/legacy run with the v2 prompt contract. An
    explicit migration/new immutable case version is required.
    """
    if version != CLINICAL_FIELD_REGISTRY_VERSION:
        raise ValueError(
            f"This saved record uses clinical field registry version {version!r}, "
            f"but this build supports new/resumed runs only on "
            f"{CLINICAL_FIELD_REGISTRY_VERSION!r}. Historical snapshots remain preserved; "
            "Create a new immutable case version before starting or resuming MDT generation."
        )


def _registry_payload(version: str) -> dict[str, object]:
    if version == HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION:
        definitions = _DEFINITIONS
        return {
            "version": version,
            "fields": [
                {
                    "field_id": item.field_id,
                    "label": item.label,
                    "value_type": item.value_type,
                    "description": item.description,
                    "aliases": list(item.aliases),
                    "allowed_states": list(item.allowed_states),
                }
                for item in definitions
            ],
            "rules": [
                "Field IDs and meanings are stable; do not invent or rename field IDs.",
                "A field definition is not evidence that a patient-specific value exists.",
                "UNKNOWN, NOT_REPORTED, NOT_ASSESSED, NOT_APPLICABLE, CONFIRMED_ABSENT and CONFLICTING are distinct states.",
                "An empty list or missing value is not a negative finding.",
                "Clinical and pathological staging are not interchangeable.",
                "Lexical TNM equivalence is not staging validation; the staging system and edition are required for clinical interpretation.",
            ],
        }
    if version != CLINICAL_FIELD_REGISTRY_VERSION:
        raise ValueError(f"Unsupported clinical field registry version: {version!r}")
    return {
        "version": version,
        "fields": [
            {
                "field_id": item.field_id,
                "label": item.label,
                "value_type": item.value_type,
                "description": item.description,
                "aliases": list(item.aliases),
                "unit": item.unit,
                "allowed_values": list(item.allowed_values),
                "allowed_states": list(item.allowed_states),
                "validation_rule": item.validation_rule,
                "source_requirement": item.source_requirement,
                "applicability": item.applicability,
                "semantic_kind": item.semantic_kind,
            }
            for item in CLINICAL_FIELD_REGISTRY.values()
        ],
        "rules": [
            "Field IDs and meanings are stable; do not invent, rename or repurpose field IDs.",
            "Registry constants standardise names and semantics; they do not guarantee model adherence or prevent every hallucination.",
            "A field definition is not evidence that a patient-specific value exists.",
            "UNKNOWN, NOT_REPORTED, NOT_ASSESSED, PENDING, DECLINED, NOT_APPLICABLE, CONFIRMED_ABSENT, CONFLICTING and INVALID are distinct states.",
            "An empty list or missing value is not a negative finding; CONFIRMED_ABSENT requires explicit source evidence.",
            "Clinical and pathological staging are distinct and may never be substituted for one another.",
            "T/N/M lexical normalization is not clinical staging validation. Site, subsite, staging system and edition are required before interpretation.",
            "Preserve raw values, field states, source provenance, conflicts and transformation warnings; do not silently repair or choose a source.",
        ],
    }


def clinical_field_registry_sha256(version: str = CLINICAL_FIELD_REGISTRY_VERSION) -> str:
    payload = _registry_payload(version)
    serialised = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def build_registry_prompt_payload(version: str = CLINICAL_FIELD_REGISTRY_VERSION) -> dict[str, object]:
    """Return a JSON-serializable registry contract with a deterministic v2 hash."""
    payload = _registry_payload(version)
    if version == CLINICAL_FIELD_REGISTRY_VERSION:
        payload["sha256"] = clinical_field_registry_sha256(version)
    return payload
