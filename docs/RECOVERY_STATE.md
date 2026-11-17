# RadOnc MDT Simulator — Recovery State

Last checkpoint: 17 November 2026  
Repository: drvishnua/RadOnc-MDT-Simulator  
Development branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: de95004d1c169f3ffa6c52ccf412d84d33055234  
PR #1: open, draft, unmerged, base main.  
Main SHA: 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from audit-v7 paired model screen 44018644704, source 91b7283, and corrected Backend CI 44018911878 on test-only follow-on de95004. Do not start competing inference; concurrency 1.

## Exact workflow state

| Workflow | Source SHA | Run ID | State | Interpretation |
|---|---|---|---|---|
| Prompt-v8/audit-v6 paired model screen | 6fb1712f9644e772c7b25c56bde067f7bfef5ab2 | 44016121962 | COMPLETED/SUCCESS | Artifact 14298999206. Qwen 12/12 with 3 flags; MedGemma 12/12 with 3 flags plus manual false shared-option finding. |
| Audit-v7 code/test commit | 91b72837aff9bcfaccf84a7cb1cfb29d9a3d5a7e | Backend 44018652084 | FAILED | 434/437; stale exact-source fixtures and audit-version assertion; artifact 14300630019. |
| Audit-v7 paired model screen | 91b72837aff9bcfaccf84a7cb1cfb29d9a3d5a7e | 44018644704 | IN PROGRESS | Prompt v8 plus audit v7, hosted Windows CPU; no final artifact. |
| Audit-v7 test-only correction | de95004d1c169f3ffa6c52ccf412d84d33055234 | — | COMMITTED | Safe conditional response now cites exact RO-01/MO-01 source rows; manifest assertion updated. |
| Corrected standard PR CI | de95004d1c169f3ffa6c52ccf412d84d33055234 | Backend 44018911878; Frontend 44018911680; Browser E2E 44018911682; Packaging 44018911677; Installer 44018911757; Security/CodeQL 44018911699 | IN PROGRESS | Packaging prerequisites passed; others running. |
| Push Installer | de95004d1c169f3ffa6c52ccf412d84d33055234 | 44018905591 | IN PROGRESS | Hosted installer run active. |

## Completed prompt-v8/audit-v6 result — 44016121962

- Artifact 14298999206; prompt v8/audit v6; Ollama 0.40.14; hosted Windows CPU, concurrency 1, GPU NOT_PERFORMED.
- Both models: 12/12 parseable, zero failed/malformed, done_reason=stop for all; no token-cap truncations.
- Qwen: 3 flags — conditionality omission, R3 inventory omission, R3 quote rejection omission. Manual review found R2 source order deviated from saved order.
- MedGemma: 3 flags — partial R2 source-ledger/attribution omission, conditionality omission, R3 quote rejection omission. Manual review found false shared treatment in distinct-option case.
- Both R4 Chair traceability responses consistent; one bounded case only.
- Sampler parity confirmed: temperature0 seed73 num_ctx4096 top_k20 top_p0.95 frequency0 presence1.5 repeat_last_n64 repeat_penalty1.1 num_predict500. No model promotion; human review pending.

## Audit-v7

Commit 91b7283 adds deterministic checks for exact R2 row coverage, order and false consensus across distinct conditional options. Initial backend run failed 434/437 due stale safe-response fixtures and audit-version expectation. Test-only correction de95004 fixes them without changing reviewer logic.

## Immediate next actions

1. Verify Backend 44018911878 and retrieve JUnit/preflight artifacts.
2. Poll audit-v7 paired screen 44018644704 and inspect manifest, script/corpus hashes, model digests/options, all 12 outputs/model, done_reason, flags and raw response.
3. Confirm detector catches MedGemma incompatible-option shared label, MedGemma incomplete R2 ledger, Qwen out-of-order rows and exact statement omissions without flagging correct original-order rows.
4. Finish all standard CI and push installer for de95004.
5. Update all continuity files and Master Checklist after artifact and exact-head CI verification.
6. Keep independent review pending; no clinical validation or promotion.

## Other outstanding gates

Historical run-9 integrity failure: 343 findings, original data immutable. Current 45-role acceptance NOT STARTED. Full missing/failed-agent acceptance IN PROGRESS. RTX 4060 proof NOT STARTED. Guideline retrieval NOT STARTED. Independent qualified clinical review NOT STARTED. Release BLOCKED.

Cloud GitHub work does not require the user's PC online; local RTX 4060 validation does.
