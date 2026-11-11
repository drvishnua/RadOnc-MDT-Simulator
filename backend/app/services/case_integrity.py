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
            "A lesion's size or anatomical subsite alone does not establish a T category or stage group; never convert a 1x1 cm measurement into T1 or infer N0/M0.",
            "Do not infer age, sex, T/N/M stage, stage group, nodal status, metastatic status, performance status, prior treatment, patient goals or comorbidity negatives.",
            "Separate source facts, clinical interpretations, hypotheses/assumptions and unknowns.",
            "If free text and structured fields differ, explicitly flag the discrepancy; do not silently reconcile it.",
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
        non_narrative = {"case_data_integrity_flags", "source_reference_integrity_flags"}
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


def _unqualified_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    """Return assertion-like matches, applying qualifiers only within the same clause."""
    findings: list[str] = []
    for match in pattern.finditer(text):
        # Preserve the whole-sentence question safeguard even when the clause
        # itself ends at a comma or contrast marker before the question mark.
        sentence_end = min(
            (
                position
                for mark in ".!?;:\n"
                if (position := text.find(mark, match.end())) >= 0
            ),
            default=len(text),
        )
        if sentence_end < len(text) and text[sentence_end] == "?":
            continue

        left = max(
            (boundary.end() for boundary in _CLAUSE_BOUNDARY.finditer(text, 0, match.start())),
            default=0,
        )
        right = min(
            (boundary.start() for boundary in _CLAUSE_BOUNDARY.finditer(text, match.end())),
            default=len(text),
        )
        clause = text[left:right]
        if _QUALIFIER.search(clause):
            continue
        token = match.group(0).strip()
        if token and token.casefold() not in {item.casefold() for item in findings}:
            findings.append(token)
    return findings


def _unsupported_matches(pattern: re.Pattern[str], generated_text: str, source_text: str) -> list[str]:
    """Keep exact assertion snippets not already present in the supplied case text."""
    source_matches = {item.casefold() for item in _unqualified_matches(pattern, source_text)}
    return [
        item for item in _unqualified_matches(pattern, generated_text)
        if item.casefold() not in source_matches
    ]


_TNM_EXPRESSION_PATTERN = re.compile(
    r"\b(?:c|p|yc|yp)?T(?:is|x|0|[1-4][a-d]?)(?:N(?:x|0|[1-3]))?(?:M(?:x|0|1))?\b"
    r"|\b(?:c|p|yc|yp)?N(?:x|0|[1-3])\b"
    r"|\b(?:c|p|yc|yp)?M(?:x|0|1)\b",
    re.IGNORECASE,
)


def _tnm_component_values(value: str, component: str) -> set[str]:
    """Extract explicit unqualified T/N/M component values from standalone or combined TNM."""
    values: set[str] = set()
    for snippet in _unqualified_matches(_TNM_EXPRESSION_PATTERN, value):
        if component == "T":
            match = re.search(r"(?:c|p|yc|yp)?(T(?:is|x|0|[1-4][a-d]?))", snippet, re.IGNORECASE)
        elif component == "N":
            match = re.search(r"N(?:x|0|[1-3])", snippet, re.IGNORECASE)
        elif component == "M":
            match = re.search(r"M(?:x|0|1)", snippet, re.IGNORECASE)
        else:
            raise ValueError(f"Unsupported TNM component: {component}")
        if match:
            values.add(match.group(0).upper().removeprefix("YC").removeprefix("YP").removeprefix("C").removeprefix("P"))
    return values


def _stage_group_values(value: str) -> set[str]:
    """Normalise explicit stage-group labels while retaining substage distinctions."""
    pattern = re.compile(
        r"\b(?:clinical\s+)?stage\s*(?:group\s*)?(IV|III|II|I|[1-4])([ABC])?\b",
        re.IGNORECASE,
    )
    roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4}
    keys: set[str] = set()
    for snippet in _unqualified_matches(pattern, value):
        match = pattern.search(snippet)
        if not match:
            continue
        numeral = match.group(1).upper()
        suffix = (match.group(2) or "").upper()
        number = roman_values.get(numeral, int(numeral) if numeral.isdigit() else None)
        if number is not None:
            keys.add(f"{number}{suffix}")
    return keys


