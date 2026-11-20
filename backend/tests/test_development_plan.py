"""Adversarial regression tests for the fail-closed development gate."""
from copy import deepcopy

import pytest

from scripts.validate_development_plan import (
    GateError,
    STEP_ALLOWED_PATHS,
    STEP_ORDER,
    STEP_REQUIRED_WORKFLOWS,
    validate_plan,
)

EVIDENCE_SHA = "a" * 40
BASELINE_SHA = "5680dfe742c87ada5a263656f12686369d00fa6c"
WORKFLOWS = [
    "Windows Installer Build",
    "GitHub-hosted Windows Packaging Prerequisites",
    "Backend Tests",
    "Patient Registry and Four-Round Dashboard Browser E2E",
    "Frontend Build",
    "Security and Dependency Audit",
]


def _fixture():
    steps = []
    for index, step_id in enumerate(STEP_ORDER):
        steps.append(
            {
                "id": step_id,
                "title": step_id,
                "status": "VERIFIED" if index == 0 else ("IN PROGRESS" if index == 1 else "BLOCKED"),
                "depends_on": [] if index == 0 else [STEP_ORDER[index - 1]],
                "required_workflow_names": (
                    WORKFLOWS if index == 0 else
                    ["Sequential Development Gate", "Backend Tests", "Security and Dependency Audit"] if index == 1 else
                    ["Sequential Development Gate"]
                ),
                "allowed_paths": list(STEP_ALLOWED_PATHS[step_id]),
                "completion_evidence": (
                    {
                        "commit_sha": EVIDENCE_SHA,
                        "workflow_runs": [
                            {"id": 1000 + i, "name": name}
                            for i, name in enumerate(WORKFLOWS)
                        ],
                    }
                    if index == 0
                    else None
                ),
            }
        )
    plan = {
        "schema_version": 1,
        "plan_id": "radonc-mdt-master-sequential-plan",
        "scope_baseline_commit": BASELINE_SHA,
        "active_step": "U12",
        "steps": steps,
    }
    runs = {
        1000 + i: {
            "name": name,
            "head_sha": EVIDENCE_SHA,
            "status": "completed",
            "conclusion": "success",
        }
        for i, name in enumerate(WORKFLOWS)
    }
    return plan, runs


def _validate(plan=None, runs=None, changed=None, ancestor=None):
    valid_plan, valid_runs = _fixture()
    validate_plan(
        plan if plan is not None else valid_plan,
        changed if changed is not None else [],
        ancestor if ancestor is not None else (lambda _sha: True),
        lambda run_id: (runs if runs is not None else valid_runs)[run_id],
    )


def test_valid_current_step_and_exact_sha_prerequisite_evidence_pass():
    _validate(changed=["backend/scripts/validate_development_plan.py"])


def test_cannot_jump_over_active_u12_step():
    plan, _ = _fixture()
    plan["active_step"] = "U09-U10"
    with pytest.raises(GateError, match="active step"):
        _validate(plan=plan)


def test_cannot_mark_prerequisite_complete_without_evidence():
    plan, _ = _fixture()
    plan["steps"][0]["completion_evidence"] = None
    with pytest.raises(GateError, match="requires completion_evidence"):
        _validate(plan=plan)


def test_cannot_reorder_or_delete_a_step():
    plan, _ = _fixture()
    plan["steps"][2], plan["steps"][3] = plan["steps"][3], plan["steps"][2]
    with pytest.raises(GateError, match="step IDs/order"):
        _validate(plan=plan)


def test_dependencies_must_be_explicit_and_linear():
    plan, _ = _fixture()
    plan["steps"][1]["depends_on"] = []
    with pytest.raises(GateError, match="dependencies"):
        _validate(plan=plan)


def test_future_step_cannot_be_started_early():
    plan, _ = _fixture()
    plan["steps"][2]["status"] = "IN PROGRESS"
    with pytest.raises(GateError, match="future step"):
        _validate(plan=plan)


def test_evidence_run_for_different_sha_is_rejected():
    plan, runs = _fixture()
    runs[1000]["head_sha"] = "c" * 40
    with pytest.raises(GateError, match="different commit SHA"):
        _validate(plan=plan, runs=runs)


def test_pending_or_failed_workflow_is_rejected():
    plan, runs = _fixture()
    runs[1000]["status"] = "in_progress"
    with pytest.raises(GateError, match="not completed successfully"):
        _validate(plan=plan, runs=runs)


def test_missing_remote_workflow_evidence_fails_closed():
    plan, _ = _fixture()
    with pytest.raises(GateError, match="cannot verify workflow run"):
        validate_plan(plan, [], lambda _sha: True, lambda _run_id: (_ for _ in ()).throw(RuntimeError("403")))


def test_changed_file_outside_active_step_scope_is_rejected():
    with pytest.raises(GateError, match="scope violation"):
        _validate(changed=["backend/app/main.py"])


def test_stale_scope_baseline_blocks_progression():
    plan, _ = _fixture()
    with pytest.raises(GateError, match="scope_baseline_commit is not an ancestor"):
        _validate(plan=plan, ancestor=lambda sha: sha != BASELINE_SHA)


def test_non_verified_step_cannot_carry_fake_completion_evidence():
    plan, _ = _fixture()
    plan["steps"][1]["completion_evidence"] = {"commit_sha": EVIDENCE_SHA, "workflow_runs": []}
    with pytest.raises(GateError, match="non-verified step"):
        _validate(plan=plan)


