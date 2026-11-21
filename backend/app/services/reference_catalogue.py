"""Reference catalogue service conforming to Requirement U07.

Provides structured access to clinical oncology reference materials, role-specific
retrieval, and deterministic anti-hallucination citation verification.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Literal
from pydantic import BaseModel, Field

SourceType = Literal["guideline", "textbook", "trial", "review", "consensus"]
AccessStatus = Literal["available", "restricted", "unavailable"]
SupersessionStatus = Literal["current", "superseded", "disputed"]

_DEFAULT_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[3] / "docs" / "reference_catalogue_v1.json"
)


class ReferenceEntry(BaseModel):
    """Structured oncology reference metadata conforming to U07 specification."""

    source_id: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=500)
    organization: str = Field(min_length=2, max_length=200)
    source_type: SourceType
    edition_or_version: str = Field(min_length=1, max_length=80)
    publication_date: str
    update_date: str | None = None
    jurisdiction: str = Field(default="International", max_length=80)
    specialties: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    doi_or_url: str = Field(min_length=4, max_length=500)
    access_status: AccessStatus = "available"
    supersession: SupersessionStatus = "current"
    key_passages: list[dict[str, str]] = Field(default_factory=list)


def load_reference_catalogue(path: pathlib.Path | None = None) -> list[ReferenceEntry]:
    """Load and parse reference catalogue entries from the authoritative JSON catalogue."""
    catalogue_path = path or _DEFAULT_CATALOGUE_PATH
    if not catalogue_path.is_file():
        return []
    try:
        data = json.loads(catalogue_path.read_text(encoding="utf-8"))
        raw_entries = data.get("entries") or []
        return [ReferenceEntry.model_validate(item) for item in raw_entries]
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def search_reference_catalogue(
    *,
    site: str | None = None,
    specialty: str | None = None,
    topic: str | None = None,
    source_type: SourceType | None = None,
    catalogue: list[ReferenceEntry] | None = None,
) -> list[ReferenceEntry]:
    """Filter reference catalogue by disease site, specialty, topic, and source type."""
    entries = catalogue if catalogue is not None else load_reference_catalogue()
    results: list[ReferenceEntry] = []

    clean_specialty = specialty.strip().lower() if specialty else None
    clean_topic = topic.strip().lower() if topic else None
    clean_site = site.strip().lower() if site else None

    for entry in entries:
        if source_type and entry.source_type != source_type:
            continue

        if clean_specialty:
            entry_specialties = [s.strip().lower() for s in entry.specialties]
            if clean_specialty not in entry_specialties:
                continue

        if clean_topic:
            entry_topics = [t.strip().lower() for t in entry.topics]
            if clean_topic not in entry_topics and not any(clean_topic in t for t in entry_topics):
                continue

        if clean_site:
            entry_topics = [t.strip().lower() for t in entry.topics]
            if clean_site not in entry_topics and not any(clean_site in t for t in entry_topics):
                continue

        results.append(entry)

    return results


def verify_citation(
    claim_source_id: str,
    doi_or_url: str | None = None,
    catalogue: list[ReferenceEntry] | None = None,
) -> bool:
    """Anti-hallucination verification of an alleged guideline or trial reference (U07).

    Returns True only if the reference exists in the verified catalogue and matches
    the recorded DOI / URL.
    """
    entries = catalogue if catalogue is not None else load_reference_catalogue()
    normalized_id = claim_source_id.strip().upper()

    match = next(
        (e for e in entries if e.source_id.strip().upper() == normalized_id),
        None,
    )
    if not match:
        return False

    if doi_or_url:
        normalized_target = doi_or_url.strip().lower().rstrip("/")
        recorded_url = match.doi_or_url.strip().lower().rstrip("/")
        if normalized_target != recorded_url:
            return False

    return True


def audit_claim_citations(
    claims: list[dict[str, Any]],
    catalogue: list[ReferenceEntry] | None = None,
) -> dict[str, Any]:
    """Audit a collection of specialist claims/citations against the reference catalogue (U09).

    Guarantees:
    - Every cited guideline, trial, or review is deterministically verified.
    - Hallucinated or non-matching citations are flagged as 'unverified_citation'.
    - Returns verified citations, unverified citations, and overall citation concordance rate.
    """
    entries = catalogue if catalogue is not None else load_reference_catalogue()
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []

    for claim in claims:
        source_id = str(claim.get("source_id") or claim.get("citation") or "").strip()
        doi = str(claim.get("doi_or_url") or "").strip() or None
        claim_text = str(claim.get("claim") or claim.get("statement") or "").strip()
        role_id = str(claim.get("role_id") or claim.get("agent_id") or "unknown").strip()

        if not source_id:
            continue

        is_valid = verify_citation(source_id, doi, catalogue=entries)
        record = {
            "role_id": role_id,
            "source_id": source_id,
            "doi_or_url": doi,
            "claim": claim_text,
            "verified": is_valid,
        }
        if is_valid:
            verified.append(record)
        else:
            unverified.append(record)

    total_citations = len(verified) + len(unverified)
    concordance = round(len(verified) / total_citations, 3) if total_citations > 0 else 1.0

    return {
        "total_citations": total_citations,
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "concordance_rate": concordance,
        "verified_citations": verified,
        "unverified_citations": unverified,
        "valid": len(unverified) == 0,
    }

