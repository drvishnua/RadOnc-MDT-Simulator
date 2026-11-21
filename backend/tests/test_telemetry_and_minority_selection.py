"""Tests for P2 rich performance telemetry and Chair minority selection."""

import json
from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services import run_store
from app.services.chair_report_quality import ensure_chair_report_completeness


def _empty_report() -> FinalMDTReport:
    return FinalMDTReport(
        run_id="synthetic-run",
        report_title="Synthetic Chair report",
        consensus_status="insufficient_information",
        chair_conclusion=(
            "No treatment recommendation can be made from the supplied synthetic information."
        ),
        overall_educational_synthesis="The source contributions require cautious interpretation.",
        consensus_points=[],
        unresolved_disagreements=[],
        minority_and_dissenting_views=[],
        major_uncertainties=[],
        missing_information_before_real_world_review=[],
        patient_and_family_considerations=[],
        feasibility_and_resource_considerations=[],
        governance_and_safeguarding_considerations=[],
        evidence_limitations=[],
        chair_reflection="This is a structural educational synthesis, not clinical validation.",
    )


def test_round_telemetry_persistence_and_summary_aggregation(tmp_path, monkeypatch):
    db_file = tmp_path / "test_telemetry.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_file)
    run_store.initialize_database()

    # Create synthetic patient and run
    case = SyntheticCase(scenario_title="Telemetry test", case_summary="Fictional case.")
    run = run_store.create_run(case)
    run_id = run["run_id"]

    # Seed a round_run for testing telemetry persistence and summary aggregations
    now = run_store._now()
    with run_store._connect() as db:
        run_store._ensure_round_tables(db)
        db.execute(
            """
            INSERT INTO round_runs (run_id, round_number, status, total_agents, started_at, created_at, updated_at)
            VALUES (?, 2, 'running', 2, ?, ?, ?)
            """,
            (run_id, now, now, now),
        )
        db.execute(
            """
            INSERT INTO agent_round_results (run_id, round_number, agent_id, agent_name, category_label, status)
            VALUES (?, 2, 'RO-01', 'Specialist 1', 'Radiation Oncology', 'running'),
                   (?, 2, 'RO-02', 'Specialist 2', 'Medical Oncology', 'running')
            """,
            (run_id, run_id),
        )

    # Save completed agent results with telemetry
    res1 = {
        "agent_id": "RO-01",
        "round_number": 2,
        "position": "conditional",
        "provisional_conclusion": "Conditional position based on margin status.",
        "preferred_educational_option": "SBRT with clear margins",
    }
    run_store.save_round_success(
        run_id, 2, "RO-01", json.dumps(res1), 2.5,
        prompt_tokens=400, output_tokens=200, tokens_per_second=40.0,
        retries=0, schema_failures=0,
    )

    res2 = {
        "agent_id": "RO-02",
        "round_number": 2,
        "position": "supports",
        "provisional_conclusion": "Supportive stance following guideline review.",
        "preferred_educational_option": "Conventional radiotherapy",
    }
    run_store.save_round_success(
        run_id, 2, "RO-02", json.dumps(res2), 3.0,
        prompt_tokens=450, output_tokens=150, tokens_per_second=30.0,
        retries=1, schema_failures=1,
    )

    # Verify list_round_results exposes telemetry
    results = run_store.list_round_results(run_id, 2)
    by_id = {r["agent_id"]: r for r in results}
    assert by_id["RO-01"]["prompt_tokens"] == 400
    assert by_id["RO-01"]["output_tokens"] == 200
    assert by_id["RO-01"]["tokens_per_second"] == 40.0
    assert by_id["RO-01"]["retries"] == 0
    assert by_id["RO-01"]["schema_failures"] == 0

    assert by_id["RO-02"]["prompt_tokens"] == 450
    assert by_id["RO-02"]["output_tokens"] == 150
    assert by_id["RO-02"]["tokens_per_second"] == 30.0
    assert by_id["RO-02"]["retries"] == 1
    assert by_id["RO-02"]["schema_failures"] == 1

    # Mark round finished and verify summary aggregations
    run_store.mark_round_finished(run_id, 2)
    summary = run_store.get_round_summary(run_id, 2)

    assert summary["total_prompt_tokens"] == 850
    assert summary["total_output_tokens"] == 350
    assert summary["avg_tokens_per_second"] == 35.0
    assert summary["total_retries"] == 1
    assert summary["total_schema_failures"] == 1
    assert summary["position_distribution"] == {"conditional": 1, "supports": 1}
    assert summary["wall_clock_seconds"] is not None
    assert summary["wall_clock_seconds"] >= 0.0


