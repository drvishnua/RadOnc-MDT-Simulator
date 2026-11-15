# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Latest application code/test commit:** `bc114eb9935ebf8b097d880dd2906dd69d73bc0e` (313/313 backend tests and 6/6 preflight; six standard workflows passed). All six standard workflows also passed on exact documentation-only HEAD `1ade8660c769f2135e441016a7fff19498165cee`. A later documentation-only checklist/status refresh has been pushed after that verification; on the refreshed snapshot, Packaging Prerequisites and Windows Installer Build are in progress, Backend Tests and Security Audit are queued, and no application code changed. Run-16 lineage and model-digest canonicalization regressions remain in the tested 313-test suite. Prior live validator fix `7671f3c` remains tested.

Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| Four-round R1–R4 architecture/data flow | IN PROGRESS | Implemented with regression coverage; full current-head 45-role live acceptance outstanding. |
| R1 independent assessment | IN PROGRESS | Run `43714529807` / simulator run `c4592dbb-ecc7-4007-9125-d0baaed9abb0`, runtime SHA `4683b0767bf5cade408e85ec31ef248b34e5321e`, saved 45/45 R1 contributions; all 45 positions were `insufficient_information`. Artifact audit: 11 case-integrity flags across 7 roles (unsupported T1 x7, N0 x2, M0 x2). Detected defects remain quality-gate failures, not accepted facts. Earlier run `43698959463` retained 16 R1 flag instances across 13 roles. |
| R2 debate and peer sourcing | IN PROGRESS | Run `43714529807` saved 45/45 R2 contributions, all positions `insufficient_information`. Artifact audit: 40 source-reference flag instances across 40/45 roles (13 unique strings), predominantly non-attributable R1 role ranges; one case-integrity flag on MO-07 for a categorical `is contraindicated` assertion unsupported by missing case information. Earlier run `43698959463` had 30 R2 source-reference flags across 30 roles. |
| R3 adversarial review | IN PROGRESS | Original run `43714529807` saved 17/45 R3 roles; 27 queued and SO-01 running. All 17 positions were `insufficient_information`; 84 source-reference flags occurred across 8 roles (50 unique strings), and 16 risk entries/31 challenges were saved but are not provenance-accepted. First continuation run `43753381558` stopped before Python inference because the installed model digest was returned as bare SHA-256 hex while the guard required the sha256: prefix; no R3 data was changed. Corrected guard in `bc114eb` canonicalizes bare/prefixed SHA-256 values before exact model comparison. Second continuation run `43753957255`: job setup, checkout, Python setup, dependency installation and checkpoint artifact restore succeeded; combined Ollama/R3/R4 step remains IN PROGRESS. Its latest queried GitHub run state is still `in_progress`; step logs and output artifact are not yet available. No live R3 continuation inference is yet confirmed because current step logs are unavailable. |
| R4 Chair synthesis | IN PROGRESS | No R4 report exists from source run #16. First continuation attempt `43753381558` failed before Python inference. Second continuation [run `43753957255`](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255) remains in progress at its combined Ollama/R3/R4 step; Chair generation must wait for all 45 R3 contributions and deterministic round checks. Earlier Chair report from `43698959463` remains historical and failed validator acceptance. |
| Clinical safety/unsupported claims | IN PROGRESS | Deterministic audits and TNM regression coverage exist; not exhaustive clinical validation. Run `43698959463` surfaced model-generated unsupported R1 T-stage values (T1/T2), N0 claims and a false `No comorbidities` assertion; Chair quarantined examples. These are known real-output failure modes, not acceptable clinical statements. |
| TNM connector CodeQL remediation | IN PROGRESS | `case_integrity.py` now uses direct string comparison; the new whitespace/case regression passed in the 303-test suite. Python and JavaScript CodeQL jobs passed on `965d6ba`; the PR thread is no longer unresolved. The separate alert record could not be queried, so formal alert closure is not claimed. |
| Unknowns, staging and contradictions | IN PROGRESS | Not-reported semantics and discrepancy warnings exist; semantic coverage and human review remain required. The run `43698959463` Chair report quarantined unsupplied T1/T2 and N0 staging assertions and unsupported absence of comorbidities. Never infer these fields from lesion size or empty arrays. |
| Conditional recommendations/prerequisites | IN PROGRESS | Deterministic checks exist; full live-output audit outstanding. |
| Distinct-role Chair counting | VERIFIED | Regression coverage and exact-baseline backend CI passed; complete live consensus validation still outstanding. |
| Proposition consensus, dissent and position history | IN PROGRESS | Deterministic reconciliation/tests exist; full current-head report audit outstanding. |
| Case hashes, run IDs, timestamps and audit history | IN PROGRESS | Mechanisms exist; complete current-head reproducibility audit outstanding. |
| Provenance and source attribution | IN PROGRESS | Round/source validation exists; malformed paired-reference R3 prose is flagged without rewriting raw output. Evidence retrieval and independent source verification are not implemented. |
| Missing/failed agent handling | IN PROGRESS | Validation mechanisms exist; current-head incomplete-case/failure-injection acceptance outstanding. |
| Live-validation source-integrity quality gate | FAILED (run #16 output) | Run `43714529807` contains 11 R1 case flags, 1 R2 case flag, 40 R2 source flags, and 84 R3 source flags in its 17 completed R3 rows. The full 45-role quality gate could not execute because R3 timed out. Backend CI verifies gate logic, not live acceptance. |
| Backend tests | VERIFIED (latest completed exact-head run); IN PROGRESS on checklist-only refresh | Exact HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076845](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076845): **313 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **6/6 passed**. Backend run `43755198671` for the later checklist-only refresh is queued. No application-code change after tested SHA `bc114eb`. |
| Frontend build | VERIFIED | Exact latest branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076689](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076689): success. |
| Browser registry/dashboard E2E | VERIFIED | Exact latest branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076722](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076722): success. |
| Packaging prerequisites | VERIFIED | Exact latest branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076846](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076846): success. |
| Windows installer build/smoke test | VERIFIED | Exact latest branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076754](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076754): success. |
| Dependency/security workflows | VERIFIED (analysis execution); alert closure pending | Exact latest branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`, [run 43754076894](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43754076894): success. Formal closure of the historical TNM alert remains unconfirmed. |
| Frontend flicker/blank screens/stale state | IN PROGRESS | Browser E2E passes; dedicated reproduction and console/network/lifecycle investigation outstanding. |
| Dashboard/API integration | IN PROGRESS | Baseline browser E2E passed; current-head acceptance outstanding. |
| Ollama context allocation | VERIFIED (hosted CPU stage-boundary scope) | In run `43698959463`, `api/ps` and `ollama ps` snapshots after R1/R2/R3/R4 showed loaded `qwen3.5:4b` at context lengths 4096/6144/8192/4096 respectively, processor 100% CPU and VRAM 0. These are stage-boundary/runtime snapshots, not per-request token-truncation proof and not GPU evidence. |
| R3 Ollama request-context propagation | IN PROGRESS | `_context_window_for_schema` maps the main adversarial draft to 8,192; the `80abe9e` no-inference test captures the actual `/api/generate` request and confirms `options.num_ctx=8192`. Live per-stage runtime allocation/truncation evidence remains outstanding. |
| Effective R3 context/truncation | IN PROGRESS | R3 schema/request regression asks for 8192. Live `api/ps` and `ollama ps` after R3 in run `43698959463` observed 8192 with the loaded model; R1/R2/R4 boundaries observed 4096/6144/4096. This verifies stage-boundary allocation on the hosted CPU run, but not every R3 request's effective context or whether inputs were truncated. |
| RTX 4060 active inference | IN PROGRESS | Historical laptop GPU measurements exist; current-head request-time GPU/offload verification outstanding. |
| Full live 45-role MDT | IN PROGRESS (checkpoint continuation) | Source run #16 `43714529807` failed after R1 45/45, R2 45/45 and R3 17/45 at the 240-minute timeout. First continuation run `43753381558` restored checkpoint and model but stopped before Python inference because of bare-vs-prefixed digest handling; artifact `14176993069` retained unchanged DB/manifest. The guard was corrected and tested in `bc114eb`. Second continuation [run `43753957255`](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255) is currently in progress: setup, checkout, Python, dependencies and checkpoint restore completed; combined Ollama/R3/R4 step is active. Do not claim inference has started or R3/R4 completed until log/artifact evidence is available. CPU-only; no RTX/GPU claim. |
| Live artefacts/reproducibility | IN PROGRESS | Original run #16 artifact `14169603817` is intact and verified. First continuation artifact `14176993069` contained SQLite DB and manifest with hashes matching the original checkpoint, confirming no DB change before its digest-guard failure. Second continuation run `43753957255` has not produced artifacts as of the latest API query. |
| Evidence retrieval/guideline verification | NOT STARTED | Retrieval is not connected; no guideline concordance is claimed. |
| Independent clinical review | NOT STARTED | Qualified clinical review/acceptance not performed. |
| Windows release/security acceptance | IN PROGRESS | Standard backend/frontend/E2E/packaging/security/installer CI passed on latest exact branch HEAD `1ade8660c769f2135e441016a7fff19498165cee`; historical TNM alert closure, complete live quality acceptance, authentication/security hardening and qualified clinical review remain open. |
| Authoritative repository checklist | VERIFIED | This file is the single master checklist; `IMPLEMENTATION_STATUS.md` points here for current status. |

## Latest full live run forensic record — 16 November 2026

Workflow [43698959463](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43698959463) used commit `2807b0c3d50b68722017fea987b9cdab8bfa283d`, hosted Windows CPU-only, concurrency 1, Ollama 0.40.14 and `qwen3.5:4b` (model digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`). Model provisioning and pull were successful; the run entered real model inference and spent 10,559.07 seconds. It failed after the Chair report was saved because the validator referenced undefined `final_modal` at line 485. This is a validator-code failure, not a model-bootstrap failure.

