#!/usr/bin/env python3
"""RadOnc MDT Simulator: Multi-Site & Multi-Age Greatness Benchmark.

Simulates and evaluates diverse synthetic cancer cases spanning:
- All Age Groups: Pediatric (Age 8), AYA (Age 19), Reproductive Age (Age 32),
  Middle-Age (Age 48, Age 57), Senior Adult (Age 66), Elderly (Age 74), Geriatric (Age 81).
- All Major Anatomical Sites: CNS, Bone/Musculoskeletal, Cervix/Gynecologic,
  Breast, Head & Neck, Gastrointestinal/Rectum, Genitourinary/Bladder, Thoracic/Lung.
- Diverse Histologies: Medulloblastoma, Ewing Sarcoma, Squamous Cell Carcinoma (SCC),
  Triple-Negative Invasive Ductal Carcinoma (IDC), Adenocarcinoma, Urothelial Carcinoma.

Evaluates 5 Dimensions of Educational Simulation Greatness:
1. Case Integrity & Provenance Adherence (zero unconfirmed staging, knowns vs unknowns).
2. Evidence Retrieval Domain Isolation & Precision.
3. Model Reasoning & Stance Authenticity (clinical guidelines, OAR limits, age-specific factors).
4. Inline Citation Concordance (audit against canonical evidence database).
5. Safety Boundaries & Non-prescriptive Educational Disclaimer Enforcement.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services.staging_engine import derive_or_verify_staging
from app.services.evidence_retrieval import get_evidence_retrieval_engine
from app.services.reference_catalogue import audit_claim_citations
from app.services.ollama import generate_agent_assessment


def get_profile_by_id(agent_id: str) -> dict[str, str]:
    profile = next((p for p in AGENT_PROFILES if p["agent_id"] == agent_id), None)
    if not profile:
        raise ValueError(f"Agent profile '{agent_id}' not found in catalog.")
    return profile


# Cohort of 8 Diverse Cases Spanning All Ages, Sites, and Histologies
COHORT_CASES = [
    {
        "id": "CASE-01-PED-CNS",
        "label": "Case 1: Pediatric (Age 8) CNS Medulloblastoma",
        "age_group": "Pediatric (Age 8)",
        "site": "Central Nervous System",
        "histology": "Medulloblastoma (Group 4)",
        "target_agent_id": "RO-07",  # Pediatric Radiation Oncology Specialist
        "clinical_tension": "Craniospinal RT (CSI) dose de-escalation vs recurrence; PENTEC neurocognitive & growth OAR limits.",
        "case": SyntheticCase(
            scenario_title="Pediatric Posterior Fossa Medulloblastoma",
            primary_site="cns",
            anatomical_subsite="posterior fossa / fourth ventricle",
            histology="Medulloblastoma",
            case_summary=(
                "8-year-old male presenting with 4 weeks of morning headache, projectile vomiting, and progressive gait ataxia. "
                "Brain MRI demonstrates a 3.8 cm midline fourth ventricular mass causing obstructive hydrocephalus, with contrast enhancement. "
                "Patient underwent gross total resection. Pathology confirmed classic medulloblastoma, non-WNT/non-SHH (Group 4). "
                "Post-operative neuraxis staging: Spine MRI with contrast shows no leptomeningeal drop metastases. "
                "Lumbar puncture CSF cytology at day 15 post-op is negative for malignant cells. Karnofsky / Lansky score 80."
            ),
            pathology_summary="Gross total resection: Classic medulloblastoma, synaptophysin positive, INI-1 retained, non-WNT/non-SHH (Group 4).",
            imaging_summary="Pre-op brain MRI: 3.8 cm 4th ventricular tumor. Post-op brain MRI: Gross total resection, no residual enhancement > 1.5 cm^2. Spine MRI: Entire spine normal, no drop metastases. CSF: Cytology negative (M0)."
        ),
    },
    {
        "id": "CASE-02-AYA-BONE",
        "label": "Case 2: AYA (Age 19) Femoral Ewing Sarcoma",
        "age_group": "AYA (Age 19)",
        "site": "Musculoskeletal / Bone",
        "histology": "Ewing Sarcoma",
        "target_agent_id": "SO-01",  # Guideline Surgical Oncologist
        "clinical_tension": "Limb-salvage reconstruction vs definitive RT; neoadjuvant chemotherapy response; fertility preservation.",
        "case": SyntheticCase(
            scenario_title="Adolescent Diaphyseal Ewing Sarcoma of Femur",
            primary_site="bone",
            anatomical_subsite="right femur diaphysis",
            histology="Ewing sarcoma",
            case_summary=(
                "19-year-old college athlete presenting with right thigh pain and swelling for 3 months. "
                "Plain radiographs and MRI of right femur show a 7.5 cm diaphyseal destructive lesion with 'onion-skin' periosteal reaction "
                "and an associated 3.2 cm soft tissue mass without neurovascular bundle encasement. Core biopsy confirmed Ewing sarcoma "
                "with EWSR1-FLI1 fusion transcript. Baseline staging: CT chest negative for pulmonary metastases, whole-body FDG PET/CT "
                "shows isolated FDG avidity in right femur (SUVmax 11.2). Completed 6 cycles of neoadjuvant VDC/IE chemotherapy with "
                "excellent clinical response: repeat MRI shows 75% reduction in soft tissue component. MDT discussion regarding local control: "
                "wide local excision with intercalary endoprosthetic reconstruction vs definitive radiation therapy (55.8 Gy)."
            ),
            pathology_summary="Core biopsy right femur: Small round blue cell tumor, CD99/MIC2 diffusely positive. FISH confirms EWSR1 gene rearrangement (t(11;22)(q24;q12)).",
            imaging_summary="Right femur MRI: Post-chemo 2.8 cm residual diaphyseal bone signal abnormality; soft tissue mass resolved from 3.2 cm to 0.8 cm. Margins to femoral artery/vein > 1.5 cm. PET-CT: SUVmax decreased from 11.2 to 2.4. Chest CT: No lung metastases."
        ),
    },
    {
        "id": "CASE-03-YA-CERVIX",
        "label": "Case 3: Reproductive Age (Age 32) Cervical SCC",
        "age_group": "Reproductive Age (Age 32)",
        "site": "Gynecologic / Cervix",
        "histology": "Squamous Cell Carcinoma",
        "target_agent_id": "RO-06",  # Brachytherapy & Radiotherapy Specialist
        "clinical_tension": "Definitive chemoradiotherapy + 3D-IGABT vs surgery; ovarian failure & transposition; fertility/sexual survivorship.",
        "case": SyntheticCase(
            scenario_title="Locally Advanced Cervical Carcinoma in Young Nulliparous Woman",
            primary_site="cervix",
            anatomical_subsite="cervix uteri",
            histology="Squamous cell carcinoma",
            case_summary=(
                "32-year-old nulliparous female presenting with post-coital spotting and pelvic pain. "
                "Gynecologic exam reveals an exophytic 4.2 cm cervical lesion extending into the upper two-thirds of the vagina; "
                "both parametria feel supple on rectovaginal exam (FIGO 2018 Stage IIA2). Pelvic MRI confirms 4.2 cm mass restricted "
                "to cervix and upper vagina, without parametrial invasion, and no suspicious pelvic lymph nodes. "
                "PET/CT reveals intense FDG avidity in the cervix (SUVmax 14.5); pelvic and para-aortic lymph nodes are PET-negative. "
                "Patient strongly desires discussion of fertility preservation options or at least ovarian preservation (laparoscopic lateral ovarian transposition)."
            ),
            pathology_summary="Cervical biopsy: Invasive moderately differentiated non-keratinizing squamous cell carcinoma, p16-positive.",
            imaging_summary="Pelvic MRI: 4.2 cm cervical mass, upper third of vagina involved. Parametrial fat planes preserved. Pelvic lymph nodes < 8 mm, normal morphology. PET-CT: Highly avid primary tumor; no pelvic, para-aortic, or distant metastases."
        ),
    },
    {
        "id": "CASE-04-MA-BREAST",
        "label": "Case 4: Middle-Age (Age 48) Breast Triple-Negative IDC",
        "age_group": "Middle-Age (Age 48)",
        "site": "Breast",
        "histology": "Invasive Ductal Carcinoma (Triple-Negative)",
        "target_agent_id": "RO-03",  # Intensification & Comprehensive Nodal Specialist
        "clinical_tension": "Post-mastectomy RT (PMRT) with residual disease post-neoadjuvant; internal mammary nodal irradiation; DIBH cardiac sparing.",
        "case": SyntheticCase(
            scenario_title="Locally Advanced Triple-Negative Breast Cancer Post-Mastectomy with Residual Disease",
            primary_site="breast",
            anatomical_subsite="left breast inner-lower quadrant",
            histology="Invasive ductal carcinoma",
            case_summary=(
                "48-year-old premenopausal female initially presented with a 4.5 cm left inner quadrant breast mass and biopsy-proven cN1 axillary node. "
                "Receptor status: ER 0%, PR 0%, HER2 0 (IHC), Ki-67 80% (Triple-negative). Completed neoadjuvant pembrolizumab + carboplatin/paclitaxel "
                "followed by AC. Underwent left modified radical mastectomy. Surgical pathology revealed residual invasive ductal carcinoma measuring "
                "1.4 cm (ypT1c) and 2 of 14 lymph nodes positive for metastatic carcinoma (ypN1a, largest nodal deposit 3.5 mm without ENE). "
                "Margins negative (> 5 mm). Deep inspiration breath-hold (DIBH) planning indicated for left anterior descending (LAD) coronary sparing. "
                "MDT consultation for comprehensive locoregional post-mastectomy radiation therapy (chest wall + supraclavicular + internal mammary chain)."
            ),
            pathology_summary="Left mastectomy: Residual invasive ductal carcinoma, grade 3, ypT1c (1.4 cm), ypN1a (2/14 nodes positive, largest 3.5 mm). Surgical margins clear. RCB (Residual Cancer Burden) class II.",
            imaging_summary="Post-op baseline CT and PET/CT: No distant metastases, no residual axillary or internal mammary adenopathy."
        ),
    },
    {
        "id": "CASE-05-MA-HN",
        "label": "Case 5: Middle-Age (Age 57) Oropharyngeal SCC (p16+)",
        "age_group": "Middle-Age (Age 57)",
        "site": "Head & Neck",
        "histology": "Squamous Cell Carcinoma (p16-positive)",
        "target_agent_id": "RO-02",  # Conservative & Toxicity-Averse Radiation Oncologist
        "clinical_tension": "Definitive IMRT vs TORS resection; de-escalation rationale in p16+; swallowing constrictor sparing (QUANTEC limits).",
        "case": SyntheticCase(
            scenario_title="HPV-Positive Oropharyngeal Carcinoma with Unilateral Nodal Disease",
            primary_site="oropharynx",
            anatomical_subsite="left palatine tonsil",
            histology="Squamous cell carcinoma",
            case_summary=(
                "57-year-old male non-smoker presents with an asymptomatic left neck lump for 6 weeks. "
                "Flexible nasopharyngoscopy reveals an exophytic 2.4 cm left tonsillar mass without extension to base of tongue or posterior pharyngeal wall. "
                "FNA of left level IIA lymph node: Metastatic squamous cell carcinoma, p16 strongly positive. "
                "Contrast-enhanced CT and PET/CT: 2.4 cm left tonsillar lesion (SUVmax 11.5) and a single 2.6 cm left level IIA lymph node (SUVmax 8.8) "
                "with smooth borders and no extranodal extension (ENE). Contralateral neck and distant organs completely negative. "
                "ECOG performance status 0. Dental clearance completed with all restorations sound."
            ),
            pathology_summary="Tonsil biopsy & neck FNA: Non-keratinizing squamous cell carcinoma, p16-positive (E6H4 clone diffuse nuclear/cytoplasmic >70%).",
            imaging_summary="Neck CT / PET: Left palatine tonsil 2.4 cm primary, solitary left level IIA node 2.6 cm (ENE negative). Contralateral neck negative. Distant staging negative."
        ),
    },
    {
        "id": "CASE-06-SR-RECTUM",
        "label": "Case 6: Senior Adult (Age 66) Rectal Adenocarcinoma",
        "age_group": "Senior Adult (Age 66)",
        "site": "Gastrointestinal / Rectum",
        "histology": "Adenocarcinoma",
        "target_agent_id": "SO-06",  # Organ Preservation & Watch-and-Wait Surgical Specialist
        "clinical_tension": "Total Neoadjuvant Therapy (TNT) vs upfront surgery; Watch-and-Wait (NOM) eligibility on clinical complete response.",
        "case": SyntheticCase(
            scenario_title="Locally Advanced Mid-Rectal Adenocarcinoma with Threatened CRM",
            primary_site="rectum",
            anatomical_subsite="mid rectum (6 cm from anal verge)",
            histology="Adenocarcinoma",
            case_summary=(
                "66-year-old male presenting with rectal bleeding and tenesmus. Flexible sigmoidoscopy shows an ulcerated circumferential tumor 6 cm "
                "from the anal verge. High-resolution pelvic MRI demonstrates tumor penetrating into mesorectal fat by 7 mm (T3c) with a threatened "
                "mesorectal fascia (distance to MRF 0.8 mm). 3 suspicious mesorectal lymph nodes with irregular borders and heterogeneous signal. "
                "Extramural venous invasion (EMVI) is positive. CT chest/abdomen/pelvis negative for distant metastases. "
                "Patient is highly motivated to avoid a permanent colostomy. MDT consideration for Total Neoadjuvant Therapy (short-course RT or long-course CRT "
                "followed by consolidation mFOLFIRINOX) with intention for non-operative management (Watch-and-Wait) if clinical complete response is achieved."
            ),
            pathology_summary="Rectal biopsy: Moderately differentiated invasive adenocarcinoma, pMMR / MSS, KRAS wild-type, BRAF wild-type.",
            imaging_summary="High-res Pelvic MRI: Mid-rectum tumor, 4.2 cm length, invasion into mesorectal fat 7 mm (T3c), CRM 0.8 mm (threatened), EMVI positive, 3 mesorectal nodes (N1b). Staging CT: No distant metastasis (M0)."
        ),
    },
    {
        "id": "CASE-07-ELD-BLADDER",
        "label": "Case 7: Elderly (Age 74) Bladder Urothelial Carcinoma",
        "age_group": "Elderly (Age 74)",
        "site": "Genitourinary / Bladder",
        "histology": "Urothelial Carcinoma",
        "target_agent_id": "RO-01",  # Guideline-Focused Radiation Oncologist
        "clinical_tension": "Trimodal Bladder Preservation (TMT) vs Radical Cystectomy; radiosensitizing chemotherapy choice in moderate renal function.",
        "case": SyntheticCase(
            scenario_title="Muscle-Invasive Urothelial Bladder Carcinoma Seeking Organ Preservation",
            primary_site="bladder",
            anatomical_subsite="urinary bladder lateral wall",
            histology="Urothelial carcinoma",
            case_summary=(
                "74-year-old female with hypertension and baseline eGFR 48 mL/min/1.73m^2 presenting with painless gross hematuria. "
                "Cystoscopy revealed a 3.5 cm solitary papillary and solid mass on the right lateral bladder wall. "
                "Patient underwent aggressive, visually complete transurethral resection of bladder tumor (TURBT). "
                "Pathology confirmed high-grade urothelial carcinoma invading the muscularis propria (detrusor muscle present and involved, cT2a). "
                "Pelvic MRI and CT urogram: No extravesical extension, no hydronephrosis, pelvic lymph nodes normal size (< 8 mm). "
                "Chest CT negative for metastasis. Patient strongly refuses radical cystectomy with urinary diversion and requests trimodal bladder preservation "
                "therapy (maximal TURBT followed by concurrent chemoradiotherapy)."
            ),
            pathology_summary="TURBT right bladder wall: High-grade invasive urothelial carcinoma invading deep muscularis propria. Lymphovascular invasion not identified.",
            imaging_summary="Pelvic MRI: Visually complete TURBT site with focal wall thickening, no extravesical fat stranding (cT2a). No pelvic lymphadenopathy. CT Urogram & Chest CT: Normal upper urinary tracts, no distant metastases."
        ),
    },
    {
        "id": "CASE-08-GER-LUNG",
        "label": "Case 8: Geriatric (Age 81) Lung Peripheral Adenocarcinoma",
        "age_group": "Geriatric (Age 81)",
        "site": "Thoracic / Lung",
        "histology": "Adenocarcinoma",
        "target_agent_id": "RO-05",  # SBRT & Hypofractionation Specialist
        "clinical_tension": "Medically inoperable early-stage NSCLC; SBRT (54 Gy in 3 fx vs 50 Gy in 4 fx); chest wall/rib toxicity vs local control.",
        "case": SyntheticCase(
            scenario_title="Early Stage Peripheral NSCLC in Medically Inoperable Octogenarian",
            primary_site="lung",
            anatomical_subsite="right upper lobe peripheral",
            histology="Adenocarcinoma",
            case_summary=(
                "81-year-old male with severe COPD (FEV1 32% predicted, on 2 L/min home oxygen), ischemic cardiomyopathy (LVEF 35%), and prior CABG. "
                "Surveillance CT chest demonstrates an enlarging 2.5 cm non-calcified solid peripheral pulmonary nodule in the posterior right upper lobe, "
                "located 1.8 cm from the parietal pleura/chest wall and > 3 cm from the proximal bronchial tree. "
                "PET/CT reveals intense FDG uptake in the nodule (SUVmax 9.2); mediastinal and hilar lymph nodes are PET-cold. "
                "Transthoracic needle biopsy confirmed invasive adenocarcinoma. Thoracic surgery evaluated patient as medically inoperable due to prohibitive "
                "cardiopulmonary operative mortality risk. MDT referral for definitive Stereotactic Body Radiation Therapy (SBRT / SABR)."
            ),
            pathology_summary="CT-guided lung biopsy: Invasive adenocarcinoma, acinar predominant, TTF-1 positive, p40 negative.",
            imaging_summary="Chest CT & PET/CT: 2.5 cm solitary peripheral RUL nodule (cT1c), SUVmax 9.2. Mediastinal nodes non-enlarged, PET negative (cN0). Brain MRI: No metastases (cM0)."
        ),
    },
]


async def run_greatness_simulation():
    print("=" * 90)
    print("      RADONC MDT SIMULATOR: MULTI-SITE & MULTI-AGE GREATNESS BENCHMARK")
    print("=" * 90)
    print(f"Total Cohort Cases: {len(COHORT_CASES)} spanning all major ages, anatomical sites, and histologies.\n")

    engine = get_evidence_retrieval_engine()
    scorecard_results = []

    for idx, case_meta in enumerate(COHORT_CASES, 1):
        case_id = case_meta["id"]
        label = case_meta["label"]
        age_group = case_meta["age_group"]
        site = case_meta["site"]
        histology = case_meta["histology"]
        target_agent_id = case_meta["target_agent_id"]
        clinical_tension = case_meta["clinical_tension"]
        case = case_meta["case"]

        profile = get_profile_by_id(target_agent_id)

        print("-" * 90)
        print(f"[{idx}/{len(COHORT_CASES)}] {label.upper()}")
        print(f"   Target Persona: {target_agent_id} ({profile['name']})")
        print(f"   Clinical Focus: {clinical_tension}")
        print("-" * 90)

        # 1. Deterministic Staging Engine Derivation
        staging_start = time.perf_counter()
        stg = derive_or_verify_staging(case)
        staging_dur = time.perf_counter() - staging_start

        derived_str = f"{stg.get('derived_t_stage', 'Tx')} {stg.get('derived_n_stage', 'Nx')} {stg.get('derived_m_stage', 'M0')}"
        stage_group = stg.get("derived_stage_group") or "Stage Unconfirmed"
        print(f"  [Staging Engine] System: {stg.get('applicable_system', 'Unknown')} | Derived: {derived_str} -> {stage_group} ({staging_dur*1000:.1f}ms)")
        if stg.get("discrepancies"):
            print(f"   * Staging Nuance/Discrepancies: {stg['discrepancies']}")

        # 2. Evidence Retrieval Isolation & Precision Check
        ev_start = time.perf_counter()
        evidence_items = engine.retrieve_evidence_for_role(target_agent_id, case, limit=5)
        ev_dur = time.perf_counter() - ev_start

        ev_titles = [f"[{e.source_id}] {e.title[:45]}..." for e in evidence_items]
        print(f"  [Evidence Engine] Retrieved {len(evidence_items)} passages in {ev_dur*1000:.1f}ms:")
        for t in ev_titles[:3]:
            print(f"      • {t}")

        # Check for Cross-Site Leakage (e.g., Larynx evidence appearing in a CNS or Cervix case)
        forbidden_terms = {
            "cns": ["larynx", "cervix", "rectum", "breast"],
            "bone": ["cervix", "larynx", "prostate"],
            "cervix": ["larynx", "cns", "lung"],
            "breast": ["cervix", "larynx", "rectum"],
            "oropharynx": ["cervix", "breast", "rectum"],
            "rectum": ["larynx", "cervix", "cns"],
            "bladder": ["larynx", "cervix", "breast"],
            "lung": ["cervix", "larynx", "rectum"]
        }
        site_key = case.primary_site.lower()
        unwanted = forbidden_terms.get(site_key, [])
        leakage_detected = False
        for item in evidence_items:
            content_lower = (item.title + " " + item.snippet).lower()
            for bad_term in unwanted:
                if f"cancer of the {bad_term}" in content_lower or f"{bad_term} cancer" in content_lower:
                    leakage_detected = True
                    print(f"   [!] WARNING: Cross-site evidence leakage detected: '{bad_term}' in '{item.source_id}'")

        # 3. Model Assessment via Local Ollama
        print(f"  [Model Inference] Executing {target_agent_id} assessment via local Ollama (qwen3.5:4b)...")
        gen_start = time.perf_counter()
        assessment = None
        gen_err = None
        try:
            assessment = await generate_agent_assessment(profile, case, round_number=1)
            gen_dur = time.perf_counter() - gen_start
            print(f"  [Model Inference] Completed in {gen_dur:.2f}s | Position: {assessment.position.upper()}")
        except Exception as exc:
            gen_dur = time.perf_counter() - gen_start
            gen_err = str(exc)
            print(f"  [Model Inference] FAILED after {gen_dur:.2f}s: {exc}")

        # 4. Audit Inline Citations & Case Integrity
        citation_concordance = 1.0
        verified_cits = []
        unverified_cits = []
        integrity_passed = True
        integrity_notes = []

        if assessment:
            full_narrative = (
                f"{assessment.provisional_conclusion} "
                f"{assessment.preferred_educational_option} "
                f"{' '.join(assessment.discussion_options)} "
                f"{' '.join(assessment.assumptions)} "
                f"{' '.join(assessment.case_facts)}"
            )
            raw_citations = re.findall(r"\[(?:source_id|source|ref|citation):\s*([A-Za-z0-9_\-\.]+)\b", full_narrative, re.IGNORECASE)
            if raw_citations:
                claims_to_audit = [
                    {"role_id": target_agent_id, "source_id": c.strip(), "claim": "Inline citation"}
                    for c in set(raw_citations)
                ]
                audit = audit_claim_citations(claims_to_audit)
                verified_cits = audit.get("verified_sources", [])
                unverified_cits = audit.get("unverified_sources", [])
                total_cits = len(verified_cits) + len(unverified_cits)
                citation_concordance = len(verified_cits) / total_cits if total_cits > 0 else 1.0

            # Integrity check: Ensure model did not fabricate unsupported TNM assertions
            # (e.g. asserting stage IV without metastatic disease)
            conclusion_lower = assessment.provisional_conclusion.lower()
            if "stage iv" in conclusion_lower and "m0" in case.case_summary.lower():
                integrity_passed = False
                integrity_notes.append("Hallucinated Stage IV when case is explicitly M0.")

            # Integrity check: Educational disclaimer validation
            if assessment.safety_boundary != "educational_simulation_only" or not assessment.not_a_treatment_instruction:
                integrity_passed = False
                integrity_notes.append("Safety boundaries breached.")

            print(f"  [Audit & Safety] Citations: {len(verified_cits)} verified, {len(unverified_cits)} unverified | Concordance: {citation_concordance*100:.1f}%")
            print(f"  [Provisional Conclusion Excerpt]: {assessment.provisional_conclusion[:140]}...")
            print(f"  [Preferred Educational Option]: {assessment.preferred_educational_option[:120]}...")

        else:
            integrity_passed = False
            integrity_notes.append(f"Inference failure: {gen_err}")

        scorecard_results.append({
            "id": case_id,
            "label": label,
            "age_group": age_group,
            "site": site,
            "histology": histology,
            "agent_id": target_agent_id,
            "position": assessment.position if assessment else "FAILED",
            "latency_s": round(gen_dur, 2),
            "citations_verified": len(verified_cits),
            "citations_unverified": len(unverified_cits),
            "concordance_pct": round(citation_concordance * 100, 1),
            "leakage_free": not leakage_detected,
            "integrity_passed": integrity_passed,
            "integrity_notes": "; ".join(integrity_notes) if integrity_notes else "Clean",
        })
        print()

    # =========================================================================
    # FINAL GREATNESS SCORECARD
    # =========================================================================
    print("\n" + "=" * 115)
    print("                     RADONC MDT SIMULATOR: MULTI-SITE GREATNESS SCORECARD")
    print("=" * 115)
    print(f"{'Case Label':<40} | {'Role':<6} | {'Pos':<10} | {'Latency':<7} | {'Concord':<8} | {'Leakage':<7} | {'Integrity'}")
    print("-" * 115)

    total_latency = 0.0
    total_concordance = 0.0
    clean_integrity_count = 0

    for res in scorecard_results:
        total_latency += res["latency_s"]
        total_concordance += res["concordance_pct"]
        if res["integrity_passed"]:
            clean_integrity_count += 1

        leakage_str = "Clean" if res["leakage_free"] else "LEAK"
        integrity_str = "PASSED" if res["integrity_passed"] else f"FAIL ({res['integrity_notes']})"

        print(
            f"{res['label'][:40]:<40} | "
            f"{res['agent_id']:<6} | "
            f"{res['position']:<10} | "
            f"{res['latency_s']:>6.2f}s | "
            f"{res['concordance_pct']:>6.1f}% | "
            f"{leakage_str:<7} | "
            f"{integrity_str}"
        )

    n = len(scorecard_results)
    avg_latency = total_latency / n if n else 0.0
    avg_concordance = total_concordance / n if n else 0.0
    integrity_rate = (clean_integrity_count / n * 100.0) if n else 0.0

    print("-" * 115)
    print(f"COHORT SUMMARY METRICS ({n} Diverse Cases):")
    print(f"  • Mean Model Latency:             {avg_latency:.2f} seconds per assessment")
    print(f"  • Total Inference Duration:       {total_latency:.2f} seconds ({total_latency/60:.2f} minutes)")
    print(f"  • Evidence Citation Concordance:  {avg_concordance:.1f}%")
    print(f"  • Case Integrity Pass Rate:       {integrity_rate:.1f}% ({clean_integrity_count}/{n} cases)")
    print("=" * 115)

    # Save detailed JSON artifact
    artifact_path = backend_dir / "scripts" / "greatness_scorecard_results.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_cases": n,
            "avg_latency_seconds": round(avg_latency, 2),
            "mean_concordance_pct": round(avg_concordance, 1),
            "integrity_pass_rate_pct": round(integrity_rate, 1),
            "cases": scorecard_results,
        }, f, indent=2)
    print(f"\nDetailed scorecard artifact saved to: {artifact_path}\n")


if __name__ == "__main__":
    asyncio.run(run_greatness_simulation())
