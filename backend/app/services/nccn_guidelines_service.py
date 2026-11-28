"""NCCN Guidelines Evidence Service.

Provides deterministic, structured access to all 67 NCCN Clinical Practice Guidelines in Oncology,
stage-specific treatment algorithms, Category 1 and 2A recommendations, concurrent systemic therapy
indications, and radiation therapy principles.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any
from pydantic import BaseModel, Field

_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "evidence_catalogues" / "nccn_guidelines_catalogue.json"
)
_DOCS_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[3] / "docs" / "nccn_guidelines_catalogue_v1.json"
)


class StageAlgorithm(BaseModel):
    """Stage-specific clinical decision algorithm."""

    stage: str
    pathway: str


class RadiationPrinciples(BaseModel):
    """Radiation therapy prescription, fractionation, and OAR constraint definitions."""

    technique: str = ""
    definitive_doses: str = ""
    sabr_doses: str | None = None
    postoperative_doses: str | None = None
    preoperative_doses: str | None = None
    long_course_doses: str | None = None
    short_course_doses: str | None = None
    wbi_doses: str | None = None
    pmrt_doses: str | None = None
    ebrt_doses: str | None = None
    brachytherapy_doses: str | None = None
    salvage_doses: str | None = None
    target_volumes: str | None = None
    normal_tissue_constraints: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class NccnGuidelineEntry(BaseModel):
    """Structured NCCN guideline metadata and clinical algorithms."""

    source_id: str = Field(min_length=3, max_length=100)
    title: str = Field(min_length=5, max_length=500)
    disease_site: str
    version: str
    date: str
    url: str
    organization: str = "National Comprehensive Cancer Network"
    source_type: str = "guideline"
    jurisdiction: str = "USA/International"
    specialties: list[str] = Field(default_factory=lambda: ["radiation_oncology", "medical_oncology", "surgical_oncology"])
    topics: list[str] = Field(default_factory=list)
    histologies: list[str] = Field(default_factory=list)
    subsites: list[str] = Field(default_factory=list)
    stage_algorithms: list[StageAlgorithm] = Field(default_factory=list)
    category_1_recommendations: list[str] = Field(default_factory=list)
    category_2a_recommendations: list[str] = Field(default_factory=list)
    concurrent_systemic_indications: str = ""
    radiation_therapy_principles: RadiationPrinciples = Field(default_factory=RadiationPrinciples)
    key_passages: list[dict[str, str]] = Field(default_factory=list)
    filename: str | None = None
    num_pages: int | None = None
    key_outline_sections: list[str] = Field(default_factory=list)


def load_nccn_catalogue(path: pathlib.Path | None = None) -> list[NccnGuidelineEntry]:
    """Load and parse NCCN guideline entries from authoritative JSON catalogue."""
    target_path = path or _CATALOGUE_PATH
    if not target_path.is_file():
        # Fallback to docs catalogue if backend copy not found
        if _DOCS_CATALOGUE_PATH.is_file():
            target_path = _DOCS_CATALOGUE_PATH
        else:
            return []
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        raw_entries = data.get("entries") or []
        return [NccnGuidelineEntry.model_validate(item) for item in raw_entries]
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def get_guideline_by_id(
    source_id: str,
    catalogue: list[NccnGuidelineEntry] | None = None,
) -> NccnGuidelineEntry | None:
    """Retrieve an NCCN guideline entry by its exact source ID (case-insensitive)."""
    entries = catalogue if catalogue is not None else load_nccn_catalogue()
    norm_id = source_id.strip().upper()
    return next((e for e in entries if e.source_id.strip().upper() == norm_id), None)


def search_nccn_guidelines(
    *,
    disease_site: str | None = None,
    histology: str | None = None,
    query: str | None = None,
    catalogue: list[NccnGuidelineEntry] | None = None,
) -> list[NccnGuidelineEntry]:
    """Search and filter NCCN guidelines by disease site, histology, or keyword."""
    entries = catalogue if catalogue is not None else load_nccn_catalogue()
    results: list[NccnGuidelineEntry] = []

    clean_site = disease_site.strip().lower() if disease_site else None
    clean_hist = histology.strip().lower() if histology else None
    clean_query = query.strip().lower() if query else None

    for entry in entries:
        if clean_site:
            entry_site = entry.disease_site.strip().lower()
            if clean_site not in entry_site and entry_site not in clean_site:
                continue

        if clean_hist:
            hist_match = any(clean_hist in h.lower() for h in entry.histologies)
            if not hist_match and clean_hist not in entry.title.lower():
                continue

        if clean_query:
            query_match = (
                clean_query in entry.title.lower()
                or clean_query in entry.source_id.lower()
                or any(clean_query in t.lower() for t in entry.topics)
                or any(clean_query in s.lower() for s in entry.subsites)
                or any(clean_query in a.stage.lower() for a in entry.stage_algorithms)
            )
            if not query_match:
                continue

        results.append(entry)

    return results


def get_stage_recommendations(
    disease_site: str,
    stage_query: str,
    catalogue: list[NccnGuidelineEntry] | None = None,
) -> dict[str, Any]:
    """Retrieve matched stage algorithms, Category 1/2A recommendations, and RT principles."""
    entries = catalogue if catalogue is not None else load_nccn_catalogue()
    matched_guidelines = search_nccn_guidelines(disease_site=disease_site, catalogue=entries)
    if not matched_guidelines:
        return {"error": f"No guideline found for disease site: {disease_site}", "matched": False}

    primary_guideline = matched_guidelines[0]
    clean_stage = stage_query.strip().lower()

    matched_algorithms = [
        alg for alg in primary_guideline.stage_algorithms
        if clean_stage in alg.stage.lower() or any(term in alg.stage.lower() for term in clean_stage.split())
    ]

    return {
        "matched": True,
        "source_id": primary_guideline.source_id,
        "title": primary_guideline.title,
        "disease_site": primary_guideline.disease_site,
        "version": primary_guideline.version,
        "url": primary_guideline.url,
        "stage_query": stage_query,
        "matched_algorithms": matched_algorithms or primary_guideline.stage_algorithms[:2],
        "category_1_recommendations": primary_guideline.category_1_recommendations,
        "category_2a_recommendations": primary_guideline.category_2a_recommendations,
        "concurrent_systemic_indications": primary_guideline.concurrent_systemic_indications,
        "radiation_therapy_principles": primary_guideline.radiation_therapy_principles.model_dump(),
        "key_passages": primary_guideline.key_passages,
    }


def verify_nccn_citation(
    source_id: str,
    catalogue: list[NccnGuidelineEntry] | None = None,
) -> bool:
    """Anti-hallucination verification of an alleged NCCN guideline reference."""
    entries = catalogue if catalogue is not None else load_nccn_catalogue()
    norm_id = source_id.strip().upper()
    return any(e.source_id.strip().upper() == norm_id for e in entries)


def format_nccn_specialist_context(
    *,
    disease_site: str,
    stage: str | None = None,
    role_id: str | None = None,
    catalogue: list[NccnGuidelineEntry] | None = None,
) -> str:
    """Format structured NCCN evidence context for prompt injection into MDT specialist agents."""
    guidelines = search_nccn_guidelines(disease_site=disease_site, catalogue=catalogue)
    if not guidelines:
        return f"[EVIDENCE GROUNDING - NCCN GUIDELINES: No guideline found matching disease site '{disease_site}']"

    g = guidelines[0]
    lines = [
        f"### EVIDENCE GROUNDING — NCCN CLINICAL PRACTICE GUIDELINE ({g.source_id})",
        f"**Source**: {g.title} ({g.version}, {g.date})",
        f"**Official Reference**: {g.url}",
        "**Legal Notice**: Educational simulation only; not a clinical treatment instruction.",
        "",
        "**Category 1 Evidence-Based Recommendations**:",
    ]
    for c1 in g.category_1_recommendations:
        lines.append(f"- {c1}")

    lines.append("")
    lines.append(f"**Concurrent Systemic Therapy Indications vs RT Alone**:\n{g.concurrent_systemic_indications}")

    rt = g.radiation_therapy_principles
    if rt.technique or rt.definitive_doses:
        lines.append("")
        lines.append("**Radiation Therapy Principles & Target Dosing**:")
        if rt.technique:
            lines.append(f"- Technique: {rt.technique}")
        if rt.definitive_doses:
            lines.append(f"- Definitive Doses: {rt.definitive_doses}")
        if rt.sabr_doses:
            lines.append(f"- SABR Doses: {rt.sabr_doses}")
        if rt.postoperative_doses:
            lines.append(f"- Postoperative Doses: {rt.postoperative_doses}")
        if rt.normal_tissue_constraints:
            lines.append("- Critical Normal Tissue Constraints:")
            for oar, constr in rt.normal_tissue_constraints.items():
                lines.append(f"  * {oar.replace('_', ' ').title()}: {constr}")

    if stage:
        matched_algs = [
            a for a in g.stage_algorithms
            if stage.lower() in a.stage.lower() or any(w in a.stage.lower() for w in stage.lower().split())
        ]
        if matched_algs:
            lines.append("")
            lines.append(f"**Stage-Specific Algorithm for '{stage}'**:")
            for ma in matched_algs:
                lines.append(f"- Stage '{ma.stage}': {ma.pathway}")

    return "\n".join(lines)
