# Engineering Quality Standard — AI-Assisted Development

**Status:** Active engineering policy  
**Applies to:** Backend, frontend, model prompts/schemas, database, installer, CI/CD, documentation and release artefacts  
**Initial repository baseline:** `feature/four-round-mdt-and-performance` at `5016e5b8270770748d9db9f85600821d723b3b2f`  
**Baseline date:** 11 November 2026

## 1. Purpose and assurance boundary

This project uses AI assistance, but AI-generated code is treated as untrusted proposed code. A plausible explanation, successful compile, passing happy-path test, large test count or successful installer build is not proof of software correctness.

No engineering process can honestly guarantee zero defects. The enforceable objective is to prevent known classes of avoidable failure, detect defects before release, preserve evidence, and stop release when critical risks remain unresolved. We will not represent the software as defect-free, clinically validated, guideline-compliant or hospital-ready without the relevant independent evidence.

This product remains a local educational simulator using fictional training data. It is not a clinical decision-support system, hospital patient-registration system, medical device, or substitute for a qualified MDT. Real patient information must not be entered.

## 2. Research and standards informing this policy

The controls below are informed by these sources (accessed 11 November 2026):

1. **Liu et al., “Debt Behind the AI Boom: A Large-Scale Empirical Study of AI-Generated Code in the Wild” (2026).** The study reports 484,606 issues across 304,362 verified AI-authored commits in 6,275 repositories; 89.1% were code smells, more than 15% of commits from each studied assistant introduced at least one issue, and 24.2% of tracked issues remained in the latest revision. This is observational repository research, not a prediction that any particular generated change is defective. It supports persistent issue tracking, static analysis and regression discipline. https://arxiv.org/abs/2603.28592
2. **Cotroneo et al., “Human-Written vs. AI-Generated Code: A Large-Scale Study of Defects, Vulnerabilities, and Complexity” (2025).** Their analysis of more than 500,000 Python and Java samples reports distinct defect profiles and more high-risk security vulnerabilities in AI-generated samples. Dataset and classification limitations mean the result should motivate verification, not be applied as a universal defect rate. https://arxiv.org/abs/2508.21634
3. **METR, “Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity” (2025).** In a randomized trial of 16 experienced developers completing 246 tasks in mature repositories, the studied AI tools increased task completion time by 19% on average, despite developers expecting a speed-up. The sample and tool period are limited; the important lesson is that perceived speed and code volume are not reliable quality or productivity measures. https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf
4. **DORA, “2025 State of AI-assisted Software Development.”** Its research frames AI as an amplifier of the surrounding organisation and engineering system. We therefore improve specification, review, testing and delivery controls rather than assume code generation alone improves outcomes. https://research.google/pubs/dora-2025-state-of-ai-assisted-software-development-report/
5. **NIST SP 800-218, Secure Software Development Framework (SSDF) v1.1.** The framework recommends integrating secure-development practices into the SDLC to reduce vulnerabilities and their root causes. https://csrc.nist.gov/pubs/sp/800/218/final
6. **OWASP Application Security Verification Standard (ASVS) 5.0.0 (published 30 May 2025).** Use its requirements as a verification catalogue for web/API security, choosing applicable requirements and recording exceptions rather than making an unsupported blanket compliance claim. https://asvs.owasp.org/
7. **OWASP Top 10:2025.** The application security review must explicitly consider broken access control, security misconfiguration, software supply-chain failures, cryptographic failures, injection, insecure design, authentication failures, software/data integrity, logging/alerting failures and mishandled exceptional conditions. https://top10.owasp.org/2025/en/
8. **OWASP GenAI/LLM Top 10:2026 (published 4 August 2026).** For the local model workflow, assess prompt injection, sensitive information disclosure, excessive agency, supply chain, data/model poisoning, unbounded consumption, misinformation, hidden context exposure, vector/embedding weaknesses where applicable, and improper output handling. https://github.com/GenAI-Security-Project/GenAI-LLM-Top10

These sources do not prove the application is unsafe or safe. They identify risks that must be tested in this system.

## 3. Non-negotiable development rules

