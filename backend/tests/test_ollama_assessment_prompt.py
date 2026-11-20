import asyncio
import json

from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.clinical_fields import CLINICAL_FIELD_REGISTRY_VERSION
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
    assert "evidence retrieval is not connected" in request["system"]
    assert assessment.conditional_options[0].condition == branch["condition"]
    assert assessment.conditional_options[0].unresolved_unknowns == branch["unresolved_unknowns"]
    assert assessment.case_facts

def test_all_45_specialist_roles_receive_identical_v2_canonical_case_context(monkeypatch):
    """Every R1 role receives the same immutable canonical case projection."""
    captured_requests = []

    draft = {
        "position": "insufficient_information",
        "provisional_conclusion": (
            "The supplied information does not establish a complete clinical stage, "
            "so this role-specific educational assessment remains limited."
        ),
        "preferred_educational_option": "No option is selected from the incomplete supplied record.",
        "perspective_summary": (
            "This role assesses only its assigned specialty remit and preserves "
            "the supplied unknown and not-assessed states."
        ),
        "assumptions": [],
        "unknowns": [
            "Clinical T stage is unknown.",
            "Clinical N stage is unknown.",
            "Clinical M stage has not been assessed.",
        ],
        "discussion_options": ["Identify the missing staging information for review."],
        "conditional_options": [],
        "evidence_gaps": ["No evidence retrieval is connected."],
        "uncertainty_notes": ["The record does not establish a complete stage."],
        "disagreement_notes": [],
        "confidence": 0.3,
    }

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
            captured_requests.append({"path": path, "request": json})
            return FakeResponse()

    monkeypatch.setattr(ollama.httpx, "AsyncClient", FakeAsyncClient)

    case = SyntheticCase(
        scenario_title="Synthetic all-role canonical-context regression",
        case_summary=(
            "Fictional educational case. Age and primary site are user-supplied. "
            "Clinical T and N are unknown; clinical M has not been assessed."
        ),
        age_years=64,
        primary_site="Larynx",
        histology="Squamous cell carcinoma",
        clinical_field_states={
            "clinical_t_stage": "UNKNOWN",
            "clinical_n_stage": "UNKNOWN",
            "clinical_m_stage": "NOT_ASSESSED",
        },
    )

    async def generate_for_all_roles():
        for profile in AGENT_PROFILES:
            await ollama.generate_agent_assessment(profile, case, 1)

    asyncio.run(generate_for_all_roles())

    assert len(AGENT_PROFILES) == EXPECTED_AGENT_COUNT == 45
    assert len(captured_requests) == EXPECTED_AGENT_COUNT
    assert all(item["path"] == "/api/generate" for item in captured_requests)

    marker = "Fictional case JSON:\n"
    ending = "\nReturn one concise JSON object."
    canonical_contexts = []
    for item in captured_requests:
        prompt = item["request"]["prompt"]
        assert marker in prompt
        assert ending in prompt
        encoded_context = prompt.split(marker, 1)[1].split(ending, 1)[0]
        canonical_contexts.append(json.loads(encoded_context))

    # Role instructions differ, but the canonical facts/context must not.
    canonical_json = [
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for context in canonical_contexts
    ]
    assert len(set(canonical_json)) == 1

    context = canonical_contexts[0]
    assert context["clinical_field_registry_version"] == CLINICAL_FIELD_REGISTRY_VERSION
    assert context["clinical_field_registry_version"] == "2.0.0"
    assert context["canonical_field_values"]["clinical_t_stage"]["state"] == "UNKNOWN"
    assert context["canonical_field_values"]["clinical_n_stage"]["state"] == "UNKNOWN"
    assert context["canonical_field_values"]["clinical_m_stage"]["state"] == "NOT_ASSESSED"
    assert context["canonical_field_values"]["clinical_t_stage"]["canonical_comparison_value"] is None
    assert context["canonical_field_values"]["clinical_n_stage"]["canonical_comparison_value"] is None
    assert context["canonical_field_values"]["clinical_m_stage"]["canonical_comparison_value"] is None
    assert context["canonical_field_values"]["age_years"]["state"] == "PRESENT"
    assert context["canonical_field_values"]["age_years"]["provenance"][0][
        "verification_status"
    ] == "user_supplied_not_independently_verified"
    assert context["case_snapshot"]["case_summary"] == case.case_summary
    assert context["case_snapshot"]["age_years"] == 64

