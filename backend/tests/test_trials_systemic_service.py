"""Tests for Landmark Trials and Systemic Therapy evidence service (U07, U09)."""
from __future__ import annotations

import pytest

from app.services.reference_catalogue import ReferenceEntry, audit_claim_citations, verify_citation
from app.services.trials_systemic_service import (
    format_systemic_context_for_specialist,
    format_trials_context_for_specialist,
    get_landmark_trials,
    get_protocol_by_id,
    get_systemic_protocols,
    get_trial_by_source_id,
    get_trials_as_reference_entries,
    load_landmark_trials,
    load_systemic_protocols,
)


def test_load_landmark_trials() -> None:
    """Verify that landmark trials load cleanly from JSON and have required attributes."""
    trials = load_landmark_trials(force_reload=True)
    assert len(trials) >= 20, f"Expected >= 20 landmark trials, got {len(trials)}"

    for trial in trials:
        assert "source_id" in trial and len(trial["source_id"]) >= 2
        assert "title" in trial and len(trial["title"]) >= 5
        assert trial.get("source_type") in ("trial", "review")
        assert "disease_site" in trial
        assert "doi_or_url" in trial and trial["doi_or_url"].startswith("http")
        assert "level_of_evidence" in trial
        assert "endpoints" in trial


def test_load_systemic_protocols() -> None:
    """Verify standard systemic chemotherapy / immunotherapy protocols."""
    protocols = load_systemic_protocols(force_reload=True)
    assert len(protocols) >= 8, f"Expected >= 8 systemic protocols, got {len(protocols)}"

    for proto in protocols:
        assert "protocol_id" in proto and proto["protocol_id"].isupper()
        assert "protocol_name" in proto
        assert "disease_site" in proto
        assert "clinical_indication" in proto
        assert "regimen_components" in proto and len(proto["regimen_components"]) > 0
        assert "eligibility_thresholds" in proto


def test_filter_trials_by_disease_site() -> None:
    """Verify site filtering across major oncologic domains."""
    hn_trials = get_landmark_trials(disease_site="Head & Neck")
    assert len(hn_trials) >= 5
    hn_ids = {t["source_id"] for t in hn_trials}
    assert "RTOG-9111" in hn_ids
    assert "EORTC-22931" in hn_ids
    assert "RTOG-9501" in hn_ids
    assert "BONNER-2006" in hn_ids

    lung_trials = get_landmark_trials(disease_site="Lung")
    assert len(lung_trials) >= 3
    lung_ids = {t["source_id"] for t in lung_trials}
    assert "PACIFIC" in lung_ids
    assert "RTOG-0617" in lung_ids
    assert "CONVERT" in lung_ids

    gi_trials = get_landmark_trials(disease_site="GI")
    assert len(gi_trials) >= 5
    gi_ids = {t["source_id"] for t in gi_trials}
    assert "CROSS" in gi_ids
    assert "CHECKMATE-577" in gi_ids
    assert "RAPIDO" in gi_ids
    assert "PRODIGE-23" in gi_ids
    assert "ACT-II" in gi_ids

    prostate_trials = get_landmark_trials(disease_site="Prostate")
    assert len(prostate_trials) >= 3
    prostate_ids = {t["source_id"] for t in prostate_trials}
    assert "STAMPEDE-RT" in prostate_ids
    assert "RTOG-9408" in prostate_ids
    assert "EORTC-22961" in prostate_ids


def test_get_trial_by_source_id() -> None:
    """Verify case-insensitive exact retrieval of individual trials."""
    pacific = get_trial_by_source_id("pacific")
    assert pacific is not None
    assert pacific["source_id"] == "PACIFIC"
    assert pacific["disease_site"] == "Lung"
    assert "durvalumab" in pacific["title"].lower()

    rtog_9111 = get_trial_by_source_id("RTOG-9111")
    assert rtog_9111 is not None
    assert "larynx" in rtog_9111["topics"]

    nonexistent = get_trial_by_source_id("DOES-NOT-EXIST")
    assert nonexistent is None


def test_get_protocol_by_id() -> None:
    """Verify retrieval of specific systemic protocols."""
    cis_hn = get_protocol_by_id("CISPLATIN-3WEEKLY-HNSCC")
    assert cis_hn is not None
    assert cis_hn["regimen_components"][0]["dose"] == 100
    assert "RTOG-9111" in cis_hn["landmark_evidence_link"]
    assert "CrCl >= 60" in cis_hn["eligibility_thresholds"]["creatinine_clearance"]

    cross_proto = get_protocol_by_id("CROSS-CARBO-PACLITAXEL")
    assert cross_proto is not None
    assert any(c["drug"] == "Paclitaxel" for c in cross_proto["regimen_components"])
    assert any(c["drug"] == "Carboplatin" for c in cross_proto["regimen_components"])


