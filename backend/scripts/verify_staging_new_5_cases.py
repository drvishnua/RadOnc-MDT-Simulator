"""Run 5 new edge-case clinical scenarios through STG-00 (Pre-MDT Staging Agent)."""
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
        "Case 6: HPV+ Oropharynx (Bilateral Level II Nodes)",
        SyntheticCase(
            scenario_title="p16-positive base of tongue SCC",
            case_summary="3.2 cm p16-positive squamous cell carcinoma of the base of tongue.",
            age_years=54,
            sex_at_birth="Male",
            primary_site="Base of tongue - oropharynx",
            histology="Squamous cell carcinoma",
            imaging_summary="CECT neck shows bilateral 2.5 cm level II lymph nodes; PET/CT negative for distant metastasis.",
        ),
    ),
    (
        "Case 7: p16- Oropharynx (Skull Base Invasion + ENE)",
        SyntheticCase(
            scenario_title="p16-negative right tonsil SCC with skull base invasion",
            case_summary="4.5 cm p16-negative squamous cell carcinoma invading skull base.",
            age_years=62,
            sex_at_birth="Male",
            primary_site="Right tonsil - oropharynx",
            histology="Squamous cell carcinoma",
            imaging_summary="MRI shows skull base invasion and a 2.8 cm right level II lymph node with overt extranodal extension (ENE); CT chest negative.",
        ),
    ),
    (
        "Case 8: Cervix (Provided T1b2 vs Pelvic Sidewall + Hydronephrosis)",
        SyntheticCase(
            scenario_title="Cervical SCC with pelvic sidewall extension",
            case_summary="Cervical mass.",
            age_years=49,
            sex_at_birth="Female",
            primary_site="Cervix",
            histology="Squamous cell carcinoma",
            clinical_t_stage="T1b2",
            clinical_n_stage="N0",
            clinical_m_stage="M0",
            imaging_summary="MRI pelvis shows 3.5 cm cervical mass extending to left pelvic sidewall with hydronephrosis, no pelvic or para-aortic lymphadenopathy; chest CT negative.",
        ),
    ),
    (
        "Case 9: Lung NSCLC (Carina Involvement + Ipsilateral Mediastinal Node)",
        SyntheticCase(
            scenario_title="Left main bronchus NSCLC",
            case_summary="3.8 cm squamous cell carcinoma of left main bronchus.",
            age_years=66,
            sex_at_birth="Male",
            primary_site="Left main bronchus - lung",
            histology="Squamous cell carcinoma",
            imaging_summary="CT chest shows 3.8 cm mass with involvement of carina and enlarged ipsilateral mediastinal lymph node; PET/CT negative for distant metastasis.",
        ),
    ),
    (
        "Case 10: Oral Cavity (Minimal Info — No Size, No Imaging, No Staging)",
        SyntheticCase(
            scenario_title="Lateral tongue ulcerative lesion",
            case_summary="Ulcerative lesion on lateral border of tongue, biopsy shows squamous cell carcinoma.",
            age_years=58,
            sex_at_birth="Female",
            primary_site="Oral cavity",
            histology="Squamous cell carcinoma",
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
