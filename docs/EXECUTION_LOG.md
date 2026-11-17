# RadOnc MDT Simulator — Execution Log

**Snapshot:** 17 November 2026  
**Branch:** feature/four-round-mdt-and-performance

Append new entries chronologically. Record actual commit SHAs, run IDs and results; do not overwrite failure history.

## 17 November 2026 — Resume after interruption

### Repository recovery and failure diagnosis

- Re-read repository operating contract and current Master Checklist. No PROJECT_STATUS.md, TASK_CHECKLIST.md, DECISIONS.md, EXECUTION_LOG.md, RECOVERY_STATE.md or KNOWN_ISSUES.md existed at the inspected branch head.
- Branch HEAD at resumption: 104821b513e1da0c316df113388ef32adef9334e. PR #1 open/draft/unmerged; main remained 39a356b8eb09399aa2da1b9b9085965999f5105a.
- Backend and browser failures were traced from workflow job steps and downloaded artifacts. The 104821b backend failure was a case mismatch in a test that lowercased the prompt but compared against uppercase EVERY. The browser failure waited on live public GitHub API access rather than deterministic UI state.
- Commit b351a815d013386e271595e2fb54a6f0d571c544 corrected the prompt assertion and injected deterministic GitHub API fixtures into the browser test. Browser E2E passed on that commit; Backend Tests failed because the first R3 status-association regex had doubled escapes.
- Commit 8b7124cf1d0b236100958fd91b8fadc506eee559 corrected the regex to use actual regex boundaries and whitespace tokens. It also carries the regression that a separate malformed reference range must not label a nearby supplied source ID invalid.
- Exact code/test SHA 8b7124c passed all six standard PR workflows: Backend 423/423, deterministic preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Windows Installer, Security/Dependency and both CodeQL analyses all passed. Runs: 44000589051, 44000589233, 44000588823, 44000588917, 44000589004, 44000588973.
- Push Installer 44000583492 passed; optional clean-hosted Ollama/model bootstrap was skipped.
- Documentation-only checklist refresh commit 1d28b0c2f80f355f34f1ff2a3153bc684f3c596f passed all six standard PR workflows: 44001410301, 44001410350, 44001410369, 44001410321, 44001410345, 44001410337.

### Model-screen state

- Commit markers automatically started run 44000326185 on intermediate source SHA b351a81. It remains reported in_progress in the provisioning/inference step, with no artifact published. It is not accepted as evidence for the corrected regex.
- Corrected-source run 44000583529, SHA 8b7124c, remains pending in the same concurrency group (cancel-in-progress is false). It must be allowed to run after the earlier attempt releases the slot.
- HAI-DEF acceptance gate completed successfully before provisioning on run 44000326185. The corrected-head run has not yet reached that gate or inference.
- Fetching the active job log returned a GitHub BlobNotFound/404 response; therefore no log-based claim about the internal provisioning phase is made.

### Current revision

- Code/test SHA: 8b7124cf1d0b236100958fd91b8fadc506eee559.
- Branch/checklist SHA: 1d28b0c2f80f355f34f1ff2a3153bc684f3c596f.
- PR #1 open/draft/unmerged; main unchanged.
- Repository checklist is the single detailed current status record. New continuity docs are supporting references.


## 17 November 2026 — intermediate v6/audit-v4 model-screen forensic result

