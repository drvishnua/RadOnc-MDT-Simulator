"""Run 5 diverse clinical cases through STG-00 (Pre-MDT Staging Agent) and check for hallucinations."""
from __future__ import annotations

import json
import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas import SyntheticCase
from app.services.pre_mdt_staging_agent import run_pre_mdt_staging_agent


CASES: list[tuple[str, SyntheticCase]] = [
    (
        "Case 1: Oropharynx (Unstaged, No Nodal Imaging)",
        SyntheticCase(
            scenario_title="Ca oropharynx - right tonsillar fossa",
            case_summary="2x1 cm ulceroproliferative growth involving right tonsillar fossa extending into soft palate.",
            age_years=50,
            sex_at_birth="Male",
            primary_site="Right tonsil - oropharynx",
            histology="Squamous cell carcinoma",
            relevant_investigations=["chest xray - normal", "CBC, RLE - normal"],
        ),
    ),
    (
        "Case 2: Oropharynx (Provided N0 vs Imaging Node)",
        SyntheticCase(
            scenario_title="Ca oropharynx - right tonsil with level II node",
            case_summary="2.5 cm right tonsillar carcinoma.",
            age_years=55,
            sex_at_birth="Male",
            primary_site="Right tonsil - oropharynx",
            histology="Squamous cell carcinoma",
            clinical_t_stage="T2",
            clinical_n_stage="N0",
            clinical_m_stage="M0",
            imaging_summary="CECT neck shows 1.5 cm right level II cervical lymph node; chest CT negative.",
        ),
    ),
    (
        "Case 3: Cervix (FIGO 2018 / AJCC 9th with Para-aortic Node)",
        SyntheticCase(
            scenario_title="Ca cervix with parametrial invasion and para-aortic node",
            case_summary="4.5 cm cervical mass with parametrial invasion.",
            age_years=48,
            sex_at_birth="Female",
            primary_site="Cervix",
            histology="Squamous cell carcinoma",
            imaging_summary="MRI pelvis shows parametrial invasion and 1.8 cm para-aortic lymph node; chest CT negative.",
        ),
    ),
    (
        "Case 4: Lung NSCLC (Negated Mediastinal/Hilar Nodes)",
        SyntheticCase(
            scenario_title="Right upper lobe NSCLC",
            case_summary="3.5 cm right upper lobe lung mass.",
            age_years=64,
            sex_at_birth="Male",
            primary_site="Lung",
            histology="Adenocarcinoma",
            imaging_summary="PET/CT shows 3.5 cm RUL mass, no FDG uptake in mediastinal or hilar lymph nodes, no distant metastasis.",
        ),
    ),
    (
        "Case 5: Rectum (Mesorectal Fat Invasion + 3 Mesorectal Nodes)",
        SyntheticCase(
            scenario_title="Locally advanced rectal adenocarcinoma",
            case_summary="Rectal mass with mesorectal fat invasion.",
            age_years=61,
            sex_at_birth="Male",
            primary_site="Rectum",
            histology="Adenocarcinoma",
            imaging_summary="MRI pelvis shows mesorectal fat invasion and 3 mesorectal lymph nodes; CT chest/abdomen negative for distant metastasis.",
        ),
    ),
]


def main() -> None:
    report = []
    for label, case in CASES:
        res = run_pre_mdt_staging_agent(case)
        report.append(
            {
                "case": label,
                "mode": res.mode,
                "provisional_stage_label": res.provisional_stage_label,
                "provisional_tnm": res.provisional_tnm,
                "discrepancies": res.discrepancies,
                "missing_for_complete_staging": res.missing_for_complete_staging,
                "staging_reference_ids": res.staging_reference_ids,
                "staging_locked": res.staging_locked,
            }
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
