# Implementation Status

Last updated: 2026-11-05

## Implemented in the development branch

| Area | State | Verification |
|---|---|---|
| Local environment | Windows self-hosted runner connected to local Ollama/GPU | Live GitHub Actions execution on RadOnc-Laptop |
| Ollama | qwen3.5:4b reachable locally | Live preflight and inference |
| Agent catalogue | 45 unique roles | Catalogue tests |
| Round 1 | 45 independent assessments with position, provisional conclusion, and preferred educational option or reason none can be preferred | Batch/resume tests and earlier live run |
| Round 2 | All 45 roles generate debate contributions from bounded peer digests | Orchestration tests and earlier live run |
| Round 3 | All 45 roles generate adversarial reviews | Orchestration tests and earlier live run |
| Round 4 | SG-07 Chair synthesis reconciled against saved position counts and role records | 2 regression tests; fresh live validation pending |
| Persistence | SQLite stores case snapshot, checksum, per-role outputs and statuses | Persistence and endpoint tests |
| Export | JSON export includes exact case JSON, checksum, outputs and report | Case snapshot/checksum test |
| Recovery | Failed/interrupted roles resume without rerunning completed roles | Batch and round resume tests |
| Frontend | Round controls, progress, per-role results and Chair report | TypeScript/Vite build and launcher checks |
| Concurrency | Default remains 1 | Laptop benchmark: two-at-once throughput was 0.86x sequential |

## Four-round behavior

Round 1 sends the saved synthetic case separately to all 45 roles. Each role receives only its own profile and the case. Round 2 asks all 45 roles to compare their independent view with selected peer perspectives. Round 3 asks all 45 roles to challenge assumptions, uncertainty, missing information, patient/context, feasibility, resource and governance issues. Round 4 runs SG-07 as Chair over compact digests of all stored results.

All outputs are persisted by role and round. A malformed structured response receives one retry with a larger output budget. Failed or interrupted work can be resumed while retaining completed outputs.

The Chair produces a structured draft, then the backend reconciles its report against saved Round-1, Round-2 and Round-3 records. It recomputes exact position distributions, derives consensus status conservatively, preserves non-modal views with source conclusions, and fills uncertainty, missing-information, patient/family, feasibility, governance and evidence-limitations sections from structured case and role data. Conditional positions are not automatically treated as opposition. This reporting safeguard is not clinical validation.

## Output budgets and runtime

- Round 1: 1,100-token initial budget; one retry at 1,500.
- Rounds 2 and 3: 700-token initial budget; one retry at 1,000.
- Round 4 Chair: 1,600-token initial budget; one retry at 2,200.
- Ollama context remains fixed at 4K.
- RADONC_AGENT_CONCURRENCY remains 1 because two simultaneous generations were slower than sequential execution on the target laptop.

## Validation record

- Live run 41941583054 on commit 4446065b53b67907861493269ea16aaed81aef7a completed 45 + 45 + 45 + 1 generations (136 total), zero failures/retries, in 798.63 seconds. This run preceded the new Chair reconciliation logic.
- Backend regression suite: 26 passed on the reconciled code/test revision.
- Backend and frontend CI checks passed on commit 1daa89eda17f7b09e028a1aa5fc981a6c3879187.
- A new live run on the local Windows/Ollama runner is exercising the reconciliation code. A stricter run also checks exact Chair counts and required sections; those live checks are not yet confirmed complete.

## Not implemented / not validated

- Evidence retrieval adapters and citation provenance verification
- Clinically validated evidence grading or accuracy evaluation
- Validation by a qualified clinical MDT
- Formal bias, reproducibility and safety evaluation
- Real-patient use

No evidence claim should be presented as source-verified. Use synthetic cases only.

## Safety

Research/education prototype only. Not a medical device or clinical decision-support system. Do not use outputs for real-patient treatment decisions or as a substitute for a qualified MDT.
