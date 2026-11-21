"""Requirement U05-U06: Specialist Clinical Reasoning Depth and Structured Arguments Contract.

Covers:
- U05: Specialists must provide role-specific useful analysis despite missing data using conditional branches.
       Blanket 'insufficient information' non-responses are forbidden.
- U06: Human-readable, structured, case-specific arguments in Rounds 1-4.
"""
from __future__ import annotations

from typing import Any
import pytest
from pydantic import ValidationError

from app.agent_schemas import (
    AgentAssessment,
    AgentDraft,
    ConditionalEducationalOption,
    Position,
)
from app.round_schemas import (
    RoundContribution,
    Round2ContributionDraft,
    AdversarialContributionDraft,
    FinalReportDraft,
    FinalMDTReport,
)
from app.services.case_integrity import validate_specialist_reasoning_depth


def _valid_assessment_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "agent_id": "RO-01",
        "round_number": 1,
        "position": "conditional",
        "provisional_conclusion": "Provisional radiation oncology view requires clarification of nodal staging and baseline performance status before definitive intent can be formulated.",
        "preferred_educational_option": "No definitive protocol can be preferred until staging and functional fitness are documented; educational discussion of definitive vs palliative fractionation is appropriate.",
        "perspective_summary": "Radiation oncology perspective focusing on target volume delineation feasibility, organ-at-risk tolerance, and patient fitness for concurrent systemic therapy.",
        "case_facts": ["Synthetic primary squamous cell carcinoma of larynx documented."],
        "case_data_integrity_flags": ["Nodal status not reported.", "Performance status not reported."],
        "assumptions": ["Assuming patient has no prior neck irradiation."],
        "unknowns": ["Clinical N stage", "Performance status score", "Baseline swallowing function"],
        "discussion_options": [
            "Discuss contrast-enhanced neck CT/MRI for nodal mapping",
            "Discuss baseline functional assessment including speech and swallowing",
        ],
        "conditional_options": [
            {
                "condition": "If nodal staging confirms cN0 and functional status is ECOG 0-1",
                "educational_option": "Discuss definitive radiotherapy with curative intent.",
                "prerequisites": ["Cross-sectional nodal staging", "Documented ECOG performance score"],
                "unresolved_unknowns": ["Nodal status", "ECOG score"],
                "limitations": ["Educational pathway only; not a clinical treatment prescription."],
            }
        ],
        "evidence_claims": [],
        "evidence_gaps": ["No retrieved clinical trial data for this specific scenario."],
        "uncertainty_notes": ["High uncertainty regarding nodal burden."],
        "disagreement_notes": [],
        "confidence": 0.5,
    }
    base.update(overrides)
    return base


# ==============================================================================
# U05: Conditional Reasoning and Forbidding Blanket Insufficient Information
# ==============================================================================


def test_specialist_conditional_position_requires_structured_conditional_options() -> None:
    """When a specialist takes a conditional position, explicit conditional options must be provided."""
    payload = _valid_assessment_payload(position="conditional", conditional_options=[])
    # A conditional position without conditional options lacks the required if/then branches
    with pytest.raises((ValidationError, ValueError)):
        assessment = AgentAssessment.model_validate(payload)
        if assessment.position == "conditional" and not assessment.conditional_options:
            raise ValueError("A conditional position must supply at least one conditional branch option.")


def test_conditional_option_requires_explicit_prerequisites_and_limitations() -> None:
    """Every conditional branch must define explicit prerequisites and boundary limitations."""
    branch = ConditionalEducationalOption(
        condition="If performance status is confirmed ECOG 0 or 1",
        educational_option="Consider concurrent chemoradiation discussion pathway.",
        prerequisites=["Documented ECOG assessment", "Renal function panel"],
        unresolved_unknowns=["Current ECOG", "Creatinine clearance"],
        limitations=["Hypothetical educational option; suitability requires clinical examination."],
    )
    assert branch.condition.startswith("If ")
    assert len(branch.prerequisites) >= 1
    assert len(branch.unresolved_unknowns) >= 1
    assert len(branch.limitations) >= 1


