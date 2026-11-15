# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Latest verified code commit:** `965d6bab30b69877b0b09f0a0d3872f900e867ab` (the subsequent checklist-evidence commit changes documentation only).

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
| TNM connector CodeQL remediation | IN PROGRESS | `case_integrity.py` now uses direct string comparison; the new whitespace/case regression passed in the 303-test suite. Python and JavaScript CodeQL jobs passed on `965d6ba`; the PR thread is no longer unresolved. The separate alert record could not be queried, so formal alert closure is not claimed. |
| Unknowns, staging and contradictions | IN PROGRESS | Not-reported semantics and discrepancy warnings exist; semantic coverage and human review remain required. |
| Conditional recommendations/prerequisites | IN PROGRESS | Deterministic checks exist; full live-output audit outstanding. |
| Distinct-role Chair counting | VERIFIED | Regression coverage and exact-baseline backend CI passed; complete live consensus validation still outstanding. |
| Proposition consensus, dissent and position history | IN PROGRESS | Deterministic reconciliation/tests exist; full current-head report audit outstanding. |
| Case hashes, run IDs, timestamps and audit history | IN PROGRESS | Mechanisms exist; complete current-head reproducibility audit outstanding. |
| Provenance and source attribution | IN PROGRESS | Round/source validation exists; evidence retrieval and independent source verification are not implemented. |
| Missing/failed agent handling | IN PROGRESS | Validation mechanisms exist; current-head incomplete-case/failure-injection acceptance outstanding. |
| Backend tests | VERIFIED | `965d6ba`, [run 43695041727](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041727): 303 passed, 0 failed/errors/skipped; preflight 6 passed, 0 failed/inconclusive. The TNM connector regression is included. |
| Frontend build | VERIFIED | [Run 43695041710](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041710): success on `965d6ba`. |
| Browser registry/dashboard E2E | VERIFIED | [Run 43695041719](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041719): success on `965d6ba`. |
| Packaging prerequisites | VERIFIED | [Run 43695041782](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041782): success on `965d6ba`. |
| Windows installer build/smoke test | VERIFIED | [Run 43695041711](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041711): build, install/smoke test, checksum and artifact upload succeeded on `965d6ba`; optional clean-hosted model bootstrap skipped. |
| Dependency/security workflows | VERIFIED (analysis execution); alert closure pending | [Run 43695041713](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43695041713): dependency audit, secret scan and both CodeQL jobs succeeded. No unresolved PR review thread remains for the TNM finding; the separate alert record was not accessible for direct state confirmation. |
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

1. Obtain direct confirmation that CodeQL alert 4 is formally closed; review all subsequent security findings.
2. Address the R3 peer-prose citation/attribution quality defect with regression coverage.
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
