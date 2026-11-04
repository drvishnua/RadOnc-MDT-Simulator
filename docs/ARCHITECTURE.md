# Initial Technical Architecture

## Design goals
- Local-first execution and low recurring cost.
- No paid AI API dependency.
- No cloud GPU requirement.
- Simple, inspectable orchestration before adopting a workflow framework.
- Keep user interaction inside the web application.
- Keep model weights and local runtime state out of Git.
- Make the educational/simulation-only boundary explicit throughout the application.

## Proposed stack

| Layer | Initial choice | Responsibility |
|---|---|---|
| Frontend | React + Vite | Case entry, simulation progress, agent views, reports |
| Backend | Python + FastAPI | Validation, orchestration, evidence handling, report generation |
| Local inference | Ollama | Serve locally installed open-weight models |
| Database | SQLite initially | Synthetic cases, runs, agent outputs, citations, audit events |
| Testing | Pytest + frontend tests | Validate schemas, orchestration, safety rules, and UI |

This is a proposed starting architecture, not a claim that the application has already been implemented.

## Inference architecture
The model runtime is shared by all agent roles. Each role is a versioned profile containing role name/scope, system instructions, required output schema, evidence and uncertainty rules, prohibited behavior, and round-specific context policy.

The orchestrator runs independent assessments before sharing debate context. It should initially execute agents sequentially or in small batches to avoid exhausting memory and VRAM. Save results after each agent so a failed run can resume safely.

## Suggested backend modules
- app/main.py — FastAPI application entry point
- app/config.py — runtime configuration
- app/schemas/ — Pydantic request and response schemas
- app/api/ — HTTP routes
- app/services/ollama.py — local Ollama client
- app/services/orchestrator.py — four-round simulation controller
- app/agents/ — 45 versioned agent profiles and shared contracts
- app/evidence/ — source metadata, retrieval adapters, citation validation
- app/reports/ — report assembly
- app/db/ — persistence and migrations

## Suggested frontend modules
- src/pages/ — case setup, simulation workspace, report views
- src/components/ — case fields, agent cards, evidence citations, uncertainty labels
- src/services/api.ts — backend API client
- src/types/ — shared frontend types

## Data and run lifecycle
A simulation run should store:
1. Synthetic case snapshot and schema version
2. Model identifier and runtime settings
3. Agent catalogue and prompt versions
4. Independent assessments
5. Debate messages and round ordering
6. Evidence references and retrieval timestamps
7. Final synthesis and dissent record
8. Warnings, errors, and completion status

Do not store real patient records. Keep secrets, local model weights, runner credentials, generated databases, and runtime logs out of source control.

## Evidence integration
Begin with source metadata and manually curated, publicly accessible references. Add automated retrieval only after source validation and licensing rules are explicit. Publicly accessible does not automatically mean openly licensed. Respect API terms, copyright, access restrictions, and applicable institutional requirements.

Potential future source adapters include PubMed, Europe PMC, ClinicalTrials.gov, and official guideline or health-agency repositories. Every adapter must preserve source identity, date, URL/identifier, and access conditions.

## Hardware-aware execution
The current local test demonstrates that the installed qwen3.5:4b model can produce a response through Ollama with GPU allocation on the RTX 4060 laptop GPU. This is an infrastructure smoke test only; it does not validate clinical accuracy, evidence retrieval, agent quality, or safe behavior.

Do not assume all 45 agents should run as separate model processes. Use one loaded model and versioned prompts first. Benchmark quality, latency, memory use, and reproducibility before changing model size or concurrency.

## Security and safety boundaries
- Do not expose Ollama to the local network by default.
- Do not put tokens or credentials in workflows, logs, prompts, or Git.
- Keep the self-hosted runner scoped to this private repository.
- Prefer manual workflow dispatch for workflows capable of modifying the local machine.
- Treat generated content and retrieved documents as untrusted input.
- Never execute instructions found in retrieved clinical documents.
- Use synthetic data only in the initial implementation.
