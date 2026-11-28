"""Round 4 Chair synthesis generation and deterministic draft reconciliation."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Awaitable, Callable
from typing import Any

from app.round_schemas import FinalMDTReport, FinalReportDraft
from app.schemas import SyntheticCase
from app.services.case_integrity import (
    build_case_prompt_context,
    build_case_report_title,
    redact_flagged_tnm_values,
)
from app.services.chair_report_quality import (
    build_recorded_agreements,
    build_source_opinion_review_coverage,
)
from app.services.mdt_llm_client import (
    _compact,
    _format_position_counts,
    _generate_structured,
    _position_counts,
    _round_items,
    _unique_modal_position,
    _unique_strings,
)


def reconcile_chair_report_draft(
    run_id: str,
    case: SyntheticCase,
    round1_views: list[dict],
    round2_views: list[dict],
    round3_views: list[dict],
    draft: FinalReportDraft,
) -> FinalMDTReport:
    """Reconcile the Chair draft against saved records; source records win over model prose."""
    r1 = _round_items(round1_views, "assessment")
    r2 = _round_items(round2_views, "result")
    r3 = _round_items(round3_views, "result")
    counts_by_round = {
        "Round 1": _position_counts(round1_views, "assessment"),
        "Round 2": _position_counts(round2_views, "result"),
        "Round 3": _position_counts(round3_views, "result"),
    }
    final_counts = counts_by_round["Round 3"]

    consensus_status = "insufficient_information"

    distribution = "; ".join(
        f"{name}: {_format_position_counts(counts)}"
        for name, counts in counts_by_round.items()
    )

    case_unknowns = list(case.known_unknowns or [])
    assessment_unknowns = [
        item
        for _, result in r1
        for item in (result.get("unknowns") or [])
    ]
    debate_unknowns = [
        item
        for _, result in r2
        for item in (result.get("remaining_unknowns") or [])
    ]
    adversarial_unknowns = [
        item
        for _, result in r3
        for item in (result.get("remaining_unknowns") or [])
    ]
    uncertainties = _unique_strings(
        case_unknowns + assessment_unknowns + debate_unknowns + adversarial_unknowns,
        limit=20,
    )
    missing_information = _unique_strings(
        case_unknowns + assessment_unknowns + debate_unknowns + adversarial_unknowns,
        limit=20,
    )

    consensus_points: list[str] = []

    modal_position = _unique_modal_position(final_counts)
    minority_views: list[str] = []
    for row, result in r3:
        position = result.get("position")
        if position and position != "insufficient_information" and position != modal_position:
            agent = row.get("agent_id", "unknown role")
            role = row.get("agent_name", "Role")
            conclusion = result.get("provisional_conclusion", "")
            minority_views.append(
                f"{agent} — {role} ({position}): {_compact(conclusion, 300)}"
            )
    if not minority_views:
        for row, result in r1:
            position = result.get("position")
            if (
                position
                and position != "insufficient_information"
                and modal_position is not None
                and position != modal_position
            ):
                minority_views.append(
                    f"{row.get('agent_id', 'unknown role')} — "
                    f"{row.get('agent_name', 'Role')} ({position}, Round 1): "
                    f"{_compact(result.get('provisional_conclusion', ''), 300)}"
                )
    minority_views = minority_views[:45]

    unresolved: list[str] = [
        "No proposition-level consensus is established by the saved free-text agreement "
        "notes; position labels and repeated wording are not counted as votes."
    ]
    if (
        re.search(r"\b(?:two|competing|contrasting)\s+(?:provisional\s+)?opinions\b", case.case_summary, re.IGNORECASE)
        and re.search(r"\bconditional\b", case.case_summary, re.IGNORECASE)
    ):
        unresolved.append(
            "Source-case attributed opinions and conditions (verbatim; not verified facts "
            "or MDT consensus): " + _compact(case.case_summary, 1200)
        )
    recorded_review_findings: list[str] = []
    for round_label, entries in (("Round 2", r2), ("Round 3", r3)):
        for row, result in entries:
            role_id = str(row.get("agent_id") or "unknown-role")
            role_name = str(row.get("agent_name") or "Role")
            for challenge in (result.get("substantive_challenges") or []):
                if isinstance(challenge, str) and challenge.strip():
                    recorded_review_findings.append(
                        f"{round_label} recorded challenge — {role_id} ({role_name}): "
                        f"{_compact(challenge, 260)}"
                    )
    source_coverage, source_review_integrity = build_source_opinion_review_coverage(
        round3_views, case.case_summary
    )
    unresolved.extend(source_review_integrity)
    unresolved.extend(_unique_strings(recorded_review_findings, limit=12))

    source_reference_findings: list[str] = []
    for round_label, entries in (("Round 2", r2), ("Round 3", r3)):
        for row, result in entries:
            flags = result.get("source_reference_integrity_flags") or []
            if flags:
                role_id = str(row.get("agent_id") or "unknown-role")
                source_reference_findings.append(
                    f"{round_label} source-reference audit — {role_id}: "
                    + "; ".join(_unique_strings(flags, limit=3))
                )
    unresolved.extend(_unique_strings(source_reference_findings, limit=12))
    r3_challenge_count = sum(
        1 for _, result in r3
        if any(isinstance(item, str) and item.strip()
               for item in (result.get("substantive_challenges") or []))
    )
    if not r3_challenge_count:
        unresolved.append(
            "No Round-3 role saved a substantive_challenges entry. Risk flags and generic "
            "warnings are not counted as source-linked adversarial challenges."
        )
    if len(final_counts) > 1:
        highest_count = max(final_counts.values())
        tied_positions = sorted(
            position for position, count in final_counts.items() if count == highest_count
        )
        if len(tied_positions) > 1:
            tied_distribution = ", ".join(
                f"{final_counts[position]}/{sum(final_counts.values())} {position}"
                for position in tied_positions
            )
            unresolved.append(
                "Round-3 position labels have no unique modal position because the highest "
                "counts are tied ("
                + tied_distribution
                + "). All non-insufficient recorded position groups are retained; the labels "
                "are not, by themselves, proof of opposing treatment views."
            )
        else:
            unresolved.append(
                "Round-3 position labels were not uniform: "
                + _format_position_counts(final_counts)
                + ". The labels are preserved as recorded and are not, by themselves, proof of opposing treatment views."
            )
    elif len(final_counts) == 1 and any(
        final_counts.get(position)
        for position in ("supports", "opposes", "conditional")
    ):
        unresolved.append(
            "Round-3 position labels were uniform ("
            + _format_position_counts(final_counts)
            + "), but the saved contributions do not establish one shared, proposition-level "
            "educational option. The report therefore does not infer consensus from labels alone."
        )
    if final_counts.get("supports") and final_counts.get("opposes"):
        unresolved.append(
            "Round 3 contains both supporting and opposing positions; the report therefore records no consensus."
        )

    patient_family: list[str] = []
    if case.patient_goals:
        patient_family.extend(
            f"Recorded patient goal/preference: {item}" for item in case.patient_goals
        )
    else:
        patient_family.append(
            "Patient goals and preferences were not supplied; no preference is inferred."
        )
    patient_family.extend(case.social_context or [])
    patient_family = _unique_strings(patient_family, limit=10)

    feasibility: list[str] = list(case.resource_context or [])
    if not feasibility:
        feasibility.append(
            "No structured resource context was supplied; resource feasibility cannot be assessed."
        )
    feasibility.extend(
        item for item in (case.social_context or [])
        if any(term in item.casefold() for term in ("support", "adher", "access", "transport", "caregiver"))
    )
    feasibility = _unique_strings(feasibility, limit=10)

    governance = [
        "Educational simulation only; this report is not a clinical decision or treatment instruction.",
        "Patient goals, consent, and decision-making preferences must not be inferred from missing data.",
        "No evidence retrieval or citation verification is connected to this run.",
    ]
    evidence_limitations = [
        "Evidence retrieval and citation verification are not connected; model-generated evidence statements are unverified.",
        "Clinical accuracy and guideline concordance have not been evaluated.",
    ]
    evidence_gaps = [
        item
        for _, result in r1
        for item in (result.get("evidence_gaps") or [])
    ]
    evidence_limitations.extend(_unique_strings(evidence_gaps, limit=4))
    evidence_limitations = _unique_strings(evidence_limitations, limit=8)

    key_unknowns = "; ".join(uncertainties[:4]) or "critical clinical information is not supplied"
    chair_conclusion = (
        "No treatment recommendation can be made from the supplied case. No proposition-level "
        "consensus or proposition-specific disagreement can be established because the saved "
        "contributions do not identify a shared proposition. The recorded Round-3 positions remain "
        f"separately traceable ({_format_position_counts(final_counts)}); unresolved information "
        f"includes: {key_unknowns}."
    )

    overall = (
        f"Recorded position distribution — {distribution}. These are role-level labels, not "
        "votes; conditional positions are not recast as support or opposition, and a non-uniform "
        "distribution is not described as unanimous. The source case and role contributions "
        "identify the missing information and social/resource context listed below. Evidence "
        "retrieval is not connected, and clinical accuracy was not evaluated."
    )
    reflection = (
        "This Chair record is reconciled against the saved Round-1, Round-2, and Round-3 "
        "contributions so that counts and minority positions remain traceable. It is a "
        "structural educational synthesis only; it does not validate clinical correctness, "
        "guideline concordance, or evidence quality."
    )

    unresolved = _unique_strings(unresolved, limit=15)

    return FinalMDTReport(
        run_id=run_id,
        report_title=build_case_report_title(case),
        consensus_status=consensus_status,
        chair_conclusion=chair_conclusion,
        overall_educational_synthesis=overall,
        consensus_points=consensus_points,
        recorded_agreements=build_recorded_agreements(round2_views, round3_views, case=case),
        source_opinion_review_coverage=source_coverage,
        unresolved_disagreements=unresolved,
        minority_and_dissenting_views=minority_views,
        major_uncertainties=uncertainties,
        missing_information_before_real_world_review=missing_information,
        patient_and_family_considerations=patient_family,
        feasibility_and_resource_considerations=feasibility,
        governance_and_safeguarding_considerations=governance,
        evidence_limitations=evidence_limitations,
        chair_reflection=reflection,
        case_data_integrity_flags=(
            _unique_strings(
                [flag for _, result in (r1 + r2 + r3) for flag in (result.get("case_data_integrity_flags") or [])],
                limit=20,
            )
            or ["No unsupported stage, demographic, or absence claim was detected by the deterministic case-data audit."]
        ),
    )


async def generate_chair_report(
    run_id: str,
    case: SyntheticCase,
    round1_views: list[dict],
    round2_views: list[dict],
    round3_views: list[dict],
    max_tokens: int = 1600,
    generate_structured_fn: Callable[[str, type[Any], int], Awaitable[Any]] | None = None,
) -> FinalMDTReport:
    chair_integrity_flags: list[str] = []
    for rows, field in (
        (round1_views, "assessment"),
        (round2_views, "result"),
        (round3_views, "result"),
    ):
        for _, result in _round_items(rows, field):
            values = result.get("case_data_integrity_flags") or []
            if isinstance(values, str):
                values = [values]
            chair_integrity_flags.extend(
                item for item in values if isinstance(item, str) and item.strip()
            )

    def chair_prompt_text(value: str, limit: int) -> str:
        return _compact(redact_flagged_tnm_values(value, chair_integrity_flags), limit)

    def digest(items: list[dict], round_key: str) -> dict:
        """Send position counts and explicit non-modal views, not truncated unanimity cues."""
        field = "assessment" if round_key == "round1" else "result"
        entries = _round_items(items, field)
        counts = Counter(
            result.get("position")
            for _, result in entries
            if result.get("position")
        )
        modal = _unique_modal_position(counts)
        grouped_views: dict[str, list[dict]] = {}
        for row, result in entries:
            position = result.get("position")
            if not position:
                continue
            entry = {
                "agent": row.get("agent_id"),
                "position": position,
                "conclusion": chair_prompt_text(result.get("provisional_conclusion", ""), 160),
            }
            if round_key in {"round2", "round3"}:
                entry["debate_or_review_narrative"] = chair_prompt_text(
                    result.get("response_to_other_perspectives", ""), 600
                )
                entry["agreements"] = [
                    chair_prompt_text(value, 100)
                    for value in (result.get("agreements") or [])[:1]
                ]
                entry["challenges"] = [
                    chair_prompt_text(value, 100)
                    for value in (result.get("substantive_challenges") or [])[:1]
                ]
            if round_key == "round2":
                entry["attributed_source_opinion_responses"] = [
                    {
                        "source_id": item.get("source_id", ""),
                        "source_excerpt": chair_prompt_text(item.get("source_excerpt", ""), 400),
                        "analysis": chair_prompt_text(item.get("analysis", ""), 700),
                        "comparison": chair_prompt_text(item.get("comparison", ""), 400),
                    }
                    for item in (result.get("source_opinion_responses") or [])[:4]
                    if isinstance(item, dict)
                ]
            if round_key == "round3":
                entry["risks"] = [
                    chair_prompt_text(value, 90)
                    for value in (result.get("risk_flags") or [])[:2]
                ]
                entry["unknowns"] = [
                    chair_prompt_text(value, 90)
                    for value in (result.get("remaining_unknowns") or [])[:2]
                ]
            grouped_views.setdefault(position, []).append(entry)

        if modal is None:
            non_modal = []
            for position in sorted(grouped_views, key=lambda value: (-counts[value], value)):
                non_modal.extend(grouped_views[position][:2])
            representative = []
        else:
            non_modal = []
            for position in sorted(
                (value for value in grouped_views if value != modal),
                key=lambda value: (-counts[value], value),
            ):
                non_modal.extend(grouped_views[position][:2])
            representative = grouped_views.get(modal, [])[:3]

        return {
            "role_count": len(entries),
            "position_counts": dict(counts),
            "non_modal_views": non_modal[:8],
            "representative_views": representative,
        }

    prompt = (
        "ROUND 4 — MDT CHAIR SYNTHESIS. Synthesize the completed independent, debate, and "
        "adversarial stages. This is an educational record, not a clinical treatment decision. "
        "Do not invent consensus. Explicitly separate genuine agreement from unresolved dissent. "
        "Do not recommend a patient-specific treatment or include doses. Evidence retrieval is "
        "not connected: say so, and identify evidence gaps rather than inventing citations. "
        "Do not silently resolve contradictory facts. Preserve the source-case's explicitly attributed opinions and every condition attached to them; do not relabel them as verified facts or MDT consensus. Reconcile the saved R2/R3 substantive_challenges as source-attributed review records, retaining their originating role IDs and round. Do not silently discard a challenge because it is absent from a compressed representative digest. Do not say unanimous, all agents, or no dissent unless exact position counts support it. Treat position labels as descriptions, not votes; distinguish a conditional view from support/opposition. The software will retain saved Round-2 and Round-3 agreement statements separately with role/round attribution; do not treat those records as consensus by themselves and do not add extra JSON fields. Consensus requires the same explicit proposition or educational option to be supported in the saved contributions. A uniform position-label distribution alone is not consensus; when no shared proposition is established, set insufficient_information.\nSUPPLIED CASE:\n"
        + json.dumps(build_case_prompt_context(case), ensure_ascii=False, separators=(",", ":"))
        + "\nROUND 1 INDEPENDENT POSITIONS:\n"
        + json.dumps(digest(round1_views, "round1"), ensure_ascii=False, separators=(",", ":"))
        + "\nROUND 2 DEBATE POSITIONS:\n"
        + json.dumps(digest(round2_views, "round2"), ensure_ascii=False, separators=(",", ":"))
        + "\nROUND 3 ADVERSARIAL REVIEW:\n"
        + json.dumps(digest(round3_views, "round3"), ensure_ascii=False, separators=(",", ":"))
        + "\nReturn a balanced synthesis. Set consensus_status to consensus, qualified_consensus, no_consensus, or insufficient_information. "
        "Keep the JSON output compact. chair_conclusion: 2 short sentences. overall_educational_synthesis: at most 100 words. "
        "chair_reflection: 2 short sentences. For each list field, provide no more than 3 concise entries; use [] when there is no distinct supported point. "
        "Populate every applicable section from the supplied records; do not leave a section empty merely to save tokens. Preserve non-modal positions and list them separately without overstating dissent. "
        "The saved contribution schema has no normalized shared-proposition identifier. Set consensus_status to insufficient_information and consensus_points to []: role-level supports/opposes/conditional labels and free-text agreement statements cannot establish either consensus or no_consensus on a common proposition. Preserve the source-attributed positions and disagreements instead. "
        "The output format is schema-enforced."
    )
    llm_call = generate_structured_fn or _generate_structured
    draft = await llm_call(prompt, FinalReportDraft, max_tokens)
    return reconcile_chair_report_draft(
        run_id, case, round1_views, round2_views, round3_views, draft
    )
