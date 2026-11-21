"""Deterministic pre-MDT intake completeness screening.

This module identifies absent information and clinical contradictions only.
It never infers clinical values, interprets a missing field as a negative,
or changes the supplied case.
"""
from __future__ import annotations

from typing import Any

from app.schemas import SyntheticCase


# Each prompt is an information request, not a clinical recommendation.
_SCREENING_DOMAINS: tuple[dict[str, Any], ...] = (
    {
        "domain": "patient_and_disease",
        "fields": ("age_years", "sex_at_birth", "primary_site", "histology"),
        "question": "Could you provide the patient's age, sex at birth, primary cancer site and histology, if known?",
    },
    {
        "domain": "staging_and_investigations",
        "fields": (
            "clinical_t_stage",
            "clinical_n_stage",
            "clinical_m_stage",
            "stage_group",
            "staging_system",
            "staging_edition",
            "pathology_summary",
            "imaging_summary",
            "relevant_investigations",
        ),
        "question": "What staging information and investigation reports are available (including the TNM system/edition, if documented)?",
    },
    {
        "domain": "comorbidity_and_medications",
        "fields": ("relevant_comorbidities", "current_medications", "known_allergies"),
        "question": "Are there any known comorbidities, current medications or allergies? If none are known, please say so explicitly.",
    },
    {
        "domain": "performance_and_function",
        "fields": ("performance_status", "performance_status_scale", "social_context"),
        "question": "Is a performance status (with scale) documented, and is there relevant functional, family or social context?",
    },
    {
        "domain": "treatment_history",
        "fields": ("prior_treatment",),
        "question": "Has the patient received any prior cancer-directed treatment? Please include details if available.",
    },
    {
        "domain": "patient_preferences",
        "fields": ("patient_goals",),
        "question": "What are the patient's stated goals, preferences and willingness regarding treatment, if discussed?",
    },
    {
        "domain": "treatment_willingness",
        "fields": ("patient_willingness",),
        "question": "Has the patient expressed willingness, goals or refusal regarding specific treatment modalities (surgery, radiotherapy, systemic therapy)?",
    },
)

def _is_reported(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, list):
        return bool(value)
    return True


def screen_case_intake(
    case: SyntheticCase,
    *,
    declined_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Return missing-field and contradiction prompts while preserving the input snapshot exactly."""
    declined = set(declined_domains or [])
    unknown_domains = declined.difference(item["domain"] for item in _SCREENING_DOMAINS)
    if unknown_domains:
        raise ValueError("Unknown declined intake domain(s): " + ", ".join(sorted(unknown_domains)))

    # 1. Surface and structure any explicit clinical contradictions / conflicts
    conflicts: list[dict[str, Any]] = []
    conflict_questions: list[dict[str, Any]] = []
    if getattr(case, "clinical_field_conflicts", None):
        for field_name, conflict_list in case.clinical_field_conflicts.items():
            if conflict_list:
                formatted_entries = [
                    c.model_dump(exclude_none=True) if hasattr(c, "model_dump") else c
                    for c in conflict_list
                ]
                conflicts.append({
                    "field_id": field_name,
                    "status": "UNRESOLVED",
                    "conflict_count": len(conflict_list),
                    "competing_entries": formatted_entries,
                })
                conflict_questions.append({
                    "domain": "clinical_conflicts",
                    "field_id": field_name,
                    "priority": "high",
                    "question": (
                        f"There is conflicting documentation for '{field_name}'. "
                        "Which source or value is correct, or should both remain recorded as conflicting for MDT review?"
                    ),
                })

    gaps: list[dict[str, str]] = []
    missing_questions: list[dict[str, str]] = []
    domain_results: list[dict[str, Any]] = []

    for item in _SCREENING_DOMAINS:
        missing = [
            field for field in item["fields"]
            if not _is_reported(getattr(case, field, None))
        ]
        status = "DECLINED" if item["domain"] in declined else ("NEEDS_REVIEW" if missing else "DOCUMENTED")
        domain_results.append({
            "domain": item["domain"],
            "status": status,
            "missing_fields": missing,
        })
        if missing:
            gaps.extend({"domain": item["domain"], "field_id": field, "status": status} for field in missing)
            if status != "DECLINED":
                missing_questions.append({"domain": item["domain"], "question": item["question"]})

    # High-priority conflict resolution questions precede missing-details questions
    prioritized_questions = conflict_questions + missing_questions

    return {
        "screening_version": "2.0.0",
        "case_snapshot": case.model_dump(exclude_none=True),
        "domains": domain_results,
        "gaps": gaps,
        "conflicts": conflicts,
        "questions": prioritized_questions,
        "declined_domains": sorted(declined),
        "ready_to_accept_with_gaps": True,
        "disclaimer": (
            "Completeness screening only; not clinical validation. Missing information remains unknown. "
            "Declining a question records a gap and does not imply a negative or normal finding."
        ),
    }
