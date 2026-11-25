import asyncio
import json

from app.schemas import SyntheticCase
from app.services import ollama


def test_r1_prompt_requires_fact_use_and_explicit_hypothetical_branches(monkeypatch):
    branch = {
        "condition": "If a documented functional assessment supports further pathway discussion",
        "educational_option": "Consider the role-relevant pathway as an educational discussion option.",
        "prerequisites": ["Documented functional assessment"],
        "unresolved_unknowns": ["Current functional status is not supplied."],
        "limitations": ["Hypothetical only; this does not establish eligibility or a treatment choice."],
    }
    draft = {
        "position": "conditional",
        "provisional_conclusion": (
            "The supplied case facts support a role-specific preliminary assessment, "
            "but a definitive pathway selection remains unresolved."
        ),
        "preferred_educational_option": "No unconditional option is selected from the current record.",
        "perspective_summary": "This role assesses only the questions within its stated remit.",
        "assumptions": [],
        "unknowns": ["Current functional status is not supplied."],
        "discussion_options": ["Review the missing functional assessment."],
        "conditional_options": [branch],
        "evidence_gaps": ["No evidence retrieval is connected."],
        "uncertainty_notes": ["The branch is hypothetical and is not a statement about this case."],
        "disagreement_notes": [],
        "confidence": 0.4,
    }
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": json.dumps(draft)}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, path, json=None):
            captured["path"] = path
            captured["request"] = json
            return FakeResponse()

    monkeypatch.setattr(ollama.httpx, "AsyncClient", FakeAsyncClient)
    case = SyntheticCase(
        scenario_title="Synthetic R1 conditional-reasoning test",
        case_summary=(
            "Fictional case. Histology is documented as squamous cell carcinoma. "
            "Functional status is not supplied."
        ),
        age_years=64,
        primary_site="Larynx",
        histology="Squamous cell carcinoma",
    )
    profile = {
        "agent_id": "RO-01",
        "name": "Guideline-focused Radiation Oncologist",
        "mandate": "Assess radiotherapy considerations and evidence gaps within this role's remit.",
    }

    assessment = asyncio.run(ollama.generate_agent_assessment(profile, case, 1))

    request = captured["request"]
    assert captured["path"] == "/api/generate"
    assert request["format"]["properties"]["conditional_options"]["type"] == "array"
    assert profile["mandate"] in request["prompt"]
    assert "Do not use a generic" in request["system"]
    assert "condition must not be presented as true or met" in request["system"]
    assert (
        "evidence retrieval is not connected" in request["system"]
        or "Verified evidence retrieval is active" in request["system"]
    )
    assert assessment.conditional_options[0].condition == branch["condition"]
    assert assessment.conditional_options[0].unresolved_unknowns == branch["unresolved_unknowns"]
    assert assessment.case_facts


