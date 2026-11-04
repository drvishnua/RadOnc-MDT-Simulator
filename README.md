# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Status: 45-agent independent assessment workflow implemented and CI-tested.** The first four-round MDT debate, evidence retrieval, and final report synthesis are not implemented yet.

## Purpose

The initial release focuses on **synthetic head-and-neck cancer cases**. It helps trainees and educators explore how clinical specialties, patient perspectives, evidence quality, resources, feasibility, ethics, and uncertainty shape an MDT discussion.

The simulator is designed to preserve independent opinions, meaningful disagreement, evidence limitations, and missing information rather than forcing artificial consensus.

## Core design

- **45 configured perspectives** spanning radiation oncology, medical oncology, surgical oncology, diagnostic/supportive specialties, patient lenses, evidence, resources, feasibility, governance, and safeguarding.
- **Independent first-round assessments:** every agent receives the same synthetic case and only its own role profile; no other agent's assessment is passed into its prompt.
- **Four simulation rounds planned:** independent assessments, MDT discussion, adversarial review, and chair synthesis.
- **Evidence-aware outputs planned:** distinguish established standard-of-care, emerging evidence, and investigational approaches.
- **Local-first inference:** one shared Ollama model with role-specific profiles; no separate model process for every agent is required.

See:
- [Product specification](docs/PRODUCT_SPEC.md)
- [45-agent catalogue](docs/AGENT_CATALOGUE.md)
- [Initial technical architecture](docs/ARCHITECTURE.md)
- [Backend setup and endpoints](backend/README.md)
- [Frontend setup and capabilities](frontend/README.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)

## Current implementation

### Backend API

- GET /health — application health and education-only mode.
- GET /api/runtime — local Ollama reachability and installed-model status.
- GET /api/agents — all 45 role profiles.
- POST /api/cases/validate — strict synthetic-case schema validation.
- POST /api/agents/{agent_id}/assess — one local, schema-validated agent assessment.
- POST /api/runs — queue a sequential run of all 45 independent assessments.
- GET /api/runs/{run_id} — progress and run status.
- GET /api/runs/{run_id}/results — saved per-agent results.
- POST /api/runs/{run_id}/resume — retry failed or interrupted agents while retaining completed results.

### 45-agent batch workflow

The browser dashboard now provides:
- A **Run all 45 agents** button after case validation.
- Sequential local Ollama execution.
- Live progress, completed/failed/remaining counts, and current agent ID.
- Per-agent expandable results.
- Continuation when an individual agent fails.
- Retry of failed agents without rerunning successful ones.
- JSON export of saved independent assessments.
- Browser refresh recovery for the active run and synthetic case.

Run records and agent results are stored locally in SQLite under the backend data folder. The model is kept loaded during a batch to reduce repeated loading. Execution is sequential to avoid competing model calls on the laptop GPU.

The batch API and resume behavior are covered by automated tests. **The complete 45-agent batch has not yet been run against a real case in the browser.**

## Current technical direction

| Layer | Technology | Status |
|---|---|---|
| Frontend | React + Vite | Dashboard and batch controls implemented |
| Backend | Python + FastAPI | Implemented |
| Local model runtime | Ollama / qwen3.5:4b | Connected; local inference verified |
| Initial database | SQLite | Batch-run persistence implemented |
| Backend tests | Pytest | 17 tests passing |
| Frontend build | TypeScript + Vite | Production build passing |

## Evidence boundary

Evidence retrieval and citation verification are **not connected yet**. The model is instructed not to invent references, and the server rejects evidence claims until a traceable retrieval source is integrated. The absence of citations must not be mistaken for verified clinical evidence.

## Safety and data boundaries

This project is for **research and education only**.

- It is not a medical device or a clinically validated decision-support system.
- Do not use outputs as diagnosis, prescriptions, radiotherapy dose instructions, treatment plans, or as a substitute for a qualified MDT.
- Use synthetic cases only. Do not enter identifiable patient information.
- AI-generated content may be incomplete or inaccurate. Material clinical claims require traceable sources and critical review.
- Economic, policy, and medico-legal perspectives are issue-spotting aids, not professional advice.
- Patient personas are discussion lenses, not demographic stereotypes or facts about an individual.

## Development roadmap

1. Run and evaluate all 45 independent perspectives on a synthetic case.
2. Improve and version the agent prompts and output quality.
3. Add evidence-source adapters and citation provenance validation.
4. Implement the four-round debate, adversarial review, and chair synthesis while preserving dissent.
5. Add structured MDT, evidence, patient-reality, and feasibility/risk reports.
6. Evaluate reliability, reproducibility, bias, and safety using synthetic test suites and clinician review.

## Local setup

Use the Windows source folder and double-click Start-RadOnc-MDT.cmd. Stop the backend and frontend with Stop-RadOnc-MDT.cmd. The services bind to localhost only.

## Repository hygiene

Local runner credentials, model weights, environment files, local databases, logs, and build artifacts are excluded through .gitignore. Never commit registration tokens, API keys, real patient information, or model files.

## License

No license is currently specified. Until a license is added, no permissions for redistribution, modification, or commercial use should be assumed.
