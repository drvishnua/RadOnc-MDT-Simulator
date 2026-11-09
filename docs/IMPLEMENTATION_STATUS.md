# Implementation Status

**Last verified:** 9 November 2026
**Repository:** `drvishnua/RadOnc-MDT-Simulator`
**Development branch:** `feature/four-round-mdt-and-performance`
**Verified code snapshot:** `b2c072581d2c6d8f870d39b644d71d5851023dd5`
**PR #1:** open, draft, unmerged; targets `main`.

This document distinguishes code/CI verification from local runtime loading, full live inference, GPU attribution and clinical validation. A passing CI workflow is not evidence of clinical accuracy.

## Current verified snapshot

| Area | State | Verification and limitation |
|---|---|---|
| Four-round architecture | Implemented | R1/R2/R3 orchestration and SG-07 Chair paths have backend tests; no fresh full 136-contribution run on this code snapshot |
| Specialist catalogue | 45 configured roles | Backend tests and local `/api/agents` diagnostic |
| R1 independent assessments | Implemented | Individual role/case prompts and persisted results; latest full live validation predates current prompt and case-integrity changes |
| R2 debate | Implemented | Bounded peer-source allowlists and source-reference checks are covered by backend regression tests; latest full live validation predates these changes |
| R3 adversarial review | Implemented | Source-bound representation/omission checks and schema/prompt constraints are covered by backend tests; latest full live validation predates these changes |
| R4 Chair | Implemented | Saved R1–R3 reconciliation, source-derived role history, distinct-role counts and conservative consensus handling have regression coverage; no fresh live Chair report on this code snapshot |
| Patient registry | Implemented | SQLite registry, sequential local RAD identifiers, immutable case versions, per-version patient-name preservation, linked runs/assessments and delete cascade have backend tests |
| Case-data integrity | Expanded | Pattern-based audits now cover unsupported age/stage-group/T/N/M and other previously implemented claim classes; explicit age/sex/TNM/stage-group discrepancies are surfaced. This is not exhaustive semantic contradiction detection |
| Case validation | Implemented | Completeness warnings are non-blocking; unknown fields remain unknown. Conflicts are warnings and must not be silently reconciled |
| Frontend case restore | Corrected | Structured list values are converted to actual newline-delimited form text and parsed with the same helper; round-trip unit tests added |
| Frontend | CI passed | 21/21 Node tests, TypeScript check and Vite production build on the verified code snapshot |
| Backend | CI passed | 110 passed, 1 warning on the verified code snapshot; warning is the existing Starlette/httpx TestClient deprecation |
| Local source mirror | Synced | Windows self-hosted workflow verified `Source` manifest at the same code SHA and completed local diagnostics |
| Running local backend | Restart not verified | Uvicorn was still running as its prior process during diagnostics. A source copy does not reload Python modules. Do not assume the live backend has loaded the latest source until services are restarted and rechecked |
| Concurrency | 1 | Keep sequential generation; do not increase without measured quality and throughput evidence |
| Model selection | Baseline retained | `qwen3.5:4b` remains the configured baseline. Candidate models are described in `docs/MODEL_BENCHMARK_PLAN.md`; no candidate has been installed or benchmarked |

## Four-round architecture

1. **R1 — Independent assessments:** 45 roles receive the saved case and their own role profile.
2. **R2 — Debate:** 45 roles compare their R1 view with bounded, selected peer perspectives. Supplied source IDs must be attributable and exact.
3. **R3 — Adversarial review:** 45 roles challenge unsupported assumptions, source omissions/distortions, uncertainty, missing information, risks and governance concerns.
4. **R4 — Chair:** SG-07 synthesises actual saved R1–R3 records. Deterministic backend reconciliation verifies saved contributions, position distributions, minority history and report completeness.

Expected saved contribution count for a complete run is 136 (45 + 45 + 45 + 1). A complete run is not necessarily a passing audit. Failed/omitted contributions must remain visible. Position labels are descriptive and are not votes; uniform labels or repeated wording do not establish proposition-level consensus.

## Case-data safeguards

The current case-integrity layer:
- represents missing structured fields as not reported, not negative;
- flags unsupported age and stage-group assertions separately from T/N/M;
- checks unsupported T/N/M, demographic, performance-status, resectability, histology/pathology, investigation, treatment-status and patient-preference assertions covered by the existing rule set;
- uses clause boundaries so a qualifier for one statement does not suppress a separate unsupported assertion after punctuation, commas or contrast markers;
- warns about explicit structured/free-text age, sex, T/N/M and stage-group discrepancies; and
- preserves both source representations for human reconciliation.

These are deterministic pattern-based checks, not comprehensive natural-language understanding. Passing them does not establish that every unsupported claim has been detected. Human review remains necessary. The Chair fallback now explicitly states that the checks are limited and that absence of recorded flags is not proof of absence of unsupported claims.

## Patient registry and persistence

