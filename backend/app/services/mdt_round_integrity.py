"""Deterministic source-reference auditing, evidence-excerpt binding, and wording repair helpers for MDT rounds."""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from difflib import SequenceMatcher
from typing import Any

from app.round_schemas import RoundTextRepairDraft
from app.schemas import SyntheticCase
from app.services.case_integrity import (
    audit_unverified_case_claims,
    build_case_prompt_context,
    case_summary_has_attributed_opinions,
    extract_attributed_note_opinions,
    is_empty_challenge_placeholder as _is_empty_challenge_placeholder,
    redact_flagged_tnm_values,
)
from app.services.mdt_llm_client import _compact, _generate_structured

_ROUND_REFERENCE_PATTERN = re.compile(r"\bR([123]):([A-Z]{2}-[0-9]{2})\b")
_ROUND_REFERENCE_RANGE_PATTERN = re.compile(
    r"\bR([123]):([A-Z]{2}-[0-9]{2})\s*(?:through|thru|to|[-–—])\s*(?:R\1:)?([A-Z]{2}-[0-9]{2})\b",
    re.IGNORECASE,
)
_EMBEDDED_ROUND_REFERENCE_PATTERN = re.compile(
    r"\bR[123]:[A-Z]{2}-[0-9]{2}\b",
    re.IGNORECASE,
)


