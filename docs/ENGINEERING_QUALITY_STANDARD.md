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

This is an initial inspection, not a complete penetration test or exhaustive code audit.

**Verified at baseline SHA `5016e5b8270770748d9db9f85600821d723b3b2f`:**
- Backend CI completed successfully: 191 passed, 1 Starlette/httpx TestClient deprecation warning.
- Frontend CI completed successfully.
- Windows installer build, installed-app smoke test and clean-hosted Ollama/model first-run provisioning completed successfully.
- The installer artifact and checksum were generated for this exact SHA.
- PR #1 is open and draft; the development branch is at this SHA. `main` remains at `39a356b8eb09399aa2da1b9b9085965999f5105a`.

**Open gaps observed in the repository at this baseline:**

| Priority | Gap | Why it matters | Required closure evidence |
|---|---|---|---|
| P0 | No fresh 136-contribution live four-round audit on SHA `5016e5b...` | Historical MDT-006 found 134 hard failures and 92 major findings on an earlier snapshot. Later R2/R3 changes have CI coverage, not live-model proof. | One exact-SHA live run; inspect all 136 saved contributions, R3 provenance challenges, Chair, failures and the full rubric output. No hidden or downgraded findings. |
| P0 | End-to-end patient-registry browser roundtrip is not currently evidenced on this SHA | API persistence and static UI delivery do not prove real user actions, refresh, edit/versioning and recovery. | Browser-driven create, validate, save, refresh, restore, edit/version, link run, delete/clear where supported; assert DB state and browser console/network. |
| P1 | No frontend `package-lock.json` is present in the inspected frontend directory; CI uses `npm install`. Backend requirements use version ranges without a resolved lock. | Transitive dependencies can change between builds, reducing reproducibility and forensic traceability. | Committed lockfiles, clean `npm ci`/locked Python install, repeat build comparison and dependency audit. |
| P1 | Current workflows do not show dedicated CodeQL/SAST, Python/Node dependency audit, secret scan, lint or coverage-report gates. | Test/build success cannot detect every security, style, dead-code or dependency issue. | Pull-request workflows with actionable severity thresholds and retained reports. |
| P1 | GitHub branch API reported branch protection disabled for both the development branch and `main` at inspection. | Required checks are not enforced by branch protection. | Configure required status checks and review rules after confirming exact check names; do not merge without explicit permission. |
| P1 | README and `docs/IMPLEMENTATION_STATUS.md` contain an older verification snapshot (for example, 691c26a.../177 tests) rather than the current 5016e5b.../191-test CI state. | Readers can mistake historical checks for current evidence. | Update release/implementation records on each release candidate; link every result to its exact SHA and mark stale results historical. |
| P1 | Windows installer is unsigned and SmartScreen reports an unknown publisher. | Users cannot authenticate the publisher identity from the installer signature. | Evaluate and configure an appropriate code-signing certificate, timestamping and signature verification. Do not claim trust/signing before this is done. |
| P2 | CI workflow action references use major tags such as `@v4` rather than immutable commit SHAs. | A mutable tag is a supply-chain and reproducibility dependency. | Pin action SHAs, document versions, and schedule controlled updates. |
| P2 | No current full-run GPU/performance evidence is attached to this exact SHA. | A one-agent inference or model residency alone does not establish full-run performance or safe concurrency. | One controlled full local run with sampled `nvidia-smi`, Ollama offload/logs, concurrency=1, latency and temperature/VRAM observations. |

The installer workflow's hosted smoke test is valuable: it exercises setup, app health, static frontend delivery, the 45-role API, a patient save and uninstall data preservation. It is not an interactive browser E2E test. Its clean-hosted first-run job exercises real provisioning and one inference on a disposable hosted VM; it does not prove NVIDIA GPU inference on the target laptop.

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