def _stage_group_supported(generated_key: str, source_keys: set[str]) -> bool:
    """A documented substage supports its parent stage; a parent does not imply a substage."""
    return any(
        source_key == generated_key
        or (generated_key.isdigit() and source_key.startswith(generated_key))
        for source_key in source_keys
    )


def audit_unverified_case_claims(case: SyntheticCase, generated_payload: dict[str, Any]) -> list[str]:
    """Flag generated assertions that lack a corresponding structured source field."""
    text = " ".join(_flatten_strings(generated_payload))
    flags: list[str] = []
    source_text = case.case_summary.casefold()

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
        supported_values = (
            _tnm_component_values(str(structured_value), component)
            if structured_value not in (None, "")
            else _tnm_component_values(case.case_summary, component)
        )
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

    # Explicit age assertions are compared with structured age when present,
    # otherwise with the exact age stated in the verbatim source summary.
    age_pattern = re.compile(
        r"\b(?:(\d{1,3})\s*[- ]?(?:year|yr)s?[- ]old|"
        r"aged\s+(\d{1,3})|age\s*[:=]\s*(\d{1,3})|"
        r"(\d{1,3})\s*y/o)\b",
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

    supported_ages = (
        {case.age_years}
        if case.age_years is not None
        else age_numbers(case.case_summary)
    )
    unsupported_ages = sorted(age_numbers(text) - supported_ages)
    if unsupported_ages:
        if case.age_years is not None:
            flags.append(
                "Generated narrative assigns age(s) "
                + ", ".join(str(age) for age in unsupported_ages[:4])
                + f", which conflict with structured age_years={case.age_years}."
            )
        else:
            flags.append(
                "Generated narrative assigns an age ("
                + ", ".join(str(age) for age in unsupported_ages[:4])
                + "), but age_years is not supplied in the structured case or explicitly recorded in the source summary."
            )

    # Stage group is checked against structured input when present, otherwise
    # against the source summary. A parent stage is not inferred from a substage's
    # absence, and a substage is never inferred from a parent stage.
    structured_group = case.stage_group
    supported_group_keys = (
        _stage_group_values(str(structured_group))
        if structured_group not in (None, "")
        else _stage_group_values(case.case_summary)
    )
    generated_group_snippets = _unqualified_matches(
        re.compile(r"\b(?:clinical\s+)?stage\s*(?:group\s*)?(IV|III|II|I|[1-4])([ABC])?\b", re.IGNORECASE),
        text,
    )
    unsupported_stage_groups = [
        snippet
        for snippet in generated_group_snippets
        if not all(
            _stage_group_supported(key, supported_group_keys)
            for key in _stage_group_values(snippet)
        )
    ]
    if unsupported_stage_groups:
        if structured_group not in (None, ""):
            flags.append(
                "Generated narrative assigns stage group(s) "
                + ", ".join(unsupported_stage_groups[:4])
                + f", which conflict with structured stage_group={structured_group!s}."
            )
        else:
            flags.append(
                "Generated narrative assigns a stage group ("
                + ", ".join(unsupported_stage_groups[:4])
                + "), but stage_group is not supplied in the structured case or explicitly recorded in the source summary."
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

    if case.sex_at_birth not in (None, ""):
        expected_sex = sex_category(str(case.sex_at_birth))
        unsupported_sex_terms = [
            term for term in generated_sex_terms
            if sex_category(term) != expected_sex
        ]
        if unsupported_sex_terms:
            flags.append(
                "Generated narrative assigns sex/gender descriptor(s) "
                + ", ".join(unsupported_sex_terms[:4])
                + f", which conflict with structured sex_at_birth={case.sex_at_birth!s}."
            )
    else:
        source_sexes = {
            category
            for category in (sex_category(term) for term in _unqualified_matches(sex_pattern, case.case_summary))
            if category
        }
        unsupported_sex_terms = [
            term for term in generated_sex_terms
            if sex_category(term) not in source_sexes
        ]
        if unsupported_sex_terms:
            flags.append(
                "Generated narrative assigns sex/gender descriptor(s) ("
                + ", ".join(unsupported_sex_terms[:4])
                + "), but they are not supported by the structured case or verbatim case summary."
            )

    comorbidity_absence_pattern = re.compile(
        r"\b(?:no known comorbidities|no comorbidities|no relevant medical history|otherwise healthy)\b",
        re.IGNORECASE,
    )
    comorbidity_source = "\n".join([case.case_summary, *(case.relevant_comorbidities or [])])
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
    prior_treatment_source = "\n".join([case.case_summary, *(case.prior_treatment or [])])
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
        r"\b(?:ECOG(?:\s*[- ]?PS|\s+performance\s+status)?|"
        r"WHO(?:\s+performance)?\s+status)\s*[:=]?\s*[0-4]\b|"
        r"\b(?:KPS|Karnofsky(?:\s+Performance\s+Status)?)\s*[:=]?\s*\d{2,3}\b",
        re.IGNORECASE,
    )
    performance_source = (
        str(case.performance_status)
        if case.performance_status not in (None, "")
        else case.case_summary
    )
    unsupported_performance = _unsupported_matches(
        performance_pattern, text, performance_source
    )
    if unsupported_performance:
        if case.performance_status not in (None, ""):
            flags.append(
                "Generated narrative assigns performance-status score(s) ("
                + ", ".join(unsupported_performance[:3])
                + f"), which conflict with structured performance_status={case.performance_status!s}."
            )
        else:
            flags.append(
                "Generated narrative assigns a performance-status score ("
                + ", ".join(unsupported_performance[:3])
                + "), but performance_status is not supplied in the structured case or verbatim case summary."
            )

    node_negative_pattern = re.compile(
        r"\b(?:node[- ]negative|no (?:regional )?nodal (?:disease|involvement)|negative (?:regional )?nodes?)\b",
        re.IGNORECASE,
    )
    generated_node_negative = _unqualified_matches(node_negative_pattern, text)
    supported_n_source = (
        str(case.clinical_n_stage)
        if case.clinical_n_stage not in (None, "")
        else case.case_summary
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
    supported_m_source = (
        str(case.clinical_m_stage)
        if case.clinical_m_stage not in (None, "")
        else case.case_summary
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

    histology_source = (
        str(case.histology)
        if case.histology not in (None, "")
        else str(case.pathology_summary)
        if case.pathology_summary not in (None, "")
        else case.case_summary
    )
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
    pathology_source = "\n".join(
        item for item in (case.pathology_summary or "", case.case_summary) if item
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
    investigation_source = "\n".join(
        item
        for item in (case.imaging_summary or "", *case.relevant_investigations, case.case_summary)
        if item
    )
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
        r"\b(?:is|are|was|were|has been|remains)\s+(?:clearly\s+)?(?:contraindicated|unsafe|not indicated)\b",
        re.IGNORECASE,
    )
    treatment_status_matches = _unsupported_matches(treatment_status_pattern, text, source_text)
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
    preference_source_text = "\n".join(
        [case.case_summary, *(f"patient {goal}" for goal in (case.patient_goals or []))]
    )
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

    # Explicit contradictions are warnings for human reconciliation; neither
    # the structured field nor free text is silently preferred.
    age_pattern = re.compile(
        r"\b(?:(\d{1,3})\s*[- ]?(?:year|yr)s?[- ]old|"
        r"aged\s+(\d{1,3})|age\s*[:=]\s*(\d{1,3})|"
        r"(\d{1,3})\s*y/o)\b",
        re.IGNORECASE,
    )
    text_ages = {
        int(value)
        for match in age_pattern.findall(summary)
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
            r"\b(?:clinical\s+)?stage\s*(?:group\s*)?(IV|III|II|I|[1-4])([ABC])?\b",
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
            for match in stage_group_pattern.finditer(summary)
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
    return warnings