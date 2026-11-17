# RadOnc MDT Simulator — Project Status

Snapshot: 17 November 2026  
Repository: drvishnua/RadOnc-MDT-Simulator  
Branch: feature/four-round-mdt-and-performance  
Latest application/test SHA: 90186c26571669fc4ffde166fb593325377d76ee  
PR #1: open, draft, unmerged, targets main.  
Main: 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Cloud/device boundary

GitHub development, hosted CI, Windows packaging and hosted CPU model screening do not require the user's PC online. Only real local RTX 4060 request-time verification requires the Windows PC powered on with local Ollama inference running. ChatGPT app connectivity is separate.

## Latest paired model screen — prompt-v8 / audit-v7

- Workflow 44018644704, artifact 14300845455, audit implementation source 91b7283. Manifest: prompt v8, audit v7, Ollama 0.40.14, GitHub-hosted Windows CPU, GPU NOT_PERFORMED.
- Qwen: 12/12 parseable, 0 failed/malformed, 5 deterministic flags across 4 cases: R2 partial-agreement source row order; R2 conditionality plus missing prerequisite-source row; R3 identifier-inventory omission; R3 explicit fabricated-quote rejection omission.
- MedGemma: 12/12 parseable, 0 failed/malformed, 6 deterministic flags across 4 cases: R2 false shared treatment across distinct conditional options; R2 partial-agreement source ledger/attribution omission (two findings); R2 conditionality plus missing source rows (two findings); R3 explicit fabricated-quote rejection omission.
- Both models passed R4-CHAIR-TRACEABILITY-012 in this bounded screen with no audit flags; both produced a consistent no-treatment-proposition Chair outcome. This is not full R4 validation.
- Both models returned 12/12 done_reason=stop, no token-cap truncations, and identical generation settings: temperature 0, seed 73, num_ctx 4096, top_k 20, top_p 0.95, frequency_penalty 0, presence_penalty 1.5, repeat_last_n 64, repeat_penalty 1.1, num_predict 500.
- Qwen digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma digest sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Both summaries remain PENDING_HUMAN_REVIEW; automatic quality score null, clinical accuracy unevaluated, GPU measurement NOT_PERFORMED. No promotion.

## Audit-v7 and exact-head software verification

- Commit 91b7283 added deterministic R2 checks for complete exact saved source-row reproduction, original source order, and false treatment consensus where distinct conditional options are supplied.
- Initial Backend run 44018652084 failed 434/437 due stale safe-response fixtures and one old audit-version assertion. Follow-up 44018911878 still failed 435/437 because an older safe R2 fixture and the mocked complete-run response set still lacked exact source-row wording/order.
- Test-only commit 90186c2 updated the safe R2 fixtures and mocked outputs to include verbatim source text in original order and a valid no-shared proposition statement. Audit logic was not weakened.
- Exact-head Backend run 44020149041 passed **437/437**, 0 failed/errors/skipped. JUnit artifact 14300457106; preflight artifact 14300053331.
- Exact-head Frontend 44020148873, Browser E2E 44020148938, Packaging Prerequisites 44020149274, Windows Installer 44020148842, Security/Dependency/CodeQL 44020148777 and Push Installer 44020142573 all passed.
- Main remains unchanged; PR #1 remains draft/unmerged.

## Remaining gates

Independent human review of both paired model outputs; remediation of R2/R3 model adherence; historical 45-role run-9 integrity failure (343 findings) without modifying original data; fresh 45-role R1–R4 and missing/failed-agent acceptance; RTX 4060 request-time GPU proof; current authoritative guideline retrieval and claim linkage; independent qualified clinical review. No zero-hallucination or clinical-validity claim. Release remains BLOCKED.

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed verification table. TASK_CHECKLIST.md lists next actions; DECISIONS.md records durable requirements; EXECUTION_LOG.md is chronological; RECOVERY_STATE.md gives the exact resume point; KNOWN_ISSUES.md lists unresolved defects.
