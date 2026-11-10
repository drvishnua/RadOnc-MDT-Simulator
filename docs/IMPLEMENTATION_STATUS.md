# Implementation Status

**Current release snapshot verified:** 10 November 2026
**Repository:** `drvishnua/RadOnc-MDT-Simulator`
**Development branch:** `feature/four-round-mdt-and-performance`
**Current commit:** `d9283d0db37c42f9e01881190b715695b1c19795`
**PR #1:** open, draft, unmerged; targets `main` at `39a356b8eb09399aa2da1b9b9085965999f5105a`.

This document separates build/CI results from local installation, live inference, GPU attribution and clinical validation. A passing software test is not evidence of clinical accuracy.

## Current Windows beta release snapshot

| Area | Current verified state | Evidence and limitation |
|---|---|---|
| Windows x64 installer | Built and uploaded | [Installer workflow 42711448884](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42711448884); artifact ID `13714784247` |
| Packaged runtime | PyInstaller one-directory application with FastAPI serving the Vite production build | Installed executable passed the health test and served HTML and JavaScript assets |
| Installer | Inno Setup 6 per-user Setup.exe | Installed and uninstalled on a clean hosted Windows runner |
| Backend CI | **177 passed, 1 warning** | [Run 42710563142](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42710563142); existing Starlette/httpx TestClient deprecation |
| Frontend CI | **32 passed** | [Run 42710563160](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42710563160); TypeScript and Vite production build passed |
| Packaging prerequisites | Passed | [Run 42710563157](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42710563157) |
| Installed application smoke test | Passed | Health, bundled frontend/assets, 45 roles, data path and training-record save verified |
| Uninstall/data retention | Passed | Saved database remained byte-for-byte unchanged after the installed uninstaller ran |
| Installer checksum | Independently checked | Setup.exe SHA-256: `771a4f85458571e3a73adc6b5f416863c1d549163dc90a8eb36ee94f7dfbc07a` |
| Ollama/model | External prerequisite | Ollama and `qwen3.5:4b` are not bundled; no inference was run by installer CI |
| Target laptop install | Not yet verified | Hosted Windows CI is not a substitute for installing on the user's laptop |
| Current-head live four-round simulation | Not run | Requires explicit authorisation; historical MDT-006 audit findings remain open |
| Current GPU attribution | Not verified | No active inference telemetry on this commit |
| Evidence and clinical validation | Not implemented/verified | No independent guideline retrieval, source validation or qualified clinical review |

