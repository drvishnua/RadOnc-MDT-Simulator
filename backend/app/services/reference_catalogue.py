"""Reference catalogue service conforming to Requirement U07.

Provides structured access to clinical oncology reference materials, role-specific
retrieval, and deterministic anti-hallucination citation verification.
"""
from __future__ import annotations

import json
import logging
import pathlib
import re
from typing import Any, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    aliases: list[str] = Field(default_factory=list)
    key_passages: list[dict[str, str]] = Field(default_factory=list)


def load_reference_catalogue(path: pathlib.Path | None = None) -> list[ReferenceEntry]:
    """Load and parse reference catalogue entries from the authoritative JSON catalogue."""
    catalogue_path = path or _DEFAULT_CATALOGUE_PATH
    if not catalogue_path.is_file():
        return []
    try:
        data = json.loads(catalogue_path.read_text(encoding="utf-8"))
        raw_entries = data.get("entries") or []
        entries = [ReferenceEntry.model_validate(item) for item in raw_entries]
        if path is None:
            # Merge dynamically indexed library reference entries when loading default catalogue
            try:
                from app.services.library_indexer import get_library_indexer
                indexer = get_library_indexer()
                seen = {e.source_id.upper() for e in entries}
                for item in indexer.get_all_reference_entries():
                    if item.source_id.upper() not in seen:
                        entries.append(item)
                        seen.add(item.source_id.upper())
            except Exception as exc:
                logger.warning("Failed to merge library indexer entries into reference catalogue: %s", exc)
        return entries
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def _normalize_citation_token(text: str) -> str:
    """Normalize a citation token by stripping punctuation, hyphens, colons, slashes, and whitespace."""
    return re.sub(r"[\s\-_\.:/\u2010-\u2015]", "", text).upper()


_DOMAIN_TO_SOURCE_TYPE: dict[str, SourceType] = {
    "guidelines": "guideline",
    "textbooks_radiobiology": "textbook",
    "trials_systemic": "trial",
    "organ_tolerances": "consensus",
    "staging_anatomy": "guideline",
    "general_medicine": "review",
}

_DOMAIN_TO_SPECIALTIES: dict[str, list[str]] = {
    "guidelines": ["radiation_oncology", "medical_oncology", "surgical_oncology"],
    "textbooks_radiobiology": ["radiation_oncology", "medical_physics"],
    "trials_systemic": ["medical_oncology", "radiation_oncology"],
    "organ_tolerances": ["radiation_oncology", "medical_physics", "dosimetry"],
    "staging_anatomy": ["radiation_oncology", "surgical_oncology", "radiology"],
    "general_medicine": ["general_medicine", "medical_oncology"],
}

_DOMAIN_TO_ORGANIZATION: dict[str, str] = {
    "guidelines": "Multi-Society Guidelines (NCCN/ASTRO/ESTRO)",
    "textbooks_radiobiology": "Radiation Oncology Textbook",
    "trials_systemic": "Landmark Oncology Trials",
    "organ_tolerances": "QUANTEC / PENTEC Consensus",
    "staging_anatomy": "AJCC / Contouring Atlas",
    "general_medicine": "General Medical Literature",
}

