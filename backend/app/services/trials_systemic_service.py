"""Landmark Trials and Systemic Therapy evidence service conforming to Requirement U07, U09.

Provides structured access to landmark clinical trial evidence (e.g., RTOG 91-11, RTOG 0522,
EORTC 22931 / RTOG 9501, PACIFIC, STAMPEDE, RAPIDO, CROSS, Stupp) and canonical systemic
chemotherapy / immunotherapy protocols (cisplatin, carboplatin/paclitaxel, durvalumab consolidation).
Supports specialist prompt injection and deterministic citation auditing.
"""
from __future__ import annotations

import json
import logging
import pathlib
from typing import Any

logger = logging.getLogger(__name__)

from app.services.reference_catalogue import ReferenceEntry, verify_citation

_EVIDENCE_CATALOGUES_DIR = pathlib.Path(__file__).resolve().parents[1] / "evidence_catalogues"
_TRIALS_FILE = _EVIDENCE_CATALOGUES_DIR / "landmark_trials.json"
_SYSTEMIC_FILE = _EVIDENCE_CATALOGUES_DIR / "systemic_protocols.json"

_CACHED_TRIALS: list[dict[str, Any]] | None = None
_CACHED_PROTOCOLS: list[dict[str, Any]] | None = None


def load_landmark_trials(force_reload: bool = False) -> list[dict[str, Any]]:
    """Load all landmark clinical trial entries from the catalog."""
    global _CACHED_TRIALS
    if _CACHED_TRIALS is not None and not force_reload:
        return _CACHED_TRIALS

    if not _TRIALS_FILE.is_file():
        return []

    try:
        data = json.loads(_TRIALS_FILE.read_text(encoding="utf-8"))
        _CACHED_TRIALS = data.get("trials", [])
        return _CACHED_TRIALS
    except (json.JSONDecodeError, OSError):
        return []


def load_systemic_protocols(force_reload: bool = False) -> list[dict[str, Any]]:
    """Load all standard systemic chemotherapy and immunotherapy protocols."""
    global _CACHED_PROTOCOLS
    if _CACHED_PROTOCOLS is not None and not force_reload:
        return _CACHED_PROTOCOLS

    if not _SYSTEMIC_FILE.is_file():
        return []

    try:
        data = json.loads(_SYSTEMIC_FILE.read_text(encoding="utf-8"))
        _CACHED_PROTOCOLS = data.get("protocols", [])
        return _CACHED_PROTOCOLS
    except (json.JSONDecodeError, OSError):
        return []


def get_trials_as_reference_entries() -> list[ReferenceEntry]:
    """Return all landmark trials validated as ReferenceEntry models."""
    trials = load_landmark_trials()
    entries: list[ReferenceEntry] = []
    for t in trials:
        try:
            entries.append(ReferenceEntry.model_validate(t))
        except Exception as exc:
            logger.warning("Skipping invalid landmark trial entry: %s", exc)
            continue
    return entries


