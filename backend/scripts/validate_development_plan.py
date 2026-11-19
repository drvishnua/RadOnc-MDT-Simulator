"""Fail-closed validation for the RadOnc MDT sequential development plan.

The gate is deliberately deterministic and fails closed when evidence cannot be
retrieved. GitHub branch protection is a separate repository setting.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

STEP_ORDER = (
    "STEP-A",
    "U12",
    "U09-U10",
    "U04",
    "U05-U06",
    "U06-U08",
    "U07",
    "U03",
    "U01-U02",
    "RELEASE",
)

# The current U12 boundary is intentionally narrow. Later boundaries are
# explicit here so broadening docs/development_plan.json alone cannot widen scope.
STEP_ALLOWED_PATHS = {
    "STEP-A": (),
    "U12": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/scripts/validate_development_plan.py",
        "backend/tests/test_development_plan.py",
        ".github/workflows/sequential-development-gate.yml",
    ),
    "U09-U10": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/app/clinical_fields.py",
        "backend/app/schemas.py",
        "backend/app/services/case_integrity.py",
        "backend/tests/*",
    ),
    "U04": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/app/services/intake*",
        "backend/app/main.py",
        "backend/tests/*",
        "frontend/src/*",
        "frontend/tests/*",
    ),
    "U05-U06": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/app/agents/*",
        "backend/app/services/mdt_generation.py",
        "backend/app/services/mdt_rounds.py",
        "backend/tests/*",
    ),
    "U06-U08": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/app/services/mdt_generation.py",
        "backend/app/services/mdt_rounds.py",
        "backend/app/services/chair_report_quality.py",
        "backend/tests/*",
        "frontend/src/*",
    ),
    "U07": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/app/*",
        "backend/tests/*",
        "docs/*",
    ),
    "U03": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        ".github/scripts/*",
        "packaging/windows/*",
        "scripts/*",
        "backend/tests/*",
    ),
    "U01-U02": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "frontend/src/*",
        "frontend/tests/*",
        "packaging/*",
        ".github/workflows/*",
    ),
    "RELEASE": (
        "docs/development_plan.json",
        "docs/MASTER_DEVELOPMENT_CHECKLIST.md",
        "backend/*",
        "frontend/*",
        "packaging/*",
        ".github/workflows/*",
    ),
}

VALID_STATUSES = {"NOT STARTED", "IN PROGRESS", "BLOCKED", "VERIFIED", "FAILED", "NOT APPLICABLE"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GateError(ValueError):
    """Raised when any sequential-plan invariant or evidence check fails."""


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def validate_plan(
    plan: dict,
    changed_files: list[str],
    is_ancestor: Callable[[str], bool],
    run_lookup: Callable[[int], dict],
) -> None:
    """Validate plan ordering, status transitions, scope and exact-SHA CI evidence."""
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("unsupported or missing schema_version")

    steps = plan.get("steps")
    if not isinstance(steps, list):
        raise GateError("steps must be a list")

    ids = [step.get("id") for step in steps if isinstance(step, dict)]
    if tuple(ids) != STEP_ORDER:
        errors.append(f"step IDs/order must exactly match {list(STEP_ORDER)}")

    by_id = {step.get("id"): step for step in steps if isinstance(step, dict)}
    for index, step_id in enumerate(STEP_ORDER):
        step = by_id.get(step_id)
        if step is None:
            continue
        expected_dependencies = [] if index == 0 else [STEP_ORDER[index - 1]]
        if step.get("depends_on") != expected_dependencies:
            errors.append(f"{step_id}: dependencies must be {expected_dependencies}")
        if step.get("status") not in VALID_STATUSES:
            errors.append(f"{step_id}: invalid status {step.get('status')!r}")

    active_id = plan.get("active_step")
    if active_id not in STEP_ORDER:
        errors.append("active_step is not a recognised step ID")
    else:
        active_index = STEP_ORDER.index(active_id)
        if by_id.get(active_id, {}).get("status") != "IN PROGRESS":
            errors.append("the active step must have status IN PROGRESS")
        for index, step_id in enumerate(STEP_ORDER):
            step = by_id.get(step_id, {})
            status = step.get("status")
            if index < active_index and status != "VERIFIED":
                errors.append(f"{step_id}: every prerequisite before {active_id} must be VERIFIED")
            elif index > active_index and status not in {"BLOCKED", "NOT STARTED"}:
                errors.append(f"{step_id}: future step cannot be {status!r} while {active_id} is active")

    # A VERIFIED step is valid only with exact-SHA successful runs for every
    # required workflow. Any API failure or stale/pending/failed run blocks.
    for step_id in STEP_ORDER:
        step = by_id.get(step_id, {})
        if step.get("status") != "VERIFIED":
            if step.get("completion_evidence") is not None:
                errors.append(f"{step_id}: non-verified step must not carry completion_evidence")
            continue

        evidence = step.get("completion_evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{step_id}: VERIFIED requires completion_evidence")
            continue
        evidence_sha = evidence.get("commit_sha")
        if not isinstance(evidence_sha, str) or not SHA_RE.fullmatch(evidence_sha):
            errors.append(f"{step_id}: evidence commit_sha must be a full 40-character SHA")
            continue
        if not is_ancestor(evidence_sha):
            errors.append(f"{step_id}: evidence SHA is not an ancestor of the checked-out head")
        required_names = step.get("required_workflow_names")
        records = evidence.get("workflow_runs")
        if not isinstance(required_names, list) or not required_names:
            errors.append(f"{step_id}: required_workflow_names must be non-empty")
            continue
        if not isinstance(records, list):
            errors.append(f"{step_id}: workflow_runs evidence must be a list")
            continue
        record_names = [record.get("name") for record in records if isinstance(record, dict)]
        record_ids = [record.get("id") for record in records if isinstance(record, dict)]
        if len(record_ids) != len(set(record_ids)):
            errors.append(f"{step_id}: duplicate workflow run IDs")
        if set(record_names) != set(required_names) or len(record_names) != len(required_names):
            errors.append(f"{step_id}: evidence must contain exactly one run for each required workflow")
            continue
        for record in records:
            try:
                run_id = int(record["id"])
                run = run_lookup(run_id)
            except Exception as exc:  # fail closed for missing IDs, network and API errors
                errors.append(f"{step_id}: cannot verify workflow run {record.get('id')}: {exc}")
                continue
            if run.get("head_sha") != evidence_sha:
                errors.append(f"{step_id}: workflow run {run_id} is for a different commit SHA")
            if run.get("name") != record.get("name"):
                errors.append(f"{step_id}: workflow run {run_id} name does not match recorded evidence")
            if run.get("status") != "completed" or run.get("conclusion") != "success":
                errors.append(f"{step_id}: workflow run {run_id} is not completed successfully")

    baseline = plan.get("scope_baseline_commit")
    if not isinstance(baseline, str) or not SHA_RE.fullmatch(baseline):
        errors.append("scope_baseline_commit must be a full 40-character SHA")
    elif not is_ancestor(baseline):
        errors.append("scope_baseline_commit is not an ancestor of the checked-out head")

    if active_id in STEP_ALLOWED_PATHS:
        allowed = STEP_ALLOWED_PATHS[active_id]
        for path in changed_files:
            if not _matches(path, allowed):
                errors.append(f"scope violation while {active_id} is active: {path}")

    if errors:
        raise GateError("; ".join(errors))


def _git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _github_run_lookup(repository: str, token: str) -> Callable[[int], dict]:
    def lookup(run_id: int) -> dict:
        url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "radonc-mdt-sequential-gate",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    return lookup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="docs/development_plan.json")
    parser.add_argument("--head", default=os.environ.get("GITHUB_HEAD_SHA", ""))
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    plan_path = (root / args.plan).resolve()
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        head = args.head or _git(root, "rev-parse", "HEAD")
        if not SHA_RE.fullmatch(head):
            raise GateError("--head must be a full commit SHA")
        if _git(root, "cat-file", "-e", f"{head}^{{commit}}", check=False) == "":
            raise GateError(f"head commit is not available locally: {head}")

        def is_ancestor(sha: str) -> bool:
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha, head],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return result.returncode == 0

        baseline = plan.get("scope_baseline_commit", "")
        changed_text = _git(root, "diff", "--name-only", f"{baseline}..{head}") if SHA_RE.fullmatch(baseline) else ""
        changed_files = [line for line in changed_text.splitlines() if line]
        token = os.environ.get("GITHUB_TOKEN")
        repository = os.environ.get("GITHUB_REPOSITORY")
        if not token or not repository:
            raise GateError("GITHUB_TOKEN and GITHUB_REPOSITORY are required to verify remote CI evidence")
        validate_plan(plan, changed_files, is_ancestor, _github_run_lookup(repository, token))
    except (OSError, json.JSONDecodeError, GateError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"SEQUENTIAL_DEVELOPMENT_GATE_BLOCKED: {exc}", file=sys.stderr)
        return 1

    print(
        "SEQUENTIAL_DEVELOPMENT_GATE_OK: "
        f"active_step={plan['active_step']} checked_head={head} "
        f"scope_baseline={plan['scope_baseline_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
