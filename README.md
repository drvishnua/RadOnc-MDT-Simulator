# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Current milestone:** The development branch implements 45 independent assessments, 45-agent debate, 45-agent adversarial review, and SG-07 Chair synthesis. An earlier full local-model run completed all 136 generations. The newer Chair reconciliation logic is covered by backend regression tests; a fresh live-model validation is pending.

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

Live run 41941583054 completed all 136 generations with zero failures or retries in 798.63 seconds. This run predates the new Chair reconciliation logic. The backend suite passed 26 tests on the reconciled code, and backend/frontend CI checks passed on commit 1daa89eda17f7b09e028a1aa5fc981a6c3879187. A fresh live run is still required to validate the reconciled Chair against the local model.

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
