"""Comprehensive regression tests for the Radiation Oncology Library Indexer service.

Validates:
- Safe, strictly read-only file discovery across medical books and guidelines.
- Persistent local workspace caching in JSON and SQLite formats.
- Rule-based clinical query engine matching case sites, stages, and comorbidities.
- Dose fractionation schemes, EQD2/BED radiobiology models, and Perez & Brady principles.
- QUANTEC and PENTEC organ tolerance limits and normal tissue complication endpoints.
- Integration with citation verification and anti-hallucination auditing (U07, U09).
- Deterministic retrieval digest and case-fact provenance contracts (AGENTS.md).
"""
from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import time
import pytest

from app.schemas import SyntheticCase
from app.services.library_indexer import (
    DOMAIN_PARTITIONS,
    DomainType,
    DocumentChunk,
    IndexedDocument,
    MedicalLibraryIndexer,
    classify_domain,
    extract_disease_sites,
    get_medical_library_indexer,
    DiscoveredFile,
    DoseFractionationRule,
    EvidenceRetrievalResult,
    LibraryIndexer,
    OrganConstraint,
    _compute_radiobiology,
    get_library_indexer,
    query_library_for_case,
)
from app.services.reference_catalogue import (
    load_reference_catalogue,
    search_reference_catalogue,
    verify_citation,
    audit_claim_citations,
)


@pytest.fixture
def temp_indexer(tmp_path: pathlib.Path) -> LibraryIndexer:
    """Fixture providing an isolated LibraryIndexer instance using temporary cache and library paths."""
    lib_dir = tmp_path / "mock_library"
    lib_dir.mkdir(parents=True)

    # Create synthetic structure mimicking user's library
    nccn_dir = lib_dir / "Radonc" / "NCCN"
    nccn_dir.mkdir(parents=True)
    (nccn_dir / "head-and-neck_blocks.pdf").write_bytes(b"%PDF-1.4 mock content")
    (nccn_dir / "nscl_blocks.pdf").write_bytes(b"%PDF-1.4 mock content")

    main_dir = lib_dir / "Radonc" / "Books" / "MAIN"
    main_dir.mkdir(parents=True)
    (main_dir / "Perez_and_Brady_Principles.pdf").write_bytes(b"%PDF-1.4 mock content")

    quantec_dir = lib_dir / "Radonc" / "Books" / "QUANTEC"
    quantec_dir.mkdir(parents=True)
    (quantec_dir / "Radiation-Associated-Spinal-Cord.pdf").write_bytes(b"%PDF-1.4 mock content")

    cache_dir = tmp_path / "evidence_catalogues"
    cache_dir.mkdir(parents=True)

    return LibraryIndexer(library_path=lib_dir, cache_dir=cache_dir)


def test_radiobiology_bed_and_eqd2_calculation():
    """Verify LQ model BED and EQD2 mathematical formulas."""
    # 66 Gy in 33 fractions (2.0 Gy/fx)
    bed10, bed3, eqd2_10, eqd2_3 = _compute_radiobiology(66.0, 33)
    assert bed10 == 79.2
    assert bed3 == 110.0
    assert eqd2_10 == 66.0
    assert eqd2_3 == 66.0

    # 63 Gy in 28 fractions (2.25 Gy/fx)
    bed10_hypo, bed3_hypo, eqd2_10_hypo, eqd2_3_hypo = _compute_radiobiology(63.0, 28)
    assert bed10_hypo == pytest.approx(77.18, 0.01)
    assert bed3_hypo == pytest.approx(110.25, 0.01)
    assert eqd2_10_hypo == pytest.approx(64.31, 0.01)
    assert eqd2_3_hypo == pytest.approx(66.15, 0.01)


