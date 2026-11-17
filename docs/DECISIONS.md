# RadOnc MDT Simulator — Decisions and Invariants

**Last updated:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance

This file records durable product and engineering decisions. The [MASTER_DEVELOPMENT_CHECKLIST.md](MASTER_DEVELOPMENT_CHECKLIST.md) remains authoritative for verification status.

## Product and clinical-safety decisions

1. The application is a synthetic educational MDT simulator, not clinical decision support or a treatment authority.
2. Unknown or undocumented data must remain unknown. Missing is not normal, negative, absent, N0, M0, ECOG 0, resectable or ineligible.
3. Never fabricate patient facts, stage, pathology, imaging, investigations, comorbidities or preferences. Preserve raw data and flag contradictions rather than silently resolving them.
4. Distinguish source facts, interpretations, assumptions, unknowns and conditional recommendations.
5. A definitive MDT conclusion is not permitted when critical information is insufficient. Preserve dissent and uncertainty.
6. Consensus requires agreement on the same substantive proposition. Conditional support is not unconditional support; insufficient information is not opposition.
7. The Chair must synthesise actual saved R1–R3 contributions, preserve prerequisites, dissent and unresolved issues, and trace conclusions to source records.
8. Deterministic code owns counts, validation, provenance and report structure; the LLM may interpret but must not control factual integrity.
9. No zero-hallucination, guideline-compliance, clinical-validity or model-promotion claim without the required evidence and independent review.

## Four-round architecture

- R1: independent specialist assessments.
- R2: structured specialist debate, with role-specific agreement, disagreement and position-change reasons.
- R3: adversarial audit of assumptions, evidence, missing information, feasibility, risk and governance.
- R4: Chair synthesis of actual saved R1–R3 contributions; never invent missing responses.

Keep round inputs/history distinct and preserve original case snapshots, hashes, run IDs, timestamps and audit trails.

## Engineering and execution decisions

1. Repository: drvishnua/RadOnc-MDT-Simulator. Development branch: feature/four-round-mdt-and-performance. PR #1 remains draft and unmerged; main is protected from this work.
2. Prefer minimal reversible patches and regression tests. Preserve unrelated work.
3. Keep agent/model concurrency at 1 unless repeatable same-workload tests demonstrate a safe improvement.
4. Model screens are synthetic, CPU-hosted and sequential by default. A hosted CPU screen cannot establish RTX 4060 performance.
5. MedGemma is an evaluation candidate, not a promoted production replacement. Compare it against Qwen using identical inputs, preserved raw outputs and deterministic audit rules; require human review.
6. The commit-marker workflow is the normal automatic trigger for the bounded model screen. HAI-DEF acceptance gates must remain explicit and must pass before provisioning.
7. Never restart or kill the user's local Ollama/model runner, change model/context/GPU settings, or interrupt a live simulation without explicit authorisation.
8. Mission Control and Development Monitor are read-only oversight surfaces. They must not initiate agent dispatch, retries or model inference.
9. CI/build/installer completion, live model inference, GPU verification and clinical validation are separate milestones.

## Change control

No merge, release, deployment, force-push or main-branch modification without explicit permission. Preserve all historical failures and immutable run records.


## Model-screen output integrity

10. A model response whose generation ends with `done_reason=length` and lacks a complete, parseable output envelope is an incomplete/failed response, never a valid contribution. Preserve raw output and telemetry for audit.
11. Qwen and MedGemma comparative screens must use identical prompts and generation options for a paired comparison. Do not raise output limits blindly to hide repetition; inspect token-cap and repetition evidence, make a controlled change, and rerun the same frozen cases.
