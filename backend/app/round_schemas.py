"""Schemas for MDT debate, adversarial review, and chair synthesis."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

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


class Round2SourceOpinionResponseDraft(StrictModel):
    source_id: str = Field(min_length=8, max_length=100)
    analysis: str = Field(
        min_length=20,
        max_length=700,
        description=(
            "Address this attributed opinion separately. Retain its distinct option and every "
            "stated prerequisite, then explain how it relates to your own R1 position and the "
            "selected peer views. Missing prerequisites remain unknown; do not imply suitability."
        ),
    )
    comparison: str = Field(
        min_length=10,
        max_length=400,
        description="Concise comparison with the role's own R1 position and the selected R1 peers.",
    )


class Round2ContributionDraft(RoundContributionDraft):
    # Required even when empty: models must explicitly return [] when no attributed opinions exist.
    source_opinion_responses: list[Round2SourceOpinionResponseDraft] = Field(max_length=4)


class Round2SourceOpinionResponse(Round2SourceOpinionResponseDraft):
    source_excerpt: str = Field(
        default="",
        max_length=400,
        description="Exact case-summary excerpt bound by the server using source_id; never model-authored.",
    )


class SourceOpinionReview(StrictModel):
    # Keep model-authored content parseable even when its provenance is incomplete.
    # Semantic requirements are checked deterministically after parsing and persisted
    # as source_reference_integrity_flags; a weak review must not erase the whole role.
    source_id: str = Field(min_length=8, max_length=100)
    opinion_label: str = Field(default="", max_length=120)
    source_excerpt: str = Field(
        default="",
        max_length=400,
        description=(
            "Server-bound exact contiguous excerpt from the original case_summary. The server "
            "attaches this immutable source text using source_id after model output validation; "
            "it is not model-authored."
        ),
    )
    option_status: Literal["preserved", "partly_preserved", "omitted", "unclear"] = Field(
        description=(
            "Representation fidelity only: whether the attributed option is faithfully retained "
            "in the actual supplied Round-2 contribution text. This does not assess clinical "
            "appropriateness, eligibility, or whether case prerequisites are fulfilled. A conditional "
            "option remains represented when its option and conditional wording are retained, even "
            "if the required MRI, staging, fitness, or other case information is missing. If Round 2 "
            "names the option and then says it cannot be assessed, selected, or acted on until a "
            "prerequisite is known, the option is still preserved in the text; do not label it omitted "
            "solely because it is not actionable. Use omitted only when supplied Round-2 text itself "
            "drops or materially distorts the option; use unclear when the supplied material is "
            "insufficient to assess."
        )
    )
    conditions_status: Literal["preserved", "partly_preserved", "omitted", "unclear"] = Field(
        description=(
            "Representation fidelity only: whether the prerequisite/condition attached to the "
            "attributed opinion is faithfully retained in the actual supplied Round-2 text. Do not "
            "confuse representation with fulfilment: an unknown or unmet clinical prerequisite is "
            "not an omission if Round 2 retains the condition, even when the peer says the option "
            "cannot yet be assessed or acted on. Use omitted only when the supplied Round-2 text "
            "itself drops or materially changes the condition."
        )
    )
    review_basis: str = Field(
        default="",
        max_length=600,
        description=(
            "Explain the comparison between the attributed source opinion and the supplied Round-2 "
            "text. Separate representation fidelity from missing/unfulfilled case prerequisites; "
            "do not infer clinical appropriateness."
        ),
    )
    source_reference_ids: list[str] = Field(default_factory=list, max_length=8)
    evidence_peer_id: str = Field(default="", max_length=100)
    evidence_excerpt: str = Field(default="", max_length=180)
    model_reported_evidence_excerpt: str = Field(default="", max_length=180, description="Original model-authored quote retained for audit; the server binds evidence_excerpt to supplied peer text.")
    evidence_excerpt_binding_method: Literal["exact_model_quote", "server_bound_contiguous_match", "server_selected_source_match", "missing", "invalid"] = Field(default="missing", description="Server-computed excerpt binding method. server_selected_source_match means the server selected an exact contiguous passage from the chosen peer's unique structured response for the same CASE source ID; it does not validate semantic interpretation or clinical correctness.")
    evidence_validation_status: Literal["verified", "invalid", "missing"] = Field(
        default="missing",
        description="Server-computed result of checking evidence_peer_id and evidence_excerpt against the exact R2 peer material supplied to this role. Model-authored values are ignored.",
    )
    model_reported_option_status: str = Field(
        default="",
        max_length=40,
        description="Server-preserved original model label for audit; do not author this field.",
    )
    model_reported_conditions_status: str = Field(
        default="",
        max_length=40,
        description="Server-preserved original model label for audit; do not author this field.",
    )
    model_reported_source_reference_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="Server-preserved original model references for audit; do not author this field.",
    )
    challenge: str = Field(
        default="",
        max_length=700,
        description=(
            "Source-linked challenge only when supplied Round-2 text actually omits, weakens, "
            "conflates, or materially distorts the attributed option or condition. Do not create "
            "a challenge solely because a clinical prerequisite is missing or unknown in the case."
        ),
    )


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
    source_opinion_responses: list[Round2SourceOpinionResponse] = Field(default_factory=list, max_length=4)
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
    recorded_agreements: list[str] = Field(default_factory=list, max_length=90)
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
