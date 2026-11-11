"""Import-path regression coverage for the hosted representative validation launcher."""

from __future__ import annotations

import asyncio
import runpy
import subprocess
import sys
from pathlib import Path


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
