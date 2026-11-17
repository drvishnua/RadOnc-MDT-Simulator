# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Current branch HEAD at snapshot:** 80ee6e9854eb6862f69dd06b63cc256c95f40fa2 (continuity-document bundle)  
**Latest verified code/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

The latest application/test changes are committed at code/test SHA 8b7124c. All six standard PR workflows passed on that SHA and again on documentation-only HEAD 80ee6e9. Backend reported 423 passed, 0 failed/errors/skipped; deterministic preflight 7/7. Browser E2E, frontend build, packaging prerequisites, installer and security/CodeQL passed.

The immediate outstanding task is the corrected prompt-v6 / audit-v4 paired Qwen and MedGemma synthetic screen. Intermediate run 44000326185 on b351a81 completed failed; artifact 14292068885 shows Qwen 12/12 parseable and MedGemma 9/12 parseable, with three repeated-output loops truncated at the 500-token limit. Corrected-source run 44000583529 on 8b7124c is now in progress. Its results are not yet available.

## Completed and verified

- Corrected prompt v6 test phrase case matching.
- Corrected R3 source-ID misclassification detection to bind status wording to the exact source ID; added a regression for a nearby malformed range.
- Stabilised the browser Development Monitor E2E with deterministic GitHub API fixtures. Production remains a live, read-only GitHub API integration with visible error handling.
- Passed exact code/test CI on 8b7124c; the six workflows are listed in the Master Checklist.
- Updated the single authoritative checklist and preserved previous CI failures as historical records.
- Added six supporting continuity documents in commit 80ee6e9; all six standard PR workflows passed on that documentation commit.

## In progress / outstanding

- Complete corrected-head paired Qwen/MedGemma v6/audit-v4 run and inspect both raw JSONL outputs plus manifest. Determine whether the three MedGemma 500-token repetition failures reproduce.
- Resolve historical 45-role run-9 audit failure (343 findings) without altering immutable original records.
- Complete a fresh 45-role R1–R4 validation and failed-agent/incomplete-data acceptance.
- Verify RTX 4060 request-time GPU activity and performance; hosted CPU runs are not GPU evidence.
- Integrate retrieved, current guideline evidence with validated claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains blocked.

## Source of truth

Use [MASTER_DEVELOPMENT_CHECKLIST.md](MASTER_DEVELOPMENT_CHECKLIST.md) for the current detailed status, exact CI references, status enums and evidence limits. This file is a concise orientation summary, not a second verification checklist.

## Continuity

See [RECOVERY_STATE.md](RECOVERY_STATE.md) for the exact resume point, active/queued workflow IDs and next operation. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for open failures and limitations.
