# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** a936993f43be349c0843123941e62cf137199ff7

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Early model-screen run on superseded source | Run 44000326185; artifact 14292068885. MedGemma 9/12 parseable with three 500-token truncations. | Preserve artifact. |
| KI-002 | FAILED | Corrected-source v6/audit-v4 paired screen | Run 44000583529; artifact 14293084055. Qwen 12/12; MedGemma 9/12; three 500-token truncations. | Preserve raw output. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 findings (R1 11, R2 41, R3 271, R4 20). | Preserve original records; fresh acceptance needed. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded screens/tests do not prove full-system behaviour. | Run controlled full validation after P0 gates and bounded model review. |
| KI-005 | NOT STARTED | RTX 4060 request-time GPU inference not proven | Hosted screens are CPU-only. | Target Windows PC must run local Ollama inference during telemetry capture. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No current verified guideline corpus integrated. | Retrieve authoritative sources and verify claim linkage. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No independent review artifact exists. | Obtain qualified review; educational-only boundary remains. |
| KI-008 | IN PROGRESS | Development Monitor live public GitHub API dependency | E2E uses fixtures; production browser uses public API subject to rate limits/network. | Verify live browser operation; preserve stale/unavailable state. |
| KI-009 | IN PROGRESS | MedGemma repetition/truncation robustness | Runs 44006972494 and 44010717466 each had 12/12 stop completions under repeat_penalty 1.1; earlier runs had three truncations. | Check v8 sample; limited samples are not universal proof. |
| KI-010 | IN PROGRESS | Prior MedGemma HTTP 500 pull failure | Run 44004929958 pull failed after blob download began; later pull succeeded. Original 500 root cause unknown. | Keep manifest pull diagnostics and investigate if reproduced. |
| KI-011 | VERIFIED | Effective paired sampler parity | Run 44011921822 confirms identical sampler values for Qwen/MedGemma; 24 normal stop completions. | Preserve options and verify every paired run. |
| KI-012 | IN PROGRESS | MedGemma semantic integrity defects in R2/R3/R4 | Audit-v6 run 44011921822: R2 source inversion; R2 shared-position misattribution; R3 exact quote omission; R4 agreement contradiction. | Prompt v8 controlled retest queued. |
| KI-013 | VERIFIED — CODE ONLY | Audit-v6 negation false-positive correction | Backend 429/429 on af88bc4; Qwen valid negated no-shared-proposition response returned 0 flags in run 44011921822. | Keep regression. |
| KI-014 | IN PROGRESS | Prompt-v7 replacement dropped regression-protected wording | Backend run 44015312495 failed 8/432. | Superseded by v8; keep failed run evidence. |
| KI-015 | IN PROGRESS | Prompt-v8 live model validation pending | v8 code/test exists; v8 hosted screen 44016121962 pending behind v7 run 44015305202. Backend 432/432 passed on test-only follow-on a936993. | Inspect v8 paired artifact after concurrency releases. |

## Cloud/device boundary

Hosted GitHub development, CI, Windows packaging and CPU model screening do not require the user's PC online. Only actual local RTX 4060 verification needs the target PC powered on with local inference running.
