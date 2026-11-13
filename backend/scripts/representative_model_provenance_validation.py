"""Bounded live R2/R3/R4 validation using the configured local Ollama endpoint.

This is a synthetic software integration check, not a clinical accuracy assessment.
Three role fixtures and actual generated R2/R3 outputs are saved and reloaded from an
isolated temporary SQLite database for Chair synthesis; no full 45-role MDT is run.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
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
from app.services.chair_report_quality import (
    build_source_opinion_review_coverage,
    ensure_chair_report_completeness,
)
from app.services.mdt_generation import (
    GENERATION_REQUEST_TIMEOUT_SECONDS,
    generate_adversarial_contribution,
    generate_chair_report,
    generate_debate_contribution,
)
from app.services.case_integrity import extract_attributed_note_opinions
from app.services import run_store

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


def _chair_source_opinion_coverage_failures(
    chair_report,
    expected_opinions: list[dict],
    expected_role_ids: set[str],
) -> list[dict]:
    """Validate source-review coverage in its dedicated report section."""
    failures: list[dict] = []
    coverage_items = getattr(chair_report, "source_opinion_review_coverage", None)
    disagreements = getattr(chair_report, "unresolved_disagreements", None)

    if not isinstance(coverage_items, list):
        return [{
            "round": 4,
            "type": "chair_source_opinion_review_coverage_field_missing_or_invalid",
        }]
    if not isinstance(disagreements, list):
        failures.append({
            "round": 4,
            "type": "chair_unresolved_disagreements_field_missing_or_invalid",
        })
        disagreements = []

    misplaced = [
        item for item in disagreements
        if isinstance(item, str) and "source-opinion review coverage" in item.casefold()
    ]
    if misplaced:
        failures.append({
            "round": 4,
            "type": "chair_source_opinion_coverage_misplaced_in_disagreements",
            "matching_sections": misplaced,
        })

    expected_count = len(expected_role_ids)
    for source in expected_opinions:
        source_id = source["source_id"]
        matching = [
            item for item in coverage_items
            if isinstance(item, str)
            and source_id in item
            and "roles supplied an exact source-bound review" in item
        ]
        if len(matching) != 1:
            failures.append({
                "round": 4,
                "type": "chair_source_opinion_review_coverage",
                "source_id": source_id,
                "matching_sections": matching,
            })
            continue

        expected_summary = (
            f"{expected_count}/{expected_count} roles supplied an exact source-bound review"
        )
        if expected_summary not in matching[0]:
            failures.append({
                "round": 4,
                "type": "chair_source_opinion_review_coverage_incomplete",
                "source_id": source_id,
                "expected": expected_summary,
                "actual": matching[0],
            })

    return failures


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


def _persist_bounded_round_records(
    case: SyntheticCase,
    roles: list[dict],
    round2_rows: list[dict],
    round3_rows: list[dict],
    generation_metrics: list[dict],
) -> dict:
    """Persist three synthetic R1 fixtures and actual R2/R3 outputs in a disposable DB.

    This deliberately does not use create_round_job or run_mdt_round: those production
    paths correctly require all 45 preceding-role records. Only this isolated validation
    database contains three role rows per round. Its database file is removed on return.
    """
    expected_ids = {role["agent_id"] for role in roles}
    if len(expected_ids) != 3 or expected_ids != set(ROLE_IDS):
        raise ValueError("Bounded Chair validation requires the three configured representative roles.")

    original_data_dir = run_store.DATA_DIR
    original_db_path = run_store.DB_PATH
    original_legacy_path = run_store.LEGACY_DB_PATH
    temporary_db_path: Path | None = None
    result: dict | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="radonc-bounded-chair-r4-") as temporary_root:
            temporary_data_dir = Path(temporary_root)
            temporary_db_path = temporary_data_dir / "simulation_runs.sqlite3"
            run_store.DATA_DIR = temporary_data_dir
            run_store.DB_PATH = temporary_db_path
            run_store.LEGACY_DB_PATH = None

            run = run_store.create_run(case)
            run_id = run["run_id"]
            for role in roles:
                fixture = _r1_fixture(role["agent_id"])
                run_store.save_agent_success(
                    run_id,
                    role["agent_id"],
                    json.dumps(fixture, ensure_ascii=False),
                    0.0,
                )
            saved_round1 = run_store.list_results(run_id)
            completed_r1_ids = {
                row["agent_id"] for row in saved_round1
                if row["status"] == "completed" and row.get("assessment")
            }
            if completed_r1_ids != expected_ids or len(saved_round1) != 45:
                raise RuntimeError(
                    "Temporary R1 fixture persistence did not retain exactly three "
                    "completed representative roles in the 45-role run structure."
                )

            metrics_by_stage = {
                item["stage"]: item["wall_seconds"]
                for item in generation_metrics
                if item.get("status") == "completed"
            }
            saved_by_round: dict[int, list[dict]] = {}
            summaries: dict[int, dict] = {}

            for round_number, source_rows in ((2, round2_rows), (3, round3_rows)):
                rows_by_id = {row["agent_id"]: row for row in source_rows}
                if set(rows_by_id) != expected_ids or len(rows_by_id) != 3:
                    raise RuntimeError(
                        f"Round {round_number} does not contain exactly one completed "
                        "contribution from each representative role."
                    )
                now = datetime.now(timezone.utc).isoformat()
                with run_store._connect() as db:
                    run_store._ensure_round_tables(db)
                    db.execute(
                        """
                        INSERT INTO round_runs
                        (run_id, round_number, status, total_agents, current_agent_id,
                         created_at, updated_at, started_at, finished_at)
                        VALUES (?, ?, 'queued', 3, NULL, ?, ?, NULL, NULL)
                        """,
                        (run_id, round_number, now, now),
                    )
                    db.executemany(
                        """
                        INSERT INTO agent_round_results
                        (run_id, round_number, agent_id, agent_name, category_label, status)
                        VALUES (?, ?, ?, ?, ?, 'queued')
                        """,
                        [
                            (
                                run_id,
                                round_number,
                                role["agent_id"],
                                role["name"],
                                role.get("category_label", role.get("category", "Specialist")),
                            )
                            for role in roles
                        ],
                    )

                for role in roles:
                    role_id = role["agent_id"]
                    row = rows_by_id[role_id]
                    result_field = row.get("result")
                    if not isinstance(result_field, dict):
                        raise RuntimeError(
                            f"Round {round_number} {role_id} has no structured result to persist."
                        )
                    if result_field.get("agent_id") != role_id:
                        raise RuntimeError(
                            f"Round {round_number} stored contribution identity mismatch for {role_id}."
                        )
                    duration = metrics_by_stage.get(
                        f"R{round_number}:{role_id}", 0.0
                    )
                    run_store.save_round_success(
                        run_id,
                        round_number,
                        role_id,
                        json.dumps(result_field, ensure_ascii=False),
                        duration,
                    )
                run_store.mark_round_finished(run_id, round_number)
                summary = run_store.get_round_summary(run_id, round_number)
                persisted_rows = run_store.list_round_results(run_id, round_number)
                if (
                    summary["status"] != "completed"
                    or summary["completed_count"] != 3
                    or summary["failed_count"] != 0
                    or len(persisted_rows) != 3
                ):
                    raise RuntimeError(
                        f"Round {round_number} did not persist and reload as three "
                        "completed contributions."
                    )
                summaries[round_number] = summary
                saved_by_round[round_number] = persisted_rows

            # Prove this bounded fixture cannot accidentally enter the production
            # R2 orchestration path: that path still requires all 45 successful R1s.
            try:
                run_store.create_round_job(run_id, 2)
            except ValueError as exc:
                production_guard = str(exc)
                if "45 successful independent assessments" not in production_guard:
                    raise
            else:
                raise RuntimeError(
                    "Production R2 creation unexpectedly accepted only three R1 fixtures."
                )

            run_summary = run_store.get_run(run_id)
            if run_summary["patient_id"] is not None or run_summary["completed_count"] != 3:
                raise RuntimeError(
                    "Temporary bounded validation run has unexpected patient linkage or R1 count."
                )
            result = {
                "run_id": run_id,
                "round1_rows": saved_round1,
                "round2_rows": saved_by_round[2],
                "round3_rows": saved_by_round[3],
                "round_summaries": summaries,
                "run_summary": run_summary,
                "production_round2_guard": production_guard,
                "temporary_database_path": str(temporary_db_path),
                "temporary_database_deleted": False,
            }
    finally:
        run_store.DATA_DIR = original_data_dir
        run_store.DB_PATH = original_db_path
        run_store.LEGACY_DB_PATH = original_legacy_path

    if result is None:
        raise RuntimeError("Temporary SQLite persistence did not produce validation records.")
    result["temporary_database_deleted"] = (
        temporary_db_path is not None and not temporary_db_path.exists()
    )
    if not result["temporary_database_deleted"]:
        raise RuntimeError("Temporary Chair-validation SQLite database was not removed.")
    return result


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
        "created_temporary_sqlite_validation_run": False,
        "persisted_patient_record": False,
        "rounds_attempted": [],
        "rounds_completed": [],
        "r1_inputs": "Deterministic non-model fixture records; not presented as model assessments.",
        "r4_validation_mode": "Bounded three-role Chair synthesis; not the production 45-role R4 orchestration.",
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
        payload["rounds_attempted"].append("R2")
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
        payload["rounds_attempted"].append("R3")
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
        # Chair R4: persist and reload actual R2/R3 outputs beside explicitly labelled R1 fixtures.
        # The production run_mdt_round(run_id, 4) path is intentionally not called because it
        # correctly requires 45 completed R1, R2 and R3 contributions.
        round2_persist_rows = [
            {
                "agent_id": role["agent_id"],
                "agent_name": role["name"],
                "status": "completed",
                "result": r2_by_id[role["agent_id"]],
            }
            for role in roles
        ]
        bounded_store = _persist_bounded_round_records(
            case,
            roles,
            round2_persist_rows,
            r3_rows,
            payload["generation_metrics"],
        )
        payload["created_temporary_sqlite_validation_run"] = True
        payload["bounded_sqlite_persistence"] = {
            "temporary_run_id": bounded_store["run_id"],
            "temporary_database_deleted": bounded_store["temporary_database_deleted"],
            "patient_id": bounded_store["run_summary"]["patient_id"],
            "configured_role_count": bounded_store["run_summary"]["total_agents"],
            "completed_r1_fixture_roles": bounded_store["run_summary"]["completed_count"],
            "round2_summary": bounded_store["round_summaries"][2],
            "round3_summary": bounded_store["round_summaries"][3],
            "production_r2_guard": bounded_store["production_round2_guard"],
            "production_run_mdt_round_called": False,
            "full_45_role_mdt_completed": False,
        }

        payload["rounds_attempted"].append("R4")
        chair_draft = await _timed_call(
            "R4:SG-07",
            lambda: generate_chair_report(
                bounded_store["run_id"],
                case,
                bounded_store["round1_rows"],
                bounded_store["round2_rows"],
                bounded_store["round3_rows"],
            ),
            payload["generation_metrics"],
        )
        chair_report = ensure_chair_report_completeness(
            chair_draft,
            case,
            bounded_store["round1_rows"],
            bounded_store["round2_rows"],
            bounded_store["round3_rows"],
        )
        payload["r4_executed"] = True
        payload["rounds_completed"].append("R4")
        payload["chair_report"] = chair_report.model_dump()
        r4_failures = []
        if chair_report.consensus_status != "insufficient_information":
            r4_failures.append({
                "round": 4,
                "type": "chair_consensus_status",
                "expected": "insufficient_information",
                "actual": chair_report.consensus_status,
            })
        if chair_report.consensus_points:
            r4_failures.append({
                "round": 4,
                "type": "unsupported_proposition_consensus_points",
                "actual": chair_report.consensus_points,
            })
        if "No proposition-level consensus" not in chair_report.chair_conclusion:
            r4_failures.append({
                "round": 4,
                "type": "chair_conclusion_not_deterministically_reconciled",
                "actual": chair_report.chair_conclusion,
            })
        if not (
            chair_report.safety_boundary == "educational_simulation_only"
            and chair_report.not_a_treatment_instruction is True
            and chair_report.evidence_retrieval_connected is False
        ):
            r4_failures.append({
                "round": 4,
                "type": "chair_safety_boundary",
                "details": {
                    "safety_boundary": chair_report.safety_boundary,
                    "not_a_treatment_instruction": chair_report.not_a_treatment_instruction,
                    "evidence_retrieval_connected": chair_report.evidence_retrieval_connected,
                },
            })
        for unknown in case.known_unknowns or []:
            if unknown not in chair_report.major_uncertainties:
                r4_failures.append({
                    "round": 4,
                    "type": "case_unknown_not_retained_as_major_uncertainty",
                    "unknown": unknown,
                })
            if unknown not in chair_report.missing_information_before_real_world_review:
                r4_failures.append({
                    "round": 4,
                    "type": "case_unknown_not_retained_as_missing_information",
                    "unknown": unknown,
                })
        r4_failures.extend(
            _chair_source_opinion_coverage_failures(
                chair_report,
                expected_opinions,
                {role["agent_id"] for role in roles},
            )
        )
        r3_challenge_roles = {
            row["agent_id"]
            for row in r3_rows
            if any(
                isinstance(item, str) and item.strip()
                for item in (row["result"].get("substantive_challenges") or [])
            )
        }
        no_challenge_note = any(
            "No Round-3 role saved a substantive_challenges entry" in item
            for item in chair_report.unresolved_disagreements
        )
        if not r3_challenge_roles and not no_challenge_note:
            r4_failures.append({
                "round": 4,
                "type": "chair_omitted_zero_r3_challenge_disclosure",
            })
        for role_id in sorted(r3_challenge_roles):
            if not any(
                f"Round 3 recorded challenge — {role_id} (" in item
                for item in chair_report.unresolved_disagreements
            ):
                r4_failures.append({
                    "round": 4,
                    "type": "chair_omitted_saved_r3_challenge",
                    "role_id": role_id,
                })
        payload["r4_validation"] = {
            "status": "passed" if not r4_failures else "failed",
            "round1_fixture_completed_roles": len({
                row["agent_id"] for row in bounded_store["round1_rows"]
                if row["status"] == "completed" and row.get("assessment")
            }),
            "round2_completed_roles_reloaded_from_sqlite": bounded_store["round_summaries"][2]["completed_count"],
            "round3_completed_roles_reloaded_from_sqlite": bounded_store["round_summaries"][3]["completed_count"],
            "chair_model_call_completed": True,
            "consensus_status": chair_report.consensus_status,
            "consensus_points": chair_report.consensus_points,
            "position_evolution": {
                "round1": chair_report.overall_educational_synthesis.split("Round 2:")[0],
                "round2": chair_report.overall_educational_synthesis.split("Round 2:")[-1].split("Round 3:")[0],
                "round3": chair_report.overall_educational_synthesis.split("Round 3:")[-1],
            },
            "r3_roles_with_substantive_challenges": len(r3_challenge_roles),
            "r3_challenge_role_ids": sorted(r3_challenge_roles),
            "r3_roles_with_risk_flags": sum(
                bool(row["result"].get("risk_flags")) for row in r3_rows
            ),
            "zero_r3_challenge_disclosed_in_chair_report": no_challenge_note,
            "quality_gate_failures": r4_failures,
        }
        payload["quality_gate_failures"].extend(r4_failures)

        if len(payload["generation_metrics"]) != 7:
            failures.append({
                "type": "generation_count",
                "expected": 7,
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
