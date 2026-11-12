import asyncio
import json

from fastapi.testclient import TestClient

from app.agent_schemas import AgentAssessment
from app.main import app
from app.round_schemas import FinalMDTReport, FinalReportDraft, RoundContribution
from app.schemas import SyntheticCase
from app.services import batch_runner, mdt_rounds, run_store
from app.services.mdt_generation import reconcile_chair_report_draft
from app.services.ollama import AgentGenerationError

client = TestClient(app)


def _case_payload():
    return {
        "scenario_title": "Synthetic MDT round test",
        "case_summary": "A fictional oncology case used only to validate multi-round orchestration.",
        "age_years": 64,
        "primary_site": "Larynx",
        "histology": "Squamous cell carcinoma",
    }


def _assessment(profile, case, round_number):
    return AgentAssessment(
        agent_id=profile["agent_id"],
        round_number=round_number,
        position="conditional",
        provisional_conclusion="A provisional educational conclusion is conditional because several case details remain unknown.",
        preferred_educational_option="No option can be preferred until the missing details are clarified.",
        perspective_summary=f"Independent synthetic-case perspective from {profile['name']}.",
        confidence=0.5,
        evidence_gaps=["No evidence retrieval is connected in this test."],
    )


def _round_contribution(profile, case, own, peers, round_number):
    return RoundContribution(
        agent_id=profile["agent_id"],
        round_number=round_number,
        position="conditional",
        provisional_conclusion="The position remains conditional after consideration of the other simulated perspectives.",
        response_to_other_perspectives="This role acknowledges relevant shared concerns and challenges unsupported assumptions.",
        agreements=["The case has important missing information."],
        substantive_challenges=["The available synthetic data do not support a definitive conclusion."],
        remaining_unknowns=["Additional staging and functional details remain unknown."],
        risk_flags=["Do not treat this educational output as clinical advice."],
        confidence=0.5,
    )


def _final_report(run_id, case, round1, round2, round3):
    return FinalMDTReport(
        run_id=run_id,
        report_title="Synthetic MDT educational synthesis",
        consensus_status="insufficient_information",
        chair_conclusion="The simulated MDT position remains conditional because the available synthetic facts are insufficient to resolve the outstanding disagreements and uncertainties.",
        overall_educational_synthesis="This simulated synthesis preserves the conditional nature of the positions and identifies missing information rather than presenting a treatment directive.",
        consensus_points=["All roles identified missing case information."],
        unresolved_disagreements=["No treatment approach can be resolved from the supplied synthetic data alone."],
        minority_and_dissenting_views=["The individual role assessments should remain available for review."],
        major_uncertainties=["Clinical details remain incomplete."],
        missing_information_before_real_world_review=["Formal staging and functional assessment are not supplied."],
        patient_and_family_considerations=["Patient preferences must be obtained rather than inferred."],
        feasibility_and_resource_considerations=["Local resources and access must be verified."],
        governance_and_safeguarding_considerations=["Consent and documentation would require review in a real setting."],
        evidence_limitations=["Evidence retrieval is not connected."],
        chair_reflection="The chair records an educational synthesis only and does not issue a clinical recommendation.",
    )


def _create_complete_round1(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "mdt_rounds.sqlite3")

    async def fake_assess(profile, case, round_number, max_tokens=1100):
        return _assessment(profile, case, round_number)

    monkeypatch.setattr(batch_runner, "generate_agent_assessment", fake_assess)
    response = client.post("/api/runs", json={"case": _case_payload()})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    assert client.get(f"/api/runs/{run_id}").json()["completed_count"] == 45

    # A fresh dashboard mount must be able to retrieve saved R1 progress and contributions.
    r1_summary = client.get(f"/api/runs/{run_id}").json()
    r1_results_response = client.get(f"/api/runs/{run_id}/results")
    assert r1_summary["completed_count"] == 45
    assert r1_summary["progress_percent"] == 100.0
    assert r1_results_response.status_code == 200
    r1_results = r1_results_response.json()["results"]
    assert len(r1_results) == 45
    assert all(item["status"] == "completed" and item["assessment"] is not None for item in r1_results)
    return run_id


def test_four_rounds_require_full_previous_round_and_preserve_all_roles(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)

    async def fake_debate(profile, case, own, peers):
        assert peers
        assert "position" in own
        return _round_contribution(profile, case, own, peers, 2)

    async def fake_adversarial(profile, case, own, debate, peers):
        assert peers
        assert debate["position"] == "conditional"
        return _round_contribution(profile, case, own, peers, 3)

    async def fake_chair(run_id_arg, case, round1, round2, round3):
        assert run_id_arg == run_id
        assert len(round1) == len(round2) == len(round3) == 45
        return _final_report(run_id_arg, case, round1, round2, round3)

    monkeypatch.setattr(mdt_rounds, "generate_debate_contribution", fake_debate)
    monkeypatch.setattr(mdt_rounds, "generate_adversarial_contribution", fake_adversarial)
    monkeypatch.setattr(mdt_rounds, "generate_chair_report", fake_chair)

    r2 = client.post(f"/api/runs/{run_id}/rounds/2")
    assert r2.status_code == 200
    r2_summary = client.get(f"/api/runs/{run_id}/rounds/2").json()
    assert r2_summary["status"] == "completed"
    assert r2_summary["completed_count"] == 45
    # Re-fetch after the round has finished, as the frontend does after a refresh.
    r2_results_response = client.get(f"/api/runs/{run_id}/rounds/2/results")
    assert r2_results_response.status_code == 200
    r2_results = r2_results_response.json()["results"]
    assert len(r2_results) == 45
    assert all(item["status"] == "completed" and item["result"]["position"] == "conditional" for item in r2_results)

    r3 = client.post(f"/api/runs/{run_id}/rounds/3")
    assert r3.status_code == 200
    r3_summary = client.get(f"/api/runs/{run_id}/rounds/3").json()
    assert r3_summary["status"] == "completed"
    assert r3_summary["completed_count"] == 45
    r3_results_response = client.get(f"/api/runs/{run_id}/rounds/3/results")
    assert r3_results_response.status_code == 200
    r3_results = r3_results_response.json()["results"]
    assert len(r3_results) == 45
    assert all(item["status"] == "completed" and item["result"]["position"] == "conditional" for item in r3_results)

    r4 = client.post(f"/api/runs/{run_id}/rounds/4")
    assert r4.status_code == 200

    # The Chair record and report must survive a second independent retrieval.
    r4_summary_response = client.get(f"/api/runs/{run_id}/rounds/4")
    r4_results_response = client.get(f"/api/runs/{run_id}/rounds/4/results")
    assert r4_summary_response.status_code == 200
    assert r4_summary_response.json()["status"] == "completed"
    assert r4_results_response.status_code == 200
    r4_results = r4_results_response.json()["results"]
    assert len(r4_results) == 1
    assert r4_results[0]["agent_id"] == "SG-07"
    assert r4_results[0]["status"] == "completed"
    assert r4_results[0]["result"]["report_title"] == "MDT Chair Synthesis: Larynx — Squamous cell carcinoma"

    report = client.get(f"/api/runs/{run_id}/report")
    reloaded_report = client.get(f"/api/runs/{run_id}/report")
    assert report.status_code == 200
    assert reloaded_report.status_code == 200
    assert report.json() == reloaded_report.json()
    assert report.json()["not_a_treatment_instruction"] is True
    assert report.json()["evidence_retrieval_connected"] is False
    assert report.json()["report_title"] == "MDT Chair Synthesis: Larynx — Squamous cell carcinoma"

    # The complete four-round route must rebuild the report from saved role rows,
    # not reuse the fake/model-authored report's consensus point or omit discussion.
    saved_report = report.json()
    agreements = saved_report["recorded_agreements"]
    assert len(agreements) == 90
    assert sum(item.startswith("Round 2 —") for item in agreements) == 45
    assert sum(item.startswith("Round 3 —") for item in agreements) == 45
    assert all("not independently validated as a shared proposition" in item for item in agreements)
    assert saved_report["consensus_points"] == []
    assert saved_report["consensus_status"] == "insufficient_information"
    assert "unanimously" not in saved_report["chair_conclusion"].casefold()
    assert any(
        "Additional staging and functional details remain unknown." in item
        for item in saved_report["major_uncertainties"]
    )
    assert any(
        "Additional staging and functional details remain unknown." in item
        for item in saved_report["missing_information_before_real_world_review"]
    )


def test_retried_or_failed_round_record_cannot_retain_stale_payload(monkeypatch, tmp_path):
    import json
    from app.agents.catalog import AGENT_PROFILES

    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "stale_round_payload.sqlite3")
    case = SyntheticCase(
        scenario_title="Synthetic stale-payload test",
        case_summary="Fictional case used to validate failed-record cleanup.",
    )
    run = run_store.create_run(case)
    for profile in AGENT_PROFILES:
        run_store.save_agent_success(
            run["run_id"],
            profile["agent_id"],
            json.dumps({"position": "insufficient_information"}),
            0.01,
        )

    run_store.create_round_job(run["run_id"], 2)
    stale = json.dumps({"position": "supports", "provisional_conclusion": "STALE"})
    run_store.save_round_success(run["run_id"], 2, "RO-01", stale, 0.01)
    run_store.mark_round_agent_running(run["run_id"], 2, "RO-01")
    row = next(item for item in run_store.list_round_results(run["run_id"], 2) if item["agent_id"] == "RO-01")
    assert row["status"] == "running"
    assert row["result"] is None
    assert row["duration_seconds"] is None

    run_store.save_round_success(run["run_id"], 2, "RO-01", stale, 0.01)
    run_store.save_round_failure(run["run_id"], 2, "RO-01", "intentional test failure", 0.01)
    row = next(item for item in run_store.list_round_results(run["run_id"], 2) if item["agent_id"] == "RO-01")
    assert row["status"] == "failed"
    assert row["result"] is None


def test_round_cannot_start_before_all_45_independent_assessments(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "incomplete.sqlite3")
    run_store.initialize_database()
    # Create an incomplete run directly; its 45 agent rows remain queued.
    from app.schemas import SyntheticCase
    case = SyntheticCase(
        scenario_title="Synthetic incomplete test",
        case_summary="Fictional case with an incomplete first round for validation.",
    )
    run = run_store.create_run(case)
    response = client.post(f"/api/runs/{run['run_id']}/rounds/2")
    assert response.status_code == 409


def test_round_three_cannot_start_until_round_two_is_complete(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)
    response = client.post(f"/api/runs/{run_id}/rounds/3")
    assert response.status_code == 409


def test_final_report_not_found_before_chair_synthesis(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)
    response = client.get(f"/api/runs/{run_id}/report")
    assert response.status_code == 404

 

def test_chair_retry_uses_higher_output_budget():
    budgets = []

    async def fake_generate(*args, max_tokens=1600):
        budgets.append(max_tokens)
        if len(budgets) == 1:
            raise AgentGenerationError("intentional chair JSON failure")
        return "valid"

    result = asyncio.run(
        mdt_rounds._with_one_schema_retry(
            fake_generate,
            "synthetic",
            retry_max_tokens=2200,
        )
    )
    assert result == "valid"
    assert budgets == [1600, 2200]


def _chair_rows(field, positions):
    rows = []
    for index, position in enumerate(positions, start=1):
        agent_id = "PP-05" if position == "conditional" else f"RO-{index:02d}"
        payload = {
            "position": position,
            "provisional_conclusion": (
                "Treatment hesitation remains plausible but cannot be confirmed without more information."
                if position == "conditional"
                else "A definitive treatment recommendation cannot be made from the missing clinical information."
            ),
            "unknowns": ["Clinical stage and functional status are not supplied."],
            "remaining_unknowns": ["Patient goals and preferences are not supplied."],
            "evidence_gaps": ["Evidence retrieval is not connected."],
            "agreements": [],
            "risk_flags": ["Do not make a treatment recommendation from incomplete synthetic data."],
        }
        rows.append({
            "agent_id": agent_id,
            "agent_name": "Treatment-averse Perspective" if position == "conditional" else f"Role {index}",
            "status": "completed",
            field: payload,
        })
    return rows


def _chair_draft():
    return FinalReportDraft(
        report_title="Synthetic Chair report",
        consensus_status="consensus",
        chair_conclusion="All roles unanimously agreed to one treatment approach despite missing information.",
        overall_educational_synthesis="All agents unanimously identified the same position and no dissent was present.",
        chair_reflection="The model draft contains enough text to satisfy the output schema.",
    )


def test_peer_selection_excludes_failed_or_running_records():
    from app.agents.catalog import AGENT_PROFILES

    current = next(item for item in AGENT_PROFILES if item["agent_id"] == "RO-01")
    completed_peer = next(item for item in AGENT_PROFILES if item["agent_id"] == "RO-02")
    failed_peer = next(item for item in AGENT_PROFILES if item["agent_id"] == "MO-01")
    rows = [
        {
            "agent_id": current["agent_id"], "agent_name": current["name"],
            "status": "completed", "result": {"position": "insufficient_information"},
        },
        {
            "agent_id": completed_peer["agent_id"], "agent_name": completed_peer["name"],
            "status": "completed", "result": {"position": "conditional"},
        },
        {
            "agent_id": failed_peer["agent_id"], "agent_name": failed_peer["name"],
            "status": "failed", "result": {"position": "supports"},
        },
    ]

    selected = mdt_rounds._select_peer_views(current, rows, "result")

    assert [item["agent_id"] for item in selected] == ["RO-02"]


