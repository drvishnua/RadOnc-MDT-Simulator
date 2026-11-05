"""Deterministic case-data provenance and unsupported-claim safeguards."""

from __future__ import annotations
import re
from typing import Any
from app.schemas import SyntheticCase

_SINGLE_FIELDS = {
    "age_years": "Age (years)", "sex_at_birth": "Sex at birth",
    "primary_site": "Primary site", "histology": "Histology",
    "clinical_t_stage": "Clinical T stage", "clinical_n_stage": "Clinical N stage",
    "clinical_m_stage": "Clinical M stage", "stage_group": "Stage group",
    "performance_status": "Performance status", "pathology_summary": "Pathology summary",
    "imaging_summary": "Imaging summary",
}
_LIST_FIELDS = {
    "relevant_comorbidities": "Relevant comorbidities", "prior_treatment": "Prior treatment",
    "patient_goals": "Patient goals", "social_context": "Social context",
    "resource_context": "Resource context", "known_unknowns": "Known unknowns",
}


def build_case_prompt_context(case: SyntheticCase) -> dict[str, Any]:
    """Serialize the immutable snapshot with explicit present/not-reported semantics."""
    snapshot = case.model_dump(exclude_none=True)
    field_status: dict[str, dict[str, Any]] = {}
    for field, label in _SINGLE_FIELDS.items():
        value = getattr(case, field)
        provided = value is not None and value != ""
        field_status[field] = {"label": label, "status": "provided" if provided else "not_reported", "value": value if provided else None}
    for field, label in _LIST_FIELDS.items():
        values = getattr(case, field) or []
        field_status[field] = {"label": label, "status": "reported" if values else "not_reported", "value": values if values else None}
    field_status["case_summary"] = {
        "label": "User-provided free-text case summary",
        "status": "provided_verbatim_unparsed",
        "value": case.case_summary,
    }
    return {
        "case_snapshot": snapshot,
        "field_status": field_status,
        "interpretation_rules": [
            "not_reported means unknown/not supplied; it never means confirmed absent or negative.",
            "The case_summary is user-provided free text. Preserve its wording and do not silently normalise shorthand into confirmed structured diagnoses.",
            "Only explicitly provided clinical_t_stage, clinical_n_stage, clinical_m_stage and stage_group fields establish recorded staging.",
            "Do not infer sex, T/N/M stage, nodal status, metastatic status, performance status, prior treatment, patient goals or comorbidity negatives.",
            "Separate source facts, clinical interpretations, hypotheses/assumptions and unknowns.",
            "If free text and structured fields differ, explicitly flag the discrepancy; do not silently reconcile it.",
        ],
    }


def build_source_case_facts(case: SyntheticCase) -> list[str]:
    """Create the factual register on the server; model-generated facts are not trusted."""
    facts = [
        "User-provided case summary (verbatim; clinical interpretation is not independently confirmed): " + case.case_summary
    ]
    for field, label in _SINGLE_FIELDS.items():
        value = getattr(case, field)
        if value is not None and value != "":
            facts.append(f"Structured case field — {label}: {value}")
    for field, label in _LIST_FIELDS.items():
        values = getattr(case, field) or []
        if values:
            facts.append(f"Structured case field — {label}: " + "; ".join(values))
    facts.append("Data-status rule: empty or missing structured fields are not reported, not confirmed negative.")
    return facts[:25]


def build_case_report_title(case: SyntheticCase) -> str:
    """Build a neutral title from verified fields only; never let the model add stage."""
    parts = [value.strip() for value in (case.primary_site, case.histology) if isinstance(value, str) and value.strip()]
    description = " — ".join(parts) if parts else "Synthetic case; primary site/histology not supplied"
    return ("MDT Chair Synthesis: " + description)[:180]


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _flatten_strings(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _flatten_strings(nested)]
    return []


_QUALIFIER = re.compile(
    r"not\s+(?:confirmed|documented|provided|reported|established|specified|verified)"
    r"|unconfirmed|unverified|unknown|not\s+supplied|not\s+reported"
    r"|cannot\s+be\s+assumed|should\s+not\s+be\s+assumed|do\s+not\s+assume"
    r"|cannot\s+confirm|without\s+(?:confirmation|a\s+confirmed)"
    r"|assum(?:e|es|ed|ing|ption|ptions)|hypothetical|provisional"
    r"|\be\.g\.?\b|for\s+example|such\s+as|\bif\b"
    r"|risk\s+of|inability\s+to\s+distinguish|cannot\s+distinguish"
    r"|not\s+possible\s+to\s+distinguish|misclassif(?:y|ication|ied)",
    re.IGNORECASE,
)


