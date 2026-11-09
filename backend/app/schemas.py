"""Strict request and response schemas for educational MDT training cases."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SyntheticCase(StrictModel):
    """De-identified clinical case payload passed to specialist agents."""

    scenario_title: str = Field(min_length=3, max_length=160)
    case_summary: str = Field(min_length=10, max_length=12000)
    age_years: int | None = Field(default=None, ge=0, le=120)
    sex_at_birth: str | None = Field(default=None, max_length=40)
    primary_site: str | None = Field(default=None, max_length=160)
    histology: str | None = Field(default=None, max_length=160)
    clinical_t_stage: str | None = Field(default=None, max_length=40)
    clinical_n_stage: str | None = Field(default=None, max_length=40)
    clinical_m_stage: str | None = Field(default=None, max_length=40)
    stage_group: str | None = Field(default=None, max_length=80)
    performance_status: str | None = Field(default=None, max_length=80)
    pathology_summary: str | None = Field(default=None, max_length=6000)
    imaging_summary: str | None = Field(default=None, max_length=6000)
    current_medications: list[str] = Field(default_factory=list, max_length=40)
    known_allergies: list[str] = Field(default_factory=list, max_length=40)
    relevant_investigations: list[str] = Field(default_factory=list, max_length=60)
    relevant_comorbidities: list[str] = Field(default_factory=list, max_length=30)
    prior_treatment: list[str] = Field(default_factory=list, max_length=30)
    patient_goals: list[str] = Field(default_factory=list, max_length=30)
    social_context: list[str] = Field(default_factory=list, max_length=30)
    resource_context: list[str] = Field(default_factory=list, max_length=30)
    known_unknowns: list[str] = Field(default_factory=list, max_length=40)

    @field_validator(
        "relevant_comorbidities",
        "prior_treatment",
        "patient_goals",
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
