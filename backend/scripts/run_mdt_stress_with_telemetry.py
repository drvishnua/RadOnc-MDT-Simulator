"""Run the synthetic MDT stress suite while continuously sampling GPU/Ollama telemetry.

Telemetry is observational only: it does not change model settings or concurrency.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts" / "stress_suite" / "runner_diagnostics"
GPU_QUERY = (
    "timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total,"
    "power.draw,power.limit,temperature.gpu,clocks.gr,clocks.mem"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ollama_ps() -> dict:
    try:
        request = urllib.request.Request("http://127.0.0.1:11434/api/ps", method="GET")
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = []
        for model in payload.get("models", []):
            models.append({
                "name": model.get("name"),
                "size": model.get("size"),
                "size_vram": model.get("size_vram"),
                "context_length": model.get("context_length"),
                "expires_at": model.get("expires_at"),
            })
        return {"reachable": True, "models": models}
    except Exception as exc:
        return {"reachable": False, "error": f"{type(exc).__name__}: {exc}"}


def sample_gpu() -> dict:
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={GPU_QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        line = result.stdout.strip().splitlines()[0]
        values = [part.strip() for part in next(csv.reader([line]))]
        keys = GPU_QUERY.split(",")
        return {"available": True, **dict(zip(keys, values))}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-ids", required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    if args.interval < 0.5:
        parser.error("--interval must be at least 0.5 seconds")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = ARTIFACT_DIR / "gpu_telemetry.csv"
    json_path = ARTIFACT_DIR / "gpu_telemetry_summary.json"
    stdout_path = ARTIFACT_DIR / "stress_stdout.log"
    stderr_path = ARTIFACT_DIR / "stress_stderr.log"
    stop = threading.Event()
    samples: list[dict] = []
    ps_samples: list[dict] = []
    lock = threading.Lock()
    started = utc_now()

    def monitor() -> None:
        last_ps = 0.0
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = None
            while not stop.is_set():
                now = time.monotonic()
                sample = {"sampled_at_utc": utc_now(), **sample_gpu()}
                with lock:
                    samples.append(sample)
                if writer is None:
                    fields = list(sample.keys())
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                writer.writerow(sample)
                handle.flush()
                if now - last_ps >= 5.0:
                    ps_samples.append({"sampled_at_utc": sample["sampled_at_utc"], **ollama_ps()})
                    last_ps = now
                stop.wait(args.interval)

    monitor_thread = threading.Thread(target=monitor, name="gpu-telemetry", daemon=True)
    monitor_thread.start()
    command = [
        sys.executable, "scripts/run_mdt_stress_suite.py",
        "--case-ids", args.case_ids,
    ]
    process_started = time.perf_counter()
    try:
        with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
            child = subprocess.Popen(
                command, cwd=BACKEND_DIR, stdout=out, stderr=err,
                text=True, env=os.environ.copy(),
            )
            exit_code = child.wait()
    finally:
        stop.set()
        monitor_thread.join(timeout=10)

    valid = [item for item in samples if item.get("available")]
    util_values = []
    for item in valid:
        try:
            util_values.append(float(item["utilization.gpu"]))
        except (KeyError, TypeError, ValueError):
            pass
    summary = {
        "schema_version": 1,
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "sample_interval_seconds": args.interval,
        "sample_count": len(samples),
        "valid_gpu_sample_count": len(valid),
        "gpu_utilization_percent": {
            "min": min(util_values) if util_values else None,
            "max": max(util_values) if util_values else None,
            "mean": round(sum(util_values) / len(util_values), 2) if util_values else None,
        },
        "ollama_ps_samples": ps_samples,
        "stress_suite_exit_code": exit_code,
        "interpretation_limitations": [
            "Samples are periodic snapshots, not per-token measurements.",
            "Ollama /api/ps reports model residency/offload allocation, not proof of active GPU computation.",
            "GPU utilisation and clocks are system-wide and may include unrelated GPU workloads.",
            "Power/temperature/clocks may be unavailable on some laptop power-management configurations.",
            "No model, context, temperature, token budget, or concurrency settings are changed by this wrapper.",
        ],
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"GPU_TELEMETRY_CSV={csv_path}")
    print(f"GPU_TELEMETRY_SUMMARY={json_path}")
    print(f"STRESS_SUITE_EXIT_CODE={exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
