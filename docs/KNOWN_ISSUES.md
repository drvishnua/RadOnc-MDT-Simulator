# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** d2e85a92fd5c91c002d36c133821dfb5aab9c09f

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Intermediate model-screen run on superseded source | Run 44000326185; artifact 14292068885. Qwen 12/12 parseable; MedGemma 9/12 parseable, 3 repeated outputs truncated at 500 tokens. R3 detector had superseded regex. | Preserve artifact; use only as truncation evidence, not valid R3 acceptance. |
| KI-002 | FAILED | Corrected-source prompt-v6 / audit-v4 paired screen | Run 44000583529; artifact 14293084055. Qwen 12/12 parseable; MedGemma 9/12, same 3 cases truncated at 500 tokens. | Preserve artifact; compare with effective-sampler-parity run 44006972494. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 integrity entries (R1 11, R2 41, R3 271, R4 20). | Preserve original records; remediate and run fresh acceptance, never retroactively relabel. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screening and unit tests do not demonstrate full-system behaviour. | After bounded model review and P0 integrity gates, run controlled full validation with concurrency 1. |
| KI-005 | NOT STARTED | RTX 4060 request-time GPU placement/performance not proven | Hosted screens are CPU-only; model loading/VRAM allocation is not proof of request-time GPU inference. | Measure ollama ps, nvidia-smi, offload logs and latency during real inference. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No retrieved, current, checked guideline set integrated. | Retrieve authoritative sources and verify claim-to-source linkage. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No independent review artifact exists. | Obtain qualified review; maintain educational-only boundary. |
| KI-008 | IN PROGRESS | Development Monitor depends on live public GitHub API in product | Browser E2E uses fixtures; production browser still fetches public GitHub endpoints, subject to rate limits/network. | Validate live operation in user's normal browser; retain stale/unavailable state. |
| KI-009 | IN PROGRESS | MedGemma repeats questions/source passages until 500-token cap | Runs 44000326185 and 44000583529 produced 3 malformed MedGemma outputs with done_reason=length/eval_count=500. | New run 44006972494 applies shared repetition penalty and pins same effective sampler; inspect raw outputs before claiming fixed. |
| KI-010 | IN PROGRESS | MedGemma model pull returns HTTP 500 on hosted screen | Run 44004929958 completed Qwen but MedGemma /api/pull returned HTTP 500 after blob download began. Artifact 14294366737 has no response body; root cause unknown. | d2e85a9 adds manifest capture of pull status/URI/body. Inspect run 44006972494; if it fails, use its saved HTTP diagnostics before retry. |
| KI-011 | IN PROGRESS | Paired effective sampler settings were previously not equal | Run 44000583529 logs show model Modelfile defaults differed despite identical request payloads: Qwen top_k20/top_p0.95/presence1.5; MedGemma top_k40/top_p0.90/presence0.0. | d2e85a9 explicitly pins common sampler parameters; verify both run manifests/logs. |

Do not delete or silently downgrade an issue. Resolved issues must remain with resolution commit and verification evidence.
