import asyncio
import json

import pytest

from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.clinical_fields import CLINICAL_FIELD_REGISTRY_VERSION
from app.round_schemas import AdversarialContributionDraft, Round2ContributionDraft
from app.schemas import SyntheticCase
from app.services import mdt_generation, ollama
from app.services.case_integrity import build_case_prompt_context


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

def test_all_45_roles_receive_identical_canonical_context_in_rounds_2_and_3(monkeypatch):
    """R2 and R3 must share the exact same v2 case context for every configured role."""
    captured_prompts = []

    round_payload = {
        "position": "conditional",
        "provisional_conclusion": (
            "This role-specific educational position remains conditional; "
            "the supplied record does not establish a definitive conclusion."
        ),
        "response_to_other_perspectives": (
            "No peer contributions were supplied in this isolated contract test, "
            "so no peer agreement or disagreement is inferred."
        ),
        "agreements": [],
        "substantive_challenges": [],
        "position_changes": [],
        "remaining_unknowns": ["Clinical T and N are unknown; clinical M is not assessed."],
        "risk_flags": [],
        "confidence": 0.4,
    }

    async def fake_generate_structured(prompt, schema_type, max_tokens):
        captured_prompts.append({"round_schema": schema_type.__name__, "prompt": prompt})
        payload = dict(round_payload)
        if schema_type is Round2ContributionDraft:
            payload["source_opinion_responses"] = []
        elif schema_type is AdversarialContributionDraft:
            payload["source_opinion_reviews"] = []
        else:
            raise AssertionError(f"Unexpected schema requested: {schema_type.__name__}")
        return schema_type.model_validate(payload)

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate_structured)

    case = SyntheticCase(
        scenario_title="Synthetic all-role R2/R3 canonical-context regression",
        case_summary=(
            "Fictional educational case. Clinical T and N are unknown; "
            "clinical M has not been assessed."
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
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": (
            "The role-specific R1 educational assessment remains conditional "
            "because relevant details are not established in the supplied record."
        ),
        "preferred_educational_option": "No unconditional option is selected.",
        "case_data_integrity_flags": [],
    }
    own_r2 = {
        "position": "conditional",
        "provisional_conclusion": (
            "The role-specific R2 educational position remains conditional "
            "and does not establish a patient-specific indication."
        ),
        "response_to_other_perspectives": (
            "No peer contributions were supplied in this isolated contract test."
        ),
        "agreements": [],
        "substantive_challenges": [],
        "position_changes": [],
        "remaining_unknowns": [],
        "risk_flags": [],
        "case_data_integrity_flags": [],
        "source_opinion_responses": [],
        "source_reference_integrity_flags": [],
    }

    async def generate_both_rounds_for_all_roles():
        for profile in AGENT_PROFILES:
            await mdt_generation.generate_debate_contribution(
                profile, case, own_r1, peer_views=[]
            )
            await mdt_generation.generate_adversarial_contribution(
                profile, case, own_r1, own_r2, peer_debate_views=[]
            )

    asyncio.run(generate_both_rounds_for_all_roles())

    assert len(AGENT_PROFILES) == EXPECTED_AGENT_COUNT == 45
    assert len(captured_prompts) == EXPECTED_AGENT_COUNT * 2
    assert sum(item["round_schema"] == "Round2ContributionDraft" for item in captured_prompts) == 45
    assert sum(item["round_schema"] == "AdversarialContributionDraft" for item in captured_prompts) == 45

    expected_context = json.dumps(
        build_case_prompt_context(case),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    for item in captured_prompts:
        prompt = item["prompt"]
        assert expected_context in prompt

    assert all(
        item["prompt"].count(expected_context) == 1
        for item in captured_prompts
    )




@pytest.mark.parametrize("summary_state", ["INVALID", "CONFLICTING"])
def test_quarantined_case_summary_is_unassessable_for_r2_and_r3_source_reviews(
    monkeypatch, summary_state
):
    selected_summary = f"WITHHELD_SELECTED_SUMMARY_{summary_state}_SECRET"
    selected_excerpt = f"WITHHELD_SELECTED_EXCERPT_{summary_state}_SECRET"
    case_data = {
        "scenario_title": "Synthetic quarantined summary source-review regression",
        "case_summary": selected_summary,
        "clinical_field_states": {"case_summary": summary_state},
    }
    if summary_state == "CONFLICTING":
        case_data["clinical_field_provenance"] = {
            "case_summary": [{
                "source_type": "CASE_SUMMARY",
                "source_reference": "selected-summary-source",
                "source_excerpt": selected_excerpt,
            }]
        }
        case_data["clinical_field_conflicts"] = {
            "case_summary": [
                {
                    "raw_value": f"WITHHELD_CONFLICT_CANDIDATE_A_{summary_state}_SECRET",
                    "provenance": {
                        "source_type": "CLINICIAN_NOTE",
                        "source_reference": "summary-conflict-a",
                        "source_excerpt": "WITHHELD_CONFLICT_EXCERPT_A_SECRET",
                    },
                },
                {
                    "raw_value": f"WITHHELD_CONFLICT_CANDIDATE_B_{summary_state}_SECRET",
                    "provenance": {
                        "source_type": "MEDICAL_RECORD",
                        "source_reference": "summary-conflict-b",
                        "source_excerpt": "WITHHELD_CONFLICT_EXCERPT_B_SECRET",
                    },
                },
            ]
        }
    case = SyntheticCase(**case_data)
    original_case_json = case.model_dump_json()

    unregistered_source_id = "CASE:case_summary#99"
    unregistered_r2_analysis = (
        "A model-only source opinion is conditional on a fabricated prerequisite and "
        "has no server-identified case-summary source."
    )
    unregistered_r2_comparison = (
        "This fabricated source is not traceable to the case."
    )
    unregistered_r3_excerpt = "MODEL_ONLY_UNREGISTERED_CASE_EXCERPT_SECRET"
    captured_prompts = []

    async def fake_generate_structured(prompt, schema_type, max_tokens):
        captured_prompts.append((schema_type.__name__, prompt))
        payload = {
            "position": "conditional",
            "provisional_conclusion": (
                "The supplied synthetic information does not establish a definitive "
                "educational pathway, and unresolved information remains unknown."
            ),
            "response_to_other_perspectives": (
                "The contribution preserves the saved source limitations and does not "
                "assert an unsupported clinical fact or patient-specific decision."
            ),
            "agreements": [],
            "substantive_challenges": [],
            "position_changes": [],
            "remaining_unknowns": ["Case-summary attribution is unassessable."],
            "risk_flags": [],
            "confidence": 0.4,
        }
        if schema_type is Round2ContributionDraft:
            payload["source_opinion_responses"] = [{
                "source_id": unregistered_source_id,
                "position_on_source_opinion": "conditional",
                "analysis": unregistered_r2_analysis,
                "comparison": unregistered_r2_comparison,
            }]
        elif schema_type is AdversarialContributionDraft:
            payload["source_opinion_reviews"] = [{
                "source_id": unregistered_source_id,
                "source_excerpt": unregistered_r3_excerpt,
                "option_status": "unclear",
                "conditions_status": "unclear",
                "review_basis": "This model-reported source cannot be verified against an eligible case summary.",
                "source_reference_ids": [unregistered_source_id],
                "evidence_peer_id": "R2:RO-02",
                "evidence_excerpt": "This contribution preserves the saved source limitations.",
            }]
        else:
            raise AssertionError(f"Unexpected schema requested: {schema_type.__name__}")
        return schema_type.model_validate(payload)

    monkeypatch.setattr(
        mdt_generation, "_generate_structured", fake_generate_structured
    )

    profile = {
        "agent_id": "RO-01",
        "name": "Synthetic Radiation Oncology Role",
        "mandate": "Review only supplied synthetic information and preserve uncertainty.",
    }
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": (
            "The supplied information is incomplete and does not establish a definitive pathway."
        ),
        "preferred_educational_option": "No unconditional educational option is selected.",
        "case_data_integrity_flags": [],
    }

    async def run_quarantined_rounds():
        r2_result = await mdt_generation.generate_debate_contribution(
            profile, case, own_r1, peer_views=[]
        )
        peer_result = r2_result.model_dump()
        peer_result["agent_id"] = "RO-02"
        peer_result["source_opinion_responses"] = list(
            peer_result.get("source_opinion_responses") or []
        )
        peer = {
            "agent_id": "RO-02",
            "agent_name": "Synthetic Peer Role",
            "result": peer_result,
            "round1_case_integrity_flags": [],
        }
        r3_result = await mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, r2_result.model_dump(), peer_debate_views=[peer]
        )
        return r2_result, r3_result

    r2_result, r3_result = asyncio.run(run_quarantined_rounds())
    r2_prompt = next(
        prompt for schema_name, prompt in captured_prompts
        if schema_name == "Round2ContributionDraft"
    )
    r3_prompt = next(
        prompt for schema_name, prompt in captured_prompts
        if schema_name == "AdversarialContributionDraft"
    )

    assert "CASE SUMMARY WITHHELD" in r2_prompt
    assert "unassessable, not that no opinions exist" in r2_prompt
    assert "First inspect the verbatim case summary" not in r2_prompt
    assert "Inspect the eligible verbatim case summary" not in r2_prompt
    assert "WITHHELD / UNASSESSABLE" in r2_prompt
    assert selected_summary not in r2_prompt
    assert selected_excerpt not in r2_prompt
    assert unregistered_source_id in " ".join(r2_result.source_reference_integrity_flags)
    assert r2_result.source_opinion_responses[0].source_excerpt == ""

    assert "CASE SUMMARY WITHHELD" in r3_prompt
    assert "unassessable, not that no attributed opinions exist" in r3_prompt
    assert "Do not treat R2 source-opinion responses as substitutes" in r3_prompt
    assert "Treat the verbatim case summary as attributed" not in r3_prompt
    assert "Review only distinct attributed opinions" not in r3_prompt
    assert '"round2_source_opinion_responses":[]' in r3_prompt
    assert '"source_opinion_responses":[]' in r3_prompt
    assert selected_summary not in r3_prompt
    assert selected_excerpt not in r3_prompt
    assert unregistered_r3_excerpt not in r3_prompt

    assert r3_result.source_opinion_reviews == []
    assert len(r3_result.model_reported_source_opinion_reviews) == 1
    assert r3_result.model_reported_source_opinion_reviews[0]["source_id"] == unregistered_source_id
    assert (
        r3_result.model_reported_source_opinion_reviews[0]["source_excerpt"]
        == unregistered_r3_excerpt
    )
    assert any(
        "server-owned attributed-opinion register is empty" in flag
        for flag in r3_result.source_reference_integrity_flags
    )
    assert case.model_dump_json() == original_case_json


