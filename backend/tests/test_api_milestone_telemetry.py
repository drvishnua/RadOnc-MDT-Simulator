import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SyntheticCase
from app.round_schemas import FinalMDTReport
from app.services import run_store

client = TestClient(app)


def _setup_test_run():
    case = SyntheticCase(
        scenario_title="Synthetic Oropharynx Milestone Case",
        case_summary="Fictional oropharyngeal SCC for milestone telemetry integration testing.",
        primary_site="oropharynx",
        histology="Squamous cell carcinoma",
    )
    run = run_store.create_run(case)
    run_id = run["run_id"]
    return run_id, case


def _record_round_in_db(run_id: str, round_number: int, agent_id: str, result_dict: dict, duration_seconds: float = 12.0):
    now = run_store._now()
    with run_store._connect() as db:
        run_store._ensure_round_tables(db)
        db.execute(
            """
            INSERT OR REPLACE INTO round_runs
            (run_id, round_number, total_agents, status, created_at, updated_at)
            VALUES (?, ?, ?, 'completed', ?, ?)
            """,
            (run_id, round_number, 1, now, now),
        )
        db.execute(
            """
            INSERT OR REPLACE INTO agent_round_results
            (run_id, round_number, agent_id, agent_name, category_label, status, result_json, completed_at, duration_seconds)
            VALUES (?, ?, ?, ?, 'RadOnc', 'completed', ?, ?, ?)
            """,
            (run_id, round_number, agent_id, agent_id, json.dumps(result_dict), now, duration_seconds),
        )


def test_api_run_telemetry_and_completed_at():
    run_id, _ = _setup_test_run()

    _record_round_in_db(
        run_id, 1, "RO-01",
        {"position": "supports", "provisional_conclusion": "Test conclusion"},
        duration_seconds=12.5,
    )

    # Directly set mdt_finished_at to verify completed_at mapping and wall-clock calculation
    with run_store._connect() as db:
        db.execute(
            "UPDATE simulation_runs SET mdt_finished_at = '2026-11-24T18:00:00+00:00', created_at = '2026-11-24T17:50:00+00:00' WHERE run_id = ?",
            (run_id,),
        )

    response = client.get(f"/api/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["run_id"] == run_id
    assert data["completed_at"] == "2026-11-24T18:00:00+00:00"
    assert data["mdt_finished_at"] == "2026-11-24T18:00:00+00:00"
    assert data["round_status"] == {"1": "completed"}
    assert data["wall_clock_runtime_seconds"] == 600.0  # 10 minutes
    assert data["all_agents_required"] is True
    assert len(data["case_snapshot_sha256"]) == 64


def test_api_round_quality_audit_inline_citations_and_telemetry():
    run_id, _ = _setup_test_run()

    audit_payload = {
        "round_number": 1,
        "total_flags": 0,
        "inline_citations_audited": 12,
        "verified_inline_citations": ["ASTRO-HN-2024", "NCCN-HN-2024", "QUANTEC-2010"],
        "unverified_inline_citations": [],
        "inline_citation_concordance_rate": 1.0,
        "telemetry_summary": {
            "total_prompt_tokens": 3200,
            "total_output_tokens": 1450,
            "avg_tokens_per_second": 16.8,
            "total_retries": 0,
            "total_schema_failures": 0,
            "wall_clock_seconds": 124.7,
        },
    }

    run_store.save_round_quality_audit(run_id, 1, audit_payload)

    response = client.get(f"/api/runs/{run_id}/rounds/1/quality-audit")
    assert response.status_code == 200
    data = response.json()

    assert data["run_id"] == run_id
    assert data["round_number"] == 1
    assert data["has_audit"] is True

    audit = data["quality_audit"]
    assert audit["inline_citations_audited"] == 12
    assert "ASTRO-HN-2024" in audit["verified_inline_citations"]
    assert audit["unverified_inline_citations"] == []
    assert audit["inline_citation_concordance_rate"] == 1.0
    assert audit["telemetry_summary"]["avg_tokens_per_second"] == 16.8
    assert audit["telemetry_summary"]["wall_clock_seconds"] == 124.7


def test_api_final_chair_report_and_title_integrity():
    run_id, _ = _setup_test_run()

    report = FinalMDTReport(
        run_id=run_id,
        round_number=4,
        report_title="MDT Chair Synthesis: oropharynx — Squamous cell carcinoma",
        consensus_status="insufficient_information",
        chair_conclusion="No treatment recommendation can be made from the supplied case.",
        overall_educational_synthesis="Fictional case for API contract validation.",
        consensus_points=[],
        unresolved_disagreements=[],
        minority_and_dissenting_views=[
            "No genuine conditional/minority position identified. Stable uncertainty preserved in uncertainties."
        ],
        major_uncertainties=[
            "Definitive dental clearance pending.",
            "Baseline speech-language swallowing assessment pending.",
        ],
        missing_information_before_real_world_review=[
            "HPV / p16 immunohistochemistry status",
        ],
        patient_and_family_considerations=["Requires swallowing evaluation"],
        feasibility_and_resource_considerations=["Access to dental clinic"],
        governance_and_safeguarding_considerations=["Standard MDT educational oversight"],
        evidence_limitations=["Simulation evidence retrieval only"],
        chair_reflection="Sufficient clinical facts missing to reach therapeutic consensus.",
        evidence_retrieval_connected=True,
        safety_boundary="educational_simulation_only",
        not_a_treatment_instruction=True,
    )

    _record_round_in_db(
        run_id, 4, "SG-07",
        report.model_dump(),
        duration_seconds=13.55,
    )

    response = client.get(f"/api/runs/{run_id}/report")
    assert response.status_code == 200
    data = response.json()

    assert data["report_title"] == "MDT Chair Synthesis: oropharynx — Squamous cell carcinoma"
    assert "T3N2" not in data["report_title"]  # Fact-grounded: no unconfirmed staging
    assert data["consensus_status"] == "insufficient_information"
    assert len(data["major_uncertainties"]) == 2
    assert len(data["minority_and_dissenting_views"]) == 1
    assert data["safety_boundary"] == "educational_simulation_only"
    assert data["not_a_treatment_instruction"] is True
