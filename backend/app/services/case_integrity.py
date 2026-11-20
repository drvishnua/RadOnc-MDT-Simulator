"""Deterministic case-data provenance and unsupported-claim safeguards."""

from __future__ import annotations
import re
from typing import Any
from app.schemas import SyntheticCase
from app.clinical_fields import (
    CLINICAL_FIELD_REGISTRY,
    CLINICAL_FIELD_REGISTRY_VERSION,
    CLINICAL_M_STAGE,
    CLINICAL_N_STAGE,
    CLINICAL_T_STAGE,
    PATHOLOGICAL_M_STAGE,
    PATHOLOGICAL_N_STAGE,
    PATHOLOGICAL_T_STAGE,
    build_registry_prompt_payload,
    clinical_field_registry_sha256,
    normalize_clinical_tnm_component,
    normalize_pathological_tnm_component,
    normalize_stage_group_token,
)


def is_empty_challenge_placeholder(value: object) -> bool:
    """Recognise exact empty-challenge sentinels, including source-labelled forms."""
    if not isinstance(value, str):
        return True
    body = re.sub(r"^\s*\[Sources:[^\]]+\]\s*", "", value, flags=re.IGNORECASE)
    # Some small models emit an empty sentinel followed by an explanation. Treat
    # only an explicit sentinel followed by punctuation as empty; do not mistake
    # phrases such as "None of the supplied records..." for a placeholder.
    if re.match(
        r"^\s*(?:none|nil|n/?a|no\s+(?:substantive\s+)?challenge|"
        r"no\s+source[\s-]+linked\s+challenge|none\s+identified)\s*"
        r"(?:[;:,.!?—–-]|$)",
        body,
        flags=re.IGNORECASE,
    ):
        return True
    normalised = re.sub(r"[\W_]+", " ", body.casefold()).strip()
    return normalised in {
        "none",
        "nil",
        "n a",
        "na",
        "not applicable",
        "no challenge",
        "no substantive challenge",
        "no source linked challenge",
        "none identified",
    }

_SINGLE_FIELDS = {
    "age_years": "Age (years)", "sex_at_birth": "Sex at birth",
    "primary_site": "Primary site", "anatomical_subsite": "Anatomical subsite",
    "laterality": "Laterality", "histology": "Histology",
    "histological_grade": "Histological grade",
    "clinical_t_stage": "Clinical T stage", "clinical_n_stage": "Clinical N stage",
    "clinical_m_stage": "Clinical M stage",
    "pathological_t_stage": "Pathological T stage",
    "pathological_n_stage": "Pathological N stage",
    "pathological_m_stage": "Pathological M stage",
    "stage_group": "Unqualified stage group",
    "clinical_stage_group": "Clinical stage group",
    "pathological_stage_group": "Pathological stage group",
    "staging_system": "Staging system", "staging_edition": "Staging edition",
    "performance_status": "Performance status",
    "performance_status_scale": "Performance-status scale",
    "diagnosis_date": "Diagnosis date",
    "patient_willingness": "Patient willingness",
    "patient_consent_status": "Patient consent status",
    "pathology_summary": "Pathology summary", "imaging_summary": "Imaging summary",
}
_LIST_FIELDS = {
    "current_medications": "Current medications",
    "known_allergies": "Known allergies",
    "relevant_investigations": "Relevant investigations",
    "investigation_records": "Typed investigation records",
    "relevant_comorbidities": "Relevant comorbidities",
    "prior_treatment": "Prior treatment",
    "family_history": "Family history",
    "family_caregiver_context": "Family/caregiver context",
    "patient_goals": "Patient goals",
    "patient_preferences": "Patient preferences",
    "social_context": "Social context",
    "resource_context": "Resource context",
    "known_unknowns": "Known unknowns",
}


_SOURCE_LATERALITY_CONFLICT_WARNING = (
    "The case summary contains opposing laterality statements attributed to distinct sources; "
    "preserve both statements verbatim and keep the discrepancy unresolved pending human/source "
    "verification. No source is selected."
)


def _source_laterality_integrity_warnings(case_summary: str) -> list[str]:
    """Flag explicit opposing laterality statements attributed to distinct sources.

    This is a non-blocking provenance warning. It does not select a source,
    adjudicate clinical laterality, or modify the original case summary.
    """
    if not isinstance(case_summary, str):
        return []
    source_pattern = re.compile(r"\bsource\s+(?P<label>[A-Za-z0-9_-]+)\b", re.IGNORECASE)
    side_pattern = re.compile(r"\b(left|right|ipsilateral|contralateral|opposite)\b", re.IGNORECASE)
    mentions = list(source_pattern.finditer(case_summary))
    claims: dict[str, set[str]] = {}
    for index, match in enumerate(mentions):
        end = mentions[index + 1].start() if index + 1 < len(mentions) else len(case_summary)
        segment = case_summary[match.end():end]
        if not re.search(r"\b(laterality|side|sided)\b", segment, re.IGNORECASE):
            continue
        values = {
            value.casefold()
            for value in side_pattern.findall(segment)
        }
        if values:
            claims.setdefault(match.group("label").casefold(), set()).update(values)
    values = list(claims.values())
    for index, first in enumerate(values):
        for second in values[index + 1:]:
            if (
                ("left" in first and "right" in second)
                or ("right" in first and "left" in second)
                or ("ipsilateral" in first and "contralateral" in second)
                or ("contralateral" in first and "ipsilateral" in second)
                or ("opposite" in first and second)
                or ("opposite" in second and first)
            ):
                return [_SOURCE_LATERALITY_CONFLICT_WARNING]
    return []


