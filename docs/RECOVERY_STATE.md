# RadOnc MDT Simulator — Recovery State

Last checkpoint: 17 November 2026  
Repository: drvishnua/RadOnc-MDT-Simulator  
Development branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 90186c26571669fc4ffde166fb593325377d76ee  
PR #1: open, draft, unmerged, base main.  
Main SHA: 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from audit-v7 paired model screen 44018644704 (completed, artifact 14300845455) and exact-head CI on 90186c2 (all six standard checks plus push Installer passed). Do not rerun completed CI/model screen unnecessarily.

## Exact workflow state

| Workflow | Source SHA | Run ID | State | Interpretation |
|---|---|---|---|---|
| Prompt-v8/audit-v6 model screen | 6fb1712f9644e772c7b25c56bde067f7bfef5ab2 | 44016121962 | COMPLETED/SUCCESS | Artifact 14298999206; Qwen 12/12, 3 flags; MedGemma 12/12, 3 flags; both R4 traceability outputs passed in one case. |
| Audit-v7 paired model screen | 91b72837aff9bcfaccf84a7cb1cfb29d9a3d5a7e | 44018644704 | COMPLETED/SUCCESS | Artifact 14300845455; Qwen 12/12, 5 flags across 4 cases; MedGemma 12/12, 6 flags across 4 cases. |
| Audit-v7 initial backend CI | 91b72837aff9bcfaccf84a7cb1cfb29d9a3d5a7e | 44018652084 | FAILED | 434/437; stale safe fixtures and audit version assertion. |
| Audit-v7 intermediate backend CI | de95004d1c169f3ffa6c52ccf412d84d33055234 | 44018911878 | FAILED | 435/437; remaining safe partial-agreement fixture and mocked complete run needed exact row text/order. |
| Audit-v7 exact-head CI | 90186c26571669fc4ffde166fb593325377d76ee | Backend 44020149041; Frontend 44020148873; Browser E2E 44020148938; Packaging 44020149274; PR Installer 44020148842; Security/CodeQL 44020148777 | COMPLETED/SUCCESS | Backend 437/437, 0 failed/errors/skipped; preflight artifact 14300053331. |
| Push Installer | 90186c26571669fc4ffde166fb593325377d76ee | 44020142573 | COMPLETED/SUCCESS | Installer passed. |

## Audit-v7 model details — run 44018644704

- Prompt v8, audit v7; script SHA-256 38eb56cef1597d79a361f8c94ffd2a4aca724da3bb0314104a033818e16a3fce; corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3; Ollama 0.40.14; hosted Windows CPU; concurrency 1; GPU NOT_PERFORMED.
- Qwen 12/12 parseable, 0 failed/malformed; flags: R2 partial-agreement source order, R2 conditionality and missing MO-01 row, R3 identifier inventory, R3 quote rejection.
- MedGemma 12/12 parseable, 0 failed/malformed; flags: R2 distinct-option false consensus, partial-agreement source ledger/attribution (two findings), conditionality and missing source rows (two findings), R3 quote rejection.
- Both 12/12 done_reason=stop, no token-cap truncations; matching sampler settings temperature0 seed73 num_ctx4096 top_k20 top_p0.95 frequency0 presence1.5 repeat_last_n64 repeat_penalty1.1 num_predict500.
- Both R4 Chair traceability outputs had zero audit flags and stated no treatment proposition was agreed. One bounded case only.
- Both model summaries remain pending human review; no automatic quality score, no clinical accuracy assessment, no GPU measurement.

## Immediate next actions

1. Arrange independent blinded review of raw outputs from audit-v7 runs 44018644704 and 44016121962.
2. Design prompt/model remediation for R2 row-by-row fidelity and conditionality; prevent a single conditional source from becoming treatment consensus.
3. Make R3 explicitly identify the model-claimed quote as absent from saved source and unsupported/not evidence even after copying exact_text.
4. Run a new bounded paired screen only after prompt/reviewer changes; keep sampler and model digests controlled.
5. Plan fresh full 45-role R1–R4 validation without reusing the failed historical run-9 data.
6. Complete local RTX 4060 request-time proof, authoritative guideline retrieval and independent clinical review.

## Other outstanding gates

Historical run-9 failure: 343 findings, original records immutable. Full current 45-role acceptance NOT STARTED. Full missing/failed-agent acceptance IN PROGRESS. RTX 4060 proof NOT STARTED. Guideline retrieval NOT STARTED. Independent qualified clinical review NOT STARTED. Release BLOCKED.

Cloud GitHub development/CI does not require the user's PC online; local RTX 4060 verification does.