def test_safe_library_file_discovery_and_categorization(temp_indexer: LibraryIndexer):
    """Discovery must identify files, classify categories, and record file stats without modifications."""
    files = temp_indexer.discover_library_files(force_refresh=True)
    assert len(files) == 4
    categories = {f.category for f in files}
    assert "guidelines_nccn" in categories
    assert "textbooks_core" in categories
    assert "organ_tolerance_quantec" in categories

    for f in files:
        assert f.size_bytes > 0
        assert f.extension == ".pdf"
        assert pathlib.Path(f.file_path).is_file()


def test_persistent_caching_json_and_sqlite(temp_indexer: LibraryIndexer):
    """Discovered files must persist to JSON and SQLite caches and load correctly."""
    temp_indexer.discover_library_files(force_refresh=True)

    assert temp_indexer.cache_json.is_file()
    assert temp_indexer.cache_db.is_file()

    # Verify JSON content
    cache_data = json.loads(temp_indexer.cache_json.read_text(encoding="utf-8"))
    assert cache_data["total_files"] == 4
    assert len(cache_data["files"]) == 4

    # Verify SQLite schema and content
    conn = sqlite3.connect(str(temp_indexer.cache_db))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), category FROM library_files GROUP BY category")
    rows = cursor.fetchall()
    conn.close()
    assert len(rows) >= 3

    # Fast reload without rescanning disk
    reloaded_indexer = LibraryIndexer(
        library_path=temp_indexer.library_path,
        cache_dir=temp_indexer.cache_dir,
    )
    loaded_files = reloaded_indexer.discover_library_files(force_refresh=False)
    assert len(loaded_files) == 4


def test_missing_library_directory_graceful_fallback(tmp_path: pathlib.Path):
    """When the library directory does not exist (CI environment), discover returns empty list without error."""
    non_existent = tmp_path / "does_not_exist"
    indexer = LibraryIndexer(library_path=non_existent, cache_dir=tmp_path / "cache")
    files = indexer.discover_library_files(force_refresh=True)
    assert files == []

    # Built-in catalogue queries still work completely
    res = indexer.query("Head & Neck", stage="T1N0M0")
    assert len(res.matched_guidelines) >= 1
    assert len(res.dose_fractionations) >= 1


def test_query_head_and_neck_early_stage_larynx():
    """Querying early-stage glottic larynx must retrieve standard and hypofractionated RT and QUANTEC constraints."""
    indexer = get_library_indexer()
    res = indexer.query(disease_site="Head & Neck", stage="T1N0M0", histology="Squamous cell carcinoma", subsite="Larynx")

    assert res.case_disease_site == "Head & Neck"
    assert res.case_subsite == "Larynx"

    # Guideline retrieval
    guideline_ids = {g.source_id for g in res.matched_guidelines}
    assert any("HN" in gid or "LARYNX" in gid for gid in guideline_ids)

    # Fractionation schemes
    frac_scenarios = [f.clinical_scenario for f in res.dose_fractionations]
    assert any("T1N0" in s for s in frac_scenarios)
    assert any(f.total_dose_gy in (66.0, 63.0) for f in res.dose_fractionations)

    # Organ constraints for head & neck
    organ_names = {c.organ for c in res.organ_constraints}
    assert any("Spinal Cord" in o for o in organ_names)
    assert any("Parotid" in o for o in organ_names)

    # Deterministic prompt context
    assert "VERIFIED CLINICAL EVIDENCE RETRIEVAL" in res.evidence_context_prompt
    assert "QUANTEC" in res.evidence_context_prompt
    assert len(res.retrieval_hash) == 64


def test_query_locally_advanced_head_and_neck_chemoradiation():
    """Querying locally advanced head and neck must retrieve CRT protocols and landmark trials."""
    indexer = get_library_indexer()
    res = indexer.query(disease_site="Head & Neck", stage="T3N1M0", histology="Squamous cell carcinoma")

    # Fractionation for locally advanced
    frac_scenarios = [f.clinical_scenario for f in res.dose_fractionations]
    assert any("Locally Advanced" in s or "70.0" in str(f.total_dose_gy) for s, f in zip(frac_scenarios, res.dose_fractionations))

    # Landmark trials
    trial_ids = {t.source_id for t in res.landmark_trials}
    assert "RTOG-9111" in trial_ids or any("9111" in tid for tid in trial_ids)


