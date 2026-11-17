# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** a936993f43be349c0843123941e62cf137199ff7  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from prompt-v8 hosted model-screen workflow **44016121962** after the older prompt-v7 workflow **44015305202** releases the concurrency-1 group. Do not start competing inference. The code/test fix on a936993 changes one assertion only; the prompt-v8 script remains the same as the 6fb1712 screen source.

## Exact workflow state

| Workflow | Source SHA | Run ID | State | Interpretation |
|---|---|---|---|---|
| Completed audit-v6/prompt-v6 screen | af88bc45e907480eabed35624b6bc194ed51c8c5 | 44011921822 | COMPLETED/SUCCESS | Artifact 14297362905. Qwen 12/12, 0 flags; MedGemma 12/12, 4 semantic flags (R2 x2, R3, R4). Both summaries pending human review. |
| Prompt-v7 code/test CI | 4f1d923c0c2b6a5b51df926993018bed1d84a349 | Backend 44015312495 | FAILED | 424/432, 8 failed due removed prior prompt assertions and phrase mismatch. |
| Prompt-v7 hosted model screen | 4f1d923c0c2b6a5b51df926993018bed1d84a349 | 44015305202 | IN PROGRESS | Provisional v7 output only; no artifact/result yet. |
| Prompt-v8 initial CI | 6fb1712f9644e772c7b25c56bde067f7bfef5ab2 | Backend 44016130343 | FAILED | 431/432; one Chair assertion hyphenation mismatch. Other PR checks and installer passed. |
| Prompt-v8 final test-only fix | a936993f43be349c0843123941e62cf137199ff7 | Backend 44016402450 | COMPLETED/SUCCESS | 432/432; preflight 7/7. This commit changes only one test assertion, not the screening script or prompt. |
| Prompt-v8 hosted model screen | 6fb1712f9644e772c7b25c56bde067f7bfef5ab2 | 44016121962 | PENDING | Queued behind v7 run 44015305202 in concurrency-1 group. |
| Latest PR standard CI | a936993f43be349c0843123941e62cf137199ff7 | Backend 44016402450; Frontend 44016402376; Packaging 44016402420; Browser E2E 44016402392; Windows Installer 44016402426; Security/CodeQL 44016402580 | PARTIAL | Backend 432/432, Frontend, Packaging and Security passed; Browser E2E and Installer remain active. |
| Push Installer | a936993f43be349c0843123941e62cf137199ff7 | 44016396209 | IN PROGRESS | Hosted installer workflow active. |

## Completed audit-v6/prompt-v6 model result — 44011921822

- Artifact 14297362905, Ollama 0.40.14, hosted Windows CPU, concurrency 1, GPU NOT_PERFORMED.
- Qwen 12/12 parseable, 0 deterministic flags. MedGemma 12/12 parseable, 4 flags on R2 source inversion, R2 shared conditional proposition, R3 source quote omission and R4 Chair contradiction.
- All 24 outputs had done_reason=stop; no truncations. Matching options: temperature 0, seed 73, num_ctx4096, top_k20, top_p0.95, frequency0, presence1.5, repeat_last_n64, repeat_penalty1.1, num_predict500.
- No automatic quality score; clinical accuracy not evaluated; both outputs pending independent human review.

## Prompt-v8 content

Prompt v8 retains copy-first R2 attribution and separately names information-sufficiency versus treatment-option propositions; requires exact source quotation in R3; and requires one mutually consistent Chair proposition outcome in R4. It keeps previously tested safety phrases. Generation sampler and 500-token cap are unchanged.

## Immediate next operation

1. Poll v7 model run 44015305202 and preserve its artifact as v7 history only.
2. When v7 releases concurrency, inspect prompt-v8 run 44016121962 artifact and manifest.
3. Verify exact prompt/audit versions, script/corpus hashes, model digests and equal sampler options.
4. Count 12 complete responses/model; check done_reason/eval_count and all audit-v6 flags.
5. Inspect all raw outputs, especially R2-PARTIAL-AGREEMENT-006, R2-CONDITIONALITY-007, R3-FABRICATED-QUOTE-009 and R4-CHAIR-TRACEABILITY-012. Confirm Qwen safe-negation remains unflagged; determine whether MedGemma defects improve.
6. Finish a936993 Browser E2E, PR installer and push installer CI; update records after terminal results.
7. Keep human review pending; do not promote MedGemma.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Guideline retrieval and claim linkage: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