The saved artifact contains 136 completed contributions: 45 each in R1/R2/R3 and one Chair R4. Every role had `insufficient_information` as its saved R1/R2/R3 position. The saved Chair report declared `insufficient_information`, no proposition-level consensus and no treatment recommendation; it is not a clinical consensus or a passed quality gate. R1 had 16 case-integrity flag instances across 13 roles. R2 had source-reference flags on 30/45 roles (30 instances, 11 unique strings). R3 had source-reference flags on 29/45 roles (271 instances, 89 unique raw strings); the Chair's aggregate summary states 259, a 12-finding mismatch that requires deterministic reconciliation. The Chair retained 20 case-data integrity findings, including source/provenance summaries. The validator crashed before its final quality-gate assertions, so these flags must be reviewed and the new run must pass that gate; do not call this live validation successful.

Runtime snapshots at the end of each round showed loaded model context lengths R1 4096, R2 6144, R3 8192, R4 4096. Ollama reported 100% CPU and 0 VRAM; 896 CPU/process samples had zero sampling errors. Stage times were R1 1940.47s, R2 2831.26s, R3 5726.48s, R4 60.41s. This is hosted CPU evidence only and cannot verify RTX 4060 inference. Stage-boundary snapshots do not prove per-request truncation behavior.

Corrective commits: `7671f3cd2976788fc01aecca1a8bc65c4c091876` factors a tie-safe unique-modal helper and removes the undefined variable; `bfb6e97f7ae9820cb76a3d51f2e6be3ac45f59e7` adds four targeted regressions. Exact-head CI on `bfb6e97`: backend [43713952905](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713952905), 311/311 passed; preflight 6/6 passed; frontend [43713953014](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713953014), browser E2E [43713952949](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713952949), packaging [43713952896](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713952896), security [43713952907](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713952907), and installer [43713952965](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43713952965) all succeeded. These are separate from the next live run.


