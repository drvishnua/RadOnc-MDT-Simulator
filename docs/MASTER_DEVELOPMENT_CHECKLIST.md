# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Baseline before this checklist/code-fix commit:** `4fb3540721342239d08cb5bca1876c9371cb7b41`.

Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| Four-round R1–R4 architecture/data flow | IN PROGRESS | Implemented with regression coverage; full current-head 45-role live acceptance outstanding. |
| R1 independent assessment | IN PROGRESS | Implemented; complete current-head production-scale output audit outstanding. |
| R2 debate and peer sourcing | IN PROGRESS | Source allowlists/provenance checks exist; current full-run provenance review outstanding. |
| R3 adversarial review | IN PROGRESS | Source-bound checks and positive/negative control tooling exist; full 45-role test and peer-prose quality follow-up outstanding. |
| R4 Chair synthesis | IN PROGRESS | Saved-contribution reconciliation and deterministic reporting have regression coverage; full current-head Chair audit outstanding. |
| Clinical safety/unsupported claims | IN PROGRESS | Deterministic audits and TNM regression coverage exist; not exhaustive clinical validation. |
| TNM connector CodeQL finding | IN PROGRESS | Open alert on `case_integrity.py`, baseline line 414. This commit replaces regex connector matching with direct string comparison and adds a regression test; new-head CI/security recheck pending. |
| Unknowns, staging and contradictions | IN PROGRESS | Not-reported semantics and discrepancy warnings exist; semantic coverage and human review remain required. |
| Conditional recommendations/prerequisites | IN PROGRESS | Deterministic checks exist; full live-output audit outstanding. |
| Distinct-role Chair counting | VERIFIED | Regression coverage and exact-baseline backend CI passed; complete live consensus validation still outstanding. |
| Proposition consensus, dissent and position history | IN PROGRESS | Deterministic reconciliation/tests exist; full current-head report audit outstanding. |
| Case hashes, run IDs, timestamps and audit history | IN PROGRESS | Mechanisms exist; complete current-head reproducibility audit outstanding. |
| Provenance and source attribution | IN PROGRESS | Round/source validation exists; evidence retrieval and independent source verification are not implemented. |
| Missing/failed agent handling | IN PROGRESS | Validation mechanisms exist; current-head incomplete-case/failure-injection acceptance outstanding. |
| Backend tests | VERIFIED (baseline only) | `4fb3540`, [run 43692521201](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521201): 302 passed, 0 failed/errors/skipped; preflight 6 passed. New regression awaits new-head CI. |
| Frontend build | VERIFIED (baseline only) | [Run 43692521263](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521263): success on baseline. |
| Browser registry/dashboard E2E | VERIFIED (baseline only) | [Run 43692521198](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521198): success on baseline. |
| Packaging prerequisites | VERIFIED (baseline only) | [Run 43692521274](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521274): success on baseline. |
| Windows installer build/smoke test | VERIFIED (baseline only) | [Run 43692521186](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521186): success on baseline. |
| Dependency/security workflows | VERIFIED (workflow execution only) | [Run 43692521176](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43692521176): dependency audit, secret scan and both CodeQL jobs succeeded. One new CodeQL alert remains open for remediation/recheck. |
| Frontend flicker/blank screens/stale state | IN PROGRESS | Browser E2E passes; dedicated reproduction and console/network/lifecycle investigation outstanding. |
| Dashboard/API integration | IN PROGRESS | Baseline browser E2E passed; current-head acceptance outstanding. |
| Ollama context allocation | VERIFIED (isolated probe only) | Hosted Windows probe observed requested/actual 6,144 and 8,192. Not proof of effective context in a full MDT run. |
| Effective R3 context/truncation | IN PROGRESS | Earlier run snapshots reported 4,096 despite an 8,192 request; end-to-end verification outstanding. |
| RTX 4060 active inference | IN PROGRESS | Historical laptop GPU measurements exist; current-head request-time GPU/offload verification outstanding. |
| Full live 45-role MDT | NOT STARTED (current HEAD) | No complete current-head 136-contribution run with audited saved outputs. Historical runs are not current proof. |
| Live artefacts/reproducibility | IN PROGRESS | Bounded synthetic artefacts exist; full current-head artefact inspection outstanding. |
| Evidence retrieval/guideline verification | NOT STARTED | Retrieval is not connected; no guideline concordance is claimed. |
| Independent clinical review | NOT STARTED | Qualified clinical review/acceptance not performed. |
| Windows release/security acceptance | IN PROGRESS | Baseline installer/security workflows passed; CodeQL finding and release gates remain. |
| Authoritative repository checklist | VERIFIED | This file is the single master checklist; `IMPLEMENTATION_STATUS.md` points here for current status. |

## Immediate priorities

1. Verify exact-head CI for the regex fix, including backend tests, CodeQL and all six workflows.
2. Confirm CodeQL alert 4 is resolved; inspect any new findings, not just workflow conclusions.
3. Address the R3 peer-prose citation/attribution quality defect with regression coverage.
4. Run one consolidated bounded live validation only after code and CI are stable; avoid repeated isolated long model runs.
5. Separately validate full 45-role execution, incomplete/failed agents, saved artefacts, effective R3 context and RTX 4060 activity.
6. Keep evidence retrieval, qualified clinical review and release approval as separate gates.

## Verification boundaries

- Passing CI/unit tests establishes software checks, not clinical accuracy.
- A bounded three-role simulation with deterministic R1 fixtures is not the production 45-role workflow.
- Model loading or allocated VRAM does not prove active GPU inference.
- A clean adversarial run does not prove detection of planted defects; retain positive and negative controls.
- Never claim evidence retrieval, guideline concordance, clinical validation or release readiness without independent evidence.
- Preserve historical failures and limitations; never erase or silently downgrade them.
