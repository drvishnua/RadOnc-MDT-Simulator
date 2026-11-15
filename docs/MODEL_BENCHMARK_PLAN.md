# Model Benchmarking and Selection Plan

**Status:** Proposed protocol; no model change authorised or performed.
**Current reference model:** `qwen3.5:4b`
**Target environment:** Windows self-hosted runner, NVIDIA RTX 4060 Laptop GPU (8 GB), local Ollama.
**MDT workload:** 45 R1 + 45 R2 + 45 R3 + 1 Chair = 136 persisted contributions; configured concurrency remains 1.

## MedGemma 1.5 candidate facts verified from primary model documentation and Ollama registry — 16 November 2026

**Google model identity**
- Official Google model identifier: `google/medgemma-1.5-4b-it`.
- Google model version: `1.5.0`, released 13 January 2026.
- Google describes this as a 4B multimodal instruction-tuned model (text + vision; text output), based on Gemma 3, with a stated context length of at least 128K tokens and maximum output length of 8,192 tokens.
- Primary source: https://developers.google.com/health-ai-developer-foundations/medgemma/model-card

**Ollama package candidate**
- Ollama Library tag: `medgemma1.5:4b-it-q4_K_M`.
- The Ollama registry lists the package as Gemma 3, 4.3B parameters, Q4_K_M, approximately 3.3 GB, text + image input, with a 128K context-window listing.
- The public tag listing shows short identifier `433252621ab1`. This is **not** accepted as the full immutable digest. The exact full SHA-256 digest must be captured from the target Ollama instance's `/api/tags` response after pulling the package; also save `ollama show --modelfile`, `/api/version`, and package metadata. Do not treat the mutable tag or short identifier as a reproducibility pin.
- Registry sources: https://ollama.com/library/medgemma1.5/tags and https://registry.ollama.com/library/medgemma1.5%3A4b

**Licence and distribution status**
- MedGemma is governed by Google's Health AI Developer Foundations Terms of Use, not a conventional OSI open-source model-weight licence. Google describes HAI-DEF models as open-weight, not open-source.
- The HAI-DEF terms contain conditions for redistribution/hosted-service distribution, incorporation and notification of use restrictions, provision of the terms to recipients, and applicable regulatory authorisation. The terms also restrict certain uses that could cause a health regulator to deem Google the manufacturer of a medical device.
- This is a factual licence-screening note, **not legal clearance**. Commercial use, hosting, redistribution, installer bundling and the simulator's intended-use boundary require a documented legal review before release.
- Sources: https://developers.google.com/health-ai-developer-foundations/terms and https://developers.google.com/health-ai-developer-foundations/faqs

**Material model limitation for this product**
- Google's model card states that MedGemma has **not been evaluated or optimised for multi-turn applications**. It also states that outputs are preliminary, require independent verification/clinical correlation, and are not intended to directly inform clinical diagnosis, patient management or treatment recommendations.
- This limitation maps directly to our multi-round R1–R4 workflow. It is a major evaluation risk, not a reason to assume MedGemma is better or worse than Qwen.
- Source: https://developers.google.com/health-ai-developer-foundations/medgemma/model-card#use-and-limitations

**Hardware interpretation**
- Google lists an approximate Q4_0 static weight footprint of 3.4 GB for MedGemma 4B; the Ollama Q4_K_M registry package is listed at approximately 3.3 GB. Static weights do not include runtime overhead or KV cache.
- On the project's RTX 4060 8 GB, fit and speed are **unverified**. Context length, KV cache, Windows display/driver reservation and runtime overhead can require additional memory. Only request-time telemetry and Ollama offload evidence can establish GPU inference.
- Source: https://developers.google.com/health-ai-developer-foundations/faqs#hardware-requirements

**Current decision:** The exact candidate tag is identified for controlled screening, but the local full digest, installed runtime compatibility, actual GPU offload, legal approval and quality performance have not been verified. Qwen remains the unchanged baseline. No model pull or production configuration change is authorised by this documentation update.

## 1. Objective and decision rule

Identify whether an alternative model or deployment improves end-to-end MDT latency while maintaining or improving the simulator's safety, traceability, schema reliability and four-round behaviour.

