from app.services.gpu_telemetry import (
    extract_ollama_telemetry,
    generation_telemetry_ctx,
    parse_nvidia_smi_csv,
    record_current_telemetry,
    summarize_gpu_telemetry,
)


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

def test_live_four_round_validation_script_parses_without_execution():
    import ast
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "live_four_round_validation.py"
    source = script.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(script))
    assert "validate_consensus_points(report)" in source
    required_sections = next(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "required_report_sections" for target in node.targets)
    )
    assert "consensus_points" not in ast.literal_eval(required_sections)


def test_extract_ollama_telemetry_computes_tokens_per_second():
    payload = {
        "prompt_eval_count": 520,
        "prompt_eval_duration": 400_000_000,
        "eval_count": 250,
        "eval_duration": 5_000_000_000,
        "total_duration": 5_600_000_000,
    }
    extracted = extract_ollama_telemetry(payload)
    assert extracted["prompt_tokens"] == 520
    assert extracted["output_tokens"] == 250
    # 250 tokens / 5 seconds = 50.0 tokens/second
    assert extracted["tokens_per_second"] == 50.0
    assert extracted["eval_duration_ns"] == 5_000_000_000
    assert extracted["total_duration_ns"] == 5_600_000_000


def test_extract_ollama_telemetry_handles_zero_duration_and_missing():
    payload = {
        "eval_count": 100,
        "eval_duration": 0,
    }
    extracted = extract_ollama_telemetry(payload)
    assert extracted["tokens_per_second"] is None
    assert extracted["prompt_tokens"] is None


def test_record_current_telemetry_updates_context_dict():
    tracker = {"retries": 0}
    token = generation_telemetry_ctx.set(tracker)
    try:
        record_current_telemetry({
            "prompt_eval_count": 120,
            "eval_count": 80,
            "eval_duration": 2_000_000_000,
        })
        assert tracker["prompt_tokens"] == 120
        assert tracker["output_tokens"] == 80
        assert tracker["tokens_per_second"] == 40.0
        assert tracker["retries"] == 0
    finally:
        generation_telemetry_ctx.reset(token)
