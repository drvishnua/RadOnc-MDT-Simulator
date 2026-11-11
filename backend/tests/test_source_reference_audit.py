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


def test_r3_rejects_model_authored_case_opinion_without_server_bound_register(monkeypatch):
    import asyncio

    from app.round_schemas import AdversarialContributionDraft
    from app.schemas import SyntheticCase
    from app.services import mdt_generation
    from app.services.case_integrity import (
        case_summary_has_attributed_opinions,
        extract_attributed_note_opinions,
    )
    from app.services.chair_report_quality import build_source_opinion_review_coverage

    case_summary = (
        "Fictional educational case. The surgeon recommends a surgery-led assessment first, "
        "conditional on complete staging."
    )
    # The broad detector recognises speaker attribution, but the deterministic
    # note-opinion extractor cannot create a stable source register for this wording.
    assert case_summary_has_attributed_opinions(case_summary)
    assert extract_attributed_note_opinions(case_summary) == []

    captured = {}

    async def fake_generate(prompt, schema_type, max_tokens):
        captured["prompt"] = prompt
        return AdversarialContributionDraft(
            position="conditional",
            provisional_conclusion=(
                "The review remains conditional because the supplied case data are incomplete."
            ),
            response_to_other_perspectives=(
                "The peer record was reviewed, but it cannot establish the case-summary attribution."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=["Complete staging remains unknown."],
            risk_flags=[],
            confidence=0.4,
            source_opinion_reviews=[{
                "source_id": "CASE:case_summary#1",
                "opinion_label": "Surgeon recommendation",
                "source_excerpt": (
                    "The surgeon recommends a surgery-led assessment first, "
                    "conditional on complete staging."
                ),
                "option_status": "preserved",
                "conditions_status": "preserved",
                "review_basis": "The peer text includes a separate conditional statement.",
                "source_reference_ids": ["CASE:case_summary#1", "R2:MO-01"],
                "evidence_peer_id": "R2:MO-01",
                "evidence_excerpt": "conditional on MRI review",
                "evidence_validation_status": "verified",
            }],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review the educational case and source attribution.",
    }
    case = SyntheticCase(
        scenario_title="Unregistered attribution fallback test",
        case_summary=case_summary,
    )
    own_r1 = {
        "position": "conditional",
        "provisional_conclusion": "The independent position remains conditional pending full case details.",
        "preferred_educational_option": "No option is established.",
    }
    own_r2 = {
        "position": "conditional",
        "provisional_conclusion": "The debate position remains conditional pending full case details.",
        "response_to_other_perspectives": "The debate does not establish a final educational option.",
    }
    peer_response = "Option remains conditional on MRI review."
    peers = [{
        "agent_id": "MO-01",
        "agent_name": "Medical Oncology",
        "result": {
            "position": "conditional",
            "provisional_conclusion": "The peer view remains conditional on additional records.",
            "response_to_other_perspectives": peer_response,
            "agreements": [],
            "substantive_challenges": [],
            "risk_flags": [],
            "position_changes": [],
        },
    }]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    review = result.source_opinion_reviews[0]
    assert "speak" in captured["prompt"].casefold()
    assert review.option_status == "unclear"
    assert review.conditions_status == "unclear"
    assert review.source_reference_ids == []
    assert review.evidence_validation_status == "invalid"
    assert review.model_reported_option_status == "preserved"
    assert review.model_reported_conditions_status == "preserved"
    assert review.model_reported_source_reference_ids == [
        "CASE:case_summary#1",
        "R2:MO-01",
    ]
    assert any(
        "server could not bind a case-summary source-opinion register" in flag
        for flag in result.source_reference_integrity_flags
    )

    coverage, integrity = build_source_opinion_review_coverage(
        [{
            "agent_id": "RO-01",
            "agent_name": "Radiation Oncology",
            "status": "completed",
            "result": result.model_dump(),
        }],
        case_summary,
    )
    assert coverage == []
    assert any("omits its exact CASE source ID" in flag for flag in integrity)


def test_r3_receives_full_peer_response_and_server_binds_preserved_and_omitted_reviews(monkeypatch):
    import asyncio

    from app.round_schemas import AdversarialContributionDraft
    from app.schemas import SyntheticCase
    from app.services import mdt_generation
    from app.services.case_integrity import extract_attributed_note_opinions

    case_summary = (
        "Fictional educational record with incomplete investigations. "
        "The surgical oncology note favours a surgery-led assessment first, "
        "conditional on complete local staging and resectability review; "
        "the medical oncology note favours discussing a preoperative multimodality "
        "sequence, conditional on MRI staging, metastatic work-up and fitness assessment. "
        "Neither note supplies the missing investigations or establishes a final plan."
    )
    opinions = extract_attributed_note_opinions(case_summary)
    assert len(opinions) == 2

    # The source-bearing text deliberately occurs after the old 100-character
    # response limit so the test catches lossy peer-digest truncation.
    peer_preserved_response = (
        "The review begins with a general discussion of the incomplete educational record. "
        "The attributed surgical oncology note favours a surgery-led assessment first, "
        "conditional on complete local staging and resectability review. "
        "The attributed medical oncology note favours discussing a preoperative multimodality "
        "sequence, conditional on MRI staging, metastatic work-up and fitness assessment."
    )
    peer_omitted_response = (
        "The supplied record does not establish a definitive educational pathway because "
        "clinical stage, investigation results, fitness and patient goals are missing."
    )
    captured = {}

    async def fake_generate(prompt, schema_type, max_tokens):
        captured["prompt"] = prompt
        return AdversarialContributionDraft(
            position="insufficient_information",
            provisional_conclusion=(
                "The peer sample does not establish a definitive educational pathway."
            ),
            response_to_other_perspectives=(
                "The two supplied peer records differ in how they represent the conditional opinions."
            ),
            agreements=[],
            substantive_challenges=[],
            remaining_unknowns=[],
            risk_flags=[],
            confidence=0.5,
            source_opinion_reviews=[
                {
                    "source_id": opinions[0]["source_id"],
                    "option_status": "preserved",
                    "conditions_status": "preserved",
                    "review_basis": (
                        "The supplied R2 peer explicitly retains the surgery-led option "
                        "and its local-staging and resectability conditions."
                    ),
                    "source_reference_ids": [
                        opinions[0]["source_id"],
                        "R2:MO-01",
                    ],
                    "evidence_peer_id": "R2:MO-01",
                    "evidence_excerpt": (
                        "surgery-led assessment first, conditional on complete local staging"
                    ),
                },
                {
                    "source_id": opinions[1]["source_id"],
                    "option_status": "omitted",
                    "conditions_status": "omitted",
                    "review_basis": (
                        "The cited R2 peer summarizes only missing case information and "
                        "does not retain the preoperative multimodality option or its conditions. "
                        "This is a representation omission in that peer record, not a conclusion "
                        "that the clinical prerequisites are fulfilled or unfulfilled."
                    ),
                    "source_reference_ids": [
                        opinions[1]["source_id"],
                        "R2:SO-02",
                    ],
                    "evidence_peer_id": "R2:SO-02",
                    "evidence_excerpt": (
                        "does not establish a definitive educational pathway because clinical stage"
                    ),
                    "challenge": (
                        "The cited R2 peer generalizes the record's uncertainty without retaining "
                        "the separately attributed preoperative multimodality option or its stated "
                        "MRI, metastatic-work-up and fitness conditions."
                    ),
                },
            ],
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "RO-01",
        "name": "Radiation Oncology",
        "mandate": "Review source representation and preserve uncertainty.",
    }
    case = SyntheticCase(
        scenario_title="R3 peer-context source audit",
        case_summary=case_summary,
    )
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": (
            "The supplied fictional record does not establish a definitive pathway."
        ),
        "preferred_educational_option": "No pathway is established from the supplied data.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": (
            "The supplied fictional record does not establish a definitive pathway."
        ),
        "response_to_other_perspectives": (
            "The R2 position remains insufficient pending further case details."
        ),
    }
    peers = [
        {
            "agent_id": "MO-01",
            "agent_name": "Medical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": (
                    "The source opinion is retained conditionally in this peer record."
                ),
                "response_to_other_perspectives": peer_preserved_response,
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
            },
        },
        {
            "agent_id": "SO-02",
            "agent_name": "Surgical Oncology",
            "result": {
                "position": "insufficient_information",
                "provisional_conclusion": (
                    "The supplied record does not establish a definitive educational pathway."
                ),
                "response_to_other_perspectives": peer_omitted_response,
                "agreements": [],
                "substantive_challenges": [],
                "risk_flags": [],
                "position_changes": [],
            },
        },
    ]

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, peers
        )
    )

    # Full peer context is supplied: the attributed option appears after the
    # previous 100-character truncation point and remains an exact source excerpt.
    assert peer_preserved_response in captured["prompt"]
    assert "For EVERY review, including omitted and unclear reviews" in captured["prompt"]
    assert "never cite your own R2 record as a peer" in captured["prompt"]

    reviews = {review.source_id: review for review in result.source_opinion_reviews}
    assert set(reviews) == {opinion["source_id"] for opinion in opinions}
    preserved = reviews[opinions[0]["source_id"]]
    omitted = reviews[opinions[1]["source_id"]]

    assert preserved.option_status == "preserved"
    assert preserved.conditions_status == "preserved"
    assert preserved.evidence_validation_status == "verified"
    assert preserved.source_reference_ids == [
        opinions[0]["source_id"],
        "R2:MO-01",
    ]

    assert omitted.option_status == "omitted"
    assert omitted.conditions_status == "omitted"
    assert omitted.evidence_validation_status == "verified"
    assert omitted.source_reference_ids == [
        opinions[1]["source_id"],
        "R2:SO-02",
    ]
    assert any(
        opinions[1]["source_id"] in challenge and "R2:SO-02" in challenge
        for challenge in result.substantive_challenges
    )
    assert result.source_reference_integrity_flags == []
