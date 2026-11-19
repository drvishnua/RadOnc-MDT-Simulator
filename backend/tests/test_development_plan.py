"""Adversarial regression tests for the fail-closed development gate."""
from copy import deepcopy

import pytest

from scripts.validate_development_plan import (
    GateError,
    STEP_ORDER,
    validate_plan,
)

EVIDENCE_SHA = "a" * 40
BASELINE_SHA = "b" * 40
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
                "required_workflow_names": WORKFLOWS if index == 0 else ["Sequential Development Gate"],
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
