# RadOnc MDT Simulator

A local-first, AI-assisted educational simulator for multidisciplinary oncology case discussions.

> **Status: Planning and infrastructure validation.** The product specification, 45-agent catalogue, initial architecture, repository safeguards, and local runner diagnostics are in place. The clinical simulation application itself has not yet been implemented or clinically validated.

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

## Current technical direction

| Layer | Planned technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Local model runtime | Ollama |
| Initial database | SQLite |
| Tests | Pytest and frontend tests |

These are the selected starting technologies, not a claim that the application stack is already implemented.

## Infrastructure validation

The GitHub self-hosted Windows runner has successfully executed jobs on the development laptop. A local Ollama smoke test verified:

- Ollama API reachable
- Installed model: qwen3.5:4b
- Test prompt returned: RADONC_LOCAL_INFERENCE_OK
- Ollama reported the model allocated **100% to GPU** on the NVIDIA RTX 4060

This confirms local execution and GPU allocation only. It does **not** validate oncology knowledge, evidence retrieval, agent quality, or clinical safety.

## Safety and data boundaries

This project is for **research and education only**.

- It is not a medical device or a clinically validated decision-support system.
- Do not use outputs as diagnosis, prescriptions, radiotherapy dose instructions, treatment plans, or as a substitute for a qualified MDT.
- Use synthetic data only in the initial release. Do not enter identifiable patient information.
- AI-generated content may be incomplete or inaccurate. Material clinical claims must be supported by traceable sources and critically reviewed.
- Economic, policy, and medico-legal perspectives are issue-spotting aids, not professional advice.
- Patient personas are discussion lenses, not demographic stereotypes or facts about an individual.

## Development roadmap

1. Define case, agent, evidence, and report schemas.
2. Implement the local Ollama client and test its response handling.
3. Implement resumable four-round orchestration for all 45 agent profiles.
4. Add evidence-source metadata and citation validation.
5. Add structured reporting and auditability.
6. Build the React interface and local setup workflow.
7. Evaluate reliability, reproducibility, bias, evidence handling, and safety using synthetic cases.

## Repository hygiene

Local runner credentials and working files, model weights, environment files, local databases, logs, and build artifacts are excluded through the .gitignore file. Never commit registration tokens, API keys, private case data, or model files.

## License

No license is currently specified. Until a license is added, no permissions for redistribution, modification, or commercial use should be assumed.
