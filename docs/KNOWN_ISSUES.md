# RadOnc MDT Simulator — Known Issues

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** af88bc45e907480eabed35624b6bc194ed51c8c5

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Intermediate model-screen run on superseded source | Run 44000326185; artifact 14292068885. MedGemma 9/12 parseable with three outputs truncated at 500 tokens. | Preserve artifact; not current acceptance. |
| KI-002 | FAILED | Corrected-source v6/audit-v4 paired screen | Run 44000583529; artifact 14293084055. Qwen 12/12; MedGemma 9/12; three 500-token truncations. | Preserve raw output; subsequent bounded samples had no truncations. |
| KI-003 | FAILED | Historical 45-role run-9 acceptance | Audit-only revalidation recorded 343 integrity entries (R1 11, R2 41, R3 271, R4 20). | Preserve original records; remediate and run fresh acceptance. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screening/unit tests do not establish full-system behaviour. | Complete controlled full validation after P0 gates and bounded review. |
| KI-005 | NOT STARTED | RTX 4060 request-time inference not proven | Hosted screens are CPU-only. | Target Windows PC must run local Ollama inference while nvidia-smi, ollama ps/offload and latency are captured. |
| KI-006 | NOT STARTED | Guideline retrieval and claim/reference verification | No current checked authoritative guideline set integrated. | Retrieve primary/authoritative sources and verify claim-to-source linkage. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No independent review artifact exists. | Obtain qualified review; maintain educational-only boundary. |
| KI-008 | IN PROGRESS | Development Monitor live public GitHub API dependency | Browser E2E uses fixtures; production browser uses public API subject to network/rate limits. | Verify live operation in user's browser; retain stale/unavailable states. |
| KI-009 | IN PROGRESS | MedGemma repetition/truncation robustness | Earlier runs had three truncations. Runs 44006972494 and 44010717466 each returned 12/12 stop completions under repeat_penalty 1.1. | Continue monitoring; two bounded samples are not a universal fix guarantee. |
| KI-010 | IN PROGRESS | MedGemma hosted pull previously returned HTTP 500 | Run 44004929958 returned HTTP 500 during /api/pull; later run 44006972494 pulled both models successfully. Original 500 root cause remains unknown. | Keep manifest HTTP diagnostics; investigate if reproduced. |
| KI-011 | VERIFIED | Effective paired sampler parity | Run 44006972494 manifests/logs confirm top_k20/top_p0.95/frequency0/presence1.5/repeat_last_n64/repeat_penalty1.1/num_predict500 for both models. | Preserve and reverify settings each run. |
| KI-012 | IN PROGRESS | MedGemma R2/R3/R4 semantic integrity defects | Raw run 44010717466: R2 position attribution inversion; R2 single-source/shared proposition error; R3 exact quote omission; R4 Chair agreement/no-agreement contradiction. | Audit-v6 model run 44011921822 is active; inspect raw outputs and flags. |
| KI-013 | VERIFIED — CODE ONLY | Audit-v5 false-positive negation matcher | Raw Qwen output in run 44010717466 correctly said no shared proposition exists but audit-v5 flagged it. | Superseded by audit-v6; verify with active run. |
| KI-014 | VERIFIED — CODE ONLY | Audit-v6 positive-only shared-position detector | Commit af88bc4 passed Backend 429/429 and all six standard CI workflows; live model test remains pending. | Inspect audit-v6 run 44011921822. |

## Cloud/device boundary

Hosted GitHub development, CI, packaging and CPU model screening do not require the user's PC online. Only actual local RTX 4060 verification requires the target PC powered on with real inference running. ChatGPT app connectivity is separate.
