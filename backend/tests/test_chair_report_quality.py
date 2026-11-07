from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.chair_report_quality import (
    SECTION_LIMITS,
    ensure_chair_report_completeness,
)


def _rows(field: str, positions: list[str], *, unknowns: bool = True) -> list[dict]:
    rows = []
    for index, position in enumerate(positions, start=1):
        agent_id = "PP-05" if position == "conditional" else f"RO-{index:02d}"
        payload = {
            "position": position,
            "provisional_conclusion": (
                "This role cannot settle the educational question without the missing case information."
            ),
        }
        if unknowns:
            payload.update({
                "unknowns": ["Patient preferences and clinical stage are not supplied."],
                "remaining_unknowns": ["Further case details are needed before real-world review."],
                "uncertainty_notes": ["The available synthetic facts leave important uncertainty."],
                "evidence_gaps": ["Evidence retrieval is not connected."],
            })
        rows.append({
            "agent_id": agent_id,
            "status": "completed",
            "agent_name": "Patient-perspective role" if position == "conditional" else f"Role {index}",
            field: payload,
        })
    return rows


def _empty_report() -> FinalMDTReport:
    return FinalMDTReport(
        run_id="synthetic-run",
        report_title="Synthetic Chair report",
        consensus_status="insufficient_information",
        chair_conclusion=(
            "No treatment recommendation can be made from the supplied synthetic information."
        ),
        overall_educational_synthesis="The source contributions require cautious interpretation.",
        consensus_points=[],
        unresolved_disagreements=[],
        minority_and_dissenting_views=[],
        major_uncertainties=[],
        missing_information_before_real_world_review=[],
        patient_and_family_considerations=[],
        feasibility_and_resource_considerations=[],
        governance_and_safeguarding_considerations=[],
        evidence_limitations=[],
        chair_reflection="This is a structural educational synthesis, not clinical validation.",
    )


def _assert_all_sections_are_explicit(report: FinalMDTReport) -> None:
    payload = report.model_dump()
    for field in SECTION_LIMITS:
        if field == "consensus_points":
            assert payload[field] == [], "Do not populate consensus points without proposition-level evidence"
            continue
        assert payload[field], f"{field} must contain findings or an explicit absence note"
        assert all(isinstance(item, str) and item.strip() for item in payload[field])
        assert len(payload[field]) <= SECTION_LIMITS[field]


def test_empty_chair_sections_are_filled_from_source_records():
    case = SyntheticCase(
        scenario_title="Synthetic Chair completeness test",
        case_summary="Fictional case used only to test deterministic report safeguards.",
        known_unknowns=["Clinical stage is not supplied."],
        patient_goals=[],
        social_context=[],
        resource_context=[],
    )
    positions = ["insufficient_information"] * 44 + ["conditional"]
    report = ensure_chair_report_completeness(
        _empty_report(),
        case,
        _rows("assessment", positions),
        _rows("result", positions),
        _rows("result", positions),
    )

    _assert_all_sections_are_explicit(report)
    assert report.consensus_points == []
    assert any("No proposition-level consensus" in item for item in report.unresolved_disagreements)
    assert any("non-uniform" in item for item in report.unresolved_disagreements)
    assert any("PP-05" in item and "conditional" in item for item in report.minority_and_dissenting_views)
    assert any("Clinical stage is not supplied" in item for item in report.major_uncertainties)
    assert any("Patient preferences" in item for item in report.missing_information_before_real_world_review)
    assert "not counted as votes" in " ".join(report.unresolved_disagreements).casefold()


def test_uniform_rounds_use_explicit_absence_notes_not_blank_or_false_consensus():
    case = SyntheticCase(
        scenario_title="Synthetic uniform-position test",
        case_summary="Fictional case with no explicit unknowns for report completeness testing.",
    )
    positions = ["insufficient_information"] * 45
    report = ensure_chair_report_completeness(
        _empty_report(),
        case,
        _rows("assessment", positions, unknowns=False),
        _rows("result", positions, unknowns=False),
        _rows("result", positions, unknowns=False),
    )

    _assert_all_sections_are_explicit(report)
    assert report.consensus_points == []
    assert "not proof" in report.unresolved_disagreements[0].casefold()
    assert "no genuine conditional/minority position" in report.minority_and_dissenting_views[0].casefold()
    assert "not establish" in report.major_uncertainties[0].casefold()
    assert "not supplied" in report.patient_and_family_considerations[0].casefold()


