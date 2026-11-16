"""No-inference regression tests for the 12-case Ollama screening harness."""

import json

import pytest

import scripts.run_medgemma_screening as screening

from scripts.run_medgemma_screening import (
    build_case_prompt,
    build_generate_payload,
    extract_raw_model_response,
    load_corpus,
    require_installed_model_record,
    validate_model_response,
)


def test_frozen_screening_corpus_loads_12_unique_synthetic_cases():
    corpus, digest = load_corpus()
    assert corpus["synthetic_only"] is True
    assert corpus["clinical_validation"] is False
    assert len(corpus["cases"]) == 12
    assert len({case["case_id"] for case in corpus["cases"]}) == 12
    assert len(digest) == 64


def test_prompt_does_not_leak_expected_behaviour_or_critical_failure_labels():
    corpus, _ = load_corpus()
    for case in corpus["cases"]:
        prompt = build_case_prompt(case)
        assert case["case_id"] in prompt
        assert "expected_behaviour" not in prompt
        assert "critical_failure_conditions" not in prompt
        for expected in case["expected_behaviour"]:
            assert expected not in prompt
        for failure in case["critical_failure_conditions"]:
            assert failure not in prompt


def test_round_specific_prompt_instructions_are_present():
    corpus, _ = load_corpus()
    prompts = {case["round"]: build_case_prompt(case) for case in corpus["cases"]}
    assert "independent role-level reading" in prompts["R1"]
    assert "positions relate to one another" in prompts["R2"]
    assert "critical audit of source-linked statements" in prompts["R3"]
    assert "closing board record" in prompts["R4"]


def test_generate_payload_pins_identical_deterministic_options():
    corpus, _ = load_corpus()
    case = corpus["cases"][0]
    qwen = build_generate_payload("qwen3.5:4b", case)
    medgemma = build_generate_payload("medgemma1.5:4b-it-q4_K_M", case)

    assert qwen["prompt"] == medgemma["prompt"]
    assert qwen["system"] == medgemma["system"]
    assert qwen["options"] == medgemma["options"]
    assert qwen["options"]["temperature"] == 0
    assert qwen["options"]["seed"] == 73
    assert qwen["stream"] is False
    assert qwen["format"]["required"] == ["response"]


def test_model_registry_requires_one_exact_model_and_full_digest():
    model = "medgemma1.5:4b-it-q4_K_M"
    digest = "sha256:" + ("a" * 64)
    record = require_installed_model_record(
        {"models": [{"name": model, "model": model, "digest": digest}]},
        model,
    )
    assert record["digest"] == digest


@pytest.mark.parametrize(
    "reported_digest",
    [
        "a" * 64,
        "A" * 64,
        "sha256:" + ("A" * 64),
        "SHA256:" + ("a" * 64),
    ],
)
def test_model_registry_normalizes_bare_and_prefixed_full_sha256_digests(reported_digest):
    model = "qwen3.5:4b"
    record = require_installed_model_record(
        {"models": [{"name": model, "model": model, "digest": reported_digest}]},
        model,
    )
    assert record["digest"] == "sha256:" + ("a" * 64)


@pytest.mark.parametrize(
    "models",
    [
        [],
        [{"name": "medgemma1.5:4b-it-q4_K_M", "digest": "433252621ab1"}],
        [
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": "sha256:" + ("b" * 64)},
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": "sha256:" + ("c" * 64)},
        ],
        [
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": "sha256:" + ("g" * 64)},
        ],
        [
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": " " + ("a" * 64)},
        ],
    ],
)
def test_model_registry_rejects_missing_short_or_ambiguous_records(models):
    with pytest.raises(RuntimeError):
        require_installed_model_record({"models": models}, "medgemma1.5:4b-it-q4_K_M")



@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"response":"Recorded uncertainty."}', {"response": "Recorded uncertainty."}),
        ("[]", None),
        ('{"other":"value"}', None),
        ('{"response":42}', None),
        ('{"response":" "}', None),
        ("not json", None),
        (None, None),
    ],
)
def test_screen_response_requires_exact_nonempty_response_string(raw, expected):
    parsed, error = validate_model_response(raw)
    if expected is None:
        assert parsed is None
        assert error
    else:
        assert parsed == expected
        assert error is None



def test_raw_model_response_is_preserved_when_post_generation_checks_fail():
    raw = '{"response":"The supplied record does not establish this fact."}'
    assert extract_raw_model_response({"response": raw}) == raw
    assert extract_raw_model_response({"error": "late digest mismatch"}) is None
    assert extract_raw_model_response(None) is None
def _installed_model_tags(model_name, digest):
    return {
        "models": [
            {
                "name": model_name,
                "model": model_name,
                "digest": digest,
                "size": 3_300_000_000,
                "details": {"quantization_level": "Q4_K_M"},
            }
        ]
    }


