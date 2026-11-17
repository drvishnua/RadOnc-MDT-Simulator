# RadOnc MDT Simulator — Task Checklist

Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: de95004d1c169f3ffa6c52ccf412d84d33055234

MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification status.

| Task | Status | Completion condition / next action |
|---|---|---|
| Prompt-v8 paired screen | VERIFIED — BOUNDED | Run 44016121962, artifact 14298999206. Qwen and MedGemma each 12/12 parseable, 3 audit-v6 flags each. |
| Prompt-v8 R4 Chair consistency | VERIFIED — BOUNDED | Both models produced a consistent no-treatment-proposition outcome in one synthetic R4 case. |
| Prompt-v8 R2/R3 integrity | FAILED — MODEL ADHERENCE | Both omitted explicit conditionality and explicit fabricated-quote rejection; MedGemma omitted source-level R2 positions and falsely labelled distinct options as shared; Qwen reordered R2 rows and omitted some R3 inventory. |
| Audit-v7 deterministic reviewer | IN PROGRESS | Commit 91b7283 adds exact source-ledger, source order and incompatible-option consensus checks. |
| Audit-v7 initial Backend CI | FAILED | Run 44018652084: 434/437. Two safe fixtures lacked exact saved source rows; one assertion expected audit-v6. |
| Audit-v7 corrected Backend CI | IN PROGRESS | Test-only commit de95004; run 44018911878. |
| Audit-v7 paired model screen | IN PROGRESS | Run 44018644704, source 91b7283, active; inspect raw artifact after completion. |
| Standard CI on previous docs head a9b946e | VERIFIED | Backend, Frontend, Browser E2E, Packaging, Installer and Security workflows passed. |
| Repetition mitigation and sampler parity | VERIFIED — BOUNDED | Run 44016121962 had 24/24 stop completions with matching sampler options; no truncations, bounded sample only. |
| Cloud/device separation | VERIFIED | Hosted GitHub work does not require the user's PC online; local RTX 4060 proof separately requires power-on device. |
| Current full 45-role acceptance | NOT STARTED | Bounded 12-case screens do not establish full-system acceptance. |
| Missing/failed-agent full-run acceptance | IN PROGRESS | Full 45-role failure injection outstanding. |
| RTX 4060 request-time proof | NOT STARTED | Real local Ollama inference with nvidia-smi, ollama ps/offload and latency telemetry. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve and verify current authoritative sources. |
| Independent qualified clinical review | NOT STARTED | Obtain and document review. |
| Release acceptance | BLOCKED | Integrity, full-run, GPU, evidence and clinical-review gates remain outstanding. |

Execution discipline: work only on the development branch; do not modify main, merge, force-push or rebase without permission; do not start competing inference; preserve failures and raw artifacts; CI does not establish clinical accuracy.
