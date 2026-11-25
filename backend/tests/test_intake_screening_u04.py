"""Requirement U04: Pre-MDT conversational intake and completeness screener tests.

These tests define the specification for:
1. Detecting and prioritizing clinical contradictions / conflicts before missing fields.
2. Expanding screening domains to include v2 canonical clinical fields.
3. Allowing the user to accept a case with gaps and conflicts without inventing facts.
4. Ensuring screener never pre-writes specialist conclusions or treatment recommendations.
"""
from __future__ import annotations

from typing import Any
import pytest

from app.schemas import SyntheticCase
from app.services.intake_screening import screen_case_intake


def _make_case(**overrides: Any) -> SyntheticCase:
    payload: dict[str, Any] = {
        "scenario_title": "Synthetic U04 Screener Case",
        "case_summary": "Fictional case summary for U04 conversational screener verification.",
    }
    payload.update(overrides)
    return SyntheticCase.model_validate(payload)


def _conflict_entry(value: Any, ref: str, excerpt: str = "Recorded finding.") -> dict[str, Any]:
    return {
        "raw_value": value,
        "provenance": {
            "source_type": "CLINICIAN_NOTE",
            "source_reference": ref,
            "source_excerpt": excerpt,
            "verification_status": "user_supplied_not_independently_verified",
        },
    }


def test_screening_detects_and_preserves_clinical_conflicts() -> None:
    """Contradictions in clinical fields must be explicitly surfaced and preserved."""
    conflicts_data = {
        "age_years": [
            _conflict_entry(70, "clinic-note-a", "Age recorded as 70 years."),
            _conflict_entry(72, "intake-form-b", "Patient reported age 72."),
        ]
    }
    case = _make_case(
        age_years=70,
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts=conflicts_data,
    )
    result = screen_case_intake(case)

    # Screener must report conflicts
    assert "conflicts" in result
    conflict_fields = {item["field_id"] for item in result["conflicts"]}
    assert "age_years" in conflict_fields

    # The raw contradictory entries must be preserved in the snapshot
    assert result["case_snapshot"]["clinical_field_conflicts"]["age_years"] == conflicts_data["age_years"]


def test_screening_prioritizes_conflicts_before_missing_fields() -> None:
    """Questions resolving contradictions must be presented first before missing details."""
    case = _make_case(
        age_years=70,
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts={
            "age_years": [
                _conflict_entry(70, "doc-a"),
                _conflict_entry(72, "doc-b"),
            ]
        },
        performance_status="",
        patient_goals=[],
    )
    result = screen_case_intake(case)

    questions = result["questions"]
    assert len(questions) > 0

    # First question must address the unresolved contradiction / conflict
    first_question = questions[0]
    assert first_question.get("priority") == "high" or "conflict" in first_question.get("domain", "").lower() or "age_years" in first_question.get("question", "").lower()


def test_screening_domains_cover_v2_canonical_fields() -> None:
    """Screener must assess v2 clinical fields when missing."""
    case = _make_case()
    result = screen_case_intake(case)

    missing_field_ids = {gap["field_id"] for gap in result["gaps"]}

    # Core v2 staging, functional and willingness fields should be tracked
    v2_expected_fields = {
        "staging_system",
        "performance_status_scale",
        "patient_willingness",
    }
    # All expected v2 fields must be recognized in gaps
    assert v2_expected_fields.issubset(missing_field_ids)


def test_screening_ready_to_accept_with_gaps_and_conflicts() -> None:
    """A case with both gaps and conflicts can still be accepted for MDT without forced data entry."""
    case = _make_case(
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts={
            "age_years": [
                _conflict_entry(68, "src-1"),
                _conflict_entry(71, "src-2"),
            ]
        },
    )
    result = screen_case_intake(case)

    # Acceptance with gaps remains available; user is never forced to fabricate facts
    assert result["ready_to_accept_with_gaps"] is True
    # Gaps and conflicts are documented, not erased
    assert len(result["gaps"]) > 0
    assert len(result.get("conflicts", [])) > 0


def test_screener_is_not_an_mdt_specialist_and_does_not_prescribe() -> None:
    """Screener is purely an information intake assistant and must never formulate treatment plans."""
    case = _make_case()
    result = screen_case_intake(case)

    assert "consensus_points" not in result

    assert "treatment_recommendation" not in result
    assert "disclaimer" in result
    assert "not clinical validation" in result["disclaimer"].lower()


def test_clinical_conflicts_domain_cannot_be_declined() -> None:
    """Conflicting fields must remain surfaced and cannot be dismissed via declined_domains."""
    import pytest

    case = _make_case(
        clinical_field_states={"age_years": "CONFLICTING"},
        clinical_field_conflicts={
            "age_years": [
                _conflict_entry(68, "src-1"),
                _conflict_entry(71, "src-2"),
            ]
        },
    )
    with pytest.raises(ValueError, match="clinical_conflicts"):
        screen_case_intake(case, declined_domains=["clinical_conflicts"])
