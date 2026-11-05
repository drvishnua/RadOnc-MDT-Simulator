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
    assert any("44/45 insufficient-information" in item for item in report.consensus_points)
    assert any("non-uniform" in item for item in report.unresolved_disagreements)
    assert any("PP-05" in item and "conditional" in item for item in report.minority_and_dissenting_views)
    assert any("Clinical stage is not supplied" in item for item in report.major_uncertainties)
    assert any("Patient preferences" in item for item in report.missing_information_before_real_world_review)
    assert "unanimous agreement" not in " ".join(report.consensus_points).casefold()


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
    assert "not proof" in report.consensus_points[0].casefold() or "not unanimous" in report.consensus_points[0].casefold()
    assert "not proof" in report.unresolved_disagreements[0].casefold()
    assert "no non-modal role position" in report.minority_and_dissenting_views[0].casefold()
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
    assert "Round 3:" not in history
    assert "earlier round" in report.unresolved_disagreements[0].casefold()
