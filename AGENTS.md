# RadOnc MDT Simulator — Agent Operating Instructions

Read this file before making project changes. It is the repository-level continuity and safety contract.

## Mission
Build a reliable, auditable, locally runnable 45-role, four-round Radiation Oncology MDT **educational simulator**. Prioritise case integrity, reasoning quality, evidence traceability and safety over speed or superficial consensus. This is not a clinical decision-support system and does not prescribe treatment.

## Start-of-session continuity
- Re-read this file and relevant project docs/recent handover notes.
- Inspect live repository state: branch, HEAD, PR status, review threads, workflows and latest checks. Never rely on remembered hashes/status.
- For local-state claims, inspect the self-hosted runner logs and `.radonc-sync-state.json` in the real `Source` directory.
- Label verified facts, inferences and unknowns separately. Prior assistant output is not evidence.
- Keep the task aligned to the current milestone; avoid unrelated redesign.

## Source-of-truth order
1. Exact user-provided case text.
2. Immutable, hash-verified run case snapshot.
3. Saved agent outputs from each round.
4. Chair report and per-round metadata.
5. Current source code and tests.
6. CI/runtime logs and telemetry.
Never silently reconcile conflicts or fill gaps.

## Non-negotiable case-integrity rules
- Missing/not reported is not confirmed absent. Empty arrays do not establish a negative finding.
- Do not invent sex, comorbidities, smoking/alcohol, prior treatment, patient goals, ECOG/KPS, TNM stage, nodal status, metastatic status, pathology or imaging.
- Preserve raw case text. If free text conflicts with structured fields, flag both and retain provenance; do not silently promote an extraction to a confirmed fact.
- Distinguish observed facts, interpretations, assumptions/hypotheses and unknowns.
- Use explicit data states where useful: present, confirmed_absent, not_reported, uncertain, conflicting.
- Preserve the case snapshot hash and ensure all 45 roles/rounds use the same snapshot.

## Clinical and evidence safety
- Never present an inferred stage as fact. A tumour size/location phrase alone does not establish TNM stage.
- Do not turn age alone into treatment eligibility/ineligibility.
- Do not provide patient-specific treatment instructions or claim guideline concordance without traceable, current sources.
- Evidence retrieval is not connected unless it is implemented, sources are retrieved, and claim/reference linkage is validated.
- JSON validity, completed runs and passing tests do not prove clinical accuracy. Qualified clinical review is required.
- Preserve `educational_simulation_only` and `not_a_treatment_instruction: true`.

## Four-round architecture
Retain 45 unique roles through:
1. Independent assessment: position, conclusion, preferred educational option, facts, assumptions, unknowns, alternatives, evidence gaps and confidence.
2. MDT debate: specific role-to-role agreements/challenges; explicit old-position → new-position transition and reason when a position changes. Do not inflate confidence or manufacture agreement.
3. Adversarial review: challenge assumptions/staging, evidence, patient/family context, feasibility/resources, safeguarding and governance; store structured challenges, risks, unknowns and changes, not just prose.
4. Chair synthesis: reconcile saved records, not model prose alone.

### Consensus / Chair
- Position labels are descriptive, not votes. Conditional is not support; insufficient_information is not opposition.
- Consensus requires agreement on the same explicit proposition/educational option.
- Never claim unanimity from uniform role labels alone.
- Minority/dissent should capture genuine distinct views, material challenges and position changes. Do not populate it with every stable insufficient-information role; put stable uncertainty in uncertainty/missing-information sections.
- Keep role IDs and round numbers traceable. Avoid truncated source summaries.
- Generate titles only from verified facts; do not insert unconfirmed stage.

## Metrics and performance
- Distinguish 45 unique roles from 136 generation records (45 R1 + 45 R2 + 45 R3 + 1 Chair).
- Inspect nested arrays and round_status; top-level total_agents/updated_at may cover only Round 1.
- Wall-clock runtime = Chair completion timestamp − run creation timestamp. Per-agent duration sums are not wall time and may overlap.
- Report per-round wall time, role counts, failures, retries, position distributions and output-quality metrics separately.
- Keep concurrency at 1 unless repeatable same-workload benchmarks show a safe improvement. A prior two-request benchmark was slower concurrently than sequentially.
- Track prompt/output tokens, tokens/sec, latency, retries, schema failures and processor placement where feasible.

## Ollama / GPU
Last known target: Windows laptop, RTX 4060 Laptop GPU (8 GB), driver 591.74, Ollama 0.40.14, `qwen3.5:4b`, CUDA v13 backend. Reverify before relying on this.
- Prove placement with `ollama ps`; use `nvidia-smi` for utilization/VRAM/process; use Ollama server logs for CUDA discovery/offload. Task Manager 0% alone proves nothing.
- Last diagnostic saw 100% GPU placement and 33/33 layers offloaded, with an intermittent CUDA discovery watchdog timeout followed by successful initialisation.
- Prefer read-only diagnostics. Do not start a second inference during an active batch.
- Do not restart Ollama, kill a model runner, unload models, alter CUDA variables, upgrade Ollama, or reinstall drivers during a simulation unless explicitly authorised.
- Do not change context, quantisation, concurrency or GPU settings without before/after performance and schema-quality tests.

## GitHub / laptop workflow
- Repository: `drvishnua/RadOnc-MDT-Simulator`.
- Development branch: `feature/four-round-mdt-and-performance`; PR #1.
- Keep PR #1 open and draft. Never merge `main`, deploy or release without explicit permission.
- Recheck live branch HEAD before every write.
- Feature pushes trigger the self-hosted `RadOnc-Laptop` sync. Claim local Source is current only after the manifest confirms exact branch and commit.
- `Source` is a runtime mirror, not necessarily the user's separate local Git worktree.
- Sync does not prove running modules reloaded. Verify processes/services and restart only when necessary and safe.
- Preserve sibling `AI_Models`, Ollama models, runner installation, database/simulation records, configuration, dependencies, logs and unrelated local files. Sync must be additive/update-only and refuse unmarked destinations.
- Avoid competing jobs on the single self-hosted runner; account for queueing and concurrency cancellation.

## Engineering definition of done
1. Inspect relevant implementation/tests first; make the smallest coherent change.
2. Add regression tests for the reported defect and adjacent edge cases.
3. Run focused tests, backend suite, frontend type-check/build as relevant.
4. Verify checks against exact latest HEAD; accurately disclose cancellations/failures.
5. Verify local sync/runtime when in scope.
6. Update docs and PR with exact changes, commit, test evidence and limitations.
7. Review comments/threads; resolve only when demonstrably addressed.

A structural pass is not a clinical-quality pass. A model loaded on GPU is not evidence-grounded reasoning. A completed run is not proof the conclusions are sound.

## Assistant behaviour
Execute work directly when tools allow. Do not fabricate results, local state, clinical facts, evidence or verification. Do not ask the user to repeat known information. For substantial tasks, state the plan and share meaningful progress. End with exact state, limitations and next priority.

## Immediate quality milestone
Fix: (P0) case-fact provenance and structured input semantics; prevent unsupported TNM/demographic claims. Then (P1) structured debate position-change traceability, Chair minority selection, title generation, and top-level completion timestamps. Then (P2) evidence retrieval/citation verification and richer performance telemetry. Re-run the same synthetic case and compare against the documented baseline. Keep PR #1 draft and `main` untouched.
