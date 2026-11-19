"""Deterministic, read-only diagnostics for exported four-round MDT runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROUND_KEYS = {
    "R1": ("independent_assessments", "assessment"),
    "R2": ("debate", "result"),
    "R3": ("adversarial_review", "result"),
}
FIELDS = {
    "R1": ("provisional_conclusion", "perspective_summary", "preferred_educational_option"),
    "R2": ("provisional_conclusion", "response_to_other_perspectives"),
    "R3": ("provisional_conclusion", "response_to_other_perspectives"),
}
STAGE_TOKEN = re.compile(r"\b(?:c|p)?T(?:is|[0-4][a-d]?)(?:N[0-3x](?:M[0-1x])?)?|\bN[0-3x]\b|\bM[0-1x]\b", re.I)
STRUCTURED_STAGE_FIELDS = (
    "clinical_stage", "pathological_stage", "tnm_stage", "stage",
    "clinical_t_stage", "clinical_n_stage", "clinical_m_stage",
    "pathological_t_stage", "pathological_n_stage", "pathological_m_stage",
)


def _structured_stage_text(snapshot: dict) -> str:
    """Read only explicitly named structured staging fields, never narrative text.

    Component fields store bare values (for example clinical_t_stage="1"), so
    retain the field's T/N/M meaning when constructing comparison tokens.
    """
    values = []
    component_prefixes = {
        "clinical_t_stage": "T", "clinical_n_stage": "N", "clinical_m_stage": "M",
        "pathological_t_stage": "T", "pathological_n_stage": "N", "pathological_m_stage": "M",
    }
    for field in STRUCTURED_STAGE_FIELDS:
        value = snapshot.get(field)
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            continue
        text_value = str(value).strip()
        if not text_value:
            continue
        prefix = component_prefixes.get(field)
        values.append(f"{prefix}{text_value}" if prefix else text_value)
    return " ".join(values)


def _text(value: Any) -> str:
    return " ".join(value.casefold().split()) if isinstance(value, str) else ""


def _populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _jaccard(a: str, b: str) -> float:
    left = set(re.findall(r"[a-z0-9]+", a))
    right = set(re.findall(r"[a-z0-9]+", b))
    return len(left & right) / len(left | right) if left or right else 1.0


def build_diagnostics(export: dict, raw_bytes: bytes, near_duplicate_threshold: float = 0.70) -> dict:
    """Summarise observable fields; never infer, adjudicate or mutate source facts."""
    if not isinstance(export, dict):
        raise ValueError("Export root must be a JSON object.")
    run = export.get("run") if isinstance(export.get("run"), dict) else {}
    snapshot = export.get("case_snapshot") if isinstance(export.get("case_snapshot"), dict) else {}
    snapshot_text = _structured_stage_text(snapshot)
    report = {
        "schema": "radonc_saved_run_quality_diagnostics_v1",
        "scope": {
            "read_only": True,
            "model_inference_performed": False,
            "clinical_correctness_assessed": False,
            "near_duplicate_threshold": near_duplicate_threshold,
            "near_duplicate_interpretation": "triage_signal_only_not_proof_of_copying",
        },
        "source": {
            "run_id": run.get("run_id"),
            "run_status": run.get("status"),
            "case_snapshot_sha256": export.get("case_snapshot_sha256"),
            "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        },
        "rounds": {},
        "text_similarity": [],
        "staging_reference_flags": [],
        "limitations": [
            "Field population is not a measure of clinical adequacy.",
            "Text similarity cannot establish copying or poor reasoning.",
            "Stage-token flags require source review and do not adjudicate stage correctness.",
            "No clinical fact is inferred and no source record is modified.",
        ],
    }
    for round_name, (rows_key, payload_key) in ROUND_KEYS.items():
        rows = export.get(rows_key)
        rows = rows if isinstance(rows, list) else []
        payloads = [(row, row.get(payload_key)) for row in rows
                    if isinstance(row, dict) and row.get("status") == "completed"
                    and isinstance(row.get(payload_key), dict)]
        role_ids = [str(row.get("agent_id") or "").strip().upper() for row, _ in payloads]
        role_counts = Counter(role_ids)
        fields = (("case_facts", "assumptions", "unknowns", "discussion_options", "evidence_claims", "evidence_gaps")
                  if round_name == "R1" else
                  ("agreements", "substantive_challenges", "position_changes", "remaining_unknowns", "risk_flags"))
        field_population = {}
        for field in fields:
            count = sum(_populated(payload.get(field)) for _, payload in payloads)
            field_population[field] = {"populated_roles": count, "empty_or_missing_roles": len(payloads) - count}
        positions = Counter(payload["position"] for _, payload in payloads
                            if isinstance(payload.get("position"), str) and payload["position"].strip())
        report["rounds"][round_name] = {
            "source_rows": len(rows),
            "completed_payload_rows": len(payloads),
            "distinct_identified_roles": len({x for x in role_ids if x}),
            "duplicate_role_ids": sorted(x for x, n in role_counts.items() if x and n > 1),
            "position_counts": dict(sorted(positions.items())),
            "field_population": field_population,
        }
        for field in FIELDS[round_name]:
            groups = defaultdict(list)
            for row, payload in payloads:
                value, role = _text(payload.get(field)), str(row.get("agent_id") or "").strip().upper()
                if value and role:
                    groups[value].append(role)
            for value, roles in groups.items():
                if len(roles) > 1:
                    report["text_similarity"].append({
                        "round": round_name, "field": field, "kind": "exact_duplicate",
                        "roles": sorted(roles), "similarity": 1.0,
                        "text_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    })

    for round_name, (rows_key, payload_key) in ROUND_KEYS.items():
        rows = export.get(rows_key)
        rows = rows if isinstance(rows, list) else []
        entries = []
        for row in rows:
            if not isinstance(row, dict) or row.get("status") != "completed":
                continue
            payload = row.get(payload_key)
            if not isinstance(payload, dict):
                continue
            value, role = _text(payload.get("provisional_conclusion")), str(row.get("agent_id") or "").strip().upper()
            if value and role:
                entries.append((role, value))
        for i, (role_a, text_a) in enumerate(entries):
            for role_b, text_b in entries[i + 1:]:
                if role_a == role_b or text_a == text_b:
                    continue
                score = _jaccard(text_a, text_b)
                if score >= near_duplicate_threshold:
                    report["text_similarity"].append({
                        "round": round_name, "field": "provisional_conclusion",
                        "kind": "near_duplicate_candidate", "roles": sorted((role_a, role_b)),
                        "similarity": round(score, 4), "text_sha256": None,
                    })

    snapshot_tokens = {x.casefold() for x in STAGE_TOKEN.findall(snapshot_text)}
    rows = export.get("independent_assessments")
    rows = rows if isinstance(rows, list) else []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "completed":
            continue
        payload = row.get("assessment")
        if not isinstance(payload, dict):
            continue
        role = str(row.get("agent_id") or "").strip().upper()
        for field in FIELDS["R1"]:
            value = payload.get(field)
            if isinstance(value, str):
                for match in STAGE_TOKEN.finditer(value):
                    token = match.group(0)
                    if token.casefold() not in snapshot_tokens:
                        report["staging_reference_flags"].append({
                            "round": "R1", "agent_id": role, "field": field, "token": token,
                            "reason": ("no_structured_stage_field_available" if not snapshot_text.strip()
                                      else "stage_token_not_found_in_structured_case_snapshot_fields"),
                        })
    report["text_similarity"].sort(key=lambda x: (x["round"], x["field"], x["kind"], tuple(x["roles"]), x["similarity"]))
    report["staging_reference_flags"].sort(key=lambda x: (x["agent_id"], x["field"], x["token"].casefold()))
    report["summary"] = {
        "exact_duplicate_groups": sum(x["kind"] == "exact_duplicate" for x in report["text_similarity"]),
        "near_duplicate_candidate_pairs": sum(x["kind"] == "near_duplicate_candidate" for x in report["text_similarity"]),
        "staging_reference_flags": len(report["staging_reference_flags"]),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.70)
    args = parser.parse_args(argv)
    if not 0.0 <= args.near_duplicate_threshold <= 1.0:
        parser.error("threshold must be between 0 and 1")
    raw = args.input.read_bytes()
    result = build_diagnostics(json.loads(raw), raw, args.near_duplicate_threshold)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
