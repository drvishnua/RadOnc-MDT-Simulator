# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** e877600c8f860013d45c8f2eb1976b9b81d34484

The MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification statuses. Keep this operational list aligned with it.

## Current tasks

| Task | Status | Completion condition / next action |
|---|---|---|
| Corrected audit-v5 deterministic regressions | VERIFIED | Commit e877600 corrects negated "does not state" matching and mock source-ID labels. Backend 428/428 passed. |
| Audit-v5 paired Qwen/MedGemma screen | IN PROGRESS | Corrected-head workflow 44010717466 is pending behind active run 44010377043. Inspect raw outputs and manifest after it starts/completes. |
| Older audit-v5 screen using flawed detector | IN PROGRESS | Run 44010377043 on c7927bd remains active. Raw outputs can inform review; its audit flags are not valid current evidence. |
| Completed paired model screen d2e85a9 | VERIFIED | Run 44006972494, artifact 14296070216: Qwen 12/12 parseable, 0 flags; MedGemma 12/12 parseable, 2 flags. Manual review found additional R2/R4 defects. Outputs await independent human review. |
| Repetition mitigation in bounded screen | IN PROGRESS | Run 44006972494 had 12/12 stop completions per model with repeat_penalty 1.1; only one paired sample, so broader robustness not proven. |
| Effective sampler parity | VERIFIED | Both raw manifests and Ollama logs show same top_k/top_p/frequency/presence/repeat settings and num_predict=500. |
| Cloud/device separation | VERIFIED | GitHub Actions and hosted CPU model screening do not require the user's PC online. Local RTX 4060 measurement separately requires the target PC running inference. |
| Standard CI on e877600 | VERIFIED | Backend 428/428, preflight 7/7; frontend, browser E2E, packaging prerequisites, installer, security/CodeQL passed. |
| Push installer on e877600 | VERIFIED | Workflow 44010719955 passed. |
| Current full 45-role four-round acceptance | NOT STARTED | Do not start until bounded model outputs are reviewed and P0 integrity gates are ready. |
| Missing/failed-agent acceptance | IN PROGRESS | Extend/run exact failure-injection coverage; missing responses must remain missing and traceable. |
| RTX 4060 request-time inference proof | NOT STARTED | During real local inference capture ollama ps, nvidia-smi utilisation/VRAM and request-time offload telemetry; target PC must be powered on. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim linkage. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Keep blocked until integrity, paired-model, full-run, evidence, GPU and clinical-review gates pass. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start competing inference while model-screen concurrency 1 is active.
- Preserve all failure records and raw artifacts; do not relabel them as passes.
- Unit tests and CI do not establish clinical accuracy.
