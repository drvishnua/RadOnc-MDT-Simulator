"""Verify 100 new distinct clinical cases across STG-00 and the 49-role Round 1 MDT pipeline."""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from dataclasses import dataclass
from unittest.mock import patch

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services import ollama
from app.services.case_integrity import audit_unverified_case_claims, build_case_prompt_context
from app.services.pre_mdt_staging_agent import run_pre_mdt_staging_agent


@dataclass
class NewCaseSpec:
    label: str
    case: SyntheticCase
    expected_mode: str
    expected_t: str | None
    expected_n: str | None
    expected_m: str | None


def build_new_100_cases() -> list[NewCaseSpec]:
    specs: list[NewCaseSpec] = []

    # Group 1: 20 new Oropharynx cases (distinct sizes/lateralities/comorbidities)
    oro_params = [
        ("1.1 cm", "p16-negative", "No cervical lymphadenopathy; chest CT negative.", "T1", "N0", "M0", None, None, "provisional_derived"),
        ("1.7 cm", "p16-negative", "Chest x-ray normal.", "T1", None, "M0", None, None, "provisional_derived"),
        ("2.1 cm", "p16-negative", "CECT neck shows 1.3 cm left level II lymph node; chest CT negative.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("3.6 cm", "p16-negative", "CECT neck shows 4.8 cm left level II lymph node; PET/CT negative for distant metastasis.", "T2", "N2a", "M0", None, None, "provisional_derived"),
        ("2.9 cm", "p16-negative", "CECT neck shows contralateral 2.1 cm right level III node; chest CT negative.", "T2", "N2c", "M0", None, None, "provisional_derived"),
        ("5.1 cm", "p16-negative", "MRI shows 2.9 cm left level II lymph node with ENE; chest CT negative.", "T3", "N3", "M0", None, None, "provisional_derived"),
        ("2.3 cm", "p16-positive", "CECT neck shows 1.9 cm left level II lymph node; PET/CT negative for distant metastasis.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("3.5 cm", "p16-positive", "CECT neck shows bilateral 2.7 cm level II lymph nodes; chest CT negative.", "T2", "N2", "M0", None, None, "provisional_derived"),
        ("4.7 cm", "p16-positive", "CECT neck shows 6.8 cm left level II lymph node; PET/CT negative.", "T3", "N3", "M0", None, None, "provisional_derived"),
        ("2.8 cm", "p16-negative", "MRI shows lateral pterygoid muscle invasion; no cervical nodes; chest CT negative.", "T4b", "N0", "M0", None, None, "provisional_derived"),
        ("3.9 cm", "p16-negative", "MRI shows medial pterygoid invasion and 1.6 cm ipsilateral node; chest CT negative.", "T4a", "N1", "M0", None, None, "provisional_derived"),
        ("1.5 cm", "p16-negative", "CECT neck shows 1.8 cm left level II node; chest CT negative.", "T1", "N1", "M0", "T1", "N0", "discrepancy_detected"),
        ("2.6 cm", "p16-negative", "CECT neck shows no enlarged cervical nodes; chest CT negative.", "T2", "N0", "M0", "T2", "N0", "verified_concordant"),
        ("3.0 cm", "p16-positive", "CECT neck shows 2.2 cm ipsilateral level II node; chest CT negative.", "T2", "N1", "M0", "T2", "N1", "verified_concordant"),
        ("4.2 cm", "p16-negative", "MRI shows no cervical lymphadenopathy; chest CT negative.", "T3", "N0", "M0", "T2", "N0", "discrepancy_detected"),
        ("1.3 cm", "p16-negative", None, "T1", None, None, None, None, "provisional_derived"),
        ("3.1 cm", "p16-negative", "MRI shows 6.2 cm left cervical node; PET/CT shows lung metastasis.", "T2", "N3", "M1", None, None, "provisional_derived"),
        ("2.4 cm", "p16-positive", "No contralateral nodes; 1.7 cm ipsilateral level II node; chest CT negative.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("1.8 cm", "p16-negative", "Extension to lingual surface of epiglottis; no cervical nodes; chest CT negative.", "T3", "N0", "M0", None, None, "provisional_derived"),
        ("2.7 cm", "p16-negative", "CECT neck shows bilateral 1.9 cm level II nodes; chest CT negative.", "T2", "N2c", "M0", "T2", "N1", "discrepancy_detected"),
    ]
    for i, (sz, hpv, img, et, en, em, pt, pn, emode) in enumerate(oro_params, start=101):
        site = "Left tonsil - oropharynx" if i % 2 else "Soft palate - oropharynx"
        specs.append(
            NewCaseSpec(
                label=f"NEW-ORO-{i}",
                case=SyntheticCase(
                    scenario_title=f"New Oropharynx Case {i}",
                    case_summary=f"{sz} {hpv} squamous cell carcinoma of {site.lower()}.",
                    age_years=42 + (i % 30),
                    sex_at_birth="Male" if i % 2 else "Female",
                    primary_site=site,
                    histology="Squamous cell carcinoma",
                    clinical_t_stage=pt,
                    clinical_n_stage=pn,
                    clinical_m_stage="M0" if pt and em == "M0" else None,
                    imaging_summary=img,
                    relevant_comorbidities=["Hypertension"] if i % 3 == 0 else [],
                ),
                expected_mode=emode,
                expected_t=et,
                expected_n=en,
                expected_m=em,
            )
        )

    # Group 2: 20 new Lung NSCLC cases
    lung_params = [
        ("0.7 cm", "T1a", "PET/CT shows no FDG uptake in mediastinal or hilar nodes, no distant metastasis.", "N0", "M0"),
        ("1.4 cm", "T1b", "PET/CT shows no FDG uptake in hilar or mediastinal nodes, no distant metastasis.", "N0", "M0"),
        ("2.2 cm", "T1c", "PET/CT shows ipsilateral hilar node; no distant metastasis.", "N1", "M0"),
        ("3.7 cm", "T2a", "CT chest shows ipsilateral mediastinal lymph node; PET/CT negative for distant metastasis.", "N2", "M0"),
        ("4.8 cm", "T2b", "PET/CT shows scalene lymph node; no distant metastasis.", "N3", "M0"),
        ("5.9 cm", "T3", "CT chest shows no enlarged nodes; chest CT negative.", "N0", "M0"),
        ("7.8 cm", "T4", "CT chest shows subcarinal node; PET/CT shows brain metastasis.", "N2", "M1"),
        ("2.7 cm", "T3", "CT chest shows phrenic nerve invasion; no hilar or mediastinal nodes; PET/CT negative.", "N0", "M0"),
        ("3.1 cm", "T4", "CT chest shows invades esophagus and ipsilateral hilar node; PET/CT negative.", "N1", "M0"),
        ("4.1 cm", "T4", "CT chest shows vertebral body invasion and contralateral mediastinal node; PET/CT negative.", "N3", "M0"),
        ("1.5 cm", "T1b", None, None, None),
        ("4.4 cm", "T2b", "CT chest shows carinal lymph node; chest CT negative.", "N2", "M0"),
        ("5.4 cm", "T3", "CT chest shows intrapulmonary node; PET/CT negative.", "N1", "M0"),
        ("2.6 cm", "T1c", "PET/CT shows no regional lymphadenopathy, no distant metastasis.", "N0", "M0"),
        ("6.7 cm", "T3", "CT chest shows invades chest wall and ipsilateral mediastinal node; PET/CT negative.", "N2", "M0"),
        ("1.9 cm", "T1b", "CT chest shows no nodal disease; no distant workup.", "N0", None),
        ("3.3 cm", "T2a", "Chest x-ray normal; no nodal exam.", None, "M0"),
        ("4.9 cm", "T2b", "PET/CT shows supraclavicular node; bone scan shows bone metastasis.", "N3", "M1"),
        ("2.4 cm", "T4", "CT chest shows carina involvement; no hilar or mediastinal nodes; PET/CT negative.", "N0", "M0"),
        ("6.1 cm", "T3", "CT chest shows parietal pleura invasion; ipsilateral hilar node; PET/CT negative.", "N1", "M0"),
    ]
    for i, (sz, et, img, en, em) in enumerate(lung_params, start=121):
        specs.append(
            NewCaseSpec(
                label=f"NEW-LUNG-{i}",
                case=SyntheticCase(
                    scenario_title=f"New NSCLC Case {i}",
                    case_summary=f"{sz} non-small cell lung carcinoma.",
                    age_years=55 + (i % 20),
                    sex_at_birth="Female" if i % 2 else "Male",
                    primary_site="Lung - left lower lobe",
                    histology="Squamous cell carcinoma" if i % 2 else "Adenocarcinoma",
                    imaging_summary=img,
                ),
                expected_mode="provisional_derived",
                expected_t=et,
                expected_n=en,
                expected_m=em,
            )
        )

    # Group 3: 20 new Cervix FIGO 2018 / AJCC 9th cases
    cervix_params = [
        ("1.2 cm", "T1b1", "MRI pelvis shows no pelvic or para-aortic lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.4 cm", "T1b2", "MRI pelvis shows no lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("5.0 cm", "T1b3", "MRI pelvis shows no pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.9 cm", "T2a", "MRI pelvis shows upper two thirds of vagina involvement; no pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("3.7 cm", "T2b", "MRI pelvis shows parametrial extension and 1.6 cm pelvic lymph node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("4.4 cm", "T2b", "MRI pelvis shows parametrial invasion and FDG-avid para-aortic lymph node; chest CT negative.", "N2", "M0", None, None, "provisional_derived"),
        ("3.6 cm", "T3a", "MRI pelvis shows lower third of vagina involvement; no para-aortic or pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("5.1 cm", "T3b", "MRI pelvis shows pelvic sidewall extension with hydronephrosis; no pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("5.6 cm", "T4", "MRI pelvis shows rectal mucosa invasion and para-aortic lymphadenopathy; chest CT negative.", "N2", "M0", None, None, "provisional_derived"),
        ("3.1 cm", "T2b", "MRI pelvis shows parametrial invasion and pelvic lymph node; chest CT negative.", "N1", "M0", "T1b2", "N0", "discrepancy_detected"),
        ("2.7 cm", "T1b2", "MRI pelvis shows no pelvic or para-aortic nodes; chest CT negative.", "N0", "M0", "T1b2", "N0", "verified_concordant"),
        ("4.3 cm", "T3b", "MRI pelvis shows hydronephrosis and pelvic lymph node; chest CT negative.", "N1", "M0", "T3b", "N1", "verified_concordant"),
        ("1.9 cm", "T1b1", None, None, None, None, None, "provisional_derived"),
        ("4.5 cm", "T2b", "MRI pelvis shows parametria invasion and pulmonary metastasis; no pelvic nodes.", "N0", "M1", None, None, "provisional_derived"),
        ("3.3 cm", "T3b", "MRI pelvis shows pelvic sidewall invasion and para-aortic lymph node; chest CT negative.", "N2", "M0", "T2b", "N1", "discrepancy_detected"),
        ("2.6 cm", "T1b2", "MRI pelvis shows pelvic lymph node; no distant workup.", "N1", None, None, None, "provisional_derived"),
        ("4.9 cm", "T1b3", "Chest x-ray normal; no pelvic nodal imaging.", None, "M0", None, None, "provisional_derived"),
        ("3.8 cm", "T2b", "MRI pelvis shows parametrial invasion; no para-aortic nodes; 1.2 cm pelvic node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("5.3 cm", "T4", "MRI pelvis shows bullous edema of bladder; no pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.1 cm", "T1b2", "MRI pelvis shows positive para-aortic lymph node; chest CT negative.", "N2", "M0", "T1b2", "N1", "discrepancy_detected"),
    ]
    for i, (sz, et, img, en, em, pt, pn, emode) in enumerate(cervix_params, start=141):
        specs.append(
            NewCaseSpec(
                label=f"NEW-CERVIX-{i}",
                case=SyntheticCase(
                    scenario_title=f"New Cervix Case {i}",
                    case_summary=f"{sz} cervical carcinoma.",
                    age_years=35 + (i % 25),
                    sex_at_birth="Female",
                    primary_site="Cervix",
                    histology="Squamous cell carcinoma",
                    clinical_t_stage=pt,
                    clinical_n_stage=pn,
                    clinical_m_stage="M0" if pt and em == "M0" else None,
                    imaging_summary=img,
                ),
                expected_mode=emode,
                expected_t=et,
                expected_n=en,
                expected_m=em,
            )
        )

    # Group 4: 20 new Rectum / Colorectal cases
    rect_params = [
        ("Submucosa invasion (T1); no mesorectal nodes; chest CT negative.", "T1", "N0", "M0", None, None, "provisional_derived"),
        ("Muscularis propria invasion (T2); no mesorectal nodes; chest CT negative.", "T2", "N0", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 1 mesorectal lymph node; CT chest/abdomen negative.", "T3", "N1a", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 2 mesorectal lymph nodes; CT chest/abdomen negative.", "T3", "N1b", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 3 mesorectal lymph nodes; CT chest/abdomen negative.", "T3", "N1b", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 4 nodes in mesorectum; CT chest/abdomen negative.", "T3", "N2", "M0", None, None, "provisional_derived"),
        ("Perforates visceral peritoneum; 3 mesorectal lymph nodes; CT chest/abdomen negative.", "T4a", "N1b", "M0", None, None, "provisional_derived"),
        ("Invades adjacent organs (bladder); 5 mesorectal lymph nodes; CT chest/abdomen negative.", "T4b", "N2", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; free of nodal disease; chest CT negative.", "T3", "N0", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 2 mesorectal lymph nodes; chest CT negative.", "T3", "N1b", "M0", "T2", "N0", "discrepancy_detected"),
        ("Muscularis propria invasion; no regional lymph nodes; chest CT negative.", "T2", "N0", "M0", "T2", "N0", "verified_concordant"),
        ("Mesorectal fat invasion; 1 mesorectal node; hepatic metastasis on CT abdomen.", "T3", "N1a", "M1", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; no distant workup.", "T3", None, None, None, None, "provisional_derived"),
        ("Invades uterus; 6 mesorectal nodes; CT chest/abdomen negative.", "T4b", "N2", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 3 mesorectal lymph nodes; chest CT negative.", "T3", "N1b", "M0", "T3", "N1b", "verified_concordant"),
        ("Perirectal fat invasion; 1 mesorectal node; no distant workup.", "T3", "N1a", None, None, None, "provisional_derived"),
        ("Muscularis propria invasion; 2 mesorectal nodes; chest CT negative.", "T2", "N1b", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; no mesorectal nodes; pulmonary metastasis on CT chest.", "T3", "N0", "M1", None, None, "provisional_derived"),
        ("Submucosa invasion (T1); 1 mesorectal node; chest CT negative.", "T1", "N1a", "M0", "T1", "N0", "discrepancy_detected"),
        ("Peritoneal reflection perforation; no mesorectal nodes; chest CT negative.", "T4a", "N0", "M0", None, None, "provisional_derived"),
    ]
    for i, (desc, et, en, em, pt, pn, emode) in enumerate(rect_params, start=161):
        specs.append(
            NewCaseSpec(
                label=f"NEW-RECT-{i}",
                case=SyntheticCase(
                    scenario_title=f"New Rectal Case {i}",
                    case_summary=f"Rectal adenocarcinoma. {desc}",
                    age_years=48 + (i % 25),
                    sex_at_birth="Male" if i % 2 else "Female",
                    primary_site="Rectum",
                    histology="Adenocarcinoma",
                    clinical_t_stage=pt,
                    clinical_n_stage=pn,
                    clinical_m_stage="M0" if pt and em == "M0" else None,
                    imaging_summary=desc if "no distant workup" not in desc else desc,
                ),
                expected_mode=emode,
                expected_t=et,
                expected_n=en,
                expected_m=em,
            )
        )

    # Group 5: 20 new Oral/Larynx/Breast/Prostate/Adversarial cases
    misc_params = [
        ("Oral cavity - tongue", "1.4 cm", None, "T1", None, None, None, None, "provisional_derived"),
        ("Oral cavity - buccal", "2.6 cm", "No cervical lymphadenopathy; chest CT negative.", "T2", "N0", "M0", None, None, "provisional_derived"),
        ("Larynx - glottis", "1.7 cm", "CECT neck shows 1.5 cm ipsilateral node; chest CT negative.", "T1", "N1", "M0", None, None, "provisional_derived"),
        ("Larynx - supraglottis", "3.8 cm", "CECT neck shows bilateral 2.3 cm nodes; chest CT negative.", "T2", "N2c", "M0", None, None, "provisional_derived"),
        ("Nasopharynx", "2.9 cm", "MRI shows skull base invasion and 2.1 cm node; chest CT negative.", "T4b", "N1", "M0", None, None, "provisional_derived"),
        ("Breast", "1.6 cm", "No axillary lymphadenopathy; chest CT negative.", "T1", "N0", "M0", None, None, "provisional_derived"),
        ("Breast", "3.9 cm", "Axillary lymph node 1.8 cm; PET/CT negative for distant metastasis.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("Breast", "5.8 cm", "No axillary nodes; no metastatic workup.", "T3", "N0", None, None, None, "provisional_derived"),
        ("Prostate", "2.7 cm", "MRI pelvis shows no pelvic nodes; bone scan negative.", "T2", "N0", "M0", None, None, "provisional_derived"),
        ("Prostate", "3.1 cm", "MRI pelvis shows 1.5 cm pelvic lymph node; bone scan shows bone metastasis.", "T2", "N1", "M1", None, None, "provisional_derived"),
        ("Esophagus", "3.3 cm", "PET/CT shows 1.8 cm paraesophageal node; no distant metastasis.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("Esophagus", "4.7 cm", "PET/CT shows no regional lymph nodes, no distant metastasis.", "T3", "N0", "M0", None, None, "provisional_derived"),
        ("Oral cavity", None, None, None, None, None, None, None, "insufficient_staging_data"),
        ("Right tonsil - oropharynx", None, None, None, None, None, None, None, "insufficient_staging_data"),
        ("Cervix", None, None, None, None, None, None, None, "insufficient_staging_data"),
        ("Lung", None, None, None, None, None, None, None, "insufficient_staging_data"),
        ("Right tonsil - oropharynx", "2.4 cm", "No contralateral node; 1.9 cm right level II node; chest CT negative.", "T2", "N1", "M0", None, None, "provisional_derived"),
        ("Right tonsil - oropharynx", "2.4 cm", "1.9 cm right level II node; chest CT negative.", "T2", "N1", "M0", "T2", "N0", "discrepancy_detected"),
        ("Oral cavity", "1.9 cm", "No cervical lymphadenopathy; no distant workup.", "T1", "N0", None, None, None, "provisional_derived"),
        ("Larynx", "2.8 cm", "1.6 cm cervical node; no distant workup.", "T2", "N1", None, None, None, "provisional_derived"),
    ]
    for i, (site, sz, img, et, en, em, pt, pn, emode) in enumerate(misc_params, start=181):
        sum_txt = f"{sz} carcinoma of {site.lower()}." if sz else f"Biopsy-proven carcinoma of {site.lower()}; no size reported."
        specs.append(
            NewCaseSpec(
                label=f"NEW-MISC-{i}",
                case=SyntheticCase(
                    scenario_title=f"New Misc Case {i}",
                    case_summary=sum_txt,
                    age_years=50 + (i % 25),
                    sex_at_birth="Female" if site in ("Breast", "Cervix") else "Male",
                    primary_site=site,
                    histology="Squamous cell carcinoma" if any(k in site.lower() for k in ["oral", "larynx", "tonsil", "oropharynx", "nasopharynx", "cervix"]) else "Carcinoma",
                    clinical_t_stage=pt,
                    clinical_n_stage=pn,
                    imaging_summary=img,
                ),
                expected_mode=emode,
                expected_t=et,
                expected_n=en,
                expected_m=em,
            )
        )

    assert len(specs) == 100, f"Expected 100 cases, got {len(specs)}"
    return specs


async def verify_r1_pipeline(spec: NewCaseSpec) -> list[str]:
    errors: list[str] = []
    res = run_pre_mdt_staging_agent(spec.case)

    if not res.staging_locked:
        errors.append("staging_locked is False")
    if "UICC-AJCC-TNM-GENERAL-RULES" not in res.staging_reference_ids:
        errors.append("missing UICC-AJCC-TNM-GENERAL-RULES")
    if any("None" in d for d in res.discrepancies):
        errors.append(f"literal None in discrepancies: {res.discrepancies}")
    if res.mode != spec.expected_mode:
        errors.append(f"mode={res.mode} != expected={spec.expected_mode}")
    if res.provisional_tnm["t"] != spec.expected_t:
        errors.append(f"t={res.provisional_tnm['t']} != expected={spec.expected_t}")
    if res.provisional_tnm["n"] != spec.expected_n:
        errors.append(f"n={res.provisional_tnm['n']} != expected={spec.expected_n}")
    if res.provisional_tnm["m"] != spec.expected_m:
        errors.append(f"m={res.provisional_tnm['m']} != expected={spec.expected_m}")

    ctx = build_case_prompt_context(spec.case)
    if "pre_mdt_staging_lock" not in ctx:
        errors.append("missing pre_mdt_staging_lock in case prompt context")

    # Run full 49-role R1 generation pipeline with mocked Ollama HTTP
    captured_prompts: list[str] = []
    stage_note = res.provisional_stage_label if spec.expected_t is not None else "staging pending workup"
    draft_payload = {
        "position": "conditional",
        "provisional_conclusion": f"Assessment aligned with STG-00 ({stage_note}) within role remit.",
        "preferred_educational_option": "Consider guideline-concordant pathway pending unresolved workup.",
        "perspective_summary": "Role-specific educational assessment respecting STG-00 locked staging.",
        "assumptions": [],
        "unknowns": list(res.missing_for_complete_staging) or ["Confirm final workup."],
        "discussion_options": [],
        "conditional_options": [],
        "evidence_gaps": [],
        "uncertainty_notes": [],
        "disagreement_notes": [],
        "confidence": 0.75,
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"response": json.dumps(draft_payload)}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, path, json=None):
            if isinstance(json, dict) and "prompt" in json:
                captured_prompts.append(json["prompt"])
            return FakeResponse()

    class NoopEngine:
        def retrieve_evidence_for_role(self, role_id, case_obj, limit=3):
            return []

        def format_prompt_injection(self, passages):
            return ""

    with (
        patch.object(ollama.httpx, "AsyncClient", FakeAsyncClient),
        patch("app.services.evidence_retrieval.get_evidence_retrieval_engine", return_value=NoopEngine()),
    ):
        for profile in AGENT_PROFILES:
            assessment = await ollama.generate_agent_assessment(profile, spec.case, 1)
            if assessment.perspective_summary.strip() == assessment.preferred_educational_option.strip():
                errors.append(f"{profile['agent_id']}: verbatim duplicate perspective_summary")
            if spec.expected_t is None and "cT1N1M0" in assessment.preferred_educational_option:
                errors.append(f"{profile['agent_id']}: fabricated cT1N1M0")
            flags = audit_unverified_case_claims(spec.case, assessment.model_dump())
            if profile["agent_id"] == "RO-01":
                bad_flags = [
                    f for f in flags
                    if "sex/gender" in f or ("histological" in f and "small cell lung carcinoma" not in f)
                ]
                if bad_flags:
                    errors.append(f"RO-01 integrity flags: {bad_flags}")

    if len(captured_prompts) != 49:
        errors.append(f"expected 49 R1 prompts, got {len(captured_prompts)}")
    elif not all("STAGING LOCK MANDATE" in p and res.provisional_stage_label in p for p in captured_prompts):
        errors.append("not all 49 R1 prompts contain STAGING LOCK MANDATE and locked stage")

    return errors


async def async_main() -> int:
    specs = build_new_100_cases()
    failures: list[dict[str, object]] = []
    passed = 0

    for spec in specs:
        errs = await verify_r1_pipeline(spec)
        if errs:
            failures.append({"case": spec.label, "errors": errs})
        else:
            passed += 1

    print(
        json.dumps(
            {
                "total_cases": len(specs),
                "total_r1_role_runs": len(specs) * len(AGENT_PROFILES),
                "passed": passed,
                "failed": len(failures),
                "failures": failures,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