- Hosted run [44000326185](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44000326185), source SHA `b351a815d013386e271595e2fb54a6f0d571c544`, terminal result **FAILED**. Artifact **14292068885** downloaded and inspected.
- Manifest confirms Qwen digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`, MedGemma digest `sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c`, Ollama 0.40.14, hosted Windows CPU, concurrency 1, and no GPU measurement. Prompt `radonc-mdt-integrity-screen-v6`; audit `radonc-mdt-integrity-audit-v4`; script hash `54f4225cf6279ae5e0bd07af56a364023572e1393cbc95373f564bab284acad3`.
- Qwen: 12/12 response records were parseable; summary status `completed_pending_human_review`, 0 malformed. Its audit flags are not used as acceptance evidence because this source contained the superseded doubled-escape R3 detector.
- MedGemma: 12 response records saved, but 3 were `malformed_or_empty_response`; overall status `incomplete_or_malformed`. Cases: `R2-FALSE-CONSENSUS-005`, `R3-FABRICATED-QUOTE-009`, `R4-CHAIR-TRACEABILITY-012`. Each had Ollama `done_reason=length`, `eval_count=500` and a truncated JSON string after repetitive phrase loops. The other 9 responses were parseable. This is a model output completeness/looping failure, not a missing model download or network provisioning failure.
- Provisioning succeeded: Ollama 0.40.14 installed; both model records/digests captured; both models pulled; Qwen completed 12/12; MedGemma generated 12 records. The workflow failed because three MedGemma responses were malformed/incomplete. Isolated Ollama was stopped in cleanup.
- Corrected-source run [44000583529](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44000583529), source code/test SHA `8b7124cf1d0b236100958fd91b8fadc506eee559`, is now **IN PROGRESS**; job `133768126103` is in the provisioning/sequential-screen step and has no artifact at this checkpoint.
- The persistent documentation bundle and Master Checklist were updated on branch HEAD `80ee6e9854eb6862f69dd06b63cc256c95f40fa2`. All six standard PR workflows passed on that docs-only head; Backend 423/423, run [44002108741](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44002108741), JUnit artifact **14293140853**.


## 17 November 2026 — corrected-source model screen and repetition-control experiment

### Corrected-source paired run 44000583529

- Source code/test SHA: 8b7124cf1d0b236100958fd91b8fadc506eee559. Run 44000583529 completed FAILED; artifact 14293084055 was downloaded and inspected.
- Manifest: Ollama 0.40.14; hosted Windows CPU; concurrency 1; GPU measurement NOT_PERFORMED; prompt v6; audit v4; frozen corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3. Qwen digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma digest sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Qwen: 12/12 response records parseable; 0 deterministic flags; status completed pending human review. MedGemma: 12 records saved, 9/12 parseable, 3 malformed/incomplete; summary incomplete_or_malformed. Cases: R2-FALSE-CONSENSUS-005, R3-FABRICATED-QUOTE-009, R4-CHAIR-TRACEABILITY-012. Each had done_reason=length and eval_count=500 after repeated question/source/synthesis text. No model-quality pass.
- Ollama server log showed repeat_penalty=1.000 (disabled) and repeat_last_n=64. Repetition was the observed cause of output truncation; do not simply raise the output cap.

### Corrective experiment commit c0fbb2a

- Commit c0fbb2ac4a586d5effa51ea8bcc4af623137008f changes backend/scripts/run_medgemma_screening.py and backend/tests/test_medgemma_screening.py only.
- Both models receive identical repeat_last_n=64 and repeat_penalty=1.1; num_predict=500, temperature, seed and context remain unchanged. Regression asserts the identical shared options and fixed output cap.
- Ollama reference consulted: https://docs.ollama.com/modelfile. This is a controlled mitigation test, not proof that repetition is fixed.
- Exact-head PR CI passed: Backend 423/423, preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL all passed. Runs: 44004936087, 44004936006, 44004935981, 44004936065, 44004935939, 44004935954. Backend JUnit artifact 14294230423; Browser E2E artifact 14293343125. All five browser success markers were present.
- Push Installer 44004930010 passed.
- Marker-qualified paired screen 44004929958, job 133777841510, is IN PROGRESS. HAI-DEF terms gate passed; provisioning/sequential inference is active; no final artifact/result is available yet. Hosted CPU only, concurrency 1.


## 17 November 2026 — paired sampler parity and MedGemma pull diagnostics

### Prior repetition-penalty run 44004929958

- Source SHA c0fbb2ac4a586d5effa51ea8bcc4af623137008f; run FAILED; artifact 14294366737 inspected.
- Qwen completed 12/12 parseable responses, 0 deterministic audit flags. Ollama log confirmed repeat_penalty=1.1 was applied to Qwen.
- MedGemma was explicitly requested and HAI-DEF terms attestation was true, but the isolated Ollama POST /api/pull returned HTTP 500 after MedGemma blob download began. No MedGemma inference occurred. The manifest incorrectly retained medgemma_status=NOT_REQUESTED because pull failure status was not persisted before the request. The artifact contained no HTTP response body, so the 500 root cause remains unknown.
- Effective sampler settings from the prior paired logs were not equal despite identical Python options: Qwen used top_k=20, top_p=0.95, presence_penalty=1.5; MedGemma used top_k=40, top_p=0.90, presence_penalty=0.0. Both had repeat_penalty=1.1. This invalidated the fairness of an output-quality comparison under that run.

### Corrective commit d2e85a9

- Commit d2e85a92fd5c91c002d36c133821dfb5aab9c09f changes backend/scripts/run_medgemma_screening.py, backend/tests/test_medgemma_screening.py, .github/workflows/model-integrity-screening.yml and backend/tests/test_medgemma_screening_workflow.py.
- Shared options now pin top_k=20, top_p=0.95, frequency_penalty=0, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1 and num_predict=500 for both models.
- Workflow now persists MedGemma PULL_IN_PROGRESS before the request. On HTTP failure it records URI, status, exception type/message and response body (capped at 8000 chars), sets PULL_FAILED and updates the manifest before raising. Success records PULL_COMPLETED_DIGEST_PENDING before digest capture.
- Regression tests assert sampler parity, fixed output cap and persisted HTTP-pull diagnostics.

### Exact-head verification and current run

- Standard PR runs on d2e85a9: Backend [44006977077](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977077), **424 passed, 0 failed/errors/skipped**; deterministic preflight **7/7**. JUnit artifact 14294297598; preflight artifact 14294467337.
- Frontend [44006977316](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977316), Browser E2E [44006977161](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977161), Packaging Prerequisites [44006977075](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977075), Windows Installer [44006977053](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977053), Security/Dependency/CodeQL [44006977278](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006977278) passed. Browser artifact 14294282765 contains patient registry, Mission Control, role drilldown, Development Monitor and four-round dashboard success markers.
- PR Installer passed; optional model bootstrap was skipped. Push Installer [44006972458](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006972458) passed.
- Marker-qualified paired model screen [44006972494](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44006972494), job 133784577318, is IN PROGRESS. HAI-DEF gate passed. Combined hosted provisioning/sequential-inference step active; no model artifact yet. Hosted Windows CPU only, concurrency 1, GPU measurement not performed.


## 17 November 2026 — paired audit-v4 result, audit-v5 corrections and cloud/device boundary

### Completed paired model screen on d2e85a9

- Run 44006972494 completed SUCCESS on GitHub-hosted Windows CPU; artifact 14296070216.
- Qwen: 12/12 complete and parseable, 0 audit-v4 flags. MedGemma: 12/12 complete and parseable, 2 audit-v4 flags (R3 quote-review omission, R4 unresolved-source traceability omission).
- Raw manual review found additional MedGemma defects: R2 partial-agreement source attribution was reversed (MO-01 was labelled silent; SO-02 was attributed agreement); R2 conditionality promoted a single source's missing-prerequisite statement into a shared proposition; R4 asserted the saved contributions established agreement and later said no proposition was agreed.
- Both JSONL manifests and Ollama logs confirmed common sampler profile: temperature 0, seed 73, num_ctx 4096, top_k 20, top_p 0.95, frequency_penalty 0, presence_penalty 1.5, repeat_last_n 64, repeat_penalty 1.1, num_predict 500. Each model had 12/12 parseable outputs; all done_reason values were stop. One sample did not reproduce the 500-token repetition/truncation. This is not a universal robustness claim or model-quality acceptance.
- The screen manifests remain PENDING_HUMAN_REVIEW, automatic quality score null, clinical accuracy unevaluated, GPU measurement NOT_PERFORMED. No model promotion.

### Audit-v5 implementation and regression correction

- Commit c7927bd introduced audit-v5 checks for R2 exact source attribution, single-source/shared prerequisite misattribution and the Chair positive-agreement/no-agreement contradiction. Initial Backend CI [44010384887](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010384887) FAILED: 425 passed, 3 failed. Artifact **14296247292** showed the checker incorrectly treated "does not state" as affirmative and a synthetic run fixture lacked the exact R1 source IDs required by the new rule.
- Commit e877600 fixed negation handling and updated the mock response to use exact source IDs. Exact-head Backend [44010725653](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725653) passed **428/428**, preflight **7/7**; JUnit artifact **14295864149**, preflight artifact **14295604676**.
- Other exact-head PR workflows passed: Frontend [44010725661](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725661), Browser E2E [44010725667](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725667), Packaging Prerequisites [44010725662](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725662), Windows Installer [44010725707](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725707), Security/Dependency/CodeQL [44010725678](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010725678). Push Installer [44010719955](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010719955) passed.
- The older paired model screen [44010377043](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010377043) is still IN PROGRESS on c7927bd, with the flawed first audit-v5 matcher. Do not accept its audit flags. Corrected-head paired screen [44010717466](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44010717466) is PENDING behind workflow concurrency 1.

### Cloud and device clarification

- GitHub cloud development and hosted model screening do not depend on the user's PC being online. The ChatGPT app's offline banner affects message sending only.
- RTX 4060 request-time inference proof is separate and requires the target Windows PC to be on and running real local Ollama inference during telemetry collection.