- Local identifiers use sequential `RAD-000001`-style training identifiers; deleted identifiers are not reused.
- Registry name is stored separately from the de-identified clinical case payload.
- Each saved case version is immutable, retains its own best-available patient name and has a snapshot hash.
- Runs and RO-01 assessments are linked to the exact saved case version.
- Deleting a registry record cascades to linked case versions and MDT outputs while preserving the serial allocation.
- Backend tests cover creation, versioning, patient-version ownership, run linkage, legacy migration, historical names and delete cascade.

The complete browser UI flow (create → validate → save → refresh → restore prior version → edit → save new version → delete) has **not** been independently exercised end-to-end in a browser during this verification. Unit and API tests do not substitute for that acceptance test.

## Validation record

### CI and source sync on code snapshot `b2c072581d2c6d8f870d39b644d71d5851023dd5`

- [Backend Tests — run 42574812785](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42574812785): success; **110 passed, 1 warning**.
- [Frontend Build — run 42574812756](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42574812756): success; **21 passed, 0 failed**, TypeScript check and Vite production build passed.
- [Local Source sync and diagnostic — run 42574809719](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42574809719): success; local manifest verified as `feature/four-round-mdt-and-performance @ b2c072581d2c6d8f870d39b644d71d5851023dd5`. Health endpoint, React shell and structured case fields passed diagnostic checks.

The push-triggered duplicate backend/frontend runs were cancelled by workflow concurrency controls. The PR-triggered runs above are the authoritative CI results for this code snapshot.

The local diagnostic found the Vite and Uvicorn processes responding and headless Edge mounted the React shell. It did not restart the existing backend process. The source mirror being current does not prove that an already-running Uvicorn process has loaded newly copied Python files.

### Historical live MDT-006 validation — audit did not pass

- [Workflow run 42502115878](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42502115878)
- Stored run ID: `beaea927-fff8-48ce-9779-1e991149e6ba`
- Code snapshot: `df3e29b7f4f126493212630e128642cecd5700eb` (requested via a later workflow commit)
- Result: `completed_with_findings`; 988.37 seconds; 136/136 expected saved contributions across four rounds.
- Audit totals: **134 hard failures and 92 major findings**. R2 had 45 hard failures; R3 had 89 hard failures and 1 major finding; R1 had 3 major findings; Chair had 2 major findings; stress oracle had 86 major findings.
- R2 findings included invalid broad role-range citations. R3 findings included unsupplied peer references and missing/unclear source-linked challenges. Unsupported resectability, investigation, preference and definitive treatment-safety wording were also identified.
- The Chair withheld a treatment recommendation and retained insufficient-information status; its saved output is not a clinical conclusion.

This run predates subsequent R2/R3 source allowlist, prompt/schema and representation-fidelity changes, and predates the latest case-integrity changes. Those changes have CI coverage but have **not** been validated in a subsequent full live Ollama MDT run. The old audit findings remain open live-validation evidence until a new separately authorised run demonstrates improvement.

### Historical GPU telemetry only

The MDT-006 run recorded 941 telemetry samples on an NVIDIA RTX 4060 Laptop GPU (8,188 MiB): mean utilisation 83.01%, peak 100%; mean VRAM 3,750.84 MiB, peak 3,765 MiB. Ollama `/api/ps` reported `qwen3.5:4b` resident in 188/189 samples. Telemetry was system-wide and does not attribute all GPU activity exclusively to Ollama. These historical measurements are **not** current-head GPU verification.

## Not implemented or not validated

- Evidence retrieval adapters and citation provenance verification.
- Independent guideline/primary literature checking for generated clinical claims.
- Clinically validated evidence grading or accuracy evaluation.
- Formal bias, reproducibility and safety evaluation.
- Qualified clinical MDT validation.
- Full browser acceptance of the patient-registry workflow on the latest source.
- Fresh full 136-contribution live simulation and Chair audit on the current code snapshot.
- Current-head GPU attribution during active inference.
- Real-hospital registration or hospital MRN integration.

## Model benchmark

The controlled model-selection protocol is in [MODEL_BENCHMARK_PLAN.md](./MODEL_BENCHMARK_PLAN.md). It retains `qwen3.5:4b` as the control, requires identical artificial cases/prompts and blinded review, sets critical safety gates before comparison, measures full 136-contribution runtime and GPU telemetry, and treats cloud inference as a separate privacy/security-reviewed phase. No model change has been made.

## Safety and data boundaries

- Fictional educational cases only. Do not enter real patient identifiers or real patient health information.
- Local RAD serials are training identifiers, not hospital medical-record numbers. This application does not register patients with a hospital.
- Registry names are stored separately from the de-identified case payload and are not sent to specialist agents.
- Not a medical device or clinical decision-support system. Outputs are not diagnosis, prescriptions, dose instructions, contours, treatment plans or patient-specific recommendations.
- Outputs must not be used for real-patient treatment decisions or as a substitute for a qualified MDT.
- Evidence retrieval is not connected; no guideline compliance or source verification should be claimed.
