# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** e877600c8f860013d45c8f2eb1976b9b81d34484  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

Cloud development and verification run independently on GitHub-hosted Windows runners. The user's PC does not need to remain online for repository changes, hosted CI, installer builds or hosted CPU model screening. A real RTX 4060 request-time inference test is a separate hardware task and does require the target Windows PC to be powered on and running its local Ollama inference workload. The offline banner in the ChatGPT app affects chat communication, not the GitHub cloud runner.

The latest application/test SHA e877600 adds audit-v5 checks for three MedGemma failure modes seen in the previous raw paired output: source-position attribution inversion in R2, misclassifying one source's prerequisite status as a shared proposition, and contradictory Chair agreement/no-agreement wording. It also corrects a negation matcher in those checks and updates a mock R2 response to cite exact source IDs.

Exact-head standard PR CI on e877600 passed: Backend **428/428**, deterministic preflight **7/7**, Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL. Push Installer passed. The new paired audit-v5 model screen is pending behind an older run in the workflow's concurrency-1 group.

## Latest completed paired model screen

Run 44006972494, source d2e85a92fd5c91c002d36c133821dfb5aab9c09f, artifact 14296070216, completed successfully on GitHub-hosted Windows CPU:
- Qwen: 12/12 complete, parseable responses; 0 audit-v4 flags.
- MedGemma: 12/12 complete, parseable responses; 2 audit-v4 flags (R3 exact-source quote review and R4 unresolved-source traceability).
- Manual inspection also found MedGemma R2 position attribution reversal, a false shared-prerequisite-status proposition, and an internally contradictory R4 agreement/no-agreement statement. These were not caught by audit-v4 and motivated audit-v5.
- Both manifests and Ollama logs confirm identical effective sampler settings: temperature 0, seed 73, num_ctx 4096, top_k 20, top_p 0.95, frequency_penalty 0, presence_penalty 1.5, repeat_last_n 64, repeat_penalty 1.1, num_predict 500.
- All responses ended with done_reason=stop; no token-cap truncation occurred in this run. This is one successful bounded sample, not proof that all repetition issues are universally fixed.
- Both summaries remain COMPLETED_PENDING_HUMAN_REVIEW. No automatic quality score, clinical accuracy evaluation or clinical validation was performed. Hosted CPU only; GPU measurement NOT_PERFORMED.

## Current audit-v5 and workflow state

- Commit c7927bd introduced audit-v5 checks and four regressions, but Backend CI failed 425/428 because the new checker treated the phrase "does not state" as affirmative and one existing test fixture did not use exact source IDs. Failure run 44010384887 and artifact 14296247292 are preserved.
- Commit e877600 corrected the negation handling and mock fixture. Exact-head Backend passed 428/428; preflight 7/7.
- The model screen on c7927bd, run 44010377043, is still in progress and uses the superseded first audit-v5 implementation. Do not accept its audit flags as current.
- The corrected e877600 model screen, run 44010717466, is pending behind the active concurrency-1 run. Do not start a competing inference workflow.

## Outstanding

- Inspect completion/artifacts for run 44010377043 only as raw-output/provisioning history; its audit flags are not accepted.
- Inspect corrected run 44010717466 after it starts: manifest hashes, paired options, 12/12 per model, completion reasons, flags and all raw outputs.
- Obtain independent blinded human review of model outputs; MedGemma is not promoted.
- Resolve historical 45-role run-9 audit failure (343 findings) without modifying original saved records.
- Complete fresh 45-role R1–R4 validation and missing/failed-agent acceptance.
- Verify RTX 4060 request-time GPU activity and performance locally; hosted CPU runs are not GPU evidence.
- Retrieve and verify current authoritative guideline sources and claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains BLOCKED.

## Source of truth

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed status/evidence table. TASK_CHECKLIST.md lists next actions, DECISIONS.md records durable requirements, EXECUTION_LOG.md is chronological, RECOVERY_STATE.md gives the precise resume point, and KNOWN_ISSUES.md lists unresolved defects.