Do not select a model on benchmark speed, medical vocabulary, parameter count or a single attractive answer. A candidate that breaches a pre-agreed critical safety gate is rejected regardless of throughput.

No production model change is permitted until:
1. the exact model tag/digest and inference configuration are recorded;
2. the same controlled case corpus and prompt versions have been evaluated;
3. automated integrity checks and independent blinded clinical review are complete;
4. the full 136-contribution workflow has been compared for each finalist;
5. the selected candidate passes frontend/backend integration and persistence tests; and
6. the change is explicitly approved.

## 2. Candidate matrix

| Candidate | Initial environment | Purpose |
|---|---|---|
| Qwen 3.5 4B | Local Ollama | Control/baseline; retain unchanged during evaluation |
| MedGemma 1.5 4B | Local Ollama, if supported by the installed Ollama/runtime stack | Medical-domain candidate; validate multi-turn MDT behaviour rather than assuming suitability |
| Gemma 4 E4B | Local Ollama, quantisation and memory fit to be measured | General-purpose local candidate |
| Larger MedGemma / Gemma / Qwen variant | Isolated cloud GPU or approved hosted inference | Second-stage quality/latency comparison; no identifiable patient data |

Before a run, pin the exact tag and immutable model digest, quantisation, model file size, context length, template, Ollama version, GPU driver, and runtime configuration. A model name alone is not a reproducible identifier. Do not download or change the active model during a live MDT run.

