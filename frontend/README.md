# Frontend

React + Vite browser interface for the local RadOnc MDT Simulator backend.

## Requirements

- Node.js 20.19+ or 22.12+
- Backend running at http://127.0.0.1:8000
- Ollama running locally for agent inference

## Setup

From the repository root:

    cd frontend
    npm install
    npm run dev

Open http://127.0.0.1:5173.

The frontend calls the local FastAPI backend. The API CORS allowlist is restricted to localhost Vite development and preview origins.

## Current capabilities

- Shows backend, Ollama, and installed-model status.
- Loads and filters the 45-role catalogue.
- Validates synthetic case structure.
- Runs a single RO-01 assessment using local Ollama.
- Runs all 45 independent assessments sequentially.
- Polls and displays live progress and per-agent statuses.
- Expands completed agent assessments and shows individual errors.
- Retries failed agents and exports results as JSON.
- Persists the active run ID and validated synthetic case in browser storage so a refresh can restore progress and results.

The 45-agent workflow is an independent first-round assessment stage. It does not yet run cross-agent debate, adversarial review, evidence retrieval, consensus, or final MDT report generation.

Use synthetic cases only. Evidence claims remain disabled until source retrieval and citation validation are implemented.
