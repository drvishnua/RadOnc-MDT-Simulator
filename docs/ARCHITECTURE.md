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

## Case-data entry and preservation

The frontend exposes every structured field supported by the backend schema: age, sex at birth, primary site, histology, clinical T/N/M stage, stage group, performance status, pathology and imaging summaries, comorbidities, prior treatment, patient goals, social context, resource context, and known unknowns. Additional structured fields are grouped in an optional expandable section. Legacy browser-saved cases are restored with newly introduced fields left unknown/empty. The original free-text case summary is preserved verbatim; the application does not silently reconcile conflicts between narrative and structured fields. Blank fields mean not reported, not negative.

## Four-round execution

1. Round 1 runs all 45 independent roles; no agent sees another's output.
2. Round 2 runs all 45 roles again, each receiving its own Round-1 view and a bounded digest of selected cross-specialty peer positions.
3. Round 3 runs all 45 roles again, each receiving their earlier views and a bounded digest of peer debate contributions; it challenges assumptions, uncertainty, patient/context, feasibility, resources, and governance. Where a case contains attributed source opinions, R3 records structured per-opinion option/condition preservation statuses, a review basis, and explicit source IDs. Every review should identify its original case-text source and at least one actual R2 peer supplied to that role. If an option or condition is marked preserved/partly preserved, the review should also identify the supplied R2 peer and provide a short verbatim excerpt; the backend checks the excerpt against the exact peer digest shown to the role, and the stress oracle rechecks it against the persisted R2 contribution. If an option or prerequisite is omitted/weakened, the review should include a source-linked challenge. These are quality requirements, not schema-level reasons to discard an otherwise parseable role output: missing/invalid references, evidence excerpts, or challenges are retained as deterministic source-reference integrity flags and checked by the stress oracle. The canonical R3 challenge is prefixed with its structured source IDs and retained for Chair reconciliation. Round-qualified citations are audited recursively, and role ranges are rejected rather than interpreted as individual source IDs. When constructing the R3 prompt, round-qualified IDs embedded in an R2 contribution are neutralized and attributed to that R2 peer; the original saved R2 text is not modified. The prompt itself uses no source-shaped role-range example that a model could copy into its output. If a model puts a challenge in the general challenge list but leaves the per-opinion challenge blank, the backend recovers it only when one unambiguous challenge explicitly names exactly that CASE source and one supplied R2 peer, and both match the review's structured references; ambiguous text remains flagged. Case-integrity checks also flag categorical assertions that a treatment is unsafe, contraindicated, or not indicated when the supplied case does not establish that status. Requests to elicit patient consent are distinguished from claims that consent has already been given.
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

Validation results must be interpreted in layers: workflow execution, saved-output integrity, semantic/model-quality gates, clinical accuracy, and target-device GPU performance are different claims.

- **Current CI, exact development SHA `35f32d1`:** backend 202 tests passed (one existing Starlette/httpx TestClient deprecation warning); frontend 32 tests, TypeScript and production build passed; isolated headless-Edge patient-registry and saved four-round dashboard E2E passed; Gitleaks, CodeQL Python/JavaScript, pip-audit and npm audit passed; packaging prerequisites passed.
- **Installer on `35f32d1`:** package build, install/uninstall smoke test, app health, frontend, 45-role API and preservation of the user database passed. The separate clean-host first-run provisioning and six-call R2/R3 provenance job is still running. A prior build on `c6499e7` independently passed Ollama 0.40.14 provisioning, qwen3.5:4b download/tag verification, real CPU inference and installed-app health, but failed the targeted model-provenance gate below.
- **Targeted R2/R3 quality gate on `c6499e7`:** three roles, three R2 calls and three R3 calls; no R1 or Chair and no saved MDT/patient record. All R2 outputs had no integrity flags. Five of six R3 opinion reviews had verified exact peer evidence. One SO-02 review paired a verbatim excerpt from supplied R2:RO-01 with model-selected peer ID R2:MO-01. Because the excerpt did not belong to the named peer, the backend rejected the pair, downgraded the review to `unclear`, preserved the model-reported labels and recorded integrity findings. This is a genuine provenance failure; the validator was not relaxed. A repeat on `35f32d1` is in progress.
- **Historical full hosted CPU run on `aaf8fb9`:** all 136 expected records (45 R1, 45 R2, 45 R3, 1 Chair) were saved, with each round completed and no failed agents/retries. The script reported `passed_structural_live_validation`, which is not a semantic/model-quality pass: saved outputs contained 26 R1 case-integrity flags across 21 roles, 44 R2 source-reference findings across 42 roles and 108 R3 source-reference findings across 38 roles. Chair reconciliation remained `insufficient_information` with no consensus points. CPU-only; GPU was not measured. The audit artefact contained JSON and SQLite but no execution manifest.
- **Full-run manifest correction on `35f32d1`:** the missing closing brace around the model-presence check had placed digest/manifest generation inside the 'model missing' branch, so a successful already-present model skipped manifest creation. The branch now closes before manifest generation; the workflow reads back and checks the manifest source SHA, model digest and size, and missing JSON/SQLite/manifest artefacts fail upload. Two backend regression tests cover this. The full-run workflow was skipped on `35f32d1` because the explicit run marker was not supplied; no new 136-role run was started.
- **R3 false-omission guard on `c6499e7`:** when a server-verified exact R2 quote contains sufficient source-specific option/condition wording, a conflicting `omitted`/`partly_preserved` label is downgraded to `unclear`. Original model labels remain available for audit. This does not upgrade to preserved or manufacture a challenge.
- **Target laptop/GPU:** current source mirror, current local browser/runtime and active inference telemetry on the RTX 4060 have not been reverified at the current head. Historical one-agent GPU observations must not be represented as current full-run performance. Concurrency remains 1.
- **Clinical/evidence boundary:** evidence retrieval and claim-to-source verification are not connected. No guideline concordance, clinical accuracy, or qualified clinical validation is claimed.

A full four-round run should only be requested after the targeted provenance failure has been resolved or formally accepted as a known limitation, the current exact commit and model digest are pinned, and a separate explicit validation request is recorded.

## Evidence integration

Evidence retrieval and citation verification are not connected yet. Evidence claims remain disabled. Future adapters may include PubMed, Europe PMC, ClinicalTrials.gov, and official guideline or health-agency repositories, subject to source terms, licensing, provenance, and validation.

## Security and safety boundaries

- Do not expose Ollama to the local network by default.
- Do not put tokens, runner credentials, or secrets in workflows, logs, prompts, or Git.
- Use synthetic cases only.
- Treat retrieved documents and generated text as untrusted content.
- The Chair report is educational synthesis, not a clinical directive; consensus must not be fabricated.
- No real-patient decision support is claimed.
