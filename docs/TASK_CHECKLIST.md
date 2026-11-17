# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** a936993f43be349c0843123941e62cf137199ff7

The MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification status.

| Task | Status | Completion condition / next action |
|---|---|---|
| Audit-v6 deterministic reviewer | VERIFIED | Explicit positive shared-position detection and valid-negation regression pass Backend 429/429 on af88bc4. |
| Prompt-v7 initial implementation | FAILED — SUPERSEDED | Commit 4f1d923 Backend 424/432; 8 tests failed because prompt replacement removed established safety phrases and a Chair wording assertion mismatch. Preserve run 44015312495. |
| Prompt-v8 implementation | IN PROGRESS | Commit 6fb1712 contains stronger R2/R3/R4 instructions and restores legacy phrases; only a test assertion mismatch remained. |
| Prompt-v8 corrected tests | VERIFIED | Test-only commit a936993; Backend 432/432, deterministic preflight 7/7. |
| Audit-v6 paired model screen | COMPLETED — BOUNDED | Run 44011921822, artifact 14297362905: Qwen 12/12, 0 flags; MedGemma 12/12, 4 flags on R2/R3/R4 semantic defects. Human review pending. |
| Prompt-v7 hosted model screen | IN PROGRESS — PROVISIONAL | Run 44015305202/source 4f1d923 is active in concurrency-1 group. Do not use as v8 acceptance. |
| Prompt-v8 hosted model screen | PENDING | Run 44016121962/source 6fb1712 is queued behind v7; it tests unchanged v8 model prompt. |
| Repetition mitigation and sampler parity | VERIFIED — BOUNDED | Runs 44011921822 and 44010717466 had complete stop outputs under repeat_penalty 1.1; limited samples only. |
| Backend tests on a936993 | VERIFIED | Backend 432/432, 0 failures/errors/skipped; preflight 7/7. Run 44016402450, JUnit 14299256259, preflight report 14298842437. |
| Frontend on a936993 | VERIFIED | Run 44016402376 passed. |
| Packaging prerequisites on a936993 | VERIFIED | Run 44016402420 passed. |
| Security/Dependency/CodeQL on a936993 | VERIFIED | Run 44016402580 passed. |
| Browser E2E on a936993 | IN PROGRESS | Run 44016402392. |
| PR Windows Installer on a936993 | IN PROGRESS | Run 44016402426. |
| Push Windows Installer on a936993 | IN PROGRESS | Run 44016396209. |
| Current full 45-role four-round acceptance | NOT STARTED | Do not start until bounded outputs and P0 integrity gates are reviewed. |
| Missing/failed-agent acceptance | IN PROGRESS | Full 45-role failure-injection acceptance remains outstanding. |
| RTX 4060 request-time inference proof | NOT STARTED | Target PC powered on with real local inference while nvidia-smi, ollama ps/offload and latency are captured. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim linkage. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Integrity, model, full-run, GPU, evidence and clinical-review gates remain outstanding. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start competing inference while the concurrency-1 screen is active.
- Preserve all failed/intermediate runs and raw artifacts.
- Unit tests and CI do not establish clinical accuracy.
