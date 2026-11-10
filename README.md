# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Latest release verification snapshot — 11 November 2026:** `5d593aa3d71e066dc6fb1d21ae1e8f493f8d6a99`. Functional/application-code baseline: `5b8159df0b0bb6ac0bedc95046d0c87784420591`; intervening commits through the installer snapshot changed CI workflow references and documentation, not application runtime code. PR #1 remains open, draft and unmerged; `main` remains unchanged at `39a356b8eb09399aa2da1b9b9085965999f5105a`.

> **Software and security CI:** On validation snapshot `a7e38146e5d4cf626abbfc419b243e26ca02d5f3` (same functional code baseline), backend regression tests passed (**191 passed, 1 existing Starlette/httpx TestClient deprecation warning**) ([run 42907820055](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42907820055)); frontend passed (**32 tests**; TypeScript and Vite **7.3.8** production build using `npm ci`) ([run 42907820019](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42907820019)); isolated Windows browser E2E passed patient registry lifecycle and saved R1–R4 dashboard checks ([run 42907820009](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42907820009)); CodeQL Python and JavaScript/TypeScript, full-history Gitleaks, pip-audit and npm audit passed with zero known dependency vulnerabilities ([run 42907820027](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42907820027)); packaging-prerequisite inspection passed ([run 42907820144](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42907820144)).

> **Latest Windows x64 installer:** **Verified** [workflow run 42908356200](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42908356200), source snapshot `5d593aa3d71e066dc6fb1d21ae1e8f493f8d6a99`, artifact ID `13806731062`. Windows package build, install/uninstall smoke test, user-database preservation, clean-machine Ollama `0.40.14` provisioning, `qwen3.5:4b` download/tag verification, CPU inference, installed-app health and 45-role API checks all passed. ZIP size **14,819,981 bytes**, ZIP SHA-256 `64cc3ea5963856c835340e3b567f1b35f60fd88fcbacfe24097e6fcc13d56c47`. Setup.exe size **15,370,274 bytes**, independently verified SHA-256 `917c9cc45072491507cab4a8bccdae5f878f6c3961cbf62033b637612d34bd29`. Hosted CPU validation only; this is not a claim of NVIDIA GPU use on the target laptop. Artifact retention expires **24 November 2026**.

> **Engineering controls:** frontend lockfile v3 is committed (120 packages); Vite is pinned at 7.3.8; Node engine is `^20.19.0 || >=22.12.0`; CI, installer, browser E2E, security audit and developer startup use `npm ci`. pytest is separated from production runtime requirements. Dependabot proposes weekly updates. Primary workflow actions are pinned to immutable commit SHAs. Branch protection is disabled and must be addressed before merge.

> **Still not validated:** a fresh full 136-contribution four-round Ollama run and latest Chair audit; clinical reasoning quality; evidence retrieval/source verification and guideline concordance; qualified clinical review; current target-laptop full-run GPU attribution/performance; installer code signing. Historical MDT-006 findings (134 hard failures and 92 major findings on an earlier code snapshot) remain open until a fresh full audit demonstrates improvement. Use fictional educational cases only; this is not clinical decision support.

## Installing the Windows release candidate

1. Download `RadOnc-MDT-Simulator-Setup.exe` from the [verified Windows Installer Build artifact (run 42908356200)](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42908356200). Verify its SHA-256 against `SHA256SUMS.txt` before installation.
2. Before upgrading an existing installation, use **Stop RadOnc MDT Simulator** from the Start menu. This stops the app only; it does not stop Ollama or alter the patient database.
3. Run Setup.exe. It installs per-user and updates the existing application in place.
4. Launch **RadOnc MDT Simulator** from the Start menu or desktop shortcut. On first launch, keep the launcher window open while it checks/provisions Ollama and `qwen3.5:4b`. Internet access and at least 8 GB of free space are needed only when the required runtime/model are not already installed.
5. The local dashboard opens at `http://127.0.0.1:8765`. No separate Python, Node.js, Ollama installation or terminal command is required.

The installer preserves `%LOCALAPPDATA%\RadOncMDT\Data`, `Logs`, `AIEngine` and `Models` when the application is uninstalled. The first-run AI bootstrap uses an existing Ollama/model where possible; the fallback runtime is isolated at localhost port 11435. Existing development databases are **not imported automatically**. To copy one, stop the old app, make a separate backup, and follow the explicit `legacy-db-path.txt` procedure in the installed README. The migration checks both source and copied SQLite integrity, never changes the source, and never overwrites an existing destination.

The installer is not configured for code signing. Windows SmartScreen may display an unfamiliar-app warning.

## Purpose

The initial scenario set focuses on fictional head-and-neck training cases. The simulator helps trainees and educators explore specialty perspectives, patient context, uncertainty, disagreement, feasibility, resources, and governance. It is not a clinical decision-support system.

## 45 configured perspectives

All 45 configured role profiles are required in each of Rounds 1–3. Round 4 uses the MDT Chair role to synthesize the stored views. The agents are role prompts using one shared Ollama model, not 45 separately loaded models.