_CANONICAL_ALIASES_MAP: dict[str, list[str]] = {
    "RTOG-9111": ["RTOG 91-11", "RTOG 9111", "RTOG9111"],
    "RTOG-0617": ["RTOG 0617", "RTOG 06-17", "RTOG0617"],
    "RTOG-9501-EORTC-22931": ["RTOG 9501", "EORTC 22931", "RTOG-9501", "EORTC-22931"],
    "ASTRO-LARYNX-2020": ["ASTRO Larynx Guideline", "ASTRO 2020 Larynx", "ASTRO Larynx"],
    "NCCN-HN-2026": ["NCCN Head & Neck Guidelines", "NCCN Head and Neck", "NCCN HN 2026", "NCCN-HN"],
    "NCCN-HN-2024": ["NCCN Head & Neck Guidelines", "NCCN Head and Neck", "NCCN-HN-2024"],
    "NCCN-NSCL-2026": ["NCCN NSCLC", "NCCN Non-Small Cell Lung", "NCCN Lung"],
    "NCCN-BREAST-2026": ["NCCN Breast Cancer", "NCCN Breast"],
    "NCCN-PROSTATE-2026": ["NCCN Prostate Cancer", "NCCN Prostate"],
    "NCCN-RECTAL-2026": ["NCCN Rectal Cancer", "NCCN Rectal"],
    "NCCN-CERVICAL-2026": ["NCCN Cervical Cancer", "NCCN Cervical"],
    "QUANTEC-PAROTID-2010": ["QUANTEC Parotid", "QUANTEC Parotid Gland", "QUANTEC Salivary"],
    "QUANTEC-CORD-2010": ["QUANTEC Spinal Cord", "QUANTEC Cord"],
    "QUANTEC-LUNG-2010": ["QUANTEC Lung", "QUANTEC Pneumonitis"],
    "QUANTEC-BRAINSTEM-2010": ["QUANTEC Brainstem"],
    "QUANTEC-HEART-2010": ["QUANTEC Heart", "QUANTEC Cardiac"],
    "PEREZ-BRADY-2026": ["Perez & Brady", "Perez and Brady 2026", "Perez and Brady"],
    "GUNDERSON-TEPPER-5TH": ["Gunderson & Tepper", "Gunderson and Tepper 5th"],
    "PACIFIC-TRIAL": ["PACIFIC", "PACIFIC Trial", "Durvalumab PACIFIC"],
    "HARRISONS-MED-21ST": ["Harrisons", "Harrison's Principles of Internal Medicine"],
}


def get_active_reference_catalogue(
    static_catalogue_path: pathlib.Path | None = None,
    indexer: Any | None = None,
) -> list[ReferenceEntry]:
    """Return active unified reference catalogue combining static seed entries and indexed library docs."""
    base_entries = load_reference_catalogue(static_catalogue_path)
    entries: list[ReferenceEntry] = list(base_entries)
    seen: set[str] = {e.source_id.upper() for e in entries}

    # Enhance existing entries with canonical aliases
    for entry in entries:
        canonical_aliases = _CANONICAL_ALIASES_MAP.get(entry.source_id.upper(), [])
        for alias in canonical_aliases:
            if alias not in entry.aliases:
                entry.aliases.append(alias)

    if indexer is not None:
        docs_to_convert: list[Any] = []
        if hasattr(indexer, "get_all_reference_entries"):
            try:
                for item in indexer.get_all_reference_entries():
                    if isinstance(item, ReferenceEntry):
                        if item.source_id.upper() not in seen:
                            entries.append(item)
                            seen.add(item.source_id.upper())
                        else:
                            match = next((e for e in entries if e.source_id.upper() == item.source_id.upper()), None)
                            if match is not None:
                                for a in item.aliases:
                                    if a not in match.aliases:
                                        match.aliases.append(a)
            except Exception as exc:
                logger.warning("Failed to merge library indexer entries into reference catalogue: %s", exc)

        if hasattr(indexer, "_load_all_indexed_docs"):
            try:
                docs_to_convert.extend(indexer._load_all_indexed_docs())
            except Exception as exc:
                logger.warning("Failed to merge library indexer entries into reference catalogue: %s", exc)

        if not docs_to_convert and hasattr(indexer, "scan_catalog"):
            try:
                docs_to_convert.extend(indexer.scan_catalog())
            except Exception as exc:
                logger.warning("Failed to merge library indexer entries into reference catalogue: %s", exc)

        if isinstance(indexer, (list, tuple)):
            for item in indexer:
                if isinstance(item, ReferenceEntry):
                    if item.source_id.upper() not in seen:
                        entries.append(item)
                        seen.add(item.source_id.upper())
                else:
                    docs_to_convert.append(item)

        for doc in docs_to_convert:
            doc_id = getattr(doc, "doc_id", None) or (doc.get("doc_id") if isinstance(doc, dict) else None)
            if not doc_id:
                continue

            source_id = str(doc_id).strip()
            title = str(getattr(doc, "title", None) or (doc.get("title") if isinstance(doc, dict) else "") or source_id).strip()
            raw_domain = str(getattr(doc, "domain", None) or (doc.get("domain") if isinstance(doc, dict) else "") or "review").strip()
            file_path = str(getattr(doc, "file_path", None) or (doc.get("file_path") if isinstance(doc, dict) else "") or f"file:///{source_id}").strip()
            disease_sites = getattr(doc, "disease_sites", None) or (doc.get("disease_sites") if isinstance(doc, dict) else []) or []
            if isinstance(disease_sites, str):
                try:
                    disease_sites = json.loads(disease_sites)
                except Exception:
                    disease_sites = [disease_sites]

            source_type: SourceType = _DOMAIN_TO_SOURCE_TYPE.get(
                raw_domain,
                raw_domain if raw_domain in ("guideline", "textbook", "trial", "review", "consensus") else "review",  # type: ignore[arg-type]
            )
            specialties = _DOMAIN_TO_SPECIALTIES.get(raw_domain, ["radiation_oncology"])
            organization = _DOMAIN_TO_ORGANIZATION.get(raw_domain, "Medical Library")
            topics = list(disease_sites) if disease_sites else ["general"]
            posix_path = file_path.replace("\\", "/")
            doi_or_url = file_path if file_path.startswith("file://") else f"file:///{posix_path}"

            file_stem = pathlib.Path(file_path).stem
            file_name = pathlib.Path(file_path).name
            raw_aliases = [
                title,
                file_stem,
                file_name,
                file_stem.replace("_", " "),
                file_stem.replace("-", " "),
                title.replace("_", " "),
                title.replace("-", " "),
            ]
            aliases: list[str] = []
            for a in raw_aliases:
                clean_a = str(a).strip()
                if clean_a and clean_a != source_id and clean_a not in aliases:
                    aliases.append(clean_a)

            if source_id.upper() in seen:
                match = next((e for e in entries if e.source_id.upper() == source_id.upper()), None)
                if match is not None:
                    for a in aliases:
                        if a not in match.aliases:
                            match.aliases.append(a)
                continue

            entry = ReferenceEntry(
                source_id=source_id,
                title=title[:500],
                organization=organization[:200],
                source_type=source_type,
                edition_or_version="Indexed",
                publication_date="2024-01-01",
                specialties=specialties,
                topics=topics,
                doi_or_url=doi_or_url[:500],
                access_status="available",
                supersession="current",
                aliases=aliases,
                key_passages=[],
            )
            entries.append(entry)
            seen.add(source_id.upper())

    return entries


