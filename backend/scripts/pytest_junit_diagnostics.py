"""Convert pytest JUnit XML into per-test, machine-readable diagnostics.

This reporter observes test results; it does not execute tests or override pytest's
exit status. Missing or unusable JUnit input is explicitly reported as inconclusive
or diagnostic error rather than being treated as a successful test run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from xml.etree.ElementTree import Element


MAX_EVIDENCE_CHARS = 6000


def _local_name(tag: str) -> str:
    """Return an XML local name, including for documents using namespaces."""
    return tag.rsplit("}", 1)[-1]


def _iter_testcases(
    element: Element, suite_name: str = ""
) -> Iterator[tuple[str, Element]]:
    current_suite = suite_name
    if _local_name(element.tag) == "testsuite":
        current_suite = element.attrib.get("name", current_suite)
    if _local_name(element.tag) == "testcase":
        yield current_suite, element
        return
    for child in element:
        yield from _iter_testcases(child, current_suite)


def _excerpt(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) <= MAX_EVIDENCE_CHARS:
        return cleaned
    return cleaned[:MAX_EVIDENCE_CHARS] + "\n...[truncated; full output remains in JUnit XML]"


def _diagnostic(
    check_id: str,
    component: str,
    status: str,
    expected: str,
    actual: str,
    evidence: list[str],
    severity: str,
    category: str,
    root_cause_status: str,
    correction: str,
    regression_test: str | None = None,
) -> dict:
    return {
        "check_id": check_id,
        "component": component,
        "status": status,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "evidence": evidence,
        "root_cause_category": category,
        "root_cause_status": root_cause_status,
        "suggested_correction": correction,
        "regression_test": regression_test,
    }


def _input_problem(path: Path, status: str, actual: str, category: str) -> dict:
    return _diagnostic(
        check_id="JUNIT_INPUT_001",
        component="test_result_capture",
        status=status,
        expected="A readable pytest JUnit XML file containing one or more test cases.",
        actual=actual,
        evidence=[str(path)],
        severity="unknown" if status == "inconclusive" else "high",
        category=category,
        root_cause_status="unknown" if status == "inconclusive" else "unresolved",
        correction=(
            "Confirm that pytest ran with --junitxml and inspect earlier workflow steps. "
            "Do not interpret missing test output as a pass."
        ),
    )


def parse_junit_report(junit_xml: Path) -> dict:
    """Parse JUnit XML without trusting suite counters or inferring root causes."""
    junit_xml = junit_xml.resolve()
    results: list[dict] = []

    if not junit_xml.is_file():
        results.append(_input_problem(
            junit_xml,
            "inconclusive",
            "JUnit XML file was not created; test execution is not established by this report.",
            "test_result_capture_missing",
        ))
    else:
        try:
            root = ET.parse(junit_xml).getroot()
        except (ET.ParseError, OSError, UnicodeError) as exc:
            results.append(_input_problem(
                junit_xml,
                "error",
                f"{type(exc).__name__}: {exc}",
                "test_result_capture_invalid",
            ))
        else:
            cases = list(_iter_testcases(root))
            if not cases:
                results.append(_diagnostic(
                    check_id="JUNIT_CASES_001",
                    component="test_execution",
                    status="inconclusive",
                    expected="At least one pytest testcase is recorded.",
                    actual="JUnit XML is readable but contains no testcase elements.",
                    evidence=[str(junit_xml)],
                    severity="unknown",
                    category="no_testcases_recorded",
                    root_cause_status="unknown",
                    correction=(
                        "Inspect pytest collection output and workflow control flow; "
                        "do not treat an empty test report as successful coverage."
                    ),
                ))

            occurrences: dict[str, int] = {}
            for index, (suite_name, case) in enumerate(cases, start=1):
                class_name = case.attrib.get("classname", "").strip()
                case_name = case.attrib.get("name", "").strip()
                identity = "::".join(part for part in (class_name, case_name) if part)
                if not identity:
                    identity = f"unnamed-testcase-{index}"
                if suite_name:
                    identity = f"{suite_name}::{identity}"

                occurrence = occurrences.get(identity, 0) + 1
                occurrences[identity] = occurrence
                unique_identity = f"{identity}#{occurrence}"
                digest = hashlib.sha256(unique_identity.encode("utf-8")).hexdigest()[:16]

                status_elements = [
                    child for child in case
                    if _local_name(child.tag) in {"failure", "error", "skipped"}
                ]
                status_names = [_local_name(child.tag) for child in status_elements]

                if not class_name and not case_name:
                    status = "inconclusive"
                    category = "test_identity_missing"
                    root_status = "unknown"
                    severity = "unknown"
                    actual = "Testcase has neither classname nor name."
                    correction = "Inspect the JUnit producer and retain a stable testcase identity."
                    evidence = [unique_identity]
                elif len(status_names) > 1:
                    status = "inconclusive"
                    category = "test_result_ambiguous"
                    root_status = "unknown"
                    severity = "unknown"
                    actual = f"Testcase has conflicting result elements: {status_names!r}."
                    correction = (
                        "Inspect the raw JUnit XML and the test reporter; do not choose "
                        "one conflicting result silently."
                    )
                    evidence = [unique_identity]
                elif status_names == ["failure"]:
                    status = "failed"
                    category = "test_assertion_failure"
                    root_status = "unresolved"
                    severity = "high"
                    node = status_elements[0]
                    detail = " ".join(
                        part for part in (
                            node.attrib.get("type", ""),
                            node.attrib.get("message", ""),
                            node.text or "",
                        ) if part
                    )
                    actual = "pytest recorded an assertion/test failure."
                    correction = (
                        "Inspect the assertion and traceback, identify the underlying cause, "
                        "and add or correct a focused regression test. This label does not "
                        "establish the underlying code root cause."
                    )
                    evidence = [unique_identity, _excerpt(detail)] if detail.strip() else [unique_identity]
                elif status_names == ["error"]:
                    status = "error"
                    category = "test_execution_error"
                    root_status = "unresolved"
                    severity = "high"
                    node = status_elements[0]
                    detail = " ".join(
                        part for part in (
                            node.attrib.get("type", ""),
                            node.attrib.get("message", ""),
                            node.text or "",
                        ) if part
                    )
                    actual = "pytest recorded a setup, teardown, collection or execution error."
                    correction = (
                        "Inspect the recorded error and workflow logs; distinguish test "
                        "infrastructure failures from application defects before changing code."
                    )
                    evidence = [unique_identity, _excerpt(detail)] if detail.strip() else [unique_identity]
                elif status_names == ["skipped"]:
                    status = "skipped"
                    category = "test_skipped"
                    root_status = "not_applicable"
                    severity = "none"
                    node = status_elements[0]
                    detail = " ".join(
                        part for part in (node.attrib.get("message", ""), node.text or "")
                        if part
                    )
                    actual = "pytest explicitly marked this testcase as skipped."
                    correction = "Review whether the skip is expected and document any coverage limitation."
                    evidence = [unique_identity, _excerpt(detail)] if detail.strip() else [unique_identity]
                elif not status_names:
                    status = "passed"
                    category = "none"
                    root_status = "not_applicable"
                    severity = "none"
                    actual = "No failure, error or skipped element was recorded for this testcase."
                    correction = "None required."
                    evidence = [unique_identity]
                else:
                    status = "inconclusive"
                    category = "test_result_unclassified"
                    root_status = "unknown"
                    severity = "unknown"
                    actual = f"Unrecognised JUnit result elements: {status_names!r}."
                    correction = "Inspect the raw JUnit XML before interpreting this testcase."
                    evidence = [unique_identity]

                results.append(_diagnostic(
                    check_id=f"PYTEST_{digest}",
                    component="backend_test",
                    status=status,
                    expected="Test completes without failure or error; skipped cases remain disclosed.",
                    actual=actual,
                    evidence=evidence,
                    severity=severity,
                    category=category,
                    root_cause_status=root_status,
                    correction=correction,
                    regression_test=identity,
                ))

    counts = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "inconclusive": 0,
        "diagnostic_errors": 0,
    }
    for item in results:
        status = item["status"]
        if item["component"] == "backend_test":
            counts["total"] += 1
            if status in {"passed", "failed", "error", "skipped", "inconclusive"}:
                key = "errors" if status == "error" else status
                counts[key] += 1
        elif status == "inconclusive":
            counts["inconclusive"] += 1
        elif status == "error":
            counts["diagnostic_errors"] += 1

    if counts["failed"] or counts["errors"]:
        overall_status = "failed"
    elif counts["inconclusive"] or counts["diagnostic_errors"] or counts["total"] == 0:
        overall_status = "inconclusive" if not counts["diagnostic_errors"] else "error"
    else:
        overall_status = "passed"

    return {
        "schema_version": 1,
        "validation_type": "pytest_junit_diagnostics",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "junit_xml": str(junit_xml),
            "exists": junit_xml.is_file(),
        },
        "scope": {
            "model_inference_performed": False,
            "ollama_started": False,
            "mdt_run_created": False,
            "patient_data_accessed": False,
            "clinical_accuracy_evaluated": False,
        },
        "summary": {"status": overall_status, **counts},
        "results": results,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# RadOnc MDT pytest diagnostics",
        "",
        f"- Status: **{summary['status'].upper()}**",
        (
            f"- Testcases: {summary['total']} total; {summary['passed']} passed; "
            f"{summary['failed']} failed; {summary['errors']} errors; "
            f"{summary['skipped']} skipped; {summary['inconclusive']} inconclusive"
        ),
        f"- Diagnostic errors: {summary['diagnostic_errors']}",
        "- This report observes pytest output; it does not change pytest's exit status.",
        "- Model inference: not performed",
        "- Clinical accuracy: not evaluated",
        "",
        "| Check ID | Test | Status | Severity | Classification |",
        "|---|---|---|---|---|",
    ]
    for item in report["results"]:
        test_name = item["regression_test"] or item["component"]
        lines.append(
            f"| {item['check_id']} | {test_name} | {item['status']} | "
            f"{item['severity']} | {item['root_cause_category']} "
            f"({item['root_cause_status']}) |"
        )

    for item in report["results"]:
        if item["status"] not in {"passed", "skipped"}:
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
    parser.add_argument(
        "--junit-xml",
        type=Path,
        default=Path("validation_artifacts/test-results/pytest-junit.xml"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("validation_artifacts/test-results"),
    )
    args = parser.parse_args(argv)

    report = parse_junit_report(args.junit_xml)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "pytest_diagnostics.json"
    markdown_path = args.output_dir / "pytest_diagnostics.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    # pytest owns the test-suite exit status; this process only records evidence.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
