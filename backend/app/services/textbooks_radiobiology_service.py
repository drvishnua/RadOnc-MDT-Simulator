"""Textbooks & Radiobiology Evidence Service conforming to Requirement U07 and repository safety contract (AGENTS.md).

Provides deterministic access to:
- Authoritative radiation oncology textbook evidence (Perez & Brady 2026, Gunderson & Tepper 5th Ed,
  2026 Essentials of Clinical Radiation Oncology, Kogel Basic Clinical Radiobiology 2019,
  Hall & Giaccia Radiobiology for the Radiologist 8th Ed).
- Canonical radiation oncology dose fractionation schemes across all 7 disease sites
  (Head & Neck, Lung, Breast, Prostate, GI, GYN, CNS) for definitive and adjuvant intent.
- Mathematical radiobiological principles: Linear-Quadratic (LQ) cell survival model,
  Biologically Effective Dose (BED), Equivalent Dose in 2 Gy fractions (EQD2),
  incomplete repair models, proliferation time factor corrections, and canonical alpha/beta tables.
- ICRU target volume definitions (GTV, CTV, ITV, PTV, OAR, PRV) and drug-radiation interaction mechanisms.
"""
from __future__ import annotations

import json
import math
import pathlib
from typing import Any, Literal
from pydantic import BaseModel, Field

_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "evidence_catalogues" / "textbooks_radiobiology_catalogue.json"
)

DiseaseSite = Literal[
    "Head & Neck",
    "Lung",
    "Breast",
    "Prostate",
    "GI",
    "GYN",
    "CNS",
    "General",
]

TreatmentSetting = Literal["all", "definitive", "adjuvant", "palliative"]


class CanonicalPrescription(BaseModel):
    """Structured representation of a canonical dose-fractionation scheme."""

    site: str
    clinical_scenario: str
    prescribed_dose: str
    total_dose_gy: float
    fractions: int
    dose_per_fraction_gy: float
    setting: Literal["definitive", "adjuvant", "palliative"]
    technique: str = ""
    target_volumes: str = ""
    concurrent_agent: str = "None"
    bed_alpha_beta_10: float | None = None
    bed_alpha_beta_3: float | None = None
    eqd2_alpha_beta_10: float | None = None
    eqd2_alpha_beta_3: float | None = None
    citation: str = ""
    notes: str = ""


def load_textbook_catalogue(path: pathlib.Path | None = None) -> list[dict[str, Any]]:
    """Load raw textbook entries from the authoritative JSON catalogue."""
    target_path = path or _CATALOGUE_PATH
    if not target_path.is_file():
        return []
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        return data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def get_textbook_by_source_id(source_id: str, path: pathlib.Path | None = None) -> dict[str, Any] | None:
    """Retrieve a specific textbook entry by its uppercase source identifier."""
    entries = load_textbook_catalogue(path)
    clean_id = source_id.strip().upper()
    return next((e for e in entries if e.get("source_id", "").strip().upper() == clean_id), None)


# ---------------------------------------------------------------------------
# MATHEMATICAL RADIOBIOLOGY ENGINE
# ---------------------------------------------------------------------------

def calculate_bed(total_dose: float, dose_per_fraction: float, alpha_beta: float) -> float:
    """Calculate Biologically Effective Dose (BED) using the linear-quadratic equation:

    BED = D * (1 + d / (alpha / beta))
    """
    if alpha_beta <= 0:
        raise ValueError("alpha_beta ratio must be strictly positive.")
    if total_dose < 0 or dose_per_fraction < 0:
        raise ValueError("Dose values cannot be negative.")
    return round(total_dose * (1.0 + dose_per_fraction / alpha_beta), 2)


def calculate_eqd2(total_dose: float, dose_per_fraction: float, alpha_beta: float) -> float:
    """Calculate Equivalent Dose in 2 Gy fractions (EQD2):

    EQD2 = Total_Dose * (dose_per_fraction + alpha_beta) / (2.0 + alpha_beta)
         = BED / (1.0 + 2.0 / alpha_beta)
    """
    if alpha_beta <= 0:
        raise ValueError("alpha_beta ratio must be strictly positive.")
    if total_dose < 0 or dose_per_fraction < 0:
        raise ValueError("Dose values cannot be negative.")
    return round(total_dose * ((dose_per_fraction + alpha_beta) / (2.0 + alpha_beta)), 2)