def test_active_allowlist_cannot_be_widened_in_the_json_plan():
    plan, _ = _fixture()
    plan["steps"][1]["allowed_paths"].append("backend/app/*")
    with pytest.raises(GateError, match="allowed_paths differ"):
        _validate(plan=plan)


def test_required_workflows_cannot_be_removed_from_the_json_plan():
    plan, _ = _fixture()
    plan["steps"][0]["required_workflow_names"].pop()
    with pytest.raises(GateError, match="required workflows differ"):
        _validate(plan=plan)


def test_active_step_scope_baseline_cannot_be_advanced_to_hide_changes():
    plan, _ = _fixture()
    plan["scope_baseline_commit"] = "c" * 40
    with pytest.raises(GateError, match="scope baseline cannot be moved"):
        _validate(plan=plan)


def test_unknown_plan_identity_is_rejected():
    plan, _ = _fixture()
    plan["plan_id"] = "different-plan"
    with pytest.raises(GateError, match="plan_id"):
        _validate(plan=plan)


def test_committed_machine_plan_matches_the_validator_contract():
    import json
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    plan = json.loads((repository_root / "docs" / "development_plan.json").read_text(encoding="utf-8"))
    assert plan["plan_id"] == "radonc-mdt-master-sequential-plan"
    assert plan["active_step"] == "U12"
    assert plan["steps"][0]["status"] == "VERIFIED"
    assert plan["steps"][1]["status"] == "IN PROGRESS"
    assert plan["steps"][1]["allowed_paths"] == list(STEP_ALLOWED_PATHS["U12"])
    assert [step["id"] for step in plan["steps"]] == list(STEP_ORDER)


def test_cannot_complete_u12_using_the_old_step_a_commit_and_old_ci():
    plan, runs = _fixture()
    u12 = plan["steps"][1]
    u12["status"] = "VERIFIED"
    u12["completion_evidence"] = {
        "commit_sha": EVIDENCE_SHA,
        "workflow_runs": [
            {"id": 2000 + i, "name": name}
            for i, name in enumerate(STEP_REQUIRED_WORKFLOWS["U12"])
        ],
    }
    plan["active_step"] = "U09-U10"
    plan["steps"][2]["status"] = "IN PROGRESS"
    plan["scope_baseline_commit"] = EVIDENCE_SHA
    for i, name in enumerate(STEP_REQUIRED_WORKFLOWS["U12"]):
        runs[2000 + i] = {
            "name": name,
            "head_sha": EVIDENCE_SHA,
            "status": "completed",
            "conclusion": "success",
        }
    with pytest.raises(GateError, match="later descendant"):
        validate_plan(
            plan,
            [],
            lambda _sha: True,
            lambda run_id: runs[run_id],
            lambda _base, _head: True,
            {"U12": ["docs/development_plan.json"]},
        )


def test_completed_step_requires_nonempty_in_scope_code_diff():
    plan, runs = _fixture()
    u12 = plan["steps"][1]
    u12_sha = "c" * 40
    u12["status"] = "VERIFIED"
    u12["completion_evidence"] = {
        "commit_sha": u12_sha,
        "workflow_runs": [
            {"id": 2000 + i, "name": name}
            for i, name in enumerate(STEP_REQUIRED_WORKFLOWS["U12"])
        ],
    }
    plan["active_step"] = "U09-U10"
    plan["steps"][2]["status"] = "IN PROGRESS"
    plan["scope_baseline_commit"] = u12_sha
    for i, name in enumerate(STEP_REQUIRED_WORKFLOWS["U12"]):
        runs[2000 + i] = {
            "name": name,
            "head_sha": u12_sha,
            "status": "completed",
            "conclusion": "success",
        }
    with pytest.raises(GateError, match="no changed-file evidence"):
        validate_plan(
            plan,
            ["docs/development_plan.json"],
            lambda _sha: True,
            lambda run_id: runs[run_id],
            lambda _base, _head: True,
            {"U12": []},
        )



def test_sequential_gate_runs_for_pull_requests_targeting_development_branch():
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    workflow = (repository_root / ".github" / "workflows" / "sequential-development-gate.yml").read_text(encoding="utf-8")
    pull_request_block = workflow.split("  pull_request:", 1)[1].split("  workflow_dispatch:", 1)[0]
    assert "- main" in pull_request_block
    assert "- feature/four-round-mdt-and-performance" in pull_request_block


def test_backend_and_security_required_checks_run_for_development_prs_and_u12_changes():
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    expected_paths = (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        ".github/workflows/sequential-development-gate.yml",
        ".github/workflows/backend-tests.yml",
        ".github/workflows/security-audit.yml",
    )
    for relative in (
        ".github/workflows/backend-tests.yml",
        ".github/workflows/security-audit.yml",
    ):
        workflow = (repository_root / relative).read_text(encoding="utf-8")
        push_block = workflow.split("  push:", 1)[1].split("\n  pull_request:", 1)[0]
        pr_block = workflow.split("  pull_request:", 1)[1].split("\n  schedule:", 1)[0].split("\npermissions:", 1)[0]
        for block in (push_block, pr_block):
            assert "- feature/four-round-mdt-and-performance" in block
            for required_path in expected_paths:
                assert f'      - "{required_path}"' in block
