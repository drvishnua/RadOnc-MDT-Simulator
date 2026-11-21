# RadOnc MDT Simulator — Current Task Checklist
Snapshot: 21 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 77a1834

| Task | Status | Evidence / next action |
|---|---|---|
| U01 Mission Control Removal | VERIFIED — CODE/TEST | Dev monitor safely removed; clean UI focused on clinical simulation. |
| U02 Standalone Windows App | VERIFIED — CODE/TEST | Native app-window launcher via Edge app-mode (`Start-RadOnc-MDT.ps1`). |
| U03 Immutable Fact Provenance | VERIFIED — CODE/TEST | SHA-256 case snapshot provenance and DataState schema verified. |
| U04 Intake Screener & Contradictions | VERIFIED — CODE/TEST | Prioritized contradiction detection and v2 clinical fields intake screener. |
| U05-U06 Specialist Reasoning Depth | VERIFIED — CODE/TEST | Anti-generic non-response guard and multi-round conditional pathways validated. |
| U07 Reference Catalogue & Citations | VERIFIED — CODE/TEST | Canonical oncology catalogue, SHA-256 registry, and deterministic citation verification. |
| U08 Anti-Duplication & Role Differentiation | VERIFIED — CODE/TEST | Semantic duplicate detection, ungrounded delegation guards, and R3 adversarial controls. |
| Post-Round Quality Gates Wiring | VERIFIED — CODE/TEST | Non-blocking post-round U05-U08 audit execution and SQLite persistence (`save_round_quality_audit`). |
| Concurrency Lock | VERIFIED — CODE/TEST | File-based mutex lock with timeout and stale-lock recovery on Windows. |
| Backend test suite | VERIFIED — LOCAL | 644 passed, 0 failed, 1 skipped. |
| Deterministic preflight | VERIFIED — LOCAL | 7 passed, 0 failed, 0 inconclusive. |
| R2 structured source ledger | VERIFIED — CODE/TEST | Server-locked exact saved statements and IDs; full source coverage validator. |
| R2 original source order | VERIFIED — CODE/TEST | Required source_order array; exact order validator and negative regression. |
| R2 conditionality/consensus audit | VERIFIED — CODE/TEST | Distinct options, prerequisite retention/status, information sufficiency vs treatment consensus separately tested. |
| R3 identifier and quote schema | VERIFIED — CODE/TEST | Locked source identity/text; separate quote-present/absent and evidence-status fields; deterministic audit. |
| RTX 4060 request-time GPU proof | NOT STARTED | Local real Ollama inference with nvidia-smi and Ollama offload/process evidence. |
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
