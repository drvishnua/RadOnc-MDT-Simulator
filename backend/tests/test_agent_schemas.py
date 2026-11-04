import pytest
from pydantic import ValidationError

from app.agent_schemas import AgentAssessment


def _valid_payload():
    return {
        "agent_id": "RO-01",
        "round_number": 1,
        "position": "conditional",
        "provisional_conclusion": "A provisional educational position is conditional because key staging and fitness details are missing.",
        "preferred_educational_option": "No option can be preferred until the missing staging and fitness information is clarified.",
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


def test_assessment_requires_explicit_position_and_conclusion() -> None:
    assessment = AgentAssessment.model_validate(_valid_payload())
    assert assessment.position == "conditional"
    assert "provisional educational position" in assessment.provisional_conclusion
    assert assessment.safety_boundary == "educational_simulation_only"
    assert assessment.not_a_treatment_instruction is True
    assert assessment.evidence_claims[0].sources[0].identifier == "TEST-SOURCE-001"


def test_evidence_claim_without_citation_is_rejected() -> None:
    payload = _valid_payload()
    payload["evidence_claims"] = [
        {
            "claim_text": "An unsupported evidence statement.",
            "evidence_maturity": "emerging",
            "sources": [],
        }
    ]
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate(payload)


def test_assessment_without_provisional_conclusion_is_rejected() -> None:
    payload = _valid_payload()
    payload.pop("provisional_conclusion")
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate(payload)


def test_agent_assessment_cannot_be_marked_as_treatment_instruction() -> None:
    payload = _valid_payload()
    payload["not_a_treatment_instruction"] = False
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate(payload)
