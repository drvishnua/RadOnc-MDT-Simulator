# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Current milestone (9 November 2026):** The development branch contains the four-round 45 + 45 + 45 + 1 workflow, patient registry/versioning, expanded case-integrity checks and Chair safeguards (including a neutral title when both primary site and histology are absent). CI passed on code snapshot `084d3353bc3dd71a7ee27895e41434c0d425644b` (backend 111 passed; frontend 21 passed and production build passed). The latest detailed live MDT-006 audit remains a historical failure with 134 hard failures and 92 major findings; the later prompt/schema and case-integrity changes have not yet had a fresh full live run. Feature-branch pushes synchronize source to the laptop `Source` folder, but an already-running backend must be restarted to load copied Python changes.

## Purpose

The initial scenario set focuses on synthetic head-and-neck cancer cases. The simulator helps trainees and educators explore specialty perspectives, patient context, uncertainty, disagreement, feasibility, resources, and governance. It is not a clinical decision-support system.

## 45 configured perspectives

All 45 configured role profiles are required in each of Rounds 1–3. Round 4 uses the MDT Chair role to synthesize the stored views. The agents are role prompts using one shared Ollama model, not 45 separately loaded models.

## Four-round workflow

1. **Round 1 — Independent assessments:** Each role receives the saved synthetic case and its own role profile. No other agent's output is included. Each must state a position, provisional conclusion, and preferred educational option or explain why none can yet be preferred.
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
- POST /api/patients — save a new synthetic patient with case version 1
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

## Validation status

### Current code/CI snapshot

The following checks ran against code snapshot `084d3353bc3dd71a7ee27895e41434c0d425644b`:

- **Backend CI:** [run 42575218662](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42575218662) — success; **111 passed, 1 warning** (the existing Starlette/httpx TestClient deprecation).
- **Frontend CI:** [run 42575218585](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42575218585) — success; **21 tests passed**, TypeScript check and Vite production build passed.
- **Windows source sync and local diagnostic:** [run 42575212397](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42575212397) — success; the local manifest was read back and verified as `feature/four-round-mdt-and-performance @ 084d3353bc3dd71a7ee27895e41434c0d425644b`. FastAPI health, React shell mounting and structured case-field presence checks passed.

The self-hosted diagnostic found existing Vite and Uvicorn processes listening and the React shell mounted. It did not restart the existing Uvicorn process. Source sync therefore does not prove that an already-running backend has loaded the latest copied Python code; stop and restart the local services after backend changes.

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

## Local setup

From the Windows Source folder, double-click Start-RadOnc-MDT.cmd. Use Stop-RadOnc-MDT.cmd to stop the backend and frontend. Ollama remains running. Services bind to localhost.

## Repository hygiene and license

Model weights, runner credentials, local database files, logs, build output, and secrets must remain outside Git. No license is currently specified; do not assume redistribution, modification, or commercial-use permission.


## Project operating instructions

Repository-wide development and safety rules are documented in [`AGENTS.md`](./AGENTS.md). Read this file before making code changes or interpreting simulation exports, especially when continuing work in a new chat.