def build_case_prompt_context(case: SyntheticCase) -> dict[str, Any]:
    """Build one deterministic v2 case context without resolving unknowns or conflicts."""
    snapshot = case.model_dump(exclude_none=True, mode="json")
    model_snapshot = dict(snapshot)
    redacted_conflicting_fields = sorted(
        field_id
        for field_id, state in case.clinical_field_states.items()
        if state == "CONFLICTING" and field_id in CLINICAL_FIELD_REGISTRY
    )
    for field_id in redacted_conflicting_fields:
        model_snapshot[field_id] = None
    field_status: dict[str, dict[str, Any]] = {}
    canonical_field_values: dict[str, dict[str, Any]] = {}
    normalization_warnings: list[str] = []

    for field, label in _SINGLE_FIELDS.items():
        value = getattr(case, field)
        explicit_state = case.clinical_field_states.get(field)
        provided = value is not None and value != ""
        status = explicit_state.casefold() if explicit_state else ("provided" if provided else "not_reported")
        field_status[field] = {
            "label": label,
            "status": status,
            "value": None if explicit_state == "CONFLICTING" else (snapshot.get(field) if provided else None),
        }
    for field, label in _LIST_FIELDS.items():
        values = getattr(case, field) or []
        explicit_state = case.clinical_field_states.get(field)
        status = explicit_state.casefold() if explicit_state else ("reported" if values else "not_reported")
        field_status[field] = {
            "label": label,
            "status": status,
            "value": None if explicit_state == "CONFLICTING" else (snapshot.get(field) if values else None),
        }
    field_status["scenario_title"] = {
        "label": "Scenario title", "status": "provided", "value": case.scenario_title,
    }
    field_status["case_summary"] = {
        "label": "User-provided free-text case summary",
        "status": "provided_verbatim_unparsed",
        "value": case.case_summary,
    }

    for field_id, definition in CLINICAL_FIELD_REGISTRY.items():
        value = getattr(case, field_id)
        if field_id == "case_summary":
            default_state = "PRESENT"
        elif isinstance(value, list):
            default_state = "PRESENT" if value else "NOT_REPORTED"
        else:
            default_state = "PRESENT" if value is not None and value != "" else "NOT_REPORTED"
        state = case.clinical_field_states.get(field_id, default_state)
        explicit_sources = case.clinical_field_provenance.get(field_id, [])
        conflict_candidates = case.clinical_field_conflicts.get(field_id, [])

        # If no document/source metadata was supplied, identify only the input
        # field itself. This is not independent verification of the underlying fact.
        if explicit_sources:
            provenance = [source.model_dump(mode="json") for source in explicit_sources]
        elif state == "PRESENT":
            source_type = "CASE_SUMMARY" if field_id == "case_summary" else "STRUCTURED_CASE_INPUT"
            provenance = [{
                "source_type": source_type,
                "source_reference": f"SyntheticCase.{field_id}",
                "source_excerpt": value if isinstance(value, str) else json.dumps(
                    snapshot.get(field_id), ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ),
                "verification_status": "user_supplied_not_independently_verified",
            }]
        else:
            provenance = []

        item: dict[str, Any] = {
            "field_id": field_id,
            "label": definition.label,
            "value_type": definition.value_type,
            "state": state,
            "status": state,
            "raw_value": snapshot.get(field_id),
            "canonical_comparison_value": None,
            "unit": definition.unit,
            "allowed_values": list(definition.allowed_values),
            "validation_rule": definition.validation_rule,
            "source_requirement": definition.source_requirement,
            "provenance": provenance,
            "conflict_candidates": [
                candidate.model_dump(mode="json") for candidate in conflict_candidates
            ],
        }

        # A conflicting flat-field value is retained in the immutable case
        # snapshot and in source-specific conflict_candidates, but is not shown
        # as a selected model-facing raw value.
        if state == "CONFLICTING":
            item["raw_value"] = None

        if state == "PRESENT":
            item["canonical_comparison_value"] = snapshot.get(field_id)
            if field_id in (CLINICAL_T_STAGE, CLINICAL_N_STAGE, CLINICAL_M_STAGE) and value not in (None, ""):
                try:
                    item["canonical_comparison_value"] = normalize_clinical_tnm_component(field_id, value)
                except ValueError as exc:
                    item["canonical_comparison_value"] = None
                    item["normalization_warning"] = str(exc)
                    normalization_warnings.append(f"{field_id}: {exc}")
            elif field_id in (PATHOLOGICAL_T_STAGE, PATHOLOGICAL_N_STAGE, PATHOLOGICAL_M_STAGE) and value not in (None, ""):
                try:
                    item["canonical_comparison_value"] = normalize_pathological_tnm_component(field_id, value)
                except ValueError as exc:
                    item["canonical_comparison_value"] = None
                    item["normalization_warning"] = str(exc)
                    normalization_warnings.append(f"{field_id}: {exc}")
            elif field_id in {"stage_group", "clinical_stage_group", "pathological_stage_group"} and value not in (None, ""):
                try:
                    item["canonical_comparison_value"] = normalize_stage_group_token(value)
                except ValueError as exc:
                    item["canonical_comparison_value"] = None
                    item["normalization_warning"] = str(exc)
                    normalization_warnings.append(f"{field_id}: {exc}")

        canonical_field_values[field_id] = item

    any_tnm_supplied = any(
        getattr(case, field_id) not in (None, "")
        for field_id in (
            CLINICAL_T_STAGE, CLINICAL_N_STAGE, CLINICAL_M_STAGE,
            PATHOLOGICAL_T_STAGE, PATHOLOGICAL_N_STAGE, PATHOLOGICAL_M_STAGE,
            "stage_group", "clinical_stage_group", "pathological_stage_group",
        )
    )
    staging_context_warnings: list[str] = []
    if any_tnm_supplied:
        missing_context = [
            name for name, supplied in (
                ("primary site", case.primary_site),
                ("staging system", case.staging_system),
                ("staging edition", case.staging_edition),
            ) if supplied in (None, "")
        ]
        if missing_context:
            warning = (
                "Staging interpretation is not validated because "
                + ", ".join(missing_context)
                + " is not supplied. Preserve the recorded token; do not infer compatibility or stage."
            )
            staging_context_warnings.append(warning)
            normalization_warnings.append(warning)
    if (
        case.performance_status not in (None, "")
        and case.performance_status_scale in (None, "")
    ):
        staging_context_warnings.append(
            "Performance-status value is recorded without its scale; do not assume ECOG, WHO or Karnofsky equivalence."
        )

    registry_payload = build_registry_prompt_payload()
    return {
        "clinical_field_registry": registry_payload,
        "clinical_field_registry_version": CLINICAL_FIELD_REGISTRY_VERSION,
        "clinical_field_registry_sha256": clinical_field_registry_sha256(),
        "case_snapshot": model_snapshot,
        "case_snapshot_redacted_conflicting_fields": redacted_conflicting_fields,
        "case_snapshot_projection_note": (
            "Model-facing projection only. Conflicting flat field values are redacted; "
            "source-specific conflict candidates remain available. The persisted immutable case snapshot is unchanged."
        ),
        "canonical_field_values": canonical_field_values,
        "field_status": field_status,
        "tnm_normalization_warnings": normalization_warnings,
        "staging_context_warnings": staging_context_warnings,
        "source_integrity_warnings": _source_laterality_integrity_warnings(case.case_summary),
        "interpretation_rules": [
            "The v2 canonical field registry is immutable; field IDs and meanings must not be renamed or repurposed.",
            "Registry constants standardise identifiers and semantics; they do not guarantee model adherence or prevent every hallucination.",
            "UNKNOWN, NOT_REPORTED, NOT_ASSESSED, PENDING, DECLINED and NOT_APPLICABLE are distinct states and are never normal/negative findings.",
            "CONFIRMED_ABSENT requires explicit source provenance; an empty or omitted field is not a confirmed absent or negative finding.",
            "CONFLICTING fields retain all source-specific candidate values and remain unresolved; do not select or average a source.",
            "The raw case snapshot and source excerpts must be preserved; canonical comparison values are analysis-only and do not overwrite the source.",
            "Clinical and pathological T/N/M components and stage groups are separate fields. Pathological values never establish clinical stage.",
            "A T/N/M token is not interpreted without the supplied primary site, staging system and edition; T/N/M lexical normalization is not clinical staging validation.",
            "A lesion's size or anatomical subsite alone does not establish a T category or stage group; never infer a T category from lesion size; never infer nodal/metastatic status from missing data; never infer stage group or resectability from missing data.",
            "Performance-status scores require their named scale; do not infer ECOG/WHO/Karnofsky equivalence.",
            "Separate source facts, clinical interpretations, hypotheses/assumptions and unknowns. Flag contradictions; never silently reconcile them.",
            "Automatically labelled case-input provenance is user-supplied provenance, not independent verification of a source document.",
        ],
    }

_ATTRIBUTED_NOTE_OPINION_PATTERN = re.compile(
    r"\b(?:the\s+)?[A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,3}\s+note\s+"
    r"(?:recommends?|proposes?|suggests?|advises?|opines?|believes?|prefers?|"
    r"favo[u]?rs?|supports?|advocates?|argues?|urges?)\b",
    re.IGNORECASE,
)


def extract_attributed_note_opinions(case_summary: str) -> list[dict[str, str]]:
    """Extract explicit note-opinion spans with stable server-owned source IDs.

    Each excerpt is an exact contiguous span from the original case summary.
    This records source wording only; it does not verify the source or its
    clinical content. The next attributed note or sentence boundary delimits
    each span, including multiple opinions joined by semicolons.
    """
    matches = list(_ATTRIBUTED_NOTE_OPINION_PATTERN.finditer(case_summary))
    opinions: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(case_summary)
        segment = case_summary[match.end():next_start]
        sentence_end = re.search(r"[.!?](?=\s|$)", segment)
        end = match.end() + sentence_end.end() if sentence_end else next_start
        excerpt = case_summary[match.start():end].rstrip(" \t\r\n;,:")
        if excerpt:
            opinions.append({
                "source_id": f"CASE:case_summary#{len(opinions) + 1}",
                "source_excerpt": excerpt,
            })
    return opinions


def case_summary_has_attributed_opinions(case_summary: str) -> bool:
    """Detect explicit speaker-attributed recommendations/statements in case text.

    This deliberately recognises only clear attribution patterns; ordinary clinical
    facts and unlabelled treatment words are not treated as an attributed opinion.
    """
    role_opinion_pattern = (
        r"\b(?:the\s+)?(?:surgeon|oncologist|medical oncologist|radiation oncologist|cardiologist|radiologist|pathologist|physician|"
        r"referring\s+(?:doctor|clinician)|patient|family|mdt|tumour\s+board|tumor\s+board)\s+"
        r"(?:recommends?|proposes?|suggests?|advises?|states?|reports?|says?|said|"
        r"opines?|believes?|prefers?|wishes?|requests?|argues?)\b"
    )
    named_person_opinion_pattern = (
        r"\b(?-i:[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){1,2})\s+"
        r"(?i:recommends?|proposes?|suggests?|advises?|states?|reports?|says?|said|"
        r"opines?|believes?|prefers?|wishes?|requests?|argues?)\b"
    )
    service_note_pattern = (
        r"\b(?-i:[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){0,2})\s+"
        r"(?i:(?:service|department)\s+note\s+"
        r"(?:recommends?|proposes?|suggests?|advises?|states?|reports?|says?|said|"
        r"opines?|believes?|prefers?|wishes?|requests?|argues?))\b"
    )
    specialty_note_opinion_pattern = (
        r"\b(?:the\s+)?(?:[a-z][a-z.'-]*\s+){0,2}"
        r"(?:surgical|medical|radiation|clinical|oncology)\s+note\s+"
        r"(?:recommends?|proposes?|suggests?|advises?|favo[u]?rs?|supports?|opposes?|prefers?|argues?)\b"
    )
    attributed_person_pattern = (
        r"\b(?i:according\s+to|per|as\s+(?:reported|stated|recommended)\s+by)\s+"
        r"(?:the\s+)?"
        r"(?:(?i:surgeon|oncologist|medical oncologist|radiation oncologist|cardiologist|radiologist|pathologist|physician|patient|family)|"
        r"(?-i:[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){1,2}))\b"
    )
    return any((
        re.search(role_opinion_pattern, case_summary, re.IGNORECASE),
        re.search(named_person_opinion_pattern, case_summary),
        re.search(service_note_pattern, case_summary),
        re.search(specialty_note_opinion_pattern, case_summary, re.IGNORECASE),
        re.search(attributed_person_pattern, case_summary),
    ))


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
    description = " — ".join(parts) if parts else "Case details not supplied"
    return ("MDT Chair Synthesis: " + description)[:180]


