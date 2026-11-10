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

def test_r3_receives_server_computed_peer_provenance_flags_and_exact_excerpt(monkeypatch):
    import asyncio

    from app.round_schemas import AdversarialContributionDraft
    from app.schemas import SyntheticCase
    from app.services import mdt_generation

    peer_response = (
        "Introductory review of the supplied record. " + ("Additional contextual wording. " * 12)
        + "There is consensus across all roles for a single pathway."
    )
    provenance_flag = _audit_source_references(
        {"response_to_other_perspectives": peer_response},
        {("R1", "RO-01"), ("R2", "MO-01")},
    )[0]
    own_r2_response = (
        "Introductory review of the supplied record. " + ("Additional contextual wording. " * 12)
        + "All 45 roles agree on this pathway."
    )
    own_r2_flag = _audit_source_references(
        {"response_to_other_perspectives": own_r2_response},
        {("R1", "RO-01"), ("R2", "RO-01")},
    )[0]
    captured = {}

    async def fake_generate(prompt, schema_type, max_tokens):
        captured["prompt"] = prompt
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion="The available record does not establish an educational option.",
            response_to_other_perspectives=(
                "The bounded peer material contains a provenance issue, not a clinical conclusion."
            ),
            agreements=[],
            substantive_challenges=[
                '[Provenance audit — R2:MO-01] The response states "consensus across all roles"; '
                "this is a scope defect in the sampled source, not a clinical disagreement."
            ],
            remaining_unknowns=[],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review the fictional educational case and its source integrity.",
    }
    case = SyntheticCase(
        scenario_title="Peer provenance audit test",
        case_summary="Fictional educational case summary with incomplete staging information.",
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The available case information is insufficient.",
        "preferred_educational_option": "No option is established.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains insufficient on the available record.",
        "response_to_other_perspectives": own_r2_response,
        "source_reference_integrity_flags": [own_r2_flag],
    }
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "insufficient_information",
            "provisional_conclusion": "The available case information is insufficient.",
            "response_to_other_perspectives": peer_response,
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
            "source_reference_integrity_flags": [
                "Reference finding before scope flag A.",
                "Reference finding before scope flag B.",
                "Reference finding before scope flag C.",
                "Reference finding before scope flag D.",
                "Reference finding before scope flag E.",
                provenance_flag,
            ],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    prompt = captured["prompt"]
    assert "provenance_audit_flags" in prompt
    assert "round2_provenance_audit_flags" in prompt
    assert own_r2_flag in prompt
    assert own_r2_response in prompt
    assert provenance_flag in prompt
    assert peer_response in prompt
    assert "For each flagged R2 source (your own or a" in prompt
    assert "not a clinical disagreement" in prompt
    assert "short exact contiguous excerpt" in prompt
    assert "Do not use a provenance flag as clinical evidence" in prompt
    assert any("R2:MO-01" in item for item in result.substantive_challenges)
    assert result.source_peer_ids == ["MO-01"]
    assert not any(
        "was not supplied as an attributable source" in item
        for item in result.source_reference_integrity_flags
    )

