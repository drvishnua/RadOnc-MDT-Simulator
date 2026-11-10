# Implementation Status

**Release candidate verification date:** 10 November 2026  
**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Development branch:** `feature/four-round-mdt-and-performance`  
**Latest verified repository head:** `d6734b285d3fdab0f72a65c2389fe121ccf4f0ef`  
**Windows installer artifact built from this head:** workflow run `42775990228`, artifact `13743792835`  
**PR #1:** open, draft, unmerged; targets `main` at `39a356b8eb09399aa2da1b9b9085965999f5105a`.

Passing software and runtime tests do not establish clinical accuracy, evidence sufficiency or guideline concordance. This section keeps installer acceptance, laptop startup, active GPU inference, full MDT validation and clinical review separate.

## Current Windows x64 release candidate

| Area | Verified state | Evidence and limitation |
|---|---|---|
| Backend CI | **177 passed, 1 existing deprecation warning** | [Run 42775990417](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990417) |
| Frontend CI | **32 passed**; TypeScript and Vite production build passed | [Run 42775990226](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990226) |
| Windows AI-bootstrap tests | PowerShell parsing, static safety checks, mocked existing-model reuse and mocked portable fallback passed | [Installer run 42775990228](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990228); portable download/model-pull branch is still mocked, not a real clean-machine download |
| Hosted Windows installer | PyInstaller package and Inno Setup per-user Setup.exe built; install, health, GUI/assets, 45 roles, registry save and uninstall/data-preservation smoke test passed | [Run 42775990228](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990228) |
| Laptop packaging prerequisites | Read-only inspection passed | [Run 42775990330](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990330); Python 3.14.3 present; no packages or existing services changed |
| Laptop Ollama/GPU discovery | Passed | [Run 42775990178](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990178); Ollama 0.40.15, `qwen3.5:4b` present (3,324,173,934 bytes), NVIDIA RTX 4060 Laptop GPU, driver 591.74, CUDA 13.1 / compute 8.9 discovered |
| Laptop installed application | Healthy and persistent across separate Actions jobs | [Run 42775990229](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990229); health endpoint, model status and 45 roles passed before and after the first runner job ended. The app was already healthy at the start of this check; no second server or scheduled task was created |
| One-agent live inference | Passed twice as two isolated one-request smoke checks while finalising the telemetry script; no full MDT run | Latest [run 42775990287](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990287); direct `POST /api/agents/RO-01/assess`, round 1; no patient/run registration endpoint called |
| Active GPU attribution | **Verified during the latest inference** | 10 of 11 `nvidia-smi` samples had non-zero GPU utilisation; peak 92%; VRAM 3,815 / 8,188 MiB; `ollama ps` reported `qwen3.5:4b`, 3.1 GB, **100% GPU**, context 4096 |
| Patient-data integrity during smoke inference | Passed | Installed SQLite SHA-256 was unchanged before/after; `NO_MDT_RUN_CREATED=True` |
| Latest Windows Setup.exe | Built and independently checksum-verified | Artifact ID `13743792835`; [download via run 42775990228](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42775990228); ZIP digest `sha256:263a7c43351d70aff6cead9697d94880f96015a8729a4296eef4b6d7fdedef40`; Setup.exe size **17,181,752 bytes** |
| Setup.exe SHA-256 | Independently checked against the artifact's `SHA256SUMS.txt` | `9188fdb5d6d5678a677f55c2664f7310a69e0722cd12294090e80d3b91571034` |
| Full 136-contribution MDT | **Not run on this release head** | Historical MDT-006 audit findings remain open; a passing one-agent smoke test is not a four-round validation |
| Evidence retrieval / clinical validation | Not implemented/verified | No independent guideline retrieval, source verification or qualified clinical review |

### Target laptop runtime details