def test_run_screen_records_complete_immutable_case_set(tmp_path, monkeypatch):
    model_name = "medgemma1.5:4b-it-q4_K_M"
    digest = "a" * 64  # Ollama /api/tags may return the full digest without a prefix.
    canonical_digest = "sha256:" + digest
    calls = {"tags": 0, "generate": 0, "show": 0, "version": 0}

    def fake_read_json(url, *, body=None, timeout=30):
        if url.endswith("/api/version"):
            calls["version"] += 1
            return {"version": "0.40.14"}
        if url.endswith("/api/tags"):
            calls["tags"] += 1
            return _installed_model_tags(model_name, digest)
        if url.endswith("/api/show"):
            calls["show"] += 1
            assert body == {"model": model_name, "verbose": True}
            return {"modelfile": "FROM synthetic-test"}
        if url.endswith("/api/generate"):
            calls["generate"] += 1
            assert timeout == 240
            assert body["model"] == model_name
            assert body["options"] == screening.GENERATION_OPTIONS
            return {
                "response": json.dumps(
                    {"response": "The synthetic record does not establish this."}
                ),
                "done": True,
                "total_duration": 1_000_000,
                "eval_count": 7,
            }
        raise AssertionError(f"Unexpected Ollama endpoint: {url}")

    monkeypatch.setattr(screening, "_read_json", fake_read_json)
    output = tmp_path / "screen.jsonl"

    assert screening.run_screen(model_name, output, "http://ollama.test") == 0

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    case_records = [record for record in records if record["record_type"] == "case_result"]
    preflight = next(record for record in records if record["record_type"] == "preflight")
    summary = next(record for record in records if record["record_type"] == "summary")

    assert calls == {"tags": 25, "generate": 12, "show": 1, "version": 1}
    assert len(case_records) == 12
    assert len({record["case_id"] for record in case_records}) == 12
    assert all(record["status"] == "response_recorded" for record in case_records)
    assert all(record["model_digest"] == canonical_digest for record in case_records)
    assert all(record["post_generation_model_digest"] == canonical_digest for record in case_records)
    assert all(record["response_parsed"] == {
        "response": "The synthetic record does not establish this."
    } for record in case_records)
    assert all(record["ollama_metrics"]["total_duration"] == 1_000_000 for record in case_records)
    assert preflight["model_metadata_captured"] is True
    assert preflight["model_digest"] == canonical_digest
    assert summary["responses_recorded"] == 12
    assert summary["failed_or_malformed"] == 0
    assert summary["status"] == "completed_pending_human_review"
    assert summary["automatic_quality_score"] is None
    assert summary["gpu_measurement"] == "NOT_PERFORMED"

    # Evidence paths are immutable: a second run cannot replace this artifact.
    with pytest.raises(FileExistsError):
        screening.run_screen(model_name, output, "http://ollama.test")


def test_run_screen_stops_before_generation_when_digest_changes(tmp_path, monkeypatch):
    model_name = "qwen3.5:4b"
    original_digest = "sha256:" + ("a" * 64)
    changed_digest = "sha256:" + ("b" * 64)
    calls = {"tags": 0, "generate": 0}

    def fake_read_json(url, *, body=None, timeout=30):
        if url.endswith("/api/version"):
            return {"version": "0.40.14"}
        if url.endswith("/api/tags"):
            calls["tags"] += 1
            digest = original_digest if calls["tags"] == 1 else changed_digest
            return _installed_model_tags(model_name, digest)
        if url.endswith("/api/show"):
            return {"modelfile": "FROM synthetic-test"}
        if url.endswith("/api/generate"):
            calls["generate"] += 1
            return {"response": '{"response":"must not be generated"}'}
        raise AssertionError(f"Unexpected Ollama endpoint: {url}")

    monkeypatch.setattr(screening, "_read_json", fake_read_json)
    output = tmp_path / "digest-drift-before.jsonl"

    assert screening.run_screen(model_name, output, "http://ollama.test") == 1

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    case_record = next(record for record in records if record["record_type"] == "case_result")
    summary = next(record for record in records if record["record_type"] == "summary")

    assert calls == {"tags": 2, "generate": 0}
    assert case_record["status"] == "inference_error"
    assert case_record["response_raw"] is None
    assert "changed before this generation" in case_record["error"]
    assert summary["responses_recorded"] == 0
    assert summary["failed_or_malformed"] == 1
    assert summary["status"] == "incomplete_or_malformed"


def test_run_screen_preserves_raw_response_when_digest_changes_after_generation(
    tmp_path, monkeypatch
):
    model_name = "medgemma1.5:4b-it-q4_K_M"
    original_digest = "sha256:" + ("a" * 64)
    changed_digest = "sha256:" + ("c" * 64)
    raw_response = '{"response":"Raw generated output retained for audit."}'
    calls = {"tags": 0, "generate": 0}

    def fake_read_json(url, *, body=None, timeout=30):
        if url.endswith("/api/version"):
            return {"version": "0.40.14"}
        if url.endswith("/api/tags"):
            calls["tags"] += 1
            digest = changed_digest if calls["tags"] == 3 else original_digest
            return _installed_model_tags(model_name, digest)
        if url.endswith("/api/show"):
            return {"modelfile": "FROM synthetic-test"}
        if url.endswith("/api/generate"):
            calls["generate"] += 1
            return {
                "response": raw_response,
                "total_duration": 2_000_000,
                "eval_count": 11,
            }
        raise AssertionError(f"Unexpected Ollama endpoint: {url}")

    monkeypatch.setattr(screening, "_read_json", fake_read_json)
    output = tmp_path / "digest-drift-after.jsonl"

    assert screening.run_screen(model_name, output, "http://ollama.test") == 1

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    case_record = next(record for record in records if record["record_type"] == "case_result")
    summary = next(record for record in records if record["record_type"] == "summary")

    assert calls == {"tags": 3, "generate": 1}
    assert case_record["status"] == "inference_error"
    assert case_record["model_digest"] == original_digest
    assert case_record["post_generation_model_digest"] == changed_digest
    assert case_record["response_raw"] == raw_response
    assert case_record["ollama_metrics"]["total_duration"] == 2_000_000
    assert case_record["ollama_metrics"]["eval_count"] == 11
    assert summary["responses_recorded"] == 1
    assert summary["failed_or_malformed"] == 1
    assert summary["status"] == "incomplete_or_malformed"
