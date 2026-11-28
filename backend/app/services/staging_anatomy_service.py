"""Staging, Anatomy & Contouring Guidelines Service.

Provides structured access to AJCC 8th/9th Edition TNM staging definitions,
anatomical lymph node station boundaries, and ICRU-83/consensus contouring margins.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Literal
from pydantic import BaseModel, Field

_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "evidence_catalogues" / "staging_anatomy_catalogue.json"
)

DiseaseSite = Literal[
    "Head & Neck",
    "Lung",
    "Breast",
    "Prostate",
    "GI",
    "GYN",
    "CNS",
    "General",
]


class StagingEntry(BaseModel):
    source_id: str
    title: str
    organization: str
    source_type: str
    disease_site: str
    doi_or_url: str
    edition_or_version: str
    key_innovations: list[str] = Field(default_factory=list)
    t_definitions: dict[str, str] = Field(default_factory=dict)
    n_definitions: dict[str, str] = Field(default_factory=dict)
    m_definitions: dict[str, str] = Field(default_factory=dict)
    stage_groups: dict[str, Any] = Field(default_factory=dict)
    levels: dict[str, Any] = Field(default_factory=dict)
    stations: dict[str, Any] = Field(default_factory=dict)
    nodal_groups: dict[str, Any] = Field(default_factory=dict)
    nodal_stations: dict[str, Any] = Field(default_factory=dict)
    volume_definitions: dict[str, str] = Field(default_factory=dict)
    expansion_rules: dict[str, str] = Field(default_factory=dict)
    key_passages: list[dict[str, str]] = Field(default_factory=list)


def load_staging_catalogue(path: pathlib.Path | None = None) -> list[dict[str, Any]]:
    """Load raw entries from the staging and anatomy catalogue."""
    target_path = path or _CATALOGUE_PATH
    if not target_path.is_file():
        return []
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        return data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def get_staging_by_site(disease_site: str) -> list[dict[str, Any]]:
    """Retrieve all staging and contouring catalogue entries for a given disease site."""
    clean_site = disease_site.strip().lower()
    entries = load_staging_catalogue()
    return [
        entry for entry in entries
        if entry.get("disease_site", "").strip().lower() == clean_site
    ]


def get_entry_by_source_id(source_id: str) -> dict[str, Any] | None:
    """Retrieve a single catalogue entry by unique source_id."""
    clean_id = source_id.strip().upper()
    for entry in load_staging_catalogue():
        if entry.get("source_id", "").strip().upper() == clean_id:
            return entry
    return None


def get_cervical_node_levels() -> dict[str, Any]:
    """Retrieve the DAHANCA/EORTC/RTOG consensus neck node level boundaries."""
    entry = get_entry_by_source_id("DAHANCA-EORTC-NECK-2014")
    return entry.get("levels", {}) if entry else {}


def get_thoracic_node_stations() -> dict[str, Any]:
    """Retrieve the IASLC / University of Michigan thoracic nodal stations."""
    entry = get_entry_by_source_id("IASLC-THORACIC-LN-2009")
    return entry.get("stations", {}) if entry else {}


def get_pelvic_node_groups() -> dict[str, Any]:
    """Retrieve the RTOG/ESTRO pelvic lymph node boundaries."""
    entry = get_entry_by_source_id("RTOG-PELVIC-LN-2007")
    return entry.get("nodal_groups", {}) if entry else {}


def get_target_volume_expansions() -> dict[str, str]:
    """Retrieve standard ICRU-83 / consensus target volume margin expansion rules."""
    entry = get_entry_by_source_id("ICRU-83-ASTRO-CONTOURING")
    return entry.get("expansion_rules", {}) if entry else {}


def get_elective_nodal_recommendations(disease_site: str, subsite: str | None = None) -> list[str]:
    """Get canonical elective nodal irradiation target recommendations by primary site."""
    site = disease_site.strip().lower()
    sub = (subsite or "").strip().lower()

    if "head" in site or "neck" in site:
        if "oral" in sub or "tongue" in sub or "floor" in sub:
            return ["Level Ia", "Level Ib", "Level IIa", "Level IIb", "Level III"]
        if "oropharynx" in sub or "tonsil" in sub or "base of tongue" in sub:
            return ["Level IIa", "Level IIb", "Level III", "Level IVa", "Level VIIa (Retropharyngeal)"]
        if "nasopharynx" in sub:
            return ["Level II", "Level III", "Level IVa", "Level IVb", "Level Va", "Level Vb", "Level Vc", "Level VIIa (Retropharyngeal)", "Level VIIb (Retro-styloid)"]
        if "larynx" in sub or "hypopharynx" in sub:
            return ["Level II", "Level III", "Level IVa", "Level VIb (pretracheal/paratracheal if subglottic or piriform apex)"]
        return ["Level II", "Level III", "Level IVa"]

    if "lung" in site:
        return ["Involved Field Nodal Irradiation (IFNI) to involved stations per PET-CT / EBUS; routine elective nodal irradiation (ENI) omitted to spare lung V20/esophagus"]

    if "prostate" in site:
        return ["Pelvic nodal irradiation (Common iliac, External iliac, Internal iliac, Presacral, Obturator) to 45-50.4 Gy for high/very-high risk or Roach score > 15%"]

    if "cervix" in site or "gyn" in site:
        return ["External iliac", "Internal iliac", "Obturator", "Presacral", "Common iliac", "+/- Para-aortic nodes if common iliac involvement or high risk"]

    if "rectum" in site or "rectal" in site:
        return ["Mesorectum (CTVA)", "Presacral nodes", "Internal iliac nodes", "+/- External iliac if T4 into anterior organs", "+/- Inguinal if invading anal canal/perianal skin"]

    if "breast" in site:
        return ["Axillary Level I-II (if node positive and ALND omitted)", "Axillary Level III / Supraclavicular fossa (Level IV)", "+/- Internal Mammary Nodes (IMN) for medial/central tumors or positive axilla"]

    return []