## Four-round workflow

1. **Round 1 — Independent assessments:** Each role receives the saved training case and its own role profile. No other agent's output is included. Each must state a position, provisional conclusion, and preferred educational option or explain why none can yet be preferred.
2. **Round 2 — MDT debate:** Each role receives its own Round-1 view and a bounded digest of selected peer positions. It records agreements, substantive challenges, and any change in position. The full independent views remain preserved.
3. **Round 3 — Adversarial review:** All roles identify unsupported assumptions, uncertainty, missing information, patient/context concerns, feasibility issues, risks, and governance questions.
4. **Round 4 — Chair synthesis:** SG-07 creates a structured Chair draft. Before storage, the backend reconciles it against saved role records: exact position counts are recomputed, non-modal views are preserved with source conclusions, and missing-information, patient/family, feasibility, governance, and evidence-limitations sections are populated from source data.

Position labels are descriptions, not votes. The system does not invent a majority or force consensus. A conditional position is not automatically classified as opposition, and a non-uniform distribution is not described as unanimous.

## Dashboard capabilities

- Fictional training patient registry with sequential local IDs, structured clinical details, version history and linked simulations.
- Case validation and 45-role directory.
- Sequential local training IDs, separate fictional patient registry profiles, de-identified immutable clinical case versions, and patient/case-version history.
- Patient-linked simulation history, with each run and standalone RO-01 result bound to its exact de-identified case version and hash.
- Sequential local Ollama execution with progress and per-agent outputs.
- One retry with a larger output budget for malformed structured responses, without rerunning successful agents.
- Resume failed/interrupted work while retaining completed results.
- Separate Start/Resume controls and progress for Rounds 2–4.
- Expandable role contributions and a final Chair report.
- JSON export of all available rounds, including exact saved case JSON and its SHA-256 checksum.
- Run and case recovery after browser refresh.

## API overview

- GET /health
- GET /api/runtime
- GET /api/agents
- GET /api/patients
- POST /api/patients — save a new fictional training patient with case version 1
- GET /api/patients/{patient_id} — patient versions and linked simulation history
- POST /api/patients/{patient_id}/versions — append an immutable case version
- POST /api/patients/{patient_id}/runs — start only from a saved case version
- POST /api/patients/{patient_id}/versions/{case_version_id}/assess/RO-01 — generate and persist RO-01
- GET /api/patients/{patient_id}/versions/{case_version_id}/assessments
- POST /api/cases/validate
- POST /api/agents/{agent_id}/assess
- POST /api/runs
- GET /api/runs/{run_id}
- GET /api/runs/{run_id}/case
- GET /api/runs/{run_id}/results
- POST /api/runs/{run_id}/resume
- POST /api/runs/{run_id}/rounds/{2|3|4}
- GET /api/runs/{run_id}/rounds/{round_number}
- GET /api/runs/{run_id}/rounds/{round_number}/results
- POST /api/runs/{run_id}/rounds/{round_number}/resume
- GET /api/runs/{run_id}/report

See the backend and frontend READMEs for setup and details.

## Local inference and runtime

The target laptop uses Ollama with qwen3.5:4b and an 8 GB RTX 4060. The orchestrator defaults to **one active generation at a time**. A real two-request benchmark measured 0.86x throughput relative to sequential execution, so two-at-once execution was not enabled.

The model is kept warm during a run. Prompts use Ollama's schema-constrained output rather than duplicating the full JSON schema in prompt text. Context remains fixed at 4K. Initial/retry output budgets are 1,100/1,500 tokens for Round 1, 700/1,000 for Rounds 2–3, and 1,600/2,200 for the Chair.

## Historical validation record (older code snapshots; superseded by the current release snapshot above)

### Older code/CI snapshot

The following CI checks ran against exact code snapshot `d6f7421f6c38862f5ca171b1023e94ac3fdcfb06`:

- **Backend CI:** [run 42581653317](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42581653317) — success; **114 passed, 1 warning** (the existing Starlette/httpx TestClient deprecation).
- **Frontend CI:** [run 42581653276](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42581653276) — success; **28 tests passed**, PowerShell launcher syntax, Node compatibility, TypeScript checking and Vite production build passed.
- **Dashboard timing:** R2–R4 attempt durations and full wall-clock elapsed time through Round 4 are rendered from persisted timestamps. The overall interval begins at run creation and includes pauses between rounds; it is not pure inference time.
- **Terminology:** generated Chair report text, agent prompts, API descriptions, validation metadata and user documentation consistently use “fictional training case” / “educational simulation” language. Internal Python/schema/DB identifiers remain unchanged for compatibility. The education-only/no-clinical-decision boundary is retained.

### Historical local source/runtime verification