### Known model-output failure patterns to validate on the retry

- R2: peer citations were emitted as role ranges (`R1:ID through R1:ID`) instead of attributable individual sources; all 30 R2 source-reference flags came from this range-citation pattern.
- R3: flagged patterns include role-range citations, IDs not supplied to the particular R3 contribution, unsupported claims about agreement across all selected peers, and source-opinion reviews for `CASE:case_summary#1` that lacked a unique exact contiguous case-summary excerpt or source-specific R2 excerpt. The deterministic auditor withheld invalid peer citations and flagged the findings; raw generated text must be retained.
- R1/Chair: generated narratives included unsupplied T1/T2 and N0 claims and a statement that there were no comorbidities, despite incomplete/empty structured fields. Chair quarantined these statements. A new live report must be examined to establish whether the existing deterministic checks continue to detect and quarantine them; do not infer normal findings from absent data.
- These findings are separate from the validator NameError. Fixing `final_modal` does not remediate the source-reference or unsupported-clinical-claim patterns. The retry must pass the live quality gate and each saved contribution/report must be audited before any acceptance claim.

## Checkpoint continuation and digest-guard correction — 16 November 2026

The existing checkpoint-resume workflow/script were retargeted to run #16 without repeating R1/R2.

**First continuation attempt**
- Workflow run [43753381558](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753381558), trigger commit `e3434e23cd2416d0a19a0be5bf92d71ba2aab7ab`.
- Checkpoint download and lineage/commit checks succeeded; isolated Ollama 0.40.14 and `qwen3.5:4b` provisioned and tag presence check passed.
- It stopped before Python inference at the PowerShell digest guard: `Installed model returned an invalid digest.`
- Root cause from source comparison: the original hosted validation workflow accepts an Ollama `/api/tags` digest as either bare 64-character hex or `sha256:`-prefixed hex, then canonicalizes it. The new resume workflow had required the prefix unconditionally. This was a bootstrap-format handling defect, not a mismatched model or failed inference.
- Artifact [14176993069](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753381558/artifacts/14176993069), SHA-256 `f296981d1e4a2f57307720d8f6049f3d1cfed593917f0d52a2f78c6c7f84c725`, contains only the original manifest and SQLite. Their individual SHA-256 hashes exactly match source artifact `14169603817`; SQLite remains `integrity_check=ok` and round state is unchanged. Python resume script was not invoked; no R3/R4 data was changed.
 
