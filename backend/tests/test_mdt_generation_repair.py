"""Regression tests for bounded R2/R3 clinical-integrity wording repair."""

from __future__ import annotations

import asyncio

from app.round_schemas import (
    AdversarialContributionDraft,
    Round2ContributionDraft,
    RoundTextRepairDraft,
    RoundTextRepairItem,
)
from app.schemas import SyntheticCase
from app.services import mdt_generation
from app.services.case_integrity import extract_attributed_note_opinions


def _case() -> SyntheticCase:
    return SyntheticCase(
        scenario_title="Synthetic prerequisite wording repair test",
        case_summary=(
            "Fictional educational case. MRI staging and fitness assessment are not supplied."
        ),
        known_unknowns=["MRI staging and fitness assessment are not supplied."],
    )


def _repair_item(path: str, text: str) -> RoundTextRepairDraft:
    return RoundTextRepairDraft(
        replacements=[RoundTextRepairItem(field_path=path, replacement_text=text)]
    )


def test_r2_generation_repairs_only_flagged_narrative_and_preserves_original(monkeypatch):
    case = _case()
    original = (
        "The role remains unable to establish a pathway because of missing information; "
        "the conditional pathways have unmet prerequisites."
    )
    safe = (
        "The status of MRI staging and fitness remains unknown because those assessments "
        "are not supplied; the source options therefore remain conditional."
    )
    calls = []

    async def fake_generate(prompt, schema_type, max_tokens):
        calls.append(schema_type)
        if schema_type is Round2ContributionDraft:
            return Round2ContributionDraft(
                position="insufficient_information",
                provisional_conclusion=(
                    "The supplied synthetic record does not establish a definitive pathway "
                    "because staging and investigation information is incomplete."
                ),
                response_to_other_perspectives=original,
                source_opinion_responses=[],
                confidence=0.5,
            )
        if schema_type is RoundTextRepairDraft:
            assert '"field_path":"response_to_other_perspectives"' in prompt
            return _repair_item("response_to_other_perspectives", safe)
        raise AssertionError(f"Unexpected schema: {schema_type.__name__}")

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "MO-01",
        "name": "Medical Oncology",
        "mandate": "Review the synthetic record and preserve uncertainty.",
    }
    own = {
        "position": "insufficient_information",
        "provisional_conclusion": "No definitive educational pathway can be established from the incomplete synthetic record.",
    }

    result = asyncio.run(
        mdt_generation.generate_debate_contribution(profile, case, own, [])
    )

    assert calls == [Round2ContributionDraft, RoundTextRepairDraft]
    assert result.position == "insufficient_information"
    assert result.response_to_other_perspectives == safe
    assert result.integrity_repair_attempted is True
    assert result.integrity_repair_status == "completed"
    assert result.integrity_repair_original_text == {
        "response_to_other_perspectives": original
    }
    assert result.integrity_repair_proposed_text == {
        "response_to_other_perspectives": safe
    }
    assert result.integrity_repair_applied_paths == [
        "response_to_other_perspectives"
    ]
    assert result.integrity_repair_original_flags
    assert not any(
        "prerequisite(s) as unmet/not met" in flag
        for flag in result.case_data_integrity_flags
    )


def test_r3_generation_repairs_flagged_narrative_and_preserves_original(monkeypatch):
    case = _case()
    original = (
        "The MRI prerequisite is not supplied, so its status is unknown; "
        "the conditionality remains unmet by the record."
    )
    safe = (
        "The MRI prerequisite remains unknown because the assessment is not supplied; "
        "the source option remains conditional on that assessment."
    )
    calls = []

    async def fake_generate(prompt, schema_type, max_tokens):
        calls.append(schema_type)
        if schema_type is AdversarialContributionDraft:
            return AdversarialContributionDraft(
                position="insufficient_information",
                provisional_conclusion=(
                    "The available synthetic data do not establish a definitive pathway "
                    "or resolve the outstanding investigation questions."
                ),
                response_to_other_perspectives=original,
                source_opinion_reviews=[],
                confidence=0.5,
            )
        if schema_type is RoundTextRepairDraft:
            return _repair_item("response_to_other_perspectives", safe)
        raise AssertionError(f"Unexpected schema: {schema_type.__name__}")

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    profile = {
        "agent_id": "SO-02",
        "name": "Surgical Oncology",
        "mandate": "Adversarially review the saved synthetic debate.",
    }
    own_r1 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The supplied record remains incomplete and does not establish a pathway.",
    }
    own_r2 = {
        "position": "insufficient_information",
        "provisional_conclusion": "The debate remains conditional because required information is not supplied.",
    }

    result = asyncio.run(
        mdt_generation.generate_adversarial_contribution(
            profile, case, own_r1, own_r2, []
        )
    )

    assert calls == [AdversarialContributionDraft, RoundTextRepairDraft]
    assert result.response_to_other_perspectives == safe
    assert result.integrity_repair_status == "completed"
    assert result.integrity_repair_original_text == {
        "response_to_other_perspectives": original
    }
    assert not any(
        "prerequisite(s) as unmet/not met" in flag
        for flag in result.case_data_integrity_flags
    )


