import asyncio
import json

from app.schemas import SyntheticCase
from scripts import run_mdt_stress_suite as stress


def test_checkpoint_json_is_atomically_written(tmp_path):
    target = tmp_path / "nested" / "checkpoint.json"

    stress.persist_json_atomic(target, {"stage": "R2_completed", "rounds": ["R1", "R2"]})

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "stage": "R2_completed",
        "rounds": ["R1", "R2"],
    }
    assert not target.with_name(target.name + ".tmp").exists()


def test_run_one_persists_partial_state_and_exception_details(monkeypatch):
    case = SyntheticCase(
        scenario_title="Synthetic checkpoint test",
        case_summary="Fictional case used only to test stress-run recovery.",
    )
    monkeypatch.setattr(stress.run_store, "create_run", lambda _case: {"run_id": "synthetic-run"})
    monkeypatch.setattr(stress, "gpu_snapshot", lambda: "test GPU snapshot")

    async def fail_r1(_run_id):
        raise RuntimeError("intentional synthetic R1 failure")

    monkeypatch.setattr(stress.batch_runner, "run_independent_assessments", fail_r1)
    monkeypatch.setattr(stress.run_store, "list_results", lambda _run_id: [
        {"agent_id": "RO-01", "status": "completed", "assessment": {"position": "insufficient_information"}}
    ])

    progress = []
    result = asyncio.run(stress.run_one(
        {"case_id": "MDT-TEST", "case": case, "oracle_checks": []},
        on_progress=lambda snapshot: progress.append(json.loads(json.dumps(snapshot))),
    ))

    assert result["status"] == "failed_or_incomplete"
    assert result["exception_type"] == "RuntimeError"
    assert result["exception_message"] == "intentional synthetic R1 failure"
    assert result["failed_at_stage"] == "R1_inference"
    assert result["last_completed_stage"] == "exception_captured"
    assert result["partial_round_1"][0]["agent_id"] == "RO-01"
    assert result["gpu_snapshots"]["at_failure"] == "test GPU snapshot"
    assert [entry["last_completed_stage"] for entry in progress] == [
        "run_created",
        "run_created",
        "exception_captured",
    ]
    assert progress[1]["current_stage"] == "R1_inference"
