from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.chair_report_quality import (
    SECTION_LIMITS,
    build_recorded_agreements,
    build_source_opinion_review_coverage,
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
        "R3 test flag retained from saved role record."
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
    flags = " ".join(report.case_data_integrity_flags)

    assert "STALE MODEL-CONTROLLED SOURCE REVIEW COVERAGE" not in unresolved
    assert "CASE:case_summary#1" in unresolved
    assert source_one in unresolved
    assert source_two in unresolved
    assert "2/45 roles supplied an exact source-bound review" in unresolved
    assert "reviewing role IDs: ['RO-01', 'RO-02']" in unresolved
    assert "reviewing role IDs: ['RO-03']" in unresolved
    assert "option status role counts {'preserved': 1}" in unresolved
    assert "condition status role counts {'omitted': 1, 'preserved': 1}" in unresolved
    assert "CASE:case_summary#2" in unresolved
    assert "1/45 roles supplied an exact source-bound review" in unresolved
    assert "option status role counts {'partly_preserved': 1}" in unresolved
    assert "condition status role counts {'unclear': 1}" in unresolved
    assert "majority supports surgery" not in unresolved.casefold()
    assert "opinion label containing a positive consensus assertion" in flags
    assert "conflicting option statuses for RO-02" in flags
    assert "lacks an exact contiguous excerpt" in flags
    assert "Round 2 source-reference audit: 1/45" in flags
    assert "Round 3 source-reference audit: 1/45" in flags
    assert "R2 duplicate-only source-reference flag" in flags
    assert "Round 2 source-reference detail (1 distinct role(s): RO-01)" in flags
    assert "unanimously" not in unresolved.casefold()

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
    assert len(report.case_data_integrity_flags) <= SECTION_LIMITS["case_data_integrity_flags"]