def test_source_opinion_analysis_repair_must_preserve_option_and_condition_anchors(monkeypatch):
    case = SyntheticCase(
        scenario_title="Synthetic attributed opinion repair test",
        case_summary=(
            "Fictional case. The surgical note favours a surgery-led assessment, "
            "conditional on complete local staging."
        ),
    )
    source = extract_attributed_note_opinions(case.case_summary)[0]
    original = (
        "The surgery-led assessment is conditional on complete local staging; "
        "conditionality remains unmet."
    )
    replacement = (
        "The surgery-led assessment remains conditional on complete local staging; "
        "the staging assessment is not supplied and its status is unknown."
    )
    payload = {
        "position": "conditional",
        "source_opinion_responses": [{
            "source_id": source["source_id"],
            "source_excerpt": source["source_excerpt"],
            "analysis": original,
            "comparison": "This source option remains distinct from the other supplied perspective.",
        }],
    }

    async def fake_generate(prompt, schema_type, max_tokens):
        assert schema_type is RoundTextRepairDraft
        return _repair_item("source_opinion_responses[0].analysis", replacement)

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    repaired, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            case,
            payload,
            round_number=2,
            role_id="RO-01",
            role_name="Radiation Oncology",
            allowed_sources=set(),
        )
    )

    assert repaired["integrity_repair_status"] == "completed"
    assert repaired["source_opinion_responses"][0]["source_id"] == source["source_id"]
    assert repaired["source_opinion_responses"][0]["analysis"] == replacement
    assert repaired["integrity_repair_original_text"] == {
        "source_opinion_responses[0].analysis": original
    }
    assert not any("prerequisite(s) as unmet/not met" in flag for flag in flags)


def test_r3_source_review_basis_repair_preserves_all_source_reference_tokens(monkeypatch):
    attributed_case = SyntheticCase(
        scenario_title="Synthetic review-basis reference test",
        case_summary=(
            "Fictional case. The surgical note favours a surgery-led assessment, "
            "conditional on complete local staging."
        ),
    )
    source = extract_attributed_note_opinions(attributed_case.case_summary)[0]
    original = (
        f"{source['source_id']} and R2:RO-01 retain the source option, but "
        "conditionality remains unmet because staging is not supplied."
    )
    replacement = (
        f"{source['source_id']} and R2:RO-01 retain the surgery-led assessment option "
        "and its complete local staging condition; staging remains unknown because "
        "the assessment is not supplied."
    )
    payload = {
        "position": "insufficient_information",
        "source_opinion_reviews": [{
            "source_id": source["source_id"],
            "source_excerpt": source["source_excerpt"],
            "option_status": "preserved",
            "conditions_status": "preserved",
            "review_basis": original,
            "challenge": "",
            "source_reference_ids": [source["source_id"], "R2:RO-01"],
        }],
    }

    async def fake_generate(prompt, schema_type, max_tokens):
        assert schema_type is RoundTextRepairDraft
        return _repair_item("source_opinion_reviews[0].review_basis", replacement)

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    repaired, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            attributed_case,
            payload,
            round_number=3,
            role_id="SO-02",
            role_name="Surgical Oncology",
            allowed_sources={("R2", "RO-01")},
        )
    )

    assert repaired["integrity_repair_status"] == "completed"
    assert repaired["source_opinion_reviews"][0]["review_basis"] == replacement
    assert repaired["integrity_repair_original_text"] == {
        "source_opinion_reviews[0].review_basis": original
    }
    assert not any("prerequisite(s) as unmet/not met" in flag for flag in flags)


