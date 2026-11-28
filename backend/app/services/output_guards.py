"""Deterministic post-generation guards for STG-00 staging lock, U09 citations, and R2 peer engagement."""
from __future__ import annotations

import re
from typing import Any

from app.services.reference_catalogue import get_active_reference_catalogue, verify_citation

_NARRATIVE_FIELDS: tuple[str, ...] = (
    "provisional_conclusion",
    "preferred_educational_option",
    "perspective_summary",
    "response_to_other_perspectives",
    "position_rationale",
    "key_evidence",
    "key_points",
    "conditional_options",
    "discussion_options",
    "remaining_unknowns",
    "agreements",
    "substantive_challenges",
    "safety_flags",
)

_NEGATION_PHRASES: tuple[str, ...] = (
    "not ",
    "unlike ",
    "rather than",
    "instead of",
    "replaces",
    "discrepancy",
    "contradict",
    "previously",
    "incorrect",
    "erroneous",
    "provided ",
    "redacted",
)

_T_N0_M_PATTERN = re.compile(r"\b(?:c|p)?T(\d[a-zA-Z]?)\s*N0(?:\s*M([01xX]))?\b", re.IGNORECASE)
_STANDALONE_N0_PATTERN = re.compile(r"\bN0\b", re.IGNORECASE)
_INLINE_CITATION_PATTERN = re.compile(
    r"\s*\[(?:source_id|source|ref|citation):\s*([A-Za-z0-9_\-\.]+)\s*\]",
    re.IGNORECASE,
)


def _apply_to_payload_fields(
    payload: dict[str, Any],
    transform: Any,
    fields: tuple[str, ...] = _NARRATIVE_FIELDS,
) -> dict[str, Any]:
    """Apply a string transformation across scalar and list-of-string payload fields."""
    for key in fields:
        val = payload.get(key)
        if isinstance(val, str):
            payload[key] = transform(val)
        elif isinstance(val, list):
            payload[key] = [transform(item) if isinstance(item, str) else item for item in val]
    return payload


def enforce_staging_lock_on_payload(payload: dict[str, Any], pre_staging: Any | None) -> dict[str, Any]:
    """Replace unnegated N0 contradictions when STG-00 locks a positive nodal stage."""
    provisional_tnm = getattr(pre_staging, "provisional_tnm", None) if pre_staging is not None else None
    if not isinstance(provisional_tnm, dict):
        return payload

    locked_n = str(provisional_tnm.get("n") or "").strip()
    if not locked_n.upper().startswith("N") or locked_n.upper() in ("N0", "NX", "NONE", ""):
        return payload

    def _sanitize_text(text: str) -> str:
        def _replace_tnm(match: re.Match[str]) -> str:
            t_part = match.group(1)
            m_part = match.group(2)
            return f"cT{t_part} {locked_n} M{m_part}" if m_part else f"cT{t_part} {locked_n}"

        updated = _T_N0_M_PATTERN.sub(_replace_tnm, text)

        def _replace_n0(match: re.Match[str]) -> str:
            prefix = updated[max(0, match.start() - 35) : match.start()].lower()
            if any(neg in prefix for neg in _NEGATION_PHRASES):
                return match.group(0)
            return locked_n

        return _STANDALONE_N0_PATTERN.sub(_replace_n0, updated)

    return _apply_to_payload_fields(payload, _sanitize_text)


def sanitize_unverified_citations_in_payload(
    payload: dict[str, Any],
    extra_valid_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Strip inline [source_id: ...] tags that fail deterministic reference catalogue verification."""
    catalogue = get_active_reference_catalogue()
    valid_extra = {s.strip().upper() for s in (extra_valid_ids or set()) if s}

    def _strip_unverified(text: str) -> str:
        def _keep_or_drop(match: re.Match[str]) -> str:
            sid = match.group(1).strip()
            if sid.upper() in valid_extra or verify_citation(sid, catalogue=catalogue):
                return match.group(0)
            return ""

        cleaned = _INLINE_CITATION_PATTERN.sub(_keep_or_drop, text)
        cleaned = re.sub(r" +([.,;:])", r"\1", cleaned)
        return re.sub(r" {2,}", " ", cleaned).strip()

    fields = _NARRATIVE_FIELDS + ("supporting_sources",)
    return _apply_to_payload_fields(payload, _strip_unverified, fields=fields)


def ensure_r2_peer_engagement(payload: dict[str, Any], peers: list[dict[str, Any]]) -> dict[str, Any]:
    """Ensure Round 2 payloads include at least one grounded peer agreement or challenge when peers exist."""
    if not peers:
        return payload
    agreements = list(payload.get("agreements") or [])
    challenges = list(payload.get("substantive_challenges") or [])
    if agreements or challenges:
        return payload

    own_pos = str(payload.get("position") or "").strip().lower()
    chosen_peer = peers[0]
    for peer in peers:
        peer_pos = str(peer.get("position") or "").strip().lower()
        if peer_pos and peer_pos != own_pos:
            chosen_peer = peer
            break

    peer_pos = str(chosen_peer.get("position") or "").strip().lower()
    peer_src = str(chosen_peer.get("source") or chosen_peer.get("role") or "peer").strip()
    peer_opt = str(
        chosen_peer.get("preferred_educational_option")
        or chosen_peer.get("provisional_conclusion")
        or ""
    ).strip()[:140]

    if peer_pos and peer_pos != own_pos:
        challenges.append(
            f"Challenges {peer_src} ({peer_pos}) perspective regarding option '{peer_opt}' "
            "pending missing diagnostic/staging prerequisites."
        )
        payload["substantive_challenges"] = challenges
    else:
        agreements.append(
            f"Agrees with {peer_src} ({peer_pos or 'peer'}) on key clinical priorities "
            f"while preserving case-specific prerequisites: '{peer_opt}'."
        )
        payload["agreements"] = agreements
    return payload
