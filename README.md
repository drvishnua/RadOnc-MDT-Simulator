# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Status: Backend foundation implemented; simulation engine and frontend are not yet implemented.** The product specification, 45-agent catalogue, initial architecture, local runner, Ollama integration check, strict synthetic-case API, and backend test workflow are in place.

## Purpose

The initial release will focus on **synthetic head-and-neck cancer cases**. It is designed to help trainees and educators explore how different clinical specialties, patient perspectives, evidence quality, resources, feasibility, ethics, and uncertainty shape an MDT discussion.

The simulator is intended to preserve independent opinions, meaningful disagreement, evidence limitations, and missing information rather than forcing artificial consensus.

## Core design

- **45 configured perspectives** spanning radiation oncology, medical oncology, surgical oncology, diagnostic/supportive specialties, patient lenses, evidence, resources, feasibility, governance, and safeguarding.
- **Four simulation rounds:** independent assessments, MDT discussion, adversarial review, and chair synthesis.
- **Evidence-aware outputs:** explicit distinction between established standard-of-care, emerging evidence, and investigational approaches.
- **Structured reports:** simulated MDT discussion, evidence and uncertainty, patient reality, and feasibility/risk review.
- **Local-first inference:** one shared local model with versioned agent profiles; no separate model process for every agent is required.

See:
- [Product specification](docs/PRODUCT_SPEC.md)
- [45-agent catalogue](docs/AGENT_CATALOGUE.md)
- [Initial technical architecture](docs/ARCHITECTURE.md)
- [Backend setup and endpoints](backend/README.md)

## Current implementation

The initial FastAPI backend is available under the backend directory:

- GET /health — application health and educational-only mode.
- GET /api/runtime — read-only Ollama reachability and installed-model status.
- POST /api/cases/validate — strict synthetic-case schema validation only.

The API rejects unapproved extra case fields, uses no patient-name or medical-record-number fields, and returns warnings for missing scenario details. This is schema validation, not clinical validation.

The four-round orchestrator, evidence retrieval, agent execution, report generation, database persistence, and React interface remain future work.

## Current technical direction

| Layer | Technology | Status |
|---|---|---|
| Frontend | React + Vite | Planned |
| Backend | Python + FastAPI | Foundation implemented |
| Local model runtime | Ollama | Connected and smoke-tested |
| Initial database | SQLite | Planned |
| Backend tests | Pytest | Five tests passing |

## Infrastructure and test validation

The GitHub self-hosted Windows runner has successfully executed jobs on the development laptop. A local Ollama smoke test verified:

- Ollama API reachable
- Installed model: qwen3.5:4b
- Test prompt returned: RADONC_LOCAL_INFERENCE_OK
- Ollama reported the model allocated **100% to GPU** on the NVIDIA RTX 4060

The backend CI workflow installed dependencies on the laptop and completed **5 tests successfully** using the laptop's existing Python 3.14 installation.

These checks validate infrastructure, basic API behavior, and schema rules only. They do **not** validate oncology knowledge, evidence retrieval, agent quality, or clinical safety.

## Safety and data boundaries

This project is for **research and education only**.

- It is not a medical device or a clinically validated decision-support system.
- Do not use outputs as diagnosis, prescriptions, radiotherapy dose instructions, treatment plans, or as a substitute for a qualified MDT.
- Use synthetic data only in the initial release. Do not enter identifiable patient information.
- AI-generated content may be incomplete or inaccurate. Material clinical claims must be supported by traceable sources and critically reviewed.
- Economic, policy, and medico-legal perspectives are issue-spotting aids, not professional advice.
- Patient personas are discussion lenses, not demographic stereotypes or facts about an individual.

## Development roadmap

1. Define agent output, evidence citation, and report schemas.
2. Implement versioned profiles for all 45 agents.
3. Implement resumable four-round orchestration with preserved independent assessments and dissent.
4. Add evidence-source adapters and citation validation.
5. Add structured report generation and auditability.
6. Build the React interface and local setup workflow.
7. Evaluate reliability, reproducibility, bias, evidence handling, and safety using synthetic cases.

## Repository hygiene

Local runner credentials and working files, model weights, environment files, local databases, logs, and build artifacts are excluded through the .gitignore file. Never commit registration tokens, API keys, private case data, or model files.

## License

No license is currently specified. Until a license is added, no permissions for redistribution, modification, or commercial use should be assumed.
