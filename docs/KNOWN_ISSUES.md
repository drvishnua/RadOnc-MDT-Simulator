# RadOnc MDT Simulator — Known Issues

Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 90186c26571669fc4ffde166fb593325377d76ee

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Early superseded screen | Run 44000326185; three MedGemma outputs truncated at 500 tokens. | Preserve artifact. |
| KI-002 | FAILED | Earlier v6/audit-v4 screen | Run 44000583529; three MedGemma truncations. | Preserve raw output. |
| KI-003 | FAILED | Historical 45-role run-9 integrity | Audit revalidation reported 343 findings (R1 11, R2 41, R3 271, R4 20). | Preserve original records; fresh full acceptance needed. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screens do not prove full system behaviour. | Controlled fresh full run and audit. |
| KI-005 | NOT STARTED | RTX 4060 request-time inference unproven | Hosted screens CPU only. | Real local inference while recording nvidia-smi, ollama ps/offload and latency. |
| KI-006 | NOT STARTED | Guideline retrieval/claim verification | No current verified guideline corpus. | Retrieve and link authoritative sources. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No review artifact. | Obtain qualified review. |
| KI-008 | IN PROGRESS | Development Monitor live GitHub API dependency | Production browser uses public API subject to network/rate limits. | Verify live browser state/stale handling. |
| KI-009 | IN PROGRESS | MedGemma repetition robustness | Latest paired runs had 12/12 stop outputs; earlier runs truncated. | Continue monitoring; bounded samples only. |
| KI-010 | IN PROGRESS | Historical MedGemma HTTP 500 pull issue | Run 44004929958 failed during pull; later pulls succeeded. Root cause unknown. | Investigate if reproduced. |
| KI-011 | VERIFIED | Paired sampler parity | Run 44018644704 shows identical generation options and 24/24 stop outputs. | Preserve settings. |
| KI-012 | IN PROGRESS | Model semantic defects R2/R3 | Audit-v7 run 44018644704: Qwen 5 flags; MedGemma 6 flags. Both quote rejection omissions; MedGemma false consensus and source ledger omissions. | Further prompt/model work and independent review. |
| KI-013 | VERIFIED — SOFTWARE | Audit-v6 safe-negation detector | Qwen no-shared proposition negative wording no longer falsely flagged. | Retain regression. |
| KI-014 | FAILED — SUPERSEDED | Prompt-v7 regressed asserted prompt phrases | Backend 44015312495 failed 8 tests. | Preserve history; v8 supersedes. |
| KI-015 | VERIFIED — BOUNDED CODE | Prompt-v8 R2/R3/R4 hardening | Backend 432/432 on a936993; output adherence remains incomplete. | Keep model acceptance open. |
| KI-016 | VERIFIED — SOFTWARE | Audit-v7 deterministic reviewer | Backend 437/437 on 90186c2; exact rows/order and incompatible-option consensus checks tested. | Verify continued behaviour in future screens. |
| KI-017 | IN PROGRESS | R2/R3 model adherence | Latest audit-v7 paired screen has 11 flags across both models; R4 traceability case passed only in this bounded screen. | Address model failures; retain blinded review. |

Cloud GitHub development, CI, packaging and CPU model screens do not require the user's PC online. Local RTX 4060 proof requires the target PC powered on with real Ollama inference running.


| ID | Status | Issue | Evidence / next action |
|---|---|---|---|
| KI-018 | IN PROGRESS | Prompt-v9/audit-v8 paired model adherence not yet known | Run 44031253593 active on exact SHA 9e78152; inspect immutable artifacts after completion. |
| KI-019 | VERIFIED | Screening workflow path filter missed test-only changes | Test path added to .github/workflows/model-integrity-screening.yml; marker-qualified run 44031253593 confirmed automatic trigger. |
| KI-020 | VERIFIED — BOUNDED SOFTWARE | R2 source ordering is explicitly represented | Required source_order array and original-order validator; 440 tests pass on 9e78152. Model must still demonstrate adherence. |
| KI-021 | FAILED — PRIOR MODEL BEHAVIOUR | Audit-v7 Qwen/MedGemma R2/R3 adherence defects | Run 44018644704, artifact 14300845455; v9 retest active. Do not close until reviewed output demonstrates remediation. |
# RadOnc MDT Simulator — Known Issues

