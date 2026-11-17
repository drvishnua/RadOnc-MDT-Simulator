# RadOnc MDT Simulator — Known Issues

Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: de95004d1c169f3ffa6c52ccf412d84d33055234

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Earlier superseded model screen | Run 44000326185; MedGemma three 500-token truncations. | Preserve artifact. |
| KI-002 | FAILED | v6/audit-v4 screen | Run 44000583529; three MedGemma truncations. | Preserve raw output. |
| KI-003 | FAILED | Historical 45-role run-9 integrity | Audit revalidation recorded 343 findings (R1 11, R2 41, R3 271, R4 20). | Original records immutable; fresh acceptance required. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screens/tests do not establish full-system behaviour. | Controlled full validation after gates. |
| KI-005 | NOT STARTED | RTX 4060 request-time inference unproven | Hosted screens CPU-only. | Local inference with nvidia-smi/ollama ps/latency. |
| KI-006 | NOT STARTED | Guideline retrieval/claim verification | No current verified authoritative guideline corpus. | Retrieve and link exact source references. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No review artifact. | Obtain qualified review. |
| KI-008 | IN PROGRESS | Development Monitor live GitHub API dependency | Production browser uses public API subject to network/rate limits. | Verify live browser operation and stale-state handling. |
| KI-009 | IN PROGRESS | MedGemma repetition robustness | Recent paired runs 44011921822, 44010717466 and 44016121962 had complete stop outputs; earlier runs truncated. | Continue monitoring; bounded samples only. |
| KI-010 | IN PROGRESS | Earlier MedGemma HTTP 500 model pull | Run 44004929958 failed; later pulls succeeded; original root cause unknown. | Investigate if reproduced. |
| KI-011 | VERIFIED | Paired sampler parity | Run 44016121962: matching model digests/options and 24/24 stop completions. | Maintain and reverify. |
| KI-012 | IN PROGRESS | MedGemma R2/R3 semantic defects | Prompt-v8/audit-v6: missing R2 source rows and conditionality, R3 exact quote rejection, plus false shared treatment proposition found manually. | Audit-v7 run 44018644704 active. |
| KI-013 | VERIFIED — CODE ONLY | Audit-v6 correct-negation handling | Backend and model output verified on prior commits. | Keep regression. |
| KI-014 | FAILED — SUPERSEDED | Prompt-v7 removed existing regression-protected phrases | Backend run 44015312495 failed 8 tests. | Preserve historical record; prompt v8 supersedes. |
| KI-015 | VERIFIED — CODE ONLY | Prompt-v8 hardening | Backend 432/432 and standard CI passed on a936993/a9b946e; model adherence remains incomplete. | Continue screening. |
| KI-016 | IN PROGRESS | Audit-v7 first Backend failure | Run 44018652084: 434/437 due two stale safe fixtures and one audit-version assertion. | Corrected test-only commit de95004; verify new CI. |
| KI-017 | IN PROGRESS | Audit-v7 paired model screen | Run 44018644704 on source 91b7283 active. | Inspect artifact after completion. |

Cloud GitHub development, CI, packaging and CPU screens do not require the user's PC online. Only actual local RTX 4060 proof requires the target PC running local Ollama inference.