### 3.1 Understand before changing

Every non-trivial change starts with:
- The user-visible requirement and acceptance criteria.
- Relevant architecture, data flow, API contracts, database schema and existing tests.
- The exact current branch, commit SHA, PR and CI state.
- Failure modes, security implications, compatibility impact and rollback strategy.
- The smallest change that addresses the root cause.

Do not make speculative broad rewrites, duplicate abstractions, speculative dependencies or unrelated formatting changes. Preserve unrelated work. Do not infer repository state from an old handoff or README; re-read the current branch.

### 3.2 AI-generated code is a proposal, not an authority

- Review every changed line and its surrounding call path.
- Verify APIs, library behaviour and version compatibility against authoritative documentation or source.
- Never accept invented functions, flags, configuration options, endpoints, model capabilities or test results.
- A generated test is not sufficient if it merely repeats the implementation's assumption. Derive tests from requirements, invariants and independently written expected outcomes.
- Do not let the same model be the sole reviewer of its own code or the sole evaluator of its clinical-style outputs.
- Do not silence a failing test, weaken an assertion, lower a threshold, skip a test or relax a validator merely to obtain a green build. Any justified exception must be documented with an owner, rationale and expiry.
- Prefer explicit types, narrow interfaces, simple control flow, clear errors and deterministic validation over clever or compressed code.

### 3.3 Change isolation and provenance

- Work only on `feature/four-round-mdt-and-performance` until explicit authorisation to do otherwise.
- Never modify `main`, merge PR #1, force-push or change branch strategy without explicit authorisation.
- Every validation result must identify the exact commit SHA it tested.
- A changed code path requires relevant regression coverage; a documentation-only change must be labelled as such.
- Preserve original case records, hashes, run IDs, timestamps, database history and failed responses.
- Keep production credentials, runner tokens, model files, private data and local databases out of Git and workflow logs.
- Do not use the running laptop installation as an uncontrolled development environment. Use a separate test database and a deliberate validation window.

## 4. Required verification layers

A meaningful change is not complete until the applicable layers below pass.

| Layer | Required evidence |
|---|---|
| Static correctness | Python compilation, formatting/lint, type checks where practical, schema validation and frontend type-check/build |
| Unit tests | Positive, negative, boundary, malformed, missing-field and exception cases for changed logic |
| API/integration | Real FastAPI request path, status codes, validation, error handling, persistence and serialization |
| Database | Fresh database, upgrade from prior schema, interruption/restart, backup/restore, integrity check, no unintended data loss |
| Browser/UI | Browser-driven workflows, console/network inspection, refresh/recovery, loading/error/empty states, keyboard/accessibility checks |
| Security | SAST, dependency/advisory audit, secret scanning, input/output validation, local-network exposure review and threat-model review |
| Packaging | Clean Windows install, upgrade, launch, first-run provisioning, offline restart after provisioning, uninstall and user-data preservation |
| Runtime | Actual Ollama endpoint, exact model tag, valid inference, error/timeout path, logs, GPU attribution and resource/latency observations |
| MDT quality | Exact R1–R4 order, 45/45 accounting per specialist round, source/provenance oracle, Chair reconciliation, clinical-safety rubric and preserved failure records |
| Release | Exact SHA, passing required checks, installer checksum, SBOM/provenance where supported, release notes, known limitations and rollback plan |

A successful unit-test run does not prove browser behaviour, successful model inference, GPU offload, clinical accuracy or end-to-end release quality. Each must have its own evidence.

## 5. Test design rules

- Use synthetic cases with explicit expected invariants and intentionally missing/contradictory information.
- Test both ordinary and adversarial input: empty, null, malformed, oversized, duplicated, conflicting, unexpected Unicode, prompt-injection text and boundary values.
- Test failure paths: unavailable Ollama, wrong model tag, malformed model JSON, schema violations, timeouts, process crash, interrupted database writes, retry and resume, partial agent failures, corrupted/missing artefacts and stale browser state.
- Test state transitions and idempotency: repeated clicks/requests, double-submit, refresh during work, resume after restart, duplicate requests and attempts to advance before the preceding round is complete.
- Test that failed or missing agents remain visible and cannot be counted as successful.
- Use an independent oracle for expected results. For clinical-style semantics, use human-authored, clinician-reviewed rubrics; do not use the tested MDT or an LLM-only judge as its own gold standard.
- Keep deterministic checks separate from human/clinical review. Automated phrase matching is a screening signal, not proof of semantic correctness.
- Report raw hard-fail, major and minor counts separately. Never hide critical failures in a passing percentage or average.
- Retain reproducible fixtures, exact prompts/schemas, model version, commit SHA, case hash, run ID and output artefacts.

