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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.catalog import AGENT_PROFILES
from app.config import OLLAMA_MODEL
from app.schemas import SyntheticCase
from app.services import batch_runner, mdt_rounds, run_store
from app.services.ollama import get_ollama_status

ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
run_store.DB_PATH = ARTIFACT_DIR / "live_four_round_validation.sqlite3"

MAX_STAGE_ATTEMPTS = 2


def gpu_snapshot() -> str:
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


def build_case() -> SyntheticCase:
    """A fixed, fictional case used only for software integration validation."""
    return SyntheticCase(
        scenario_title="LIVE-VALIDATION-SYNTHETIC-01 — right vocal-cord SCC",
        case_summary=(
            "Fictional software-validation scenario only. A 75-year-old man has a "
            "1 x 1 cm lesion involving the right vocal cord and anterior commissure. "
            "Biopsy is described as squamous cell carcinoma. The synthetic history lists "
            "diabetes, hypertension, smoking, and alcohol use. It also records family "
            "support difficulties and prior difficulty adhering to planned appointments. "
            "No staging, cord mobility, imaging, pulmonary function, formal fitness, "
            "or complete work-up details are supplied. Do not infer missing facts."
        ),
        age_years=75,
        primary_site="Right vocal cord",
        histology="Squamous cell carcinoma",
        relevant_comorbidities=["Diabetes", "Hypertension"],
        social_context=[
            "Smoking and alcohol use recorded in the fictional scenario",
            "Family support difficulties recorded in the fictional scenario",
            "Prior difficulty adhering to planned appointments recorded in the fictional scenario",
        ],
        known_unknowns=[
            "Clinical T and N stage not supplied",
            "Vocal cord mobility and fixation status not supplied",
            "Imaging and endoscopic extent not supplied",
            "Performance status and formal fitness not supplied",
            "Renal, pulmonary, and hearing assessments not supplied",
            "Patient goals and preferences not supplied",
            "Dental, nutritional, and swallowing assessments not supplied",
        ],
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ids_match(rows: list[dict], expected: set[str], label: str) -> None:
    actual = {item["agent_id"] for item in rows}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    require(not missing and not extra, f"{label}: role mismatch; missing={missing}, extra={extra}")


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
    result_payload: dict = {
        "validation_type": "live_four_round_synthetic_integration",
        "synthetic_only": True,
        "started_at": started_at,
        "host_platform": platform.platform(),
        "python_version": sys.version,
        "ollama": runtime,
        "model": OLLAMA_MODEL,
        "gpu_before": gpu_snapshot(),
        "case_snapshot": json.loads(case_json),
        "case_snapshot_json": case_json,
        "case_snapshot_sha256": case_hash,
        "expected_agent_count": 45,
        "concurrency": 1,
        "metrics": metrics,
    }
    run_id = None

    try:
        created = run_store.create_run(case)
        run_id = created["run_id"]
        result_payload["run_id"] = run_id

        round1_summary = await ensure_round1(run_id, metrics)
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

        round2_summary = await ensure_round(run_id, 2, metrics)
        round2 = run_store.list_round_results(run_id, 2)
        ids_match(round2, expected_ids, "Round 2")
        require(all(row["status"] == "completed" and row["result"] for row in round2),
                "Round 2 contains an incomplete agent result.")
        require(all(row["result"].get("provisional_conclusion") for row in round2),
                "At least one Round-2 contribution lacks a conclusion.")

        round3_summary = await ensure_round(run_id, 3, metrics)
        round3 = run_store.list_round_results(run_id, 3)
        ids_match(round3, expected_ids, "Round 3")
        require(all(row["status"] == "completed" and row["result"] for row in round3),
                "Round 3 contains an incomplete agent result.")
        require(all(row["result"].get("risk_flags") is not None for row in round3),
                "At least one Round-3 risk review is malformed.")

        round4_summary = await ensure_round(run_id, 4, metrics)
        report = run_store.get_final_report(run_id)
        require(report is not None, "Final Chair report was not saved.")
        require(bool(report.get("chair_conclusion", "").strip()), "Chair conclusion is empty.")
        require(report.get("consensus_status") in {
            "consensus", "qualified_consensus", "no_consensus", "insufficient_information"
        }, "Chair consensus status is invalid.")
        require(report.get("not_a_treatment_instruction") is True,
                "Chair report safety boundary missing.")
        require(report.get("evidence_retrieval_connected") is False,
                "Evidence boundary flag is missing.")


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
        if final_positions.get("supports") and final_positions.get("opposes"):
            expected_chair_status = "no_consensus"
        elif final_positions.get("insufficient_information"):
            expected_chair_status = "insufficient_information"
        elif final_positions.get("conditional"):
            expected_chair_status = "qualified_consensus"
        elif final_positions.get("supports") or final_positions.get("opposes"):
            expected_chair_status = "consensus"
        else:
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

        # Every report section must contain source-grounded content or an explicit
        # statement that no applicable item was recorded. Empty arrays are not a pass.
        required_report_sections = (
            "consensus_points",
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
        if (
            final_positions.get("insufficient_information")
            and not final_positions.get("supports")
            and not final_positions.get("opposes")
        ):
            require(bool(report.get("consensus_points")),
                    "Chair did not summarize the lack of a definitive Round-3 treatment position.")

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
        result_payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        result_payload["total_wall_seconds"] = round(time.perf_counter() - started_all, 2)
        result_payload["gpu_after"] = gpu_snapshot()
        artifact_path = ARTIFACT_DIR / "live_four_round_validation.json"
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
