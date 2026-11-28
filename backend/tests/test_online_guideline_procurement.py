"""Comprehensive Unit & Integration Test Suite for Online Guideline Procurement Service.

Tests:
1. Seed Registry Completeness: ASTRO, ESTRO, ESMO, ASCO, NCCN across canonical disease sites.
2. Society-Specific Query Methods: fetch_astro, fetch_estro, fetch_esmo, fetch_asco, fetch_nccn.
3. Multi-facet Search & Disease Site Normalization.
4. Local Disk Caching: Structured serialization, atomic write, load, and clearing.
5. Medical Library SQLite FTS5 Indexing Bridge.
6. ReferenceEntry Export & Anti-Hallucination Citation Verification Bridge.
7. Europe PMC Mocked Online Retrieval & Resilient Offline Fallback.

Executes completely offline without external network dependency in < 2 seconds.
"""
from __future__ import annotations

import io
import json
import pathlib
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.services.library_indexer import MedicalLibraryIndexer
from app.services.online_guideline_procurement import (
    OnlineGuidelineProcurementService,
    SocietyGuideline,
    get_curated_seed_guidelines,
    normalize_disease_site,
)
from app.services.reference_catalogue import ReferenceEntry, verify_citation


# ===========================================================================
# 1. Seed Registry Completeness & Data Integrity
# ===========================================================================


def test_seed_guidelines_completeness() -> None:
    seeds = get_curated_seed_guidelines()
    assert len(seeds) >= 10

    societies = {g.society for g in seeds}
    assert societies == {"ASTRO", "ESTRO", "ESMO", "ASCO", "NCCN"}

    disease_sites = {g.disease_site for g in seeds}
    expected_sites = {"head_and_neck", "lung", "gynecologic", "prostate", "gastrointestinal", "breast"}
    assert expected_sites.issubset(disease_sites)

    for g in seeds:
        assert g.source_id
        assert g.title
        assert g.publication_year >= 2020
        assert g.doi or g.pdf_or_text_url
        assert len(g.recommendations) > 0, f"Guideline {g.source_id} missing recommendations"
        assert len(g.target_delineation) > 0, f"Guideline {g.source_id} missing target delineation"

        for rec in g.recommendations:
            assert "topic" in rec
            assert "recommendation" in rec
            assert "evidence_level" in rec

        for td in g.target_delineation:
            assert "volume" in td
            assert "dose_gy" in td
            assert "fractionation" in td


# ===========================================================================
# 2. Society-Specific Query Methods & Site Filtering
# ===========================================================================


def test_fetch_astro_guidelines() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    all_astro = service.fetch_astro_guidelines()
    assert len(all_astro) >= 2
    assert all(g.society == "ASTRO" for g in all_astro)

    hn_astro = service.fetch_astro_guidelines(disease_site="head_and_neck")
    assert len(hn_astro) >= 1
    assert any(g.source_id == "ASTRO-2024-LARYNX" for g in hn_astro)

    lung_astro = service.fetch_astro_guidelines(disease_site="lung")
    assert len(lung_astro) >= 1
    assert any(g.source_id == "ASTRO-2022-NSCLC" for g in lung_astro)


def test_fetch_estro_guidelines() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    all_estro = service.fetch_estro_guidelines()
    assert len(all_estro) >= 2
    assert all(g.society == "ESTRO" for g in all_estro)

    cervix = service.fetch_estro_guidelines(disease_site="gynecologic")
    assert any(g.source_id == "ESTRO-2023-CERVIX" for g in cervix)

    prostate = service.fetch_estro_guidelines(disease_site="prostate")
    assert any(g.source_id == "ESTRO-2022-PROSTATE" for g in prostate)


def test_fetch_esmo_guidelines() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    all_esmo = service.fetch_esmo_guidelines()
    assert len(all_esmo) >= 2
    assert all(g.society == "ESMO" for g in all_esmo)

    gi = service.fetch_esmo_guidelines(disease_site="gastrointestinal")
    assert any(g.source_id == "ESMO-2023-RECTAL" for g in gi)


