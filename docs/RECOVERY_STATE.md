# RadOnc MDT Simulator — Recovery State

**Last checkpoint:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Development branch:** feature/four-round-mdt-and-performance  
**Application/test SHA:** c0fbb2ac4a586d5effa51ea8bcc4af623137008f  
**PR #1:** open, draft, unmerged, base main.  
**Main SHA:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Recovery instruction

Resume from paired model-screen workflow 44004929958. Do not rerun passed standard code CI or restart earlier project phases. Do not launch another model workflow while this concurrency-1 run is active.

## Exact workflow state

| Workflow | Source SHA | Run ID / Job | State | Interpretation |
|---|---|---|---|---|
| Intermediate model screen | b351a815d013386e271595e2fb54a6f0d571c544 | 44000326185 / 133762488994 | FAILED | Artifact 14292068885 inspected. Qwen 12/12; MedGemma 9/12; 3 repeated outputs truncated at 500 tokens. Superseded R3 regex; R3 flags not accepted. |
| Corrected-source model screen | 8b7124cf1d0b236100958fd91b8fadc506eee559 | 44000583529 / 133768126103 | FAILED | Artifact 14293084055 inspected. Qwen 12/12 parseable, 0 flags. MedGemma 9/12 parseable; R2 false-consensus, R3 fabricated-quote and R4 Chair-traceability each ended with done_reason=length/eval_count=500 and truncated JSON. |
| Shared repetition-mitigation screen | c0fbb2ac4a586d5effa51ea8bcc4af623137008f | 44004929958 / 133777841510 | IN PROGRESS | HAI-DEF terms gate passed. Isolated Ollama provision/sequential paired screening active. No final artifact/result yet. |
| Standard six-workflow PR CI | c0fbb2ac4a586d5effa51ea8bcc4af623137008f | 44004935939, 44004935954, 44004935981, 44004936006, 44004936065, 44004936087 | COMPLETED/SUCCESS | Backend 423/423, preflight 7/7; frontend, browser E2E, packaging prerequisites, installer and security/CodeQL passed. |
| Push Installer | c0fbb2ac4a586d5effa51ea8bcc4af623137008f | 44004930010 | COMPLETED/SUCCESS | Installer workflow passed. |

## Corrected-source model-screen facts

- Ollama 0.40.14, hosted Windows CPU, concurrency 1, GPU measurement NOT_PERFORMED.
- Prompt v6, audit v4, corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3.
- Qwen digest: sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04.
- MedGemma digest: sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Artifact 14293084055 contains manifest, Qwen JSONL, MedGemma JSONL and Ollama logs. Qwen 12/12 parseable, 0 flags. MedGemma 9/12 parseable, 3 malformed due repeated text until token cap. No model-quality acceptance.
- Ollama log recorded repeat_penalty 1.000 (disabled), repeat_last_n 64. Current experiment sets repeat_penalty 1.1/repeat_last_n 64 for BOTH models while leaving num_predict 500 and all paired prompts/options identical.

## Immediate next operation

1. Check workflow 44004929958 / job 133777841510 for terminal state and artifact.
2. Download manifest and both model JSONL files. Check script/corpus hashes, prompt/audit versions, exact model digests and recorded generation_options.
3. Count parseable/incomplete outputs, response records, done_reason/eval_count, per-case deterministic audit flags and repeated clauses. Inspect raw output for all cases, not just summary counters.
4. Compare Qwen and MedGemma under identical settings. Check whether the three known MedGemma failures remain; also ensure Qwen output quality did not regress.
5. Do not raise num_predict or alter concurrency blindly. If the shared repeat penalty does not resolve loops, preserve the artifact and choose the next controlled correction based on actual output.
6. Update this recovery file, Master Checklist, TASK_CHECKLIST, EXECUTION_LOG, PROJECT_STATUS and KNOWN_ISSUES after the run is inspected.

## Other outstanding gates

- Historical run-9 integrity failure: 343 entries; original records immutable.
- Current full 45-role R1–R4 acceptance: NOT STARTED.
- Missing/failed-agent full-run acceptance: IN PROGRESS.
- RTX 4060 request-time inference: NOT STARTED.
- Current guideline retrieval and claim linkage: NOT STARTED.
- Independent qualified clinical review: NOT STARTED.
- Release acceptance: BLOCKED.
