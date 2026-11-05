"""Initial API surface: runtime, agent catalogue, and synthetic case assessment."""

from __future__ import annotations

import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.config import APP_NAME, APP_VERSION
from app.schemas import AgentAssessmentRequest, BatchRunRequest, CaseValidationResult, SyntheticCase
from app.services.case_integrity import build_case_validation_warnings
from app.services import run_store
from app.services.batch_runner import batch_is_running, run_independent_assessments, validate_resume_state
from app.services.mdt_rounds import prepare_round_resume, round_is_running, run_mdt_round
from app.services.ollama import (
    AgentGenerationError,
    OllamaUnavailable,
    generate_agent_assessment,
    get_ollama_status,
)

logger = logging.getLogger("radonc.agent")

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
        logger.warning("Agent generation rejected for %s: %s", agent_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The local model output did not meet the required educational assessment schema.",
        ) from exc


@app.post("/api/runs")
async def create_independent_batch(
    request: BatchRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    """Queue all 45 independent first-round assessments and return immediately."""
    run_store.initialize_database()
    record = run_store.create_run(request.case)
    background_tasks.add_task(run_independent_assessments, record["run_id"])
    return record


@app.get("/api/runs/{run_id}")
async def get_independent_batch(run_id: str) -> dict[str, object]:
    try:
        return run_store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found.") from exc


@app.get("/api/runs/{run_id}/case")
async def get_run_case_snapshot(run_id: str) -> dict[str, object]:
    """Return the exact synthetic case snapshot saved when this run was created."""
    try:
        case_json = run_store.get_case_json(run_id)
        case = run_store.get_case(run_id)
        summary = run_store.get_run(run_id)
        return {
            "run_id": run_id,
            "case_snapshot_sha256": summary["case_snapshot_sha256"],
            "case_snapshot_json": case_json,
            "case": case.model_dump(exclude_none=True),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found.") from exc


@app.get("/api/runs/{run_id}/results")
async def get_independent_batch_results(run_id: str) -> dict[str, object]:
    try:
        return {"run_id": run_id, "results": run_store.list_results(run_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found.") from exc


@app.post("/api/runs/{run_id}/resume")
async def resume_independent_batch(
    run_id: str,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    """Resume failed/interrupted agents while preserving already completed outputs."""
    try:
        summary = run_store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found.") from exc

    if batch_is_running():
        raise HTTPException(status_code=409, detail="Another 45-agent batch is currently running.")
    if summary["status"] == "completed":
        raise HTTPException(status_code=409, detail="All 45 agents have already completed.")

    updated = validate_resume_state(run_id)
    background_tasks.add_task(run_independent_assessments, run_id)
    return updated


@app.post("/api/runs/{run_id}/rounds/{round_number}")
async def start_mdt_round(
    run_id: str,
    round_number: int,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    if round_is_running() or batch_is_running():
        raise HTTPException(status_code=409, detail="Another local model run is already active.")
    try:
        summary = run_store.create_round_job(run_id, round_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run or preceding round not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    background_tasks.add_task(run_mdt_round, run_id, round_number)
    return summary


@app.get("/api/runs/{run_id}/rounds/{round_number}")
async def get_mdt_round(run_id: str, round_number: int) -> dict[str, object]:
    try:
        return run_store.get_round_summary(run_id, round_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="MDT round not found.") from exc


@app.get("/api/runs/{run_id}/rounds/{round_number}/results")
async def get_mdt_round_results(run_id: str, round_number: int) -> dict[str, object]:
    try:
        return {
            "run_id": run_id,
            "round_number": round_number,
            "results": run_store.list_round_results(run_id, round_number),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="MDT round not found.") from exc


@app.post("/api/runs/{run_id}/rounds/{round_number}/resume")
async def resume_mdt_round(
    run_id: str,
    round_number: int,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    if round_is_running() or batch_is_running():
        raise HTTPException(status_code=409, detail="Another local model run is already active.")
    try:
        summary = run_store.get_round_summary(run_id, round_number)
        if summary["status"] == "completed":
            raise HTTPException(status_code=409, detail="This round is already complete.")
        updated = prepare_round_resume(run_id, round_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="MDT round not found.") from exc
    background_tasks.add_task(run_mdt_round, run_id, round_number)
    return updated


@app.get("/api/runs/{run_id}/report")
async def get_final_mdt_report(run_id: str) -> dict[str, object]:
    try:
        report = run_store.get_final_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Final Chair synthesis is not available yet.")
        return report
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found.") from exc


@app.post("/api/cases/validate", response_model=CaseValidationResult)
async def validate_case(case: SyntheticCase) -> CaseValidationResult:
    warnings = build_case_validation_warnings(case)
    if not case.known_unknowns:
        warnings.append("No explicit known-unknowns were listed; review for missing case details.")
    return CaseValidationResult(valid=True, warnings=warnings)
