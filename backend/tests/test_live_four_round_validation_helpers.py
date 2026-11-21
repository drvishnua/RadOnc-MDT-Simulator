"""Unit tests for deterministic role-position checks in the live validator."""

from __future__ import annotations

import runpy
from pathlib import Path


def _minority_helper():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = backend_dir / "scripts" / "live_four_round_validation.py"
    namespace = runpy.run_path(
        str(script_path),
        run_name="live_four_round_validation_helper_test",
    )
    return namespace["_expected_minority_role_ids"]


def test_unique_modal_position_identifies_only_non_modal_final_positions():
    expected_ids = {"A", "B", "C", "D"}
    stable = {"A": "supports", "B": "supports", "C": "supports", "D": "opposes"}

    result = _minority_helper()(
        expected_ids,
        stable,
        stable,
        stable,
        {"supports": 3, "opposes": 1},
    )

    assert result == {"D"}


def test_tied_final_positions_do_not_create_an_arbitrary_minority_group():
    expected_ids = {"A", "B", "C", "D"}
    stable = {"A": "supports", "B": "supports", "C": "opposes", "D": "opposes"}

    result = _minority_helper()(
        expected_ids,
        stable,
        stable,
        stable,
        {"supports": 2, "opposes": 2},
    )

    assert result == set()


def test_tied_final_positions_still_preserve_actual_position_changes():
    expected_ids = {"A", "B", "C", "D"}
    round1 = {"A": "supports", "B": "supports", "C": "opposes", "D": "conditional"}
    round2 = {"A": "supports", "B": "supports", "C": "opposes", "D": "opposes"}
    round3 = {"A": "supports", "B": "supports", "C": "opposes", "D": "opposes"}

    result = _minority_helper()(
        expected_ids,
        round1,
        round2,
        round3,
        {"supports": 2, "opposes": 2},
    )

    assert result == {"D"}


def test_position_validation_rejects_missing_role_entries():
    expected_ids = {"A", "B"}
    positions = {"A": "insufficient_information"}

    try:
        _minority_helper()(
            expected_ids,
            positions,
            {"A": "insufficient_information", "B": "insufficient_information"},
            {"A": "insufficient_information", "B": "insufficient_information"},
            {"insufficient_information": 2},
        )
    except ValueError as exc:
        assert "R1 position map is missing roles" in str(exc)
    else:
        raise AssertionError("Missing role positions must not be accepted.")



def _quality_gate_helper():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = backend_dir / "scripts" / "live_four_round_validation.py"
    namespace = runpy.run_path(
        str(script_path),
        run_name="live_four_round_validation_quality_gate_test",
    )
    return namespace["_collect_integrity_quality_gate_failures"]


def test_malformed_r3_peer_prose_flag_fails_live_quality_gate_without_rewriting():
    malformed_flag = (
        "Malformed paired-source wording: response contains 'both and' without "
        "the intervening source/subject phrase."
    )
    saved_result = {
        "source_reference_integrity_flags": [malformed_flag],
        "case_data_integrity_flags": [],
    }
    payloads = [
        ("R3", [{"agent_id": "RO-03", "result": saved_result}], "result"),
    ]

    failures = _quality_gate_helper()(payloads)

    assert failures == [{
        "round": "R3",
        "agent_id": "RO-03",
        "type": "source_reference_integrity_flags",
        "detail": malformed_flag,
    }]
    assert saved_result["source_reference_integrity_flags"] == [malformed_flag]

def _modal_helpers():
    backend_dir = Path(__file__).resolve().parents[1]
    script_path = backend_dir / "scripts" / "live_four_round_validation.py"
    namespace = runpy.run_path(
        str(script_path),
        run_name="live_four_round_validation_modal_test",
    )
    return (
        namespace["_unique_modal_position"],
        namespace["_stable_modal_insufficient_role_ids"],
    )


def test_unique_modal_position_returns_none_for_ties_and_empty_counts():
    unique_modal, _ = _modal_helpers()

    assert unique_modal({"insufficient_information": 45}) == "insufficient_information"
    assert unique_modal({"supports": 2, "opposes": 2}) is None
    assert unique_modal({}) is None


def test_all_stable_insufficient_information_roles_are_not_labelled_as_dissent():
    _, stable_insufficient_roles = _modal_helpers()
    expected_ids = {"A", "B", "C"}
    positions = {
        "A": "insufficient_information",
        "B": "insufficient_information",
        "C": "supports",
    }

    assert stable_insufficient_roles(
        expected_ids,
        positions,
        positions,
        positions,
        {"insufficient_information": 2, "supports": 1},
    ) == {"A", "B"}


def test_tied_insufficient_and_support_positions_have_no_unique_insufficient_mode():
    _, stable_insufficient_roles = _modal_helpers()
    expected_ids = {"A", "B", "C", "D"}
    positions = {
        "A": "insufficient_information",
        "B": "insufficient_information",
        "C": "supports",
        "D": "supports",
    }

    assert stable_insufficient_roles(
        expected_ids,
        positions,
        positions,
        positions,
        {"insufficient_information": 2, "supports": 2},
    ) == set()


def test_unique_support_mode_does_not_mark_stable_insufficient_roles_as_modal():
    _, stable_insufficient_roles = _modal_helpers()
    expected_ids = {"A", "B", "C"}
    positions = {
        "A": "insufficient_information",
        "B": "supports",
        "C": "supports",
    }

    assert stable_insufficient_roles(
        expected_ids,
        positions,
        positions,
        positions,
        {"insufficient_information": 1, "supports": 2},
    ) == set()

