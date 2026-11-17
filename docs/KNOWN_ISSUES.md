# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** c0fbb2ac4a586d5effa51ea8bcc4af623137008f

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Intermediate model-screen run on superseded source | Run 44000326185 failed; artifact 14292068885. Qwen 12/12 parseable; MedGemma 9/12 parseable, 3 repeated outputs truncated at 500 tokens. Its R3 detector used a superseded doubled-escape regex. | Preserve artifact; use only as evidence of output truncation, not as valid R3 audit acceptance. |
| KI-002 | FAILED | Corrected-source prompt-v6 / audit-v4 paired screen | Run 44000583529 failed; artifact 14293084055. Qwen 12/12 parseable; MedGemma 9/12 parseable. Same 3 cases hit done_reason=length at eval_count=500. | Preserve raw outputs; compare against current controlled repetition-mitigation run 44004929958. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 integrity entries (R1 11, R2 41, R3 271, R4 20). | Preserve original records; remediate and run a fresh acceptance, never retroactively relabel. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screening and unit tests do not demonstrate full-system behaviour. | After bounded model review and P0 integrity gates, run controlled full validation with concurrency 1 and inspect all saved outputs. |
| KI-005 | NOT STARTED | RTX 4060 request-time GPU placement/performance not proven | Hosted screens are CPU-only; model loading or allocated VRAM is not proof of request-time GPU inference. | Measure ollama ps, nvidia-smi utilisation/VRAM, offload logs and latency during real inference. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No retrieved, current, checked guideline set is integrated. | Retrieve authoritative sources and verify claim-to-source linkage before any compliance statement. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No independent review artifact exists. | Obtain qualified review; maintain educational-only boundary. |
| KI-008 | IN PROGRESS | Development Monitor depends on live public GitHub API in the product | Browser E2E uses deterministic fixtures; production browser still fetches public GitHub endpoints, which may be rate-limited or unavailable. Error presentation and last-snapshot retention are implemented. | Validate live behaviour in the user's normal browser; retain clear stale/unavailable state. |
| KI-009 | IN PROGRESS | MedGemma repeats questions/source passages until the 500-token output cap | Both runs 44000326185 and 44000583529 produced three malformed MedGemma responses with done_reason=length and eval_count=500. Ollama logs showed repeat_penalty=1.000 (disabled). | Evaluate shared repeat_penalty=1.1/repeat_last_n=64 in run 44004929958; keep num_predict=500. Do not claim fixed until all 12 responses are complete and raw outputs are reviewed. |

Do not delete or silently downgrade an issue. Resolved issues must be retained with their resolution commit and verification evidence.
