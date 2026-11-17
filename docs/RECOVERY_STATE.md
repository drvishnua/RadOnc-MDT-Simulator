# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Branch HEAD at checkpoint:** 1d28b0c2f80f355f34f1ff2a3153bc684f3c596f  
**Latest verified code/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from the corrected-source model-screen queue. Do not repeat already-passed CI or restart the application work from scratch.

## Exact workflow state

| Workflow | Source SHA | Run ID | State at checkpoint | Interpretation |
|---|---|---:|---|---|
| Synthetic Model Integrity Screening | b351a815d013386e271595e2fb54a6f0d571c544 | 44000326185 | IN PROGRESS | Superseded intermediate source with doubled regex escapes. Preserve run; do not accept its model/audit result for current source. No artifacts published. |
| Synthetic Model Integrity Screening | 8b7124cf1d0b236100958fd91b8fadc506eee559 | 44000583529 | PENDING | Corrected source. Same concurrency group, cancel-in-progress false. Await slot; do not launch another model run. |
| Standard six-workflow PR CI | 8b7124cf1d0b236100958fd91b8fadc506eee559 | See Master Checklist | COMPLETED/SUCCESS | Backend 423/423, preflight 7/7; all remaining standard workflows passed. |
| Standard six-workflow PR CI | 1d28b0c2f80f355f34f1ff2a3153bc684f3c596f | 44001410301, 44001410321, 44001410337, 44001410345, 44001410350, 44001410369 | COMPLETED/SUCCESS | Documentation-only checklist follow-on; all six workflows passed. |

## Immediate next operation

1. Re-read this file and verify branch HEAD, PR #1, main SHA and current workflow states.
2. Check run 44000326185 and whether it has completed or published artifacts. Its job-log fetch previously returned BlobNotFound/404; don't infer the reason it is still active.
3. Once run 44000326185 releases the concurrency slot, verify that 44000583529 starts on exact SHA 8b7124c.
4. Wait for actual completion through repeated status checks in this active session; do not claim the workflow will run in the background beyond available automation.
5. Download and inspect the corrected run manifest, Qwen JSONL and MedGemma JSONL. Verify prompt/audit versions, script SHA, corpus SHA, exact model digests, 12 responses per model, errors, deterministic flags, per-case evidence and any discrepancies.
6. Compare Qwen versus MedGemma. Do not promote MedGemma based on latency or syntactic validity; require preserved behaviour, no unexplained audit flags and independent qualified review.
7. Update the Master Checklist, TASK_CHECKLIST, EXECUTION_LOG, KNOWN_ISSUES and this recovery file with exact artifacts and source SHAs.

## Other outstanding gates

- Historical run-9 audit integrity failure: 343 entries, original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval and independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.

## Tooling limitation

The GitHub Actions wrapper returned BlobNotFound/404 when requesting logs for job 133762488994. The run remains visible as in_progress; no root cause can be assigned without fresh logs/status or final artifacts.
