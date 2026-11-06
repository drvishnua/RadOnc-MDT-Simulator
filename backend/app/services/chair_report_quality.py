"""Completeness and consistency safeguards for the final Chair report."""

from __future__ import annotations

from collections import Counter, defaultdict
import re

from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.case_integrity import build_case_report_title


ROUND_SOURCES = (
    (1, "assessment"),
    (2, "result"),
    (3, "result"),
)

SECTION_LIMITS = {
    "consensus_points": 15,
    "unresolved_disagreements": 15,
    "minority_and_dissenting_views": 45,
    "major_uncertainties": 20,
    "missing_information_before_real_world_review": 20,
    "patient_and_family_considerations": 15,
    "feasibility_and_resource_considerations": 15,
    "governance_and_safeguarding_considerations": 15,
    "evidence_limitations": 15,
    "case_data_integrity_flags": 20,
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
    """Keep genuine qualified minority views and auditable position changes.

    Stable insufficient-information roles are uncertainty contributors, not dissenters.
    """
    by_agent: dict[str, dict[str, object]] = defaultdict(lambda: {"name": "Role", "positions": [], "events": []})
    for round_number, rows, field in ((1, round1_rows, "assessment"), (2, round2_rows, "result"), (3, round3_rows, "result")):
        for row, item in _entries(rows, field):
            agent_id = str(row.get("agent_id") or "unknown-role")
            record = by_agent[agent_id]
            record["name"] = row.get("agent_name") or record["name"]
            position = item.get("position")
            if not position:
                continue
            record["positions"].append(position)
            conclusion = " ".join(str(item.get("provisional_conclusion") or "").split())
            if len(conclusion) > 180:
                conclusion = conclusion[:179].rstrip() + "…"
            event = f"Round {round_number}: {position}"
            if conclusion:
                event += f" — {conclusion}"
            record["events"].append(event)

    round3_counts = _position_counts(round3_rows, "result")
    final_modal = round3_counts.most_common(1)[0][0] if round3_counts else None
    output: list[tuple[int, str]] = []
    for agent_id in sorted(by_agent):
        record = by_agent[agent_id]
        positions = record["positions"]
        if not positions:
            continue
        changed = len(set(positions)) > 1
        final_position = positions[-1]
        qualified_minority = final_position in {"conditional", "supports", "opposes"} and final_position != final_modal
        if not (changed or qualified_minority):
            continue
        transition = "Position evolution: " + " → ".join(positions) + ". " if changed else ""
        priority = 0 if qualified_minority else 1
        output.append((priority, f"{agent_id} — {record['name']}: " + transition + "; ".join(record["events"])))
    return [item for _, item in sorted(output)][:45]

def _merge_minority_views(
    history: list[str],
    existing: list[str],
    limit: int = 45,
) -> list[str]:
    """Prefer complete source-derived round histories and retain unmatched Chair entries."""
    agent_pattern = re.compile(r"^([A-Z]{2}-[0-9]{2})\s+—")
    merged: list[str] = []
    seen_agents: set[str] = set()
    seen_text: set[str] = set()

    for entry in history:
        cleaned = " ".join(str(entry).split())
        if not cleaned:
            continue
        match = agent_pattern.match(cleaned)
        if match:
            seen_agents.add(match.group(1))
        key = cleaned.casefold()
        if key not in seen_text:
            merged.append(cleaned)
            seen_text.add(key)

    for entry in existing:
        cleaned = " ".join(str(entry).split())
        if not cleaned:
            continue
        match = agent_pattern.match(cleaned)
        if match and match.group(1) in seen_agents:
            # The source-derived entry already contains that role's complete history.
            continue
        key = cleaned.casefold()
        if key not in seen_text:
            merged.append(cleaned)
            seen_text.add(key)
        if len(merged) >= limit:
            break

    return merged[:limit]


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
    data["report_title"] = build_case_report_title(case)
    rows_by_round = (round1_rows, round2_rows, round3_rows)
    counts_by_round = {
        round_number: _position_counts(rows, field)
        for (round_number, field), rows in zip(ROUND_SOURCES, rows_by_round)
    }
    final_counts = counts_by_round[3]

    for field, limit in SECTION_LIMITS.items():
        data[field] = _unique(data.get(field) or [], limit)

    # An empty consensus_points list is meaningful: free-text agreement
    # notes do not provide proposition-level evidence and must not be replaced
    # with a position-count statement labelled as a consensus point.

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
        elif len(final_counts) == 1 and any(
            final_counts.get(position)
            for position in ("supports", "opposes", "conditional")
        ):
            distribution = ", ".join(
                f"{count}/{sum(final_counts.values())} {position.replace('_', '-')}"
                for position, count in sorted(final_counts.items())
            )
            note = (
                "Round-3 positions were uniform ("
                + distribution
                + "), but the saved contributions do not establish one shared, "
                "proposition-level educational option. Uniform labels alone do not prove consensus."
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

    if not any("proposition-level consensus" in item.casefold() for item in data["unresolved_disagreements"]):
        data["unresolved_disagreements"] = _unique(
            [
                *data["unresolved_disagreements"],
                "No proposition-level consensus is established by free-text agreement notes; "
                "position labels and repeated wording are not counted as votes.",
            ],
            SECTION_LIMITS["unresolved_disagreements"],
        )

    history = _minority_history(round1_rows, round2_rows, round3_rows)
    # Saved role records are authoritative; ignore model-generated entries for
    # stable insufficient-information roles.
    data["minority_and_dissenting_views"] = history or [
        "No genuine conditional/minority position or position change was identified in the saved rounds. "
        "Stable insufficient-information roles are represented in uncertainty sections, not as dissent."
    ]

    integrity_flags: list[str] = []
    for rows, field in ((round1_rows, "assessment"), (round2_rows, "result"), (round3_rows, "result")):
        for _, item in _entries(rows, field):
            integrity_flags.extend(item.get("case_data_integrity_flags") or [])
    data["case_data_integrity_flags"] = _unique(integrity_flags, SECTION_LIMITS["case_data_integrity_flags"]) or [
        "No unsupported stage, demographic, or absence claim was detected by the deterministic case-data audit."
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
