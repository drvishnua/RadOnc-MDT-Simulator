# Technical Architecture — RadOnc MDT Simulator

## Design goals

- Local-first execution and low recurring cost.
- No paid AI API or cloud GPU dependency.
- One shared Ollama model with 45 role-specific profiles.
- Persist each result immediately and support interrupted-run recovery.
- Keep case snapshots, outputs, and reports auditable.
- Preserve disagreements and label uncertainty.
- Keep the educational/simulation-only boundary explicit.

## Implemented stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React + Vite | Case entry, progress, agent views, four-round controls, Chair report |
| Backend | Python + FastAPI | Validation, orchestration, persistence, report API |
| Local inference | Ollama / qwen3.5:4b | Local structured generation |
| Database | SQLite | Case snapshots, run/round statuses, per-agent outputs |
| Tests | Pytest + TypeScript/Vite build | Schema, orchestration, persistence, and UI validation |

## Four-round execution

1. Round 1 runs all 45 independent roles; no agent sees another's output.
2. Round 2 runs all 45 roles again, each receiving its own Round-1 view and a bounded digest of selected cross-specialty peer positions.
3. Round 3 runs all 45 roles again, each receiving its earlier views and a bounded digest of peer debate contributions; it challenges assumptions, uncertainty, patient/context, feasibility, resources, and governance.
4. Round 4 runs SG-07, the MDT Chair, over compressed digests of all 45 contributions from Rounds 1–3.

The full outputs are preserved in SQLite. The bounded digest is a context-window optimization: every role contributes in each stage, but every role does not receive all 44 full-length peer outputs.

## Model-generation strategy

- Schema-constrained JSON is passed through Ollama's structured-output format field.
- The full schema is not repeated as prompt text.
- Round 1 output cap: 700 tokens; Round 2: 420; Round 3: 420; Round 4: 950.
- The model remains loaded for 30 minutes between agent calls.
- Context remains fixed at 4K until a production-shaped live benchmark validates both speed and structured-output correctness.
- Concurrency remains one. A real two-request test on the connected laptop measured 0.86× throughput versus sequential execution; higher concurrency is therefore not enabled.
- A production-shaped context-size benchmark is still pending.

## Persistence and audit

A run stores:
- Exact serialized synthetic case and SHA-256
- Agent and round statuses
- Independent assessments
- Debate contributions
- Adversarial review contributions
- Final Chair synthesis
- Errors, timestamps, and durations

The JSON export includes the parsed case snapshot, exact serialized case JSON, checksum, all available role outputs, and final report. Local SQLite data is excluded from Git.

## Evidence integration

Evidence retrieval and citation verification are not connected yet. Evidence claims remain disabled. Future adapters may include PubMed, Europe PMC, ClinicalTrials.gov, and official guideline or health-agency repositories, subject to source terms, licensing, provenance, and validation.

## Security and safety boundaries

- Do not expose Ollama to the local network by default.
- Do not put tokens, runner credentials, or secrets in workflows, logs, prompts, or Git.
- Use synthetic cases only.
- Treat retrieved documents and generated text as untrusted content.
- The Chair report is educational synthesis, not a clinical directive; consensus must not be fabricated.
- No real-patient decision support is claimed.
