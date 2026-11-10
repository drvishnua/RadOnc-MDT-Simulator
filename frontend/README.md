# Frontend

React + Vite browser interface for the local RadOnc MDT Simulator backend.

## Requirements

- Node.js 20.19+ or 22.12+
- Backend at http://127.0.0.1:8000
- Local Ollama service for model generation

## Setup

From the repository root:

    cd frontend
    npm ci
    npm run dev

Open http://127.0.0.1:5173.

## Capabilities

- Shows backend, Ollama, local model, and 45-role catalogue status.
- Validates the structure of a training case.
- Runs one RO-01 test assessment or the full 45-role Round 1 batch.
- Displays each agent's required position, provisional conclusion, preferred educational option, discussion topics, unknowns, and evidence gaps.
- Runs Round 2 debate and Round 3 adversarial review across all 45 roles, with independent progress and results.
- Runs Round 4 Chair synthesis and displays a distinct consensus status and Chair conclusion plus consensus, dissent, uncertainty, missing information, patient/context, feasibility, governance, and evidence-limitations sections.
- Retries failed/interrupted roles without rerunning successful roles.
- Restores the run and case after browser refresh.
- Exports available rounds and final report as JSON with the exact saved case JSON and SHA-256 checksum.

The export is the audit record for an educational simulation. It records the case supplied to the model and the outputs saved by the backend.

## Important limitations

- Evidence retrieval and citation verification are not implemented; evidence claims remain disabled.
- Round 2 passes a compact selected peer digest to each role to bound prompt size; it does not pass all 44 full-length peer outputs into every prompt.
- Automated tests use mocked model calls for orchestration. A full four-round run of 45 live local model calls per stage has not yet been completed end-to-end.

Fictional educational cases only. This is not clinical decision support or a substitute for a qualified MDT.