## 6. Security and supply-chain controls

Before release, implement and verify the following controls:

1. **Dependency reproducibility:** commit a frontend lockfile and use `npm ci`; produce a fully resolved backend lock/constraints file and build from it. Avoid floating dependency resolution in release builds.
2. **Dependency health:** automate vulnerability/advisory scans for Python and Node dependencies; review advisories and transitive dependencies; document exceptions with expiry.
3. **Static security analysis:** add language-appropriate SAST and secret scanning to pull-request CI. Treat findings as triage items; block on confirmed high/critical issues and track accepted false positives.
4. **Action pinning:** pin third-party GitHub Actions to immutable commit SHAs where practical, with human-readable version comments and a controlled update process.
5. **CI permissions:** use least-privilege workflow permissions; do not expose write-capable secrets to untrusted pull-request code.
6. **Application threat model:** document assets, trust boundaries, entry points, data flows, localhost binding, browser-origin/CSRF considerations, file handling, subprocesses, model endpoints and failure behaviour.
7. **LLM boundary:** treat case text, retrieved content, peer outputs and model output as untrusted. Enforce schema, size and semantic validation in deterministic code. Model text must never directly execute commands, SQL, scripts or privileged actions.
8. **Privacy:** keep the runtime local by default; do not transmit real patient information. Redact secrets and sensitive content from logs and exported diagnostics.
9. **Release integrity:** generate an SBOM, retain checksums and build provenance; investigate code signing so Windows can identify a trusted publisher. A checksum proves file integrity relative to a known digest; it does not prove publisher identity.
10. **Recovery:** verify that backup and restore work, not merely that a backup file exists. Test database migration and uninstall against preserved user data.

## 7. RadOnc-specific model and clinical-safety controls

These controls remain stricter than ordinary application correctness:

- R1 stays independent. R2 receives only permitted, source-labelled peer context. R3 challenges actual supplied claims and distinguishes provenance defects from clinical disagreement. R4 synthesises actual saved R1–R3 contributions.
- No missing case fact may be inferred. Unknown stays unknown; a blank field is not a negative finding.
- Preserve the original free text and structured data. Conflicts are flagged, never silently reconciled.
- Distinguish case fact, interpretation, assumption, missing information and conditional recommendation.
- Do not infer N0/M0, performance status, resectability, operability, treatment suitability, prior treatment or patient goals without source data.
- Deterministic code calculates counts, distributions, provenance, state transitions and report structure from stored contributions.
- Consensus requires distinct roles supporting the same substantive proposition with compatible conditions. Repeated phrases or generic position labels do not create consensus.
- Preserve opposition, conditional support, insufficient information, uncertainty and minority views. Do not convert conditional support into unconditional support.
- Never fabricate a missing contribution or conceal a failed role.
- No guideline compliance or evidence verification claim unless authoritative sources were actually retrieved, checked and preserved with title, organisation, date, URL/identifier and supporting locator.
- Model self-reported confidence is not calibrated certainty. Validate its behaviour across incomplete cases and report it as model-reported only.
- A live run reaching all 136 expected records is execution completeness, not a clinical pass. Clinical quality is scored against a separate human-reviewed rubric.

## 8. Current baseline findings and open gaps

This is an evidence-based engineering status review, not a complete penetration test, clinical validation or exhaustive code audit.

