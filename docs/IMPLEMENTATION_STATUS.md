# Implementation Status

Last updated: 2026-11-05

## Implemented and verified

| Area | Current state | Verification |
|---|---|---|
| Self-hosted runner | Windows laptop connected | GitHub Actions executed on RadOnc-Laptop |
| Local GPU | NVIDIA RTX 4060 detected | nvidia-smi succeeded |
| Ollama | qwen3.5:4b reachable | Local API and inference smoke tests passed |
| GPU inference | Model reported 100% GPU allocation | Ollama processor and GPU diagnostics |
| Product design | Scope and safety boundaries documented | docs/PRODUCT_SPEC.md |
| Agent catalogue | 45 unique role profiles | API count/category tests |
| Backend | FastAPI runtime, catalogue, validation, assessment, and batch-run endpoints | Backend CI: 17 tests passed |
| Single-agent inference | RO-01 generated a structured response | Real synthetic-case local inference passed |
| Independent batch engine | Sequential execution of all 45 profiles | Batch tests cover all 45 IDs |
| Run persistence | SQLite stores run state and each agent result | Batch and resume tests |
| Failure handling | A failed role does not stop the remaining roles | Automated failure-continuation test |
| Resume behavior | Retry failed/interrupted agents while preserving successes | Automated resume test |
| Frontend | React + Vite dashboard with progress, results, retry and export | TypeScript/Vite production build passed |
| Browser recovery | Active run and synthetic case restored after refresh | Implemented in frontend |
| Local source sync | Source copied to project-root Source folder | Required-file sync check passed |
| Local launcher | One-command Windows start/stop | PowerShell parser check passed |

## Current API

- GET /health
- GET /api/runtime
- GET /api/agents
- POST /api/cases/validate
- POST /api/agents/{agent_id}/assess
- POST /api/runs
- GET /api/runs/{run_id}
- GET /api/runs/{run_id}/results
- POST /api/runs/{run_id}/resume

## What the 45-agent feature does

A batch run sends the same synthetic case separately to each of the 45 role profiles, in catalogue order. The generator does not include other agents' outputs in an agent's prompt. Successful assessments are saved immediately in the local SQLite database.

If an agent fails, the remaining agents continue. A retry skips successful agents and retries failed or interrupted ones. The dashboard displays progress and individual results and can export the saved run as JSON.

The full 45-agent batch has been automated-tested with mocked model calls, but has **not yet been run end-to-end against HN-001 in the browser**.

## Current limitations / not implemented yet

- Evidence retrieval adapters and citation provenance verification
- Clinically validated evidence grading or medical accuracy evaluation
- Cross-agent debate, adversarial review, and chair synthesis (rounds 2–4)
- Structured final MDT, evidence, patient-reality, and feasibility/risk reports
- Formal evaluation of oncology accuracy, bias, reproducibility, and safety

The model is instructed not to fabricate sources. Evidence claims remain disabled until traceable retrieval is implemented.

## Local folder layout

The runner and model store remain at the project root. GitHub synchronizes source code into the separate Source subfolder, without deleting or overwriting actions-runner or AI_Models.

Double-click Start-RadOnc-MDT.cmd inside Source to start the local app. Double-click Stop-RadOnc-MDT.cmd to stop the backend and frontend; Ollama is left running.

## Next development sequence

1. Run the 45-agent feature against the synthetic HN-001 case and review its outputs.
2. Improve role prompts and output quality based on the independent assessments.
3. Add traceable evidence retrieval and citation validation.
4. Implement rounds 2–4 with preserved independent views and dissent.
5. Generate structured reports and continue synthetic-case safety evaluation.

## Safety boundary

This is a research/education prototype, not a medical device or clinical decision-support system. Use synthetic cases only. Do not use outputs to make real-patient treatment decisions or replace a qualified MDT.