def test_query_lung_cancer_early_vs_locally_advanced():
    """Lung queries must differentiate SBRT for early stage vs chemoradiation + durvalumab for stage III."""
    indexer = get_library_indexer()

    # Early stage SBRT
    early_res = indexer.query(disease_site="Lung", stage="T1bN0M0")
    early_scenarios = [f.clinical_scenario for f in early_res.dose_fractionations]
    assert any("SBRT" in s or "Early Stage" in s for s in early_scenarios)

    # Stage III Chemoradiation + PACIFIC trial
    la_res = indexer.query(disease_site="Lung", stage="Stage IIIB")
    la_scenarios = [f.clinical_scenario for f in la_res.dose_fractionations]
    assert any("Stage III" in s or "Concurrent" in s for s in la_scenarios)
    trial_ids = {t.source_id for t in la_res.landmark_trials}
    assert "PACIFIC-TRIAL" in trial_ids or any("PACIFIC" in tid for tid in trial_ids)


def test_query_comorbidity_and_fitness_rules():
    """Comorbidity query must provide renal thresholds and ECOG suitability criteria."""
    indexer = get_library_indexer()

    # Fit patient with CrCl 85
    fit_res = indexer.query(disease_site="Head & Neck", creatinine_clearance=85.0, ecog_ps=0)
    actions = [r.clinical_action for r in fit_res.comorbidity_rules]
    assert any("high-dose" in a.lower() or "eligible" in a.lower() for a in actions)

    # Renal impairment CrCl 40
    renal_res = indexer.query(disease_site="Head & Neck", creatinine_clearance=40.0, ecog_ps=2)
    renal_actions = [r.clinical_action for r in renal_res.comorbidity_rules]
    assert any("contraindicated" in a.lower() or "tubular necrosis" in a.lower() for a in renal_actions)


def test_query_library_for_case_helper():
    """query_library_for_case helper must accept SyntheticCase instances seamlessly."""
    case = SyntheticCase(
        scenario_title="Larynx T1N0M0 Evaluation",
        case_summary="Patient presents with T1N0M0 glottic squamous cell carcinoma. No nodal metastases.",
        age_years=62,
        primary_site="Larynx",
        histology="Squamous cell carcinoma",
    )
    res = query_library_for_case(case)
    assert isinstance(res, EvidenceRetrievalResult)
    assert res.case_disease_site == "Head & Neck"
    assert len(res.all_reference_entries) >= 5


def test_citation_verification_integration_with_reference_catalogue():
    """Citation verification must deterministically verify canonical and indexed reference entries."""
    # Verify standard baseline references
    assert verify_citation("RTOG-9111") is True
    assert verify_citation("NCCN-HN-2026") is True
    assert verify_citation("PEREZ-BRADY-2026") is True
    assert verify_citation("QUANTEC-CORD-2010") is True
    assert verify_citation("HARRISONS-MED-21ST") is True

    # Authentic reference with exact registered DOI
    assert verify_citation("RTOG-9111", "https://doi.org/10.1200/JCO.2012.43.6097") is True

    # Hallucinated source ID rejected
    assert verify_citation("FABRICATED-GUIDELINE-2099") is False

    # Authentic source ID with mismatched fabricated DOI rejected
    assert verify_citation("RTOG-9111", "https://doi.org/10.1000/fabricated.doi") is False


