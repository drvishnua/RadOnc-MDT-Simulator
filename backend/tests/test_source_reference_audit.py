from app.services.mdt_generation import _audit_source_references


def test_source_reference_audit_flags_role_ranges_without_rewriting_payload():
    payload = {
        "response_to_other_perspectives": (
            "All selected peers agree; see R1:RO-01 through R1:SV-02."
        )
    }
    original = payload["response_to_other_perspectives"]

    findings = _audit_source_references(
        payload,
        {("R1", "RO-01"), ("R1", "SV-02")},
    )

    assert any("Reference range R1:RO-01 through R1:SV-02" in item for item in findings)
    assert payload["response_to_other_perspectives"] == original


def test_source_reference_audit_flags_whole_mdt_scope_in_bounded_peer_response():
    payload = {
        "response_to_other_perspectives": (
            "There is consensus across all roles and the entire MDT agrees."
        )
    }

    findings = _audit_source_references(
        payload,
        {("R1", "RO-01"), ("R1", "MO-01")},
    )

    assert any("Peer-scope overclaim" in item for item in findings)


def test_source_reference_audit_accepts_only_supplied_individual_ids():
    payload = {
        "response_to_other_perspectives": (
            "R1:RO-01 and R1:MO-01 express similar uncertainty, without establishing "
            "agreement on an educational option."
        )
    }

    findings = _audit_source_references(
        payload,
        {("R1", "RO-01"), ("R1", "MO-01")},
    )

    assert findings == []