def test_repair_rejects_unsafe_replacement_and_retains_original(monkeypatch):
    case = _case()
    original = "The MRI prerequisite remains unmet because no MRI result was supplied."
    payload = {
        "position": "conditional",
        "provisional_conclusion": (
            "The educational assessment remains conditional pending the missing information."
        ),
        "response_to_other_perspectives": original,
    }

    async def unsafe_generate(prompt, schema_type, max_tokens):
        return _repair_item(
            "response_to_other_perspectives",
            "The MRI prerequisite remains unmet and the educational option is therefore conditional.",
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", unsafe_generate)
    result, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            case,
            payload,
            round_number=2,
            role_id="MO-01",
            role_name="Medical Oncology",
            allowed_sources=set(),
        )
    )

    assert result["response_to_other_perspectives"] == original
    assert result["integrity_repair_status"] == "blocked"
    assert result["integrity_repair_applied_paths"] == []
    assert result["integrity_repair_proposed_text"]["response_to_other_perspectives"]
    assert any("prerequisite(s) as unmet/not met" in flag for flag in flags)


def test_repair_rejects_incomplete_path_coverage_and_preserves_original(monkeypatch):
    case = _case()
    original = "The clinical prerequisites remain unmet because their assessments are not supplied."
    payload = {
        "position": "insufficient_information",
        "response_to_other_perspectives": original,
    }

    async def incomplete_generate(prompt, schema_type, max_tokens):
        return RoundTextRepairDraft(replacements=[])

    monkeypatch.setattr(mdt_generation, "_generate_structured", incomplete_generate)
    result, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            case,
            payload,
            round_number=3,
            role_id="SO-02",
            role_name="Surgical Oncology",
            allowed_sources=set(),
        )
    )

    assert result["response_to_other_perspectives"] == original
    assert result["integrity_repair_status"] == "blocked"
    assert any("exactly one replacement" in item for item in result["integrity_repair_flags"])
    assert flags


def test_repair_generation_failure_is_recorded_without_mutating_original(monkeypatch):
    case = _case()
    original = "The clinical prerequisites remain unmet because their assessments are not supplied."
    payload = {
        "position": "insufficient_information",
        "response_to_other_perspectives": original,
    }

    async def failed_generate(prompt, schema_type, max_tokens):
        raise RuntimeError("synthetic repair failure")

    monkeypatch.setattr(mdt_generation, "_generate_structured", failed_generate)
    result, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            case,
            payload,
            round_number=2,
            role_id="MO-01",
            role_name="Medical Oncology",
            allowed_sources=set(),
        )
    )

    assert result["response_to_other_perspectives"] == original
    assert result["integrity_repair_attempted"] is True
    assert result["integrity_repair_status"] == "failed"
    assert "synthetic repair failure" in result["integrity_repair_flags"][0]
    assert flags



def test_source_review_basis_repair_rejects_replacement_that_drops_preserved_option_anchor(monkeypatch):
    case = SyntheticCase(
        scenario_title="Synthetic source review anchor rejection test",
        case_summary=(
            "Fictional case. The surgical note favours a surgery-led assessment, "
            "conditional on complete local staging."
        ),
    )
    source = extract_attributed_note_opinions(case.case_summary)[0]
    original = (
        "The surgery-led assessment is conditional on complete local staging; "
        "conditionality remains unmet."
    )
    unsafe_replacement = (
        "The assessment remains conditional because staging information is not supplied; "
        "its status is unknown."
    )
    payload = {
        "position": "conditional",
        "source_opinion_reviews": [{
            "source_id": source["source_id"],
            "source_excerpt": source["source_excerpt"],
            "option_status": "preserved",
            "conditions_status": "preserved",
            "review_basis": original,
        }],
    }

    async def fake_generate(prompt, schema_type, max_tokens):
        return _repair_item(
            "source_opinion_reviews[0].review_basis",
            unsafe_replacement,
        )

    monkeypatch.setattr(mdt_generation, "_generate_structured", fake_generate)
    repaired, flags = asyncio.run(
        mdt_generation._repair_unsupported_prerequisite_wording(
            case,
            payload,
            round_number=3,
            role_id="SO-02",
            role_name="Surgical Oncology",
            allowed_sources=set(),
        )
    )

    assert repaired["source_opinion_reviews"][0]["review_basis"] == original
    assert repaired["integrity_repair_status"] == "blocked"
    assert repaired["integrity_repair_applied_paths"] == []
    assert any("source option and prerequisite anchors" in item for item in repaired["integrity_repair_flags"])
    assert flags
