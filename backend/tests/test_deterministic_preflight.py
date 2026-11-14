"""Tests for the deterministic, no-inference validation preflight."""
from __future__ import annotations

import json
from pathlib import Path

from scripts import deterministic_preflight as preflight


def _minimal_repository(root: Path) -> Path:
    backend = root / "backend"
    for directory in ("app", "scripts", "tests"):
        (backend / directory).mkdir(parents=True)
    (backend / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.11"\n'
        '[tool.pytest.ini_options]\ntestpaths = [\"tests\"]\n',
        encoding="utf-8",
    )
    for relative in preflight.REQUIRED_VALIDATION_SCRIPTS:
        path = backend / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"""fixture"""\n', encoding="utf-8")
    for relative in preflight.REQUIRED_REGRESSION_TESTS:
        path = backend / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "windows-installer.yml").write_text(
        "on:\\n"
        "  workflow_dispatch:\\n"
        "  push:\\n"
        "    branches:\\n"
        "      - feature/four-round-mdt-and-performance\\n"
        "hosted-first-run-bootstrap:\\n"
        "    if: >-\\n"
        "      github.event_name == 'workflow_dispatch' ||\\n"
        "      (github.event_name == 'push' && github.ref == 'refs/heads/feature/four-round-mdt-and-performance')\\n",
        encoding="utf-8",
    )
    (workflows / "hosted-cpu-four-round-validation.yml").write_text(
        'RADONC_AGENT_CONCURRENCY: "1"\n'
        'RADONC_VALIDATION_CPU_ONLY: "1"\n'
        "timeout-minutes: 250\n",
        encoding="utf-8",
    )
    return backend


def test_preflight_passes_minimal_valid_repository_without_model_inference(tmp_path):
    backend = _minimal_repository(tmp_path)

    report = preflight.run_preflight(backend)

    assert report["summary"] == {"status": "passed", "passed": 6, "failed": 0, "inconclusive": 0}
    assert report["scope"]["model_inference_performed"] is False
    assert report["scope"]["ollama_started"] is False
    assert report["scope"]["mdt_run_created"] is False
    assert all(item["root_cause_status"] == "not_applicable" for item in report["results"])


def test_preflight_reports_missing_manual_bootstrap_guard_as_environment_failure(tmp_path):
    backend = _minimal_repository(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "windows-installer.yml"
    workflow.write_text("hosted-first-run-bootstrap:\n", encoding="utf-8")

    report = preflight.run_preflight(backend)
    failure = next(item for item in report["results"] if item["check_id"] == "WORKFLOW_BOOTSTRAP_001")

    assert report["summary"]["status"] == "failed"
    assert failure["status"] == "failed"
    assert failure["severity"] == "critical"
    assert failure["root_cause_category"] == "environment"
    assert failure["root_cause_status"] == "unresolved"
    assert failure["regression_test"] == "tests/test_deterministic_preflight.py"


def test_preflight_detects_python_syntax_error_and_records_file_evidence(tmp_path):
    backend = _minimal_repository(tmp_path)
    broken = backend / "app" / "broken.py"
    broken.write_text("def incomplete(:\n", encoding="utf-8")

    report = preflight.run_preflight(backend)
    failure = next(item for item in report["results"] if item["check_id"] == "PYTHON_AST_001")

    assert failure["status"] == "failed"
    assert failure["root_cause_category"] == "implementation"
    assert any("app/broken.py" in evidence for evidence in failure["evidence"])


def test_preflight_writes_machine_and_human_readable_reports(tmp_path):
    backend = _minimal_repository(tmp_path)
    output = tmp_path / "reports"

    exit_code = preflight.main([
        "--backend-dir", str(backend),
        "--output-dir", str(output),
    ])

    payload = json.loads((output / "deterministic_preflight.json").read_text(encoding="utf-8"))
    markdown = (output / "deterministic_preflight.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert payload["validation_type"] == "deterministic_static_preflight"
    assert "# RadOnc MDT deterministic preflight" in markdown
    assert "Model inference: not performed" in markdown

def test_preflight_detects_missing_junit_diagnostics_script_in_validation_inventory(tmp_path):
    backend = _minimal_repository(tmp_path)
    (backend / "scripts" / "pytest_junit_diagnostics.py").unlink()

    report = preflight.run_preflight(backend)
    failure = next(item for item in report["results"] if item["check_id"] == "VALIDATION_ASSETS_001")

    assert failure["status"] == "failed"
    assert "scripts/pytest_junit_diagnostics.py" in failure["actual"]


def test_preflight_detects_missing_diagnostic_regression_suite_in_inventory(tmp_path):
    backend = _minimal_repository(tmp_path)
    (backend / "tests" / "test_pytest_junit_diagnostics.py").unlink()

    report = preflight.run_preflight(backend)
    failure = next(item for item in report["results"] if item["check_id"] == "REGRESSION_ASSETS_001")

    assert failure["status"] == "failed"
    assert "tests/test_pytest_junit_diagnostics.py" in failure["actual"]



def test_preflight_accepts_only_dispatch_or_exact_development_branch_push(tmp_path):
    backend = _minimal_repository(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "windows-installer.yml"

    valid = preflight.run_preflight(backend)
    valid_guard = next(item for item in valid["results"] if item["check_id"] == "WORKFLOW_BOOTSTRAP_001")
    assert valid_guard["status"] == "passed"

    workflow.write_text(
        "on:\\n"
        "  workflow_dispatch:\\n"
        "  push:\\n"
        "    branches:\\n"
        "      - '**'\\n"
        "hosted-first-run-bootstrap:\\n"
        "    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'\\n",
        encoding="utf-8",
    )
    broad = preflight.run_preflight(backend)
    broad_guard = next(item for item in broad["results"] if item["check_id"] == "WORKFLOW_BOOTSTRAP_001")
    assert broad_guard["status"] == "failed"
