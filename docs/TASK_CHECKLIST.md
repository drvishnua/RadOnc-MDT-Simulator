# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** c0fbb2ac4a586d5effa51ea8bcc4af623137008f

The MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification statuses. Keep this operational list aligned with it.

## Current tasks

| Task | Status | Completion condition / next action |
|---|---|---|
| Paired prompt-v6 / audit-v4 model screen with shared repetition mitigation | IN PROGRESS | Workflow 44004929958 is active on c0fbb2a. Inspect both raw JSONL files and manifest; check 12 responses/model, done_reason, eval_count, flags and repeated text. |
| Corrected-source screen 44000583529 | FAILED | Artifact 14293084055 inspected. Qwen 12/12 parseable; MedGemma 9/12 parseable; three MedGemma responses looped to the 500-token cap. Preserve the artifact. |
| MedGemma repetition/truncation defect | IN PROGRESS | Two paired screens reproduced three malformed MedGemma outputs. Test shared Ollama repeat_penalty 1.1/repeat_last_n 64; keep num_predict 500. |
| Shared model options regression | VERIFIED | Backend test pins identical Qwen/MedGemma prompt/system/options, repeat_penalty 1.1, repeat_last_n 64 and num_predict 500. |
| R3 exact source-ID audit regression | VERIFIED | Status association is bound to the exact source ID; a separate malformed range cannot taint a nearby supplied source ID. |
| Prompt-v6 assertion correction | VERIFIED | Case-folded prompt assertion compares case-insensitively. |
| Development Monitor browser test | VERIFIED | E2E uses deterministic GitHub API fixtures; production live-fetch/error behaviour remains unchanged. |
| Standard backend/frontend/browser CI | VERIFIED | Exact code/test SHA c0fbb2a: Backend 423/423, preflight 7/7; frontend, browser E2E, packaging prerequisites, installer and security/CodeQL passed. |
| Current full 45-role four-round acceptance | NOT STARTED | Do not start until bounded model outputs are reviewed and P0 integrity gates are ready. |
| Missing/failed-agent acceptance | IN PROGRESS | Extend/run exact failure-injection coverage; missing responses must remain missing and traceable. |
| RTX 4060 request-time inference proof | NOT STARTED | During real inference capture ollama ps, nvidia-smi utilisation/VRAM and request-time offload telemetry; no runner restart or competing request. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim linkage. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Keep blocked until integrity, paired-model, full-run, evidence, GPU and clinical-review gates pass. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start a competing inference while a model-screen workflow holds concurrency 1.
- Keep failed/intermediate runs and raw artifacts visible; do not relabel them as passes.
- Unit tests and CI do not establish clinical accuracy.
