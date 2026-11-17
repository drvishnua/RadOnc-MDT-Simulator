# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Current branch HEAD at snapshot:** 1d28b0c2f80f355f34f1ff2a3153bc684f3c596f (documentation-only checklist refresh)  
**Latest verified code/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Overall position

The latest application/test changes are committed and all six standard PR workflows passed on code/test SHA 8b7124c. The subsequent checklist-only commit 1d28b0c also passed all six standard workflows. The backend suite reported 423 passed, 0 failed/errors/skipped; deterministic preflight 7/7. Browser E2E, frontend build, packaging prerequisites, installer and security/CodeQL passed.

The immediate outstanding task is the corrected prompt-v6 / audit-v4 paired Qwen and MedGemma synthetic screen. An earlier run against intermediate commit b351a81 remains marked in progress without artifacts; its source was superseded by the regex correction at 8b7124c. The corrected-head run 44000583529 is pending in the same concurrency group. No new model output can yet be reviewed.

## Completed and verified

- Corrected prompt v6 test phrase case matching.
- Corrected R3 source-ID misclassification detection to bind status wording to the exact source ID; added a regression for a nearby malformed range.
- Stabilised the browser Development Monitor E2E with deterministic GitHub API fixtures. Production remains a live, read-only GitHub API integration with visible error handling.
- Passed exact code/test CI on 8b7124c; the six workflows are listed in the Master Checklist.
- Updated the single authoritative checklist and preserved previous CI failures as historical records.

## In progress / outstanding

- Complete corrected-head paired Qwen/MedGemma v6/audit-v4 run and inspect both raw JSONL outputs plus manifest.
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
