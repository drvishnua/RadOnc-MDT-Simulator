"""Validate the synthetic model-screening corpus structure (not model accuracy)."""

from __future__ import annotations

import json
from pathlib import Path


CORPUS_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "medgemma_model_integrity_screening_v1.json"
)


def test_model_integrity_screening_corpus_is_explicitly_synthetic():
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    assert corpus["corpus_id"] == "radonc-mdt-model-integrity-screening"
    assert corpus["version"] == "1.0.0"
    assert corpus["synthetic_only"] is True
    assert corpus["clinical_validation"] is False
    assert "not clinical cases" in corpus["purpose"]


def test_model_integrity_screening_corpus_has_unique_complete_cases():
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    cases = corpus["cases"]

    assert len(cases) >= 10
    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))

    required_categories = {
        "unsupported_staging_inference",
        "fabricated_patient_or_case_facts",
        "silent_contradiction_resolution",
        "untrusted_case_text",
        "false_proposition_consensus",
        "overbroad_consensus",
        "dropped_prerequisite",
        "fabricated_or_malformed_provenance",
        "unbound_source_quote",
        "negation_and_false_positive",
        "fabricated_missing_contribution",
        "untraceable_chair_synthesis",
    }
    assert {case["category"] for case in cases} == required_categories

    for case in cases:
        assert case["synthetic_only"] is True
        assert case["round"] in {"R1", "R2", "R3", "R4"}
        assert isinstance(case["input"], dict) and case["input"]
        assert case["expected_behaviour"]
        assert case["critical_failure_conditions"]


def test_corpus_does_not_claim_to_be_a_clinical_gold_standard():
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    assert corpus["clinical_validation"] is False
    assert "does not automatically determine clinical correctness" in corpus[
        "scoring_warning"
    ]