def test_r2_and_r3_prompts_require_source_linked_peer_engagement(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, Round2ContributionDraft, RoundContributionDraft
    from app.services import mdt_generation

    prompts = []

    async def fake_generate(prompt, schema_type, max_tokens):
        prompts.append(prompt)
        draft_fields = dict(
            position="conditional",
            provisional_conclusion="The educational position remains conditional because source information is incomplete.",
            response_to_other_perspectives="The reviewed peer material was considered by source ID; no unsupported agreement is inferred.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Complete staging remains unknown."],
            risk_flags=["Do not infer stage from incomplete data."],
            confidence=0.5,
        )
        if schema_type is AdversarialContributionDraft:
            return AdversarialContributionDraft(**draft_fields, source_opinion_reviews=[])
        if schema_type is Round2ContributionDraft:
            return Round2ContributionDraft(
                **draft_fields,
                source_opinion_responses=[
                    {
                        "source_id": "CASE:case_summary#1",
                        "analysis": "A specialist assessment first remains the distinct option, conditional on complete staging.",
                        "comparison": "This differs from a generic no-pathway conclusion in the selected R1 views.",
                    },
                    {
                        "source_id": "CASE:case_summary#2",
                        "analysis": "A separate preoperative sequence is conditional on MRI review and documented fitness.",
                        "comparison": "This remains distinct from the specialist assessment option in the selected R1 view.",
                    },
                ],
            )
        raise AssertionError(f"Unexpected generation schema: {schema_type.__name__}")

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review educational radiotherapy considerations."}
    case = SyntheticCase(
        scenario_title="Synthetic attributed-opinion case",
        case_summary=(
            "Fictional case. Neurology service note proposes a specialist assessment first, conditional on "
            "complete staging. Cardiology service note proposes a separate preoperative sequence, conditional "
            "on MRI review and documented fitness."
        ),
    )
    own = {
        "position": "conditional",
        "provisional_conclusion": "The source case contains competing conditional opinions.",
        "preferred_educational_option": "No option until prerequisites are reviewed.",
    }
    peer_r1 = [{
        "agent_id": "SO-01", "agent_name": "Surgical Oncology",
        "assessment": {
            "position": "conditional",
            "provisional_conclusion": "Surgical assessment first, conditional on complete local staging.",
            "preferred_educational_option": "Surgery-led assessment.",
            "disagreement_notes": ["Do not proceed without local staging."],
            "unknowns": ["MRI is unknown; citation R1:ZZ-99 must be ignored."],
        },
    }]
    r2_result = asyncio.run(mdt_generation.generate_debate_contribution(profile, case, own, peer_r1))
    assert [item.source_id for item in r2_result.source_opinion_responses] == [
        "CASE:case_summary#1",
        "CASE:case_summary#2",
    ]
    assert all(item.source_excerpt for item in r2_result.source_opinion_responses)
    assert not r2_result.source_reference_integrity_flags
    assert "R1:SO-01" in prompts[0]
    assert "ALLOWED ROUND SOURCE IDS: R1:RO-01, R1:SO-01" in prompts[0]
    assert "Never cite a role range, role band" in prompts[0]
    assert "[embedded reference omitted]" in prompts[0]
    assert "R1:ZZ-99" not in prompts[0]
    assert "Surgery-led assessment" in prompts[0]
    assert "Record an agreement only when" in prompts[0]
    assert "bounded sample of at most 15 of 44 other roles" in prompts[0]
    assert "Shared uncertainty about prerequisites" in prompts[0]
    assert "surgery-first/surgical-assessment" in prompts[0]
    assert "Agreement that information is missing does not establish agreement on an option" in prompts[0]
    assert "SERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS" in prompts[0]
    assert "CASE:case_summary#1" in prompts[0]
    assert "Missing prerequisites mean suitability is unknown" in prompts[0]
    assert "return exactly one item in the required source_opinion_responses array" in prompts[0]
    assert "source_opinion_responses" in prompts[0]
    # Prompt section boundaries must be actual newlines, not literal backslash-n text.
    assert "conditionality; do not convert conditional positions into support.\nROLE:" in prompts[0]

    own_r2 = {
        "position": "conditional",
        "provisional_conclusion": "The debate retains conditionality.",
        "response_to_other_perspectives": "The surgical assessment and multimodality options remain distinct.",
        "agreements": ["Both pathways require completion of missing investigations."],
        "substantive_challenges": ["CASE:case_summary — do not collapse the two conditional options."],
        "position_changes": ["Round 1 → Round 2: insufficient_information → conditional."],
        "remaining_unknowns": ["MRI and distant staging remain unknown."],
        "risk_flags": ["Do not infer resectability."],
    }
    peer_r2 = [{
        "agent_id": "MO-01", "agent_name": "Medical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "Preoperative multimodality discussion, conditional on MRI and fitness.",
            "response_to_other_perspectives": "The source condition is not yet met.",
            "agreements": [],
            "substantive_challenges": ["R1:SO-01 — local staging prerequisite remains unresolved; R2:DS-02 was also cited inside this R2 text."],
            "risk_flags": ["Do not assume resectability."],
        },
    }]
    asyncio.run(mdt_generation.generate_adversarial_contribution(profile, case, own, own_r2, peer_r2))
    assert "R2:MO-01" in prompts[1]
    assert "local staging prerequisite remains unresolved" in prompts[1]
    assert "make a source-linked challenge naming CASE:case_summary" in prompts[1]
    assert "Risk flags are not substitutes" in prompts[1]
    assert "YOUR R1 AND COMPLETE OWN R2 RECORD" in prompts[1]
    assert "The surgical assessment and multimodality options remain distinct" in prompts[1]
    assert "CASE:case_summary — do not collapse the two conditional options" in prompts[1]
    assert "bounded sample of at most 5 of 44 other roles" in prompts[1]
    assert "never relabel an R2 peer as R1" in prompts[1]
    assert "When discussing your own R2 record, cite it as R2:RO-01" in prompts[1]
    assert "The only R1 source you may cite in this round is R1:RO-01" in prompts[1]
    assert "REPRESENTATION FIDELITY ONLY" in prompts[1]
    assert (
        "Missing or undocumented case prerequisites are case unknowns; do not describe their "
        "status as unfulfilled without an explicit assessed finding"
    ) in prompts[1]
    assert "not an assessment of clinical appropriateness" in prompts[1].casefold()
    assert "If no peer record permits a reliable assessment, use unclear" in prompts[1]
    assert "[embedded round ref; cite R2]" not in prompts[1]
    assert "R1:SO-01" not in prompts[1]
    assert "R2:DS-02" not in prompts[1]
    assert "R2:MO-01" in prompts[1]
    assert "R1:RO-01 through R1:SV-02" not in prompts[1]
    assert "local staging prerequisite remains unresolved" in prompts[1]
    assert '"round1_source":"R1:RO-01"' in prompts[1]
    assert "Never cite role ranges" in prompts[1]
    assert "Cite only individual source IDs listed under ALLOWED ROUND SOURCE IDS" in prompts[1]
    assert "source_opinion_reviews" in prompts[1]
    assert "source_reference_ids" in prompts[1]
    assert "exact CASE source ID and one exact R2:AGENT_ID from the supplied" in prompts[1]
    assert "CASE:case_summary#N" in prompts[1]
    assert "Do not assume a fixed number of opinions" in prompts[1]
    assert "CASE ATTRIBUTION CHECK" in prompts[1]
    assert "server has identified explicitly attributed note opinions" in prompts[1]
    assert "SERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS" in prompts[1]
    assert "Neurology service note proposes a specialist assessment first, conditional on complete staging." in prompts[1]
    assert "Cardiology service note proposes a separate preoperative sequence, conditional on MRI review and documented fitness." in prompts[1]
    assert "source_excerpt is server-bound metadata" in prompts[1]
    assert "attaches the exact original case_summary excerpt by source_id" in prompts[1]
    assert "For MDT-006" not in prompts[1]
    assert "colorectal surgical note" not in prompts[1]
    assert "medical oncology note" not in prompts[1]
    assert "ALLOWED ROUND SOURCE IDS" in prompts[1]
    assert "\nROLE: Radiation Oncology\nMANDATE:" in prompts[1]
    assert "\nSUPPLIED CASE:\n{" in prompts[1]


def test_chair_reconciliation_preserves_saved_round_challenges_as_unresolved():
    case = SyntheticCase(
        scenario_title="Synthetic source challenge test",
        case_summary="Fictional case for source-linked challenge preservation.",
    )
    round1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    round2 = _chair_rows("result", ["insufficient_information"] * 45)
    round3 = _chair_rows("result", ["insufficient_information"] * 45)
    round2[0]["result"]["substantive_challenges"] = [
        "R1:SO-01 — the proposed sequence remains conditional on local staging."
    ]
    round3[1]["result"]["substantive_challenges"] = [
        "R2:MO-01 — MRI and fitness prerequisites are not documented."
    ]
    report = reconcile_chair_report_draft(
        "synthetic-source-challenges", case, round1, round2, round3, _chair_draft()
    )
    joined = " ".join(report.unresolved_disagreements)
    assert "Round 2 recorded challenge —" in joined
    assert "Round 3 recorded challenge —" in joined
    assert "R1:SO-01" in joined
    assert "R2:MO-01" in joined


def test_chair_source_opinion_coverage_is_dynamic_and_counts_distinct_roles():
    case_summary = (
        "Fictional case. Neurology service note proposes specialist assessment, conditional on MRI. "
        "Cardiology service note proposes a separate review, conditional on documented fitness. "
        "Psychology service note records a preference-sensitive discussion, conditional on patient goals."
    )
    case = SyntheticCase(
        scenario_title="Synthetic dynamic source opinion coverage",
        case_summary=case_summary,
    )
    round1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    round2 = _chair_rows("result", ["insufficient_information"] * 45)
    round3 = _chair_rows("result", ["insufficient_information"] * 45)

    neurology_excerpt = "Neurology service note proposes specialist assessment, conditional on MRI."
    cardiology_excerpt = "Cardiology service note proposes a separate review, conditional on documented fitness."
    psychology_excerpt = "Psychology service note records a preference-sensitive discussion, conditional on patient goals."

    def review(source_id, label, excerpt, option_status, conditions_status, peer_id):
        return {
            "source_id": source_id,
            "opinion_label": label,
            "source_excerpt": excerpt,
            "option_status": option_status,
            "conditions_status": conditions_status,
            "source_reference_ids": [source_id, f"R2:{peer_id}"],
            "evidence_peer_id": f"R2:{peer_id}",
            "evidence_excerpt": "Exact peer excerpt retained by test fixture.",
            "evidence_validation_status": "verified",
        }

    round3[0]["result"]["source_peer_ids"] = ["RO-10"]
    round3[0]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#1", "Neurology service note", neurology_excerpt, "omitted", "preserved", "RO-10"),
        # Conflicting duplicate from the same role must not be counted as a second role.
        review("CASE:case_summary#1", "Neurology service note", neurology_excerpt, "preserved", "preserved", "RO-10"),
        review("CASE:case_summary#2", "Cardiology service note", cardiology_excerpt, "unclear", "unclear", "RO-10"),
    ]
    round3[1]["result"]["source_peer_ids"] = ["RO-11"]
    round3[1]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#1", "Neurology service note", neurology_excerpt, "omitted", "preserved", "RO-11"),
    ]
    round3[2]["result"]["source_peer_ids"] = ["RO-12"]
    round3[2]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#1", "Neurology service note", neurology_excerpt, "preserved", "partly_preserved", "RO-12"),
        review("CASE:case_summary#3", "Psychology service note", psychology_excerpt, "preserved", "preserved", "RO-12"),
    ]

    report = reconcile_chair_report_draft(
        "synthetic-dynamic-source-coverage",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )
    joined = " ".join(report.unresolved_disagreements)

    assert "CASE:case_summary#1" in joined
    assert "CASE:case_summary#2" in joined
    assert "CASE:case_summary#3" in joined
    assert "Neurology service note" in joined
    assert "Cardiology service note" in joined
    assert "Psychology service note" in joined
    assert "distinct roles" in joined
    assert "RO-01" in joined and "conflicting duplicate-role reviews excluded" in joined
    assert "colorectal surgical note" not in joined
    assert "medical oncology note" not in joined


