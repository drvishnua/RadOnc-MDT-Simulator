"""Unit tests for NCCN Guidelines Evidence Service.

Tests deterministic indexing, stage-specific algorithmic retrieval, Category 1/2A
recommendations, concurrent systemic therapy indications, normal tissue constraints,
and anti-hallucination citation verification across all 67 NCCN guideline blocks.
"""
import pytest
from app.services.nccn_guidelines_service import (
    load_nccn_catalogue,
    get_guideline_by_id,
    search_nccn_guidelines,
    get_stage_recommendations,
    verify_nccn_citation,
    format_nccn_specialist_context,
)


def test_catalogue_loads_all_67_guidelines():
    """Verify that all NCCN guideline blocks (at least 67) plus society guidelines are loaded."""
    entries = load_nccn_catalogue()
    assert len(entries) >= 67, f"Expected at least 67 guidelines, got {len(entries)}"


def test_key_guidelines_exist_with_structured_content():
    """Verify core radiation oncology sites have full stage algorithms and RT principles."""
    core_ids = [
        "NCCN-HN-2025",
        "NCCN-NSCLC-2025",
        "NCCN-PROSTATE-2026",
        "NCCN-RECTAL-2025",
        "NCCN-CERVICAL-2025",
        "NCCN-ANAL-2025",
        "NCCN-BLADDER-2025",
        "NCCN-BREAST-2025",
        "NCCN-CNS-2025",
        "NCCN-ESOPHAGEAL-2025",
    ]
    for cid in core_ids:
        entry = get_guideline_by_id(cid)
        assert entry is not None, f"Failed to retrieve {cid}"
        assert len(entry.stage_algorithms) > 0, f"{cid} missing stage algorithms"
        assert len(entry.category_1_recommendations) > 0, f"{cid} missing Category 1 recommendations"
        assert len(entry.concurrent_systemic_indications) > 0, f"{cid} missing concurrent systemic indications"
        assert entry.radiation_therapy_principles.technique != "", f"{cid} missing RT technique"


def test_head_and_neck_category_1_postoperative_chemoradiation():
    """Verify EORTC 22931 / RTOG 9501 Category 1 indications for HN (margins/extranodal extension)."""
    hn = get_guideline_by_id("NCCN-HN-2025")
    assert hn is not None
    cat1_texts = " ".join(hn.category_1_recommendations).lower()
    assert "extranodal extension" in cat1_texts or "ene" in cat1_texts
    assert "positive surgical margin" in cat1_texts or "positive margin" in cat1_texts

    # Check normal tissue constraints in RAD-A
    constraints = hn.radiation_therapy_principles.normal_tissue_constraints
    assert "mandible" in constraints
    assert "spinal_cord" in constraints
    assert "parotid_glands" in constraints


def test_nsclc_sabr_and_concurrent_chemoradiation():
    """Verify NSCLC stage I SABR doses and unresectable stage III concurrent CRT + Durvalumab."""
    nsclc = get_guideline_by_id("NCCN-NSCLC-2025")
    assert nsclc is not None
    cat1_texts = " ".join(nsclc.category_1_recommendations)
    assert "SABR" in cat1_texts or "SBRT" in cat1_texts
    assert "Durvalumab" in cat1_texts
    assert "PACIFIC" in cat1_texts or "concurrent chemoradiotherapy" in cat1_texts

    rt = nsclc.radiation_therapy_principles
    assert "60-66 Gy" in rt.definitive_doses or "60-70 Gy" in rt.definitive_doses
    assert rt.normal_tissue_constraints["lungs_bilateral"] != ""


def test_prostate_risk_stratification_and_adt():
    """Verify Prostate cancer active surveillance, hypofractionation, and ADT rules."""
    prostate = get_guideline_by_id("NCCN-PROSTATE-2026")
    assert prostate is not None

    # Check Low Risk (no ADT) vs High Risk (long-term ADT)
    low_risk = next((a for a in prostate.stage_algorithms if "Low Risk" in a.stage), None)
    assert low_risk is not None
    assert "Active Surveillance" in low_risk.pathway or "surveillance" in low_risk.pathway.lower()
    assert "NO ADT" in low_risk.pathway

    high_risk = next((a for a in prostate.stage_algorithms if "High" in a.stage), None)
    assert high_risk is not None
    assert "Long-term ADT" in high_risk.pathway or "18-36 months" in high_risk.pathway


def test_rectal_tnt_and_non_operative_management():
    """Verify Rectal cancer Total Neoadjuvant Therapy and Watch-and-Wait protocol."""
    rectal = get_guideline_by_id("NCCN-RECTAL-2025")
    assert rectal is not None
    cat1_texts = " ".join(rectal.category_1_recommendations)
    assert "Total Neoadjuvant Therapy" in cat1_texts or "TNT" in cat1_texts

    # Check nonoperative surveillance for complete clinical response
    rec = get_stage_recommendations("GI", "Locally Advanced pMMR/MSS")
    assert rec["matched"] is True
    pathway_texts = " ".join(a.pathway for a in rec["matched_algorithms"])
    assert "Watch-and-Wait" in pathway_texts or "surveillance" in pathway_texts.lower()


def test_cervical_concurrent_cisplatin_and_brachytherapy():
    """Verify Cervical cancer Stage IB3/IIA2+ concurrent chemoradiation with weekly cisplatin and brachytherapy."""
    cerv = get_guideline_by_id("NCCN-CERVICAL-2025")
    assert cerv is not None
    assert "weekly Cisplatin" in cerv.concurrent_systemic_indications or "Cisplatin" in cerv.concurrent_systemic_indications
    assert cerv.radiation_therapy_principles.brachytherapy_doses is not None
    assert "80-85 Gy" in cerv.radiation_therapy_principles.brachytherapy_doses or "EQD2" in cerv.radiation_therapy_principles.brachytherapy_doses


def test_search_nccn_guidelines():
    """Verify filtering guidelines by disease site and query terms."""
    gi_guidelines = search_nccn_guidelines(disease_site="GI")
    assert len(gi_guidelines) >= 10, f"Expected >= 10 GI guidelines, got {len(gi_guidelines)}"

    lung_guidelines = search_nccn_guidelines(disease_site="Lung")
    assert len(lung_guidelines) >= 3

    matched = search_nccn_guidelines(query="Glioblastoma")
    assert any("CNS" in m.disease_site for m in matched)


def test_verify_nccn_citation():
    """Verify deterministic anti-hallucination citation validation."""
    assert verify_nccn_citation("NCCN-HN-2025") is True
    assert verify_nccn_citation("nccn-nsclc-2025") is True
    assert verify_nccn_citation("NCCN-PROSTATE-2026") is True
    assert verify_nccn_citation("NCCN-FAKE-HALLUCINATED-2029") is False
    assert verify_nccn_citation("NONEXISTENT-GUIDELINE") is False


def test_format_nccn_specialist_context():
    """Verify formatted context generation for specialist persona prompt injection."""
    ctx = format_nccn_specialist_context(disease_site="Head & Neck", stage="T1-2, N0")
    assert "EVIDENCE GROUNDING — NCCN CLINICAL PRACTICE GUIDELINE (NCCN-HN-2025)" in ctx
    assert "Category 1 Evidence-Based Recommendations" in ctx
    assert "Concurrent Systemic Therapy Indications" in ctx
    assert "Normal Tissue Constraints" in ctx
    assert "Educational simulation only" in ctx
