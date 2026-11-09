"""Completeness and consistency safeguards for the final Chair report."""

from __future__ import annotations

from collections import Counter, defaultdict
import re

from app.round_schemas import FinalMDTReport
from app.schemas import SyntheticCase
from app.services.case_integrity import audit_unverified_case_claims, build_case_report_title


ROUND_SOURCES = (
    (1, "assessment"),
    (2, "result"),
    (3, "result"),
)

SECTION_LIMITS = {
    "consensus_points": 15,
    "recorded_agreements": 90,
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
        if row.get("status") == "completed" and isinstance(row.get(field), dict)
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


def validate_consensus_points(report: dict) -> None:
    """Require explicit empty consensus until proposition-level support is implemented."""
    points = report.get("consensus_points")
    if not isinstance(points, list):
        raise ValueError("Chair consensus_points must be a list.")
    if points:
        raise ValueError(
            "Chair consensus_points must remain empty until proposition-level support is implemented."
        )


def _note_quarantined_claims(
    integrity_flags: list[str] | None,
    source_label: str,
    findings: list[str],
) -> None:
    if integrity_flags is None:
        return
    integrity_flags.extend(
        f"Quarantined {source_label}: {finding}"
        for finding in findings
    )


def _safe_text_items(
    case: SyntheticCase,
    values: object,
    field: str,
    integrity_flags: list[str] | None = None,
    source_label: str = "Chair text",
) -> list[str]:
    """Keep only individually auditable strings; retain quarantine findings."""
    safe: list[str] = []
    if not isinstance(values, (list, tuple)):
        return safe
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        findings = audit_unverified_case_claims(case, {field: value})
        if findings:
            _note_quarantined_claims(integrity_flags, source_label, findings)
            continue
        safe.append(value)
    return safe


def _safe_role_text_items(
    case: SyntheticCase,
    payload: dict,
    field: str,
    integrity_flags: list[str] | None = None,
    source_label: str = "role contribution",
) -> list[str]:
    """Exclude unsupported role text without altering the saved contribution."""
    return _safe_text_items(
        case,
        payload.get(field),
        field,
        integrity_flags=integrity_flags,
        source_label=source_label,
    )


def _position_counts(rows: list[dict], field: str) -> Counter:
    return Counter(
        item.get("position")
        for _, item in _entries(rows, field)
        if item.get("position")
    )


def _format_position_counts(counts: Counter) -> str:
    total = sum(counts.values())
    if not total:
        return "no valid positions recorded"
    labels = {
        "insufficient_information": "insufficient-information",
        "conditional": "conditional",
        "supports": "supports",
        "opposes": "opposes",
    }
    return ", ".join(
        f"{count}/{total} {labels.get(position, position)}"
        for position, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _unique_modal_position(counts: Counter) -> str | None:
    """Return a modal label only when one position is uniquely most frequent."""
    if not counts:
        return None
    highest = max(counts.values())
    modes = [position for position, count in counts.items() if count == highest]
    return modes[0] if len(modes) == 1 else None


def _minority_history(
    round1_rows: list[dict],
    round2_rows: list[dict],
    round3_rows: list[dict],
    case: SyntheticCase | None = None,
    integrity_flags: list[str] | None = None,
) -> list[str]:
    """Keep role-position history while quarantining unsupported conclusions.

    Stable insufficient-information roles are uncertainty contributors, not dissenters.
    Original role records remain stored unchanged.
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
            withheld = False
            if conclusion and case is not None:
                findings = audit_unverified_case_claims(case, {"provisional_conclusion": conclusion})
                if findings:
                    withheld = True
                    _note_quarantined_claims(
                        integrity_flags,
                        f"R{round_number} {agent_id} minority-history conclusion",
                        findings,
                    )
            if len(conclusion) > 180:
                conclusion = conclusion[:179].rstrip() + "…"
            event = f"Round {round_number}: {position}"
            if withheld:
                event += " — provisional conclusion withheld by deterministic case-integrity audit"
            elif conclusion:
                event += f" — {conclusion}"
            record["events"].append(event)

    round3_counts = _position_counts(round3_rows, "result")
    final_modal = _unique_modal_position(round3_counts)
    output: list[tuple[int, str]] = []
    for agent_id in sorted(by_agent):
        record = by_agent[agent_id]
        positions = record["positions"]
        if not positions:
            continue
        changed = len(set(positions)) > 1
        final_position = positions[-1]
        qualified_minority = (
            final_position in {"conditional", "supports", "opposes"}
            and (final_modal is None or final_position != final_modal)
        )
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


def build_recorded_agreements(
    round2_rows: list[dict],
    round3_rows: list[dict],
    case: SyntheticCase | None = None,
    integrity_flags: list[str] | None = None,
) -> list[str]:
    """Preserve only auditable, role-attributed agreement statements, never consensus."""
    output: list[str] = []
    for round_number, rows in ((2, round2_rows), (3, round3_rows)):
        for row, item in _entries(rows, "result"):
            role_id = str(row.get("agent_id") or "unknown-role")
            role_name = str(row.get("agent_name") or "Role")
            statements: list[str] = []
            seen: set[str] = set()
            for value in item.get("agreements") or []:
                if not isinstance(value, str):
                    continue
                cleaned = " ".join(value.split())
                key = cleaned.casefold()
                if not cleaned or key in seen:
                    continue
                seen.add(key)
                if case is not None:
                    findings = audit_unverified_case_claims(case, {"agreement": cleaned})
                    if findings:
                        _note_quarantined_claims(
                            integrity_flags,
                            f"R{round_number} {role_id} agreement",
                            findings,
                        )
                        continue
                statements.append(cleaned)
            if statements:
                output.append(
                    f"Round {round_number} — {role_id} ({role_name}); "
                    "role-recorded agreement statements, not independently validated "
                    "as a shared proposition: " + " | ".join(statements)
                )
    return output[:SECTION_LIMITS["recorded_agreements"]]

def ensure_chair_report_completeness(
    report: FinalMDTReport,
    case: SyntheticCase,
    round1_rows: list[dict],
    round2_rows: list[dict],
    round3_rows: list[dict],
) -> FinalMDTReport:
    """Rebuild the Chair report from saved records and quarantine unsupported text.

    This is the final report boundary. It never rewrites source contributions; it
    removes an unsafe statement only from the derived Chair view and records why.
    """
    data = report.model_dump()
    data["report_title"] = build_case_report_title(case)
    rows_by_round = (round1_rows, round2_rows, round3_rows)
    counts_by_round = {
        round_number: _position_counts(rows, field)
        for (round_number, field), rows in zip(ROUND_SOURCES, rows_by_round)
    }
    final_counts = counts_by_round[3]
    quarantine_flags: list[str] = []
    stored_integrity_flags: list[str] = []

    for round_number, rows, field in (
        (1, round1_rows, "assessment"),
        (2, round2_rows, "result"),
        (3, round3_rows, "result"),
    ):
        for row, item in _entries(rows, field):
            role_id = str(row.get("agent_id") or "unknown-role")
            for flag in item.get("case_data_integrity_flags") or []:
                if isinstance(flag, str) and flag.strip():
                    stored_integrity_flags.append(f"R{round_number} {role_id}: {flag}")

    # No proposition-level support exists in the saved contribution schema.
    # Position labels alone therefore cannot create a consensus point or status.
    data["consensus_points"] = []
    if final_counts.get("supports") and final_counts.get("opposes"):
        data["consensus_status"] = "no_consensus"
        data["chair_conclusion"] = (
            "The saved Round-3 role positions include both supporting and opposing views. "
            "The simulated MDT did not reach a single position; review the attributed "
            "contributions and their unresolved conditions."
        )
    else:
        data["consensus_status"] = "insufficient_information"
        data["chair_conclusion"] = (
            "No proposition-level consensus can be established from the saved structured "
            "contributions. No treatment recommendation can be made from this educational record."
        )

    for field, limit in SECTION_LIMITS.items():
        data[field] = _unique(data.get(field) or [], limit)

    # Agreements remain individually attributed and are excluded when their text
    # asserts a case finding not supported by the saved case snapshot.
    data["recorded_agreements"] = build_recorded_agreements(
        round2_rows,
        round3_rows,
        case=case,
        integrity_flags=quarantine_flags,
    )

    # Reconstruct source-linked challenge entries from the actual saved R2/R3 rows.
    # This makes the final boundary independently reconcile challenges rather than
    # trusting an earlier Chair draft/reconciliation string.
    saved_challenge_items: list[str] = []
    for round_number, rows in ((2, round2_rows), (3, round3_rows)):
        for row, item in _entries(rows, "result"):
            role_id = str(row.get("agent_id") or "unknown-role")
            role_name = str(row.get("agent_name") or "Role")
            safe_challenges = _safe_role_text_items(
                case,
                item,
                "substantive_challenges",
                quarantine_flags,
                f"R{round_number} {role_id} substantive challenge",
            )
            for challenge in safe_challenges:
                cleaned = " ".join(challenge.split())
                if len(cleaned) > 260:
                    cleaned = cleaned[:259].rstrip() + "…"
                saved_challenge_items.append(
                    f"Round {round_number} recorded challenge — {role_id} ({role_name}): {cleaned}"
                )
    data["unresolved_disagreements"] = _unique(
        [*(data.get("unresolved_disagreements") or []), *saved_challenge_items],
        SECTION_LIMITS["unresolved_disagreements"],
    )

    if not data["unresolved_disagreements"]:
        if len(final_counts) > 1:
            distribution = ", ".join(
                f"{count}/{sum(final_counts.values())} {position.replace('_', '-')}"
                for position, count in sorted(final_counts.items())
            )
            highest_count = max(final_counts.values())
            tied_positions = sorted(
                position for position, count in final_counts.items() if count == highest_count
            )
            if len(tied_positions) > 1:
                note = (
                    "Round-3 positions have no unique modal label because the highest "
                    "counts are tied (" + distribution + "). All non-insufficient position "
                    "groups are retained; the labels do not by themselves establish opposing treatment views."
                )
            else:
                note = (
                    "Round-3 positions were non-uniform (" + distribution
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
                "Round-3 positions were uniform (" + distribution
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

    # Challenges are useful only when their case claims pass the same deterministic
    # case-integrity audit applied to role-authored uncertainty and evidence-gap text.
    data["unresolved_disagreements"] = _unique(
        _safe_text_items(
            case,
            data["unresolved_disagreements"],
            "unresolved_disagreement",
            integrity_flags=quarantine_flags,
            source_label="Chair unresolved disagreement",
        ),
        SECTION_LIMITS["unresolved_disagreements"],
    )
    if not data["unresolved_disagreements"]:
        data["unresolved_disagreements"] = [
            "No auditable unresolved-disagreement text was retained. This is not evidence that all clinical questions are resolved.",
            "No proposition-level consensus is established by free-text agreement notes; position labels and repeated wording are not counted as votes.",
        ]

    history = _minority_history(
        round1_rows,
        round2_rows,
        round3_rows,
        case=case,
        integrity_flags=quarantine_flags,
    )
    data["minority_and_dissenting_views"] = history or [
        "No genuine conditional/minority position or position change was identified in the saved rounds. "
        "Stable insufficient-information roles are represented in uncertainty sections, not as dissent."
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

    for round_number, rows, field in (
        (1, round1_rows, "assessment"),
        (2, round2_rows, "result"),
        (3, round3_rows, "result"),
    ):
        for row, item in _entries(rows, field):
            role_id = str(row.get("agent_id") or "unknown-role")
            source_label = f"R{round_number} {role_id}"
            role_unknowns = _safe_role_text_items(
                case, item, "unknowns", quarantine_flags, source_label
            )
            role_remaining_unknowns = _safe_role_text_items(
                case, item, "remaining_unknowns", quarantine_flags, source_label
            )
            role_uncertainty_notes = _safe_role_text_items(
                case, item, "uncertainty_notes", quarantine_flags, source_label
            )
            uncertainty_items.extend(role_unknowns)
            uncertainty_items.extend(role_remaining_unknowns)
            uncertainty_items.extend(role_uncertainty_notes)
            missing_items.extend(role_unknowns)
            missing_items.extend(role_remaining_unknowns)
            evidence_items.extend(
                _safe_role_text_items(
                    case, item, "evidence_gaps", quarantine_flags, source_label
                )
            )
            for candidate in role_unknowns + role_remaining_unknowns:
                lowered = candidate.casefold()
                if any(term in lowered for term in ("patient", "family", "preference", "goal", "support")):
                    patient_items.append(candidate)

    safe_chair_uncertainties = _safe_text_items(
        case,
        data.get("major_uncertainties"),
        "major_uncertainty",
        integrity_flags=quarantine_flags,
        source_label="Chair major uncertainty",
    )
    safe_chair_missing = _safe_text_items(
        case,
        data.get("missing_information_before_real_world_review"),
        "missing_information",
        integrity_flags=quarantine_flags,
        source_label="Chair missing-information item",
    )
    data["major_uncertainties"] = _unique(
        [*uncertainty_items, *safe_chair_uncertainties],
        SECTION_LIMITS["major_uncertainties"],
    ) or [
        "No explicit uncertainty item was recorded in the case snapshot or role "
        "contributions; this does not establish that uncertainty is absent."
    ]
    data["missing_information_before_real_world_review"] = _unique(
        [*missing_items, *safe_chair_missing],
        SECTION_LIMITS["missing_information_before_real_world_review"],
    ) or [
        "No specific missing-information item was recorded. Completeness of the "
        "supplied case has not been independently verified."
    ]

    # These sections are reconstructed from structured case fields and safe role
    # unknowns; pre-existing Chair prose is never allowed to replace their sources.
    data["patient_and_family_considerations"] = _unique(
        patient_items,
        SECTION_LIMITS["patient_and_family_considerations"],
    ) or [
        "Patient goals, preferences, and family context were not supplied; none "
        "should be inferred from this simulation."
    ]
    data["feasibility_and_resource_considerations"] = _unique(
        feasibility_items,
        SECTION_LIMITS["feasibility_and_resource_considerations"],
    ) or [
        "No structured resource or access context was supplied; feasibility cannot "
        "be assessed from the saved case."
    ]
    data["governance_and_safeguarding_considerations"] = [
        "Educational simulation only; not a clinical decision or treatment instruction.",
        "Consent, patient preferences, safeguarding, and documentation require qualified review in any real setting.",
        "No real-patient data should be entered into this educational workflow.",
    ]
    data["evidence_limitations"] = _unique(
        [
            "Evidence retrieval and citation verification are not connected.",
            "Clinical accuracy and guideline concordance have not been evaluated.",
            *evidence_items,
        ],
        SECTION_LIMITS["evidence_limitations"],
    )

    round_distribution = "; ".join(
        f"Round {round_number}: {_format_position_counts(counts_by_round[round_number])}"
        for round_number in (1, 2, 3)
    )
    data["overall_educational_synthesis"] = (
        f"Recorded position distribution — {round_distribution}. These are role-level labels, not "
        "votes; conditional positions are not recast as support or opposition, and a non-uniform "
        "distribution is not described as unanimous. The source case and saved role contributions "
        "may identify missing information, which is listed separately. Evidence retrieval is not "
        "connected, and clinical accuracy was not evaluated."
    )
    data["chair_reflection"] = (
        "This Chair record is reconciled against the saved Round-1, Round-2, and Round-3 "
        "contributions so that counts and minority positions remain traceable. Unsupported "
        "role-authored assertions are withheld from the Chair view and retained in the "
        "source contribution/audit history. This is a structural educational synthesis only; "
        "it does not validate clinical correctness, guideline concordance, or evidence quality."
    )

    data["case_data_integrity_flags"] = _unique(
        [*quarantine_flags, *stored_integrity_flags],
        SECTION_LIMITS["case_data_integrity_flags"],
    ) or [
        "No case-data integrity flags were recorded in completed role contributions by the deterministic checks that ran. "
        "These checks are limited in scope and do not establish the absence of unsupported claims; manual review remains necessary."
    ]

    validate_consensus_points(data)
    return FinalMDTReport.model_validate(data)
