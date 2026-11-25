"""Sequential, independent execution of all 45 configured agent profiles."""

from __future__ import annotations

import asyncio
import logging
import time

from app.agents.catalog import AGENT_PROFILES
from app.config import CIRCUIT_BREAKER_THRESHOLD, RADONC_AGENT_CONCURRENCY
from app.schemas import SyntheticCase
from app.services import run_store
from app.services.execution_lock import MODEL_EXECUTION_LOCK
from app.services.gpu_telemetry import generation_telemetry_ctx
from app.services.mdt_rounds import _run_post_round_quality_gates
from app.services.ollama import AgentGenerationError, OllamaUnavailable, generate_agent_assessment

logger = logging.getLogger("radonc.batch")
_batch_lock = MODEL_EXECUTION_LOCK
MAX_SCHEMA_ATTEMPTS = 2


def _format_error_message(exc: Exception, max_chars: int = 400) -> str:
    msg = f"{type(exc).__name__}: {exc}".strip()
    return msg if len(msg) <= max_chars else msg[: max_chars - 3].rstrip() + "..."


def batch_is_running() -> bool:
    return _batch_lock.locked()


async def _generate_with_schema_retry(profile, case: SyntheticCase):
    """Retry malformed structured output once with a larger token budget."""
    token_budgets = (1100, 1500)
    ctx = generation_telemetry_ctx.get()
    for attempt, max_tokens in enumerate(token_budgets, start=1):
        try:
            return await generate_agent_assessment(
                profile=profile,
                case=case,
                round_number=1,
                max_tokens=max_tokens,
            )
        except AgentGenerationError:
            if ctx is not None:
                ctx["retries"] = ctx.get("retries", 0) + 1
                ctx["schema_failures"] = ctx.get("schema_failures", 0) + 1
            if attempt >= len(token_budgets):
                raise
            logger.warning(
                "Retrying malformed structured output for %s with increased output budget (%s tokens)",
                profile["agent_id"],
                token_budgets[attempt],
            )


async def run_independent_assessments(
    run_id: str,
    selected_agent_ids: list[str] | None = None,
) -> None:
    """Run every unfinished (or selected) role against the same case, without sharing agent outputs."""
    from app.services.simulation_controller import get_simulation_controller

    run_store.require_run_registry_version(run_id)
    run_store.require_run_intake_provenance(run_id)
    controller = get_simulation_controller()

    async with _batch_lock:
        try:
            case = run_store.get_case(run_id)
            if not controller.is_simulation_paused(run_id):
                run_store.mark_run_running(run_id)
            existing = {
                item["agent_id"]: item["status"]
                for item in run_store.list_results(run_id)
            }

            profiles_to_run = AGENT_PROFILES
            if selected_agent_ids:
                allowed_set = set(selected_agent_ids)
                profiles_to_run = [p for p in AGENT_PROFILES if p["agent_id"] in allowed_set]

            semaphore = asyncio.Semaphore(RADONC_AGENT_CONCURRENCY)
            consecutive_infra_failures = 0

            async def process_profile(profile: dict[str, str]) -> None:
                nonlocal consecutive_infra_failures
                agent_id = profile["agent_id"]
                if existing.get(agent_id, "queued") == "completed" and not selected_agent_ids:
                    return

                if not await controller.check_execution_allowed(run_id, 1, agent_id):
                    logger.info("Agent %s in run %s skipped (execution not allowed/stopped)", agent_id, run_id)
                    return

                async with semaphore:
                    if not await controller.check_execution_allowed(run_id, 1, agent_id):
                        return
                    if consecutive_infra_failures >= CIRCUIT_BREAKER_THRESHOLD:
                        run_store.save_agent_failure(
                            run_id=run_id,
                            agent_id=agent_id,
                            error_message="CircuitBreakerOpen: Halted after consecutive Ollama unavailable failures.",
                            duration_seconds=0.0,
                            retries=0,
                            schema_failures=0,
                        )
                        return
                    started = time.perf_counter()
                    run_store.mark_agent_running(run_id, agent_id)
                    tracker: dict[str, Any] = {"retries": 0, "schema_failures": 0}
                    token = generation_telemetry_ctx.set(tracker)
                    try:
                        # Each agent receives only the original case and its own role profile.
                        assessment = await _generate_with_schema_retry(profile, case)
                        consecutive_infra_failures = 0
                        run_store.save_agent_success(
                            run_id=run_id,
                            agent_id=agent_id,
                            assessment_json=assessment.model_dump_json(),
                            duration_seconds=time.perf_counter() - started,
                            prompt_tokens=tracker.get("prompt_tokens"),
                            output_tokens=tracker.get("output_tokens"),
                            tokens_per_second=tracker.get("tokens_per_second"),
                            retries=tracker.get("retries", 0),
                            schema_failures=tracker.get("schema_failures", 0),
                        )
                    except OllamaUnavailable as exc:
                        consecutive_infra_failures += 1
                        logger.warning(
                            "Independent assessment infrastructure error for run %s agent %s (%d/%d): %s",
                            run_id,
                            agent_id,
                            consecutive_infra_failures,
                            CIRCUIT_BREAKER_THRESHOLD,
                            exc,
                        )
                        run_store.save_agent_failure(
                            run_id=run_id,
                            agent_id=agent_id,
                            error_message=_format_error_message(exc),
                            duration_seconds=time.perf_counter() - started,
                            retries=tracker.get("retries", 0),
                            schema_failures=tracker.get("schema_failures", 0),
                        )
                    except Exception as exc:
                        consecutive_infra_failures = 0
                        logger.exception(
                            "Independent assessment failed for run %s agent %s",
                            run_id,
                            agent_id,
                        )
                        run_store.save_agent_failure(
                            run_id=run_id,
                            agent_id=agent_id,
                            error_message=_format_error_message(exc),
                            duration_seconds=time.perf_counter() - started,
                            retries=tracker.get("retries", 0),
                            schema_failures=tracker.get("schema_failures", 0),
                        )
                    finally:
                        generation_telemetry_ctx.reset(token)

            await asyncio.gather(*(process_profile(profile) for profile in profiles_to_run))
            
            if not controller.is_simulation_stopped(run_id) and not controller.is_simulation_paused(run_id):
                if not selected_agent_ids:
                    run_store.mark_run_finished(run_id)
                else:
                    run_data = run_store.get_run(run_id)
                    if run_data.get("finished_count", 0) >= run_data.get("total_agents", 49):
                        run_store.mark_run_finished(run_id)

            # Run deterministic post-round quality gates (U05-U08) for Round 1.
            try:
                r1_rows = run_store.list_results(run_id)
                audit = _run_post_round_quality_gates(run_id, 1, r1_rows)
                run_store.save_round_quality_audit(run_id, 1, audit)
            except Exception:
                logger.warning(
                    "Post-round quality gates failed for run %s R1; results are unaffected.",
                    run_id, exc_info=True,
                )
        except Exception:
            logger.exception("Batch run orchestration failed for run %s", run_id)
            try:
                if not controller.is_simulation_stopped(run_id) and not controller.is_simulation_paused(run_id):
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
