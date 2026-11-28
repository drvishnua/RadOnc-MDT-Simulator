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

This status is evidence-based but is not a complete penetration test, legal opinion, clinical validation or exhaustive code audit. Every result below is tied to the exact development SHA.

**Current code HEAD:** `b47ca1fb2acdc6957e26f148bc6b55a5890ee91f`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR #1:** open, draft, unmerged; targets `main`.  
**Base main:** `39a356b8eb09399aa2da1b9b9085965999f5105a` (unchanged).  
**Latest functional commits:** `4e8c3cc` (negated treatment-status qualifier and structured R3 peer-reference recovery), `b47ca1f` (require the exact CASE source ID alongside the structured R2 peer reference).

### Verification on exact HEAD `b47ca1fb2acdc6957e26f148bc6b55a5890ee91f`

- **Backend:** 206 passed, 1 existing Starlette/httpx TestClient deprecation warning ([run 43113102935](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102935)).
- **Frontend:** passed case-draft persistence tests, launcher syntax/Node compatibility checks, TypeScript check and production build ([run 43113102929](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102929)).
- **Browser E2E:** passed isolated patient-registry and saved-MDT-dashboard browser workflow ([run 43113102914](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102914)).
- **Security:** CodeQL Python and JavaScript/TypeScript, full-history Gitleaks, Python dependency audit and Node dependency audit passed ([run 43113102923](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102923)). This is not a penetration test or a guarantee of no vulnerabilities.
- **Windows packaging prerequisites:** read-only tool inspection passed ([run 43113102963](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102963)).
- **Windows installer build and clean-host live validation:** workflow [run 43113102981](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43113102981) had not yet started at the time of this status update. No installer result is claimed for HEAD `b47ca1f`.
- **Latest completed clean-host model result on preceding HEAD `71fdefb`:** installer build and clean-host installation/runtime provisioning passed; Ollama 0.40.14 and `qwen3.5:4b` were downloaded and verified, real CPU inference succeeded, the installed app started and 45 role profiles were returned. The six-call live R2/R3 quality gate **failed** ([run 43074475749](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43074475749), clean-host job 130711471545, report artifact 13882612751). The report identified a deterministic false-positive for the negated phrase “does not imply … contraindicated”, R3 misclassification of source opinions and unresolved peer attribution. The next two commits address narrowly scoped failure modes; they do not prove that the live-model quality gate now passes.
- **CPU/GPU:** the clean-host run on `71fdefb` used CPU inference and reported zero VRAM. This does not verify the target laptop RTX 4060. No current-HEAD active GPU utilisation, Ollama GPU offload or full-run performance claim is made.
- **Full MDT:** no new 136-contribution four-round run has been started on this HEAD. A full run is a separately authorised milestone and must not be inferred from unit tests or a six-call sample.
- **Clinical/evidence:** no guideline retrieval is connected; no guideline concordance, clinical accuracy or qualified clinical validation is claimed.

### Changes validated by the latest backend suite

- The deterministic treatment-status qualifier now recognises explicit “does not imply/mean” negation. A contrastive regression ensures a separate later positive assertion (for example, after “however”) is still flagged.
- R3 can select a peer from a unique structured R2 reference only when the same structured reference list also contains the exact server-identified CASE source ID and the R2 peer is in the actual supplied-peer allowlist. The server still binds the excerpt to that peer's unique structured response for the same CASE opinion. Ambiguous, invalid or unpaired references remain unverified.
- R3 instructions now explicitly require inspection of the source-specific `source_opinion_responses` entry rather than relying only on a peer's general conclusion/response.
- Regression coverage includes the missing CASE-link failure path. These checks establish provenance/representation handling, not the clinical correctness of the quoted statements.

### Open gaps and release risks

