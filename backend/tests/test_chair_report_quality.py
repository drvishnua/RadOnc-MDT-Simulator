from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.chair_report_quality import (
    SECTION_LIMITS,
    ensure_chair_report_completeness,
    validate_consensus_points,
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
        if field in {"consensus_points", "recorded_agreements"}:
            assert payload[field] == [], "Do not invent consensus or recorded agreement statements"
            continue
        assert payload[field], f"{field} must contain findings or an explicit absence note"
        assert all(isinstance(item, str) and item.strip() for item in payload[field])
        assert len(payload[field]) <= SECTION_LIMITS[field]


def test_empty_consensus_points_are_valid_until_proposition_level_support_exists():
    validate_consensus_points({"consensus_points": []})


def test_nonempty_consensus_points_are_rejected_without_proposition_level_provenance():
    import pytest

    with pytest.raises(ValueError, match="proposition-level support"):
        validate_consensus_points({"consensus_points": ["Unverified agreement"]})


def test_chair_uncertainties_exclude_unverified_role_assertions_but_keep_unknowns():
    case = SyntheticCase(
        scenario_title="Chair case-integrity quarantine test",
        case_summary="1x1 cm growth involving right vocal cord and anterior commissure.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round1[0]["assessment"]["unknowns"] = [
        "T1 glottic cancer typically does not require intensification.",
        "Clinical T stage is not supplied and must not be inferred from lesion size.",
    ]
    round1[0]["assessment"]["case_data_integrity_flags"] = [
        "Generated narrative contains unsupported T-stage terminology."
    ]
    chair_draft = _empty_report().model_copy(update={
        "major_uncertainties": [
            "T1 glottic cancer typically does not require intensification."
        ],
    })
    report = ensure_chair_report_completeness(
        chair_draft,
        case,
        round1,
        _rows("result", ["insufficient_information"] * 45),
        _rows("result", ["insufficient_information"] * 45),
    )
    joined = " ".join(report.major_uncertainties)
    assert "T1 glottic cancer typically" not in joined
    assert "Clinical T stage is not supplied" in joined
    assert any("unsupported T-stage" in item for item in report.case_data_integrity_flags)


def test_completeness_rebuilds_recorded_agreements_from_completed_round_records():
    case = SyntheticCase(
        scenario_title="Chair completeness agreement provenance test",
        case_summary="Fictional case used only for a deterministic report integrity regression.",
    )
    report = _empty_report().model_copy(
        update={
            "recorded_agreements": ["UNTRUSTED LLM INVENTED AGREEMENT"],
            "consensus_status": "consensus",
            "consensus_points": ["UNSUPPORTED MODEL-AUTHORED CONSENSUS"],
            "chair_conclusion": "All roles unanimously agreed to one educational option.",
        }
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    statement = "The two educational options remain distinct."
    round2[0]["result"]["agreements"] = [statement, statement]
    round3[1]["result"]["agreements"] = ["The missing prerequisite remains unresolved."]
    round3[2]["status"] = "failed"
    round3[2]["result"]["agreements"] = ["FAILED PAYLOAD MUST NOT APPEAR"]

    reconciled = ensure_chair_report_completeness(
        report, case, round1, round2, round3
    )

    assert not any("UNTRUSTED" in item or "FAILED PAYLOAD" in item for item in reconciled.recorded_agreements)
    assert sum(statement in item for item in reconciled.recorded_agreements) == 1
    assert any("Round 2 — RO-01" in item for item in reconciled.recorded_agreements)
    assert any("Round 3 — RO-02" in item for item in reconciled.recorded_agreements)
    assert reconciled.consensus_points == []
    assert reconciled.consensus_status == "insufficient_information"
    assert "unanimously" not in reconciled.chair_conclusion.casefold()
    assert "No proposition-level consensus" in reconciled.chair_conclusion


def test_completeness_rejects_model_consensus_when_saved_round_three_positions_conflict():
    case = SyntheticCase(
        scenario_title="Chair split-position consensus guard",
        case_summary="Fictional case used only to test deterministic consensus rejection.",
    )
    report = _empty_report().model_copy(
        update={
            "consensus_status": "consensus",
            "consensus_points": ["The model claims every role supports one pathway."],
            "chair_conclusion": "All roles unanimously agreed to one educational option.",
        }
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["supports"] * 44 + ["opposes"])

    reconciled = ensure_chair_report_completeness(
        report, case, round1, round2, round3
    )

    assert reconciled.consensus_status == "no_consensus"
    assert reconciled.consensus_points == []
    assert "both supporting and opposing" in reconciled.chair_conclusion
    assert "unanimously" not in reconciled.chair_conclusion.casefold()


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



def test_minority_history_retains_all_groups_when_round_three_modal_is_tied():
    case = SyntheticCase(
        scenario_title="Synthetic tied Round-3 completeness test",
        case_summary="Fictional case for validating balanced position-history preservation.",
    )
    positions = ["supports"] * 22 + ["opposes"] * 22 + ["insufficient_information"]
    round1 = _rows("assessment", positions, unknowns=False)
    round2 = _rows("result", positions, unknowns=False)
    round3 = _rows("result", positions, unknowns=False)

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    expected_roles = {
        row["agent_id"]
        for row in round3
        if row["result"]["position"] in {"supports", "opposes"}
    }
    visible_history = " ".join(report.minority_and_dissenting_views)
    assert all(agent_id in visible_history for agent_id in expected_roles)
    assert "RO-45" not in visible_history
    assert "no unique modal label" in " ".join(report.unresolved_disagreements).casefold()


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