def get_landmark_trials(
    disease_site: str | None = None,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """Filter landmark trials by disease site and/or clinical topic."""
    trials = load_landmark_trials()
    clean_site = disease_site.strip().lower() if disease_site else None
    clean_topic = topic.strip().lower() if topic else None

    results: list[dict[str, Any]] = []
    for trial in trials:
        if clean_site:
            trial_site = trial.get("disease_site", "").strip().lower()
            if clean_site not in trial_site and trial_site not in clean_site:
                continue

        if clean_topic:
            topics = [t.strip().lower() for t in trial.get("topics", [])]
            if clean_topic not in topics and not any(clean_topic in t for t in topics):
                continue

        results.append(trial)

    return results


def get_trial_by_source_id(source_id: str) -> dict[str, Any] | None:
    """Retrieve a landmark trial by exact or case-insensitive source ID."""
    trials = load_landmark_trials()
    norm = source_id.strip().upper()
    return next((t for t in trials if t.get("source_id", "").strip().upper() == norm), None)


def get_systemic_protocols(disease_site: str | None = None) -> list[dict[str, Any]]:
    """Filter systemic therapy protocols by disease site."""
    protocols = load_systemic_protocols()
    if not disease_site:
        return protocols

    clean_site = disease_site.strip().lower()
    return [
        p
        for p in protocols
        if clean_site in p.get("disease_site", "").strip().lower()
        or p.get("disease_site", "").strip().lower() in clean_site
    ]


def get_protocol_by_id(protocol_id: str) -> dict[str, Any] | None:
    """Retrieve a standard systemic protocol by unique protocol ID."""
    protocols = load_systemic_protocols()
    norm = protocol_id.strip().upper()
    return next((p for p in protocols if p.get("protocol_id", "").strip().upper() == norm), None)


def format_trials_context_for_specialist(
    disease_site: str,
    stage: str | None = None,
) -> str:
    """Format an evidence-dense landmark clinical trials context block for prompt injection."""
    matched_trials = get_landmark_trials(disease_site=disease_site)
    if not matched_trials:
        return ""

    lines = [
        f"### Landmark Clinical Trial Evidence ({disease_site})",
        "Deterministic citations for guideline concordance and claim verification:",
    ]

    for trial in matched_trials:
        source_id = trial.get("source_id", "")
        title = trial.get("title", "")
        level = trial.get("level_of_evidence", "")
        endpoints = trial.get("endpoints", {})
        recommendation = trial.get("clinical_recommendation", "")
        doi = trial.get("doi_or_url", "")

        lines.append(f"- **[{source_id}]** {title} ({level})")
        lines.append(f"  *Criteria*: {trial.get('stage_criteria', 'N/A')}")
        lines.append(f"  *Key Finding*: {recommendation}")
        lines.append(f"  *DOI/URL*: {doi}")

    return "\n".join(lines)


def format_systemic_context_for_specialist(disease_site: str) -> str:
    """Format canonical systemic chemotherapy and immunotherapy protocols for prompt injection."""
    matched_protocols = get_systemic_protocols(disease_site=disease_site)
    if not matched_protocols:
        return ""

    lines = [
        f"### Standard Systemic Therapy Protocols ({disease_site})",
        "Mandatory regimens, dosing, hydration, antiemetics, and organ thresholds:",
    ]

    for proto in matched_protocols:
        pid = proto.get("protocol_id", "")
        pname = proto.get("protocol_name", "")
        indication = proto.get("clinical_indication", "")
        components = proto.get("regimen_components", [])
        antiemetics = proto.get("antiemetic_protocol", {})
        eligibility = proto.get("eligibility_thresholds", {})
        linked = proto.get("landmark_evidence_link", [])

        lines.append(f"- **{pname}** (`{pid}`)")
        lines.append(f"  *Indication*: {indication}")

        comp_strs = []
        for c in components:
            if isinstance(c, dict):
                drug = c.get("drug", "")
                dose = c.get("dose", "")
                unit = c.get("unit", "")
                route = c.get("route", "")
                freq = c.get("frequency", "")
                comp_strs.append(f"{drug} {dose} {unit} ({route}, {freq})")
        if comp_strs:
            lines.append(f"  *Components*: {'; '.join(comp_strs)}")

        if eligibility:
            crcl = eligibility.get("creatinine_clearance", "N/A")
            anc = eligibility.get("absolute_neutrophil_count", "N/A")
            lines.append(f"  *Eligibility*: CrCl: {crcl} | ANC: {anc}")

        if antiemetics:
            risk = antiemetics.get("emetogenic_risk", "")
            reg = antiemetics.get("regimen", "")
            desc = f"{risk}: {reg}" if (risk and reg) else (reg or risk or "N/A")
            lines.append(f"  *Antiemetics*: {desc}")

        if linked:
            lines.append(f"  *Evidence Base*: {', '.join(linked)}")

    return "\n".join(lines)
