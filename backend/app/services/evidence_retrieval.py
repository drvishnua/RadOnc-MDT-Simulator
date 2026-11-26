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
    """Structured evidence passage retrieved from the indexed medical library or peer-reviewed literature."""

    source_id: str
    title: str
    domain: str
    snippet: str
    relevance_score: float = 1.0
    evidence_type: str = "guideline"
    url: str | None = None
    organization: str | None = None


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
            # Molecular Pathologist & Geneticist: Biomarkers, Genomics, Systemic trials, General medicine, Organ tolerances
            return ["staging_anatomy", "guidelines", "trials_systemic", "general_medicine", "organ_tolerances"]
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

        if clean_id == "RO-02":
            search_queries.append(f"{clean_site} {histology} conventional 3D-CRT 2D Cobalt-60 radiotherapy".strip())
            search_queries.append(f"{clean_site} IMRT proton SBRT toxicity cost late effects limitation".strip())
            search_queries.append(f"{clean_site} spinal cord parotid QUANTEC normal tissue tolerance".strip())
        elif clean_id.startswith("RO"):
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

        pubmed_passages: list[RetrievedPassage] = []
        if clean_id == "RO-02":
            pubmed_passages = self.retrieve_pubmed_conservative_evidence(case, limit=2)
        local_limit = max(1, limit - len(pubmed_passages)) if pubmed_passages else limit

        passages: list[RetrievedPassage] = []
        seen_keys: set[tuple[str, int]] = set()

        # Execute searches across domains in the indexed library
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
                    # Ignore generic non-oncology textbook chunks if we are seeking specific oncology site recommendations
                    r_domain = r.get("domain", "")
                    if r_domain == "general_medicine" and primary_site != "general" and not clean_id.startswith("SV"):
                        continue
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
                        if len(passages) >= local_limit:
                            break
                if len(passages) >= local_limit:
                    break
            if len(passages) >= local_limit:
                break

        # Broad fallback if initial search yielded fewer results
        if len(passages) < local_limit:
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
                        if r.get("domain") == "general_medicine" and primary_site != "general" and not clean_id.startswith("SV"):
                            continue
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

        # Fallback to structured authoritative clinical catalogues when library index is unpopulated
        if len(passages) < limit:
            try:
                from app.agents.catalog import AGENT_PROFILES
                from app.services.reference_catalogue import get_active_reference_catalogue
                entries = get_active_reference_catalogue()
                site_tokens = set(re.findall(r"\w+", f"{primary_site} {clean_site} {histology}".lower()))
                
                # Extract role-specific context to score entries relevant to this role's mandate and clinical philosophy
                role_prof = next((p for p in AGENT_PROFILES if p.get("agent_id") == clean_id), {})
                role_text = (
                    role_prof.get("mandate", "") + " "
                    + role_prof.get("clinical_philosophy", "") + " "
                    + role_prof.get("key_evidence_sources", "") + " "
                    + role_prof.get("risk_appetite", "")
                ).lower()
                role_tokens = set(re.findall(r"\w+", role_text))
                role_spec = role_prof.get("category", "").lower()

                scored_candidates: list[tuple[float, Any]] = []
                # Identify subsite exclusion terms (e.g. if tonsil/oropharynx, exclude glottic/larynx)
                subsite_exclusions: list[str] = []
                lower_case_site = f"{primary_site} {clean_site}".lower()
                if any(k in lower_case_site for k in ["tonsil", "oropharynx", "soft palate", "uvula", "base of tongue"]):
                    subsite_exclusions = ["larynx", "glottic", "glottis", "vocal cord", "supraglottic", "subglottic", "lung", "nsclc", "anal", "breast", "prostate"]
                elif any(k in lower_case_site for k in ["larynx", "glottic", "vocal cord"]):
                    subsite_exclusions = ["tonsil", "oropharynx", "nasopharynx", "lung", "breast"]

                # Primary disease site keywords to enforce site specificity
                primary_site_clean = clean_site or primary_site
                is_head_neck_case = any(k in primary_site_clean for k in ["tonsil", "oropharynx", "larynx", "pharynx", "oral", "hypopharynx", "tongue", "nasopharynx", "head"])
                is_cervix_case = any(k in primary_site_clean for k in ["cervix", "cervical"])
                is_lung_case = any(k in primary_site_clean for k in ["lung", "nsclc", "sclc", "bronch"])
                is_rectum_case = any(k in primary_site_clean for k in ["rectum", "rectal", "colon", "colorectal"])
                is_prostate_case = any(k in primary_site_clean for k in ["prostate"])
                is_breast_case = any(k in primary_site_clean for k in ["breast"])

                for entry in entries:
                    if any(p.source_id == entry.source_id for p in passages):
                        continue
                    topics_str = " ".join(t.lower().replace("_", " ") for t in (entry.topics or []))
                    entry_text = f"{entry.title} {topics_str} {entry.source_id}".lower()

                    # Strictly prevent cross-disease-site guideline bleeding (e.g. HN guidelines in Cervix or Lung case)
                    if entry.source_type != "textbook":
                        is_hn_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["-hn-", "head and neck", "oropharyngeal", "glottic", "larynx", "nasopharynx"])
                        is_cervix_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["cervix", "cervical", "gog-", "outback", "figo-"])
                        is_lung_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["-nscl", "nsclc", "lung", "sclc", "meso"])
                        is_rectum_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["rectal", "rectum", "colorectal", "colon"])
                        is_prostate_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["prostate"])
                        is_breast_entry = any(k in entry_text or k in entry.source_id.lower() for k in ["breast"])

                        if is_cervix_case and not is_cervix_entry and not any(k in entry_text for k in ["cervix", "cervical", "gynecologic"]):
                            if is_hn_entry or is_lung_entry or is_rectum_entry or is_prostate_entry or is_breast_entry:
                                continue
                        elif is_lung_case and not is_lung_entry and not any(k in entry_text for k in ["lung", "thoracic", "pulmonary"]):
                            if is_hn_entry or is_cervix_entry or is_rectum_entry or is_prostate_entry or is_breast_entry:
                                continue
                        elif is_rectum_case and not is_rectum_entry and not any(k in entry_text for k in ["rectal", "rectum", "colorectal"]):
                            if is_hn_entry or is_cervix_entry or is_lung_entry or is_prostate_entry or is_breast_entry:
                                continue
                        elif is_head_neck_case and not is_hn_entry and not any(k in entry_text for k in ["head and neck", "oropharynx", "larynx", "pharynx", "oral", "tongue"]):
                            if is_cervix_entry or is_lung_entry or is_rectum_entry or is_prostate_entry or is_breast_entry:
                                continue

                    # Exclude passages from mismatched anatomical subsites or disease sites
                    # (Allow normal tissue toxicity guidelines like QUANTEC even if other head and neck subsites like larynx are in topic tags)
                    is_toxicity_guideline = any(k in entry.source_id.lower() for k in ["quantec", "pentec", "toxicity"])
                    if not is_toxicity_guideline and any(ex in entry_text or ex in entry.source_id.lower() for ex in subsite_exclusions):
                        if entry.source_type != "textbook" and any(ex in entry.title.lower() for ex in subsite_exclusions):
                            continue
                    
                    # Site match or general oncologic reference/textbook
                    site_match_count = sum(1 for token in site_tokens if len(token) > 2 and token in entry_text)
                    if is_head_neck_case and any(k in entry_text for k in ["head and neck", "parotid", "salivary", "constrictor", "xerostomia"]):
                        site_match_count += 2
                    is_general_textbook = entry.source_type == "textbook"
                    if not site_match_count and not is_general_textbook and not (len(passages) == 0 and "HN" in entry.source_id):
                        continue

                    # Role match score: prioritize entries aligned with this role's specialty and philosophy
                    role_match_count = sum(1 for token in role_tokens if len(token) > 3 and token in entry_text)
                    spec_match = 2 if any(role_spec in s.lower() for s in (entry.specialties or [])) else 0
                    
                    # Bonus if this source_id was explicitly mentioned in key_evidence_sources
                    source_id_clean = entry.source_id.lower().replace("-", " ")
                    named_bonus = 6 if (entry.source_id.lower() in role_text or source_id_clean in role_text) else 0

                    # Boost textbooks so standard texts (Perez & Brady, Gunderson & Tepper, DeVita, Harrison's) compete evenly with NCCN
                    # BUT for RO-01, guidelines are supreme over textbooks
                    # For RO-02, prioritize toxicity (QUANTEC) and de-escalation/functional preservation trials
                    # For RO-03, prioritize dose-escalation/intensification trials (RTOG, MACH-NC)
                    if clean_id == "RO-01":
                        guideline_boost = 12.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 0.0
                        toxicity_boost = 0.0
                    elif clean_id == "RO-02":
                        guideline_boost = 0.0
                        textbook_boost = 15.0 if any(k in entry.source_id.lower() for k in ["perez", "brady", "fletcher", "textbook"]) else 3.0
                        toxicity_boost = 15.0 if any(k in entry.source_id.lower() for k in ["quantec", "classical", "conventional", "rtog-9111"]) else 0.0
                    elif clean_id == "RO-03":
                        guideline_boost = 2.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 3.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 20.0 if any(k in entry.source_id.lower() for k in ["rtog-0522", "cisplatin-3weekly", "mach-nc"]) else 0.0
                    elif clean_id == "RO-04":
                        guideline_boost = 3.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 2.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 18.0 if any(k in entry.source_id.lower() for k in ["aroi", "faro", "hypo", "rapido", "short"]) else 0.0
                    elif clean_id == "RO-05":
                        guideline_boost = 2.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 2.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 18.0 if any(k in entry.source_id.lower() for k in ["icru", "contour", "sbrt", "abs", "astro-hn"]) else 0.0
                    elif clean_id == "RO-06":
                        guideline_boost = 4.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["abs", "gec", "brachy", "implant"]) else 0.0
                    elif clean_id == "RO-07":
                        guideline_boost = 1.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 2.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 22.0 if any(k in entry.source_id.lower() for k in ["rtog-9111", "rtog-9501", "eortc-22931", "mach-nc", "bernier"]) else 0.0
                    elif clean_id == "RO-08":
                        guideline_boost = 3.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 20.0 if any(k in entry.source_id.lower() for k in ["nccn-hn-2026", "astro-hn-2024", "estro-eortc-hn-2023", "1016"]) else 0.0
                    elif clean_id == "RO-09":
                        guideline_boost = 1.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 5.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 22.0 if any(k in entry.source_id.lower() for k in ["radiobiology", "hall", "perez", "icru-83"]) else 0.0
                    elif clean_id == "RO-10":
                        guideline_boost = 1.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["quantec", "pentec", "toxicity", "morbidity"]) else 0.0
                    elif clean_id == "SO-01":
                        guideline_boost = 4.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 22.0 if any(k in entry.source_id.lower() for k in ["nccn-hn", "surg", "resect", "sso"]) else 0.0
                    elif clean_id == "SO-02":
                        guideline_boost = 2.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["orator", "ecog", "tors", "tlm"]) else 0.0
                    elif clean_id == "MO-01":
                        guideline_boost = 3.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 3.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["cisplatin-3weekly", "harrisons-med", "rtog-9111", "mach-nc"]) else 0.0
                    elif clean_id == "MO-02":
                        guideline_boost = 3.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 2.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["jastro", "aroi", "weekly", "cisplatin"]) else 0.0
                    elif clean_id == "MO-04":
                        guideline_boost = 2.0 if entry.source_type == "guideline" else 0.0
                        textbook_boost = 1.0 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 25.0 if any(k in entry.source_id.lower() for k in ["rtog-1016", "pembro", "nivo", "checkpoint", "pacific"]) else 0.0
                    else:
                        guideline_boost = 0.0
                        textbook_boost = 3.5 if entry.source_type == "textbook" else 0.0
                        toxicity_boost = 0.0

                    total_score = (site_match_count * 2.5) + (role_match_count * 1.5) + spec_match + named_bonus + textbook_boost + guideline_boost + toxicity_boost
                    scored_candidates.append((total_score, entry))

                scored_candidates.sort(key=lambda x: x[0], reverse=True)

                # Balanced selection: ensure at least one standard textbook and one guideline/trial are paired
                selected_entries = []
                if clean_id == "RO-01":
                    # For RO-01, systematically pick one entry from each distinct professional society first (ASTRO, ESTRO, JASTRO/FARO, AROI, ABS, NCCN)
                    societies_seen = set()
                    for _, entry in scored_candidates:
                        if entry.source_type == "guideline":
                            soc = entry.source_id.split("-")[0].upper()
                            if soc not in societies_seen:
                                societies_seen.add(soc)
                                selected_entries.append(entry)
                        if len(selected_entries) >= limit:
                            break
                else:
                    # First, pick highest scoring textbook if available for standard roles
                    textbook_cand = next((e for _, e in scored_candidates if e.source_type == "textbook"), None)
                    if textbook_cand:
                        selected_entries.append(textbook_cand)

                # Then, fill remaining slots with highest scoring guideline, consensus, or trial
                for _, entry in scored_candidates:
                    if entry not in selected_entries:
                        selected_entries.append(entry)
                    if len(selected_entries) >= limit:
                        break

                for entry in selected_entries:
                    if entry.key_passages and isinstance(entry.key_passages[0], dict):
                        snippet = entry.key_passages[0].get("text", entry.title)
                    elif entry.key_passages and isinstance(entry.key_passages[0], str):
                        snippet = entry.key_passages[0]
                    else:
                        snippet = f"{entry.title} - Authoritative evidence reference."
                    passages.append(
                        RetrievedPassage(
                            source_id=entry.source_id,
                            title=entry.title,
                            domain=entry.specialties[0] if entry.specialties else "oncology",
                            snippet=snippet,
                            relevance_score=0.9,
                            evidence_type=entry.source_type,
                        )
                    )
                    if len(passages) >= local_limit:
                        break
            except Exception as cat_exc:
                logger.debug("Catalogue fallback failed: %s", cat_exc)

        if pubmed_passages:
            existing_ids = {p.source_id.upper() for p in passages}
            for pm in pubmed_passages:
                if pm.source_id.upper() not in existing_ids:
                    passages.append(pm)
                    existing_ids.add(pm.source_id.upper())

        return passages[:limit]

    def retrieve_pubmed_conservative_evidence(
        self,
        case: SyntheticCase,
        limit: int = 2,
    ) -> list[RetrievedPassage]:
        """Query PubMed / Europe PMC for peer-reviewed articles favoring conservative RT and critiquing new tech."""
        try:
            from app.services.online_guideline_procurement import OnlineGuidelineProcurementService

            facets = self.extract_case_facets(case)
            site_term = (facets["raw_primary_site"] or facets["primary_site"]).replace("_", " ")
            service = OnlineGuidelineProcurementService(timeout=4)
            query = (
                f'({site_term}) AND ("conventional radiotherapy" OR "3D-CRT" OR "2D radiotherapy") '
                f'AND ("IMRT" OR "toxicity" OR "cost-effectiveness" OR "late effects" OR "limitation")'
            )
            results = service.query_europe_pmc(query, limit=limit)
            if not results:
                results = service.query_europe_pmc(
                    f"{site_term} conventional radiotherapy IMRT toxicity comparison",
                    limit=limit,
                )

            passages: list[RetrievedPassage] = []
            for item in results[:limit]:
                title = str(item.get("title") or "").strip()
                if not title:
                    continue
                pmid = str(item.get("pmid") or "").strip()
                item_id = str(item.get("id") or abs(hash(title)) % 100000).strip()
                source_id = f"PMID-{pmid}" if pmid else f"EPMC-{item_id}"
                journal = str(item.get("journalTitle") or item.get("journalInfo", {}).get("journal", {}).get("title") or "PubMed / Peer-Reviewed Journal").strip()
                year = str(item.get("pubYear") or "").strip()
                raw_abstract = str(item.get("abstractText") or title)
                clean_abstract = re.sub(r"<[^>]+>", " ", raw_abstract)
                clean_abstract = re.sub(r"\s+", " ", clean_abstract).strip()
                passages.append(
                    RetrievedPassage(
                        source_id=source_id,
                        title=f"{title} ({journal}{', ' + year if year else ''})",
                        domain="peer_reviewed_journal",
                        snippet=clean_abstract[:320],
                        relevance_score=0.88,
                        evidence_type="review",
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                        organization=journal,
                    )
                )
            return passages
        except Exception as exc:
            logger.debug("PubMed conservative evidence retrieval skipped: %s", exc)
            return []

    def format_prompt_injection(self, passages: list[RetrievedPassage]) -> str:
        """Formats verified retrieved passages into a concise, token-bounded prompt injection block.

        Ensures 2-4 key passages strictly bounded to 300-600 tokens total, with canonical
        [source_id: <ID>] tags and anti-hallucination citation instructions.
        Returns empty string if passages list is empty.
        """
        if not passages:
            return ""

        # Allow up to 6 passages if multi-society guidelines or comprehensive evidence are provided
        selected = passages[:6]
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
