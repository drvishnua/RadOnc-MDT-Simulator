"""Initial API surface: runtime, agent catalogue, and educational case assessment."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES, EXPECTED_AGENT_COUNT
from app.config import APP_NAME, APP_VERSION
from app.schemas import (
    AgentAssessmentRequest, BatchRunRequest, CaseValidationResult,
    PatientCaseUpdateRequest, PatientRegistrationRequest, PatientRunRequest, SyntheticCase,
)
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
        "Educational simulation backend. Fictional training cases only; not clinical decision support."
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
    allow_methods=["GET", "POST", "DELETE"],
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




@app.get("/api/patients")
async def list_training_patients() -> dict[str, object]:
    return {"patients": run_store.list_patients(), "training_records_only": True}


@app.post("/api/patients")
async def create_training_patient(request: PatientRegistrationRequest) -> dict[str, object]:
    """Save a fictional registry profile and a separate de-identified case snapshot."""
    return run_store.create_patient(request.patient_name, request.case)


@app.get("/api/patients/{patient_id}")
async def get_training_patient(patient_id: str) -> dict[str, object]:
    try:
        return run_store.get_patient(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Saved case-version integrity check failed.") from exc


@app.post("/api/patients/{patient_id}/versions")
async def save_training_case_version(patient_id: str, request: PatientCaseUpdateRequest) -> dict[str, object]:
    """Update the registry profile and append a new immutable case version."""
    try:
        return run_store.create_case_version(patient_id, request.patient_name, request.case)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient record not found.") from exc


@app.delete("/api/patients/{patient_id}")
async def delete_training_patient(patient_id: str) -> dict[str, object]:
    """Delete a training patient and its linked simulation outputs."""
    if batch_is_running() or round_is_running():
        raise HTTPException(status_code=409, detail="Wait until active MDT inference has stopped before deleting a patient.")
    try:
        run_store.delete_patient(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient record not found.") from exc
    return {"deleted": True, "patient_id": patient_id}


@app.post("/api/patients/{patient_id}/runs")
async def create_patient_simulation(
    patient_id: str,
    request: PatientRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    """Run only a case version already saved under this training record."""
    if batch_is_running() or round_is_running():
        raise HTTPException(status_code=409, detail="Another local model run is already active.")
    try:
        record = run_store.create_run_for_case_version(patient_id, request.case_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient or saved case version not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    background_tasks.add_task(run_independent_assessments, record["run_id"])
    return record


@app.post("/api/patients/{patient_id}/versions/{case_version_id}/assess/RO-01")
async def assess_saved_patient_case(patient_id: str, case_version_id: str) -> dict[str, object]:
    """Generate and persist the standalone RO-01 assessment against a saved version."""
    if batch_is_running() or round_is_running():
        raise HTTPException(status_code=409, detail="Another local model run is already active.")
    try:
        version = run_store.get_patient_case_version(patient_id, case_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient or saved case version not found.") from exc
    profile = next(item for item in AGENT_PROFILES if item["agent_id"] == "RO-01")
    case = SyntheticCase.model_validate(version["case"])
    try:
        assessment = await generate_agent_assessment(profile=profile, case=case, round_number=1)
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=503, detail="The local Ollama service is unavailable.") from exc
    except AgentGenerationError as exc:
        logger.warning("Saved-case RO-01 generation rejected: %s", exc)
        raise HTTPException(status_code=502, detail="The local model output did not meet the required educational assessment schema.") from exc
    return run_store.save_patient_assessment(
        patient_id, case_version_id, "RO-01", 1,
        assessment.model_dump_json(exclude_none=True),
    )


@app.get("/api/patients/{patient_id}/versions/{case_version_id}/assessments")
async def get_saved_patient_assessments(patient_id: str, case_version_id: str) -> dict[str, object]:
    try:
        return {
            "patient_id": patient_id,
            "case_version_id": case_version_id,
            "assessments": run_store.list_patient_assessments(patient_id, case_version_id),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Patient or saved case version not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Saved case-version integrity check failed.") from exc


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
    """Return the exact case snapshot saved when this run was created."""
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
    if summary["completed_count"] == summary["total_agents"] and summary["failed_count"] == 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "All 45 independent assessments are complete; resume the failed MDT round "
                "instead of restarting Round 1."
            ),
        )

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


def mount_frontend_assets(application: FastAPI, dist_directory: Path) -> bool:
    """Mount a completed Vite build after API routes; return False when no build exists."""
    index_file = dist_directory / "index.html"
    if not index_file.is_file():
        return False
    application.mount(
        "/",
        StaticFiles(directory=str(dist_directory), html=True),
        name="frontend",
    )
    return True


def _frontend_dist_directory() -> Path:
    """Resolve frontend assets in both source and PyInstaller onedir layouts."""
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        bundle_root = Path(__file__).resolve().parents[2]
    return bundle_root / "frontend" / "dist"


# In development the Vite server owns the UI. In an installed build the bundled
# static assets are served by this same FastAPI process on the API origin.
FRONTEND_STATIC_MOUNTED = mount_frontend_assets(app, _frontend_dist_directory())
