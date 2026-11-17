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

## Controlled model-screen repetition experiment

12. After two paired prompt-v6/audit-v4 screens showed MedGemma repeating phrases/passages until done_reason=length at the unchanged 500-token cap, the next paired experiment explicitly sets Ollama repeat_last_n=64 and repeat_penalty=1.1 for BOTH Qwen and MedGemma. The output cap remains num_predict=500; do not hide loops by blindly raising it. This is a controlled test setting, not evidence that repetition is fixed or that either model is promoted. Inspect both models' raw outputs, options and completion telemetry before deciding whether to retain or revise it. Parameter reference: https://docs.ollama.com/modelfile (Ollama documents repeat_penalty 1.0 as disabled and 1.1 as an example).

## Effective sampler parity and pull-failure diagnostics

13. Paired model comparisons must pin effective sampler parameters, not only send matching Python dictionaries. Model-specific Modelfile defaults may otherwise cause different top_k/top_p/presence_penalty behaviour. The synthetic Qwen/MedGemma screen explicitly pins top_k=20, top_p=0.95, frequency_penalty=0, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1 and num_predict=500 for both. This represents the observed Qwen baseline plus the shared repeat-control experiment; live model output quality remains to be tested.
14. MedGemma provisioning failures are distinct from inference failures. Persist pull state, URI, HTTP status, response body and exception details in the manifest before raising. Do not classify a model as NOT_REQUESTED when the user explicitly requested it and the pull fails.

## Cloud execution and local hardware boundary

15. Repository changes, GitHub Actions CI, Windows hosted builds and the synthetic Ollama model-screen workflow execute on GitHub-hosted cloud runners. Do not require the user's laptop/desktop to remain online for these cloud operations.
16. RTX 4060 request-time GPU verification is a separate local-hardware acceptance task. It requires the target Windows PC to be powered on and a real local Ollama inference request to be running while GPU/process telemetry is collected. Do not confuse this requirement with hosted development or with the ChatGPT app's own network connection.

## Audit-v6 explicit-positive shared-position rule

18. The audit distinguishes an explicit positive claim that a source-specific prerequisite/option is a shared R2 proposition from an explicit negation that no shared treatment proposition exists. Require positive construction wording for the former and retain a regression for the latter. Do not interpret audit-v5 flags as audit-v6 findings; record audit version beside every screening result.

## Cloud execution and local hardware

19. GitHub-hosted code changes, CI, packaging and hosted CPU screens do not require the user's PC online. RTX 4060 request-time proof is a separate local test requiring the target Windows machine powered on and real local inference underway.

## Prompt-v8 copy-first source attribution

20. R2 screening must copy each saved source row verbatim with its exact source ID in original input order. Keep information-sufficiency agreement separate from treatment-option agreement; only classify a shared treatment proposition when at least two source IDs explicitly support the same proposition under compatible prerequisites.
21. R3 quote review must copy the entire exact_text verbatim before classifying the model-claimed quote as present or absent. A paraphrase is not a source quotation.
22. R4 Chair synthesis must select one proposition outcome and ensure the rest of the synthesis is consistent with that outcome. A source statement denying treatment agreement cannot coexist with an unqualified Chair claim that the same contributions establish agreement.
23. These prompt changes do not alter generation sampler settings, output cap or production model selection. Prompt version is separately recorded to keep model outputs comparable and auditable.
