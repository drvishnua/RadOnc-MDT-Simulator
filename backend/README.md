# Backend

Initial FastAPI foundation for the RadOnc MDT Simulator.

## Requirements

- Python 3.11 or newer
- Ollama installed locally for the optional runtime status endpoint

## Setup (Windows PowerShell)

From the repository root:

    cd backend
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

## Run the API

    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

Open the local API documentation at http://127.0.0.1:8000/docs.

## Test

    pytest

## Current endpoints

- GET /health — application health and educational-only mode
- GET /api/runtime — read-only Ollama reachability and installed-model status
- GET /api/agents — catalogue of all 45 required role profiles
- POST /api/cases/validate — strict synthetic-case schema validation only

The agent endpoint returns role metadata; the actual agent execution and four-round orchestrator are not implemented yet. Case validation is not clinical validation. Use synthetic cases only.
