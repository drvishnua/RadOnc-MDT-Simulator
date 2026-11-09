from app.services.gpu_telemetry import parse_nvidia_smi_csv, summarize_gpu_telemetry


def test_parse_nvidia_smi_csv_preserves_gpu_utilisation_and_vram():
    parsed = parse_nvidia_smi_csv(
        "NVIDIA GeForce RTX 4060, 4096, 8192, 73, 28\n"
    )

    assert parsed == [{
        "name": "NVIDIA GeForce RTX 4060",
        "memory_used_mib": 4096.0,
        "memory_total_mib": 8192.0,
        "gpu_utilization_percent": 73.0,
        "memory_utilization_percent": 28.0,
    }]


def test_parse_nvidia_smi_csv_keeps_unavailable_fields_unknown():
    parsed = parse_nvidia_smi_csv(
        "NVIDIA GeForce RTX 4060, N/A, 8192, 0, N/A\n"
    )

    assert parsed[0]["memory_used_mib"] is None
    assert parsed[0]["memory_total_mib"] == 8192.0
    assert parsed[0]["gpu_utilization_percent"] == 0.0
    assert parsed[0]["memory_utilization_percent"] is None


def test_gpu_inference_is_not_verified_by_vram_allocation_alone():
    samples = [{
        "gpus": [{
            "name": "RTX 4060",
            "memory_used_mib": 4096.0,
            "gpu_utilization_percent": 0.0,
        }]
    }]
    snapshots = [{
        "snapshot": {"api_ps": {"models": [{"name": "qwen3.5:4b", "size_vram": 3_000_000_000}]}}
    }]

    result = summarize_gpu_telemetry(samples, snapshots)

    assert result["ollama_gpu_allocation_observed"] is True
    assert result["active_gpu_inference_observed"] is False


def test_gpu_inference_requires_activity_and_ollama_gpu_allocation():
    samples = [{
        "gpus": [{
            "name": "RTX 4060",
            "memory_used_mib": 4096.0,
            "gpu_utilization_percent": 73.0,
        }]
    }]
    snapshots = [{
        "snapshot": {"api_ps": {"models": [{"name": "qwen3.5:4b", "size_vram": 3_000_000_000}]}}
    }]

    result = summarize_gpu_telemetry(samples, snapshots)

    assert result["nonzero_gpu_utilization_sample_count"] == 1
    assert result["peak_gpu_utilization_percent"] == 73.0
    assert result["max_ollama_vram_allocation_bytes"] == 3_000_000_000
    assert result["active_gpu_inference_observed"] is True