**Correction and regression**
- Continuation guard now accepts only bare or prefixed SHA-256 representation, strips only the optional `sha256:` prefix, requires exactly 64 hex characters, validates every character, canonicalizes to lowercase `sha256:<hex>`, and then compares to the manifest digest exactly. It does not waive model identity.
- Added `test_resume_workflow_normalizes_ollama_digest_before_exact_checkpoint_match`.
- Exact code/test head `bc114eb9935ebf8b097d880dd2906dd69d73bc0e`: backend **313/313 passed**, preflight **6/6**, both checkpoint-lineage and digest-normalization tests passed; frontend, browser E2E, packaging prerequisites, security and installer checks all succeeded.
  - Backend: [43753664328](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664328)
  - Frontend: [43753664322](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664322)
  - Browser E2E: [43753664321](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664321)
  - Packaging prerequisites: [43753664353](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664353)
  - Security: [43753664327](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664327)
  - Windows installer: [43753664378](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753664378)
 
**Second continuation attempt**
- Trigger commit `28fd7eccfa0e32200eefb995158e8788b0296c97`; workflow run [43753957255](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255).
- Latest observed status: **in progress**, during hosted Python setup. No inference, R3 completion, R4 report or new artifact is confirmed yet.
- It must retain exact source run/commit and exact model digest checks, resume only unfinished R3 roles, preserve completed R3 outputs, and upload the DB/manifest/report even if the quality gate rejects existing integrity flags.

## Run #16 forensic record — 16 November 2026

Workflow [43714529807](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43714529807), run #16, runtime commit `4683b0767bf5cade408e85ec31ef248b34e5321e`; workflow conclusion `failure`. The sole job `132813068060` ran 14,356.24 seconds before the nested `Provision isolated portable Ollama and qwen3.5:4b` step reached its configured 240-minute timeout. Ollama 0.40.14 and `qwen3.5:4b` provisioned successfully (model digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`). The Python process was in `ensure_round(run_id, 3)` / `mdt_rounds.run_mdt_round`; cancellation propagated through `asyncio.gather` while agent tasks awaited the concurrency semaphore. This is evidence of workflow-step timeout and cancellation, not proof of a semaphore deadlock.

