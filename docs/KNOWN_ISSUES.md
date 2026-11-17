# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** e877600c8f860013d45c8f2eb1976b9b81d34484

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Intermediate model-screen run on superseded source | Run 44000326185; artifact 14292068885. MedGemma 9/12 parseable due three repeated outputs truncated at 500 tokens. R3 detector had superseded regex. | Preserve artifact; not current R3 acceptance. |
| KI-002 | FAILED | Corrected-source v6/audit-v4 paired screen | Run 44000583529; artifact 14293084055. Qwen 12/12; MedGemma 9/12; same three 500-token loop/truncation failures. | Preserve raw outputs; later d2e85a9 paired screen has a completed non-truncated sample. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 integrity entries (R1 11, R2 41, R3 271, R4 20). | Preserve original records; remediate and run fresh acceptance, never retroactively relabel. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screening/unit tests do not demonstrate full-system behaviour. | Complete controlled full validation after bounded review and P0 gates. |
| KI-005 | NOT STARTED | RTX 4060 request-time GPU placement/performance not proven | Hosted screens are CPU-only; model loading/VRAM allocation is not proof of request-time GPU inference. | Target PC must run real inference while nvidia-smi, ollama ps/offload and latency are captured. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No retrieved, current, checked guideline set integrated. | Retrieve authoritative sources and verify claim-to-source linkage. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No independent review artifact exists. | Obtain qualified review; maintain educational-only boundary. |
| KI-008 | IN PROGRESS | Development Monitor depends on live public GitHub API in the product | Browser E2E uses fixtures; production browser fetches public GitHub endpoints subject to network/rate limits. | Validate live operation in user's normal browser; retain stale/unavailable state. |
| KI-009 | IN PROGRESS | MedGemma repetition/truncation robustness | Runs 44000326185 and 44000583529 each had 3 truncations. Run 44006972494 had 12/12 stop completions per model under repeat_penalty 1.1, but this is one bounded sample only. | Confirm on corrected audit-v5 paired screen and broader repeat tests; do not claim universal fix. |
| KI-010 | IN PROGRESS | MedGemma hosted pull previously returned HTTP 500 | Run 44004929958 failed on MedGemma /api/pull after blob download started; artifact 14294366737 had no response body. Later run 44006972494 pulled both models successfully, but original 500 root cause remains unknown. | Retain pull HTTP diagnostics in manifest; investigate only if reproduced. |
| KI-011 | VERIFIED | Effective paired sampler parity | Run 44006972494 manifests and logs show matching sampler values for both models: top_k20, top_p0.95, frequency0, presence1.5, repeat_last_n64, repeat_penalty1.1, num_predict500. | Preserve parity across future comparisons; verify logs/manifests. |
| KI-012 | IN PROGRESS | MedGemma R2/R3/R4 semantic integrity defects | Run 44006972494 manual review: R2 partial-agreement position reversal; R2 prerequisite-status statement miscast as shared proposition; R3 exact quote omission flag; R4 missing-source traceability flag and contradictory positive agreement/no-agreement. Audit-v5 adds targeted checks. | Await corrected audit-v5 model screen 44010717466 and review all raw output. |
| KI-013 | IN PROGRESS | First audit-v5 matcher falsely classified negative "does not state" wording | c7927bd Backend run 44010384887 failed 425/428; checker treated negated 'state' as affirmative and the synthetic fixture lacked exact IDs. Correction e877600 passed 428/428. | Preserve failure; verify the corrected audit-v5 paired run. |

Do not delete or silently downgrade an issue. Resolved issues must remain with resolution commit and verification evidence.

## Cloud/device boundary

Hosted GitHub development, CI, packaging and CPU model screening do not require the user's PC online. Only actual local RTX 4060 validation requires the target PC powered on with local inference running. ChatGPT app connectivity is separate.