def calculate_time_corrected_bed(
    total_dose: float,
    dose_per_fraction: float,
    alpha_beta: float,
    total_days: int,
    kickoff_days: int = 28,
    dose_per_day_loss: float = 0.6,
) -> float:
    """Calculate Biologically Effective Dose with time factor correction for accelerated tumor repopulation:

    BED_corrected = BED - D_prolif * max(0, total_days - kickoff_days)
    Standard in Head & Neck SCC where Tk ~ 28 days and D_prolif ~ 0.6 Gy/day.
    """
    base_bed = calculate_bed(total_dose, dose_per_fraction, alpha_beta)
    excess_days = max(0, total_days - kickoff_days)
    loss = excess_days * dose_per_day_loss
    return round(max(0.0, base_bed - loss), 2)


def calculate_incomplete_repair_bed(
    n_fractions: int,
    dose_per_fraction: float,
    alpha_beta: float,
    hours_between_fractions: float,
    repair_halftime_hours: float = 1.0,
) -> float:
    """Calculate Biologically Effective Dose for twice-daily (hyperfractionated) regimens

    accounting for Lea-Catcheside incomplete repair factor:
    h_m = exp(-mu * Delta_t) where mu = ln(2) / T_1/2
    BED = n * d * [1 + (d / (alpha/beta)) * (1 + h_m)]
    """
    if alpha_beta <= 0:
        raise ValueError("alpha_beta ratio must be strictly positive.")
    if repair_halftime_hours <= 0:
        raise ValueError("repair_halftime_hours must be strictly positive.")

    mu = math.log(2.0) / repair_halftime_hours
    hm = math.exp(-mu * hours_between_fractions)
    total_dose = n_fractions * dose_per_fraction
    bed = total_dose * (1.0 + (dose_per_fraction / alpha_beta) * (1.0 + hm))
    return round(bed, 2)


def get_alpha_beta_table() -> dict[str, dict[str, float]]:
    """Retrieve canonical alpha/beta ratios for tumors, acute normal tissues, and late normal tissues."""
    return {
        "tumors": {
            "head_and_neck_scc": 10.0,
            "cervical_scc": 10.0,
            "non_small_cell_lung_cancer": 10.0,
            "small_cell_lung_cancer": 10.0,
            "colorectal_adenocarcinoma": 10.0,
            "pancreatic_adenocarcinoma": 10.0,
            "high_grade_glioma_gbm": 10.0,
            "low_grade_glioma": 4.0,
            "breast_adenocarcinoma": 4.0,
            "prostate_adenocarcinoma": 1.5,
            "melanoma": 2.5,
            "soft_tissue_sarcoma": 4.0,
            "lymphoma": 10.0,
        },
        "normal_tissues_acute": {
            "mucosa_oral_pharyngeal": 10.0,
            "skin_epidermis": 10.0,
            "gastrointestinal_mucosa": 10.0,
            "bone_marrow": 10.0,
        },
        "normal_tissues_late": {
            "spinal_cord_myelopathy": 2.0,
            "brain_necrosis": 2.5,
            "brainstem_necrosis": 2.5,
            "optic_nerve_chiasm": 2.0,
            "lung_fibrosis_pneumonitis": 3.0,
            "heart_myocardium_coronary": 2.5,
            "kidney_nephropathy": 2.5,
            "rectum_late_telangiectasia_stricture": 3.0,
            "bladder_late_contracture": 3.5,
            "liver_radiation_induced_liver_disease": 2.5,
            "bone_necrosis": 2.5,
        },
    }


def get_canonical_alpha_beta(target_name: str) -> float | None:
    """Lookup alpha/beta ratio for a specified tumor type or organ at risk."""
    clean_target = target_name.strip().lower().replace(" ", "_").replace("-", "_")
    table = get_alpha_beta_table()
    for category in ("tumors", "normal_tissues_late", "normal_tissues_acute"):
        for k, val in table[category].items():
            if clean_target in k or k in clean_target:
                return val
    return None


