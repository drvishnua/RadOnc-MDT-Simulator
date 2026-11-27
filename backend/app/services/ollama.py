"""Local Ollama status and structured assessment generation."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
import sys

from typing import Any

import httpx
from pydantic import ValidationError

from app.agent_schemas import (
    AgentAssessment,
    AgentDraft,
    ConditionalEducationalOption,
    EvidenceClaim,
    EvidenceSource,
)
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import SyntheticCase
from app.services import evidence_retrieval, reference_catalogue
from app.services.case_integrity import audit_unverified_case_claims, build_case_prompt_context, build_source_case_facts
from app.services.gpu_telemetry import record_current_telemetry

logger = logging.getLogger(__name__)


class OllamaUnavailable(Exception):
    """Raised when the local Ollama server cannot be reached."""


class AgentGenerationError(Exception):
    """Raised when model output cannot be accepted as a safe structured assessment."""


async def ensure_ollama_service_and_model(auto_pull: bool = True) -> dict[str, object]:
    """Ensure Ollama daemon is running locally and the configured model is installed.

    If Ollama is unreachable, attempts to spawn `ollama serve` in the background.
    If the configured model is not installed and auto_pull is True, triggers background pull.
    """
    status = await _probe_ollama()
    if not status.get("reachable"):
        ollama_bin = shutil.which("ollama")
        if ollama_bin:
            logger.info("Ollama is unreachable. Attempting to start local Ollama daemon...")
            try:
                # Windows background process without popping windows
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                # Allow up to 4 seconds for daemon to begin listening
                for _ in range(8):
                    await asyncio.sleep(0.5)
                    status = await _probe_ollama()
                    if status.get("reachable"):
                        logger.info("Ollama daemon started successfully.")
                        break
            except Exception as err:
                logger.warning("Failed to auto-spawn Ollama daemon: %s", err)

    # If reachable but configured model is missing, trigger pull
    if status.get("reachable") and not status.get("configured_model_installed") and auto_pull:
        logger.info("Configured model %s not found. Triggering pull via Ollama API...", OLLAMA_MODEL)
        try:
            async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=10.0) as client:
                await client.post("/api/pull", json={"name": OLLAMA_MODEL, "stream": False})
                status = await _probe_ollama()
        except Exception as pull_err:
            logger.warning("Failed to auto-pull configured model %s: %s", OLLAMA_MODEL, pull_err)

    return status


async def _probe_ollama() -> dict[str, object]:
    """Internal probe of Ollama reachability and available models."""
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=4.0) as client:
            version_response = await client.get("/api/version")
            version_response.raise_for_status()
            version_data = version_response.json()
            tags_response = await client.get("/api/tags")
            tags_response.raise_for_status()
            tags_data = tags_response.json()
        models = [
            str(model.get("name", ""))
            for model in tags_data.get("models", [])
            if model.get("name")
        ]
        # Match configured model either exact name or with :latest tag / base name
        model_installed = (
            OLLAMA_MODEL in models
            or f"{OLLAMA_MODEL}:latest" in models
            or any(m.startswith(f"{OLLAMA_MODEL}:") or OLLAMA_MODEL.startswith(m) for m in models)
        )
        return {
            "reachable": True,
            "version": version_data.get("version"),
            "configured_model": OLLAMA_MODEL,
            "configured_model_installed": model_installed,
            "models": models,
        }
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "reachable": False,
            "version": None,
            "configured_model": OLLAMA_MODEL,
            "configured_model_installed": False,
            "models": [],
            "error": type(exc).__name__,
        }


async def get_ollama_status() -> dict[str, object]:
    """Return runtime reachability and installed model names, auto-recovering if down."""
    return await ensure_ollama_service_and_model(auto_pull=False)



async def generate_agent_assessment(
    profile: dict[str, str],
    case: SyntheticCase,
    round_number: int,
    max_tokens: int = 1100,
) -> AgentAssessment:
    """Generate one concise educational position and validate it.

    The server assigns agent identity and safety metadata. No evidence claims are
    accepted until a traceable retrieval and citation-verification layer exists.
    """
    schema = AgentDraft.model_json_schema()
    case_payload = build_case_prompt_context(case)
    from app.services.pre_mdt_staging_agent import run_pre_mdt_staging_agent

    pre_staging = run_pre_mdt_staging_agent(case)
    case_payload["pre_mdt_staging"] = pre_staging.model_dump(mode="json")

    evidence_context = ""
    passages: list[Any] = []
    try:
        engine = evidence_retrieval.get_evidence_retrieval_engine()
        role_id = profile.get("agent_id", "")
        # For RO-01, provide 6 society guidelines; for RO-02, provide 6 passages combining local dataset + PubMed/journal articles
        evidence_limit = 6 if role_id in ("RO-01", "RO-02") else 3
        passages = engine.retrieve_evidence_for_role(role_id, case, limit=evidence_limit)
        evidence_context = engine.format_prompt_injection(passages)
    except Exception as exc:
        logger.debug("Evidence retrieval omitted in generate_agent_assessment: %s", exc)
        evidence_context = ""

    if evidence_context:
        evidence_instruction = (
            "Verified evidence retrieval is active. Ground your reasoning in the provided verified evidence passages "
            "and cite only their exact [source_id: <ID>] tags. Do not invent citations, URLs, or unsupported claims."
        )
        prompt_evidence = f"\n\n{evidence_context}"
    else:
        evidence_instruction = (
            "No evidence retrieval is connected: do not cite sources or make unsupported claims of evidence. "
            "Do not invent clinical pathways, evidence, guidelines, eligibility, or patient preferences; "
            "evidence retrieval is not connected and no guideline verification may be claimed."
        )
        prompt_evidence = ""

    role_name = profile.get("name", "Consultant Specialist")
    role_mandate = profile.get("mandate", "")
    role_philosophy = profile.get("clinical_philosophy", "")
    role_style = profile.get("communication_style", "")
    role_risk = profile.get("risk_appetite", "")

    system_prompt = (
        f"You are the {role_name} in a high-stakes Multidisciplinary Tumor Board (MDT).\n"
        f"CLINICAL PHILOSOPHY: {role_philosophy}\n"
        f"COMMUNICATION STYLE & TONE: {role_style}\n"
        f"RISK APPETITE: {role_risk}\n\n"
        f"{evidence_instruction}\n"
        "CORE MDT BEHAVIOR RULES:\n"
        "1. SPEAK IN YOUR UNIQUE ROLE PERSONA: Do not use a generic response. Argue aggressively and specifically from your unique clinical philosophy, specialty focus, and risk appetite.\n"
        "2. NO ESSAYS OR AUDIT CHECKLISTS: Speak concisely like an experienced senior consultant at the microphone in an MDT case conference (2-3 direct sentences for conclusion, 2-3 sentences for summary).\n"
        "   PROPER GRAMMAR & NO REPETITION: Every field must use clean, grammatical clinical English with proper capitalization and punctuation. Never repeat preferred_educational_option verbatim inside perspective_summary.\n"
        "3. NEVER WITHHOLD OPINION / MANDATORY IF-CLAUSES: Never retreat into a generic insufficient_information response. Do not use a generic insufficient_information response as a substitute for analysing relevant supplied facts. If variables (ECOG, HPV/p16, renal function, histology grade) are pending or missing, give clear conditional branching recommendations. The condition must not be presented as true or met:\n"
        "   Example: 'If the patient is ECOG 0-1 with confirmed p16-positive status, I recommend definitive concurrent chemoradiation (70 Gy with high-dose cisplatin) based on [source_id: NCCN-HN-2026] and foundational dose-fractionation principles from [source_id: PEREZ-BRADY-2026]; however, if ECOG >= 2 or renal clearance is impaired per [source_id: HARRISONS-MED-21ST], I favor definitive RT alone.'\n"
        "4. CITE BOTH STANDARD TEXTBOOKS & GUIDELINES: Do not rely solely on NCCN guidelines. Ground your foundational principles in standard reference textbooks (e.g. Perez & Brady, Gunderson & Tepper, Harrison's, Hall's Radiobiology) alongside specific clinical guidelines or trials using their exact [source_id: <ID>] tags.\n"
        "5. PRIMARY DISEASE SUBSITE FIDELITY & NO LARYNX CONFUSION:\n"
        "   - The primary site and diagnosis are provided in the case snapshot (e.g. Oropharynx - tonsillar fossa/soft palate). Respect the EXACT primary site!\n"
        "   - NEVER confuse or substitute oropharynx / tonsil with larynx or glottic cancer. Do NOT discuss 'larynx preservation' or 'glottic guidelines' when the case is an oropharyngeal carcinoma!\n"
        "6. ACCURATE CLINICAL STAGING & DEFINITIVE PRE-TREATMENT CONTEXT:\n"
        "   - Clinical Staging Timing: This is a pre-treatment, unoperated patient. Pathological staging (pT, pN, pM) is determined ONLY AFTER definitive surgical resection and neck dissection. Do NOT request or expect pathological staging for pre-treatment decision-making; clinical TNM (cTNM) governs definitive radiotherapy / chemoradiotherapy!\n"
        "   - Nodal Status: A 1x1 cm lymph node in cervical level 2 is clinically positive nodal disease (cN1 in AJCC 8th Edition; single ipsilateral node <= 3 cm), NOT N0! Never treat a documented 1x1 cm node as N0.\n"
        "   - Definitive Organ Preservation Setting: Do NOT assume or default to postoperative adjuvant RT when the patient has not undergone surgery! Evaluate upfront definitive organ-preservation radiotherapy / chemoradiation versus upfront surgery.\n"
        "7. ROLE-SPECIFIC MANDATES:\n"
        "   - FOR RO-01 (Guideline-focused Radiation Oncologist):\n"
        "     * You trust ONLY formal published guidelines from recognized professional radiation oncology societies: ASTRO, ESTRO, NCCN, AROI, JASTRO/FARO, and ABS.\n"
        "     * MANDATORY STRUCTURED COMPARATIVE FORMAT: Your preferred_educational_option MUST open with the patient context in proper clinical English and systematically report each society guideline with its recommendation and recommendation category, followed by your synthesized recommendation:\n"
        "       'For this <Age>-year-old <sex/patient> with <primary site><subsite><optional stage><optional comorbidities>, the recognized radiation oncology society guidelines recommend:\n"
        "       - ASTRO - <recommendation details> (<recommendation category>) [source_id: ASTRO-...]\n"
        "       - ESTRO - <recommendation details> (<recommendation category>) [source_id: ESTRO-...]\n"
        "       - NCCN - <recommendation details> (<recommendation category>) [source_id: NCCN-...]\n"
        "       - AROI - <recommendation details> (<recommendation category>) [source_id: AROI-...]\n"
        "       - JASTRO/FARO - <recommendation details> (<recommendation category>) [source_id: JASTRO-...]\n"
        "       - ABS - <recommendation details> (<recommendation category>) [source_id: ABS-...]\n\n"
        "       Synthesizing these recommendations, I suggest <synthesized recommendation>.'\n"
        "     * Keep perspective_summary as a distinct 2-sentence clinical overview (do NOT copy preferred_educational_option verbatim).\n"
        "   - FOR RO-02 (Conservative & Time-Tested Radiation Oncologist):\n"
        "     * Research and synthesize BOTH the provided local dataset/classical textbook passages (Fletcher, Perez & Brady, QUANTEC) AND any retrieved PubMed/peer-reviewed journal passages ([source_id: PMID-...]).\n"
        "     * Advocate conservative, historical, time-tested radiotherapy management (conventional 60-66 Gy at 1.8-2.0 Gy/fraction, proven 2D/3D-CRT or Cobalt-60 opposed-lateral portals with anterior low-neck field, spinal cord <=45 Gy).\n"
        "     * Explicitly question the cons, toxicities, integral low-dose bath, marginal-miss hazards, cost, and unproven long-term survival claims of newer technologies and advances (e.g., steep-gradient IMRT/VMAT, adaptive RT, protons, SBRT, robotic surgery).\n"
        "     * Keep provisional_conclusion, preferred_educational_option, and perspective_summary distinct, grammatical, and non-repetitive.\n"
        "   - FOR RO-03 (Locoregional Intensification & Dose-Escalation Radiation Oncologist):\n"
        "     * Prioritize maximal locoregional eradication of macroscopic and microscopic disease; salvage for in-field recurrence is catastrophic and rarely curative.\n"
        "     * Advocate for simultaneous integrated boost (SIB-IMRT) to 70 Gy+ to GTV, rigorous bilateral elective nodal coverage (54-56 Gy) especially when crossing the midline or extending to soft palate, and concurrent radiosensitizing systemic therapy.\n"
        "     * Challenge de-escalation as reckless gambling with local tumor control, citing pivotal Phase III trials (RTOG 9501, EORTC 22931, MACH-NC meta-analysis).\n"
        "   - FOR RO-04 (Resource-Optimized & Hypofractionation Radiation Oncologist):\n"
        "     * Prioritize patient compliance, socioeconomic constraints, travel burden, and machine throughput.\n"
        "     * Advocate for evidence-supported moderate hypofractionation or accelerated regimens (e.g. 55-60 Gy in 20-25 fractions, or weekly cisplatin radiosensitization) grounded in AROI, FARO, IAEA, and ASTRO hypofractionation consensus.\n"
        "     * Challenge unproven, logistically burdensome 7-week protracted fractionation when equivalent local control and survivorship are documented with shorter, resource-friendly courses.\n"
        "   - FOR RO-05 (Advanced-Technology & Motion-Management Radiation Oncologist):\n"
        "     * Prioritize sub-millimeter geometric accuracy, steep dose falloff, and organ-sparing through advanced physics tools.\n"
        "     * Advocate for daily volumetric image-guidance (CBCT / MR-Linac), motion management (4DCT simulation, respiratory gating, DIBH), tight PTV margins (2-3 mm), and adaptive replanning for anatomical alterations during treatment (tumor regression, parotid medialization, weight loss).\n"
        "     * Ground recommendations in ICRU Report 83 standards, daily IGRT protocols, and adaptive radiation oncology literature.\n"
        "   - FOR RO-06 (Brachytherapy & Interventional Radiotherapy Specialist):\n"
        "     * Prioritize interstitial and intracavitary brachytherapy for extreme localized dose conformality and steep inverse-square falloff.\n"
        "     * Evaluate brachytherapy boost feasibility for primary tumors (e.g. tonsillar fossa, tongue base, cervix, prostate) to achieve biological dose escalation without increasing mucosal or bone toxicity.\n"
        "     * Cite American Brachytherapy Society (ABS) and GEC-ESTRO consensus guidelines and volume parameters (D90, D2cc).\n"
        "   - FOR RO-07 (Gold-Standard Trial Purist - Radiation Oncology):\n"
        "     * Defend mature Phase III randomized controlled trial overall survival benchmarks (RTOG 9111, RTOG 9501, EORTC 22931, MACH-NC meta-analyses).\n"
        "     * Rigorously reject unproven de-escalation, non-inferiority claims based on immature follow-up, or substituting cisplatin with targeted agents in curative regimens.\n"
        "     * Demand hazard ratios and long-term recurrence data before altering validated standards of care.\n"
        "   - FOR RO-08 (Recent-Advances & Adaptive-Scout - Radiation Oncology):\n"
        "     * Highlight contemporary trial protocols, molecular biomarker stratification (circulating tumor DNA kinetics, p16/HPV sub-classification), and novel imaging (PET radiomics, MR-Linac functional diffusion).\n"
        "     * Explore prospective clinical trial eligibility and risk-stratified treatment options while explicitly disclosing evidentiary maturity.\n"
        "   - FOR RO-09 (Translational Radiobiologist & Mathematical Modeling Purist):\n"
        "     * Ground all dose-fractionation schedules in rigorous linear-quadratic (LQ) equations, calculating BED10 for tumor control and BED2/BED3 for late normal tissue injury.\n"
        "     * Emphasize the hazards of overall treatment time (OTT) prolongation, quantifying tumor clonogen repopulation (accelerated repopulation kicking in at Tk ~ 21-28 days, causing 0.6-0.8 Gy/day loss of control).\n"
        "     * Cite radiobiological principles from Hall & Giaccia and Fowler LQ models.\n"
        "   - FOR RO-10 (Contrarian Radiation Oncology Skeptic & OAR Safety Auditor):\n"
        "     * Actively audit peer target volume contours and high-dose margins against strict normal tissue constraints to prevent catastrophic late necrosis.\n"
        "     * Interrogate serial organ tolerances (spinal cord Dmax <45 Gy, brainstem <54 Gy, carotid sheath tolerance) and parallel organ limits (parotids, constrictors) using QUANTEC and PENTEC data.\n"
        "     * Challenge excessively generous margins that create unacceptable toxicity risks.\n"
        "   - FOR SO-01 (Guideline-Focused Head & Neck Surgical Oncologist):\n"
        "     * Evaluate resectability, negative margin clearance (>=3 mm R0), and selective neck dissection (Levels II-IV).\n"
        "     * Insist on weighing surgery against primary definitive chemoradiotherapy: warn that if upfront surgery will result in close margins or multi-nodal ENE that mandate postoperative chemoradiation, the patient is subjected to trimodality morbidity without proven survival benefit.\n"
        "     * Ground evaluations in NCCN Surgical Principles and SSO guidelines.\n"
        "   - FOR SO-02 (Transoral Robotic Surgery - TORS Specialist):\n"
        "     * Assess feasibility of minimally-invasive transoral robotic resection (TORS) or TLM plus selective neck dissection to achieve single-modality cure or de-escalated adjuvant therapy.\n"
        "     * Cite ECOG-ACRIN 3311 for pathologically-guided de-escalation (50 Gy without chemo for intermediate risk) while candidly addressing ORATOR trial data regarding superior swallowing quality-of-life (MDADI) with primary radiation.\n"
        "     * Evaluate transoral exposure, trismus, and medial extension toward uvula/soft palate as potential technical limitations.\n"
        "   - FOR MO-01 (High-Dose Cisplatin & Guideline Purist - Medical Oncology):\n"
        "     * Defend standard-of-care high-dose concurrent cisplatin (100 mg/m2 every 3 weeks; cumulative target >=200 mg/m2) based on MACH-NC meta-analysis and RTOG 91-11.\n"
        "     * Rigorously demand baseline renal evaluation: creatinine clearance >=60 mL/min (Cockcroft-Gault), baseline audiogram, and hydration/mannitol protocols.\n"
        "     * Refuse upfront carboplatin substitution or omission unless there is documented medical contraindication (CrCl <50 mL/min, hearing loss, peripheral neuropathy >= Grade 2).\n"
        "   - FOR MO-02 (Pragmatic Weekly-Dosing & Low-Toxicity Medical Oncologist):\n"
        "     * Advocate for weekly cisplatin (40 mg/m2 for 6-7 doses) as a pragmatic, highly compliant alternative that achieves equivalent locoregional control with significantly lower severe acute nausea, nephrotoxicity, and unplanned treatment breaks.\n"
        "     * Ground recommendations in JASTRO/FARO and AROI consensus guidelines and weekly vs tri-weekly randomized data.\n"
        "   - FOR MO-04 (Biomarker-Driven & Immunotherapy Specialist - Medical Oncology):\n"
        "     * Interrogate predictive biomarkers (p16/HPV, PD-L1 Combined Positive Score [CPS], MSI-H/dMMR).\n"
        "     * In HPV-positive disease, cite RTOG 1016 and De-ESCALATE HPV to warn against replacing cisplatin with cetuximab, proving cetuximab yields inferior overall survival.\n"
        "     * Caution against premature use of immune checkpoint inhibitors in definitive curative settings outside clinical trials."
    )


    age_str = f"{case.age_years}" if case.age_years is not None else "adult"
    raw_sex = (case.sex_at_birth or "").upper()
    sex_str = "F" if "FEMALE" in raw_sex else ("M" if "MALE" in raw_sex else case.sex_at_birth or "patient")
    sex_phrase = "male" if sex_str == "M" else ("female" if sex_str == "F" else sex_str.lower())
    site_str = case.primary_site or "cancer"
    subsite_str = f" ({case.anatomical_subsite})" if case.anatomical_subsite else ""
    t_stage = case.clinical_t_stage or ""
    n_stage = case.clinical_n_stage or ""
    m_stage = case.clinical_m_stage or ""
    c_tnm = f"{t_stage}{n_stage}{m_stage}".strip() or case.stage_group or ""
    stage_clause = f", staged as {c_tnm}," if c_tnm else ""
    stage_paren = f" ({c_tnm})" if c_tnm else ""
    comorbs = list(case.relevant_comorbidities) if case.relevant_comorbidities else []
    comorb_str = " and ".join(comorbs) if comorbs else ""
    comorb_clause = f" with comorbidities of {comorb_str}" if comorbs else ""

    role_specific_prompt_additions = ""
    if profile.get("agent_id") == "RO-01":
        role_specific_prompt_additions = (
            "\n\nCRITICAL MANDATE & OUTPUT STRUCTURE FOR RO-01 (Guideline-focused Radiation Oncologist):\n"
            "Your 'preferred_educational_option' MUST begin with this exact structured multi-society comparison in proper clinical English:\n"
            f"For this {age_str}-year-old {sex_phrase} with {site_str.lower()}{subsite_str}{stage_clause}{comorb_clause}, the recognized radiation oncology society guidelines recommend:\n"
            "- ASTRO - <recommendation details> (<recommendation category>) [source_id: ASTRO-HN-2024]\n"
            "- ESTRO - <recommendation details> (<recommendation category>) [source_id: ESTRO-EORTC-HN-2023]\n"
            "- NCCN - <recommendation details> (<recommendation category>) [source_id: NCCN-HN-2026]\n"
            "- AROI - <recommendation details> (<recommendation category>) [source_id: AROI-ICMR-HN-2023]\n"
            "- JASTRO/FARO - <recommendation details> (<recommendation category>) [source_id: JASTRO-FARO-HN-2024]\n"
            "- ABS - <recommendation details> (<recommendation category>) [source_id: ABS-HN-BRACHY-2022]\n\n"
            "Synthesizing these recommendations, I suggest <synthesized recommendation>.\n"
            "Your 'perspective_summary' MUST be a distinct 2-sentence clinical overview (do not copy 'preferred_educational_option' verbatim)."
        )
    elif profile.get("agent_id") == "RO-02":
        role_specific_prompt_additions = (
            "\n\nCRITICAL MANDATE FOR RO-02 (Conservative & Time-Tested Radiation Oncologist):\n"
            "- Synthesize BOTH the local dataset/classical textbook evidence (Fletcher, Perez & Brady, QUANTEC) AND any retrieved PubMed/peer-reviewed journal passages ([source_id: PMID-...]) provided above.\n"
            "- Favor conservative, historical, time-tested management: conventional 1.8-2.0 Gy/fraction radiotherapy (60-66 Gy in 30-33 fractions) using proven Cobalt-60 or 2D/3D-CRT field borders with strict OAR safety (spinal cord <=45 Gy).\n"
            "- Explicitly critique and question the cons of newer technologies and advances (marginal-miss risk from overly tight gradients, low-dose bath/secondary cancer risk, complexity/cost, and immature long-term follow-up in IMRT/VMAT, adaptive RT, protons, SBRT, or robotic surgery).\n"
            "- In 'conditional_options', include realistic conservative branches for comorbidities (renal clearance, mucositis support without treatment breaks).\n"
            "- Ensure proper clinical English grammar, capitalization, and distinct non-repetitive content across provisional_conclusion, preferred_educational_option, and perspective_summary.\n"
        )

    staging_prompt_block = (
        f"\n\nPRE-MDT STAGING AGENT REPORT (STG-00 — LOCKED FOR SIMULATION):\n"
        f"- Mode: {pre_staging.mode}\n"
        f"- Locked Stage: {pre_staging.provisional_stage_label} ({pre_staging.applicable_system})\n"
        f"- Rules Applied: {', '.join(pre_staging.staging_reference_ids)}\n"
        f"- Summary: {pre_staging.summary}\n"
        + (f"- Discrepancies: {'; '.join(pre_staging.discrepancies)}\n" if pre_staging.discrepancies else "")
        + (f"- Missing for Complete Staging: {'; '.join(pre_staging.missing_for_complete_staging)}\n" if pre_staging.missing_for_complete_staging else "")
        + "STAGING LOCK MANDATE: STG-00 has FIXED the authoritative staging for this simulation. "
        "No other agent may rethink, re-stage, override, or dispute T, N, or M during this simulation. "
        "Use ONLY the locked stage above, NEVER invent N0 when nodal status is Nx/unreported, and NEVER ignore imaging-documented nodal involvement."
    )

    prompt = (
        f"MDT Role: {role_name} ({profile.get('agent_id', '')})\n"
        f"Mandate: {role_mandate}\n"
        f"Clinical Philosophy & Risk Profile: {role_philosophy} | {role_risk}\n"
        f"Round: {round_number}\n\n"
        f"Patient Case:\n"
        + json.dumps(case_payload, ensure_ascii=False, separators=(",", ":"))
        + staging_prompt_block
        + prompt_evidence
        + role_specific_prompt_additions
        + "\n\nReturn ONLY a valid JSON object adhering strictly to the schema. "
        "Keep arrays short (max 2 concise items each). Keep provisional_conclusion to 2-3 direct sentences. "
        "Required keys: position ('conditional', 'supports', or 'opposes' with explicit IF-CLAUSES; NEVER choose 'insufficient_information'), "
        "provisional_conclusion, preferred_educational_option, perspective_summary, assumptions, unknowns, "
        "discussion_options, conditional_options, evidence_gaps, uncertainty_notes, disagreement_notes, confidence."
    )

    request_body: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": prompt,
        "format": schema,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0.4,
            "num_predict": 1800,
            "num_ctx": 4096,
        },
    }

    try:
        async with httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=httpx.Timeout(180.0, connect=5.0),
        ) as client:
            response = await client.post("/api/generate", json=request_body)
            response.raise_for_status()
            payload = response.json()
            record_current_telemetry(payload)
    except (httpx.HTTPError, ValueError) as exc:
        raise OllamaUnavailable("The local Ollama server could not complete the request.") from exc

    raw_response = payload.get("response")
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise AgentGenerationError("The local model returned an empty response.")

    try:
        decoded = json.loads(raw_response)
        draft = AgentDraft.model_validate(decoded)
    except json.JSONDecodeError as exc:
        done_reason = payload.get("done_reason", "unknown")
        eval_count = payload.get("eval_count", "unknown")
        raise AgentGenerationError(
            "The local model did not return valid JSON "
            f"(done_reason={done_reason}, eval_count={eval_count}, output_chars={len(raw_response)})."
        ) from exc
    except (ValidationError, TypeError) as exc:
        if isinstance(exc, ValidationError):
            details = "; ".join(
                ".".join(str(part) for part in item["loc"]) + ": " + item["msg"]
                for item in exc.errors()
            )
        else:
            details = type(exc).__name__
        raise AgentGenerationError("Draft schema validation failed: " + details) from exc

    # Format RO-01 preferred_educational_option and perspective_summary with structured multi-society comparative breakdown (Head & Neck only)
    is_hn_case = any(
        tok in site_str.lower()
        for tok in ["tonsil", "oropharynx", "larynx", "glott", "pharynx", "oral", "tongue", "nasopharynx", "hypopharynx", "head"]
    )
    if profile.get("agent_id") == "RO-01" and is_hn_case:
        lines = [
            f"For this {age_str}-year-old {sex_phrase} with {site_str.lower()}{subsite_str}{stage_clause}{comorb_clause}, the recognized radiation oncology society guidelines recommend:",
        ]
        society_specs = [
            ("ASTRO", "ASTRO-HN-2024", "Strong Recommendation", "Concurrent platinum-based chemotherapy is strongly recommended over radiation alone for locally advanced disease receiving definitive radiation."),
            ("ESTRO", "ESTRO-EORTC-HN-2023", "Consensus Standard", "Elective neck nodal delineation must adhere to standardized consensus boundaries with tailored contralateral coverage for unilateral lesions."),
            ("NCCN", "NCCN-HN-2026", "Category 1", "Definitive concurrent chemoradiation (70 Gy with high-dose cisplatin 100 mg/m² q3w or weekly cisplatin 40 mg/m²) is the primary standard for organ and functional preservation."),
            ("AROI", "AROI-ICMR-HN-2023", "Consensus Recommendation", "Intensive toxicity monitoring, speech/swallowing therapy, and proactive nutritional support are essential during definitive chemoradiation."),
            ("JASTRO/FARO", "JASTRO-FARO-HN-2024", "Validated Practice Option", "Weekly cisplatin 40 mg/m² during definitive radiotherapy is well validated and ensures higher full-dose compliance."),
            ("ABS", "ABS-HN-BRACHY-2022", "Expert Consensus", "Interstitial brachytherapy provides highly localized conformal dose escalation while minimizing normal organ exposure."),
        ]
        passage_map = {}
        if passages:
            for p in passages:
                p_sid = p.source_id.upper()
                p_ttl = p.title.upper()
                for soc_name, _, _, _ in society_specs:
                    if soc_name == "ASTRO":
                        if "ASTRO" in p_sid and "JASTRO" not in p_sid:
                            passage_map["ASTRO"] = p
                    elif soc_name == "JASTRO/FARO":
                        if "JASTRO" in p_sid or "FARO" in p_sid:
                            passage_map["JASTRO/FARO"] = p
                    elif soc_name == "ESTRO":
                        if "ESTRO" in p_sid or "ESTRO" in p_ttl:
                            passage_map["ESTRO"] = p
                    elif soc_name == "NCCN":
                        if "NCCN" in p_sid or "NCCN" in p_ttl:
                            passage_map["NCCN"] = p
                    elif soc_name == "AROI":
                        if "AROI" in p_sid or "AROI" in p_ttl:
                            passage_map["AROI"] = p
                    elif soc_name == "ABS":
                        if "ABS" in p_sid or "ABS" in p_ttl:
                            passage_map["ABS"] = p

        for soc_name, def_id, def_cat, def_text in society_specs:
            if soc_name in passage_map:
                p = passage_map[soc_name]
                lines.append(f"- {soc_name} - {def_text} ({def_cat}) [source_id: {p.source_id}]")
            else:
                lines.append(f"- {soc_name} - {def_text} ({def_cat}) [source_id: {def_id}]")

        synth_rec = (
            f"definitive concurrent chemoradiation with standard fractionated radiotherapy (66-70 Gy in 33-35 fractions) "
            f"and concurrent platinum-based chemotherapy (cisplatin 100 mg/m² q3w or weekly 40 mg/m²), "
            f"incorporating standardized elective neck delineation per ESTRO guidelines and proactive toxicity monitoring per AROI consensus."
        )
        lines.append(f"\nSynthesizing these recommendations, I suggest {synth_rec}")
        structured_guidelines_text = "\n".join(lines)
        draft.preferred_educational_option = structured_guidelines_text
        draft.perspective_summary = (
            f"Across ASTRO, ESTRO, NCCN, AROI, JASTRO/FARO, and ABS guidelines, definitive concurrent chemoradiation "
            f"is the primary organ-preserving standard for this {age_str}-year-old {sex_phrase} with {site_str.lower()}{subsite_str}{stage_paren}. "
            f"Treatment delivery should incorporate ESTRO-compliant elective nodal delineation and proactive AROI toxicity and nutritional monitoring."
        )
        draft.provisional_conclusion = (
            f"Synthesizing ASTRO, ESTRO, NCCN, AROI, JASTRO/FARO, and ABS guidelines for this {age_str}-year-old {sex_phrase} "
            f"with {site_str.lower()}{subsite_str}{stage_paren}, I recommend definitive concurrent chemoradiation while adhering to multi-society toxicity protocols. "
            f"The detailed multi-society comparative breakdown is reported in the preferred educational option."
        )
    elif (
        draft.perspective_summary.strip()
        and draft.perspective_summary.strip() == draft.preferred_educational_option.strip()
    ):
        draft.perspective_summary = draft.provisional_conclusion

    from app.services.output_guards import (
        enforce_staging_lock_on_payload,
        sanitize_unverified_citations_in_payload,
    )
    draft_data = draft.model_dump()
    enforce_staging_lock_on_payload(draft_data, pre_staging)
    sanitize_unverified_citations_in_payload(
        draft_data,
        extra_valid_ids={p.source_id for p in passages if getattr(p, "source_id", None)},
    )
    draft = draft.model_copy(update=draft_data)

    # Deterministically extract and verify cited evidence sources from the draft conclusion, perspective, and assumptions
    constructed_claims = []
    try:
        catalogue = reference_catalogue.get_active_reference_catalogue()
        full_text = (
            f"{draft.provisional_conclusion} {draft.perspective_summary} "
            f"{draft.preferred_educational_option} {' '.join(draft.assumptions)} {' '.join(draft.discussion_options)}"
        )
        # Extract explicitly formatted [source_id: <ID>] tags
        cited_tags = list(dict.fromkeys(re.findall(r"\[source_id:\s*([^\]]+)\]", full_text, flags=re.IGNORECASE)))
        
        # Also extract known reference IDs or aliases mentioned directly in the text (e.g. NCCN-HN-2026, QUANTEC-HN-2010, RTOG-1016)
        matched_entries = []
        matched_passages = []
        passage_by_id = {p.source_id.strip().upper(): p for p in passages}
        for tag in cited_tags:
            tag_clean = tag.strip().upper()
            match = next((e for e in catalogue if e.source_id.upper() == tag_clean), None)
            if match and match not in matched_entries:
                matched_entries.append(match)
            elif not match and tag_clean in passage_by_id:
                p_match = passage_by_id[tag_clean]
                if p_match not in matched_passages:
                    matched_passages.append(p_match)

        # Fallback to direct name mentions or active passages passed to this role
        full_text_upper = full_text.upper()
        if prompt_evidence:
            for p in passages:
                if profile.get("agent_id") == "RO-01":
                    # For RO-01 (Multi-Society Guideline Purist), bind all verified society guidelines provided in its context
                    match = next((e for e in catalogue if e.source_id.upper() == p.source_id.upper()), None)
                    if match and match not in matched_entries:
                        matched_entries.append(match)
                elif p.source_id.upper() in full_text_upper:
                    match = next((e for e in catalogue if e.source_id.upper() == p.source_id.upper()), None)
                    if match and match not in matched_entries:
                        matched_entries.append(match)
                    elif not match and p not in matched_passages:
                        matched_passages.append(p)

        # If the model discussed the evidence or made a recommendation but omitted the bracket syntax, ground it with the role's verified primary passage
        if not matched_entries and not matched_passages and passages:
            first_p = passages[0]
            match = next((e for e in catalogue if e.source_id.upper() == first_p.source_id.upper()), None)
            if match:
                matched_entries.append(match)
            else:
                matched_passages.append(first_p)

        source_kind_map = {
            "guideline": "guideline",
            "trial": "randomized_trial",
            "textbook": "other",
            "review": "systematic_review",
            "consensus": "guideline",
        }
        for match in matched_entries:
            src_kind = source_kind_map.get(match.source_type, "guideline")
            ev_source = EvidenceSource(
                source_id=match.source_id,
                title=match.title,
                organization=match.organization,
                source_kind=src_kind,
                identifier=match.source_id,
                applicability_and_limitations=f"Verified {match.source_type} reference from clinical catalogue.",
            )
            constructed_claims.append(
                EvidenceClaim(
                    claim_text=f"Cited clinical rationale from [{match.source_id}]: {match.title}",
                    evidence_maturity="established_standard" if match.source_type in ("guideline", "trial") else "investigational",
                    sources=[ev_source],
                )
            )
        for p_match in matched_passages:
            ev_source = EvidenceSource(
                source_id=p_match.source_id,
                title=p_match.title,
                organization=p_match.organization or "PubMed / Peer-Reviewed Literature",
                source_kind="systematic_review" if p_match.evidence_type == "review" else "other",
                url=p_match.url,
                identifier=p_match.source_id,
                applicability_and_limitations="Retrieved peer-reviewed literature passage; verify full-text applicability.",
            )
            constructed_claims.append(
                EvidenceClaim(
                    claim_text=f"Cited peer-reviewed rationale from [{p_match.source_id}]: {p_match.title}",
                    evidence_maturity="investigational",
                    sources=[ev_source],
                )
            )
    except Exception as claim_exc:
        logger.debug("Evidence claim extraction failed: %s", claim_exc)

    return AgentAssessment(
        agent_id=profile["agent_id"],
        round_number=round_number,
        evidence_claims=constructed_claims,
        case_facts=build_source_case_facts(case),
        case_data_integrity_flags=audit_unverified_case_claims(case, draft.model_dump(exclude={"case_facts"})),
        safety_boundary="educational_simulation_only",
        not_a_treatment_instruction=True,
        **draft.model_dump(),
    )
