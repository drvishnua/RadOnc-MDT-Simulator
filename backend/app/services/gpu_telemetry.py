"""Pure helpers for sampled NVIDIA and Ollama GPU-inference telemetry."""

from __future__ import annotations

import csv
import io
from typing import Any


def parse_nvidia_smi_csv(output: str) -> list[dict[str, Any]]:
    """Parse nvidia-smi CSV output without units; preserve unknown values as None."""
    parsed: list[dict[str, Any]] = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) < 5:
            continue

        def number(value: str) -> float | None:
            try:
                return float(value.strip())
            except (TypeError, ValueError):
                return None

        name = row[0].strip()
        if not name or name.casefold() == "n/a":
            continue
        parsed.append({
            "name": name,
            "memory_used_mib": number(row[1]),
            "memory_total_mib": number(row[2]),
            "gpu_utilization_percent": number(row[3]),
            "memory_utilization_percent": number(row[4]),
        })
    return parsed


def summarize_gpu_telemetry(
    samples: list[dict[str, Any]],
    ollama_process_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Require both in-run GPU activity and Ollama GPU allocation for a positive finding."""
    devices = [
        device
        for sample in samples
        for device in sample.get("gpus", [])
        if isinstance(device, dict)
    ]
    util_values = [
        float(device["gpu_utilization_percent"])
        for device in devices
        if isinstance(device.get("gpu_utilization_percent"), (int, float))
    ]
    memory_values = [
        float(device["memory_used_mib"])
        for device in devices
        if isinstance(device.get("memory_used_mib"), (int, float))
    ]

    ollama_gpu_allocation = False
    observed_vram_bytes: list[int] = []
    for entry in ollama_process_snapshots:
        snapshot = entry.get("snapshot", {})
        if not isinstance(snapshot, dict):
            continue
        api_ps = snapshot.get("api_ps", {})
        if isinstance(api_ps, dict):
            for model in api_ps.get("models", []):
                if not isinstance(model, dict):
                    continue
                try:
                    vram = int(model.get("size_vram") or 0)
                except (TypeError, ValueError):
                    vram = 0
                if vram > 0:
                    ollama_gpu_allocation = True
                    observed_vram_bytes.append(vram)

        cli_ps = str(snapshot.get("cli_ps") or "")
        for line in cli_ps.splitlines()[1:]:
            upper = line.upper()
            if "GPU" in upper and ("%" in upper or "GB" in upper or "MIB" in upper):
                ollama_gpu_allocation = True

    active_samples = sum(value > 0 for value in util_values)
    active_inference_observed = active_samples > 0 and ollama_gpu_allocation
    return {
        "nvidia_smi_sample_count": len(samples),
        "gpu_device_sample_count": len(devices),
        "nonzero_gpu_utilization_sample_count": active_samples,
        "peak_gpu_utilization_percent": max(util_values) if util_values else None,
        "peak_memory_used_mib": max(memory_values) if memory_values else None,
        "ollama_gpu_allocation_observed": ollama_gpu_allocation,
        "max_ollama_vram_allocation_bytes": max(observed_vram_bytes) if observed_vram_bytes else None,
        "active_gpu_inference_observed": active_inference_observed,
        "verification_note": (
            "Confirmed by non-zero NVIDIA GPU utilisation sampled during the run and "
            "Ollama reporting GPU-backed model allocation."
            if active_inference_observed
            else "GPU inference is not verified: both in-run non-zero GPU utilisation and "
            "Ollama GPU allocation must be observed."
        ),
    }
