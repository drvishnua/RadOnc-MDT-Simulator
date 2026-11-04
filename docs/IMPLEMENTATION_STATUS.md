# Implementation Status

Last updated: 2026-11-05

## Implemented in the development branch

| Area | State | Verification |
|---|---|---|
| Local environment | Windows self-hosted runner connected | GitHub Actions runs on RadOnc-Laptop |
| Ollama | qwen3.5:4b reachable | Local inference smoke test |
| Agent catalogue | 45 unique roles | Catalogue tests |
| Round 1 | 45 independent assessments with required position, provisional conclusion, and preferred educational option | Batch/resume tests; prior browser run exercised this stage |
| Round 2 | All 45 roles generate debate contributions from bounded peer digests | Four-round mocked orchestration test |
| Round 3 | All 45 roles generate adversarial review contributions | Four-round mocked orchestration test |
| Round 4 | SG-07 generates structured Chair synthesis with consensus status and explicit conclusion | Four-round mocked orchestration test |
| Persistence | SQLite stores case snapshot, case hash, per-agent outputs and round statuses | Persistence and endpoint tests |
| Export | JSON export includes exact stored case JSON, checksum, R1–R3 outputs and final report | Case snapshot/checksum test |
| Recovery | Failed/interrupted agents can be resumed without rerunning successes | Batch and round resume tests |
| Frontend | Round controls, progress, per-role results and Chair report view | TypeScript/Vite build |
| Prompt size | JSON Schema passed via Ollama structured-output format; duplicated schema removed from prompt text | Code review and CI |
| Concurrency | Default remains 1 | Two-request laptop benchmark: 0.86× versus sequential |
| Context | Fixed 4K for reliable structured output | 2K optimization deferred; live structured-output benchmark did not return valid JSON |

## Current API

- GET /health
- GET /api/runtime
- GET /api/agents
- POST /api/cases/validate
- POST /api/agents/{agent_id}/assess
- POST /api/runs
- GET /api/runs/{run_id}
- GET /api/runs/{run_id}/case
- GET /api/runs/{run_id}/results
- POST /api/runs/{run_id}/resume
- POST /api/runs/{run_id}/rounds/{2|3|4}
- GET /api/runs/{run_id}/rounds/{round_number}
- GET /api/runs/{run_id}/rounds/{round_number}/results
- POST /api/runs/{run_id}/rounds/{round_number}/resume
- GET /api/runs/{run_id}/report

## Four-round behavior

Round 1 sends the same saved synthetic case separately to all 45 roles. Each role receives only its own profile and the case. Round 2 asks all 45 roles to compare their independent position with a compact selection of peer perspectives. Round 3 asks all 45 roles to challenge assumptions, uncertainty, patient/context, feasibility, resource, and governance issues. Round 4 runs SG-07 as Chair over compact digests of all stored results.

All outputs are persisted by role and round. A single malformed structured response receives one automatic retry. A failed or interrupted stage can be resumed, retaining completed outputs. The Chair report distinguishes consensus status from each agent's individual support/opposition position and preserves dissent.

## Runtime optimization

- Two-at-once inference was measured on the laptop and produced 0.86× the throughput of sequential execution. The project therefore keeps RADONC_AGENT_CONCURRENCY=1.
- Ollama structured-output schema is passed in the API format field, avoiding repeated schema text in every prompt.
- Context remains fixed at 4K. A 2K optimization is deferred because the live structured-output benchmark did not return valid JSON.
- R1 output cap is 700 tokens; Round 2 and 3 caps are 420 each; Round 4 cap is 950.

## Not implemented / not validated yet

- Evidence source retrieval adapters and citation provenance verification
- Clinically validated evidence grading or accuracy evaluation
- Clinical validation by a qualified MDT
- Full live end-to-end four-round run on a synthetic case (round tests use mocked generation)
- Formal bias, reproducibility, and safety evaluation

No evidence claim should be presented as source-verified. Use synthetic cases only.

## Local folder layout

Source contains synchronized code. The project-root actions-runner and AI_Models folders remain separate and excluded from source sync. Run Start-RadOnc-MDT.cmd and Stop-RadOnc-MDT.cmd from Source.

## Safety

Research/education prototype only. Not a medical device or clinical decision-support system. Do not use outputs for real-patient treatment decisions or as a substitute for a qualified MDT.
