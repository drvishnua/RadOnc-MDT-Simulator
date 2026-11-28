"""Pre-MDT Clinical & Imaging Staging Agent (STG-00).

Runs deterministically before the 49-role MDT simulation begins:
1. When no staging is provided, derives provisional clinical T/N/M (using Nx/Mx when
   nodal or metastatic imaging is not documented—never silently inventing N0).
2. When staging IS provided, checks whether provided T, N, M, and stage group match
   the documented clinical and imaging findings, flagging any discrepancies.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from app.schemas import SyntheticCase
from app.services.staging_anatomy_service import load_staging_catalogue
from app.services.staging_engine import derive_or_verify_staging


class PreMDTStagingAssessment(BaseModel):
    """Structured output of the Pre-MDT Staging Agent (STG-00)."""

    agent_id: str = "STG-00"
    agent_name: str = "Pre-MDT Clinical & Imaging Staging Agent"
    staging_locked: bool = True
    mode: Literal[
        "provisional_derived",
        "verified_concordant",
        "discrepancy_detected",
        "insufficient_staging_data",
    ]
    applicable_system: str
    staging_reference_ids: list[str] = Field(default_factory=list)
    staging_rules_applied: list[str] = Field(default_factory=list)
    provided_staging: dict[str, str | None] = Field(default_factory=dict)
    provisional_tnm: dict[str, str | None] = Field(default_factory=dict)
    provisional_stage_label: str
    clinical_findings_used: list[str] = Field(default_factory=list)
    discrepancies: list[str] = Field(default_factory=list)
    correlation_notes: list[str] = Field(default_factory=list)
    missing_for_complete_staging: list[str] = Field(default_factory=list)
    summary: str
    safety_boundary: str = "educational_simulation_only"


def _match_staging_catalogue_rules(
    case: SyntheticCase,
    applicable_system: str,
    t_tok: str,
    n_tok: str,
    m_tok: str,
) -> tuple[list[str], list[str]]:
    """Select exact AJCC/UICC/FIGO reference IDs and rules applied from staging_anatomy_catalogue."""
    entries = load_staging_catalogue()
    by_id = {str(e.get("source_id", "")).upper(): e for e in entries}
    ref_ids: list[str] = []
    rules: list[str] = []

    gen = by_id.get("UICC-AJCC-TNM-GENERAL-RULES")
    if gen:
        ref_ids.append(gen["source_id"])
        for rule in (gen.get("key_innovations") or [])[:2]:
            rules.append(str(rule))

    site = (case.primary_site or "").lower()
    sys_lower = applicable_system.lower()
    site_id = None
    if "cervix" in site or "figo" in sys_lower:
        site_id = "FIGO-2023-ENDOMETRIUM" if "endometri" in site else "FIGO-2018-AJCC-CERVIX"
    elif "hpv/p16-positive" in sys_lower:
        site_id = "AJCC-8TH-HPV-OROPHARYNX"
    elif any(k in site for k in ["oropharynx", "tonsil", "hypopharynx"]):
        site_id = "AJCC-8TH-NONHPV-OROPHARYNX"
    elif "nasopharynx" in site:
        site_id = "AJCC-8TH-NASOPHARYNX"
    elif "larynx" in site or "glott" in site:
        site_id = "AJCC-8TH-LARYNX"
    elif any(k in site for k in ["oral", "tongue", "buccal"]):
        site_id = "AJCC-8TH-ORAL-CAVITY"
    elif any(k in site for k in ["lung", "nsclc", "sclc"]):
        site_id = "AJCC-8TH-9TH-NSCLC"
    elif "breast" in site:
        site_id = "AJCC-8TH-BREAST"
    elif "prostate" in site:
        site_id = "AJCC-8TH-PROSTATE"
    elif any(k in site for k in ["rectum", "rectal", "colon", "colorectal"]):
        site_id = "AJCC-8TH-COLORECTAL"
    elif "esophag" in site:
        site_id = "AJCC-8TH-ESOPHAGUS"

    site_entry = by_id.get(site_id) if site_id else None
    if site_entry:
        ref_ids.append(site_entry["source_id"])
        t_defs = site_entry.get("t_definitions") or {}
        n_defs = site_entry.get("n_definitions") or {}
        m_defs = site_entry.get("m_definitions") or {}
        if t_tok in t_defs:
            rules.append(f"{t_tok}: {t_defs[t_tok]}")
        if n_tok in n_defs:
            rules.append(f"{n_tok}: {n_defs[n_tok]}")
        if m_tok in m_defs:
            rules.append(f"{m_tok}: {m_defs[m_tok]}")

    return ref_ids, rules


def run_pre_mdt_staging_agent(case: SyntheticCase) -> PreMDTStagingAssessment:
    """Derive provisional staging or verify provided staging against clinical and imaging findings."""
    raw = derive_or_verify_staging(case)

    provided_t = case.clinical_t_stage or None
    provided_n = case.clinical_n_stage or None
    provided_m = case.clinical_m_stage or None
    provided_group = case.stage_group or None
    has_provided = any([provided_t, provided_n, provided_m, provided_group])

    derived_t = raw.get("derived_t_stage")
    derived_n = raw.get("derived_n_stage")
    derived_m = raw.get("derived_m_stage")
    derived_group = raw.get("derived_stage_group")
    discrepancies: list[str] = list(raw.get("discrepancies") or [])
    correlation_notes: list[str] = list(raw.get("correlation_notes") or [])

    t_tok = derived_t or "Tx"
    n_tok = derived_n or "Nx"
    m_tok = derived_m or "Mx"
    group_suffix = f" ({derived_group})" if derived_group else ""
    provisional_stage_label = f"c{t_tok} {n_tok} {m_tok}{group_suffix}"

    findings: list[str] = []
    if raw.get("extracted_tumor_size_cm") is not None:
        findings.append(f"Primary tumor dimension documented: {raw['extracted_tumor_size_cm']} cm.")
    node_details = raw.get("extracted_node_details") or {}
    if derived_n:
        findings.append(
            f"Nodal assessment: {node_details.get('description', 'documented')} -> {derived_n}."
        )
    if derived_m:
        findings.append(f"Metastatic workup: {derived_m}.")
    if case.imaging_summary:
        findings.append(f"Imaging summary: {case.imaging_summary.strip()}")

    missing: list[str] = []
    if not derived_t:
        missing.append("Primary tumor dimension or local anatomical extent (Tx).")
    if not derived_n:
        missing.append("Neck/regional nodal imaging or examination (Nx — do not assume N0).")
    if not derived_m:
        missing.append("Distant metastatic workup (Mx — do not assume M0).")
    if raw.get("hpv_p16_status") == "unknown" and "oropharynx" in (case.primary_site or "").lower():
        missing.append("p16/HPV biomarker status for AJCC 8th Edition oropharyngeal staging.")

    if has_provided and discrepancies:
        mode: Literal[
            "provisional_derived",
            "verified_concordant",
            "discrepancy_detected",
            "insufficient_staging_data",
        ] = "discrepancy_detected"
        summary = (
            f"Provided staging does not fully match clinical and imaging findings: {discrepancies[0]} "
            f"Provisional imaging-correlated staging is {provisional_stage_label} under {raw.get('applicable_system', 'AJCC 8th Edition')}."
        )
    elif has_provided:
        mode = "verified_concordant"
        summary = (
            f"Provided staging is concordant with documented clinical and imaging findings ({provisional_stage_label} "
            f"under {raw.get('applicable_system', 'AJCC 8th Edition')}). "
            f"{'All core T/N/M components are documented.' if not missing else 'Remaining gaps: ' + missing[0]}"
        )
    elif derived_t or derived_n or derived_m:
        mode = "provisional_derived"
        summary = (
            f"No formal staging was supplied; provisional pre-MDT staging derived from clinical and imaging findings is "
            f"{provisional_stage_label} ({raw.get('applicable_system', 'AJCC 8th Edition')}). "
            f"{'Unreported components remain Nx/Mx and must not be assumed negative.' if missing else 'All core components were derived from supplied findings.'}"
        )
    else:
        mode = "insufficient_staging_data"
        summary = (
            "Insufficient clinical and imaging details were supplied to derive T, N, or M staging. "
            "All specialists must treat staging as Tx Nx Mx rather than assuming early-stage or node-negative disease."
        )

    applicable_system = str(raw.get("applicable_system") or "AJCC 8th Edition")
    ref_ids, rules_applied = _match_staging_catalogue_rules(
        case, applicable_system, t_tok, n_tok, m_tok
    )

    return PreMDTStagingAssessment(
        staging_locked=True,
        mode=mode,
        applicable_system=applicable_system,
        staging_reference_ids=ref_ids,
        staging_rules_applied=rules_applied,
        provided_staging={
            "clinical_t": provided_t,
            "clinical_n": provided_n,
            "clinical_m": provided_m,
            "stage_group": provided_group,
        },
        provisional_tnm={
            "t": derived_t,
            "n": derived_n,
            "m": derived_m,
            "stage_group": derived_group,
        },
        provisional_stage_label=provisional_stage_label,
        clinical_findings_used=findings,
        discrepancies=discrepancies,
        correlation_notes=correlation_notes,
        missing_for_complete_staging=missing,
        summary=summary,
    )