def _flatten_strings(value: Any) -> list[str]:
    """Collect narrative text while excluding server-generated audit metadata."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        non_narrative = {
            "case_data_integrity_flags",
            "source_reference_integrity_flags",
            # These are verbatim quotations bound to a case source or supplied peer.
            # Audit the role's own narrative fields, not the quoted source material.
            "source_excerpt",
            "evidence_excerpt",
            "model_reported_evidence_excerpt",
            "provenance_excerpt",
        }
        return [
            item
            for key, nested in value.items()
            if key not in non_narrative
            for item in _flatten_strings(nested)
        ]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _flatten_strings(nested)]
    return []


_QUALIFIER = re.compile(
    r"not\s+(?:confirmed|documented|provided|reported|established|specified|verified)"
    r"|unconfirmed|unverified|unknown|not\s+supplied|not\s+reported"
    r"|cannot\s+be\s+assumed|should\s+not\s+be\s+assumed|do\s+not\s+assume"
    r"|cannot\s+confirm|(?:does|do|did)\s+not\s+(?:imply|mean|confirm|establish|show|demonstrate|support|indicate|prove)"
    r"|without\s+(?:confirmation|a\s+confirmed)"
    r"|no\s+prior\s+treatment\s+(?:data|records?|history|information|details|documentation)\b"
    r"|assum(?:e|es|ed|ing|ption|ptions)|hypothetical|provisional"
    r"|\be\.g\.?\b|for\s+example|such\s+as|\bif\b"
    r"|risk\s+of|inability\s+to\s+distinguish|cannot\s+distinguish"
    r"|not\s+possible\s+to\s+distinguish|misclassif(?:y|ication|ied)"
    r"|cannot\s+exclude|exclusion\s+of|exclude[sd]?\s+(?:the\s+)?possibility\s+of"
    r"|rule\s+out|not\s+(?:evidence|proof)\s+of",
    re.IGNORECASE,
)


# Sentence punctuation alone is too broad: a qualifier for one assertion must
# not suppress a separate assertion later in the sentence. Treat commas and
# contrast markers as clause boundaries while keeping a qualifier attached to
# the assertion in its own clause.
_CLAUSE_BOUNDARY = re.compile(
    r"[.!?;:\n,]|\b(?:but|however|whereas|while|although|yet|nevertheless)\b",
    re.IGNORECASE,
)

def _collapse_horizontal_whitespace(text: str) -> str:
    """Collapse repeated horizontal whitespace for bounded, reproducible regex matching.

    This function creates an analysis-only view. The original case and model text
    remain unchanged in their persisted source records.
    """
    output: list[str] = []
    in_horizontal_run = False
    for character in text:
        if character in " \t\f\v":
            if not in_horizontal_run:
                output.append(" ")
            in_horizontal_run = True
        else:
            output.append(character)
            in_horizontal_run = False
    return "".join(output)



def _unqualified_matches(
    pattern: re.Pattern[str],
    text: str,
    *,
    ignore_generated_prefix_pattern: re.Pattern[str] | None = None,
) -> list[str]:
    """Return assertion-like matches, applying qualifiers only within the same clause."""
    findings: list[str] = []
    # Repeated spaces/tabs are common in pasted case text. Collapse them in an
    # analysis-only copy so whitespace-heavy input cannot amplify regex work.
    analysis_text = _collapse_horizontal_whitespace(text)
    for match in pattern.finditer(analysis_text):
        # Preserve the whole-sentence question safeguard even when the clause
        # itself ends at a comma or contrast marker before the question mark.
        sentence_end = min(
            (
                position
                for mark in ".!?;:\n"
                if (position := analysis_text.find(mark, match.end())) >= 0
            ),
            default=len(analysis_text),
        )
        if sentence_end < len(analysis_text) and analysis_text[sentence_end] == "?":
            continue

        left = max(
            (boundary.end() for boundary in _CLAUSE_BOUNDARY.finditer(analysis_text, 0, match.start())),
            default=0,
        )
        right = min(
            (boundary.start() for boundary in _CLAUSE_BOUNDARY.finditer(analysis_text, match.end())),
            default=len(analysis_text),
        )
        clause = analysis_text[left:right]
        # A reported absence of a peer's claim is not itself a clinical finding.
        # This exception is deliberately limited to an attributed report prefix;
        # direct assertions about an option remain subject to the normal audit.
        if (
            ignore_generated_prefix_pattern is not None
            and ignore_generated_prefix_pattern.search(analysis_text[left:match.start()])
        ):
            continue
        if _QUALIFIER.search(clause):
            continue
        # A separate "unknown" or "unverified" phrase elsewhere in the same clause
        # must not hide a categorical unmet-prerequisite assertion.
        token = match.group(0).strip()
        if token and token.casefold() not in {item.casefold() for item in findings}:
            findings.append(token)
    return findings


def _unsupported_matches(
    pattern: re.Pattern[str],
    generated_text: str,
    source_text: str,
    *,
    ignore_generated_prefix_pattern: re.Pattern[str] | None = None,
) -> list[str]:
    """Keep exact assertion snippets not already present in the supplied case text."""
    source_matches = {item.casefold() for item in _unqualified_matches(pattern, source_text)}
    return [
        item for item in _unqualified_matches(
            pattern,
            generated_text,
            ignore_generated_prefix_pattern=ignore_generated_prefix_pattern,
        )
        if item.casefold() not in source_matches
    ]


_TNM_EXPRESSION_PATTERN = re.compile(
    r"\b(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)(?:N(?:x|0|[1-3]))?(?:M(?:x|0|1))?\b"
    r"|\b(?:c|p|yc|yp)?N(?:x|0|[1-3])\b"
    r"|\b(?:c|p|yc|yp)?M(?:x|0|1)\b",
    re.IGNORECASE,
)

def redact_flagged_tnm_values(value: str, integrity_flags: object) -> str:
    """Redact only TNM components named by source-specific flags in prompt views.

    Supported, unflagged components in a combined TNM expression are preserved.
    This helper never mutates saved contributions or the original audit flags.
    """
    if not isinstance(value, str) or not value:
        return value
    if isinstance(integrity_flags, str):
        flags = [integrity_flags]
    elif isinstance(integrity_flags, (list, tuple)):
        flags = [item for item in integrity_flags if isinstance(item, str)]
    else:
        return value

    component_patterns = (
        ("T", re.compile(r"(?:yc|yp|c|p)?(T(?:is|x|0|[1-4][a-d]?))", re.IGNORECASE)),
        ("N", re.compile(r"(?:yc|yp|c|p)?(N(?:x|0|[1-3]))", re.IGNORECASE)),
        ("M", re.compile(r"(?:yc|yp|c|p)?(M(?:x|0|1))", re.IGNORECASE)),
    )

    def component_matches(token: str) -> list[tuple[int, int, str]]:
        found: list[tuple[int, int, str]] = []
        for _, pattern in component_patterns:
            for match in pattern.finditer(token):
                # Replace the prefix together with the stage token so a redaction
                # cannot leave a misleading orphaned c/p/yc/yp category prefix.
                found.append((match.start(), match.end(), match.group(1).upper()))
        return found

    flagged_components: set[str] = set()
    for flag in flags:
        for match in _TNM_EXPRESSION_PATTERN.finditer(flag):
            flagged_components.update(
                component for _, _, component in component_matches(match.group(0))
            )

    if not flagged_components:
        return value

    def redact_match(match: re.Match[str]) -> str:
        token = match.group(0)
        components = component_matches(token)
        flagged = [
            (start, end, component)
            for start, end, component in components
            if component in flagged_components
        ]
        if not flagged:
            return token
        if len(flagged) == len(components):
            return "[flagged unsupported staging assertion]"

        redacted = token
        for start, end, _ in sorted(flagged, reverse=True):
            redacted = (
                redacted[:start]
                + "[flagged unsupported staging assertion]"
                + redacted[end:]
            )
        return redacted

    return _TNM_EXPRESSION_PATTERN.sub(redact_match, value)


_TNM_NEGATED_PREFIX_PATTERN = re.compile(
    r"\b(?:does|do|did)\s+not\s+(?:(?:automatically|by\s+itself|alone)\s+)?"
    r"(?:equate\s+(?:to|with)|equal|translate\s+(?:to|into)|infer|define|constitute|"
    r"establish|confirm|represent|indicate|classify)"
    r"(?:\s+(?:a|an|the|confirmed|as|to|into)){0,2}\s*$"
    r"|\b(?:cannot|can\s+not)\s+(?:be\s+)?(?:inferred|determined|classified|"
    r"established|confirmed|assigned|defined|excluded|converted)(?:\s+(?:as|to|into))?\s*$"
    r"|\bcannot\s+infer\s*$"
    r"|\b(?:should|must)\s+not\s+be\s+(?:inferred|assumed|classified|assigned)\s*$"
    r"|\bdo\s+not\s+(?:infer|assume|classify|assign)\s*$"
    r"|\b(?:not\s+equivalent|not\s+identical)\s+to\s*$"
    r"|\b(?:insufficient|inadequate)\s+to\s+(?:confirm|establish|classify|define|call)\s*$"
    r"|\b(?:may|might|could)\s+(?:be|suggest|represent|indicate)\s*$"
    r"|\b(?:suggests?|suggested|suspected|whether|potential|potentially|"
    r"possible|possibly|hypothetical|provisional|unconfirmed|unverified)\s*$"
    r"|\b(?:review\s+)?(?:guidelines?|guidance|criteria)\s+for\s*$"
    r"|\b(?:risk\s+of|cannot\s+exclude|does\s+not\s+permit\s+exclusion\s+of|"
    r"not\s+evidence\s+of)\s*$",
    re.IGNORECASE,
)
_TNM_NEGATED_SUFFIX_PATTERN = re.compile(
    r"^\s*(?:cannot\s+(?:be\s+)?(?:inferred|assumed|determined|confirmed|excluded|established)|"
    r"(?:should|must)\s+not\s+be\s+(?:inferred|assumed|classified|assigned)|"
    r"(?:is|are|was|were|remains?)\s+(?:not\s+)?(?:confirmed|established|documented|"
    r"reported|verified|known|determined|inferable|unknown|unclear|undetermined)|"
    r"(?:status|stage|category)\s+(?:is\s+|remains\s+)?(?:unknown|unclear|undetermined|"
    r"not\s+confirmed|not\s+established|not\s+documented))\b",
    re.IGNORECASE,
)
_TNM_CONDITIONAL_SUFFIX_PATTERN = re.compile(
    r"\b(?:once\s+(?:the\s+)?(?:full\s+)?staging(?:\s+data)?\s+"
    r"(?:is|are|has\s+been|have\s+been)\s+(?:confirmed|provided|completed|available)|"
    r"pending\s+(?:the\s+)?(?:full\s+)?work[- ]?up|"
    r"pending\s+complete\s+staging|"
    r"after\s+staging\s+(?:is|has\s+been)\s+confirmed)\b",
    re.IGNORECASE,
)


_TNM_ANAPHORIC_REJECTION_PATTERN = re.compile(
    r"\b(?:but|however|yet)\s+(?:this|that|these|those)\s+"
    r"(?:is|are|was|were)\s+not\s+(?:confirmed|established|documented|verified)\b",
    re.IGNORECASE,
)


def _unqualified_tnm_matches(value: str) -> list[str]:
    """Return TNM tokens that are asserted, not explicitly rejected as inference.

    The general case-claim qualifier matcher intentionally remains unchanged.
    These additional forms are TNM-specific and are scoped to the individual
    token, so rejecting an inferred T category cannot hide a separate asserted
    N/M category later in the same clause.
    """
    analysis_text = _collapse_horizontal_whitespace(value)
    findings: list[str] = []
    previous_qualified_end: int | None = None
    previous_qualified_clause: tuple[int, int] | None = None
    for match in _TNM_EXPRESSION_PATTERN.finditer(analysis_text):
        sentence_end = min(
            (
                position
                for mark in ".!?;:\n"
                if (position := analysis_text.find(mark, match.end())) >= 0
            ),
            default=len(analysis_text),
        )
        if sentence_end < len(analysis_text) and analysis_text[sentence_end] == "?":
            continue

        left = max(
            (boundary.end() for boundary in _CLAUSE_BOUNDARY.finditer(analysis_text, 0, match.start())),
            default=0,
        )
        right = min(
            (boundary.start() for boundary in _CLAUSE_BOUNDARY.finditer(analysis_text, match.end())),
            default=len(analysis_text),
        )

        # A rejected or hypothetical TNM list may contain several components
        # joined by "or" or "/". Carry that qualification only across the exact
        # list connector; do not let it hide a later, independent TNM assertion.
        if previous_qualified_end is not None and previous_qualified_clause == (left, right):
            connector = analysis_text[previous_qualified_end:match.start()]
            if connector.strip().casefold() in {"/", "or"}:
                previous_qualified_end = match.end()
                continue
        previous_qualified_end = None
        previous_qualified_clause = None

        clause = analysis_text[left:right]
        prefix = analysis_text[max(left, match.start() - 120):match.start()]
        suffix = analysis_text[match.end():min(right, match.end() + 120)]
        following_sentence_text = analysis_text[match.end():sentence_end]
        is_qualified = (
            _QUALIFIER.search(clause) is not None
            or _TNM_NEGATED_PREFIX_PATTERN.search(prefix) is not None
            or _TNM_NEGATED_SUFFIX_PATTERN.match(suffix) is not None
            or _TNM_CONDITIONAL_SUFFIX_PATTERN.search(suffix) is not None
            or _TNM_ANAPHORIC_REJECTION_PATTERN.search(following_sentence_text) is not None
        )
        if is_qualified:
            previous_qualified_end = match.end()
            previous_qualified_clause = (left, right)
            continue

        token = match.group(0).strip()
        if token and token.casefold() not in {item.casefold() for item in findings}:
            findings.append(token)
    return findings


def _tnm_component_values(
    value: str,
    component: str,
    *,
    allowed_prefixes: tuple[str, ...] = ("", "C", "YC"),
    default_prefix: str | None = None,
) -> set[str]:
    """Extract TNM components without collapsing clinical/pathological phases.

    A prefix on a combined token (for example pT2N1M0) applies to every
    component in that token. Treatment-phase prefixes remain distinct.
    """
    if component not in {"T", "N", "M"}:
        raise ValueError(f"Unsupported TNM component: {component}")
    token_patterns = {
        "T": r"(?:IS|X|0|[1-4][A-D]?)",
        "N": r"(?:X|0|[1-3])",
        "M": r"(?:X|0|1)",
    }
    combined_pattern = re.compile(
        r"(?<![A-Z0-9])(?P<prefix>YC|YP|C|P)?"
        r"T(?P<T>IS|X|0|[1-4][A-D]?)"
        r"(?P<N>N(?:X|0|[1-3]))?"
        r"(?P<M>M(?:X|0|1))?"
        r"(?![A-Z0-9])",
        re.IGNORECASE,
    )
    standalone_pattern = re.compile(
        rf"(?<![A-Z0-9])(?P<prefix>YC|YP|C|P)?"
        rf"(?P<component>{component})(?P<value>{token_patterns[component]})(?![A-Z0-9])",
        re.IGNORECASE,
    )
    values: set[str] = set()
    for snippet in _unqualified_tnm_matches(value):
        covered_spans: list[tuple[int, int]] = []
        for combined in combined_pattern.finditer(snippet):
            prefix = (combined.group("prefix") or "").upper()
            effective_prefix = prefix or (default_prefix or "")
            if effective_prefix not in allowed_prefixes:
                continue
            for name in ("T", "N", "M"):
                raw_component = combined.group(name)
                if not raw_component:
                    continue
                if name == component:
                    category_value = raw_component[1:] if name in {"N", "M"} else raw_component
                    category = f"{name}{category_value.upper()}"
                    key = f"{effective_prefix}:{category}" if effective_prefix in {"YC", "P", "YP"} else category
                    values.add(key)
            covered_spans.append(combined.span())

        for match in standalone_pattern.finditer(snippet):
            if any(match.start() < end and match.end() > start for start, end in covered_spans):
                continue
            prefix = (match.group("prefix") or "").upper()
            effective_prefix = prefix or (default_prefix or "")
            if effective_prefix not in allowed_prefixes:
                continue
            category = f"{component}{match.group('value').upper()}"
            key = f"{effective_prefix}:{category}" if effective_prefix in {"YC", "P", "YP"} else category
            values.add(key)
    return values


_STAGE_GROUP_ASSERTION_PATTERN = re.compile(
    r"\b(?P<kind>clinical|pathological)?[ \t\r\n]*"
    r"(?:stage[ \t\r\n]?(?:group[ \t\r\n]?)?)"
    r"(?:[ \t\r\n]*(?:is|was|of)?[ \t\r\n]*[:=]?[ \t\r\n]*)?"
    r"(?P<number>IV|III|II|I|[1-4])(?P<suffix>[ABC])?\b",
    re.IGNORECASE,
)


def _stage_group_records(value: str) -> list[tuple[str, str, str]]:
    """Return explicit (kind, normalized group, source excerpt) records."""
    records: list[tuple[str, str, str]] = []
    roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4}
    for snippet in _unqualified_matches(_STAGE_GROUP_ASSERTION_PATTERN, value):
        match = _STAGE_GROUP_ASSERTION_PATTERN.search(snippet)
        if not match:
            continue
        numeral = match.group("number").upper()
        suffix = (match.group("suffix") or "").upper()
        number = roman_values.get(numeral, int(numeral) if numeral.isdigit() else None)
        if number is None:
            continue
        kind = (match.group("kind") or "UNSPECIFIED").upper()
        records.append((kind, f"{number}{suffix}", snippet))
    return records


def _stage_group_value_key(value: str) -> str | None:
    """Delegate stage-group lexical normalization to the canonical registry."""
    try:
        return normalize_stage_group_token(value)
    except ValueError:
        return None


def _stage_group_values(value: str) -> set[str]:
    """Compatibility helper returning stage group values without their label."""
    key = _stage_group_value_key(value)
    return {key} if key else set()


def _stage_group_supported(generated_key: str, source_keys: set[str]) -> bool:
    """A documented substage supports its parent stage; a parent does not imply a substage."""
    return any(
        source_key == generated_key
        or (generated_key.isdigit() and source_key.startswith(generated_key))
        for source_key in source_keys
    )


_PREREQUISITE_STATUS_WORD_PATTERN = re.compile(
    r"\b(?:unmet|unfulfilled|not\s+(?:been\s+)?(?:met|fulfilled)|failed|negative(?!\s+(?:[\w-]+\s+){0,2}findings\b))\b",
    re.IGNORECASE,
)
_PREREQUISITE_NON_ASSERTION_PREFIX_PATTERN = re.compile(
    r"\bwithout\s+(?:converting|treating|describing|classifying|interpreting|"
    r"labelling|labeling|presenting|regarding)\b[^.!?;:\n]{0,100}\b(?:as|into)\s*$"
    r"|\b(?:do|does|did)\s+not\s+(?:convert|treat|describe|classify|interpret|"
    r"label|regard|present)\b[^.!?;:\n]{0,100}\b(?:as|into)\s*$"
    r"|\b(?:not|never)\s+(?:(?:to\s+be|being)\s+)?(?:converted|treated|described|"
    r"classified|interpreted|labelled|labeled|presented|regarded)\s+as\s*$"
    r"|\b(?:must|should|need\s+to)\s+not\s+(?:be\s+)?(?:converted|treated|described|"
    r"classified|interpreted|labelled|labeled|presented|regarded)\s+(?:as|into)\s*$"
    r"|\brather\s+than\s+(?:converting|treating|describing|classifying|interpreting|"
    r"labelling|labeling|presenting|regarding)\b[^.!?;:\n]{0,100}"
    r"\b(?:as|into|claims?\s+of|assertions?\s+of|findings?\s+of|statements?\s+of)\s*$"
    r"|\b(?:does|do|did)\s+not\s+(?:imply|mean|confirm|establish|show|demonstrate|support|indicate|prove)"
    r"\b[^.!?;:\n]{0,100}\b(?:is|are|was|were|remain(?:s)?|have(?:\s+been)?|has(?:\s+been)?)\s*$"
    r"|\bcannot\s+(?:confirm|establish|show|demonstrate|indicate)\b[^.!?;:\n]{0,100}"
    r"\b(?:is|are|was|were|remain(?:s)?|have(?:\s+been)?|has(?:\s+been)?)\s*$"
    r"|\b(?:unknown|unclear|undetermined|not\s+clear)\s+whether\b[^.!?;:\n]{0,100}"
    r"\b(?:is|are|was|were|remain(?:s)?|have(?:\s+been)?|has(?:\s+been)?)\s*$"
    r"|\bnot\s+(?:yet\s+)?(?:confirmed|documented|provided|reported|established|specified|verified)"
    r"\s+as\s*$"
    r"|\b(?:not|never)\s+(?:a|an)\s+(?:conclusion|claim|assertion|finding|determination)\s+that\b"
    r"[^.!?;:\n]{0,100}\s*$"
    # A negated attribution ("neither peer asserts that prerequisites are met")
    # reports what peers did not claim; it is not an assertion that they are met.
    # The enclosing matcher has already clipped the text to a single clause,
    # so a separate assertion after a clause boundary remains independently audited.
    r"|\bneither\s+(?:(?:of\s+)?(?:the\s+)?(?:selected\s+)?"
    r"(?:source|peer|note|role|agent|specialist|contribution|assessment|record|report)s?)\b"
    r"[^.!?;:\n]{0,100}\b(?:asserts?|claims?|states?|says?|reports?|indicates?|"
    r"suggests?|recommends?|endorses?|confirms?)\b[^.!?;:\n]{0,140}\s*$",
    re.IGNORECASE,
)


def _unqualified_prerequisite_status_matches(
    pattern: re.Pattern[str], value: str
) -> list[str]:
    """Find categorical unmet-prerequisite claims without misreading explicit denials.

    Unlike a generic sentence-level qualifier, the denial must directly govern
    the status word: e.g. "without converting them into unmet conditions".
    This keeps a negated description from suppressing a separate positive claim.
    """
    findings: list[str] = []
    for match in pattern.finditer(value):
        sentence_end = min(
            (
                position
                for mark in ".!?;:\n"
                if (position := value.find(mark, match.end())) >= 0
            ),
            default=len(value),
        )
        if sentence_end < len(value) and value[sentence_end] == "?":
            continue

        left = max(
            (boundary.end() for boundary in _CLAUSE_BOUNDARY.finditer(value, 0, match.start())),
            default=0,
        )
        status_word = _PREREQUISITE_STATUS_WORD_PATTERN.search(match.group())
        if status_word is None:
            # Bare "met" is not a negative status in general. The dedicated
            # matcher accepts only the explicit "neither prerequisite is met"
            # construction, so recover its terminal token narrowly here.
            if (
                match.group().casefold().startswith("neither ")
                and re.search(
                    r"\b(?:is|are|was|were|has\s+been|have\s+been)\s+met\b$",
                    match.group(),
                    re.IGNORECASE,
                )
            ):
                status_word = re.search(r"\bmet\b", match.group(), re.IGNORECASE)
            else:
                continue
        before_status = value[left:match.start() + status_word.start()]
        if _PREREQUISITE_NON_ASSERTION_PREFIX_PATTERN.search(before_status):
            continue
        # Distinguish explicit denial of a negative-status word ("unknown, not unmet",
        # "unknown rather than unfulfilled") from an actual failed prerequisite.
        # Do not exempt "not met": that remains a categorical non-fulfilment assertion.
        status_token = status_word.group().casefold()
        if (
            status_token == "negative"
            and re.search(
                r"\b(?:unknown|unclear|undetermined)\b"
                r"[^.!?;:\n]{0,120}\brather\s+than\s+absent\s+or\s*$",
                before_status,
                re.IGNORECASE,
            )
        ):
            # "Unknown ... rather than absent or negative" explicitly rejects
            # a negative finding; the word "negative" is not an asserted result.
            continue
        if (
            status_token in {"unmet", "unfulfilled", "failed", "negative"}
            and re.search(r"\b(?:not|never|rather\s+than|instead\s+of)\s*$", before_status, re.IGNORECASE)
        ):
            continue
        # In "unknown rather than met or unmet", the second status word is part
        # of a contrast describing uncertainty, not a finding of non-fulfilment.
        # Keep this exception narrow: an independent assertion after a clause
        # boundary (for example, "; the fitness prerequisite remains unmet")
        # is still detected by the normal matcher.
        if (
            status_token == "unmet"
            and re.search(
                r"\b(?:unknown|unclear|undetermined|not\s+established)\b"
                r"[^.!?;:\n]{0,80}\b(?:rather\s+than|instead\s+of)\s+met\s+or\s*$",
                before_status,
                re.IGNORECASE,
            )
        ):
            continue
        token = match.group(0).strip()
        if token and token.casefold() not in {item.casefold() for item in findings}:
            findings.append(token)
    return findings


def _unsupported_prerequisite_status_matches(
    pattern: re.Pattern[str], generated_text: str, source_text: str
) -> list[str]:
    """Return generated unmet-prerequisite claims not explicitly present in the source."""
    source_matches = {
        item.casefold()
        for item in _unqualified_prerequisite_status_matches(pattern, source_text)
    }
    return [
        item
        for item in _unqualified_prerequisite_status_matches(pattern, generated_text)
        if item.casefold() not in source_matches
    ]


def audit_unverified_case_claims(case: SyntheticCase, generated_payload: dict[str, Any]) -> list[str]:
    """Flag generated assertions that lack a corresponding structured source field."""
    text = " ".join(_flatten_strings(generated_payload))
    flags: list[str] = _source_laterality_integrity_warnings(case.case_summary)
    source_text = case.case_summary.casefold()

    def field_state(field_id: str) -> str | None:
        return case.clinical_field_states.get(field_id)

    def field_assertable(field_id: str) -> bool:
        return field_state(field_id) in (None, "PRESENT")

    def field_provenance_text(field_id: str) -> str:
        return "\n".join(
            source.source_excerpt
            for source in case.clinical_field_provenance.get(field_id, [])
        )

    def list_field_source(field_id: str, values: list[str]) -> str:
        state = field_state(field_id)
        if state == "CONFIRMED_ABSENT":
            return field_provenance_text(field_id)
        if state in (None, "PRESENT"):
            return "\n".join([case.case_summary, *values])
        return ""

    # Compare generated stage components with the exact structured value when
    # present; otherwise compare with the verbatim case summary. A supplied
    # structured stage must not silently legitimise a contradictory generated
    # value merely because another field is populated.
    for component, field, label in (
        ("T", "clinical_t_stage", "clinical_t_stage"),
        ("N", "clinical_n_stage", "clinical_n_stage"),
        ("M", "clinical_m_stage", "clinical_m_stage"),
    ):
        structured_value = getattr(case, field)
        explicit_state = case.clinical_field_states.get(field)
        if explicit_state == "CONFLICTING":
            supported_values = set()
        elif structured_value not in (None, "") and explicit_state in (None, "PRESENT"):
            try:
                canonical_structured = normalize_clinical_tnm_component(field, str(structured_value))
                supported_values = _tnm_component_values(canonical_structured, component)
            except ValueError:
                supported_values = set()
        elif explicit_state is not None:
            supported_values = set()
        else:
            supported_values = _tnm_component_values(case.case_summary, component)
        generated_values = _tnm_component_values(text, component)
        unsupported_values = sorted(generated_values - supported_values)
        if unsupported_values:
            if structured_value not in (None, ""):
                flags.append(
                    f"Generated narrative contains {component}-stage value(s) "
                    + ", ".join(unsupported_values[:4])
                    + f", which conflict with structured {label}={structured_value!s}."
                )
            else:
                flags.append(
                    f"Generated narrative contains {component}-stage value(s) "
                    + ", ".join(unsupported_values[:4])
                    + f", but {label} is not supplied and those values are not explicitly recorded in the verbatim case summary."
                )

    # Pathological stage assertions are audited separately. A p/yp source
    # can never legitimize a clinical T/N/M assertion, and a clinical source
    # can never legitimize a pathological assertion.
    for component, field in (
        ("T", PATHOLOGICAL_T_STAGE),
        ("N", PATHOLOGICAL_N_STAGE),
        ("M", PATHOLOGICAL_M_STAGE),
    ):
        structured_value = getattr(case, field)
        explicit_state = case.clinical_field_states.get(field)
        if explicit_state == "CONFLICTING":
            supported_values = set()
        elif structured_value not in (None, "") and explicit_state in (None, "PRESENT"):
            try:
                canonical_structured = normalize_pathological_tnm_component(field, str(structured_value))
                supported_values = _tnm_component_values(
                    canonical_structured, component, allowed_prefixes=("P", "YP")
                )
            except ValueError:
                supported_values = set()
        elif explicit_state is not None:
            supported_values = set()
        else:
            supported_values = _tnm_component_values(
                case.case_summary, component, allowed_prefixes=("P", "YP")
            )
        generated_values = _tnm_component_values(
            text, component, allowed_prefixes=("P", "YP")
        )
        unsupported_values = sorted(generated_values - supported_values)
        if unsupported_values:
            flags.append(
                f"Generated narrative contains unsupported pathological {component}-stage value(s) "
                + ", ".join(unsupported_values[:4])
                + f"; {field} is absent or does not support those exact pathological values."
            )

    # Explicit age assertions are compared with structured age when present,
    # otherwise with the exact age stated in the verbatim source summary.
    age_pattern = re.compile(
        r"\b(?:(\d{1,3})[ \t\r\n]?[ -]?(?:year|yr)s?[ -]old|"
        r"aged[ \t\r\n](\d{1,3})|age[ \t\r\n]?[:=][ \t\r\n]?(\d{1,3})|"
        r"(\d{1,3})[ \t\r\n]y/o)\b",
        re.IGNORECASE,
    )

    def age_numbers(value: str) -> set[int]:
        return {
            int(number)
            for snippet in _unqualified_matches(age_pattern, value)
            for groups in age_pattern.findall(snippet)
            for number in groups
            if number
        }

    age_state = field_state("age_years")
    supported_ages = (
        {case.age_years}
        if case.age_years is not None and field_assertable("age_years")
        else age_numbers(case.case_summary) if age_state is None
        else set()
    )
    unsupported_ages = sorted(age_numbers(text) - supported_ages)
    if unsupported_ages:
        if case.age_years is not None and field_assertable("age_years"):
            reason = f"which conflict with structured age_years={case.age_years}."
        elif age_state == "CONFLICTING":
            reason = "but age_years has conflicting source values; no single age may be selected."
        else:
            reason = "but age_years is not supplied as an assertable value or explicitly recorded in the source summary."
        flags.append(
            "Generated narrative assigns an age ("
            + ", ".join(str(age) for age in unsupported_ages[:4])
            + "), "
            + reason
        )

    # Stage groups are audited by declared type. Pathological staging cannot
    # support a clinical stage-group assertion, or vice versa. An untyped legacy
    # stage_group supports only an untyped generated/source statement.
    source_group_records = _stage_group_records(case.case_summary)
    generated_group_records = _stage_group_records(text)
    stage_sources = {
        "UNSPECIFIED": (
            case.stage_group
            if case.clinical_field_states.get("stage_group") in (None, "PRESENT")
            else None
        ),
        "CLINICAL": (
            case.clinical_stage_group
            if case.clinical_field_states.get("clinical_stage_group") in (None, "PRESENT")
            else None
        ),
        "PATHOLOGICAL": (
            case.pathological_stage_group
            if case.clinical_field_states.get("pathological_stage_group") in (None, "PRESENT")
            else None
        ),
    }
    structured_group_keys = {
        kind: _stage_group_values(str(value)) if value not in (None, "") else set()
        for kind, value in stage_sources.items()
    }
    summary_group_keys = {
        kind: {key for record_kind, key, _snippet in source_group_records if record_kind == kind}
        for kind in ("UNSPECIFIED", "CLINICAL", "PATHOLOGICAL")
    }
    unsupported_stage_groups: list[str] = []
    for generated_kind, generated_key, snippet in generated_group_records:
        supported = (
            structured_group_keys[generated_kind]
            | summary_group_keys[generated_kind]
        )
        if not any(_stage_group_supported(generated_key, {source_key}) for source_key in supported):
            unsupported_stage_groups.append(snippet)
    if unsupported_stage_groups:
        flags.append(
            "Generated narrative assigns a stage group ("
            + ", ".join(unsupported_stage_groups[:4])
            + "); this is an unsupported or type-conflicting stage group assertion and may conflict with structured stage_group. "
            + "Clinical, pathological and untyped stage groups must be explicitly sourced separately."
        )
    sex_pattern = re.compile(r"\b(?:male|female|man|woman|boy|girl)\b", re.IGNORECASE)
    generated_sex_terms = _unqualified_matches(sex_pattern, text)

    def sex_category(value: str) -> str | None:
        normalised = value.casefold()
        if re.search(r"\b(?:male|man|boy)\b", normalised):
            return "male"
        if re.search(r"\b(?:female|woman|girl)\b", normalised):
            return "female"
        return None

    sex_state = field_state("sex_at_birth")
    if case.sex_at_birth not in (None, "") and field_assertable("sex_at_birth"):
        expected_sex = sex_category(str(case.sex_at_birth))
        source_sexes = {expected_sex} if expected_sex else set()
    elif sex_state is None:
        source_sexes = {
            category
            for category in (
                sex_category(term)
                for term in _unqualified_matches(sex_pattern, case.case_summary)
            )
            if category
        }
    else:
        source_sexes = set()
    unsupported_sex_terms = [
        term for term in generated_sex_terms
        if sex_category(term) not in source_sexes
    ]
    if unsupported_sex_terms:
        if sex_state == "CONFLICTING":
            reason = "sex_at_birth has conflicting source values and no single descriptor may be selected."
        elif case.sex_at_birth not in (None, "") and field_assertable("sex_at_birth"):
            reason = f"the descriptor conflicts with structured sex_at_birth={case.sex_at_birth!s}."
        else:
            reason = "the descriptor is not supported by an assertable structured field or verbatim case summary."
        flags.append(
            "Generated narrative assigns sex/gender descriptor(s) ("
            + ", ".join(unsupported_sex_terms[:4])
            + "), but "
            + reason
        )

    comorbidity_absence_pattern = re.compile(
        r"\b(?:no known comorbidities|no comorbidities|no relevant medical history|otherwise healthy)\b",
        re.IGNORECASE,
    )
    comorbidity_source = list_field_source("relevant_comorbidities", case.relevant_comorbidities or [])
    unsupported_comorbidity_absence = _unsupported_matches(
        comorbidity_absence_pattern, text, comorbidity_source
    )
    if unsupported_comorbidity_absence:
        flags.append(
            "Generated narrative treats comorbidities as absent or denies relevant medical history "
            "(" + ", ".join(unsupported_comorbidity_absence[:3])
            + "), but that absence is not explicitly supported by the supplied case."
        )

    prior_treatment_absence_pattern = re.compile(
        r"\b(?:no prior treatment|treatment[- ]na[iï]ve|never treated)\b",
        re.IGNORECASE,
    )
    prior_treatment_source = list_field_source("prior_treatment", case.prior_treatment or [])
    unsupported_prior_treatment_absence = _unsupported_matches(
        prior_treatment_absence_pattern, text, prior_treatment_source
    )
    if unsupported_prior_treatment_absence:
        flags.append(
            "Generated narrative treats prior treatment as absent ("
            + ", ".join(unsupported_prior_treatment_absence[:3])
            + "), but that absence is not explicitly supported by the supplied case."
        )

    # High-specificity assertion checks. Questions and qualified uncertainty are not
    # treated as findings. Exact matching source snippets remain attributed to the
    # user-provided case summary rather than being relabelled as model inventions.
    performance_pattern = re.compile(
        r"\b(?:ECOG(?:[ \t\r\n]?[- ]?PS|[ \t\r\n]performance[ \t\r\n]status)?|"
        r"WHO(?:[ \t\r\n]performance)?[ \t\r\n]status)[ \t\r\n]?[:=]?[ \t\r\n]?[0-4]\b|"
        r"\b(?:KPS|Karnofsky(?:[ \t\r\n]Performance[ \t\r\n]Status)?)[ \t\r\n]?[:=]?[ \t\r\n]?\d{2,3}\b",
        re.IGNORECASE,
    )
    ps_state = field_state("performance_status")
    scale_state = field_state("performance_status_scale")
    scale_is_assertable = (
        case.performance_status_scale not in (None, "")
        and scale_state in (None, "PRESENT")
    )
    if case.performance_status not in (None, "") and field_assertable("performance_status") and scale_is_assertable:
        performance_source = f"{case.performance_status_scale} {case.performance_status}"
    elif ps_state is None and scale_state is None:
        performance_source = case.case_summary
    else:
        performance_source = ""
    unsupported_performance = _unsupported_matches(
        performance_pattern, text, performance_source
    )
    if unsupported_performance:
        if ps_state == "CONFLICTING" or scale_state == "CONFLICTING":
            reason = "the performance-status value or scale has conflicting source values."
        elif case.performance_status not in (None, "") and field_assertable("performance_status") and not scale_is_assertable:
            reason = "the performance-status scale is absent or not assertable."
        elif case.performance_status not in (None, "") and field_assertable("performance_status"):
            reason = f"the score conflicts with structured performance_status={case.performance_status!s}."
        else:
            reason = "performance_status and its scale are not supplied as assertable structured values or explicitly recorded in the source summary."
        flags.append(
            "Generated narrative assigns unsupported performance-status score(s) ("
            + ", ".join(unsupported_performance[:3])
            + "); "
            + reason
        )

    node_negative_pattern = re.compile(
        r"\b(?:node[- ]negative|no (?:regional )?nodal (?:disease|involvement)|negative (?:regional )?nodes?)\b",
        re.IGNORECASE,
    )
    generated_node_negative = _unqualified_matches(node_negative_pattern, text)
    n_state = case.clinical_field_states.get("clinical_n_stage")
    supported_n_source = (
        str(case.clinical_n_stage)
        if case.clinical_n_stage not in (None, "") and n_state in (None, "PRESENT")
        else case.case_summary if n_state is None else ""
    )
    source_n_values = _tnm_component_values(supported_n_source, "N")
    source_explicitly_node_negative = bool(
        _unqualified_matches(node_negative_pattern, supported_n_source)
    )
    supported_negative_n = (
        "N0" in source_n_values
        or (not source_n_values and source_explicitly_node_negative)
    )
    if generated_node_negative and not supported_negative_n:
        flags.append(
            "Generated narrative asserts node-negative status ("
            + ", ".join(generated_node_negative[:3])
            + "), but the supplied structured/source data do not establish N0 or an equivalent explicit negative nodal finding."
        )

    no_metastases_pattern = re.compile(
        r"\b(?:no (?:evidence of )?(?:distant )?metastases?|no (?:evidence of )?(?:distant )?metastatic disease|without (?:distant )?metastases?|metastasis[- ]free|(?:distant )?metastases? (?:are|is) absent)\b",
        re.IGNORECASE,
    )
    generated_no_metastases = _unqualified_matches(no_metastases_pattern, text)
    m_state = case.clinical_field_states.get("clinical_m_stage")
    supported_m_source = (
        str(case.clinical_m_stage)
        if case.clinical_m_stage not in (None, "") and m_state in (None, "PRESENT")
        else case.case_summary if m_state is None else ""
    )
    source_m_values = _tnm_component_values(supported_m_source, "M")
    source_explicitly_no_metastases = bool(
        _unqualified_matches(no_metastases_pattern, supported_m_source)
    )
    supported_negative_m = (
        "M0" in source_m_values
        or (not source_m_values and source_explicitly_no_metastases)
    )
    if generated_no_metastases and not supported_negative_m:
        flags.append(
            "Generated narrative asserts absence of metastatic disease ("
            + ", ".join(generated_no_metastases[:3])
            + "), but the supplied structured/source data do not establish M0 or an equivalent explicit negative metastatic finding."
        )

    resectability_pattern = re.compile(
        r"\b(?:is|was|remains|appears|seems|deemed|considered)\s+(?:clearly |technically |borderline )?(?:resectable|unresectable|operable|inoperable)\b|\b(?:resectable|unresectable|operable|inoperable)\s+(?:tumou?r|disease|lesion|cancer)\b|\bnot (?:resectable|operable)\b",
        re.IGNORECASE,
    )
    matches = _unsupported_matches(resectability_pattern, text, source_text)
    if matches:
        flags.append("Generated narrative asserts resectability status (" + ", ".join(matches[:3]) + "), which is not explicitly documented in the supplied case.")

    histology_pattern = re.compile(
        r"\b(?:squamous cell carcinoma|squamous carcinoma|adenocarcinoma|small[- ]cell(?: lung)? carcinoma|large[- ]cell(?: lung)? carcinoma|urothelial carcinoma|neuroendocrine carcinoma|lymphoma|melanoma|sarcoma|NSCLC|SCLC|SCC)\b",
        re.IGNORECASE,
    )

    def histology_key(value: str) -> str:
        normalised = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
        if normalised in {"scc", "squamous carcinoma", "squamous cell carcinoma"}:
            return "squamous_cell_carcinoma"
        if normalised in {"nsclc", "non small cell carcinoma", "non small cell lung carcinoma"}:
            return "non_small_cell_carcinoma"
        if normalised in {"sclc", "small cell carcinoma", "small cell lung carcinoma"}:
            return "small_cell_carcinoma"
        return normalised

    histology_state = field_state("histology")
    pathology_summary_state = field_state("pathology_summary")
    if histology_state == "CONFLICTING" or pathology_summary_state == "CONFLICTING":
        histology_source = ""
    elif case.histology not in (None, "") and field_assertable("histology"):
        histology_source = str(case.histology)
    elif histology_state is None and case.pathology_summary not in (None, "") and field_assertable("pathology_summary"):
        histology_source = str(case.pathology_summary)
    elif histology_state is None and pathology_summary_state is None:
        histology_source = case.case_summary
    else:
        histology_source = ""
    source_histologies = {
        histology_key(item)
        for item in _unqualified_matches(histology_pattern, histology_source)
    }
    generated_histologies = _unqualified_matches(histology_pattern, text)
    unsupported_histologies = [
        item for item in generated_histologies
        if histology_key(item) not in source_histologies
    ]
    if unsupported_histologies:
        flags.append(
            "Generated narrative asserts histological diagnosis(es) ("
            + ", ".join(unsupported_histologies[:3])
            + "), which are not supported by the available structured histology/pathology field or verbatim case summary."
        )

    pathology_pattern = re.compile(
        r"\b(?:p16|HPV|HER2|ER|PR|PD-L1|Ki-67)\s*(?:positive|negative|high|low|[+-])\b|\b(?:grade|G)\s*[1-4]\b|\b(?:lymphovascular|perineural) invasion\b|\b(?:positive|negative) margins?\b",
        re.IGNORECASE,
    )
    pathology_summary_state = field_state("pathology_summary")
    pathology_source = "\n".join(
        item
        for item in (
            case.pathology_summary if pathology_summary_state in (None, "PRESENT") else "",
            case.case_summary if pathology_summary_state is None else "",
        )
        if item
    )
    unsupported_pathology = _unsupported_matches(
        pathology_pattern, text, pathology_source
    )
    if unsupported_pathology:
        flags.append(
            "Generated narrative asserts pathology/biomarker finding(s) ("
            + ", ".join(unsupported_pathology[:3])
            + "), which are not explicitly supported by the structured pathology summary or verbatim case summary."
        )

    investigation_pattern = re.compile(
        r"\b(?:CT|MRI|PET(?:[- ]CT)?|ultrasound|USG|X[- ]ray|radiograph|bone scan|colonoscopy|endoscopy|bronchoscopy|cystoscopy|biopsy)\s+(?:scan\s+)?(?:shows?|demonstrates?|reveals?|confirms?|identifies?|detected|reported)\s+[^.!?;\n]{1,100}",
        re.IGNORECASE,
    )
    imaging_state = field_state("imaging_summary")
    investigations_state = field_state("relevant_investigations")
    records_state = field_state("investigation_records")
    investigation_parts: list[str] = []
    if imaging_state in (None, "PRESENT") and case.imaging_summary:
        investigation_parts.append(case.imaging_summary)
    if investigations_state in (None, "PRESENT"):
        investigation_parts.extend(case.relevant_investigations)
    if records_state in (None, "PRESENT"):
        investigation_parts.extend(
            " ".join(
                part for part in (
                    record.investigation_name,
                    record.result_summary or "",
                    record.source_excerpt or "",
                ) if part
            )
            for record in case.investigation_records
        )
    if imaging_state is None and investigations_state is None and records_state is None:
        investigation_parts.append(case.case_summary)
    investigation_source = "\n".join(investigation_parts)
    unsupported_investigations = _unsupported_matches(
        investigation_pattern, text, investigation_source
    )
    # A biopsy paraphrase such as "confirms adenocarcinoma" is supported when
    # the verbatim case summary explicitly reports that same histology on biopsy.
    # This does not validate any additional biomarker, grade, margin, or stage claim;
    # those are checked independently by the pathology and TNM audits below/above.
    source_biopsy_statements = re.findall(
        r"\bbiopsy\b[^.!?;\n]{1,140}", case.case_summary, re.IGNORECASE
    )
    source_biopsy_histologies = {
        histology_key(item)
        for statement in source_biopsy_statements
        for item in _unqualified_matches(histology_pattern, statement)
    }
    def biopsy_result_is_supported(statement: str) -> bool:
        if not re.match(r"\bbiopsy\b", statement, re.IGNORECASE):
            return False
        generated_biopsy_histologies = {
            histology_key(item)
            for item in _unqualified_matches(histology_pattern, statement)
        }
        return bool(
            generated_biopsy_histologies
            and generated_biopsy_histologies.issubset(source_biopsy_histologies)
        )
    unsupported_investigations = [
        item for item in unsupported_investigations
        if not biopsy_result_is_supported(item)
    ]
    if unsupported_investigations:
        flags.append(
            "Generated narrative asserts imaging/investigation result(s) ("
            + "; ".join(unsupported_investigations[:2])
            + "), which are not explicitly supported by the supplied imaging summary, relevant investigations, or verbatim case summary."
        )

    # Missing information alone does not establish that a treatment is unsafe,
    # contraindicated, or not indicated. Flag categorical clinical status claims;
    # conditional risk language (e.g. "may be unsafe") remains an interpretation.
    treatment_status_pattern = re.compile(
        r"\b(?:"
        r"(?:is|are|was|were|has been|remains)\s+(?:clearly\s+)?(?:contraindicated|unsafe|not indicated)"
        r"|neither\b(?![^.!?;:\n]{0,120}\b(?:claims?|states?|says?|said|reports?|reported|asserts?|asserted|suggests?|suggested|recommends?|recommended|argues?|argued|believes?|believed)\b)[^.!?;:\n]{0,120}\b(?:is|are|was|were|has been|remains)\s+(?:clearly\s+)?(?:indicated|recommended|appropriate|suitable)"
        r"|no\s+(?:(?:available|proposed|treatment|therapeutic)\s+)*(?:option|approach|pathway|therapy|modality|sequence)s?\s+(?:is|are|was|were|has been|remains)\s+(?:clearly\s+)?(?:indicated|recommended|appropriate|suitable)"
        r")\b",
        re.IGNORECASE,
    )
    attributed_status_report_pattern = re.compile(
        r"\b(?:neither|no)\s+(?:(?:selected|supplied|participating|other)\s+)?"
        r"(?:peer|source|note|role|agent|specialist|clinician|contribution|assessment|record|report)s?\b"
        r"[^.!?;:\n]{0,100}\b(?:claims?|states?|says?|said|reports?|reported|asserts?|asserted|"
        r"suggests?|suggested|recommends?|recommended|argues?|argued|believes?|believed)\b"
        r"|\b(?:nor|and\s+nor)\s+(?:do|does|did)\s+any\s+(?:claim|state|say|report|assert|suggest|recommend|argue|believe)\b",
        re.IGNORECASE,
    )
    treatment_status_matches = _unsupported_matches(
        treatment_status_pattern,
        text,
        source_text,
        ignore_generated_prefix_pattern=attributed_status_report_pattern,
    )
    if treatment_status_matches:
        flags.append(
            "Generated narrative makes a definitive treatment safety/indication assertion ("
            + "; ".join(treatment_status_matches[:3])
            + "); missing information alone does not establish contraindication, safety, or indication."
        )

    treatment_suitability_pattern = re.compile(
        r"\b(?:is|are|was|were|remains|appears|seems|deemed|considered)\s+(?:a\s+)?(?:suitable|appropriate|eligible|fit|unfit)\s+candidate\s+for\b[^.!?;\n]{0,100}|"
        r"\b(?:is|are|was|were|remains|appears|seems|deemed|considered)\s+(?:medically\s+)?(?:suitable|appropriate|eligible|fit|unfit|operable|inoperable)\s+for\b[^.!?;\n]{0,100}|"
        r"\b(?:can|cannot|could|could\s+not|is\s+able\s+to|unable\s+to)\s+tolerate\s+(?:surgery|chemotherapy|radiotherapy|radiation|systemic\s+therapy|treatment)\b[^.!?;\n]{0,80}",
        re.IGNORECASE,
    )
    conditional_suitability_marker = re.compile(
        r"\b(?:may|might|could|possibly|potentially|pending|subject\s+to|"
        r"awaiting|conditional\s+on|until|unless)\b",
        re.IGNORECASE,
    )
    treatment_suitability_matches = [
        item
        for item in _unsupported_matches(
            treatment_suitability_pattern, text, case.case_summary
        )
        if not conditional_suitability_marker.search(item)
    ]
    if treatment_suitability_matches:
        flags.append(
            "Generated narrative makes an unsupported treatment-suitability/eligibility assertion ("
            + "; ".join(treatment_suitability_matches[:3])
            + "); suitability cannot be established without explicit supporting case information."
        )

    preference_pattern = re.compile(
        # Match an actual patient-attributed choice/act. The noun phrase
        # "obtain patient consent" is a recommendation to elicit consent,
        # not evidence that the patient has already consented.
        r"\bpatient(?:'s)?\s+(?:prefers?|wishes?|wants?|chooses?|declines?|refuses?|agrees?|consents\b|has chosen|has consented|does not want|doesn't want)\b[^.!?;\n]{0,100}",
        re.IGNORECASE,
    )
    goals_state = field_state("patient_goals")
    preferences_state = field_state("patient_preferences")
    preference_sources: list[str] = []
    if goals_state in (None, "PRESENT"):
        preference_sources.extend(f"patient {goal}" for goal in (case.patient_goals or []))
    if preferences_state in (None, "PRESENT"):
        preference_sources.extend(f"patient {item}" for item in (case.patient_preferences or []))
    if goals_state is None and preferences_state is None:
        preference_sources.append(case.case_summary)
    preference_source_text = "\n".join(preference_sources)
    unsupported_preferences = _unsupported_matches(
        preference_pattern,
        text,
        preference_source_text,
    )
    if unsupported_preferences:
        flags.append(
            "Generated narrative attributes patient preference/decision statement(s) "
            + "; ".join(unsupported_preferences[:2])
            + ", which are not explicitly supported by the verbatim case summary or structured patient_goals."
        )
    prerequisite_status_pattern = re.compile(
        # Explicit "neither prerequisite is met" is a negative-status assertion,
        # even though it does not contain the literal words "not met" or "unmet".
        r"\bneither\s+(?:(?:of\s+)?(?:the\s+)?(?:two|both|these|those)\s+)?(?:the\s+)?"
        r"(?:clinical\s+)?(?:prerequisite|condition|requirement)s?\b"
        r"[^.!?;:\n]{0,80}\b(?:is|are|was|were|has\s+been|have\s+been)\s+met\b|"
        r"\b(?:unmet|unfulfilled)\s+(?:clinical\s+)?(?:prerequisite|condition|requirement)s?\b|"
        r"\b(?:clinical\s+)?(?:prerequisite|condition|requirement)s?\b"
        r"[^.!?;\n]{0,100}\b(?:remain(?:s)?|are|is|were|was|have(?:\s+been)?|has(?:\s+been)?)?\s*"
        r"(?:unmet|unfulfilled|not\s+(?:been\s+)?(?:met|fulfilled)|failed|negative(?!\s+(?:[\w-]+\s+){0,2}findings\b))\b|"
        r"\b(?:conditionality|conditional\s+(?:status|position|option))\b"
        r"[^.!?;\n]{0,100}\b(?:remain(?:s)?|are|is|were|was|have(?:\s+been)?|has(?:\s+been)?)?\s*"
        r"(?:unmet|unfulfilled|not\s+(?:been\s+)?(?:met|fulfilled)|failed)\b",
        re.IGNORECASE,
    )
    unsupported_prerequisite_status = _unsupported_prerequisite_status_matches(
        prerequisite_status_pattern, text, source_text
    )
    if unsupported_prerequisite_status:
        flags.insert(
            0,
            "Generated narrative describes prerequisite(s) as unmet/not met without a matching "
            "documented assessment finding in the supplied case ("
            + "; ".join(unsupported_prerequisite_status[:3])
            + "). Missing or undocumented prerequisites must remain unknown; review before Chair synthesis."
        )

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
    empty_fields = [field for field in ("current_medications", "known_allergies", "relevant_investigations", "relevant_comorbidities", "prior_treatment", "patient_goals", "social_context", "resource_context", "known_unknowns") if not getattr(case, field)]
    if empty_fields:
        warnings.append("Empty structured lists are not confirmed negatives; these fields are not reported: " + ", ".join(empty_fields) + ". Review the raw case summary before interpreting them.")
    summary = case.case_summary.casefold()
    warnings.extend(_source_laterality_integrity_warnings(case.case_summary))

    # Explicit contradictions are warnings for human reconciliation; neither
    # the structured field nor free text is silently preferred.
    age_pattern = re.compile(
        r"\b(?:(\d{1,3})[ \t\r\n]?[ -]?(?:year|yr)s?[ -]old|"
        r"aged[ \t\r\n](\d{1,3})|age[ \t\r\n]?[:=][ \t\r\n]?(\d{1,3})|"
        r"(\d{1,3})[ \t\r\n]y/o)\b",
        re.IGNORECASE,
    )
    text_ages = {
        int(value)
        for match in age_pattern.findall(_collapse_horizontal_whitespace(summary))
        for value in match
        if value
    }
    if case.age_years is not None and text_ages and text_ages != {case.age_years}:
        warnings.append(
            f"Structured age_years is {case.age_years}, but free text explicitly states age(s) "
            + ", ".join(str(value) for value in sorted(text_ages))
            + "; preserve both and reconcile before simulation."
        )

    if case.sex_at_birth:
        structured_sex = case.sex_at_birth.casefold()
        text_male = bool(re.search(r"\b(?:male|man|boy)\b", summary))
        text_female = bool(re.search(r"\b(?:female|woman|girl)\b", summary))
        if (("male" in structured_sex and "female" not in structured_sex and text_female)
                or ("female" in structured_sex and text_male)):
            warnings.append(
                "Structured sex_at_birth conflicts with an explicit sex descriptor in free text; preserve both and reconcile before simulation."
            )

    if case.stage_group:
        stage_group_pattern = re.compile(
            r"\b(?:clinical[ \t\r\n])?stage[ \t\r\n]?(?:group[ \t\r\n]?)?(IV|III|II|I|[1-4])([ABC])?\b",
            re.IGNORECASE,
        )
        roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4}
        def stage_group_key(value: str) -> str:
            match = stage_group_pattern.search(value)
            if not match:
                return value.strip().casefold()
            numeral = match.group(1).upper()
            suffix = (match.group(2) or "").upper()
            number = roman_values.get(numeral, int(numeral) if numeral.isdigit() else None)
            return f"{number}{suffix}" if number is not None else value.strip().casefold()

        text_stage_groups = {
            stage_group_key(match.group(0))
            for match in stage_group_pattern.finditer(_collapse_horizontal_whitespace(summary))
        }
        structured_group = stage_group_key(case.stage_group)

        def stage_groups_compatible(first: str, second: str) -> bool:
            if first[:1] != second[:1]:
                return False
            first_suffix, second_suffix = first[1:], second[1:]
            return not first_suffix or not second_suffix or first_suffix == second_suffix

        if text_stage_groups and not any(
            stage_groups_compatible(structured_group, text_group)
            for text_group in text_stage_groups
        ):
            warnings.append(
                "Structured stage_group conflicts with an explicit stage-group statement in free text; preserve both and reconcile before simulation."
            )

    for field, label, pattern in (
        ("clinical_t_stage", "T stage", re.compile(r"\b(?:c|p|yc|yp)?(T(?:is|x|0|[1-4][a-d]?))(?=(?:N(?:x|0|[1-3]))?(?:M(?:x|0|1))?\b)", re.IGNORECASE)),
        ("clinical_n_stage", "N stage", re.compile(r"\b(?:c|p|yc|yp)?(N(?:x|0|[1-3]))(?=(?:M(?:x|0|1))?\b)", re.IGNORECASE)),
        ("clinical_m_stage", "M stage", re.compile(r"\b(?:c|p|yc|yp)?(M(?:x|0|1))\b", re.IGNORECASE)),
    ):
        structured_value = getattr(case, field)
        normalize_stage = lambda value: re.sub(
            r"^(?:yc|yp|c|p)", "", value.casefold().replace(" ", "")
        )
        text_values = {
            normalize_stage(match.group(1))
            for match in pattern.finditer(summary)
        }
        # In a contiguous cT3N1M0 token, N and M are not preceded by word
        # boundaries. Capture those components from the complete TNM expression.
        if field in {"clinical_n_stage", "clinical_m_stage"}:
            combined_tnm = re.compile(
                r"\b(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)"
                r"(N(?:x|0|[1-3]))?(M(?:x|0|1))?\b",
                re.IGNORECASE,
            )
            component_index = 1 if field == "clinical_n_stage" else 2
            text_values.update(
                normalize_stage(match.group(component_index))
                for match in combined_tnm.finditer(summary)
                if match.group(component_index)
            )
        if (
            structured_value
            and text_values
            and normalize_stage(structured_value) not in text_values
        ):
            warnings.append(
                f"Structured {label} conflicts with an explicit {label} statement in free text; preserve both and reconcile before simulation."
            )
    if not case.relevant_comorbidities:
        if re.search(r"\b(dm|diabetes|diabetic)\b", summary):
            warnings.append("The free-text summary mentions diabetes/DM, but relevant_comorbidities is empty; reconcile the fields before simulation.")
        if re.search(r"\b(shtn|htn|hypertension)\b", summary):
            warnings.append("The free-text summary mentions hypertension/HTN, but relevant_comorbidities is empty; reconcile the fields before simulation.")
    if re.search(r"\b(smoker|smoking|tobacco)\b", summary):
        warnings.append("Smoking is mentioned in free text; keep it identified as a text-reported risk factor unless explicitly structured/confirmed.")
    staged_fields = (
        "clinical_t_stage", "clinical_n_stage", "clinical_m_stage",
        "pathological_t_stage", "pathological_n_stage", "pathological_m_stage",
        "stage_group", "clinical_stage_group", "pathological_stage_group",
    )
    if any(getattr(case, field) not in (None, "") for field in staged_fields):
        missing = [label for label, value in (("primary site", case.primary_site), ("staging system", case.staging_system), ("staging edition", case.staging_edition)) if value in (None, "")]
        if missing:
            warnings.append("Staging token is retained but site/system/edition compatibility is not validated because " + ", ".join(missing) + " is not supplied. Do not infer stage or compatibility.")
    if case.performance_status not in (None, "") and case.performance_status_scale in (None, ""):
        warnings.append("Performance-status value is supplied without a named scale; do not infer ECOG/WHO/Karnofsky equivalence.")
    if case.stage_group not in (None, "") and case.clinical_stage_group in (None, "") and case.pathological_stage_group in (None, ""):
        warnings.append("Legacy stage_group is untyped; do not assume it is clinical or pathological staging.")
    for field_id, state in case.clinical_field_states.items():
        if state == "CONFLICTING":
            warnings.append(f"{field_id} has conflicting source values; all candidates are preserved and human/source reconciliation remains outstanding.")
    return warnings