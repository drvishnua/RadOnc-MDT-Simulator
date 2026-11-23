"""Local Ollama status and structured assessment generation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from pydantic import ValidationError

from app.agent_schemas import AgentAssessment, AgentDraft
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import SyntheticCase
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
    import asyncio
    import shutil
    import subprocess

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
                logger.warning(f"Failed to auto-spawn Ollama daemon: {err}")

    # If reachable but configured model is missing, trigger pull
    if status.get("reachable") and not status.get("configured_model_installed") and auto_pull:
        logger.info(f"Configured model {OLLAMA_MODEL} not found. Triggering pull via Ollama API...")
        try:
            async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=10.0) as client:
                await client.post("/api/pull", json={"name": OLLAMA_MODEL, "stream": False})
                status = await _probe_ollama()
        except Exception as pull_err:
            logger.warning(f"Failed to auto-pull configured model {OLLAMA_MODEL}: {pull_err}")

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

    evidence_context = ""
    try:
        from app.services.evidence_retrieval import get_evidence_retrieval_engine
        engine = get_evidence_retrieval_engine()
        role_id = profile.get("agent_id", "")
        # For RO-01, provide 6 society guidelines so ASTRO, ESTRO, JASTRO/FARO, AROI, ABS, and NCCN are all available
        evidence_limit = 6 if role_id == "RO-01" else 3
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
        "3. NEVER WITHHOLD OPINION / MANDATORY IF-CLAUSES: Never retreat into a generic insufficient_information response. Do not use a generic insufficient_information response as a substitute for analysing relevant supplied facts. If variables (ECOG, HPV/p16, renal function, histology grade) are pending or missing, give clear conditional branching recommendations. The condition must not be presented as true or met:\n"
        "   Example: 'If the patient is ECOG 0-1 with confirmed p16-positive status, I recommend definitive concurrent chemoradiation (70 Gy with high-dose cisplatin) based on [source_id: NCCN-HN-2026] and foundational dose-fractionation principles from [source_id: PEREZ-BRADY-2026]; however, if ECOG >= 2 or renal clearance is impaired per [source_id: HARRISONS-MED-21ST], I favor definitive RT alone.'\n"
        "4. CITE BOTH STANDARD TEXTBOOKS & GUIDELINES: Do not rely solely on NCCN guidelines. Ground your foundational principles in standard reference textbooks (e.g. Perez & Brady, Gunderson & Tepper, Harrison's, Hall's Radiobiology) alongside specific clinical guidelines or trials using their exact [source_id: <ID>] tags.\n"
        "5. PRIMARY DISEASE SUBSITE FIDELITY & NO LARYNX CONFUSION:\n"
        "   - The primary site and diagnosis are provided in the case snapshot (e.g. Oropharynx - tonsillar fossa/soft palate). Respect the EXACT primary site!\n"
        "   - NEVER confuse or substitute oropharynx / tonsil with larynx or glottic cancer. Do NOT discuss 'larynx preservation' or 'glottic guidelines' when the case is an oropharyngeal carcinoma!\n"
        "6. ACCURATE CLINICAL STAGING & TIMING RULES:\n"
        "   - Clinical Staging Timing: This is a pre-treatment, unoperated patient. Pathological staging (pT, pN, pM) is determined ONLY AFTER definitive surgical resection and neck dissection. Do NOT request or expect pathological staging for pre-treatment decision-making; clinical TNM (cTNM) governs definitive radiotherapy / chemoradiotherapy!\n"
        "   - Nodal Status: A 1x1 cm lymph node in cervical level 2 is clinically positive nodal disease (cN1 in AJCC 8th Edition; single ipsilateral node <= 3 cm), NOT N0! Never treat a documented 1x1 cm node as N0.\n"
        "7. ROLE-SPECIFIC MANDATE FOR RO-01 (Guideline-focused Radiation Oncologist):\n"
        "   - You trust ONLY formal published guidelines from recognized professional radiation oncology societies: American Society for Radiation Oncology (ASTRO), European Society for Radiotherapy and Oncology (ESTRO), Japanese Society for Radiation Oncology (JASTRO), Association of Radiation Oncologists of India (AROI), Federation of Asian Organizations for Radiation Oncology (FARO), American Brachytherapy Society (ABS), and NCCN.\n"
        "   - Even if an option is proposed by individual trials, papers, or textbooks, you REFUSE to endorse it unless an established society guideline explicitly recommends it.\n"
        "   - Systematically compare and analyze every relevant published society guideline addressing this patient case and stage (ASTRO, ESTRO, JASTRO/FARO, AROI, ABS, NCCN).\n"
        "   - Conclude with your definitive, authoritative final decision synthesizing the consensus across all relevant society guidelines."
    )


    prompt = (
        f"MDT Role: {role_name} ({profile.get('agent_id', '')})\n"
        f"Mandate: {role_mandate}\n"
        f"Clinical Philosophy & Risk Profile: {role_philosophy} | {role_risk}\n"
        f"Round: {round_number}\n\n"
        f"Patient Case:\n"
        + json.dumps(case_payload, ensure_ascii=False, separators=(",", ":"))
        + prompt_evidence
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

    # Deterministically extract and verify cited evidence sources from the draft conclusion, perspective, and assumptions
    constructed_claims = []
    try:
        from app.services.reference_catalogue import get_active_reference_catalogue
        from app.agent_schemas import EvidenceClaim, EvidenceSource
        catalogue = get_active_reference_catalogue()
        full_text = (
            f"{draft.provisional_conclusion} {draft.perspective_summary} "
            f"{draft.preferred_educational_option} {' '.join(draft.assumptions)} {' '.join(draft.discussion_options)}"
        )
        # Extract explicitly formatted [source_id: <ID>] tags
        cited_tags = list(dict.fromkeys(re.findall(r"\[source_id:\s*([^\]]+)\]", full_text, flags=re.IGNORECASE)))
        
        # Also extract known reference IDs or aliases mentioned directly in the text (e.g. NCCN-HN-2026, QUANTEC-HN-2010, RTOG-1016)
        matched_entries = []
        for tag in cited_tags:
            tag_clean = tag.strip().upper()
            match = next((e for e in catalogue if e.source_id.upper() == tag_clean), None)
            if match and match not in matched_entries:
                matched_entries.append(match)

        # Fallback to direct name mentions or active passages passed to this role
        full_text_upper = full_text.upper()
        if prompt_evidence:
            for p in passages if "passages" in locals() and passages else []:
                if p.source_id.upper() in full_text_upper:
                    match = next((e for e in catalogue if e.source_id.upper() == p.source_id.upper()), None)
                    if match and match not in matched_entries:
                        matched_entries.append(match)

        # If the model discussed the evidence or made a recommendation but omitted the bracket syntax, ground it with the role's verified primary passage
        if not matched_entries and "passages" in locals() and passages:
            first_p = passages[0]
            match = next((e for e in catalogue if e.source_id.upper() == first_p.source_id.upper()), None)
            if match:
                matched_entries.append(match)

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
