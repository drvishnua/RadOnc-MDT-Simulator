# Frontend

React + Vite browser interface for the local RadOnc MDT Simulator backend.

## Requirements

- Node.js 20.19+ or 22.12+
- Backend running at http://127.0.0.1:8000

## Setup

From the repository root:

    cd frontend
    npm install
    npm run dev

Open http://127.0.0.1:5173.

The frontend calls the local FastAPI backend. The API CORS allowlist is restricted to localhost Vite development and preview origins.

## Current capabilities

- Shows backend and Ollama connection status.
- Loads and filters the 45-role catalogue.
- Submits a synthetic case to the schema validation endpoint.

The full four-round MDT simulation, agent execution, evidence retrieval, and report generation are not implemented yet.
