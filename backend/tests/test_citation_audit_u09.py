"""Unit tests for U09 claim and citation auditing against the reference catalogue."""

from app.services.reference_catalogue import ReferenceEntry, audit_claim_citations


def _sample_catalogue() -> list[ReferenceEntry]:
    return [
        ReferenceEntry(
            source_id="RTOG-9111",
            title="Long-Term Results of RTOG 91-11",
            organization="NRG Oncology / RTOG",
            source_type="trial",
            edition_or_version="Phase III",
            publication_date="2013-02-01",
            specialties=["radiation_oncology", "medical_oncology"],
            topics=["larynx", "chemoradiation", "organ_preservation"],
            doi_or_url="https://doi.org/10.1200/JCO.2012.43.6097",
        ),
        ReferenceEntry(
            source_id="ASTRO-LARYNX-2020",
            title="Radiation Therapy for Orally/Laryngeally Advanced SCC",
            organization="ASTRO",
            source_type="guideline",
            edition_or_version="2020",
            publication_date="2020-07-01",
            specialties=["radiation_oncology"],
            topics=["larynx", "radiotherapy"],
            doi_or_url="https://doi.org/10.1016/j.prro.2020.04.002",
        ),
    ]


def test_audit_claim_citations_with_valid_and_invalid():
    catalogue = _sample_catalogue()
    claims = [
        {
            "role_id": "radiation_oncologist",
            "source_id": "RTOG-9111",
            "doi_or_url": "https://doi.org/10.1200/JCO.2012.43.6097",
            "claim": "Concurrent CRT achieves superior 10-year intact larynx preservation.",
        },
        {
            "role_id": "medical_oncologist",
            "source_id": "FABRICATED-2099",
            "doi_or_url": "https://doi.org/10.1000/fabricated",
            "claim": "Novel quadruplet immunotherapy improves overall survival.",
        },
    ]

    report = audit_claim_citations(claims, catalogue=catalogue)
    assert report["total_citations"] == 2
    assert report["verified_count"] == 1
    assert report["unverified_count"] == 1
    assert report["concordance_rate"] == 0.5
    assert not report["valid"]
    assert report["verified_citations"][0]["source_id"] == "RTOG-9111"
    assert report["unverified_citations"][0]["source_id"] == "FABRICATED-2099"


def test_audit_claim_citations_empty():
    report = audit_claim_citations([])
    assert report["total_citations"] == 0
    assert report["verified_count"] == 0
    assert report["unverified_count"] == 0
    assert report["concordance_rate"] == 1.0
    assert report["valid"] is True
