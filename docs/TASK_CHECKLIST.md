# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** d2e85a92fd5c91c002d36c133821dfb5aab9c09f

The MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification statuses. Keep this operational list aligned with it.

## Current tasks

| Task | Status | Completion condition / next action |
|---|---|---|
| Paired prompt-v6 / audit-v4 model screen | IN PROGRESS | Workflow 44006972494 is active on d2e85a9. Inspect manifest and both raw JSONL files; confirm 12 responses/model, effective sampler profile, done_reason, eval_count, audit flags and repeated text. |
| Effective sampler parity | VERIFIED | Request options now pin top_k=20, top_p=0.95, frequency_penalty=0, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1, num_predict=500 for both models; regression tests pass. Live output comparison remains IN PROGRESS. |
| MedGemma pull HTTP diagnostics | VERIFIED | Workflow now persists PULL_IN_PROGRESS/PULL_FAILED, URI, HTTP status and response body to the manifest on pull failure. Current retry evidence remains pending. |
| Previous repeated-output failure | FAILED | Runs 44000326185 and 44000583529 each had 3 MedGemma responses truncated at 500 tokens after repeated loops. Preserve their artifacts. |
| Previous MedGemma pull failure | FAILED | Run 44004929958: Qwen 12/12 parseable, 0 flags; MedGemma pull returned HTTP 500 after blob download began; no MedGemma generation. Artifact 14294366737 had no error body. |
| R3 exact source-ID audit regression | VERIFIED | Misclassification is bound to exact source ID; separate malformed range cannot taint supplied ID. |
| Prompt-v6 assertion correction | VERIFIED | Case-folded prompt assertion compares case-insensitively. |
| Development Monitor browser test | VERIFIED | Browser E2E uses deterministic GitHub API fixtures; product live-fetch/error handling remains unchanged. |
| Standard CI on d2e85a9 | VERIFIED | Backend 424/424, preflight 7/7; frontend, browser E2E, packaging prerequisites, installer, security/CodeQL passed. |
| Current full 45-role four-round acceptance | NOT STARTED | Do not start until bounded model outputs are reviewed and P0 integrity gates are ready. |
| Missing/failed-agent acceptance | IN PROGRESS | Extend/run exact failure-injection coverage; missing responses must remain missing and traceable. |
| RTX 4060 request-time inference proof | NOT STARTED | During real inference capture ollama ps, nvidia-smi utilisation/VRAM and request-time offload telemetry; no runner restart. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim linkage. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Keep blocked until integrity, paired-model, full-run, evidence, GPU and clinical-review gates pass. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start competing inference while model-screen concurrency 1 is active.
- Preserve all failure records and raw artifacts; do not relabel them as passes.
- Unit tests and CI do not establish clinical accuracy.
