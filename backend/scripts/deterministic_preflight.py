"""Cheap, deterministic preflight for the RadOnc MDT validation pipeline.

This stage performs static repository checks only. It never starts Ollama, calls a
model, creates an MDT run, or accesses patient data. Full pytest and live-model
acceptance remain separate stages.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    component: str
    status: str
    expected: str
    actual: str
    severity: str
    evidence: list[str]
    root_cause_category: str
    root_cause_status: str
    suggested_correction: str
    regression_test: str | None = None


REQUIRED_VALIDATION_SCRIPTS = (
    "scripts/deterministic_preflight.py",
    "scripts/pytest_junit_diagnostics.py",
    "scripts/live_four_round_validation.py",
    "scripts/representative_model_provenance_validation.py",
    "scripts/run_mdt_stress_suite.py",
    "scripts/run_mdt_stress_with_telemetry.py",
)
REQUIRED_REGRESSION_TESTS = (
    "tests/test_deterministic_preflight.py",
    "tests/test_pytest_junit_diagnostics.py",
    "tests/test_case_integrity.py",
    "tests/test_chair_report_quality.py",
    "tests/test_mdt_rounds.py",
    "tests/test_representative_model_provenance_validation.py",
    "tests/test_source_reference_audit.py",
)
PYTHON_SCAN_DIRECTORIES = ("app", "scripts", "tests")


def _result(
    check_id: str,
    component: str,
    passed: bool,
    expected: str,
    actual: str,
    evidence: Iterable[str],
    *,
    severity: str = "high",
    category: str = "implementation",
    correction: str = "Inspect the cited evidence, correct the underlying defect, and add a regression test.",
    regression_test: str | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        component=component,
        status="passed" if passed else "failed",
        expected=expected,
        actual=actual,
        severity="none" if passed else severity,
        evidence=list(evidence),
        root_cause_category="none" if passed else category,
        root_cause_status="not_applicable" if passed else "unresolved",
        suggested_correction="None required." if passed else correction,
        regression_test=regression_test,
    )


def _python_files(backend_dir: Path) -> list[Path]:
    files: list[Path] = []
    for directory in PYTHON_SCAN_DIRECTORIES:
        root = backend_dir / directory
        if root.is_dir():
            files.extend(
                path for path in root.rglob("*.py")
                if not any(part in {".venv", "venv", "__pycache__"} for part in path.parts)
            )
    return sorted(set(files))


def run_preflight(backend_dir: Path) -> dict:
    """Run static checks and return a stable, machine-readable report."""
    backend_dir = backend_dir.resolve()
    repository_root = backend_dir.parent
    results: list[CheckResult] = []

    python_files = _python_files(backend_dir)
    syntax_errors: list[str] = []
    for path in python_files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            syntax_errors.append(f"{path.relative_to(repository_root)}: {type(exc).__name__}: {exc}")
    results.append(_result(
        "PYTHON_AST_001",
        "python_syntax",
        not syntax_errors and bool(python_files),
        "All Python files under backend/app, scripts and tests parse successfully.",
        f"{len(python_files)} files scanned; {len(syntax_errors)} syntax/read errors.",
        syntax_errors or [f"Scanned {len(python_files)} Python files."],
        category="implementation",
        correction="Fix the syntax or encoding error in each listed file before running tests.",
    ))

    pyproject = backend_dir / "pyproject.toml"
    config_error = None
    config = {}
    try:
        with pyproject.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        config_error = f"{type(exc).__name__}: {exc}"
    python_requirement = config.get("project", {}).get("requires-python")
    test_paths = config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("testpaths")
    config_ok = (
        config_error is None
        and isinstance(python_requirement, str)
        and python_requirement.startswith(">=")
        and isinstance(test_paths, list)
        and "tests" in test_paths
    )
    results.append(_result(
        "CONFIG_TOML_001",
        "backend_configuration",
        config_ok,
        "Valid pyproject.toml declares a Python minimum and pytest discovers backend/tests.",
        config_error or f"requires-python={python_requirement!r}; testpaths={test_paths!r}",
        [str(pyproject.relative_to(repository_root))],
        category="environment",
        correction="Repair pyproject.toml and ensure pytest discovers the backend test directory.",
    ))

    missing_scripts = [
        relative for relative in REQUIRED_VALIDATION_SCRIPTS
        if not (backend_dir / relative).is_file()
    ]
    results.append(_result(
        "VALIDATION_ASSETS_001",
        "validation_inventory",
        not missing_scripts,
        "Existing bounded live, provenance and stress validation scripts remain present.",
        "All required scripts present." if not missing_scripts else f"Missing: {missing_scripts}",
        [str((backend_dir / item).relative_to(repository_root)) for item in REQUIRED_VALIDATION_SCRIPTS],
        category="implementation",
        correction="Restore or deliberately replace missing validation assets; do not create duplicate harnesses.",
    ))

    missing_tests = [
        relative for relative in REQUIRED_REGRESSION_TESTS
        if not (backend_dir / relative).is_file()
    ]
    results.append(_result(
        "REGRESSION_ASSETS_001",
        "regression_coverage",
        not missing_tests,
        "Core clinical-integrity, Chair, round and provenance regression suites are present.",
        "All required regression suites present." if not missing_tests else f"Missing: {missing_tests}",
        [str((backend_dir / item).relative_to(repository_root)) for item in REQUIRED_REGRESSION_TESTS],
        category="implementation",
        correction="Restore the missing regression suite or update this explicit inventory with a reviewed replacement.",
    ))

    installer_workflow = repository_root / ".github/workflows/windows-installer.yml"
    workflow_text = ""
    workflow_error = None
    try:
        workflow_text = installer_workflow.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        workflow_error = f"{type(exc).__name__}: {exc}"
    bootstrap_guard_ok = (
        workflow_error is None
        and "hosted-first-run-bootstrap:" in workflow_text
        and "if: github.event_name == 'workflow_dispatch'" in workflow_text
    )
    results.append(_result(
        "WORKFLOW_BOOTSTRAP_001",
        "workflow_cost_guard",
        bootstrap_guard_ok,
        "Expensive clean-hosted Ollama/model bootstrap is manual-dispatch only.",
        workflow_error or (
            "Manual-dispatch guard present."
            if bootstrap_guard_ok
            else "Expected manual-dispatch-only guard was not found."
        ),
        [str(installer_workflow.relative_to(repository_root))],
        severity="critical",
        category="environment",
        correction="Restore an explicit workflow_dispatch-only condition; do not run model provisioning on every PR.",
        regression_test="tests/test_hosted_cpu_validation_workflow.py",
    ))

    cpu_workflow = repository_root / ".github/workflows/hosted-cpu-four-round-validation.yml"
    cpu_text = ""
    cpu_error = None
    try:
        cpu_text = cpu_workflow.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        cpu_error = f"{type(exc).__name__}: {exc}"
    cpu_guard_ok = (
        cpu_error is None
        and 'RADONC_AGENT_CONCURRENCY: "1"' in cpu_text
        and 'RADONC_VALIDATION_CPU_ONLY: "1"' in cpu_text
        and "timeout-minutes: 250" in cpu_text
    )
    results.append(_result(
        "WORKFLOW_CPU_GUARD_001",
        "workflow_resource_guard",
        cpu_guard_ok,
        "Hosted full-run validation remains CPU-only, concurrency 1 and explicitly time-bounded.",
        cpu_error or (
            "CPU-only, concurrency-1 and timeout guards present."
            if cpu_guard_ok
            else "One or more required CPU/concurrency/timeout guards are missing."
        ),
        [str(cpu_workflow.relative_to(repository_root))],
        severity="critical",
        category="environment",
        correction="Restore CPU-only mode, concurrency 1 and an explicit job timeout before dispatch.",
        regression_test="tests/test_hosted_cpu_validation_workflow.py",
    ))

    failures = [item for item in results if item.status == "failed"]
    return {
        "schema_version": 1,
        "validation_type": "deterministic_static_preflight",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root_name": repository_root.name,
        "scope": {
            "model_inference_performed": False,
            "ollama_started": False,
            "mdt_run_created": False,
            "patient_data_accessed": False,
            "clinical_accuracy_evaluated": False,
            "checks_executed": len(results),
        },
        "summary": {
            "status": "passed" if not failures else "failed",
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "inconclusive": 0,
        },
        "results": [asdict(item) for item in results],
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# RadOnc MDT deterministic preflight",
        "",
        f"- Status: **{summary['status'].upper()}**",
        f"- Checks: {summary['passed']} passed, {summary['failed']} failed, {summary['inconclusive']} inconclusive",
        f"- Generated (UTC): {report['generated_at_utc']}",
        "- Model inference: not performed",
        "- Clinical accuracy: not evaluated",
        "",
        "| Check ID | Component | Status | Severity | Root cause |",
        "|---|---|---|---|---|",
    ]
    for item in report["results"]:
        lines.append(
            f"| {item['check_id']} | {item['component']} | {item['status']} | "
            f"{item['severity']} | {item['root_cause_category']} ({item['root_cause_status']}) |"
        )
    for item in report["results"]:
        if item["status"] == "failed":
            lines.extend([
                "",
                f"## {item['check_id']}: {item['component']}",
                "",
                f"- Expected: {item['expected']}",
                f"- Actual: {item['actual']}",
                f"- Suggested correction: {item['suggested_correction']}",
                f"- Regression test: {item['regression_test'] or 'Not assigned'}",
                "- Evidence:",
                *[f"  - {entry}" for entry in item["evidence"]],
            ])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "validation_artifacts" / "preflight",
    )
    args = parser.parse_args(argv)

    report = run_preflight(args.backend_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "deterministic_preflight.json"
    markdown_path = args.output_dir / "deterministic_preflight.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
