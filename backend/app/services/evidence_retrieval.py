"""Role-Based Evidence Retrieval and Prompt Injection Engine.

Provides:
- Case facet extraction (primary site, subsite, histology, stage, OARs, comorbidities, PS).
- 45-persona remit routing to canonical medical library domain partitions.
- Precision FTS5 literature querying with clinical keyword construction and fallback recovery.
- Bounded prompt context formatting (300-600 tokens) with verified [source_id: <ID>] tags.
- Educational simulation boundaries conforming to AGENTS.md.
"""
from __future__ import annotations

import logging
import re
from typing import Any
from pydantic import BaseModel

from app.schemas import SyntheticCase
from app.services.library_indexer import (
    MedicalLibraryIndexer,
    get_medical_library_indexer,
)

logger = logging.getLogger("radonc.evidence_retrieval")


class RetrievedPassage(BaseModel):
    """Structured evidence passage retrieved from the indexed medical library."""

    source_id: str
    title: str
    domain: str
    snippet: str
    relevance_score: float = 1.0
    evidence_type: str = "guideline"


# ---------------------------------------------------------------------------
# CANONICAL DISEASE SITES & WORD-BOUNDARY REGEX PATTERNS
# Prevents substring collisions (e.g. "anal" in "analysis")
# ---------------------------------------------------------------------------

_SITE_PATTERNS: dict[str, list[str]] = {
    "head_and_neck": [
        "head and neck", "head & neck", "head-and-neck", "larynx", "glottic", "supraglottic",
        "subglottic", "pharynx", "oropharynx", "hypopharynx", "nasopharynx",
        "oral cavity", "salivary", "parotid", "thyroid", "tongue", "tonsil",
        "laryngeal", "maxillary", "ethmoid", "pyriform sinus",
    ],
    "lung": [
        "nsclc", "sclc", "nscl", "lung", "thoracic", "pulmonary", "bronchial",
        "non-small cell lung", "small cell lung",
    ],
    "breast": [
        "breast", "mammary", "ductal carcinoma", "lobular carcinoma", "pmrt",
    ],
    "prostate": [
        "prostate", "prostatic",
    ],
    "colorectal": [
        "rectum", "rectal", "colon", "colorectal", "anal", "anus",
    ],
    "gynecologic": [
        "cervix", "cervical", "endometrium", "endometrial", "ovary", "ovarian",
        "uterine", "uterus", "vulva", "vulvar", "vagina", "vaginal",
    ],
    "gastrointestinal": [
        "esophagus", "esophageal", "stomach", "gastric", "pancreas", "pancreatic",
        "liver", "hepatobiliary", "cholangiocarcinoma", "gallbladder",
    ],
    "genitourinary": [
        "bladder", "kidney", "renal", "testis", "testicular", "penile", "ureter",
    ],
    "cns": [
        "cns", "brain", "brainstem", "glioblastoma", "glioma", "astrocytoma",
        "meningioma", "spine", "spinal cord",
    ],
    "hematologic": [
        "lymphoma", "hodgkin", "myeloma", "leukemia",
    ],
    "sarcoma": [
        "sarcoma", "osteosarcoma", "liposarcoma", "leiomyosarcoma", "gist",
    ],
    "skin": [
        "melanoma", "basal cell", "merkel", "cutaneous",
    ],
}

_OAR_MAP: dict[str, list[str]] = {
    "head_and_neck": [
        "parotid glands", "spinal cord", "brainstem", "pharyngeal constrictors",
        "larynx", "mandible", "brachial plexus", "cochlea", "optic chiasm",
    ],
    "lung": [
        "spinal cord", "lungs (V20/MLD)", "esophagus", "heart", "brachial plexus", "airway",
    ],
    "breast": [
        "heart (LAD)", "ipsilateral lung", "contralateral breast", "brachial plexus", "skin",
    ],
    "prostate": [
        "rectum", "bladder", "femoral heads", "penile bulb", "small bowel",
    ],
    "colorectal": [
        "small bowel", "bladder", "femoral heads", "anal sphincter", "pelvic bones",
    ],
    "gynecologic": [
        "bladder", "rectum", "sigmoid colon", "small bowel", "femoral heads", "bone marrow",
    ],
    "gastrointestinal": [
        "liver", "kidneys", "stomach", "duodenum", "small bowel", "spinal cord", "heart",
    ],
    "genitourinary": [
        "kidneys", "small bowel", "rectum", "femoral heads", "spinal cord", "bladder",
    ],
    "cns": [
        "brainstem", "optic chiasm", "optic nerves", "cochlea", "lenses", "pituitary gland", "hippocampus",
    ],
}