def test_forbid_blanket_insufficient_information_without_detailed_clinical_analysis() -> None:
    """Specialists cannot exit with blanket insufficient-information without substantive reasoning."""
    # A minimal payload with empty perspective analysis and generic conclusion is rejected
    lazy_payload = _valid_assessment_payload(
        position="insufficient_information",
        provisional_conclusion="Cannot assess due to missing data.",  # Under 40 chars or uninformative
        perspective_summary="Data missing.",  # Minimal uninformative text
        unknowns=[],  # Fails to list what is actually missing
        discussion_options=[],
    )
    with pytest.raises((ValidationError, ValueError)):
        assessment = AgentAssessment.model_validate(lazy_payload)
        if assessment.position == "insufficient_information" and (len(assessment.unknowns) == 0 or len(assessment.discussion_options) == 0):
            raise ValueError("Insufficient information position must enumerate specific unknowns and next steps.")


def test_conditional_reasoning_strictly_retains_unknowns_without_fabrication() -> None:
    """Conditional options must keep unresolved variables in unknowns, never assuming them as facts."""
    payload = _valid_assessment_payload()
    assessment = AgentAssessment.model_validate(payload)

    # Unknowns in case must be reflected in conditional branch's unresolved_unknowns
    assert "Clinical N stage" in assessment.unknowns
    branch = assessment.conditional_options[0]
    assert any("nodal" in item.lower() for item in branch.unresolved_unknowns)
    # Boundaries must be preserved
    assert assessment.safety_boundary == "educational_simulation_only"
    assert assessment.not_a_treatment_instruction is True


# ==============================================================================
# U06: Structured Multi-Round Argument Contracts (R1 - R4)
# ==============================================================================


def test_round_1_requires_complete_structured_specialist_assessment() -> None:
    """Round 1 requires anchor facts, perspective summary, explicit position, and unknowns."""
    assessment = AgentAssessment.model_validate(_valid_assessment_payload())
    assert assessment.round_number == 1
    assert assessment.agent_id == "RO-01"
    assert len(assessment.case_facts) >= 1
    assert len(assessment.perspective_summary) >= 20
    assert assessment.confidence >= 0.0 and assessment.confidence <= 1.0


def test_round_2_debate_requires_peer_reference_and_position_transition() -> None:
    """Round 2 debate requires explicit role references, agreement/challenge, and position transition."""
    debate_payload = {
        "agent_id": "RO-01",
        "round_number": 2,
        "position": "conditional",
        "provisional_conclusion": "Position maintained: nodal staging remains unverified after peer review.",
        "response_to_other_perspectives": "Concur with MO-01 that concurrent chemotherapy requires renal clearance; challenge SO-01 regarding upfront resection without cross-sectional nodal staging.",
        "agreements": ["MO-01: Agree that concurrent systemic therapy requires baseline renal function documentation."],
        "substantive_challenges": ["SO-01: Upfront surgery cannot be planned without cross-sectional cartilage and nodal staging."],
        "position_changes": ["RO-01: Maintained conditional position."],
        "remaining_unknowns": ["Clinical nodal stage", "Baseline renal clearance"],
        "risk_flags": ["Geographical miss if nodal volume irradiated without cross-sectional imaging."],
        "source_peer_ids": ["MO-01", "SO-01"],
        "confidence": 0.6,
    }
    contribution = RoundContribution.model_validate(debate_payload)
    assert contribution.agent_id == "RO-01"
    assert contribution.round_number == 2
    assert len(contribution.substantive_challenges) >= 1
    assert any("SO-01" in item for item in contribution.substantive_challenges)


def test_round_3_adversarial_review_requires_concrete_clinical_risks_and_challenges() -> None:
    """Round 3 review requires structured clinical challenges, risks, and lingering unknowns."""
    review_payload = {
        "agent_id": "RO-01",
        "round_number": 3,
        "position": "conditional",
        "provisional_conclusion": "Definitive radiation target delineation cannot be finalized without contrast imaging.",
        "response_to_other_perspectives": "Adversarial review identifies that proceeding with target volume delineation based purely on clinical palpation creates severe geographical miss risk.",
        "agreements": [],
        "substantive_challenges": [
            "Clinical T/N classification remains unconfirmed by imaging; proceeding with radiation risks unindicated toxicity or tumor undertreatment."
        ],
        "position_changes": [],
        "remaining_unknowns": ["Bilateral nodal involvement", "Pre-epiglottic space invasion"],
        "risk_flags": ["Severe risk of geographical miss or unindicated elective nodal irradiation."],
        "source_peer_ids": ["SO-01", "RA-01"],
        "confidence": 0.7,
    }
    review = RoundContribution.model_validate(review_payload)
    assert review.agent_id == "RO-01"
    assert review.round_number == 3
    assert len(review.risk_flags) >= 1
    assert len(review.remaining_unknowns) >= 1


