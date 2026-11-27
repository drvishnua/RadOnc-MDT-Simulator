"""Unit tests for deterministic post-generation guards (STG-00 lock, U09 citations, R2 peer engagement)."""
from types import SimpleNamespace

from app.services.output_guards import (
    enforce_staging_lock_on_payload,
    ensure_r2_peer_engagement,
    sanitize_unverified_citations_in_payload,
)
from app.services.reference_catalogue import get_active_reference_catalogue


def test_enforce_staging_lock_replaces_unnegated_n0():
    pre_staging = SimpleNamespace(provisional_tnm={"t": "T3", "n": "N1b", "m": "M0"})
    payload = {
        "provisional_conclusion": "For cT3N0M0 rectal cancer, offer CRT.",
        "perspective_summary": "Unlike N0, this case has N1b nodes.",
    }
    enforce_staging_lock_on_payload(payload, pre_staging)
    assert "N1b" in payload["provisional_conclusion"]
    assert "N0" not in payload["provisional_conclusion"]
    assert "Unlike N0" in payload["perspective_summary"]


def test_sanitize_unverified_citations_strips_fake_tags():
    real_id = get_active_reference_catalogue()[0].source_id
    payload = {
        "provisional_conclusion": f"Standard CRT [source_id: {real_id}] vs [source_id: FAKE-TRIAL-999]."
    }
    sanitize_unverified_citations_in_payload(payload)
    assert real_id in payload["provisional_conclusion"]
    assert "FAKE-TRIAL-999" not in payload["provisional_conclusion"]


def test_ensure_r2_peer_engagement_populates_when_empty():
    payload = {
        "position": "conditional",
        "agreements": [],
        "substantive_challenges": [],
    }
    peers = [
        {
            "source": "R1:RO-01",
            "position": "supports",
            "preferred_educational_option": "Definitive CRT",
        }
    ]
    ensure_r2_peer_engagement(payload, peers)
    assert len(payload["substantive_challenges"]) == 1
    assert "R1:RO-01" in payload["substantive_challenges"][0]

    preserved = {
        "position": "supports",
        "agreements": ["Agrees with R1:RO-01 on CRT."],
        "substantive_challenges": [],
    }
    ensure_r2_peer_engagement(preserved, peers)
    assert preserved["agreements"] == ["Agrees with R1:RO-01 on CRT."]
    assert preserved["substantive_challenges"] == []