def _unqualified_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    findings: list[str] = []
    for match in pattern.finditer(text):
        context = text[max(0, match.start() - 100):min(len(text), match.end() + 70)]
        if _QUALIFIER.search(context):
            continue
        token = match.group(0)
        if token not in findings:
            findings.append(token)
    return findings


def audit_unverified_case_claims(case: SyntheticCase, generated_payload: dict[str, Any]) -> list[str]:
    """Flag generated assertions that lack a corresponding structured source field."""
    text = " ".join(_flatten_strings(generated_payload))
    flags: list[str] = []
    if case.clinical_t_stage is None:
        matches = _unqualified_matches(re.compile(r"\b(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)(?:N(?:x|0|[1-3]))?(?:M(?:x|0|1))?\b", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative contains T-stage terminology (" + ", ".join(matches[:4]) + "), but clinical_t_stage is not supplied in the case snapshot.")
    if case.clinical_n_stage is None:
        matches = _unqualified_matches(re.compile(r"(?:\b(?:c|p|yc|yp)?N(?:x|0|[1-3])\b|(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)N(?:x|0|[1-3])(?:M(?:x|0|1))?\b)", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative contains N-stage terminology (" + ", ".join(matches[:4]) + "), but clinical_n_stage is not supplied in the case snapshot.")
    if case.clinical_m_stage is None:
        matches = _unqualified_matches(re.compile(r"(?:\b(?:c|p|yc|yp)?M(?:x|0|1)\b|(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)(?:N(?:x|0|[1-3]))?M(?:x|0|1)\b)", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative contains M-stage terminology (" + ", ".join(matches[:4]) + "), but clinical_m_stage is not supplied in the case snapshot.")
    source_text = case.case_summary.casefold()
    sex_is_reported_in_source = bool(
        re.search(
            r"\b(?:male|female|man|woman|boy|girl)\b|\b(?:sex|gender)\s*[:=]\s*(?:male|female)\b",
            source_text,
            re.IGNORECASE,
        )
    )
    if case.sex_at_birth is None and not sex_is_reported_in_source:
        matches = _unqualified_matches(re.compile(r"\b(?:male|female|man|woman|boy|girl)\b", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative assigns a sex/gender descriptor (" + ", ".join(matches[:4]) + "), but sex_at_birth is not supplied in the case snapshot or source text.")
    if not case.relevant_comorbidities:
        matches = _unqualified_matches(re.compile(r"\b(?:no known comorbidities|no comorbidities|no relevant medical history|otherwise healthy)\b", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative treats comorbidities as absent, but the structured comorbidity list is not reported.")
    if not case.prior_treatment:
        matches = _unqualified_matches(re.compile(r"\b(?:no prior treatment|treatment[- ]na[iï]ve|never treated)\b", re.IGNORECASE), text)
        if matches:
            flags.append("Generated narrative treats prior treatment as absent, but the structured prior-treatment list is not reported.")
    return flags[:20]


def build_case_validation_warnings(case: SyntheticCase) -> list[str]:
    """Return non-blocking completeness and free-text/structured-field warnings."""
    warnings: list[str] = []
    for field, message in (
        ("age_years", "Age is not supplied."),
        ("sex_at_birth", "Sex at birth is not supplied; do not infer it."),
        ("primary_site", "Primary site is not supplied."),
        ("histology", "Histology is not supplied."),
        ("clinical_t_stage", "Clinical T stage is not supplied."),
        ("clinical_n_stage", "Clinical N stage is not supplied."),
        ("clinical_m_stage", "Clinical M stage is not supplied."),
        ("performance_status", "Performance status is not supplied."),
    ):
        if getattr(case, field) in (None, ""):
            warnings.append(message)
    empty_fields = [field for field in ("relevant_comorbidities", "prior_treatment", "patient_goals", "social_context", "resource_context") if not getattr(case, field)]
    if empty_fields:
        warnings.append("Empty structured lists are not confirmed negatives; these fields are not reported: " + ", ".join(empty_fields) + ". Review the raw case summary before interpreting them.")
    summary = case.case_summary.casefold()
    if not case.relevant_comorbidities:
        if re.search(r"\b(dm|diabetes|diabetic)\b", summary):
            warnings.append("The free-text summary mentions diabetes/DM, but relevant_comorbidities is empty; reconcile the fields before simulation.")
        if re.search(r"\b(shtn|htn|hypertension)\b", summary):
            warnings.append("The free-text summary mentions hypertension/HTN, but relevant_comorbidities is empty; reconcile the fields before simulation.")
    if re.search(r"\b(smoker|smoking|tobacco)\b", summary):
        warnings.append("Smoking is mentioned in free text; keep it identified as a text-reported risk factor unless explicitly structured/confirmed.")
    return warnings
