"""Schemas for MDT debate, adversarial review, and chair synthesis."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.schemas import StrictModel


Position = Literal["supports", "opposes", "conditional", "insufficient_information"]


class RoundContributionDraft(StrictModel):
    position: Position
    provisional_conclusion: str = Field(min_length=20, max_length=900)
    response_to_other_perspectives: str = Field(min_length=20, max_length=1600)
    agreements: list[str] = Field(default_factory=list, max_length=8)
    substantive_challenges: list[str] = Field(default_factory=list, max_length=8)
    position_changes: list[str] = Field(default_factory=list, max_length=5)
    remaining_unknowns: list[str] = Field(default_factory=list, max_length=8)
    risk_flags: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)


class SourceOpinionReview(StrictModel):
    source_id: str = Field(min_length=8, max_length=100)
    opinion_label: str = Field(min_length=4, max_length=120)
    option_status: Literal["preserved", "partly_preserved", "omitted", "unclear"]
    conditions_status: Literal["preserved", "partly_preserved", "omitted", "unclear"]
    review_basis: str = Field(min_length=20, max_length=600)
    source_reference_ids: list[str] = Field(min_length=2, max_length=8)
    evidence_peer_id: str = Field(default="", pattern=r"^(?:R2:[A-Z]{2}-[0-9]{2})?$")
    evidence_excerpt: str = Field(default="", max_length=180)
    challenge: str = Field(default="", max_length=700)

    @model_validator(mode="after")
    def require_attributed_case_and_peer_sources(self) -> "SourceOpinionReview":
        if self.source_id not in self.source_reference_ids:
            raise ValueError("source_reference_ids must include this review's attributed case source.")
        if not any(source_id.startswith("R2:") for source_id in self.source_reference_ids):
            raise ValueError("source_reference_ids must include an R2 peer source.")
        preservation_claimed = (
            self.option_status in {"preserved", "partly_preserved"}
            or self.conditions_status in {"preserved", "partly_preserved"}
        )
        if preservation_claimed and (
            not self.evidence_peer_id or len(self.evidence_excerpt.strip()) < 12
        ):
            raise ValueError(
                "A preserved or partly preserved element requires an exact R2 peer ID and verbatim supporting excerpt."
            )
        if self.evidence_peer_id and self.evidence_peer_id not in self.source_reference_ids:
            raise ValueError("evidence_peer_id must also appear in source_reference_ids.")
        if (
            self.option_status in {"partly_preserved", "omitted"}
            or self.conditions_status in {"partly_preserved", "omitted"}
        ) and not self.challenge.strip():
            raise ValueError("An omitted or partly preserved opinion requires a substantive challenge.")
        return self


class AdversarialContributionDraft(RoundContributionDraft):
    # Required even when empty: absence of review data must be explicit in R3.
    source_opinion_reviews: list[SourceOpinionReview] = Field(max_length=4)


class RoundContribution(StrictModel):
    agent_id: str = Field(pattern=r"^[A-Z]{2}-[0-9]{2}$")
    round_number: Literal[2, 3]
    position: Position
    provisional_conclusion: str = Field(min_length=20, max_length=900)
    response_to_other_perspectives: str = Field(min_length=20, max_length=1600)
    agreements: list[str] = Field(default_factory=list, max_length=8)
    substantive_challenges: list[str] = Field(default_factory=list, max_length=8)
    source_opinion_reviews: list[SourceOpinionReview] = Field(default_factory=list, max_length=4)
    position_changes: list[str] = Field(default_factory=list, max_length=5)
    remaining_unknowns: list[str] = Field(default_factory=list, max_length=8)
    risk_flags: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    case_data_integrity_flags: list[str] = Field(default_factory=list, max_length=20)
    # Deterministic orchestration metadata: exact peer records supplied to this role.
    source_peer_ids: list[str] = Field(default_factory=list, max_length=15)
    # Generated round-qualified references are audited against the actual prompt inputs.
    source_reference_integrity_flags: list[str] = Field(default_factory=list, max_length=20)
    safety_boundary: Literal["educational_simulation_only"] = "educational_simulation_only"
    not_a_treatment_instruction: Literal[True] = True


class FinalReportDraft(StrictModel):
    report_title: str = Field(min_length=5, max_length=180)
    consensus_status: Literal["consensus", "qualified_consensus", "no_consensus", "insufficient_information"]
    chair_conclusion: str = Field(min_length=30, max_length=1500)
    overall_educational_synthesis: str = Field(min_length=50, max_length=5000)
    consensus_points: list[str] = Field(default_factory=list, max_length=15)
    unresolved_disagreements: list[str] = Field(default_factory=list, max_length=15)
    minority_and_dissenting_views: list[str] = Field(default_factory=list, max_length=15)
    major_uncertainties: list[str] = Field(default_factory=list, max_length=20)
    missing_information_before_real_world_review: list[str] = Field(default_factory=list, max_length=20)
    patient_and_family_considerations: list[str] = Field(default_factory=list, max_length=15)
    feasibility_and_resource_considerations: list[str] = Field(default_factory=list, max_length=15)
    governance_and_safeguarding_considerations: list[str] = Field(default_factory=list, max_length=15)
    evidence_limitations: list[str] = Field(default_factory=list, max_length=15)
    chair_reflection: str = Field(min_length=30, max_length=1800)


class FinalMDTReport(StrictModel):
    run_id: str
    round_number: Literal[4] = 4
    report_title: str
    consensus_status: Literal["consensus", "qualified_consensus", "no_consensus", "insufficient_information"]
    chair_conclusion: str
    overall_educational_synthesis: str
    consensus_points: list[str]
    unresolved_disagreements: list[str]
    minority_and_dissenting_views: list[str]
    major_uncertainties: list[str]
    missing_information_before_real_world_review: list[str]
    patient_and_family_considerations: list[str]
    feasibility_and_resource_considerations: list[str]
    governance_and_safeguarding_considerations: list[str]
    evidence_limitations: list[str]
    chair_reflection: str
    case_data_integrity_flags: list[str] = Field(default_factory=list, max_length=20)
    evidence_retrieval_connected: Literal[False] = False
    safety_boundary: Literal["educational_simulation_only"] = "educational_simulation_only"
    not_a_treatment_instruction: Literal[True] = True
