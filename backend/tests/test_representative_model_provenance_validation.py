"""Regression tests for the live R3 positive-control oracle."""

from scripts.representative_model_provenance_validation import (
    _has_expected_source_bound_challenge,
)


def test_positive_control_requires_exact_supplied_peer_and_quoted_claim():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion" '
            "this is unsupported because no complete role-level record was supplied."
        ],
    }

    assert _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_challenge_attributed_to_wrong_peer():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:MO-01 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_generic_challenge_without_exact_quote():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            "The peer makes an unsupported claim about overall agreement."
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_quote_from_peer_not_in_supplied_sample():
    result = {
        "source_peer_ids": ["MO-01", "RO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_source_identifier_prefix_collision():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02-extra states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )



def test_positive_control_rejects_repeated_claim_without_explicit_rebuttal():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_rebuttal_marker_that_occurs_only_inside_the_quote():
    quoted_claim = "The entire 45-role MDT agrees; unsupported evidence is absent"
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            f'R2:SO-02 states "{quoted_claim}".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim=quoted_claim,
    )


def test_positive_control_rejects_empty_claim_and_non_list_peer_ids():
    challenge = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion"; '
            "this is unsupported because no complete role-level record was supplied."
        ],
    }
    assert not _has_expected_source_bound_challenge(
        challenge,
        source_agent_id="SO-02",
        quoted_claim="",
    )

    malformed = {
        "source_peer_ids": "SO-02",
        "substantive_challenges": challenge["substantive_challenges"],
    }
    assert not _has_expected_source_bound_challenge(
        malformed,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )
