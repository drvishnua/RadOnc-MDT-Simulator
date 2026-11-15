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
| Full live 45-role MDT | IN PROGRESS (checkpoint continuation) | Source run #16 `43714529807` failed after R1 45/45, R2 45/45 and R3 17/45 at the 240-minute timeout. First continuation run `43753381558` restored checkpoint and model but stopped before Python inference because of bare-vs-prefixed digest handling; artifact `14176993069` retained unchanged DB/manifest. The guard was corrected and tested in `bc114eb`. Second continuation [run `43753957255`](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255) is currently in progress: setup, checkout, Python, dependencies and checkpoint restore completed; combined Ollama/R3/R4 step is active. Latest job query confirms step 6 is in progress, with no logs or artifacts yet. Do not claim inference has started or R3/R4 completed until log/artifact evidence is available. CPU-only; no RTX/GPU claim. |
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
- Latest observed GitHub job query: **in progress**. The job Resume saved R3 contributions and generate Chair R4 has completed checkout, Python setup, dependency installation and checkpoint restoration. Its combined Resume R3 and Chair R4 using isolated Ollama step (step 6) is now active. No step logs or output artifacts were available at the latest query; do not infer that model inference, R3 completion or R4 generation has succeeded until logs and saved artefacts prove it.
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

---

# Commercial SaaS Development and Release Readiness — expanded 16 November 2026

**Purpose.** This is the same authoritative master checklist, extended to cover a commercially distributable, hosted, multi-customer SaaS product. It does not assert that the current local Windows application is SaaS-ready. The present application must remain loopback-bound and synthetic-data-only until the relevant controls are implemented and independently verified. A cloud deployment is a separate, gated architecture and security project; do not expose the current unauthenticated local API to a network, and do not weaken the existing four-round or clinical-integrity controls to accelerate commercialisation.

**Status rule.** Every row below has one of the project statuses. VERIFIED must name exact artefacts, versions, test results and reviewer; a policy draft, checkbox, passing unit test or vendor marketing claim is not sufficient. Statuses below reflect evidence available on 16 November 2026, not assumed future work.

## A. Intended use, product scope and governance

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| SaaS-001 | Define product intended purpose, intended users, training/education versus clinical use, clinical environment, outputs, limitations and prohibited use | IN PROGRESS | Product specification signed by product owner and qualified clinical/regulatory reviewer; reconcile all UI, API, website, sales and contract claims |
| SaaS-002 | Decide whether SaaS is a separate cloud product, hosted edition of the local application, or managed private deployment | NOT STARTED | Architecture decision record; compare tenant isolation, deployment boundary, data residency, offline/local mode and support implications |
| SaaS-003 | Define launch countries, customer types, user roles, languages, data locations and support hours | NOT STARTED | Market/jurisdiction matrix with owners and legal review |
| SaaS-004 | Establish product requirements and acceptance criteria covering functional, safety, security, privacy, performance, accessibility, operations and commercial requirements | NOT STARTED | Requirements traceability matrix linking requirement → hazard/risk → design → implementation → test → evidence → release |
| SaaS-005 | Identify product owner, clinical safety officer, security owner, privacy owner/DPO where required, service owner, incident commander and release approvers | NOT STARTED | Named RACI, delegated authority, escalation and absence/backup arrangements |
| SaaS-006 | Establish design review, architecture decision, change control, risk acceptance and independent release approval processes | NOT STARTED | Controlled SOPs, meeting records, approval history and exception register |
| SaaS-007 | Define supported configurations, browsers, devices, network assumptions, model providers and customer-managed versus vendor-managed deployment | NOT STARTED | Support matrix and tested compatibility matrix |
| SaaS-008 | Maintain a product claims register; prohibit unsupported claims such as clinical accuracy, guideline compliance, consensus, safety certification or GPU performance | IN PROGRESS | Marketing/UI/contract review with claim owner and supporting evidence for every claim |
| SaaS-009 | Define feature boundary for future patient-specific recommendations, triage, treatment selection, dose calculation, contouring, planning, image interpretation or EHR integration | BLOCKED | Separate intended-use and regulatory/safety review before any such feature is designed, enabled or marketed |
| SaaS-010 | Define product lifecycle and end-of-life/exit plan, including customer notice, data export, deletion, transition assistance and service shutdown | NOT STARTED | Approved lifecycle and customer-exit plan |

## B. Regulatory, standards and jurisdictional assessment

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| REG-001 | Obtain written Indian regulatory assessment of intended purpose and whether each software function is Medical Device Software under Medical Devices Rules 2017; do not infer exemption from an education-only disclaimer | BLOCKED | Signed Indian regulatory counsel/specialist opinion mapped to actual features, claims, users and outputs |
| REG-002 | Review CDSCO final Guidance Document on Medical Device Software under MDR-2017, Doc. No. CDSCO/MD/GD/MDSW/01/2026, dated 21 July 2026 | IN PROGRESS | Classification rationale, applicable essential principles, quality, clinical/performance evidence, submission and post-market obligations documented |
| REG-003 | Review current CDSCO risk-classification lists for oncology (2 January 2026) and radiotherapy (27 November 2025) where relevant; confirm software/function applicability rather than treating device lists as an automatic classification of this product | NOT STARTED | Saved official version, review date, affected functions and written applicability decision |
| REG-004 | Map India obligations across Medical Devices Rules 2017, Drugs and Cosmetics Act, applicable labelling/licensing, quality system, clinical investigation/evaluation and post-market vigilance | BLOCKED | Market-entry gap assessment and counsel-approved regulatory plan |
| REG-005 | Reassess DPDP Act 2023 and DPDP Rules 2025 phased commencement for each release and processing role | IN PROGRESS | Dated legal applicability matrix: G.S.R. 843(E) commencement notification dated 13 November 2025; G.S.R. 846(E) Rules dated 13 November 2025; sections 6(9) and 27(1)(d) commenced 13 November 2026; main provisions listed for the 18-month phase are scheduled from 13 May 2027. Confirm corresponding Rules commencement and transition requirements with counsel |
| REG-006 | Determine roles as Data Fiduciary, Data Processor, Significant Data Fiduciary or other applicable role; assess customer/vendor allocation and contracts | BLOCKED | Counsel-approved data-role map per deployment and processing purpose |
| REG-007 | Review continuing/interacting Indian IT Act 2000 and SPDI Rules 2011 duties during DPDP transition; assess applicability to the actual entity and service | NOT STARTED | Current legal memorandum; do not assume older provisions have ceased before statutory commencement |
| REG-008 | Determine CERT-In Directions applicability, incident-reporting triggers/timelines, point of contact and ICT-log retention/location requirements (including six-hour reporting and 180-day retention where applicable) | NOT STARTED | Counsel-reviewed applicability matrix, incident SOP, time synchronisation and tested retention evidence |
| REG-009 | Review Consumer Protection Act 2019, product/service liability, e-commerce obligations, misleading-advertisement and unfair-contract risks for the specific distribution model | NOT STARTED | Indian counsel review of labels, claims, warranties, support, terms and complaint handling |
| REG-010 | Review Indian GST, invoicing, place-of-supply, subscription, withholding, export-of-services and foreign-currency/payment obligations | NOT STARTED | CA/tax advice, registration decision, invoice samples, accounting and reconciliation tests |
| REG-011 | For US distribution, determine FDA device/CDS status for each software function using the January 2026 final Clinical Decision Support Software Guidance and other applicable FDA digital-health/device guidance | BLOCKED | US regulatory opinion; function-level analysis; no reliance on a general CDS label |
| REG-012 | For US-regulated device functions, assess FDA QMSR (effective 2 February 2026), 21 CFR requirements, registration/listing, submissions, labelling, complaint/MDR reporting and inspection readiness as applicable | BLOCKED | Regulatory applicability assessment and implementation evidence; QMSR is not assumed applicable to an unclassified educational product |
| REG-013 | For EU/EEA, assess MDR 2017/745, Rule 11, qualification/classification, clinical evaluation, conformity assessment, CE marking, UDI/EUDAMED and post-market obligations as applicable | BLOCKED | Written function-specific EU regulatory opinion; current MDCG guidance mapping |
| REG-014 | Review MDCG 2019-11 rev.1 (June 2025), MDCG 2021-24 rev.1 (April 2026) and current European Commission MDCG index before EU decisions | IN PROGRESS | Saved revision/date, rationale, source URL and regulatory reviewer sign-off |
| REG-015 | Assess EU AI Act applicability, provider/deployer/importer roles, prohibited practices, AI literacy, transparency, GPAI dependencies and high-risk classification/timing | BLOCKED | EU counsel assessment using consolidated law and current Commission implementation timeline; do not assume all AI functions are high-risk or exempt |
| REG-016 | For UK, assess UK MDR 2002, MHRA software/AI guidance, UK GDPR and Data Protection Act 2018; track current reform/transition | NOT STARTED | UK-specific market-entry checklist and counsel sign-off |
| REG-017 | For any additional country, complete a market-specific regulatory/privacy/consumer/tax/export matrix before enabling registration or sales | BLOCKED | Country approval record, local representative/importer requirements and geofencing/contract controls where needed |
| REG-018 | Maintain regulatory change monitoring with owner, review cadence, trigger-based reassessment and effective-date tracking | NOT STARTED | Quarterly and event-triggered review log; archived versions and impact assessments |

## C. Privacy, confidentiality and data governance

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| PRIV-001 | Complete data inventory and data-flow maps for registration, case input, prompts, model inference, R1–R4 outputs, audit, telemetry, support, billing, backups and exports | NOT STARTED | Versioned data inventory, DFDs, system boundary and vendor/subprocessor map |
| PRIV-002 | Maintain synthetic-only default; prohibit real patient identifiers/records until a separately approved privacy, regulatory, clinical and security gate is passed | IN PROGRESS | UI/API controls, onboarding warnings, acceptable-use terms, test fixtures and documented exception process (no exception presently authorised) |
| PRIV-003 | Define lawful basis, purpose limitation, notice, consent/authorisation where required, minimisation, accuracy, retention, deletion and data-principal workflows | BLOCKED | Counsel-approved privacy design per jurisdiction and customer role |
| PRIV-004 | Perform DPIA/privacy impact assessment before any production health/personal data or high-risk processing | BLOCKED | Approved DPIA, mitigations, residual-risk acceptance and re-assessment triggers |
| PRIV-005 | Define tenant-specific data ownership, access, export, correction, retention, legal hold and deletion workflows | NOT STARTED | Tested data lifecycle matrix, tenant-scoped APIs and support procedures |
| PRIV-006 | Specify whether prompts, completions, uploaded documents, feedback and telemetry are used for model training or product improvement; default to no training without explicit valid authorisation | NOT STARTED | Contract, provider settings, technical verification and customer-facing notice |
| PRIV-007 | Inventory every external transfer, region, recipient, subprocessor, remote support path, crash reporter, analytics and model endpoint | NOT STARTED | Egress allowlist, vendor register, privacy notice and network-level test |
| PRIV-008 | Review cross-border transfer and localisation requirements, including India, EU/EEA and customer contractual restrictions | BLOCKED | Legal assessment and approved data-region architecture |
| PRIV-009 | Implement retention schedules for case data, model prompts, generated content, immutable audit events, application logs, backups and billing records | NOT STARTED | Configured lifecycle jobs and automated retention/deletion tests |
| PRIV-010 | Implement verifiable customer export and deletion with documented limits for backups, replicas, caches, legal holds and SSD/cloud media | NOT STARTED | Tenant-level export/deletion tests, completion receipts and truthful deletion wording |
| PRIV-011 | Ensure logs, traces, metrics, crash reports and support bundles do not contain patient text, secrets, tokens or unnecessary personal data | NOT STARTED | Redaction tests, sampling review and privacy-safe telemetry schema |
| PRIV-012 | Define privacy incident/breach assessment, customer notice, regulator/data-principal notification and evidence preservation | NOT STARTED | Jurisdiction-specific incident decision tree and tabletop exercise |
| PRIV-013 | Assess HIPAA/HITECH and business-associate obligations before any US PHI processing; execute BAAs only where required and technically supported | BLOCKED | Counsel assessment and signed BAA/vendor flow-down where applicable |
| PRIV-014 | Provide clear privacy, cookie/analytics and telemetry controls; do not use non-essential tracking without applicable consent | NOT STARTED | Reviewed notices, consent records and automated preference enforcement |

## D. Cloud, SaaS and tenant-isolation architecture

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| ARCH-001 | Produce target cloud architecture, trust boundaries, service catalogue, data stores, identity flow, inference flow, admin plane and disaster-recovery design | NOT STARTED | Reviewed architecture diagrams and threat model |
| ARCH-002 | Decide multi-tenant shared infrastructure versus isolated database/schema/instance per tenant and document the security trade-off | NOT STARTED | ADR and abuse-case analysis; default deny between tenants |
| ARCH-003 | Enforce tenant identity server-side from authenticated principal; never trust a client-supplied tenant ID as authority | NOT STARTED | Code review, API tests and negative tests for tenant substitution |
| ARCH-004 | Enforce tenant scoping in every database query, object-store key, cache key, search index, queue, export, background task and model context | NOT STARTED | Cross-tenant isolation test suite across all data paths |
| ARCH-005 | Prevent IDOR/BOLA, insecure direct object access, cross-tenant report downloads, cache leakage and support-console leakage | NOT STARTED | OWASP API test suite and independent penetration test |
| ARCH-006 | Define per-tenant quotas, concurrency, storage, context, model-provider routing and fair-use limits | NOT STARTED | Metering/limit tests and abuse controls |
| ARCH-007 | Separate production, staging, test, development and customer-specific environments/accounts/projects | NOT STARTED | Cloud account inventory, IAM boundaries and deployment policy |
| ARCH-008 | Implement infrastructure as code, peer review, drift detection, policy-as-code and reversible environment provisioning | NOT STARTED | Versioned IaC, plan/apply approvals and drift reports |
| ARCH-009 | Use managed secrets/KMS, least-privilege workload identity and automatic secret rotation; prohibit secrets in source, images and logs | NOT STARTED | Secret scan, rotation test and access review |
| ARCH-010 | Establish network segmentation, private service endpoints, outbound egress controls, WAF/API gateway, DDoS controls and secure DNS | NOT STARTED | Network diagram, firewall rules, external scan and fail-closed tests |
| ARCH-011 | Apply TLS 1.2 or stronger (prefer TLS 1.3 where supported), certificate renewal, HSTS and secure service-to-service authentication | NOT STARTED | TLS scan, certificate automation and expiry alert |
| ARCH-012 | Encrypt databases, object storage, backups and queues at rest using managed keys; design key rotation and tenant separation | NOT STARTED | KMS configuration, key access audit and restore/decryption test |
| ARCH-013 | Harden containers/VMs/host OS: non-root, minimal images, patching, immutable deployment, EDR, host firewall and runtime restrictions | NOT STARTED | Baseline configuration and compliance scan |
| ARCH-014 | Secure browser sessions, CSRF protection, content security policy, clickjacking protection, secure cookies, CORS and origin checks | NOT STARTED | Browser security tests; CORS must never be treated as authentication |
| ARCH-015 | Protect model and retrieval services from SSRF, prompt injection, malicious uploaded documents, unsafe tool/function calls and egress/data exfiltration | NOT STARTED | Threat tests using hostile prompts/documents and egress monitoring |
| ARCH-016 | Implement rate limiting, request size limits, input validation, timeouts, back-pressure, queue limits and denial-of-wallet controls | NOT STARTED | Load/abuse tests and per-tenant enforcement evidence |
| ARCH-017 | Document data residency, cloud region, disaster-recovery region, provider access and lawful government-request process | NOT STARTED | Customer-facing region statement, vendor contracts and access logs |

## E. Identity, access control and administration

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| IAM-001 | Implement mature authentication (OIDC/OAuth 2.1 or equivalent), email verification and secure account recovery | NOT STARTED | Protocol review, negative tests and recovery tabletop |
| IAM-002 | Provide MFA for privileged accounts and customer administrators; assess passkeys and phishing-resistant MFA | NOT STARTED | Enforced policy and bypass/resilience tests |
| IAM-003 | Implement role-based and, where needed, attribute-based authorisation with least privilege and deny-by-default | NOT STARTED | Permission matrix and endpoint-by-endpoint tests |
| IAM-004 | Support institutional SSO/SAML/OIDC only after secure configuration, metadata validation and tenant binding | NOT STARTED | SSO integration tests, certificate rotation and misconfiguration tests |
| IAM-005 | Implement session expiry, refresh-token rotation/revocation, device/session visibility and logout invalidation | NOT STARTED | Session security tests |
| IAM-006 | Add joiner/mover/leaver, SCIM provisioning where required, admin approval and periodic access recertification | NOT STARTED | Lifecycle logs and quarterly access review |
| IAM-007 | Separate customer admin, vendor support, system operator, security admin and break-glass roles; require just-in-time approval for support access | NOT STARTED | Privileged access workflow and audit trail |
| IAM-008 | Protect service accounts, API keys, webhooks and integration credentials with scoped permissions and rotation | NOT STARTED | Token inventory, least-privilege tests and revocation evidence |
| IAM-009 | Record security-relevant account, privilege, authentication, data export, deletion and administrative actions in tamper-evident audit events | NOT STARTED | Audit completeness and integrity verification |
| IAM-010 | Provide account suspension, tenant suspension, compromised-account containment and safe offboarding | NOT STARTED | Tested incident and offboarding runbooks |

## F. Application and infrastructure security / secure SDLC

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| SEC-001 | Threat-model the complete system, including local desktop mode, SaaS control plane, tenant plane, APIs, model/RAG, CI/CD and support tooling | IN PROGRESS | Versioned threat model, data-flow diagrams, abuse cases and tracked mitigations |
| SEC-002 | Adopt a secure development lifecycle aligned to NIST SSDF SP 800-218 and maintain documented security requirements | NOT STARTED | SDLC policy, developer training and CI evidence |
| SEC-003 | Use OWASP ASVS 5.0.0 as a testable application/API security verification baseline; record requirement-level pass/fail/NA with rationale | NOT STARTED | ASVS control matrix and independent verification |
| SEC-004 | Apply OWASP API Security Top 10 and OWASP GenAI LLM Top 10 2026 to API, agent and retrieval threat testing | NOT STARTED | Versioned threat-to-test mapping and test artefacts |
| SEC-005 | Require protected branches, mandatory review, CODEOWNERS for security/clinical logic, signed/reviewed release tags and no direct main-branch changes | IN PROGRESS | Repository settings export and attempted bypass tests |
| SEC-006 | Pin dependencies, lock transitive dependencies, verify hashes/signatures and define controlled update policy | IN PROGRESS | Reproducible lockfiles, dependency review and update PRs |
| SEC-007 | Generate SBOM (SPDX or CycloneDX) for application, containers, installer, Python/Node dependencies, Ollama/runtime and model package | NOT STARTED | Versioned SBOM per release and vulnerability correlation |
| SEC-008 | Produce build provenance/attestation, immutable artifact identifiers and reproducible build evidence (target SLSA-aligned controls) | NOT STARTED | Signed provenance and independent verification |
| SEC-009 | Run SAST, SCA, secret scanning, IaC scanning, container scanning, licence scanning and malware scanning in CI | IN PROGRESS | Exact-commit reports; no unresolved critical/high findings or documented risk acceptance |
| SEC-010 | Add DAST, API fuzzing, dependency confusion/typosquatting checks, malicious package tests and runtime security testing | NOT STARTED | Scheduled scans and retained reports |
| SEC-011 | Establish vulnerability intake, security contact, coordinated disclosure policy, severity triage, patch SLAs and CVE handling | NOT STARTED | Published policy and exercised intake workflow |
| SEC-012 | Conduct independent penetration testing, including tenant isolation, auth, API, cloud, admin, model, file upload and privacy controls | BLOCKED | Qualified external tester report, retest and closure of critical/high findings |
| SEC-013 | Establish patch management for OS, Python, Node, browser, container base images, Ollama, model and cloud services | NOT STARTED | Patch cadence, emergency process and ageing dashboard |
| SEC-014 | Protect secrets and certificates in CI, deployment, support and runtime; test revocation after suspected exposure | NOT STARTED | Secret lifecycle test and incident evidence |
| SEC-015 | Define cryptographic algorithms, key lifecycle, rotation, recovery, separation of duties and key compromise response | NOT STARTED | Cryptographic design review and KMS/HSM evidence |
| SEC-016 | Verify backup encryption, immutability, ransomware resistance and separate administrative credentials | NOT STARTED | Restore and destructive-account compromise exercise |
| SEC-017 | Perform annual and change-triggered independent security assessments and maintain risk acceptances with expiry dates | NOT STARTED | Signed assessment, remediation tracking and risk owner |

## G. AI/LLM model, agent and inference governance

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| AI-001 | Maintain model registry: provider, name, exact digest, quantisation, licence, version, runtime, hardware, parameters, prompt versions and supported purpose | IN PROGRESS | Immutable registry record for each run and deployable model |
| AI-002 | Verify model licensing, commercial SaaS rights, acceptable-use terms, attribution, redistribution and hosting conditions for Qwen/Ollama and every alternative | BLOCKED | Legal/licence review for exact model/runtime release and any derivative/adapter |
| AI-003 | Define provider privacy and security contracts: region, retention, training use, subprocessors, access, audit, incident notice and deletion | BLOCKED | Vendor due diligence, DPA/BAA where required and verified technical settings |
| AI-004 | Keep model calls local to approved infrastructure or use a contractually approved inference provider; block unapproved outbound transfer | IN PROGRESS | Network egress tests, endpoint allowlist and prompt-data flow audit |
| AI-005 | Keep R1 independent; enforce exact R2/R3 peer allowlists, source-bound quotes and R4 use of actual saved R1–R3 contributions | IN PROGRESS | Existing regression suite plus full-run audit and no cross-round leakage tests |
| AI-006 | Deterministically enforce counts, schema, state transitions, missing/failed agents, consensus, dissent, prerequisites and provenance outside the LLM | IN PROGRESS | Code-level validation and adversarial regression tests |
| AI-007 | Treat model output, retrieved documents, uploaded files, peer text and tool results as untrusted; prevent prompt injection and indirect instruction takeover | NOT STARTED | Threat model, hostile-source test corpus and fail-closed test results |
| AI-008 | Test hallucinated staging, fabricated investigations, unsupported negative findings, invented comorbidities, false consensus and loss of conditionality | IN PROGRESS | Source-grounded challenge suite, human-reviewed gold labels and zero tolerated critical errors |
| AI-009 | Test truncated/invalid JSON, schema drift, token exhaustion, context under-allocation, timeouts, retries, duplicate calls and partial persistence | IN PROGRESS | Fault-injection suite, raw request/response capture with privacy-safe controls and idempotency proof |
| AI-010 | Evaluate R3 with clean-record negative controls and seeded-defect positive controls; never equate zero challenges with successful adversarial review | IN PROGRESS | Role-level sensitivity/specificity and source attribution report |
| AI-011 | Evaluate full 45-role R1–R4 orchestration at concurrency 1 before performance tuning | IN PROGRESS | Complete saved 136-contribution run, deterministic audits and exact report reconciliation |
| AI-012 | Establish independently curated evaluation datasets across tumour sites, stages, rare cases, incomplete data, contradictions and missing investigations | NOT STARTED | Dataset provenance, inclusion criteria, expert labels, versioning and licence/consent |
| AI-013 | Measure clinical-content factuality, source entailment, citation correctness, omission, calibration, uncertainty, fairness and subgroup performance | NOT STARTED | Pre-registered protocol, blinded qualified reviewers, denominators and confidence intervals |
| AI-014 | Assess prompt/model updates for regression, drift, role bias, verbosity, latency, cost and safety before promotion | NOT STARTED | Version-to-version regression report and approval record |
| AI-015 | Provide deterministic stop/abstain behavior where information is insufficient, evidence is absent or validation fails | IN PROGRESS | Failure-injection tests and review of user-visible outputs |
| AI-016 | Prevent model-driven tool execution, arbitrary code, shell access, network access or unapproved writes; mediate tools through narrow server-owned interfaces | NOT STARTED | Tool permission matrix, sandbox tests and deny-by-default policy |
| AI-017 | Monitor model quality, latency, tokens, queue, context, GPU/CPU, VRAM and error distributions without logging sensitive case content | IN PROGRESS | Per-request telemetry with redaction and reproducible benchmark |
| AI-018 | Establish model retirement, rollback, emergency disablement and fallback policy; never silently change model digest | NOT STARTED | Tested model rollback and customer notification policy |
| AI-019 | Validate inference capacity, per-tenant quotas, concurrency, cost ceilings and denial-of-wallet resistance | NOT STARTED | Load/soak tests and measured unit economics at target load |
| AI-020 | Verify RTX 4060 active inference separately from hosted CPU tests; record request-time utilisation, VRAM, offload layers, latency and logs | IN PROGRESS | Captured nvidia-smi/Ollama telemetry during actual request; no VRAM-allocation-only proof |

## H. Clinical safety, evidence, guideline and reference governance

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| CLIN-001 | Maintain strict synthetic educational boundary until intended-use/regulatory and clinical approvals authorise any broader use | IN PROGRESS | UI, API, onboarding, contracts and marketing consistency audit |
| CLIN-002 | Create clinical hazard log covering fabricated facts, incorrect staging, missed contraindications, omitted options, false consensus, omitted dissent, incorrect citations and automation bias | IN PROGRESS | Hazard analysis with severity, probability, control, residual risk and owner |
| CLIN-003 | Complete lifecycle risk management using ISO 14971 principles if the function is within medical-device scope; assess usability-related risk | BLOCKED | Qualified regulatory/clinical safety decision and approved risk-management file |
| CLIN-004 | Establish independent multidisciplinary clinical review with radiation oncologist, medical oncologist, surgeon, radiologist, pathologist, physicist and other relevant roles | NOT STARTED | Reviewer credentials, conflicts, protocol, signed review and tracked remediation |
| CLIN-005 | Create tumour-site-specific and role-specific clinical validation plan; do not treat a single synthetic run as clinical validation | NOT STARTED | Protocol, representative cohorts, expert adjudication and acceptance thresholds |
| CLIN-006 | Implement a controlled evidence registry with title, organisation, author, publication/update date, jurisdiction, version, URL/DOI, access date, section/page, hash and superseded/withdrawn state | NOT STARTED | Searchable registry and provenance export |
| CLIN-007 | Restrict evidence retrieval to authoritative sources and approved licensed content; separate primary guidelines, primary literature, consensus statements, textbooks and general web content | NOT STARTED | Source allowlist, ranking policy, licence record and retrieval tests |
| CLIN-008 | Attach a traceable citation to every externally sourced clinical assertion; citation must support exact claim and preserve uncertainty/conditionality | NOT STARTED | Claim-to-source entailment audit and no-fabricated-citation tests |
| CLIN-009 | Record guideline edition/version/date, update date, region, tumour-site applicability, evidence grade and recommendation category where supplied by source | NOT STARTED | Versioned guideline metadata and exact version shown to users |
| CLIN-010 | Monitor guideline updates, rapid updates, errata, withdrawals and staging changes; prevent stale sources from silently remaining current | NOT STARTED | Update monitoring, change review queue and affected-output impact report |
| CLIN-011 | Obtain and document copyright/licence permission for each guideline, textbook, journal article, image, figure, table, dataset and retrieval corpus; do not bulk-copy protected content | BLOCKED | Publisher/society licence or counsel-approved basis; audit retrieval/storage/quotation restrictions |
| CLIN-012 | Maintain a clinical reference register including NCCN, ASTRO, ESTRO, ESMO, ASCO, IAEA, WHO/IARC, ICRU, AJCC, relevant Indian national guidance and primary peer-reviewed evidence where applicable | NOT STARTED | Per-source owner, edition, jurisdiction, URL, update cadence, licence and currentness review |
| CLIN-013 | Maintain textbook/reference inventory and confirm each title's latest edition, errata, publisher permissions and applicability before use | IN PROGRESS | Bibliographic record and licence check. Verified catalogue examples at this review: Perez, Brady, Halperin, and Wazer's Principles and Practice of Radiation Oncology, 8th ed. (2025); Gunderson and Tepper's Clinical Radiation Oncology, 6th ed. (2026); Khan's The Physics of Radiation Therapy, 6th ed. (2019; verify whether superseded before adoption) |
| CLIN-014 | Treat textbooks as foundational/reference material, not a substitute for current guidelines, systematic reviews, primary studies or updated staging manuals | IN PROGRESS | Evidence hierarchy, prompt policy and reviewer checklist |
| CLIN-015 | Verify AJCC/UICC TNM edition/version for each tumour site and diagnosis date; stage components must remain unknown when evidence is absent | IN PROGRESS | Site-specific staging source registry, test cases and reviewer audit |
| CLIN-016 | Establish evidence conflict handling (different guideline jurisdictions, version conflicts, contradictory trials, uncertainty and minority recommendations) | NOT STARTED | Structured conflict record and transparent user-facing disclosure |
| CLIN-017 | Establish update-impact assessment when a guideline, staging version, model or prompt changes; identify affected old reports without silently rewriting historical runs | NOT STARTED | Change-impact analysis, audit history and report versioning |
| CLIN-018 | Ensure no recommendation is presented as verified guideline-concordant unless source retrieval and human/source validation support it | IN PROGRESS | Automated disclosure gates and manual audit |
| CLIN-019 | Assess usability, automation bias, alert fatigue, accessibility and safe user interpretation of uncertainty and dissent | NOT STARTED | IEC 62366-1-informed usability engineering, formative/summative evaluation where applicable |
| CLIN-020 | Define post-market clinical feedback, complaint handling, safety signal detection, field corrections and recall/FSCA process if regulated | BLOCKED | Regulatory classification and written vigilance/complaint procedure |

