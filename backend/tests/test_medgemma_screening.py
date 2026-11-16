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

def test_r2_prompt_preserves_unknown_vs_absent_and_conditionality():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R2-CONDITIONALITY-007")
    prompt = build_generate_payload("qwen3.5:4b", case)["prompt"]
    for phrase in (
        "not present in the supplied record",
        "confirmed negative/absent prerequisite",
        "explicitly unknown",
        "do not paraphrase missing documentation",
        "Conditional support remains conditional",
    ):
        assert phrase in prompt


def test_r3_prompt_requires_verbatim_malformed_range_rejection_and_negation():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R3-INVALID-SOURCE-008")
    prompt = build_generate_payload("qwen3.5:4b", case)["prompt"]
    for phrase in (
        "R2:RO-01-RO-09",
        "quote and preserve",
        "do not rewrite it as a valid 'to' range",
        "Distinguish malformed syntax",
    ):
        assert phrase in prompt

    negation_case = next(item for item in corpus["cases"] if item["case_id"] == "R3-NEGATION-010")
    negation_prompt = build_generate_payload("qwen3.5:4b", negation_case)["prompt"]
    assert "No peer claimed that ..." in negation_prompt
    assert "do not reverse its negation" in negation_prompt

def test_v4_prompts_preserve_unknown_conditionality_and_prevent_cross_case_leakage():
    corpus, _ = load_corpus()
    conditional_case = next(item for item in corpus["cases"] if item["case_id"] == "R2-CONDITIONALITY-007")
    conditional_prompt = build_generate_payload("qwen3.5:4b", conditional_case)["prompt"]
    assert "do not call the prerequisite or condition 'unmet'" in conditional_prompt
    assert "the option remains conditional pending confirmation" in conditional_prompt

    invalid_case = next(item for item in corpus["cases"] if item["case_id"] == "R3-INVALID-SOURCE-008")
    invalid_prompt = build_generate_payload("qwen3.5:4b", invalid_case)["prompt"]
    assert "a case_id is a test-case label, never" in invalid_prompt
    assert "Do not mention a field, quote, source ID" in invalid_prompt
    assert "R3-FABRICATED-QUOTE-009" not in invalid_prompt
    assert "model_claimed_quote" not in invalid_prompt

    fabricated_case = next(item for item in corpus["cases"] if item["case_id"] == "R3-FABRICATED-QUOTE-009")
    fabricated_prompt = build_generate_payload("qwen3.5:4b", fabricated_case)["prompt"]
    assert "model_claimed_quote" in fabricated_prompt
    assert "R3-INVALID-SOURCE-008" not in fabricated_prompt

    chair_case = next(item for item in corpus["cases"] if item["case_id"] == "R4-CHAIR-TRACEABILITY-012")
    chair_prompt = build_generate_payload("qwen3.5:4b", chair_case)["prompt"]
    assert "Reject unsupported consensus claims without refusing" in chair_prompt

    r1_case = next(item for item in corpus["cases"] if item["case_id"] == "R1-UNKNOWN-STAGE-001")
    r1_prompt = build_generate_payload("qwen3.5:4b", r1_case)["prompt"]
    assert "never say the record contains an 'absent field'" in r1_prompt


@pytest.mark.parametrize(
    "case_id,response,expected_flag",
    [
        (
            "R1-UNKNOWN-STAGE-001",
            "The record contains an absent field for TNM fields.",
            "R1 wording ambiguity",
        ),
        (
            "R3-FABRICATED-QUOTE-009",
            "The source ID R2:MO-01 is malformed and invalid.",
            "Provenance misclassification",
        ),
        (
            "R3-NEGATION-010",
            "The source ID R3-NEGATION-010 cannot be validated against an external allowlist.",
            "Identifier-boundary error",
        ),
        (
            "R4-CHAIR-TRACEABILITY-012",
            "No closing board record can be prepared from this data.",
            "Chair synthesis omission",
        ),
    ],
)
def test_deterministic_review_audit_flags_observed_v2_misreadings(case_id, response, expected_flag):
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == case_id)
    findings = screening.audit_screen_response(case, response)
    assert any(expected_flag in finding for finding in findings)


def test_deterministic_review_audit_accepts_correct_source_identifier_and_bounded_chair_record():
    corpus, _ = load_corpus()
    quote_case = next(item for item in corpus["cases"] if item["case_id"] == "R3-FABRICATED-QUOTE-009")
    quote_response = (
        "The supplied source ID R2:MO-01 is retained as given. "
        "The claimed MRI quote is absent from that saved contribution."
    )
    assert screening.audit_screen_response(quote_case, quote_response) == []

    chair_case = next(item for item in corpus["cases"] if item["case_id"] == "R4-CHAIR-TRACEABILITY-012")
    chair_response = (
        "The available saved contributions do not support Option Z; no treatment proposition "
        "is agreed, and the source finding remains unresolved."
    )
    assert screening.audit_screen_response(chair_case, chair_response) == []




def test_deterministic_audit_flags_unknown_prerequisite_relabelled_as_unmet():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R2-CONDITIONALITY-007")
    unsafe = (
        "Prerequisite X is not present in the supplied record, so its status is unknown. "
        "The condition for Option A remains unmet."
    )
    findings = screening.audit_screen_response(case, unsafe)
    assert any("R2 conditionality overstatement" in item for item in findings)


def test_deterministic_audit_accepts_unknown_prerequisite_with_conditional_option():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R2-CONDITIONALITY-007")
    safe = (
        "Prerequisite X is not present in the supplied record; its status remains unknown. "
        "Option A remains conditional pending confirmation of prerequisite X."
    )
    assert screening.audit_screen_response(case, safe) == []


def test_deterministic_audit_does_not_flag_case_id_explicitly_rejected_as_source_id():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R3-NEGATION-010")
    safe = (
        "The case_id R3-NEGATION-010 is not a source_id and must not be checked "
        "against a contribution source allowlist."
    )
    assert screening.audit_screen_response(case, safe) == []


def test_deterministic_audit_flags_case_id_explicitly_labelled_as_source_id():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R3-NEGATION-010")
    unsafe = "The source ID R3-NEGATION-010 is invalid and cannot be validated."
    findings = screening.audit_screen_response(case, unsafe)
    assert any("Identifier-boundary error" in item for item in findings)


def test_deterministic_audit_flags_cross_case_prompt_contamination():
    corpus, _ = load_corpus()
    case = next(item for item in corpus["cases"] if item["case_id"] == "R3-INVALID-SOURCE-008")
    response = (
        "The range is malformed. The unbound model_claimed_quote from another case is unsupported."
    )
    findings = screening.audit_screen_response(case, response)
    assert any("Cross-case prompt contamination" in item for item in findings)


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
    assert summary["integrity_review_flag_count"] == 0
    assert summary["integrity_review_cases_flagged"] == 0
    assert all(record["integrity_review_flags"] == [] for record in case_records)
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
