# RadOnc MDT Simulator — Current Task Checklist
Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 9e781525fbf6ac07cf2f6a19d035b82b888f305a

| Task | Status | Evidence / next action |
|---|---|---|
| R2 structured source ledger | VERIFIED — CODE/TEST | Server-locked exact saved statements and IDs; full source coverage validator. |
| R2 original source order | VERIFIED — CODE/TEST | Required source_order array; exact order validator and negative regression. |
| R2 conditionality/consensus audit | VERIFIED — CODE/TEST | Distinct options, prerequisite retention/status, information sufficiency vs treatment consensus separately tested. |
| R3 identifier and quote schema | VERIFIED — CODE/TEST | Locked source identity/text; separate quote-present/absent and evidence-status fields; deterministic audit. |
| Backend suite | VERIFIED | Run 44031259073; 440 passed, 0 failed/errors/skipped. |
| Frontend | VERIFIED | Run 44031258961 passed. |
| Browser E2E | VERIFIED | Run 44031258943 passed. |
| Packaging prerequisites | VERIFIED | Run 44031258941 passed. |
| Security/dependency/CodeQL | VERIFIED | Run 44031259043 passed. |
| PR and push Windows installer | VERIFIED | Runs 44031258958 and 44031253605 passed. |
| Paired Qwen/MedGemma v9 model screen | IN PROGRESS | Run 44031253593 active; no result artifact yet. Inspect manifest, model digests/options, raw responses, done_reason and deterministic flags. |
| Independent model-output review | NOT STARTED | Review both exact raw outputs after screening. |
| R2/R3 model adherence | IN PROGRESS | Previous audit-v7 screen failed several R2/R3 controls; v9 schema retest pending. |
| Fresh 45-role R1–R4 validation | NOT STARTED | Run only after bounded acceptance gates and review. |
| Missing/failed-agent full-run acceptance | IN PROGRESS | Full 45-role failure injection remains outstanding. |
| RTX 4060 request-time GPU proof | NOT STARTED | Local real Ollama inference with nvidia-smi and Ollama offload/process evidence. |
| Current guideline retrieval and claim linkage | NOT STARTED | Retrieve and verify current authoritative sources. |
| Independent qualified clinical review | NOT STARTED | No signed/attributable review artifact. |
| Release acceptance | BLOCKED | Full-run, clinical, evidence, model and GPU gates remain. |

Historical audit-v7 findings and failed CI runs remain recorded; they are not overwritten by the v9 run. Do not change main, merge, force-push, or alter the screening corpus/sampler without authorization.
# RadOnc MDT Simulator — Task Checklist

Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 90186c26571669fc4ffde166fb593325377d76ee

MASTER_DEVELOPMENT_CHECKLIST.md is authoritative for verification status.

| Task | Status | Completion condition / next action |
|---|---|---|
| Prompt-v8/audit-v7 paired screen | VERIFIED — BOUNDED | Run 44018644704, artifact 14300845455. Qwen 12/12, 5 flags; MedGemma 12/12, 6 flags. R2/R3 failures remain; R4 traceability case passed. |
| Audit-v7 deterministic reviewer | VERIFIED — SOFTWARE | Exact R2 source coverage/order and incompatible-option false-consensus checks pass Backend 437/437. |
| Backend and deterministic preflight | VERIFIED | Run 44020149041: 437/437; preflight report 14300053331. |
| Frontend | VERIFIED | Run 44020148873 passed. |
| Browser E2E | VERIFIED | Run 44020148938 passed. |
| Packaging prerequisites | VERIFIED | Run 44020149274 passed. |
| PR Windows installer | VERIFIED | Run 44020148842 passed. |
| Push Windows installer | VERIFIED | Run 44020142573 passed. |
| Security/dependency/CodeQL | VERIFIED | Run 44020148777 passed. |
| Independent model-output review | NOT STARTED | Both model runs remain PENDING_HUMAN_REVIEW. |
| R2/R3 model adherence | FAILED — MODEL ADHERENCE | Qwen source order/conditionality/inventory/quote rejection failures; MedGemma false consensus, missing rows, conditionality and quote rejection. Needs further prompt/model work. |
| R4 Chair synthesis | IN PROGRESS | Both models passed one no-treatment-proposition Chair case; full role/case coverage still outstanding. |
| Current full 45-role R1–R4 acceptance | NOT STARTED | Fresh complete run and audit required; historical 343 findings preserved. |
| Missing/failed-agent acceptance | IN PROGRESS | Full 45-role failure-injection validation outstanding. |
| RTX 4060 request-time inference proof | NOT STARTED | Target Windows PC powered on during real local Ollama inference and telemetry capture. |
| Guideline retrieval and claim linkage | NOT STARTED | Retrieve and verify current authoritative sources. |
| Independent qualified clinical review | NOT STARTED | Obtain and document review. |
| Release acceptance | BLOCKED | Model, 45-role, GPU, evidence and clinical-review gates outstanding. |

Execution discipline: work only on the development branch; do not modify main, merge, force-push or rebase without permission; do not start competing inference; preserve failures and raw artifacts; CI does not establish clinical accuracy.