The saved SQLite database gives the precise work state: R1 45/45 complete (3,298.7s; 73.3s mean); R2 45/45 complete (6,455.6s; 143.5s mean); R3 17/45 completed, SO-01 running, 27 queued; R4 absent. The 17 R3 generations averaged 262.9s (4.38 min) each; their combined saved duration was 4,470s (74.5 min). A linear projection for 45 R3 calls is about 197.2 min. Adding observed R1/R2 time yields about 359.8 min before Chair synthesis and provisioning/cleanup overhead. This projection is approximate; remaining roles may take longer or shorter. Concurrency was explicitly 1; no concurrency increase is justified without a measured benchmark. GitHub documents a 6-hour maximum execution time per GitHub-hosted job ([Actions limits](https://docs.github.com/en/actions/reference/limits)). The current 240-minute step cut off the run; merely raising the timeout is not a reliable single-job remedy given the approximately six-hour projection and platform ceiling.

Artifact `14169603817` (`radonc-hosted-cpu-four-round-validation`) archive SHA-256 `73a7ece5be348e36a1458c9d6f3679fe694a6b5d08c03556a82988859f5e1392`; simulator run ID `c4592dbb-ecc7-4007-9125-d0baaed9abb0`. Artifact downloaded and inspected. SQLite `integrity_check` returned `ok`; `foreign_key_check` returned no rows. Case snapshot hash `8fdc3c2536c6c3487d3142498a1731e57ea4eefbb5a110b6ce98b105d069393f` matched both JSON and SQLite. It contains 1,032 CPU/Ollama process samples, 3 stage snapshots and no NVIDIA measurements; final `/api/ps` showed `context_length=8192`, `size_vram=0`, and CLI `100% CPU`. This is CPU-only telemetry, not GPU proof or per-request truncation proof.

**Live quality findings are separate from timeout:** R1 emitted 11 unsupported stage flags across 7 roles (T1 x7, N0 x2, M0 x2). R2 emitted 40 source-reference flags across 40 roles (13 unique strings) and one case-integrity flag where MO-07 made a categorical `is contraindicated` assertion unsupported by missing data. The 17 saved R3 outputs all had `insufficient_information` positions and contained 84 source-reference flags across 8 roles (50 unique strings), including unbound CASE opinion reviews and unsupplied/role-range references; 16 risk flags and 31 challenge entries were saved, but their provenance is not accepted. No R4 report exists. Therefore this incomplete run cannot be accepted even after timeout remediation; the source/clinical integrity findings also require remediation and live revalidation.

## Updated immediate priorities — 16 November 2026

1. Do not rerun the monolithic 45-role job with only a longer timeout: observed work projects to roughly six hours before R4 and the current step limit is 240 minutes.
2. Design and regression-test resumable per-round jobs (R1 → verified DB/artifact checkpoint → R2 → checkpoint → R3 → checkpoint → R4), checking case hash, model digest, run ID, completed-role identities and SQLite integrity at every boundary. Preserve immutable prior artifacts and never mark an incomplete round complete.
3. Alternatively, first run a bounded concurrency 1-vs-2 benchmark using the same model/runtime and representative R3 inputs; do not change concurrency without measured throughput and output-quality evidence.
4. Audit and correct persisted R1 unsupported stage claims, R2 categorical contraindication and R2/R3 source-reference patterns without rewriting raw output or inventing sources; add exact regression tests and quality gates.
5. Only after stage/checkpoint architecture and integrity failures are corrected, perform one new full 45-role run and audit all 136 contributions, R4, source flags, case flags, position distributions, hashes and artifacts.
6. Keep RTX 4060 active inference, per-request context/truncation, incomplete/failed-agent recovery, independent clinical review, evidence retrieval, authentication/security and release acceptance as separate gates.


## Immediate priorities

1. Monitor checkpoint continuation run [43753957255](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255); when the job finishes, retrieve its logs and output artifact. Confirm which 17 completed R3 records were preserved, which 28 outstanding roles completed, whether R4 was saved, and whether the full 136 contributions remain traceable.
2. Expect the final quality gate to remain failed unless the already-saved R1/R2/R3 source and case-integrity findings are remediated; completing R3/R4 is not a clean acceptance result.
3. If run 43753957255 fails or times out, inspect its newly uploaded DB/manifest and use the latest verified checkpoint lineage for a subsequent continuation; never restart R1/R2 or overwrite previously completed R3 outputs.
4. Audit and correct persisted R1 unsupported stage claims, R2 categorical contraindication and R2/R3 source-reference patterns without rewriting raw output or inventing sources; add exact regression tests and quality gates.
5. Keep RTX 4060 active inference, per-request context/truncation, incomplete/failed-agent recovery, independent clinical review, evidence retrieval, authentication/security and release acceptance as separate gates.

## Verification boundaries

- Passing CI/unit tests establishes software checks, not clinical accuracy.
- A bounded three-role simulation with deterministic R1 fixtures is not the production 45-role workflow.
- Model loading or allocated VRAM does not prove active GPU inference.
- A clean adversarial run does not prove detection of planted defects; retain positive and negative controls.
- Never claim evidence retrieval, guideline concordance, clinical validation or release readiness without independent evidence.
- Preserve historical failures and limitations; never erase or silently downgrade them.
