"""Resume the saved hosted CPU MDT checkpoint at R3 without repeating R1 or R2."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts"
DB_PATH = ARTIFACT_DIR / "live_four_round_hosted_cpu_validation.sqlite3"
MANIFEST_PATH = Path(os.environ.get("RADONC_CHECKPOINT_MANIFEST", ""))
RESUME_MANIFEST_PATH = ARTIFACT_DIR / "live_four_round_hosted_cpu_resume_manifest.json"
REPORT_PATH = ARTIFACT_DIR / "live_four_round_hosted_cpu_resume_validation.json"
EXPECTED_SOURCE_SHA = "4683b0767bf5cade408e85ec31ef248b34e5321e"
EXPECTED_SOURCE_RUN = "43714529807"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from app.agents.catalog import AGENT_PROFILES
from app.config import OLLAMA_MODEL
from app.services import mdt_rounds, run_store
from app.services.case_integrity import build_case_report_title, build_source_case_facts
from app.services.chair_report_quality import validate_consensus_points
from live_four_round_validation import (
    _collect_integrity_quality_gate_failures,
    verify_position_transitions,
)

ROLE_IDS = {item["agent_id"] for item in AGENT_PROFILES}
run_store.DB_PATH = DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _require_roles(rows: list[dict], field: str, label: str) -> None:
    ids = [row.get("agent_id") for row in rows]
    counts = Counter(ids)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    missing = sorted(ROLE_IDS - set(ids))
    extra = sorted(set(ids) - ROLE_IDS)
    incomplete = sorted(
        row.get("agent_id", "<missing>")
        for row in rows
        if row.get("status") != "completed" or not isinstance(row.get(field), dict)
    )
    if duplicates or missing or extra or incomplete:
        raise RuntimeError(
            f"{label} role coverage invalid: missing={missing}, extra={extra}, "
            f"duplicates={duplicates}, incomplete={incomplete}"
        )


def _position_counts(rows: list[dict], field: str) -> dict[str, int]:
    return dict(Counter(
        row[field].get("position")
        for row in rows
        if isinstance(row.get(field), dict) and row[field].get("position")
    ))


def _validate_chair_position_counts(
    synthesis: str,
    positions_by_round: dict[str, dict[str, int]],
) -> None:
    """Validate each deterministic position distribution in its own Chair round section.

    The Chair report uses human-readable labels such as "Round 1:", not necessarily
    the abbreviated keys ("R1:") used by the validator. Counts must appear under
    their corresponding round label; a count elsewhere in the prose is insufficient.
    """
    marker = re.search(
        r"\bRecorded\s+position\s+distribution\s*[—–-]\s*",
        synthesis,
        flags=re.IGNORECASE,
    )
    if marker is None:
        raise RuntimeError("Chair synthesis omits deterministic round position counts.")

    distribution = synthesis[marker.end():]
    sections: dict[str, str] = {}
    section_pattern = re.compile(
        r"(?:^|;)\s*(?:Round\s+(?P<word>[123])|R(?P<short>[123]))\s*:\s*(?P<counts>[^;.\n]+)",
        flags=re.IGNORECASE,
    )
    for match in section_pattern.finditer(distribution):
        round_number = match.group("word") or match.group("short")
        label = f"R{round_number}"
        if label in sections:
            raise RuntimeError(f"Chair synthesis repeats {label} position counts.")
        sections[label] = match.group("counts").strip()

    for label, counts in positions_by_round.items():
        if label not in sections:
            raise RuntimeError(f"Chair synthesis omits {label} position counts.")
        denominator = sum(counts.values())
        if denominator != len(ROLE_IDS):
            raise RuntimeError(
                f"Saved {label} positions cover {denominator}/{len(ROLE_IDS)} roles."
            )
        section = sections[label]
        for position, count in counts.items():
            position_label = position.replace("_", "-")
            expected = re.compile(
                rf"(?<!\d){count}/{denominator}\s+{re.escape(position_label)}(?![A-Za-z0-9_-])",
                flags=re.IGNORECASE,
            )
            if expected.search(section) is None:
                raise RuntimeError(
                    f"Chair synthesis omits {label} count "
                    f"{count}/{denominator} {position_label}."
                )



def _round_generation_required(round_summary: dict | None, round_label: str, *, audit_only: bool) -> bool:
    """Return whether a missing/incomplete round may be generated in this execution mode."""
    if round_summary and round_summary.get("status") == "completed":
        return False
    if audit_only:
        status = round_summary.get("status") if isinstance(round_summary, dict) else "missing"
        raise RuntimeError(
            f"Audit-only mode requires {round_label} to be completed; found status={status!r}. "
            "Inference is prohibited in audit-only mode."
        )
    return True

def _validate_checkpoint(manifest: dict, checkpoint_run_id: str, model_digest: str) -> None:
    source = manifest.get("source") or {}
    resume = manifest.get("resume_checkpoint") or {}
    latest_run = str(resume.get("checkpoint_workflow_run_id") or source.get("workflow_run_id") or "")
    if latest_run != checkpoint_run_id:
        raise RuntimeError(
            f"Manifest checkpoint run {latest_run!r} does not match requested run {checkpoint_run_id!r}."
        )
    if str(source.get("workflow_run_id")) != EXPECTED_SOURCE_RUN:
        raise RuntimeError("Checkpoint lineage does not identify the original timed-out run.")
    if source.get("commit_sha") != EXPECTED_SOURCE_SHA:
        raise RuntimeError("Checkpoint source SHA differs from the saved database source revision.")
    execution = manifest.get("execution") or {}
    if execution.get("mode") != "github_hosted_cpu_only" or execution.get("gpu_measured") is not False:
        raise RuntimeError("Checkpoint is not explicitly marked as CPU-only.")
    if execution.get("agent_concurrency") != 1 or execution.get("expected_role_count") != 45:
        raise RuntimeError("Checkpoint execution contract is not 45 roles at concurrency 1.")
    expected_digest = str((manifest.get("model") or {}).get("digest") or "")
    if not expected_digest or model_digest != expected_digest:
        raise RuntimeError("Installed model digest differs from checkpoint; refusing mixed-model continuation.")


async def main() -> int:
    started = time.perf_counter()
    checkpoint_run_id = os.environ.get("RADONC_CHECKPOINT_RUN_ID", EXPECTED_SOURCE_RUN).strip()
    current_run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    current_sha = os.environ.get("GITHUB_SHA", "").strip()
    model_digest = os.environ.get("RADONC_MODEL_DIGEST", "").strip()
    audit_only = os.environ.get("RADONC_AUDIT_ONLY", "").strip() == "1"
    run_id: str | None = None
    checkpoint_database_sha256_before: str | None = None
    report: dict = {
        "validation_type": (
            "audited_saved_four_round_hosted_cpu_synthetic_integration"
            if audit_only
            else "resumed_full_four_round_hosted_cpu_synthetic_integration"
        ),
        "status": "not_started",
        "audit_only": audit_only,
        "inference_performed": False,
        "execution_mode": "github_hosted_cpu_only",
        "gpu_measured": False,
        "clinical_accuracy_evaluated": False,
        "evidence_retrieval_connected": False,
        "model": OLLAMA_MODEL,
        "model_digest": model_digest,
        "checkpoint_workflow_run_id": checkpoint_run_id,
        "resume_workflow_run_id": current_run_id,
        "resume_commit_sha": current_sha,
        "expected_role_count": 45,
        "concurrency": 1,
        "quality_gate_failures": [],
    }
    exit_code = 1

    try:
        if not current_run_id or not current_sha or not model_digest:
            raise RuntimeError("Current workflow identity or installed model digest is missing.")
        if not MANIFEST_PATH.is_file() or not DB_PATH.is_file():
            raise RuntimeError("Restored manifest or SQLite checkpoint is missing.")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
        _validate_checkpoint(manifest, checkpoint_run_id, model_digest)
        with sqlite3.connect(DB_PATH) as db:
            integrity = db.execute("PRAGMA integrity_check").fetchone()
            stored_runs = db.execute(
                "SELECT run_id, patient_id, case_version_id, case_json FROM simulation_runs"
            ).fetchall()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError(f"Restored SQLite integrity_check failed: {integrity!r}")
        if len(stored_runs) != 1:
            raise RuntimeError(f"Expected one synthetic run in checkpoint; found {len(stored_runs)}.")

        if not audit_only:
            # Update lineage before inference. An interrupted continuation can therefore
            # upload this new checkpoint and be resumed again without losing completed work.
            history = list(manifest.get("resume_history") or [])
            history.append({
                "workflow_run_id": current_run_id,
                "commit_sha": current_sha,
                "started_at": _now(),
                "previous_checkpoint_run_id": checkpoint_run_id,
            })
            manifest["resume_history"] = history
            manifest["resume_checkpoint"] = {
                "checkpoint_workflow_run_id": current_run_id,
                "commit_sha": current_sha,
                "started_at": _now(),
                "source_checkpoint_workflow_run_id": checkpoint_run_id,
            }
            RESUME_MANIFEST_PATH.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        run_id, patient_id, case_version_id, case_json = stored_runs[0]
        run_id = str(run_id)
        if patient_id is not None or case_version_id is not None:
            raise RuntimeError("Synthetic checkpoint is linked to a patient registry record.")
        from app.schemas import SyntheticCase
        case = SyntheticCase.model_validate_json(case_json)
        if case.scenario_title != "Synthetic head-and-neck case":
            raise RuntimeError("Checkpoint case does not match the approved synthetic fixture.")
        case_hash = hashlib.sha256(case_json.encode("utf-8")).hexdigest()
        run_summary = run_store.get_run(run_id)
        if run_summary["total_agents"] != 45 or run_summary["completed_count"] != 45:
            raise RuntimeError("Checkpoint does not contain 45 completed R1 assessments.")

        round1 = run_store.list_results(run_id)
        _require_roles(round1, "assessment", "R1")
        expected_facts = build_source_case_facts(case)
        if any(row["assessment"].get("case_facts") != expected_facts for row in round1):
            raise RuntimeError("Saved R1 case-fact registers differ from the immutable case snapshot.")
        if any(row["assessment"].get("not_a_treatment_instruction") is not True for row in round1):
            raise RuntimeError("A saved R1 contribution lacks the educational safety boundary.")
        if any(row["assessment"].get("evidence_claims") for row in round1):
            raise RuntimeError("R1 contains evidence claims while evidence retrieval is disconnected.")

        round2_summary = run_store.get_round_summary(run_id, 2)
        if round2_summary["status"] != "completed" or round2_summary["completed_count"] != 45:
            raise RuntimeError("Checkpoint R2 is not complete; R3 continuation is unsafe.")
        round2 = run_store.list_round_results(run_id, 2)
        _require_roles(round2, "result", "R2")

        round3_summary_before = run_store.get_round_summary(run_id, 3)
        if round3_summary_before["status"] not in {"running", "queued", "completed_with_errors", "completed"}:
            raise RuntimeError(f"Unsupported R3 checkpoint status: {round3_summary_before['status']}")
        round3_before = run_store.list_round_results(run_id, 3)
        completed_before = {
            row["agent_id"]: json.dumps(row["result"], sort_keys=True, ensure_ascii=False)
            for row in round3_before
            if row.get("status") == "completed" and row.get("result")
        }
        if not set(completed_before).issubset(ROLE_IDS):
            raise RuntimeError("Checkpoint R3 contains an unknown completed role.")
        report["case_snapshot_sha256"] = case_hash
        report["run_id"] = run_id
        report["r1_completed_before_resume"] = len(round1)
        report["r2_completed_before_resume"] = len(round2)
        report["r3_completed_before_resume"] = len(completed_before)
        report["r3_remaining_before_resume"] = 45 - len(completed_before)
        checkpoint_database_sha256_before = _sha256(DB_PATH)
        report["checkpoint_database_sha256_before_resume"] = checkpoint_database_sha256_before

        if _round_generation_required(round3_summary_before, "R3", audit_only=audit_only):
            mdt_rounds.prepare_round_resume(run_id, 3)
            ready = run_store.get_round_summary(run_id, 3)
            if ready["completed_count"] != len(completed_before) or ready["failed_count"] or ready["running_count"]:
                raise RuntimeError("R3 resume preparation changed saved completions or left interrupted rows running.")
            resume_started = time.perf_counter()
            report["inference_performed"] = True
            await mdt_rounds.run_mdt_round(run_id, 3)
            report["r3_resume_seconds"] = round(time.perf_counter() - resume_started, 2)

        round3_summary = run_store.get_round_summary(run_id, 3)
        round3 = run_store.list_round_results(run_id, 3)
        if round3_summary["status"] != "completed" or round3_summary["completed_count"] != 45:
            report["status"] = "incomplete_r3"
            report["partial_round3_results"] = round3
            raise RuntimeError("R3 is incomplete; Chair R4 was not started.")
        _require_roles(round3, "result", "R3")
        for agent_id, previous_json in completed_before.items():
            current = next(row for row in round3 if row["agent_id"] == agent_id)
            if json.dumps(current["result"], sort_keys=True, ensure_ascii=False) != previous_json:
                raise RuntimeError(f"Previously completed R3 contribution was overwritten: {agent_id}")

        verify_position_transitions(round1, round2, "Round 2")
        verify_position_transitions(round2, round3, "Round 3")

        try:
            round4_before = run_store.get_round_summary(run_id, 4)
        except KeyError:
            round4_before = None
            if not audit_only:
                run_store.create_round_job(run_id, 4)
        if _round_generation_required(round4_before, "Chair R4", audit_only=audit_only):
            if round4_before:
                mdt_rounds.prepare_round_resume(run_id, 4)
            chair_started = time.perf_counter()
            report["inference_performed"] = True
            await mdt_rounds.run_mdt_round(run_id, 4)
            report["chair_r4_seconds"] = round(time.perf_counter() - chair_started, 2)

        round4_summary = run_store.get_round_summary(run_id, 4)
        chair = run_store.get_final_report(run_id)
        if round4_summary["status"] != "completed" or round4_summary["completed_count"] != 1 or not chair:
            raise RuntimeError("Chair R4 did not save one completed report.")
        if not str(chair.get("chair_conclusion") or "").strip():
            raise RuntimeError("Chair conclusion is empty.")
        if chair.get("not_a_treatment_instruction") is not True or chair.get("evidence_retrieval_connected") is not False:
            raise RuntimeError("Chair safety/evidence boundary is absent or inconsistent.")
        if chair.get("report_title") != build_case_report_title(case):
            raise RuntimeError("Chair title contains unsupported case-derived content.")
        validate_consensus_points(chair)

        positions = {
            "R1": _position_counts(round1, "assessment"),
            "R2": _position_counts(round2, "result"),
            "R3": _position_counts(round3, "result"),
        }
        expected_consensus = (
            "no_consensus"
            if positions["R3"].get("supports") and positions["R3"].get("opposes")
            else "insufficient_information"
        )
        if chair.get("consensus_status") != expected_consensus:
            raise RuntimeError("Chair consensus status disagrees with deterministic R3 position safeguards.")
        synthesis = str(chair.get("overall_educational_synthesis") or "")
        _validate_chair_position_counts(synthesis, positions)

        failures = _collect_integrity_quality_gate_failures([
            ("R1", round1, "assessment"),
            ("R2", round2, "result"),
            ("R3", round3, "result"),
            ("R4", [{"agent_id": "SG-07", "report": chair}], "report"),
        ])
        report.update({
            "status": (\n                "completed_with_quality_gate_failures" if failures\n                else ("passed_structural_checkpoint_audit" if audit_only else "passed_structural_live_validation")\n            ),
            "round_summaries_after": {
                "R1": run_summary,
                "R2": round2_summary,
                "R3": round3_summary,
                "R4": round4_summary,
            },
            "position_counts_by_round": positions,
            "chair_consensus_status": chair.get("consensus_status"),
            "quality_gate_passed": not bool(failures),
            "quality_gate_failures": failures,
            "round1_results": round1,
            "round2_results": round2,
            "round3_results": round3,
            "final_chair_report": chair,
            "saved_contribution_count": 136,
        })
        exit_code = 1 if failures else 0

    except Exception as exc:
        if report.get("status") != "incomplete_r3":
            report["status"] = "failed_resume_validation"
        report["error"] = f"{type(exc).__name__}: {exc}"
        if run_id:
            try:
                report["partial_round3_results"] = run_store.list_round_results(run_id, 3)
            except Exception:
                pass
            try:
                report["partial_round4_results"] = run_store.list_round_results(run_id, 4)
            except Exception:
                pass
        exit_code = 1
    finally:
        report["finished_at"] = _now()
        report["total_wall_seconds"] = round(time.perf_counter() - started, 2)
        if DB_PATH.is_file():
            report["sqlite_database_sha256"] = _sha256(DB_PATH)
        if audit_only:
            report["model_process_after"] = "NOT_CAPTURED_AUDIT_ONLY"
            database_sha_after = _sha256(DB_PATH) if DB_PATH.is_file() else None
            report["checkpoint_database_sha256_after_audit"] = database_sha_after
            report["checkpoint_database_unchanged"] = (
                checkpoint_database_sha256_before is not None
                and database_sha_after == checkpoint_database_sha256_before
            )
            if not report["checkpoint_database_unchanged"]:
                report["status"] = "failed_audit_database_mutation"
                report["error"] = "Audit-only validation changed the restored SQLite database; checkpoint was not preserved byte-for-byte."
                exit_code = 1
        else:
            try:
                import urllib.request
                url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11435").rstrip("/") + "/api/ps"
                with urllib.request.urlopen(url, timeout=5) as response:
                    report["model_process_after"] = json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                report["model_process_snapshot_error"] = type(exc).__name__
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"RESUME_VALIDATION_ARTIFACT={REPORT_PATH}")
        print(f"RESUME_VALIDATION_STATUS={report.get('status')}")
        print(f"RESUME_VALIDATION_RUN_ID={run_id}")
        print(f"RESUME_VALIDATION_SECONDS={report['total_wall_seconds']}")
        print(f"RESUME_VALIDATION_QUALITY_FLAGS={len(report.get('quality_gate_failures') or [])}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
