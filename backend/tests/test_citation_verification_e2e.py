"""Comprehensive End-to-End Test Suite for Milestone 3 Citation Verification.

Validates:
1. ReferenceEntry model extension with aliases.
2. Active reference catalogue dynamic loader with MedicalLibraryIndexer integration.
3. Alias-tolerant citation resolution (hyphens, spaces, uppercase, title variants).
4. Strict anti-hallucination rejection of fabricated/ungrounded trial and guideline references.
5. DOI and URL verification (standard DOIs, case-insensitivity, trailing-slash, file:/// URIs).
6. Multi-specialist persona citation audit across RO, MO, SO, DS, PP, and SG roles.
7. Edge cases (empty strings, None values, whitespace, special characters).
"""
from __future__ import annotations

import pathlib
import pytest

from app.services.reference_catalogue import (
    ReferenceEntry,
    audit_claim_citations,
    get_active_reference_catalogue,
    load_reference_catalogue,
    search_reference_catalogue,
    verify_citation,
)
from app.services.library_indexer import IndexedDocument, MedicalLibraryIndexer


STATIC_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "docs" / "reference_catalogue_v1.json"
)


# ---------------------------------------------------------------------------
# 1. ReferenceEntry Aliases Field
# ---------------------------------------------------------------------------


def test_reference_entry_aliases_support() -> None:
    """ReferenceEntry must allow specifying aliases, defaulting to an empty list."""
    default_entry = ReferenceEntry(
        source_id="TEST-001",
        title="Test Guideline",
        organization="Test Org",
        source_type="guideline",
        edition_or_version="2024",
        publication_date="2024-01-01",
        doi_or_url="https://doi.org/10.1000/182",
    )
    assert default_entry.aliases == []

    aliased_entry = ReferenceEntry(
        source_id="RTOG-0617",
        title="High-Dose vs Standard-Dose Chemoradiotherapy in NSCLC",
        organization="Radiation Therapy Oncology Group",
        source_type="trial",
        edition_or_version="Phase III",
        publication_date="2015-05-01",
        doi_or_url="https://doi.org/10.1016/S1470-2045(14)71207-0",
        aliases=["RTOG 0617", "RTOG 06-17", "RTOG0617"],
    )
    assert "RTOG 0617" in aliased_entry.aliases
    assert len(aliased_entry.aliases) == 3


# ---------------------------------------------------------------------------
# 2. Static and Dynamic Catalogue Loading
# ---------------------------------------------------------------------------


def test_get_active_reference_catalogue_static_only() -> None:
    """get_active_reference_catalogue loads static seed entries with canonical aliases."""
    catalogue = get_active_reference_catalogue(static_catalogue_path=STATIC_CATALOGUE_PATH)
    assert len(catalogue) >= 2
    source_ids = {e.source_id for e in catalogue}
    assert "ASTRO-LARYNX-2020" in source_ids
    assert "RTOG-9111" in source_ids

    # Confirm canonical aliases were attached to the base entries
    rtog = next(e for e in catalogue if e.source_id == "RTOG-9111")
    assert any("9111" in a for a in rtog.aliases)


def test_get_active_reference_catalogue_with_duck_typed_indexer() -> None:
    """get_active_reference_catalogue converts duck-typed IndexedDocuments and maps domains."""
    mock_docs = [
        IndexedDocument(
            doc_id="NCCN-HEAD-AND-NECK",
            file_path="C:/Users/VCR/RadOnc/Medical books/Radonc/NCCN/head-and-neck_blocks.pdf",
            title="Head and Neck Blocks NCCN",
            domain="guidelines",
            disease_sites=["head_and_neck", "larynx"],
            sha256_hash="a" * 64,
            mtime_ns=1000,
            file_size=50000,
        ),
        IndexedDocument(
            doc_id="PEREZ-BRADY-RADIOBIOLOGY",
            file_path="C:/Users/VCR/RadOnc/Medical books/Radonc/Books/MAIN/PerezBrady2026.pdf",
            title="Perez and Brady Radiobiology",
            domain="textbooks_radiobiology",
            disease_sites=["general"],
            sha256_hash="b" * 64,
            mtime_ns=2000,
            file_size=800000,
        ),
        IndexedDocument(
            doc_id="QUANTEC-PAROTID-MONOGRAPH",
            file_path="C:/Users/VCR/RadOnc/Medical books/Radonc/Books/QUANTEC/quantec_parotid.pdf",
            title="QUANTEC Parotid Salivary Gland",
            domain="organ_tolerances",
            disease_sites=["head_and_neck"],
            sha256_hash="c" * 64,
            mtime_ns=3000,
            file_size=20000,
        ),
    ]

    catalogue = get_active_reference_catalogue(
        static_catalogue_path=STATIC_CATALOGUE_PATH,
        indexer=mock_docs,
    )

    ids = {e.source_id for e in catalogue}
    assert "NCCN-HEAD-AND-NECK" in ids
    assert "PEREZ-BRADY-RADIOBIOLOGY" in ids
    assert "QUANTEC-PAROTID-MONOGRAPH" in ids

    nccn_entry = next(e for e in catalogue if e.source_id == "NCCN-HEAD-AND-NECK")
    assert nccn_entry.source_type == "guideline"
    assert "head_and_neck" in nccn_entry.topics
    assert "head-and-neck_blocks" in nccn_entry.aliases or "Head and Neck Blocks NCCN" in nccn_entry.aliases

    perez_entry = next(e for e in catalogue if e.source_id == "PEREZ-BRADY-RADIOBIOLOGY")
    assert perez_entry.source_type == "textbook"

    quantec_entry = next(e for e in catalogue if e.source_id == "QUANTEC-PAROTID-MONOGRAPH")
    assert quantec_entry.source_type == "consensus"