def get_the_rs_of_radiobiology() -> list[dict[str, str]]:
    """Retrieve the classical 4 R's and modern 5th/6th R's of radiobiology."""
    kogel = get_textbook_by_source_id("TEXTBOOK-KOGEL-2019")
    if kogel and "radiobiology_principles" in kogel:
        return kogel["radiobiology_principles"].get("the_classical_and_modern_rs_of_radiobiology", [])
    return [
        {"r": "Repair", "mechanism": "Sublethal damage repair in normal tissues between fractions."},
        {"r": "Reassortment", "mechanism": "Redistribution of surviving cells into radiosensitive cell cycle phases."},
        {"r": "Repopulation", "mechanism": "Accelerated tumor clonogen proliferation requiring minimal treatment prolongation."},
        {"r": "Reoxygenation", "mechanism": "Hypoxic tumor cells reoxygenate between fractions as aerated cells die."},
        {"r": "Radiosensitivity", "mechanism": "Intrinsic cellular susceptibility to ionizing radiation."},
        {"r": "Reactivation of Immunity", "mechanism": "Radiation-induced immunogenic cell death and cGAS-STING priming."},
    ]


# ---------------------------------------------------------------------------
# CANONICAL TARGET PRESCRIPTIONS BY SITE
# ---------------------------------------------------------------------------