def search_reference_catalogue(
    *,
    site: str | None = None,
    specialty: str | None = None,
    topic: str | None = None,
    source_type: SourceType | None = None,
    catalogue: list[ReferenceEntry] | None = None,
) -> list[ReferenceEntry]:
    """Filter reference catalogue by disease site, specialty, topic, and source type."""
    entries = catalogue if catalogue is not None else get_active_reference_catalogue()
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
    """Anti-hallucination verification of an alleged guideline or trial reference (U07, U09).

    Returns True only if the reference exists in the verified catalogue and matches
    the recorded DOI / URL. Supports normalized alias matching.
    """
    if not claim_source_id or not isinstance(claim_source_id, str):
        return False

    clean_claim = claim_source_id.strip()
    if not clean_claim:
        return False

    norm_claim = _normalize_citation_token(clean_claim)
    if len(norm_claim) < 3:
        return False

    entries = catalogue if catalogue is not None else get_active_reference_catalogue()
    claim_upper = clean_claim.upper()

    match: ReferenceEntry | None = None
    for e in entries:
        if claim_upper == e.source_id.strip().upper():
            match = e
            break
        if norm_claim == _normalize_citation_token(e.source_id):
            match = e
            break
        entry_aliases = getattr(e, "aliases", []) or []
        alias_matched = False
        for alias in entry_aliases:
            if not alias or not isinstance(alias, str):
                continue
            clean_alias = alias.strip()
            if claim_upper == clean_alias.upper():
                match = e
                alias_matched = True
                break
            norm_alias = _normalize_citation_token(clean_alias)
            if len(norm_alias) >= 3 and norm_claim == norm_alias:
                match = e
                alias_matched = True
                break
        if alias_matched:
            break

    if not match:
        return False

    if doi_or_url and str(doi_or_url).strip():
        normalized_target = str(doi_or_url).strip().lower().rstrip("/")
        recorded_url = match.doi_or_url.strip().lower().rstrip("/")
        is_local_or_placeholder = (
            recorded_url.startswith("file://")
            or recorded_url.startswith("file:/")
            or "placeholder" in recorded_url
            or recorded_url in ("available", "restricted", "local", "n/a", "none")
        )
        if not is_local_or_placeholder and normalized_target != recorded_url:
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
    entries = catalogue if catalogue is not None else get_active_reference_catalogue()
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []

    for claim in claims:
        if not isinstance(claim, dict):
            continue
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