def test_round1_batch_telemetry_persistence(tmp_path, monkeypatch):
    db_file = tmp_path / "test_r1_telemetry.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_file)
    run_store.initialize_database()

    case = SyntheticCase(scenario_title="R1 Telemetry test", case_summary="Fictional case.")
    run = run_store.create_run(case)
    run_id = run["run_id"]

    # Save agent result with telemetry
    assessment_payload = {
        "agent_id": "RO-01",
        "round_number": 1,
        "position": "supports",
        "provisional_conclusion": "Standard assessment based on available facts.",
        "preferred_educational_option": "Definitive chemoradiation",
        "perspective_summary": "Summary of perspective.",
        "confidence": 0.85,
    }
    run_store.save_agent_success(
        run_id, "RO-01", json.dumps(assessment_payload), 1.8,
        prompt_tokens=320, output_tokens=180, tokens_per_second=45.0,
        retries=0, schema_failures=0,
    )

    results = run_store.list_results(run_id)
    by_id = {r["agent_id"]: r for r in results}
    assert by_id["RO-01"]["prompt_tokens"] == 320
    assert by_id["RO-01"]["output_tokens"] == 180
    assert by_id["RO-01"]["tokens_per_second"] == 45.0
    assert by_id["RO-01"]["retries"] == 0
    assert by_id["RO-01"]["schema_failures"] == 0


def test_minority_selection_highlights_material_challenges():
    case = SyntheticCase(
        scenario_title="Minority challenge test",
        case_summary="Fictional case for testing material challenge inclusion in minority views.",
    )

    # 44 supports, 1 conditional with material challenges
    round1 = [
        {
            "agent_id": f"RO-{i+1:02d}",
            "agent_name": f"Specialist {i+1}",
            "status": "completed",
            "assessment": {
                "position": "conditional" if i == 0 else "supports",
                "provisional_conclusion": "Conditional on node staging" if i == 0 else "Supports standard pathway",
            },
        }
        for i in range(45)
    ]
    round2 = [
        {
            "agent_id": f"RO-{i+1:02d}",
            "agent_name": f"Specialist {i+1}",
            "status": "completed",
            "result": {
                "position": "conditional" if i == 0 else "supports",
                "provisional_conclusion": "Maintains conditional stance" if i == 0 else "Reiterates support",
                "substantive_challenges": [
                    "Challenge: nodal metastasis risk was underestimated by peer assessment."
                ] if i == 0 else [],
            },
        }
        for i in range(45)
    ]
    round3 = [
        {
            "agent_id": f"RO-{i+1:02d}",
            "agent_name": f"Specialist {i+1}",
            "status": "completed",
            "result": {
                "position": "conditional" if i == 0 else "supports",
                "provisional_conclusion": "Final conditional recommendation" if i == 0 else "Consensus support",
                "substantive_challenges": [
                    "R3 Challenge: margin clearance not proven on histology."
                ] if i == 0 else [],
            },
        }
        for i in range(45)
    ]

    report = ensure_chair_report_completeness(_empty_report(), case, round1, round2, round3)

    # RO-01 should be in minority views with challenges highlighted
    minority_text = " ".join(report.minority_and_dissenting_views)
    assert "RO-01" in minority_text
    assert "nodal metastasis risk was underestimated" in minority_text
    assert "margin clearance not proven" in minority_text