def test_fetch_asco_guidelines() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    all_asco = service.fetch_asco_guidelines()
    assert len(all_asco) >= 2
    assert all(g.society == "ASCO" for g in all_asco)

    breast = service.fetch_asco_guidelines(disease_site="breast")
    assert any(g.source_id == "ASCO-2023-BREAST" for g in breast)


def test_fetch_nccn_updates() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    all_nccn = service.fetch_nccn_updates()
    assert len(all_nccn) >= 2
    assert all(g.society == "NCCN" for g in all_nccn)

    hn = service.fetch_nccn_updates(disease_site="head_and_neck")
    assert any(g.source_id == "NCCN-2024-HEAD-NECK" for g in hn)


# ===========================================================================
# 3. Keyword Search & Disease Site Normalization
# ===========================================================================


def test_query_guidelines_keyword_filtering() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)

    # Brachytherapy should find cervical IGABT guideline
    brachy_results = service.query_guidelines(keyword="brachytherapy")
    assert len(brachy_results) >= 1
    assert any("ESTRO-2023-CERVIX" in g.source_id for g in brachy_results)

    # Cisplatin should find Head & Neck and Cervical chemoradiation guidelines
    cis_results = service.query_guidelines(keyword="cisplatin")
    assert len(cis_results) >= 2

    # SBRT / stereotactic should find lung guidelines
    sbrt_results = service.query_guidelines(keyword="SBRT")
    assert len(sbrt_results) >= 1
    assert any("ASTRO-2022-NSCLC" in g.source_id for g in sbrt_results)

    # Negative keyword check
    none_results = service.query_guidelines(keyword="nonexistent_xyz_cancer_term")
    assert len(none_results) == 0


def test_normalize_disease_site_synonyms() -> None:
    assert normalize_disease_site("larynx") == "head_and_neck"
    assert normalize_disease_site("glottic") == "head_and_neck"
    assert normalize_disease_site("Oropharyngeal") == "head_and_neck"
    assert normalize_disease_site("NSCLC") == "lung"
    assert normalize_disease_site("pulmonary") == "lung"
    assert normalize_disease_site("mammary") == "breast"
    assert normalize_disease_site("prostatic carcinoma") == "prostate"
    assert normalize_disease_site("cervical") == "gynecologic"
    assert normalize_disease_site("colorectal") == "gastrointestinal"
    assert normalize_disease_site("glioblastoma") == "cns"
    assert normalize_disease_site(None) == "general"
    assert normalize_disease_site("unknown_xyz") == "general"


# ===========================================================================
# 4. Local Caching Roundtrip
# ===========================================================================


def test_local_caching_roundtrip(tmp_path: pathlib.Path) -> None:
    cache_dir = tmp_path / "guidelines_cache"
    service = OnlineGuidelineProcurementService(cache_dir=cache_dir, auto_load_seeds=True)

    # 1. Save to cache
    save_stats = service.save_to_cache()
    assert save_stats["saved_records"] >= 10
    assert save_stats["saved_files"] >= 5

    # Verify directory structure
    astro_dir = cache_dir / "astro"
    assert astro_dir.is_dir()
    assert (astro_dir / "head_and_neck.json").is_file()
    assert (astro_dir / "lung.json").is_file()

    # 2. Create blank service without seeds and reload from cache
    service_blank = OnlineGuidelineProcurementService(cache_dir=cache_dir, auto_load_seeds=False)
    assert service_blank.total_guidelines == 0

    reloaded = service_blank.load_from_cache()
    assert len(reloaded) >= 10
    assert service_blank.total_guidelines >= 10

    # 3. Filtered load by society
    service_blank2 = OnlineGuidelineProcurementService(cache_dir=cache_dir, auto_load_seeds=False)
    astro_only = service_blank2.load_from_cache(society="astro")
    assert len(astro_only) >= 2
    assert all(g.society == "ASTRO" for g in astro_only)

    # 4. Clear cache
    removed = service.clear_cache(society="astro")
    assert removed >= 2
    assert not (astro_dir / "head_and_neck.json").exists()


