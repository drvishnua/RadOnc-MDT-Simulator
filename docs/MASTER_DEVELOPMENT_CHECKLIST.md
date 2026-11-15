# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Latest fully verified code/test commit:** `970c89952c4414d79b0aea767f10e91d482602ad` (all six workflows passed; application-code fix is `92dbb559ed1a0f781ec838f6e30acb42cf405f98`).

Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| Four-round R1–R4 architecture/data flow | IN PROGRESS | Implemented with regression coverage; full current-head 45-role live acceptance outstanding. |
| R1 independent assessment | IN PROGRESS | Implemented; complete current-head production-scale output audit outstanding. |
| R2 debate and peer sourcing | IN PROGRESS | Source allowlists/provenance checks exist; current full-run provenance review outstanding. |
| R3 adversarial review | IN PROGRESS | Source-bound checks and positive/negative control tooling exist; full 45-role test outstanding; bounded artifact from run 43559331144 showed malformed model output ('Both and explicitly state...'). Input neutralisation was grammatical. Commit `92dbb55` adds a non-rewriting audit flag and failure/grammatical negative-control tests. The `970c899` Chair regression confirms the flag is retained in `case_data_integrity_flags` and attributed to fixture role RO-03. All six workflows passed. Full 45-role validation remains outstanding. |
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
| Backend tests | VERIFIED | `970c899`, [run 43696654434](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654434): 305 passed, 0 failed/errors/skipped; preflight 6 passed, 0 failed/inconclusive. Includes malformed-prose detector, grammatical negative control and Chair handoff regression. Failure history retained: `685761a` failed due an over-escaped regex, fixed in `92dbb55`; test-only `39140b4` expected RO-01 but fixture was RO-03, corrected in `970c899`. |
| Frontend build | VERIFIED | [Run 43696654466](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654466): success on `970c899`. |
| Browser registry/dashboard E2E | VERIFIED | [Run 43696654555](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654555): success on `970c899`. |
| Packaging prerequisites | VERIFIED | [Run 43696654501](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654501): success on `970c899`. |
| Windows installer build/smoke test | VERIFIED | [Run 43696654364](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654364): build, install/smoke test, checksum and artifact upload passed on `970c899`; optional clean-host first-run Ollama/model bootstrap skipped. |
| Dependency/security workflows | VERIFIED (analysis execution); alert closure pending | [Run 43696654379](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43696654379): dependency audit, secret scan and Python/JS CodeQL jobs passed on `970c899`. No unresolved PR review threads; direct code-scanning alert record was inaccessible, so formal alert closure is not claimed. |
| Frontend flicker/blank screens/stale state | IN PROGRESS | Browser E2E passes; dedicated reproduction and console/network/lifecycle investigation outstanding. |
| Dashboard/API integration | IN PROGRESS | Baseline browser E2E passed; current-head acceptance outstanding. |
| Ollama context allocation | VERIFIED (isolated probe only) | Hosted Windows probe observed requested/actual 6,144 and 8,192. Not proof of effective context in a full MDT run. |
| Effective R3 context/truncation | IN PROGRESS | Earlier run snapshots reported 4,096 despite an 8,192 request; end-to-end verification outstanding. |
| RTX 4060 active inference | IN PROGRESS | Historical laptop GPU measurements exist; current-head request-time GPU/offload verification outstanding. |
| Full live 45-role MDT | NOT STARTED (current HEAD) | No complete current-head 136-contribution run with audited saved outputs. Historical runs are not current proof. |
| Live artefacts/reproducibility | IN PROGRESS | Bounded synthetic artefacts exist; full current-head artefact inspection outstanding. |
| Evidence retrieval/guideline verification | NOT STARTED | Retrieval is not connected; no guideline concordance is claimed. |
| Independent clinical review | NOT STARTED | Qualified clinical review/acceptance not performed. |
| Windows release/security acceptance | IN PROGRESS | Installer and security workflows passed on `970c899`; direct alert-state confirmation, full live validation and release gates remain. |
| Authoritative repository checklist | VERIFIED | This file is the single master checklist; `IMPLEMENTATION_STATUS.md` points here for current status. |

## Immediate priorities

1. Obtain direct confirmation that CodeQL alert 4 is formally closed; review all subsequent security findings.
2. On the next justified live run, verify a saved R3 malformed-prose flag appears in the persisted R3 contribution and final Chair report; the synthetic Chair boundary regression now passes.
3. Run one consolidated bounded live validation only after code and CI are stable; avoid repeated isolated long model runs.
4. Separately validate full 45-role execution, incomplete/failed agents, saved artefacts, effective R3 context and RTX 4060 activity.
5. Keep evidence retrieval, qualified clinical review and release approval as separate gates.

## Verification boundaries

- Passing CI/unit tests establishes software checks, not clinical accuracy.
- A bounded three-role simulation with deterministic R1 fixtures is not the production 45-role workflow.
- Model loading or allocated VRAM does not prove active GPU inference.
- A clean adversarial run does not prove detection of planted defects; retain positive and negative controls.
- Never claim evidence retrieval, guideline concordance, clinical validation or release readiness without independent evidence.
- Preserve historical failures and limitations; never erase or silently downgrade them.
