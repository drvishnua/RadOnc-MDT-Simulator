"""Sequential, independent execution of all 45 configured agent profiles."""

from __future__ import annotations

import logging
import time

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services import run_store
from app.services.execution_lock import MODEL_EXECUTION_LOCK
from app.services.ollama import AgentGenerationError, generate_agent_assessment

logger = logging.getLogger("radonc.batch")
_batch_lock = MODEL_EXECUTION_LOCK
MAX_SCHEMA_ATTEMPTS = 2


def batch_is_running() -> bool:
    return _batch_lock.locked()


async def _generate_with_schema_retry(profile, case: SyntheticCase):
    """Retry one malformed/empty structured response without rerunning other agents."""
    for attempt in range(1, MAX_SCHEMA_ATTEMPTS + 1):
        try:
            return await generate_agent_assessment(
                profile=profile,
                case=case,
                round_number=1,
            )
        except AgentGenerationError:
            if attempt >= MAX_SCHEMA_ATTEMPTS:
                raise
            logger.warning(
                "Retrying malformed structured output for %s (attempt %s/%s)",
                profile["agent_id"],
                attempt + 1,
                MAX_SCHEMA_ATTEMPTS,
            )


async def run_independent_assessments(run_id: str) -> None:
    """Run every unfinished role against the same case, without sharing agent outputs."""
    async with _batch_lock:
        try:
            case = run_store.get_case(run_id)
            run_store.mark_run_running(run_id)
            existing = {
                item["agent_id"]: item["status"]
                for item in run_store.list_results(run_id)
            }

            for profile in AGENT_PROFILES:
                status = existing.get(profile["agent_id"], "queued")
                if status == "completed":
                    continue

                started = time.perf_counter()
                run_store.mark_agent_running(run_id, profile["agent_id"])
                try:
                    # Each agent receives only the original case and its own role profile.
                    assessment = await _generate_with_schema_retry(profile, case)
                    run_store.save_agent_success(
                        run_id=run_id,
                        agent_id=profile["agent_id"],
                        assessment_json=assessment.model_dump_json(),
                        duration_seconds=time.perf_counter() - started,
                    )
                except Exception as exc:
                    logger.exception(
                        "Independent assessment failed for run %s agent %s",
                        run_id,
                        profile["agent_id"],
                    )
                    run_store.save_agent_failure(
                        run_id=run_id,
                        agent_id=profile["agent_id"],
                        error_message=f"{type(exc).__name__}: {exc}",
                        duration_seconds=time.perf_counter() - started,
                    )

            run_store.mark_run_finished(run_id)
        except Exception:
            logger.exception("Batch run orchestration failed for run %s", run_id)
            try:
                run_store.mark_run_finished(run_id)
            except Exception:
                logger.exception("Could not finalize batch run %s", run_id)


def validate_resume_state(run_id: str) -> dict[str, object]:
    """Reset interrupted or failed records before resuming; completed outputs remain intact."""
    summary = run_store.get_run(run_id)
    if summary["status"] == "completed":
        return summary
    if summary["status"] == "completed_with_errors":
        run_store.reset_failed_agents(run_id)
    elif summary["status"] in {"running", "queued"}:
        run_store.reset_interrupted_agents(run_id)
    return run_store.get_run(run_id)
