# RadOnc MDT Simulator — Project Status

**Snapshot:** 17 November 2026  
**Repository:** drvishnua/RadOnc-MDT-Simulator  
**Branch:** feature/four-round-mdt-and-performance  
**Latest application/test SHA:** a936993f43be349c0843123941e62cf137199ff7  
**PR #1:** open, draft, unmerged, targets main.  
**Main:** 39a356b8eb09399aa2da1b9b9085965999f5105a (unchanged).

## Execution environment

GitHub development, CI, packaging and hosted CPU model screening run in the cloud and do not require the user's PC online. Local RTX 4060 request-time verification is separate and requires the Windows PC powered on with local Ollama inference running. ChatGPT app network is needed only for chat communication.

## Latest confirmed model result — audit-v6 / prompt-v6

Run 44011921822, artifact 14297362905, source af88bc4:
- Qwen 12/12 parseable, 0 deterministic flags.
- MedGemma 12/12 parseable, 4 deterministic flags: R2 partial-agreement source-attribution inversion; R2 single-source conditional option presented as shared proposition; R3 exact-source quotation omitted; R4 contradictory Chair agreement/no-agreement claims.
- All 24 outputs ended with done_reason=stop; no token-cap truncations. Sampler options matched across models, including top_k=20, top_p=0.95, presence_penalty=1.5, repeat_last_n=64, repeat_penalty=1.1 and num_predict=500.
- Hosted Windows CPU only; GPU measurement NOT_PERFORMED. Both summaries say PENDING_HUMAN_REVIEW, automatic quality score null and clinical accuracy unevaluated. This does not validate clinical accuracy or establish universal repetition robustness.

## Current model-screen development

- Prompt-v7 commit 4f1d923 introduced stronger source-bound R2/R3/R4 rules but accidentally dropped existing asserted safety wording. Its Backend CI failed 8/432. Its hosted model screen 44015305202 is still IN PROGRESS on the v7 prompt. Treat any output as provisional raw evidence, not current acceptance.
- Prompt-v8 implementation commit 6fb1712 restores those safeguards and strengthens exact R2 source-row copying, separates shared information agreement from shared treatment propositions, requires exact verbatim R3 source quotation, and constrains R4 to one consistent proposition outcome.
- The first v8 Backend run on 6fb1712 passed 431/432; the sole failure was a test hyphenation mismatch. Test-only correction a936993 changed that assertion to match the prompt wording.
- Exact-head Backend on a936993 passed **432/432**, deterministic preflight **7/7**. Frontend, Packaging Prerequisites and Security/Dependency/CodeQL passed. Browser E2E, PR Installer and Push Installer remain IN PROGRESS at this checkpoint.
- Prompt-v8 hosted screen 44016121962 (source 6fb1712, identical prompt/script to current a936993; later a936 commit changes only a test assertion) is PENDING behind the older v7 model screen 44015305202 in the concurrency-1 group.

## Outstanding

- Inspect v7 screen 44015305202 and preserve its artifact; do not accept its output as v8 evidence.
- Inspect v8 screen 44016121962 after it starts/completes: manifest/script/corpus hashes, model digests, sampler parity, 12/12 responses/model, completion reasons, flags and every raw response.
- Obtain independent human review; MedGemma is not promoted.
- Resolve the historical 45-role run-9 audit failure (343 findings) without modifying original saved records.
- Complete fresh 45-role R1–R4 acceptance and missing/failed-agent validation.
- Verify RTX 4060 request-time GPU activity locally.
- Retrieve and verify current authoritative guidelines and claim/reference links.
- Obtain independent qualified clinical review. No zero-hallucination or clinical-validity claim is permitted.
- Release remains BLOCKED.

## Source of truth

MASTER_DEVELOPMENT_CHECKLIST.md is the single authoritative detailed status/evidence table. TASK_CHECKLIST.md lists next actions, DECISIONS.md records durable requirements, EXECUTION_LOG.md is chronological, RECOVERY_STATE.md gives the exact resume point, and KNOWN_ISSUES.md lists unresolved defects.
