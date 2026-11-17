# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Branch HEAD at checkpoint:** 80ee6e9854eb6862f69dd06b63cc256c95f40fa2  
**Latest verified application/test SHA:** 8b7124cf1d0b236100958fd91b8fadc506eee559  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from the corrected-source model-screen run 44000583529. Do not repeat passed code CI, rebuild the continuity bundle, or restart earlier project phases.

## Exact workflow state

| Workflow | Source SHA | Run ID / Job | State | Interpretation |
|---|---|---|---|---|
| Intermediate Synthetic Model Integrity Screening | b351a815d013386e271595e2fb54a6f0d571c544 | 44000326185 / 133762488994 | FAILED | Artifact 14292068885 inspected. Qwen 12/12 parseable. MedGemma 9/12 parseable; 3 outputs malformed after repeated loops hit 500-token limit. Do not accept R3 audit flags because this source had the superseded doubled-escape regex. |
| Corrected Synthetic Model Integrity Screening | 8b7124cf1d0b236100958fd91b8fadc506eee559 | 44000583529 / 133768126103 | IN PROGRESS | Corrected R3 regex source. HAI-DEF terms gate passed. Provisioning/sequential-screen job active; no artifact at checkpoint. |
| Standard six-workflow PR CI | 8b7124cf1d0b236100958fd91b8fadc506eee559 | See Master Checklist | COMPLETED/SUCCESS | Backend 423/423, preflight 7/7; all six standard workflows passed. |
| Standard six-workflow PR CI | 80ee6e9854eb6862f69dd06b63cc256c95f40fa2 | 44002108715, 44002108718, 44002108732, 44002108741, 44002108744, 44002109028 | COMPLETED/SUCCESS | Persistent-documentation bundle; Backend 423/423 and all other standard workflows passed. |

## Intermediate model-screen facts

- Ollama 0.40.14 and both exact model digests were provisioned successfully on hosted Windows CPU; concurrency 1; no GPU measurement.
- Qwen model digest: `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
- MedGemma model digest: `sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c`.
- MedGemma incomplete cases: `R2-FALSE-CONSENSUS-005`, `R3-FABRICATED-QUOTE-009`, `R4-CHAIR-TRACEABILITY-012`; each hit `done_reason=length`, `eval_count=500` and saved truncated JSON after repetition. Overall run failure was due to malformed MedGemma responses, not provisioning.
- Intermediate artifact **14292068885** contains manifest, Qwen JSONL, MedGemma JSONL and Ollama logs. Preserve it.

## Immediate next operation

1. Verify current branch HEAD, PR #1, main SHA and corrected workflow status.
2. Check run 44000583529 for terminal state and artifact. Job log retrieval previously returned BlobNotFound/404, so use run/job states and final artifacts.
3. Download manifest and both JSONL files. Verify script/corpus hashes, prompt/audit versions, model digests, 12 responses per model, malformed/failed counts, done_reason/eval_count, integrity flags and raw per-case text.
4. Compare whether MedGemma repeats the same three 500-token failures. Do not infer that the corrected R3 regex fixes generation loops.
5. If truncation repeats, design a controlled prompt/output-format correction based on the raw text. Preserve identical inputs/options for paired model comparisons; do not increase num_predict blindly because repetition may continue.
6. Commit only the smallest reversible correction with regression tests; allow its marker-triggered workflow to start automatically after the current concurrency group is clear.
7. Update Master Checklist, TASK_CHECKLIST, EXECUTION_LOG, KNOWN_ISSUES and this recovery file with exact SHA/run/artifact evidence.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
