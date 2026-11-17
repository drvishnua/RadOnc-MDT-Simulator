# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest branch HEAD:** 80ee6e9854eb6862f69dd06b63cc256c95f40fa2  
**Latest verified code/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Intermediate model-screen run on superseded source | Run 44000326185 failed; artifact 14292068885. Qwen 12/12 parseable; MedGemma 9/12 parseable, 3 truncated at 500 tokens after repetitive loops. Its R3 audit used the superseded regex. | Preserve raw artifact; do not accept its audit result. Use it as evidence of output-truncation behaviour only. |
| KI-002 | IN PROGRESS | Corrected v6 / audit-v4 paired model screen | Run 44000583529 is active on SHA 8b7124c in the provisioning/sequential-screen job; no artifact yet. | Inspect terminal state and raw artifacts before making a model-quality decision. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 integrity entries (R1 11, R2 41, R3 271, R4 20). | Preserve original records; investigate/remediate and run a fresh acceptance, not a retrospective relabel. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | The bounded 12-case prompt screen and unit tests do not demonstrate whole-system behaviour. | After bounded output review and P0 gate work, run controlled full validation with concurrency 1 and inspect all saved outputs. |
| KI-005 | NOT STARTED | RTX 4060 request-time GPU placement/performance not proven | Hosted screening is explicitly CPU-only; model loading/VRAM allocation is insufficient proof. | Measure nvidia-smi, Ollama placement/offload, request-time GPU activity and latency during real inference. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No retrieved, current and checked guideline set is integrated. | Retrieve authoritative sources and verify claim-to-source linkage before claiming evidence compliance. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No review artifact exists. | Obtain qualified review; maintain educational-only boundary. |
| KI-008 | IN PROGRESS | Development Monitor depends on live public GitHub API in the product | Browser E2E now uses fixtures so it is deterministic; production browser still fetches public GitHub endpoints, which can be rate-limited or unavailable. Error presentation and last-snapshot retention are implemented. | Validate live operation in the user's normal browser; retain clear stale/unavailable state. |

Do not delete or silently downgrade an issue. Resolved issues should be retained with their resolution commit and verification evidence.

| KI-009 | IN PROGRESS | MedGemma repeats clauses until the 500-token output cap | Intermediate v6/audit-v4 run 44000326185 produced 3 malformed JSON responses with done_reason=length and eval_count=500 (R2 false-consensus, R3 fabricated-quote, R4 Chair-traceability). | Check corrected-source run 44000583529; if reproduced, add a constrained anti-repetition/concise response instruction and a regression, then rerun identical frozen cases. Do not simply raise the cap without evidence. |