def test_get_active_reference_catalogue_with_medical_library_indexer(tmp_path: pathlib.Path) -> None:
    """Integration test: MedicalLibraryIndexer populates active catalogue via SQLite FTS5."""
    db_path = tmp_path / "test_indexer.db"
    indexer = MedicalLibraryIndexer(library_dir=tmp_path, db_path=db_path)

    indexer.index_text_chunks(
        doc_id="SYNTH-TRIAL-001",
        title="Phase III Laryngeal Preservation Trial",
        domain="trials_systemic",
        text_chunks=["Concurrent cisplatin with definitive radiation."],
        disease_sites=["larynx"],
        file_path=str(tmp_path / "synth_trial.pdf"),
    )

    catalogue = get_active_reference_catalogue(
        static_catalogue_path=STATIC_CATALOGUE_PATH,
        indexer=indexer,
    )
    indexer.close()

    synth_entry = next((e for e in catalogue if e.source_id == "SYNTH-TRIAL-001"), None)
    assert synth_entry is not None
    assert synth_entry.source_type == "trial"
    assert synth_entry.edition_or_version == "Indexed"
    assert "synth_trial" in synth_entry.aliases or "Phase III Laryngeal Preservation Trial" in synth_entry.aliases


# ---------------------------------------------------------------------------
# 3. Alias-Tolerant Citation Verification
# ---------------------------------------------------------------------------


def test_alias_tolerant_citation_verification() -> None:
    """verify_citation must resolve hyphen, space, punctuation, and registered aliases."""
    test_entries = [
        ReferenceEntry(
            source_id="RTOG-0617",
            title="High-dose vs standard-dose radiation in NSCLC",
            organization="NRG/RTOG",
            source_type="trial",
            edition_or_version="Phase III",
            publication_date="2015-01-01",
            doi_or_url="https://doi.org/10.1016/S1470-2045(14)71207-0",
            aliases=["RTOG 0617", "RTOG 06-17", "RTOG0617"],
        ),
        ReferenceEntry(
            source_id="QUANTEC-PAROTID-2010",
            title="Radiation dose-volume effects in the salivary glands",
            organization="QUANTEC",
            source_type="consensus",
            edition_or_version="2010",
            publication_date="2010-03-01",
            doi_or_url="https://doi.org/10.1016/j.ijrobp.2009.09.042",
            aliases=["QUANTEC Parotid", "QUANTEC Salivary"],
        ),
        ReferenceEntry(
            source_id="NCCN-HN-2026",
            title="NCCN Clinical Practice Guidelines: Head and Neck",
            organization="NCCN",
            source_type="guideline",
            edition_or_version="1.2026",
            publication_date="2026-01-01",
            doi_or_url="https://doi.org/10.6004/jnccn.2026.0010",
            aliases=["NCCN Head & Neck Guidelines", "NCCN Head and Neck"],
        ),
    ]

    # Exact source_id matches
    assert verify_citation("RTOG-0617", catalogue=test_entries) is True
    assert verify_citation("QUANTEC-PAROTID-2010", catalogue=test_entries) is True

    # Punctuation / space variations on source_id
    assert verify_citation("RTOG 0617", catalogue=test_entries) is True
    assert verify_citation("rtog_0617", catalogue=test_entries) is True
    assert verify_citation("RTOG0617", catalogue=test_entries) is True
    assert verify_citation("quantec-parotid-2010", catalogue=test_entries) is True
    assert verify_citation("QUANTEC PAROTID 2010", catalogue=test_entries) is True

    # Alias matches
    assert verify_citation("QUANTEC Parotid", catalogue=test_entries) is True
    assert verify_citation("quantec parotid", catalogue=test_entries) is True
    assert verify_citation("NCCN Head & Neck Guidelines", catalogue=test_entries) is True
    assert verify_citation("NCCN Head and Neck", catalogue=test_entries) is True