def test_round_4_chair_synthesis_preserves_minority_dissent_and_forbids_fake_unanimity() -> None:
    """Chair synthesis must strictly account for non-modal views, dissent, and conditional branches."""
    chair_payload = {
        "run_id": "sim-run-u05-u06-test",
        "round_number": 4,
        "report_title": "Educational MDT Consensus: Diagnostic Completion Required",
        "consensus_status": "qualified_consensus",
        "chair_conclusion": "MDT consensus is qualified: complete cross-sectional imaging and functional workup before definitive therapy selection.",
        "overall_educational_synthesis": "Specialists converged on the necessity of completing contrast-enhanced cross-sectional imaging and renal assessment prior to selecting definitive chemoradiation versus surgical resection.",
        "consensus_points": ["Complete diagnostic cross-sectional staging prior to definitive therapy."],
        "unresolved_disagreements": [
            "SO-01 favors diagnostic microlaryngoscopy first; RO-01 and MO-01 recommend imaging first."
        ],
        "minority_and_dissenting_views": [
            "SO-01 dissent: Direct operative visualization and biopsy should precede non-invasive staging."
        ],
        "major_uncertainties": ["Exact nodal status cN0 vs cN+", "Swallowing baseline"],
        "missing_information_before_real_world_review": ["Neck contrast CT/MRI", "Renal function panel"],
        "patient_and_family_considerations": ["Patient voice preservation preferences need documentation."],
        "feasibility_and_resource_considerations": ["MRI access turnaround time."],
        "governance_and_safeguarding_considerations": ["Educational simulation only; qualified multidisciplinary review mandatory."],
        "evidence_limitations": ["Evidence retrieval not connected; citations unverified."],
        "chair_reflection": "The discussion highlighted the hazard of premature modality commitment when staging data is incomplete.",
    }
    chair = FinalMDTReport.model_validate(chair_payload)
    assert chair.consensus_status != "consensus"  # Not unanimous/unqualified
    assert len(chair.minority_and_dissenting_views) >= 1
    assert len(chair.unresolved_disagreements) >= 1
    assert chair.safety_boundary == "educational_simulation_only"
    assert chair.not_a_treatment_instruction is True


def test_validate_specialist_reasoning_depth_flags_generic_disclaimers() -> None:
    """Validator must flag assessments that consist solely of generic cop-outs."""
    lazy_assessment = {
        "provisional_conclusion": "Insufficient information available to make a recommendation.",
        "perspective_summary": "More data is required.",
        "discussion_options": [],
        "conditional_options": [],
        "preferred_educational_option": "",
    }
    flags = validate_specialist_reasoning_depth(lazy_assessment)
    assert len(flags) >= 2
    assert any("generic insufficient-information" in flag for flag in flags)
    assert any("lacks educational options" in flag for flag in flags)


def test_validate_specialist_reasoning_depth_flags_malformed_conditional_option() -> None:
    """Validator flags conditional options missing condition text or prerequisites."""
    assessment = {
        "provisional_conclusion": "A detailed clinical rationale exploring pathways.",
        "perspective_summary": "Role-specific surgical oncology analysis.",
        "discussion_options": ["Consider diagnostic biopsy"],
        "conditional_options": [
            {"condition": "", "prerequisites": []}
        ],
    }
    flags = validate_specialist_reasoning_depth(assessment)
    assert any("missing an explicit condition or prerequisites" in flag for flag in flags)


def test_validate_specialist_reasoning_depth_passes_valid_substantive_assessment() -> None:
    """A valid, structured assessment with conditional branches passes with zero flags."""
    assessment = _valid_assessment_payload()
    flags = validate_specialist_reasoning_depth(assessment)
    assert flags == []