| Priority | Gap | Why it matters | Required closure evidence |
|---|---|---|---|
| P0 | Latest live R2/R3 quality gate has not passed on a current checkpoint | The prior clean-host gate on `71fdefb` failed. Prompt/schema and deterministic corrections now have CI coverage, but live model behaviour must be measured again. | Run the bounded six-call current-HEAD clean-host test, retrieve the report, inspect every role/source opinion, and pass all provenance and quality gates without weakening validators. |
| P0 | No fresh 136-contribution live four-round audit on current code | Historical MDT-006 found 134 hard failures and 92 major findings on an earlier snapshot. | Separately authorised immutable-SHA/model run; inspect all 136 records, all failures/retries, R3 provenance, R4 Chair report and an independently authored rubric. |
| P0 | Clinical reasoning/evidence validation is not established | Schema-valid model output and traceable quotations do not prove clinical correctness. | Authoritative evidence retrieval with provenance and independent qualified clinical review against human-authored rubrics. No clinical-accuracy or guideline-compliance claims before this. |
| P1 | Real patient data cannot be technically ruled out | The UI instructs users to enter fictional cases only, but free-text data is not reliably classified as synthetic or de-identified. SQLite persists user-entered case data locally. | Keep external/hospital use blocked; add explicit synthetic-data attestation and misuse controls; assess data minimisation, encryption, retention, access and breach response with counsel. Do not claim that a PHI detector can guarantee detection. |
| P1 | Local API has no application authentication | The packaged server binds to loopback and CORS is restricted, but CORS is not authentication and another local process can call a loopback API. | Threat model, hostile-local-origin/CSRF/DNS-rebinding tests as applicable, and a reviewed per-install request-authentication or equivalent local trust mechanism before multi-user/network deployment. |
| P1 | Database encryption and backup/restore are not verified | The SQLite database is stored in the local user data directory; filesystem permissions alone do not demonstrate encryption at rest or recoverability. | Security-reviewed encryption decision, privacy/retention documentation, tested backup/restore, interruption recovery and upgrade/rollback checks. |
| P1 | Backend dependency versions are not fully locked | Backend requirements still use version ranges, so clean builds can resolve different transitive versions. | Reviewed fully resolved backend lock/constraints strategy; build, test and audit from that file on clean runners. |
| P1 | Branch protection and required checks are disabled | GitHub branch metadata showed protection disabled for both `main` and the development branch. | Repository-owner authorisation, then enforce required checks, PR review and restrictions on direct updates. No settings were changed. |
| P1 | Installer is unsigned | Checksums detect mismatch against a known digest but do not authenticate publisher identity. | Obtain appropriate signing certificate, sign and timestamp installer, and verify Authenticode before making publisher-trust claims. |
| P1 | Indian legal/regulatory review and release documents are not signed off | Educational intent is relevant to medical-device scope, but product behaviour, promotion, real-data handling and commercial distribution affect legal risk. | Specialist Indian healthcare/regulatory, privacy and product-liability counsel review; approved intended-use statement, EULA, privacy notice, acceptable-use terms, warnings and incident process. See `docs/LEGAL_AND_REGULATORY_RISK_REGISTER.md`. |
| P2 | Lint/format and coverage thresholds are not mandatory CI gates | Test passes do not provide maintainability or untested-path measurements. | Add Python/TypeScript lint/format and coverage reporting with independently reviewed thresholds. |
| P2 | SBOM and reproducible release provenance are not complete | Dependency audit is not a complete software bill of materials or build-attestation process. | Generate and retain an SBOM and build provenance; verify installer checksums and dependency/model/runtime licences. |
| P2 | Current-head laptop GPU/performance evidence is not available | CPU clean-host inference does not establish target RTX 4060 behaviour. | With explicit local validation window, sample `nvidia-smi`, Ollama placement/logs, latency, VRAM and thermal telemetry during real inference at concurrency 1. |

### Anti-vibe-coding enforcement

The existing rules in Sections 3–7 remain mandatory. For this project they mean: inspect repository state before editing; define acceptance criteria; make the smallest root-cause change; review every changed line; add a regression from an independent requirement/oracle; run the exact affected tests and CI; inspect logs and generated artefacts; preserve failing outputs; and record the tested SHA. The implementation model must not be its own sole reviewer or clinical-quality judge. No test, threshold, validator or warning may be weakened merely to obtain green CI.

**Current process limitations:** Python lint/format and coverage are not mandatory CI gates; backend dependency ranges are not fully locked; human code review/required-check enforcement is not technically required by branch rules. These are known gaps, not silently accepted standards.

### Controls already present

- Frontend `package-lock.json` and `npm ci` are used for reproducible frontend installs; Node/Vite compatibility is checked.
- pytest is isolated to development requirements, not production runtime.
- PR workflows include CodeQL, Gitleaks and Python/Node dependency audits; third-party GitHub Actions are pinned to immutable commit SHAs.
- Model generation uses structured schemas and deterministic server-side case/provenance checks; Ollama concurrency remains 1.
- Packaged runtime binds to `127.0.0.1`; default inference is local Ollama. The installer pins the Ollama runtime archive by SHA-256 and verifies the configured model tag.
- Patient registry names are stored separately from case JSON and are not passed to specialist agents; case versions carry snapshot hashes.

These controls reduce specific risks but do not replace penetration testing, data protection review, legal advice, clinical validation or independent release acceptance.

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
