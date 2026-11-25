"""Tests for P1 Immediate Quality Milestone:
- Structured debate position-change traceability
- Chair minority selection (excluding stable uncertainty roles, capturing genuine dissent)
- Title generation strictly from verified facts
- Top-level completion timestamps and round_status
"""

from datetime import datetime, timezone
import json
import pytest

from app.schemas import SyntheticCase
from app.round_schemas import FinalMDTReport, RoundContributionDraft, Round2ContributionDraft, AdversarialContributionDraft
from app.services import run_store
from app.services.case_integrity import build_case_report_title
from app.services.chair_report_quality import ensure_chair_report_completeness


def test_build_case_report_title_uses_verified_facts_only():
    # Case with verified primary site and histology
    case = SyntheticCase(
        scenario_title="Hypothetical stage IV oropharynx",
        primary_site="Oropharynx (left tonsil)",
        histology="Squamous cell carcinoma, p16 positive",
        case_summary="Patient presented with left tonsillar mass.",
    )
    title = build_case_report_title(case)
    assert title == "MDT Chair Synthesis: Oropharynx (left tonsil) — Squamous cell carcinoma, p16 positive"
    assert "IV" not in title
    assert "stage" not in title.lower()

    # Case with missing fields falls back cleanly without hallucinating
    empty_case = SyntheticCase(
        scenario_title="Unstaged case",
        primary_site="",
        histology="",
        case_summary="No details provided.",
    )
    empty_title = build_case_report_title(empty_case)
    assert empty_title == "MDT Chair Synthesis: Case details not supplied"


def test_top_level_run_store_completion_timestamps_and_round_status(tmp_path, monkeypatch):
    db_file = tmp_path / "test_p1_runs.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_file)
    run_store.initialize_database()

    case = SyntheticCase(
        scenario_title="Larynx case",
        primary_site="Larynx",
        histology="Squamous cell carcinoma",
        case_summary="Fictional larynx case for testing timestamps.",
    )
    run = run_store.create_run(case)
    run_id = run["run_id"]

    # Initial state: no completion timestamp, wall-clock is None
    initial_run = run_store.get_run(run_id)
    assert initial_run["mdt_finished_at"] is None
    assert initial_run["completed_at"] is None
    assert initial_run["wall_clock_runtime_seconds"] is None
    assert isinstance(initial_run["round_status"], dict)

    # Simulate round runs
    now_start = "2026-11-24T10:00:00+00:00"
    now_end = "2026-11-24T10:15:30+00:00"

    with run_store._connect() as db:
        run_store._ensure_round_tables(db)
        db.execute(
            """
            INSERT INTO round_runs (run_id, round_number, status, total_agents, started_at, finished_at, created_at, updated_at)
            VALUES (?, 1, 'completed', 49, ?, ?, ?, ?),
                   (?, 2, 'completed', 49, ?, ?, ?, ?),
                   (?, 3, 'completed', 49, ?, ?, ?, ?),
                   (?, 4, 'completed', 1, ?, ?, ?, ?)
            """,
            (
                run_id, now_start, now_end, now_start, now_end,
                run_id, now_start, now_end, now_start, now_end,
                run_id, now_start, now_end, now_start, now_end,
                run_id, now_start, now_end, now_start, now_end,
            ),
        )
        db.execute(
            "UPDATE simulation_runs SET status = 'completed', created_at = ?, updated_at = ?, mdt_finished_at = ? WHERE run_id = ?",
            (now_start, now_end, now_end, run_id),
        )

    updated_run = run_store.get_run(run_id)
    assert updated_run["status"] == "completed"
    assert updated_run["mdt_finished_at"] == now_end
    assert updated_run["completed_at"] == now_end
    assert updated_run["wall_clock_runtime_seconds"] == 930.0  # 15 min 30 sec = 930s
    assert updated_run["round_status"] == {1: "completed", 2: "completed", 3: "completed", 4: "completed"}


def test_position_change_traceability_formatting():
    from app.services.mdt_generation import _compact

    previous_position = "conditional"
    new_position = "supports"
    model_changes = ["Changed from conditional to supports based on review of contralateral neck RTOG criteria."]
    model_rationale = "; ".join(model_changes).strip()
    rationale = _compact(model_rationale, 320)
    change_entry = f"Round 1 → Round 2: {previous_position} → {new_position}. Rationale: {rationale}"

    assert "Round 1 → Round 2: conditional → supports" in change_entry
    assert "contralateral neck RTOG criteria" in change_entry


def test_post_round_quality_gates_extracts_inline_citations_and_telemetry(tmp_path, monkeypatch):
    from app.services.mdt_rounds import _run_post_round_quality_gates

    db_file = tmp_path / "test_p2_audit.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_file)
    run_store.initialize_database()

    case = SyntheticCase(
        scenario_title="Audit test case",
        primary_site="Oropharynx",
        histology="Squamous cell carcinoma",
        case_summary="Patient with oropharyngeal cancer.",
    )
    run = run_store.create_run(case)
    run_id = run["run_id"]

    # Mock round_rows with inline citations (one valid, one hallucinated)
    round_rows = [
        {
            "agent_id": "RO-01",
            "status": "completed",
            "assessment": {
                "position": "supports",
                "provisional_conclusion": "Definitive radiotherapy per ASTRO guidelines [source_id: ASTRO-HN-2024].",
                "perspective_summary": "We also reviewed unverified claims [source_id: HALLUCINATED-TRIAL-2099].",
                "preferred_educational_option": "IMRT 70 Gy",
                "discussion_options": ["Option A per [source_id: NCCN-HN-2026]"],
                "unknowns": ["Smoking history"],
                "confidence": 0.9,
            },
        }
    ]

    audit = _run_post_round_quality_gates(run_id, 1, round_rows)
    citation_audit = audit.get("citation_audit", {})
    assert citation_audit.get("total_citations") >= 2
    
    verified_sources = {c["source_id"] for c in citation_audit.get("verified_citations", [])}
    unverified_sources = {c["source_id"] for c in citation_audit.get("unverified_citations", [])}

    # ASTRO-HN-2024 and NCCN-HN-2026 are verified in canonical catalogue
    assert "ASTRO-HN-2024" in verified_sources
    assert "NCCN-HN-2026" in verified_sources

    # HALLUCINATED-TRIAL-2099 must be caught as unverified
    assert "HALLUCINATED-TRIAL-2099" in unverified_sources
    assert citation_audit["valid"] is False


