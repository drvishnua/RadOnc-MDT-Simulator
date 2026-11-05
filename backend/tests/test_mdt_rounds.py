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
    assert report.json()["report_title"] == "Synthetic MDT educational synthesis"


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
    assert report.consensus_points
    assert "not unanimous agreement" in report.consensus_points[0]
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
    assert "descriptive, not votes" in " ".join(report.consensus_points)
    assert report.chair_conclusion.startswith("No treatment recommendation can be made")