def test_chair_preserves_round_two_and_round_three_agreements_and_unknowns_without_calling_them_consensus():
    case = SyntheticCase(
        scenario_title="Chair preserves discussion records",
        case_summary="Fictional case used only to test attributed MDT discussion records.",
    )
    positions = ["insufficient_information"] * 45
    round1 = _chair_rows("assessment", positions)
    round2 = _chair_rows("result", positions)
    round3 = _chair_rows("result", positions)

    repeated = "The source records require further staging clarification."
    round2[0]["result"]["agreements"] = [repeated, repeated]
    round2[1]["result"]["agreements"] = [
        "The treatment-sequence options must remain distinct until their prerequisites are reviewed."
    ]
    round3[2]["result"]["agreements"] = [
        "The adversarial review records a shared concern about missing patient goals."
    ]
    round2[0]["result"]["remaining_unknowns"] = [
        "R2-only unresolved question: the date of the staging investigation is not supplied."
    ]

    report = reconcile_chair_report_draft(
        "chair-agreement-traceability",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    assert report.consensus_points == []
    assert any(
        "Round 2 — RO-01" in item and repeated in item
        and "not independently validated as a shared proposition" in item
        for item in report.recorded_agreements
    )
    assert sum("Round 2 — RO-01" in item for item in report.recorded_agreements) == 1
    assert any("Round 2 — RO-02" in item for item in report.recorded_agreements)
    assert any("Round 3 — RO-03" in item for item in report.recorded_agreements)
    assert any("R2-only unresolved question" in item for item in report.major_uncertainties)
    assert any("R2-only unresolved question" in item for item in report.missing_information_before_real_world_review)


def test_chair_prompt_samples_each_position_when_round_three_counts_are_tied(monkeypatch):
    from app.services import mdt_generation

    prompts = []

    async def fake_generate(prompt, schema_type, max_tokens):
        prompts.append(prompt)
        return _chair_draft()

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    case = SyntheticCase(
        scenario_title="Chair tied position prompt sample",
        case_summary="Fictional case used only to test balanced source sampling.",
    )
    round1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    round2 = _chair_rows("result", ["insufficient_information"] * 45)
    round3 = _chair_rows(
        "result",
        ["supports"] * 22 + ["opposes"] * 22 + ["insufficient_information"],
    )

    asyncio.run(
        mdt_generation.generate_chair_report(
            "chair-tied-digest", case, round1, round2, round3
        )
    )

    assert "software will retain saved Round-2 and Round-3 agreement statements separately" in prompts[0]
    assert "do not add extra JSON fields" in prompts[0]
    assert "recorded_agreements" not in prompts[0]

    digest_text = prompts[0].split("ROUND 3 ADVERSARIAL REVIEW:\n", 1)[1].split(
        "\nReturn a balanced synthesis.", 1
    )[0]
    digest = json.loads(digest_text)
    sampled = digest["non_modal_views"]
    sampled_agents = {item["agent"] for item in sampled}
    sampled_positions = {item["position"] for item in sampled}
    assert {"RO-01", "RO-23", "RO-45"}.issubset(sampled_agents)
    assert {"supports", "opposes", "insufficient_information"}.issubset(sampled_positions)


def test_chair_reconciliation_preserves_position_counts_and_minor_view():
    case = SyntheticCase(
        scenario_title="Synthetic reconciliation test",
        case_summary="Fictional case for validating source-grounded Chair reconciliation.",
        known_unknowns=["Clinical stage is not supplied.", "Patient goals are not supplied."],
        social_context=["Family support difficulties are recorded."],
        resource_context=[],
    )
    positions = ["insufficient_information"] * 44 + ["conditional"]
    report = reconcile_chair_report_draft(
        "synthetic-run",
        case,
        _chair_rows("assessment", positions),
        _chair_rows("result", positions),
        _chair_rows("result", positions),
        _chair_draft(),
    )

    assert report.consensus_status == "insufficient_information"
    assert "44/45 insufficient-information" in report.overall_educational_synthesis
    assert "1/45 conditional" in report.overall_educational_synthesis
    assert "unanimously" not in report.overall_educational_synthesis.casefold()
    assert report.minority_and_dissenting_views
    assert report.consensus_points == []
    assert any("No proposition-level consensus" in item for item in report.unresolved_disagreements)
    assert any("PP-05" in item and "conditional" in item for item in report.minority_and_dissenting_views)
    assert report.major_uncertainties
    assert report.missing_information_before_real_world_review
    assert report.patient_and_family_considerations
    assert report.feasibility_and_resource_considerations
    assert report.governance_and_safeguarding_considerations
    assert report.evidence_limitations


def test_chair_reconciliation_marks_support_opposition_split_as_no_consensus():
    case = SyntheticCase(
        scenario_title="Synthetic disagreement test",
        case_summary="Fictional case for validating position disagreement handling.",
    )
    round1 = _chair_rows("assessment", ["conditional"] * 45)
    round2 = _chair_rows("result", ["conditional"] * 45)
    round3 = _chair_rows("result", ["supports"] * 44 + ["opposes"])
    report = reconcile_chair_report_draft(
        "synthetic-disagreement",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    assert report.consensus_status == "no_consensus"
    assert any("supports" in item and "opposes" in item for item in report.unresolved_disagreements)


def test_uniform_support_labels_with_conflicting_options_are_not_consensus():
    case = SyntheticCase(
        scenario_title="Synthetic conflicting-options test",
        case_summary="Fictional case used only to test consensus proposition safeguards.",
    )
    round1 = _chair_rows("assessment", ["supports"] * 45)
    for index, row in enumerate(round1):
        row["assessment"]["preferred_educational_option"] = (
            "Educational option A: compare a surgery-led pathway."
            if index < 22
            else "Educational option B: compare a non-surgical pathway."
        )
    round2 = _chair_rows("result", ["supports"] * 45)
    round3 = _chair_rows("result", ["supports"] * 45)

    report = reconcile_chair_report_draft(
        "synthetic-conflicting-options",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    assert report.consensus_status == "insufficient_information"
    assert "shared, proposition-level" in " ".join(report.unresolved_disagreements)
    assert report.consensus_points == []
    assert report.chair_conclusion.startswith("No treatment recommendation can be made")



def test_chair_reconciliation_preserves_all_groups_when_round3_top_positions_tie():
    case = SyntheticCase(
        scenario_title="Synthetic tied-position test",
        case_summary="Fictional case used only to verify tied position labels are not arbitrarily ranked.",
    )
    positions = ["supports"] * 22 + ["opposes"] * 22 + ["insufficient_information"]
    round1 = _chair_rows("assessment", positions)
    round2 = _chair_rows("result", positions)
    round3 = _chair_rows("result", positions)

    report = reconcile_chair_report_draft(
        "synthetic-tied-positions",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    expected_roles = {
        row["agent_id"]
        for row in round3
        if row["result"]["position"] in {"supports", "opposes"}
    }
    visible_history = " ".join(report.minority_and_dissenting_views)
    assert all(agent_id in visible_history for agent_id in expected_roles)
    assert "RO-45" not in visible_history
    assert "no unique modal position" in " ".join(report.unresolved_disagreements).casefold()
    assert report.consensus_status == "no_consensus"


def test_round_finish_updates_parent_run_timestamp(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)
    run_store.create_round_job(run_id, 2)
    expected = "2099-01-01T00:00:00+00:00"
    monkeypatch.setattr(run_store, "_now", lambda: expected)
    run_store.mark_round_finished(run_id, 2)
    assert run_store.get_run(run_id)["updated_at"] == expected



def test_repeated_agreement_from_one_role_does_not_meet_cross_role_threshold():
    case = SyntheticCase(
        scenario_title="Synthetic repeated-agreement test",
        case_summary="Fictional case for validating distinct-role agreement counting.",
    )
    round1 = _chair_rows("assessment", ["supports"] * 45)
    round2 = _chair_rows("result", ["supports"] * 45)
    round3 = _chair_rows("result", ["supports"] * 45)

    repeated_statement = "The same educational concern is recorded."
    round2[0]["result"]["agreements"] = [repeated_statement] * 12

    report = reconcile_chair_report_draft(
        "synthetic-repeated-agreement",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    assert not any(
        item.startswith("Repeated Round-2 statement")
        for item in report.consensus_points
    )
    assert report.consensus_points == []
    assert any("No proposition-level consensus" in item for item in report.unresolved_disagreements)



def test_chair_preserves_competing_source_opinions_verbatim_with_conditions():
    case = SyntheticCase(
        scenario_title="Synthetic competing opinions",
        case_summary=(
            "Fictional scenario. The referral includes two provisional opinions: the "
            "colorectal surgical note favours proceeding to a surgical assessment first, "
            "conditional on complete local staging and resectability review; the medical "
            "oncology note favours discussing a preoperative multimodality sequence, "
            "conditional on MRI staging, metastatic work-up and fitness assessment."
        ),
    )
    round1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    round2 = _chair_rows("result", ["insufficient_information"] * 45)
    round3 = _chair_rows("result", ["insufficient_information"] * 45)
    report = reconcile_chair_report_draft(
        "synthetic-competing-source-opinions", case, round1, round2, round3, _chair_draft()
    )
    joined = " ".join(report.unresolved_disagreements)
    assert "Source-case attributed opinions and conditions (verbatim" in joined
    assert "surgical assessment first" in joined
    assert "complete local staging and resectability review" in joined
    assert "preoperative multimodality sequence" in joined
    assert "MRI staging, metastatic work-up and fitness assessment" in joined
    assert report.consensus_points == []


def test_round_three_peer_selector_enforces_small_bounded_sample():
    from app.agents.catalog import AGENT_PROFILES

    current = next(profile for profile in AGENT_PROFILES if profile["agent_id"] == "RO-01")
    rows = [
        {
            "agent_id": profile["agent_id"],
            "agent_name": profile["name"],
            "status": "completed",
            "result": {
                "position": "conditional",
                "provisional_conclusion": "The position remains conditional pending missing information.",
            },
        }
        for profile in AGENT_PROFILES
    ]
    selected = mdt_rounds._select_peer_views(current, rows, "result", max_total=5)
    assert len(selected) == 5
    assert all(item["agent_id"] != current["agent_id"] for item in selected)
    assert all("result" in item for item in selected)

    profile_categories = {item["agent_id"]: item["category"] for item in AGENT_PROFILES}
    ordered_categories = list(dict.fromkeys(item["category"] for item in AGENT_PROFILES))
    current_index = ordered_categories.index(current["category"])
    expected_cross_specialties = (
        ordered_categories[current_index + 1 :] + ordered_categories[:current_index]
    )
    selected_categories = [profile_categories[item["agent_id"]] for item in selected]
    assert selected_categories == expected_cross_specialties[:5]
    assert len(set(selected_categories)) == 5
    assert current["category"] not in selected_categories

    # The 15-record R2 sample should cover all seven categories before repeats.
    selected_r2 = mdt_rounds._select_peer_views(current, rows, "result", max_total=15)
    r2_category_counts = {
        category: selected_r2_categories.count(category)
        for category in ordered_categories
        for selected_r2_categories in [[profile_categories[item["agent_id"]] for item in selected_r2]]
    }
    assert len(selected_r2) == 15
    assert r2_category_counts[current["category"]] == 3
    assert all(
        count == 2 for category, count in r2_category_counts.items()
        if category != current["category"]
    )

    # A role in the last catalogue category receives a rotated cross-specialty sample.
    last_category_role = next(
        item for item in AGENT_PROFILES if item["category"] == ordered_categories[-1]
    )
    last_selected = mdt_rounds._select_peer_views(
        last_category_role, rows, "result", max_total=5
    )
    last_index = ordered_categories.index(last_category_role["category"])
    last_expected = ordered_categories[last_index + 1 :] + ordered_categories[:last_index]
    assert [profile_categories[item["agent_id"]] for item in last_selected] == last_expected[:5]


def test_adversarial_prompt_truncates_peer_digest_to_five_source_records(monkeypatch):
    from app.round_schemas import RoundContributionDraft
    from app.services import mdt_generation

    captured = []

    async def fake_generate(prompt, schema_type, max_tokens):
        captured.append(prompt)
        return RoundContributionDraft(
            position="conditional",
            provisional_conclusion="The educational position remains conditional because source information is incomplete.",
            response_to_other_perspectives="The bounded peer sample does not justify a broader claim about all roles.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Complete staging remains unknown."],
            risk_flags=["Do not infer stage from incomplete data."],
            confidence=0.5,
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review educational radiotherapy considerations."}
    case = SyntheticCase(
        scenario_title="Synthetic bounded-context test",
        case_summary="Fictional case with unknown staging and no verified treatment recommendation.",
    )
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": "The case information is incomplete.",
        "preferred_educational_option": "No option can be selected.",
    }
    own_r2 = {
        "position": "conditional",
        "provisional_conclusion": "The debate remains conditional.",
        "response_to_other_perspectives": "No proposition-level agreement is established.",
    }
    peers = [
        {
            "agent_id": f"SO-{index:02d}",
            "agent_name": f"Surgical role {index}",
            "result": {
                "position": "conditional",
                "provisional_conclusion": f"Peer conclusion {index} remains conditional.",
                "response_to_other_perspectives": "The source record remains incomplete.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
            },
        }
        for index in range(1, 9)
    ]
    asyncio.run(mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers))
    assert captured[0].count('"source":"R2:') == 5
    assert '"source":"R2:SO-01"' in captured[0]
    assert '"source":"R2:SO-05"' in captured[0]
    assert '"source":"R2:SO-06"' not in captured[0]
    assert "CASE ATTRIBUTION CHECK: the verbatim case summary contains no clearly speaker-attributed opinion." in captured[0]
    assert "Return source_opinion_reviews as an empty list" in captured[0]



def test_r2_records_exact_peer_sources_and_flags_broad_or_unsupplied_references(monkeypatch):
    from app.round_schemas import Round2ContributionDraft
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        assert "ALLOWED ROUND SOURCE IDS: R1:RO-01, R1:MO-01" in prompt
        return Round2ContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The available synthetic information remains insufficient for a definitive conclusion.",
            response_to_other_perspectives=(
                "R1:RO-01 through R1:SV-02 is an invalid broad range; "
                "R1:MO-01 is supplied; R1:ZZ-99 was not supplied."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Staging remains unknown."],
            risk_flags=[],
            confidence=0.5,
            source_opinion_responses=[],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the synthetic case."}
    case = SyntheticCase(
        scenario_title="Synthetic R2 provenance audit",
        case_summary="Fictional case with incomplete staging and no established treatment plan.",
    )
    own = {
        "position": "insufficient_information",
        "provisional_conclusion": "The case lacks verified staging and patient goals.",
        "preferred_educational_option": "Complete missing information first.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "assessment": {
            "position": "conditional",
            "provisional_conclusion": "The supplied educational position remains conditional pending staging.",
            "preferred_educational_option": "Conditional multimodality discussion.",
            "disagreement_notes": [],
            "unknowns": ["MRI remains unknown."],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_debate_contribution(profile, case, own, peers)
    )

    assert result.source_peer_ids == ["MO-01"]
    assert any("Reference range R1:RO-01 through R1:SV-02" in flag
               for flag in result.source_reference_integrity_flags)
    assert any("Reference R1:ZZ-99 was not supplied" in flag
               for flag in result.source_reference_integrity_flags)


def test_r3_records_exact_peer_sources_and_flags_wrong_round_references(monkeypatch):
    from app.round_schemas import RoundContributionDraft
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        assert '"source":"R2:MO-01"' in prompt
        return RoundContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The available synthetic information remains insufficient for a definitive conclusion.",
            response_to_other_perspectives=(
                "R1:RO-01 is my own independent record; R1:SO-01 was not supplied here; "
                "R1:RO-02 through R1:SV-02 is an invalid range; R2:MO-01 is a selected debate source."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Staging remains unknown."],
            risk_flags=[],
            confidence=0.5,
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the synthetic case."}
    case = SyntheticCase(
        scenario_title="Synthetic provenance audit",
        case_summary="Fictional case with incomplete staging and no established treatment plan.",
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The case lacks verified staging and patient goals.",
        "preferred_educational_option": "Complete the missing information first.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains insufficient pending missing information.",
        "response_to_other_perspectives": "No proposition-level agreement is established.",
    }
    peer_r2 = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The source case remains incomplete.",
            "response_to_other_perspectives": "The missing investigations remain unresolved.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peer_r2
        )
    )

    assert result.source_peer_ids == ["MO-01"]
    assert result.response_to_other_perspectives.startswith("R1:RO-01")
    assert any("R1:SO-01" in flag and "not supplied" in flag for flag in result.source_reference_integrity_flags)
    assert any("Reference range R1:RO-02 through R1:SV-02" in flag for flag in result.source_reference_integrity_flags)


def test_chair_report_surfaces_round_source_reference_integrity_flags():
    case = SyntheticCase(
        scenario_title="Synthetic provenance audit",
        case_summary="Fictional case for validating source-reference audit reporting.",
    )
    round1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    round2 = _chair_rows("result", ["insufficient_information"] * 45)
    round3 = _chair_rows("result", ["insufficient_information"] * 45)
    round3[0]["result"]["source_peer_ids"] = ["MO-01", "SO-02"]
    round3[0]["result"]["source_reference_integrity_flags"] = [
        "Reference R1:SO-01 was not supplied as an attributable source to this contribution."
    ]

    report = reconcile_chair_report_draft(
        "synthetic-source-reference-audit",
        case,
        round1,
        round2,
        round3,
        _chair_draft(),
    )

    assert any(
        "Round 3 source-reference audit" in item and "R1:SO-01" in item
        for item in report.unresolved_disagreements
    )


def test_source_opinion_review_keeps_semantically_incomplete_content_available_for_audit():
    from app.round_schemas import SourceOpinionReview

    incomplete = SourceOpinionReview(
        source_id="CASE:case_summary#1",
        opinion_label="colorectal surgical note",
        option_status="omitted",
        conditions_status="partly_preserved",
        review_basis="The source text is not adequately represented in the peer digest.",
        source_reference_ids=["R2:RO-02"],
        challenge="",
    )
    assert incomplete.source_reference_ids == ["R2:RO-02"]
    assert incomplete.challenge == ""

    unsupported_preservation = SourceOpinionReview(
        source_id="CASE:case_summary#2",
        opinion_label="medical oncology note",
        option_status="preserved",
        conditions_status="preserved",
        review_basis="The output claims preservation but provides no checkable evidence.",
    )
    assert unsupported_preservation.evidence_peer_id == ""
    assert unsupported_preservation.evidence_excerpt == ""

    schema = SourceOpinionReview.model_json_schema()
    option_description = schema["properties"]["option_status"]["description"].casefold()
    conditions_description = schema["properties"]["conditions_status"]["description"].casefold()
    assert "representation fidelity only" in option_description
    assert "case prerequisites are fulfilled" in option_description
    assert "unknown or unmet clinical prerequisite" in conditions_description



def test_r3_server_selects_exact_source_linked_excerpt_from_selected_peer(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    source_id = "CASE:case_summary#1"
    case = SyntheticCase(
        scenario_title="R3 server-selected source evidence test",
        case_summary=(
            "Fictional case. ENT service note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    peer_analysis = (
        "The option proposed is a surgery-led assessment first, conditional on "
        "complete local staging and resectability review. The peer notes that the "
        "case information remains incomplete."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion=(
                "The supplied fictional information does not establish clinical stage "
                "or a definitive educational pathway."
            ),
            response_to_other_perspectives=(
                "The peer text retains a conditional option, but the case prerequisites "
                "remain unverified."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Clinical stage and local staging information are not supplied."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id=source_id,
                    opinion_label="ENT service note",
                    option_status="preserved",
                    conditions_status="preserved",
                    review_basis="The selected peer retains the option and its prerequisites.",
                    source_reference_ids=[source_id, "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt=(
                        "This paraphrased model quote is not present as a contiguous "
                        "passage in the selected peer record."
                    ),
                )
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review source representation and preserve uncertainty.",
    }
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The fictional record lacks verified staging information.",
        "preferred_educational_option": "No definitive pathway can be established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved pending missing information.",
        "response_to_other_perspectives": "The case prerequisites remain unknown.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The supplied information does not establish a pathway.",
            "response_to_other_perspectives": "The case prerequisites remain unknown.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
            "source_opinion_responses": [{
                "source_id": source_id,
                "analysis": peer_analysis,
                "comparison": "The source-linked option remains conditional in the peer text.",
            }],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    review = result.source_opinion_reviews[0]
    assert review.evidence_validation_status == "verified"
    assert review.evidence_excerpt_binding_method == "server_selected_source_match"
    assert review.model_reported_evidence_excerpt.startswith("This paraphrased model quote")
    assert review.evidence_excerpt in peer_analysis
    assert len(review.evidence_excerpt) <= 180
    assert review.option_status == "preserved"
    assert review.conditions_status == "preserved"
    assert review.source_reference_ids == [source_id, "R2:MO-01"]
    assert result.source_reference_integrity_flags == []


def test_r3_binds_peer_from_unique_review_basis_reference_when_model_omits_structured_evidence_fields(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    source_id = "CASE:case_summary#1"
    source_analysis = (
        "The source proposes a surgery-led assessment first, conditional on "
        "complete local staging and resectability review."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The supplied fictional information does not establish a pathway.",
            response_to_other_perspectives="The source option remains conditional on missing prerequisites.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Clinical staging and resectability review remain unknown."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id=source_id,
                    option_status="preserved",
                    conditions_status="preserved",
                    review_basis=(
                        "The supplied R2:SO-02 source-specific analysis retains the option "
                        "and its stated prerequisites."
                    ),
                    # The model omitted the peer from structured references and
                    # omitted both evidence_peer_id and evidence_excerpt.
                    source_reference_ids=[source_id],
                    evidence_peer_id="",
                    evidence_excerpt="",
                )
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review source representation and preserve uncertainty.",
    }
    case = SyntheticCase(
        scenario_title="Synthetic R3 structured-evidence recovery test",
        case_summary=(
            "Fictional case. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The fictional record lacks verified staging information.",
        "preferred_educational_option": "No definitive pathway can be established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved pending missing information.",
        "response_to_other_perspectives": "The case prerequisites remain unknown.",
    }
    peers = [
        {
            "agent_id": "SO-02",
            "agent_name": "Surgical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": "The case remains insufficiently specified.",
                "response_to_other_perspectives": "The peer review retains the conditional option.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
                "source_opinion_responses": [
                    {
                        "source_id": source_id,
                        "analysis": source_analysis,
                        "comparison": "The prerequisites remain unknown.",
                    }
                ],
            },
        }
    ]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    review = result.source_opinion_reviews[0]
    assert review.model_reported_evidence_peer_id == ""
    assert review.evidence_peer_id == "R2:SO-02"
    assert review.evidence_peer_selection_method == "server_bound_review_basis_reference"
    assert review.evidence_excerpt_binding_method == "server_selected_source_match"
    assert review.evidence_validation_status == "verified"
    assert review.evidence_excerpt in source_analysis
    assert review.option_status == "preserved"
    assert review.conditions_status == "preserved"
    assert review.source_reference_ids == [source_id, "R2:SO-02"]
    assert result.source_reference_integrity_flags == []


def test_r3_binds_peer_from_unique_structured_source_reference_when_evidence_fields_are_missing(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    source_id = "CASE:case_summary#1"
    source_analysis = (
        "The source proposes a surgery-led assessment first, conditional on "
        "complete local staging and resectability review."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The supplied fictional information does not establish a pathway.",
            response_to_other_perspectives="The source option remains conditional on missing prerequisites.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Clinical staging and resectability review remain unknown."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id=source_id,
                    option_status="preserved",
                    conditions_status="preserved",
                    review_basis=(
                        "R2:RO-01 and R2:SO-02 discuss the source opinion, but the structured "
                        "source reference below selects R2:RO-01 for this review."
                    ),
                    source_reference_ids=[source_id, "R2:RO-01"],
                    evidence_peer_id="",
                    evidence_excerpt="",
                )
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "MO-01",
        "name": "Medical Oncology",
        "mandate": "Review source representation and preserve uncertainty.",
    }
    case = SyntheticCase(
        scenario_title="Synthetic R3 structured peer-reference test",
        case_summary=(
            "Fictional case. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The fictional record lacks verified staging information.",
        "preferred_educational_option": "No definitive pathway can be established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved pending missing information.",
        "response_to_other_perspectives": "The case prerequisites remain unknown.",
    }
    peers = [
        {
            "agent_id": "RO-01",
            "agent_name": "Radiation Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": "The case remains insufficiently specified.",
                "response_to_other_perspectives": "The peer review retains the conditional option.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
                "source_opinion_responses": [
                    {
                        "source_id": source_id,
                        "analysis": source_analysis,
                        "comparison": "The stated prerequisites remain unknown.",
                    }
                ],
            },
        },
        {
            "agent_id": "SO-02",
            "agent_name": "Surgical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": "The case remains insufficiently specified.",
                "response_to_other_perspectives": "The peer review retains the conditional option.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
                "source_opinion_responses": [
                    {
                        "source_id": source_id,
                        "analysis": "A separate peer view is supplied for the same case opinion.",
                        "comparison": "It is not selected as this review's evidence source.",
                    }
                ],
            },
        },
    ]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    review = result.source_opinion_reviews[0]
    assert review.model_reported_evidence_peer_id == ""
    assert review.evidence_peer_id == "R2:RO-01"
    assert review.evidence_peer_selection_method == "server_bound_structured_source_reference"
    assert review.evidence_excerpt_binding_method == "server_selected_source_match"
    assert review.evidence_validation_status == "verified"
    assert review.evidence_excerpt in source_analysis
    assert review.source_reference_ids == [source_id, "R2:RO-01"]
    assert result.source_reference_integrity_flags == []


def test_r3_source_excerpt_fallback_never_borrows_from_another_peer_or_case_opinion(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    first_source_id = "CASE:case_summary#1"
    second_source_id = "CASE:case_summary#2"
    case = SyntheticCase(
        scenario_title="R3 peer and CASE source isolation test",
        case_summary=(
            "Fictional case. ENT service note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review. "
            "The medical oncology note favours discussing a preoperative multimodality "
            "sequence, conditional on MRI staging, metastatic work-up and fitness assessment."
        ),
    )
    second_peer_analysis = (
        "The option proposed is discussing a preoperative multimodality sequence, "
        "conditional on MRI staging, metastatic work-up and fitness assessment."
    )
    first_peer_analysis = (
        "The option proposed is a surgery-led assessment first, conditional on "
        "complete local staging and resectability review."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion=(
                "The supplied fictional information does not establish either educational pathway."
            ),
            response_to_other_perspectives=(
                "The options remain conditional on information that is not supplied."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Staging, investigations, fitness and patient goals are not supplied."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id=first_source_id,
                    opinion_label="ENT service note",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="The selected peer does not provide the relevant source-specific passage.",
                    source_reference_ids=[first_source_id, "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt="A paraphrased statement that is not present in the selected peer.",
                ),
                SourceOpinionReview(
                    source_id=second_source_id,
                    opinion_label="medical oncology note",
                    option_status="preserved",
                    conditions_status="preserved",
                    review_basis="The selected peer retains this source-linked conditional option.",
                    source_reference_ids=[second_source_id, "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt=second_peer_analysis,
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review source representation and preserve uncertainty.",
    }
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The fictional record lacks verified staging information.",
        "preferred_educational_option": "No definitive pathway can be established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved pending missing information.",
        "response_to_other_perspectives": "The case prerequisites remain unknown.",
    }
    peers = [
        {
            "agent_id": "MO-01",
            "agent_name": "Medical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": "The case remains insufficiently specified.",
                "response_to_other_perspectives": "The peer text records the medical oncology source opinion.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
                "source_opinion_responses": [{
                    "source_id": second_source_id,
                    "analysis": second_peer_analysis,
                    "comparison": "The medical oncology option remains conditional.",
                }],
            },
        },
        {
            "agent_id": "SO-02",
            "agent_name": "Surgical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": "The case remains insufficiently specified.",
                "response_to_other_perspectives": "The peer text records the surgical source opinion.",
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
                "source_opinion_responses": [{
                    "source_id": first_source_id,
                    "analysis": first_peer_analysis,
                    "comparison": "The surgical option remains conditional.",
                }],
            },
        },
    ]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    first_review, second_review = result.source_opinion_reviews
    assert first_review.evidence_peer_id == "R2:MO-01"
    assert first_review.evidence_validation_status == "invalid"
    assert first_review.evidence_excerpt_binding_method == "invalid"
    assert first_review.option_status == "unclear"
    assert first_review.conditions_status == "unclear"
    assert first_review.source_reference_ids == [first_source_id]

    assert second_review.evidence_validation_status == "verified"
    assert second_review.evidence_excerpt_binding_method == "exact_model_quote"
    assert second_review.evidence_excerpt == second_peer_analysis
    assert second_review.source_reference_ids == [second_source_id, "R2:MO-01"]
    assert any(
        first_source_id in flag and "no exact supporting excerpt" in flag
        for flag in result.source_reference_integrity_flags
    )


def test_r3_omission_labels_are_downgraded_when_verified_peer_excerpt_retains_source_content(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    first_evidence = (
        "The source proposes a 'surgery-led assessment first' option conditional on "
        "complete local staging and resectability review."
    )
    second_evidence = (
        "The source proposes discussing a 'preoperative multimodality sequence' conditional "
        "on MRI staging, metastatic work-up, and fitness assessment."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        assert "representation fidelity only" in prompt
        assert "The fact that a peer does not endorse, validate, select, or act on a conditional option is not an omission" in prompt
        assert "surgery-led assessment first, conditional on complete local staging and resectability review" in prompt
        assert "partly_preserved only when the R2 text actually retains only part of the option or condition" in prompt
        assert "Likewise, saying that no definitive pathway can yet be established does not erase that source-specific entry" in prompt
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The supplied case does not establish either educational pathway.",
            response_to_other_perspectives="The case prerequisites remain unknown and no definitive pathway is established.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Clinical staging and the required investigations remain unknown."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="The option and its prerequisites are not retained because case information is missing.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt=first_evidence,
                    challenge="",
                ),
                SourceOpinionReview(
                    source_id="CASE:case_summary#2",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="The option and its prerequisites are not retained because case information is missing.",
                    source_reference_ids=["CASE:case_summary#2", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt=second_evidence,
                    challenge="",
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review the educational case and preserve uncertainty.",
    }
    case = SyntheticCase(
        scenario_title="Synthetic R3 verified-omission contradiction test",
        case_summary=(
            "Fictional case. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review. "
            "The medical oncology note favours discussing a preoperative multimodality sequence, "
            "conditional on MRI staging, metastatic work-up and fitness assessment."
        ),
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The case is incomplete and no pathway can be established.",
        "preferred_educational_option": "No option can be preferred from the supplied information.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved pending missing investigations.",
        "response_to_other_perspectives": "The supplied information does not establish suitability for either option.",
    }
    peer = {
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The case remains insufficiently specified.",
            "response_to_other_perspectives": "No definitive pathway can be established.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
            "source_opinion_responses": [
                {
                    "source_id": "CASE:case_summary#1",
                    "analysis": first_evidence,
                    "comparison": "The option remains conditional and cannot be assessed without its prerequisites.",
                },
                {
                    "source_id": "CASE:case_summary#2",
                    "analysis": second_evidence,
                    "comparison": "The option remains conditional and cannot be assessed without its prerequisites.",
                },
            ],
        },
    }

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, [peer]
        )
    )

    reviews = result.model_dump()["source_opinion_reviews"]
    assert len(reviews) == 2
    for review in reviews:
        assert review["evidence_validation_status"] == "verified"
        assert review["option_status"] == "unclear"
        assert review["conditions_status"] == "unclear"
        assert review["model_reported_option_status"] == "omitted"
        assert review["model_reported_conditions_status"] == "omitted"
        assert review["challenge"] == ""
    assert any(
        "exact verified R2 peer excerpt contains sufficient source-specific wording"
        in flag
        for flag in result.source_reference_integrity_flags
    )
    assert not any(
        "marks an option/condition omitted or partly preserved but provides no source-linked challenge"
        in flag
        for flag in result.source_reference_integrity_flags
    )


def test_r3_generation_copies_review_challenge_with_structured_source_prefix(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        assert "CASE:case_summary#N" in prompt
        assert "R2:MO-01" in prompt
        return AdversarialContributionDraft(
            position="conditional",
            provisional_conclusion="The educational view remains conditional pending adequate source review.",
            response_to_other_perspectives="The source opinions are reviewed separately and no ungrounded agreement is inferred.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["The case information remains incomplete."],
            risk_flags=[],
            confidence=0.5,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    opinion_label="ENT service note",
                    source_excerpt="ENT service note proposes a surgery-led assessment, conditional on complete staging.",
                    option_status="omitted",
                    conditions_status="partly_preserved",
                    review_basis="The supplied debate digest retains one staging prerequisite but not the full option.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt="Local staging remains a prerequisite for surgical assessment.",
                    challenge="The surgical-assessment option and its conditions are not retained in the supplied peer record.",
                ),
                SourceOpinionReview(
                    source_id="CASE:case_summary#2",
                    opinion_label="Cardiology service note",
                    source_excerpt="Cardiology service note proposes a separate preoperative sequence, conditional on MRI review.",
                    option_status="unclear",
                    conditions_status="unclear",
                    review_basis="The supplied debate sample does not contain enough detail to assess this opinion.",
                    source_reference_ids=["CASE:case_summary#2", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt="Local staging remains a prerequisite for surgical assessment.",
                    challenge="",
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the synthetic case."}
    case = SyntheticCase(
        scenario_title="Synthetic structured-review citation test",
        case_summary=(
            "Fictional case. ENT service note proposes a surgery-led assessment, conditional on complete staging. "
            "Cardiology service note proposes a separate preoperative sequence, conditional on MRI review."
        ),
    )
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": "The independent view remains conditional on missing information.",
        "preferred_educational_option": "No educational option can be preferred yet.",
    }
    own_r2 = {
        "position": "conditional",
        "provisional_conclusion": "The debate position remains conditional pending missing details.",
        "response_to_other_perspectives": "The source material is incomplete and no common option is established.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "The supplied peer record remains provisional and conditional.",
            "response_to_other_perspectives": "Local staging remains a prerequisite for surgical assessment.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )
    expected = (
        "[Sources: CASE:case_summary#1; R2:MO-01] "
        "The surgical-assessment option and its conditions are not retained in the supplied peer record."
    )
    assert expected in result.substantive_challenges
    assert result.source_reference_integrity_flags == []
    assert result.source_peer_ids == ["MO-01"]


def test_r3_generation_recovers_only_explicitly_source_linked_review_challenge(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The available synthetic information remains insufficient for a definitive conclusion.",
            response_to_other_perspectives="The review retains uncertainty and does not infer a treatment sequence.",
            agreements=[],
            substantive_challenges=[
                "[Sources: CASE:case_summary#1; R2:MO-01] The surgical-assessment option is omitted because the supplied peer record does not preserve its stated prerequisite."
            ],
            remaining_unknowns=["Local staging and resectability remain unknown."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    opinion_label="ENT service note",
                    source_excerpt="ENT service note proposes a surgery-led assessment, conditional on complete staging.",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="The supplied peer record does not preserve the attributed option or its prerequisite.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt="The supplied peer record does not preserve the surgical prerequisite.",
                    challenge="",
                ),
                SourceOpinionReview(
                    source_id="CASE:case_summary#2",
                    opinion_label="Cardiology service note",
                    source_excerpt="Cardiology service note proposes a separate preoperative sequence, conditional on MRI review.",
                    option_status="unclear",
                    conditions_status="unclear",
                    review_basis="The supplied peer record does not permit a separate assessment.",
                    source_reference_ids=["CASE:case_summary#2", "R2:MO-01"],
                    challenge="",
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the synthetic case."}
    case = SyntheticCase(
        scenario_title="Synthetic source-linked challenge recovery",
        case_summary=(
            "Fictional case. ENT service note proposes a surgery-led assessment, conditional on complete staging. "
            "Cardiology service note proposes a separate preoperative sequence, conditional on MRI review."
        ),
    )
    own_r1 = {"position": "insufficient_information", "provisional_conclusion": "The case is incomplete.", "preferred_educational_option": "No option yet."}
    own_r2 = {"position": "insufficient_information", "provisional_conclusion": "The debate remains unresolved.", "response_to_other_perspectives": "No common pathway is established."}
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The supplied peer record does not preserve the surgical prerequisite.",
            "response_to_other_perspectives": "Local staging remains unknown.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )
    recovered = result.source_opinion_reviews[0]
    assert recovered.challenge.startswith("The surgical-assessment option is omitted")
    assert (
        "[Sources: CASE:case_summary#1; R2:MO-01] " + recovered.challenge
    ) in result.substantive_challenges
    assert result.source_opinion_reviews[1].challenge == ""
    assert not any("CASE:case_summary#1" in flag and "source-linked challenge" in flag for flag in result.source_reference_integrity_flags)


def test_r3_case_source_reviews_require_exact_case_summary_excerpt(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        assert "source_excerpt is server-bound metadata" in prompt
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The educational review remains incomplete because a source excerpt cannot be verified.",
            response_to_other_perspectives="The supplied case summary does not contain the quoted source material.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["The attributed source text requires verification."],
            risk_flags=[],
            confidence=0.3,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    opinion_label="Unverified service note",
                    source_excerpt="This fabricated excerpt is not present in the case summary.",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="A source review was drafted without a matching case-summary excerpt.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01"],
                    challenge="The source option is allegedly omitted from the supplied peer record.",
                )
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the educational case."}
    case = SyntheticCase(
        scenario_title="Synthetic missing source excerpt test",
        case_summary="Fictional case. No attributed specialist opinion is explicitly supplied.",
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The case does not contain enough information for a definitive view.",
        "preferred_educational_option": "No option can be preferred from the supplied case.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains unresolved because the case summary is incomplete.",
        "response_to_other_perspectives": "No source-attributed opinion can be verified in the supplied case summary.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The peer record remains unresolved.",
            "response_to_other_perspectives": "No exact case source excerpt was supplied.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )
    flags = " ".join(result.source_reference_integrity_flags)
    assert "no exact contiguous source_excerpt" in flags
    assert "not bound to one unique exact case-summary excerpt" in flags
    assert not any("Unverified service note" in item for item in result.substantive_challenges)
    assert result.agent_id == "RO-01"


def test_r3_generation_flags_missing_verbatim_peer_evidence_without_dropping_role(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="conditional",
            provisional_conclusion="The educational position remains conditional because the source material is incomplete.",
            response_to_other_perspectives="The supplied peer views are not sufficient to establish preservation of either attributed option.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["The source-linked treatment prerequisites remain unresolved."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    opinion_label="colorectal surgical note",
                    option_status="omitted",
                    conditions_status="partly_preserved",
                    review_basis="The option is not preserved in the selected peer digest.",
                    source_reference_ids=["R2:MO-01"],
                    challenge="",
                ),
                SourceOpinionReview(
                    source_id="CASE:case_summary#2",
                    opinion_label="Cardiology service note",
                    source_excerpt="Cardiology service note proposes staged assessment, conditional on MRI review.",
                    option_status="preserved",
                    conditions_status="unclear",
                    review_basis="The output claims preservation but quotes no supplied evidence.",
                    source_reference_ids=["CASE:case_summary#2", "R2:MO-01"],
                    evidence_peer_id="R2:MO-01",
                    evidence_excerpt="This invented excerpt does not appear in the peer digest.",
                    challenge="",
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the synthetic case."}
    case = SyntheticCase(
        scenario_title="Synthetic incomplete R3 review test",
        case_summary="Fictional case. Cardiology service note proposes staged assessment, conditional on MRI review.",
    )
    own_r1 = {"position": "conditional", "provisional_conclusion": "The independent position remains conditional pending case information."}
    own_r2 = {"position": "conditional", "provisional_conclusion": "The debate position remains conditional pending case information."}
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "The selected peer has a conditional view.",
            "response_to_other_perspectives": "No exact quotation supporting the claimed preservation is present.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )
    assert result.agent_id == "RO-01"
    assert result.source_reference_integrity_flags
    flags = " ".join(result.source_reference_integrity_flags)
    assert "omits its attributed CASE source ID" in flags
    reviews = result.model_dump()["source_opinion_reviews"]
    assert reviews[0]["model_reported_option_status"] == "omitted"
    assert reviews[0]["option_status"] == "unclear"
    assert reviews[0]["evidence_peer_id"] == ""
    assert reviews[0]["evidence_peer_selection_method"] == "invalid"
    assert reviews[0]["evidence_validation_status"] == "missing"
    assert reviews[1]["model_reported_option_status"] == "preserved"
    assert reviews[1]["option_status"] == "unclear"
    assert reviews[1]["evidence_validation_status"] == "invalid"
    assert "no exact supporting excerpt" in flags



def test_mdt_and_round_timestamps_cover_all_rounds_and_clear_on_chair_retry(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)
    assert run_store.get_run(run_id)["mdt_finished_at"] is None

    role_ids = [profile["agent_id"] for profile in run_store.AGENT_PROFILES]

    def complete_round(round_number, agent_ids, started_at, finished_at):
        monkeypatch.setattr(run_store, "_now", lambda: started_at)
        run_store.mark_round_running(run_id, round_number)
        for agent_id in agent_ids:
            run_store.save_round_success(run_id, round_number, agent_id, "{}", 0.01)
        monkeypatch.setattr(run_store, "_now", lambda: finished_at)
        run_store.mark_round_finished(run_id, round_number)
        summary = run_store.get_round_summary(run_id, round_number)
        assert summary["started_at"] == started_at
        assert summary["finished_at"] == finished_at

    run_store.create_round_job(run_id, 2)
    complete_round(2, role_ids, "2099-01-01T10:00:00+00:00", "2099-01-01T10:05:00+00:00")
    assert run_store.get_run(run_id)["mdt_finished_at"] is None

    run_store.create_round_job(run_id, 3)
    complete_round(3, role_ids, "2099-01-01T10:06:00+00:00", "2099-01-01T10:12:00+00:00")
    assert run_store.get_run(run_id)["mdt_finished_at"] is None

    run_store.create_round_job(run_id, 4)
    monkeypatch.setattr(run_store, "_now", lambda: "2099-01-01T10:13:00+00:00")
    run_store.mark_round_running(run_id, 4)
    run_store.save_round_failure(run_id, 4, "SG-07", "Intentional timestamp retry test.", 0.01)
    monkeypatch.setattr(run_store, "_now", lambda: "2099-01-01T10:14:00+00:00")
    run_store.mark_round_finished(run_id, 4)
    assert run_store.get_run(run_id)["status"] == "completed_with_errors"
    assert run_store.get_run(run_id)["mdt_finished_at"] == "2099-01-01T10:14:00+00:00"

    monkeypatch.setattr(run_store, "_now", lambda: "2099-01-01T10:15:00+00:00")
    run_store.reset_failed_round_agents(run_id, 4)
    assert run_store.get_run(run_id)["mdt_finished_at"] is None
    reset_summary = run_store.get_round_summary(run_id, 4)
    assert reset_summary["started_at"] is None
    assert reset_summary["finished_at"] is None

    complete_round(4, ["SG-07"], "2099-01-01T10:16:00+00:00", "2099-01-01T10:17:00+00:00")
    assert run_store.get_run(run_id)["status"] == "completed"
    assert run_store.get_run(run_id)["mdt_finished_at"] == "2099-01-01T10:17:00+00:00"


def test_completion_timestamp_columns_migrate_existing_sqlite_database(monkeypatch, tmp_path):
    legacy_db = tmp_path / "legacy-timestamps.sqlite3"
    connection = run_store.sqlite3.connect(legacy_db)
    connection.execute(
        """CREATE TABLE simulation_runs (
            run_id TEXT PRIMARY KEY, case_json TEXT NOT NULL, status TEXT NOT NULL,
            total_agents INTEGER NOT NULL, current_agent_id TEXT, patient_id TEXT,
            case_version_id TEXT, case_version_number INTEGER,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )"""
    )
    connection.execute(
        """CREATE TABLE round_runs (
            run_id TEXT NOT NULL, round_number INTEGER NOT NULL, status TEXT NOT NULL,
            total_agents INTEGER NOT NULL, current_agent_id TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            PRIMARY KEY (run_id, round_number),
            FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id) ON DELETE CASCADE
        )"""
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(run_store, "DB_PATH", legacy_db)
    run_store.initialize_database()
    with run_store._connect() as db:
        run_store._ensure_round_tables(db)
        run_columns = {row["name"] for row in db.execute("PRAGMA table_info(simulation_runs)")}
        round_columns = {row["name"] for row in db.execute("PRAGMA table_info(round_runs)")}

    assert "mdt_finished_at" in run_columns
    assert {"started_at", "finished_at"}.issubset(round_columns)



def test_chair_report_uses_neutral_case_wording_and_retains_education_boundary():
    case = SyntheticCase(
        scenario_title="Neutral wording regression test",
        case_summary="Fictional training case used to test report wording only.",
    )
    rows1 = _chair_rows("assessment", ["insufficient_information"] * 45)
    rows2 = _chair_rows("result", ["insufficient_information"] * 45)
    rows3 = _chair_rows("result", ["insufficient_information"] * 45)
    report = reconcile_chair_report_draft(
        "neutral-wording-regression", case, rows1, rows2, rows3, _chair_draft()
    )

    user_visible = [
        report.report_title,
        report.chair_conclusion,
        report.overall_educational_synthesis,
        report.chair_reflection,
        *report.governance_and_safeguarding_considerations,
        *report.evidence_limitations,
    ]
    assert all("synthetic" not in item.casefold() for item in user_visible)
    assert "supplied case" in report.chair_conclusion.casefold()
    assert any("educational simulation only" in item.casefold()
               for item in report.governance_and_safeguarding_considerations)
    assert report.not_a_treatment_instruction is True

def test_failed_round_agent_resumes_without_replacing_completed_peer_records(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)
    attempts = {"RO-01": 0}

    async def fake_debate(profile, case, own, peers, max_tokens=900):
        agent_id = profile["agent_id"]
        assert peers
        if agent_id == "RO-01":
            attempts[agent_id] += 1
            # Fail both the initial structured response and its one schema retry.
            if attempts[agent_id] <= 2:
                raise AgentGenerationError("intentional transient failure")
        return _round_contribution(profile, case, own, peers, 2)

    monkeypatch.setattr(mdt_rounds, "generate_debate_contribution", fake_debate)

    started = client.post(f"/api/runs/{run_id}/rounds/2")
    assert started.status_code == 200
    failed_summary = client.get(f"/api/runs/{run_id}/rounds/2").json()
    assert failed_summary["status"] == "completed_with_errors"
    assert failed_summary["completed_count"] == 44
    assert failed_summary["failed_count"] == 1

    before_resume = client.get(f"/api/runs/{run_id}/rounds/2/results").json()["results"]
    failed_row = next(row for row in before_resume if row["agent_id"] == "RO-01")
    completed_peer_before = next(row for row in before_resume if row["agent_id"] == "RO-02")
    assert failed_row["status"] == "failed"
    assert failed_row["result"] is None
    assert failed_row["error_message"]
    # A failed R2 cannot be treated as a complete prerequisite for R3.
    assert client.post(f"/api/runs/{run_id}/rounds/3").status_code == 409
    assert completed_peer_before["status"] == "completed"
    assert completed_peer_before["result"] is not None

    resumed = client.post(f"/api/runs/{run_id}/rounds/2/resume")
    assert resumed.status_code == 200
    final_summary = client.get(f"/api/runs/{run_id}/rounds/2").json()
    assert final_summary["status"] == "completed"
    assert final_summary["completed_count"] == 45
    assert final_summary["failed_count"] == 0
    assert attempts["RO-01"] == 3

    after_resume = client.get(f"/api/runs/{run_id}/rounds/2/results").json()["results"]
    recovered_row = next(row for row in after_resume if row["agent_id"] == "RO-01")
    completed_peer_after = next(row for row in after_resume if row["agent_id"] == "RO-02")
    assert recovered_row["status"] == "completed"
    assert recovered_row["result"] is not None
    assert completed_peer_after["result"] == completed_peer_before["result"]

def test_failed_round_three_agent_resumes_without_replacing_completed_peer_records(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)

    async def fake_debate(profile, case, own, peers, max_tokens=900):
        assert peers
        return _round_contribution(profile, case, own, peers, 2)

    attempts = {"RO-01": 0}

    async def fake_adversarial(profile, case, own, debate, peers, max_tokens=1300):
        assert peers
        assert debate["position"] == "conditional"
        if profile["agent_id"] == "RO-01":
            attempts["RO-01"] += 1
            # Fail both the initial structured response and its one schema retry.
            if attempts["RO-01"] <= 2:
                raise AgentGenerationError("intentional R3 transient failure")
        return _round_contribution(profile, case, own, peers, 3)

    monkeypatch.setattr(mdt_rounds, "generate_debate_contribution", fake_debate)
    monkeypatch.setattr(mdt_rounds, "generate_adversarial_contribution", fake_adversarial)

    assert client.post(f"/api/runs/{run_id}/rounds/2").status_code == 200
    r2_summary = client.get(f"/api/runs/{run_id}/rounds/2").json()
    assert r2_summary["status"] == "completed"
    assert r2_summary["completed_count"] == 45

    assert client.post(f"/api/runs/{run_id}/rounds/3").status_code == 200
    failed_summary = client.get(f"/api/runs/{run_id}/rounds/3").json()
    assert failed_summary["status"] == "completed_with_errors"
    assert failed_summary["completed_count"] == 44
    assert failed_summary["failed_count"] == 1

    before_resume = client.get(f"/api/runs/{run_id}/rounds/3/results").json()["results"]
    failed_row = next(row for row in before_resume if row["agent_id"] == "RO-01")
    completed_peer_before = next(row for row in before_resume if row["agent_id"] == "RO-02")
    assert failed_row["status"] == "failed"
    assert failed_row["result"] is None
    assert failed_row["error_message"]
    # A failed R3 cannot be treated as a complete prerequisite for Chair synthesis.
    assert client.post(f"/api/runs/{run_id}/rounds/4").status_code == 409
    assert completed_peer_before["status"] == "completed"
    assert completed_peer_before["result"]["round_number"] == 3

    resumed = client.post(f"/api/runs/{run_id}/rounds/3/resume")
    assert resumed.status_code == 200
    final_summary = client.get(f"/api/runs/{run_id}/rounds/3").json()
    assert final_summary["status"] == "completed"
    assert final_summary["completed_count"] == 45
    assert final_summary["failed_count"] == 0
    assert attempts["RO-01"] == 3

    after_resume = client.get(f"/api/runs/{run_id}/rounds/3/results").json()["results"]
    recovered_row = next(row for row in after_resume if row["agent_id"] == "RO-01")
    completed_peer_after = next(row for row in after_resume if row["agent_id"] == "RO-02")
    assert recovered_row["status"] == "completed"
    assert recovered_row["result"]["round_number"] == 3
    assert completed_peer_after["result"] == completed_peer_before["result"]


def test_chair_failure_retry_and_saved_four_round_records_survive_database_reinitialisation(monkeypatch, tmp_path):
    run_id = _create_complete_round1(monkeypatch, tmp_path)

    async def fake_debate(profile, case, own, peers, max_tokens=900):
        assert peers
        return _round_contribution(profile, case, own, peers, 2)

    async def fake_adversarial(profile, case, own, debate, peers, max_tokens=1300):
        assert peers
        return _round_contribution(profile, case, own, peers, 3)

    chair_attempts = 0

    async def fake_chair(run_id_arg, case, round1, round2, round3, max_tokens=1600):
        nonlocal chair_attempts
        chair_attempts += 1
        assert run_id_arg == run_id
        assert len(round1) == len(round2) == len(round3) == 45
        if chair_attempts <= 2:
            raise AgentGenerationError("intentional Chair structured-output failure")
        return _final_report(run_id_arg, case, round1, round2, round3)

    monkeypatch.setattr(mdt_rounds, "generate_debate_contribution", fake_debate)
    monkeypatch.setattr(mdt_rounds, "generate_adversarial_contribution", fake_adversarial)
    monkeypatch.setattr(mdt_rounds, "generate_chair_report", fake_chair)

    assert client.post(f"/api/runs/{run_id}/rounds/2").status_code == 200
    assert client.get(f"/api/runs/{run_id}/rounds/2").json()["status"] == "completed"
    assert client.post(f"/api/runs/{run_id}/rounds/3").status_code == 200
    assert client.get(f"/api/runs/{run_id}/rounds/3").json()["status"] == "completed"

    assert client.post(f"/api/runs/{run_id}/rounds/4").status_code == 200
    failed_summary = client.get(f"/api/runs/{run_id}/rounds/4").json()
    assert failed_summary["status"] == "completed_with_errors"
    assert failed_summary["completed_count"] == 0
    assert failed_summary["failed_count"] == 1
    chair_failure = client.get(f"/api/runs/{run_id}/rounds/4/results").json()["results"][0]
    assert chair_failure["agent_id"] == "SG-07"
    assert chair_failure["status"] == "failed"
    assert chair_failure["result"] is None
    assert chair_failure["error_message"]
    assert client.get(f"/api/runs/{run_id}/report").status_code == 404

    # The parent run is terminal-with-errors because R4 failed, but R1 itself
    # has no failed agents. R1 resume must not silently mark the whole MDT complete.
    wrong_stage_resume = client.post(f"/api/runs/{run_id}/resume")
    assert wrong_stage_resume.status_code == 409
    assert "resume the failed MDT round" in wrong_stage_resume.json()["detail"]
    assert client.get(f"/api/runs/{run_id}/rounds/4").json()["status"] == "completed_with_errors"

    resumed = client.post(f"/api/runs/{run_id}/rounds/4/resume")
    assert resumed.status_code == 200
    completed_summary = client.get(f"/api/runs/{run_id}/rounds/4").json()
    assert completed_summary["status"] == "completed"
    assert completed_summary["completed_count"] == 1
    assert completed_summary["failed_count"] == 0
    assert chair_attempts == 3

    report_before_restart = client.get(f"/api/runs/{run_id}/report").json()
    assert report_before_restart["not_a_treatment_instruction"] is True
    assert report_before_restart["consensus_points"] == []
    assert report_before_restart["consensus_status"] == "insufficient_information"
    run_before_restart = run_store.get_run(run_id)
    saved_r1 = client.get(f"/api/runs/{run_id}/results").json()["results"]
    saved_r2 = client.get(f"/api/runs/{run_id}/rounds/2/results").json()["results"]
    saved_r3 = client.get(f"/api/runs/{run_id}/rounds/3/results").json()["results"]
    saved_r4 = client.get(f"/api/runs/{run_id}/rounds/4/results").json()["results"]

    # Each store operation uses a fresh SQLite connection; explicit reinitialisation
    # exercises schema migration/startup against the persisted database file.
    run_store.initialize_database()

    assert run_store.get_run(run_id)["case_snapshot_sha256"] == run_before_restart["case_snapshot_sha256"]
    assert run_store.list_results(run_id) == saved_r1
    assert run_store.list_round_results(run_id, 2) == saved_r2
    assert run_store.list_round_results(run_id, 3) == saved_r3
    assert run_store.list_round_results(run_id, 4) == saved_r4
    assert run_store.get_final_report(run_id) == report_before_restart

    # Launch a separate interpreter against the same SQLite file to simulate a
    # backend process restart rather than relying only on fresh connections.
    import subprocess
    import sys

    restart_probe = """
import json
import sys
from pathlib import Path
from app.services import run_store

run_store.DB_PATH = Path(sys.argv[1])
run_id = sys.argv[2]
run_store.initialize_database()
report = run_store.get_final_report(run_id)
print(json.dumps({
    "run_id": run_store.get_run(run_id)["run_id"],
    "case_snapshot_sha256": run_store.get_run(run_id)["case_snapshot_sha256"],
    "r1_completed": sum(row["status"] == "completed" for row in run_store.list_results(run_id)),
    "round_completed": [
        run_store.get_round_summary(run_id, number)["completed_count"]
        for number in (2, 3, 4)
    ],
    "chair_report_available": report is not None,
    "chair_consensus_status": report["consensus_status"] if report else None,
}))
"""
    restarted = subprocess.run(
        [sys.executable, "-c", restart_probe, str(run_store.DB_PATH), run_id],
        cwd=str(run_store.BACKEND_DIR),
        check=True,
        capture_output=True,
        text=True,
    )
    restarted_state = json.loads(restarted.stdout)
    assert restarted_state == {
        "run_id": run_id,
        "case_snapshot_sha256": run_before_restart["case_snapshot_sha256"],
        "r1_completed": 45,
        "round_completed": [45, 45, 1],
        "chair_report_available": True,
        "chair_consensus_status": "insufficient_information",
    }


def test_r2_and_r3_use_larger_context_without_changing_chair_default():
    from app.round_schemas import AdversarialContributionDraft, FinalReportDraft, Round2ContributionDraft, RoundContributionDraft
    from app.services.mdt_generation import _context_window_for_schema

    assert _context_window_for_schema(RoundContributionDraft) == 6144
    assert _context_window_for_schema(Round2ContributionDraft) == 6144
    assert _context_window_for_schema(AdversarialContributionDraft) == 6144
    assert _context_window_for_schema(FinalReportDraft) == 4096

def test_r3_does_not_promote_challenges_using_an_unsupplied_peer_id(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    summary = (
        "Fictional case. The neurology service note proposes a specialist assessment first, "
        "conditional on complete staging."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The source opinion remains conditional on the missing staging information.",
            response_to_other_perspectives="The selected peer record does not establish whether the source opinion was retained.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Complete staging is not supplied."],
            risk_flags=[],
            confidence=0.3,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    option_status="omitted",
                    conditions_status="omitted",
                    review_basis="The supplied peer record does not include the attributed option.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-99"],
                    challenge="The supplied R2 record omits the attributed option.",
                )
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the educational case."}
    case = SyntheticCase(scenario_title="Unsupplied peer citation test", case_summary=summary)
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The source opinion remains conditional on missing information.",
        "preferred_educational_option": "No final option can be established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains insufficient pending review of the source opinion.",
        "response_to_other_perspectives": "The supplied material does not establish a common sequence.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The peer record remains insufficient.",
            "response_to_other_perspectives": "No source-linked option is established.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )
    assert not any("The supplied R2 record omits the attributed option." in item for item in result.substantive_challenges)
    review = result.model_dump()["source_opinion_reviews"][0]
    assert review["evidence_validation_status"] == "missing"
    assert review["model_reported_source_reference_ids"] == ["CASE:case_summary#1", "R2:MO-99"]
    assert review["source_reference_ids"] == ["CASE:case_summary#1"]
    assert any(
        "Challenge for CASE:case_summary#1 was not promoted" in item
        and "server-verified exact excerpt from a supplied R2 peer" in item
        for item in result.source_reference_integrity_flags
    )



def test_r3_uses_server_identified_opinion_ids_and_flags_duplicate_or_missing_reviews(monkeypatch):
    from app.round_schemas import AdversarialContributionDraft, SourceOpinionReview
    from app.services import mdt_generation

    summary = (
        "Fictional case. The colorectal surgical note favours a surgical assessment first, "
        "conditional on complete local staging and resectability review; "
        "the medical oncology note favours discussing a preoperative multimodality sequence, "
        "conditional on MRI staging, metastatic work-up and fitness assessment."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        assert "SERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS" in prompt
        assert "CASE:case_summary#1" in prompt and "CASE:case_summary#2" in prompt
        assert "ALLOWED SOURCE-OPINION REVIEW PEER IDS" in prompt
        assert "ABSENT-IS-NOT-UNMET RULE" in prompt
        assert "this exact prerequisite was assessed" in prompt
        assert "Never describe undocumented prerequisites as 'not met' or 'unmet'" in prompt
        assert "Never conclude that 'neither option is indicated'" in prompt
        assert "R2:MO-01" in prompt and "FORBIDDEN FOR SOURCE-OPINION REVIEWS: R2:RO-01" in prompt
        assert "the colorectal surgical note favours a surgical assessment first" in prompt.casefold()
        assert "the medical oncology note favours discussing a preoperative multimodality sequence" in prompt.casefold()
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The two source opinions remain conditional and require separate review.",
            response_to_other_perspectives="The supplied peer records state that the prerequisites remain unmet.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["The source conditions remain to be assessed."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    source_excerpt="",
                    option_status="unclear",
                    conditions_status="unclear",
                    review_basis="The bounded supplied peer sample is insufficient to assess this opinion.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01", "R2:RO-01"],
                    challenge="This duplicate review challenge must not be promoted.",
                ),
                SourceOpinionReview(
                    source_id="CASE:case_summary#1",
                    source_excerpt=(
                        "the colorectal surgical note favours a surgical assessment first, "
                        "conditional on complete local staging and resectability review"
                    ),
                    option_status="unclear",
                    conditions_status="unclear",
                    review_basis="This duplicate does not provide a separate review of the second opinion.",
                    source_reference_ids=["CASE:case_summary#1", "R2:MO-01"],
                ),
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the fictional case."}
    case = SyntheticCase(
        scenario_title="Fictional competing source opinions",
        case_summary=summary,
        known_unknowns=["MRI staging result is not supplied."],
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The independent assessment remains conditional on missing information.",
        "preferred_educational_option": "No option is established from the supplied information.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains insufficient pending separate review of the source opinions.",
        "response_to_other_perspectives": "The supplied contributions do not establish a common proposition.",
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "The source material remains conditional pending further information.",
            "response_to_other_perspectives": "The selected record does not establish a shared sequence.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(profile, case, own_r1, own_r2, peers)
    )

    flags = " ".join(result.source_reference_integrity_flags)
    assert "CASE:case_summary#1 has 2 duplicate R3 reviews" in flags
    assert "Required server-identified source opinion CASE:case_summary#2 has no R3 review" in flags
    expected_excerpt = (
        "The colorectal surgical note favours a surgical assessment first, "
        "conditional on complete local staging and resectability review"
    )
    assert [item["source_excerpt"] for item in result.model_dump()["source_opinion_reviews"]] == [
        expected_excerpt, expected_excerpt
    ]
    assert not any("duplicate review challenge must not be promoted" in item for item in result.substantive_challenges)
    assert result.source_peer_ids == ["MO-01"]
    assert any(
        "R2:RO-01" in flag and "not supplied to this role" in flag
        for flag in result.source_reference_integrity_flags
    )
    assert any(
        "describes prerequisite(s) as unmet/not met" in flag
        for flag in result.case_data_integrity_flags
    )
    assert "MRI staging result is not supplied." in result.remaining_unknowns


def test_r2_flags_incomplete_structured_opinion_content(monkeypatch):
    import asyncio

    from app.round_schemas import Round2ContributionDraft
    from app.services import mdt_generation
    from app.schemas import SyntheticCase

    async def fake_generate(prompt, schema_type, max_tokens):
        return Round2ContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The supplied case remains incomplete pending further review.",
            response_to_other_perspectives="The supplied peer data do not establish a definitive pathway.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=[],
            risk_flags=[],
            confidence=0.4,
            source_opinion_responses=[{
                "source_id": "CASE:case_summary#1",
                "analysis": "The case remains incomplete pending clinical staging and fitness review.",
                "comparison": "The source opinion cannot be evaluated because the required information is missing.",
            }],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    case = SyntheticCase(
        scenario_title="R2 incomplete opinion response",
        case_summary=(
            "Fictional record. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    result = asyncio.run(
        mdt_generation.generate_debate_contribution(
            {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review options."},
            case,
            {
                "position": "insufficient_information",
                "provisional_conclusion": "The supplied case remains incomplete pending further review.",
                "preferred_educational_option": "No definitive pathway established.",
            },
            [],
        )
    )
    flags = " ".join(result.source_reference_integrity_flags)
    assert "does not retain sufficient source-specific language for the distinct option" in flags


def test_r2_flags_unaddressed_server_registered_case_opinions(monkeypatch):
    import asyncio

    from app.round_schemas import Round2ContributionDraft
    from app.services import mdt_generation
    from app.schemas import SyntheticCase

    async def fake_generate(prompt, schema_type, max_tokens):
        return Round2ContributionDraft(
            position="insufficient_information",
            provisional_conclusion=(
                "The supplied case does not establish stage, fitness or a definitive pathway."
            ),
            response_to_other_perspectives=(
                "The case data are incomplete and the selected peer record also reports missing information."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=[],
            risk_flags=[],
            confidence=0.4,
            source_opinion_responses=[],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    case = SyntheticCase(
        scenario_title="R2 case opinion coverage",
        case_summary=(
            "Fictional record. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    result = asyncio.run(
        mdt_generation.generate_debate_contribution(
            {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review options."},
            case,
            {
                "position": "insufficient_information",
                "provisional_conclusion": "The supplied case does not establish a definitive pathway.",
                "preferred_educational_option": "No option established.",
            },
            [],
        )
    )
    assert any(
        "R2 has no structured response for server-identified attributed opinion CASE:case_summary#1"
        in flag
        for flag in result.source_reference_integrity_flags
    )


def test_r2_distinguishes_unknown_prerequisites_from_assessed_unmet_prerequisites(monkeypatch):
    import asyncio

    from app.round_schemas import Round2ContributionDraft
    from app.schemas import SyntheticCase
    from app.services import mdt_generation

    prompts = []
    analysis = (
        "The surgery-led assessment first remains conditional on complete local staging, "
        "MRI staging result and fitness assessment. These prerequisites are not supplied "
        "in the case; suitability remains unknown."
    )

    async def fake_generate(prompt, schema_type, max_tokens):
        assert schema_type is Round2ContributionDraft
        prompts.append(prompt)
        return Round2ContributionDraft(
            position="conditional",
            provisional_conclusion=(
                "The source proposal remains conditional; suitability cannot be determined "
                "from the unreported prerequisite results."
            ),
            response_to_other_perspectives=(
                "The conditional source option is retained as a source statement, not endorsed; "
                "the prerequisites remain unmet."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=[],
            risk_flags=[],
            confidence=0.4,
            source_opinion_responses=[
                {
                    "source_id": "CASE:case_summary#1",
                    "analysis": analysis,
                    "comparison": (
                        "The proposal remains conditional; unknown prerequisite status "
                        "does not establish that the prerequisite was unmet."
                    ),
                }
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    case = SyntheticCase(
        scenario_title="R2 unknown-versus-unmet prerequisite test",
        case_summary=(
            "Fictional case. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging, MRI staging result and fitness assessment."
        ),
        known_unknowns=[
            "MRI staging result is not supplied.",
            "Complete staging is not documented.",
            "Fitness assessment is not supplied.",
        ],
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The supplied record does not establish suitability.",
        "preferred_educational_option": "The source proposal remains conditional.",
    }

    result = asyncio.run(
        mdt_generation.generate_debate_contribution(
            {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review the fictional educational case."},
            case,
            own_r1,
            [],
        )
    )

    prompt = prompts[0]
    assert "ABSENT-IS-NOT-UNMET RULE" in prompt
    assert "no MRI result supplied means MRI staging is unknown" in prompt
    assert "no staging entry means stage is undocumented" in prompt
    assert "no fitness assessment means fitness is unknown" in prompt
    assert "Use 'not met' or 'unmet' only when the case explicitly records that the prerequisite was assessed" in prompt
    assert "identify that exact documented finding and do not infer a threshold" in prompt
    assert "A conditional source option remains conditional when prerequisite status is unknown" in prompt
    assert "Never describe undocumented prerequisites as 'not met' or 'unmet'" in prompt
    assert "Never conclude that 'neither option is indicated'" in prompt
    assert "MRI staging result is not supplied." in prompt
    assert "Complete staging is not documented." in prompt
    assert "Fitness assessment is not supplied." in prompt

    assert len(result.source_opinion_responses) == 1
    source_response = result.source_opinion_responses[0]
    assert "conditional on complete local staging, MRI staging result and fitness assessment" in source_response.source_excerpt
    assert "remains conditional" in source_response.analysis
    assert not any(
        "does not retain sufficient source-specific language" in flag
        for flag in result.source_reference_integrity_flags
    )
    assert all(item in result.remaining_unknowns for item in case.known_unknowns)
    assert any(
        "describes prerequisite(s) as unmet/not met" in flag
        for flag in result.case_data_integrity_flags
    )


def test_r2_repairs_only_missing_server_registered_opinion_responses(monkeypatch):
    from app.round_schemas import (
        Round2ContributionDraft,
        Round2SourceOpinionResponseDraft,
        Round2SourceOpinionResponsesRepairDraft,
    )
    from app.services import mdt_generation

    summary = (
        "Fictional case. The colorectal surgical note favours a surgical assessment first, "
        "conditional on complete local staging and resectability review; the medical oncology "
        "note favours discussing a preoperative multimodality sequence, conditional on MRI "
        "staging, metastatic work-up and fitness assessment."
    )
    calls = []

    async def fake_generate(prompt, schema_type, max_tokens):
        calls.append((prompt, schema_type, max_tokens))
        if schema_type is Round2ContributionDraft:
            return Round2ContributionDraft(
                position="insufficient_information",
                provisional_conclusion="The synthetic record does not establish a definitive educational pathway.",
                response_to_other_perspectives="The supplied peer records describe missing prerequisites without establishing their status.",
                agreements=[],
                substantive_challenges=[],
                remaining_unknowns=[],
                risk_flags=[],
                confidence=0.4,
                source_opinion_responses=[],
            )
        assert schema_type is Round2SourceOpinionResponsesRepairDraft
        assert "CASE:case_summary#1" in prompt and "CASE:case_summary#2" in prompt
        assert "ACTUAL SELECTED PEER R1 POSITIONS" in prompt
        return Round2SourceOpinionResponsesRepairDraft(
            source_opinion_responses=[
                Round2SourceOpinionResponseDraft(
                    source_id="CASE:case_summary#1",
                    analysis="The surgery-led assessment first option remains conditional on complete local staging and resectability review; both prerequisites are unknown/not supplied.",
                    comparison="This is compared separately with the own assessment and selected R1 peers, without implying endorsement.",
                ),
                Round2SourceOpinionResponseDraft(
                    source_id="CASE:case_summary#2",
                    analysis="The preoperative multimodality sequence remains conditional on MRI staging, metastatic work-up and fitness assessment; these prerequisites are unknown/not supplied.",
                    comparison="This remains a distinct source option from the surgery-led assessment and is not endorsed as a treatment choice.",
                ),
            ]
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    case = SyntheticCase(scenario_title="R2 missing-opinion repair", case_summary=summary)
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The supplied record does not establish a pathway.",
        "preferred_educational_option": "No pathway is established from the available information.",
    }
    peers = [
        {"agent_id": "SO-02", "agent_name": "Surgical Oncology", "assessment": {
            "position": "conditional",
            "provisional_conclusion": "The surgery-led assessment remains conditional on local staging and resectability review.",
            "preferred_educational_option": "Surgery-led assessment first.",
            "disagreement_notes": [], "unknowns": ["Staging is not supplied."],
        }},
        {"agent_id": "MO-01", "agent_name": "Medical Oncology", "assessment": {
            "position": "insufficient_information",
            "provisional_conclusion": "The preoperative sequence cannot be assessed without MRI and fitness information.",
            "preferred_educational_option": "Preoperative multimodality sequence.",
            "disagreement_notes": [], "unknowns": ["MRI and fitness are not supplied."],
        }},
    ]

    result = asyncio.run(
        mdt_generation.generate_debate_contribution(
            {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review educational options."},
            case,
            own_r1,
            peers,
        )
    )

    assert len(calls) == 2
    assert calls[1][1] is Round2SourceOpinionResponsesRepairDraft
    assert calls[1][2] == 750
    assert [item.source_id for item in result.source_opinion_responses] == [
        "CASE:case_summary#1", "CASE:case_summary#2"
    ]
    assert result.source_opinion_repair_attempted is True
    assert result.source_opinion_repair_status == "completed"
    assert result.source_opinion_repaired_ids == ["CASE:case_summary#1", "CASE:case_summary#2"]
    assert not any("no structured response" in flag for flag in result.source_reference_integrity_flags)
    assert all(item.source_excerpt for item in result.source_opinion_responses)


def test_r3_repairs_missing_review_from_exact_supplied_peer_record(monkeypatch):
    from app.round_schemas import (
        AdversarialContributionDraft,
        AdversarialSourceOpinionReviewsRepairDraft,
        SourceOpinionReview,
    )
    from app.services import mdt_generation

    summary = (
        "Fictional case. The colorectal surgical note favours a surgical assessment first, "
        "conditional on complete local staging and resectability review; the medical oncology "
        "note favours discussing a preoperative multimodality sequence, conditional on MRI "
        "staging, metastatic work-up and fitness assessment."
    )
    first_id = "CASE:case_summary#1"
    second_id = "CASE:case_summary#2"
    first_analysis = (
        "The surgery-led assessment first remains conditional on complete local staging "
        "and resectability review; both prerequisites are unknown/not supplied."
    )
    second_analysis = (
        "The preoperative multimodality sequence remains conditional on MRI staging, "
        "metastatic work-up and fitness assessment; these prerequisites are unknown/not supplied."
    )
    calls = []

    async def fake_generate(prompt, schema_type, max_tokens):
        calls.append((prompt, schema_type, max_tokens))
        if schema_type is AdversarialContributionDraft:
            return AdversarialContributionDraft(
                position="insufficient_information",
                provisional_conclusion="The supplied information does not establish a definitive educational pathway.",
                response_to_other_perspectives="The selected peer R2 record retains the first conditional option; the second requires separate review.",
                agreements=[],
                substantive_challenges=[],
                remaining_unknowns=["Clinical staging remains unknown."],
                risk_flags=[],
                confidence=0.4,
                source_opinion_reviews=[
                    SourceOpinionReview(
                        source_id=first_id,
                        option_status="preserved",
                        conditions_status="preserved",
                        review_basis="R2:SO-02 retains the surgery-led assessment and its complete local staging and resectability conditions.",
                        source_reference_ids=[first_id, "R2:SO-02"],
                        evidence_peer_id="R2:SO-02",
                        evidence_excerpt=first_analysis,
                    )
                ],
            )
        assert schema_type is AdversarialSourceOpinionReviewsRepairDraft
        assert second_id in prompt and "R2:SO-02" in prompt
        assert "matching structured source_opinion_responses" in prompt
        return AdversarialSourceOpinionReviewsRepairDraft(
            source_opinion_reviews=[
                SourceOpinionReview(
                    source_id=second_id,
                    option_status="preserved",
                    conditions_status="preserved",
                    review_basis="R2:SO-02 retains the preoperative multimodality sequence and its MRI, metastatic work-up and fitness conditions.",
                    source_reference_ids=[second_id, "R2:SO-02"],
                    evidence_peer_id="R2:SO-02",
                    evidence_excerpt=second_analysis,
                )
            ]
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review source representation."}
    case = SyntheticCase(scenario_title="R3 missing-review repair", case_summary=summary)
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The case data do not establish either conditional pathway.",
        "preferred_educational_option": "No definitive pathway is established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The first and second source opinions remain conditional.",
        "response_to_other_perspectives": "Both prerequisites are unknown.",
        "source_opinion_responses": [],
    }
    peer_views = [{
        "agent_id": "SO-02",
        "agent_name": "Surgical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "Both source options remain conditional.",
            "response_to_other_perspectives": "Both options retain their stated prerequisites.",
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
            "source_opinion_responses": [
                {"source_id": first_id, "analysis": first_analysis, "comparison": "The option remains conditional."},
                {"source_id": second_id, "analysis": second_analysis, "comparison": "The option remains conditional."},
            ],
            "source_reference_integrity_flags": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peer_views
        )
    )

    assert len(calls) == 2
    assert calls[1][1] is AdversarialSourceOpinionReviewsRepairDraft
    assert calls[1][2] == 850
    assert [item.source_id for item in result.source_opinion_reviews] == [first_id, second_id]
    assert result.source_opinion_repair_attempted is True
    assert result.source_opinion_repair_status == "completed"
    assert result.source_opinion_repaired_ids == [second_id]
    assert all(item.source_excerpt for item in result.source_opinion_reviews)
    assert all(item.evidence_validation_status == "verified" for item in result.source_opinion_reviews)
    assert not any("has no R3 review" in flag for flag in result.source_reference_integrity_flags)


def test_source_opinion_repair_failure_remains_flagged(monkeypatch):
    from app.round_schemas import (
        Round2ContributionDraft,
        Round2SourceOpinionResponsesRepairDraft,
    )
    from app.services import mdt_generation

    case = SyntheticCase(
        scenario_title="R2 repair failure remains visible",
        case_summary=(
            "Fictional case. The surgical oncology note favours a surgery-led assessment first, "
            "conditional on complete local staging and resectability review."
        ),
    )
    async def fake_generate(prompt, schema_type, max_tokens):
        if schema_type is Round2ContributionDraft:
            return Round2ContributionDraft(
                position="insufficient_information",
                provisional_conclusion="The case does not establish a definitive pathway.",
                response_to_other_perspectives="The supplied peer views do not establish an option.",
                agreements=[], substantive_challenges=[], remaining_unknowns=[], risk_flags=[], confidence=0.4,
                source_opinion_responses=[],
            )
        assert schema_type is Round2SourceOpinionResponsesRepairDraft
        raise RuntimeError("synthetic repair inference failure")

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    result = asyncio.run(
        mdt_generation.generate_debate_contribution(
            {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review educational options."},
            case,
            {"position": "insufficient_information", "provisional_conclusion": "No pathway is established.", "preferred_educational_option": "None established."},
            [],
        )
    )
    assert result.source_opinion_repair_attempted is True
    assert result.source_opinion_repair_status == "failed"
    assert any("source-opinion repair failed" in flag for flag in result.source_reference_integrity_flags)
    assert any("no structured response" in flag for flag in result.source_reference_integrity_flags)
