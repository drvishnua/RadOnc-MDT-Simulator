# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Current milestone:** The development branch implements 45 independent assessments, 45-agent debate, 45-agent adversarial review, and SG-07 Chair synthesis. The reconciled Chair logic has passed backend regression tests and a fresh 136-generation live run on the target laptop. Feature-branch pushes now automatically synchronize the source into the laptop's `Source` folder.

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

- Synthetic case validation and 45-role directory.
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

- **Fresh live local-model validation:** run [41979964363](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/41979964363) passed on commit `cf1792b617bdceb7e0beea4cc42c183f9068f9b2`. It completed all 136 generations (45 + 45 + 45 + 1) with zero failures or retries in 793.06 seconds using Ollama `qwen3.5:4b` and the laptop RTX 4060.
- **Backend regression suite:** 31 tests passed on the final reconciled backend.
- **Frontend/launcher CI:** PowerShell parsing, Node compatibility checks, dependency installation, TypeScript checking, and production build passed on commit `1f9212653457dbeb5a656d72d3b333833842b5a2`.
- **Laptop source sync:** run [41984385622](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/41984385622) passed on the self-hosted `RadOnc-Laptop` runner and verified the local `Source` folder at commit `1f9212653457dbeb5a656d72d3b333833842b5a2`.

## Automatic laptop source synchronization

Pushes to `main` and `feature/four-round-mdt-and-performance` trigger the Windows self-hosted runner to check out that exact commit and copy/update the repository into the persistent sibling `Source` folder. The workflow writes `.radonc-sync-state.json` with the branch and commit, then reads it back to verify the copy.

The sync is additive/update-only: it does not delete unrelated files in `Source`. It excludes Git metadata, installed Node/Python dependencies, Python caches, and local logs. The runner installation and sibling `AI_Models` folder are outside the destination and are not copied over.

The `Source` folder is a runtime source mirror, not a separate Git working tree. The Actions runner's own checkout is refreshed to the pushed branch/commit for each workflow run. After a sync, use `Start-RadOnc-MDT.cmd` from `Source` to start the local app; use `Stop-RadOnc-MDT.cmd` to stop the backend and frontend. The sync does not forcibly restart an already-running app, so restart the local services after backend-code changes to load the new backend modules. The launcher prepares/checks dependencies, starts FastAPI and Vite, and starts Ollama if it is installed but not already reachable.

## Evidence boundary

Evidence retrieval and citation verification are not connected yet. Evidence claims remain disabled. The model must not invent guidelines, trials, statistics, identifiers, or citations. Lack of citations must not be mistaken for verified evidence.

## Safety and data boundaries

- Synthetic cases only. Do not enter identifiable or real patient information.
- Not a medical device, clinical decision-support system, treatment-planning tool, or substitute for a qualified MDT.
- Do not use outputs as diagnosis, prescriptions, dose instructions, contours, or treatment plans.
- Model outputs may be incomplete or inaccurate; clinical claims require traceable evidence and qualified review.
- Economic, policy, safeguarding, and medico-legal perspectives are issue-spotting aids, not professional advice.
- Patient personas are discussion lenses, not demographic stereotypes or assumptions about an individual.

## Local setup

From the Windows Source folder, double-click Start-RadOnc-MDT.cmd. Use Stop-RadOnc-MDT.cmd to stop the backend and frontend. Ollama remains running. Services bind to localhost.

## Repository hygiene and license

Model weights, runner credentials, local database files, logs, build output, and secrets must remain outside Git. No license is currently specified; do not assume redistribution, modification, or commercial-use permission.