## I. Software quality, verification and validation

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| QA-001 | Maintain requirements-to-test traceability and risk-based test coverage for backend, frontend, APIs, database, AI, infrastructure and operations | NOT STARTED | Versioned traceability matrix and coverage report |
| QA-002 | Maintain unit, integration, contract, property-based, mutation, regression and end-to-end test suites | IN PROGRESS | Exact-commit test results and coverage thresholds |
| QA-003 | Test R1–R4 state machine, round-specific inputs, history, role identity and correct saved-contribution reuse | IN PROGRESS | 45-role end-to-end fixtures and DB/report reconciliation |
| QA-004 | Test incomplete, duplicate, missing, failed, timed-out, interrupted and resumed agents without fabricated replacement contributions | IN PROGRESS | Fault-injection tests with persisted audit evidence |
| QA-005 | Test concurrency, idempotency, retry semantics, race conditions, lock expiry and process crash recovery | IN PROGRESS | Repeated stress runs and duplicate-write assertions |
| QA-006 | Test database migrations from every supported released schema; include rollback/forward-fix decision and data-integrity checks | NOT STARTED | Migration matrix and restored fixture databases |
| QA-007 | Test supported browsers, display sizes, refresh, navigation, keyboard, screen reader, slow network and interrupted requests | IN PROGRESS | Browser matrix, console/network captures and accessibility audit |
| QA-008 | Test API schemas, authz boundaries, malformed payloads, injection, rate limits, pagination, error disclosure and version compatibility | NOT STARTED | API contract and negative-test reports |
| QA-009 | Run load, soak, spike, stress and capacity tests at expected tenant/role/inference volumes | NOT STARTED | Reproducible workload, resource profiles and acceptance thresholds |
| QA-010 | Run resilience tests for database loss, model service outage, cloud-region outage, queue backlog, provider throttling and DNS/certificate failure | NOT STARTED | Recovery-time and data-loss measurements |
| QA-011 | Conduct accessibility conformance testing against WCAG 2.2 AA for web UI, administration, onboarding, billing and support surfaces | NOT STARTED | Automated and expert manual audit; accessibility statement and remediation log |
| QA-012 | Validate language, locale, time-zone, date/time, number, currency, translation and right-to-left behavior where offered | NOT STARTED | Localisation test matrix and clinical translation review |
| QA-013 | Test browser rendering and UI state for flicker, stale data, blank screens, duplicate submissions and misleading progress | IN PROGRESS | Reproduction steps, console/network traces and regression tests |
| QA-014 | Require independent verification of safety-critical code paths, including stage/unknown semantics, audit, provenance, consensus and source mapping | NOT STARTED | Reviewer approval and targeted code/test review |
| QA-015 | Preserve raw model outputs and input hashes separately from normalized/derived repairs; record every repair and why it was permitted | IN PROGRESS | Audit artefact cross-check and regression tests |

## J. Reliability, observability, support and troubleshooting

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| OPS-001 | Define service SLI/SLOs for availability, latency, successful run completion, API errors, inference queue, data durability and support response | NOT STARTED | Approved SLO document and measurement dashboards |
| OPS-002 | Define contractual SLA, planned maintenance, exclusions, service credits and escalation; do not advertise unmeasured uptime | NOT STARTED | Counsel-reviewed SLA and evidence-backed service history |
| OPS-003 | Implement centralised structured logs, metrics and distributed traces with correlation/request/run/tenant IDs and strict content redaction | NOT STARTED | Dashboard, retention policy and redaction tests |
| OPS-004 | Implement alerts for elevated errors, latency, queue depth, token exhaustion, model unavailable, GPU/VRAM pressure, DB failures, tenant quota breaches and security signals | NOT STARTED | Alert rules, routing, ownership and tested paging |
| OPS-005 | Maintain customer-facing service status page and incident communications process | NOT STARTED | Status page, incident templates and update cadence |
| OPS-006 | Define backup cadence, point-in-time recovery, immutable/offsite copies, encryption, retention and tenant-level restore | NOT STARTED | Automated backup reports and restore drill |
| OPS-007 | Set and test recovery point objective (RPO) and recovery time objective (RTO) for each service tier | NOT STARTED | Timed restore/failover reports and customer commitments derived from evidence |
| OPS-008 | Test disaster recovery, regional outage, ransomware, key compromise, cloud account compromise and provider exit | NOT STARTED | At least annual tabletop and technical recovery evidence |
| OPS-009 | Create runbooks for login/SSO failure, account recovery, tenant mismatch, suspected cross-tenant access, API 4xx/5xx, DB lock/corruption, migration failure and export/deletion failure | NOT STARTED | Versioned runbooks and drills |
| OPS-010 | Create AI/Ollama troubleshooting runbooks for unavailable model, digest mismatch, model pull, invalid JSON, truncation, context allocation, timeout, OOM, GPU offload, CPU fallback, queue saturation and incorrect output | IN PROGRESS | Reproducible diagnostics, redacted log bundle, known-error catalogue and remediation tests |
| OPS-011 | Create frontend/browser troubleshooting runbooks for blank screen, refresh flicker, stale cache/state, failed API, CORS/auth/session errors and unsupported browsers | IN PROGRESS | Console/network capture guide and tested resolution procedures |
| OPS-012 | Create deployment/network troubleshooting for DNS, TLS expiry, WAF blocks, firewall/egress, proxy, rate limit, queue, storage and cloud-region failure | NOT STARTED | Operational playbooks and fault-injection results |
| OPS-013 | Define severity levels, 24x7 critical incident contact where contracted, support hours, response/resolution targets and clinical-safety escalation | NOT STARTED | Support policy and simulated incidents |
| OPS-014 | Maintain known-errors register with symptom, root cause, affected versions, diagnostic evidence, mitigation, fix, regression test and customer advisory | IN PROGRESS | Audited issue history; failures must not be silently closed |
| OPS-015 | Define maintenance windows, status notifications, security patch windows, emergency hotfix, rollback and customer communications | NOT STARTED | Operational change calendar and change records |
| OPS-016 | Establish vendor/third-party outage and exit plan for cloud, identity, email, payments, telemetry, LLM/model and backup providers | NOT STARTED | Dependency map, exit test and portability strategy |
| OPS-017 | Perform capacity planning, quota forecasts and unit economics for CPU/GPU, VRAM, tokens, storage, network egress, logs and backups | NOT STARTED | Measured cost per tenant/run and load curves |
| OPS-018 | Ensure operational telemetry never becomes a shadow clinical record or uncontrolled secondary copy of case data | NOT STARTED | Data-flow audit, sampling and retention test |

