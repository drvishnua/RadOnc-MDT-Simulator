# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** c0fbb2ac4a586d5effa51ea8bcc4af623137008f  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

The latest code/test commit applies a controlled repetition-mitigation experiment to the paired synthetic Qwen/MedGemma screen. It explicitly sets Ollama repeat_last_n=64 and repeat_penalty=1.1 for both models, while keeping num_predict=500, prompt v6, audit v4 and concurrency 1 unchanged. This responds to two runs in which MedGemma repeated questions or source text until the 500-token cap truncated JSON.

Exact-head standard PR CI on c0fbb2a passed: Backend 423/423, deterministic preflight 7/7, Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL. Run IDs are in the Master Checklist and Execution Log.

The new marker-triggered paired model screen, workflow 44004929958, is IN PROGRESS on this commit. Its result is not yet available. The HAI-DEF terms gate passed before provisioning.

## Completed and verified

- Prompt-v6 assertion correction and R3 exact-source-ID detector correction.
- Browser Development Monitor E2E uses deterministic public GitHub API fixtures; production UI still performs live read-only GitHub requests and retains error handling.
- Exact-head test asserts identical prompts/options for Qwen and MedGemma, repetition penalty 1.1 and unchanged output cap 500.
- Standard CI on c0fbb2a: Backend 423/423, preflight 7/7; frontend, real-browser E2E, packaging prerequisites, installer and security/CodeQL passed.
- Previous corrected-source paired screen 44000583529 and its raw artifact were downloaded and inspected. Qwen returned 12/12 parseable responses; MedGemma returned 9/12 parseable. Three MedGemma cases repeated content until done_reason=length, eval_count=500 and incomplete JSON. This is a failed/incomplete run, not a model-quality pass.

## In progress / outstanding

- Inspect new paired run 44004929958 and its manifest/raw JSONL when uploaded. Confirm recorded generation options, 12/12 output completeness, repetition behaviour, integrity flags and raw text.
- Resolve historical 45-role run-9 audit failure (343 findings) without modifying original saved records.
- Complete fresh 45-role R1–R4 validation and missing/failed-agent acceptance.
- Verify RTX 4060 request-time GPU activity/performance; hosted CPU runs are not GPU evidence.
- Retrieve and verify current authoritative guideline sources and claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains blocked.

## Source of truth

Use MASTER_DEVELOPMENT_CHECKLIST.md for the single authoritative detailed status/evidence table. Use TASK_CHECKLIST.md for next actions, DECISIONS.md for durable decisions, EXECUTION_LOG.md for chronological events, RECOVERY_STATE.md for the exact resume point, and KNOWN_ISSUES.md for unresolved defects.