# ---------------------------------------------------------------------------
# 4. Strict Anti-Hallucination Rejection
# ---------------------------------------------------------------------------


def test_strict_anti_hallucination_rejection() -> None:
    """verify_citation must strictly reject fabricated or ungrounded citations."""
    catalogue = get_active_reference_catalogue(static_catalogue_path=STATIC_CATALOGUE_PATH)

    # Fabricated / forged identifiers
    assert verify_citation("FABRICATED-2099", catalogue=catalogue) is False
    assert verify_citation("FAKE-TRIAL-9999", catalogue=catalogue) is False
    assert verify_citation("RANDOM-PHARMA-STUDY-2026", catalogue=catalogue) is False
    assert verify_citation("NONEXISTENT_GUIDELINE", catalogue=catalogue) is False

    # Generic or truncated tokens that should not trigger false positive matches
    assert verify_citation("RT", catalogue=catalogue) is False
    assert verify_citation("NCCN", catalogue=catalogue) is False
    assert verify_citation("ASTRO", catalogue=catalogue) is False


def test_citation_verification_edge_cases() -> None:
    """Empty, whitespace, None, and short strings must safely return False."""
    catalogue = get_active_reference_catalogue(static_catalogue_path=STATIC_CATALOGUE_PATH)

    assert verify_citation("", catalogue=catalogue) is False
    assert verify_citation("   ", catalogue=catalogue) is False
    assert verify_citation(None, catalogue=catalogue) is False  # type: ignore[arg-type]
    assert verify_citation("--", catalogue=catalogue) is False
    assert verify_citation("::", catalogue=catalogue) is False
    assert verify_citation("X", catalogue=catalogue) is False
    assert verify_citation(12345, catalogue=catalogue) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 5. DOI and URL Verification
# ---------------------------------------------------------------------------


def test_doi_and_url_verification() -> None:
    """verify_citation must enforce DOI correctness and accept local file:/// URIs."""
    test_entries = [
        ReferenceEntry(
            source_id="RTOG-9111",
            title="Laryngeal preservation trial",
            organization="RTOG",
            source_type="trial",
            edition_or_version="Phase III",
            publication_date="2013-01-01",
            doi_or_url="https://doi.org/10.1200/JCO.2012.43.6097",
        ),
        ReferenceEntry(
            source_id="LOCAL-BOOK-001",
            title="Local Textbook Reference",
            organization="Medical Library",
            source_type="textbook",
            edition_or_version="Indexed",
            publication_date="2024-01-01",
            doi_or_url="file:///C:/Users/VCR/RadOnc/Medical books/book.pdf",
        ),
    ]

    # Valid matching DOI
    assert verify_citation(
        "RTOG-9111",
        "https://doi.org/10.1200/JCO.2012.43.6097",
        catalogue=test_entries,
    ) is True

    # Case-insensitive and trailing-slash tolerant DOI match
    assert verify_citation(
        "RTOG-9111",
        "https://doi.org/10.1200/jco.2012.43.6097/",
        catalogue=test_entries,
    ) is True

    # Forged DOI for authentic source ID rejected
    assert verify_citation(
        "RTOG-9111",
        "https://doi.org/10.9999/forged.doi.link",
        catalogue=test_entries,
    ) is False

    # Local file:/// URI is considered valid when source_id matches
    assert verify_citation(
        "LOCAL-BOOK-001",
        "file:///C:/Users/VCR/RadOnc/Medical books/book.pdf",
        catalogue=test_entries,
    ) is True
    assert verify_citation(
        "LOCAL-BOOK-001",
        None,
        catalogue=test_entries,
    ) is True


# ---------------------------------------------------------------------------
# 6. Multi-Specialist Persona Citation Audit (RO, MO, SO, DS, PP, SG)
# ---------------------------------------------------------------------------


