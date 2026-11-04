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
- GET /api/agents — catalogue of all 45 required role profiles
- POST /api/cases/validate — strict synthetic-case schema validation only
- POST /api/agents/{agent_id}/assess — one local model-generated educational assessment

The single-agent endpoint is an initial prototype. It does not run the full MDT and does not retrieve evidence. Evidence claims are deliberately rejected until a traceable retrieval subsystem is connected. It is not clinical validation or treatment advice.

Use synthetic cases only. Requests with extra identifying fields such as patient_name are rejected by the schema.
