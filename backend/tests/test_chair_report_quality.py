from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.chair_report_quality import (
    SECTION_LIMITS,
    build_recorded_agreements,
    build_source_opinion_position_summary,
    build_source_opinion_review_coverage,
    ensure_chair_report_completeness,
    _round_completion_disclosures,
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


def test_failed_duplicate_row_does_not_hide_a_usable_completed_role_contribution():
    rows = [
        {
            "agent_id": "RO-01",
            "status": "completed",
            "assessment": {"position": "supports"},
        },
        {
            "agent_id": "RO-01",
            "status": "failed",
            "assessment": None,
        },
        {
            "agent_id": "MO-01",
            "status": "failed",
            "assessment": None,
        },
    ]

    disclosures = _round_completion_disclosures(rows, "assessment", 1)
    no_usable = [item for item in disclosures if "no usable completed" in item]
    duplicate_rows = [item for item in disclosures if "additional non-usable row" in item]

    assert len(no_usable) == 1
    assert "MO-01" in no_usable[0]
    assert "RO-01" not in no_usable[0]
    assert len(duplicate_rows) == 1
    assert "RO-01" in duplicate_rows[0]
    assert "completed contribution remains eligible" in duplicate_rows[0]


def test_conflicting_completed_duplicates_do_not_make_failed_duplicate_look_usable():
    rows = [
        {
            "agent_id": "RO-01",
            "status": "completed",
            "assessment": {"position": "supports"},
        },
        {
            "agent_id": "RO-01",
            "status": "completed",
            "assessment": {"position": "opposes"},
        },
        {
            "agent_id": "RO-01",
            "status": "failed",
            "assessment": None,
        },
    ]

    disclosures = _round_completion_disclosures(rows, "assessment", 1)

    assert any(
        "RO-01" in item and "no usable completed" in item
        for item in disclosures
    )
    assert not any(
        "RO-01" in item and "additional non-usable row" in item
        for item in disclosures
    )



def test_chair_excludes_saved_payloads_with_mismatched_role_or_round_identity():
    case = SyntheticCase(
        scenario_title="Chair payload provenance mismatch test",
        case_summary="Fictional case used only to validate saved row identity integrity.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round3[0]["result"].update({"agent_id": "MO-01", "round_number": 3})
    round3[1]["result"].update({"agent_id": "RO-02", "round_number": 2})

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    assert "43/43 insufficient-information" in report.overall_educational_synthesis
    integrity = " ".join(report.case_data_integrity_flags)
    assert "saved row RO-01 identifies payload agent_id MO-01" in integrity
    assert "saved row RO-02 identifies payload round_number 2; expected 3" in integrity


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
        if field in {"consensus_points", "recorded_agreements", "source_opinion_review_coverage"}:
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


def test_completeness_rebuilds_proposition_consensus_note_without_near_duplicate_draft_text():
    case = SyntheticCase(
        scenario_title="Chair duplicate proposition note test",
        case_summary="Fictional case used only for deterministic Chair report validation.",
    )
    draft = _empty_report().model_copy(update={
        "unresolved_disagreements": [
            "No proposition-level consensus is established by free-text agreement notes; position labels and repeated wording are not counted as votes.",
            "No proposition-level consensus is established by the saved free-text agreement notes; position labels and repeated wording are not counted as votes.",
            "A genuine source-linked disagreement remains open: R2:RO-01 and R2:SO-02 describe distinct conditional options.",
        ],
    })
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)

    report = ensure_chair_report_completeness(draft, case, round1, round2, round3)

    proposition_notes = [
        item for item in report.unresolved_disagreements
        if item.casefold().startswith("no proposition-level consensus is established by")
    ]
    assert proposition_notes == [
        "No proposition-level consensus is established by free-text agreement notes; "
        "position labels and repeated wording are not counted as votes."
    ]
    assert any("genuine source-linked disagreement" in item for item in report.unresolved_disagreements)


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


def test_completeness_rejects_model_consensus_from_unlinked_support_opposition_labels():
    case = SyntheticCase(
        scenario_title="Chair unlinked-position consensus guard",
        case_summary="Fictional case used only to test deterministic proposition-status handling.",
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

    assert reconciled.consensus_status == "insufficient_information"
    assert reconciled.consensus_points == []
    assert "No proposition-level consensus" in reconciled.chair_conclusion
    assert any("supports" in item and "opposes" in item for item in reconciled.unresolved_disagreements)
    assert "unanimously" not in reconciled.chair_conclusion.casefold()



def test_completeness_does_not_infer_no_consensus_from_uniform_unlinked_support_labels():
    case = SyntheticCase(
        scenario_title="Chair unsupported no-consensus guard",
        case_summary="Fictional case used only to test proposition-status integrity.",
    )
    report = _empty_report().model_copy(
        update={
            "consensus_status": "no_consensus",
            "chair_conclusion": "The model claims no consensus was reached.",
        }
    )
    round1 = _rows("assessment", ["supports"] * 45)
    round2 = _rows("result", ["supports"] * 45)
    round3 = _rows("result", ["supports"] * 45)

    reconciled = ensure_chair_report_completeness(
        report, case, round1, round2, round3
    )

    assert reconciled.consensus_status == "insufficient_information"
    assert reconciled.consensus_points == []
    assert "No proposition-level consensus" in reconciled.chair_conclusion
    assert "45/45 supports" in reconciled.overall_educational_synthesis


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

def test_final_chair_quarantines_unsupported_claims_across_saved_role_text_sections():
    case = SyntheticCase(
        scenario_title="Chair all-section quarantine regression",
        case_summary="1x1 cm growth involving right vocal cord and anterior commissure.",
        clinical_t_stage=None,
        clinical_n_stage=None,
        clinical_m_stage=None,
        relevant_comorbidities=[],
        prior_treatment=[],
        patient_goals=[],
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)

    round1[0]["assessment"]["unknowns"] = ["The patient prefers surgery."]
    round1[0]["assessment"]["evidence_gaps"] = ["MRI demonstrates node-negative disease."]
    round2[0]["result"]["agreements"] = [
        "The patient is node-negative and the tumour is resectable."
    ]
    round3[1]["result"]["substantive_challenges"] = [
        "The patient has no distant metastases; treatment is unsafe."
    ]
    round3[-1]["result"]["position"] = "supports"
    round3[-1]["result"]["provisional_conclusion"] = (
        "The patient has T1N0M0 and the tumour is resectable."
    )

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    agreements = " ".join(report.recorded_agreements).casefold()
    unresolved = " ".join(report.unresolved_disagreements).casefold()
    minority = " ".join(report.minority_and_dissenting_views).casefold()
    evidence = " ".join(report.evidence_limitations).casefold()
    patient = " ".join(report.patient_and_family_considerations).casefold()
    flags = " ".join(report.case_data_integrity_flags).casefold()

    assert "node-negative" not in agreements
    assert "resectable" not in agreements
    assert "no distant metastases" not in unresolved
    assert "unsafe" not in unresolved
    assert "ro-45" in minority and "round 3: supports" in minority
    assert "t1n0m0" not in minority and "resectable" not in minority
    assert "withheld by deterministic case-integrity audit" in minority
    assert "mri demonstrates" not in evidence
    assert "prefers surgery" not in patient
    assert "node-negative" in flags
    assert "resectability status" in flags
    assert "absence of metastatic disease" in flags
    assert "treatment safety/indication" in flags
    assert "performance" not in flags


def test_chair_finalizer_rebuilds_synthesis_and_case_sections_instead_of_trusting_preexisting_text():
    case = SyntheticCase(
        scenario_title="Chair deterministic-section rebuild regression",
        case_summary="Fictional incomplete case for report-boundary testing.",
        patient_goals=[],
        social_context=[],
        resource_context=[],
    )
    untrusted_report = _empty_report().model_copy(update={
        "chair_conclusion": "The patient is T1N0M0 and should receive treatment.",
        "overall_educational_synthesis": "All roles agree the patient is node-negative.",
        "chair_reflection": "The patient prefers surgery.",
        "patient_and_family_considerations": ["The patient prefers surgery."],
        "feasibility_and_resource_considerations": ["The tumour is resectable."],
        "governance_and_safeguarding_considerations": ["Treatment is not indicated."],
        "evidence_limitations": ["MRI shows no distant metastases."],
        "unresolved_disagreements": ["The patient is node-negative."],
        "recorded_agreements": ["All roles agreed."],
    })
    rows1 = _rows("assessment", ["insufficient_information"] * 45)
    rows2 = _rows("result", ["insufficient_information"] * 45)
    rows3 = _rows("result", ["insufficient_information"] * 45)

    report = ensure_chair_report_completeness(
        untrusted_report, case, rows1, rows2, rows3
    )

    rendered = " ".join([
        report.chair_conclusion,
        report.overall_educational_synthesis,
        report.chair_reflection,
        *report.patient_and_family_considerations,
        *report.feasibility_and_resource_considerations,
        *report.governance_and_safeguarding_considerations,
        *report.evidence_limitations,
        *report.unresolved_disagreements,
        *report.recorded_agreements,
    ]).casefold()
    assert "t1n0m0" not in rendered
    assert "node-negative" not in rendered
    assert "prefers surgery" not in rendered
    assert "resectable" not in rendered
    assert "not indicated" not in rendered
    assert "no distant metastases" not in rendered

def test_position_counts_deduplicate_same_role_rows_and_flag_them():
    case = SyntheticCase(
        scenario_title="Duplicate same-position role regression",
        case_summary="Fictional case for deterministic role-count testing.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    duplicate = {
        **round3[0],
        "result": {**round3[0]["result"], "provisional_conclusion": "A repeated saved record from the same role."},
    }
    round3.append(duplicate)

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    assert "Round 3: 45/45 insufficient-information" in report.overall_educational_synthesis
    assert any(
        "Round 3 contains 2 completed records for RO-01" in item
        and "counted once" in item
        for item in report.case_data_integrity_flags
    )


def test_conflicting_duplicate_role_positions_are_excluded_and_flagged():
    case = SyntheticCase(
        scenario_title="Duplicate conflicting role regression",
        case_summary="Fictional case for deterministic role-count testing.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round3[0]["result"]["case_data_integrity_flags"] = ["Original RO-01 source flag must remain visible."]
    duplicate = {
        **round3[0],
        "result": {
            **round3[0]["result"],
            "position": "supports",
            "case_data_integrity_flags": ["Duplicate RO-01 source flag must remain visible."],
        },
    }
    round3.append(duplicate)

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    assert "Round 3: 44/44 insufficient-information" in report.overall_educational_synthesis
    assert not any("RO-01" in item for item in report.minority_and_dissenting_views)
    assert any("Original RO-01 source flag must remain visible" in item for item in report.case_data_integrity_flags)
    assert any("Duplicate RO-01 source flag must remain visible" in item for item in report.case_data_integrity_flags)
    assert any(
        "duplicate completed records for RO-01" in item
        and "conflicting positions" in item
        and "excluded" in item
        for item in report.case_data_integrity_flags
    )

def test_positive_model_consensus_claims_are_quarantined_across_chair_sections():
    case = SyntheticCase(
        scenario_title="Positive consensus quarantine regression",
        case_summary="Fictional incomplete case for testing the Chair consensus boundary.",
    )
    report_draft = _empty_report().model_copy(update={
        "unresolved_disagreements": [
            "All 45 roles unanimously agree surgery is the appropriate educational pathway."
        ],
        "major_uncertainties": [
            "The majority supports surgery as the appropriate pathway."
        ],
    })
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round1[0]["assessment"]["unknowns"] = [
        "Every role agreed that surgery should proceed."
    ]
    round2[0]["result"]["agreements"] = [
        "All roles unanimously support surgery."
    ]
    round3[-1]["result"]["position"] = "supports"
    round3[-1]["result"]["provisional_conclusion"] = (
        "All 45 roles unanimously agree surgery is the appropriate pathway."
    )

    report = ensure_chair_report_completeness(
        report_draft, case, round1, round2, round3
    )
    rendered = " ".join([
        *report.unresolved_disagreements,
        *report.major_uncertainties,
        *report.recorded_agreements,
        *report.minority_and_dissenting_views,
    ]).casefold()

    assert "all 45 roles unanimously agree" not in rendered
    assert "the majority supports surgery" not in rendered
    assert "every role agreed" not in rendered
    assert "all roles unanimously support" not in rendered
    assert "round 3: supports" in rendered
    assert "positive consensus assertion withheld" in " ".join(report.case_data_integrity_flags).casefold()
    assert any("no proposition-level consensus" in item.casefold() for item in report.unresolved_disagreements)


def test_explicit_negative_consensus_statements_are_not_quarantined_as_positive_claims():
    case = SyntheticCase(
        scenario_title="Negative consensus wording regression",
        case_summary="Fictional incomplete case for testing.",
    )
    draft = _empty_report().model_copy(update={
        "unresolved_disagreements": ["No consensus was reached because positions remained non-uniform."]
    })
    rows1 = _rows("assessment", ["insufficient_information"] * 45)
    rows2 = _rows("result", ["insufficient_information"] * 45)
    rows3 = _rows("result", ["insufficient_information"] * 45)

    report = ensure_chair_report_completeness(draft, case, rows1, rows2, rows3)

    assert any("No consensus was reached" in item for item in report.unresolved_disagreements)

def test_negative_consensus_clause_does_not_mask_separate_positive_consensus_claims():
    case = SyntheticCase(
        scenario_title="Mixed positive and negative consensus quarantine regression",
        case_summary="Fictional incomplete case for testing the Chair consensus boundary.",
    )
    mixed_claim = (
        "No consensus was reached, but the majority supports surgery "
        "as the appropriate educational pathway."
    )
    draft = _empty_report().model_copy(update={
        "major_uncertainties": [mixed_claim],
    })
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)

    round1[0]["assessment"]["unknowns"] = [mixed_claim]
    round2[0]["result"]["agreements"] = [mixed_claim]
    round3[-1]["result"]["position"] = "supports"
    round3[-1]["result"]["provisional_conclusion"] = mixed_claim

    report = ensure_chair_report_completeness(
        draft, case, round1, round2, round3
    )
    rendered = " ".join([
        *report.major_uncertainties,
        *report.recorded_agreements,
        *report.minority_and_dissenting_views,
    ]).casefold()
    flags = " ".join(report.case_data_integrity_flags).casefold()

    assert mixed_claim.casefold() not in rendered
    assert "positive consensus assertion withheld" in flags
    assert "round 3: supports" in rendered

def test_position_counts_collapse_case_and_whitespace_variants_of_the_same_role_id():
    case = SyntheticCase(
        scenario_title="Case-variant duplicate role regression",
        case_summary="Fictional case for deterministic role-count testing.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    duplicate = {**round3[0], "agent_id": " ro-01 "}
    round3.append(duplicate)

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    assert "Round 3: 45/45 insufficient-information" in report.overall_educational_synthesis
    assert any(
        "2 completed records for RO-01" in item and "counted once" in item
        for item in report.case_data_integrity_flags
    )


def test_completed_contribution_without_agent_id_is_excluded_from_role_counts():
    case = SyntheticCase(
        scenario_title="Missing role identifier exclusion regression",
        case_summary="Fictional case for deterministic role-count testing.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round3[0]["agent_id"] = None

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )

    assert "Round 3: 44/44 insufficient-information" in report.overall_educational_synthesis
    assert any(
        "has no agent_id and was excluded" in item
        for item in report.case_data_integrity_flags
    )

def test_final_chair_rebuilds_source_opinion_coverage_from_saved_r3_reviews():
    source_one = (
        "colorectal surgical note favours surgical assessment first "
        "conditional on complete local staging"
    )
    source_two = (
        "medical oncology note favours discussion of preoperative multimodality "
        "pending MRI staging and fitness review"
    )
    case = SyntheticCase(
        scenario_title="Source-opinion final-boundary regression",
        case_summary=f"Referral records two opinions: {source_one}. {source_two}.",
    )

    def review(source_id, excerpt, option, conditions, peer_id):
        return {
            "source_id": source_id,
            "opinion_label": "model-reported source label",
            "source_excerpt": excerpt,
            "option_status": option,
            "conditions_status": conditions,
            "review_basis": "Representation comparison only.",
            "source_reference_ids": [source_id, f"R2:{peer_id}"],
            "evidence_peer_id": f"R2:{peer_id}",
            "evidence_excerpt": "Exact peer excerpt retained by test fixture.",
            "evidence_validation_status": "verified",
            "challenge": "",
        }

    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round2[0]["result"]["source_reference_integrity_flags"] = [
        "R2 test flag retained from saved role record."
    ]
    # Duplicate same-position record: its audit flag must not be lost when
    # distinct-role position/count summaries retain only the first row.
    round2.append({
        **round2[0],
        "result": {
            **round2[0]["result"],
            "source_reference_integrity_flags": [
                "R2 duplicate-only source-reference flag."
            ],
        },
    })
    round3[2]["result"]["source_reference_integrity_flags"] = [
        "R3 test flag retained from saved role record.",
        "Malformed paired-source wording: response contains 'both and' without the intervening source/subject phrase."
    ]

    round3[0]["result"]["source_peer_ids"] = ["RO-02"]
    round3[0]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#1", source_one, "preserved", "preserved", "RO-02")
    ]
    # Unsafe model-authored labels must not suppress the deterministic review counts.
    round3[0]["result"]["source_opinion_reviews"][0]["opinion_label"] = (
        "The majority supports surgery"
    )
    round3[1]["result"]["source_peer_ids"] = ["RO-03"]
    round3[1]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#1", source_one, "omitted", "omitted", "RO-03"),
        review("CASE:case_summary#1", source_one, "preserved", "omitted", "RO-03"),
    ]
    round3[2]["result"]["source_peer_ids"] = ["RO-04"]
    round3[2]["result"]["source_opinion_reviews"] = [
        review("CASE:case_summary#2", source_two, "partly_preserved", "unclear", "RO-04")
    ]
    round3[3]["result"]["source_peer_ids"] = ["RO-05"]
    round3[3]["result"]["source_opinion_reviews"] = [
        {
            **review(
                "CASE:case_summary#2",
                "This excerpt is not present in the supplied case.",
                "preserved",
                "preserved",
                "RO-05",
            )
        }
    ]

    draft = _empty_report().model_copy(update={
        "unresolved_disagreements": [
            "STALE MODEL-CONTROLLED SOURCE REVIEW COVERAGE — 45/45 roles unanimously preserved all options."
        ],
    })
    report = ensure_chair_report_completeness(
        draft, case, round1, round2, round3
    )
    unresolved = " ".join(report.unresolved_disagreements)
    coverage = " ".join(report.source_opinion_review_coverage)
    flags = " ".join(report.case_data_integrity_flags)

    assert "STALE MODEL-CONTROLLED SOURCE REVIEW COVERAGE" not in unresolved
    assert "CASE:case_summary#1" in coverage
    assert source_one in coverage
    assert source_two in coverage
    assert "2/45 roles supplied an exact source-bound review" in coverage
    assert "reviewing role IDs: ['RO-01', 'RO-02']" in coverage
    assert "reviewing role IDs: ['RO-03']" in coverage
    assert "option status role counts {'preserved': 1}" in coverage
    assert "condition status role counts {'omitted': 1, 'preserved': 1}" in coverage
    assert "CASE:case_summary#2" in coverage
    assert "1/45 roles supplied an exact source-bound review" in coverage
    assert "option status role counts {'partly_preserved': 1}" in coverage
    assert "condition status role counts {'unclear': 1}" in coverage
    assert "majority supports surgery" not in coverage.casefold()
    assert "source-opinion review coverage" not in unresolved.casefold()
    assert any("No proposition-level consensus" in item for item in report.unresolved_disagreements)
    assert "opinion label containing a positive consensus assertion" in flags
    assert "conflicting option statuses for RO-02" in flags
    assert "lacks an exact contiguous excerpt" in flags
    assert "Round 2 source-reference audit: 1/45" in flags
    assert "Round 3 source-reference audit: 1/45" in flags
    assert "R2 duplicate-only source-reference flag" in flags
    assert "Malformed paired-source wording" in flags
    assert "Round 3 source-reference detail (1 distinct role(s): RO-03)" in flags
    assert "Round 2 source-reference detail (1 distinct role(s): RO-01)" in flags
    assert "unanimously" not in unresolved.casefold()




def test_source_opinion_position_summary_keeps_each_server_identified_opinion_separate():
    case_summary = (
        "The surgical note recommends a surgery-led assessment first, conditional on complete local staging. "
        "The medical oncology note favours discussing a preoperative multimodality sequence, conditional on MRI staging and fitness assessment."
    )
    from app.services.case_integrity import extract_attributed_note_opinions
    register = extract_attributed_note_opinions(case_summary)
    assert [item["source_id"] for item in register] == [
        "CASE:case_summary#1",
        "CASE:case_summary#2",
    ]

    def make_row(role_id, responses):
        return {
            "agent_id": role_id,
            "agent_name": role_id,
            "status": "completed",
            "result": {"source_opinion_responses": responses},
        }

    def response(source, position):
        return {
            "source_id": source["source_id"],
            "source_excerpt": source["source_excerpt"],
            "position_on_source_opinion": position,
        }

    rows = [
        make_row("RO-01", [
            response(register[0], "supports"),
            response(register[1], "conditional"),
        ]),
        make_row("MO-01", [
            response(register[0], "opposes"),
            response(register[1], "supports"),
        ]),
        make_row("SO-01", [
            response(register[0], "conditional"),
        ]),
    ]

    summary, flags = build_source_opinion_position_summary(rows, case_summary)
    first = next(item for item in summary if "CASE:case_summary#1" in item)
    second = next(item for item in summary if "CASE:case_summary#2" in item)

    assert "supports 1 [RO-01]" in first
    assert "opposes 1 [MO-01]" in first
    assert "conditional 1 [SO-01]" in first
    assert "no response 0 [none]" in first
    assert "conditional 1 [RO-01]" in second
    assert "supports 1 [MO-01]" in second
    assert "no response 1 [SO-01]" in second
    assert "not a vote, verified clinical finding, or consensus" in first
    assert flags == []


def test_source_opinion_position_summary_excludes_duplicate_unbound_and_missing_positions():
    case_summary = (
        "The surgical note recommends a surgery-led assessment first, conditional on complete local staging."
    )
    from app.services.case_integrity import extract_attributed_note_opinions
    source = extract_attributed_note_opinions(case_summary)[0]

    rows = [
        {
            "agent_id": "RO-01",
            "status": "completed",
            "result": {
                "source_opinion_responses": [
                    {
                        "source_id": source["source_id"],
                        "source_excerpt": source["source_excerpt"],
                        "position_on_source_opinion": "supports",
                    },
                    {
                        "source_id": source["source_id"],
                        "source_excerpt": source["source_excerpt"],
                        "position_on_source_opinion": "opposes",
                    },
                ]
            },
        },
        {
            "agent_id": "MO-01",
            "status": "completed",
            "result": {
                "source_opinion_responses": [
                    {
                        "source_id": source["source_id"],
                        "source_excerpt": "not the exact server-bound excerpt",
                        "position_on_source_opinion": "supports",
                    }
                ]
            },
        },
        {
            "agent_id": "SO-01",
            "status": "completed",
            "result": {
                "source_opinion_responses": [
                    {
                        "source_id": source["source_id"],
                        "source_excerpt": source["source_excerpt"],
                    }
                ]
            },
        },
        {
            "agent_id": "DS-01",
            "status": "completed",
            "result": {
                "source_opinion_responses": [
                    {
                        "source_id": "CASE:case_summary#99",
                        "source_excerpt": "unregistered excerpt",
                        "position_on_source_opinion": "supports",
                    }
                ]
            },
        },
    ]

    summary, flags = build_source_opinion_position_summary(rows, case_summary)
    line = summary[0]

    assert "supports 0 [none]" in line
    assert "opposes 0 [none]" in line
    assert "ambiguous duplicate response 1 [RO-01]" in line
    assert "invalid excerpt binding 1 [MO-01]" in line
    assert "position not reported 1 [SO-01]" in line
    assert any("unregistered source-opinion ID CASE:case_summary#99" in item for item in flags)
    assert any("did not report a valid position_on_source_opinion" in item for item in flags)


def test_recorded_agreements_quarantine_overbroad_claims_and_unsupplied_sources():
    rows = [{
        "agent_id": "RO-01",
        "agent_name": "Radiation Oncologist",
        "status": "completed",
        "result": {
            "position": "insufficient_information",
            "source_peer_ids": ["MO-01"],
            "agreements": [
                "All peers agree that a final sequence cannot be selected yet.",
                "R1:RO-01 through R1:SV-02 agree that staging is incomplete.",
                "R1:MO-01 | R1:RO-03",
                "R1:MO-01 agrees that the source record does not establish a final sequence.",
            ],
        },
    }]
    flags = []
    agreements = build_recorded_agreements(rows, [], integrity_flags=flags)

    assert len(agreements) == 1
    assert "R1:MO-01 agrees" in agreements[0]
    joined = " ".join(flags).casefold()
    assert "overbroad peer/consensus assertion withheld" in joined
    assert "broad role range" in joined
    assert "only source identifiers" in joined


def test_source_excerpt_id_conflicts_are_flagged_even_when_one_review_has_an_invalid_peer_reference():
    source_one = "Surgical service note records a conditional surgical assessment."
    source_two = "Medical oncology note records a conditional systemic review."
    case_summary = f"Referral contains two notes. {source_one} {source_two}"
    rows = _rows("result", ["insufficient_information"] * 45)

    rows[0]["result"]["source_peer_ids"] = ["RO-02"]
    rows[0]["result"]["source_opinion_reviews"] = [{
        "source_id": "CASE:case_summary#1",
        "opinion_label": "Surgical service note",
        "source_excerpt": source_one,
        "option_status": "preserved",
        "conditions_status": "preserved",
        "source_reference_ids": ["CASE:case_summary#1", "R2:RO-02"],
    }]
    rows[1]["result"]["source_peer_ids"] = ["RO-03"]
    rows[1]["result"]["source_opinion_reviews"] = [{
        "source_id": "CASE:case_summary#1",
        "opinion_label": "Medical oncology note",
        "source_excerpt": source_two,
        "option_status": "omitted",
        "conditions_status": "omitted",
        # This peer was not supplied to RO-02, so this review is not countable.
        "source_reference_ids": ["CASE:case_summary#1", "R2:RO-04"],
    }]

    coverage, flags = build_source_opinion_review_coverage(rows, case_summary)

    assert coverage == []
    assert any(
        "CASE:case_summary#1 maps to more than one exact case-summary excerpt" in item
        for item in flags
    )
    assert any(
        "does not cite an R2 peer recorded as supplied to that role" in item
        for item in flags
    )

def test_high_volume_source_excerpt_failures_are_summarised_by_distinct_role():
    case_summary = (
        "Referral note records a conditional option pending MRI staging. "
        "No further exact opinion excerpts were supplied."
    )
    rows = _rows("result", ["insufficient_information"] * 45)
    for index in range(3):
        role_id = f"RO-{index + 1:02d}"
        peer_id = f"RO-{index + 10:02d}"
        rows[index]["result"]["source_peer_ids"] = [peer_id]
        rows[index]["result"]["source_opinion_reviews"] = [{
            "source_id": "CASE:case_summary#1",
            "opinion_label": "Unverified attributed opinion",
            "source_excerpt": f"Paraphrased excerpt for {role_id}, not present verbatim.",
            "option_status": "unclear",
            "conditions_status": "unclear",
            "source_reference_ids": ["CASE:case_summary#1", f"R2:{peer_id}"],
        }]

    coverage, flags = build_source_opinion_review_coverage(rows, case_summary)
    joined_flags = " ".join(flags)

    assert coverage == []
    assert (
        "R3 source-opinion exact-excerpt audit: 3 finding(s) across "
        "3 distinct role(s): ['RO-01', 'RO-02', 'RO-03']."
    ) in joined_flags
    assert "from RO-01 lacks an exact contiguous excerpt" in joined_flags

def test_final_chair_report_keeps_high_volume_source_excerpt_audit_visible():
    case = SyntheticCase(
        scenario_title="High-volume source-excerpt final-boundary regression",
        case_summary="Referral note records two conditional options pending staging.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)

    for index in range(30):
        role_id = f"RO-{index + 1:02d}"
        peer_id = f"RO-{index + 11:02d}"
        round3[index]["result"]["source_peer_ids"] = [peer_id]
        round3[index]["result"]["source_opinion_reviews"] = [{
            "source_id": "CASE:case_summary#1",
            "opinion_label": "Unverified attributed opinion",
            "source_excerpt": f"Paraphrased source excerpt for {role_id}.",
            "option_status": "unclear",
            "conditions_status": "unclear",
            "source_reference_ids": ["CASE:case_summary#1", f"R2:{peer_id}"],
        }]

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )
    flags = " ".join(report.case_data_integrity_flags)

    assert (
        "R3 source-opinion exact-excerpt audit: 30 finding(s) across "
        "30 distinct role(s)"
    ) in flags
    assert "from RO-01 lacks an exact contiguous excerpt" in flags
    assert "from RO-03 lacks an exact contiguous excerpt" in flags
    assert report.source_opinion_review_coverage == []
    assert len(report.case_data_integrity_flags) <= SECTION_LIMITS["case_data_integrity_flags"]




def test_completion_disclosure_names_absent_configured_ids_without_conflating_failed_or_unexpected_rows():
    expected_role_ids = {"RO-01", "MO-01", "SO-01"}
    rows = [
        {
            "agent_id": "RO-01",
            "status": "completed",
            "assessment": {"position": "insufficient_information"},
        },
        {
            "agent_id": "MO-01",
            "status": "failed",
            "assessment": None,
        },
        {
            "agent_id": "XX-99",
            "status": "completed",
            "assessment": {"position": "supports"},
        },
    ]

    disclosures = _round_completion_disclosures(
        rows,
        "assessment",
        1,
        expected_role_ids=expected_role_ids,
    )
    absent = [item for item in disclosures if "configured role row(s) are absent" in item]
    failed = [item for item in disclosures if "no usable completed" in item]
    unexpected = [item for item in disclosures if "unexpected role ID(s)" in item]

    assert len(absent) == 1
    assert "SO-01" in absent[0]
    assert "RO-01" not in absent[0]
    assert "MO-01" not in absent[0]
    assert len(failed) == 1
    assert "MO-01" in failed[0]
    assert len(unexpected) == 1
    assert "XX-99" in unexpected[0]
    assert "XX-99" not in absent[0]


def test_final_chair_discloses_failed_and_absent_role_inputs_without_counting_them():
    case = SyntheticCase(
        scenario_title="Chair missing-agent disclosure regression",
        case_summary="Fictional incomplete case for deterministic completion accounting.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    round2[4]["status"] = "failed"
    round2[4]["error_message"] = "Synthetic agent failure."
    round3.pop()

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )
    unresolved = " ".join(report.unresolved_disagreements)
    flags = " ".join(report.case_data_integrity_flags)

    assert "Round 2: 1 distinct role(s) have no usable completed result contribution" in unresolved
    assert "RO-05" in unresolved
    assert "Round 3: the Chair input contains 44 distinct identified role rows of 45 configured roles" in unresolved
    assert "At least 1 role row(s) are absent" in unresolved
    assert "RO-05" in flags
    assert "Saved-input completeness" in report.chair_conclusion
    assert "Round 2: 1 distinct role(s) have no usable completed result contribution" in report.chair_conclusion
    assert "Round 3: the Chair input contains 44 distinct identified role rows of 45 configured roles" in report.chair_conclusion
    assert "Round 2: 44/44 insufficient-information" in report.overall_educational_synthesis
    assert "Round 3: 44/44 insufficient-information" in report.overall_educational_synthesis


def test_chair_synthesis_traces_examples_to_saved_role_records_in_all_three_rounds():
    case = SyntheticCase(
        scenario_title="Saved contribution synthesis traceability regression",
        case_summary="Fictional incomplete case; the staging status remains unknown.",
    )
    round1 = _rows("assessment", ["insufficient_information"] * 45)
    round2 = _rows("result", ["insufficient_information"] * 45)
    round3 = _rows("result", ["insufficient_information"] * 45)
    # Give each seeded example its own position group so the deterministic
    # one-example-per-position selector can be asserted unambiguously.
    round1[0]["assessment"]["position"] = "conditional"
    round2[0]["result"]["position"] = "supports"
    round2[1]["result"]["position"] = "conditional"
    round3[0]["result"]["position"] = "supports"
    round3[1]["result"]["position"] = "opposes"
    round3[2]["result"]["position"] = "conditional"

    round1[0]["assessment"]["provisional_conclusion"] = (
        "The R1 contribution records that the supplied information is insufficient "
        "to determine the educational question."
    )
    round2[1]["result"]["provisional_conclusion"] = (
        "The R2 contribution records that the debate retained distinct, attributed views."
    )
    round3[2]["result"]["provisional_conclusion"] = (
        "The R3 contribution records that one source-attribution question remains unresolved."
    )

    report = ensure_chair_report_completeness(
        _empty_report(), case, round1, round2, round3
    )
    synthesis = report.overall_educational_synthesis

    assert "Round 1 saved role positions and attributed examples" in synthesis
    assert "Example RO-01" in synthesis
    assert "R1 contribution records" in synthesis
    assert "Round 2 saved role positions and attributed examples" in synthesis
    assert "Example RO-02" in synthesis
    assert "R2 contribution records" in synthesis
    assert "Round 3 saved role positions and attributed examples" in synthesis
    assert "Example RO-03" in synthesis
    assert "R3 contribution records" in synthesis
    assert "not exhaustive" in synthesis
    assert "verified clinical facts" in synthesis
    assert "not an exhaustive summary" in synthesis