## K. Commercial operations, contracts and customer lifecycle

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| COM-001 | Decide legal entity, jurisdiction, ownership, IP assignment, founder/contractor agreements and authority to commercialise | NOT STARTED | Corporate and IP counsel review |
| COM-002 | Complete trademark/name/domain review and open-source brand attribution policy | NOT STARTED | Search results, ownership record and brand policy |
| COM-003 | Define customer segments, buyer/user/admin personas, procurement requirements and supported deployment options | NOT STARTED | Validated product/market requirements |
| COM-004 | Define pricing, tiers, trials, seat/run/token/storage limits, model/inference surcharges and overage controls | NOT STARTED | Unit-economics model and pricing approval |
| COM-005 | Implement subscription lifecycle: trial, activate, upgrade, downgrade, pause, suspend, cancel, refund and renewal | NOT STARTED | End-to-end payment/subscription tests |
| COM-006 | Use a compliant payment processor; avoid storing card data; document PCI DSS responsibility allocation and webhook verification | NOT STARTED | Provider assessment, signed contract, tokenised checkout and replay/signature tests |
| COM-007 | Implement billing ledger, invoices, tax handling, credit notes, failed payments, retries and reconciliation | NOT STARTED | Accountant-approved flows and month-end reconciliation |
| COM-008 | Implement tenant provisioning, trial expiry, administrator setup, user invitations, plan entitlements and offboarding | NOT STARTED | Tenant lifecycle E2E tests including deletion/export |
| COM-009 | Prepare Terms of Service/EULA, acceptable-use policy, privacy notice, cookie notice, DPA, SLA, support policy and order form | BLOCKED | Jurisdiction-specific legal review and approved version control |
| COM-010 | Prepare subprocessor list, vendor security schedule, data-processing clauses, audit rights, breach notice and deletion/return terms | NOT STARTED | Contract register and vendor sign-off |
| COM-011 | If serving HIPAA-regulated customers, complete covered-entity/business-associate analysis and BAA flow-down before PHI processing | BLOCKED | Executed BAA and security controls verified |
| COM-012 | Define customer onboarding, administrator training, secure configuration, user education and clinical-safety limitations | NOT STARTED | Onboarding guides, training and completion record |
| COM-013 | Create help centre, FAQ, release notes, changelog, known limitations, system requirements and support intake | NOT STARTED | Published versioned documentation |
| COM-014 | Provide customer data export, account closure, cancellation, complaints, dispute and escalation workflows | NOT STARTED | Customer journey acceptance tests |
| COM-015 | Establish sales/demo policy using synthetic examples only; prohibit fabricated testimonials, unsupported comparative/clinical claims and misleading performance statements | IN PROGRESS | Approved demo dataset, claims review and sales training |
| COM-016 | Assess professional indemnity, cyber liability, product liability and directors/officers insurance with broker/counsel | NOT STARTED | Written coverage analysis and bound policies where appropriate |
| COM-017 | Establish customer reference, logo, testimonial and case-study permission; no identifiable case materials without lawful approval | NOT STARTED | Signed permission and privacy review |

## L. Documentation and customer-facing transparency

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| DOC-001 | Publish architecture overview, deployment guide, system requirements and network/data-flow explanation | NOT STARTED | Versioned docs matching deployed release |
| DOC-002 | Publish user/admin guide for all rounds, saved records, Chair report, uncertainty, dissent, flags and export | IN PROGRESS | Usability-tested guide with screenshots from release |
| DOC-003 | Explain model identity/version, generated-content limitations, evidence/citation coverage and failure/abstention behavior | NOT STARTED | In-product transparency and help documentation |
| DOC-004 | Publish security overview, privacy notice, subprocessors, hosting/data-region details and incident contact | NOT STARTED | Legal/security approval and release URL |
| DOC-005 | Publish accessibility statement and known accessibility limitations | NOT STARTED | WCAG audit evidence and remediation plan |
| DOC-006 | Maintain API reference, versioning policy, authentication, rate limit, error catalogue and integration examples | NOT STARTED | OpenAPI spec validated against live endpoints |
| DOC-007 | Maintain administrator troubleshooting, backup/restore, identity integration and audit/export guides | NOT STARTED | Tested procedures |
| DOC-008 | Make all warnings, disclaimers and limitations consistent across UI, docs, website, marketing, invoices and contracts | IN PROGRESS | Cross-channel claims and safety copy audit |

## M. Release engineering, deployment and go-live

| ID | Deliverable / acceptance gate | Status | Required evidence |
|---|---|---|---|
| REL-001 | Maintain separate SaaS deployment pipeline and infrastructure boundary from the local Windows installer | NOT STARTED | Approved architecture and pipeline separation |
| REL-002 | Use immutable, signed release artefacts/images, deployment provenance, SBOM, checksums and controlled promotion | NOT STARTED | Release attestation and signature verification |
| REL-003 | Establish database migration, compatibility, rollback/forward-fix and data recovery plan for each release | NOT STARTED | Tested migration on production-like anonymised data and restore point |
| REL-004 | Gate production deploys on code review, unit/integration/E2E/security/accessibility tests, model-quality gates and approvals | NOT STARTED | Protected deployment environment and signed approval record |
| REL-005 | Conduct staging/UAT with synthetic data, representative customer workflows, tenant-isolation tests and operational drills | NOT STARTED | Signed UAT report and no unresolved critical/high defects |
| REL-006 | Perform pre-launch penetration test and close all critical/high security findings | BLOCKED | Independent report and verified retest |
| REL-007 | Complete clinical safety/regulatory/privacy/legal sign-offs for exact marketed functions and launch countries | BLOCKED | Signed release dossier |
| REL-008 | Verify backups, restore, RPO/RTO, monitoring, alert routing, incident rota, status page, customer support and rollback before launch | NOT STARTED | Go-live rehearsal and evidence bundle |
| REL-009 | Roll out using controlled pilot/canary, tenant allowlist, kill switch, feature flags, rollback and post-deploy verification | NOT STARTED | Pilot criteria, telemetry and signed go/no-go |
| REL-010 | Create release dossier: source commit, build ID, SBOM, provenance, test/scan reports, model digest, prompt/schema versions, known issues and approvals | NOT STARTED | Immutable release manifest |
| REL-011 | Establish post-release surveillance, security patching, user feedback, complaints, AI/model drift and evidence update review | NOT STARTED | Monitoring plan, review cadence and CAPA linkage |
| REL-012 | Do not label product production-ready, commercially distributable, secure, compliant, clinically validated or guideline-concordant until every applicable blocking gate is passed | IN PROGRESS | Release manager signed gate review; exceptions require documented authority and expiry |

