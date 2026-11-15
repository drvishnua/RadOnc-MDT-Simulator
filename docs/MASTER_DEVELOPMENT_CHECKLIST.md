# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Latest fully verified code/test commit:** `80abe9e22b957ee93071064c1b99614689be3bf8` (all six exact-head workflows passed; production-code detector fix is `92dbb559ed1a0f781ec838f6e30acb42cf405f98`).
**Latest branch head:** `2af68fc8d4ef53ac3cb094337fed8007f83b23d4` (checklist-only commit; all six standard CI workflows passed: runs 43699036280, 43699036296, 43699036337, 43699036336, 43699036274, 43699036288).

Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| Four-round R1–R4 architecture/data flow | IN PROGRESS | Implemented with regression coverage; full current-head 45-role live acceptance outstanding. |
| R1 independent assessment | IN PROGRESS | Implemented; complete current-head production-scale output audit outstanding. |
| R2 debate and peer sourcing | IN PROGRESS | Source allowlists/provenance checks exist; current full-run provenance review outstanding. |
| R3 adversarial review | IN PROGRESS | Source-bound checks and positive/negative control tooling exist; full 45-role test outstanding; bounded artifact from run 43559331144 showed malformed model output ('Both and explicitly state...'). Input neutralisation was grammatical. Commit `92dbb55` adds a non-rewriting audit flag and failure/grammatical negative-control tests. The `970c899` Chair regression confirms the flag is retained in `case_data_integrity_flags` and attributed to fixture role RO-03. The `263d13a` generation-level regression injects the malformed sentence into mocked R3 model output and confirms `generate_adversarial_contribution` returns the integrity flag. Backend CI passed; this verifies the generation/save payload boundary in a mocked run, not a real 45-role inference. Full live validation remains outstanding. Full 45-role validation remains outstanding. |
| R4 Chair synthesis | IN PROGRESS | Saved-contribution reconciliation, deterministic reporting and the malformed R3 source-flag handoff to Chair integrity findings have regression coverage; full live 45-role Chair audit remains outstanding. |
| Clinical safety/unsupported claims | IN PROGRESS | Deterministic audits and TNM regression coverage exist; not exhaustive clinical validation. |
| TNM connector CodeQL remediation | IN PROGRESS | `case_integrity.py` now uses direct string comparison; the new whitespace/case regression passed in the 303-test suite. Python and JavaScript CodeQL jobs passed on `965d6ba`; the PR thread is no longer unresolved. The separate alert record could not be queried, so formal alert closure is not claimed. |
| Unknowns, staging and contradictions | IN PROGRESS | Not-reported semantics and discrepancy warnings exist; semantic coverage and human review remain required. |
| Conditional recommendations/prerequisites | IN PROGRESS | Deterministic checks exist; full live-output audit outstanding. |
| Distinct-role Chair counting | VERIFIED | Regression coverage and exact-baseline backend CI passed; complete live consensus validation still outstanding. |
| Proposition consensus, dissent and position history | IN PROGRESS | Deterministic reconciliation/tests exist; full current-head report audit outstanding. |
| Case hashes, run IDs, timestamps and audit history | IN PROGRESS | Mechanisms exist; complete current-head reproducibility audit outstanding. |
| Provenance and source attribution | IN PROGRESS | Round/source validation exists; malformed paired-reference R3 prose is flagged without rewriting raw output. Evidence retrieval and independent source verification are not implemented. |
| Missing/failed agent handling | IN PROGRESS | Validation mechanisms exist; current-head incomplete-case/failure-injection acceptance outstanding. |
| Live-validation source-integrity quality gate | IN PROGRESS | The validator maps both case-data and source-reference flags to failed quality-gate items. The no-inference regression for the exact malformed R3 paired-source flag passed in the 307-test backend suite on `80abe9e`; the test confirms the saved flag becomes an R3 failed quality-gate item without rewriting source text. |
| Backend tests | VERIFIED | `80abe9e`, [run 43698410262](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410262): 307 passed, 0 failed/errors/skipped; preflight 6 passed, 0 failed/inconclusive. Includes malformed-prose detection, R3 generation, Chair handoff, live quality-gate and actual R3 `num_ctx=8192` request-payload regressions. Failure history retained: `685761a` failed due an over-escaped regex, fixed in `92dbb55`; `39140b4` had a wrong fixture role expectation, corrected in `970c899`. |
| Frontend build | VERIFIED | [Run 43698410277](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410277): success on `80abe9e`. |
| Browser registry/dashboard E2E | VERIFIED | [Run 43698410259](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410259): success on `80abe9e`. |
| Packaging prerequisites | VERIFIED | [Run 43698410249](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410249): success on `80abe9e`. |
| Windows installer build/smoke test | VERIFIED | [Run 43698410319](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410319): build, install/smoke test, checksum and artifact upload passed on `80abe9e`; optional clean-host first-run Ollama/model bootstrap skipped. |
| Dependency/security workflows | VERIFIED (analysis execution); alert closure pending | [Run 43698410290](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698410290): dependency audit, secret scan and Python/JS CodeQL jobs passed on `80abe9e`. No unresolved PR review threads; direct code-scanning alert record was inaccessible, so formal TNM alert closure is not claimed. |
| Frontend flicker/blank screens/stale state | IN PROGRESS | Browser E2E passes; dedicated reproduction and console/network/lifecycle investigation outstanding. |
| Dashboard/API integration | IN PROGRESS | Baseline browser E2E passed; current-head acceptance outstanding. |
| Ollama context allocation | VERIFIED (isolated probe only) | Hosted Windows probe observed requested/actual 6,144 and 8,192. Not proof of effective context in a full MDT run. |
| R3 Ollama request-context propagation | IN PROGRESS | `_context_window_for_schema` maps the main adversarial draft to 8,192; the `80abe9e` no-inference test captures the actual `/api/generate` request and confirms `options.num_ctx=8192`. Live per-stage runtime allocation/truncation evidence remains outstanding. |
| Effective R3 context/truncation | IN PROGRESS | A historical pre-R2 and post-R4 process snapshot showed `context_length=4096`; those snapshots do not identify the context used inside the R3 call. Schema mapping and request-payload regression verify R3 asks for 8,192, while R2/R3 repair schemas ask for 6,144. Stage-specific live runtime allocation and truncation verification remain outstanding. |
| RTX 4060 active inference | IN PROGRESS | Historical laptop GPU measurements exist; current-head request-time GPU/offload verification outstanding. |
| Full live 45-role MDT | BLOCKED | Workflow run [43698959463](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698959463) remains API-status `in_progress` on commit `2807b0c3d50b68722017fea987b9cdab8bfa283d`: 45 roles, R1-R4/Chair, isolated hosted Windows CPU, concurrency 1, synthetic case, expected 136 saved contributions and JSON/SQLite/manifest artefacts. Last observed active step: portable Ollama/model provisioning; GitHub run metadata has not updated since `2026-11-15T09:22:42Z` (checked `12:10Z`), job-log download returned `BlobNotFound`, and no artifacts are present. Mark as BLOCKED pending observable progress/completion; not a confirmed failure. Workflow provisioning step cap is 240 minutes, job cap 250 minutes. No GPU evidence is claimed. |
| Live artefacts/reproducibility | IN PROGRESS | Workflow 43698959463 has no published artifacts while its provisioning step remains active; job metadata is stale and log archive is unavailable. Artefact inspection and 45-role/136-row reconciliation cannot begin until run completion. |
| Evidence retrieval/guideline verification | NOT STARTED | Retrieval is not connected; no guideline concordance is claimed. |
| Independent clinical review | NOT STARTED | Qualified clinical review/acceptance not performed. |
| Windows release/security acceptance | IN PROGRESS | Installer and security workflows passed on `80abe9e`; direct TNM alert-state confirmation, hosted full live validation and release gates remain. |
| Authoritative repository checklist | VERIFIED | This file is the single master checklist; `IMPLEMENTATION_STATUS.md` points here for current status. |