def test_minority_history_is_preserved_from_earlier_rounds_after_round_three_converges():
    case = SyntheticCase(
        scenario_title="Synthetic convergence-history test",
        case_summary="Fictional case used only to validate historical role-position traceability.",
    )
    first_positions = ["supports"] * 44 + ["conditional"]
    second_positions = ["supports"] * 44 + ["conditional"]
    third_positions = ["insufficient_information"] * 45
    report = ensure_chair_report_completeness(
        _empty_report(),
        case,
        _rows("assessment", first_positions, unknowns=False),
        _rows("result", second_positions, unknowns=False),
        _rows("result", third_positions, unknowns=False),
    )

    history = " ".join(report.minority_and_dissenting_views)
    assert "PP-05" in history
    assert "Round 1: conditional" in history
    assert "Round 2: conditional" in history
    assert "Round 3: insufficient_information" in history
    assert "Position evolution" in history
    assert "earlier round" in report.unresolved_disagreements[0].casefold()


def test_minority_history_merges_earlier_roles_with_existing_round_three_minority():
    case = SyntheticCase(
        scenario_title="Synthetic multi-round minority merge test",
        case_summary="Fictional case used only to validate distinct minority roles across rounds.",
    )
    round1 = _rows("assessment", ["supports"] * 44 + ["conditional"], unknowns=False)
    round1[-1]["agent_id"] = "PP-01"
    round1[-1]["agent_name"] = "Earlier patient perspective"

    round2 = _rows("result", ["supports"] * 44 + ["conditional"], unknowns=False)
    round2[-1]["agent_id"] = "FE-02"
    round2[-1]["agent_name"] = "Earlier feasibility perspective"

    round3 = _rows(
        "result",
        ["insufficient_information"] * 44 + ["supports"],
        unknowns=False,
    )
    round3[-1]["agent_id"] = "SG-07"
    round3[-1]["agent_name"] = "Current Round-3 minority"

    report_with_round_three_minority = _empty_report().model_copy(
        update={
            "minority_and_dissenting_views": [
                "SG-07 — Current Round-3 minority (supports): The saved review retains a distinct position."
            ]
        }
    )
    report = ensure_chair_report_completeness(
        report_with_round_three_minority,
        case,
        round1,
        round2,
        round3,
    )

    history = " ".join(report.minority_and_dissenting_views)
    assert "PP-01" in history and "Round 1: conditional" in history
    assert "FE-02" in history and "Round 2: conditional" in history
    assert "SG-07" in history and "Round 3: supports" in history
    assert len(report.minority_and_dissenting_views) <= 45



def test_failed_round_payloads_are_excluded_from_chair_counts_and_history():
    case = SyntheticCase(
        scenario_title="Synthetic failed-record exclusion test",
        case_summary="Fictional case used to validate completed-record provenance.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round3[-1]["status"] = "failed"
    round3[-1]["result"]["position"] = "supports"
    round3[-1]["result"]["provisional_conclusion"] = "STALE FAILED PAYLOAD MUST NOT ENTER THE CHAIR REPORT."
    round3[-1]["result"]["unknowns"] = ["STALE FAILED UNKNOWN MUST NOT ENTER THE REPORT."]

    report = ensure_chair_report_completeness(_empty_report(), case, round1, round2, round3)

    assert report.consensus_status == "insufficient_information"
    assert not any("RO-45" in item or "STALE FAILED" in item for item in report.minority_and_dissenting_views)
    assert not any("STALE FAILED" in item for item in report.major_uncertainties)


def test_uniform_support_positions_are_not_reported_as_minority_dissent():
    case = SyntheticCase(
        scenario_title="Synthetic uniform-support test",
        case_summary="Fictional case for validating minority classification.",
    )
    positions = ["supports"] * 45
    report = ensure_chair_report_completeness(
        _empty_report(),
        case,
        _rows("assessment", positions, unknowns=False),
        _rows("result", positions, unknowns=False),
        _rows("result", positions, unknowns=False),
    )
    joined = " ".join(report.minority_and_dissenting_views).casefold()
    assert "no genuine conditional/minority position" in joined
    assert not any(f"RO-{index:02d}" in joined for index in range(1, 46))
