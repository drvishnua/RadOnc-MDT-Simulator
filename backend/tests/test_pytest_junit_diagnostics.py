"""Regression tests for per-test pytest JUnit diagnostics."""
import json
from pathlib import Path

from scripts import pytest_junit_diagnostics as diagnostics


def _write_junit(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_junit_report_classifies_each_test_and_preserves_failure_evidence(tmp_path):
    junit = _write_junit(
        tmp_path / "pytest.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
        <testsuites>
          <testsuite name="backend" tests="4">
            <testcase classname="tests.test_case" name="test_pass"/>
            <testcase classname="tests.test_case" name="test_assertion">
              <failure type="AssertionError" message="expected option preserved">
                AssertionError: expected option preserved
              </failure>
            </testcase>
            <testcase classname="tests.test_case" name="test_setup">
              <error type="RuntimeError" message="fixture unavailable">
                RuntimeError: fixture unavailable
              </error>
            </testcase>
            <testcase classname="tests.test_case" name="test_skipped">
              <skipped message="platform-specific"/>
            </testcase>
          </testsuite>
        </testsuites>
        """,
    )

    report = diagnostics.parse_junit_report(junit)

    assert report["summary"] == {
        "status": "failed",
        "total": 4,
        "passed": 1,
        "failed": 1,
        "errors": 1,
        "skipped": 1,
        "inconclusive": 0,
        "diagnostic_errors": 0,
    }
    by_name = {item["regression_test"].split("::")[-1]: item for item in report["results"]}
    assert by_name["test_pass"]["status"] == "passed"
    assert by_name["test_assertion"]["status"] == "failed"
    assert by_name["test_assertion"]["root_cause_category"] == "test_assertion_failure"
    assert by_name["test_assertion"]["root_cause_status"] == "unresolved"
    assert any("expected option preserved" in entry for entry in by_name["test_assertion"]["evidence"])
    assert by_name["test_setup"]["status"] == "error"
    assert by_name["test_skipped"]["status"] == "skipped"


def test_junit_check_ids_are_stable_for_the_same_testcase_order(tmp_path):
    junit = _write_junit(
        tmp_path / "pytest.xml",
        '<testsuite name="suite"><testcase classname="tests.test_a" name="test_one"/></testsuite>',
    )

    first = diagnostics.parse_junit_report(junit)
    second = diagnostics.parse_junit_report(junit)

    assert first["results"][0]["check_id"] == second["results"][0]["check_id"]


def test_missing_junit_file_is_inconclusive_not_a_pass(tmp_path):
    report = diagnostics.parse_junit_report(tmp_path / "missing.xml")

    assert report["summary"]["status"] == "inconclusive"
    assert report["summary"]["total"] == 0
    assert report["summary"]["inconclusive"] == 1
    assert report["results"][0]["component"] == "test_result_capture"
    assert report["results"][0]["status"] == "inconclusive"


def test_malformed_junit_file_is_reported_as_diagnostic_error(tmp_path):
    junit = _write_junit(tmp_path / "bad.xml", "<testsuites><testsuite>")

    report = diagnostics.parse_junit_report(junit)

    assert report["summary"]["status"] == "error"
    assert report["summary"]["diagnostic_errors"] == 1
    assert report["results"][0]["status"] == "error"
    assert "ParseError" in report["results"][0]["actual"]


def test_empty_junit_file_with_no_testcases_is_inconclusive(tmp_path):
    junit = _write_junit(tmp_path / "empty.xml", "<testsuites><testsuite name='empty'/></testsuites>")

    report = diagnostics.parse_junit_report(junit)

    assert report["summary"]["status"] == "inconclusive"
    assert report["summary"]["total"] == 0
    assert report["results"][0]["check_id"] == "JUNIT_CASES_001"


def test_cli_writes_json_and_markdown_reports(tmp_path):
    junit = _write_junit(
        tmp_path / "pytest.xml",
        '<testsuite name="suite"><testcase classname="tests.test_a" name="test_one"/></testsuite>',
    )
    output_dir = tmp_path / "reports"

    exit_code = diagnostics.main([
        "--junit-xml", str(junit),
        "--output-dir", str(output_dir),
    ])

    payload = json.loads(
        (output_dir / "pytest_diagnostics.json").read_text(encoding="utf-8")
    )
    markdown = (output_dir / "pytest_diagnostics.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert payload["validation_type"] == "pytest_junit_diagnostics"
    assert payload["summary"]["passed"] == 1
    assert "# RadOnc MDT pytest diagnostics" in markdown
