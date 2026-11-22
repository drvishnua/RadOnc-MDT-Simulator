"""Comprehensive End-to-End Integration Test Suite for Evidence Retrieval Pipeline.

Covers the 5 Tier-4 real-world clinical application scenarios (Requirement R1-R4, U07, U09):
1. Head & Neck Early Glottic Larynx (T1N0M0) - RO-01 guidelines/QUANTEC, SO-01 organ preservation, bounded injection, 1.0 concordance.
2. Locally Advanced NSCLC (Stage IIIA) - RO-02 & MO-01 PACIFIC trial durvalumab & QUANTEC lung V20, alias tolerance.
3. Breast Invasive Ductal Carcinoma (T2N0M0) - RO-03 & SO-02 whole-breast hypofractionation & margins.
4. High-Risk Prostate Adenocarcinoma (T3aN0M0, Gleason 8) - RO-04 & MO-03 definitive RT+ADT & QUANTEC rectum/bladder.
5. Anti-Hallucination Trap & Governance Stress - Fabricated trials, forged DOIs, corrupted claims, exact precision/recall.

Also includes Tier 1-3 property, boundary, and pairwise tests for complete determinism.
"""
from __future__ import annotations

import pytest

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services.evidence_retrieval import (
    EvidenceRetrievalEngine,
    RetrievedPassage,
)
from app.services.library_indexer import (
    DOMAIN_PARTITIONS,
    MedicalLibraryIndexer,
)
from app.services.reference_catalogue import (
    ReferenceEntry,
    audit_claim_citations,
    get_active_reference_catalogue,
    verify_citation,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------


def _make_case(**kwargs) -> SyntheticCase:
    base = {
        "scenario_title": "Synthetic MDT Case",
        "case_summary": "Synthetic test patient evaluated by multidisciplinary tumor board.",
    }
    base.update(kwargs)
    return SyntheticCase.model_validate(base)


@pytest.fixture
def synthetic_library_indexer() -> MedicalLibraryIndexer:
    """Provides an isolated, in-memory MedicalLibraryIndexer populated with multi-domain clinical literature."""
    indexer = MedicalLibraryIndexer(library_dir=".", db_path=":memory:")

    # 1. Head and Neck (Larynx)
    indexer.index_text_chunks(
        doc_id="NCCN-HN-LARYNX-2024",
        title="NCCN Head and Neck Cancers Larynx Guideline",
        domain="guidelines",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "Larynx Squamous cell carcinoma radiation therapy dose guideline: For T1-T2 N0 glottic cancer, "
            "definitive radiotherapy (66-70 Gy in 2.0 Gy/fx or 65.25 Gy in 2.25 Gy/fx) achieves 85-95% local "
            "control with functional organ preservation.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="ASTRO-LARYNX-2020",
        title="ASTRO Clinical Practice Guideline on Radiation Therapy for Larynx Cancer",
        domain="guidelines",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "ASTRO larynx clinical guideline recommends definitive radiotherapy or transoral laser microsurgery "
            "for T1-T2 N0 glottic larynx cancer to preserve natural voice and avoid laryngectomy.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="AHNS-SURGERY-LARYNX-2023",
        title="AHNS Consensus Guideline on Laryngeal Resection and Margins",
        domain="guidelines",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "Larynx surgical resection margin guideline: Transoral laser microsurgery (TLM) or partial laryngectomy "
            "for T1-T2 glottic cancer achieves 1-2 mm negative mucosal margins with functional preservation.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-PAROTID-2010",
        title="QUANTEC Salivary Gland and Parotid Tolerance",
        domain="organ_tolerances",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "parotid glands organ tolerance constraint QUANTEC mean dose < 20 Gy to one gland or mean dose < 25 Gy "
            "combined reduces severe long-term xerostomia risk to under 20%.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-CORD-2010",
        title="QUANTEC Spinal Cord Dose Constraints",
        domain="organ_tolerances",
        disease_sites=["general", "head_and_neck", "lung", "gastrointestinal"],
        text_chunks=[
            "spinal cord organ tolerance constraint QUANTEC maximum dose Dmax < 45-50 Gy in conventional 1.8-2.0 Gy "
            "fractions limits radiation myelopathy risk to < 0.2%.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="RTOG-9111",
        title="RTOG 91-11 Landmark Laryngeal Preservation Trial",
        domain="trials_systemic",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "Larynx organ preservation trial RTOG 91-11 demonstrated concurrent cisplatin with radiation therapy "
            "achieves superior 10-year larynx preservation (81.7%) compared to induction chemotherapy followed by RT "
            "(67.5%) or RT alone (63.8%).",
        ],
    )

    # 2. Thoracic / Lung (NSCLC)
    indexer.index_text_chunks(
        doc_id="NCCN-NSCL-2026",
        title="NCCN Non-Small Cell Lung Cancer Guideline",
        domain="guidelines",
        disease_sites=["lung"],
        text_chunks=[
            "Lung Non-small cell lung carcinoma Stage IIIA unresectable disease recommendation: concurrent "
            "chemoradiotherapy (60 Gy in 30 fractions with platinum-doublet chemotherapy) followed by durvalumab "
            "consolidation immunotherapy for 12 months.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="PACIFIC-TRIAL",
        title="PACIFIC Landmark Trial Durvalumab After Chemoradiotherapy in Stage III NSCLC",
        domain="trials_systemic",
        disease_sites=["lung"],
        text_chunks=[
            "Lung Non-small cell lung carcinoma Stage IIIA overall survival landmark trial PACIFIC trial "
            "demonstrated consolidation durvalumab significantly prolonged progression-free survival (16.8 vs 5.6 months) "
            "and overall survival after concurrent chemoradiotherapy.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="RTOG-0617",
        title="RTOG 0617 Standard vs High-Dose Chemoradiotherapy in Stage III NSCLC",
        domain="trials_systemic",
        disease_sites=["lung"],
        text_chunks=[
            "Lung Non-small cell lung carcinoma Stage IIIA trial RTOG 0617 confirmed 60 Gy standard-dose radiotherapy "
            "was superior to 74 Gy high-dose escalation due to excess cardiopulmonary toxicity.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-LUNG-2010",
        title="QUANTEC Lung Radiation Toxicity Monograph",
        domain="organ_tolerances",
        disease_sites=["lung"],
        text_chunks=[
            "lungs (V20/MLD) organ tolerance constraint QUANTEC: bilateral lung V20 Gy < 30-35% and mean lung dose "
            "MLD < 20 Gy to limit symptomatic radiation pneumonitis risk < 20%.",
        ],
    )

    # 3. Breast
    indexer.index_text_chunks(
        doc_id="NCCN-BREAST-2026",
        title="NCCN Clinical Practice Guidelines in Oncology: Breast Cancer",
        domain="guidelines",
        disease_sites=["breast"],
        text_chunks=[
            "Breast Invasive ductal carcinoma radiation therapy dose guideline recommends whole-breast "
            "hypofractionation (40 Gy in 15 fractions or 42.5 Gy in 16 fractions) for breast conserving therapy.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="ASTRO-BREAST-HYPO-2018",
        title="ASTRO Whole Breast Hypofractionation Guideline",
        domain="guidelines",
        disease_sites=["breast"],
        text_chunks=[
            "Breast Invasive ductal carcinoma whole-breast hypofractionation guideline: moderate hypofractionated "
            "whole-breast irradiation (40 Gy/15 fx) is preferred standard of care for breast conservation.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="SSO-ASTRO-MARGINS-2014",
        title="SSO-ASTRO Consensus Guideline on Margins for Breast Conservation Surgery",
        domain="guidelines",
        disease_sites=["breast"],
        text_chunks=[
            "Breast surgical resection margin guideline: 'no ink on tumor' is standard adequate negative surgical "
            "margin for invasive ductal carcinoma undergoing breast conservation therapy with whole-breast radiotherapy.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-HEART-2010",
        title="QUANTEC Cardiac Radiation Dose Tolerance",
        domain="organ_tolerances",
        disease_sites=["breast", "lung"],
        text_chunks=[
            "heart (LAD) organ tolerance constraint QUANTEC: mean heart dose < 4-5 Gy, V25 < 10% to reduce long-term "
            "ischemic cardiac disease and LAD coronary artery stenosis.",
        ],
    )

    # 4. Prostate
    indexer.index_text_chunks(
        doc_id="NCCN-PROSTATE-2026",
        title="NCCN Clinical Practice Guidelines: Prostate Cancer",
        domain="guidelines",
        disease_sites=["prostate"],
        text_chunks=[
            "Prostate Adenocarcinoma radiation therapy dose guideline for high-risk disease (T3a, Gleason 8, PSA > 20): "
            "definitive radiotherapy (78-80 Gy in 39-40 fx or moderate hypofractionation 60 Gy/20 fx) combined with "
            "long-term androgen deprivation therapy (ADT) for 24-36 months.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="STAMPEDE-TRIAL",
        title="STAMPEDE Landmark Multi-Arm Multi-Stage Trial in Prostate Cancer",
        domain="trials_systemic",
        disease_sites=["prostate"],
        text_chunks=[
            "Prostate Adenocarcinoma high-risk localized and locally advanced disease overall survival landmark trial "
            "STAMPEDE trial established standard of care systemic therapy intensification with androgen deprivation therapy (ADT).",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-RECTUM-2010",
        title="QUANTEC Rectal Dose-Volume Constraints",
        domain="organ_tolerances",
        disease_sites=["prostate", "colorectal"],
        text_chunks=[
            "rectum organ tolerance constraint QUANTEC: V50 < 50%, V60 < 35%, V70 < 20%, V75 < 15% to limit late "
            "Grade >= 2 rectal toxicity and bleeding to < 10%.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-BLADDER-2010",
        title="QUANTEC Bladder Normal Tissue Complication Probability",
        domain="organ_tolerances",
        disease_sites=["prostate", "genitourinary", "gynecologic"],
        text_chunks=[
            "bladder organ tolerance constraint QUANTEC: V65 < 50%, V70 < 35%, V75 < 25%, V80 < 15% to minimize "
            "late dysuria, hematuria, and contracted bladder.",
        ],
    )

    # 5. Staging, Textbooks & General Medicine
    indexer.index_text_chunks(
        doc_id="AJCC-8TH-LARYNX",
        title="AJCC 8th Edition Cancer Staging: Larynx and Pharynx",
        domain="staging_anatomy",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "Larynx T1 N0 M0 glottic carcinoma staging: T1a tumor limited to one vocal cord, normal vocal cord mobility; "
            "T1b tumor involves both vocal cords with normal mobility; regional nodes N0; distant metastasis M0.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="PEREZ-BRADY-2026",
        title="Perez & Brady's Principles and Practice of Radiation Oncology 2026",
        domain="textbooks_radiobiology",
        disease_sites=["general", "head_and_neck", "lung", "breast", "prostate"],
        text_chunks=[
            "Radiobiology fractionation principles: alpha/beta ratios for early responding tissues (10 Gy) and late "
            "responding normal tissues (3 Gy). EQD2 and BED formulations guide safe dose escalation.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="HARRISONS-MED-21ST",
        title="Harrison's Principles of Internal Medicine 21st Edition",
        domain="general_medicine",
        disease_sites=["general"],
        text_chunks=[
            "Assessment of medical comorbidities, performance status (ECOG 0-4), pulmonary reserve, and cardiovascular "
            "tolerance in patients undergoing multidisciplinary cancer treatment.",
        ],
    )

    return indexer


# ---------------------------------------------------------------------------
# TIER 4: CLINICAL SCENARIOS
# ---------------------------------------------------------------------------


def test_scenario_1_head_and_neck_larynx_t1n0m0_e2e(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Scenario 1: Head & Neck Early Glottic Larynx (T1N0M0) E2E Pipeline.

    Exercises:
    - Facet extraction for early glottic larynx.
    - RO-01 retrieves NCCN/ASTRO larynx guidelines + QUANTEC parotid/cord constraints.
    - SO-01 retrieves organ preservation trials (RTOG 91-11).
    - Prompt injection is strictly bounded (<600 tokens).
    - Specialist claims referencing RTOG 91-11 and ASTRO-LARYNX-2020 verify with 1.0 concordance.
    """
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)
    case = _make_case(
        primary_site="Larynx",
        anatomical_subsite="Glottic",
        histology="Squamous cell carcinoma",
        clinical_t_stage="T1",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        performance_status="ECOG 0",
        relevant_comorbidities=["Mild GERD"],
        case_summary="62-year-old teacher presenting with hoarseness. Laryngoscopy reveals T1N0M0 right true vocal cord lesion.",
    )

    # 1. Facet extraction verification
    facets = engine.extract_case_facets(case)
    assert facets["primary_site"] == "head_and_neck"
    assert facets["raw_primary_site"] == "Larynx"
    assert facets["anatomical_subsite"] == "Glottic"
    assert facets["histology"] == "Squamous cell carcinoma"
    assert facets["stage"] == "T1 N0 M0"
    assert "parotid glands" in facets["oars"]
    assert "spinal cord" in facets["oars"]

    # 2. Radiation Oncologist (RO-01) retrieval
    ro_passages = engine.retrieve_evidence_for_role("RO-01", case, limit=3)
    assert len(ro_passages) >= 2
    ro_source_ids = {p.source_id for p in ro_passages}
    assert any("NCCN-HN-LARYNX" in sid or "ASTRO-LARYNX" in sid for sid in ro_source_ids)
    assert any("QUANTEC-PAROTID" in sid or "QUANTEC-CORD" in sid for sid in ro_source_ids)

    # 3. Surgical Oncologist (SO-01) retrieval
    so_passages = engine.retrieve_evidence_for_role("SO-01", case, limit=3)
    assert len(so_passages) >= 1
    so_source_ids = {p.source_id for p in so_passages}
    assert any("RTOG-9111" in sid for sid in so_source_ids)

    # 4. Prompt injection formatting and token bound check (<600 tokens ~ 2400 chars)
    prompt_context = engine.format_prompt_injection(ro_passages)
    assert "VERIFIED CLINICAL EVIDENCE CONTEXT:" in prompt_context
    assert "[source_id:" in prompt_context
    assert len(prompt_context) < 2400
    assert len(prompt_context) > 300

    # 5. Citation verification with active catalogue
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)
    claims = [
        {
            "role_id": "RO-01",
            "source_id": "ASTRO-LARYNX-2020",
            "claim": "Definitive radiotherapy provides 85-95% local control with natural voice preservation.",
        },
        {
            "role_id": "SO-01",
            "source_id": "RTOG 91-11",
            "claim": "Organ preservation trials support larynx preservation approaches over primary total laryngectomy.",
        },
    ]
    audit = audit_claim_citations(claims, catalogue=catalogue)
    assert audit["total_citations"] == 2
    assert audit["verified_count"] == 2
    assert audit["unverified_count"] == 0
    assert audit["concordance_rate"] == 1.0
    assert audit["valid"] is True


def test_scenario_2_locally_advanced_nsclc_stage_iiia_e2e(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Scenario 2: Locally Advanced Non-Small Cell Lung Cancer (NSCLC Stage IIIA) E2E Pipeline.

    Exercises:
    - RO-02 (Thoracic RO) and MO-01 (Thoracic MO) receive PACIFIC trial durvalumab consolidation and QUANTEC lung V20.
    - Citations resolve with alias tolerance ('PACIFIC trial', 'RTOG 0617').
    """
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)
    case = _make_case(
        primary_site="Lung",
        histology="Non-small cell lung carcinoma",
        stage_group="Stage IIIA",
        clinical_t_stage="T2a",
        clinical_n_stage="N2",
        clinical_m_stage="M0",
        relevant_comorbidities=["COPD", "Tobacco use disorder"],
        case_summary="58-year-old presenting with persistent cough and hemoptysis. CT shows 4.5 cm right upper lobe mass with subcarinal nodal metastasis (Stage IIIA).",
    )

    # 1. Facet extraction verification
    facets = engine.extract_case_facets(case)
    assert facets["primary_site"] == "lung"
    assert facets["stage"] == "Stage IIIA"
    assert "lungs (V20/MLD)" in facets["oars"]
    assert "esophagus" in facets["oars"]

    # 2. Evidence retrieval for RO-02 & MO-01
    ro_passages = engine.retrieve_evidence_for_role("RO-02", case, limit=3)
    assert ro_passages
    ro_source_ids = {p.source_id for p in ro_passages}
    assert any("NCCN-NSCL" in sid or "QUANTEC-LUNG" in sid for sid in ro_source_ids)

    mo_passages = engine.retrieve_evidence_for_role("MO-01", case, limit=3)
    assert mo_passages
    mo_source_ids = {p.source_id for p in mo_passages}
    assert any("PACIFIC-TRIAL" in sid or "RTOG-0617" in sid or "NCCN-NSCL" in sid for sid in mo_source_ids)

    # 3. Citation resolution with alias tolerance
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)
    assert verify_citation("PACIFIC trial", catalogue=catalogue) is True
    assert verify_citation("RTOG 0617", catalogue=catalogue) is True
    assert verify_citation("RTOG-0617", catalogue=catalogue) is True

    claims = [
        {
            "role_id": "MO-01",
            "source_id": "PACIFIC trial",
            "claim": "Consolidation durvalumab significantly prolongs overall survival following concurrent chemoradiotherapy.",
        },
        {
            "role_id": "RO-02",
            "source_id": "RTOG 0617",
            "claim": "Standard 60 Gy radiotherapy remains guideline benchmark; high-dose 74 Gy escalation resulted in worse survival.",
        },
    ]
    audit = audit_claim_citations(claims, catalogue=catalogue)
    assert audit["verified_count"] == 2
    assert audit["unverified_count"] == 0
    assert audit["concordance_rate"] == 1.0


def test_scenario_3_breast_invasive_ductal_carcinoma_t2n0m0_e2e(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Scenario 3: Breast Invasive Ductal Carcinoma (T2N0M0) E2E Pipeline.

    Exercises:
    - RO-03 (Breast RO) and SO-02 (Breast SO) retrieve whole-breast hypofractionation and surgical margin evidence.
    - Verified prompt injection formatting and bounded length.
    """
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)
    case = _make_case(
        primary_site="Breast",
        histology="Invasive ductal carcinoma",
        clinical_t_stage="T2",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        case_summary="51-year-old with a 2.8 cm palpable left breast mass. Core biopsy shows ER+ PR+ HER2- invasive ductal carcinoma.",
    )

    # 1. Facet extraction
    facets = engine.extract_case_facets(case)
    assert facets["primary_site"] == "breast"
    assert facets["stage"] == "T2 N0 M0"
    assert "heart (LAD)" in facets["oars"]
    assert "ipsilateral lung" in facets["oars"]

    # 2. Retrieval for RO-03 and SO-02
    ro_passages = engine.retrieve_evidence_for_role("RO-03", case, limit=3)
    assert ro_passages
    ro_source_ids = {p.source_id for p in ro_passages}
    assert any("BREAST" in sid for sid in ro_source_ids)

    so_passages = engine.retrieve_evidence_for_role("SO-02", case, limit=3)
    assert so_passages
    so_source_ids = {p.source_id for p in so_passages}
    assert any("BREAST" in sid or "MARGIN" in sid for sid in so_source_ids)

    # 3. Prompt injection length and tag formatting
    prompt_context = engine.format_prompt_injection(ro_passages)
    assert "[source_id:" in prompt_context
    assert len(prompt_context) < 2400
    assert len(prompt_context) > 200

    # 4. Citation auditing
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)
    claims = [
        {
            "role_id": "RO-03",
            "source_id": "ASTRO-BREAST-HYPO-2018",
            "claim": "Moderate hypofractionated whole-breast irradiation (40 Gy in 15 fractions) is preferred standard.",
        },
        {
            "role_id": "SO-02",
            "source_id": "SSO-ASTRO-MARGINS-2014",
            "claim": "No ink on tumor constitutes an adequate negative margin in invasive breast cancer undergoing BCT.",
        },
    ]
    audit = audit_claim_citations(claims, catalogue=catalogue)
    assert audit["verified_count"] == 2
    assert audit["unverified_count"] == 0
    assert audit["valid"] is True


def test_scenario_4_high_risk_prostate_adenocarcinoma_t3an0m0_e2e(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Scenario 4: High-Risk Prostate Adenocarcinoma (T3aN0M0, Gleason 8) E2E Pipeline.

    Exercises:
    - Definitive RT + ADT evidence retrieval (NCCN prostate, STAMPEDE).
    - Normal tissue constraints (QUANTEC rectum and bladder constraints).
    """
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)
    case = _make_case(
        primary_site="Prostate",
        histology="Adenocarcinoma",
        clinical_t_stage="T3a",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        case_summary="68-year-old male with PSA 24 ng/mL and MRI showing extracapsular extension (cT3a). Biopsy confirms Gleason 8 (4+4) adenocarcinoma.",
    )

    # 1. Facet extraction
    facets = engine.extract_case_facets(case)
    assert facets["primary_site"] == "prostate"
    assert facets["stage"] == "T3a N0 M0"
    assert "rectum" in facets["oars"]
    assert "bladder" in facets["oars"]

    # 2. RO-04 and MO-03 retrieval
    ro_passages = engine.retrieve_evidence_for_role("RO-04", case, limit=3)
    assert ro_passages
    ro_source_ids = {p.source_id for p in ro_passages}
    assert any("PROSTATE" in sid or "RECTUM" in sid for sid in ro_source_ids)

    mo_passages = engine.retrieve_evidence_for_role("MO-03", case, limit=3)
    assert mo_passages
    mo_source_ids = {p.source_id for p in mo_passages}
    assert any("STAMPEDE" in sid or "PROSTATE" in sid for sid in mo_source_ids)

    # 3. Citation auditing
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)
    claims = [
        {
            "role_id": "RO-04",
            "source_id": "NCCN-PROSTATE-2026",
            "claim": "High-risk prostate cancer requires dose-escalated radiotherapy combined with 24-36 months of ADT.",
        },
        {
            "role_id": "RO-04",
            "source_id": "QUANTEC-RECTUM-2010",
            "claim": "Keep rectal V70 < 20% to avoid late bleeding.",
        },
        {
            "role_id": "MO-03",
            "source_id": "STAMPEDE-TRIAL",
            "claim": "Systemic therapy intensification improves failure-free survival in locally advanced prostate cancer.",
        },
    ]
    audit = audit_claim_citations(claims, catalogue=catalogue)
    assert audit["total_citations"] == 3
    assert audit["verified_count"] == 3
    assert audit["unverified_count"] == 0
    assert audit["concordance_rate"] == 1.0


def test_scenario_5_anti_hallucination_trap_and_governance_stress(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Scenario 5: Anti-Hallucination Trap & Governance Stress Testing.

    Exercises:
    - Simulated fabricated trials (FABRICATED-2099-QUADRUPLET, FAKE-GUIDELINE-99).
    - Forged DOIs on genuine trials.
    - Corrupted claim data structures (non-dict types, empty citations).
    - Verifies exact precision and recall of the anti-hallucination audit.
    """
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)

    mixed_claims = [
        # Genuine citations
        {
            "role_id": "RO-01",
            "source_id": "ASTRO-LARYNX-2020",
            "doi_or_url": "https://doi.org/10.1016/j.prro.2020.02.004",
            "claim": "Definitive radiotherapy for early glottic cancer.",
        },
        {
            "role_id": "SO-01",
            "source_id": "RTOG 91-11",
            "claim": "Concurrent chemoradiation for laryngeal preservation.",
        },
        {
            "role_id": "MO-01",
            "source_id": "PACIFIC trial",
            "claim": "Consolidation durvalumab improves overall survival.",
        },
        # Fabricated trials
        {
            "role_id": "RO-99",
            "source_id": "FABRICATED-2099-QUADRUPLET",
            "claim": "Quadruplet targeted therapy cures 100% of glottic cancer with zero toxicity.",
        },
        {
            "role_id": "MO-99",
            "source_id": "FAKE-GUIDELINE-99",
            "claim": "Unproven systemic regimen replaces standard of care.",
        },
        # Forged DOI on genuine trial
        {
            "role_id": "SO-01",
            "source_id": "RTOG-9111",
            "doi_or_url": "https://doi.org/10.9999/forged.doi.12345",
            "claim": "Claim with fabricated citation DOI.",
        },
        # Corrupted non-dict entries (handled defensibly)
        "corrupted_string_claim",
        None,
        12345,
        {"source_id": ""},  # empty source ID
    ]

    audit = audit_claim_citations(mixed_claims, catalogue=catalogue)

    # Exactly 6 valid dict claims with source_ids were audited
    assert audit["total_citations"] == 6
    assert audit["verified_count"] == 3
    assert audit["unverified_count"] == 3
    assert audit["concordance_rate"] == 0.5
    assert audit["valid"] is False

    # Check precision & recall
    verified_sources = {c["source_id"] for c in audit["verified_citations"]}
    assert verified_sources == {"ASTRO-LARYNX-2020", "RTOG 91-11", "PACIFIC trial"}

    unverified_sources = {c["source_id"] for c in audit["unverified_citations"]}
    assert "FABRICATED-2099-QUADRUPLET" in unverified_sources
    assert "FAKE-GUIDELINE-99" in unverified_sources
    assert "RTOG-9111" in unverified_sources  # flagged due to forged DOI


# ---------------------------------------------------------------------------
# TIER 1, 2, 3: PROPERTY, BOUNDARY, AND PAIRWISE TESTS
# ---------------------------------------------------------------------------


def test_unicode_dash_tolerance_across_citation_verification(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Verify that all Unicode dash variants normalize and verify successfully."""
    catalogue = get_active_reference_catalogue(indexer=synthetic_library_indexer)

    # Unicode dashes: hyphen \u2010, non-breaking \u2011, figure \u2012, en \u2013, em \u2014, horizontal \u2015
    dash_variants = [
        "RTOG-9111",      # standard ASCII hyphen
        "RTOG\u20109111",  # hyphen
        "RTOG\u20119111",  # non-breaking hyphen
        "RTOG\u20129111",  # figure dash
        "RTOG\u20139111",  # en-dash
        "RTOG\u20149111",  # em-dash
        "RTOG\u20159111",  # horizontal bar
        "RTOG 91–11",     # en-dash in space variant
        "RTOG 91—11",     # em-dash in space variant
    ]
    for variant in dash_variants:
        assert verify_citation(variant, catalogue=catalogue) is True, f"Failed for {variant!r}"


def test_all_45_personas_domain_routing_integrity(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Verify all 45 catalog personas route deterministically to canonical domain partitions."""
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)
    valid_domains = set(DOMAIN_PARTITIONS)

    assert len(AGENT_PROFILES) == 45
    for agent in AGENT_PROFILES:
        role_id = agent["agent_id"]
        domains = engine.get_role_domains(role_id)
        assert len(domains) >= 1
        assert all(d in valid_domains for d in domains)


def test_prompt_injection_boundary_and_truncation(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Verify prompt injection bounds and safe snippet truncation."""
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)

    # 1. Empty passages list returns empty string
    assert engine.format_prompt_injection([]) == ""

    # 2. Giant snippet (>300 chars) is truncated with ellipsis
    long_snippet = "Radiation therapy dose fractionation " * 20  # ~740 chars
    giant_passages = [
        RetrievedPassage(
            source_id="TEST-LARGE-01",
            title="Large Monograph",
            domain="guidelines",
            snippet=long_snippet,
        )
    ]
    formatted = engine.format_prompt_injection(giant_passages)
    assert formatted.endswith("Do not invent citations, URLs, or unsupported claims.")
    assert "..." in formatted
    assert len(formatted) < 2400


def test_defensive_facet_extraction_on_sparse_case(
    synthetic_library_indexer: MedicalLibraryIndexer,
) -> None:
    """Verify engine handles minimal or sparse cases without raising exceptions."""
    engine = EvidenceRetrievalEngine(indexer=synthetic_library_indexer)

    minimal_case = SyntheticCase.model_validate({
        "scenario_title": "Minimal Case",
        "case_summary": "Unspecified cancer presentation.",
    })
    facets = engine.extract_case_facets(minimal_case)
    assert facets["primary_site"] == "general"
    assert facets["stage"] is None
    assert isinstance(facets["oars"], list)

    passages = engine.retrieve_evidence_for_role("RO-01", minimal_case, limit=2)
    assert isinstance(passages, list)