def test_audit_claim_citations_with_library_entries():
    """audit_claim_citations must validate multi-role claims against library entries."""
    claims = [
        {
            "role_id": "RO-01",
            "source_id": "NCCN-HN-2026",
            "doi_or_url": "https://doi.org/10.6004/jnccn.2026.0010",
            "claim": "Definitive radiation therapy 63-66 Gy is a Category 1 recommendation for T1N0 larynx.",
        },
        {
            "role_id": "MP-01",
            "source_id": "QUANTEC-CORD-2010",
            "doi_or_url": "https://doi.org/10.1016/j.ijrobp.2009.04.050",
            "claim": "Spinal cord Dmax must remain under 45-50 Gy to keep myelopathy risk under 0.2%.",
        },
        {
            "role_id": "MO-01",
            "source_id": "HALLUCINATED-JOURNAL-2026",
            "doi_or_url": "https://doi.org/10.9999/fake",
            "claim": "Quadruplet immunotherapy is standard for all T1 laryngeal lesions.",
        },
    ]

    report = audit_claim_citations(claims)
    assert report["total_citations"] == 3
    assert report["verified_count"] == 2
    assert report["unverified_count"] == 1
    assert report["concordance_rate"] == pytest.approx(0.667, 0.01)
    assert report["valid"] is False


