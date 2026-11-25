#!/usr/bin/env python3
"""Run multi-site simulation audit for RO-01 across Cervix, Lung, and Rectum cases.

Validates:
1. Disease site fidelity (no larynx or cross-site organ leakage).
2. Site-specific staging derivation (FIGO 2018, AJCC 8th Thoracic & Colorectal).
3. Evidence retrieval site-isolation.
4. Multi-society guideline citation and conditional reasoning.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services.staging_engine import derive_or_verify_staging
from app.services.evidence_retrieval import get_evidence_retrieval_engine
from app.services.ollama import generate_agent_assessment


async def main():
    profile = next((p for p in AGENT_PROFILES if p["agent_id"] == "RO-01"), None)
    if not profile:
        print("ERROR: RO-01 profile not found in catalog.")
        return

    engine = get_evidence_retrieval_engine()

    cases = [
        {
            "site_label": "CERVIX (FIGO Stage IIIC1)",
            "case": SyntheticCase(
                scenario_title="Locally Advanced Cervical Carcinoma",
                primary_site="cervix",
                anatomical_subsite="cervix uteri",
                case_summary="52-year-old female presenting with vaginal bleeding. Pelvic MRI demonstrates a 4.5 cm cervical mass extending laterally into bilateral parametria reaching the pelvic sidewalls. Multiple enlarged, FDG-avid external iliac and obturator pelvic lymph nodes (largest 1.8 cm). No para-aortic lymphadenopathy. PET/CT confirms no distant metastases.",
                histology="Squamous cell carcinoma",
                pathology_summary="Cervical biopsy: Moderately differentiated invasive squamous cell carcinoma.",
                imaging_summary="Pelvic MRI: 4.5 cm cervical lesion, bilateral parametrial infiltration extending to pelvic sidewall (bilateral). Bilateral pelvic lymphadenopathy. PET-CT: High FDG uptake in primary cervical tumor and pelvic nodes; no FDG-avid para-aortic nodes or distant metastases."
            )
        },
        {
            "site_label": "LUNG (Stage IA Peripheral Adenocarcinoma - SBRT candidate)",
            "case": SyntheticCase(
                scenario_title="Early Stage Peripheral NSCLC in Medically Inoperable Patient",
                primary_site="lung",
                anatomical_subsite="right upper lobe peripheral",
                case_summary="68-year-old male with severe COPD (FEV1 35% predicted, GOLD Grade 3) and 45 pack-year smoking history. CT chest reveals a 2.8 cm solitary peripheral pulmonary nodule in the right upper lobe. PET/CT shows intense FDG avidity (SUVmax 8.5) in the RUL nodule; mediastinal and hilar lymph nodes are PET-negative. No distant metastatic disease.",
                histology="Adenocarcinoma",
                pathology_summary="CT-guided core biopsy RUL nodule: Invasive adenocarcinoma, acinar predominant.",
                imaging_summary="Chest CT and PET/CT: 2.8 cm peripheral right upper lobe mass, >2 cm from carina and proximal bronchial tree. Mediastinum and hila PET-negative. Brain MRI and abdominal CT without distant metastases."
            )
        },
        {
            "site_label": "RECTUM (Stage IIIB Locally Advanced Rectal Cancer - TNT candidate)",
            "case": SyntheticCase(
                scenario_title="Locally Advanced Mid-Rectal Adenocarcinoma with Threatened CRM",
                primary_site="rectum",
                anatomical_subsite="mid rectum (7 cm from anal verge)",
                case_summary="59-year-old male presenting with hematochezia and altered bowel habits. Colonoscopy reveals an ulceroproliferative tumor 7 cm from the anal verge. High-resolution pelvic MRI demonstrates tumor penetration into mesorectal fat by 6 mm (T3c), extending to within 1.0 mm of the mesorectal fascia (threatened circumferential resection margin). 3 suspicious mesorectal lymph nodes with irregular borders. CT chest/abdomen/pelvis negative for distant metastasis.",
                histology="Adenocarcinoma",
                pathology_summary="Rectal biopsy: Moderately differentiated adenocarcinoma, mismatch repair proficient (pMMR / MSS).",
                imaging_summary="Pelvic MRI: Mid-rectal tumor 4.0 cm length, mesorectal fat invasion 6 mm (T3c). Distance to mesorectal fascia 1.0 mm (threatened CRM). 3 involved mesorectal lymph nodes (N1b). CT staging: No liver, lung, or distant metastases."
            )
        }
    ]

    print("================================================================================")
    print("      MULTI-SITE MDT SIMULATION AUDIT: RO-01 (GUIDELINE-FOCUSED SPECIALIST)     ")
    print("================================================================================\n")

    for idx, item in enumerate(cases, 1):
        site_label = item["site_label"]
        case = item["case"]

        print(f"[{idx}/3] TESTING CASE: {site_label}")
        print("--------------------------------------------------------------------------------")

        # 1. Deterministic Staging Derivation
        stg = derive_or_verify_staging(case)
        print(f"Staging Engine Derived: {stg['applicable_system']}")
        print(f"TNM Category: {stg['derived_t_stage']} {stg['derived_n_stage']} {stg['derived_m_stage']} -> Stage Group: {stg['derived_stage_group']}")
        if stg['discrepancies']:
            print(f"Discrepancies / Notes: {stg['discrepancies']}")

        # 2. Evidence Retrieval Site-Isolation Check
        ev = engine.retrieve_evidence_for_role("RO-01", case, limit=6)
        ev_sources = [f"{e.source_id} ({e.title[:45]}...)" for e in ev]
        print(f"RO-01 Retrieved Evidence Passages ({len(ev)}):")
        for s in ev_sources:
            print(f"   * {s}")

        # 3. Model Generation via Local Ollama
        print("\nExecuting Local Ollama Generation (RO-01)...")
        try:
            assessment = await generate_agent_assessment(profile, case, round_number=1)
            print("\n>>> RO-01 PROVISIONAL CONCLUSION:")
            print(f"    Position: {assessment.position.upper()}")
            print(f"    Text: {assessment.provisional_conclusion}")
            print("\n>>> RO-01 PREFERRED EDUCATIONAL OPTION:")
            print(f"    {assessment.preferred_educational_option}")
            print("\n>>> RO-01 TOPICS FOR MDT DISCUSSION:")
            for opt in assessment.discussion_options:
                print(f"    - {opt}")
        except Exception as exc:
            print(f"ERROR during generation: {exc}")

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