# ===========================================================================
# 5. Integration Bridge: MedicalLibraryIndexer (SQLite FTS5)
# ===========================================================================


def test_index_into_medical_library_fts5(tmp_path: pathlib.Path) -> None:
    indexer = MedicalLibraryIndexer(library_dir=tmp_path, db_path=":memory:")
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)

    indexed_count = service.index_into_medical_library(indexer)
    assert indexed_count >= 10

    # Query FTS5 for brachytherapy in guidelines domain
    results_brachy = indexer.query("brachytherapy", domain="guidelines")
    assert len(results_brachy) > 0
    assert any("ESTRO-2023-CERVIX" in r["doc_id"] for r in results_brachy)

    # Query FTS5 for cisplatin glottic larynx
    results_larynx = indexer.query("glottic", domain="guidelines")
    assert len(results_larynx) > 0
    assert any("ASTRO-2024-LARYNX" in r["doc_id"] for r in results_larynx)

    # Query FTS5 with disease site filter
    results_lung = indexer.query("SBRT", domain="guidelines", disease_site="lung")
    assert len(results_lung) > 0
    assert any("ASTRO-2022-NSCLC" in r["doc_id"] for r in results_lung)

    indexer.close()


# ===========================================================================
# 6. Integration Bridge: ReferenceEntry & Citation Verification
# ===========================================================================


def test_export_reference_entries_and_verify_citation() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    entries = service.export_reference_entries()

    assert len(entries) >= 10
    for e in entries:
        assert isinstance(e, ReferenceEntry)
        assert e.source_type == "guideline"
        assert len(e.aliases) >= 2
        assert len(e.key_passages) > 0

    # Test anti-hallucination verification against exported catalogue
    assert verify_citation("ASTRO-2024-LARYNX", catalogue=entries) is True
    assert verify_citation("ASTRO 2024 LARYNX", catalogue=entries) is True
    assert verify_citation("ESTRO-2023-CERVIX", catalogue=entries) is True
    assert verify_citation("ESMO-2024-NSCLC", catalogue=entries) is True
    assert verify_citation("ASCO-2023-BREAST", catalogue=entries) is True
    assert verify_citation("NCCN-2024-HEAD-NECK", catalogue=entries) is True

    # Negative test: fabricated citation must be rejected
    assert verify_citation("FABRICATED-2025-RADIATION", catalogue=entries) is False
    assert verify_citation("UNREGISTERED-TRIAL-9999", catalogue=entries) is False


# ===========================================================================
# 7. Online Procurement Helpers (Europe PMC Mock & Offline Fallback)
# ===========================================================================