_CANONICAL_PRESCRIPTIONS_STORE: list[CanonicalPrescription] = [
    # Head & Neck
    CanonicalPrescription(
        site="Head & Neck",
        clinical_scenario="Definitive Locally Advanced Head and Neck SCC",
        prescribed_dose="70 Gy in 35 fractions (high-risk), 59.5-63 Gy (intermediate), 54-56 Gy (elective)",
        total_dose_gy=70.0,
        fractions=35,
        dose_per_fraction_gy=2.0,
        setting="definitive",
        technique="Simultaneous Integrated Boost (SIB) IMRT / VMAT",
        target_volumes="PTV_high = primary tumor + gross nodes + 3-5 mm; PTV_intermediate = high-risk subclinical; PTV_low = bilateral elective nodal levels",
        concurrent_agent="High-dose cisplatin 100 mg/m2 IV q3w x 3 cycles or weekly 40 mg/m2",
        bed_alpha_beta_10=84.0,
        bed_alpha_beta_3=116.67,
        eqd2_alpha_beta_10=70.0,
        eqd2_alpha_beta_3=70.0,
        citation="Perez & Brady 8th Ed, Chapter 46; Essentials 2026, Chapter 11/14",
        notes="Gold standard definitive organ preservation chemoradiation.",
    ),
    CanonicalPrescription(
        site="Head & Neck",
        clinical_scenario="Early Glottic Laryngeal Cancer (T1N0)",
        prescribed_dose="63 Gy in 28 fractions (2.25 Gy/fx) or 66 Gy in 33 fractions (2.0 Gy/fx)",
        total_dose_gy=63.0,
        fractions=28,
        dose_per_fraction_gy=2.25,
        setting="definitive",
        technique="Carotid-sparing 3D-CRT or IMRT",
        target_volumes="CTV = true vocal cords + anterior commissure; PTV = CTV + 3-5 mm; No elective nodal irradiation",
        concurrent_agent="None",
        bed_alpha_beta_10=77.18,
        bed_alpha_beta_3=110.25,
        eqd2_alpha_beta_10=64.31,
        eqd2_alpha_beta_3=66.15,
        citation="Yamazaki et al.; Perez & Brady 8th Ed, Chapter 45",
        notes="Moderate hypofractionation improves local control without excess late toxicity.",
    ),
    CanonicalPrescription(
        site="Head & Neck",
        clinical_scenario="Postoperative High-Risk Head and Neck SCC (ECE+ or R1 Margin)",
        prescribed_dose="66 Gy in 33 fractions (high-risk bed) + 54-56 Gy (elective neck)",
        total_dose_gy=66.0,
        fractions=33,
        dose_per_fraction_gy=2.0,
        setting="adjuvant",
        technique="IMRT / VMAT with daily IGRT",
        target_volumes="High-risk surgical bed + nodal basin with extracapsular extension",
        concurrent_agent="Cisplatin 100 mg/m2 IV q3w x 3 cycles (EORTC 22931 / RTOG 9501)",
        bed_alpha_beta_10=79.2,
        bed_alpha_beta_3=110.0,
        eqd2_alpha_beta_10=66.0,
        eqd2_alpha_beta_3=66.0,
        citation="RTOG 9501 / EORTC 22931 / Perez & Brady 8th Ed, Chapter 46",
        notes="Mandatory concurrent cisplatin for positive margins or extranodal extension.",
    ),
    # Lung
    CanonicalPrescription(
        site="Lung",
        clinical_scenario="Early-Stage Peripheral NSCLC (T1-T2aN0, Inoperable)",
        prescribed_dose="54 Gy in 3 fractions (18 Gy/fx) or 50 Gy in 5 fractions (10 Gy/fx)",
        total_dose_gy=54.0,
        fractions=3,
        dose_per_fraction_gy=18.0,
        setting="definitive",
        technique="4D-CT motion-managed SBRT / SABR",
        target_volumes="ITV encompassing all respiratory phases; PTV = ITV + 5 mm",
        concurrent_agent="None",
        bed_alpha_beta_10=151.2,
        bed_alpha_beta_3=378.0,
        eqd2_alpha_beta_10=126.0,
        eqd2_alpha_beta_3=226.8,
        citation="RTOG 0236; Perez & Brady 8th Ed, Chapter 57; Essentials 2026, Chapter 28",
        notes="BED10 > 100 Gy is mandatory for optimal local control (>90%).",
    ),
    CanonicalPrescription(
        site="Lung",
        clinical_scenario="Locally Advanced Stage III Inoperable NSCLC",
        prescribed_dose="60-66 Gy in 30-33 fractions (2.0 Gy/fx)",
        total_dose_gy=60.0,
        fractions=30,
        dose_per_fraction_gy=2.0,
        setting="definitive",
        technique="IMRT / VMAT with daily CBCT",
        target_volumes="CTV = primary tumor + involved nodal stations; PTV = CTV + 5-7 mm",
        concurrent_agent="Platinum doublet (cisplatin/etoposide or weekly carboplatin/paclitaxel) + consolidation durvalumab (PACIFIC)",
        bed_alpha_beta_10=72.0,
        bed_alpha_beta_3=100.0,
        eqd2_alpha_beta_10=60.0,
        eqd2_alpha_beta_3=60.0,
        citation="RTOG 0617 / PACIFIC Trial; Perez & Brady 8th Ed, Chapter 57",
        notes="RTOG 0617 proved 60 Gy is superior in overall survival compared to 74 Gy due to heart/esophagus toxicity.",
    ),
    # Breast
    CanonicalPrescription(
        site="Breast",
        clinical_scenario="Adjuvant Whole Breast Irradiation post-BCT (Standard Hypofractionation)",
        prescribed_dose="40.05 Gy in 15 fractions (2.67 Gy/fx) over 3 weeks",
        total_dose_gy=40.05,
        fractions=15,
        dose_per_fraction_gy=2.67,
        setting="adjuvant",
        technique="3D-CRT or Field-in-Field IMRT with DIBH for left breast",
        target_volumes="CTV = whole breast tissue; PTV = CTV + 5 mm; +/- tumor bed boost 10-12 Gy for high risk",
        concurrent_agent="Sequential endocrine therapy or chemotherapy (concurrent avoided)",
        bed_alpha_beta_10=50.74,
        bed_alpha_beta_3=75.69,
        eqd2_alpha_beta_10=42.28,
        eqd2_alpha_beta_3=45.42,
        citation="UK START-B / Canadian Trial / ASTRO Whole Breast Guideline; Essentials 2026, Chapter 24",
        notes="Preferred standard of care across all ages and stages post-lumpectomy.",
    ),
    CanonicalPrescription(
        site="Breast",
        clinical_scenario="Adjuvant Whole Breast Ultra-Hypofractionation (FAST-Forward)",
        prescribed_dose="26 Gy in 5 fractions over 1 week (5.2 Gy/fx daily)",
        total_dose_gy=26.0,
        fractions=5,
        dose_per_fraction_gy=5.2,
        setting="adjuvant",
        technique="3D-CRT or Tangential IMRT / VMAT",
        target_volumes="CTV = whole breast tissue; PTV = CTV + 5 mm",
        concurrent_agent="Sequential therapy",
        bed_alpha_beta_10=39.52,
        bed_alpha_beta_3=71.07,
        eqd2_alpha_beta_10=32.93,
        eqd2_alpha_beta_3=42.64,
        citation="FAST-Forward Trial (Lancet 2020); Perez & Brady 8th Ed, Chapter 62",
        notes="Non-inferior local control and normal tissue cosmesis over 10-year follow-up.",
    ),
    CanonicalPrescription(
        site="Breast",
        clinical_scenario="Post-Mastectomy Radiation Therapy (PMRT) with Regional Nodes",
        prescribed_dose="50 Gy in 25 fractions (2.0 Gy/fx) or 40.05 Gy in 15 fractions (2.67 Gy/fx)",
        total_dose_gy=50.0,
        fractions=25,
        dose_per_fraction_gy=2.0,
        setting="adjuvant",
        technique="IMRT / VMAT with bolus +/- DIBH",
        target_volumes="Chest wall + supraclavicular fossa + internal mammary lymph nodes",
        concurrent_agent="None concurrent",
        bed_alpha_beta_10=60.0,
        bed_alpha_beta_3=83.33,
        eqd2_alpha_beta_10=50.0,
        eqd2_alpha_beta_3=50.0,
        citation="EBCTCG Meta-analysis / MA.20 / EORTC 22922; Perez & Brady 8th Ed, Chapter 63",
        notes="Indicated for >=4 positive nodes, T3-T4, or 1-3 nodes with high-risk features.",
    ),
    # Prostate
    CanonicalPrescription(
        site="Prostate",
        clinical_scenario="Definitive Moderate Hypofractionation for Intact Prostate",
        prescribed_dose="60 Gy in 20 fractions (3.0 Gy/fx) over 4 weeks",
        total_dose_gy=60.0,
        fractions=20,
        dose_per_fraction_gy=3.0,
        setting="definitive",
        technique="Image-Guided IMRT / VMAT with daily fiducial/CBCT tracking",
        target_volumes="CTV = prostate +/- proximal seminal vesicles; PTV = CTV + 4-7 mm",
        concurrent_agent="Short-term (4-6 mo) ADT for unfavorable intermediate; long-term (24-36 mo) for high risk",
        bed_alpha_beta_10=78.0,
        bed_alpha_beta_3=120.0,
        eqd2_alpha_beta_10=65.0,
        eqd2_alpha_beta_3=72.0,
        citation="CHHiP / PROFIT / RTOG 0415; Perez & Brady 8th Ed, Chapter 72/73",
        notes="Prostate alpha/beta ~ 1.5 Gy gives high biological sensitivity to fraction size.",
    ),
    CanonicalPrescription(
        site="Prostate",
        clinical_scenario="Ultra-Hypofractionated Prostate SBRT",
        prescribed_dose="36.25 Gy in 5 fractions (7.25 Gy/fx) every other day",
        total_dose_gy=36.25,
        fractions=5,
        dose_per_fraction_gy=7.25,
        setting="definitive",
        technique="SBRT / CyberKnife / VMAT with real-time tracking or rectal spacer",
        target_volumes="CTV = prostate +/- seminal vesicles; PTV = CTV + 3-5 mm",
        concurrent_agent="Optional short-term ADT for unfavorable intermediate",
        bed_alpha_beta_10=62.53,
        bed_alpha_beta_3=123.98,
        eqd2_alpha_beta_10=52.11,
        eqd2_alpha_beta_3=74.39,
        citation="PACE-B / HYPO-RT-PC; Essentials 2026, Chapter 40",
        notes="Equivalent biochemical control with acceptable rectal and bladder profiles.",
    ),
    CanonicalPrescription(
        site="Prostate",
        clinical_scenario="Post-Prostatectomy Salvage Radiation Therapy",
        prescribed_dose="64.8-66 Gy in 32-36 fractions (1.8-2.0 Gy/fx) to prostatic fossa",
        total_dose_gy=66.0,
        fractions=33,
        dose_per_fraction_gy=2.0,
        setting="adjuvant",
        technique="IMRT / VMAT with bladder/rectal filling protocol",
        target_volumes="CTV = prostatic bed; PTV = CTV + 5-7 mm",
        concurrent_agent="+/- 6 months short-term ADT for PSA > 0.5 or Gleason 8-10",
        bed_alpha_beta_10=79.2,
        bed_alpha_beta_3=110.0,
        eqd2_alpha_beta_10=66.0,
        eqd2_alpha_beta_3=66.0,
        citation="RADICALS-RT / RAVES / GETUG-AFU 17 (ARTISTIC meta-analysis); Essentials 2026, Chapter 42",
        notes="Early salvage at PSA 0.1-0.2 ng/mL is equivalent to routine adjuvant while sparing overtreatment.",
    ),
    # GI
    CanonicalPrescription(
        site="GI",
        clinical_scenario="Neoadjuvant Trimodality Therapy for Esophageal Cancer (CROSS)",
        prescribed_dose="41.4 Gy in 23 fractions (1.8 Gy/fx) over 4.5 weeks",
        total_dose_gy=41.4,
        fractions=23,
        dose_per_fraction_gy=1.8,
        setting="adjuvant",
        technique="IMRT / 3D-CRT with 4D-CT motion management",
        target_volumes="GTV = primary esophageal tumor + involved nodes; CTV = GTV + 3-4 cm craniocaudal, 1 cm radial; PTV = CTV + 5-7 mm",
        concurrent_agent="Weekly carboplatin (AUC 2) + paclitaxel (50 mg/m2) (CROSS protocol)",
        bed_alpha_beta_10=48.85,
        bed_alpha_beta_3=66.24,
        eqd2_alpha_beta_10=40.71,
        eqd2_alpha_beta_3=39.74,
        citation="CROSS Trial (van Hagen et al. NEJM 2012); Perez & Brady 8th Ed, Chapter 65",
        notes="Significantly improves pathological complete response and overall survival.",
    ),
    CanonicalPrescription(
        site="GI",
        clinical_scenario="Total Neoadjuvant Therapy (TNT) for Locally Advanced Rectal Cancer",
        prescribed_dose="Short-Course RT: 25 Gy in 5 fractions (5.0 Gy/fx) followed by consolidation chemotherapy",
        total_dose_gy=25.0,
        fractions=5,
        dose_per_fraction_gy=5.0,
        setting="definitive",
        technique="VMAT / IMRT with full bladder and daily CBCT",
        target_volumes="Mesorectum + presacral space + internal iliac lymph nodes; PTV = CTV + 5-7 mm",
        concurrent_agent="Consolidation systemic CAPOX x 6 cycles or FOLFOX x 9 cycles (RAPIDO trial)",
        bed_alpha_beta_10=37.5,
        bed_alpha_beta_3=66.67,
        eqd2_alpha_beta_10=31.25,
        eqd2_alpha_beta_3=40.0,
        citation="RAPIDO / STELLAR Trials; Essentials 2026, Chapter 37",
        notes="Doubles complete response rate, facilitating Watch-and-Wait organ preservation.",
    ),
    CanonicalPrescription(
        site="GI",
        clinical_scenario="Definitive Chemoradiation for Anal Canal SCC (Nigro Regimen)",
        prescribed_dose="50.4-54 Gy in 28-30 fractions (primary) + 45 Gy in 25 fractions (elective nodes)",
        total_dose_gy=54.0,
        fractions=30,
        dose_per_fraction_gy=1.8,
        setting="definitive",
        technique="Simultaneous Integrated Boost (SIB) IMRT / VMAT",
        target_volumes="PTV_primary = anal tumor + 1 cm; PTV_nodal = mesorectum, internal/external iliac, and bilateral inguinal nodes",
        concurrent_agent="Mitomycin-C (10-12 mg/m2 IV bolus days 1, 29) + 5-FU (1000 mg/m2/day continuous infusion days 1-4, 29-32) or capecitabine",
        bed_alpha_beta_10=63.72,
        bed_alpha_beta_3=86.4,
        eqd2_alpha_beta_10=53.1,
        eqd2_alpha_beta_3=51.84,
        citation="Nigro Protocol / RTOG 98-11 / ACT II; Perez & Brady 8th Ed, Chapter 69",
        notes="Definitive sphincter-preserving cure with local control ~80-85%.",
    ),
    # GYN
    CanonicalPrescription(
        site="GYN",
        clinical_scenario="Definitive Chemoradiation with IGABT for Locally Advanced Cervical Cancer",
        prescribed_dose="45 Gy in 25 fractions Pelvic EBRT + HDR IGABT to HR-CTV total EQD2 >= 85-90 Gy",
        total_dose_gy=45.0,
        fractions=25,
        dose_per_fraction_gy=1.8,
        setting="definitive",
        technique="Pelvic IMRT/VMAT + MRI-guided tandem & ring/ovoids brachytherapy",
        target_volumes="EBRT CTV = gross disease, cervix, uterus, parametria, upper vagina, internal/external/common iliac and presacral nodes; HR-CTV on MRI at brachytherapy",
        concurrent_agent="Weekly cisplatin 40 mg/m2 IV x 5-6 cycles",
        bed_alpha_beta_10=53.1,
        bed_alpha_beta_3=72.0,
        eqd2_alpha_beta_10=44.25,
        eqd2_alpha_beta_3=43.2,
        citation="EMBRACE I & II / GEC-ESTRO Guidelines; Perez & Brady 8th Ed, Chapter 76",
        notes="Total HR-CTV D90 >= 85 Gy EQD2 required for >90% local control.",
    ),
    CanonicalPrescription(
        site="GYN",
        clinical_scenario="Postoperative Vaginal Cuff Brachytherapy (VCB) for Endometrial Cancer",
        prescribed_dose="HDR 21 Gy in 3 fractions (7.0 Gy/fx at 0.5 cm depth) or 15 Gy in 3 fractions at surface",
        total_dose_gy=21.0,
        fractions=3,
        dose_per_fraction_gy=7.0,
        setting="adjuvant",
        technique="Single-channel vaginal cylinder HDR brachytherapy",
        target_volumes="Upper 3-4 cm of vaginal cuff",
        concurrent_agent="None",
        bed_alpha_beta_10=35.7,
        bed_alpha_beta_3=70.0,
        eqd2_alpha_beta_10=29.75,
        eqd2_alpha_beta_3=42.0,
        citation="PORTEC-1 / PORTEC-2 Trials; Essentials 2026, Chapter 49",
        notes="Provides excellent vaginal control with minimal bowel/bladder toxicity compared to pelvic EBRT.",
    ),
    # CNS
    CanonicalPrescription(
        site="CNS",
        clinical_scenario="Definitive / Adjuvant Glioblastoma, IDH-wildtype (Stupp Protocol)",
        prescribed_dose="60 Gy in 30 fractions (2.0 Gy/fx)",
        total_dose_gy=60.0,
        fractions=30,
        dose_per_fraction_gy=2.0,
        setting="definitive",
        technique="3D-CRT or IMRT with daily rigid immobilization",
        target_volumes="Phase 1: resection cavity/residual T1+Gd + T2/FLAIR edema + 1.5-2.0 cm (to 46 Gy); Phase 2 boost: surgical cavity/residual tumor + 1.0-1.5 cm (to 60 Gy)",
        concurrent_agent="Daily temozolomide 75 mg/m2 during RT, followed by 6 cycles adjuvant maintenance (150-200 mg/m2 days 1-5 q28d) +/- TTF",
        bed_alpha_beta_10=72.0,
        bed_alpha_beta_3=100.0,
        eqd2_alpha_beta_10=60.0,
        eqd2_alpha_beta_3=60.0,
        citation="Stupp et al. NEJM 2005; Perez & Brady 8th Ed, Part B; Essentials 2026, Chapter 1",
        notes="Standard of care for fit patients with newly diagnosed glioblastoma.",
    ),
    CanonicalPrescription(
        site="CNS",
        clinical_scenario="Hypofractionated RT for Elderly or Fragile Glioblastoma",
        prescribed_dose="40 Gy in 15 fractions (2.67 Gy/fx) or 34 Gy in 10 fractions (3.4 Gy/fx)",
        total_dose_gy=40.0,
        fractions=15,
        dose_per_fraction_gy=2.67,
        setting="definitive",
        technique="IMRT / VMAT with reduced margins",
        target_volumes="GTV = cavity + residual contrast enhancement; PTV = GTV + 1.0-1.5 cm",
        concurrent_agent="Concurrent and maintenance temozolomide if MGMT promoter is methylated (Perry et al. NEJM 2017)",
        bed_alpha_beta_10=50.68,
        bed_alpha_beta_3=75.6,
        eqd2_alpha_beta_10=42.23,
        eqd2_alpha_beta_3=45.36,
        citation="Perry et al. NEJM 2017 / Roa et al. JCO 2004; Essentials 2026, Chapter 1",
        notes="Shortens treatment burden while maintaining survival in patients >= 65-70 years or WHO PS >= 2.",
    ),
    CanonicalPrescription(
        site="CNS",
        clinical_scenario="Stereotactic Radiosurgery (SRS) for Intact Brain Metastases",
        prescribed_dose="Single fraction: <=20 mm: 24 Gy; 21-30 mm: 18 Gy; 31-40 mm: 15 Gy",
        total_dose_gy=24.0,
        fractions=1,
        dose_per_fraction_gy=24.0,
        setting="definitive",
        technique="Frameless or framed Linac SRS / Gamma Knife with high-resolution MRI planning",
        target_volumes="GTV = contrast-enhancing lesion; PTV = GTV + 0-1 mm",
        concurrent_agent="None concurrent with radiation",
        bed_alpha_beta_10=81.6,
        bed_alpha_beta_3=216.0,
        eqd2_alpha_beta_10=68.0,
        eqd2_alpha_beta_3=129.6,
        citation="RTOG 90-05 / Shaw et al.; Perez & Brady 8th Ed, Chapter 16; Essentials 2026, Chapter 68",
        notes="Dose prescribed to peripheral isodose line (typically 50% for GK, 80% for Linac).",
    ),
]


