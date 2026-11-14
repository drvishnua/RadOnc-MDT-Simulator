"""Run a full four-round live-model validation on the connected Windows laptop.

Synthetic software-validation case only. This script exercises the real local Ollama
model and writes a JSON audit artifact. It does not contact a hospital or use patient data.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.catalog import AGENT_PROFILES
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import SyntheticCase
from app.services import batch_runner, mdt_rounds, run_store
from app.services.gpu_telemetry import parse_nvidia_smi_csv, summarize_gpu_telemetry
from app.services.ollama import get_ollama_status
from app.services.case_integrity import build_source_case_facts, build_case_report_title
from app.services.chair_report_quality import validate_consensus_points

ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
# Keep one bounded retry per stage; no unbounded local-model generation loop.
MAX_STAGE_ATTEMPTS = 2
CPU_ONLY_VALIDATION = os.environ.get("RADONC_VALIDATION_CPU_ONLY", "").strip() == "1"
ARTIFACT_NAME = "live_four_round_hosted_cpu_validation.json" if CPU_ONLY_VALIDATION else "live_four_round_validation.json"
DATABASE_NAME = "live_four_round_hosted_cpu_validation.sqlite3" if CPU_ONLY_VALIDATION else "live_four_round_validation.sqlite3"
run_store.DB_PATH = ARTIFACT_DIR / DATABASE_NAME


def gpu_snapshot() -> str:
    if CPU_ONLY_VALIDATION:
        return "not measured: GitHub-hosted CPU-only validation; no NVIDIA GPU claim"
    try:
        return subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=8,
        ).strip()
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}"


def ollama_process_snapshot() -> dict:
    """Capture Ollama API VRAM allocation and its human-readable processor split."""
    snapshot: dict = {}
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/ps", timeout=5) as response:
            snapshot["api_ps"] = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        snapshot["api_ps_error"] = f"{type(exc).__name__}: {exc}"
    try:
        snapshot["cli_ps"] = subprocess.check_output(
            ["ollama", "ps"], text=True, timeout=5
        ).strip()
    except Exception as exc:
        snapshot["cli_ps_error"] = f"{type(exc).__name__}: {exc}"
    return snapshot


async def record_ollama_process_snapshot(telemetry: dict, label: str) -> None:
    snapshot = await asyncio.to_thread(ollama_process_snapshot)
    telemetry["ollama_process_snapshots"].append({
        "label": label,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
    })


async def sample_gpu_during_run(stop_event: asyncio.Event, telemetry: dict) -> None:
    """Sample GPU telemetry locally, or Ollama process telemetry on a hosted CPU runner."""
    if CPU_ONLY_VALIDATION:
        while not stop_event.is_set():
            captured_at = datetime.now(timezone.utc).isoformat()
            snapshot = await asyncio.to_thread(ollama_process_snapshot)
            telemetry["cpu_samples"].append({
                "captured_at": captured_at,
                "ollama_process": snapshot,
                "gpu_measured": False,
            })
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                pass
        return

    last_ollama_snapshot = 0.0
    query = [
        "nvidia-smi",
        "--query-gpu=name,memory.used,memory.total,utilization.gpu,utilization.memory",
        "--format=csv,noheader,nounits",
    ]
    while not stop_event.is_set():
        captured_at = datetime.now(timezone.utc).isoformat()
        try:
            output = await asyncio.to_thread(
                subprocess.check_output, query, text=True, timeout=8
            )
            telemetry["samples"].append({
                "captured_at": captured_at,
                "gpus": parse_nvidia_smi_csv(output),
            })
        except Exception as exc:
            telemetry["sampling_errors"].append({
                "captured_at": captured_at,
                "error": f"{type(exc).__name__}: {exc}",
            })

        now = time.monotonic()
        if now - last_ollama_snapshot >= 10:
            await record_ollama_process_snapshot(telemetry, "during_inference")
            last_ollama_snapshot = now

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass


def build_case() -> SyntheticCase:
    """A fixed, fictional case used only for software integration validation."""
    # Exact snapshot from the user-uploaded baseline export. Preserve the raw
    # shorthand and empty structured arrays so the regression run tests the
    # free-text/structured-field discrepancy rather than silently repairing it.
    return SyntheticCase(
        scenario_title="Synthetic head-and-neck case",
        case_summary="dm\\nshtn\\nsmoker\\n\\n1x1 cm growth involving right vocal cord and anterior commissure",
        age_years=75,
        primary_site="ca glottis",
        histology="scc",
        relevant_comorbidities=[],
        prior_treatment=[],
        patient_goals=[],
        social_context=[],
        resource_context=[],
        known_unknowns=[],
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ids_match(rows: list[dict], expected: set[str], label: str) -> None:
    actual = {item["agent_id"] for item in rows}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    require(not missing and not extra, f"{label}: role mismatch; missing={missing}, extra={extra}")



def verify_position_transitions(previous_rows: list[dict], current_rows: list[dict], label: str) -> None:
    previous_field = "assessment" if label == "Round 2" else "result"
    current_by_id = {row["agent_id"]: row for row in current_rows}
    for previous in previous_rows:
        agent_id = previous["agent_id"]
        old_position = previous[previous_field]["position"]
        current = current_by_id[agent_id]["result"]
        new_position = current["position"]
        transitions = current.get("position_changes") or []
        if old_position != new_position:
            expected = f"{old_position} → {new_position}"
            require(
                any(expected in item for item in transitions),
                f"{label}: {agent_id} changed {old_position} → {new_position} without a traceable transition record.",
            )
        else:
            require(
                not transitions,
                f"{label}: {agent_id} has a position-change record despite retaining {old_position}.",
            )


async def ensure_round1(run_id: str, metrics: dict) -> dict:
    for attempt in range(1, MAX_STAGE_ATTEMPTS + 1):
        started = time.perf_counter()
        if attempt == 1:
            await batch_runner.run_independent_assessments(run_id)
        else:
            batch_runner.validate_resume_state(run_id)
            await batch_runner.run_independent_assessments(run_id)
        summary = run_store.get_run(run_id)
        metrics["round_1_attempts"].append({
            "attempt": attempt,
            "wall_seconds": round(time.perf_counter() - started, 2),
            "completed": summary["completed_count"],
            "failed": summary["failed_count"],
        })
        if summary["status"] == "completed" and summary["completed_count"] == 45:
            return summary
    raise RuntimeError("Round 1 did not complete all 45 independent assessments after retry.")


async def ensure_round(run_id: str, round_number: int, metrics: dict) -> dict:
    attempt_records = metrics[f"round_{round_number}_attempts"]
    for attempt in range(1, MAX_STAGE_ATTEMPTS + 1):
        started = time.perf_counter()
        if attempt == 1:
            run_store.create_round_job(run_id, round_number)
        else:
            mdt_rounds.prepare_round_resume(run_id, round_number)
        await mdt_rounds.run_mdt_round(run_id, round_number)
        summary = run_store.get_round_summary(run_id, round_number)
        attempt_records.append({
            "attempt": attempt,
            "wall_seconds": round(time.perf_counter() - started, 2),
            "completed": summary["completed_count"],
            "failed": summary["failed_count"],
        })
        if summary["status"] == "completed" and summary["completed_count"] == summary["total_agents"]:
            return summary
    raise RuntimeError(
        f"Round {round_number} did not complete all required roles after retry."
    )


async def main() -> int:
    started_all = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    case = build_case()
    case_json = case.model_dump_json(exclude_none=True)
    case_hash = hashlib.sha256(case_json.encode("utf-8")).hexdigest()
    expected_ids = {profile["agent_id"] for profile in AGENT_PROFILES}
    require(len(expected_ids) == 45, f"Expected 45 unique roles, found {len(expected_ids)}.")

    runtime = await get_ollama_status()
    require(runtime.get("reachable") is True, "Ollama is not reachable on localhost.")
    require(runtime.get("configured_model_installed") is True, f"Configured model {OLLAMA_MODEL} is not installed.")

    metrics = {
        "round_1_attempts": [],
        "round_2_attempts": [],
        "round_3_attempts": [],
        "round_4_attempts": [],
    }
    gpu_telemetry = {
        "sample_interval_seconds": 10.0 if CPU_ONLY_VALIDATION else 1.0,
        "samples": [],
        "cpu_samples": [],
        "sampling_errors": [],
        "ollama_process_snapshots": [],
        "gpu_measured": not CPU_ONLY_VALIDATION,
    }
    stop_gpu_sampler = asyncio.Event()
    gpu_sampler_task: asyncio.Task | None = None
    result_payload: dict = {
        "validation_type": "live_four_round_hosted_cpu_synthetic_integration" if CPU_ONLY_VALIDATION else "live_four_round_synthetic_integration",
        "execution_mode": "github_hosted_cpu_only" if CPU_ONLY_VALIDATION else "local_gpu_or_cpu",
        "gpu_measured": not CPU_ONLY_VALIDATION,
        "synthetic_only": True,
        "started_at": started_at,
        "host_platform": platform.platform(),
        "python_version": sys.version,
        "ollama": runtime,
        "model": OLLAMA_MODEL,
        "gpu_before": gpu_snapshot(),
        "gpu_telemetry": gpu_telemetry,
        "ollama_process_before": None,
        "case_snapshot": json.loads(case_json),
        "case_snapshot_json": case_json,
        "case_snapshot_sha256": case_hash,
        "expected_agent_count": 45,
        "concurrency": 1,
        "metrics": metrics,
    }
    run_id = None

    try:
        result_payload["ollama_process_before"] = await asyncio.to_thread(ollama_process_snapshot)
        gpu_sampler_task = asyncio.create_task(
            sample_gpu_during_run(stop_gpu_sampler, gpu_telemetry)
        )
        created = run_store.create_run(case)
        run_id = created["run_id"]
        result_payload["run_id"] = run_id

        round1_summary = await ensure_round1(run_id, metrics)
        await record_ollama_process_snapshot(gpu_telemetry, "after_round_1")
        round1 = run_store.list_results(run_id)
        ids_match(round1, expected_ids, "Round 1")
        require(all(row["status"] == "completed" and row["assessment"] for row in round1),
                "Round 1 contains an incomplete agent result.")
        require(all(row["assessment"].get("provisional_conclusion") for row in round1),
                "At least one Round-1 agent did not provide a provisional conclusion.")
        require(all(row["assessment"].get("position") for row in round1),
                "At least one Round-1 agent did not provide a position.")
        require(all(row["assessment"].get("not_a_treatment_instruction") is True for row in round1),
                "Round 1 safety boundary missing.")
        require(all(not row["assessment"].get("evidence_claims") for row in round1),
                "Evidence claims must remain empty until evidence retrieval is implemented.")
        expected_case_facts = build_source_case_facts(case)
        require(
            all(row["assessment"].get("case_facts") == expected_case_facts for row in round1),
            "Round 1 factual registers differ from the immutable source case snapshot.",
        )
        require(
            all("case_data_integrity_flags" in row["assessment"] for row in round1),
            "Round 1 case-data integrity audit fields are missing.",
        )
        saved_run = run_store.get_run(run_id)
        require(
            saved_run["case_snapshot_sha256"] == case_hash,
            "Persisted run case snapshot hash does not match the validation input.",
        )

        round2_summary = await ensure_round(run_id, 2, metrics)
        round2 = run_store.list_round_results(run_id, 2)
        ids_match(round2, expected_ids, "Round 2")
        require(all(row["status"] == "completed" and row["result"] for row in round2),
                "Round 2 contains an incomplete agent result.")
        require(all(row["result"].get("provisional_conclusion") for row in round2),
                "At least one Round-2 contribution lacks a conclusion.")
        require(
            all("case_data_integrity_flags" in row["result"] for row in round2),
            "Round 2 case-data integrity audit fields are missing.",
        )
        verify_position_transitions(round1, round2, "Round 2")
        await record_ollama_process_snapshot(gpu_telemetry, "after_round_2")

        round3_summary = await ensure_round(run_id, 3, metrics)
        round3 = run_store.list_round_results(run_id, 3)
        ids_match(round3, expected_ids, "Round 3")
        require(all(row["status"] == "completed" and row["result"] for row in round3),
                "Round 3 contains an incomplete agent result.")
        require(all(row["result"].get("risk_flags") is not None for row in round3),
                "At least one Round-3 risk review is malformed.")
        require(
            all("case_data_integrity_flags" in row["result"] for row in round3),
            "Round 3 case-data integrity audit fields are missing.",
        )
        verify_position_transitions(round2, round3, "Round 3")
        await record_ollama_process_snapshot(gpu_telemetry, "after_round_3")

        round4_summary = await ensure_round(run_id, 4, metrics)
        report = run_store.get_final_report(run_id)
        require(report is not None, "Final Chair report was not saved.")
        await record_ollama_process_snapshot(gpu_telemetry, "after_round_4")
        require(bool(report.get("chair_conclusion", "").strip()), "Chair conclusion is empty.")
        require(report.get("consensus_status") in {
            "consensus", "qualified_consensus", "no_consensus", "insufficient_information"
        }, "Chair consensus status is invalid.")
        require(report.get("not_a_treatment_instruction") is True,
                "Chair report safety boundary missing.")
        require(report.get("evidence_retrieval_connected") is False,
                "Evidence boundary flag is missing.")
        require(
            report.get("report_title") == build_case_report_title(case),
            "Chair title contains fields not sourced from the verified case snapshot.",
        )
        require(
            bool(report.get("case_data_integrity_flags")),
            "Chair report did not include case-data integrity findings or an explicit no-flags note.",
        )
        require(
            run_store.get_run(run_id)["updated_at"] >= round4_summary["updated_at"],
            "Parent run updated_at was not advanced after the Chair stage.",
        )


        def position_counts(rows: list[dict], result_field: str) -> dict[str, int]:
            return dict(Counter(
                row[result_field].get("position")
                for row in rows
                if row.get(result_field) and row[result_field].get("position")
            ))

        position_counts_by_round = {
            "round_1": position_counts(round1, "assessment"),
            "round_2": position_counts(round2, "result"),
            "round_3": position_counts(round3, "result"),
        }
        final_positions = position_counts_by_round["round_3"]
        r1_positions = {row["agent_id"]: row["assessment"]["position"] for row in round1}
        r2_positions = {row["agent_id"]: row["result"]["position"] for row in round2}
        r3_positions = {row["agent_id"]: row["result"]["position"] for row in round3}
        final_modal = max(final_positions, key=final_positions.get)
        expected_minority_ids = {
            agent_id
            for agent_id in expected_ids
            if len({r1_positions[agent_id], r2_positions[agent_id], r3_positions[agent_id]}) > 1
            or (
                r3_positions[agent_id] in {"conditional", "supports", "opposes"}
                and r3_positions[agent_id] != final_modal
            )
        }
        chair_minority_text = " ".join(report.get("minority_and_dissenting_views") or [])
        require(
            all(agent_id in chair_minority_text for agent_id in expected_minority_ids),
            "Chair minority history omits at least one genuine position change or final non-modal view.",
        )
        stable_modal_insufficient = {
            agent_id for agent_id in expected_ids
            if r1_positions[agent_id] == r2_positions[agent_id] == r3_positions[agent_id] == final_modal
            and final_modal == "insufficient_information"
        }
        require(
            not any(agent_id in chair_minority_text for agent_id in stable_modal_insufficient),
            "Chair minority history incorrectly labels stable modal insufficient-information roles as dissent.",
        )
        if final_positions.get("supports") and final_positions.get("opposes"):
            expected_chair_status = "no_consensus"
        else:
            # Uniform labels do not establish a shared proposition or common option.
            expected_chair_status = "insufficient_information"
        require(
            report.get("consensus_status") == expected_chair_status,
            "Chair consensus status does not match the saved Round-3 position distribution.",
        )
        synthesis = report.get("overall_educational_synthesis", "")
        for round_name, counts in position_counts_by_round.items():
            label = round_name.replace("_", " ").title()
            require(f"{label}:" in synthesis, f"Chair synthesis omits {label} position counts.")
            for position, count in counts.items():
                expected_count = f"{count}/{sum(counts.values())} {position.replace('_', '-')}"
                require(
                    expected_count in synthesis,
                    f"Chair synthesis omits {expected_count} for {label}.",
                )
        require(bool(report.get("major_uncertainties")), "Chair major uncertainties are empty.")
        require(bool(report.get("missing_information_before_real_world_review")),
                "Chair missing-information section is empty.")
        require(bool(report.get("patient_and_family_considerations")),
                "Chair patient/family section is empty.")
        require(bool(report.get("feasibility_and_resource_considerations")),
                "Chair feasibility/resource section is empty.")
        require(bool(report.get("governance_and_safeguarding_considerations")),
                "Chair governance section is empty.")
        require(bool(report.get("evidence_limitations")),
                "Chair evidence limitations are empty.")

        # consensus_points must remain an empty list until proposition-level
        # provenance exists. It is not a completeness section that should be filled.
        validate_consensus_points(report)

        # Every applicable report section must contain source-grounded content or an
        # explicit statement that no applicable item was recorded.
        required_report_sections = (
            "unresolved_disagreements",
            "minority_and_dissenting_views",
            "major_uncertainties",
            "missing_information_before_real_world_review",
            "patient_and_family_considerations",
            "feasibility_and_resource_considerations",
            "governance_and_safeguarding_considerations",
            "evidence_limitations",
        )
        for section in required_report_sections:
            require(bool(report.get(section)), f"Chair report section is empty: {section}")
            require(
                all(isinstance(item, str) and item.strip() for item in report[section]),
                f"Chair report section contains a blank item: {section}",
            )
        report_text = " ".join(
            [report.get("chair_conclusion", ""), report.get("overall_educational_synthesis", "")]
            + [
                item
                for section in required_report_sections
                for item in report.get(section, [])
            ]
        ).casefold()
        if any(len(counts) > 1 for counts in position_counts_by_round.values()):
            for unsupported_claim in (
                "unanimously agreed",
                "unanimous consensus",
                "no dissent was present",
                "all agents agreed",
            ):
                require(
                    unsupported_claim not in report_text,
                    f"Chair report makes an unsupported unanimity claim: {unsupported_claim}",
                )
        if len(final_positions) > 1:
            require(bool(report.get("unresolved_disagreements")),
                    "Non-uniform Round-3 positions were not preserved.")
            require(bool(report.get("minority_and_dissenting_views")),
                    "Non-modal Round-3 positions were not listed separately.")
        # Check variety as a diagnostic only; it is not a clinical quality score.
        round1_conclusions = [
            row["assessment"]["provisional_conclusion"].strip().lower()
            for row in round1
        ]
        unique_conclusions = len(set(round1_conclusions))
        durations = [
            float(row["duration_seconds"])
            for row in round1 + round2 + round3
            if row.get("duration_seconds") is not None
        ]

        result_payload.update({
            "status": "passed_structural_live_validation",
            "round_summaries": {
                "round_1": round1_summary,
                "round_2": round2_summary,
                "round_3": round3_summary,
                "round_4": round4_summary,
            },
            "round_1_results": round1,
            "round_2_results": round2,
            "round_3_results": round3,
            "final_chair_report": report,
            "diagnostics": {
                "round_1_unique_conclusion_count": unique_conclusions,
                "round_1_total_conclusion_count": len(round1_conclusions),
                "median_agent_seconds_across_rounds_1_to_3": round(median(durations), 2) if durations else None,
                "total_agent_generations_saved": len(round1) + len(round2) + len(round3) + 1,
                "evidence_retrieval_connected": False,
                "clinical_accuracy_evaluated": False,
                "chair_position_counts_by_round": position_counts_by_round,
                "chair_consensus_status_reconciled": expected_chair_status,
                "consensus_points_empty_is_expected": not bool(report.get("consensus_points")),
            },
        })
    except Exception as exc:
        result_payload["status"] = "failed_live_validation"
        result_payload["error"] = f"{type(exc).__name__}: {exc}"
        if run_id:
            try:
                result_payload["partial_round_1"] = run_store.list_results(run_id)
                for number in (2, 3, 4):
                    try:
                        result_payload[f"partial_round_{number}"] = run_store.list_round_results(run_id, number)
                    except KeyError:
                        pass
            except Exception as nested:
                result_payload["partial_results_error"] = type(nested).__name__
        raise
    finally:
        stop_gpu_sampler.set()
        if gpu_sampler_task is not None:
            await gpu_sampler_task
        await record_ollama_process_snapshot(gpu_telemetry, "after_validation")
        if CPU_ONLY_VALIDATION:
            gpu_telemetry["summary"] = {
                "gpu_measured": False,
                "execution_mode": "github_hosted_cpu_only",
                "ollama_cpu_process_samples": len(gpu_telemetry["cpu_samples"]),
                "ollama_process_snapshots": len(gpu_telemetry["ollama_process_snapshots"]),
                "note": "No NVIDIA telemetry was collected or inferred from model allocation."
            }
        else:
            gpu_telemetry["summary"] = summarize_gpu_telemetry(
                gpu_telemetry["samples"],
                gpu_telemetry["ollama_process_snapshots"],
            )
        result_payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        result_payload["total_wall_seconds"] = round(time.perf_counter() - started_all, 2)
        result_payload["gpu_after"] = gpu_snapshot()
        result_payload["gpu_telemetry"] = gpu_telemetry
        artifact_path = ARTIFACT_DIR / ARTIFACT_NAME
        artifact_path.write_text(
            json.dumps(result_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"LIVE_VALIDATION_ARTIFACT={artifact_path}")
        print(f"LIVE_VALIDATION_STATUS={result_payload.get('status', 'failed_live_validation')}")
        print(f"LIVE_VALIDATION_RUN_ID={run_id}")
        print(f"LIVE_VALIDATION_SECONDS={result_payload['total_wall_seconds']}")


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:
        print(f"LIVE_VALIDATION_FAILED: {type(exc).__name__}: {exc}")
        raise
