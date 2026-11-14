"""Regression tests for the short Ollama context-allocation acceptance probe."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_DIR.parent
SCRIPT_PATH = BACKEND_DIR / "scripts" / "ollama_context_allocation_probe.py"
SPEC = importlib.util.spec_from_file_location("ollama_context_allocation_probe", SCRIPT_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_probe_verifies_cold_6144_load_then_8192_resize(monkeypatch):
    state = {"loaded": False, "context": None}
    calls = []

    def fake_request(url, *, payload=None, timeout=30.0):
        calls.append((url, payload))
        if url.endswith("/api/ps"):
            models = []
            if state["loaded"]:
                models.append({"name": "qwen3.5:4b", "model": "qwen3.5:4b", "context_length": state["context"]})
            return {"models": models}
        assert url.endswith("/api/generate")
        if payload.get("keep_alive") == 0:
            state.update(loaded=False, context=None)
            return {"response": ""}
        state.update(loaded=True, context=payload["options"]["num_ctx"])
        return {
            "response": "RADONC_CONTEXT_PROBE_OK",
            "total_duration": 100,
            "load_duration": 50,
        }

    monkeypatch.setattr(probe, "_request_json", fake_request)
    report = probe.run_context_allocation_probe(
        "http://127.0.0.1:11435",
        "qwen3.5:4b",
        sleep_seconds=0,
    )

    assert report["status"] == "passed"
    assert [item["actual_context_length"] for item in report["context_checks"]] == [6144, 8192]
    assert report["context_allocation_verified"] is True
    assert [payload["options"]["num_ctx"] for _, payload in calls if payload and "options" in payload] == [6144, 8192]


def test_probe_fails_if_ollama_does_not_resize_to_requested_context(monkeypatch):
    state = {"context": None}

    def fake_request(url, *, payload=None, timeout=30.0):
        if url.endswith("/api/ps"):
            return {"models": [] if state["context"] is None else [
                {"name": "qwen3.5:4b", "context_length": state["context"]}
            ]}
        if payload.get("keep_alive") == 0:
            state["context"] = None
            return {"response": ""}
        requested = payload["options"]["num_ctx"]
        if requested == 6144:
            state["context"] = 6144
        # Simulate a runner that remains at 6144 when 8192 is requested.
        return {"response": "RADONC_CONTEXT_PROBE_OK"}

    monkeypatch.setattr(probe, "_request_json", fake_request)

    with pytest.raises(RuntimeError, match="context_length=6144.*num_ctx=8192"):
        probe.run_context_allocation_probe(
            "http://127.0.0.1:11435",
            "qwen3.5:4b",
            sleep_seconds=0,
        )


def test_probe_rejects_missing_or_ambiguous_loaded_model_entries():
    assert probe._loaded_model({"models": []}, "qwen3.5:4b") is None
    assert probe._loaded_model(
        {"models": [{"name": "QWEN3.5:4B", "context_length": 6144}]},
        "qwen3.5:4b",
    )["context_length"] == 6144
    with pytest.raises(RuntimeError, match="multiple loaded entries"):
        probe._loaded_model(
            {"models": [
                {"name": "qwen3.5:4b"},
                {"model": "qwen3.5:4b"},
            ]},
            "qwen3.5:4b",
        )


def test_workflow_exposes_context_probe_without_running_eight_call_mdt():
    workflow = (
        REPOSITORY_ROOT
        / ".github"
        / "workflows"
        / "windows-installer.yml"
    ).read_text(encoding="utf-8")

    assert "validation_mode:" in workflow
    assert "- context_probe" in workflow
    assert "$validationMode -ne \"context_probe\"" in workflow
    assert "HOSTED_CPU_WARMUP_SKIPPED_FOR_COLD_CONTEXT_PROBE" in workflow
    assert "python scripts/ollama_context_allocation_probe.py" in workflow
    assert "if ($validationMode -eq \"context_probe\")" in workflow
    assert "python scripts/representative_model_provenance_validation.py" in workflow
    assert "name: ollama-context-allocation-probe" in workflow
    assert "HOSTED_OLLAMA_CONTEXT_ALLOCATION_PROBE_OK" in workflow
    assert "github.event_name == 'push' && contains(github.event.head_commit.message, '[context-probe]')" in workflow