## N. Mandatory programme-level go/no-go gates

| Gate | Status | Meaning |
|---|---|---|
| GATE-01 — Current 45-role R1–R4 execution and 136-contribution reconciliation | IN PROGRESS | Run-16 checkpoint and continuation remain unresolved; quality failures must be repaired and independently revalidated |
| GATE-02 — Clinical integrity, uncertainty, conditionality, source provenance, consensus and dissent | FAILED | Run-16 saved output contains material R1/R2/R3 integrity findings; continuation completion does not erase them |
| GATE-03 — Independent clinical evaluation and evidence/guideline retrieval | NOT STARTED | No clinical validation or guideline-concordance claim |
| GATE-04 — Indian regulatory classification and intended-use opinion | BLOCKED | No external clinical or institutional deployment until written assessment |
| GATE-05 — Privacy/data protection and health-data processing approval | BLOCKED | No real patient data or PHI processing |
| GATE-06 — SaaS identity, tenant isolation and cloud security architecture | NOT STARTED | Current local application is not an authenticated multi-tenant SaaS |
| GATE-07 — External penetration test and security risk closure | BLOCKED | No public/network exposure |
| GATE-08 — QMS/software lifecycle, traceability and post-market process where applicable | NOT STARTED | Scope depends on regulatory assessment; do not assert certification |
| GATE-09 — Reliability, backup/restore, disaster recovery, RPO/RTO and support readiness | NOT STARTED | No availability or SLA commitment |
| GATE-10 — Contracts, privacy notice, DPA, billing/tax, licensing and IP clearance | BLOCKED | No paid commercial launch |
| GATE-11 — Signed build, SBOM, provenance, supply-chain and controlled deployment | NOT STARTED | No trusted SaaS release artefact |
| GATE-12 — Final independent go-live review for exact release and market | NOT STARTED | Product owner, clinical, security, privacy, legal and operations sign-offs required |

## O. Standards, guidance, law and reference register

**Review date:** 16 November 2026. These references are a monitoring baseline, not a declaration of compliance. Obtain authoritative copies, verify current editions/amendments and applicability, maintain a licensed standards register, and have qualified counsel/regulatory/clinical experts interpret them. Full standards are often copyrighted and must be purchased/licensed; this checklist does not reproduce their text.

### India — priority for initial market assessment
- CDSCO, Guidance Document on Medical Device Software under MDR-2017, Doc. No. CDSCO/MD/GD/MDSW/01/2026, circular dated 21 July 2026: https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf
- CDSCO Medical Device & Diagnostics current index, including oncology and radiotherapy risk-classification list updates: https://cdsco.gov.in/opencms/opencms/en/Medical-Device-Diagnostics/Medical-Device-Diagnostics
- Digital Personal Data Protection Act 2023 and commencement notification G.S.R. 843(E), 13 November 2025 (official Gazette): https://egazette.gov.in/WriteReadData/2025/267647.pdf
- Digital Personal Data Protection Rules 2025, G.S.R. 846(E), 13 November 2025 (official Gazette): https://egazette.gov.in/WriteReadData/2025/267650.pdf
- IT Act 2000 and SPDI Rules 2011: https://www.indiacode.nic.in/ and https://www.meity.gov.in/
- CERT-In Directions, 28 April 2022: https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf
- Consumer Protection Act 2019: https://consumeraffairs.gov.in/
- GST and tax: https://www.gst.gov.in/ and https://www.incometax.gov.in/

### United States, EU and UK — only if those markets/functions are in scope
- FDA, Clinical Decision Support Software Guidance for Industry and FDA Staff, final guidance, January 2026: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- FDA, Quality Management System Regulation (QMSR), effective 2 February 2026; incorporates ISO 13485:2016 by reference for applicable device manufacturers: https://www.fda.gov/medical-devices/quality-management-system-regulation-qmsr
- EU Regulation 2017/745 (MDR) and current consolidated text: https://eur-lex.europa.eu/eli/reg/2017/745/oj
- MDCG 2019-11 rev.1, June 2025, Guidance on Qualification and Classification of Software: https://health.ec.europa.eu/system/files/2025-06/mdcg_2019_11_en.pdf
- European Commission MDCG guidance index (check later revisions; MDCG 2021-24 rev.1 was listed April 2026): https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- EU AI Act Regulation (EU) 2024/1689, current consolidated text: https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng
- European Commission AI Act implementation timeline (includes current phased dates following Digital Omnibus amendments): https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline
- UK MHRA medical-device software guidance and UK legislation: https://www.gov.uk/government/organisations/medicines-and-healthcare-products-regulatory-agency

### Software quality, medical-device lifecycle, safety and usability
- ISO 13485:2016, Medical devices — Quality management systems — Requirements for regulatory purposes; verify national adoption and current amendments.
- IEC 62304:2006 + AMD1:2015, Medical device software — Software life cycle processes; ISO catalogue reported the 2006 edition confirmed in 2023 with the 2015 amendment.
- ISO 14971:2019, Medical devices — Application of risk management to medical devices; ISO catalogue reported confirmed current in 2025.
- IEC 82304-1:2016, Health software — Part 1: General requirements for product safety; ISO catalogue showed a systematic review opened 15 July 2026, so re-check status before baselining.
- IEC 62366-1:2015 + AMD1:2020, Medical devices — Application of usability engineering to medical devices; verify current edition and applicability.
- ISO 20417, Information supplied by the manufacturer of medical devices; verify current edition.
- ISO 15223-1, Symbols to be used with information supplied by the manufacturer of medical devices; verify current edition.

### Security, privacy, AI and software supply chain
- ISO/IEC 27001:2022, Information security management systems — Requirements: https://www.iso.org/standard/27001
- ISO/IEC 27017, ISO/IEC 27018 and ISO/IEC 27701: cloud security, PII protection and privacy information management; verify current editions/amendments before procurement or certification claims.
- ISO/IEC 42001:2023, Artificial intelligence management system: https://www.iso.org/standard/42001
- ISO/IEC 23894:2023, Artificial intelligence — Guidance on risk management: https://www.iso.org/standard/77304.html
- NIST CSF 2.0, NIST CSWP 29 (26 February 2024): https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20
- NIST SP 800-218 SSDF v1.1 and SP 800-218A generative-AI community profile: https://csrc.nist.gov/Projects/ssdf
- NIST AI RMF 1.0 and NIST AI 600-1, Generative AI Profile (26 July 2024): https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP Application Security Verification Standard (ASVS) 5.0.0 (30 May 2025): https://asvs.owasp.org/
- OWASP GenAI LLM Top 10 2026 (published 4 August 2026; use active GenAI Security Project source, not the legacy 2025 archive): https://genai.owasp.org/
- OWASP API Security Top 10 (2023): https://owasp.org/API-Security/
- SLSA supply-chain levels and provenance: https://slsa.dev/
- SPDX and CycloneDX SBOM formats: https://spdx.dev/ and https://cyclonedx.org/

