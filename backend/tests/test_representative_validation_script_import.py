"""Import-path regression coverage for the hosted representative validation launcher."""

from __future__ import annotations

import asyncio
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


def test_representative_validation_script_imports_from_repository_root_without_inference():
    backend_dir = Path(__file__).resolve().parents[1]
    repository_root = backend_dir.parent
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    probe = (
        "import runpy, sys\n"
        "runpy.run_path(sys.argv[1], run_name='representative_validation_import_probe')\n"
        "assert 'app.agents.catalog' in sys.modules\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", probe, str(script_path)],
        cwd=repository_root,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, (
        "The validation script must import the backend package when launched "
        "from the repository root, without starting Ollama inference.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )



def test_timed_call_invokes_async_callback_and_records_timing():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    namespace = runpy.run_path(
        str(script_path),
        run_name="representative_validation_timing_probe",
    )
    metrics = []

    async def generation():
        return {"status": "completed"}

    result = asyncio.run(
        namespace["_timed_call"]("R2:TEST", generation, metrics)
    )

    assert result == {"status": "completed"}
    assert len(metrics) == 1
    assert metrics[0]["stage"] == "R2:TEST"
    assert metrics[0]["status"] == "completed"
    assert metrics[0]["wall_seconds"] >= 0



def test_timed_call_records_failed_generation_attempt_and_cause():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    namespace = runpy.run_path(
        str(script_path),
        run_name="representative_validation_failure_timing_probe",
    )
    assert namespace["MAX_SECONDS_PER_GENERATION"] > namespace["GENERATION_REQUEST_TIMEOUT_SECONDS"]
    metrics = []

    async def generation():
        try:
            raise TimeoutError("synthetic underlying timeout")
        except TimeoutError as cause:
            raise RuntimeError("synthetic wrapped generation failure") from cause

    try:
        asyncio.run(namespace["_timed_call"]("R3:TEST", generation, metrics))
    except RuntimeError as exc:
        assert str(exc) == "synthetic wrapped generation failure"
    else:
        raise AssertionError("A failed generation must propagate its exception.")

    assert len(metrics) == 1
    assert metrics[0]["stage"] == "R3:TEST"
    assert metrics[0]["status"] == "failed"
    assert metrics[0]["error_type"] == "RuntimeError"
    assert metrics[0]["cause_type"] == "TimeoutError"
    assert metrics[0]["wall_seconds"] >= 0


def test_round_attempts_are_recorded_only_after_ollama_preflight():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    source = script_path.read_text(encoding="utf-8")
    preflight = source.index('if not payload["ollama_before"].get("version")')
    r2_attempt = source.index('payload["rounds_attempted"].append("R2")')
    r2_start = source.index("# Round 2:", preflight)
    r3_attempt = source.index('payload["rounds_attempted"].append("R3")')
    r3_start = source.index("# Round 3:", r2_start)

    assert '"rounds_attempted": []' in source
    assert preflight < r2_start < r2_attempt < r3_start < r3_attempt


def test_bounded_chair_records_are_saved_and_reloaded_without_bypassing_45_role_guard(tmp_path):
    from app.services import run_store

    backend_dir = Path(__file__).resolve().parents[1]
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    namespace = runpy.run_path(
        str(script_path),
        run_name="representative_validation_sqlite_persistence_probe",
    )
    roles = namespace["_role_rows"]()
    case = namespace["_build_case"]()
    r2_rows = [
        {
            "agent_id": role["agent_id"],
            "agent_name": role["name"],
            "status": "completed",
            "result": {
                "agent_id": role["agent_id"],
                "round_number": 2,
                "position": "insufficient_information",
                "provisional_conclusion": "The fictional case does not establish a definitive pathway.",
            },
        }
        for role in roles
    ]
    r3_rows = [
        {
            "agent_id": role["agent_id"],
            "agent_name": role["name"],
            "status": "completed",
            "result": {
                "agent_id": role["agent_id"],
                "round_number": 3,
                "position": "insufficient_information",
                "provisional_conclusion": "The fictional case still lacks the information needed for a definitive pathway.",
            },
        }
        for role in roles
    ]
    previous_db_path = run_store.DB_PATH
    previous_data_dir = run_store.DATA_DIR
    previous_legacy_path = run_store.LEGACY_DB_PATH

    saved = namespace["_persist_bounded_round_records"](
        case, roles, r2_rows, r3_rows, []
    )

    assert saved["run_summary"]["total_agents"] == 45
    assert saved["run_summary"]["patient_id"] is None
    assert len(saved["round1_rows"]) == 45
    assert sum(row["status"] == "completed" for row in saved["round1_rows"]) == 3
    assert {row["agent_id"] for row in saved["round2_rows"]} == {
        role["agent_id"] for role in roles
    }
    assert {row["agent_id"] for row in saved["round3_rows"]} == {
        role["agent_id"] for role in roles
    }
    assert all(row["status"] == "completed" and row["result"] for row in saved["round2_rows"])
    assert all(row["status"] == "completed" and row["result"] for row in saved["round3_rows"])
    assert saved["round_summaries"][2]["status"] == "completed"
    assert saved["round_summaries"][2]["total_agents"] == 3
    assert saved["round_summaries"][3]["status"] == "completed"
    assert saved["round_summaries"][3]["total_agents"] == 3
    assert "45 successful independent assessments" in saved["production_round2_guard"]
    assert saved["temporary_database_deleted"] is True
    assert not Path(saved["temporary_database_path"]).exists()
    assert run_store.DB_PATH == previous_db_path
    assert run_store.DATA_DIR == previous_data_dir
    assert run_store.LEGACY_DB_PATH == previous_legacy_path




def _coverage_gate():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    namespace = runpy.run_path(
        str(script_path),
        run_name="representative_validation_coverage_gate_probe",
    )
    return namespace["_chair_source_opinion_coverage_failures"]


def test_chair_source_opinion_coverage_gate_reads_dedicated_report_field():
    validate = _coverage_gate()
    expected = [
        {"source_id": "CASE:case_summary#1"},
        {"source_id": "CASE:case_summary#2"},
    ]
    coverage = [
        "R3 source-opinion review coverage — CASE:case_summary#1: "
        "3/3 roles supplied an exact source-bound review.",
        "R3 source-opinion review coverage — CASE:case_summary#2: "
        "3/3 roles supplied an exact source-bound review.",
    ]
    report = SimpleNamespace(
        source_opinion_review_coverage=coverage,
        unresolved_disagreements=[
            "No proposition-level consensus is established from the saved contributions.",
            "No Round-3 role saved a substantive_challenges entry.",
        ],
    )

    assert validate(report, expected, {"RO-01", "SO-02", "MO-01"}) == []


def test_chair_source_opinion_coverage_gate_rejects_coverage_left_in_disagreements():
    validate = _coverage_gate()
    expected = [{"source_id": "CASE:case_summary#1"}]
    misplaced = (
        "R3 source-opinion review coverage — CASE:case_summary#1: "
        "3/3 roles supplied an exact source-bound review."
    )
    report = SimpleNamespace(
        source_opinion_review_coverage=[],
        unresolved_disagreements=[misplaced],
    )

    failures = validate(report, expected, {"RO-01", "SO-02", "MO-01"})

    assert any(item["type"] == "chair_source_opinion_review_coverage" for item in failures)
    assert any(item["type"] == "chair_source_opinion_coverage_misplaced_in_disagreements" for item in failures)


def test_chair_source_opinion_coverage_gate_rejects_partial_distinct_role_coverage():
    validate = _coverage_gate()
    expected = [{"source_id": "CASE:case_summary#1"}]
    report = SimpleNamespace(
        source_opinion_review_coverage=[
            "R3 source-opinion review coverage — CASE:case_summary#1: "
            "2/3 roles supplied an exact source-bound review."
        ],
        unresolved_disagreements=["No proposition-level consensus is established."],
    )

    failures = validate(report, expected, {"RO-01", "SO-02", "MO-01"})

    assert len(failures) == 1
    assert failures[0]["type"] == "chair_source_opinion_review_coverage_incomplete"
