"""Unit tests for ComorbidityEvidenceService and clinical decision rules."""
from __future__ import annotations

import pytest
from app.services.comorbidities_service import (
    ComorbidityEvidenceService,
    default_comorbidity_service,
)


def test_catalogue_loading() -> None:
    service = default_comorbidity_service
    assert len(service.entries) >= 11
    assert service.get_entry("WASHMAN-ECOG-KPS-2020") is not None
    assert service.get_entry("washman-cisplatin-renal-2020") is not None
    assert service.get_entry("ACC-AHA-LEE-RCRI-2014") is not None
    assert service.get_entry("NON-EXISTENT") is None


def test_search_by_topic() -> None:
    service = default_comorbidity_service
    renal_entries = service.search_by_topic("renal")
    assert len(renal_entries) >= 2
    ids = [e["source_id"] for e in renal_entries]
    assert "WASHMAN-CISPLATIN-RENAL-2020" in ids
    assert "DECISION-MAKING-ARF-2009" in ids


def test_calculate_creatinine_clearance() -> None:
    service = default_comorbidity_service

    # 60-year-old male, 70 kg, SCr 1.0 mg/dL: (140-60)*70 / 72 = 77.8 mL/min
    crcl_male = service.calculate_creatinine_clearance(
        age=60, weight_kg=70.0, serum_creatinine_mg_dl=1.0, is_female=False
    )
    assert crcl_male == 77.8

    # Same parameters for female: 77.78 * 0.85 = 66.1 mL/min
    crcl_female = service.calculate_creatinine_clearance(
        age=60, weight_kg=70.0, serum_creatinine_mg_dl=1.0, is_female=True
    )
    assert crcl_female == 66.1

    # Impaired renal function: SCr 2.0 mg/dL
    crcl_impaired = service.calculate_creatinine_clearance(
        age=60, weight_kg=70.0, serum_creatinine_mg_dl=2.0, is_female=False
    )
    assert crcl_impaired == 38.9

    # Validation errors
    with pytest.raises(ValueError):
        service.calculate_creatinine_clearance(
            age=-5, weight_kg=70.0, serum_creatinine_mg_dl=1.0, is_female=False
        )
    with pytest.raises(ValueError):
        service.calculate_creatinine_clearance(
            age=60, weight_kg=0.0, serum_creatinine_mg_dl=1.0, is_female=False
        )


def test_calculate_carboplatin_dose() -> None:
    service = default_comorbidity_service

    # Target AUC 5, GFR 75: Dose = 5 * (75 + 25) = 500 mg
    dose = service.calculate_carboplatin_dose(target_auc=5.0, gfr_ml_min=75.0)
    assert dose == 500.0

    # GFR capping at 125 mL/min: Target AUC 6, GFR 160 -> capped at 125 -> Dose = 6 * 150 = 900 mg
    capped_dose = service.calculate_carboplatin_dose(
        target_auc=6.0, gfr_ml_min=160.0, cap_gfr=True
    )
    assert capped_dose == 900.0

    # Uncapped
    uncapped_dose = service.calculate_carboplatin_dose(
        target_auc=6.0, gfr_ml_min=160.0, cap_gfr=False
    )
    assert uncapped_dose == 1110.0


def test_evaluate_performance_status() -> None:
    service = default_comorbidity_service

    # ECOG 0
    res0 = service.evaluate_performance_status(ecog=0)
    assert res0["fitness_tier"] == "fit_for_all_treatments"
    assert res0["multimodal_eligible"] is True

    # ECOG 1
    res1 = service.evaluate_performance_status(ecog=1)
    assert res1["fitness_tier"] == "fit_for_curative_multimodal"
    assert res1["multimodal_eligible"] is True

    # ECOG 2
    res2 = service.evaluate_performance_status(ecog=2)
    assert res2["fitness_tier"] == "borderline_vulnerable"
    assert res2["multimodal_eligible"] is False
    assert "weekly" in res2["conditional_statement"].lower() or "carboplatin" in res2["conditional_statement"].lower()

    # ECOG 3
    res3 = service.evaluate_performance_status(ecog=3)
    assert res3["fitness_tier"] == "unfit_for_aggressive_therapy"

    # Unrecorded (None)
    res_none = service.evaluate_performance_status(ecog=None, kps=None)
    assert res_none["status"] == "unrecorded"
    assert "Assuming baseline ECOG 0-1" in res_none["conditional_statement"]

    # KPS fallback: KPS 70 -> ECOG 2
    res_kps = service.evaluate_performance_status(ecog=None, kps=70)
    assert res_kps["ecog"] == 2


