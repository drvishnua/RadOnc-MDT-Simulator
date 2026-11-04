import pytest
from pydantic import ValidationError

from app.agent_schemas import AgentAssessment


def test_assessment_accepts_only_education_bounded_cited_claims() -> None:
    assessment = AgentAssessment.model_validate(
        {
            "agent_id": "RO-01",
            "round_number": 1,
            "perspective_summary": "This is a simulated educational perspective for a synthetic case.",
            "case_facts": ["Synthetic pathology summary supplied."],
            "assumptions": ["No additional clinical facts are assumed."],
            "unknowns": ["Additional staging details are not supplied."],
            "discussion_options": ["Discuss what additional information would be needed."],
            "evidence_claims": [
                {
                    "claim_text": "Example evidence statement for schema testing only.",
                    "evidence_maturity": "uncertain",
                    "sources": [
                        {
                            "source_id": "TEST-SOURCE-001",
                            "title": "Synthetic reference used only for schema testing",
                            "source_kind": "other",
                            "identifier": "TEST-SOURCE-001",
                            "applicability_and_limitations": "Not a real clinical reference; validation fixture only.",
                        }
                    ],
                }
            ],
            "evidence_gaps": ["No real source was retrieved for this test."],
            "uncertainty_notes": ["This fixture does not assess clinical validity."],
            "disagreement_notes": [],
            "confidence": 0.4,
        }
    )
    assert assessment.safety_boundary == "educational_simulation_only"
    assert assessment.not_a_treatment_instruction is True
    assert assessment.evidence_claims[0].sources[0].identifier == "TEST-SOURCE-001"


def test_evidence_claim_without_citation_is_rejected() -> None:
    payload = {
        "agent_id": "RO-01",
        "round_number": 1,
        "perspective_summary": "This is a simulated educational perspective for a synthetic case.",
        "confidence": 0.4,
        "evidence_claims": [
            {
                "claim_text": "An unsupported evidence statement.",
                "evidence_maturity": "emerging",
                "sources": [],
            }
        ],
    }
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate(payload)


def test_agent_assessment_cannot_be_marked_as_treatment_instruction() -> None:
    payload = {
        "agent_id": "RO-01",
        "round_number": 1,
        "perspective_summary": "This is a simulated educational perspective for a synthetic case.",
        "confidence": 0.4,
        "not_a_treatment_instruction": False,
    }
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate(payload)