## Immediate priorities

1. Obtain direct confirmation that CodeQL alert 4 is formally closed; review all subsequent security findings.
2. Verify the live-validator quality-gate regression for the malformed R3 flag on exact-head CI.
3. Resolve/observe the stale provisioning state of run 43698959463 within its existing timeout; do not launch a duplicate live run. If it completes, inspect JSON/SQLite/manifest, saved role coverage, Chair report, integrity flags and R3 per-stage context.
4. On the next justified live run, verify a saved R3 malformed-prose flag appears in the persisted R3 contribution and final Chair report; synthetic generation and Chair boundary regressions pass.
5. Run one consolidated bounded live validation only after code and CI are stable; avoid repeated isolated long model runs.
6. Separately validate full 45-role execution, incomplete/failed agents, saved artefacts, effective R3 context and RTX 4060 activity.
7. Keep evidence retrieval, qualified clinical review and release approval as separate gates.

## Verification boundaries

- Passing CI/unit tests establishes software checks, not clinical accuracy.
- A bounded three-role simulation with deterministic R1 fixtures is not the production 45-role workflow.
- Model loading or allocated VRAM does not prove active GPU inference.
- A clean adversarial run does not prove detection of planted defects; retain positive and negative controls.
- Never claim evidence retrieval, guideline concordance, clinical validation or release readiness without independent evidence.
- Preserve historical failures and limitations; never erase or silently downgrade them.
