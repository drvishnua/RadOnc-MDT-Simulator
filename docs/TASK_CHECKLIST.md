# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest branch HEAD:** 80ee6e9854eb6862f69dd06b63cc256c95f40fa2  
**Latest verified code/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559

This is the operational next-action list. The detailed status/evidence table in [MASTER_DEVELOPMENT_CHECKLIST.md](MASTER_DEVELOPMENT_CHECKLIST.md) is authoritative; update both consistently whenever a status changes.

## Current tasks

| Task | Status | Completion condition / next action |
|---|---|---|
| Prompt v6 / audit v4 paired model screen | IN PROGRESS | Corrected-source run 44000583529 is now IN PROGRESS after run 44000326185 released concurrency. Inspect manifest and raw JSONL when complete; compare against the intermediate finding of 3 MedGemma outputs truncated at 500 tokens. |
| Intermediate model-screen run | FAILED | Run 44000326185 uses superseded commit b351a81; wait for actual terminal state, preserve its artefacts if produced, and do not use its audit result as current acceptance evidence. |
| R3 source-ID audit regression | VERIFIED | Exact-ID status association and adjacent malformed-range regression pass in backend suite on 8b7124c. |
| Prompt v6 assertion correction | VERIFIED | Case-folded prompt assertion compares case-insensitively; backend suite passes. |
| Development Monitor browser test | VERIFIED | Browser E2E uses deterministic GitHub API fixtures and passed on 8b7124c. |
| Standard backend/frontend/browser CI | VERIFIED | Backend 423/423, deterministic preflight 7/7; frontend, browser E2E, packaging prerequisites, installer, security and CodeQL all passed on 8b7124c. The six documentation-only workflows on 80ee6e9 also passed. |
| MedGemma 500-token repetition/truncation defect | IN PROGRESS | Three intermediate cases hit done_reason=length at eval_count=500 and returned incomplete JSON; verify corrected-source run before prompt/output setting changes. |
| Current full 45-role four-round acceptance | NOT STARTED | Run a fresh validation only after the corrected bounded model screen is reviewed and the current P0 data/provenance gates are ready. Preserve concurrency 1. |
| Missing/failed-agent acceptance | IN PROGRESS | Extend/run exact failure-injection coverage; ensure missing output stays missing and is traced. |
| RTX 4060 request-time inference proof | NOT STARTED | Capture ollama ps, nvidia-smi utilization/VRAM and server offload/request telemetry during real inference; no runner restart or competing request. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim mapping before any compliance statement. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Keep blocked until integrity, live-model, full-run, evidence, GPU and clinical review gates pass. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start a competing inference while a model-screen workflow holds concurrency 1.
- Keep failed/intermediate runs visible; do not recast them as passes.
- Unit tests and CI do not establish clinical accuracy.
