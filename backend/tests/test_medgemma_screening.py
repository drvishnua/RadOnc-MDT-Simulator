"""No-inference regression tests for the 12-case Ollama screening harness."""

import json

import pytest

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
    "models",
    [
        [],
        [{"name": "medgemma1.5:4b-it-q4_K_M", "digest": "433252621ab1"}],
        [
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": "sha256:" + ("b" * 64)},
            {"name": "medgemma1.5:4b-it-q4_K_M", "digest": "sha256:" + ("c" * 64)},
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
