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

    # Explicit age assertions are audited separately from general demographic language.
    # Do not flag an age already stated in the user-provided free-text source.
    if case.age_years is None:
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

        unsupported_ages = sorted(age_numbers(text) - age_numbers(source_text))
        if unsupported_ages:
            flags.append(
                "Generated narrative assigns an age ("
                + ", ".join(str(age) for age in unsupported_ages[:4])
                + "), but age_years is not supplied in the structured case or explicitly recorded in the source summary."
            )

    # A stage group is distinct from T/N/M components. It must not be inferred
    # from an incomplete TNM record or from a site/histology description.
    if case.stage_group in (None, ""):
        stage_group_pattern = re.compile(
            r"\b(?:clinical\s+)?stage\s*(?:group\s*)?(IV|III|II|I|[1-4])([ABC])?\b",
            re.IGNORECASE,
        )
        roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4}
        def stage_group_keys(value: str) -> set[str]:
            keys: set[str] = set()
            for snippet in _unqualified_matches(stage_group_pattern, value):
                match = stage_group_pattern.search(snippet)
                if not match:
                    continue
                numeral = match.group(1).upper()
                suffix = (match.group(2) or "").upper()
                number = roman_values.get(numeral, int(numeral) if numeral.isdigit() else None)
                if number is not None:
                    keys.add(f"{number}{suffix}")
            return keys

        source_group_keys = stage_group_keys(source_text)

        def stage_group_is_supported(generated_key: str) -> bool:
            return any(
                source_key == generated_key
                or (generated_key.isdigit() and source_key.startswith(generated_key))
                for source_key in source_group_keys
            )

        unsupported_stage_groups = [
            snippet
            for snippet in _unqualified_matches(stage_group_pattern, text)
            if not all(
                stage_group_is_supported(key)
                for key in stage_group_keys(snippet)
            )
        ]
        if unsupported_stage_groups:
            flags.append(
                "Generated narrative assigns a stage group ("
                + ", ".join(unsupported_stage_groups[:4])
                + "), but stage_group is not supplied in the structured case or explicitly recorded in the source summary."
            )
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

    # High-specificity assertion checks. Questions and qualified uncertainty are not
    # treated as findings. Exact matching source snippets remain attributed to the
    # user-provided case summary rather than being relabelled as model inventions.
    if case.performance_status in (None, ""):
        pattern = re.compile(
            r"\b(?:ECOG(?:\s*[- ]?PS|\s+performance\s+status)?|"
            r"WHO(?:\s+performance)?\s+status)\s*[:=]?\s*[0-4]\b|"
            r"\b(?:KPS|Karnofsky(?:\s+Performance\s+Status)?)\s*[:=]?\s*\d{2,3}\b",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(pattern, text, source_text)
        if matches:
            flags.append("Generated narrative assigns a performance-status score (" + ", ".join(matches[:3]) + "), but performance_status is not supplied in the structured case.")

    if case.clinical_n_stage is None:
        pattern = re.compile(
            r"\b(?:node[- ]negative|no (?:regional )?nodal (?:disease|involvement)|negative (?:regional )?nodes?)\b",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(pattern, text, source_text)
        if matches:
            flags.append("Generated narrative asserts node-negative status (" + ", ".join(matches[:3]) + "), but clinical_n_stage is not supplied.")

    if case.clinical_m_stage is None:
        pattern = re.compile(
            r"\b(?:no (?:evidence of )?(?:distant )?metastases?|no (?:evidence of )?(?:distant )?metastatic disease|without (?:distant )?metastases?|metastasis[- ]free|(?:distant )?metastases? (?:are|is) absent)\b",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(pattern, text, source_text)
        if matches:
            flags.append("Generated narrative asserts absence of metastatic disease (" + ", ".join(matches[:3]) + "), but clinical_m_stage is not supplied; absence of a reported metastasis is not M0.")

    resectability_pattern = re.compile(
        r"\b(?:is|was|remains|appears|seems|deemed|considered)\s+(?:clearly |technically |borderline )?(?:resectable|unresectable)\b|\b(?:resectable|unresectable)\s+(?:tumou?r|disease|lesion|cancer)\b|\bnot resectable\b",
        re.IGNORECASE,
    )
    matches = _unsupported_matches(resectability_pattern, text, source_text)
    if matches:
        flags.append("Generated narrative asserts resectability status (" + ", ".join(matches[:3]) + "), which is not explicitly documented in the supplied case.")

    if case.histology in (None, "") and case.pathology_summary in (None, ""):
        histology_pattern = re.compile(
            r"\b(?:squamous cell carcinoma|adenocarcinoma|small[- ]cell carcinoma|large[- ]cell carcinoma|urothelial carcinoma|neuroendocrine carcinoma|lymphoma|melanoma|sarcoma|SCC)\b",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(histology_pattern, text, source_text)
        if matches:
            flags.append("Generated narrative asserts a histological diagnosis (" + ", ".join(matches[:3]) + "), but histology/pathology is not supplied as a structured case finding.")

    if case.pathology_summary in (None, ""):
        pathology_pattern = re.compile(
            r"\b(?:p16|HPV|HER2|ER|PR|PD-L1|Ki-67)\s*(?:positive|negative|high|low|[+-])\b|\b(?:grade|G)\s*[1-4]\b|\b(?:lymphovascular|perineural) invasion\b|\b(?:positive|negative) margins?\b",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(pathology_pattern, text, source_text)
        if matches:
            flags.append("Generated narrative asserts a specific pathology/biomarker finding (" + ", ".join(matches[:3]) + "), but pathology_summary is not supplied.")

    if case.imaging_summary in (None, ""):
        investigation_pattern = re.compile(
            r"\b(?:CT|MRI|PET(?:[- ]CT)?|ultrasound|USG|X[- ]ray|radiograph|bone scan|colonoscopy|endoscopy|bronchoscopy|cystoscopy|biopsy)\s+(?:scan\s+)?(?:shows?|demonstrates?|reveals?|confirms?|identifies?|detected|reported)\s+[^.!?;\n]{1,100}",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(investigation_pattern, text, source_text)
        if matches:
            flags.append("Generated narrative asserts an imaging/investigation result (" + "; ".join(matches[:2]) + "), but imaging_summary is not supplied.")

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

    if not case.patient_goals:
        preference_pattern = re.compile(
            # Match an actual patient-attributed choice/act. The noun phrase
            # "obtain patient consent" is a recommendation to elicit consent,
            # not evidence that the patient has already consented.
            r"\bpatient(?:'s)?\s+(?:prefers?|wishes?|wants?|chooses?|declines?|refuses?|agrees?|consents\b|has chosen|has consented|does not want|doesn't want)\b[^.!?;\n]{0,100}",
            re.IGNORECASE,
        )
        matches = _unsupported_matches(preference_pattern, text, source_text)
        if matches:
            flags.append("Generated narrative attributes a patient preference/decision (" + "; ".join(matches[:2]) + "), but patient_goals are not supplied.")
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