def get_all_canonical_prescriptions() -> list[CanonicalPrescription]:
    """Retrieve all canonical radiation therapy dose-fractionation prescriptions."""
    return list(_CANONICAL_PRESCRIPTIONS_STORE)


def get_dose_prescriptions_by_site(
    disease_site: str,
    setting: TreatmentSetting = "all",
) -> list[CanonicalPrescription]:
    """Filter canonical prescriptions by anatomical disease site and treatment setting."""
    clean_site = disease_site.strip().lower()
    clean_setting = setting.strip().lower()

    results: list[CanonicalPrescription] = []
    for rx in _CANONICAL_PRESCRIPTIONS_STORE:
        site_match = False
        rx_site_lower = rx.site.lower()
        if clean_site in rx_site_lower or rx_site_lower in clean_site:
            site_match = True
        elif clean_site in ("head & neck", "head and neck", "hn") and "head & neck" in rx_site_lower:
            site_match = True
        elif clean_site in ("thoracic", "lung") and "lung" in rx_site_lower:
            site_match = True
        elif clean_site in ("colorectal", "gi", "gastrointestinal") and "gi" in rx_site_lower:
            site_match = True
        elif clean_site in ("cervix", "gyn", "gynecologic") and "gyn" in rx_site_lower:
            site_match = True
        elif clean_site in ("brain", "cns", "central nervous system") and "cns" in rx_site_lower:
            site_match = True

        if not site_match:
            continue

        if clean_setting != "all" and rx.setting != clean_setting:
            continue

        results.append(rx)

    return results


