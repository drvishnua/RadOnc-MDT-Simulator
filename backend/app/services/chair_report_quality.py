"""Completeness and consistency safeguards for the final Chair report."""

from __future__ import annotations

from collections import Counter, defaultdict

from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase


ROUND_SOURCES = (
    (1, "assessment"),
    (2, "result"),
    (3, "result"),
)

SECTION_LIMITS = {
    "consensus_points": 15,
    "unresolved_disagreements": 15,
    "minority_and_dissenting_views": 15,
    "major_uncertainties": 20,
    "missing_information_before_real_world_review": 20,
    "patient_and_family_considerations": 15,
    "feasibility_and_resource_considerations": 15,
    "governance_and_safeguarding_considerations": 15,
    "evidence_limitations": 15,
}


def _entries(rows: list[dict], field: str) -> list[tuple[dict, dict]]:
    return [
        (row, row[field])
        for row in rows
        if isinstance(row.get(field), dict)
    ]


def _unique(values: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = " ".join(value.split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
        if len(result) >= limit:
            break
    return result


def _position_counts(rows: list[dict], field: str) -> Counter:
    return Counter(
        item.get("position")
        for _, item in _entries(rows, field)
        if item.get("position")
    )


def _minority_history(
    round1_rows: list[dict],
    round2_rows: list[dict],
    round3_rows: list[dict],
) -> list[str]:
    by_agent: dict[str, dict[str, object]] = defaultdict(
        lambda: {"name": "Role", "events": []}
    )
    for round_number, rows, field in (
        (1, round1_rows, "assessment"),
        (2, round2_rows, "result"),
        (3, round3_rows, "result"),
    ):
        entries = _entries(rows, field)
        counts = Counter(
            item.get("position")
            for _, item in entries
            if item.get("position")
        )
        if not counts:
            continue
        modal_position = counts.most_common(1)[0][0]
        for row, item in entries:
            position = item.get("position")
            if not position or position == modal_position:
                continue
            agent_id = str(row.get("agent_id") or "unknown-role")
            record = by_agent[agent_id]
            record["name"] = row.get("agent_name") or record["name"]
            conclusion = " ".join(
                str(item.get("provisional_conclusion") or "").split()
            )
            if len(conclusion) > 180:
                conclusion = conclusion[:179].rstrip() + "…"
            event = f"Round {round_number}: {position}"
            if conclusion:
                event += f" — {conclusion}"
            record["events"].append(event)

    output = []
    for agent_id in sorted(by_agent):
        record = by_agent[agent_id]
        output.append(
            f"{agent_id} — {record['name']}: "
            + "; ".join(record["events"])
        )
    return output[:10]


def ensure_chair_report_completeness(
    report: FinalMDTReport,
    case: SyntheticCase,
    round1_rows: list[dict],
    round2_rows: list[dict],
    round3_rows: list[dict],
) -> FinalMDTReport:
    """Fill empty report sections with traceable findings or explicit absence notes.

    Existing source-grounded reconciliation is retained. This function is a final
    defensive layer so the UI and live validator never mistake an empty array for
    a completed analysis.
    """
    data = report.model_dump()
    rows_by_round = (round1_rows, round2_rows, round3_rows)
    counts_by_round = {
        round_number: _position_counts(rows, field)
        for (round_number, field), rows in zip(ROUND_SOURCES, rows_by_round)
    }
    final_counts = counts_by_round[3]

    for field, limit in SECTION_LIMITS.items():
        data[field] = _unique(data.get(field) or [], limit)

    if not data["consensus_points"]:
        if (
            final_counts.get("insufficient_information")
            and not final_counts.get("supports")
            and not final_counts.get("opposes")
        ):
            note = (
                "No definitive consensus point was established: Round 3 recorded "
                + ", ".join(
                    f"{count}/{sum(final_counts.values())} {position.replace('_', '-')}"
                    for position, count in sorted(final_counts.items())
                )
                + "; this is insufficient information, not unanimous agreement."
            )
        else:
            note = (
                "No repeated cross-role agreement met the reporting threshold in "
                "the saved Round-2 contributions; position labels are descriptive, "
                "not votes."
            )
        data["consensus_points"] = [note]

    if not data["unresolved_disagreements"]:
        if len(final_counts) > 1:
            distribution = ", ".join(
                f"{count}/{sum(final_counts.values())} {position.replace('_', '-')}"
                for position, count in sorted(final_counts.items())
            )
            note = (
                "Round-3 positions were non-uniform ("
                + distribution
                + "); these labels do not by themselves establish opposing treatment views."
            )
        else:
            earlier_variation = any(
                len(counts_by_round[round_number]) > 1
                for round_number in (1, 2)
            )
            if earlier_variation:
                note = (
                    "Round-3 position labels were uniform, while at least one earlier "
                    "round contained differing positions. Earlier role-level variation "
                    "is retained in the minority-view history; uniform labels do not "
                    "prove that clinical questions are resolved."
                )
            else:
                note = (
                    "No non-uniform position labels were recorded across the completed "
                    "rounds. This absence of recorded label variation is not proof of "
                    "clinical unanimity or clinical validity."
                )
        data["unresolved_disagreements"] = [note]

    if not data["minority_and_dissenting_views"]:
        history = _minority_history(round1_rows, round2_rows, round3_rows)
        data["minority_and_dissenting_views"] = history or [
            "No non-modal role position was recorded in Rounds 1–3. This does not "
            "establish unanimous clinical agreement; inspect the full role contributions."
        ]

    uncertainty_items = list(case.known_unknowns or [])
    missing_items = list(case.known_unknowns or [])
    patient_items = [
        f"Recorded patient goal/preference: {item}"
        for item in (case.patient_goals or [])
    ]
    patient_items.extend(case.social_context or [])
    feasibility_items = list(case.resource_context or [])
    feasibility_items.extend(
        item
        for item in (case.social_context or [])
        if any(
            term in item.casefold()
            for term in ("support", "adher", "access", "transport", "caregiver")
        )
    )
    evidence_items: list[str] = []

    for _, rows, field in (
        (1, round1_rows, "assessment"),
        (2, round2_rows, "result"),
        (3, round3_rows, "result"),
    ):
        for _, item in _entries(rows, field):
            uncertainty_items.extend(item.get("unknowns") or [])
            uncertainty_items.extend(item.get("remaining_unknowns") or [])
            uncertainty_items.extend(item.get("uncertainty_notes") or [])
            missing_items.extend(item.get("unknowns") or [])
            missing_items.extend(item.get("remaining_unknowns") or [])
            evidence_items.extend(item.get("evidence_gaps") or [])
            for candidate in (
                item.get("unknowns") or []
            ) + (
                item.get("remaining_unknowns") or []
            ):
                lowered = str(candidate).casefold()
                if any(
                    term in lowered
                    for term in ("patient", "family", "preference", "goal", "support")
                ):
                    patient_items.append(str(candidate))

    if not data["major_uncertainties"]:
        data["major_uncertainties"] = _unique(
            uncertainty_items,
            SECTION_LIMITS["major_uncertainties"],
        ) or [
            "No explicit uncertainty item was recorded in the case snapshot or role "
            "contributions; this does not establish that uncertainty is absent."
        ]

    if not data["missing_information_before_real_world_review"]:
        data["missing_information_before_real_world_review"] = _unique(
            missing_items,
            SECTION_LIMITS["missing_information_before_real_world_review"],
        ) or [
            "No specific missing-information item was recorded. Completeness of the "
            "synthetic case has not been independently verified."
        ]

    if not data["patient_and_family_considerations"]:
        data["patient_and_family_considerations"] = _unique(
            patient_items,
            SECTION_LIMITS["patient_and_family_considerations"],
        ) or [
            "Patient goals, preferences, and family context were not supplied; none "
            "should be inferred from this simulation."
        ]

    if not data["feasibility_and_resource_considerations"]:
        data["feasibility_and_resource_considerations"] = _unique(
            feasibility_items,
            SECTION_LIMITS["feasibility_and_resource_considerations"],
        ) or [
            "No structured resource or access context was supplied; feasibility cannot "
            "be assessed from the saved case."
        ]

    if not data["governance_and_safeguarding_considerations"]:
        data["governance_and_safeguarding_considerations"] = [
            "Synthetic educational simulation only; not a clinical decision or treatment instruction.",
            "Consent, patient preferences, safeguarding, and documentation require qualified review in any real setting.",
            "No real-patient data should be entered into this educational workflow.",
        ]

    if not data["evidence_limitations"]:
        data["evidence_limitations"] = _unique(
            [
                "Evidence retrieval and citation verification are not connected.",
                "Clinical accuracy and guideline concordance have not been evaluated.",
                *evidence_items,
            ],
            SECTION_LIMITS["evidence_limitations"],
        )

    return FinalMDTReport.model_validate(data)