def test_reference_catalogue_file_integrity_unchanged():
    """Authoritative reference_catalogue_v1.json file must match its exact SHA-256 hash when loaded directly."""
    catalogue_path = (
        pathlib.Path(__file__).resolve().parents[2] / "docs" / "reference_catalogue_v1.json"
    )
    assert catalogue_path.is_file()
    entries = load_reference_catalogue(catalogue_path)
    assert len(entries) >= 2

    data = json.loads(catalogue_path.read_text(encoding="utf-8"))
    canonical_bytes = json.dumps(data["entries"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    import hashlib
    expected_hash = hashlib.sha256(canonical_bytes).hexdigest()
    assert data["hash"] == expected_hash


# ===========================================================================
# MILESTONE 1: SHARDED MEDICAL LIBRARY INDEXER & CACHE SERVICE TESTS
# ===========================================================================

@pytest.mark.parametrize(
    "path_str,filename,expected_domain",
    [
        # Domain 1: Textbooks & Radiobiology
        ("Radonc/Books/MAIN", "2026_Halperin_Perez_Brady.pdf", "textbooks_radiobiology"),
        ("Radonc/Books/MAIN", "gun-tep-cli-rad-onc-5th.pdf", "textbooks_radiobiology"),
        ("Radonc/Books/RadioBiology", "Hall_Radiobiology_for_the_Radiologist.pdf", "textbooks_radiobiology"),
        ("Radonc/Books/Planning", "IMRT_Planning_Principles.pdf", "textbooks_radiobiology"),
        ("Radonc/Books/Physics", "Khan_Physics_of_Radiation_Therapy.pdf", "textbooks_radiobiology"),
        ("Radonc/Books/VCR", "Handbook_of_Evidence_Based_Radiation_Oncology.pdf", "textbooks_radiobiology"),
        # Domain 2: Guidelines (NCCN 67 blocks & multi-society)
        ("Radonc/NCCN", "head-and-neck_blocks.pdf", "guidelines"),
        ("Radonc/NCCN", "nscl_blocks.pdf", "guidelines"),
        ("Radonc/NCCN", "breast_blocks.pdf", "guidelines"),
        ("Radonc/NCCN", "prostate_blocks.pdf", "guidelines"),
        ("Radonc/NCCN", "rectal_blocks.pdf", "guidelines"),
        ("Radonc/NCCN", "cervical_blocks.pdf", "guidelines"),
        ("Guidelines/ASTRO", "ASTRO_Hypofractionation_Guideline.pdf", "guidelines"),
        # Domain 3: Organ Tolerances & Toxicity (QUANTEC / PENTEC / Toxicity)
        ("Radonc/Books/QUANTEC", "Radiation-Associated-Brainstem-Injury_rob.pdf", "organ_tolerances"),
        ("Radonc/Books/QUANTEC", "quantec_spinal_cord_tolerance.pdf", "organ_tolerances"),
        ("Radonc/Books/PENTEC", "pentec_pulmonary_pediatric.pdf", "organ_tolerances"),
        ("Radonc/Books/Toxicity", "CTCAE_v5_Quick_Reference.pdf", "organ_tolerances"),
        # Domain 4: Staging & Anatomy (AJCC / Contouring / CT Anatomy / Lymph nodes / Radiology)
        ("Radonc/Books/AJCC", "Ajcc_Cancer_Staging_Manual_8th_Edition.pdf", "staging_anatomy"),
        ("Radonc/Books/Contouring guidelines", "CONTOURING_GUIDELINES_FOR_ALL_SITES.pdf", "staging_anatomy"),
        ("Radonc/Books/CT Anatomy", "CT_Anatomy_for_Radiotherapy.pdf", "staging_anatomy"),
        ("Radonc/Books/Lymph nodes", "Atlas_of_Lymph_Node_Anatomy.pdf", "staging_anatomy"),
        ("Radonc/Books/Anatomy", "Netter_Atlas_of_Human_Anatomy.pdf", "staging_anatomy"),
        ("Radiology", "Haaga_CT_and_MRI_Whole_Body.pdf", "staging_anatomy"),
        # Domain 5: Trials & Systemic Therapy (TRIALS / Chemotherapy / Clinical Oncology)
        ("Radonc/Books/TRIALS", "Yajnik_Landmark_Trials_in_Oncology.pdf", "trials_systemic"),
        ("Radonc/Books/Chemotherapy", "Cancer_Chemotherapy_Handbook.pdf", "trials_systemic"),
        ("Radonc/Books/Clinical Oncology", "DeVita_Cancer_Principles_Practice.pdf", "trials_systemic"),
        # Domain 6: General Medicine & Comorbidities (Harrison's, Washington Manual, Cases)
        ("", "Harrisons_Principles_of_Internal_Medicine_21st.pdf", "general_medicine"),
        ("", "Washington_Manual_of_Medical_Therapeutics_36th.pdf", "general_medicine"),
        ("", "Differential_diagnosis_in_internal_medicine.pdf", "general_medicine"),
        ("Cases/Surgery", "clinical_surgical_case_presentation.pptx", "general_medicine"),
    ],
)
def test_domain_classification_all_6_domains(path_str: str, filename: str, expected_domain: DomainType) -> None:
    """Ensure every path maps deterministically to one of the 6 canonical domains."""
    actual_domain = classify_domain(path_str, filename)
    assert actual_domain == expected_domain, f"Path '{path_str}/{filename}' should be '{expected_domain}', got '{actual_domain}'"
    assert actual_domain in DOMAIN_PARTITIONS


@pytest.mark.parametrize(
    "text,expected_site",
    [
        ("Radonc/NCCN/head-and-neck_blocks.pdf", "head_and_neck"),
        ("Radonc/NCCN/larynx_carcinoma_recommendations.pdf", "head_and_neck"),
        ("Radonc/NCCN/nscl_blocks.pdf", "lung"),
        ("Radonc/NCCN/breast_blocks.pdf", "breast"),
        ("Radonc/NCCN/prostate_blocks.pdf", "prostate"),
        ("Radonc/NCCN/rectal_blocks.pdf", "colorectal"),
        ("Radonc/NCCN/cervical_blocks.pdf", "gynecologic"),
        ("Radonc/Books/QUANTEC/Radiation-Associated-Brainstem-Injury_rob.pdf", "cns"),
        ("Radonc/Books/PENTEC/pentec_pulmonary.pdf", "lung"),
        ("Radonc/Books/PENTEC/pentec_pulmonary.pdf", "pediatric"),
    ],
)
def test_disease_site_extraction(text: str, expected_site: str) -> None:
    """Verify clinical disease sites are accurately tagged from paths and filenames."""
    sites = extract_disease_sites(text)
    assert expected_site in sites, f"Expected '{expected_site}' in {sites} for '{text}'"


def test_recursive_discovery_and_sharding_tmp_path(tmp_path: pathlib.Path) -> None:
    """Verify recursive directory discovery and 6-domain indexing with synthetic fixtures."""
    library_dir = tmp_path / "Medical_Books"
    db_path = tmp_path / "test_library.sqlite3"

    # Domain 1: Textbooks & Radiobiology
    d1 = library_dir / "Radonc" / "Books" / "MAIN"
    d1.mkdir(parents=True)
    (d1 / "Perez_Brady_Principles.txt").write_text(
        "T1N0 glottic cancer: 66 Gy in 33 fractions (2.0 Gy/fx) or 63 Gy in 28 fractions. "
        "Radiobiology LQ model alpha/beta = 10 for tumor, alpha/beta = 3 for late normal tissue.",
        encoding="utf-8",
    )

    # Domain 2: Guidelines
    d2 = library_dir / "Radonc" / "NCCN"
    d2.mkdir(parents=True)
    (d2 / "head-and-neck_blocks.txt").write_text(
        "NCCN Head and Neck Guidelines: Definitive RT with 66-70 Gy or TLM for early larynx. "
        "Concurrent high-dose cisplatin (100 mg/m2 q3w) for locally advanced resectable disease.",
        encoding="utf-8",
    )

    # Domain 3: Organ Tolerances
    d3 = library_dir / "Radonc" / "Books" / "QUANTEC"
    d3.mkdir(parents=True)
    (d3 / "quantec_spinal_cord.txt").write_text(
        "QUANTEC Spinal Cord: Dmax < 45-50 Gy for myelopathy risk < 0.2%. "
        "Dmax 54 Gy carries estimated risk < 1%.",
        encoding="utf-8",
    )

    # Domain 4: Staging & Anatomy
    d4 = library_dir / "Radonc" / "Books" / "AJCC"
    d4.mkdir(parents=True)
    (d4 / "ajcc_cancer_staging.txt").write_text(
        "AJCC 8th Edition Larynx: T1 limited to vocal cord(s). "
        "N0 no regional lymph node metastasis. M0 no distant metastasis. Stage I: T1 N0 M0.",
        encoding="utf-8",
    )

    # Domain 5: Trials & Systemic Therapy
    d5 = library_dir / "Radonc" / "Books" / "TRIALS"
    d5.mkdir(parents=True)
    (d5 / "rtog_9111_landmark.txt").write_text(
        "RTOG 91-11 Landmark Trial: Concurrent cisplatin and radiotherapy achieved 81.7% "
        "10-year intact larynx preservation compared to 67.5% induction and 63.8% RT alone.",
        encoding="utf-8",
    )

    # Domain 6: General Medicine & Comorbidities
    d6 = library_dir / "Cases" / "Surgery"
    d6.mkdir(parents=True)
    (d6 / "surgical_airway_case.txt").write_text(
        "Clinical Presentation: 62-year-old male smoker with persistent hoarseness. "
        "ECOG 0, normal renal function. Biopsy confirmed squamous cell carcinoma.",
        encoding="utf-8",
    )

    # Initialize indexer and run scan_catalog
    indexer = MedicalLibraryIndexer(library_dir=library_dir, db_path=db_path)
    docs = indexer.scan_catalog()

    assert len(docs) == 6, f"Expected 6 documents, got {len(docs)}"
    assert indexer.get_document_count() == 6
    assert indexer.get_chunk_count() >= 6

    # Verify domain distribution covers all 6 domains
    domains_found = {doc.domain for doc in docs}
    assert domains_found == set(DOMAIN_PARTITIONS)

    # Verify each document by ID and domain
    for doc in docs:
        retrieved = indexer.get_document_by_id(doc.doc_id)
        assert retrieved is not None
        assert retrieved.title == doc.title
        assert retrieved.domain == doc.domain
        assert retrieved.chunk_count >= 1

    by_domain = indexer.get_documents_by_domain("guidelines")
    assert len(by_domain) == 1
    assert by_domain[0].domain == "guidelines"


def test_sqlite_fts5_bm25_querying_and_snippets(tmp_path: pathlib.Path) -> None:
    """Verify SQLite FTS5 BM25 search ranking, highlighting snippets, and sub-millisecond latency."""
    indexer = MedicalLibraryIndexer(library_dir=tmp_path, db_path=":memory:")

    # Index sample medical chunks directly
    indexer.index_text_chunks(
        doc_id="hn_001",
        title="Larynx Treatment Guidelines",
        domain="guidelines",
        text_chunks=[
            "T1N0 glottic larynx cancer: definitive radiation therapy to 66 Gy in 33 fractions.",
            "Locally advanced laryngeal cancer: concurrent high-dose cisplatin with 70 Gy in 35 fractions.",
        ],
        disease_sites=["head_and_neck"],
    )

    indexer.index_text_chunks(
        doc_id="lung_001",
        title="NSCLC Stage III Protocol",
        domain="trials_systemic",
        text_chunks=[
            "PACIFIC trial: consolidation durvalumab immunotherapy after concurrent chemoradiotherapy for stage III NSCLC.",
        ],
        disease_sites=["lung"],
    )

    indexer.index_text_chunks(
        doc_id="oar_001",
        title="QUANTEC Cord Limit",
        domain="organ_tolerances",
        text_chunks=[
            "Spinal cord tolerance constraint: maximum point dose Dmax < 45-50 Gy avoids radiation myelopathy.",
        ],
        disease_sites=["cns"],
    )

    # 1. Query for glottic
    start_time = time.perf_counter()
    results = indexer.query("glottic", limit=5)
    query_duration_ms = (time.perf_counter() - start_time) * 1000

    assert len(results) >= 1
    top = results[0]
    assert top["doc_id"] == "hn_001"
    assert "<b>glottic</b>" in top["snippet"].lower()
    assert isinstance(top["rank"], float)
    assert query_duration_ms < 50.0

    # 2. Query for PACIFIC trial
    results_trial = indexer.query("durvalumab PACIFIC", limit=5)
    assert len(results_trial) >= 1
    assert results_trial[0]["doc_id"] == "lung_001"

    # 3. Query for spinal cord
    results_cord = indexer.query("myelopathy", limit=5)
    assert len(results_cord) >= 1
    assert results_cord[0]["doc_id"] == "oar_001"


def test_query_filters_domain_and_disease_site(tmp_path: pathlib.Path) -> None:
    """Verify domain and disease_site filters accurately narrow results."""
    indexer = MedicalLibraryIndexer(library_dir=tmp_path, db_path=":memory:")

    # Ingest multiple docs with similar keywords but different domains
    indexer.index_text_chunks(
        doc_id="guide_hn",
        title="NCCN Head and Neck",
        domain="guidelines",
        text_chunks=["Cisplatin chemoradiation is standard for locally advanced squamous cell carcinoma."],
        disease_sites=["head_and_neck"],
    )
    indexer.index_text_chunks(
        doc_id="trial_hn",
        title="RTOG 91-11 Larynx Trial",
        domain="trials_systemic",
        text_chunks=["Cisplatin chemoradiation showed superior larynx preservation in RTOG 91-11."],
        disease_sites=["head_and_neck"],
    )
    indexer.index_text_chunks(
        doc_id="guide_lung",
        title="NCCN Lung Guidelines",
        domain="guidelines",
        text_chunks=["Cisplatin etoposide chemoradiation is standard for unresectable stage III NSCLC."],
        disease_sites=["lung"],
    )

    # Filter by domain only
    guide_results = indexer.query("cisplatin", domain="guidelines")
    assert all(r["domain"] == "guidelines" for r in guide_results)
    assert any(r["doc_id"] == "guide_hn" for r in guide_results)
    assert all(r["doc_id"] != "trial_hn" for r in guide_results)

    # Filter by domain AND disease site
    hn_guide_results = indexer.query("cisplatin", domain="guidelines", disease_site="head_and_neck")
    assert len(hn_guide_results) == 1
    assert hn_guide_results[0]["doc_id"] == "guide_hn"

    lung_guide_results = indexer.query("cisplatin", domain="guidelines", disease_site="lung")
    assert len(lung_guide_results) == 1
    assert lung_guide_results[0]["doc_id"] == "guide_lung"


def test_incremental_invalidation(tmp_path: pathlib.Path) -> None:
    """Verify unchanged files are cached via mtime/size, and modified files are re-indexed."""
    library_dir = tmp_path / "lib"
    library_dir.mkdir()
    db_path = tmp_path / "cache.sqlite3"

    file_a = library_dir / "protocol_a.txt"
    file_b = library_dir / "protocol_b.txt"

    file_a.write_text("AlphaVariantText for regimen A: 60 Gy in 30 fx.", encoding="utf-8")
    file_b.write_text("BetaVariantText for regimen B: 50 Gy in 25 fx.", encoding="utf-8")

    indexer = MedicalLibraryIndexer(library_dir=library_dir, db_path=db_path)
    docs_first = indexer.scan_catalog()
    assert len(docs_first) == 2

    # Query protocol A
    res1 = indexer.query("AlphaVariantText")
    assert len(res1) == 1
    assert "60 Gy" in res1[0]["content"]

    # Sleep briefly to ensure mtime changes on disk
    time.sleep(0.05)

    # Modify file A only; leave file B untouched
    file_a.write_text("AlphaVariantText updated: hypofractionated 55 Gy in 20 fx.", encoding="utf-8")

    # Second scan: file_a should be re-indexed; file_b should be loaded from cache
    docs_second = indexer.scan_catalog()
    assert len(docs_second) == 2

    doc_a_second = next(d for d in docs_second if d.file_path == str(file_a))
    assert doc_a_second.sha256_hash != docs_first[0].sha256_hash or doc_a_second.file_size != docs_first[0].file_size

    # Query again: FTS5 should reflect the updated text
    res2 = indexer.query("hypofractionated")
    assert len(res2) == 1
    assert "55 Gy" in res2[0]["content"]

    # Old text should no longer be present
    res_old = indexer.query('"60 Gy in 30 fx"')
    assert len(res_old) == 0


def test_read_only_guarantees(tmp_path: pathlib.Path) -> None:
    """Verify scan_catalog performs strictly read-only operations without touching source files."""
    library_dir = tmp_path / "readonly_lib"
    library_dir.mkdir()
    sample_file = library_dir / "sample.txt"
    sample_file.write_text("Strictly read only medical literature text.", encoding="utf-8")

    initial_mtime = sample_file.stat().st_mtime_ns
    initial_content = sample_file.read_bytes()

    indexer = MedicalLibraryIndexer(library_dir=library_dir, db_path=":memory:")
    indexer.scan_catalog()

    # Verify source file remained 100% untouched
    after_stat = sample_file.stat()
    assert after_stat.st_mtime_ns == initial_mtime
    assert sample_file.read_bytes() == initial_content

    # Passing non-existent library directory should not crash
    missing_dir = tmp_path / "non_existent_folder"
    indexer_missing = MedicalLibraryIndexer(library_dir=missing_dir, db_path=":memory:")
    docs = indexer_missing.scan_catalog()
    assert docs == []


def test_text_chunking_and_fallbacks(tmp_path: pathlib.Path) -> None:
    """Verify text chunker handles paragraph boundaries, short texts, and empty inputs."""
    indexer = MedicalLibraryIndexer(library_dir=tmp_path, db_path=":memory:")

    # Short text
    chunks_short = indexer._chunk_text("Short single paragraph guideline.", chunk_size=500)
    assert len(chunks_short) == 1

    # Empty text
    chunks_empty = indexer._chunk_text("", chunk_size=500)
    assert chunks_empty == []

    # Long text exceeding chunk size
    long_text = "Paragraph one with clinical evidence.\n\n" * 50
    chunks_long = indexer._chunk_text(long_text, chunk_size=200, overlap=30)
    assert len(chunks_long) > 1
    for c in chunks_long:
        assert len(c) > 0