def test_evaluate_renal_fitness() -> None:
    service = default_comorbidity_service

    # CrCl 80 -> Full dose eligible
    res_good = service.evaluate_renal_fitness(crcl_ml_min=80.0)
    assert res_good["eligibility"] == "eligible_full_dose"
    assert res_good["cisplatin_eligible"] is True

    # CrCl 55 -> Borderline
    res_borderline = service.evaluate_renal_fitness(crcl_ml_min=55.0)
    assert res_borderline["eligibility"] == "borderline_modified_regimen"
    assert res_borderline["cisplatin_eligible"] is False
    assert res_borderline["carboplatin_eligible"] is True

    # CrCl 40 -> Cisplatin contraindicated
    res_contra = service.evaluate_renal_fitness(crcl_ml_min=40.0)
    assert res_contra["eligibility"] == "cisplatin_contraindicated"
    assert res_contra["cisplatin_eligible"] is False
    assert res_contra["carboplatin_eligible"] is True

    # CrCl 20 -> ESRD / Chemotherapy contraindicated
    res_esrd = service.evaluate_renal_fitness(crcl_ml_min=20.0)
    assert res_esrd["eligibility"] == "chemotherapy_contraindicated"
    assert res_esrd["cisplatin_eligible"] is False
    assert res_esrd["carboplatin_eligible"] is False

    # Unverified
    res_unverified = service.evaluate_renal_fitness(crcl_ml_min=None)
    assert res_unverified["status"] == "unverified"
    assert "mandatory" in res_unverified["conditional_statement"]


def test_evaluate_cardiopulmonary_risk() -> None:
    service = default_comorbidity_service

    # Normal cardiopulmonary
    res_normal = service.evaluate_cardiopulmonary_risk()
    assert res_normal["fluid_tolerance"] == "normal"
    assert res_normal["pulmonary_fitness"] == "normal"
    assert len(res_normal["warnings"]) == 0

    # CHF and reduced EF
    res_chf = service.evaluate_cardiopulmonary_risk(has_chf=True, lvef_pct=35.0)
    assert res_chf["fluid_tolerance"] == "severely_compromised"
    assert any("pulmonary edema" in w for w in res_chf["warnings"])

    # Active ILD
    res_ild = service.evaluate_cardiopulmonary_risk(has_ild=True)
    assert res_ild["pulmonary_fitness"] == "contraindicated_for_rt"
    assert any("Interstitial Lung Disease" in w for w in res_ild["warnings"])

    # Severe COPD: FEV1 30%
    res_copd = service.evaluate_cardiopulmonary_risk(fev1_pct=30.0, is_active_smoker=True)
    assert res_copd["pulmonary_fitness"] == "very_severe_impairment"
    assert any("smoking" in w.lower() for w in res_copd["warnings"])


def test_evaluate_hematologic_fitness() -> None:
    service = default_comorbidity_service

    # Normal labs
    res_normal = service.evaluate_hematologic_fitness(
        anc_per_ul=2500, platelets_per_ul=220000, hemoglobin_g_dl=13.0
    )
    assert res_normal["chemo_can_proceed"] is True
    assert res_normal["rt_oxygenation_adequate"] is True
    assert len(res_normal["findings"]) == 0

    # Low ANC: 800 -> Hold chemo
    res_low_anc = service.evaluate_hematologic_fitness(anc_per_ul=800)
    assert res_low_anc["chemo_can_proceed"] is False
    assert any("Moderate neutropenia" in f for f in res_low_anc["findings"])

    # Anemia: Hb 9.2 -> RT oxygenation alert
    res_anemia = service.evaluate_hematologic_fitness(hemoglobin_g_dl=9.2)
    assert res_anemia["rt_oxygenation_adequate"] is False
    assert any("radioresponsiveness target" in f for f in res_anemia["findings"])


def test_format_comorbidity_prompt_context() -> None:
    service = default_comorbidity_service
    general_prompt = service.format_comorbidity_prompt_context()
    assert "WASHMAN-ECOG-KPS-2020" in general_prompt
    assert "WASHMAN-CISPLATIN-RENAL-2020" in general_prompt
    assert "DO NOT assume ECOG 0" in general_prompt

    lung_prompt = service.format_comorbidity_prompt_context(disease_site="Lung")
    assert "WASHMAN-PULMONARY-EVAL-2020" in lung_prompt
    assert "FEV1" in lung_prompt

    hn_prompt = service.format_comorbidity_prompt_context(disease_site="Head & Neck")
    assert "WASHMAN-NUTRITION-DYSPHAGIA-2020" in hn_prompt
    assert "PEG/RIG" in hn_prompt
