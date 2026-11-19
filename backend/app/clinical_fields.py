"""Immutable, versioned clinical field identifiers and safe terminology helpers.

Field IDs and meanings are stable API contracts. Evolve definitions by adding a
new registry version; never repurpose an existing identifier. This registry
standardises data semantics but cannot guarantee model adherence or prevent all
hallucinations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal


CLINICAL_FIELD_REGISTRY_VERSION: Final[str] = "1.0.0"
LEGACY_FIELD_REGISTRY_VERSION: Final[str] = "legacy-unversioned"

# Stable field IDs. Never rename or repurpose these identifiers.
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
    "NOT_APPLICABLE",
    "CONFLICTING",
]


@dataclass(frozen=True, slots=True)
class ClinicalFieldDefinition:
    field_id: str
    label: str
    value_type: str
    description: str
    aliases: tuple[str, ...] = ()
    allowed_states: tuple[DataState, ...] = (
        "PRESENT",
        "CONFIRMED_ABSENT",
        "UNKNOWN",
        "NOT_REPORTED",
        "NOT_ASSESSED",
        "NOT_APPLICABLE",
        "CONFLICTING",
    )


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

# Read-only registry and read-only alias index; definitions themselves are frozen.
CLINICAL_FIELD_REGISTRY: Final = MappingProxyType(
    {definition.field_id: definition for definition in _DEFINITIONS}
)
CLINICAL_FIELD_ALIASES: Final = MappingProxyType(
    {
        alias: definition.field_id
        for definition in _DEFINITIONS
        for alias in definition.aliases
    }
)

_TNM_FIELD_PREFIX: Final = MappingProxyType({
    CLINICAL_T_STAGE: "T",
    CLINICAL_N_STAGE: "N",
    CLINICAL_M_STAGE: "M",
})
_TNM_VALUE_PATTERN = re.compile(r"^(?:(?P<prefix>[CP])\s*)?(?P<component>[TNM])?\s*(?P<value>[A-Z0-9][A-Z0-9./+_-]*)$", re.IGNORECASE)


def normalize_clinical_tnm_component(field_id: str, raw_value: str) -> str:
    """Return a comparable clinical component (e.g. '1' and 'T1' -> 'T1').

    The original source value must always be retained separately. Only the
    clinical T/N/M fields are accepted. A pathological prefix is rejected;
    a clinical prefix is tolerated because the target field itself is clinical.
    This is lexical normalization, not TNM staging validation or edition-aware
    interpretation.
    """
    expected = _TNM_FIELD_PREFIX.get(field_id)
    if expected is None:
        raise ValueError(f"Unsupported clinical TNM field: {field_id}")
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError("TNM component must be a non-empty string.")
    match = _TNM_VALUE_PATTERN.fullmatch(raw_value.strip())
    if match is None:
        raise ValueError(f"Unrecognised TNM component syntax: {raw_value!r}")
    prefix = (match.group("prefix") or "").upper()
    component = (match.group("component") or expected).upper()
    # A combined TNM token is not a single component value.
    if re.search(r"[TNM](?:[0-4]|IS|X)", match.group("value")[1:], re.IGNORECASE):
        raise ValueError("Combined TNM tokens must be split into their individual components.")
    if prefix == "P":
        raise ValueError("Pathological staging cannot be normalized into a clinical field.")
    if component != expected:
        raise ValueError(
            f"{field_id} requires a {expected}-component, not {component}."
        )
    return expected + match.group("value").upper()


def require_supported_registry_version(version: str) -> None:
    """Prevent a saved run from mixing a historical registry with the current one.

    Historical registry payloads must be retained and explicitly added to the
    supported-version set before they can be resumed under a future release.
    """
    if version != CLINICAL_FIELD_REGISTRY_VERSION:
        raise ValueError(
            f"This saved record uses clinical field registry version {version!r}, "
            f"but this build supports {CLINICAL_FIELD_REGISTRY_VERSION!r}. "
            "Create a new immutable case version before starting or resuming MDT generation."
        )


def build_registry_prompt_payload() -> dict[str, object]:
    """Return a JSON-serializable copy of the immutable registry for model context."""
    return {
        "version": CLINICAL_FIELD_REGISTRY_VERSION,
        "fields": [
            {
                "field_id": item.field_id,
                "label": item.label,
                "value_type": item.value_type,
                "description": item.description,
                "aliases": list(item.aliases),
                "allowed_states": list(item.allowed_states),
            }
            for item in CLINICAL_FIELD_REGISTRY.values()
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
