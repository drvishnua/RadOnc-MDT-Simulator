"""Initial API surface: runtime, agent catalogue, and synthetic case assessment."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.config import APP_NAME, APP_VERSION
from app.schemas import AgentAssessmentRequest, CaseValidationResult, SyntheticCase
from app.services.ollama import (
    AgentGenerationError,
    OllamaUnavailable,
    generate_agent_assessment,
    get_ollama_status,
)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Educational simulation backend. Synthetic cases only; not clinical decision support."
    ),
)

# Allow only the local Vite development/preview origins. Do not expose the API to arbitrary sites.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "application": APP_NAME,
        "version": APP_VERSION,
        "mode": "education_simulation_only",
    }


@app.get("/api/runtime")
async def runtime_status() -> dict[str, object]:
    return {"ollama": await get_ollama_status()}


@app.get("/api/agents")
async def list_agents() -> dict[str, object]:
    return {
        "expected_agent_count": EXPECTED_AGENT_COUNT,
        "returned_agent_count": len(AGENT_PROFILES),
        "all_roles_required": True,
        "agents": AGENT_PROFILES,
    }


@app.post("/api/agents/{agent_id}/assess", response_model=AgentAssessment)
async def assess_with_agent(
    agent_id: str,
    request: AgentAssessmentRequest,
) -> AgentAssessment:
    profile = next(
        (item for item in AGENT_PROFILES if item["agent_id"] == agent_id),
        None,
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Unknown agent profile.")

    try:
        return await generate_agent_assessment(
            profile=profile,
            case=request.case,
            round_number=request.round_number,
        )
    except OllamaUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="The local Ollama service is unavailable.",
        ) from exc
    except AgentGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail="The local model output did not meet the required educational assessment schema.",
        ) from exc


@app.post("/api/cases/validate", response_model=CaseValidationResult)
async def validate_case(case: SyntheticCase) -> CaseValidationResult:
    warnings: list[str] = []
    if case.age_years is None:
        warnings.append("Age is not supplied; keep it marked as unknown in the simulation.")
    if not case.primary_site:
        warnings.append("Primary site is not supplied.")
    if not case.histology:
        warnings.append("Histology is not supplied.")
    if not case.known_unknowns:
        warnings.append("No explicit known-unknowns were listed; review for missing case details.")

    return CaseValidationResult(valid=True, warnings=warnings)