def get_target_volume_definitions() -> dict[str, str]:
    """Retrieve canonical ICRU target volume definitions from Gunderson & Tepper."""
    gt = get_textbook_by_source_id("TEXTBOOK-GUNDERSON-TEPPER-5TH")
    if gt and "target_volume_specifications" in gt:
        return gt["target_volume_specifications"]
    return {
        "gtv": "Gross Tumor Volume: Demonstrable extent and location of malignant growth.",
        "ctv": "Clinical Target Volume: Tissue volume containing GTV and/or subclinical microscopic disease.",
        "itv": "Internal Target Volume: CTV plus internal margin for physiologic motion.",
        "ptv": "Planning Target Volume: Geometric expansion accounting for net setup uncertainties.",
        "oar": "Organ At Risk: Normal tissue whose radiation sensitivity influences treatment planning.",
        "prv": "Planning Organ at Risk Volume: Safety margin added around an OAR.",
    }


def get_drug_radiation_interactions() -> dict[str, Any]:
    """Retrieve canonical chemo-radiation synergy mechanisms from Gunderson & Tepper."""
    gt = get_textbook_by_source_id("TEXTBOOK-GUNDERSON-TEPPER-5TH")
    if gt and "drug_radiation_interaction_mechanisms" in gt:
        return gt["drug_radiation_interaction_mechanisms"]
    return {
        "spatial_cooperation": "Chemotherapy treats micrometastases; radiation treats primary disease.",
        "toxicity_independence": "Different toxicities allow full doses without synergism in normal tissues.",
        "radiosensitization": [
            {"agent": "Cisplatin", "mechanism": "Inhibits sublethal DNA damage repair, active in hypoxic cells."},
            {"agent": "5-FU", "mechanism": "Thymidylate synthase inhibition depletes dTMP, producing repair failure."},
            {"agent": "Temozolomide", "mechanism": "DNA methylation triggering futile mismatch repair and apoptosis."},
            {"agent": "Paclitaxel", "mechanism": "Microtubule stabilization arresting cells in radiosensitive G2/M phase."},
        ],
    }
