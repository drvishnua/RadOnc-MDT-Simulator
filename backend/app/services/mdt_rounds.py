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
from app.services.chair_report_quality import ensure_chair_report_completeness
from app.services.mdt_generation import (
    generate_adversarial_contribution,
    generate_chair_report,
    generate_debate_contribution,
)
from app.services.ollama import AgentGenerationError

logger = logging.getLogger("radonc.mdt_rounds")


def _profile_map() -> dict[str, dict[str, str]]:
    return {item["agent_id"]: item for item in AGENT_PROFILES}


def _require_exact_completed_role_payloads(
    rows: list[dict],
    payload_field: str,
    round_label: str,
) -> dict[str, dict]:
    """Require one structured saved contribution from every expected specialist.

    A raw completed-row count is not sufficient: duplicate specialist rows can mask a
    missing role. This guard uses canonical role IDs and does not inspect clinical text.
    """
    expected_ids = set(_profile_map())
    rows_by_role: dict[str, list[dict]] = {}
    unidentified_completed_rows = 0
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "completed":
            continue
        role_id = str(row.get("agent_id") or "").strip().upper()
        if not role_id:
            unidentified_completed_rows += 1
            continue
        rows_by_role.setdefault(role_id, []).append(row)

    actual_ids = set(rows_by_role)
    missing_ids = sorted(expected_ids - actual_ids)
    duplicate_ids = sorted(
        role_id for role_id, role_rows in rows_by_role.items()
        if len(role_rows) != 1
    )
    unexpected_ids = sorted(actual_ids - expected_ids)
    malformed_payload_ids = sorted(
        role_id
        for role_id, role_rows in rows_by_role.items()
        if role_id in expected_ids
        and len(role_rows) == 1
        and not isinstance(role_rows[0].get(payload_field), dict)
    )
    try:
        expected_round_number = int(round_label.rsplit(" ", 1)[-1])
    except (TypeError, ValueError):
        raise ValueError(f"Invalid round label for payload validation: {round_label!r}")

    payload_identity_errors: list[str] = []
    for role_id, role_rows in rows_by_role.items():
        if len(role_rows) != 1:
            continue
        payload = role_rows[0].get(payload_field)
        if not isinstance(payload, dict):
            continue
        payload_agent_id = payload.get("agent_id")
        if not isinstance(payload_agent_id, str) or not payload_agent_id.strip():
            payload_identity_errors.append(f"{role_id}: missing or invalid payload agent_id")
        elif payload_agent_id.strip().upper() != role_id:
            payload_identity_errors.append(
                f"{role_id}: payload agent_id={payload_agent_id.strip().upper()}"
            )
        payload_round_number = payload.get("round_number")
        if (
            isinstance(payload_round_number, bool)
            or not isinstance(payload_round_number, int)
            or payload_round_number != expected_round_number
        ):
            payload_identity_errors.append(
                f"{role_id}: payload round_number={payload_round_number!r}, "
                f"expected={expected_round_number}"
            )

    if (
        missing_ids
        or duplicate_ids
        or unexpected_ids
        or unidentified_completed_rows
        or malformed_payload_ids
        or payload_identity_errors
    ):
        raise RuntimeError(
            f"{round_label} requires exactly one completed, structured "
            f"{payload_field} contribution per expected specialist; "
            f"missing={missing_ids}; duplicates={duplicate_ids}; "
            f"unexpected={unexpected_ids}; "
            f"unidentified_completed_rows={unidentified_completed_rows}; "
            f"malformed_payloads={malformed_payload_ids}; "
            f"payload_identity_errors={payload_identity_errors}."
        )

    return {
        role_id: role_rows[0][payload_field]
        for role_id, role_rows in rows_by_role.items()
    }


def _select_peer_views(
    current_profile: dict[str, str],
    rows: list[dict],
    result_field: str,
    max_total: int = 15,
) -> list[dict]:
    """Select a bounded, position-aware peer sample with broad specialty coverage.

    Every configured role completes its own round contribution. Peer categories are
    rotated after the current role's specialty and selected round-robin, so a small R3
    sample is not consumed by same-specialty or early catalogue entries. The selector
    allows up to three same-specialty peers and two from each other specialty.
    """
    profiles = _profile_map()
    current_position = None
    for row in rows:
        if row["agent_id"] == current_profile["agent_id"]:
            data = row.get(result_field) if row.get("status") == "completed" else None
            if data:
                current_position = data.get("position")
            break

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if (
            row.get("status") != "completed"
            or row["agent_id"] == current_profile["agent_id"]
            or not row.get(result_field)
        ):
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

    categories = list(dict.fromkeys(p["category"] for p in AGENT_PROFILES))
    current_category = current_profile["category"]
    if current_category in categories:
        current_index = categories.index(current_category)
        # Prioritise other specialties, while rotating the order for each role.
        categories = categories[current_index + 1 :] + categories[:current_index] + [current_category]

    for category in categories:
        candidates = grouped.get(category, [])
        # Prefer a peer with a different expressed position to make disagreement visible.
        candidates.sort(
            key=lambda item: (
                item[result_field].get("position") == current_position,
                item["agent_id"],
            )
        )

    selected: list[dict] = []
    # Add one peer from each available category before considering a second.
    # Own-specialty peers are limited to three; all other specialties to two.
    for peer_index in range(3):
        for category in categories:
            category_limit = 3 if category == current_category else 2
            candidates = grouped.get(category, [])
            if peer_index < category_limit and peer_index < len(candidates):
                selected.append(candidates[peer_index])
                if len(selected) >= max_total:
                    break
        if len(selected) >= max_total:
            break
    for item in selected:
        item.pop("_category", None)
    return selected


def _attach_r1_case_integrity_flags(peer_views: list[dict], round1_by_id: dict[str, dict]) -> list[dict]:
    """Carry server R1 audit warnings beside each selected R2 peer, without mutating saved rows."""
    for peer in peer_views:
        assessment = round1_by_id.get(peer.get("agent_id"), {})
        flags = assessment.get("case_data_integrity_flags") if isinstance(assessment, dict) else []
        peer["round1_case_integrity_flags"] = [
            item for item in flags if isinstance(item, str) and item.strip()
        ] if isinstance(flags, (list, tuple)) else []
    return peer_views


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
            round1_by_id = _require_exact_completed_role_payloads(
                round1_rows, "assessment", "Round 1"
            )

            if round_number >= 3:
                round2_rows = run_store.list_round_results(run_id, 2)
                round2_by_id = _require_exact_completed_role_payloads(
                    round2_rows, "result", "Round 2"
                )
            else:
                round2_rows = []
                round2_by_id = {}

            if round_number == 4:
                round3_rows = run_store.list_round_results(run_id, 3)
                _require_exact_completed_role_payloads(
                    round3_rows, "result", "Round 3"
                )
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
                            retry_max_tokens=2200,
                        )
                        report = ensure_chair_report_completeness(
                            report,
                            case,
                            round1_rows,
                            round2_rows,
                            round3_rows,
                            expected_role_ids={profile["agent_id"] for profile in AGENT_PROFILES},
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
                                peer_views = _select_peer_views(profile, round2_rows, "result", max_total=5)
                                peer_views = _attach_r1_case_integrity_flags(peer_views, round1_by_id)
                                result = await _with_one_schema_retry(
                                    generate_adversarial_contribution,
                                    profile,
                                    case,
                                    round1_by_id[agent_id],
                                    round2_by_id[agent_id],
                                    peer_views,
                                    retry_max_tokens=1500,
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
