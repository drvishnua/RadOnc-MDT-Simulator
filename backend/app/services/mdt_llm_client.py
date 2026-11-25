"""Low-level structured Ollama client and compact formatting utilities for MDT rounds."""

from __future__ import annotations

import json
from collections import Counter
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.round_schemas import (
    AdversarialContributionDraft,
    AdversarialSourceOpinionReviewsRepairDraft,
    Round2ContributionDraft,
    Round2SourceOpinionResponsesRepairDraft,
    RoundContributionDraft,
    RoundTextRepairDraft,
)
from app.services.chair_report_quality import count_distinct_role_positions
from app.services.gpu_telemetry import record_current_telemetry
from app.services.ollama import AgentGenerationError, OllamaUnavailable

T = TypeVar("T", bound=BaseModel)

# Large structured R2/R3 prompts can exceed four minutes on CPU-only hosts.
# Keep the request bounded while allowing slower local inference to finish.
GENERATION_REQUEST_TIMEOUT_SECONDS = 600.0


def _context_window_for_schema(schema_type: type[BaseModel]) -> int:
    """Give R3 extra context for its source-linked peer review and JSON output."""
    if schema_type is AdversarialContributionDraft:
        return 8192
    return (
        6144
        if schema_type
        in (
            RoundContributionDraft,
            Round2ContributionDraft,
            Round2SourceOpinionResponsesRepairDraft,
            AdversarialSourceOpinionReviewsRepairDraft,
            RoundTextRepairDraft,
        )
        else 4096
    )


async def _generate_structured(prompt: str, schema_type: type[T], max_tokens: int) -> T:
    system = (
        "You are an expert specialist clinician in an educational Multidisciplinary Tumor Board (MDT) discussion. "
        "Speak directly, concisely, and authoritatively like a clinician speaking aloud in an MDT meeting—not writing an essay or bureaucratic audit. "
        "MANDATORY CLINICAL OPINION RULE: Once a case is under review, do not withhold your clinical perspective or give non-committal answers. "
        "If staging, performance status, or comorbidities are missing or pending, state your recommendation using explicit IF-CLAUSES: "
        "(e.g., 'If ECOG 0-1 and fit for systemic therapy, we recommend definitive CCRT; if poor performance status or severe comorbidities, we recommend definitive RT alone'). "
        "Ground your reasoning in your role's perspective, challenge peer assumptions constructively, and cite verified evidence using exact [source_id: ...] tags when provided. "
        "Be concise and return only a JSON object that validates against the supplied schema."
    )
    request_body = {
        "model": OLLAMA_MODEL,
        "system": system,
        "prompt": prompt,
        "format": schema_type.model_json_schema(),
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0.1,
            "num_predict": max_tokens,
            "num_ctx": _context_window_for_schema(schema_type),
        },
    }
    try:
        async with httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=httpx.Timeout(GENERATION_REQUEST_TIMEOUT_SECONDS, connect=5.0),
        ) as client:
            response = await client.post("/api/generate", json=request_body)
            response.raise_for_status()
            payload = response.json()
            record_current_telemetry(payload)
    except (httpx.HTTPError, ValueError) as exc:
        raise OllamaUnavailable("The local Ollama service could not complete this MDT round.") from exc

    raw = payload.get("response")
    if not isinstance(raw, str) or not raw.strip():
        raise AgentGenerationError("The local model returned an empty MDT-round response.")
    try:
        return schema_type.model_validate(json.loads(raw))
    except json.JSONDecodeError as exc:
        done_reason = payload.get("done_reason", "unknown")
        eval_count = payload.get("eval_count", "unknown")
        prompt_eval_count = payload.get("prompt_eval_count", "unknown")
        raise AgentGenerationError(
            "The model did not return valid JSON for this MDT round "
            f"(done_reason={done_reason}, prompt_tokens={prompt_eval_count}, "
            f"output_tokens={eval_count}, output_chars={len(raw)})."
        ) from exc
    except ValidationError as exc:
        details = "; ".join(
            ".".join(str(part) for part in item["loc"]) + ": " + item["msg"]
            for item in exc.errors()
        )
        raise AgentGenerationError("MDT-round schema validation failed: " + details) from exc


def _compact(value: str, limit: int) -> str:
    normalized = " ".join(value.split())
    return normalized if len(normalized) <= limit else normalized[: limit - 1].rstrip() + "…"


def _round_items(rows: list[dict], field: str) -> list[tuple[dict, dict]]:
    return [
        (row, row[field])
        for row in rows
        if row.get("status") == "completed" and isinstance(row.get(field), dict)
    ]


def _position_counts(rows: list[dict], field: str) -> Counter:
    return count_distinct_role_positions(rows, field)


def _unique_modal_position(counts: Counter) -> str | None:
    """Return a modal label only when one position is uniquely most frequent."""
    if not counts:
        return None
    highest = max(counts.values())
    modes = [position for position, count in counts.items() if count == highest]
    return modes[0] if len(modes) == 1 else None


def _unique_strings(values: list[str], limit: int = 12) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = " ".join(value.split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            output.append(cleaned)
            seen.add(key)
        if len(output) >= limit:
            break
    return output


def _format_position_counts(counts: Counter) -> str:
    total = sum(counts.values())
    if not total:
        return "no valid positions recorded"
    labels = {
        "insufficient_information": "insufficient-information",
        "conditional": "conditional",
        "supports": "supports",
        "opposes": "opposes",
    }
    return ", ".join(
        f"{count}/{total} {labels.get(position, position)}"
        for position, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )
