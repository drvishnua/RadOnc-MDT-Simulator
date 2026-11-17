# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** af88bc45e907480eabed35624b6bc194ed51c8c5  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

GitHub development, hosted CI, Windows packaging and hosted CPU model screening do not require the user's PC online. Only real local RTX 4060 request-time verification requires the target Windows PC powered on and running local Ollama inference. ChatGPT app connectivity is separate.

## Latest code and software verification

Commit af88bc4 advances the deterministic screening reviewer to audit-v6. It narrows the shared-R2-proposition detector to require explicit positive wording and adds a regression for the correct negated statement "No shared proposition on a treatment option exists." Audit-v5 code and its false-positive history are retained.

Exact-head PR CI on af88bc4 passed: Backend **429/429**, deterministic preflight **7/7**, Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL. Push Installer passed. PR #1 remains draft/unmerged; main is unchanged.

## Latest paired model evidence

**Run 44006972494** (d2e85a9, artifact 14296070216), prompt v6/audit v4:
- Qwen 12/12 parseable; 0 audit-v4 flags.
- MedGemma 12/12 parseable; 2 audit-v4 flags and additional manual R2/R4 semantic defects.
- Both models used identical effective sampler settings; all 24 responses ended with done_reason=stop. This was one bounded hosted CPU sample, not a universal repetition fix or model-quality acceptance.

**Run 44010717466** (e877600, artifact 14297710993), prompt v6/audit v5:
- Qwen 12/12 parseable; 1 audit-v5 flag. Raw response inspection shows the valid negated "No shared proposition on a treatment option exists" wording was falsely flagged by the broad audit-v5 matcher.
- MedGemma 12/12 parseable; 4 audit-v5 flags: R2 source attribution inversion, R2 single-source/shared-prerequisite misattribution, R3 quote-review omission and R4 Chair agreement/no-agreement contradiction.
- Both models had 12/12 done_reason=stop outputs; no token-cap truncation in this run.
- This run's output is retained as raw evidence, but its audit-v5 flag counts are superseded and must not be reported as audit-v6 findings.

## Current audit-v6 model run

Corrected audit-v6 run **44011921822** is IN PROGRESS on source af88bc4, hosted Windows CPU, concurrency 1. HAI-DEF terms gate passed. The combined provisioning/sequential screening step is active; no final artifact/result is available yet. Its purpose is to re-evaluate the same paired models under audit-v6, including both positive misattribution and correct-negation regression behaviour.

## Outstanding

- Inspect run 44011921822 manifest, JSONL files and logs after completion. Verify exact hashes, model digests, sampler parity, 12/12 outputs/model, completion reasons and all raw responses.
- Obtain independent human review of both model outputs; MedGemma is not promoted.
- Resolve historical 45-role run-9 audit failure (343 findings) without modifying original saved records.
- Complete a fresh 45-role R1–R4 validation and missing/failed-agent acceptance.
- Verify RTX 4060 request-time GPU activity locally; hosted CPU screens are not GPU evidence.
- Retrieve and verify current authoritative guideline sources and claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains BLOCKED.

## Source of truth

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed status/evidence table. TASK_CHECKLIST.md lists next actions, DECISIONS.md records durable requirements, EXECUTION_LOG.md is chronological, RECOVERY_STATE.md gives the exact resume point, and KNOWN_ISSUES.md lists unresolved defects.
