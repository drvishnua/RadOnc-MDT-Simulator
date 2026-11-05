"""Run a bounded, multi-case live synthetic MDT stress suite on local Ollama.

This is an integration and process-safety harness, not a clinical accuracy evaluator.
Run on the connected Windows laptop only after reviewing the case library.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.catalog import AGENT_PROFILES
from app.config import OLLAMA_MODEL
from app.services import batch_runner, mdt_rounds, run_store
from app.services.case_integrity import build_source_case_facts
from app.services.ollama import get_ollama_status
from app.services.stress_testing import audit_case_outputs, load_stress_cases

ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts" / "stress_suite"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
run_store.DB_PATH = ARTIFACT_DIR / "stress_suite.sqlite3"
EXPECTED_IDS = {item["agent_id"] for item in AGENT_PROFILES}


def gpu_snapshot() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader"],
            text=True, timeout=8,
        ).strip()
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_rows(rows: list[dict], field: str, label: str) -> None:
    actual = {row["agent_id"] for row in rows}
    require(actual == EXPECTED_IDS, f"{label} role set mismatch: missing={sorted(EXPECTED_IDS-actual)}, extra={sorted(actual-EXPECTED_IDS)}")
    failures = [row["agent_id"] for row in rows if row.get("status") != "completed" or not isinstance(row.get(field), dict)]
    require(not failures, f"{label} contains failed/missing outputs: {failures}")


async def run_one(item: dict[str, Any]) -> dict[str, Any]:
    case = item["case"]
    case_json = case.model_dump_json(exclude_none=True)
    case_hash = hashlib.sha256(case_json.encode("utf-8")).hexdigest()
    metrics: dict[str, Any] = {"round_seconds": {}, "agent_generations_expected": 136}
    started = time.perf_counter()
    created = run_store.create_run(case)
    run_id = created["run_id"]
    output: dict[str, Any] = {
        "case_id": item["case_id"], "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "case_snapshot": json.loads(case_json), "case_snapshot_sha256": case_hash,
        "oracle_checks": item["oracle_checks"], "status": "running",
    }
    try:
        t = time.perf_counter()
        await batch_runner.run_independent_assessments(run_id)
        r1_summary = run_store.get_run(run_id)
        require(r1_summary["status"] == "completed" and r1_summary["completed_count"] == 45 and r1_summary["failed_count"] == 0,
                f"{item['case_id']} R1 incomplete: {r1_summary}")
        r1 = run_store.list_results(run_id)
        verify_rows(r1, "assessment", "R1")
        require(all(row["assessment"].get("case_facts") == build_source_case_facts(case) for row in r1),
                "R1 source facts differ from immutable case snapshot.")
        require(run_store.get_run(run_id)["case_snapshot_sha256"] == case_hash, "Persisted case hash mismatch.")
        metrics["round_seconds"]["R1"] = round(time.perf_counter() - t, 2)

        rounds: dict[int, list[dict]] = {}
        for number in (2, 3, 4):
            t = time.perf_counter()
            run_store.create_round_job(run_id, number)
            await mdt_rounds.run_mdt_round(run_id, number)
            summary = run_store.get_round_summary(run_id, number)
            require(summary["status"] == "completed" and summary["completed_count"] == summary["total_agents"] and summary["failed_count"] == 0,
                    f"{item['case_id']} R{number} incomplete: {summary}")
            rows = run_store.list_round_results(run_id, number)
            if number in (2, 3):
                verify_rows(rows, "result", f"R{number}")
                rounds[number] = rows
            else:
                require(len(rows) == 1 and rows[0]["agent_id"] == "SG-07" and rows[0]["status"] == "completed",
                        "R4 Chair output missing or incomplete.")
            r4 = rows
            metrics["round_seconds"][f"R{number}"] = round(time.perf_counter() - t, 2)

        rounds[1] = r1
        chair = run_store.get_final_report(run_id)
        require(isinstance(chair, dict), "Chair report not persisted.")
        require(chair.get("not_a_treatment_instruction") is True, "Chair safety boundary missing.")
        require(chair.get("evidence_retrieval_connected") is False, "Evidence-retrieval boundary missing.")
        findings = audit_case_outputs(item["case_id"], case, rounds, chair)
        output.update({
            "status": "completed_with_findings" if findings else "completed_no_process_findings",
            "metrics": metrics,
            "round_summaries": {str(n): run_store.get_round_summary(run_id, n) for n in (2, 3, 4)},
            "round_1_results": r1,
            "round_2_results": rounds[2],
            "round_3_results": rounds[3],
            "round_4_results": r4,
            "position_counts": {
                "R1": _position_counts(r1, "assessment"),
                "R2": _position_counts(rounds[2], "result"),
                "R3": _position_counts(rounds[3], "result"),
            },
            "process_safety_findings": findings,
            "chair_report": chair,
            "total_seconds": round(time.perf_counter() - started, 2),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:
        output.update({"status": "failed_or_incomplete", "error": f"{type(exc).__name__}: {exc}",
                       "total_seconds": round(time.perf_counter() - started, 2),
                       "completed_at": datetime.now(timezone.utc).isoformat()})
        try:
            output["partial_round_1"] = run_store.list_results(run_id)
            for n in (2, 3, 4):
                try:
                    output[f"partial_round_{n}"] = run_store.list_round_results(run_id, n)
                except KeyError:
                    pass
        except Exception as nested:
            output["partial_capture_error"] = type(nested).__name__
    return output


def _position_counts(rows: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        payload = row.get(field) or {}
        position = payload.get("position")
        if position:
            counts[position] = counts.get(position, 0) + 1
    return counts


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-ids", default="MDT-002,MDT-003,MDT-004,MDT-005,MDT-006,MDT-007")
    parser.add_argument("--case-file", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=ARTIFACT_DIR / "stress_suite_report.json")
    args = parser.parse_args()

    selected_ids = {value.strip() for value in args.case_ids.split(",") if value.strip()}
    cases = load_stress_cases(args.case_file) if args.case_file else load_stress_cases()
    cases = [item for item in cases if item["case_id"] in selected_ids]
    require({item["case_id"] for item in cases} == selected_ids, "One or more requested case IDs are absent from the library.")
    require(len(EXPECTED_IDS) == 45, f"Expected 45 roles, found {len(EXPECTED_IDS)}.")
    runtime = await get_ollama_status()
    require(runtime.get("reachable") is True, "Local Ollama is unreachable.")
    require(runtime.get("configured_model_installed") is True, f"Configured model {OLLAMA_MODEL} is not installed.")

    try:
        simulator_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, timeout=5).strip()
    except Exception:
        simulator_commit = "unavailable"
    report: dict[str, Any] = {
        "suite_version": "1.0", "synthetic_only": True,
        "simulator_commit": simulator_commit,
        "branch": "feature/four-round-mdt-and-performance",
        "prompt_schema_version": "repository-head-unversioned",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "host_platform": platform.platform(), "python_version": sys.version,
        "model": OLLAMA_MODEL, "ollama": runtime, "concurrency": 1,
        "gpu_before": gpu_snapshot(), "selected_case_ids": [item["case_id"] for item in cases],
        "estimated_agent_generations": len(cases) * 136, "cases": [],
    }
    for item in cases:
        print(f"STRESS_CASE_START={item['case_id']}", flush=True)
        result = await run_one(item)
        report["cases"].append(result)
        print(f"STRESS_CASE_END={item['case_id']} STATUS={result['status']}", flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        report["updated_at"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["gpu_after"] = gpu_snapshot()
    report["summary"] = {
        "completed": sum(item["status"].startswith("completed") for item in report["cases"]),
        "failed_or_incomplete": sum(item["status"] == "failed_or_incomplete" for item in report["cases"]),
        "cases_with_process_findings": sum(bool(item.get("process_safety_findings")) for item in report["cases"]),
        "hard_fail_findings": sum(1 for item in report["cases"] for finding in item.get("process_safety_findings", []) if finding["severity"] == "hard_fail"),
        "major_findings": sum(1 for item in report["cases"] for finding in item.get("process_safety_findings", []) if finding["severity"] == "major"),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STRESS_SUITE_REPORT={args.output}")
    print(f"STRESS_SUITE_SUMMARY={json.dumps(report['summary'])}")
    return 0 if report["summary"]["failed_or_incomplete"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