The installer serves the local dashboard at `http://127.0.0.1:8765`. Application data and logs are stored under `%LOCALAPPDATA%\RadOncMDT\`. The installed application includes its Python runtime and does not require Python or Node.js to be separately installed. Ollama and model weights remain separate prerequisites.

The installer was built from the current application code and smoke-tested without contacting Ollama. The test created a fictional training registry record, checked its local RAD serial, uninstalled the application and verified that the SQLite database remained unchanged. This demonstrates software/data-path behaviour only; it does not validate model quality or clinical safety.

## Historical implementation snapshot (9 November 2026; superseded)

The detailed implementation, live-run, local-source and GPU records below refer to older code snapshots. They are retained for audit history and must not be interpreted as the current release status.

## Historical verified snapshot

| Area | State | Verification and limitation |
|---|---|---|
| Four-round architecture | Implemented | R1/R2/R3 orchestration and SG-07 Chair paths have backend tests; no fresh full 136-contribution run on this code snapshot |
| Specialist catalogue | 45 configured roles | Backend tests and local `/api/agents` diagnostic |
| R1 independent assessments | Implemented | Individual role/case prompts and persisted results; latest full live validation predates current prompt and case-integrity changes |
| R2 debate | Implemented | Bounded peer-source allowlists and source-reference checks are covered by backend regression tests; latest full live validation predates these changes |
| R3 adversarial review | Implemented | Source-bound representation/omission checks and schema/prompt constraints are covered by backend tests; latest full live validation predates these changes |
| R4 Chair | Implemented | Saved R1–R3 reconciliation, source-derived role history, distinct-role counts and conservative consensus handling have regression coverage. Missing primary-site/histology title fallback is neutral (“Case details not supplied”); no fresh live Chair report on this code snapshot |
| Patient registry | Implemented | SQLite registry, sequential local RAD identifiers, immutable case versions, per-version patient-name preservation, linked runs/assessments and delete cascade have backend tests |
| Case-data integrity | Expanded | Pattern-based audits cover unsupported age/stage-group/T/N/M assertions and explicit age/sex/TNM/stage-group discrepancies; qualifiers are scoped to clauses. This is not exhaustive semantic contradiction detection |
| Case validation | Implemented | Completeness warnings are non-blocking; unknown fields remain unknown. Conflicts are warnings and must not be silently reconciled |
| Frontend case restore | Corrected | Structured list values are converted to actual newline-delimited form text and parsed with the same helper; round-trip unit tests added |
| Frontend | CI passed | 28 Node tests, launcher syntax/compatibility checks, TypeScript check and Vite production build on the verified code snapshot |
| Backend | CI passed | 114 passed, 1 warning on the verified code snapshot; warning is the existing Starlette/httpx TestClient deprecation |
| Local source mirror | Older snapshot only | Last Windows self-hosted sync verified `Source` at `aa0e90b7...`; current code snapshot `8a318900...` is not yet verified in the local mirror |
| Running local backend | Restart not verified | Uvicorn was not restarted during the last local diagnostic. A source copy does not reload Python modules. Do not assume the live backend has loaded the latest source until services are restarted and rechecked |
| Dashboard MDT timing | Implemented | Displays latest-attempt durations for R2–R4 and wall-clock elapsed time from run creation through the end of R4; includes pauses between rounds and is not pure inference time |
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
- builds Chair report titles only from supplied primary-site/histology fields and uses “Case details not supplied” if both are absent;
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

### CI on exact code snapshot `d6f7421f6c38862f5ca171b1023e94ac3fdcfb06`

- [Backend Tests — run 42581653317](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42581653317): success; **114 passed, 1 warning** (the existing Starlette/httpx TestClient deprecation).
- [Frontend Build — run 42581653276](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42581653276): success; **28 tests passed**, PowerShell launcher parsing, Node compatibility, TypeScript check and Vite production build passed.
- Dashboard timing display has regression coverage for valid, zero, long, missing, invalid and reversed intervals. The parent run is refreshed at the terminal Chair state so the full-MDT duration updates without hiding retry controls after a Chair error.

### Local source/runtime verification

- [Last Local Source sync and diagnostic — run 42576725334](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42576725334): success; manifest read back as `feature/four-round-mdt-and-performance @ aa0e90b7ec6fbbea9fc359c98f2deefdad2cf902`.
- The current verified code snapshot `8a318900f9a661116dba2130b118d924741bfcfe` has **not** yet been verified in the local `Source` manifest.
- The older diagnostic checked FastAPI health, Ollama reachability, React shell mounting and structured case-field presence. It did not restart the existing Uvicorn process.
- Full browser create/validate/save/refresh/restore/edit/delete acceptance, browser console/network review and current-head backend module reload remain outstanding.

### Persisted execution timing

- `simulation_runs.mdt_finished_at` records terminal completion of the full four-round MDT when Round 4 finishes, including terminal `completed_with_errors`; it stays null before Round 4 ends.
- `round_runs.started_at` and `round_runs.finished_at` expose each round interval.
- Existing SQLite databases receive additive column migrations; regression tests cover migration, completion and Chair retry.
- Retrying Round 4 clears the earlier parent finish time before setting it again on terminal completion.
- `simulation_runs.created_at` is the overall elapsed-time start reference. First-token timing is not measured; round timestamps reflect the latest attempt rather than cumulative retry time.

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
- Full browser acceptance of the patient-registry workflow and confirmation of backend module reload on the latest source.
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
