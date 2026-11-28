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


def test_ro01_and_ro02_enforce_grammar_non_repetition_and_no_fabricated_stage(monkeypatch):
    draft = {
        "position": "supports",
        "provisional_conclusion": "Placeholder conclusion.",
        "preferred_educational_option": "Placeholder option.",
        "perspective_summary": "Placeholder summary.",
        "assumptions": [],
        "unknowns": ["HPV/p16 status is not supplied."],
        "discussion_options": [],
        "conditional_options": [],
        "evidence_gaps": [],
        "uncertainty_notes": [],
        "disagreement_notes": [],
        "confidence": 0.8,
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
            return FakeResponse()

    monkeypatch.setattr(ollama.httpx, "AsyncClient", FakeAsyncClient)
    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsil",
        case_summary="2x1 cm growth in right tonsillar fossa.",
        age_years=50,
        sex_at_birth="Male",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        relevant_comorbidities=["T2DM & Hypertension"],
    )

    ro01_profile = {
        "agent_id": "RO-01",
        "name": "Guideline-focused Radiation Oncologist",
        "mandate": "Synthesize multi-society guidelines.",
    }
    ro01 = asyncio.run(ollama.generate_agent_assessment(ro01_profile, case, 1))
    assert ro01.preferred_educational_option.startswith("For this 50-year-old male with ")
    assert "suggest like.." not in ro01.preferred_educational_option
    assert "who is a " not in ro01.preferred_educational_option
    assert "considering all these" not in ro01.preferred_educational_option
    assert "cT1N1M0" not in ro01.preferred_educational_option
    assert "cT1N1M0" not in ro01.provisional_conclusion
    assert ro01.perspective_summary != ro01.preferred_educational_option

    ro02_profile = {
        "agent_id": "RO-02",
        "name": "Conservative & Time-Tested Radiation Oncologist",
        "mandate": "Recommend conservative radiotherapy.",
    }
    captured_ro02 = {}

    class CapturingAsyncClient(FakeAsyncClient):
        async def post(self, path, json=None):
            captured_ro02["request"] = json
            return FakeResponse()

    monkeypatch.setattr(ollama.httpx, "AsyncClient", CapturingAsyncClient)
    draft["provisional_conclusion"] = "Conventional 3D-CRT avoids unproven IMRT low-dose bath risks."
    draft["preferred_educational_option"] = (
        "Deliver conventional 3D-CRT 60-66 Gy at 2.0 Gy/fraction while questioning steep-gradient IMRT marginal-miss hazards [source_id: PMID-99999999]."
    )
    draft["perspective_summary"] = draft["preferred_educational_option"]

    from app.services import evidence_retrieval

    class FakeEngine:
        def retrieve_evidence_for_role(self, role_id, case_obj, limit=3):
            if role_id == "RO-02":
                return [
                    evidence_retrieval.RetrievedPassage(
                        source_id="PMID-99999999",
                        title="Conventional 3D-CRT vs IMRT late toxicity tradeoffs (Radiother Oncol, 2023)",
                        domain="peer_reviewed_journal",
                        snippet="Conventional fields remain reliable where steep gradients risk marginal miss.",
                        evidence_type="review",
                        url="https://pubmed.ncbi.nlm.nih.gov/99999999/",
                        organization="Radiotherapy and Oncology",
                    )
                ]
            return []

        def format_prompt_injection(self, passages):
            return "\n".join(f"[{p.source_id}] {p.title}: {p.snippet}" for p in passages)

    monkeypatch.setattr(evidence_retrieval, "get_evidence_retrieval_engine", lambda: FakeEngine())
    ro02 = asyncio.run(ollama.generate_agent_assessment(ro02_profile, case, 1))
    assert "PubMed" in captured_ro02["request"]["prompt"]
    assert "question" in captured_ro02["request"]["prompt"].lower()
    assert ro02.preferred_educational_option == draft["preferred_educational_option"]
    assert ro02.perspective_summary != ro02.preferred_educational_option
    assert any(c.sources[0].source_id == "PMID-99999999" for c in ro02.evidence_claims)


def test_ro02_evidence_retrieval_combines_dataset_and_pubmed(monkeypatch):
    from app.services import evidence_retrieval
    from app.services import online_guideline_procurement

    def fake_query_europe_pmc(self, query, limit=5):
        return [
            {
                "pmid": "12345678",
                "title": "Critical appraisal of IMRT vs conventional 3D-CRT late toxicity",
                "journalTitle": "Int J Radiat Oncol Biol Phys",
                "pubYear": "2024",
                "abstractText": "Evaluates low-dose bath and marginal miss cons of newer IMRT compared with 3D-CRT.",
            }
        ]

    monkeypatch.setattr(
        online_guideline_procurement.OnlineGuidelineProcurementService,
        "query_europe_pmc",
        fake_query_europe_pmc,
    )
    engine = evidence_retrieval.get_evidence_retrieval_engine()
    case = SyntheticCase(
        scenario_title="Ca oropharynx",
        case_summary="2x1 cm growth in right tonsil.",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
    )
    passages = engine.retrieve_evidence_for_role("RO-02", case, limit=6)
    source_ids = [p.source_id for p in passages]
    assert "PMID-12345678" in source_ids
    assert any(sid != "PMID-12345678" for sid in source_ids)


