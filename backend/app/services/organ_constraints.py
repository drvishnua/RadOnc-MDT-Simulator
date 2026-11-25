"""Organ constraints and normal tissue toxicity service conforming to QUANTEC and PENTEC standards.

Provides deterministic, structured access to normal tissue dose-volume limits,
fractionation-specific tolerances, and RTOG/EORTC toxicity scoring criteria.
Supplies exact numerical constraints to Radiation Oncologist, Dosimetrist, and Medical Physicist roles.
"""
from __future__ import annotations

import json
import pathlib
from typing import Literal
from pydantic import BaseModel, Field

FractionationType = Literal["conventional", "stereotactic_single_fx", "hypofractionated_sbrt", "pediatric"]
RiskLevel = Literal["standard_safe", "acceptable_risk", "high_risk"]

_DEFAULT_CATALOGUE_PATH = (
    pathlib.Path(__file__).resolve().parents[3] / "docs" / "organ_constraints_catalogue_v1.json"
)


class OrganConstraint(BaseModel):
    """Normal tissue dose-volume limit model."""

    id: str = Field(min_length=3, max_length=100)
    source_id: str = Field(min_length=2, max_length=80)
    anatomical_site: str = Field(min_length=2, max_length=100)
    organ: str = Field(min_length=2, max_length=100)
    volume_spec: str = Field(min_length=2, max_length=200)
    fractionation_type: FractionationType
    fractions: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=2, max_length=200)
    metric: str = Field(min_length=1, max_length=50)
    limit_value: float
    unit: str = Field(min_length=1, max_length=20)
    operator: str = Field(min_length=1, max_length=10)
    risk_rate_percent: str = Field(min_length=1, max_length=50)
    risk_level: RiskLevel = "standard_safe"
    notes: str = Field(default="")
    target_specialists: list[str] = Field(default_factory=list)
    pediatric_age_group: str | None = None


def load_organ_constraints(path: pathlib.Path | None = None) -> list[OrganConstraint]:
    """Load and parse organ constraints from the authoritative JSON catalogue."""
    target_path = path or _DEFAULT_CATALOGUE_PATH
    if not target_path.is_file():
        return []
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        raw_constraints = data.get("constraints") or []
        return [OrganConstraint.model_validate(item) for item in raw_constraints]
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def get_constraints_for_site(
    site: str,
    fractionation_type: FractionationType | None = None,
    is_pediatric: bool = False,
    catalogue: list[OrganConstraint] | None = None,
) -> list[OrganConstraint]:
    """Filter constraints by anatomical site and fractionation type."""
    items = catalogue if catalogue is not None else load_organ_constraints()
    clean_site = site.strip().lower()

    # Map colloquial or cancer disease site terms to anatomical site
    site_map = {
        "head and neck": "Head and Neck",
        "head & neck": "Head and Neck",
        "h&n": "Head and Neck",
        "larynx": "Head and Neck",
        "glottic": "Head and Neck",
        "oropharynx": "Head and Neck",
        "oral cavity": "Head and Neck",
        "nasopharynx": "Head and Neck",
        "cns": "CNS",
        "brain": "CNS",
        "spine": "CNS",
        "spinal cord": "CNS",
        "glioblastoma": "CNS",
        "meningioma": "CNS",
        "lung": "Thorax",
        "thorax": "Thorax",
        "chest": "Thorax",
        "esophagus": "Thorax",
        "breast": "Thorax",
        "gi": "Abdomen",
        "abdomen": "Abdomen",
        "liver": "Abdomen",
        "pancreas": "Abdomen",
        "stomach": "Abdomen",
        "prostate": "Pelvis",
        "pelvis": "Pelvis",
        "rectum": "Pelvis",
        "rectal": "Pelvis",
        "bladder": "Pelvis",
        "cervix": "Pelvis",
        "gyn": "Pelvis",
        "musculoskeletal": "Musculoskeletal",
        "sarcoma": "Musculoskeletal",
    }

    target_site = site_map.get(clean_site, clean_site.title())

    results: list[OrganConstraint] = []
    for c in items:
        # Check pediatric status
        if is_pediatric:
            if c.fractionation_type != "pediatric":
                continue
        else:
            if c.fractionation_type == "pediatric":
                continue

        # Check fractionation type if specified
        if fractionation_type and c.fractionation_type != fractionation_type:
            continue

        # Site match
        if c.anatomical_site.lower() == target_site.lower() or target_site.lower() in c.anatomical_site.lower():
            results.append(c)

    return results


def get_constraints_for_organ(
    organ_name: str,
    catalogue: list[OrganConstraint] | None = None,
) -> list[OrganConstraint]:
    """Filter constraints by organ name (e.g. 'spinal cord', 'parotid', 'lung')."""
    items = catalogue if catalogue is not None else load_organ_constraints()
    clean_name = organ_name.strip().lower()
    return [c for c in items if clean_name in c.organ.lower()]


def format_specialist_constraints_prompt(
    site: str,
    role_name: str | None = None,
    fractionation_type: FractionationType | None = None,
    is_pediatric: bool = False,
    catalogue: list[OrganConstraint] | None = None,
) -> str:
    """Format exact numeric organ dose constraints as a prompt section for specialist personas."""
    constraints = get_constraints_for_site(
        site,
        fractionation_type=fractionation_type,
        is_pediatric=is_pediatric,
        catalogue=catalogue,
    )

    if not constraints:
        return f"### Normal Tissue Constraints ({site})\nNo site-specific OAR constraints matched for {site}."

    role_str = f" for {role_name}" if role_name else ""
    lines = [
        f"### Normal Tissue Tolerance & Organ-at-Risk Constraints{role_str}",
        f"Evidence Baseline: {'PENTEC (2024)' if is_pediatric else 'QUANTEC (2010)'}",
        "",
        "| Organ | Metric | Limit | Risk Endpoint | Estimated Risk Rate | Clinical Notes |",
        "|---|---|---|---|---|---|",
    ]

    for c in constraints:
        limit_str = f"{c.metric} {c.operator} {c.limit_value:g} {c.unit}"
        clean_notes = c.notes.replace("|", "/")
        lines.append(
            f"| {c.organ} ({c.volume_spec}) | {c.metric} | {limit_str} | {c.endpoint} | {c.risk_rate_percent} | {clean_notes} |"
        )

    lines.extend([
        "",
        "> [!IMPORTANT]",
        "> Constraints are strict upper bounds. The Radiation Oncologist, Dosimetrist, and Medical Physicist must optimize normal tissue sparing below these thresholds while maintaining target volume coverage.",
    ])

    return "\n".join(lines)
