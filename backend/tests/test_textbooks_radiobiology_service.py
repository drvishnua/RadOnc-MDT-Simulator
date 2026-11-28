"""Unit tests for the Textbooks & Radiobiology Evidence Service."""
import pytest
from app.services.textbooks_radiobiology_service import (
    load_textbook_catalogue,
    get_textbook_by_source_id,
    calculate_bed,
    calculate_eqd2,
    calculate_time_corrected_bed,
    calculate_incomplete_repair_bed,
    get_alpha_beta_table,
    get_canonical_alpha_beta,
    get_the_rs_of_radiobiology,
    get_all_canonical_prescriptions,
    get_dose_prescriptions_by_site,
    get_target_volume_definitions,
    get_drug_radiation_interactions,
)


def test_textbook_catalogue_loads_and_has_all_five_books():
    entries = load_textbook_catalogue()
    assert len(entries) >= 5

    source_ids = [e["source_id"] for e in entries]
    assert "TEXTBOOK-KOGEL-2019" in source_ids
    assert "TEXTBOOK-HALL-RADIOBIOLOGY" in source_ids
    assert "TEXTBOOK-PEREZ-BRADY-2026" in source_ids
    assert "TEXTBOOK-GUNDERSON-TEPPER-5TH" in source_ids
    assert "TEXTBOOK-ESSENTIALS-2026" in source_ids

    for e in entries:
        assert "title" in e
        assert "organization" in e
        assert "source_type" in e
        assert "doi_or_url" in e
        assert "edition_or_version" in e


def test_get_textbook_by_source_id():
    perez = get_textbook_by_source_id("TEXTBOOK-PEREZ-BRADY-2026")
    assert perez is not None
    assert "Perez" in perez["title"]
    assert "site_schemes" in perez

    kogel = get_textbook_by_source_id("TEXTBOOK-KOGEL-2019")
    assert kogel is not None
    assert "Basic Clinical Radiobiology" in kogel["title"]
    assert "radiobiology_principles" in kogel


def test_calculate_bed_standard_and_sbrt():
    # Standard 70 Gy in 35 fx (2.0 Gy/fx) with alpha/beta=10 -> BED = 70 * (1 + 2/10) = 84.0 Gy
    assert calculate_bed(70.0, 2.0, 10.0) == 84.0

    # SBRT 54 Gy in 3 fx (18.0 Gy/fx) with alpha/beta=10 -> BED = 54 * (1 + 18/10) = 151.2 Gy
    assert calculate_bed(54.0, 18.0, 10.0) == 151.2

    # Prostate 60 Gy in 20 fx (3.0 Gy/fx) with alpha/beta=1.5 -> BED = 60 * (1 + 3/1.5) = 180.0 Gy
    assert calculate_bed(60.0, 3.0, 1.5) == 180.0

    # Error handling
    with pytest.raises(ValueError):
        calculate_bed(70.0, 2.0, 0.0)
    with pytest.raises(ValueError):
        calculate_bed(-10.0, 2.0, 10.0)


def test_calculate_eqd2():
    # 70 Gy in 35 fx (2.0 Gy/fx) with alpha/beta=10 -> EQD2 = 70.0 Gy
    assert calculate_eqd2(70.0, 2.0, 10.0) == 70.0

    # FAST-Forward 26 Gy in 5 fx (5.2 Gy/fx) with alpha/beta=4.0
    # EQD2 = 26 * (5.2 + 4.0) / (2.0 + 4.0) = 26 * 9.2 / 6.0 = 39.87 Gy
    assert calculate_eqd2(26.0, 5.2, 4.0) == 39.87

    # SBRT 54 Gy in 3 fx (18.0 Gy/fx) with alpha/beta=10 -> EQD2 = 54 * 28 / 12 = 126.0 Gy
    assert calculate_eqd2(54.0, 18.0, 10.0) == 126.0


