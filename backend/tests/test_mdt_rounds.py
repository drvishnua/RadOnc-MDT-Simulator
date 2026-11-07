import asyncio

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

    r3 = client.post(f"/api/runs/{run_id}/rounds/3")
    assert r3.status_code == 200
    r3_summary = client.get(f"/api/runs/{run_id}/rounds/3").json()
    assert r3_summary["status"] == "completed"
    assert r3_summary["completed_count"] == 45

    r4 = client.post(f"/api/runs/{run_id}/rounds/4")
    assert r4.status_code == 200
    report = client.get(f"/api/runs/{run_id}/report")
    assert report.status_code == 200
    assert report.json()["not_a_treatment_instruction"] is True
    assert report.json()["evidence_retrieval_connected"] is False
    assert report.json()["report_title"] == "MDT Chair Synthesis: Larynx — Squamous cell carcinoma"


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


def test_r2_and_r3_prompts_require_source_linked_peer_engagement(monkeypatch):
    from app.round_schemas import RoundContributionDraft
    from app.services import mdt_generation

    prompts = []

    async def fake_generate(prompt, schema_type, max_tokens):
        prompts.append(prompt)
        return RoundContributionDraft(
            position="conditional",
            provisional_conclusion="The educational position remains conditional because source information is incomplete.",
            response_to_other_perspectives="The reviewed peer material was considered by source ID; no unsupported agreement is inferred.",
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Complete staging remains unknown."],
            risk_flags=["Do not infer stage from incomplete data."],
            confidence=0.5,
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {"agent_id": "RO-01", "name": "Radiation Oncology", "mandate": "Review educational radiotherapy considerations."}
    case = SyntheticCase(
        scenario_title="Synthetic attributed-opinion case",
        case_summary=(
            "Fictional case. Surgical note favours surgical assessment first, conditional on local staging. "
            "Medical oncology note favours discussion of preoperative multimodality sequencing, conditional on MRI and fitness."
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
            "unknowns": ["MRI staging is not supplied."],
        },
    }]
    asyncio.run(mdt_generation.generate_debate_contribution(profile, case, own, peer_r1))
    assert "R1:SO-01" in prompts[0]
    assert "Surgery-led assessment" in prompts[0]
    assert "Record an agreement only when" in prompts[0]
    assert "bounded sample of at most 15 of 44 other roles" in prompts[0]
    assert "Shared uncertainty about prerequisites" in prompts[0]
    assert "surgery-first/surgical-assessment" in prompts[0]
    assert "Agreement that information is missing does not establish agreement on an option" in prompts[0]

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
            "substantive_challenges": ["R1:SO-01 — local staging prerequisite remains unresolved."],
            "risk_flags": ["Do not assume resectability."],
        },
    }]
    asyncio.run(mdt_generation.generate_adversarial_contribution(profile, case, own, own_r2, peer_r2))
    assert "R2:MO-01" in prompts[1]
    assert "local staging prerequisite remains unresolved" in prompts[1]
    assert "For every substantive challenge, name its exact source" in prompts[1]
    assert "state whether its option and conditions are preserved" in prompts[1]
    assert "Silence or a generic statement that staging is missing is not proof of preservation" in prompts[1]
    assert "Risk flags are not substitutes" in prompts[1]
    assert "COMPLETE own R2 record" in prompts[1]
    assert "The surgical assessment and multimodality options remain distinct" in prompts[1]
    assert "CASE:case_summary — do not collapse the two conditional options" in prompts[1]
    assert "bounded sample of at most 5 of 44 other roles" in prompts[1]


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
            "result": {
                "position": "conditional",
                "provisional_conclusion": "The position remains conditional pending missing information.",
            },
        }
        for profile in AGENT_PROFILES
    ]
    selected = mdt_rounds._select_peer_views(current, rows, "result", max_total=5)
    assert len(selected) <= 5
    assert all(item["agent_id"] != current["agent_id"] for item in selected)
    assert all("result" in item for item in selected)


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
