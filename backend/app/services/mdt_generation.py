"""Compact Ollama generation for debate, adversarial review, and chair synthesis."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.round_schemas import (
    AdversarialContributionDraft,
    AdversarialSourceOpinionReviewsRepairDraft,
    FinalMDTReport,
    FinalReportDraft,
    Round2ContributionDraft,
    Round2SourceOpinionResponsesRepairDraft,
    RoundContribution,
    RoundContributionDraft,
    RoundTextRepairDraft,
)
from app.schemas import SyntheticCase
from app.services.case_integrity import (
    audit_unverified_case_claims,
    build_case_prompt_context,
    case_summary_has_attributed_opinions,
    extract_attributed_note_opinions,
    is_empty_challenge_placeholder as _is_empty_challenge_placeholder,
    redact_flagged_tnm_values,
)
from app.services.mdt_chair_reconciler import (
    generate_chair_report as _generate_chair_report_impl,
    reconcile_chair_report_draft,
)
from app.services.mdt_llm_client import (
    GENERATION_REQUEST_TIMEOUT_SECONDS,
    _compact,
    _context_window_for_schema,
    _format_position_counts,
    _generate_structured,
    _position_counts,
    _round_items,
    _unique_modal_position,
    _unique_strings,
)
from app.services.mdt_round_integrity import (
    _EMBEDDED_ROUND_REFERENCE_PATTERN,
    _NEITHER_INDICATION_ASSERTION,
    _OPINION_ATTRIBUTION_VERB_PATTERN,
    _OPINION_CONDITION_PATTERN,
    _OPINION_TERM_STOPWORDS,
    _PREREQUISITE_INTEGRITY_FLAG_PREFIX,
    _REPAIRABLE_TOP_LEVEL_TEXT_FIELDS,
    _ROUND_REFERENCE_PATTERN,
    _ROUND_REFERENCE_RANGE_PATTERN,
    _TREATMENT_INDICATION_INTEGRITY_FLAG_PREFIX,
    _active_case_integrity_payload,
    _audit_source_references,
    _bind_exact_peer_evidence_excerpt,
    _bounded_exact_excerpt,
    _combined_case_integrity_flags,
    _compact_case_integrity_flags,
    _compact_r1_text,
    _compact_r2_text,
    _deterministically_neutralise_neither_indication_claim,
    _deterministically_neutralise_unsupported_prerequisite_status,
    _payload_strings,
    _prerequisite_integrity_flags,
    _prioritized_provenance_flags,
    _r3_peer_case_integrity_flags,
    _repair_unsupported_prerequisite_wording as _repair_unsupported_prerequisite_wording_impl,
    _repairable_clinical_integrity_flags,
    _repairable_narrative_locations,
    _repairable_text_max_length,
    _round_reference_tokens,
    _select_source_opinion_evidence_excerpt,
    _set_repairable_narrative_text,
    _source_opinion_component_has_any_support,
    _source_opinion_component_match_counts,
    _source_opinion_component_supported,
    _source_opinion_component_tokens,
    _source_opinion_repair_preserves_anchors,
)

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


async def generate_chair_report(
    run_id: str,
    case: SyntheticCase,
    round1_views: list[dict],
    round2_views: list[dict],
    round3_views: list[dict],
    max_tokens: int = 1600,
) -> FinalMDTReport:
    return await _generate_chair_report_impl(
        run_id,
        case,
        round1_views,
        round2_views,
        round3_views,
        max_tokens=max_tokens,
        generate_structured_fn=_generate_structured,
    )


async def _repair_unsupported_prerequisite_wording(
    case: SyntheticCase,
    payload: dict,
    *,
    round_number: int,
    role_id: str,
    role_name: str,
    allowed_sources: set[tuple[str, str]],
) -> tuple[dict, list[str]]:
    return await _repair_unsupported_prerequisite_wording_impl(
        case,
        payload,
        round_number=round_number,
        role_id=role_id,
        role_name=role_name,
        allowed_sources=allowed_sources,
        generate_structured_fn=_generate_structured,
    )


async def generate_debate_contribution(
    profile: dict[str, str],
    case: SyntheticCase,
    own_independent_assessment: dict,
    peer_views: list[dict],
    max_tokens: int = 1100,
) -> RoundContribution:
    peers = [
        {
            "role": peer["agent_name"],
            "position": peer["assessment"].get("position", "unknown"),
            "conclusion": _compact_r1_text(
                peer["assessment"].get("provisional_conclusion", ""),
                180,
                peer["assessment"].get("case_data_integrity_flags"),
            ),
            "educational_option": _compact_r1_text(
                peer["assessment"].get("preferred_educational_option", ""),
                140,
                peer["assessment"].get("case_data_integrity_flags"),
            ),
            "disagreement_notes": [
                _compact_r1_text(
                    item, 100, peer["assessment"].get("case_data_integrity_flags")
                )
                for item in (peer["assessment"].get("disagreement_notes") or [])[:2]
            ],
            "unknowns": [
                _compact_r1_text(
                    item, 90, peer["assessment"].get("case_data_integrity_flags")
                )
                for item in (peer["assessment"].get("unknowns") or [])[:2]
            ],
            "case_integrity_audit_flags": _compact_case_integrity_flags(
                peer["assessment"].get("case_data_integrity_flags")
            ),
        }
        for peer in peer_views
    ]
    own_r1_integrity_flags = own_independent_assessment.get("case_data_integrity_flags") or []
    own = {
        "position": own_independent_assessment.get("position"),
        "conclusion": _compact_r1_text(
            own_independent_assessment.get("provisional_conclusion", ""),
            240,
            own_r1_integrity_flags,
        ),
        "option": _compact_r1_text(
            own_independent_assessment.get("preferred_educational_option", ""),
            160,
            own_r1_integrity_flags,
        ),
        "case_integrity_audit_flags": _compact_case_integrity_flags(
            own_r1_integrity_flags
        ),
    }
    source_opinion_register = extract_attributed_note_opinions(case.case_summary)
    allowed_sources = {("R1", profile["agent_id"])} | {
        ("R1", peer["agent_id"]) for peer in peer_views
    }
    prompt = (
        "ROUND 2 — STRUCTURED MDT DEBATE. You are the role below. First inspect the "
        "verbatim case summary for each explicitly attributed opinion, its proposed option, "
        "and every stated prerequisite. Treat each as a source statement (CASE:case_summary), "
        "not a verified fact. Compare each option separately with your own R1 view and the "
        "selected peer views. Do not collapse distinct conditional pathways into generic "
        "uncertainty about missing staging. In particular, a surgery-first/surgical-assessment "
        "pathway and a preoperative multimodality pathway remain distinct options even when "
        "both depend on some missing investigations. Shared uncertainty about prerequisites "
        "is not agreement on treatment sequence, option, resectability, or fitness. Do not "
        "describe different prerequisites as identical unless the source text explicitly says so. "
        "For EACH server-identified attributed opinion listed in the dedicated register below, return exactly "
        "one item in the required source_opinion_responses array using that exact CASE source ID. "
        "Also set position_on_source_opinion for that exact opinion: supports, opposes, conditional, or "
        "insufficient_information. This is your role's reported stance on that one attributed opinion, "
        "not the source author's stance, your overall round position, an endorsement, or a vote. Use "
        "conditional when your view depends on prerequisites and name those prerequisites in analysis; "
        "do not imply they are fulfilled. Use insufficient_information when you cannot state a defensible "
        "stance. Do not transfer a stance between different CASE source IDs. "
        "In its analysis, name the distinct option and every stated prerequisite/condition; in comparison, "
        "compare it with your own R1 position and the selected peer R1 records. Do not replace an "
        "option with generic uncertainty about missing data. "
        "ABSENT-IS-NOT-UNMET RULE: distinguish missing documentation from an assessed negative finding for each prerequisite. "
        "If an MRI result, complete staging, or fitness/performance assessment is not present in the supplied case, describe it as 'not supplied', 'not documented', or 'unknown'. "
        "Do not say that a prerequisite is 'not met', failed, negative, or absent solely because its result or assessment is missing. "
        "For example, no MRI result supplied means MRI staging is unknown; no staging entry means stage is undocumented, not evidence of a negative staging result; "
        "no fitness assessment means fitness is unknown, not that the patient is unfit or that a fitness threshold failed. "
        "Use 'not met' or 'unmet' only when the case explicitly records that the prerequisite was assessed and a documented finding establishes it was not fulfilled; "
        "identify that exact documented finding and do not infer a threshold. "
        "SOURCE-WORDING FIDELITY: if a peer statement says a prerequisite is 'not present in the supplied record', 'not documented', or 'not supplied', report only that the prerequisite is not documented in that record. "
        "Do not paraphrase it as the peer claiming that the prerequisite is clinically absent, negative, failed, or unmet; that changes an information-status statement into a clinical finding. "
        "If supplied prerequisite status is unknown, explicitly preserve unknown. A peer's description of what the record contains does not establish the real-world prerequisite status. "
        "A conditional source option remains conditional when prerequisite status is unknown; representing it is not endorsement or a finding that its prerequisites are satisfied. "
        "Missing prerequisites mean suitability is unknown; they do not erase the source's conditional option. "
        "Never describe undocumented prerequisites as 'not met' or 'unmet'; state that their status is unknown or not supplied. "
        "Never conclude that 'neither option is indicated' or that 'no option is appropriate' from missing data alone. "
        "Never convert 'no definitive pathway can be established from this incomplete record' into 'no pathway is indicated'; "
        "the former describes information sufficiency, while the latter asserts a clinical indication decision that the case does not support. "
        "Do not conclude that neither option is clinically indicated, that no pathway is indicated, or that no option is appropriate from missing data alone. "
        "When describing peer contributions, you may state that the supplied peer records do not claim an option is indicated only when accurate and explicitly attributed; "
        "this reports what those records say and is not a clinical indication conclusion. "
        "Use this exact safe formulation when indication cannot be determined: 'The supplied information does not establish whether either source option is indicated or appropriate; indication and suitability remain undetermined.' "
        "Do not infer a negative indication from agreement that data are missing or from a peer saying that no definitive pathway can yet be established. "
        "Do not imply "
        "that repeating a source opinion means you endorse it. If a peer omits or weakens the option, "
        "explain that separately without inventing evidence. If no attributed opinions are registered, "
        "return an empty source_opinion_responses array. The server binds each exact source_excerpt after generation. "
        "Peer provenance is recorded separately by the server in the exact source_peer_ids field; "
        "do not emit round-qualified source identifiers in generated prose. Refer to an individual "
        "peer only by the exact role name shown in the supplied peer record. Do not abbreviate or "
        "group peer identifiers in prose. If a specific role cannot be attributed from the supplied "
        "material, state that limitation. The server-owned peer list is the authoritative source "
        "boundary for this contribution. Engage only with the peers actually supplied below. "
        "The digest is a "
        "bounded sample of at most 15 of 44 other roles, not the complete MDT; never say all "
        "roles or all peers agree, and never generalise sampled views to unshown roles. Record "
        "an agreement only when the same substantive proposition or educational option is "
        "explicitly present in both source contributions. Agreement that information is missing "
        "does not establish agreement on an option. Record a substantive challenge only when "
        "you identify its source, exact claim or condition, the reason it is unsupported or "
        "misrepresented, and what information would resolve it. Do not manufacture challenges. "
        "If no agreement or challenge is justified, explain the evidence limitation in "
        "response_to_other_perspectives and leave the corresponding list empty. Preserve "
        "conditionality; do not convert conditional positions into support. "
        "SERVER CASE-INTEGRITY AUDIT: your own R1 assessment and selected peer R1 records may "
        "include case_integrity_audit_flags. These are deterministic server warnings that the "
        "corresponding R1 narrative contains a claim not supported by the immutable case snapshot; "
        "they are not new case facts and do not prove the opposite finding. Treat the flagged claim "
        "as unverified/quarantined, do not repeat it as a clinical fact, do not use it to justify "
        "agreement or a position change, and do not infer the opposite. Do not reproduce or quote the literal TNM/stage values from a flagged assertion, even when attributing or rebutting it; refer only to 'the flagged unsupported staging assertion'. If relevant, attribute it only as an "
        "unverified statement from that named R1 contribution and explain that the source case does "
        "not establish it. The verbatim case and structured fields remain authoritative.\n"
        f"ROLE: {profile['name']}\nMANDATE: {profile['mandate']}\nCLINICAL PHILOSOPHY: {profile.get('clinical_philosophy', '')}\n"
        "SUPPLIED CASE:\n"
        + json.dumps(build_case_prompt_context(case), ensure_ascii=False, separators=(",", ":"))
        + "\nSTAGING LOCK (STG-00): Do NOT rethink, re-stage, or dispute T/N/M values during debate or adversarial review; accept STG-00's fixed staging.\n"
        + "\nSERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS (exact case-summary excerpts; source statements, not verified facts or your endorsement):\n"
        + json.dumps(source_opinion_register, ensure_ascii=False, separators=(",", ":"))
        + "\nYOUR ROUND-1 POSITION:\n"
        + json.dumps(own, ensure_ascii=False, separators=(",", ":"))
        + "\nSELECTED PEER POSITIONS (compressed for local context limits):\n"
        + json.dumps(peers, ensure_ascii=False, separators=(",", ":"))
        + "\nReturn a concise response with specific agreements, disagreements, and any reason for changing or retaining your position. The output format is schema-enforced."
    )
    try:
        from app.services.evidence_retrieval import get_evidence_retrieval_engine
        engine = get_evidence_retrieval_engine()
        passages = engine.retrieve_evidence_for_role(profile.get("agent_id", ""), case, limit=3)
        evidence_context = engine.format_prompt_injection(passages)
        if evidence_context:
            prompt += f"\n\n{evidence_context}"
    except Exception as exc:
        logger.debug("Evidence retrieval omitted in generate_debate_contribution: %s", exc)

    draft = await _generate_structured(prompt, Round2ContributionDraft, max_tokens)
    payload = draft.model_dump()
    payload["remaining_unknowns"] = _unique_strings(
        list(case.known_unknowns or []) + list(payload.get("remaining_unknowns") or []),
        limit=8,
    )
    expected_source_opinions = {
        item["source_id"]: item["source_excerpt"] for item in source_opinion_register
    }
    reported_responses = payload.get("source_opinion_responses") or []
    source_opinion_response_flags: list[str] = []
    response_repair_attempted = False
    response_repair_status = "not_needed"
    repaired_response_ids: list[str] = []
    initial_response_counts = Counter(
        str(item.get("source_id") or "")
        for item in reported_responses
        if isinstance(item, dict)
    )
    missing_response_ids = [
        source_id for source_id in expected_source_opinions
        if initial_response_counts.get(source_id, 0) == 0
    ]
    if missing_response_ids:
        response_repair_attempted = True
        response_repair_status = "incomplete"
        missing_register = [
            {"source_id": source_id, "source_excerpt": expected_source_opinions[source_id]}
            for source_id in missing_response_ids
        ]
        repair_prompt = (
            "ROUND 2 SOURCE-OPINION COVERAGE REPAIR. This is a narrowly scoped completion "
            "of structured source records omitted from your first response, not a new MDT position. "
            "Return exactly one source_opinion_response for each item in MISSING REGISTER, in the "
            "same order, and return no other IDs. Do not say that no peer views were supplied: "
            "the actual selected R1 peer records are included below. For each opinion, name its "
            "distinct educational option and every prerequisite exactly enough to preserve the "
            "source meaning. Explain how it relates to your own R1 position and the supplied peer "
            "R1 positions. Also report position_on_source_opinion for that exact source ID using "
            "supports, opposes, conditional, or insufficient_information. This is your role-reported "
            "stance, not an endorsement, vote, or clinical determination. Keep every prerequisite "
            "explicit and unknown unless the case confirms it. Missing prerequisites remain unknown/"
            "not supplied, not unmet; do not infer clinical appropriateness or endorse the source option. "
            "Do not invent peer statements, facts, or treatment recommendations. Use only the source_id "
            "values in MISSING REGISTER. Return only source_id, position_on_source_opinion, analysis, "
            "and comparison.\n"
            f"ROLE: {profile['name']} ({profile['agent_id']})\n"
            "SUPPLIED CASE (source data, not verified findings):\n"
            + json.dumps(build_case_prompt_context(case), ensure_ascii=False, separators=(",", ":"))
            + "\nMISSING REGISTER (server-identified IDs and exact excerpts):\n"
            + json.dumps(missing_register, ensure_ascii=False, separators=(",", ":"))
            + "\nYOUR R1 POSITION:\n"
            + json.dumps(own, ensure_ascii=False, separators=(",", ":"))
            + "\nACTUAL SELECTED PEER R1 POSITIONS:\n"
            + json.dumps(peers, ensure_ascii=False, separators=(",", ":"))
        )
        try:
            repair_draft = await _generate_structured(
                repair_prompt, Round2SourceOpinionResponsesRepairDraft, 750
            )
            repaired_items = [item.model_dump() for item in repair_draft.source_opinion_responses]
            reported_responses.extend(repaired_items)
            repaired_response_ids = list(dict.fromkeys(
                str(item.get("source_id") or "")
                for item in repaired_items
                if str(item.get("source_id") or "") in missing_response_ids
            ))
            repaired_counts = Counter(
                str(item.get("source_id") or "")
                for item in repaired_items
                if isinstance(item, dict)
            )
            response_repair_status = (
                "completed"
                if all(repaired_counts.get(source_id, 0) == 1 for source_id in missing_response_ids)
                and all(source_id in missing_response_ids for source_id in repaired_counts)
                else "incomplete"
            )
            if response_repair_status != "completed":
                source_opinion_response_flags.append(
                    "R2 source-opinion repair did not return exactly one response for each missing registered source ID."
                )
            payload["source_opinion_responses"] = reported_responses
        except Exception as exc:
            response_repair_status = "failed"
            source_opinion_response_flags.append(
                f"R2 source-opinion repair failed ({type(exc).__name__}: {str(exc)[:180]})."
            )
    response_counts = Counter(
        str(item.get("source_id") or "")
        for item in reported_responses
        if isinstance(item, dict)
    )
    for source_id in expected_source_opinions:
        count = response_counts.get(source_id, 0)
        if count == 0:
            source_opinion_response_flags.append(
                f"R2 has no structured response for server-identified attributed opinion {source_id}."
            )
        elif count > 1:
            source_opinion_response_flags.append(
                f"R2 has {count} structured responses for {source_id}; exactly one is required."
            )
    for response_item in reported_responses:
        if not isinstance(response_item, dict):
            source_opinion_response_flags.append(
                "R2 returned a non-object attributed-opinion response; it was excluded."
            )
            continue
        source_id = str(response_item.get("source_id") or "")
        expected_excerpt = expected_source_opinions.get(source_id)
        if response_item.get("position_on_source_opinion") not in {
            "supports", "opposes", "conditional", "insufficient_information"
        }:
            source_opinion_response_flags.append(
                f"R2 structured response for {source_id or '(missing source ID)'} "
                "has no valid model-reported position_on_source_opinion; no stance was inferred."
            )
        if expected_excerpt is None:
            source_opinion_response_flags.append(
                f"R2 returned an unregistered attributed-opinion response ID: {source_id or '(missing)'}."
            )
            response_item["source_excerpt"] = ""
            continue
        response_item["source_excerpt"] = expected_excerpt
        analysis = str(response_item.get("analysis") or "")
        option_supported = _source_opinion_component_supported(
            expected_excerpt, analysis, "option"
        )
        conditions_supported = _source_opinion_component_supported(
            expected_excerpt, analysis, "conditions"
        )
        if not option_supported or not conditions_supported:
            missing_parts = []
            if not option_supported:
                missing_parts.append("distinct option")
            if not conditions_supported:
                missing_parts.append("stated prerequisites")
            source_opinion_response_flags.append(
                f"R2 structured response for {source_id} does not retain sufficient source-specific "
                f"language for the {' and '.join(missing_parts)}."
            )
    previous_position = own_independent_assessment.get("position", "unknown")
    if draft.position != previous_position:
        model_rationale = "; ".join(draft.position_changes).strip() if draft.position_changes else ""
        rationale = _compact(model_rationale or draft.response_to_other_perspectives or draft.provisional_conclusion, 320)
        payload["position_changes"] = [f"Round 1 → Round 2: {previous_position} → {draft.position}. Rationale: {rationale}"]
    else:
        payload["position_changes"] = []
    payload["source_peer_ids"] = [peer["agent_id"] for peer in peer_views]
    payload["source_opinion_repair_attempted"] = response_repair_attempted
    payload["source_opinion_repair_status"] = response_repair_status
    payload["source_opinion_repaired_ids"] = repaired_response_ids
    payload["source_reference_integrity_flags"] = (
        _audit_source_references(payload, allowed_sources) + source_opinion_response_flags
    )[:20]
    # Append a clearly labelled, server-authored register of the exact case-summary
    # opinions. This guarantees that a model omission in its free-text narrative
    # cannot make an attributed option or prerequisite disappear from the saved R2
    # narrative. The register is source text, not a specialist conclusion/endorsement.
    if expected_source_opinions:
        register_lines = [
            f"{source_id}: {source_excerpt}"
            for source_id, source_excerpt in expected_source_opinions.items()
        ]
        server_register = (
            "SERVER-BOUND CASE OPINION REGISTER (verbatim source excerpts; "
            "not specialist-authored conclusions, verified facts, or endorsements):\n"
            + "\n".join(register_lines)
        )
        payload["response_to_other_perspectives"] = (
            str(payload.get("response_to_other_perspectives") or "").rstrip()
            + "\n\n"
            + server_register
        )
    payload, case_integrity_flags = await _repair_unsupported_prerequisite_wording(
        case,
        payload,
        round_number=2,
        role_id=profile["agent_id"],
        role_name=profile["name"],
        allowed_sources=allowed_sources,
    )
    return RoundContribution(
        agent_id=profile["agent_id"],
        round_number=2,
        case_data_integrity_flags=case_integrity_flags,
        **payload,
    )


async def generate_adversarial_contribution(
    profile: dict[str, str],
    case: SyntheticCase,
    own_independent_assessment: dict,
    own_debate_contribution: dict,
    peer_debate_views: list[dict],
    max_tokens: int = 1100,
) -> RoundContribution:
    # R3 receives a deliberately small, source-labelled sample. All 45 saved
    # contributions remain in storage and are supplied to the Chair in R4.
    peers = []
    for peer in peer_debate_views[:5]:
        peer_integrity_flags = _r3_peer_case_integrity_flags(peer)
        result = peer["result"]
        peers.append({
            "source": f"R2:{peer['agent_id']}",
            "role": peer["agent_name"],
            "position": result.get("position", "unknown"),
            "conclusion": _compact_r2_text(
                result.get("provisional_conclusion", ""), 260, peer_integrity_flags
            ),
            "response": _compact_r2_text(
                result.get("response_to_other_perspectives", ""), 700, peer_integrity_flags
            ),
            "agreements": [
                _compact_r2_text(item, 180, peer_integrity_flags)
                for item in (result.get("agreements") or [])[:1]
            ],
            "challenges": [
                _compact_r2_text(item, 260, peer_integrity_flags)
                for item in (result.get("substantive_challenges") or [])[:1]
            ],
            "risks": [
                _compact_r2_text(item, 160, peer_integrity_flags)
                for item in (result.get("risk_flags") or [])[:1]
            ],
            "position_changes": [
                _compact_r2_text(item, 180, peer_integrity_flags)
                for item in (result.get("position_changes") or [])[:1]
            ],
            "round1_case_integrity_audit_flags": _compact_case_integrity_flags(
                peer.get("round1_case_integrity_flags"),
                redaction_flags=peer_integrity_flags,
            ),
            "round2_case_integrity_audit_flags": _compact_case_integrity_flags(
                result.get("case_data_integrity_flags"),
                redaction_flags=peer_integrity_flags,
            ),
            "source_opinion_responses": [
                {
                    "source_id": item.get("source_id", ""),
                    "analysis": _compact_r2_text(
                        item.get("analysis", ""), 300, peer_integrity_flags
                    ),
                    "comparison": _compact_r2_text(
                        item.get("comparison", ""), 120, peer_integrity_flags
                    ),
                }
                for item in (result.get("source_opinion_responses") or [])[:4]
                if isinstance(item, dict)
            ],
            "provenance_audit_flags": [
                _compact_r2_text(item, 220, peer_integrity_flags)
                for item in _prioritized_provenance_flags(
                    result.get("source_reference_integrity_flags") or []
                )
            ],
            "provenance_excerpt": (
                _compact_r2_text(
                    _bounded_exact_excerpt(
                        result.get("response_to_other_perspectives", ""), 1600
                    ),
                    1600,
                    peer_integrity_flags,
                )
                if result.get("source_reference_integrity_flags")
                else ""
            ),
        })

    own_r1_integrity_flags = own_independent_assessment.get("case_data_integrity_flags") or []
    own_r2_integrity_flags = own_debate_contribution.get("case_data_integrity_flags") or []
    own_case_integrity_flags = _combined_case_integrity_flags(
        own_r1_integrity_flags, own_r2_integrity_flags
    )
    own = {
        "round1_source": f"R1:{profile['agent_id']}",
        "round1_position": own_independent_assessment.get("position"),
        "round1_conclusion": _compact_r1_text(
            own_independent_assessment.get("provisional_conclusion", ""),
            150,
            own_r1_integrity_flags,
        ),
        "round1_option": _compact_r1_text(
            own_independent_assessment.get("preferred_educational_option", ""),
            140,
            own_r1_integrity_flags,
        ),
        "round1_case_integrity_audit_flags": _compact_case_integrity_flags(
            own_r1_integrity_flags,
            redaction_flags=own_case_integrity_flags,
        ),
        "round2_source": f"R2:{profile['agent_id']}",
        "round2_position": own_debate_contribution.get("position"),
        "round2_conclusion": _compact_r2_text(
            own_debate_contribution.get("provisional_conclusion", ""),
            260,
            own_case_integrity_flags,
        ),
        "round2_response": _compact_r2_text(
            own_debate_contribution.get("response_to_other_perspectives", ""),
            600,
            own_case_integrity_flags,
        ),
        "round2_agreements": [
            _compact_r2_text(item, 180, own_case_integrity_flags)
            for item in (own_debate_contribution.get("agreements") or [])[:2]
        ],
        "round2_challenges": [
            _compact_r2_text(item, 220, own_case_integrity_flags)
            for item in (own_debate_contribution.get("substantive_challenges") or [])[:2]
        ],
        "round2_position_changes": [
            _compact_r2_text(item, 180, own_case_integrity_flags)
            for item in (own_debate_contribution.get("position_changes") or [])[:1]
        ],
        "round2_unknowns": [
            _compact_r2_text(item, 90, own_case_integrity_flags)
            for item in (own_debate_contribution.get("remaining_unknowns") or [])[:2]
        ],
        "round2_risks": [
            _compact_r2_text(item, 90, own_case_integrity_flags)
            for item in (own_debate_contribution.get("risk_flags") or [])[:2]
        ],
        "round2_case_integrity_audit_flags": _compact_case_integrity_flags(
            own_r2_integrity_flags,
            redaction_flags=own_case_integrity_flags,
        ),
        "round2_source_opinion_responses": [
            {
                "source_id": item.get("source_id", ""),
                "analysis": _compact_r2_text(
                    item.get("analysis", ""), 300, own_case_integrity_flags
                ),
                "comparison": _compact_r2_text(
                    item.get("comparison", ""), 120, own_case_integrity_flags
                ),
            }
            for item in (own_debate_contribution.get("source_opinion_responses") or [])[:4]
            if isinstance(item, dict)
        ],
        "round2_provenance_audit_flags": [
            _compact_r2_text(item, 220, own_case_integrity_flags)
            for item in _prioritized_provenance_flags(
                own_debate_contribution.get("source_reference_integrity_flags") or []
            )
        ],
        "round2_provenance_excerpt": (
            _compact_r2_text(
                _bounded_exact_excerpt(
                    own_debate_contribution.get("response_to_other_perspectives", ""), 1600
                ),
                1600,
                own_case_integrity_flags,
            )
            if own_debate_contribution.get("source_reference_integrity_flags")
            else ""
        ),
    }
    allowed_source_ids = [
        f"R1:{profile['agent_id']}",
        f"R2:{profile['agent_id']}",
        *(f"R2:{peer['agent_id']}" for peer in peer_debate_views[:5]),
    ]
    # Source-opinion reviews must cite one of the supplied R2 peers, never this role's own R2 record.
    allowed_peer_source_ids = {f"R2:{peer['agent_id']}" for peer in peer_debate_views[:5]}
    source_opinion_register = extract_attributed_note_opinions(case.case_summary)
    if source_opinion_register:
        attribution_instruction = (
            "CASE ATTRIBUTION CHECK: the server has identified explicitly attributed note opinions in the "
            "original case summary. The ordered server register is authoritative for source IDs and exact excerpts. "
            "Return exactly one source_opinion_review for each listed ID, in the same order; copy source_id and "
            "source_excerpt exactly. Do not duplicate, renumber, merge, omit, or invent an opinion. If the supplied "
            "R2 sample is insufficient to assess an opinion, still return its one review with unclear statuses and "
            "explain the limitation. These are source-reported opinions, not verified facts or MDT consensus. "
            "A peer's R2 contribution is never itself a case-summary attributed opinion."
        )
    elif case_summary_has_attributed_opinions(case.case_summary):
        attribution_instruction = (
            "CASE ATTRIBUTION CHECK: review only clearly speaker-attributed opinions in the verbatim case summary. "
            "A peer's R2 contribution is never itself a case-summary attributed opinion. Do not create a case opinion from a peer role or its R2 ID."
        )
    else:
        attribution_instruction = (
            "CASE ATTRIBUTION CHECK: the verbatim case summary contains no clearly speaker-attributed opinion. "
            "Return source_opinion_reviews as an empty list. Do not invent opinions, treat R2 peer roles as case sources, "
            "or create CASE source IDs from R2 identifiers. Peer records remain separately attributable as R2 sources."
        )
    prompt = (
        "ROUND 3 — ADVERSARIAL REVIEW. Educational simulation only; do not give a treatment "
        "instruction or invent facts/evidence. ABSENT-IS-NOT-UNMET RULE: a missing or undocumented "
        "clinical prerequisite is unknown, not unmet, not met, failed, negative, or absent. If MRI, "
        "local staging, metastatic work-up, resectability review, or fitness/performance assessment "
        "is not supplied in the case, describe it as 'not supplied', 'not documented', or 'unknown'. "
        "Never say that a prerequisite or case condition is 'unmet' or 'not met' merely because its "
        "result or assessment is missing. Use 'unmet'/'not met' only when the case explicitly records "
        "that this exact prerequisite was assessed and a documented finding establishes non-fulfilment; "
        "identify that exact finding. Never describe undocumented prerequisites as 'not met' or 'unmet'; "
        "state that their status is unknown or not supplied. Never conclude that 'neither option is indicated' "
        "or that 'no option is appropriate' from missing data alone. Never convert 'no definitive pathway can be established from this incomplete record' "
        "into 'no pathway is indicated': information sufficiency and a clinical indication decision are different propositions. "
        "Do not conclude that neither option is clinically indicated, that no pathway is indicated, or that no option is appropriate from missing data alone. "
        "When describing peer contributions, you may state that the supplied peer records do not claim an option is indicated only when accurate and explicitly attributed; "
        "this reports what those records say and is not a clinical indication conclusion. "
        "Use this exact safe formulation when indication cannot be determined: 'The supplied information does not establish whether either source option is indicated or appropriate; indication and suitability remain undetermined.' "
        "Do not infer a negative indication from agreement that data are missing or from a peer saying that no definitive pathway can yet be established. "
        "Preserve the source option as conditional while status is unknown; "
        "representation is not endorsement. Treat the verbatim case summary as attributed "
        "source text, not verified fact or consensus. Identify each distinct attributed opinion, "
        "its option, and every prerequisite. Compare each separately with your own saved R1/R2 "
        f"positions and the supplied R2 peer sample. Cite peer roles only with their exact R2:AGENT_ID labels from that sample; never relabel an R2 peer as R1. An R1 citation is permitted only for your own role's independent assessment. When discussing your own R2 record, cite it as R2:{profile['agent_id']}; do not reuse an R1 source ID merely because that ID appears inside your quoted R2 text. The only R1 source you may cite in this round is R1:{profile['agent_id']}. Never cite role ranges, a complete role directory, or an unsupplied role as evidence. Cite only individual source IDs listed under ALLOWED ROUND SOURCE IDS; if an earlier source is mentioned inside an R2 contribution and its original record was not supplied, attribute the statement to that R2 contribution instead. Do not invent or cite an unprovided role. Embedded reference lists inside supplied R2 prose are neutralised to grammatical generic phrases such as 'the referenced role records'; these phrases are not attributable citations. When describing that prose, cite only the outer R2:AGENT_ID label attached to the supplied peer object. Do not copy a neutralised fragment as though it were a direct quotation. Do not conflate different conditional options "
        "or treat shared missing investigations as agreement on a pathway. For each opinion, "
        "assess REPRESENTATION FIDELITY ONLY: whether its option and conditions are faithfully "
        "represented in the actual R2 contribution text supplied to you. Before marking an option or "
        "condition omitted, inspect the matching source_opinion_responses entry for that exact CASE source ID "
        "in each supplied R2 peer record. Those structured source-specific analysis and comparison fields "
        "are part of the saved R2 contribution; do not treat an option or prerequisite as omitted merely "
        "because it is absent from the peer's general conclusion or response_to_other_perspectives. If the "
        "matching source-specific R2 entry retains the distinct option and its prerequisite, classify the "
        "representation as preserved unless that same entry materially changes or contradicts it. "
        "The fact that a peer does not endorse, validate, select, or act on a conditional option is not "
        "an omission when the matching source-specific R2 entry explicitly names that option and retains "
        "its prerequisite. CALIBRATION: an R2 entry that says 'surgery-led assessment first, conditional "
        "on complete local staging and resectability review' but also says it cannot be endorsed until "
        "those data are known has preserved both the option and its condition. Likewise, saying that no "
        "definitive pathway can yet be established does not erase that source-specific entry. Mark "
        "partly_preserved only when the R2 text actually retains only part of the option or condition; "
        "do not use it merely because a fully stated conditional option is unendorsed or not actionable. "
        "This is not an assessment of clinical appropriateness, eligibility, or whether the case satisfies the prerequisites. "
        "A source opinion conditional on MRI, fitness, local staging, or another prerequisite remains "
        "a represented conditional option when R2 retains that option and its conditional wording, "
        "even when the prerequisite is missing or unknown in the case. Missing or undocumented case "
        "prerequisites are case unknowns; do not describe their status as unfulfilled without an explicit assessed finding. They are NOT, by themselves, omissions of the option or "
        "conditions from R2. Mark preserved when the supplied R2 text faithfully retains the option "
        "or condition; partly_preserved when it retains only part; omitted only when the supplied R2 "
        "text itself drops or materially distorts it; use unclear when the supplied material is "
        "insufficient to assess. Assess only the supplied R2 records and never generalise a bounded "
        "sample to all 45 roles. Do not treat an unknown clinical prerequisite as proof that an "
        "option/condition was omitted. If an option/condition was actually omitted, weakened, "
        "conflated, or misrepresented in supplied R2 text, make a source-linked challenge naming CASE:case_summary "
        "and the exact R2:AGENT_ID, the claim/condition, the data or reasoning gap, its possible "
        "effect on the educational synthesis, and what information would resolve it. Do not "
        "manufacture challenges; if the records do not support one, leave the challenge list "
        "empty and explain the limitation. The peer digest is a bounded sample of at most 5 of "
        "44 other roles, not the full MDT. Never generalise it to unshown roles or claim all roles "
        "agree. Your saved R2 contribution and each supplied peer may include server-computed "
        "provenance audit flags and an exact excerpt from that R2 response. These flags are "
        "deterministic source-attribution/scope audit metadata, not clinical evidence or proof that "
        "the contributor's clinical reasoning is wrong. For each flagged R2 source (your own or a "
        "selected peer), compare the flag with its supplied excerpt. When the excerpt supports an "
        "invalid role-range/unsupplied citation or an unsupported whole-MDT scope claim, record a "
        "concise provenance-integrity challenge in substantive_challenges naming that exact "
        "R2:AGENT_ID, explaining the attribution or scope defect (not a clinical disagreement), "
        "and quoting a short exact contiguous excerpt from the supplied R2 response text. For "
        "citation defects, quote the adjacent substantive claim rather than repeating the invalid "
        "role range or unsupplied identifier. If a server-computed audit flag identifies a malformed role range, treat it as invalid syntax: never normalise it into a valid 'to' range, expand the endpoints, infer intermediate roles, or describe the range as partially verified. "
        "The original R2 text and its raw reference string remain saved separately by the server; the flag is an audit warning, not an attributable source citation. Do not cite the audit flag itself as a source; cite "
        "the exact R2 source ID. Do not use a "
        "provenance flag as clinical evidence, infer a clinical disagreement, or change your "
        "clinical position solely because of it. Do not manufacture a challenge when the excerpt "
        "does not support the flag. Preserve uncertainty, conditions, and minority views. Risk "
        "flags are not substitutes for source-linked challenges. "
        "CASE-INTEGRITY AUDIT FLAGS: your own R1/R2 records and selected peer R1/R2 records may "
        "include server-computed case_integrity_audit_flags. These are audit warnings that specific "
        "narrative claims were not supported by the immutable case snapshot; they are not new facts, "
        "not clinical evidence, and do not establish the opposite finding. Treat the flagged claim "
        "as unverified unless the actual supplied case source explicitly supports it. Do not repeat "
        "or rely on it as a fact, do not infer the opposite, and do not silently rewrite the saved "
        "contribution. When the exact supplied text and case source establish a genuine defect, "
        "describe it as an unsupported-claim/provenance risk and cite the exact R2 source; when a "
        "flag appears inconsistent with the supplied source, state that it remains a flag requiring "
        "review rather than declaring the clinical assertion true or false. Preserve the original "
        "narrative and the server audit flag as separate records. Do not reproduce or quote literal TNM/stage values from any flagged R1/R2 assertion, even when attributing or rebutting it; refer only to 'the flagged unsupported staging assertion'. "
        "ADVERSARIAL ASSUMPTION AND RISK CHECK: inspect your own and each supplied R2 record for "
        "unsupported case facts or assumptions (stage, nodal/metastatic status, resectability, "
        "fitness, comorbidities, prior treatment, or patient goals); conclusions treating missing "
        "data as positive, negative, normal, or proof of eligibility/ineligibility; conditional "
        "options converted into unconditional directions; contradictions between position and "
        "narrative/structured fields; overbroad agreement or consensus claims; unsupported "
        "efficacy, safety, guideline, trial, or citation claims; and omitted case-stated "
        "uncertainties or supplied patient, resource, or governance constraints. "
        "WHOLE-MDT CONSENSUS SCOPE CHECK: the supplied peer sample is not a complete 45-role roll-up. "
        "When a supplied R2 record claims that the entire MDT or all 45 roles agree without a complete "
        "45-role contribution set and deterministic proposition-level roll-up in this input, create a "
        "source-linked substantive_challenges entry naming that exact R2:AGENT_ID and quoting a short "
        "exact contiguous phrase from that peer's supplied R2 text. Explain that the bounded sample "
        "cannot establish whole-MDT agreement. Explicitly reject or qualify the quoted claim in "
        "plain language (for example, say it is unsupported by the supplied input or cannot be "
        "established from the supplied sample); quoting or repeating the claim alone does not satisfy "
        "this check. A generic collective critique without the individual R2 source ID and exact quote "
        "is not auditable and does not satisfy this check. Do not challenge "
        "a claim that is explicitly limited to the supplied sample. Check only the "
        "case and R2 text actually supplied; do not import external clinical assumptions. "
        "For each concrete defect, add a concise substantive_challenges item with the exact "
        "R2:AGENT_ID, a short exact quote from that R2 text, the unsupported assumption or "
        "contradiction, why the supplied case does not support it, its possible effect on the "
        "educational synthesis, and what information or evidence would resolve it. Do not "
        "repeat the challenged assertion as fact. If no specific defect is evidenced, leave "
        "substantive_challenges empty and state that no grounded challenge was identified in "
        "the selected sample, with its sampling limitation. Missing information alone is not "
        "a defect when the R2 record correctly preserves it as unknown; never invent a challenge "
        "or risk merely to populate the schema. "
        "Review only distinct attributed opinions explicitly present in the supplied verbatim case_summary; "
        "Assign stable CASE:case_summary#N identifiers in order of first appearance and keep each "
        "identifier attached to the same attributed opinion. Do not assume a fixed number of opinions, "
        "specialty labels, or source institutions. source_excerpt is server-bound metadata; do not generate, paraphrase, or reconstruct it. "
        "Return each server-provided source_id exactly once. After schema validation, the backend attaches the exact original case_summary excerpt by source_id and flags any conflicting model-supplied excerpt. Missing or duplicate source IDs remain validation failures. "
        "If no distinct attributed opinion is clearly present, return an empty source_opinion_reviews list. "
        "For each review, include its source ID, option_status, conditions_status, "
        "a concise review_basis, and source_reference_ids. For each review, source_reference_ids "
        "must include that review's exact CASE source ID and one exact R2:AGENT_ID from the supplied "
        "peer sample. Use only IDs in ALLOWED ROUND SOURCE IDS; never invent an ID and never cite "
        "your own R2 record as a peer. These structured IDs are the machine-readable provenance "
        "for the review and challenge. For EVERY review, including omitted and unclear reviews, "
        "set evidence_peer_id to the selected supplied R2 peer and evidence_excerpt to a short, "
        "verbatim contiguous excerpt from that peer's supplied conclusion, response, agreement, "
        "challenge, risk, or position-change text. For preserved or partly_preserved statuses, "
        "the excerpt must directly contain the option or condition said to be retained. For an "
        "omitted status, quote the most relevant exact text showing how that peer summarised the "
        "issue without retaining the attributed option or condition; explain in review_basis that "
        "the omission is determined by comparing the full cited R2 record with the exact CASE "
        "source, and do not present the quote as affirmative evidence that the option was preserved. "
        "For unclear, quote the relevant available context and explain why it is insufficient. "
        "Do not paraphrase or invent excerpts. If no peer record permits a reliable assessment, "
        "use unclear rather than guessing. The backend checks that the peer ID was supplied and "
        "that the excerpt is an exact substring; this source-binding check does not validate the "
        "clinical or semantic correctness of your interpretation. "
        "Assess representation fidelity only against the actual supplied peer R2 text, not against "
        "whether MRI, staging, fitness, or other clinical prerequisites are fulfilled in the case. "
        "If a conditional option and its prerequisites are retained in a peer R2 record, mark them "
        "preserved even when those prerequisites remain unknown; this does not validate clinical "
        "suitability. A selected evidence excerpt for a preserved option or condition must itself "
        "contain source-specific wording for that component; an unrelated sentence about missing "
        "stage, fitness, or investigations is not evidence that the option/condition was retained. "
        "The saved R2 record may include structured source_opinion_responses; these are part of the "
        "actual R2 contribution, and their analysis/comparison fields may be cited as R2 evidence. "
        "Mark omitted or partly_preserved only when supplied peer R2 text itself omits "
        "or materially distorts the attributed content. Use the full bounded peer response text supplied below (with embedded round-reference tokens neutralized) "
        "and other supplied R2 fields, not only your own R2 response or abbreviated role summaries. "
        "If the peer sample contains both preserved and omitted representations, describe that mixed "
        "sample accurately in review_basis and do not generalise beyond the supplied peers. For an "
        "actual R2 representation omission or distortion, write a source-linked challenge in the review "
        "and copy it into substantive_challenges. Such a challenge must cite the exact CASE source ID "
        "and the selected supplied R2 peer ID. If status is unclear, explain the limitation and do not "
        "invent a challenge. Cases without clearly attributable opinions must have an empty review list.\n"
        + attribution_instruction + "\n"
        + f"ALLOWED ROUND SOURCE IDS: {', '.join(allowed_source_ids)}\n"
        + f"ALLOWED SOURCE-OPINION REVIEW PEER IDS (the only permitted R2 evidence_peer_id values and R2 citations inside source_opinion_reviews): {', '.join(sorted(allowed_peer_source_ids))}\n"
        + f"FORBIDDEN FOR SOURCE-OPINION REVIEWS: R2:{profile['agent_id']} is your own R2 record, not a peer; never cite it as review evidence. This narrower peer-only list overrides ALLOWED ROUND SOURCE IDS for source_opinion_reviews.\n"
        f"ROLE: {profile['name']}\nMANDATE: {profile['mandate']}\nCLINICAL PHILOSOPHY: {profile.get('clinical_philosophy', '')}\n"
        "SUPPLIED CASE:\n"
        + json.dumps(build_case_prompt_context(case), ensure_ascii=False, separators=(",", ":"))
        + "\nSTAGING LOCK (STG-00): Do NOT rethink, re-stage, or dispute T/N/M values during debate or adversarial review; accept STG-00's fixed staging.\n"
        + "\nSERVER-IDENTIFIED ATTRIBUTED SOURCE OPINIONS (exact case-summary excerpts; not verified facts):\n"
        + json.dumps(source_opinion_register, ensure_ascii=False, separators=(",", ":"))
        + "\nYOUR R1 AND COMPLETE OWN R2 RECORD (bounded fields):\n"
        + json.dumps(own, ensure_ascii=False, separators=(",", ":"))
        + "\nSELECTED SOURCE-LABELLED R2 PEER SAMPLE:\n"
        + json.dumps(peers, ensure_ascii=False, separators=(",", ":"))
        + "\nReturn concise, concrete findings only. The output format is schema-enforced."
    )
    try:
        from app.services.evidence_retrieval import get_evidence_retrieval_engine
        engine = get_evidence_retrieval_engine()
        passages = engine.retrieve_evidence_for_role(profile.get("agent_id", ""), case, limit=3)
        evidence_context = engine.format_prompt_injection(passages)
        if evidence_context:
            prompt += f"\n\n{evidence_context}"
    except Exception as exc:
        logger.debug("Evidence retrieval omitted in generate_adversarial_contribution: %s", exc)

    draft = await _generate_structured(prompt, AdversarialContributionDraft, max_tokens)
    payload = draft.model_dump()
    payload["remaining_unknowns"] = _unique_strings(
        list(case.known_unknowns or []) + list(payload.get("remaining_unknowns") or []),
        limit=8,
    )
    allowed_review_source_ids = {
        f"R1:{profile['agent_id']}",
        *allowed_peer_source_ids,
    }
    review_reference_flags: list[str] = []
    expected_source_opinions_by_id = {
        item["source_id"]: item["source_excerpt"]
        for item in source_opinion_register
    }
    initial_reviews = payload.get("source_opinion_reviews") or []
    payload["model_reported_source_opinion_reviews"] = [
        json.loads(json.dumps(item))
        for item in initial_reviews
        if isinstance(item, dict)
    ][:4]
    if not expected_source_opinions_by_id and initial_reviews:
        review_reference_flags.append(
            f"Model returned {len(initial_reviews)} source-opinion review(s) although the "
            "server-owned attributed-opinion register is empty; raw entries were preserved "
            "in model_reported_source_opinion_reviews and excluded from canonical source_opinion_reviews."
        )
        payload["source_opinion_reviews"] = []
    initial_review_counts = Counter(
        str(item.get("source_id") or "")
        for item in initial_reviews
        if isinstance(item, dict)
    )
    missing_review_ids = [
        source_id for source_id in expected_source_opinions_by_id
        if initial_review_counts.get(source_id, 0) == 0
    ]
    review_repair_attempted = False
    review_repair_status = "not_needed"
    repaired_review_ids: list[str] = []
    if missing_review_ids:
        review_repair_attempted = True
        review_repair_status = "incomplete"
        missing_review_register = [
            {"source_id": source_id, "source_excerpt": expected_source_opinions_by_id[source_id]}
            for source_id in missing_review_ids
        ]
        repair_peer_context = []
        for peer in peers:
            matching_responses = [
                item for item in (peer.get("source_opinion_responses") or [])
                if isinstance(item, dict) and item.get("source_id") in missing_review_ids
            ]
            if matching_responses:
                repair_peer_context.append({
                    "source": peer["source"],
                    "role": peer["role"],
                    "source_opinion_responses": matching_responses,
                })
        repair_prompt = (
            "ROUND 3 SOURCE-OPINION REVIEW COVERAGE REPAIR. Complete only the missing "
            "server-identified source reviews listed below. Return exactly one review for each "
            "missing ID, in the same order, and no other IDs. This is REPRESENTATION FIDELITY "
            "ONLY: compare the original source option and its prerequisites with the matching "
            "structured source_opinion_responses in the actually supplied R2 peer records. "
            "Do not assess clinical appropriateness, eligibility, or whether case prerequisites "
            "are fulfilled. A conditional option remains preserved if that exact R2 structured "
            "response retains the option and condition, even if the general conclusion is that "
            "no pathway can yet be established. Do not mark omitted because clinical information "
            "is missing. If a supplied peer has a matching structured response, use one such peer "
            "only; source_reference_ids must contain the exact CASE source ID and exactly one "
            "matching supplied R2 peer ID, and evidence_peer_id must use that same R2 ID. "
            "Never cite a peer lacking a matching source_opinion_responses entry. If no supplied "
            "peer has a matching entry, return unclear statuses and explain the evidence limitation "
            "without fabricating a citation. Do not invent facts, excerpts, or challenges. The "
            "server will bind the exact case-summary excerpt and verify the peer evidence.\n"
            f"ROLE: {profile['name']} ({profile['agent_id']})\n"
            "MISSING REGISTER (server-authoritative IDs and exact excerpts):\n"
            + json.dumps(missing_review_register, ensure_ascii=False, separators=(",", ":"))
            + "\nACTUALLY SUPPLIED R2 PEER SOURCE-OPINION RECORDS:\n"
            + json.dumps(repair_peer_context, ensure_ascii=False, separators=(",", ":"))
            + "\nALLOWED R2 PEER IDS:\n"
            + json.dumps(sorted(allowed_peer_source_ids), ensure_ascii=False, separators=(",", ":"))
            + "\nReturn only source_id, option_status, conditions_status, review_basis, "
            "source_reference_ids, evidence_peer_id, evidence_excerpt, and challenge. "
            "Do not author server-computed provenance metadata."
        )
        try:
            repair_draft = await _generate_structured(
                repair_prompt, AdversarialSourceOpinionReviewsRepairDraft, 850
            )
            repaired_items = [item.model_dump() for item in repair_draft.source_opinion_reviews]
            existing_reviews = list(initial_reviews)
            existing_reviews.extend(repaired_items)
            payload["source_opinion_reviews"] = existing_reviews
            repaired_review_ids = list(dict.fromkeys(
                str(item.get("source_id") or "")
                for item in repaired_items
                if str(item.get("source_id") or "") in missing_review_ids
            ))
            repaired_counts = Counter(
                str(item.get("source_id") or "")
                for item in repaired_items
                if isinstance(item, dict)
            )
            review_repair_status = (
                "completed"
                if all(repaired_counts.get(source_id, 0) == 1 for source_id in missing_review_ids)
                and all(source_id in missing_review_ids for source_id in repaired_counts)
                else "incomplete"
            )
            if review_repair_status != "completed":
                review_reference_flags.append(
                    "R3 source-opinion review repair did not return exactly one review for each missing registered source ID."
                )
        except Exception as exc:
            review_repair_status = "failed"
            review_reference_flags.append(
                f"R3 source-opinion review repair failed ({type(exc).__name__}: {str(exc)[:180]})."
            )
    actual_review_counts = Counter(
        str(item.get("source_id") or "")
        for item in (payload.get("source_opinion_reviews") or [])
        if isinstance(item, dict)
    )
    duplicate_review_ids = {
        source_id for source_id, count in actual_review_counts.items() if source_id and count > 1
    }
    if expected_source_opinions_by_id:
        for expected_id in expected_source_opinions_by_id:
            count = actual_review_counts.get(expected_id, 0)
            if count == 0:
                review_reference_flags.append(
                    f"Required server-identified source opinion {expected_id} has no R3 review."
                )
            elif count > 1:
                review_reference_flags.append(
                    f"Server-identified source opinion {expected_id} has {count} duplicate R3 reviews; exactly one is required."
                )
        for actual_id in sorted(set(actual_review_counts) - set(expected_source_opinions_by_id)):
            if actual_id:
                review_reference_flags.append(
                    f"R3 returned an unregistered case-summary source opinion ID: {actual_id}."
                )
    # The exact excerpt is immutable source data already extracted by the server.
    # Bind it deterministically instead of spending model tokens copying it or
    # trusting a paraphrase. Unknown IDs remain unbound and are still flagged below.
    for review in payload.get("source_opinion_reviews") or []:
        if not isinstance(review, dict):
            continue
        source_id = str(review.get("source_id") or "")
        expected_excerpt = expected_source_opinions_by_id.get(source_id)
        if expected_excerpt is None:
            continue
        model_excerpt = str(review.get("source_excerpt") or "")
        if model_excerpt and model_excerpt != expected_excerpt:
            review_reference_flags.append(
                f"Model-supplied excerpt for {source_id} differed from the server register; "
                "the exact case-summary excerpt was bound by the server."
            )
        review["source_excerpt"] = expected_excerpt

    case_source_id_pattern = re.compile(r"^CASE:case_summary#([1-9][0-9]*)$")
    case_source_id_to_excerpt: dict[str, str] = {}
    case_excerpt_to_source_id: dict[str, str] = {}
    conflicting_case_source_ids: set[str] = set()

    # Keep weak source reviews parseable, but require exact source text for traceability.
    for review in payload.get("source_opinion_reviews") or []:
        if not isinstance(review, dict):
            continue
        source_id = str(review.get("source_id") or "")
        source_excerpt = str(review.get("source_excerpt") or "")
        if not case_source_id_pattern.fullmatch(source_id):
            review_reference_flags.append(
                f"Review for {source_id or 'unknown source'} has an invalid CASE source identifier; "
                "expected CASE:case_summary#N."
            )
            continue
        expected_excerpt = expected_source_opinions_by_id.get(source_id)
        if expected_source_opinions_by_id and expected_excerpt is None:
            review_reference_flags.append(
                f"Review for {source_id} does not match a server-identified source opinion."
            )
            continue
        if expected_excerpt is not None and source_excerpt != expected_excerpt:
            review_reference_flags.append(
                f"Review for {source_id} does not reproduce its exact server-identified case-summary excerpt."
            )
            continue
        if not source_excerpt or source_excerpt not in case.case_summary:
            review_reference_flags.append(
                f"Review for {source_id} has no exact contiguous source_excerpt from the supplied case_summary."
            )
            continue
        prior_excerpt = case_source_id_to_excerpt.get(source_id)
        if prior_excerpt is not None and prior_excerpt != source_excerpt:
            conflicting_case_source_ids.add(source_id)
            review_reference_flags.append(
                f"CASE source identifier {source_id} is assigned to multiple different case-summary excerpts."
            )
        prior_id = case_excerpt_to_source_id.get(source_excerpt)
        if prior_id is not None and prior_id != source_id:
            conflicting_case_source_ids.update({prior_id, source_id})
            review_reference_flags.append(
                f"The same exact case-summary excerpt is assigned both {prior_id} and {source_id}."
            )
        case_source_id_to_excerpt[source_id] = source_excerpt
        case_excerpt_to_source_id[source_excerpt] = source_id

    traceable_case_source_ids = (
        set(case_source_id_to_excerpt) - conflicting_case_source_ids - duplicate_review_ids
    )

    # Capture the model's raw labels and references, then server-bind a trusted
    # peer citation only when its excerpt is an exact substring of an R2 peer record
    # that was actually supplied to this role. The model cannot self-author provenance.
    for review in payload.get("source_opinion_reviews") or []:
        if not isinstance(review, dict):
            continue
        review["model_reported_option_status"] = str(review.get("option_status") or "")
        review["model_reported_conditions_status"] = str(review.get("conditions_status") or "")
        reported_refs = review.get("source_reference_ids") or []
        review["model_reported_source_reference_ids"] = [
            str(item) for item in reported_refs if isinstance(item, str)
        ]
        source_id = str(review.get("source_id") or "")
        evidence_peer_id = str(review.get("evidence_peer_id") or "")
        model_evidence_excerpt = str(review.get("evidence_excerpt") or "").strip()
        review["model_reported_evidence_excerpt"] = model_evidence_excerpt
        review["model_reported_evidence_peer_id"] = evidence_peer_id
        evidence_peer_selection_method = (
            "model_reported" if evidence_peer_id in allowed_peer_source_ids else
            ("invalid" if evidence_peer_id else "missing")
        )
        # Small local models may cite the correct supplied peer in review_basis but
        # omit the dedicated evidence_peer_id field. Treat that prose citation only
        # as an untrusted selection hint: accept it only when exactly one R2 ID is
        # named and it is in this role's actual supplied-peer allowlist. The server
        # still binds the evidence to that peer's unique structured response for
        # this exact CASE source; prose alone can never verify an excerpt.
        if not evidence_peer_id:
            structured_peer_ids = sorted({
                str(item).strip()
                for item in reported_refs
                if isinstance(item, str)
                and re.fullmatch(r"R2:[A-Z]{2}-[0-9]{2}", item.strip())
            })
            structured_case_source_present = any(
                isinstance(item, str) and item.strip() == source_id
                for item in reported_refs
            )
            if (
                structured_case_source_present
                and len(structured_peer_ids) == 1
                and structured_peer_ids[0] in allowed_peer_source_ids
            ):
                evidence_peer_id = structured_peer_ids[0]
                review["evidence_peer_id"] = evidence_peer_id
                evidence_peer_selection_method = "server_bound_structured_source_reference"
            elif structured_peer_ids:
                # More than one candidate or an unsupplied candidate is ambiguous/invalid.
                # Do not let prose override an ambiguous structured citation.
                evidence_peer_selection_method = "invalid"
            else:
                basis_peer_ids = sorted(set(re.findall(
                    r"\bR2:[A-Z]{2}-[0-9]{2}\b",
                    str(review.get("review_basis") or ""),
                )))
                if len(basis_peer_ids) == 1 and basis_peer_ids[0] in allowed_peer_source_ids:
                    evidence_peer_id = basis_peer_ids[0]
                    review["evidence_peer_id"] = evidence_peer_id
                    evidence_peer_selection_method = "server_bound_review_basis_reference"
                elif basis_peer_ids:
                    evidence_peer_selection_method = "invalid"
        review["evidence_peer_selection_method"] = evidence_peer_selection_method
        # Evidence validation uses the original saved R2 contribution, never the
        # prompt-sanitised peer copy. Sanitised prompt phrases (for example,
        # "the referenced role records") must not become quotable source evidence.
        evidence_peer = next(
            (
                item for item in peer_debate_views[:5]
                if f"R2:{item.get('agent_id', '')}" == evidence_peer_id
            ),
            None,
        )
        evidence_peer_result = (
            evidence_peer.get("result")
            if isinstance(evidence_peer, dict) and isinstance(evidence_peer.get("result"), dict)
            else None
        )
        evidence_texts: list[str] = []
        if evidence_peer_result is not None:
            conclusion = evidence_peer_result.get("provisional_conclusion")
            response = evidence_peer_result.get("response_to_other_perspectives")
            if isinstance(conclusion, str):
                evidence_texts.append(conclusion)
            if isinstance(response, str):
                evidence_texts.append(response)
            for key in ("agreements", "substantive_challenges", "risk_flags", "position_changes"):
                evidence_texts.extend(
                    item for item in (evidence_peer_result.get(key) or [])
                    if isinstance(item, str)
                )
            for opinion_response in evidence_peer_result.get("source_opinion_responses") or []:
                if isinstance(opinion_response, dict):
                    for key in ("analysis", "comparison"):
                        if isinstance(opinion_response.get(key), str):
                            evidence_texts.append(opinion_response[key])
        evidence_excerpt, evidence_binding_method = (
            _bind_exact_peer_evidence_excerpt(model_evidence_excerpt, evidence_texts)
            if evidence_peer is not None and evidence_peer_id in allowed_peer_source_ids
            else ("", "invalid" if evidence_peer_id or model_evidence_excerpt else "missing")
        )
        source_excerpt_for_review = expected_source_opinions_by_id.get(source_id, "")
        matching_source_opinion_responses = [
            item
            for item in (evidence_peer_result.get("source_opinion_responses") or [])
            if isinstance(item, dict) and item.get("source_id") == source_id
        ] if evidence_peer_result is not None else []
        source_specific_evidence_texts: list[str] = []
        if len(matching_source_opinion_responses) == 1:
            for key in ("analysis", "comparison"):
                value = matching_source_opinion_responses[0].get(key)
                if isinstance(value, str):
                    source_specific_evidence_texts.append(value)

        # A valid quote can still point to the wrong CASE opinion within the
        # selected peer, or omit the source-specific option while quoting only
        # its missing prerequisites. In that situation, select a bounded exact
        # passage only from the selected peer's unique structured response for
        # this same server-identified CASE source. Never search another peer or
        # another CASE source; an absent/ambiguous response remains unverified.
        if (
            (model_evidence_excerpt or evidence_peer_id)
            and evidence_peer is not None
            and evidence_peer_id in allowed_peer_source_ids
            and source_id in traceable_case_source_ids
            and source_excerpt_for_review
        ):
            quote_has_source_anchors = bool(evidence_excerpt) and all(
                _source_opinion_component_supported(
                    source_excerpt_for_review, evidence_excerpt, component
                )
                for component in ("option", "conditions")
            )
            if not quote_has_source_anchors:
                server_selected_excerpt = _select_source_opinion_evidence_excerpt(
                    source_excerpt_for_review,
                    source_specific_evidence_texts,
                )
                if server_selected_excerpt:
                    evidence_excerpt = server_selected_excerpt
                    evidence_binding_method = "server_selected_source_match"

        review["evidence_excerpt"] = evidence_excerpt
        review["evidence_excerpt_binding_method"] = evidence_binding_method
        if evidence_excerpt:
            for field, model_field, component in (
                ("option_status", "model_reported_option_status", "option"),
                ("conditions_status", "model_reported_conditions_status", "conditions"),
            ):
                reported_status = review.get(model_field)
                source_excerpt_for_review = expected_source_opinions_by_id.get(source_id, "")
                supported = _source_opinion_component_supported(
                    source_excerpt_for_review, evidence_excerpt, component
                )
                partial_support = _source_opinion_component_has_any_support(
                    source_excerpt_for_review, evidence_excerpt, component
                )
                source_tokens = _source_opinion_component_tokens(
                    source_excerpt_for_review, component
                )
                omitted_but_supported = (
                    reported_status in {"omitted", "partly_preserved"}
                    and bool(source_tokens)
                    and supported
                )
                unsupported_preservation = (
                    reported_status == "preserved" and not supported
                ) or (
                    reported_status == "partly_preserved" and not partial_support
                )
                if omitted_but_supported:
                    review[field] = "unclear"
                    review_reference_flags.append(
                        f"R3 review for {source_id or 'unknown source'} reports the {component} as "
                        f"{reported_status}, but the exact verified R2 peer excerpt contains "
                        "sufficient source-specific wording; the status was downgraded to unclear. "
                        "The model's original label remains in the audit fields."
                    )
                elif unsupported_preservation:
                    review[field] = "unclear"
                    review_reference_flags.append(
                        f"Review for {source_id or 'unknown source'} marks the {component} as "
                        f"{reported_status}, but its exact R2 excerpt does not contain sufficient "
                        "source-specific wording; the status was downgraded to unclear."
                    )
        # A model-authored CASE identifier is never sufficient to create a
        # source opinion. Only opinions extracted into the server-owned register
        # can participate in coverage or carry a verified peer citation.
        if not expected_source_opinions_by_id:
            evidence_status = "invalid"
            review["option_status"] = "unclear"
            review["conditions_status"] = "unclear"
            review["source_reference_ids"] = []
            review["evidence_validation_status"] = evidence_status
            review_reference_flags.append(
                f"R3 review for {source_id or 'unknown source'} was excluded because "
                "the server could not bind a case-summary source-opinion register."
            )
            continue
        if not evidence_peer_id and not model_evidence_excerpt:
            evidence_status = "missing"
        elif (
            evidence_peer is not None
            and evidence_peer_id in allowed_peer_source_ids
            and evidence_excerpt
            and evidence_binding_method in {
                "exact_model_quote",
                "server_bound_contiguous_match",
                "server_selected_source_match",
            }
        ):
            evidence_status = "verified"
        else:
            evidence_status = "invalid"
        review["evidence_validation_status"] = evidence_status
        # Rebuild canonical references from server-verified material only. The
        # original model references remain separately persisted for audit.
        review["source_reference_ids"] = (
            [source_id, evidence_peer_id]
            if source_id and evidence_status == "verified"
            else ([source_id] if source_id else [])
        )
        if evidence_status != "verified":
            if review["model_reported_option_status"] in {"preserved", "partly_preserved", "omitted"}:
                review["option_status"] = "unclear"
            if review["model_reported_conditions_status"] in {"preserved", "partly_preserved", "omitted"}:
                review["conditions_status"] = "unclear"

    # Preserve raw model challenge values for audit, but do not promote exact
    # empty-response sentinels such as "none" into substantive Chair challenges.
    raw_challenges = [
        item for item in (payload.get("substantive_challenges") or [])
        if isinstance(item, str)
    ]
    payload["model_reported_substantive_challenges"] = raw_challenges[:8]
    payload["model_reported_source_review_challenges"] = [
        {
            "source_id": str(item.get("source_id") or ""),
            "challenge": str(item.get("challenge") or ""),
        }
        for item in (payload.get("source_opinion_reviews") or [])
        if isinstance(item, dict) and str(item.get("challenge") or "").strip()
    ][:4]
    challenges = [
        item for item in raw_challenges
        if not _is_empty_challenge_placeholder(item)
    ]
    for review in payload.get("source_opinion_reviews") or []:
        if isinstance(review, dict) and _is_empty_challenge_placeholder(review.get("challenge")):
            # Preserve the original in model_reported_source_review_challenges above.
            review["challenge"] = ""
    for review in payload.get("source_opinion_reviews") or []:
        if not isinstance(review, dict):
            continue
        source_id = str(review.get("source_id") or "")
        reference_ids = review.get("source_reference_ids") or []
        valid_peer_reference_ids = {
            str(reference_id)
            for reference_id in reference_ids
            if str(reference_id) in allowed_peer_source_ids
        }
        review_source_excerpt = str(review.get("source_excerpt") or "")
        review_source_is_traceable = (
            source_id in traceable_case_source_ids
            and review_source_excerpt == case_source_id_to_excerpt.get(source_id)
            and review_source_excerpt in case.case_summary
        )
        statuses = {
            review.get("option_status"),
            review.get("conditions_status"),
        }
        # Small local models sometimes place a correctly source-labelled challenge in
        # substantive_challenges but leave the corresponding review.challenge blank.
        # Recover it only when exactly one challenge names this CASE source and one
        # actually supplied R2 peer, and both IDs are also present in this review's
        # structured references. Ambiguous/unreferenced prose remains unassigned and
        # is still flagged below; no challenge text or citation is invented.
        if statuses.intersection({"partly_preserved", "omitted"}) and not str(review.get("challenge") or "").strip():
            candidate_bodies: dict[str, str] = {}
            for candidate in challenges:
                if not isinstance(candidate, str) or len(candidate) > 700:
                    continue
                case_refs = set(re.findall(r"\bCASE:case_summary#\d+\b", candidate))
                peer_refs = set(re.findall(r"\bR2:[A-Z]{2}-[0-9]{2}\b", candidate))
                round_refs = set(_ROUND_REFERENCE_PATTERN.findall(candidate))
                if (
                    case_refs == {source_id}
                    and len(peer_refs) == 1
                    and peer_refs.issubset(allowed_peer_source_ids)
                    and peer_refs.issubset(set(reference_ids))
                    and all(round_number == "2" and f"R2:{agent_id}" in peer_refs
                            for round_number, agent_id in round_refs)
                ):
                    body = re.sub(r"^\[Sources:\s*[^\]]+\]\s*", "", candidate).strip()
                    if body:
                        candidate_bodies[body] = body
            if len(candidate_bodies) == 1:
                review["challenge"] = next(iter(candidate_bodies))
        reported_reference_ids = {
            str(item)
            for item in (review.get("model_reported_source_reference_ids") or [])
            if isinstance(item, str)
        }
        if source_id not in reported_reference_ids:
            review_reference_flags.append(
                f"Model-reported references for {source_id or 'unknown source'} omits its attributed CASE source ID; the canonical CASE ID was server-bound."
            )
        if not review_source_is_traceable:
            review_reference_flags.append(
                f"Review for {source_id or 'unknown source'} is not bound to one unique exact case-summary excerpt."
            )
        if not any(reference_id in allowed_peer_source_ids for reference_id in reference_ids):
            model_reported_peer_ids = sorted(
                (
                    reported_reference_ids
                    | {str(review.get("model_reported_evidence_peer_id") or "")}
                )
                & allowed_peer_source_ids
            )
            if model_reported_peer_ids:
                review_reference_flags.append(
                    f"Review for {source_id or 'unknown source'} named supplied R2 peer(s) "
                    + ", ".join(model_reported_peer_ids)
                    + ", but no server-verified source-specific excerpt could be bound; "
                    "the peer citation was withheld from canonical references."
                )
            else:
                review_reference_flags.append(
                    f"Review for {source_id or 'unknown source'} does not cite an R2 peer actually supplied to this role."
                )
        invalid_ids = sorted(reported_reference_ids - ({source_id} | allowed_review_source_ids))
        if invalid_ids:
            review_reference_flags.append(
                f"Review for {source_id or 'unknown source'} cites source IDs not supplied to this role: "
                + ", ".join(invalid_ids[:4]) + "."
            )
        statuses = {
            review.get("option_status"),
            review.get("conditions_status"),
        }
        challenge = str(review.get("challenge") or "").strip()
        if statuses.intersection({"partly_preserved", "omitted"}) and not challenge:
            review_reference_flags.append(
                f"Review for {source_id or 'unknown source'} marks an option/condition omitted "
                "or partly preserved but provides no source-linked challenge."
            )
        model_statuses = {
            review.get("model_reported_option_status"),
            review.get("model_reported_conditions_status"),
        }
        if model_statuses.intersection({"preserved", "partly_preserved", "omitted"}) and review.get("evidence_validation_status") != "verified":
            review_reference_flags.append(
                f"Review for {source_id or 'unknown source'} has no exact supporting excerpt "
                "from a cited R2 peer record actually supplied to this role; model-reported "
                "option/condition labels were downgraded to unclear."
            )
        if challenge:
            if (
                not review_source_is_traceable
                or source_id not in reference_ids
                or len(valid_peer_reference_ids) != 1
                or invalid_ids
                or review.get("evidence_validation_status") != "verified"
            ):
                review_reference_flags.append(
                    f"Challenge for {source_id or 'unknown source'} was not promoted because it requires "
                    "one unique CASE review and one server-verified exact excerpt from a supplied R2 peer."
                )
            else:
                canonical_source_ids = [source_id, next(iter(valid_peer_reference_ids))]
                source_prefix = "[Sources: " + "; ".join(canonical_source_ids) + "] "
                canonical_challenge = source_prefix + challenge
                if canonical_challenge not in challenges:
                    challenges.append(canonical_challenge)
    generated_case_refs = set(
        re.findall(r"\bCASE:case_summary#\d+\b", " ".join(_payload_strings(payload)))
    )
    for reference_id in sorted(generated_case_refs - traceable_case_source_ids):
        review_reference_flags.append(
            f"Reference {reference_id} is not backed by a unique exact case-summary source excerpt."
        )
    payload["substantive_challenges"] = challenges[:8]
    previous_position = own_debate_contribution.get("position", "unknown")
    if draft.position != previous_position:
        model_rationale = "; ".join(draft.position_changes).strip() if draft.position_changes else ""
        rationale = _compact(model_rationale or draft.response_to_other_perspectives or draft.provisional_conclusion, 320)
        payload["position_changes"] = [f"Round 2 → Round 3: {previous_position} → {draft.position}. Rationale: {rationale}"]
    else:
        payload["position_changes"] = []
    allowed_sources = {("R1", profile["agent_id"]), ("R2", profile["agent_id"])} | {
        ("R2", peer["agent_id"]) for peer in peer_debate_views[:5]
    }
    payload["source_peer_ids"] = [peer["agent_id"] for peer in peer_debate_views[:5]]
    payload["source_opinion_repair_attempted"] = review_repair_attempted
    payload["source_opinion_repair_status"] = review_repair_status
    payload["source_opinion_repaired_ids"] = repaired_review_ids
    payload["source_reference_integrity_flags"] = (
        _audit_source_references(payload, allowed_sources)
        + review_reference_flags
    )[:20]
    payload, case_integrity_flags = await _repair_unsupported_prerequisite_wording(
        case,
        payload,
        round_number=3,
        role_id=profile["agent_id"],
        role_name=profile["name"],
        allowed_sources=allowed_sources,
    )
    return RoundContribution(
        agent_id=profile["agent_id"],
        round_number=3,
        case_data_integrity_flags=case_integrity_flags,
        **payload,
    )
