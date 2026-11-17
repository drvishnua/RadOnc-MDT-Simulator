# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** af88bc45e907480eabed35624b6bc194ed51c8c5  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from audit-v6 model-screen workflow 44011921822, job 133803226696. It is active in the isolated hosted provisioning/sequential inference step. Do not start another inference workflow while concurrency 1 is held. Do not rerun passed standard CI.

## Exact workflow state

| Workflow | Source SHA | Run ID / Job | State | Interpretation |
|---|---|---|---|---|
| Paired v6/audit-v4 screen | d2e85a92fd5c91c002d36c133821dfb5aab9c09f | 44006972494 / 133784577318 | COMPLETED/SUCCESS | Artifact 14296070216. Qwen 12/12 parseable, 0 flags; MedGemma 12/12 parseable, 2 flags plus manual R2/R4 defects. |
| First audit-v5 code/test | c7927bd134a3dfb838bedb75dd69b50dfe197576 | Backend 44010384887 | FAILED | 425/428; false-positive negation matcher and stale mock source IDs; artifact 14296247292. |
| Older audit-v5 paired screen | c7927bd134a3dfb838bedb75dd69b50dfe197576 | 44010377043 | COMPLETED/SUCCESS | Artifact 14295834243. Raw outputs available; flags not accepted due known false positive. |
| Corrected audit-v5 paired screen | e877600c8f860013d45c8f2eb1976b9b81d34484 | 44010717466 / 133798144618 | COMPLETED/SUCCESS | Artifact 14297710993 inspected. Qwen 12/12 parseable, 1 false-positive flag; MedGemma 12/12 parseable, 4 flags including observed R2/R3/R4 defects. Outputs stop normally; no truncation. Not valid audit-v6 evidence. |
| Corrected audit-v6 paired screen | af88bc45e907480eabed35624b6bc194ed51c8c5 | 44011921822 / 133803226696 | IN PROGRESS | HAI-DEF terms gate passed. Combined hosted provisioning/sequential screen active. No final artifact. |
| Standard six-workflow PR CI | af88bc45e907480eabed35624b6bc194ed51c8c5 | 44011927961, 44011928009, 44011928041, 44011927977, 44011928059, 44011928078 | COMPLETED/SUCCESS | Backend 429/429, preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Installer, Security/Dependency/CodeQL passed. |
| Push Installer | af88bc45e907480eabed35624b6bc194ed51c8c5 | 44011921759 | COMPLETED/SUCCESS | Installer passed; optional clean-hosted Ollama/model bootstrap skipped. |

## Verified raw paired screen — 44010717466

- Prompt v6, audit v5; Ollama 0.40.14; GitHub-hosted Windows CPU; concurrency 1; GPU measurement NOT_PERFORMED.
- Corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3.
- Qwen digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma digest sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Qwen 12/12 parseable; audit-v5 recorded 1 flag, which raw review confirmed was a false positive on the correct negation "No shared proposition on a treatment option exists".
- MedGemma 12/12 parseable; audit-v5 recorded 4 flags. Raw review confirms source-position inversion (R2), false shared proposition (R2), omission of exact source quote/rejection (R3), contradictory agreement/no-agreement statements (R4).
- All 24 responses ended done_reason=stop; no token-cap truncation. Both summaries are PENDING_HUMAN_REVIEW, automatic quality score null, clinical accuracy not evaluated.

## Audit-v6 software verification

- Audit version: radonc-mdt-integrity-audit-v6. It requires explicit positive shared-position wording and contains a negative-case regression.
- Backend 44011927961: 429 passed, 0 failed/errors/skipped; preflight 7/7. JUnit artifact 14297420668; preflight artifact 14296618112.
- Frontend 44011928009, Browser E2E 44011927977, Packaging 44011928041, Installer 44011928059, Security/CodeQL 44011928078 and Push Installer 44011921759 passed.
- This verifies code/tests only; model behaviour under audit-v6 remains pending.

## Immediate next operation

1. Poll workflow 44011921822 / job 133803226696 until terminal; preserve the raw artifact.
2. Inspect manifest, Qwen JSONL, MedGemma JSONL and Ollama logs. Verify exact script/corpus hashes, prompt/audit versions, model digests and identical sampler options.
3. Count 12/12 records per model, parseability, done_reason/eval_count, and audit-v6 flags. Inspect every raw response, especially R2-PARTIAL-AGREEMENT-006, R2-CONDITIONALITY-007, R3-FABRICATED-QUOTE-009 and R4-CHAIR-TRACEABILITY-012.
4. Verify the Qwen negated no-shared-proposition response is no longer falsely flagged and the positive MedGemma misattribution remains flagged.
5. Distinguish deterministic audit flags from manual semantic findings; preserve all evidence. Keep human review pending and do not promote MedGemma.
6. Update all seven continuity records after the artifact is actually inspected.

## Cloud/device boundary

GitHub code changes, hosted CI, packaging and hosted CPU screening do not require the user's PC online. RTX 4060 proof separately requires the target Windows PC powered on and real local Ollama inference running. ChatGPT app network is needed only for communication.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval and claim linkage: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
