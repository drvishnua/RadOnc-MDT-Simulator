"""Regression tests for read-only saved-run quality diagnostics."""
from __future__ import annotations

import copy
import hashlib

from scripts.saved_run_quality_diagnostics import build_diagnostics


def _export():
    return {
        "run": {"run_id": "synthetic-run", "status": "completed"},
        "case_snapshot_sha256": "snapshot-hash",
        "case_snapshot": {"primary_site": "glottis", "histology": "SCC", "case_summary": "75-year-old with a 1 cm lesion"},
        "independent_assessments": [
            {"agent_id": "RO-01", "status": "completed", "assessment": {
                "position": "conditional", "provisional_conclusion": "T1N0M0 glottic cancer",
                "perspective_summary": "Needs staging", "preferred_educational_option": "RT",
                "case_facts": ["age 75"], "assumptions": [], "unknowns": ["stage"],
                "discussion_options": ["RT"], "evidence_claims": [], "evidence_gaps": ["guideline source"],
            }},
            {"agent_id": "RO-02", "status": "completed", "assessment": {
                "position": "conditional", "provisional_conclusion": "T1N0M0 glottic cancer",
                "perspective_summary": "Needs staging", "preferred_educational_option": "RT",
                "case_facts": ["age 75"], "assumptions": [], "unknowns": ["stage"],
                "discussion_options": ["RT"], "evidence_claims": [], "evidence_gaps": ["guideline source"],
            }},
            {"agent_id": "RO-03", "status": "failed", "assessment": None},
        ],
        "debate": [
            {"agent_id": "RO-01", "status": "completed", "result": {
                "position": "conditional", "provisional_conclusion": "More staging is needed",
                "response_to_other_perspectives": "The supplied opinions differ.",
                "agreements": [], "substantive_challenges": [], "position_changes": [],
                "remaining_unknowns": ["stage"], "risk_flags": [],
            }},
        ],
        "adversarial_review": [
            {"agent_id": "RO-01", "status": "completed", "result": {
                "position": "insufficient_information", "provisional_conclusion": "Cannot conclude",
                "response_to_other_perspectives": "The source needs review.",
                "agreements": [], "substantive_challenges": [], "position_changes": [],
                "remaining_unknowns": ["stage"], "risk_flags": ["unsupported stage"],
            }},
        ],
    }


def test_diagnostics_are_read_only_and_retain_input_hash():
    export = _export()
    before = copy.deepcopy(export)
    raw = b'{"fixture": true}'
    result = build_diagnostics(export, raw)
    assert export == before
    assert result["source"]["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["scope"]["model_inference_performed"] is False
    assert result["scope"]["clinical_correctness_assessed"] is False


def test_counts_missing_evidence_and_empty_structured_debate_without_inference():
    result = build_diagnostics(_export(), b"fixture")
    assert result["rounds"]["R1"]["completed_payload_rows"] == 2
    assert result["rounds"]["R1"]["distinct_identified_roles"] == 2
    assert result["rounds"]["R1"]["field_population"]["evidence_claims"] == {
        "populated_roles": 0, "empty_or_missing_roles": 2,
    }
    assert result["rounds"]["R2"]["field_population"]["substantive_challenges"] == {
        "populated_roles": 0, "empty_or_missing_roles": 1,
    }


def test_exact_duplicate_is_separate_from_near_duplicate_and_flagged_not_adjudicated():
    result = build_diagnostics(_export(), b"fixture")
    exact = [x for x in result["text_similarity"] if x["kind"] == "exact_duplicate"]
    assert any(x["round"] == "R1" and x["field"] == "provisional_conclusion" for x in exact)
    assert result["summary"]["near_duplicate_candidate_pairs"] == 0
    assert result["staging_reference_flags"]
    assert all(x["reason"] == "no_structured_stage_field_available"
               for x in result["staging_reference_flags"])


def test_near_duplicate_threshold_is_configurable_and_similarity_is_not_a_quality_verdict():
    export = _export()
    export["independent_assessments"][1]["assessment"]["provisional_conclusion"] = (
        "T1N0M0 glottic carcinoma requiring assessment"
    )
    result = build_diagnostics(export, b"fixture", near_duplicate_threshold=0.1)
    candidates = [x for x in result["text_similarity"] if x["kind"] == "near_duplicate_candidate"]
    assert candidates
    assert result["scope"]["near_duplicate_interpretation"] == "triage_signal_only_not_proof_of_copying"


def test_stage_audit_ignores_narrative_and_uses_only_structured_stage_fields():
    export = _export()
    export["case_snapshot"]["case_summary"] = "The narrative mentions T1N0M0 but this is not structured staging."
    result = build_diagnostics(export, b"fixture")
    assert result["staging_reference_flags"]
    assert all(item["reason"] == "no_structured_stage_field_available"
               for item in result["staging_reference_flags"])

    export["case_snapshot"]["clinical_stage"] = "T1N0M0"
    result = build_diagnostics(export, b"fixture")
    assert result["staging_reference_flags"] == []


def test_stage_audit_detects_partial_tnm_tokens():
    export = _export()
    export["independent_assessments"][0]["assessment"]["provisional_conclusion"] = "T1N0 glottic cancer"
    export["independent_assessments"][1]["assessment"]["provisional_conclusion"] = "T1a disease; M0"
    result = build_diagnostics(export, b"fixture")
    tokens = {item["token"].upper() for item in result["staging_reference_flags"]}
    assert {"T1N0", "T1A", "M0"} <= tokens


def test_malformed_round_collection_is_reported_as_zero_rows_not_crashing():
    result = build_diagnostics({"run": {}, "independent_assessments": "bad"}, b"fixture")
    assert result["rounds"]["R1"]["source_rows"] == 0
    assert result["rounds"]["R1"]["completed_payload_rows"] == 0