def test_trials_as_reference_entries_and_citation_audit() -> None:
    """Verify that all landmark trials conform to ReferenceEntry and integrate with citation auditing."""
    entries = get_trials_as_reference_entries()
    assert len(entries) >= 20

    # Ensure every entry validates as ReferenceEntry model
    for e in entries:
        assert isinstance(e, ReferenceEntry)
        assert e.source_type in ("trial", "review")
        assert len(e.key_passages) > 0

    # Test audit_claim_citations with authentic vs fabricated references
    claims = [
        {
            "role_id": "radiation_oncologist",
            "source_id": "RTOG-9111",
            "doi_or_url": "https://doi.org/10.1200/JCO.2012.43.6097",
            "claim": "Concurrent cisplatin CRT achieves 67% 10-year intact larynx preservation.",
        },
        {
            "role_id": "medical_oncologist",
            "source_id": "PACIFIC",
            "doi_or_url": "https://doi.org/10.1056/NEJMoa1809697",
            "claim": "Consolidation durvalumab significantly prolongs 5-year overall survival (HR 0.72).",
        },
        {
            "role_id": "medical_oncologist",
            "source_id": "FABRICATED-IMAGINARY-2099",
            "doi_or_url": "https://doi.org/10.1000/imaginary",
            "claim": "Fictional quadruplet therapy.",
        },
    ]

    audit_result = audit_claim_citations(claims, catalogue=entries)
    assert audit_result["total_citations"] == 3
    assert audit_result["verified_count"] == 2
    assert audit_result["unverified_count"] == 1
    assert audit_result["concordance_rate"] == 0.667
    assert audit_result["valid"] is False
    assert audit_result["unverified_citations"][0]["source_id"] == "FABRICATED-IMAGINARY-2099"


def test_format_trials_context_for_specialist() -> None:
    """Verify markdown context formatting for specialist prompt injection."""
    ctx = format_trials_context_for_specialist("Head & Neck")
    assert "### Landmark Clinical Trial Evidence (Head & Neck)" in ctx
    assert "[RTOG-9111]" in ctx
    assert "[EORTC-22931]" in ctx
    assert "https://doi.org/" in ctx


def test_format_systemic_context_for_specialist() -> None:
    """Verify systemic context formatting for specialist prompt injection."""
    ctx = format_systemic_context_for_specialist("Head & Neck")
    assert "### Standard Systemic Therapy Protocols (Head & Neck)" in ctx
    assert "CISPLATIN-3WEEKLY-HNSCC" in ctx
    assert "CrCl >= 60" in ctx
    assert "High emetogenic risk" in ctx


def test_clinical_data_integrity_matches_canonical_literature() -> None:
    """Verify that statistical trial endpoints match published values."""
    # RTOG-9111
    rtog_9111 = get_trial_by_source_id("RTOG-9111")
    endpoints = rtog_9111["endpoints"]
    assert endpoints["locoregional_control_hr"]["concurrent_vs_rt_alone"]["hr"] == 0.58
    assert endpoints["10_year_intact_larynx_rate"]["concurrent_crt"] == "67.4%"

    # PACIFIC
    pacific = get_trial_by_source_id("PACIFIC")
    assert pacific["endpoints"]["5_year_overall_survival"]["durvalumab"] == "42.9%"
    assert pacific["endpoints"]["5_year_overall_survival"]["hr"] == 0.72

    # CROSS
    cross = get_trial_by_source_id("CROSS")
    assert cross["endpoints"]["median_overall_survival"]["crt_surgery"] == "49.4 months"
    assert cross["endpoints"]["median_overall_survival"]["hr"] == 0.657

    # Stupp Glioblastoma
    stupp = get_trial_by_source_id("STUPP-EORTC-26981")
    assert stupp["endpoints"]["median_overall_survival"]["rt_tmz"] == "14.6 months"
    assert stupp["endpoints"]["median_overall_survival"]["hr"] == 0.63

    # RAPIDO
    rapido = get_trial_by_source_id("RAPIDO")
    assert rapido["endpoints"]["pathological_complete_response_pcr"]["tnt_arm"] == "28%"
    assert rapido["endpoints"]["3_year_disease_related_treatment_failure"]["hr"] == 0.75
