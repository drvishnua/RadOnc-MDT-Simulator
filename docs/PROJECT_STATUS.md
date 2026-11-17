# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** d2e85a92fd5c91c002d36c133821dfb5aab9c09f  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

The latest application/test commit pins the effective Qwen sampler profile for both Qwen and MedGemma, in addition to the shared repetition penalty. This is necessary because prior paired runs sent identical request options but Ollama applied model-specific Modelfile defaults: Qwen used top_k=20/top_p=0.95/presence_penalty=1.5 while MedGemma used top_k=40/top_p=0.90/presence_penalty=0.0. The current request explicitly pins top_k=20, top_p=0.95, frequency_penalty=0, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1 and num_predict=500 for both models.

The same commit adds workflow-manifest capture of MedGemma pull HTTP status, URI and response body. This follows workflow 44004929958, where Qwen completed 12/12 with 0 flags, then the MedGemma /api/pull returned HTTP 500; no MedGemma inference took place and the original artifact had no response body.

Exact-head standard PR CI on d2e85a9 is green: Backend 424/424, deterministic preflight 7/7, Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL passed. The marker-triggered paired model screen 44006972494 is IN PROGRESS; its HAI-DEF terms gate passed and the combined hosted provisioning/sequential inference step remains active. No final model artifact is available yet.

## Completed and verified

- R3 exact source-ID regex correction and regression; prompt-v6 case-insensitive assertion correction.
- Browser Development Monitor E2E uses deterministic GitHub API fixtures; production still performs live read-only requests with error handling.
- Shared paired sampler regression pins identical prompts/system/options including top_k=20, top_p=0.95, frequency_penalty=0, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1 and num_predict=500.
- Workflow tests assert MedGemma pull state and HTTP error-body persistence.
- Exact-head CI on d2e85a9: Backend 424/424; preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Installer and Security/CodeQL all passed.
- Push Installer 44006972458 passed. Its optional model bootstrap is separate from the model-screen workflow.

## In progress / outstanding

- Inspect workflow 44006972494 and artifact when complete. Verify effective sampler options for BOTH models, 12 responses/model, parseability, done_reason/eval_count, audit flags and raw response text.
- If MedGemma pull fails again, use the persisted HTTP status/URI/response body. Do not assume the pull failure is a model inference failure.
- Resolve historical run-9 full 45-role audit failure (343 findings) without modifying original saved records.
- Complete fresh 45-role R1–R4 validation and missing/failed-agent acceptance.
- Verify RTX 4060 request-time GPU activity/performance; hosted CPU screens are not GPU evidence.
- Retrieve and verify current authoritative guideline sources and claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains blocked.

## Source of truth

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed status/evidence table. TASK_CHECKLIST.md lists next actions, DECISIONS.md records durable requirements, EXECUTION_LOG.md is chronological, RECOVERY_STATE.md gives the precise resume point, and KNOWN_ISSUES.md lists unresolved defects.
