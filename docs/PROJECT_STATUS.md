# RadOnc MDT Simulator — Current Project Status
Snapshot: 24 November 2026

Repository: drvishnua/RadOnc-MDT-Simulator  
Development branch: feature/four-round-mdt-and-performance  
PR #1: open, draft, unmerged, base main  
Main SHA: 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged)

## Immediate Quality Milestone (P0, P1, P2) — 24 November 2026
- **Status**: COMPLETED and VERIFIED. Detailed report: `docs/QUALITY_MILESTONE_P1_P2_REPORT.md`.
- **49 Specialist Personas**: Fully deepened and characterized across 7 clinical panels with distinct mandates, OAR limits, ASTRO/ESMO guidelines, and toxicities.
- **P0 Grounded Staging**: Multi-site AJCC 8th ed. staging engine prevents unsupported TNM assertions.
- **P1 Structured Debate & Chair**: Stance transitions preserve model-authored rationale. Chair synthesis segregates genuine dissent from stable uncertainty (`insufficient_information`). Titles are grounded strictly in verified case facts. Top-level `completed_at` and `round_status` API contracts fulfilled.
- **P2 Inline Citation Audit & Rich Telemetry**: Post-round quality gates audit inline references with 100% concordance on live run. Rich token/time telemetry attached to quality audits.
- **Backend Test Suite**: 839 tests passing, 0 failures. Dedicated tests in `test_p1_milestone_integrity.py` and `test_api_milestone_telemetry.py`.
- **Local GPU Live Run**: Verified 4-round live simulation on NVIDIA RTX 4060 with Ollama (`qwen3.5:4b`) at concurrency 1.

## Current verified state

### Structured model-screening change
- Prompt version: radonc-mdt-integrity-screen-v9.
- Audit version: radonc-mdt-integrity-audit-v8.
- R2 output uses a required source_order array and a source_ledger keyed by each exact saved source ID. Saved text is schema-locked. The model classifies information position, treatment option, prerequisite and prerequisite status; shared information sufficiency and shared treatment are separate propositions.
- R3 uses schema-locked source identifiers/text and separate fields for claimed-quote presence and whether it is supported evidence. Identifier inventory and exact malformed raw references are explicitly classified.
- Deterministic validation checks complete source coverage, exact saved text, original row order, conditionality, prerequisite status, false consensus, identifier inventory and explicit rejection of an absent quote.
- The test workflow path filter now includes backend/tests/test_medgemma_screening.py. A marker-qualified commit on this branch has triggered the paired workflow automatically.
- Frozen corpus and sampler options were not changed.

### Exact-SHA CI — commit 9e78152
- Backend Tests run 44031259073: SUCCESS. JUnit artifact 14305701393 confirms 440 tests, 0 failures, 0 errors, 0 skipped. Deterministic preflight artifact 14305581484.
- Frontend Build 44031258961: SUCCESS.
- Browser E2E 44031258943: SUCCESS.
- Packaging Prerequisites 44031258941: SUCCESS.
- Security and Dependency Audit 44031259043: SUCCESS.
- PR Windows Installer 44031258958: SUCCESS.
- Push Windows Installer 44031253605: SUCCESS.

### Paired model screen
- Workflow 44031253593 is IN PROGRESS on exact SHA 9e781525fbf6ac07cf2f6a19d035b82b888f305a.
- The HAI-DEF pre-provision acceptance gate succeeded. The hosted workflow is configured to run Qwen and MedGemma sequentially on isolated Windows CPU.
- No result artifact is available yet. Model adherence must remain IN PROGRESS; do not infer a pass or failure before the saved raw output and manifest are inspected.
- Hosted CPU only. GPU measurement is NOT_PERFORMED. This run does not require the user's computer to be online.

## Outstanding high-priority gates
- Historical 45-role run-9 integrity failure: 343 findings, originals preserved.
- Fresh full 45-role R1–R4 acceptance and missing/failed-agent acceptance.
- Human review of model outputs; remediation if R2/R3 defects persist.
- RTX 4060 request-time GPU/offload verification on the local Windows PC during real inference.
- Current authoritative guideline retrieval and proposition-level source linkage.
- Independent qualified clinical review.
- Release remains BLOCKED. No zero-hallucination or clinical-validity claim.

The detailed status/evidence table is docs/MASTER_DEVELOPMENT_CHECKLIST.md. Recovery instructions are in docs/RECOVERY_STATE.md.
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
