# RadOnc MDT Simulator — Project Status

Snapshot: 17 November 2026  
Repository: drvishnua/RadOnc-MDT-Simulator  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: de95004d1c169f3ffa6c52ccf412d84d33055234  
PR #1: open, draft, unmerged, targets main.  
Main: 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Cloud/device boundary

GitHub development, hosted CI, Windows packaging and hosted CPU model screening do not require the user's PC online. Only real local RTX 4060 request-time verification requires the Windows PC powered on with local Ollama inference running. ChatGPT app connectivity is separate.

## Latest completed paired model screen — prompt-v8 / audit-v6

- Workflow 44016121962, artifact 14298999206, prompt source 6fb1712; prompt v8, audit v6.
- Qwen: 12/12 parseable; 3 audit flags: R2 conditionality omission, R3 identifier-inventory omission, R3 quote-rejection omission. Manual review found R2 source rows were emitted in a different order from saved order.
- MedGemma: 12/12 parseable; 3 audit flags: R2 partial-agreement source-ledger/attribution omission, R2 conditionality omission, R3 quote-rejection omission. Manual review also found an unsupported shared-treatment label in the two-distinct-options R2 case.
- Both models had 12/12 done_reason=stop; no token-cap truncations. Both used matching model digests and sampler settings: temperature 0, seed 73, num_ctx 4096, top_k 20, top_p 0.95, frequency_penalty 0, presence_penalty 1.5, repeat_last_n 64, repeat_penalty 1.1, num_predict 500.
- Both results remain PENDING_HUMAN_REVIEW; automatic quality score null, clinical accuracy unevaluated and GPU measurement NOT_PERFORMED. Hosted Windows CPU only.
- Positive observation: both produced a consistent no-treatment-proposition R4 outcome in this bounded case. This does not establish general R4 correctness. Both still omitted the explicit R3 statement that the model-claimed quote was absent from the saved source and unsupported.

## Audit-v7 deterministic reviewer and current retest

- Commit 91b7283 added five regressions for exact R2 source statements, original source-row order, and detection of a false shared-treatment claim when sources contain distinct conditional options. Prompt-v8 and the sampler were unchanged.
- Initial Backend run 44018652084 failed 434/437. Failure artifact 14300630019 identified two old safe-response fixtures without exact saved rows and a manifest assertion still expecting audit-v6.
- Test-only correction de95004 updates those fixtures and the manifest assertion; audit logic remains unchanged.
- Corrected Backend run 44018911878 and the other standard CI checks are in progress. Packaging prerequisites passed.
- Audit-v7 paired model screen 44018644704, source 91b7283, is in progress on hosted Windows CPU. No final artifact/result yet.

## Outstanding

Inspect audit-v7 run 44018644704 and verify the new detector. Complete exact-head CI on de95004. Obtain independent human review; neither model is promoted. Resolve historical 45-role run-9 failure (343 findings), complete fresh 45-role R1–R4 and missing/failed-agent acceptance, verify RTX 4060 request-time activity, retrieve current authoritative guidelines and obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim. Release remains BLOCKED.

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed status/evidence table. TASK_CHECKLIST.md lists next actions; DECISIONS.md records durable requirements; EXECUTION_LOG.md is chronological; RECOVERY_STATE.md gives the exact resume point; KNOWN_ISSUES.md lists unresolved defects.