**Functional/application-code baseline:** `5b8159df0b0bb6ac0bedc95046d0c87784420591`  
**Documentation-only updates:** README and implementation status were refreshed after this code baseline; they do not change the application runtime.  
**Branch:** `feature/four-round-mdt-and-performance`; PR #1 remains open/draft/unmerged.  
**Base main:** `39a356b8eb09399aa2da1b9b9085965999f5105a` (unchanged).

**Verification passed on current snapshot `aaf8fb9`:**
- Backend: 191 passed, 1 existing Starlette/httpx TestClient deprecation warning ([run 42910431942](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431942)).
- Frontend: 32 passed; npm ci, TypeScript and Vite 7.3.8 production build passed ([run 42910431710](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431710)).
- Browser E2E: patient registry lifecycle and persisted R1–R4 dashboard assertions passed in isolated headless Edge with a disposable database and no Ollama calls ([run 42910431865](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431865)).
- Security: CodeQL Python and JavaScript/TypeScript, Gitleaks full-history scan, pip-audit and npm audit all passed; zero known Python/Node dependency vulnerabilities were reported ([run 42910431926](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431926)).
- Windows packaging-prerequisite inspection passed ([run 42910431949](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431949)).
- Latest Windows installer exact-SHA build/install/uninstall and clean-hosted Ollama/model bootstrap passed ([run 42910431940](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910431940)); artifact `13806987082`. User-data preservation, portable Ollama 0.40.14, qwen3.5:4b download/tag verification, CPU inference, installed-app health and 45-role API check passed. ZIP SHA-256 `cc00301aa95b65cc94e3a9a9c27681d8f08a47997142d3802d4e81e5b2e7fd0a`; Setup.exe SHA-256 `9a075c56a9e93d00bd6e4476aff4864a19dd89f05390a9483ce43315e76b97e2`.
- Full live 45-role R1–R4 validation is **in progress** on this exact SHA ([run 42910414046](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/42910414046)). No live result has yet been inspected. The run is CPU-only and uses concurrency 1. Its artifact is configured to include JSON, SQLite and a manifest binding source SHA, Actions run ID, Ollama version and exact qwen3.5:4b digest/size.
- Two earlier manifest-trigger attempts failed before model execution because the digest-validation block was truncated during file editing. They did not invoke Ollama or generate MDT output. The corrected workflow was rebuilt from the clean baseline and the current run was accepted.

**Open gaps and current priority:**

| Priority | Gap | Why it matters | Required closure evidence |
|---|---|---|---|
| P0 | No fresh 136-contribution live four-round audit on current code | Historical MDT-006 found 134 hard failures and 92 major findings on an earlier snapshot. Prompt/schema corrections have unit-test and CI coverage but need live-model validation. | Explicitly authorised full run on an immutable code/model/prompt snapshot; inspect all 136 saved contributions, R3 provenance challenges, Chair synthesis, failures/retries and the complete rubric. Do not downgrade findings. |
| P0 | Clinical reasoning/evidence validation is not established | Schema-valid model output, successful inference and deterministic consistency checks do not prove clinical correctness. Evidence retrieval and source verification remain unimplemented. | Authoritative source retrieval with provenance plus independent qualified clinical review against human-authored rubrics. No guideline/clinical-accuracy claim before this. |
| P1 | Backend dependency versions are not fully locked | Backend requirements and test-only dependencies still use version ranges, so transitive resolution can vary. | Add a reviewed, fully resolved backend lock/constraints strategy; build/test/audit from it on clean runners. |
| P1 | Branch protection is disabled | Required checks are not enforced by repository branch rules. | Obtain repository-owner authorisation, then configure required status checks and review rules. No branch settings have been modified. |
| P1 | Installer is unsigned | Windows cannot authenticate publisher identity; SmartScreen may show an unknown-publisher warning. | Obtain appropriate signing certificate, sign and timestamp the installer, then verify Authenticode signature. Do not claim signed/trusted before that. |
| P1 | Backup/restore and broader lifecycle acceptance remain incomplete | Installer uninstall preservation and browser CRUD tests do not prove backup recovery, schema rollback, power-loss resilience or all upgrade paths. | Isolated backup/restore, migration from prior supported schema, crash/restart and upgrade/rollback tests, with database integrity and hashes checked. |
| P2 | Lint/format and coverage thresholds are not yet mandatory CI gates | Passing tests and builds do not measure all maintainability or untested-path risks. | Add Python/TypeScript lint/format and coverage reports with reviewed thresholds; do not game coverage by adding low-value tests. |
| P2 | Current-head full-run GPU/performance evidence is not available | A one-agent smoke or model residency does not establish full-run GPU attribution, thermal behaviour or throughput. | Separately authorised, controlled local run with sampled `nvidia-smi`, Ollama offload/logs, concurrency=1, latency and temperature/VRAM evidence. Do not disturb the user's running installation. |

