"""Probe whether Ollama honours context-size changes across successive requests.

This is a short synthetic infrastructure check, not an MDT or clinical validation.
It cold-loads the configured model at the application's 6144-token R1/R2 context,
then requests 8192 for R3 and verifies the actual loaded runner via /api/ps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL  # noqa: E402

ARTIFACT_PATH = BACKEND_DIR / "validation_artifacts" / "ollama_context_allocation_probe.json"
CONTEXT_SEQUENCE = (6144, 8192)
MODEL_UNLOAD_TIMEOUT_SECONDS = 30.0


def _request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise RuntimeError(f"Ollama returned a non-object JSON response from {url}.")
    return decoded


def _snapshot(base_url: str) -> dict[str, Any]:
    return _request_json(f"{base_url.rstrip('/')}/api/ps", timeout=10.0)


def _loaded_model(snapshot: dict[str, Any], model: str) -> dict[str, Any] | None:
    models = snapshot.get("models")
    if not isinstance(models, list):
        raise RuntimeError("Ollama /api/ps response has no models array.")
    matches = [
        item
        for item in models
        if isinstance(item, dict)
        and any(
            isinstance(item.get(key), str)
            and item[key].casefold() == model.casefold()
            for key in ("name", "model")
        )
    ]
    if len(matches) > 1:
        raise RuntimeError(f"Ollama /api/ps returned multiple loaded entries for {model}.")
    return matches[0] if matches else None


def _context_length(entry: dict[str, Any] | None) -> int | None:
    if entry is None:
        return None
    value = entry.get("context_length")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def run_context_allocation_probe(
    base_url: str,
    model: str,
    *,
    requested_contexts: tuple[int, ...] = CONTEXT_SEQUENCE,
    sleep_seconds: float = 1.0,
    unload_timeout_seconds: float = MODEL_UNLOAD_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL.")
    if not model.strip():
        raise ValueError("OLLAMA_MODEL must be configured.")
    if requested_contexts != CONTEXT_SEQUENCE:
        raise ValueError("The acceptance probe must test the application sequence 6144 then 8192.")

    started_at = datetime.now(timezone.utc).isoformat()
    initial = _snapshot(base_url)
    initial_entry = _loaded_model(initial, model)

    if initial_entry is not None:
        _request_json(
            f"{base_url.rstrip('/')}/api/generate",
            payload={"model": model, "keep_alive": 0, "stream": False},
            timeout=30.0,
        )
        deadline = time.monotonic() + unload_timeout_seconds
        while time.monotonic() < deadline:
            if _loaded_model(_snapshot(base_url), model) is None:
                break
            time.sleep(sleep_seconds)
        else:
            raise RuntimeError("Ollama did not unload the model before the cold context probe.")

    checks: list[dict[str, Any]] = []
    for requested_context in requested_contexts:
        generation = _request_json(
            f"{base_url.rstrip('/')}/api/generate",
            payload={
                "model": model,
                "prompt": "Reply with exactly this token: RADONC_CONTEXT_PROBE_OK",
                "stream": False,
                "think": False,
                "keep_alive": "5m",
                "options": {
                    "temperature": 0,
                    "num_predict": 16,
                    "num_ctx": requested_context,
                },
            },
            timeout=600.0,
        )
        response_text = generation.get("response")
        if not isinstance(response_text, str) or "RADONC_CONTEXT_PROBE_OK" not in response_text:
            raise RuntimeError(
                f"Ollama inference did not return the expected marker at num_ctx={requested_context}."
            )

        after = _snapshot(base_url)
        loaded = _loaded_model(after, model)
        actual_context = _context_length(loaded)
        check = {
            "requested_context_length": requested_context,
            "actual_context_length": actual_context,
            "context_matches": actual_context == requested_context,
            "response_chars": len(response_text),
            "total_duration_ns": generation.get("total_duration"),
            "load_duration_ns": generation.get("load_duration"),
            "process_snapshot": after,
        }
        checks.append(check)
        if actual_context != requested_context:
            raise RuntimeError(
                f"Ollama loaded context_length={actual_context!r} after num_ctx={requested_context}."
            )

    return {
        "status": "passed",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "probe_type": "cold_load_6144_then_resize_8192",
        "initial_process_snapshot": initial,
        "context_checks": checks,
        "context_allocation_verified": True,
        "clinical_accuracy_evaluated": False,
        "full_mdt_executed": False,
        "gpu_measured": False,
    }


def main() -> int:
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = run_context_allocation_probe(OLLAMA_BASE_URL, OLLAMA_MODEL)
    except Exception as exc:
        report = {
            "status": "failed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "probe_type": "cold_load_6144_then_resize_8192",
            "context_allocation_verified": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "clinical_accuracy_evaluated": False,
            "full_mdt_executed": False,
            "gpu_measured": False,
        }
    ARTIFACT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