### Accessibility, reliability and service management
- W3C WCAG 2.2 Recommendation, 12 December 2024: https://www.w3.org/TR/wcag/
- ISO/IEC 40500:2025 (WCAG 2.2); verify the latest 2026 amendment/status where relevant.
- ISO 22301, Business continuity management systems; verify current edition.
- ITIL 4 service management practices / incident, change, problem and service-level management; use as operational guidance, not as a certification claim.

### Radiation oncology and oncology knowledge sources
- NCCN Clinical Practice Guidelines in Oncology and NCCN updates: https://www.nccn.org/guidelines
- ASTRO Clinical Practice Guidelines: https://www.astro.org/provider-resources/guidelines
- ESTRO recommendations and resources: https://www.estro.org/
- ESMO Clinical Practice Guidelines and eUpdates: https://www.esmo.org/guidelines
- ASCO guidelines: https://www.asco.org/guidelines
- IAEA Human Health Campus and publications: https://www.iaea.org/resources/hhc and https://www.iaea.org/publications
- WHO Classification of Tumours / IARC: https://tumourclassification.iarc.who.int/
- AJCC staging resources: https://www.facs.org/quality-programs/cancer-programs/american-joint-committee-on-cancer/
- ICRU reports: https://www.icru.org/
- Core textbook catalogue examples (edition must be checked at each evidence refresh): Perez, Brady, Halperin, and Wazer's Principles and Practice of Radiation Oncology, 8th edition (2025; LWW); Gunderson and Tepper's Clinical Radiation Oncology, 6th edition (2026; Elsevier); Khan's The Physics of Radiation Therapy, 6th edition (2019; Wolters Kluwer). Publisher catalogue links: https://shop.lww.com/ and https://shop.elsevier.com/
- Add site-specific texts as required: medical oncology, surgical oncology, pathology, radiology, nuclear medicine, paediatric oncology, palliative care, medical physics, brachytherapy and radiobiology. Each must have an author/editor, ISBN, publisher, edition, publication date, errata, licence and review owner.

## P. Commonly missed engineering controls — mandatory anti-vibe-coding review

| ID | Frequently omitted control | Status | Required evidence |
|---|---|---|---|
| VIBE-001 | Requirements and acceptance criteria written before implementation | NOT STARTED | Approved requirements baseline |
| VIBE-002 | Traceability from user need to design, code, test, risk and release artefact | NOT STARTED | Bidirectional traceability report |
| VIBE-003 | Architecture decision records and explicit non-goals | NOT STARTED | ADR index with reviewers |
| VIBE-004 | Threat model and abuse cases before exposing APIs or models | IN PROGRESS | Current reviewed threat model |
| VIBE-005 | Data dictionary, schema constraints, migration and rollback strategy | IN PROGRESS | Versioned schema docs and migration tests |
| VIBE-006 | Idempotency, transaction boundaries, locking and concurrency/race tests | IN PROGRESS | Fault-injection and stress results |
| VIBE-007 | Observability and correlation IDs with sensitive-data redaction | NOT STARTED | Trace/log/metric schema and privacy tests |
| VIBE-008 | Accessibility and keyboard/screen-reader usability | NOT STARTED | WCAG 2.2 AA audit |
| VIBE-009 | Browser/device compatibility, responsive layout and real-user workflow tests | IN PROGRESS | Browser matrix and E2E artefacts |
| VIBE-010 | Dependency pinning, SBOM, licence review and reproducible builds | IN PROGRESS | Build artefacts and SBOM |
| VIBE-011 | Backups, restore drills, disaster recovery, data export and deletion | NOT STARTED | Tested RPO/RTO and deletion reports |
| VIBE-012 | Authentication, authorisation, tenant isolation and privileged access | BLOCKED | Full IAM and penetration-test acceptance |
| VIBE-013 | Privacy notice, DPA, data map, retention, subprocessor and breach process | BLOCKED | Counsel-approved documents and tested data handling |
| VIBE-014 | Monitoring, alert ownership, on-call, incident response and customer status | NOT STARTED | Operational drills |
| VIBE-015 | Upgrade, downgrade, cancellation, billing reconciliation and customer offboarding | NOT STARTED | Subscription lifecycle E2E tests |
| VIBE-016 | Model digest, prompt/schema versioning, evaluation set and rollback | IN PROGRESS | Per-run provenance and model-change approval |
| VIBE-017 | AI red-team, prompt-injection, data exfiltration and denial-of-wallet testing | NOT STARTED | Independent GenAI test report |
| VIBE-018 | Performance budgets, load/soak tests, cost model and capacity limits | NOT STARTED | Reproducible measured report |
| VIBE-019 | Release signing, build provenance, deployment approval and rollback | NOT STARTED | Signed release dossier |
| VIBE-020 | Customer support, product documentation, claims review and support runbooks | IN PROGRESS | Complete support/documentation package |
| VIBE-021 | Independent legal, regulatory, privacy, clinical and security review | BLOCKED | Signed reviews; developer self-review is not a substitute |
| VIBE-022 | Post-release surveillance, complaint/CAPA, security updates and evidence/guideline refresh | NOT STARTED | Operated review cadence and retained records |

## Q. Checklist maintenance and release discipline

1. This document remains the **single authoritative master checklist**. Do not create a separate SaaS checklist that can drift. Other documents may contain detailed procedures but must link back here.
2. Every new feature, API, integration, model, prompt, dataset, market, data category or marketing claim must be assessed against applicable sections above before merge/release.
3. Keep original raw records and prior failures. A corrected model output does not erase the original, and a later pass does not retroactively change the earlier run's status.
4. Any VERIFIED row must record commit SHA/build ID, test/CI run, artifact hash, test environment, reviewer and verification date. Any FAILED item remains visible until a documented corrective change and passing re-test are linked. Any BLOCKED item must name the blocking dependency and owner.
5. Re-check official laws, guidance and standards before each country launch and at least quarterly; check immediately after a regulator, standards body, publisher or critical vendor update.
6. A paid SaaS beta, public SaaS launch, hospital pilot, real-patient data use and clinical decision-support use are separate approval gates. Approval for one does not imply approval for another.
7. No public network exposure, production PHI processing, real-patient pilot, clinical-use marketing or paid SaaS launch is authorised by this checklist update.
8. Do not claim the project is commercially distributable until all applicable BLOCKED, FAILED and NOT STARTED release gates are closed with evidence and independent sign-offs.

**Commercial readiness at this checkpoint:** NOT READY. The existing local application has useful engineering/packaging and test foundations, but the current project evidence does not establish SaaS identity, multi-tenancy, cloud security, DPDP/privacy readiness, regulatory classification, clinical validity, evidence licensing, contractual readiness, operational resilience, penetration-test acceptance or production service reliability.
