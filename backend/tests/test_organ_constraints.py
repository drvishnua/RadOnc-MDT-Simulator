"""Unit tests for the Organ Constraints service (QUANTEC & PENTEC)."""
import pytest
try:
    from app.services.organ_constraints import (
        load_organ_constraints,
        get_constraints_for_site,
        get_constraints_for_organ,
        format_specialist_constraints_prompt,
        OrganConstraint,
    )
except ImportError:
    from backend.app.services.organ_constraints import (
        load_organ_constraints,
        get_constraints_for_site,
        get_constraints_for_organ,
        format_specialist_constraints_prompt,
        OrganConstraint,
    )


def test_load_organ_constraints_success():
    """Verify loading constraints from the authoritative JSON catalogue."""
    constraints = load_organ_constraints()
    assert len(constraints) >= 40

    # Verify spinal cord constraint presence
    cord_constraints = [c for c in constraints if c.organ == "Spinal Cord" and c.limit_value == 50.0]
    assert len(cord_constraints) >= 1
    cord = cord_constraints[0]
    assert cord.source_id == "QUANTEC-CNS-2010"
    assert cord.limit_value == 50.0
    assert cord.unit == "Gy"
    assert cord.operator == "<="


def test_get_constraints_for_site_cns():
    """Verify CNS constraints retrieval."""
    cns_constraints = get_constraints_for_site("CNS")
    assert len(cns_constraints) >= 5

    organs = {c.organ for c in cns_constraints}
    assert "Brain" in organs
    assert "Brainstem" in organs
    assert "Optic Nerve / Chiasm" in organs
    assert "Spinal Cord" in organs
    assert "Cochlea" in organs


def test_get_constraints_for_site_head_and_neck():
    """Verify Head and Neck constraints retrieval."""
    hn_constraints = get_constraints_for_site("Head and Neck")
    assert len(hn_constraints) >= 4

    organs = {c.organ for c in hn_constraints}
    assert "Parotid Gland" in organs
    assert "Pharyngeal Constrictors" in organs
    assert "Larynx" in organs


def test_get_constraints_for_site_thorax():
    """Verify Thorax / Lung constraints retrieval."""
    thorax_constraints = get_constraints_for_site("Lung")
    assert len(thorax_constraints) >= 4

    organs = {c.organ for c in thorax_constraints}
    assert "Lungs (Bilateral)" in organs
    assert "Esophagus" in organs
    assert "Heart" in organs


def test_get_constraints_for_site_pelvis():
    """Verify Pelvis / Prostate constraints retrieval."""
    pelvis_constraints = get_constraints_for_site("Prostate")
    assert len(pelvis_constraints) >= 4

    organs = {c.organ for c in pelvis_constraints}
    assert "Rectum" in organs
    assert "Urinary Bladder" in organs
    assert "Penile Bulb" in organs
    assert "Femoral Heads (Bilateral)" in organs


def test_get_pediatric_constraints():
    """Verify pediatric PENTEC constraints."""
    ped_cns = get_constraints_for_site("CNS", is_pediatric=True)
    assert len(ped_cns) >= 5

    organs = {c.organ for c in ped_cns}
    assert "Brain (Pediatric)" in organs
    assert "Circle of Willis / Suprasellar Cistern" in organs
    assert "Retina (Pediatric)" in organs
    assert "Hypothalamus / Pituitary Gland" in organs
    assert "Spinal Cord (Pediatric)" in organs


def test_get_constraints_for_organ():
    """Verify lookup by specific organ name."""
    parotids = get_constraints_for_organ("parotid")
    assert len(parotids) >= 2
    for p in parotids:
        assert "parotid" in p.organ.lower()


def test_format_specialist_constraints_prompt():
    """Verify formatting markdown table for specialist prompts."""
    prompt = format_specialist_constraints_prompt(
        site="Head and Neck",
        role_name="Dosimetrist",
        fractionation_type="conventional",
    )
    assert "### Normal Tissue Tolerance & Organ-at-Risk Constraints for Dosimetrist" in prompt
    assert "Parotid Gland" in prompt
    assert "Mean dose < 25 Gy" in prompt
    assert "Dmax < 66 Gy" in prompt
    assert "QUANTEC (2010)" in prompt


def test_unknown_site_fallback():
    """Verify unknown site returns empty list cleanly without crashing."""
    res = get_constraints_for_site("UnknownRegion12345")
    assert res == []

    prompt = format_specialist_constraints_prompt("UnknownRegion12345")
    assert "No site-specific OAR constraints matched" in prompt
