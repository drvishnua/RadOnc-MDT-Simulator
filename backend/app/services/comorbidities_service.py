"""General Medicine, Comorbidities, and Patient Fitness Evidence Service.

Provides structured access to clinical decision rules, performance status thresholds,
renal/cardiopulmonary risk evaluations, and conditional MDT pathway generation.
Derived from Washington Manual 36e, Harrison's Principles of Internal Medicine 21e,
and Decision Making in Medicine 3e.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Literal

_DEFAULT_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "evidence_catalogues"
    / "general_med_comorbidities.json"
)

FitnessTier = Literal[
    "fit_for_all_treatments",
    "fit_for_curative_multimodal",
    "borderline_vulnerable",
    "unfit_for_aggressive_therapy",
    "severely_compromised",
    "terminal",
    "unknown",
]

RenalEligibility = Literal[
    "eligible_full_dose",
    "borderline_modified_regimen",
    "cisplatin_contraindicated",
    "chemotherapy_contraindicated",
    "unverified",
]


class ComorbidityEvidenceService:
    """Service for querying comorbidity decision rules and evaluating patient fitness."""

    def __init__(self, catalogue_path: pathlib.Path | None = None) -> None:
        self.catalogue_path = catalogue_path or _DEFAULT_CATALOGUE_PATH
        self._catalogue_data: dict[str, Any] = {}
        self._entries: list[dict[str, Any]] = []
        self._entries_by_id: dict[str, dict[str, Any]] = {}
        self._load_catalogue()

    def _load_catalogue(self) -> None:
        if not self.catalogue_path.is_file():
            self._catalogue_data = {}
            self._entries = []
            self._entries_by_id = {}
            return

        try:
            raw = self.catalogue_path.read_text(encoding="utf-8")
            self._catalogue_data = json.loads(raw)
            self._entries = self._catalogue_data.get("entries", [])
            self._entries_by_id = {
                e["source_id"].upper(): e for e in self._entries if "source_id" in e
            }
        except (json.JSONDecodeError, OSError):
            self._catalogue_data = {}
            self._entries = []
            self._entries_by_id = {}

    @property
    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def get_entry(self, source_id: str) -> dict[str, Any] | None:
        """Retrieve an entry by source ID (case-insensitive)."""
        return self._entries_by_id.get(source_id.strip().upper())

    def search_by_topic(self, topic: str) -> list[dict[str, Any]]:
        """Find entries relevant to a clinical topic (e.g. 'renal', 'cardiac', 'ecog')."""
        clean_topic = topic.strip().lower()
        results: list[dict[str, Any]] = []
        for e in self._entries:
            topics = [t.lower() for t in e.get("topics", [])]
            title = e.get("title", "").lower()
            if any(clean_topic in t for t in topics) or clean_topic in title:
                results.append(e)
        return results

    # =========================================================================
    # Clinical Calculators and Rule Engines
    # =========================================================================

    @staticmethod
    def calculate_creatinine_clearance(
        *,
        age: int,
        weight_kg: float,
        serum_creatinine_mg_dl: float,
        is_female: bool,
    ) -> float:
        """Calculate Creatinine Clearance using the Cockcroft-Gault formula (mL/min).

        CrCl = [(140 - Age) * Weight (kg)] / [72 * SCr (mg/dL)] * (0.85 if female)
        """
        if age <= 0 or weight_kg <= 0 or serum_creatinine_mg_dl <= 0:
            raise ValueError("Age, weight, and serum creatinine must be strictly positive.")

        base_crcl = ((140.0 - float(age)) * float(weight_kg)) / (72.0 * float(serum_creatinine_mg_dl))
        if is_female:
            base_crcl *= 0.85
        return round(base_crcl, 1)

    @staticmethod
    def calculate_carboplatin_dose(
        *,
        target_auc: float,
        gfr_ml_min: float,
        cap_gfr: bool = True,
    ) -> float:
        """Calculate Carboplatin dose in milligrams using the Calvert Formula.

        Total Dose (mg) = Target AUC * (GFR + 25)
        Per ASCO/FDA standards, GFR is capped at 125 mL/min to prevent overdosing.
        """
        if target_auc <= 0 or gfr_ml_min <= 0:
            raise ValueError("Target AUC and GFR must be strictly positive.")

        effective_gfr = min(gfr_ml_min, 125.0) if cap_gfr else gfr_ml_min
        dose = float(target_auc) * (effective_gfr + 25.0)
        return round(dose, 1)

    @staticmethod
    def evaluate_performance_status(
        *,
        ecog: int | None = None,
        kps: int | None = None,
    ) -> dict[str, Any]:
        """Evaluate patient fitness tier from ECOG or Karnofsky Performance Status."""
        if ecog is None and kps is not None:
            if kps >= 100:
                ecog = 0
            elif kps >= 80:
                ecog = 1
            elif kps >= 60:
                ecog = 2
            elif kps >= 40:
                ecog = 3
            elif kps >= 10:
                ecog = 4
            else:
                ecog = 5

        if ecog is None:
            return {
                "status": "unrecorded",
                "fitness_tier": "unknown",
                "multimodal_eligible": None,
                "preferred_pathway": "Conditional: Verify baseline performance status.",
                "conditional_statement": (
                    "Assuming baseline ECOG 0-1, patient is eligible for definitive concurrent chemoradiotherapy; "
                    "if formal evaluation confirms ECOG >= 2, omit concurrent high-dose cisplatin in favor of "
                    "definitive radiation alone or weekly carboplatin."
                ),
            }

        if ecog == 0:
            return {
                "ecog": 0,
                "kps_correlate": 100,
                "fitness_tier": "fit_for_all_treatments",
                "multimodal_eligible": True,
                "preferred_pathway": "Standard full-dose definitive concurrent chemoradiotherapy (CCRT), radical surgery, or definitive RT.",
                "cisplatin_schedule": "Cisplatin 100 mg/m2 q3w or 40 mg/m2 weekly concurrent with radiotherapy.",
            }
        elif ecog == 1:
            return {
                "ecog": 1,
                "kps_correlate": 80,
                "fitness_tier": "fit_for_curative_multimodal",
                "multimodal_eligible": True,
                "preferred_pathway": "Full-dose definitive CCRT (e.g. cisplatin 100 mg/m2 q3w or 40 mg/m2 weekly) or surgery.",
                "cisplatin_schedule": "Standard 3-weekly or weekly cisplatin with standard pre/post hydration.",
            }
        elif ecog == 2:
            return {
                "ecog": 2,
                "kps_correlate": 60,
                "fitness_tier": "borderline_vulnerable",
                "multimodal_eligible": False,  # Not eligible for full-dose tri-weekly cisplatin
                "preferred_pathway": "Modified CCRT or RT alone. Unfit for high-dose 3-weekly cisplatin.",
                "recommended_alternatives": [
                    "Definitive radiation therapy alone (66-70 Gy)",
                    "Weekly low-dose cisplatin (30-40 mg/m2) with close renal/toxic monitoring",
                    "Carboplatin AUC 4-5 concurrent with radiation",
                    "Cetuximab concurrent with radiation (for Head & Neck SCC)",
                ],
                "conditional_statement": (
                    "Assess whether ECOG 2 is driven by local tumor burden (potentially reversible) or comorbid decline. "
                    "If comorbid, avoid high-dose 3-weekly cisplatin; prioritize definitive radiotherapy alone or carboplatin."
                ),
            }
        elif ecog == 3:
            return {
                "ecog": 3,
                "kps_correlate": 40,
                "fitness_tier": "unfit_for_aggressive_therapy",
                "multimodal_eligible": False,
                "preferred_pathway": "Palliative hypofractionated radiotherapy or best supportive care; high-dose CCRT contraindicated.",
            }
        elif ecog == 4:
            return {
                "ecog": 4,
                "kps_correlate": 20,
                "fitness_tier": "severely_compromised",
                "multimodal_eligible": False,
                "preferred_pathway": "Best supportive care / hospice; short-course emergency palliative RT only for acute bleeding or spinal compression.",
            }
        else:
            return {
                "ecog": 5,
                "kps_correlate": 0,
                "fitness_tier": "terminal",
                "multimodal_eligible": False,
                "preferred_pathway": "Patient deceased.",
            }

    @staticmethod
    def evaluate_renal_fitness(
        *,
        crcl_ml_min: float | None = None,
        serum_creatinine_mg_dl: float | None = None,
    ) -> dict[str, Any]:
        """Evaluate platinum chemotherapy eligibility based on renal function cutoffs."""
        if crcl_ml_min is None:
            return {
                "status": "unverified",
                "eligibility": "unverified",
                "cisplatin_eligible": None,
                "carboplatin_eligible": None,
                "conditional_statement": (
                    "Renal function is unrecorded. Serum creatinine and calculated CrCl (Cockcroft-Gault) "
                    "are mandatory before platinum administration. If CrCl >= 60 mL/min, proceed with cisplatin; "
                    "if CrCl is 50-59 mL/min, consider weekly cisplatin or carboplatin AUC 4-5; "
                    "if CrCl < 50 mL/min, cisplatin is contraindicated, deliver radiotherapy alone or carboplatin."
                ),
            }

        if crcl_ml_min >= 60.0:
            return {
                "crcl_ml_min": crcl_ml_min,
                "status": "normal_to_mild",
                "eligibility": "eligible_full_dose",
                "cisplatin_eligible": True,
                "carboplatin_eligible": True,
                "preferred_regimen": "Standard cisplatin 100 mg/m2 q3w or 40 mg/m2 weekly with 2-3 L IV hydration.",
                "cautions": "Ensure euvolemia and avoid nephrotoxic co-medications.",
            }
        elif 50.0 <= crcl_ml_min < 60.0:
            return {
                "crcl_ml_min": crcl_ml_min,
                "status": "borderline_renal_reserve",
                "eligibility": "borderline_modified_regimen",
                "cisplatin_eligible": False,  # Full-dose 3-weekly is not recommended
                "carboplatin_eligible": True,
                "preferred_regimen": "Weekly split-dose cisplatin (30-40 mg/m2) OR Carboplatin AUC 4-5 (Calvert formula) OR RT alone.",
                "conditional_statement": (
                    "Patient has borderline creatinine clearance (50-59 mL/min). Tri-weekly high-dose cisplatin carries "
                    "heightened AKI risk. Recommend weekly cisplatin with diuresis, carboplatin AUC 4-5, or RT alone."
                ),
            }
        elif 30.0 <= crcl_ml_min < 50.0:
            return {
                "crcl_ml_min": crcl_ml_min,
                "status": "moderate_renal_impairment",
                "eligibility": "cisplatin_contraindicated",
                "cisplatin_eligible": False,
                "carboplatin_eligible": True,
                "preferred_regimen": "Carboplatin (dosed via Calvert formula) OR Definitive Radiation Therapy alone.",
                "warning": "Cisplatin is strictly contraindicated due to irreversible cumulative nephrotoxicity.",
            }
        else:  # < 30.0
            return {
                "crcl_ml_min": crcl_ml_min,
                "status": "severe_renal_impairment_esrd",
                "eligibility": "chemotherapy_contraindicated",
                "cisplatin_eligible": False,
                "carboplatin_eligible": False,
                "preferred_regimen": "Definitive Radiation Therapy alone without concurrent cytotoxic chemotherapy.",
                "warning": "Severe CKD / ESRD. Avoid cytotoxic chemotherapy; deliver radiation alone with nephrology co-management.",
            }

    @staticmethod
    def evaluate_cardiopulmonary_risk(
        *,
        has_cad: bool = False,
        has_chf: bool = False,
        lvef_pct: float | None = None,
        fev1_pct: float | None = None,
        dlco_pct: float | None = None,
        has_ild: bool = False,
        is_active_smoker: bool = False,
    ) -> dict[str, Any]:
        """Evaluate cardiovascular and pulmonary tolerance for multimodal oncology therapy."""
        warnings: list[str] = []
        pathways: list[str] = []

        # Cardiac assessment
        fluid_tolerance = "normal"
        if has_chf or (lvef_pct is not None and lvef_pct < 45.0):
            fluid_tolerance = "severely_compromised"
            warnings.append(
                "Congestive heart failure / reduced LVEF (<45%): High-volume IV hydration (2-3 L) for high-dose "
                "cisplatin carries severe risk of acute pulmonary edema. Weekly low-dose regimen or carboplatin preferred."
            )
        elif has_cad:
            fluid_tolerance = "cautious"
            warnings.append("Known coronary artery disease: Maintain strict fluid balance and avoid acute anemia.")

        # Pulmonary assessment
        pulmonary_fitness = "normal"
        if has_ild:
            pulmonary_fitness = "contraindicated_for_rt"
            warnings.append(
                "Pre-existing Interstitial Lung Disease / Idiopathic Pulmonary Fibrosis: Major relative-to-absolute "
                "contraindication to definitive thoracic radiotherapy due to high risk of fatal acute exacerbation (>30-50% mortality)."
            )
        elif fev1_pct is not None or dlco_pct is not None:
            min_val = min(v for v in [fev1_pct, dlco_pct] if v is not None)
            if min_val < 35.0:
                pulmonary_fitness = "very_severe_impairment"
                warnings.append(
                    "Severely compromised pulmonary function (FEV1 or DLCO < 35%): Large-volume thoracic chemoradiation "
                    "carries prohibitive risk of respiratory failure. SBRT or palliative RT strongly preferred."
                )
            elif min_val < 50.0:
                pulmonary_fitness = "severe_impairment"
                warnings.append(
                    "Severe airflow or diffusion limitation (35-49%): Medically inoperable for lobectomy. SBRT preferred for "
                    "early-stage NSCLC; strict lung dosimetric constraints (V20 < 25-30%) for locally advanced disease."
                )
            elif min_val < 80.0:
                pulmonary_fitness = "moderate_impairment"

        if is_active_smoker:
            warnings.append(
                "Active smoking during radiotherapy reduces locoregional control by 20-30% and exacerbates acute toxicities; "
                "mandatory smoking cessation support required."
            )

        return {
            "fluid_tolerance": fluid_tolerance,
            "pulmonary_fitness": pulmonary_fitness,
            "warnings": warnings,
            "cardiac_dose_constraints": "Heart Mean Dose < 26 Gy, V30 < 45%, V25 < 10%",
            "lung_dose_constraints": "Total Lung V20 <= 30-35%, Mean Lung Dose <= 20 Gy (preferably <= 13-15 Gy)",
        }

    @staticmethod
    def evaluate_hematologic_fitness(
        *,
        anc_per_ul: float | None = None,
        platelets_per_ul: float | None = None,
        hemoglobin_g_dl: float | None = None,
    ) -> dict[str, Any]:
        """Evaluate hematologic baselines against chemotherapy and radiotherapy thresholds."""
        findings: list[str] = []
        chemo_hold = False
        rt_oxygenation_alert = False

        if anc_per_ul is not None:
            if anc_per_ul < 500:
                chemo_hold = True
                findings.append(f"Severe neutropenia (ANC {anc_per_ul:.0f}/uL): Chemotherapy must be held; high infection risk.")
            elif anc_per_ul < 1000:
                chemo_hold = True
                findings.append(f"Moderate neutropenia (ANC {anc_per_ul:.0f}/uL): Chemotherapy must be held until ANC >= 1,500/uL.")
            elif anc_per_ul < 1500:
                findings.append(f"Mild neutropenia (ANC {anc_per_ul:.0f}/uL): Chemotherapy delay or 20% dose reduction indicated.")

        if platelets_per_ul is not None:
            if platelets_per_ul < 50000:
                chemo_hold = True
                findings.append(f"Severe thrombocytopenia (Platelets {platelets_per_ul:.0f}/uL): Chemotherapy held; invasive procedures contraindicated.")
            elif platelets_per_ul < 100000:
                chemo_hold = True
                findings.append(f"Thrombocytopenia (Platelets {platelets_per_ul:.0f}/uL): Chemotherapy held until count >= 100,000/uL.")

        if hemoglobin_g_dl is not None:
            if hemoglobin_g_dl < 10.0:
                rt_oxygenation_alert = True
                findings.append(
                    f"Hemoglobin {hemoglobin_g_dl:.1f} g/dL is below the radioresponsiveness target (>= 10.0 g/dL). "
                    "Intratumoral hypoxia impairs free radical DNA damage; correct anemia to maintain local tumor control."
                )

        return {
            "chemo_can_proceed": not chemo_hold,
            "rt_oxygenation_adequate": not rt_oxygenation_alert,
            "findings": findings,
            "fever_rule": (
                "Febrile Neutropenia emergency: Single temp >= 38.3°C or >= 38.0°C for 1h with ANC < 500/uL. "
                "Initiate empiric IV antipseudomonal beta-lactam monotherapy (cefepime, pip-tazo, meropenem) within 60 minutes."
            ),
        }

    def format_comorbidity_prompt_context(self, disease_site: str | None = None) -> str:
        """Format structured comorbidity and patient fitness rules for prompt injection into MDT agents."""
        lines = [
            "### Clinical Fitness & Comorbidity Decision Rules (Evidence Grounding):",
            "- **Performance Status (ECOG / KPS)** (Source: WASHMAN-ECOG-KPS-2020):",
            "  * ECOG 0-1 (KPS >= 80): Fit for standard high-dose concurrent chemoradiotherapy (cisplatin 100 mg/m2 q3w or 40 mg/m2 weekly) and radical surgery.",
            "  * ECOG 2 (KPS 60-70): Fragile. High-dose 3-weekly cisplatin not recommended. Conditional: weekly low-dose cisplatin, carboplatin AUC 4-5, cetuximab, or definitive RT alone.",
            "  * ECOG >= 3: High-dose CCRT contraindicated; consider palliative hypofractionated RT or best supportive care.",
            "  * **Crucial Rule**: If ECOG/KPS is NOT reported in case facts, DO NOT assume ECOG 0. State conditional recommendation based on verified formal staging.",
            "- **Renal Reserve & Platinum Chemotherapy** (Source: WASHMAN-CISPLATIN-RENAL-2020):",
            "  * CrCl >= 60 mL/min: Eligible for full-dose cisplatin.",
            "  * CrCl 50-59 mL/min: Borderline. High-dose cisplatin carries high AKI risk; consider weekly cisplatin or Carboplatin AUC 4-5.",
            "  * CrCl < 50 mL/min: Cisplatin CONTRAINDICATED. Switch to Carboplatin (Calvert formula) or Definitive RT alone.",
            "  * CrCl < 30 mL/min: Avoid cytotoxic chemotherapy; definitive RT alone.",
            "- **Hematology & Radiation Oxygenation** (Source: IDSA-ASCO-FEBRILE-NEUTROPENIA-2021):",
            "  * Chemotherapy initiation requires ANC >= 1,500/uL and Platelets >= 100,000/uL.",
            "  * Target Hemoglobin >= 10.0 g/dL throughout definitive radiotherapy to prevent tumor hypoxia and radioresistance.",
            "- **Cardiopulmonary & Connective Tissue Flags** (Sources: ACC-AHA-LEE-RCRI-2014, ASTRO-COLLAGEN-VASCULAR-RT-2021):",
            "  * Pre-existing heart failure (LVEF < 40%): vigorous cisplatin hydration (2-3 L) can cause pulmonary edema; use weekly regimen or carboplatin.",
            "  * Systemic sclerosis (scleroderma): major relative-to-absolute contraindication for radiotherapy due to severe irreversible fibrosis.",
        ]

        if disease_site and disease_site.lower() in ["lung", "thoracic"]:
            lines.extend([
                "- **Thoracic Pulmonary Function (FEV1 & DLCO)** (Source: WASHMAN-PULMONARY-EVAL-2020):",
                "  * Severe COPD / FEV1 < 40%: Lobectomy contraindicated; SBRT preferred for early-stage NSCLC.",
                "  * Interstitial lung disease (ILD/IPF): Major contraindication to thoracic RT due to fatal radiation pneumonitis risk.",
                "  * Normal lung constraints: Bilateral lung V20 <= 30-35%, Mean Lung Dose <= 20 Gy.",
            ])
        elif disease_site and disease_site.lower() in ["head & neck", "head and neck", "h&n"]:
            lines.extend([
                "- **Head & Neck Nutritional & Airway Support** (Source: WASHMAN-NUTRITION-DYSPHAGIA-2020):",
                "  * Proactive PEG/RIG tube recommended prior to definitive 70 Gy CCRT if baseline severe dysphagia or weight loss > 5-10%.",
            ])

        return "\n".join(lines)


# Singleton instance for convenient application-wide access
default_comorbidity_service = ComorbidityEvidenceService()