- The last successful Windows source-sync diagnostic is [run 42576725334](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42576725334), which verified the local `Source` manifest at the older code snapshot `aa0e90b7ec6fbbea9fc359c98f2deefdad2cf902`.
- The current code snapshot `8a318900f9a661116dba2130b118d924741bfcfe` has **not** yet been verified in the local `Source` manifest.
- The older diagnostic found FastAPI health, Ollama reachability, the React app shell and structured case-field presence, but did not restart Uvicorn. A source copy does not prove that an already-running backend process has imported changed Python modules.
- Full patient-registry browser acceptance (create → validate → save → refresh → restore → edit → save version → delete), browser console/network inspection and a current-head backend restart remain outstanding.

Round-level execution timing is persisted as `round_runs.started_at` and `round_runs.finished_at`; the parent run stores `mdt_finished_at` when Round 4 reaches a terminal state. Existing SQLite databases receive additive migrations. Resetting the Chair also clears the parent MDT finish time. The parent run's `created_at` is the start reference for elapsed time from run creation, not a separately measured first-token timestamp.

### Historical full live runs — not current-head validation

- Earlier live run [41979964363](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/41979964363) completed all 136 generations in 793.06 seconds with zero failures/retries on code commit `cf1792b617bdceb7e0beea4cc42c183f9068f9b2`. This is a historical successful execution, not evidence for the current code snapshot.
- The later, more detailed MDT-006 audit [run 42502115878](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42502115878) completed all 136 saved contributions in 988.37 seconds but reported **134 hard failures and 92 major findings**. Workflow completion means inference and artefact upload completed; it does not mean the audit passed.
- The MDT-006 audit found broad/invalid R2 citations, unsupplied peer references and omissions/unclear challenges in R3, plus unsupported resectability, investigation, preference and treatment-safety assertions. Its Chair withheld a treatment recommendation and retained insufficient-information status.
- The subsequent R2/R3 prompt/schema changes and the latest case-integrity changes have CI coverage but have **not** been validated in a new full live Ollama run. The MDT-006 findings remain open until a separately authorised live validation demonstrates improvement.

### GPU evidence boundary

The historical MDT-006 run recorded sustained system-wide RTX 4060 activity (mean 83.01%, peak 100%) and Ollama model residency telemetry. The telemetry was system-wide and cannot attribute all GPU activity exclusively to Ollama. These values are historical, not a current-head GPU verification. Model residency or VRAM allocation alone is not proof of active token inference.

A fresh live 136-contribution run, current-head GPU attribution and qualified clinical review are still outstanding. CI and backend tests do not establish clinical accuracy or guideline concordance.

## Automatic laptop source synchronization

Pushes to `main` and `feature/four-round-mdt-and-performance` trigger the Windows self-hosted runner to check out that exact commit and copy/update the repository into the persistent sibling `Source` folder. The workflow writes `.radonc-sync-state.json` with the branch and commit, then reads it back to verify the copy.

The sync is additive/update-only: it does not delete unrelated files in `Source`. It excludes Git metadata, installed Node/Python dependencies, Python caches, and local logs. The runner installation and sibling `AI_Models` folder are outside the destination and are not copied over.

The `Source` folder is a runtime source mirror, not a separate Git working tree. The Actions runner's own checkout is refreshed to the pushed branch/commit for each workflow run. The sync does not forcibly restart an already-running app. After backend-code changes, use `Stop-RadOnc-MDT.cmd` from `Source`, then `Start-RadOnc-MDT.cmd` to ensure the new Python modules are loaded; running the Start launcher alone while the backend is already responding leaves that process in place. The launcher prepares/checks dependencies, starts FastAPI and Vite, and starts Ollama if it is installed but not already reachable. Do not stop services while a simulation is queued or running.

## Evidence boundary

Evidence retrieval and citation verification are not connected yet. Evidence claims remain disabled. The model must not invent guidelines, trials, statistics, identifiers, or citations. Lack of citations must not be mistaken for verified evidence.

## Safety and data boundaries

- Fictional training records only. Do not enter real patient identifiers or real patient health information. Local RAD serials are training identifiers, not hospital medical-record numbers; this application does not register patients with a hospital. Registry names are stored separately and are never sent to specialist agents.
- Not a medical device, clinical decision-support system, treatment-planning tool, or substitute for a qualified MDT.
- Do not use outputs as diagnosis, prescriptions, dose instructions, contours, or treatment plans.
- Model outputs may be incomplete or inaccurate; clinical claims require traceable evidence and qualified review.
- Economic, policy, safeguarding, and medico-legal perspectives are issue-spotting aids, not professional advice.
- Patient personas are discussion lenses, not demographic stereotypes or assumptions about an individual.

## Local development setup

For source-tree development only, from the Windows Source folder, double-click Start-RadOnc-MDT.cmd. Use Stop-RadOnc-MDT.cmd to stop the backend and frontend. Ollama remains running. Development services bind to localhost. Installed users should use the Start-menu or desktop shortcuts described above.

## Repository hygiene and license

Model weights, runner credentials, local database files, logs, build output, and secrets must remain outside Git. No license is currently specified; do not assume redistribution, modification, or commercial-use permission.


## Project operating instructions

Repository-wide development and safety rules are documented in [`AGENTS.md`](./AGENTS.md). Read this file before making code changes or interpreting simulation exports, especially when continuing work in a new chat.