def test_audit_claim_citations_across_specialist_roster() -> None:
    """audit_claim_citations must audit citations across diverse specialist roles."""
    catalogue = [
        ReferenceEntry(
            source_id="ASTRO-LARYNX-2020",
            title="ASTRO Glottic Cancer Guideline",
            organization="ASTRO",
            source_type="guideline",
            edition_or_version="2020",
            publication_date="2020-04-01",
            doi_or_url="https://doi.org/10.1016/j.prro.2020.02.004",
            aliases=["ASTRO Larynx Guideline", "ASTRO 2020 Larynx"],
        ),
        ReferenceEntry(
            source_id="QUANTEC-PAROTID-2010",
            title="QUANTEC Salivary Toxicity",
            organization="QUANTEC",
            source_type="consensus",
            edition_or_version="2010",
            publication_date="2010-03-01",
            doi_or_url="https://doi.org/10.1016/j.ijrobp.2009.09.042",
            aliases=["QUANTEC Parotid", "QUANTEC Salivary"],
        ),
        ReferenceEntry(
            source_id="RTOG-9111",
            title="Laryngeal Organ Preservation",
            organization="RTOG",
            source_type="trial",
            edition_or_version="Phase III",
            publication_date="2013-02-01",
            doi_or_url="https://doi.org/10.1200/JCO.2012.43.6097",
            aliases=["RTOG 91-11", "RTOG 9111"],
        ),
        ReferenceEntry(
            source_id="NCCN-HN-2026",
            title="NCCN Head and Neck Cancers",
            organization="NCCN",
            source_type="guideline",
            edition_or_version="1.2026",
            publication_date="2026-01-15",
            doi_or_url="https://doi.org/10.6004/jnccn.2026.0010",
            aliases=["NCCN Head & Neck Guidelines", "NCCN Head and Neck"],
        ),
    ]

    claims = [
        # Radiation Oncologist (RO-01): Valid canonical source
        {
            "role_id": "RO-01",
            "source_id": "ASTRO-LARYNX-2020",
            "doi_or_url": "https://doi.org/10.1016/j.prro.2020.02.004",
            "claim": "Definitive radiation is recommended for early glottic carcinoma.",
        },
        # Radiation Oncologist / Dosimetrist (RO-02): Valid alias
        {
            "role_id": "RO-02",
            "source_id": "QUANTEC Parotid",
            "doi_or_url": None,
            "claim": "Mean dose to at least one parotid gland should be < 20 Gy to preserve function.",
        },
        # Medical Oncologist (MO-01): Valid hyphenated alias
        {
            "role_id": "MO-01",
            "source_id": "RTOG 91-11",
            "doi_or_url": "https://doi.org/10.1200/JCO.2012.43.6097",
            "claim": "Concurrent high-dose cisplatin with radiation maximizes intact larynx preservation.",
        },
        # Surgical Oncologist (SO-01): Valid title alias
        {
            "role_id": "SO-01",
            "source_id": "NCCN Head & Neck Guidelines",
            "doi_or_url": None,
            "claim": "TLM and definitive RT show equivalent 5-year local control in T1a glottic disease.",
        },
        # Diagnostic Specialist / Pathologist (DS-02): Hallucinated trial citation
        {
            "role_id": "DS-02",
            "source_id": "FABRICATED-PATHOLOGY-TRIAL-2099",
            "doi_or_url": "https://doi.org/10.1000/fabricated.doi",
            "claim": "Novel molecular biomarker demonstrates 100% sensitivity for occult nodal metastasis.",
        },
        # System & Governance / Evidence Auditor (SG-05): Forged trial citation
        {
            "role_id": "SG-05",
            "source_id": "FAKE-GOVERNANCE-GUIDELINE-8888",
            "doi_or_url": None,
            "claim": "Mandatory protocol compliance audit requires ungrounded study.",
        },
        # Patient Perspective (PP-01): Empty citation ignored
        {
            "role_id": "PP-01",
            "source_id": "",
            "claim": "Patient prioritizes vocal quality and swallowing preservation.",
        },
    ]

    report = audit_claim_citations(claims, catalogue=catalogue)

    assert report["total_citations"] == 6
    assert report["verified_count"] == 4
    assert report["unverified_count"] == 2
    assert report["concordance_rate"] == round(4 / 6, 3)
    assert report["valid"] is False

    verified_roles = {c["role_id"] for c in report["verified_citations"]}
    assert verified_roles == {"RO-01", "RO-02", "MO-01", "SO-01"}

    unverified_roles = {c["role_id"] for c in report["unverified_citations"]}
    assert unverified_roles == {"DS-02", "SG-05"}


def test_audit_claim_citations_default_active_catalogue() -> None:
    """When catalogue is None, audit_claim_citations defaults to get_active_reference_catalogue."""
    claims = [
        {
            "role_id": "RO-01",
            "source_id": "RTOG-9111",
            "claim": "Laryngeal preservation established in RTOG 91-11.",
        },
    ]
    report = audit_claim_citations(claims, catalogue=None)
    assert report["total_citations"] == 1
    assert report["verified_count"] == 1
    assert report["unverified_count"] == 0
    assert report["valid"] is True


def test_search_reference_catalogue_with_active_catalogue() -> None:
    """search_reference_catalogue defaults to active catalogue and supports filtering."""
    results = search_reference_catalogue(topic="larynx")
    assert len(results) >= 1
    assert any(e.source_id == "ASTRO-LARYNX-2020" for e in results)
