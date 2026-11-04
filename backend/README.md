# Backend

FastAPI backend for the local RadOnc MDT Simulator.

## Requirements

- Python 3.11 or newer
- Ollama installed locally for agent inference

## Setup (Windows PowerShell)

From the repository root:

    cd backend
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

## Run the API

    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

Open the API documentation at http://127.0.0.1:8000/docs.

## Test

    pytest

## Endpoints

- GET /health — application health and education-only mode
- GET /api/runtime — read-only Ollama reachability and installed-model status
- GET /api/agents — catalogue of all 45 role profiles
- POST /api/cases/validate — strict synthetic-case schema validation
- POST /api/agents/{agent_id}/assess — one local model-generated educational assessment
- POST /api/runs — queue all 45 independent first-round assessments
- GET /api/runs/{run_id} — persisted progress, counts, and current agent
- GET /api/runs/{run_id}/results — saved agent results and errors
- POST /api/runs/{run_id}/resume — retry failed or interrupted assessments

## Batch-run behavior

- Runs all 45 profiles sequentially against the same synthetic case.
- Every agent receives only the original case and its own role profile. Other agents' outputs are not included in its prompt.
- Saves each completed result to SQLite immediately.
- Continues to the next agent if an individual assessment fails.
- A retry skips completed agents and retries failed/interrupted ones.
- Only one batch is actively executed at a time by the local backend.

The default local database is backend/data/simulation_runs.sqlite3. It is excluded from Git. Do not delete this file while a run is active or before exporting results.

## Evidence boundary and safety

The initial agent generator does not retrieve external evidence. Evidence claims are deliberately disallowed until a traceable retrieval layer is connected, so model-generated citations cannot be mistaken for verified sources.

Use synthetic cases only. Extra identifying case fields such as patient_name are rejected by the schema. The simulator is not clinical validation or treatment advice; it must not be used for real-patient decisions.
