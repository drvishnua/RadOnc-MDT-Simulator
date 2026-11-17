# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** e877600c8f860013d45c8f2eb1976b9b81d34484  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from the corrected audit-v5 model screen **44010717466**. Do not rerun passed standard CI or restart earlier phases. Do not start another model workflow while concurrency 1 is held.

## Exact workflow state

| Workflow | Source SHA | Run ID / Job | State | Interpretation |
|---|---|---|---|---|
| Completed paired v6/audit-v4 screen | d2e85a92fd5c91c002d36c133821dfb5aab9c09f | 44006972494 / 133784577318 | COMPLETED/SUCCESS | Artifact 14296070216. Qwen 12/12 parseable, 0 flags. MedGemma 12/12 parseable, 2 flags plus additional manual R2/R4 defects. Pending human review; hosted CPU only. |
| First audit-v5 code/test commit | c7927bd134a3dfb838bedb75dd69b50dfe197576 | Backend 44010384887 | FAILED | 425/428, 3 failed; artifact 14296247292. Negative "does not state" was matched as affirmative; mock R2 data did not use exact source IDs. |
| Old audit-v5 paired screen | c7927bd134a3dfb838bedb75dd69b50dfe197576 | 44010377043 | IN PROGRESS | Uses first audit-v5 implementation with flawed negation matcher. Do not accept audit flags from it. It remains in concurrency group ahead of corrected run. |
| Corrected audit-v5 paired screen | e877600c8f860013d45c8f2eb1976b9b81d34484 | 44010717466 | PENDING | Queued in concurrency group after old run 44010377043. Will use negative-aware matcher and exact-source-ID regression fix. |
| Standard six-workflow PR CI | e877600c8f860013d45c8f2eb1976b9b81d34484 | 44010725653, 44010725661, 44010725662, 44010725667, 44010725678, 44010725707 | COMPLETED/SUCCESS | Backend 428/428, preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Installer, Security/Dependency/CodeQL passed. |
| Push Installer | e877600c8f860013d45c8f2eb1976b9b81d34484 | 44010719955 | COMPLETED/SUCCESS | Installer workflow passed. |

## Completed screen details — 44006972494

- Prompt v6, audit v4; Ollama 0.40.14; hosted Windows CPU; concurrency 1; GPU measurement NOT_PERFORMED.
- Qwen model digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma digest sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Both manifests and Ollama logs show identical options: temperature 0, seed 73, num_ctx 4096, top_k 20, top_p 0.95, frequency_penalty 0, presence_penalty 1.5, repeat_last_n 64, repeat_penalty 1.1, num_predict 500.
- Qwen 12/12 parseable, 0 audit flags. MedGemma 12/12 parseable, 2 audit flags: R3 quote-review omission; R4 Chair traceability omission.
- Manual raw-output review also found: R2 partial-agreement roles MO-01/SO-02 were misattributed; R2 single-source missing prerequisite was called a shared proposition; R4 contained a positive claim of agreement followed by a no-agreement conclusion.
- Both models had done_reason=stop on all responses; no 500-token truncations in this one screen. No automatic quality score; both pending independent human review. No clinical accuracy evaluation.

## Exact audit-v5 correction

- Audit-v5 adds deterministic checks for R2 source attribution polarity, single-source/shared prerequisite misattribution and Chair agreement contradiction.
- Initial audit-v5 commit c7927bd failed three tests. Correction e877600 adds a negative-aware attribution matcher and updates a synthetic response fixture with exact R1 source IDs.
- Exact code/test CI: backend 428/428, preflight 7/7; six standard workflows and push installer passed. JUnit artifact 14295864149; preflight artifact 14295604676.

## Immediate next operation

1. Inspect terminal state and artifact for old run 44010377043; preserve it, but do not accept its audit flags.
2. Wait for corrected-head run 44010717466 to start after concurrency is released. Inspect both JSONL outputs and manifest.
3. Verify script/corpus hashes, prompt/audit versions, model digests, sampler parity and 12/12 complete outputs for both models.
4. Confirm audit-v5 flags the observed R2 source inversion, single-source shared-prerequisite claim, R3 exact quote omission and R4 Chair contradiction/traceability, without flagging correct Qwen responses.
5. Inspect every raw response and distinguish deterministic findings from manual reviewer observations. Keep human review pending; do not promote MedGemma.
6. Update all continuity records and the Master Checklist after verified results.

## Cloud/device boundary

GitHub code changes, hosted CI, packaging and hosted CPU model screens do not require the user's PC online. Local RTX 4060 proof is separate and requires the target Windows PC powered on with real local Ollama inference running. The ChatGPT app's network connection is needed only to send/receive chat messages.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval and claim linkage: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