Snapshot: 17 November 2026  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 90186c26571669fc4ffde166fb593325377d76ee

| ID | Status | Issue | Evidence / impact | Next action |
|---|---|---|---|---|
| KI-001 | FAILED | Early superseded screen | Run 44000326185; three MedGemma outputs truncated at 500 tokens. | Preserve artifact. |
| KI-002 | FAILED | Earlier v6/audit-v4 screen | Run 44000583529; three MedGemma truncations. | Preserve raw output. |
| KI-003 | FAILED | Historical 45-role run-9 integrity | Audit revalidation reported 343 findings (R1 11, R2 41, R3 271, R4 20). | Preserve original records; fresh full acceptance needed. |
| KI-004 | IN PROGRESS | No current full 45-role R1–R4 acceptance | Bounded 12-case screens do not prove full system behaviour. | Controlled fresh full run and audit. |
| KI-005 | NOT STARTED | RTX 4060 request-time inference unproven | Hosted screens CPU only. | Real local inference while recording nvidia-smi, ollama ps/offload and latency. |
| KI-006 | NOT STARTED | Guideline retrieval/claim verification | No current verified guideline corpus. | Retrieve and link authoritative sources. |
| KI-007 | NOT STARTED | Independent qualified clinical review | No review artifact. | Obtain qualified review. |
| KI-008 | IN PROGRESS | Development Monitor live GitHub API dependency | Production browser uses public API subject to network/rate limits. | Verify live browser state/stale handling. |
| KI-009 | IN PROGRESS | MedGemma repetition robustness | Latest paired runs had 12/12 stop outputs; earlier runs truncated. | Continue monitoring; bounded samples only. |
| KI-010 | IN PROGRESS | Historical MedGemma HTTP 500 pull issue | Run 44004929958 failed during pull; later pulls succeeded. Root cause unknown. | Investigate if reproduced. |
| KI-011 | VERIFIED | Paired sampler parity | Run 44018644704 shows identical generation options and 24/24 stop outputs. | Preserve settings. |
| KI-012 | IN PROGRESS | Model semantic defects R2/R3 | Audit-v7 run 44018644704: Qwen 5 flags; MedGemma 6 flags. Both quote rejection omissions; MedGemma false consensus and source ledger omissions. | Further prompt/model work and independent review. |
| KI-013 | VERIFIED — SOFTWARE | Audit-v6 safe-negation detector | Qwen no-shared proposition negative wording no longer falsely flagged. | Retain regression. |
| KI-014 | FAILED — SUPERSEDED | Prompt-v7 regressed asserted prompt phrases | Backend 44015312495 failed 8 tests. | Preserve history; v8 supersedes. |
| KI-015 | VERIFIED — BOUNDED CODE | Prompt-v8 R2/R3/R4 hardening | Backend 432/432 on a936993; output adherence remains incomplete. | Keep model acceptance open. |
| KI-016 | VERIFIED — SOFTWARE | Audit-v7 deterministic reviewer | Backend 437/437 on 90186c2; exact rows/order and incompatible-option consensus checks tested. | Verify continued behaviour in future screens. |
| KI-017 | IN PROGRESS | R2/R3 model adherence | Latest audit-v7 paired screen has 11 flags across both models; R4 traceability case passed only in this bounded screen. | Address model failures; retain blinded review. |

Cloud GitHub development, CI, packaging and CPU model screens do not require the user's PC online. Local RTX 4060 proof requires the target PC powered on with real Ollama inference running.
