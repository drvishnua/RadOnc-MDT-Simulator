# RadOnc MDT Simulator — Task Checklist

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** af88bc45e907480eabed35624b6bc194ed51c8c5

The MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification statuses.

| Task | Status | Completion condition / next action |
|---|---|---|
| Audit-v6 deterministic reviewer | VERIFIED | Commit af88bc4 requires explicit positive shared-position wording and tests the correct negation case. Backend 429/429 passed. |
| Audit-v6 paired Qwen/MedGemma screen | IN PROGRESS | Run 44011921822 is active on af88bc4. Inspect manifest, hashes, paired options, 12 outputs/model and raw text after completion. |
| Audit-v5 screen on e877600 | COMPLETED — SUPERSEDED | Run 44010717466, artifact 14297710993. Qwen 12/12 parseable, 1 false-positive audit-v5 flag; MedGemma 12/12 parseable, 4 flags including observed R2/R3/R4 errors. Do not accept audit-v5 flag counts as audit-v6 findings. |
| Earlier v6/audit-v4 paired model screen | COMPLETED — BOUNDED | Run 44006972494, artifact 14296070216. Qwen 12/12, 0 flags; MedGemma 12/12, 2 flags plus manual R2/R4 defects. |
| Repetition mitigation and sampler parity | VERIFIED — BOUNDED | Run 44006972494 and 44010717466 produced 24/24 and 24/24 stop completions respectively under repeat_penalty 1.1. This is limited sampling, not universal robustness. |
| Standard CI on af88bc4 | VERIFIED | Backend 429/429, preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Installer and Security/CodeQL passed. |
| Push installer on af88bc4 | VERIFIED | Workflow 44011921759 passed; optional model bootstrap skipped. |
| Cloud/device separation | VERIFIED | GitHub Actions and hosted CPU screening do not require the user's PC online. Local RTX 4060 measurement is separate. |
| Current full 45-role four-round acceptance | NOT STARTED | Do not start until bounded model outputs and P0 integrity gates are reviewed. |
| Missing/failed-agent acceptance | IN PROGRESS | Full 45-role failure-injection acceptance remains outstanding. Missing responses must remain missing and traceable. |
| RTX 4060 request-time inference proof | NOT STARTED | Target Windows PC must be powered on with real local Ollama inference while nvidia-smi, ollama ps/offload and latency are captured. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve current authoritative sources and verify title, organisation, date, URL and claim linkage. |
| Independent qualified clinical review | NOT STARTED | Obtain and record independent review; no clinical-quality acceptance before this gate. |
| Release acceptance | BLOCKED | Integrity, paired model, full run, evidence, GPU and clinical review gates remain outstanding. |

## Execution discipline

- Work only on feature/four-round-mdt-and-performance.
- Never modify main, merge, force-push or rebase without explicit permission.
- Do not start competing inference while model-screen concurrency 1 is active.
- Preserve all failure records and raw artifacts; do not relabel them as passes.
- Unit tests and CI do not establish clinical accuracy.
