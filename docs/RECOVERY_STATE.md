# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Application/test SHA:** d2e85a92fd5c91c002d36c133821dfb5aab9c09f  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from paired model-screen workflow 44006972494, job 133784577318. Do not rerun passed code CI or restart earlier project phases. Do not launch another model workflow while concurrency 1 is held.

## Exact workflow state

| Workflow | Source SHA | Run ID / Job | State | Interpretation |
|---|---|---|---|---|
| Intermediate model screen | b351a815d013386e271595e2fb54a6f0d571c544 | 44000326185 / 133762488994 | FAILED | Artifact 14292068885. Qwen 12/12; MedGemma 9/12 with three truncated outputs. Superseded R3 regex; R3 flags not accepted. |
| Corrected-source model screen | 8b7124cf1d0b236100958fd91b8fadc506eee559 | 44000583529 / 133768126103 | FAILED | Artifact 14293084055. Qwen 12/12 parseable, 0 flags; MedGemma 9/12 parseable, 3 loop/truncation cases at 500 tokens. |
| Repetition-penalty run | c0fbb2ac4a586d5effa51ea8bcc4af623137008f | 44004929958 / 133777841510 | FAILED | Artifact 14294366737. Qwen 12/12 parseable, 0 flags. MedGemma pull /api/pull HTTP 500; no MedGemma inference. Prior effective samplers differed across models. |
| Effective-sampler and pull-diagnostics run | d2e85a92fd5c91c002d36c133821dfb5aab9c09f | 44006972494 / 133784577318 | IN PROGRESS | HAI-DEF terms gate passed. Combined isolated hosted provisioning/sequential inference step active; no artifact yet. Workflow persists MedGemma pull HTTP details if it fails. |
| Standard six-workflow PR CI | d2e85a92fd5c91c002d36c133821dfb5aab9c09f | 44006977053, 44006977075, 44006977077, 44006977161, 44006977278, 44006977316 | COMPLETED/SUCCESS | Backend 424/424, preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Installer and Security/CodeQL passed. |
| Push Installer | d2e85a92fd5c91c002d36c133821dfb5aab9c09f | 44006972458 | COMPLETED/SUCCESS | Installer workflow passed. |

## Effective paired model options

The screen runner now passes identical options to both models:
- temperature 0; seed 73; num_ctx 4096.
- top_k 20; top_p 0.95; frequency_penalty 0.0; presence_penalty 1.5.
- repeat_last_n 64; repeat_penalty 1.1; num_predict 500.

The first run using repeat_penalty 1.1 (44004929958) did not generate MedGemma outputs because the model pull returned HTTP 500. It cannot validate MedGemma repetition behaviour. Prior sampler logs showed model defaults differed; d2e85a9 pins the observed Qwen baseline for both and adds pull diagnostics.

## Immediate next operation

1. Check run 44006972494 / job 133784577318 for terminal state and artifact.
2. If successful, download the artifact; inspect manifest, Qwen/MedGemma JSONL and logs. Verify exact model digests, common generation_options, 12 responses per model, done_reason/eval_count and output parseability.
3. Confirm whether MedGemma was successfully pulled and whether its generation actually started. Do not infer from Qwen-only output.
4. Review all raw output and deterministic audit flags; specifically compare the three known MedGemma looping cases and check Qwen for regressions.
5. If pull fails, inspect the new manifest's status, HTTP code, URI and response body before proposing any retry. Do not infer a cause absent those diagnostics.
6. Update this file, Master Checklist, TASK_CHECKLIST, EXECUTION_LOG, PROJECT_STATUS, KNOWN_ISSUES and DECISIONS after verified results.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval and claim linkage: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