def _payload_strings(value: object) -> list[str]:
    """Collect every generated string, including nested structured review fields."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _payload_strings(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _payload_strings(nested)]
    return []


def _audit_source_references(payload: dict, allowed: set[tuple[str, str]]) -> list[str]:
    """Flag unsupplied citations and unsupported scope claims without rewriting output."""
    text = " ".join(_payload_strings(payload))
    findings: list[str] = []
    ranges = sorted(set(_ROUND_REFERENCE_RANGE_PATTERN.findall(text)))
    for round_number, first_agent, last_agent in ranges:
        findings.append(
            f"Reference range R{round_number}:{first_agent} through R{round_number}:{last_agent} "
            "is not an attributable individual source citation."
        )
    references = sorted(set(_ROUND_REFERENCE_PATTERN.findall(text)))
    findings.extend(
        f"Reference R{round_number}:{agent_id} was not supplied as an attributable source to this contribution."
        for round_number, agent_id in references
        if (f"R{round_number}", agent_id) not in allowed
    )

    # A bounded peer digest cannot support claims about the complete MDT. Preserve
    # generated wording in the source contribution, but flag scope inflation so the
    # Chair can disclose it instead of presenting it as cross-role agreement.
    response = str(payload.get("response_to_other_perspectives") or "").casefold()
    unsupported_scope_phrases = (
        "all 45 roles",
        "all 45 agents",
        "all 45 specialists",
        "all roles agree",
        "all agents agree",
        "all specialists agree",
        "consensus across roles",
        "consensus across all roles",
        "complete agreement across roles",
        "complete agreement across all roles",
        "the entire mdt agrees",
        "the entire mdt supports",
        "the entire mdt opposes",
    )
    def paragraph_explicitly_rejects_scope_claim(paragraph: str) -> bool:
        # R3 must be able to quote a deliberately planted whole-MDT assertion in
        # order to challenge it. A literal phrase match alone confuses that rebuttal
        # with endorsement. Require an explicit rejection in the same paragraph;
        # attribution or quotation without rejection remains auditable as a claim.
        rejection_markers = (
            "unsupported",
            "not supported",
            "not established",
            "cannot establish",
            "cannot be established",
            "does not establish",
            "no evidence",
            "not evidenced",
            "not substantiated",
            "unverified",
            "cannot verify",
            "cannot be verified",
            "cannot be inferred",
            "bounded sample cannot",
            "not supplied",
            "not available",
            "contradicts the case",
            "contradicts the supplied",
            "false claim",
        )
        return any(marker in paragraph for marker in rejection_markers)

    paragraphs = [part.strip() for part in response.splitlines() if part.strip()]
    has_unrebutted_scope_claim = any(
        any(phrase in paragraph for phrase in unsupported_scope_phrases)
        and not paragraph_explicitly_rejects_scope_claim(paragraph)
        for paragraph in paragraphs
    )
    if has_unrebutted_scope_claim:
        findings.append(
            "Peer-scope overclaim: the response generalises agreement or conclusions beyond "
            "the individually supplied peer records; only those supplied records may be described."
        )

    # In R2, identical position labels or shared missing-information observations do not
    # demonstrate agreement on a substantive educational option. Flag explicit claims
    # that every selected peer aligns, agrees, or has no disagreement, while retaining
    # the model-authored text for Chair review. R3 may quote/rebut these claims.
    if {round_label for round_label, _ in allowed} == {"R1"}:
        peer_agreement_phrases = (
            "all selected peer positions",
            "all selected peers agree",
            "all peers agree",
            "all peers explicitly",
            "no substantive disagreement exists among peers",
            "no substantive disagreement was identified",
            "no substantive disagreement or challenge was identified",
            "there is complete agreement among peers",
            "complete agreement among peers",
            "consensus confirms",
            "consensus among peers",
            "unanimous agreement among peers",
        )
        peer_agreement_rejection_markers = (
            "unsupported",
            "not supported",
            "not established",
            "cannot establish",
            "cannot be established",
            "does not establish",
            "no evidence",
            "not evidenced",
            "not substantiated",
            "unverified",
            "cannot verify",
            "cannot be verified",
            "cannot be inferred",
            "false claim",
            "not a substantive agreement",
            "not a consensus",
        )
        peer_agreement_sentences = [
            sentence.strip()
            for paragraph in paragraphs
            for sentence in re.split("[.!?] +", paragraph)
            if sentence.strip()
        ]
        has_unrebutted_peer_agreement_claim = any(
            any(phrase in sentence for phrase in peer_agreement_phrases)
            and not any(marker in sentence for marker in peer_agreement_rejection_markers)
            for sentence in peer_agreement_sentences
        )
        if has_unrebutted_peer_agreement_claim:
            findings.append(
                "Unsupported peer-agreement claim: the R2 narrative asserts alignment, "
                "absence of substantive disagreement, or consensus across selected peers "
                "without establishing a shared source-linked proposition. Identical position "
                "labels or shared missing-information observations do not establish agreement "
                "on an educational option; the original narrative is retained for review."
            )

    # A model may drop the neutralised subject phrase from a paired-reference
    # construction (observed output: "Both and explicitly state ..."). This is
    # not safe to silently accept as traceable peer prose. Flag the malformed
    # construction, preserve the original narrative, and expose it to R4.
    if re.search(r"\bboth\s+and\b", response, re.IGNORECASE):
        findings.append(
            "Malformed paired-source wording: response contains 'both and' without "
            "the intervening source/subject phrase; review against the actual supplied peer records."
        )
    return findings

def _bounded_exact_excerpt(value: object, limit: int) -> str:
    """Return a bounded contiguous excerpt without rewriting source characters."""
    if not isinstance(value, str):
        return ""
    source = value.strip()
    if len(source) <= limit:
        return source
    boundary = source.rfind(" ", 0, limit + 1)
    return source[: boundary if boundary > 0 else limit]

def _prioritized_provenance_flags(value: object, limit: int = 5) -> list[str]:
    """Keep scope overclaims visible ahead of lower-priority citation findings."""
    if not isinstance(value, (list, tuple)):
        return []
    flags = [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]
    flags.sort(
        key=lambda item: (
            not item.startswith("Peer-scope overclaim:"),
            item.casefold(),
        )
    )
    return [_compact(item, 220) for item in flags[:limit]]


def _combined_case_integrity_flags(*values: object) -> list[str]:
    """Collect source-specific R1/R2 audit flags without mutating saved records."""
    combined: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip():
            combined.append(value.strip())
        elif isinstance(value, (list, tuple)):
            combined.extend(
                item.strip()
                for item in value
                if isinstance(item, str) and item.strip()
            )
    return combined


def _r3_peer_case_integrity_flags(peer: dict) -> list[str]:
    """Return both saved audit layers for the exact R3 peer record."""
    result = peer.get("result") or {}
    return _combined_case_integrity_flags(
        peer.get("round1_case_integrity_flags"),
        result.get("case_data_integrity_flags"),
    )


def _compact_case_integrity_flags(
    value: object,
    limit: int = 6,
    redaction_flags: object = None,
) -> list[str]:
    """Pass bounded audit warnings to prompts without leaking flagged TNM literals."""
    if not isinstance(value, (list, tuple)):
        return []
    flags = [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]
    redaction_source = flags if redaction_flags is None else redaction_flags
    return [
        _compact(redact_flagged_tnm_values(item, redaction_source), 220)
        for item in flags[:limit]
    ]


def _compact_r1_text(
    value: str,
    limit: int,
    integrity_flags: object = None,
) -> str:
    """Build an R1 prompt view with source-flagged TNM values redacted."""
    redacted = redact_flagged_tnm_values(value, integrity_flags)
    neutralized = _EMBEDDED_ROUND_REFERENCE_PATTERN.sub(
        "[embedded reference omitted]",
        redacted,
    )
    return _compact(neutralized, limit)


def _compact_r2_text(
    value: str,
    limit: int,
    integrity_flags: object = None,
) -> str:
    """Build an R2 prompt view with flagged TNM values redacted and references neutralised."""
    redacted = redact_flagged_tnm_values(value, integrity_flags)
    reference = r"R[123]:[A-Z]{2}-[0-9]{2}"
    reference_list = re.compile(
        rf"\b{reference}(?:(?:\s*,\s*(?:and\s+)?|\s+(?:and|&)\s+){reference})+\b",
        re.IGNORECASE,
    )
    # Replace a cited list as one grammatical unit before handling single IDs.
    # These generic phrases are not attributable citations; R3 must cite the
    # explicit outer source label attached to the supplied peer record instead.
    neutralized = _ROUND_REFERENCE_RANGE_PATTERN.sub(
        "the referenced role records", redacted
    )
    neutralized = reference_list.sub("the referenced role records", neutralized)
    neutralized = _EMBEDDED_ROUND_REFERENCE_PATTERN.sub(
        "the referenced role record", neutralized
    )
    return _compact(neutralized, limit)


def _bind_exact_peer_evidence_excerpt(
    model_excerpt: object,
    evidence_texts: list[str],
    *,
    minimum_match_chars: int = 48,
    minimum_match_ratio: float = 0.72,
    maximum_excerpt_chars: int = 180,
) -> tuple[str, str]:
    """Bind a model-selected quote to a contiguous server-supplied peer-text span.

    Exact matches are preferred. Small-model quote truncation/typos are tolerated
    only when a long contiguous span matches the selected peer text. The returned
    excerpt always comes verbatim from the supplied peer text; the model's original
    quote is retained separately for audit. This verifies traceability, not meaning.
    """
    if not isinstance(model_excerpt, str):
        return "", "missing"
    candidate = " ".join(model_excerpt.split())
    if not candidate:
        return "", "missing"

    best: tuple[float, int, str] | None = None
    candidate_folded = candidate.casefold()
    for value in evidence_texts:
        if not isinstance(value, str):
            continue
        source = " ".join(value.split())
        if not source:
            continue
        if candidate in source:
            exact = candidate[:maximum_excerpt_chars]
            return exact, "exact_model_quote"

        matcher = SequenceMatcher(
            None,
            candidate_folded,
            source.casefold(),
            autojunk=False,
        )
        blocks = [
            block for block in matcher.get_matching_blocks()
            if block.size > 0
        ]
        if not blocks:
            continue
        matched_chars = sum(block.size for block in blocks)
        first_source = min(block.b for block in blocks)
        last_source = max(block.b + block.size for block in blocks)
        span_length = last_source - first_source
        required = max(
            minimum_match_chars,
            int(min(len(candidate), maximum_excerpt_chars) * minimum_match_ratio),
        )
        longest_block = max(block.size for block in blocks)
        if (
            matched_chars < required
            or longest_block < min(36, required)
            or span_length > maximum_excerpt_chars
        ):
            continue
        # Gaps between matching blocks are copied only from the original peer
        # string, so the final bound remains one exact contiguous source span.
        bound = source[first_source:last_source]
        ratio = matched_chars / max(1, len(candidate), len(bound))
        option = (ratio, matched_chars, bound)
        if best is None or option[:2] > best[:2]:
            best = option

    if best is None:
        return "", "invalid"
    return best[2], "server_bound_contiguous_match"


_OPINION_ATTRIBUTION_VERB_PATTERN = re.compile(
    r"\b(?:favours?|favors?|proposes?|recommends?|supports?|prefers?|advocates?|suggests?)\b",
    re.IGNORECASE,
)
_OPINION_CONDITION_PATTERN = re.compile(
    r"\b(?:conditional on|subject to|provided that|contingent on|dependent on)\b",
    re.IGNORECASE,
)
_OPINION_TERM_STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "on", "of", "in", "for", "with",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "note", "service", "surgical", "medical", "oncology", "favours", "favour",
    "favors", "favor", "proposes", "propose", "recommends", "recommend",
    "supports", "support", "prefers", "prefer", "advocates", "advocate",
    "suggests", "suggest", "conditional", "subject", "provided", "contingent",
    "dependent", "that", "discussing", "discussion", "assessment", "review",
}


def _source_opinion_component_tokens(source_excerpt: str, component: str) -> list[str]:
    """Extract source-specific lexical anchors; this is a conservative audit, not semantic proof."""
    action = _OPINION_ATTRIBUTION_VERB_PATTERN.search(source_excerpt)
    remainder = source_excerpt[action.end():] if action else source_excerpt
    condition = _OPINION_CONDITION_PATTERN.search(remainder)
    if condition:
        option_text = remainder[:condition.start()]
        condition_text = remainder[condition.end():]
    else:
        option_text = remainder
        condition_text = ""
    selected = option_text if component == "option" else condition_text
    return [
        token
        for token in re.findall(r"[a-z0-9]+", selected.casefold())
        if len(token) >= 3 and token not in _OPINION_TERM_STOPWORDS
    ]


def _source_opinion_component_match_counts(
    source_excerpt: str,
    evidence_text: str,
    component: str,
) -> tuple[int, int]:
    source_tokens = set(_source_opinion_component_tokens(source_excerpt, component))
    if not source_tokens:
        return (0, 0)
    evidence_tokens = set(re.findall(r"[a-z0-9]+", evidence_text.casefold()))
    return len(source_tokens & evidence_tokens), len(source_tokens)


def _source_opinion_component_supported(
    source_excerpt: str,
    evidence_text: str,
    component: str,
) -> bool:
    """Require direct lexical support; exact quotation alone is not semantic support."""
    matched, total = _source_opinion_component_match_counts(
        source_excerpt, evidence_text, component
    )
    if total == 0:
        return component == "conditions"
    required = max(1, (total * 3 + 4) // 5)
    return matched >= required


def _select_source_opinion_evidence_excerpt(
    source_excerpt: str,
    evidence_texts: list[str],
    *,
    maximum_excerpt_chars: int = 180,
) -> str:
    """Select a verbatim peer excerpt meeting the same anchors used by R2 validation.

    R2 accepts source-specific wording when at least 60% of the component's
    lexical anchors are retained. R3 must use that same policy: requiring every
    token here rejects benign variants such as "surgery-first assessment" for
    "surgery-led assessment first", even though the R2 audit accepts the match.
    Provenance remains strict: the returned quote must be an exact contiguous
    substring of the one selected peer's saved text and must independently
    support both option and condition components.
    """
    option_tokens = set(_source_opinion_component_tokens(source_excerpt, "option"))
    if not option_tokens:
        return ""

    best: tuple[int, int, int, str] | None = None
    for text_index, value in enumerate(evidence_texts):
        if not isinstance(value, str):
            continue
        normalized = " ".join(value.split())
        if not normalized:
            continue
        words = list(re.finditer(r"\S+", normalized))
        for start_index, start_word in enumerate(words):
            for end_index in range(start_index, len(words)):
                end_word = words[end_index]
                if end_word.end() - start_word.start() > maximum_excerpt_chars:
                    break
                candidate = normalized[start_word.start():end_word.end()]
                if not all(
                    _source_opinion_component_supported(source_excerpt, candidate, component)
                    for component in ("option", "conditions")
                ):
                    continue
                option = (len(candidate), text_index, start_index, candidate)
                if best is None or option[:3] < best[:3]:
                    best = option
                # Extending this start can only make the excerpt longer; retain
                # the shortest evidence window that meets both component checks.
                break

    return best[3] if best is not None else ""


def _source_opinion_component_has_any_support(
    source_excerpt: str,
    evidence_text: str,
    component: str,
) -> bool:
    matched, total = _source_opinion_component_match_counts(
        source_excerpt, evidence_text, component
    )
    return total == 0 or matched > 0



_PREREQUISITE_INTEGRITY_FLAG_PREFIX = (
    "Generated narrative describes prerequisite(s) as unmet/not met"
)
_REPAIRABLE_TOP_LEVEL_TEXT_FIELDS = (
    "provisional_conclusion",
    "response_to_other_perspectives",
    "agreements",
    "substantive_challenges",
    "remaining_unknowns",
    "risk_flags",
)


def _active_case_integrity_payload(value):
    """Remove preserved audit copies; only current authored narrative is re-audited."""
    if isinstance(value, dict):
        return {
            key: _active_case_integrity_payload(item)
            for key, item in value.items()
            if not key.startswith(("model_reported_", "integrity_repair_"))
            and key not in {"case_data_integrity_flags", "source_reference_integrity_flags"}
        }
    if isinstance(value, (list, tuple)):
        return [_active_case_integrity_payload(item) for item in value]
    return value


def _prerequisite_integrity_flags(flags: list[str]) -> list[str]:
    return [
        flag for flag in flags
        if flag.startswith(_PREREQUISITE_INTEGRITY_FLAG_PREFIX)
    ]


_TREATMENT_INDICATION_INTEGRITY_FLAG_PREFIX = (
    "Generated narrative makes a definitive treatment safety/indication assertion"
)


def _repairable_clinical_integrity_flags(flags: list[str]) -> list[str]:
    """Select only narrowly repairable wording defects; all other audit flags block."""
    return [
        flag for flag in flags
        if flag.startswith(_PREREQUISITE_INTEGRITY_FLAG_PREFIX)
        or flag.startswith(_TREATMENT_INDICATION_INTEGRITY_FLAG_PREFIX)
    ]


def _repairable_narrative_locations(payload: dict) -> dict[str, tuple[str, int | None, str | None, str]]:
    """Map a closed set of authored narrative paths to their container locations."""
    locations: dict[str, tuple[str, int | None, str | None, str]] = {}
    for field in _REPAIRABLE_TOP_LEVEL_TEXT_FIELDS:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            locations[field] = (field, None, None, value)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, str) and item.strip():
                    locations[f"{field}[{index}]"] = (field, index, None, item)

    for collection, subfields in (
        ("source_opinion_responses", ("analysis", "comparison")),
        ("source_opinion_reviews", ("review_basis", "challenge")),
    ):
        items = payload.get(collection)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for subfield in subfields:
                value = item.get(subfield)
                if isinstance(value, str) and value.strip():
                    path = f"{collection}[{index}].{subfield}"
                    locations[path] = (collection, index, subfield, value)
    return locations


def _repairable_text_max_length(path: str) -> int | None:
    """Return the actual schema limit for a narrowly repairable narrative path."""
    response_match = re.fullmatch(
        r"source_opinion_responses\[\d+\]\.(analysis|comparison)", path
    )
    if response_match:
        return {"analysis": 700, "comparison": 400}[response_match.group(1)]
    review_match = re.fullmatch(
        r"source_opinion_reviews\[\d+\]\.(review_basis|challenge)", path
    )
    if review_match:
        return {"review_basis": 600, "challenge": 700}[review_match.group(1)]
    return {
        "provisional_conclusion": 900,
        "response_to_other_perspectives": 1600,
    }.get(path)


def _set_repairable_narrative_text(
    payload: dict,
    location: tuple[str, int | None, str | None, str],
    replacement: str,
) -> None:
    field, index, subfield, _ = location
    if index is None:
        payload[field] = replacement
    elif subfield is None:
        payload[field][index] = replacement
    else:
        payload[field][index][subfield] = replacement


def _round_reference_tokens(value: str) -> list[str]:
    return re.findall(
        r"\b(?:CASE:case_summary#[1-9][0-9]*|R[123]:[A-Z]{2}-[0-9]{2})\b",
        value,
    )


_NEITHER_INDICATION_ASSERTION = re.compile(
    r"\bneither\s+(?P<subjects>[^.!?;:\n]{1,120}?)\s+"
    r"(?P<verb>is|are|was|were|has been|remains)\s+"
    r"(?P<qualifier>clearly\s+)?"
    r"(?P<status>indicated|recommended|appropriate|suitable)\b",
    re.IGNORECASE,
)


def _deterministically_neutralise_unsupported_prerequisite_status(value: str) -> str | None:
    """Convert unsupported categorical prerequisite status into explicit uncertainty.

    This deliberately edits only the exact status construction identified by the
    deterministic audit. It does not infer that a prerequisite is fulfilled or
    change the option, condition, role position, or surrounding source references.
    The candidate is still subjected to the complete post-repair audit.
    """
    repaired = value

    # "unmet prerequisites" -> "prerequisites whose fulfilment status is unknown"
    repaired, noun_replacements = re.subn(
        r"\b(?P<status>unmet|unfulfilled)\s+(?P<kind>(?:clinical\s+)?(?:prerequisite|condition|requirement)s?)\b",
        lambda match: (
            f"{match.group('kind')} whose fulfilment status is not established "
            "by the supplied record"
        ),
        repaired,
        flags=re.IGNORECASE,
    )

    # Coordinated negative-status wording must be repaired as one predicate.
    # Otherwise "prerequisites are not met or documented" would become an
    # ungrammatical "undetermined fulfilment status ... or documented".
    repaired, coordinated_replacements = re.subn(
        r"\b(?P<subject>(?:(?:these|those|the|all|their)\s+)?"
        r"(?:clinical\s+)?(?:prerequisite|condition|requirement)s?"
        r"(?:\s+for\s+(?:this|that|the)\s+option)?)\s+"
        r"(?P<verb>remain(?:s)?|are|is|were|was|have(?:\s+been)?|has(?:\s+been)?)\s+"
        r"not\s+(?:been\s+)?met\s+or\s+(?:been\s+)?"
        r"(?:documented|assessed|verified|established)\b",
        lambda match: (
            f"{match.group('subject')} "
            f"{'have' if match.group('subject').rstrip().casefold().endswith(('prerequisites', 'conditions', 'requirements')) else 'has'} "
            "no documented fulfilment assessment in the supplied record"
        ),
        repaired,
        flags=re.IGNORECASE,
    )

    # "these prerequisites remain unmet" / "prerequisites are not met".
    repaired, predicate_replacements = re.subn(
        r"\b(?P<subject>(?:(?:these|those|the|all|their)\s+)?"
        r"(?:clinical\s+)?(?:prerequisite|condition|requirement)s?"
        r"(?:\s+for\s+(?:this|that|the)\s+option)?)\s+"
        r"(?P<verb>remain(?:s)?|are|is|were|was|have(?:\s+been)?|has(?:\s+been)?)\s+"
        r"(?:unmet(?:\s*/\s*unknown)?|unfulfilled|not\s+(?:been\s+)?(?:met|fulfilled))\b",
        lambda match: (
            f"{match.group('subject')} "
            f"{'have' if match.group('subject').rstrip().casefold().endswith(('prerequisites', 'conditions', 'requirements')) else 'has'} "
            "an undetermined fulfilment status in the supplied record"
        ),
        repaired,
        flags=re.IGNORECASE,
    )

    # "neither prerequisite is met" is also a categorical negative status, even
    # though it does not contain the literal phrase "not met".
    def neutralise_neither_status(match: re.Match[str]) -> str:
        prefix = repaired[:match.start()]
        lead = "The" if not prefix.strip() or prefix.rstrip().endswith((".", "!", "?", "\n")) else "the"
        return (
            f"{lead} fulfilment status of the referenced "
            f"{match.group('subject')} is undetermined"
        )

    repaired, neither_status_replacements = re.subn(
        r"\bneither\s+(?:(?:of\s+)?(?:the\s+)?(?:two|both|these|those)\s+)?(?:the\s+)?"
        r"(?P<subject>(?:clinical\s+)?(?:prerequisite|condition|requirement)s?)\s+"
        r"(?:is|are|was|were|has\s+been|have\s+been)\s+met\b",
        neutralise_neither_status,
        repaired,
        flags=re.IGNORECASE,
    )

    # "conditionality remains unmet" is also an unsupported categorical status.
    repaired, conditionality_replacements = re.subn(
        r"\b(?P<subject>conditionality|conditional\s+(?:status|position|option))\s+"
        r"(?P<verb>remain(?:s)?|is|are|was|were)\s+"
        r"(?:unmet(?:\s*/\s*unknown)?|unfulfilled|not\s+(?:been\s+)?(?:met|fulfilled))\b",
        lambda match: (
            f"{match.group('subject')} {match.group('verb')} unresolved "
            "in the supplied record"
        ),
        repaired,
        flags=re.IGNORECASE,
    )

    if noun_replacements + coordinated_replacements + predicate_replacements + neither_status_replacements + conditionality_replacements == 0:
        return None
    return repaired if repaired != value else None


def _deterministically_neutralise_neither_indication_claim(value: str) -> str | None:
    """Narrowly neutralise 'neither X nor Y is indicated' without rewriting context.

    This fallback is used only when the model's proposed repair drops source
    reference tokens. It changes only the categorical predicate, retains both
    option phrases and every surrounding word/token, and is re-audited before
    it can be applied.
    """
    def replace(match: re.Match[str]) -> str:
        subjects = match.group("subjects")
        revised_subjects, connector_count = re.subn(
            r"\s+nor\s+", " or ", subjects, count=1, flags=re.IGNORECASE
        )
        if connector_count > 1:
            return match.group(0)
        prefix = value[:match.start()]
        sentence_start = not prefix.strip() or prefix.rstrip().endswith((".", "!", "?", "\n"))
        lead = "The supplied information" if sentence_start else "the supplied information"
        qualifier = match.group("qualifier") or ""
        subject_phrase = (
            f"whether either {revised_subjects}"
            if connector_count == 1
            else f"whether {subjects}"
        )
        return (
            f"{lead} does not establish {subject_phrase} "
            f"{match.group('verb')} {qualifier}{match.group('status')}"
        )

    repaired, replacements = _NEITHER_INDICATION_ASSERTION.subn(replace, value)
    return repaired if replacements and repaired != value else None


def _source_opinion_repair_preserves_anchors(
    case: SyntheticCase,
    payload: dict,
    path: str,
    replacement: str,
) -> bool:
    response_match = re.fullmatch(
        r"source_opinion_responses\[(\d+)\]\.(analysis|comparison)", path
    )
    review_match = re.fullmatch(
        r"source_opinion_reviews\[(\d+)\]\.review_basis", path
    )
    if not response_match and not review_match:
        return True

    if response_match:
        index = int(response_match.group(1))
        records = payload.get("source_opinion_responses") or []
        required_components = ("option", "conditions")
    else:
        index = int(review_match.group(1))
        records = payload.get("source_opinion_reviews") or []
        if index >= len(records) or not isinstance(records[index], dict):
            return False
        review = records[index]
        # A review that explicitly labels a component as preserved must keep
        # its source anchors in the repaired explanation. Omitted/unclear
        # components are not forced to quote anchors they say are absent.
        status_to_component = {
            "option_status": "option",
            "conditions_status": "conditions",
        }
        required_components = tuple(
            component
            for status_field, component in status_to_component.items()
            if review.get(status_field) == "preserved"
        )

    if index >= len(records) or not isinstance(records[index], dict):
        return False
    record = records[index]
    source_id = str(record.get("source_id") or "")
    source_excerpt = str(record.get("source_excerpt") or "")
    registered = {
        item["source_id"]: item["source_excerpt"]
        for item in extract_attributed_note_opinions(case.case_summary)
    }
    if not source_id or registered.get(source_id) != source_excerpt:
        return False
    if response_match:
        # The option and its prerequisites must remain represented across the
        # complete structured source response after replacing either text field.
        replaced_field = response_match.group(2)
        support_text = " ".join(
            str(record.get(field) or "")
            for field in ("analysis", "comparison")
            if field != replaced_field
        ) + " " + replacement
    else:
        support_text = replacement
    return all(
        _source_opinion_component_supported(source_excerpt, support_text, component)
        for component in required_components
    )


async def _repair_unsupported_prerequisite_wording(
    case: SyntheticCase,
    payload: dict,
    *,
    round_number: int,
    role_id: str,
    role_name: str,
    allowed_sources: set[tuple[str, str]],
    generate_structured_fn: Callable[[str, type[Any], int], Awaitable[Any]] | None = None,
) -> tuple[dict, list[str]]:
    """Repair only audited prerequisite/negative-indication wording at exact text paths."""
    active_payload = _active_case_integrity_payload(payload)
    original_flags = audit_unverified_case_claims(case, active_payload)
    target_flags = _repairable_clinical_integrity_flags(original_flags)
    if not target_flags:
        payload.update({
            "integrity_repair_attempted": False,
            "integrity_repair_status": "not_needed",
            "integrity_repair_original_text": {},
            "integrity_repair_proposed_text": {},
            "integrity_repair_original_flags": [],
            "integrity_repair_applied_paths": [],
            "integrity_repair_flags": [],
        })
        return payload, original_flags

    locations = _repairable_narrative_locations(payload)
    repair_targets = {
        path: location
        for path, location in locations.items()
        if _repairable_clinical_integrity_flags(
            audit_unverified_case_claims(case, {"candidate": location[3]})
        )
    }
    original_text = {path: location[3] for path, location in repair_targets.items()}

    def blocked_without_call(message: str) -> tuple[dict, list[str]]:
        payload.update({
            "integrity_repair_attempted": False,
            "integrity_repair_status": "blocked",
            "integrity_repair_original_text": original_text,
            "integrity_repair_proposed_text": {},
            "integrity_repair_original_flags": original_flags[:20],
            "integrity_repair_applied_paths": [],
            "integrity_repair_flags": [message],
        })
        return payload, original_flags

    if not repair_targets:
        return blocked_without_call(
            "The prerequisite integrity finding could not be mapped to a single repairable authored text field; no automatic repair was attempted."
        )
    if len(repair_targets) > 12:
        return blocked_without_call(
            "The prerequisite integrity finding affected more than 12 text fields; bounded automatic repair was not attempted."
        )

    repair_register = [
        {"field_path": path, "original_text": original_text[path]}
        for path in repair_targets
    ]
    repair_prompt = (
        f"ROUND {round_number} CLINICAL-INTEGRITY WORDING REPAIR. This is one narrowly scoped "
        "correction to the exact text fields listed below, not a new clinical assessment or position. "
        "The deterministic audit found either an unsupported unmet-prerequisite statement or a categorical "
        "negative treatment indication/safety statement that is not supported by the supplied case. "
        "Rewrite each listed field so missing or undocumented assessments remain UNKNOWN / NOT SUPPLIED, "
        "never unmet or not met. When the text claims that no option, neither option, or no pathway is "
        "indicated/appropriate solely because information is missing, replace that assertion with an "
        "information-sufficiency statement: 'The supplied information does not establish whether the "
        "source option is indicated or appropriate; indication and suitability remain undetermined.' "
        "Do not infer that the option is indicated either. Preserve the existing educational position, all distinct "
        "source options, every condition attached to each option, the level of uncertainty, and the "
        "role's original reasoning. Do not add clinical facts, findings, staging, fitness, suitability, "
        "patient preferences, recommendations, or new conclusions. Do not delete the option or its "
        "condition to avoid the audit. Keep every source-reference token exactly as supplied: do not "
        "add, remove, rename, or move CASE:case_summary#N or R1/R2/R3:AGENT_ID references. "
        "Return exactly one replacement for every field_path, in the same order, and no other path. "
        "Do not return position, confidence, source metadata, or any other fields. A failed or incomplete "
        "repair will be rejected and the original text retained.\n"
        f"ROUND: {round_number}\nROLE: {role_name} ({role_id})\n"
        "SAVED EDUCATIONAL POSITION (immutable): "
        + str(payload.get("position") or "unknown")
        + "\nSUPPLIED CASE (source data, not verified findings):\n"
        + json.dumps(build_case_prompt_context(case), ensure_ascii=False, separators=(",", ":"))
        + "\nEXACT REPAIR REGISTER:\n"
        + json.dumps(repair_register, ensure_ascii=False, separators=(",", ":"))
        + "\nReturn only the RoundTextRepairDraft schema."
    )
    proposed_text: dict[str, str] = {}
    try:
        llm_call = generate_structured_fn or _generate_structured
        draft = await llm_call(repair_prompt, RoundTextRepairDraft, 1400)
        returned = draft.replacements
        returned_paths = [item.field_path for item in returned]
        expected_paths = list(repair_targets)
        proposed_text = {
            item.field_path: item.replacement_text
            for item in returned
        }
        if (
            returned_paths != expected_paths
            or len(set(returned_paths)) != len(expected_paths)
        ):
            raise ValueError(
                "Repair response did not return exactly one replacement for every requested field path in order."
            )
        for path, replacement in proposed_text.items():
            original = original_text[path]
            field_limit = _repairable_text_max_length(path)
            references_changed = (
                _round_reference_tokens(replacement) != _round_reference_tokens(original)
            )
            exceeds_field_limit = field_limit is not None and len(replacement) > field_limit
            if references_changed or exceeds_field_limit:
                # A generic repair response permits up to 1,600 characters, but
                # nested persisted fields have narrower schema limits. Prefer a
                # surgical deterministic rewrite of the original when it can
                # preserve the existing source/condition anchors and fit the
                # destination field. Otherwise reject the repair and retain the
                # original text rather than allowing final model validation to crash.
                deterministic_replacement = (
                    _deterministically_neutralise_unsupported_prerequisite_status(original)
                    or _deterministically_neutralise_neither_indication_claim(original)
                )
                if (
                    deterministic_replacement is None
                    or _round_reference_tokens(deterministic_replacement)
                    != _round_reference_tokens(original)
                    or (field_limit is not None and len(deterministic_replacement) > field_limit)
                ):
                    if references_changed:
                        raise ValueError(
                            f"Repair changed source-reference tokens in {path}; the original text was retained."
                        )
                    raise ValueError(
                        f"Repair exceeded the {field_limit}-character schema limit for {path}, "
                        "and no safe in-limit deterministic rewrite was available; the original text was retained."
                    )
                replacement = deterministic_replacement
                proposed_text[path] = deterministic_replacement
            if field_limit is not None and len(replacement) > field_limit:
                raise ValueError(
                    f"Repair exceeded the {field_limit}-character schema limit for {path}; the original text was retained."
                )
            if not _source_opinion_repair_preserves_anchors(case, payload, path, replacement):
                # A semantically safe generic rewrite can still erase the exact
                # attributed option/condition. In that case, prefer a surgical
                # rewrite of the original unsafe sentence, then re-check every
                # source anchor and the complete integrity audit below.
                deterministic_replacement = (
                    _deterministically_neutralise_unsupported_prerequisite_status(original)
                    or _deterministically_neutralise_neither_indication_claim(original)
                )
                if (
                    deterministic_replacement is not None
                    and not _source_opinion_repair_preserves_anchors(
                        case, payload, path, deterministic_replacement
                    )
                ):
                    # The exact server-registered excerpt is trusted source text.
                    # Append it only when the original field's deterministic edit
                    # lacks enough lexical anchors; never ask the model to recreate
                    # or paraphrase the source option/conditions.
                    match = re.fullmatch(
                        r"source_opinion_responses\[(\d+)\]\.(analysis|comparison)",
                        path,
                    )
                    if match:
                        source_records = payload.get("source_opinion_responses") or []
                    else:
                        match = re.fullmatch(
                            r"source_opinion_reviews\[(\d+)\]\.review_basis",
                            path,
                        )
                        source_records = payload.get("source_opinion_reviews") or []
                    if match:
                        source_index = int(match.group(1))
                        if source_index < len(source_records) and isinstance(source_records[source_index], dict):
                            exact_excerpt = str(source_records[source_index].get("source_excerpt") or "")
                            anchored_candidate = (
                                deterministic_replacement + " Attributed source wording: " + exact_excerpt
                            )
                            if _source_opinion_repair_preserves_anchors(
                                case, payload, path, anchored_candidate
                            ):
                                deterministic_replacement = anchored_candidate
                if (
                    deterministic_replacement is None
                    or _round_reference_tokens(deterministic_replacement)
                    != _round_reference_tokens(original)
                    or (field_limit is not None and len(deterministic_replacement) > field_limit)
                    or not _source_opinion_repair_preserves_anchors(
                        case, payload, path, deterministic_replacement
                    )
                ):
                    raise ValueError(
                        f"Repair did not retain the registered source option and prerequisite anchors in {path}; "
                        "no safe deterministic rewrite of the original text was available."
                    )
                replacement = deterministic_replacement
                proposed_text[path] = deterministic_replacement

        # A model can append a safe disclaimer while leaving the audited unsafe
        # status wording intact. If its candidate still fails the targeted audit,
        # fall back to a deterministic edit of the original exact field.
        for path, replacement in list(proposed_text.items()):
            remaining_candidate_flags = _repairable_clinical_integrity_flags(
                audit_unverified_case_claims(case, {"candidate": replacement})
            )
            if not remaining_candidate_flags:
                continue
            original = original_text[path]
            deterministic_replacement = (
                _deterministically_neutralise_unsupported_prerequisite_status(original)
                or _deterministically_neutralise_neither_indication_claim(original)
            )
            if (
                deterministic_replacement is not None
                and _round_reference_tokens(deterministic_replacement)
                == _round_reference_tokens(original)
                and _source_opinion_repair_preserves_anchors(
                    case, payload, path, deterministic_replacement
                )
            ):
                proposed_text[path] = deterministic_replacement

        trial = json.loads(json.dumps(payload))
        for path, replacement in proposed_text.items():
            _set_repairable_narrative_text(trial, repair_targets[path], replacement)

        post_active = _active_case_integrity_payload(trial)
        post_flags = audit_unverified_case_claims(case, post_active)
        remaining_target_flags = _repairable_clinical_integrity_flags(post_flags)
        new_case_flags = [flag for flag in post_flags if flag not in original_flags]
        prior_reference_flags = set(_audit_source_references(payload, allowed_sources))
        repaired_reference_flags = set(_audit_source_references(trial, allowed_sources))
        new_reference_flags = sorted(repaired_reference_flags - prior_reference_flags)
        if remaining_target_flags or new_case_flags or new_reference_flags:
            details = remaining_target_flags + new_case_flags + new_reference_flags
            payload.update({
                "integrity_repair_attempted": True,
                "integrity_repair_status": "blocked",
                "integrity_repair_original_text": original_text,
                "integrity_repair_proposed_text": proposed_text,
                "integrity_repair_original_flags": original_flags[:20],
                "integrity_repair_applied_paths": [],
                "integrity_repair_flags": list(dict.fromkeys(details))[:20],
            })
            return payload, original_flags

        trial.update({
            "integrity_repair_attempted": True,
            "integrity_repair_status": "completed",
            "integrity_repair_original_text": original_text,
            "integrity_repair_proposed_text": proposed_text,
            "integrity_repair_original_flags": original_flags[:20],
            "integrity_repair_applied_paths": list(proposed_text),
            "integrity_repair_flags": [],
        })
        return trial, post_flags
    except Exception as exc:
        payload.update({
            "integrity_repair_attempted": True,
            "integrity_repair_status": "blocked" if isinstance(exc, ValueError) or proposed_text else "failed",
            "integrity_repair_original_text": original_text,
            "integrity_repair_proposed_text": proposed_text,
            "integrity_repair_original_flags": original_flags[:20],
            "integrity_repair_applied_paths": [],
            "integrity_repair_flags": [
                f"{type(exc).__name__}: {str(exc)[:240]}"
            ],
        })
        return payload, original_flags