The candidate list is exploratory, not a claim that any candidate is more clinically accurate. MedGemma model documentation describes it as a starting point for downstream healthcare applications and notes important validation limitations, including multi-turn use. Review the current model card before a test:
- [Google MedGemma model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card)
- [Google DeepMind MedGemma overview](https://deepmind.google/models/gemma/medgemma/)
- [Google Gemma documentation](https://ai.google.dev/gemma/docs)

## 3. Controlled test corpus

Use only entirely artificial, non-identifiable educational cases. Each case must have a versioned source snapshot and a documented expected-data register. The same exact case JSON, role profiles, prompts, schema, temperature, token limits and preceding-round inputs must be used for every model.

The screening corpus should cover at least:
- complete and incomplete demographic/staging fields, including absent age and absent stage group;
- incomplete T/N/M staging and non-inference of N0/M0;
- explicit structured/free-text contradictions;
- pathology, imaging and investigation data absent or only partially reported;
- resectability and fitness not established;
- absent patient preferences, goals, consent and social context;
- conditional options with explicit prerequisites;
- genuine disagreement and a minority position that evolves between rounds;
- failed or malformed model responses, retries and incomplete role contributions;
- source-reference boundary tests, including unsupplied peers and malformed/broad identifiers.

For initial screening, use a fixed representative role subset spanning medical oncology, radiation oncology, surgery, radiology, pathology, nursing/allied health, supportive care, governance and patient-perspective roles. This is only a model-screening sample; it must not be described as a completed 45-role MDT or used to calculate consensus. Run the full 45-role / 136-contribution workflow on finalists.

Repeat the same evaluation at least three times per candidate to measure run-to-run variability. Keep a separate untouched holdout set for final confirmation to reduce prompt/test-set overfitting.

## 3A. Zero-hallucination requirement: strict acceptance, honest limits

The product requirement is **zero tolerance for detected critical fabrication**. A candidate fails the evaluation if any run contains a material invented patient fact, unsupported staging/T/N/M assertion, fabricated investigation/pathology result, unsupported negative finding, invented source/quotation, false consensus, dropped mandatory prerequisite, fabricated missing-agent contribution, or untraceable Chair conclusion.

This is a fail-closed quality gate:
- Keep every material patient/case claim tied to an original supplied case field or an exact saved contribution.
- Unknown information remains unknown; do not infer a normal/negative result.
- Generated interpretation must remain visibly an interpretation and must not be promoted into a verified case fact.
- Unsupported or untraceable claims are flagged, quarantined from the canonical Chair input, or cause the report to fail validation.
- Chair calculations, counts, provenance and consensus are deterministic backend operations, not LLM decisions.
- Do not waive a critical finding because a candidate is medically fluent, faster or has a higher aggregate score.

**Important scientific limit:** No finite test set, model card, deterministic validator or human review can prove that a generative model will never hallucinate on every possible future input. Therefore the product must not advertise or claim a mathematical guarantee of "zero hallucinations". The defensible claim is that the system is engineered for zero tolerance of detected critical fabrication, with explicit abstention, source-binding, independent review and continuing monitoring. Any detected critical failure blocks model promotion; a clean test sample is evidence only for that tested corpus, prompts, model digest and run configuration.

The Google model card adds a specific risk: MedGemma has not been evaluated or optimised for multi-turn applications. The benchmark must therefore test round-separated context handoff, position changes, dissent preservation and Chair synthesis rather than extrapolating from single-turn medical benchmarks.

## 4. Quality and safety evaluation

### Deterministic checks

Run the existing deterministic case-integrity, schema, source-reference, round-provenance, failed-response and Chair-report validators against every saved output. Record:
- unsupported patient facts, age, demographics, stage group and T/N/M claims;
- contradictions that were silently resolved or not surfaced;
- missing-data converted to negative/normal findings;
- unsupported resectability, performance-status, treatment suitability or preference assertions;
- conditional recommendations whose prerequisites were dropped;
- invalid or unsupplied citations and source IDs;
- missing or duplicated role contributions;
- wrong-round input leakage;
- Chair statements not traceable to saved R1–R3 records;
- invalid position distributions, consensus, unanimity or dissent handling;
- malformed JSON, schema errors, retries and failed outputs.

Do not relax a deterministic checker to make one candidate pass. If a checker is itself defective, fix and test it against all candidates before scoring them.

### Independent review

Use blinded reviewers who do not know the model identity. Clinical reviewers should assess oncology reasoning, relevance to the supplied facts, uncertainty, material omissions, conditionality and whether the Chair synthesis accurately represents its sources. A qualified clinical MDT review is required before any claim of clinical suitability.

Do not use a language model's self-rating or the model's own assertion of guideline compliance as evidence of correctness. Evidence retrieval and citation verification are not connected yet; model outputs must not be treated as independently evidence-verified.

### Pre-registered critical gates

Before evaluation, agree and document the critical-error taxonomy and acceptance thresholds with the project owner and qualified reviewers. At minimum, any fabricated material patient fact, unsupported definitive stage/N0/M0, dropped mandatory condition, invented source, loss of a material minority view, or untraceable Chair conclusion is a critical finding requiring review. Do not trade such a failure against a faster runtime.

## 5. Performance and hardware measurements

For every run, collect:
- per-generation wall-clock latency, time to first token if available, prompt/evaluation token counts and tokens/second;
- per-round elapsed time and total elapsed time;
- retries, malformed responses, timeouts and failure rate;
- CPU utilisation, memory, GPU utilisation, GPU memory, temperature and power at regular intervals;
- Ollama `/api/ps` model residency and GPU-layer/offload details;
- exact Ollama logs and model/runtime configuration.

Measure cold-load and warm-load behaviour separately. Keep local concurrency at 1 throughout the baseline. Do not test concurrency increases until one-model sequential measurements and quality gates are complete; any later concurrency experiment must use a separate controlled benchmark.

Report medians, ranges and variability across repeated runs. Do not extrapolate 136-call duration solely from one generation. Run a full 136-contribution test for each finalist and verify all 136 saved records, round inputs, Chair provenance and report artefacts.

System-wide GPU utilisation is not by itself proof of Ollama attribution. Correlate telemetry timestamps with requests, process/runtime information and Ollama offload reporting. VRAM allocation or model residency alone does not prove active inference.

## 6. Cloud and data protection

Cloud testing is a separate phase. Use only wholly artificial test cases, with no real patient identifiers or confidential hospital data. Review provider data retention, training use, region, access controls, encryption, contractual terms, and applicable privacy/security obligations before any integration. Do not add cloud credentials or provider endpoints to the production application as part of a benchmark.

Keep a local fallback option, but do not assume local and cloud outputs are interchangeable. Re-run the same quality, provenance and schema tests for every deployed provider/model version.

## 7. Reproducibility record

Each benchmark record must include:
- Git commit SHA, branch, clean/dirty working-tree state and prompt/schema revision;
- case corpus version and case snapshot hashes;
- role subset or full role catalogue version;
- model name, immutable digest, quantisation, Ollama/runtime versions and generation options;
- operating system, CPU, RAM, GPU model/driver and power mode;
- exact run ID, timestamps, round-level results, retries, failures and saved artefact hashes;
- machine-readable safety findings and blinded reviewer results;
- raw telemetry and calculation method for reported timing summaries.

Never merge results from different code SHAs, prompt revisions, case versions or model digests into one comparison without clearly separating the strata.

## 8. Staged execution

1. **Baseline capture:** verify current Qwen model digest/configuration, hardware telemetry and repeatable representative-case results.
2. **Local screening:** test Qwen, MedGemma 1.5 4B and Gemma 4 E4B on identical screening cases, sequentially.
3. **Independent review:** blinded clinical review and deterministic audit; reject candidates that fail a critical gate.
4. **Finalist validation:** run the full 136-contribution workload three times per finalist, inspecting every round and the saved Chair artefacts.
5. **Cloud comparison:** only after privacy/security review, test larger candidates with the same artificial corpus and evaluation rubric.
6. **Selection proposal:** compare quality first, then latency, GPU/resource footprint, cost, reliability and operational complexity. Present the evidence and trade-offs for approval.
7. **Controlled integration:** only after approval, change configuration behind a reversible model setting, retain the Qwen baseline and rerun regression, persistence, live workflow and hardware tests.


## 10. MedGemma 1.5 screening protocol and frozen synthetic corpus

The initial synthetic screening corpus is committed at:
`backend/tests/fixtures/medgemma_model_integrity_screening_v1.json`.

It contains 12 software-integrity scenarios spanning:
- unsupported TNM/stage inference and fabricated case facts;
- unresolved contradictions and untrusted prompt-like case text;
- false or overbroad R2 consensus and lost conditional prerequisites;
- invented/malformed source IDs and fabricated source quotations;
- negation/false-positive handling;
- missing-agent fabrication; and
- untraceable Chair synthesis.

The corpus has a structural pytest check. That test proves only that the fixture is present, explicitly synthetic, and structurally complete. **It does not test model behaviour, clinical accuracy, or zero hallucinations.**

Before inference:
1. Obtain the full local model digests for both Qwen baseline and MedGemma from the same target Ollama runtime and store the complete `/api/tags` records.
2. Confirm the Ollama version, Modelfile/template, model options and exact generated request body for each model.
3. Confirm no production app configuration is changed; screening calls must explicitly select the candidate model and save outputs to a separate benchmark directory/database.
4. Run a short, bounded screening batch sequentially, at concurrency 1. Stop on timeout, resource exhaustion, malformed outputs or any critical fabrication. Do not start the 136-contribution run before screening is reviewed.
5. Repeat the same corpus at least three times per model, with order alternated or otherwise controlled to minimise warm-cache/order effects.
6. Run deterministic case-integrity, schema, source-reference and Chair checks on every output. Keep raw outputs immutable.
7. Have reviewers blinded to model identity assess relevant clinical-language claims and omissions. The corpus alone is not a clinically validated answer key.
8. Do not promote a model if any critical failure is observed. A zero-failure result on this finite screening set is not proof of zero future hallucination risk.
9. Only after screening passes should a finalist progress to representative-role live workflow tests and, later, the full 136-contribution comparison.

**No GPU or model-pull result is implied by this protocol.** Do not infer that the Ollama package is loaded on the RTX 4060 because the public registry lists its size or architecture.

## 9. Current state

No model has been installed, changed, selected or benchmarked by this plan. The MedGemma candidate tag is now identified from the Ollama Library, but its full local digest, real runtime compatibility, GPU inference and MDT quality remain unverified. No fresh live 136-contribution run or current GPU verification is claimed. The existing Qwen model remains the control and production configuration until a separate, verified selection decision.
