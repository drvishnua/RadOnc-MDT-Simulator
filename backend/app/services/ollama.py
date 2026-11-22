"""Local Ollama status and structured assessment generation."""

from __future__ import annotations

import json
import logging
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


async def get_ollama_status() -> dict[str, object]:
    """Return runtime reachability and installed model names without generating text."""
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=5.0) as client:
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
        return {
            "reachable": True,
            "version": version_data.get("version"),
            "configured_model": OLLAMA_MODEL,
            "configured_model_installed": OLLAMA_MODEL in models,
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
        passages = engine.retrieve_evidence_for_role(role_id, case, limit=3)
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

    system_prompt = (
        "You are an expert specialist clinician in an educational Multidisciplinary Tumor Board (MDT) simulation. "
        "Speak directly, concisely, and authoritatively like a senior consultant speaking aloud in an MDT meeting—not writing an essay or a bureaucratic audit. "
        "MANDATORY CLINICAL OPINION RULE: Once a case is accepted for review, do not withhold your clinical opinion or retreat into a non-committal 'insufficient_information' position. "
        "If critical variables (such as performance status, exact TNM stage, or organ function) are missing or pending, state your recommendation using explicit IF-CLAUSES: "
        "e.g., 'For this patient, we recommend definitive CCRT if ECOG 0-1 and renal function is adequate; if ECOG >= 2 or with significant comorbidities, we recommend definitive RT alone or palliative intent.' "
        "Ground your reasoning in your role's clinical perspective and cite the verified evidence sources provided above using their exact [source_id: <ID>] tags. "
        "Keep your response punchy and concise: provisional_conclusion in 2-3 direct sentences, perspective_summary in 2-3 sentences. "
        "Do not invent unverified clinical facts or unsupplied investigations, but provide your clear conditional recommendation."
    )

    prompt = (
        f"Role: {profile['name']}\nRole mandate: {profile['mandate']}\n"
        f"Round: {round_number}\nFictional case JSON:\n"
        + json.dumps(case_payload, ensure_ascii=False, separators=(",", ":"))
        + prompt_evidence
        + "\nReturn one concise JSON object. Required fields: position "
        "(supports/opposes/conditional/insufficient_information), provisional_conclusion, "
        "preferred_educational_option, perspective_summary, assumptions, unknowns, "
        "discussion_options, conditional_options, evidence_gaps, uncertainty_notes, disagreement_notes, confidence. "
        "Do not add keys or markdown. The response format is schema-enforced."
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
            "temperature": 0.1,
            "num_predict": max_tokens,
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

    return AgentAssessment(
        agent_id=profile["agent_id"],
        round_number=round_number,
        evidence_claims=[],
        case_facts=build_source_case_facts(case),
        case_data_integrity_flags=audit_unverified_case_claims(case, draft.model_dump(exclude={"case_facts"})),
        safety_boundary="educational_simulation_only",
        not_a_treatment_instruction=True,
        **draft.model_dump(),
    )