def test_query_europe_pmc_mock_success() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=False)

    sample_api_response = {
        "resultList": {
            "result": [
                {
                    "id": "38245678",
                    "title": "Radiation Therapy for Oropharyngeal and Laryngeal Squamous Cell Carcinoma",
                    "pubYear": "2024",
                    "doi": "10.1016/j.prro.2024.01.002",
                    "abstractText": "Clinical practice guideline from ASTRO on target delineation and dose.",
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(sample_api_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = service.query_europe_pmc("ASTRO larynx guideline")
        assert len(results) == 1
        assert results[0]["id"] == "38245678"

        # Test online guideline fetch and registration
        fetched = service.fetch_online_guideline_updates("ASTRO", "head_and_neck")
        assert len(fetched) == 1
        assert fetched[0].society == "ASTRO"
        assert fetched[0].publication_year == 2024
        assert service.total_guidelines == 1


def test_query_europe_pmc_offline_fallback() -> None:
    # Service with seed guidelines preloaded
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)

    # When network fails, query_europe_pmc must return empty list without raising
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network unreachable")):
        raw = service.query_europe_pmc("ASTRO lung")
        assert raw == []

        # fetch_online_guideline_updates falls back gracefully to local matching seed guidelines
        fallback = service.fetch_online_guideline_updates("ASTRO", "lung")
        assert len(fallback) >= 1
        assert any(g.source_id == "ASTRO-2022-NSCLC" for g in fallback)


def test_register_custom_guideline() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=False)
    custom = SocietyGuideline(
        society="ASTRO",
        title="ASTRO Consensus on Oligometastases",
        disease_site="general",
        publication_year=2025,
        doi="10.1016/j.ijrobp.2025.01.001",
        source_id="ASTRO-2025-OLIGO",
        summary="Clinical consensus on stereotactic radiation for oligometastatic disease.",
        recommendations=[
            {
                "topic": "Extracranial Oligometastases",
                "recommendation": "SBRT with BED10 >= 100 Gy is recommended for 1-5 active lesions.",
                "evidence_level": "Level 1B",
            }
        ],
        target_delineation=[
            {
                "volume": "GTV_Oligo",
                "dose_gy": 50.0,
                "fractionation": "10.0 Gy x 5 fx",
            }
        ],
    )

    service.register_guideline(custom)
    assert service.total_guidelines == 1
    found = service.query_guidelines(keyword="oligometastases")
    assert len(found) == 1
    assert found[0].source_id == "ASTRO-2025-OLIGO"


# ===========================================================================
# 8. Edge Cases, Corruption Resilience & Validation
# ===========================================================================


def test_empty_query_returns_all() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)
    assert len(service.query_guidelines()) == service.total_guidelines


def test_query_guidelines_multiple_filters() -> None:
    service = OnlineGuidelineProcurementService(auto_load_seeds=True)

    # 1. ASTRO + head_and_neck + glottic -> ASTRO-2024-LARYNX
    res1 = service.query_guidelines(society="ASTRO", disease_site="head_and_neck", keyword="glottic")
    assert len(res1) == 1
    assert res1[0].source_id == "ASTRO-2024-LARYNX"

    # 2. ESMO + gastrointestinal + TNT -> ESMO-2023-RECTAL
    res2 = service.query_guidelines(society="ESMO", disease_site="gastrointestinal", keyword="TNT")
    assert len(res2) == 1
    assert res2[0].source_id == "ESMO-2023-RECTAL"

    # 3. Cross mismatch: ASTRO + breast -> empty (seeds have ASCO/NCCN for breast)
    res3 = service.query_guidelines(society="ASTRO", disease_site="breast")
    assert len(res3) == 0


def test_load_from_cache_corrupted_file_resilience(tmp_path: pathlib.Path) -> None:
    cache_dir = tmp_path / "corrupted_cache"
    soc_dir = cache_dir / "astro"
    soc_dir.mkdir(parents=True, exist_ok=True)

    # Write a corrupted non-JSON file
    (soc_dir / "bad.json").write_text("INVALID JSON NOT A LIST OR OBJECT", encoding="utf-8")

    service = OnlineGuidelineProcurementService(cache_dir=cache_dir, auto_load_seeds=False)
    # Must not crash, should log warning and return empty
    loaded = service.load_from_cache()
    assert loaded == []
    assert service.total_guidelines == 0


def test_society_guideline_pydantic_validation() -> None:
    from pydantic import ValidationError

    # Invalid society literal
    with pytest.raises(ValidationError):
        SocietyGuideline(
            society="INVALID_SOCIETY",  # type: ignore[arg-type]
            title="Invalid",
            disease_site="general",
            publication_year=2024,
            source_id="INVALID-1",
        )

    # Valid minimal guideline with default factories
    valid_minimal = SocietyGuideline(
        society="ASTRO",
        title="Minimal ASTRO Guideline",
        disease_site="head_and_neck",
        publication_year=2024,
        source_id="ASTRO-2024-MIN",
    )
    assert valid_minimal.recommendations == []
    assert valid_minimal.target_delineation == []
    assert valid_minimal.summary == ""