- Windows x64, NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM), driver 591.74.
- Installed Ollama 0.40.15; configured model `qwen3.5:4b` is present in the user's existing model store. The release launcher reused that installation; it did not install a second Ollama runtime or download another model on this laptop.
- Ollama's server log identifies the RTX 4060 as a discrete CUDA device (compute 8.9, CUDA 13.1). At idle, the read-only diagnostic sampled 0% utilisation, which is expected when no generation is active.
- During the latest one-agent inference, Ollama explicitly reported 100% GPU placement at 4096 context. `nvidia-smi` showed non-zero utilisation in 10/11 samples and peaked at 92%, with VRAM usage at 3,815 MiB of 8,188 MiB.
- The latest request took 5.17 seconds. An earlier one-request smoke check on the immediately preceding workflow version took 11.74 seconds. These are individual smoke timings, not a benchmark or a full-run runtime estimate.
- The app was already healthy at the start of the persistence check and remained healthy in a subsequent job. The health, runtime and 45-role API checks succeeded; the backend PID still referred to the installed `RadOncMDT.exe`.

### One-agent output quality review

The latest RO-01 response:
- was schema-valid and retained `educational_simulation_only` and `not_a_treatment_instruction=true`;
- used `insufficient_information` and stated that no treatment recommendation could be made;
- returned zero evidence claims; and
- recorded the missing primary site, histology, T/N/M staging, performance status and comorbidities.

Limitations in that same response:
- the model did not repeat every supplied unknown in its `unknowns` list (notably imaging/investigations, prior treatment and patient goals/preferences);
- its confidence value was 0.95 despite the deliberately incomplete case; and
- the deterministic case-integrity flag list was empty, which does not prove that all relevant omissions or reasoning defects were detected.

These observations are retained as a model-quality follow-up, not described as clinical validation. Two isolated RO-01 smoke requests were executed on successive workflow versions while finalising the PowerShell telemetry helper; both were non-persisted and neither created a patient, assessment record, or MDT run.

### First-run AI provisioning and installer boundary

The installer includes the packaged Python application, FastAPI service, Vite production assets and the PowerShell bootstrap. It does **not** embed the Ollama runtime or model weights inside Setup.exe.

On first launch:
1. The launcher probes the standard Ollama service at `127.0.0.1:11434`.
2. If the service is reachable and `qwen3.5:4b` is present, it reuses that model.
3. If an existing Ollama executable is found but its server is stopped and the standard port is free, it starts that executable without replacing the existing installation or model directory.
4. If Ollama is absent or the standard port is occupied by a non-Ollama process, the launcher provisions the pinned portable Windows runtime under `%LOCALAPPDATA%\RadOncMDT\AIEngine`, verifies its ZIP SHA-256, and uses an isolated loopback service on port 11435 with model files under `%LOCALAPPDATA%\RadOncMDT\Models`.
5. It verifies the configured model via Ollama's `/api/tags` endpoint and pulls `qwen3.5:4b` only when absent.

The portable fallback runtime is pinned to Ollama v0.40.14. Its Windows amd64 ZIP SHA-256 was checked against the official release asset listing: `65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29`. A fresh runtime/model setup requires internet access and at least 8 GB free disk space. After provisioning, inference runs locally.

The installed app database remains under `%LOCALAPPDATA%\RadOncMDT\Data`; logs remain under `Logs`. Uninstall preserves `Data`, `Logs`, `AIEngine` and `Models`. The bootstrap does not stop, upgrade or overwrite an existing Ollama process/model store.

### Explicit remaining limitations

- The self-provisioning installer is **not** an offline all-in-one Setup.exe; a new machine must download missing runtime/model files at first launch.
- The portable-runtime installation and actual model download branch have only mocked tests; this laptop used its existing Ollama/model.
- The two RO-01 smoke requests do not validate all 45 roles, debate, adversarial review, Chair synthesis, consensus integrity or clinical reasoning quality.
- The model's confidence calibration and completeness of its unknowns list need further testing.
- A fresh full 136-contribution MDT run, current-head Chair audit, evidence retrieval/citation verification and qualified clinical review remain outstanding.
- Historical MDT-006 audit findings remain open: 134 hard failures and 92 major findings on an earlier code snapshot.


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
