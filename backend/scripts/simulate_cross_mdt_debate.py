#!/usr/bin/env python3
"""Cross-Disciplinary Multi-Round MDT Simulation.

Simulates an authentic tumor board discussion on the unoperated oropharynx case across:
- Radiation Oncology: RO-01 (Guideline Purist), RO-02 (Toxicity/Swallowing Conservative)
- Surgical Oncology: SO-01 (Guideline Head & Neck Surgeon), SO-02 (TORS Specialist)
- Medical Oncology: MO-01 (High-Dose Cisplatin Purist), MO-02 (Weekly Dosing Pragmatist)

Rounds:
Round 1: Independent Specialist Assessments.
Round 2: Cross-Disciplinary MDT Debate & Position Reconciliations.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services.ollama import generate_agent_assessment
from app.services.mdt_rounds import generate_debate_contribution


async def main():
    target_roles = ["RO-01", "RO-02", "SO-01", "SO-02", "MO-01", "MO-02"]
    profiles = {p["agent_id"]: p for p in AGENT_PROFILES if p["agent_id"] in target_roles}

    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsillar fossa extending to uvula",
        primary_site="oropharynx",
        anatomical_subsite="right tonsillar fossa",
        case_summary="58-year-old male, unoperated pre-treatment. Squamous cell carcinoma right tonsillar fossa (2.0 cm) extending to uvula, crossing midline. Contrast CT shows a 1x1 cm lymph node in right cervical level 2. Biopsy confirmed SCC, p16 positive. Normal renal function (CrCl 85 mL/min). ECOG 0. Chest CT negative for distant metastasis.",
        histology="Squamous cell carcinoma",
        pathology_summary="Biopsy right tonsil: Infiltrating squamous cell carcinoma, p16 positive (diffuse nuclear and cytoplasmic immunoreactivity >70%).",
        imaging_summary="Contrast CT neck: 2.0 cm right tonsillar mass with medial extension to soft palate/uvula. 1.0 x 1.0 cm level IIA lymph node right neck. Chest CT negative."
    )

    print("================================================================================")
    print("      CROSS-DISCIPLINARY MDT SIMULATION: ROUND 1 & ROUND 2 DEBATE               ")
    print("      (Radiation Oncology vs Surgical Oncology vs Medical Oncology)             ")
    print("================================================================================\n")

    # --------------------------------------------------------------------------
    # ROUND 1: Independent Initial Assessments
    # --------------------------------------------------------------------------
    print(">>> RUNNING ROUND 1: Independent Specialist Assessments...\n")
    r1_records = {}
    for role_id in target_roles:
        prof = profiles[role_id]
        print(f"Generating Round 1 for {role_id}: {prof['name']}...")
        r1_records[role_id] = await generate_agent_assessment(prof, case, round_number=1)

    print("\n--------------------------------------------------------------------------------")
    print("ROUND 1 INDEPENDENT POSITIONS SUMMARY:")
    print("--------------------------------------------------------------------------------")
    for role_id, record in r1_records.items():
        prof = profiles[role_id]
        print(f"[{role_id}] {prof['name']}:")
        print(f"   Position: {record.position.upper()}")
        print(f"   Conclusion: {record.provisional_conclusion[:140]}...")
        print(f"   Preferred Option: {record.preferred_educational_option[:100]}...\n")

    # --------------------------------------------------------------------------
    # ROUND 2: Cross-Disciplinary Debate
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(">>> RUNNING ROUND 2: Cross-Disciplinary MDT Debate & Challenge Interactions...")
    print("================================================================================\n")

    # Key debate perspectives:
    # 1. SO-02 (TORS Surgeon) enters Round 2 having seen RO-01 (Definitive CCRT) and RO-02 (Toxicity)
    # 2. MO-01 (High-Dose Cisplatin) enters Round 2 challenging MO-02 (Weekly Dosing) and SO-02 (Surgery)
    from app.services.mdt_rounds import generate_debate_contribution

    debate_roles = ["SO-02", "MO-01"]

    for debater_id in debate_roles:
        debater_prof = profiles[debater_id]
        own_r1 = r1_records[debater_id].model_dump()
        peer_views = [
            {
                "agent_id": rid,
                "agent_name": profiles[rid]["name"],
                "assessment": rec.model_dump(),
            }
            for rid, rec in r1_records.items()
            if rid != debater_id
        ]

        print(f"Generating Round 2 Debate Contribution for [{debater_id}: {debater_prof['name']}]...")
        try:
            r2_contribution = await generate_debate_contribution(
                profile=debater_prof,
                case=case,
                own_independent_assessment=own_r1,
                peer_views=peer_views,
            )
            print(f">>> [{debater_id}] ROUND 2 RECONCILIATION & DEBATE:")
            print(f"    Position: {getattr(r2_contribution, 'position', 'N/A').upper()}")
            print(f"    Statement: {getattr(r2_contribution, 'perspective_summary', getattr(r2_contribution, 'provisional_conclusion', 'N/A'))}")
            print(f"    Disagreements / Challenges: {getattr(r2_contribution, 'disagreement_notes', [])}")
            print(f"    Confidence: {getattr(r2_contribution, 'confidence', 'N/A')}\n")
        except Exception as exc:
            print(f"    Debate generation error: {exc}\n")

    print("================================================================================")
    print("MDT Simulation Completed.")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(main())
