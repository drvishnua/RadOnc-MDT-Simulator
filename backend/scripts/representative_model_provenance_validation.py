"""Bounded live R2/R3 provenance check using the configured local Ollama endpoint.

This is a synthetic software integration check, not a clinical accuracy assessment.
It deliberately runs three representative roles and does not create a saved MDT run.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# This script is invoked by path from the installer workflow, so Python sets
# sys.path[0] to backend/scripts rather than the backend package root.
# Add the backend root explicitly before importing the application package.
BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.agents.catalog import AGENT_PROFILES
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import SyntheticCase
from app.services.chair_report_quality import build_source_opinion_review_coverage
from app.services.mdt_generation import (
    GENERATION_REQUEST_TIMEOUT_SECONDS,
    generate_adversarial_contribution,
    generate_debate_contribution,
)
from app.services.case_integrity import extract_attributed_note_opinions

ARTIFACT_DIR = BACKEND_DIR / "validation_artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "representative_model_provenance_validation.json"
ROLE_IDS = ("RO-01", "SO-02", "MO-01")
MAX_SECONDS_PER_GENERATION = GENERATION_REQUEST_TIMEOUT_SECONDS + 60.0


def _ollama_snapshot() -> dict:
    result: dict = {}
    for suffix, url in (
        ("version", f"{OLLAMA_BASE_URL}/api/version"),
        ("processes", f"{OLLAMA_BASE_URL}/api/ps"),
    ):
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                result[suffix] = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            result[f"{suffix}_error"] = f"{type(exc).__name__}: {exc}"
    try:
        result["cli_ps"] = subprocess.check_output(
            ["ollama", "ps"], text=True, timeout=8
        ).strip()
    except Exception as exc:
        result["cli_ps_error"] = f"{type(exc).__name__}: {exc}"
    return result


def _build_case() -> SyntheticCase:
    return SyntheticCase(
        scenario_title="Fictional source-attribution validation case",
        case_summary=(
            "Fictional educational record with incomplete staging and investigation data. "
            "The surgical oncology note favours a surgery-led assessment first, conditional "
            "on complete local staging and resectability review; the medical oncology note "
            "favours discussing a preoperative multimodality sequence, conditional on MRI "
            "staging, metastatic work-up and fitness assessment. "
            "Neither note supplies the missing investigations or establishes a final plan."
        ),
        known_unknowns=[
            "Clinical stage is not supplied.",
            "Required imaging and investigation results are not supplied.",
            "Performance status and patient goals are not supplied.",
        ],
    )


def _r1_fixture(role_id: str) -> dict:
    """Explicit non-model fixture: no stage, fitness, or treatment facts are asserted."""
    return {
        "position": "insufficient_information",
        "provisional_conclusion": (
            "The supplied fictional record does not establish clinical stage, "
            "investigation results, fitness, patient goals, or a definitive pathway."
        ),
        "preferred_educational_option": (
            "No educational pathway can be established from the supplied information."
        ),
        "disagreement_notes": [],
        "unknowns": [
            "Clinical stage and investigation results are not supplied.",
            "Fitness and patient goals are not supplied.",
        ],
        "case_facts": [],
        "evidence_claims": [],
        "not_a_treatment_instruction": True,
        "fixture_id": f"R1-FIXTURE:{role_id}",
    }


def _role_rows():
    by_id = {item["agent_id"]: item for item in AGENT_PROFILES}
    missing = sorted(set(ROLE_IDS) - set(by_id))
    if missing:
        raise RuntimeError(f"Configured representative roles are missing: {missing}")
    return [by_id[role_id] for role_id in ROLE_IDS]


async def _timed_call(label: str, callback, metrics: list[dict]):
    started = time.perf_counter()
    try:
        value = await asyncio.wait_for(callback(), timeout=MAX_SECONDS_PER_GENERATION)
    except Exception as exc:
        cause = exc.__cause__
        metrics.append({
            "stage": label,
            "wall_seconds": round(time.perf_counter() - started, 3),
            "status": "failed",
            "error_type": type(exc).__name__,
            "cause_type": type(cause).__name__ if cause is not None else None,
        })
        raise
    metrics.append({
        "stage": label,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "status": "completed",
    })
    return value


async def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    case = _build_case()
    case_json = case.model_dump_json(exclude_none=True)
    roles = _role_rows()
    expected_opinions = extract_attributed_note_opinions(case.case_summary)
    if len(expected_opinions) != 2:
        raise RuntimeError(
            "Validation fixture must yield exactly two server-extracted source opinions."
        )

    payload = {
        "validation_type": "representative_live_r2_r3_provenance",
        "execution_mode": "github_hosted_windows_cpu_only",
        "gpu_measured": False,
        "clinical_accuracy_evaluated": False,
        "evidence_retrieval_connected": False,
        "synthetic_only": True,
        "created_saved_mdt_run": False,
        "rounds_attempted": ["R2", "R3"],
        "rounds_completed": [],
        "r1_inputs": "Deterministic non-model fixture records; not presented as model assessments.",
        "r4_executed": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "host_platform": platform.platform(),
        "python_version": platform.python_version(),
        "model": OLLAMA_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
        "case_snapshot": json.loads(case_json),
        "case_snapshot_sha256": hashlib.sha256(case_json.encode("utf-8")).hexdigest(),
        "selected_roles": [
            {"agent_id": role["agent_id"], "name": role["name"], "category": role["category"]}
            for role in roles
        ],
        "server_source_opinion_register": expected_opinions,
        "ollama_before": _ollama_snapshot(),
        "generation_metrics": [],
        "round2": [],
        "round3": [],
        "source_opinion_coverage": [],
        "source_opinion_coverage_integrity": [],
        "quality_gate_failures": [],
        "status": "running",
    }

    try:
        if not payload["ollama_before"].get("version"):
            raise RuntimeError("Ollama version endpoint is not reachable.")
        # Round 2: each of the three roles sees the other two R1 fixture records.
        r2_by_id = {}
        for role in roles:
            role_id = role["agent_id"]
            peers = [
                {
                    "agent_id": peer["agent_id"],
                    "agent_name": peer["name"],
                    "assessment": _r1_fixture(peer["agent_id"]),
                }
                for peer in roles
                if peer["agent_id"] != role_id
            ]
            contribution = await _timed_call(
                f"R2:{role_id}",
                lambda role=role, role_id=role_id, peers=peers: generate_debate_contribution(
                    role, case, _r1_fixture(role_id), peers
                ),
                payload["generation_metrics"],
            )
            row = contribution.model_dump()
            r2_by_id[role_id] = row
            payload["round2"].append(row)
        payload["rounds_completed"].append("R2")

        # Round 3: each role receives the actual R2 records from the other two roles.
        r3_rows = []
        for role in roles:
            role_id = role["agent_id"]
            peer_views = [
                {
                    "agent_id": peer["agent_id"],
                    "agent_name": peer["name"],
                    "result": r2_by_id[peer["agent_id"]],
                }
                for peer in roles
                if peer["agent_id"] != role_id
            ]
            contribution = await _timed_call(
                f"R3:{role_id}",
                lambda role=role, role_id=role_id, peer_views=peer_views: generate_adversarial_contribution(
                    role,
                    case,
                    _r1_fixture(role_id),
                    r2_by_id[role_id],
                    peer_views,
                ),
                payload["generation_metrics"],
            )
            row = {
                "agent_id": role_id,
                "agent_name": role["name"],
                "status": "completed",
                "result": contribution.model_dump(),
            }
            r3_rows.append(row)
            payload["round3"].append(row)
        payload["rounds_completed"].append("R3")

        coverage, coverage_integrity = build_source_opinion_review_coverage(
            r3_rows, case.case_summary
        )
        payload["source_opinion_coverage"] = coverage
        payload["source_opinion_coverage_integrity"] = coverage_integrity

        failures = payload["quality_gate_failures"]
        expected_ids = {item["source_id"] for item in expected_opinions}
        for row in payload["round2"]:
            role_id = row["agent_id"]
            if row["source_reference_integrity_flags"]:
                failures.append({
                    "role": role_id,
                    "round": 2,
                    "type": "source_reference_integrity",
                    "details": row["source_reference_integrity_flags"],
                })
            if row["case_data_integrity_flags"]:
                failures.append({
                    "role": role_id,
                    "round": 2,
                    "type": "case_data_integrity",
                    "details": row["case_data_integrity_flags"],
                })

        for row in r3_rows:
            role_id = row["agent_id"]
            result = row["result"]
            if result["source_reference_integrity_flags"]:
                failures.append({
                    "role": role_id,
                    "round": 3,
                    "type": "source_reference_integrity",
                    "details": result["source_reference_integrity_flags"],
                })
            if result["case_data_integrity_flags"]:
                failures.append({
                    "role": role_id,
                    "round": 3,
                    "type": "case_data_integrity",
                    "details": result["case_data_integrity_flags"],
                })
            reviews = result["source_opinion_reviews"]
            review_ids = [review["source_id"] for review in reviews]
            if len(review_ids) != len(set(review_ids)) or set(review_ids) != expected_ids:
                failures.append({
                    "role": role_id,
                    "round": 3,
                    "type": "source_opinion_register_coverage",
                    "expected": sorted(expected_ids),
                    "actual": review_ids,
                })
            for review in reviews:
                if review["source_id"] in expected_ids:
                    expected_excerpt = next(
                        item["source_excerpt"]
                        for item in expected_opinions
                        if item["source_id"] == review["source_id"]
                    )
                    if review["source_excerpt"] != expected_excerpt:
                        failures.append({
                            "role": role_id,
                            "round": 3,
                            "type": "source_excerpt_mismatch",
                            "source_id": review["source_id"],
                        })
                    if review["evidence_validation_status"] != "verified":
                        failures.append({
                            "role": role_id,
                            "round": 3,
                            "type": "peer_evidence_not_verified",
                            "source_id": review["source_id"],
                            "evidence_validation_status": review["evidence_validation_status"],
                            "model_reported_option_status": review["model_reported_option_status"],
                            "model_reported_conditions_status": review["model_reported_conditions_status"],
                        })

        if coverage_integrity:
            failures.append({
                "type": "chair_source_opinion_coverage_integrity",
                "details": coverage_integrity,
            })
        if len(payload["generation_metrics"]) != 6:
            failures.append({
                "type": "generation_count",
                "expected": 6,
                "actual": len(payload["generation_metrics"]),
            })

        payload["status"] = "passed" if not failures else "failed_quality_gates"
        return 0 if not failures else 1
    except Exception as exc:
        payload["status"] = "execution_error"
        payload["execution_error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        payload["generation_attempt_count"] = len(payload["generation_metrics"])
        payload["generation_completed_count"] = sum(
            item.get("status") == "completed" for item in payload["generation_metrics"]
        )
        payload["generation_failed_count"] = sum(
            item.get("status") == "failed" for item in payload["generation_metrics"]
        )
        payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        payload["ollama_after"] = _ollama_snapshot()
        payload["total_generation_wall_seconds"] = round(
            sum(item["wall_seconds"] for item in payload["generation_metrics"]), 3
        )
        ARTIFACT_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"REPRESENTATIVE_MODEL_VALIDATION_ARTIFACT={ARTIFACT_PATH}")
        print(f"REPRESENTATIVE_MODEL_VALIDATION_STATUS={payload['status']}")
        print(f"REPRESENTATIVE_MODEL_VALIDATION_CALLS={len(payload['generation_metrics'])}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
