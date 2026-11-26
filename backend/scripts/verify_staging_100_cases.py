"""Run 100 distinct clinical cases across major oncology sites and check STG-00 staging integrity."""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas import SyntheticCase
from app.services.pre_mdt_staging_agent import run_pre_mdt_staging_agent


@dataclass
class CaseSpec:
    label: str
    case: SyntheticCase
    expected_mode: str | None = None
    expected_t: str | None = None
    expected_n: str | None = None
    expected_m: str | None = None
    check_n: bool = False
    check_m: bool = False


def build_100_cases() -> list[CaseSpec]:
    specs: list[CaseSpec] = []

    # 1. Oropharynx (20 cases: HPV+ / HPV- / unknown, varied sizes, nodes, negations, discrepancies)
    oro_variants = [
        ("1.4 cm", "T1", "p16-negative", "No cervical lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.0 cm", "T1", "p16-negative", "Chest x-ray normal.", None, "M0", None, None, "provisional_derived"),
        ("2.4 cm", "T2", "p16-negative", "CECT neck shows 1.8 cm right level II lymph node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("3.3 cm", "T2", "p16-negative", "CECT neck shows 4.2 cm right level II lymph node; PET/CT negative for distant metastasis.", "N2a", "M0", None, None, "provisional_derived"),
        ("3.8 cm", "T2", "p16-negative", "CECT neck shows bilateral 2.2 cm level II lymph nodes; chest CT negative.", "N2c", "M0", None, None, "provisional_derived"),
        ("4.6 cm", "T3", "p16-negative", "MRI shows 2.5 cm right level II lymph node with overt extranodal extension (ENE); chest CT negative.", "N3", "M0", None, None, "provisional_derived"),
        ("2.6 cm", "T2", "p16-positive", "CECT neck shows 2.1 cm right level II lymph node; PET/CT negative for distant metastasis.", "N1", "M0", None, None, "provisional_derived"),
        ("3.1 cm", "T2", "p16-positive", "CECT neck shows bilateral 2.4 cm level II lymph nodes; chest CT negative.", "N2", "M0", None, None, "provisional_derived"),
        ("4.4 cm", "T3", "p16-positive", "CECT neck shows 6.5 cm right level II lymph node; PET/CT negative for distant metastasis.", "N3", "M0", None, None, "provisional_derived"),
        ("2.2 cm", "T4b", "p16-negative", "MRI shows skull base invasion and no cervical lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("3.0 cm", "T4a", "p16-negative", "MRI shows mandible invasion and 1.9 cm ipsilateral level II node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("1.8 cm", "T1", "p16-negative", "CECT neck shows 1.5 cm right level II node; chest CT negative.", "N1", "M0", "T1", "N0", "discrepancy_detected"),
        ("3.4 cm", "T2", "p16-negative", "CECT neck shows no suspicious lymph nodes; chest CT negative.", "N0", "M0", "T2", "N0", "verified_concordant"),
        ("2.7 cm", "T2", "p16-positive", "CECT neck shows 2.0 cm ipsilateral level II node; chest CT negative.", "N1", "M0", "T2", "N1", "verified_concordant"),
        ("4.9 cm", "T3", "p16-negative", "MRI shows no enlarged cervical nodes; chest CT negative.", "N0", "M0", "T1", "N0", "discrepancy_detected"),
        ("1.6 cm", "T1", "p16-negative", "No imaging performed.", None, None, None, None, "provisional_derived"),
        ("2.9 cm", "T2", "p16-negative", "MRI shows 7.0 cm right cervical lymph node; PET/CT shows bone metastasis.", "N3", "M1", None, None, "provisional_derived"),
        ("3.7 cm", "T2", "p16-positive", "No contralateral lymph nodes; 2.0 cm ipsilateral level II lymph node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("1.9 cm", "T1", "p16-negative", "Extension to lingual surface of epiglottis; no cervical adenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.5 cm", "T2", "p16-negative", "CECT neck shows 2.3 cm contralateral level III lymph node; chest CT negative.", "N2c", "M0", "T2", "N1", "discrepancy_detected"),
    ]
    for idx, (sz, exp_t, hpv, img, exp_n, exp_m, prov_t, prov_n, exp_mode) in enumerate(oro_variants, start=1):
        subsite = "Right tonsil - oropharynx" if idx % 2 == 1 else "Base of tongue - oropharynx"
        ext = " Extension to lingual surface of epiglottis." if idx == 19 else ""
        specs.append(
            CaseSpec(
                label=f"ORO-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"Oropharyngeal SCC case {idx}",
                    case_summary=f"{sz} {hpv} squamous cell carcinoma of {subsite.lower()}.{ext}",
                    age_years=45 + idx,
                    sex_at_birth="Male" if idx % 3 else "Female",
                    primary_site=subsite,
                    histology="Squamous cell carcinoma",
                    clinical_t_stage=prov_t,
                    clinical_n_stage=prov_n,
                    clinical_m_stage="M0" if prov_t and exp_m == "M0" else None,
                    imaging_summary=img if img != "No imaging performed." else None,
                ),
                expected_mode=exp_mode,
                expected_t=exp_t if idx != 19 else "T3",
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 2. Larynx, Oral Cavity & Nasopharynx (15 cases)
    hn_sites = [
        ("Larynx - glottis", "1.2 cm", "T1", "No cervical lymphadenopathy; chest CT negative.", "N0", "M0"),
        ("Larynx - supraglottis", "2.6 cm", "T2", "CECT neck shows 1.7 cm right level II node; chest CT negative.", "N1", "M0"),
        ("Larynx - glottis", "3.4 cm", "T2", "CECT neck shows bilateral 2.0 cm level III nodes; chest CT negative.", "N2c", "M0"),
        ("Oral cavity - tongue", "1.5 cm", "T1", "No imaging available.", None, None),
        ("Oral cavity - buccal mucosa", "2.8 cm", "T2", "CECT neck shows 3.6 cm ipsilateral level Ib node; chest CT negative.", "N2a", "M0"),
        ("Oral cavity - floor of mouth", "4.3 cm", "T3", "MRI shows mandible invasion and no cervical nodes; chest CT negative.", "N0", "M0"),
        ("Nasopharynx", "2.2 cm", "T2", "MRI shows skull base invasion and 2.5 cm retropharyngeal node; PET/CT negative.", "N1", "M0"),
        ("Larynx - glottis", "1.9 cm", "T1", "Chest x-ray normal.", None, "M0"),
        ("Oral cavity - tongue", "3.9 cm", "T2", "CECT neck shows 2.0 cm ipsilateral node with ENE; chest CT negative.", "N3", "M0"),
        ("Oral cavity - palate", "2.1 cm", "T2", "MRI shows hard palate invasion; no lymphadenopathy; chest CT negative.", "N0", "M0"),
        ("Larynx - supraglottis", "4.8 cm", "T3", "CECT neck shows 2.4 cm ipsilateral level II node; PET/CT shows lung metastasis.", "N1", "M1"),
        ("Nasopharynx", "3.1 cm", "T2", "CECT neck shows bilateral 2.2 cm cervical nodes; chest CT negative.", "N2c", "M0"),
        ("Oral cavity - tongue", "1.1 cm", "T1", "PET/CT shows no FDG uptake in cervical lymph nodes, no distant metastasis.", "N0", "M0"),
        ("Larynx - glottis", "2.5 cm", "T2", "MRI shows carotid encasement; no cervical adenopathy; chest CT negative.", "N0", "M0"),
        ("Oral cavity - alveolus", "3.2 cm", "T2", "CECT neck shows 1.8 cm ipsilateral node; chest CT negative.", "N1", "M0"),
    ]
    for idx, (site, sz, exp_t, img, exp_n, exp_m) in enumerate(hn_sites, start=1):
        real_t = "T4a" if idx == 6 else ("T4b" if idx in (7, 14) else ("T4a" if idx == 10 else exp_t))
        specs.append(
            CaseSpec(
                label=f"HN-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"Head & neck case {idx}: {site}",
                    case_summary=f"{sz} squamous cell carcinoma of {site.lower()}.",
                    age_years=50 + idx,
                    sex_at_birth="Male",
                    primary_site=site,
                    histology="Squamous cell carcinoma",
                    imaging_summary=img if img != "No imaging available." else None,
                ),
                expected_mode="provisional_derived",
                expected_t=real_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 3. Lung NSCLC (15 cases)
    lung_variants = [
        ("0.9 cm", "T1a", "PET/CT shows no FDG uptake in hilar or mediastinal nodes, no distant metastasis.", "N0", "M0"),
        ("1.6 cm", "T1b", "PET/CT shows 1.6 cm RUL nodule, no FDG uptake in mediastinal or hilar lymph nodes, no distant metastasis.", "N0", "M0"),
        ("2.5 cm", "T1c", "PET/CT shows ipsilateral hilar lymph node; no distant metastasis.", "N1", "M0"),
        ("3.4 cm", "T2a", "CT chest shows ipsilateral mediastinal lymph node; PET/CT negative for distant metastasis.", "N2", "M0"),
        ("4.5 cm", "T2b", "PET/CT shows contralateral mediastinal lymph node; no distant metastasis.", "N3", "M0"),
        ("5.6 cm", "T3", "CT chest shows no enlarged nodes; chest CT negative for distant metastasis.", "N0", "M0"),
        ("7.4 cm", "T4", "CT chest shows ipsilateral mediastinal node; bone scan shows bone metastasis.", "N2", "M1"),
        ("3.2 cm", "T3", "CT chest shows chest wall invasion; no hilar or mediastinal nodes; PET/CT negative.", "N0", "M0"),
        ("2.8 cm", "T4", "CT chest shows carina involvement and ipsilateral hilar node; PET/CT negative.", "N1", "M0"),
        ("3.9 cm", "T4", "CT chest shows mediastinum invasion and supraclavicular lymph node; PET/CT negative.", "N3", "M0"),
        ("1.8 cm", "T1b", "No nodal or metastatic imaging provided.", None, None),
        ("4.2 cm", "T2b", "CT chest shows subcarinal lymph node; chest CT negative.", "N2", "M0"),
        ("5.2 cm", "T3", "CT chest shows peribronchial node; PET/CT negative for distant metastasis.", "N1", "M0"),
        ("2.3 cm", "T1c", "PET/CT shows no regional lymph node involvement, no distant metastasis.", "N0", "M0"),
        ("6.4 cm", "T3", "CT chest shows parietal pericardium invasion and ipsilateral mediastinal node; PET/CT negative.", "N2", "M0"),
    ]
    for idx, (sz, exp_t, img, exp_n, exp_m) in enumerate(lung_variants, start=1):
        specs.append(
            CaseSpec(
                label=f"LUNG-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"NSCLC case {idx}",
                    case_summary=f"{sz} non-small cell lung carcinoma.",
                    age_years=58 + idx,
                    sex_at_birth="Male" if idx % 2 else "Female",
                    primary_site="Lung - right upper lobe",
                    histology="Adenocarcinoma",
                    imaging_summary=img if "No nodal" not in img else None,
                ),
                expected_mode="provisional_derived",
                expected_t=exp_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 4. Cervix FIGO 2018 / AJCC 9th (15 cases)
    cervix_variants = [
        ("1.6 cm", "T1b1", "MRI pelvis shows no pelvic or para-aortic lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("2.8 cm", "T1b2", "MRI pelvis shows no lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("4.6 cm", "T1b3", "MRI pelvis shows no pelvic nodes; chest x-ray normal.", "N0", "M0", None, None, "provisional_derived"),
        ("3.2 cm", "T2a", "MRI pelvis shows upper two thirds of vagina involvement; no lymphadenopathy; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("3.5 cm", "T2b", "MRI pelvis shows parametrial invasion and 1.4 cm pelvic lymph node; chest CT negative.", "N1", "M0", None, None, "provisional_derived"),
        ("4.0 cm", "T2b", "MRI pelvis shows parametrial invasion and 1.8 cm para-aortic lymph node; chest CT negative.", "N2", "M0", None, None, "provisional_derived"),
        ("4.2 cm", "T3a", "MRI pelvis shows lower third of vagina involvement and no para-aortic or pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("4.8 cm", "T3b", "MRI pelvis shows pelvic sidewall extension with hydronephrosis; no pelvic nodes; chest CT negative.", "N0", "M0", None, None, "provisional_derived"),
        ("5.2 cm", "T4", "MRI pelvis shows bladder mucosa invasion and para-aortic lymphadenopathy; chest CT negative.", "N2", "M0", None, None, "provisional_derived"),
        ("3.4 cm", "T2b", "MRI pelvis shows parametrial invasion and pelvic lymph node; chest CT negative.", "N1", "M0", "T1b2", "N0", "discrepancy_detected"),
        ("2.5 cm", "T1b2", "MRI pelvis shows no pelvic or para-aortic nodes; chest CT negative.", "N0", "M0", "T1b2", "N0", "verified_concordant"),
        ("3.8 cm", "T3b", "MRI pelvis shows hydronephrosis and pelvic lymph node; chest CT negative.", "N1", "M0", "T3b", "N1", "verified_concordant"),
        ("2.2 cm", "T1b2", "No imaging performed.", None, None, None, None, "provisional_derived"),
        ("4.1 cm", "T2b", "MRI pelvis shows parametria involvement and liver metastasis; no pelvic nodes.", "N0", "M1", None, None, "provisional_derived"),
        ("3.9 cm", "T3b", "MRI pelvis shows pelvic sidewall invasion and para-aortic lymph node; chest CT negative.", "N2", "M0", "T2b", "N1", "discrepancy_detected"),
    ]
    for idx, (sz, exp_t, img, exp_n, exp_m, prov_t, prov_n, exp_mode) in enumerate(cervix_variants, start=1):
        specs.append(
            CaseSpec(
                label=f"CERVIX-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"Cervical cancer case {idx}",
                    case_summary=f"{sz} cervical squamous cell carcinoma.",
                    age_years=38 + idx,
                    sex_at_birth="Female",
                    primary_site="Cervix",
                    histology="Squamous cell carcinoma",
                    clinical_t_stage=prov_t,
                    clinical_n_stage=prov_n,
                    clinical_m_stage="M0" if prov_t and exp_m == "M0" else None,
                    imaging_summary=img if img != "No imaging performed." else None,
                ),
                expected_mode=exp_mode,
                expected_t=exp_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 5. Rectum / Colorectal (15 cases)
    rect_variants = [
        ("Submucosa invasion (T1); no mesorectal nodes; chest CT negative.", "T1", "N0", "M0", None, None, "provisional_derived"),
        ("Muscularis propria invasion (T2); no mesorectal nodes; chest CT negative.", "T2", "N0", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 1 mesorectal lymph node; CT chest/abdomen negative.", "T3", "N1a", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 2 mesorectal lymph nodes; CT chest/abdomen negative.", "T3", "N1b", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 3 mesorectal lymph nodes; CT chest/abdomen negative.", "T3", "N1b", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 5 mesorectal lymph nodes; CT chest/abdomen negative.", "T3", "N2", "M0", None, None, "provisional_derived"),
        ("Perforates visceral peritoneum; 2 mesorectal lymph nodes; CT chest/abdomen negative.", "T4a", "N1b", "M0", None, None, "provisional_derived"),
        ("Invades adjacent organs (prostate); 4 mesorectal lymph nodes; CT chest/abdomen negative.", "T4b", "N2", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; without mesorectal nodes; chest CT negative.", "T3", "N0", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 3 mesorectal lymph nodes; chest CT negative.", "T3", "N1b", "M0", "T2", "N0", "discrepancy_detected"),
        ("Muscularis propria invasion; no regional lymph nodes; chest CT negative.", "T2", "N0", "M0", "T2", "N0", "verified_concordant"),
        ("Mesorectal fat invasion; 1 mesorectal node; liver metastasis on CT abdomen.", "T3", "N1a", "M1", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; no imaging of distant sites.", "T3", None, None, None, None, "provisional_derived"),
        ("Invades bladder; 6 mesorectal nodes; CT chest/abdomen negative.", "T4b", "N2", "M0", None, None, "provisional_derived"),
        ("Mesorectal fat invasion; 2 mesorectal lymph nodes; chest CT negative.", "T3", "N1b", "M0", "T3", "N1b", "verified_concordant"),
    ]
    for idx, (desc, exp_t, exp_n, exp_m, prov_t, prov_n, exp_mode) in enumerate(rect_variants, start=1):
        specs.append(
            CaseSpec(
                label=f"RECT-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"Rectal adenocarcinoma case {idx}",
                    case_summary=f"Rectal adenocarcinoma. {desc}",
                    age_years=52 + idx,
                    sex_at_birth="Male" if idx % 2 else "Female",
                    primary_site="Rectum",
                    histology="Adenocarcinoma",
                    clinical_t_stage=prov_t,
                    clinical_n_stage=prov_n,
                    clinical_m_stage="M0" if prov_t and exp_m == "M0" else None,
                    imaging_summary=desc if "no imaging" not in desc else None,
                ),
                expected_mode=exp_mode,
                expected_t=exp_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 6. Breast, Prostate & Esophagus (10 cases)
    other_sites = [
        ("Breast", "1.8 cm invasive ductal carcinoma.", "No axillary lymphadenopathy; chest CT negative.", "T1", "N0", "M0"),
        ("Breast", "3.2 cm invasive ductal carcinoma.", "Axillary lymph node 1.5 cm; PET/CT negative for distant metastasis.", "T2", "N1", "M0"),
        ("Breast", "5.5 cm invasive ductal carcinoma.", "No axillary nodes; no metastatic workup.", "T3", "N0", None),
        ("Prostate", "2.4 cm prostatic adenocarcinoma.", "MRI pelvis shows no pelvic lymph nodes; bone scan negative.", "T2", "N0", "M0"),
        ("Prostate", "3.5 cm prostatic adenocarcinoma.", "MRI pelvis shows 1.6 cm pelvic lymph node; bone scan shows bone metastasis.", "T2", "N1", "M1"),
        ("Esophagus", "3.6 cm esophageal squamous cell carcinoma.", "PET/CT shows 2.0 cm paraesophageal lymph node; no distant metastasis.", "T2", "N1", "M0"),
        ("Esophagus", "4.8 cm esophageal adenocarcinoma.", "PET/CT shows no regional lymph nodes, no distant metastasis.", "T3", "N0", "M0"),
        ("Breast", "2.2 cm invasive lobular carcinoma.", "No imaging provided.", "T2", None, None),
        ("Prostate", "1.9 cm prostatic adenocarcinoma.", "No nodal or bone imaging provided.", "T1", None, None),
        ("Esophagus", "2.9 cm esophageal SCC.", "Chest x-ray normal; no nodal exam.", "T2", None, "M0"),
    ]
    for idx, (site, sum_txt, img, exp_t, exp_n, exp_m) in enumerate(other_sites, start=1):
        specs.append(
            CaseSpec(
                label=f"OTHER-{idx:02d}",
                case=SyntheticCase(
                    scenario_title=f"{site} case {idx}",
                    case_summary=sum_txt,
                    age_years=60 + idx,
                    sex_at_birth="Female" if site == "Breast" else "Male",
                    primary_site=site,
                    histology="Carcinoma",
                    imaging_summary=img if "No imaging" not in img and "No nodal" not in img else None,
                ),
                expected_mode="provisional_derived",
                expected_t=exp_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    # 7. Minimal & Adversarial Integrity Cases (10 cases)
    adv_cases = [
        ("ADV-01", "Oral cavity", "Ulcerative lesion on tongue; biopsy shows SCC.", None, None, None, None, None, None, "insufficient_staging_data"),
        ("ADV-02", "Right tonsil - oropharynx", "Tonsillar lesion; biopsy pending.", None, None, None, None, None, None, "insufficient_staging_data"),
        ("ADV-03", "Cervix", "Cervical lesion; no size or imaging.", None, None, None, None, None, None, "insufficient_staging_data"),
        ("ADV-04", "Lung", "Lung mass; no size or imaging.", None, None, None, None, None, None, "insufficient_staging_data"),
        ("ADV-05", "Right tonsil - oropharynx", "2.3 cm tonsillar SCC.", "No contralateral node; 1.7 cm right level II lymph node; chest CT negative.", None, None, "T2", "N1", "M0", "provisional_derived"),
        ("ADV-06", "Right tonsil - oropharynx", "2.3 cm tonsillar SCC.", "1.7 cm right level II lymph node; chest CT negative.", "T2", "N0", "T2", "N1", "M0", "discrepancy_detected"),
        ("ADV-07", "Right tonsil - oropharynx", "2.3 cm tonsillar SCC.", "PET/CT shows distant liver metastasis; no cervical nodes.", None, None, "T2", "N0", "M1", "discrepancy_detected"),
        ("ADV-08", "Rectum", "Rectal mass.", "No node notes available; chest CT negative.", None, None, "T3", None, "M0", "provisional_derived"),
        ("ADV-09", "Oral cavity", "1.7 cm tongue SCC.", "No cervical lymphadenopathy; no chest imaging.", None, None, "T1", "N0", None, "provisional_derived"),
        ("ADV-10", "Larynx", "2.5 cm glottic SCC.", "1.5 cm cervical node; no distant workup.", None, None, "T2", "N1", None, "provisional_derived"),
    ]
    for label, site, sum_txt, img, prov_t, prov_n, exp_t, exp_n, exp_m, exp_mode in adv_cases:
        prov_m = "M0" if label == "ADV-07" else None
        specs.append(
            CaseSpec(
                label=label,
                case=SyntheticCase(
                    scenario_title=f"Adversarial integrity case {label}",
                    case_summary=sum_txt,
                    age_years=55,
                    sex_at_birth="Male",
                    primary_site=site,
                    histology="Squamous cell carcinoma",
                    clinical_t_stage=prov_t,
                    clinical_n_stage=prov_n,
                    clinical_m_stage=prov_m,
                    imaging_summary=img,
                ),
                expected_mode=exp_mode,
                expected_t=exp_t,
                expected_n=exp_n,
                expected_m=exp_m,
                check_n=True,
                check_m=True,
            )
        )

    assert len(specs) == 100, f"Expected 100 cases, built {len(specs)}"
    return specs


def main() -> int:
    specs = build_100_cases()
    failures: list[dict[str, object]] = []
    passed = 0

    for spec in specs:
        res = run_pre_mdt_staging_agent(spec.case)
        reasons: list[str] = []

        if not res.staging_locked:
            reasons.append("staging_locked is False")
        if "UICC-AJCC-TNM-GENERAL-RULES" not in res.staging_reference_ids:
            reasons.append("missing UICC-AJCC-TNM-GENERAL-RULES")
        if any("None" in d for d in res.discrepancies):
            reasons.append(f"literal None in discrepancies: {res.discrepancies}")
        if spec.expected_mode and res.mode != spec.expected_mode:
            reasons.append(f"mode={res.mode} != expected={spec.expected_mode}")
        if spec.expected_t is not None and res.provisional_tnm["t"] != spec.expected_t:
            reasons.append(f"t={res.provisional_tnm['t']} != expected={spec.expected_t}")
        if spec.check_n and res.provisional_tnm["n"] != spec.expected_n:
            reasons.append(f"n={res.provisional_tnm['n']} != expected={spec.expected_n}")
        if spec.check_m and res.provisional_tnm["m"] != spec.expected_m:
            reasons.append(f"m={res.provisional_tnm['m']} != expected={spec.expected_m}")

        if reasons:
            failures.append(
                {
                    "case": spec.label,
                    "reasons": reasons,
                    "got": {
                        "mode": res.mode,
                        "label": res.provisional_stage_label,
                        "tnm": res.provisional_tnm,
                        "discrepancies": res.discrepancies,
                    },
                }
            )
        else:
            passed += 1

    print(
        json.dumps(
            {
                "total": len(specs),
                "passed": passed,
                "failed": len(failures),
                "failures": failures,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
