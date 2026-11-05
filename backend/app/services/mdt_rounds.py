"""Orchestrate MDT rounds 2-4 while preserving all 45 role identities."""

from __future__ import annotations

import asyncio
import logging
import time

from app.agents.catalog import AGENT_PROFILES
from app.config import RADONC_AGENT_CONCURRENCY
from app.schemas import SyntheticCase
from app.services import run_store
from app.services.execution_lock import MODEL_EXECUTION_LOCK
from app.services.mdt_generation import (
    generate_adversarial_contribution,
    generate_chair_report,
    generate_debate_contribution,
)
from app.services.ollama import AgentGenerationError

logger = logging.getLogger("radonc.mdt_rounds")


def _profile_map() -> dict[str, dict[str, str]]:
    return {item["agent_id"]: item for item in AGENT_PROFILES}


def _select_peer_views(
    current_profile: dict[str, str],
    rows: list[dict],
    result_field: str,
) -> list[dict]:
    """Select compact cross-specialty context that fits the local context window.

    Every configured role completes its own round contribution. For each contribution,
    peer context includes up to three same-specialty and two per other specialty. This
    bounds prompt size rather than sending all full-length outputs to every agent.
    """
    profiles = _profile_map()
    current_position = None
    for row in rows:
        if row["agent_id"] == current_profile["agent_id"]:
            data = row.get(result_field)
            if data:
                current_position = data.get("position")
            break

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if row["agent_id"] == current_profile["agent_id"] or not row.get(result_field):
            continue
        profile = profiles.get(row["agent_id"])
        if not profile:
            continue
        item = {
            "agent_id": row["agent_id"],
            "agent_name": row["agent_name"],
            result_field: row[result_field],
            "_category": profile["category"],
        }
        grouped.setdefault(profile["category"], []).append(item)

    selected: list[dict] = []
    categories = list(dict.fromkeys(p["category"] for p in AGENT_PROFILES))
    for category in categories:
        candidates = grouped.get(category, [])
        # Prefer a peer with a different expressed position to make disagreement visible.
        candidates.sort(
            key=lambda item: (
                item[result_field].get("position") == current_position,
                item["agent_id"],
            )
        )
        limit = 3 if category == current_profile["category"] else 2
        selected.extend(candidates[:limit])

    selected = selected[:15]
    for item in selected:
        item.pop("_category", None)
    return selected


async def _with_one_schema_retry(callable_, *args, retry_max_tokens: int):
    try:
        return await callable_(*args)
    except AgentGenerationError:
        logger.warning(
            "Retrying invalid structured MDT response with increased output budget (%s tokens).",
            retry_max_tokens,
        )
        return await callable_(*args, max_tokens=retry_max_tokens)


async def run_mdt_round(run_id: str, round_number: int) -> None:
    """Execute Round 2, 3, or 4, saving every individual result immediately."""
    if round_number not in (2, 3, 4):
        raise ValueError("Round number must be 2, 3, or 4.")

    async with MODEL_EXECUTION_LOCK:
        try:
            case = run_store.get_case(run_id)
            run_store.mark_round_running(run_id, round_number)
            round_rows = run_store.list_round_results(run_id, round_number)
            completed_ids = {
                row["agent_id"] for row in round_rows if row["status"] == "completed"
            }

            round1_rows = run_store.list_results(run_id)
            round1_by_id = {
                row["agent_id"]: row["assessment"]
                for row in round1_rows
                if row.get("assessment")
            }
            if len(round1_by_id) != len(AGENT_PROFILES):
                raise RuntimeError("All 45 Round-1 assessments are required before debate.")

            if round_number >= 3:
                round2_rows = run_store.list_round_results(run_id, 2)
                round2_by_id = {
                    row["agent_id"]: row["result"]
                    for row in round2_rows
                    if row.get("result")
                }
                if len(round2_by_id) != len(AGENT_PROFILES):
                    raise RuntimeError("All 45 Round-2 debate contributions are required.")
            else:
                round2_rows = []
                round2_by_id = {}

            if round_number == 4:
                round3_rows = run_store.list_round_results(run_id, 3)
                if sum(1 for row in round3_rows if row.get("result")) != len(AGENT_PROFILES):
                    raise RuntimeError("All 45 Round-3 adversarial reviews are required.")
                if "SG-07" not in completed_ids:
                    started = time.perf_counter()
                    run_store.mark_round_agent_running(run_id, 4, "SG-07")
                    try:
                        report = await _with_one_schema_retry(
                            generate_chair_report,
                            run_id,
                            case,
                            round1_rows,
                            round2_rows,
                            round3_rows,
                            retry_max_tokens=1600,
                        )
                        run_store.save_round_success(
                            run_id, 4, "SG-07", report.model_dump_json(),
                            time.perf_counter() - started,
                        )
                    except Exception as exc:
                        logger.exception("Final chair report failed for run %s", run_id)
                        run_store.save_round_failure(
                            run_id, 4, "SG-07", f"{type(exc).__name__}: {exc}",
                            time.perf_counter() - started,
                        )
            else:
                semaphore = asyncio.Semaphore(RADONC_AGENT_CONCURRENCY)

                async def process_profile(profile: dict[str, str]) -> None:
                    agent_id = profile["agent_id"]
                    if agent_id in completed_ids:
                        return
                    async with semaphore:
                        started = time.perf_counter()
                        run_store.mark_round_agent_running(run_id, round_number, agent_id)
                        try:
                            if round_number == 2:
                                peer_views = _select_peer_views(profile, round1_rows, "assessment")
                                result = await _with_one_schema_retry(
                                    generate_debate_contribution,
                                    profile,
                                    case,
                                    round1_by_id[agent_id],
                                    peer_views,
                                    retry_max_tokens=1000,
                                )
                            else:
                                peer_views = _select_peer_views(profile, round2_rows, "result")
                                result = await _with_one_schema_retry(
                                    generate_adversarial_contribution,
                                    profile,
                                    case,
                                    round1_by_id[agent_id],
                                    round2_by_id[agent_id],
                                    peer_views,
                                    retry_max_tokens=1000,
                                )
                            run_store.save_round_success(
                                run_id,
                                round_number,
                                agent_id,
                                result.model_dump_json(),
                                time.perf_counter() - started,
                            )
                        except Exception as exc:
                            logger.exception(
                                "Round %s contribution failed for run %s agent %s",
                                round_number, run_id, agent_id,
                            )
                            run_store.save_round_failure(
                                run_id, round_number, agent_id,
                                f"{type(exc).__name__}: {exc}",
                                time.perf_counter() - started,
                            )

                await asyncio.gather(*(process_profile(profile) for profile in AGENT_PROFILES))

            run_store.mark_round_finished(run_id, round_number)
        except Exception:
            logger.exception("MDT round %s orchestration failed for run %s", round_number, run_id)
            try:
                run_store.mark_round_finished(run_id, round_number)
            except Exception:
                logger.exception("Could not finalize MDT round %s for run %s", round_number, run_id)


def prepare_round_resume(run_id: str, round_number: int) -> dict[str, object]:
    summary = run_store.get_round_summary(run_id, round_number)
    if summary["status"] == "completed":
        return summary
    if summary["status"] in {"queued", "running", "completed_with_errors"}:
        run_store.reset_failed_round_agents(run_id, round_number)
    return run_store.get_round_summary(run_id, round_number)


def round_is_running() -> bool:
    return MODEL_EXECUTION_LOCK.locked()
