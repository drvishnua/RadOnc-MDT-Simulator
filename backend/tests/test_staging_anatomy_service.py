"""Unit tests for the Staging, Anatomy & Contouring service and catalogue."""
import pytest
from app.services.staging_anatomy_service import (
    load_staging_catalogue,
    get_staging_by_site,
    get_entry_by_source_id,
    get_cervical_node_levels,
    get_thoracic_node_stations,
    get_pelvic_node_groups,
    get_target_volume_expansions,
    get_elective_nodal_recommendations,
)


def test_staging_catalogue_loads():
    entries = load_staging_catalogue()
    assert len(entries) >= 12
    for entry in entries:
        assert "source_id" in entry
        assert "title" in entry
        assert "organization" in entry
        assert "disease_site" in entry
        assert "edition_or_version" in entry


def test_get_staging_by_site():
    hn_entries = get_staging_by_site("Head & Neck")
    assert len(hn_entries) >= 4
    hn_ids = [e["source_id"] for e in hn_entries]
    assert "AJCC-8TH-ORAL-CAVITY" in hn_ids
    assert "AJCC-8TH-HPV-OROPHARYNX" in hn_ids
    assert "DAHANCA-EORTC-NECK-2014" in hn_ids

    lung_entries = get_staging_by_site("Lung")
    assert len(lung_entries) >= 1
    assert any(e["source_id"] == "AJCC-8TH-9TH-NSCLC" for e in lung_entries)

    breast_entries = get_staging_by_site("Breast")
    assert any(e["source_id"] == "AJCC-8TH-BREAST" for e in breast_entries)

    prostate_entries = get_staging_by_site("Prostate")
    assert any(e["source_id"] == "AJCC-8TH-PROSTATE" for e in prostate_entries)


def test_get_entry_by_source_id():
    entry = get_entry_by_source_id("AJCC-8TH-HPV-OROPHARYNX")
    assert entry is not None
    assert "HPV-Mediated" in entry["title"]
    assert "cN1" in entry["n_definitions_clinical"]
    assert "pN1" in entry["n_definitions_pathological"]

    missing = get_entry_by_source_id("NONEXISTENT-SOURCE")
    assert missing is None


def test_cervical_node_levels():
    levels = get_cervical_node_levels()
    assert "Level Ia (Submental)" in levels
    assert "Level Ib (Submandibular)" in levels
    assert "Level II (Upper Jugular)" in levels
    assert "Level III (Middle Jugular)" in levels
    assert "Level IVa (Lower Jugular)" in levels
    assert "Level VIIa (Retropharyngeal)" in levels

    # Verify anatomical boundaries structure
    level_ia = levels["Level Ia (Submental)"]
    assert "cranial" in level_ia
    assert "caudal" in level_ia
    assert "anterior" in level_ia
    assert "posterior" in level_ia


def test_thoracic_node_stations():
    stations = get_thoracic_node_stations()
    assert "Station 4R (Right Lower Paratracheal)" in stations
    assert "Station 7 (Subcarinal)" in stations
    assert "Station 5 (Subaortic / AP Window)" in stations


def test_pelvic_node_groups():
    groups = get_pelvic_node_groups()
    assert "Common Iliac" in groups
    assert "External Iliac" in groups
    assert "Internal Iliac (Hypogastric)" in groups
    assert "Obturator" in groups
    assert "Presacral" in groups
    assert "vessel_margin" in groups["Common Iliac"]


def test_target_volume_expansions():
    expansions = get_target_volume_expansions()
    assert "Head & Neck CTV-P" in expansions
    assert "Thorax NSCLC CTV" in expansions
    assert "Glioblastoma CTV" in expansions


def test_elective_nodal_recommendations():
    hn_oral = get_elective_nodal_recommendations("Head & Neck", "oral tongue")
    assert "Level Ia" in hn_oral
    assert "Level Ib" in hn_oral

    hn_opc = get_elective_nodal_recommendations("Head & Neck", "tonsil oropharynx")
    assert "Level IIa" in hn_opc
    assert "Level VIIa (Retropharyngeal)" in hn_opc

    lung = get_elective_nodal_recommendations("Lung")
    assert any("Involved Field" in r for r in lung)

    gyn = get_elective_nodal_recommendations("GYN", "cervix")
    assert "External iliac" in gyn
    assert "Internal iliac" in gyn
