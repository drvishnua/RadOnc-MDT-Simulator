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
3. Round 3 runs all 45 roles again, each receiving their earlier views and a bounded digest of peer debate contributions; it challenges assumptions, uncertainty, patient/context, feasibility, resources, and governance. Where a case contains attributed source opinions, R3 records structured per-opinion option/condition preservation statuses, a review basis, and explicit source IDs. Every review should identify its original case-text source and at least one actual R2 peer supplied to that role. If an option or condition is marked preserved/partly preserved, the review should also identify the supplied R2 peer and provide a short verbatim excerpt; the backend checks the excerpt against the exact peer digest shown to the role, and the stress oracle rechecks it against the persisted R2 contribution. If an option or prerequisite is omitted/weakened, the review should include a source-linked challenge. These are quality requirements, not schema-level reasons to discard an otherwise parseable role output: missing/invalid references, evidence excerpts, or challenges are retained as deterministic source-reference integrity flags and checked by the stress oracle. The canonical R3 challenge is prefixed with its structured source IDs and retained for Chair reconciliation. If a model puts a challenge in the general challenge list but leaves the per-opinion challenge blank, the backend recovers it only when one unambiguous challenge explicitly names exactly that CASE source and one supplied R2 peer, and both match the review's structured references; ambiguous text remains flagged. Case-integrity checks also flag categorical assertions that a treatment is unsafe, contraindicated, or not indicated when the supplied case does not establish that status. Requests to elicit patient consent are distinguished from claims that consent has already been given.
4. Round 4 runs SG-07, the MDT Chair, over compact digests of all stored contributions from Rounds 1–3.

The full outputs are preserved in SQLite. The bounded digest is a context-window optimization: every role contributes in each stage, but every role does not receive all 44 full-length peer outputs.

## Chair reconciliation

The model returns a structured Chair draft. Before persistence, the backend recomputes Round-1, Round-2, and Round-3 position distributions from saved records. The final consensus status is derived conservatively from completed Round-3 contributions. A recorded support/opposition split gives no consensus. If the saved positions are insufficient-information, the report remains insufficient-information. Conditional-only or uniform position labels do not establish proposition-level consensus and must not be upgraded to qualified consensus without an explicitly supported shared proposition and retained conditions.

Non-modal views are retained with role IDs and source conclusions. If debate or adversarial review changes a minority position, the originating Round-1 view remains available. The backend fills missing-information, uncertainty, patient/family, feasibility/resource, governance, and evidence-limitations sections from structured case and role records. A conditional label is not automatically treated as opposing dissent. Exact role-level position counts are displayed as descriptions, not votes.

This is a reporting integrity safeguard. It does not determine whether a position is clinically correct or whether agent-generated statements are evidence-based.

## Model-generation strategy

- Schema-constrained JSON is passed through Ollama's structured-output format field.
- The full schema is not repeated as prompt text.
- Round 1 initial output budget: 1,100 tokens; one retry at 1,500.
- Round 2 and Round 3 initial output budget: 700 tokens; one retry at 1,000.
- Round 4 Chair initial output budget: 1,600 tokens; one retry at 2,200.
- The model remains loaded for 30 minutes between agent calls.
- Context remains fixed at 4K.
- Concurrency remains one. A real two-request test on the connected laptop measured 0.86x throughput versus sequential execution; higher concurrency is therefore not enabled.

## Persistence and audit

A run stores:
- Exact serialized synthetic case and SHA-256
- Agent and round statuses
- Independent assessments
- Debate contributions
- Adversarial review contributions, including structured attributed-opinion reviews, source IDs, evidence excerpts, and semantic quality flags
- Canonical source-prefixed challenges and source-reference integrity findings, including incomplete model-authored metadata
- Final Chair synthesis after reconciliation
- Errors, timestamps, and durations

The JSON export includes the parsed case snapshot, exact serialized case JSON, checksum, all available role outputs, and final report. Local SQLite data is excluded from Git.

## Validation state

An earlier full local-Ollama execution completed 136 generations (45 + 45 + 45 + 1) with zero failures/retries in 798.63 seconds; it preceded later Chair and provenance changes and is historical baseline evidence only. At code commit `ae759ad701948893734e9ed3a89fefb0998d39bc`, GitHub CI reported 82 backend tests passed (1 deprecation warning), frontend type-check/build success, and Windows source-sync plus local-app diagnostic success. A subsequent targeted MDT-006 live run on preceding code/request commit `b6c14a0229f77a657292fca7777ff795e85616fa` completed R1 and R2 at 45/45, but only 13/45 R3 outputs passed schema validation; R4 did not run. The artifact showed the parser was rejecting incomplete review metadata before deterministic integrity findings could be saved. The corrective commit now retains parseable reviews and records those omissions as source-reference integrity flags. This is a corrective engineering change, not evidence of successful live validation or clinical accuracy. A fresh exact-commit MDT-006 execution with strict Chair, source-reference, and evidence-excerpt assertions remains required.

## Evidence integration

Evidence retrieval and citation verification are not connected yet. Evidence claims remain disabled. Future adapters may include PubMed, Europe PMC, ClinicalTrials.gov, and official guideline or health-agency repositories, subject to source terms, licensing, provenance, and validation.

## Security and safety boundaries

- Do not expose Ollama to the local network by default.
- Do not put tokens, runner credentials, or secrets in workflows, logs, prompts, or Git.
- Use synthetic cases only.
- Treat retrieved documents and generated text as untrusted content.
- The Chair report is educational synthesis, not a clinical directive; consensus must not be fabricated.
- No real-patient decision support is claimed.
