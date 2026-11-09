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


_POSITIVE_CONSENSUS_PATTERN = re.compile(
    r"\b(?:unanimous(?:ly)?|all\s+(?:\d+\s+)?roles?|every\s+role|all\s+specialists|"
    r"the\s+majority|majority|most\s+(?:roles|specialists))\b.{0,120}\b"
    r"(?:agree(?:s|d)?|support(?:s|ed)?|endorse(?:s|d)?|approve(?:s|ed)?|"
    r"recommend(?:s|ed)?|back(?:s|ed)?|favour(?:s|ed)?|favor(?:s|ed)?)\b"
    r"|\b(?:consensus|unanimity)\s+(?:was|has\s+been|is)\s+"
    r"(?:reached|achieved|established|confirmed)\b",
    re.IGNORECASE,
)


_NEGATED_CONSENSUS_PATTERN = re.compile(
    r"\b(?:no|not|never|without|cannot|could\s+not|did\s+not|has\s+not|was\s+not)\b"
    r"[^.!?;]{0,100}\b(?:consensus|unanimity|unanimous\s+agreement|majority\s+agreement)\b",
    re.IGNORECASE,
)


def _is_positive_consensus_claim(value: str) -> bool:
    """Reject unnegated positive consensus claims without proposition provenance."""
    positive_matches = list(_POSITIVE_CONSENSUS_PATTERN.finditer(value))
    if not positive_matches:
        return False
    negated_matches = list(_NEGATED_CONSENSUS_PATTERN.finditer(value))
    return any(
        not any(
            negative.start() <= positive.start() < negative.end()
            for negative in negated_matches
        )
        for positive in positive_matches
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
        if _is_positive_consensus_claim(value):
            _note_quarantined_claims(
                integrity_flags,
                source_label,
                ["Positive model-authored consensus assertion withheld; proposition-level consensus is not established by the saved report contract."],
            )
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


def _distinct_role_entries(rows: list[dict], field: str, round_label: str, integrity_flags: list[str] | None = None) -> list[tuple[dict, dict]]:
    """Return at most one unambiguous completed contribution per role and round."""
    grouped: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for row, item in _entries(rows, field):
        raw_agent_id = str(row.get("agent_id") or "").strip()
        if not raw_agent_id:
            if integrity_flags is not None:
                integrity_flags.append(f"{round_label} completed contribution has no agent_id and was excluded from distinct-role summaries.")
            continue
        # Role identifiers are canonical uppercase codes (for example RO-01).
        # Normalise only the grouping key; the saved source row is left unchanged.
        grouped[raw_agent_id.upper()].append((row, item))
    output: list[tuple[dict, dict]] = []
    for agent_id, entries in grouped.items():
        if len(entries) > 1:
            positions = {item.get("position") for _, item in entries}
            if len(positions) > 1:
                if integrity_flags is not None:
                    values = sorted(str(value) for value in positions)
                    integrity_flags.append(f"{round_label} contains duplicate completed records for {agent_id} with conflicting positions {values}; the role was excluded from deterministic position counts and derived role summaries.")
                continue
            if integrity_flags is not None:
                integrity_flags.append(f"{round_label} contains {len(entries)} completed records for {agent_id} with the same position; the role was counted once and the first record retained.")
        output.append(entries[0])
    return output

def count_distinct_role_positions(rows: list[dict], field: str, round_label: str = "Round", integrity_flags: list[str] | None = None) -> Counter:
    """Count one unambiguous position per distinct completed role."""
    return Counter(item.get("position") for _, item in _distinct_role_entries(rows, field, round_label, integrity_flags) if item.get("position"))

def _position_counts(rows: list[dict], field: str, round_label: str = "Round", integrity_flags: list[str] | None = None) -> Counter:
    return count_distinct_role_positions(rows, field, round_label, integrity_flags)

_SOURCE_OPINION_SOURCE_ID_PATTERN = re.compile(r"^CASE:case_summary#([1-9][0-9]*)$")
_SOURCE_OPINION_STATUSES = {"preserved", "partly_preserved", "omitted", "unclear"}


def build_source_opinion_review_coverage(
    round3_rows: list[dict],
    case_summary: str,
) -> tuple[list[str], list[str]]:
    """Rebuild source-opinion review coverage from distinct, completed saved R3 roles.

    Statuses are model-reported representation labels only. They are not clinical
    findings, evidence of prerequisite fulfilment, votes, or consensus.
    """
    integrity: list[str] = []
    entries = _distinct_role_entries(
        round3_rows, "result", "Round 3", integrity
    )
    id_to_excerpt: dict[str, str] = {}
    excerpt_to_id: dict[str, str] = {}
    roles_by_source: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )
    conflicting_ids: set[str] = set()

    for row, result in entries:
        role_id = str(row.get("agent_id") or "").strip().upper()
        reviews = result.get("source_opinion_reviews") or []
        if not isinstance(reviews, (list, tuple)):
            integrity.append(
                f"R3 source-opinion reviews from {role_id} are not a list and were excluded."
            )
            continue
        supplied_peer_refs = {
            f"R2:{str(peer_id).strip().upper()}"
            for peer_id in (row.get("source_peer_ids") or [])
            if isinstance(peer_id, str) and peer_id.strip()
        }
        for review in reviews:
            if not isinstance(review, dict):
                integrity.append(
                    f"R3 source-opinion review from {role_id} is not a structured object and was excluded."
                )
                continue
            source_id = str(review.get("source_id") or "").strip()
            excerpt = str(review.get("source_excerpt") or "")
            match = _SOURCE_OPINION_SOURCE_ID_PATTERN.fullmatch(source_id)
            if not match:
                integrity.append(
                    f"R3 source-opinion review from {role_id} has invalid source identifier "
                    f"{source_id or '(missing)'}; expected CASE:case_summary#N."
                )
                continue
            if not excerpt or excerpt not in case_summary:
                integrity.append(
                    f"R3 source-opinion review {source_id} from {role_id} lacks an exact "
                    "contiguous excerpt from the saved case_summary."
                )
                continue
            reference_ids = {
                str(reference).strip()
                for reference in (review.get("source_reference_ids") or [])
                if isinstance(reference, str) and reference.strip()
            }
            if source_id not in reference_ids:
                integrity.append(
                    f"R3 source-opinion review {source_id} from {role_id} omits its exact CASE source ID."
                )
                continue
            if not (reference_ids & supplied_peer_refs):
                integrity.append(
                    f"R3 source-opinion review {source_id} from {role_id} does not cite an R2 peer "
                    "recorded as supplied to that role."
                )
                continue

            prior_excerpt = id_to_excerpt.get(source_id)
            if prior_excerpt is not None and prior_excerpt != excerpt:
                conflicting_ids.add(source_id)
                integrity.append(
                    f"R3 source identifier {source_id} maps to more than one exact case-summary excerpt."
                )
            prior_id = excerpt_to_id.get(excerpt)
            if prior_id is not None and prior_id != source_id:
                conflicting_ids.update({prior_id, source_id})
                integrity.append(
                    f"An exact case-summary excerpt is assigned both {prior_id} and {source_id}."
                )
            id_to_excerpt[source_id] = excerpt
            excerpt_to_id[excerpt] = source_id
            roles_by_source[source_id][role_id].append(review)

    valid_numbers = sorted(
        int(match.group(1))
        for source_id in id_to_excerpt
        if (match := _SOURCE_OPINION_SOURCE_ID_PATTERN.fullmatch(source_id))
    )
    if valid_numbers and valid_numbers != list(range(1, max(valid_numbers) + 1)):
        integrity.append(
            "R3 source-opinion identifiers are not sequential from CASE:case_summary#1; "
            "one or more attributed source identifiers may be missing or inconsistently numbered."
        )

    coverage: list[str] = []
    for source_id in sorted(
        roles_by_source,
        key=lambda value: int(_SOURCE_OPINION_SOURCE_ID_PATTERN.fullmatch(value).group(1)),
    ):
        if source_id in conflicting_ids:
            integrity.append(
                f"R3 coverage for {source_id} was excluded because its identifier-to-excerpt mapping conflicts."
            )
            continue

        option_counts: Counter = Counter()
        condition_counts: Counter = Counter()
        for role_id, reviews in sorted(roles_by_source[source_id].items()):
            if len(reviews) > 1:
                integrity.append(
                    f"R3 source-opinion review {source_id} has {len(reviews)} records for "
                    f"distinct role {role_id}; each status is counted at most once."
                )
            for field, counts, label in (
                ("option_status", option_counts, "option"),
                ("conditions_status", condition_counts, "condition"),
            ):
                statuses = {
                    str(review.get(field) or "").strip()
                    for review in reviews
                }
                invalid = statuses - _SOURCE_OPINION_STATUSES
                if invalid:
                    integrity.append(
                        f"R3 source-opinion review {source_id} from {role_id} has missing or "
                        f"invalid {label} status {sorted(invalid)}; excluded from that status count."
                    )
                    continue
                if len(statuses) > 1:
                    integrity.append(
                        f"R3 source-opinion review {source_id} has conflicting {label} statuses "
                        f"for {role_id}; that role was excluded from the {label} status count."
                    )
                    continue
                if statuses:
                    counts[next(iter(statuses))] += 1

        coverage.append(
            "R3 source-opinion review coverage (distinct completed roles; model-reported "
            "representation labels only, not clinical findings or consensus) — "
            f"{source_id}: {len(roles_by_source[source_id])}/{len(entries)} roles supplied "
            "an exact source-bound review; option status role counts "
            f"{dict(sorted(option_counts.items()))}; condition status role counts "
            f"{dict(sorted(condition_counts.items()))}."
        )

    return coverage, _unique(integrity, 45)



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
        for row, item in _distinct_role_entries(rows, field, f"Round {round_number}", integrity_flags):
            agent_id = str(row.get("agent_id") or "unknown-role")
            record = by_agent[agent_id]
            record["name"] = row.get("agent_name") or record["name"]
            position = item.get("position")
            if not position:
                continue
            record["positions"].append(position)
            conclusion = " ".join(str(item.get("provisional_conclusion") or "").split())
            withheld = False
            if conclusion and _is_positive_consensus_claim(conclusion):
                withheld = True
                _note_quarantined_claims(
                    integrity_flags,
                    f"R{round_number} {agent_id} minority-history conclusion",
                    ["Positive consensus assertion withheld; one role's text cannot establish shared proposition-level agreement."],
                )
            if conclusion and not withheld and case is not None:
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

    round3_counts = _position_counts(round3_rows, "result", "Round 3", integrity_flags)
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
        for row, item in _distinct_role_entries(rows, "result", f"Round {round_number}", integrity_flags):
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
                if _is_positive_consensus_claim(cleaned):
                    _note_quarantined_claims(
                        integrity_flags,
                        f"R{round_number} {role_id} agreement",
                        ["Positive consensus assertion withheld; this role-authored statement is not evidence of agreement by other roles."],
                    )
                    continue
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
    quarantine_flags: list[str] = []
    stored_integrity_flags: list[str] = []
    counts_by_round = {
        round_number: _position_counts(rows, field, f"Round {round_number}", quarantine_flags)
        for (round_number, field), rows in zip(ROUND_SOURCES, rows_by_round)
    }
    final_counts = counts_by_round[3]

    for round_number, rows, field in (
        (1, round1_rows, "assessment"),
        (2, round2_rows, "result"),
        (3, round3_rows, "result"),
    ):
        # Preserve source integrity flags from every completed record, including
        # duplicate/conflicting role rows that are excluded from derived summaries.
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
        for row, item in _distinct_role_entries(rows, "result", f"Round {round_number}", quarantine_flags):
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
