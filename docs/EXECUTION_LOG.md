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
