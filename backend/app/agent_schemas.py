"""Structured and safety-bounded contracts for simulated agent assessments."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator

from app.schemas import StrictModel


EvidenceMaturity = Literal[
    "established_standard",
    "emerging",
    "investigational",
    "uncertain",
]

SourceKind = Literal[
    "guideline",
    "systematic_review",
    "randomized_trial",
    "observational_study",
    "trial_registry",
    "government_or_agency",
    "other",
]


class EvidenceSource(StrictModel):
    source_id: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=500)
    organization: str | None = Field(default=None, max_length=200)
    source_kind: SourceKind
    published_or_updated: date | None = None
    url: AnyHttpUrl | None = None
    identifier: str | None = Field(default=None, max_length=160)
    locator: str | None = Field(default=None, max_length=500)
    applicability_and_limitations: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def require_traceable_locator(self) -> "EvidenceSource":
        if self.url is None and not self.identifier:
            raise ValueError("An evidence source needs a URL or stable identifier.")
        return self


class EvidenceClaim(StrictModel):
    claim_text: str = Field(min_length=5, max_length=2000)
    evidence_maturity: EvidenceMaturity
    sources: list[EvidenceSource] = Field(min_length=1, max_length=12)


Position = Literal["supports", "opposes", "conditional", "insufficient_information"]


class ConditionalEducationalOption(StrictModel):
    """One explicitly hypothetical pathway with its prerequisites and limitations."""

    condition: str = Field(
        min_length=8,
        max_length=500,
        description="A clearly hypothetical condition; never present it as an established patient fact.",
    )
    educational_option: str = Field(
        min_length=5,
        max_length=700,
        description="A role-relevant educational option for discussion, not a treatment instruction.",
    )
    prerequisites: list[str] = Field(
        min_length=1,
        max_length=6,
        description="Information, assessments, or prerequisites needed before the option could be considered.",
    )
    unresolved_unknowns: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Decision-relevant variables that remain unknown in the supplied case.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Boundaries on interpretation; do not imply eligibility, suitability, or guideline verification.",
    )


class AgentDraft(StrictModel):
    """Model-generated content only; identity and safety fields are added by the server."""

    position: Position
    provisional_conclusion: str = Field(min_length=20, max_length=1500)
    preferred_educational_option: str = Field(min_length=5, max_length=2500)
    perspective_summary: str = Field(min_length=10, max_length=3500)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    unknowns: list[str] = Field(default_factory=list, max_length=20)
    discussion_options: list[str] = Field(default_factory=list, max_length=12)
    conditional_options: list[ConditionalEducationalOption] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Optional explicitly hypothetical, role-relevant branches. Use [] when no defensible "
            "conditional option can be grounded in the supplied case and remit."
        ),
    )
    evidence_gaps: list[str] = Field(default_factory=list, max_length=15)
    uncertainty_notes: list[str] = Field(default_factory=list, max_length=15)
    disagreement_notes: list[str] = Field(default_factory=list, max_length=15)
    confidence: float = Field(ge=0.0, le=1.0)


class AgentAssessment(StrictModel):
    """An educational perspective; explicitly not a patient-care instruction."""

    agent_id: str = Field(pattern=r"^[A-Z]{2}-[0-9]{2}$")
    round_number: int = Field(ge=1, le=4)
    position: Position
    provisional_conclusion: str = Field(min_length=20, max_length=1500)
    preferred_educational_option: str = Field(min_length=5, max_length=2500)
    perspective_summary: str = Field(min_length=10, max_length=3500)
    case_facts: list[str] = Field(default_factory=list, max_length=25)
    case_data_integrity_flags: list[str] = Field(default_factory=list, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    unknowns: list[str] = Field(default_factory=list, max_length=20)
    discussion_options: list[str] = Field(default_factory=list, max_length=12)
    conditional_options: list[ConditionalEducationalOption] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Structured hypothetical options with explicit conditions, prerequisites, unresolved "
            "unknowns, and limitations. These are not confirmed patient facts or treatment instructions."
        ),
    )
    evidence_claims: list[EvidenceClaim] = Field(default_factory=list, max_length=30)
    evidence_gaps: list[str] = Field(default_factory=list, max_length=15)
    uncertainty_notes: list[str] = Field(default_factory=list, max_length=15)
    disagreement_notes: list[str] = Field(default_factory=list, max_length=15)
    confidence: float = Field(ge=0.0, le=1.0)
    safety_boundary: Literal["educational_simulation_only"] = "educational_simulation_only"
    not_a_treatment_instruction: Literal[True] = True