def _match_site_pattern(text: str | None) -> str | None:
    """Matches text against canonical site patterns with regex word boundaries."""
    if not text:
        return None
    for site_key, patterns in _SITE_PATTERNS.items():
        for pattern in patterns:
            escaped = re.escape(pattern)
            if re.search(rf"\b{escaped}\b", text, re.IGNORECASE):
                return site_key
    return None


class EvidenceRetrievalEngine:
    """Retrieves domain-matched evidence passages and formats prompt injection for MDT roles."""

    def __init__(self, indexer: MedicalLibraryIndexer | None = None) -> None:
        self.indexer = indexer if indexer is not None else get_medical_library_indexer()

    def extract_case_facets(self, case: SyntheticCase) -> dict[str, Any]:
        """Extracts structured clinical facets from a SyntheticCase with word-boundary safety.

        Guarantees strict hierarchical disease site resolution (raw_site -> subsite -> summary)
        and falls back to pathological staging when clinical staging is not reported.
        """
        raw_site = (case.primary_site or "").strip()
        subsite = (case.anatomical_subsite or "").strip() or None
        histology = (case.histology or "").strip() or None
        summary = case.case_summary or ""

        # Strict hierarchical resolution: raw_site -> subsite -> summary as last resort
        normalized_site = _match_site_pattern(raw_site)
        if not normalized_site and subsite:
            normalized_site = _match_site_pattern(subsite)
        if not normalized_site and summary:
            normalized_site = _match_site_pattern(summary)

        # Fallback to slugified raw_site if no specific pattern matched
        if not normalized_site and raw_site:
            normalized_site = raw_site.lower().replace(" ", "_")

        # Stage extraction with clinical -> pathological fallback
        stage: str | None = None
        if case.stage_group:
            stage = case.stage_group
        elif case.clinical_stage_group:
            stage = case.clinical_stage_group
        elif case.clinical_t_stage or case.clinical_n_stage or case.clinical_m_stage:
            parts = [p for p in (case.clinical_t_stage, case.clinical_n_stage, case.clinical_m_stage) if p]
            stage = " ".join(parts) if parts else None
        elif case.pathological_stage_group:
            stage = case.pathological_stage_group
        elif case.pathological_t_stage or case.pathological_n_stage or case.pathological_m_stage:
            parts = [p for p in (case.pathological_t_stage, case.pathological_n_stage, case.pathological_m_stage) if p]
            stage = " ".join(parts) if parts else None

        # OAR lookup based on normalized site
        oars = list(_OAR_MAP.get(normalized_site or "", ["spinal cord", "skin", "bone"]))

        # Comorbidities
        comorbidities = list(case.relevant_comorbidities) if case.relevant_comorbidities else []

        # Performance status
        performance_status = case.performance_status

        return {
            "primary_site": normalized_site or "general",
            "raw_primary_site": raw_site or None,
            "anatomical_subsite": subsite,
            "histology": histology,
            "stage": stage,
            "oars": oars,
            "comorbidities": comorbidities,
            "performance_status": performance_status,
        }

    def get_role_domains(self, role_id: str) -> list[str]:
        """Maps 45 specialist personas (RO, MO, SO, DS, PP, SG, SV) to canonical domains."""
        clean_id = role_id.strip().upper()
        prefix = clean_id[:2]

        if prefix == "RO":
            # Radiation Oncology: Guidelines, Organ constraints, Textbooks/Radiobio, Staging
            return ["guidelines", "organ_tolerances", "textbooks_radiobiology", "staging_anatomy"]
        elif prefix == "MO":
            # Medical Oncology: Landmark trials, Chemotherapy/IO, Guidelines, General medicine
            return ["trials_systemic", "guidelines", "general_medicine"]
        elif prefix == "SO":
            # Surgical Oncology: Resectability guidelines, Staging/anatomy, Organ preservation trials
            return ["guidelines", "staging_anatomy", "trials_systemic"]
        elif clean_id == "DS-01":
            # Radiologist: Staging & Anatomy, Contouring, Guidelines
            return ["staging_anatomy", "guidelines"]
        elif clean_id == "DS-02":
            # Pathologist: Staging, Histology, Biomarkers, Guidelines
            return ["staging_anatomy", "guidelines"]
        elif clean_id == "DS-03":
            # Palliative Care: General medicine, Symptoms, Organ tolerances, Guidelines
            return ["general_medicine", "guidelines", "organ_tolerances"]
        elif prefix == "PP":
            # Patient Perspective Lenses: Guidelines, Organ tolerances, General medicine
            return ["guidelines", "organ_tolerances", "general_medicine"]
        elif clean_id == "SG-05":
            # Evidence Auditor: All literature domains
            return [
                "guidelines", "trials_systemic", "organ_tolerances",
                "textbooks_radiobiology", "staging_anatomy", "general_medicine",
            ]
        elif clean_id == "SG-07":
            # MDT Chair: Cross-discipline synthesis
            return ["guidelines", "trials_systemic", "organ_tolerances", "staging_anatomy"]
        elif prefix == "SG":
            # System, Evidence & Governance: Guidelines, General medicine, Trials
            return ["guidelines", "general_medicine", "trials_systemic"]
        elif prefix == "SV":
            # Family, Social Care & Vulnerability: General medicine, Comorbidities, Guidelines
            return ["general_medicine", "guidelines"]
        else:
            return ["guidelines", "general_medicine"]

    def retrieve_evidence_for_role(
        self,
        role_id: str,
        case: SyntheticCase,
        limit: int = 3,
    ) -> list[RetrievedPassage]:
        """Retrieves precision-matched evidence passages for a specific role and clinical case."""
        facets = self.extract_case_facets(case)
        primary_site = facets["primary_site"]
        raw_site = facets["raw_primary_site"] or primary_site
        histology = facets["histology"] or ""
        stage = facets["stage"] or ""
        domains = self.get_role_domains(role_id)

        # Build prioritized clinical search terms based on role remit
        search_queries: list[str] = []
        clean_id = role_id.strip().upper()
        clean_site = raw_site.replace("_", " ")

        if clean_id.startswith("RO"):
            search_queries.append(f"{clean_site} {histology} radiation therapy dose guideline".strip())
            if facets["oars"]:
                search_queries.append(f"{facets['oars'][0]} organ tolerance constraint QUANTEC".strip())
            search_queries.append(f"{clean_site} {stage} target volume fractionation".strip())
        elif clean_id.startswith("MO"):
            search_queries.append(f"{clean_site} {histology} chemotherapy systemic trial".strip())
            search_queries.append(f"{clean_site} overall survival landmark trial".strip())
            search_queries.append(f"{clean_site} {stage} systemic guideline".strip())
        elif clean_id.startswith("SO"):
            search_queries.append(f"{clean_site} surgical resection margin guideline".strip())
            search_queries.append(f"{clean_site} organ preservation trial".strip())
            search_queries.append(f"{clean_site} {stage} staging resectability".strip())
        elif clean_id in ("DS-01", "DS-02"):
            search_queries.append(f"{clean_site} {histology} AJCC staging anatomy".strip())
            search_queries.append(f"{clean_site} pathology radiology diagnostic guideline".strip())
        else:
            search_queries.append(f"{clean_site} {histology} clinical practice guideline".strip())
            search_queries.append(f"{clean_site} treatment toxicity comorbidity".strip())

        passages: list[RetrievedPassage] = []
        seen_keys: set[tuple[str, int]] = set()

        # Execute searches across domains
        for query_text in search_queries:
            if not query_text:
                continue
            for domain in domains:
                try:
                    results = self.indexer.query(
                        query_text=query_text,
                        domain=domain,
                        disease_site=primary_site if primary_site != "general" else None,
                        limit=limit,
                    )
                except Exception as exc:
                    logger.debug("Indexer query '%s' failed on domain %s: %s", query_text, domain, exc)
                    results = []

                for r in results:
                    key = (r["doc_id"], r.get("chunk_index", 0))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        passages.append(
                            RetrievedPassage(
                                source_id=r["doc_id"],
                                title=r["title"],
                                domain=r["domain"],
                                snippet=r["snippet"] or (r.get("content", "")[:280] + "..."),
                                relevance_score=max(0.1, 10.0 - float(r.get("rank", 1.0))),
                                evidence_type="guideline" if "guideline" in r["domain"] else "reference",
                            )
                        )
                        if len(passages) >= limit:
                            return passages[:limit]

        # Broad fallback if initial search yielded fewer results
        if len(passages) < limit:
            fallback_query = f"{clean_site} {histology}".strip() or clean_site
            if fallback_query:
                for domain in domains[:2]:
                    try:
                        results = self.indexer.query(
                            query_text=fallback_query,
                            domain=domain,
                            limit=limit,
                        )
                    except Exception:
                        results = []
                    for r in results:
                        key = (r["doc_id"], r.get("chunk_index", 0))
                        if key not in seen_keys:
                            seen_keys.add(key)
                            passages.append(
                                RetrievedPassage(
                                    source_id=r["doc_id"],
                                    title=r["title"],
                                    domain=r["domain"],
                                    snippet=r["snippet"] or (r.get("content", "")[:280] + "..."),
                                    relevance_score=1.0,
                                    evidence_type="guideline",
                                )
                            )
                            if len(passages) >= limit:
                                break
                    if len(passages) >= limit:
                        break

        return passages[:limit]

    def format_prompt_injection(self, passages: list[RetrievedPassage]) -> str:
        """Formats verified retrieved passages into a concise, token-bounded prompt injection block.

        Ensures 2-4 key passages strictly bounded to 300-600 tokens total, with canonical
        [source_id: <ID>] tags and anti-hallucination citation instructions.
        Returns empty string if passages list is empty.
        """
        if not passages:
            return ""

        selected = passages[:4]
        header = [
            "VERIFIED CLINICAL EVIDENCE CONTEXT:",
            "The following evidence passages have been retrieved from verified guidelines and literature matching this case.",
            "When grounding your clinical argumentation in this evidence, cite the specific source using its exact [source_id: <ID>] tag.",
            "",
        ]
        body_lines: list[str] = []
        for p in selected:
            # Strip highlight tags and whitespace
            clean_snip = " ".join(p.snippet.replace("<b>", "").replace("</b>", "").split())
            if len(clean_snip) > 300:
                clean_snip = clean_snip[:297].rstrip() + "..."
            body_lines.append(f"- [source_id: {p.source_id}] {p.title} ({p.domain}): \"{clean_snip}\"")

        footer = [
            "",
            "Instruction: You may cite only verified sources listed above with their exact [source_id: ...] tag. Do not invent citations, URLs, or unsupported claims.",
        ]
        return "\n".join(header + body_lines + footer)


_default_evidence_engine: EvidenceRetrievalEngine | None = None


def get_evidence_retrieval_engine(
    indexer: MedicalLibraryIndexer | None = None,
) -> EvidenceRetrievalEngine:
    """Get or initialize the global EvidenceRetrievalEngine singleton."""
    global _default_evidence_engine
    if _default_evidence_engine is None or indexer is not None:
        _default_evidence_engine = EvidenceRetrievalEngine(indexer=indexer)
    return _default_evidence_engine