**Controls now implemented in the development branch:**
- Frontend `package-lock.json` v3 is committed (120 packages); Vite is pinned at 7.3.8; Node engine is `^20.19.0 || >=22.12.0`.
- CI, installer packaging, browser E2E, security audit and developer startup use `npm ci`; lockfile regeneration is restricted to trusted pushes to the development branch.
- pytest has been removed from production/runtime requirements and isolated in `backend/requirements-dev.txt`.
- CodeQL, Gitleaks and Python/Node dependency audits are part of PR CI; Dependabot proposes weekly dependency/action updates.
- Primary workflows pin third-party GitHub Actions to immutable commit SHAs.
- Duplicate push+PR CI for the development branch was removed; PR #1 is the authoritative development validation path.
- The browser E2E uses GitHub-hosted Windows, disposable data and no model inference; it never touches the user's laptop.

The installer workflow's hosted smoke test exercises package build, install, health, frontend assets, 45 role profiles, a training registry save and uninstall data preservation. The clean-hosted bootstrap separately downloads the pinned runtime/model and performs CPU inference. Neither proves the target laptop's current install or NVIDIA GPU inference for the current full four-round run.

## 9. Release gates — no waiver by green CI alone

A release candidate must not be described as fully verified until all applicable release gates below have evidence on the exact release SHA:

- Backend and frontend tests pass, with failures and warnings reviewed.
- Dependency lockfiles are used and dependency/security reports have no unresolved release-blocking findings.
- SAST/secret scans have no unresolved critical/high findings.
- Required PR checks and human code review are complete; merge remains separately authorised.
- Browser E2E covers the supported patient and four-round dashboard workflows.
- Database upgrade, backup/restore and uninstall preservation are tested.
- Clean Windows install, upgrade and first-run Ollama/model provisioning are verified; local existing-Ollama reuse is verified separately.
- Live model validation covers all 45 roles in R1/R2/R3 and Chair R4 on the exact SHA; all failures and retries are visible.
- The MDT audit has zero unresolved hard failures. Major findings are triaged and resolved or explicitly accepted with evidence and owner; clinical-critical major findings block release.
- Chair outputs are source-traceable, deterministic counts match saved contributions, and clinical-safety invariants hold.
- GPU claims are backed by active-inference telemetry, not idle/model-loaded status.
- Release artifact has a verified checksum, SBOM/provenance where supported, signature status disclosed, and known limitations documented.
- The product boundary remains fictional educational use only; no clinical validation or hospital readiness is implied.

Any emergency exception must identify the failed gate, risk, compensating control, approver, scope and expiry. Clinical-safety hard fails, data loss, fabricated provenance, hidden failed contributions and untraceable Chair conclusions are not waivable for release.

## 10. Operating cadence

For each change: inspect → specify → assess risk → implement the smallest fix → add independent regression tests → run relevant checks → inspect artefacts/logs → verify exact SHA → update status.

For each release candidate: freeze SHA → clean build → backend/frontend/security checks → browser and database acceptance → installer acceptance → model/MDT audit → independent review → release decision.

Do not repeatedly rerun large stress suites without a question the run is intended to answer. Fix a classified root cause, then run the smallest regression capable of demonstrating the fix; use the full suite at defined release checkpoints.

## 11. Source register maintenance

Review this standard whenever major changes are made to the architecture, dependency supply chain, model orchestration, security boundary or release pipeline. Record the date and exact versions of standards used. Do not claim certification or compliance simply because a checklist has been adopted.