def test_calculate_time_corrected_bed():
    # 70 Gy in 35 fx over 7 weeks (49 days), kickoff Tk=28 days -> excess 21 days
    # Loss = 21 * 0.6 = 12.6 Gy
    # Base BED = 84.0, Corrected = 84.0 - 12.6 = 71.4 Gy
    assert calculate_time_corrected_bed(70.0, 2.0, 10.0, total_days=49, kickoff_days=28, dose_per_day_loss=0.6) == 71.4

    # If within kickoff time (e.g. 25 days), no loss applied
    assert calculate_time_corrected_bed(70.0, 2.0, 10.0, total_days=25, kickoff_days=28) == 84.0


def test_calculate_incomplete_repair_bed():
    # BID regimen with 6h gap vs 4h gap (repair half-time = 1.0 h)
    # Shorter interval results in higher late-tissue BED due to incomplete repair
    bed_6h = calculate_incomplete_repair_bed(n_fractions=60, dose_per_fraction=1.2, alpha_beta=2.0, hours_between_fractions=6.0)
    bed_4h = calculate_incomplete_repair_bed(n_fractions=60, dose_per_fraction=1.2, alpha_beta=2.0, hours_between_fractions=4.0)
    assert bed_4h > bed_6h


def test_canonical_alpha_beta_table_and_lookup():
    table = get_alpha_beta_table()
    assert table["tumors"]["prostate_adenocarcinoma"] == 1.5
    assert table["tumors"]["head_and_neck_scc"] == 10.0
    assert table["tumors"]["breast_adenocarcinoma"] == 4.0
    assert table["normal_tissues_late"]["spinal_cord_myelopathy"] == 2.0
    assert table["normal_tissues_late"]["brain_necrosis"] == 2.5

    assert get_canonical_alpha_beta("prostate") == 1.5
    assert get_canonical_alpha_beta("spinal cord") == 2.0
    assert get_canonical_alpha_beta("head and neck") == 10.0
    assert get_canonical_alpha_beta("non-existent organ") is None


def test_the_rs_of_radiobiology():
    rs = get_the_rs_of_radiobiology()
    assert len(rs) >= 4
    r_names = [item["r"] for item in rs]
    assert any("Repair" in r for r in r_names)
    assert any("Reassortment" in r for r in r_names)
    assert any("Repopulation" in r for r in r_names)
    assert any("Reoxygenation" in r for r in r_names)


def test_canonical_prescriptions_covers_all_seven_sites():
    all_rx = get_all_canonical_prescriptions()
    assert len(all_rx) >= 15

    sites = {"Head & Neck", "Lung", "Breast", "Prostate", "GI", "GYN", "CNS"}
    for s in sites:
        site_rx = get_dose_prescriptions_by_site(s)
        assert len(site_rx) >= 1, f"Missing canonical prescriptions for disease site: {s}"

        # Verify positive doses and fractions
        for rx in site_rx:
            assert rx.total_dose_gy > 0
            assert rx.fractions > 0
            assert rx.dose_per_fraction_gy > 0
            assert rx.bed_alpha_beta_10 is not None
            assert rx.eqd2_alpha_beta_10 is not None


def test_definitive_vs_adjuvant_filtering():
    hn_def = get_dose_prescriptions_by_site("Head & Neck", setting="definitive")
    assert any("70 Gy" in rx.prescribed_dose for rx in hn_def)
    assert all(rx.setting == "definitive" for rx in hn_def)

    hn_adj = get_dose_prescriptions_by_site("Head & Neck", setting="adjuvant")
    assert any("66 Gy" in rx.prescribed_dose for rx in hn_adj)
    assert all(rx.setting == "adjuvant" for rx in hn_adj)

    breast_adj = get_dose_prescriptions_by_site("Breast", setting="adjuvant")
    assert len(breast_adj) >= 2


def test_target_volumes_and_drug_interactions():
    vols = get_target_volume_definitions()
    assert "gtv" in vols
    assert "ctv" in vols
    assert "itv" in vols
    assert "ptv" in vols
    assert "oar" in vols

    interactions = get_drug_radiation_interactions()
    assert "radiosensitization" in interactions
    agents = [item["agent"] for item in interactions["radiosensitization"]]
    assert "Cisplatin" in agents
    assert "Temozolomide" in agents
    assert "Paclitaxel" in agents
