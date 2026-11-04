"""Initial API surface: runtime, agents, and synthetic case validation."""

from __future__ import annotations

from fastapi import FastAPI

from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.config import APP_NAME, APP_VERSION
from app.schemas import CaseValidationResult, SyntheticCase
from app.services.ollama import get_ollama_status

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Educational simulation backend. Synthetic cases only; not clinical decision support."
    ),
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
