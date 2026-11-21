"""Regression tests for Requirement U07: Evidence and reference-library architecture.

Validates:
- Structured reference catalogue entries conforming to U07 specification.
- Specialty, disease site, and topic filtering.
- Anti-hallucination citation verification rejecting fabricated sources/DOIs.
- SHA-256 catalog file integrity.
"""
from __future__ import annotations

import pathlib
import pytest

from app.services.reference_catalogue import (
    ReferenceEntry,
    load_reference_catalogue,
    search_reference_catalogue,
    verify_citation,
)


CATALOGUE_PATH = pathlib.Path(__file__).resolve().parents[2] / "docs" / "reference_catalogue_v1.json"


def test_reference_entry_schema_validation() -> None:
    """A reference entry must contain all required U07 fields."""
    entry = ReferenceEntry(
        source_id="ASTRO-LARYNX-2020",
        title="Radiation Therapy for Glottic Squamous Cell Carcinoma: An ASTRO Clinical Practice Guideline",
        organization="American Society for Radiation Oncology (ASTRO)",
        source_type="guideline",
        edition_or_version="2020 Guideline",
        publication_date="2020-04-01",
        update_date="2020-04-01",
        jurisdiction="USA/International",
        specialties=["radiation_oncology"],
        topics=["larynx", "glottic_cancer", "radiotherapy_fractionation"],
        doi_or_url="https://doi.org/10.1016/j.prro.2020.02.004",
        access_status="available",
        supersession="current",
        key_passages=[
            {
                "section": "Recommendation 1.1",
                "text": "For patients with T1N0 glottic cancer, definitive RT is recommended with curative intent.",
            }
        ],
    )
    assert entry.source_id == "ASTRO-LARYNX-2020"
    assert entry.source_type == "guideline"
    assert "radiation_oncology" in entry.specialties


def test_search_reference_catalogue_filtering() -> None:
    """Catalogue search must correctly filter by specialty, disease site, and topic."""
    entries = [
        ReferenceEntry(
            source_id="ASTRO-LARYNX-2020",
            title="ASTRO Larynx Guideline",
            organization="ASTRO",
            source_type="guideline",
            edition_or_version="2020",
            publication_date="2020-01-01",
            specialties=["radiation_oncology"],
            topics=["larynx", "fractionation"],
            doi_or_url="https://doi.org/10.1016/j.prro.2020.02.004",
        ),
        ReferenceEntry(
            source_id="NCCN-HN-2024",
            title="NCCN Clinical Practice Guidelines in Oncology: Head and Neck Cancers",
            organization="NCCN",
            source_type="guideline",
            edition_or_version="Version 1.2024",
            publication_date="2024-01-01",
            specialties=["radiation_oncology", "medical_oncology", "surgical_oncology"],
            topics=["head_and_neck", "larynx", "pharynx", "systemic_therapy"],
            doi_or_url="https://www.nccn.org/professionals/physician_gls/pdf/head-and-neck.pdf",
        ),
        ReferenceEntry(
            source_id="ASCO-IMMUNO-2023",
            title="Management of Immune-Related Toxicities",
            organization="ASCO",
            source_type="guideline",
            edition_or_version="2023 Update",
            publication_date="2023-06-01",
            specialties=["medical_oncology"],
            topics=["immunotherapy", "toxicity"],
            doi_or_url="https://doi.org/10.1200/JCO.22.02568",
        ),
    ]

    # Search for radiation oncology larynx references
    ro_larynx = search_reference_catalogue(
        specialty="radiation_oncology",
        topic="larynx",
        catalogue=entries,
    )
    assert len(ro_larynx) == 2
    ids = {e.source_id for e in ro_larynx}
    assert ids == {"ASTRO-LARYNX-2020", "NCCN-HN-2024"}

    # Search for immunotherapy references
    immuno = search_reference_catalogue(topic="immunotherapy", catalogue=entries)
    assert len(immuno) == 1
    assert immuno[0].source_id == "ASCO-IMMUNO-2023"


def test_citation_verification_detects_fabricated_sources() -> None:
    """Anti-hallucination verification must reject uncatalogued or forged references."""
    entries = [
        ReferenceEntry(
            source_id="RTOG-9111",
            title="Concurrent Chemotherapy and Radiotherapy for Organ Preservation in Advanced Laryngeal Cancer",
            organization="Radiation Therapy Oncology Group",
            source_type="trial",
            edition_or_version="Long-term Follow-up",
            publication_date="2013-03-01",
            specialties=["radiation_oncology", "medical_oncology"],
            topics=["larynx", "organ_preservation", "chemoradiation"],
            doi_or_url="https://doi.org/10.1200/JCO.2012.43.6097",
        )
    ]

    # Authentic reference verifies
    assert verify_citation("RTOG-9111", "https://doi.org/10.1200/JCO.2012.43.6097", catalogue=entries) is True

    # Fabricated source ID rejected
    assert verify_citation("FABRICATED-GUIDELINE-2099", "https://doi.org/10.1200/fake", catalogue=entries) is False

    # Authentic source ID with mismatched fake URL rejected
    assert verify_citation("RTOG-9111", "https://doi.org/10.1000/fabricated.doi", catalogue=entries) is False


def test_reference_catalogue_file_integrity_and_hash() -> None:
    """The authoritative reference catalogue file must exist, validate, and match its SHA-256 digest."""
    import json
    import hashlib

    assert CATALOGUE_PATH.is_file(), f"Missing catalogue at {CATALOGUE_PATH}"
    data = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries") or []
    assert len(entries) >= 2

    # Check that entries load and parse into ReferenceEntry models
    parsed = load_reference_catalogue(CATALOGUE_PATH)
    assert len(parsed) == len(entries)

    # Check SHA-256 integrity
    canonical_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_hash = hashlib.sha256(canonical_bytes).hexdigest()
    assert data["hash"] == expected_hash

