# Backend

FastAPI backend for the local RadOnc MDT Simulator.

## Requirements

- Python 3.11 or newer
- Ollama installed locally
- Configured local model (default: qwen3.5:4b)

## Setup

From the repository root in PowerShell:

    cd backend
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

Run:

    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

API docs: http://127.0.0.1:8000/docs

Tests:

    pytest

## Endpoints

- GET /health — application mode and health
- GET /api/runtime — Ollama reachability and installed model
- GET /api/agents — all 45 role profiles
- POST /api/cases/validate — synthetic case schema validation
- POST /api/agents/{agent_id}/assess — one Round-1 assessment
- POST /api/runs — create and start a Round-1 batch
- GET /api/runs/{run_id} — Round-1 progress
- GET /api/runs/{run_id}/case — exact saved case object, serialized JSON, and SHA-256 checksum
- GET /api/runs/{run_id}/results — Round-1 results
- POST /api/runs/{run_id}/resume — retry failed/interrupted Round-1 agents
- POST /api/runs/{run_id}/rounds/{round_number} — start Round 2, 3, or 4 when prerequisites are complete
- GET /api/runs/{run_id}/rounds/{round_number} — round progress
- GET /api/runs/{run_id}/rounds/{round_number}/results — per-role round contributions
- POST /api/runs/{run_id}/rounds/{round_number}/resume — resume failed/interrupted round work
- GET /api/runs/{run_id}/report — final Chair report (available after Round 4)

## Round execution

- Rounds 1–3 execute all 45 configured roles separately.
- Each role's Round-1 assessment is isolated from other roles' outputs.
- Round 2 supplies a bounded cross-specialty digest of selected peer positions, not every full peer response, to keep the local context size controlled.
- Round 3 supplies the agent's earlier positions plus a bounded digest of peer debate contributions.
- Round 4 runs SG-07, the MDT Chair, over compressed digests of all stored Round-1, Round-2, and Round-3 outputs.
- Each result is persisted immediately in SQLite. A failed role does not stop the remaining roles.
- Malformed structured output is retried once for that role. Failed/interrupted work can be resumed without rerunning completed roles.
- A shared execution lock prevents overlapping model-generation stages.

## Runtime and performance

RADONC_AGENT_CONCURRENCY is bounded to 1 or 2 and defaults to 1. The live two-request benchmark on the connected RTX 4060 laptop measured 0.86× throughput compared with sequential execution; therefore the default remains 1. Do not raise it without a new measured improvement.

Prompts pass JSON Schema through Ollama's structured-output format field instead of duplicating the full schema in prompt text. Context remains fixed at 4K; a 2K setting will only be enabled after a reliable live structured-output benchmark.

## Persistence

SQLite database: backend/data/simulation_runs.sqlite3. It stores the case snapshot, hash, round status, and individual outputs. The local database is excluded from Git. Do not delete it while work is active or before exporting results.

## Evidence and safety

No evidence retrieval or citation verification is connected. Evidence claims are disabled; do not interpret model-generated text as sourced clinical evidence. Use synthetic cases only. The application is for research/education, not patient-care decisions.
