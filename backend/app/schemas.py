"""Strict request and response schemas for educational MDT training cases."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.clinical_fields import CLINICAL_FIELD_REGISTRY, DataState


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ClinicalFieldProvenance(StrictModel):
    """Source metadata for one supplied clinical field value or explicit state."""

    source_type: Literal[
        "CASE_SUMMARY",
        "STRUCTURED_CASE_INPUT",
        "PATIENT_REPORT",
        "FAMILY_REPORT",
        "PATHOLOGY_REPORT",
        "IMAGING_REPORT",
        "INVESTIGATION_REPORT",
        "CLINICIAN_NOTE",
        "MEDICAL_RECORD",
        "OTHER",
    ]
    source_reference: str = Field(min_length=1, max_length=300)
    source_excerpt: str = Field(min_length=1, max_length=500000)
    verification_status: Literal["user_supplied_not_independently_verified"] = "user_supplied_not_independently_verified"
    observed_at: datetime | None = None
    recorded_at: datetime | None = None
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def verify_source_hash(self) -> "ClinicalFieldProvenance":
        if self.source_sha256:
            actual = hashlib.sha256(self.source_excerpt.encode("utf-8")).hexdigest()
            if actual != self.source_sha256:
                raise ValueError("source_sha256 does not match the preserved source_excerpt.")
        return self


class ClinicalFieldConflict(StrictModel):
    """One source-specific value retained when two or more sources disagree."""

    raw_value: Any
    provenance: ClinicalFieldProvenance


class InvestigationRecord(StrictModel):
    """Typed investigation record; missing results are never treated as normal."""

    investigation_name: str = Field(min_length=1, max_length=160)
    result_summary: str | None = Field(default=None, max_length=4000)
    status: Literal["COMPLETED", "PENDING", "NOT_AVAILABLE", "DECLINED"] = "COMPLETED"
    performed_on: date | None = None
    reported_on: date | None = None
    source_reference: str | None = Field(default=None, max_length=300)
    source_excerpt: str | None = Field(default=None, max_length=500000)


class SyntheticCase(StrictModel):
    """De-identified clinical case payload passed to specialist agents.

    Flat fields remain backward-compatible. The v2 state/provenance maps add
    explicit epistemic status without rewriting the original structured values.
    """

    scenario_title: str = Field(min_length=3, max_length=160)
    case_summary: str = Field(min_length=10, max_length=12000)
    age_years: int | None = Field(default=None, ge=0, le=120)
    sex_at_birth: str | None = Field(default=None, max_length=40)
    primary_site: str | None = Field(default=None, max_length=160)
    anatomical_subsite: str | None = Field(default=None, max_length=160)
    laterality: Literal["LEFT", "RIGHT", "BILATERAL", "MIDLINE", "NOT_LATERALIZED"] | None = None
    histology: str | None = Field(default=None, max_length=160)
    histological_grade: str | None = Field(default=None, max_length=80)
    clinical_t_stage: str | None = Field(default=None, max_length=40)
    clinical_n_stage: str | None = Field(default=None, max_length=40)
    clinical_m_stage: str | None = Field(default=None, max_length=40)
    pathological_t_stage: str | None = Field(default=None, max_length=40)
    pathological_n_stage: str | None = Field(default=None, max_length=40)
    pathological_m_stage: str | None = Field(default=None, max_length=40)
    stage_group: str | None = Field(default=None, max_length=80)
    clinical_stage_group: str | None = Field(default=None, max_length=80)
    pathological_stage_group: str | None = Field(default=None, max_length=80)
    staging_system: str | None = Field(default=None, max_length=120)
    staging_edition: str | None = Field(default=None, max_length=80)
    performance_status: str | None = Field(default=None, max_length=80)
    performance_status_scale: str | None = Field(default=None, max_length=80)
    diagnosis_date: date | None = None
    pathology_summary: str | None = Field(default=None, max_length=6000)
    imaging_summary: str | None = Field(default=None, max_length=6000)
    current_medications: list[str] = Field(default_factory=list, max_length=40)
    known_allergies: list[str] = Field(default_factory=list, max_length=40)
    relevant_investigations: list[str] = Field(default_factory=list, max_length=60)
    investigation_records: list[InvestigationRecord] = Field(default_factory=list, max_length=60)
    relevant_comorbidities: list[str] = Field(default_factory=list, max_length=30)
    prior_treatment: list[str] = Field(default_factory=list, max_length=30)
    family_history: list[str] = Field(default_factory=list, max_length=40)
    family_caregiver_context: list[str] = Field(default_factory=list, max_length=30)
    patient_goals: list[str] = Field(default_factory=list, max_length=30)
    patient_preferences: list[str] = Field(default_factory=list, max_length=30)
    patient_willingness: str | None = Field(default=None, max_length=1000)
    patient_consent_status: Literal["NOT_ASKED", "PENDING", "GIVEN", "DECLINED", "WITHDRAWN"] | None = None
    social_context: list[str] = Field(default_factory=list, max_length=30)
    resource_context: list[str] = Field(default_factory=list, max_length=30)
    known_unknowns: list[str] = Field(default_factory=list, max_length=40)

    # Metadata maps are intentionally not registry fields: they describe the
    # epistemic state and lineage of the clinical values above.
    clinical_field_states: dict[str, DataState] = Field(default_factory=dict)
    clinical_field_provenance: dict[str, list[ClinicalFieldProvenance]] = Field(default_factory=dict)
    clinical_field_conflicts: dict[str, list[ClinicalFieldConflict]] = Field(default_factory=dict)

    @field_validator(
        "relevant_comorbidities",
        "prior_treatment",
        "patient_goals",
        "patient_preferences",
        "family_history",
        "family_caregiver_context",
        "social_context",
        "resource_context",
        "known_unknowns",
        "current_medications",
        "known_allergies",
        "relevant_investigations",
    )
    @classmethod
    def reject_blank_list_items(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values]
        if any(not item for item in cleaned):
            raise ValueError("List items must not be blank.")
        return cleaned

    @model_validator(mode="after")
    def validate_clinical_field_metadata(self) -> "SyntheticCase":
        known_fields = set(CLINICAL_FIELD_REGISTRY)
        metadata_maps = (
            ("clinical_field_states", self.clinical_field_states),
            ("clinical_field_provenance", self.clinical_field_provenance),
            ("clinical_field_conflicts", self.clinical_field_conflicts),
        )
        for map_name, entries in metadata_maps:
            unknown = sorted(set(entries) - known_fields)
            if unknown:
                raise ValueError(f"{map_name} contains unknown canonical field ID(s): {', '.join(unknown)}")

        def has_value(value: Any) -> bool:
            if value is None or value == "":
                return False
            if isinstance(value, (list, tuple, dict)):
                return bool(value)
            return True

        for field_id, state in self.clinical_field_states.items():
            definition = CLINICAL_FIELD_REGISTRY[field_id]
            if state not in definition.allowed_states:
                raise ValueError(f"{field_id} does not allow clinical data state {state!r}.")
            value_present = has_value(getattr(self, field_id))
            sources = self.clinical_field_provenance.get(field_id, [])
            conflicts = self.clinical_field_conflicts.get(field_id, [])

            if state == "PRESENT" and not value_present:
                raise ValueError(f"{field_id} cannot be PRESENT without a supplied value.")
            if state == "CONFIRMED_ABSENT":
                if value_present:
                    raise ValueError(f"{field_id} cannot carry a positive value while marked CONFIRMED_ABSENT.")
                if not sources or not any(source.source_excerpt.strip() for source in sources):
                    raise ValueError(f"{field_id} CONFIRMED_ABSENT requires explicit source provenance.")
            if state in {"UNKNOWN", "NOT_REPORTED", "NOT_ASSESSED", "PENDING", "DECLINED", "NOT_APPLICABLE"} and value_present:
                raise ValueError(f"{field_id} cannot carry a supplied value while marked {state}.")
            if state == "CONFLICTING":
                if len(conflicts) < 2:
                    raise ValueError(f"{field_id} CONFLICTING requires at least two source-specific conflict values.")
                distinct = {
                    json.dumps(item.raw_value, ensure_ascii=False, sort_keys=True, default=str)
                    for item in conflicts
                }
                if len(distinct) < 2:
                    raise ValueError(f"{field_id} CONFLICTING requires at least two distinct raw values.")

        for field_id, conflicts in self.clinical_field_conflicts.items():
            if self.clinical_field_states.get(field_id) != "CONFLICTING":
                raise ValueError(f"{field_id} conflict values require clinical_field_states[{field_id!r}]='CONFLICTING'.")
            if len(conflicts) < 2:
                raise ValueError(f"{field_id} requires at least two conflict values.")

        # Persist a minimal, hash-bound provenance record for every supplied
        # value that lacks an explicit source reference. It identifies the
        # actual request field as its source and explicitly does NOT claim
        # independent document verification.
        provenance = dict(self.clinical_field_provenance)
        serialised_values = self.model_dump(mode="json", exclude_none=True)
        for field_id in CLINICAL_FIELD_REGISTRY:
            value = getattr(self, field_id)
            state = self.clinical_field_states.get(
                field_id,
                "PRESENT" if value is not None and value != "" and (not isinstance(value, list) or bool(value)) else "NOT_REPORTED",
            )
            if field_id in provenance or state not in {"PRESENT", "INVALID"}:
                continue
            if value is None or value == "" or (isinstance(value, list) and not value):
                continue
            serialised = serialised_values.get(field_id)
            excerpt = serialised if isinstance(serialised, str) else json.dumps(
                serialised, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            source_excerpt = excerpt
            source_hash = hashlib.sha256(source_excerpt.encode("utf-8")).hexdigest()
            provenance[field_id] = [
                ClinicalFieldProvenance(
                    source_type="CASE_SUMMARY" if field_id == "case_summary" else "STRUCTURED_CASE_INPUT",
                    source_reference=f"SyntheticCase.{field_id}",
                    source_excerpt=source_excerpt,
                    source_sha256=source_hash,
                    verification_status="user_supplied_not_independently_verified",
                )
            ]
        self.clinical_field_provenance = provenance

        return self


class PatientRegistrationRequest(StrictModel):
    """Registry identity plus a separate de-identified clinical case."""

    patient_name: str = Field(min_length=2, max_length=120)
    case: SyntheticCase


class PatientCaseUpdateRequest(StrictModel):
    """Update registry identity and append a de-identified clinical case version."""

    patient_name: str = Field(min_length=2, max_length=120)
    case: SyntheticCase


class CaseValidationResult(StrictModel):
    valid: bool
    mode: str = "fictional_educational_case"
    warnings: list[str] = Field(default_factory=list)
    note: str = (
        "Schema validation only. This is not clinical validation or a treatment recommendation."
    )


class AgentAssessmentRequest(StrictModel):
    case: SyntheticCase
    round_number: int = Field(default=1, ge=1, le=4)


class BatchRunRequest(StrictModel):
    case: SyntheticCase


class PatientRunRequest(StrictModel):
    """Start a simulation from an already-saved immutable patient case version."""

    case_version_id: str = Field(
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
    )


class CaseIntakeScreenRequest(StrictModel):
    """Deterministic screening request; declined domains remain explicit gaps."""

    case: SyntheticCase
    declined_domains: list[str] = Field(default_factory=list, max_length=6)


class IntakeSessionCreateRequest(StrictModel):
    """Create a new auditable pre-MDT intake session."""

    case: SyntheticCase


class IntakeEventRequest(StrictModel):
    """Append one answer, correction or declined-domain event."""

    event_type: str
    field_id: str | None = Field(default=None, max_length=80)
    value: object | None = None
    domain: str | None = Field(default=None, max_length=80)
    source_text: str | None = Field(default=None, max_length=4000)


class IntakeAcceptRequest(StrictModel):
    """Explicit user confirmation to accept an incomplete intake."""

    confirmed: bool = False


class IntakePromoteRequest(StrictModel):
    """Promote an accepted intake to a fictional patient registry record/version."""

    patient_name: str = Field(min_length=2, max_length=120)
    patient_id: str | None = Field(default=None, min_length=36, max_length=36, pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