def test_r2_and_r3_attributed_source_opinion_register_labels_are_round_scoped(monkeypatch):
    source_excerpt = (
        "The colorectal surgical note favours a surgery-led assessment first, "
        "conditional on complete local staging and resectability review"
    )
    case = SyntheticCase(
        scenario_title="Synthetic R2/R3 register label-scope regression",
        case_summary=(
            source_excerpt
            + ". The fictional record does not supply the prerequisite investigations "
            "or establish a final pathway."
        ),
    )
    captured_prompts = []

    async def fake_generate_structured(prompt, schema_type, max_tokens):
        captured_prompts.append((schema_type.__name__, prompt))
        payload = {
            "position": "conditional",
            "provisional_conclusion": (
                "The supplied fictional information does not establish a definitive pathway."
            ),
            "response_to_other_perspectives": (
                "The contribution preserves the source option and its stated conditions "
                "without asserting that any prerequisite is fulfilled."
            ),
            "agreements": [],
            "substantive_challenges": [],
            "position_changes": [],
            "remaining_unknowns": ["The stated prerequisites remain unverified in this fictional record."],
            "risk_flags": [],
            "confidence": 0.4,
        }
        if schema_type is Round2ContributionDraft:
            payload["source_opinion_responses"] = [{
                "source_id": "CASE:case_summary#1",
                "position_on_source_opinion": "conditional",
                "analysis": (
                    source_excerpt
                    + "; this is a source-reported conditional option, not a verified fact."
                ),
                "comparison": (
                    "The option remains conditional; suitability is not established."
                ),
            }]
        elif schema_type is AdversarialContributionDraft:
            payload["source_opinion_reviews"] = [{
                "source_id": "CASE:case_summary#1",
                "source_excerpt": source_excerpt,
                "option_status": "preserved",
                "conditions_status": "preserved",
                "review_basis": (
                    "The supplied peer R2 source-specific response retains the option and condition."
                ),
                "source_reference_ids": ["CASE:case_summary#1", "R2:RO-02"],
                "evidence_peer_id": "R2:RO-02",
                "evidence_excerpt": source_excerpt,
            }]
        else:
            raise AssertionError(f"Unexpected schema requested: {schema_type.__name__}")
        return schema_type.model_validate(payload)

    monkeypatch.setattr(
        mdt_generation, "_generate_structured", fake_generate_structured
    )

    profile = {
        "agent_id": "RO-01",
        "name": "Synthetic Radiation Oncology Role",
        "mandate": "Review only supplied synthetic information and preserve uncertainty.",
    }
    peer_profile = {
        "agent_id": "RO-02",
        "name": "Synthetic Peer Role",
        "mandate": "Review only supplied synthetic information and preserve uncertainty.",
    }
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": (
            "The supplied information does not establish a definitive educational pathway."
        ),
        "preferred_educational_option": (
            "No unconditional educational option is selected from this incomplete record."
        ),
        "case_data_integrity_flags": [],
    }

    async def run_rounds():
        own_r2 = await mdt_generation.generate_debate_contribution(
            profile, case, own_r1, peer_views=[]
        )
        peer_r2 = await mdt_generation.generate_debate_contribution(
            peer_profile, case, own_r1, peer_views=[]
        )
        peer = {
            "agent_id": "RO-02",
            "agent_name": "Synthetic Peer Role",
            "result": peer_r2.model_dump(),
            "round1_case_integrity_flags": [],
        }
        r3 = await mdt_generation.generate_adversarial_contribution(
            profile,
            case,
            own_r1,
            own_r2.model_dump(),
            peer_debate_views=[peer],
        )
        return r3

    asyncio.run(run_rounds())
    r2_prompt = next(
        prompt for schema_name, prompt in captured_prompts
        if schema_name == "Round2ContributionDraft"
    )
    r3_prompt = next(
        prompt for schema_name, prompt in captured_prompts
        if schema_name == "AdversarialContributionDraft"
    )

    r2_register_label = (
        "SERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS (exact case-summary excerpts; "
        "source statements, not verified facts or your endorsement)"
    )
    r3_register_label = (
        "SERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS "
        "(exact case-summary excerpts; not verified facts)."
    )

    assert r2_prompt.count(r2_register_label) == 1
    assert r3_register_label not in r2_prompt
    assert r3_prompt.count(r3_register_label) == 1
    assert r2_register_label not in r3_prompt
    assert source_excerpt in r2_prompt
    assert source_excerpt in r3_prompt
