# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Latest application code/test HEAD:** `9b9d3d3b8c3b32c075c003385f253ec6986c707f` (Backend `43783537385`: **362 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **7/7 passed**). All six exact-head PR workflows succeeded: Backend `43783537385`, Frontend `43783537334`, Browser E2E `43783537341`, Windows Installer `43783537343`, Packaging Prerequisites `43783537331`, Security/Dependency/CodeQL `43783537413`. Backend artifacts: JUnit diagnostics `14189221503`, preflight `14188599455`; installer artifact `14189506990`. First Qwen run `43782748488` failed before generation (0/12); digest and PowerShell finalizer fixes are covered by this exact-head CI. Corrected Qwen retry `43783994924` is currently running; no retry digest or outputs are available yet. No MedGemma inference or current RTX 4060 request-time verification.

Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| Four-round R1–R4 architecture/data flow | IN PROGRESS | Implemented with regression coverage; full current-head 45-role live acceptance outstanding. |
| R1 independent assessment | IN PROGRESS | Run 43714529807 / simulator run c4592dbb-ecc7-4007-9125-d0baaed9abb0 inherited R1 45/45 contributions; all positions were insufficient_information. Eleven persisted TNM flag instances across seven roles split into five qualifier/negation false positives (covered by 11fa2fb no-inference tests) and six unqualified cT1N0M0 preferred-option references in RO-01/SG-07 that remain genuine findings. Run #9 did not regenerate R1; historical rows/flags remain unchanged. |
| R2 debate and peer sourcing | IN PROGRESS | Run `43714529807` has 45/45 saved R2 roles, all `insufficient_information`; 40/45 had role-range citation flags (13 unique strings). A no-inference audit of run-9 SQLite shows 44/45 narratives assert selected-peer alignment, absence of substantive disagreement or peer consensus despite **0/45 structured agreements and 0/45 substantive challenges**. `SV-02` is the exception: it records no substantive agreement or disagreement and therefore is not counted as an alignment claim. Commit `534bbe1` removes explicit peer IDs/ID lists from model-facing R2 prompts while server `source_peer_ids` remains exact. Commit `1d28b96` adds sentence-level peer-overclaim flags; Chair exposes them in unresolved disagreements. Regression coverage and exact-head CI pass on `3ccbe1c` (324 backend tests). Historical R2 text/flags remain unchanged; live qwen3.5:4b effectiveness remains unverified. |
| R3 adversarial review | IN PROGRESS | Run `43753957255` saved 45/45 R3 roles. Raw SQLite: 269 source-reference flag entries across 27/45 roles, 89 exact raw strings. No-inference category breakdown: 67 role-range entries, 107 unsupplied individual-source entries, 82 case-summary/source-review binding entries and 13 other peer/review-binding entries. The Chair's 247 finding count is distinct role/finding pairs after within-role deduplication; 22 repeated entries are in MO-08 and SG-01. SO-06 has two historical case-integrity flags. Current code now (a) tests the exact `rather than converting them into categorical claims of unmet or absent conditions` wording as a negated/non-asserted prerequisite statement (`3ccbe1c`), and (b) stores unregistered model-authored source reviews only in `model_reported_source_opinion_reviews`, excluding them from active clinical-claim auditing and canonical source-opinion/Chair inputs; R3 tests cover the fabricated `no option is indicated` review-basis wording. These are no-inference regressions, not live-model evidence. The historical run-9 DB is unchanged; no current-head live R3 revalidation. |
| R4 Chair synthesis | IN PROGRESS | Run 43753957255 saved one completed Chair R4 report (SG-07). It reports insufficient_information, empty proposition-level consensus, and no treatment recommendation; its deterministic narrative records R1/R2/R3 as 45/45 insufficient-information. The continuation validator incorrectly required R1: while the Chair emits Round 1: and aborted before quality-flag collection; corrected by script/test commits 0db6402 and de49d9c with 320-test CI. The saved report is not retroactively revalidated and run #9 remains failed acceptance due to its other saved findings. |
| Clinical safety/unsupported claims | IN PROGRESS | Deterministic audits exist; no exhaustive clinical validation. MO-07's negated peer-attribution false positive was corrected by `49730bd`; five qualifier/negation R1 TNM false positives are covered by `11fa2fb`, while six unqualified `cT1N0M0` preferred-option references in RO-01/SG-07 remain genuine findings and are still quarantined in Chair. Run-9 SO-06's two historical case-integrity findings now have separate no-inference regressions in current code (`3ccbe1c` plus earlier unregistered-review isolation); historical flags remain unchanged and live-model revalidation is outstanding. Earlier run `43698959463` also contained unsupported T1/T2/N0 and `No comorbidities` assertions. |
| TNM connector CodeQL remediation | IN PROGRESS | Python and JS/TS CodeQL passed on latest exact-head run `43768624991`; a formal historical alert record query remains unavailable, so closure is not claimed. |
| Unknowns, staging and contradictions | IN PROGRESS | Not-reported semantics and discrepancy warnings exist; semantic coverage and human review remain required. The run `43698959463` Chair report quarantined unsupplied T1/T2 and N0 staging assertions and unsupported absence of comorbidities. Never infer these fields from lesion size or empty arrays. |
| Conditional recommendations/prerequisites | IN PROGRESS | Deterministic checks exist; full live-output audit outstanding. |
| Distinct-role Chair counting | VERIFIED | Regression coverage and exact-baseline backend CI passed; complete live consensus validation still outstanding. |
| Proposition consensus, dissent and position history | IN PROGRESS | Deterministic reconciliation/tests exist; full current-head report audit outstanding. |
| Case hashes, run IDs, timestamps and audit history | IN PROGRESS | Mechanisms exist; complete current-head reproducibility audit outstanding. |
| Provenance and source attribution | IN PROGRESS | R3 evidence quotes bind only to original saved R2 records; unregistered CASE reviews are preserved in raw `model_reported_*` fields and excluded from canonical Chair inputs. R2 model-facing peer IDs/enumerated list removed; exact `source_peer_ids` remains server-owned. Sentence-level R2 peer-overclaim detector and Chair unresolved-disagreement visibility have regression coverage. Run-9 audit shows 40 R2 range flags and 44/45 broad alignment/consensus narratives; R3 has 269 raw source-flag entries across 27 roles (67 ranges, 107 unsupplied individual refs, 82 case/source-review binding entries, 13 other peer/review-binding entries). Historical records unchanged; live-model verification outstanding. External evidence retrieval/guideline verification not implemented. |
| Missing/failed agent handling | IN PROGRESS | Validation mechanisms exist; current-head incomplete-case/failure-injection acceptance outstanding. |
| Synthetic model-screening execution | IN PROGRESS | Workflow, runner, digest normalization and resilient finalizer are CI-verified on application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`: 362 backend tests passed, preflight 7/7, all six standard workflows passed. First Qwen run `43782748488` failed before generation (0/12). Corrected Qwen retry `43783994924` is active in the isolated Ollama provisioning/screening step on hosted Windows CPU; GitHub has not exposed logs, digest or artifacts yet. MedGemma remains blocked behind manual HAI-DEF terms attestation. |
| Synthetic screening workflow guard | VERIFIED | Workflow YAML is registered by GitHub Actions; marker-gated push run `43783532169` concluded `skipped` because it had no `[model-integrity-screen]` marker. Three workflow safety regressions and deterministic `WORKFLOW_MODEL_SCREEN_001` preflight passed on `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; all six standard workflows passed. This proves the workflow guard only, not model inference. |
| Qwen 12-case baseline inference | IN PROGRESS | First hosted attempt [43782748488](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782748488) provisioned Ollama 0.40.14 and pulled `qwen3.5:4b`; full digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` was captured, but the Python runner rejected the bare `/api/tags` digest before generation. JSONL summary: **0/12**, `execution_failed`; artifact `14189605356`. The PowerShell finalizer defect is also corrected. Retry [43783994924](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783994924), triggered by workflow commit `359fb69cd7c6b5f18d61d655fcf1a230a01b0ae1`, is still in the isolated provisioning/screening step; no retry digest/output/artifact is available yet. |
| Qwen digest/finalizer correction | VERIFIED (software scope) | `run_medgemma_screening.py` now accepts a full bare 64-hex or `sha256:`-prefixed digest and canonicalizes it; the end-to-end mocked runner test uses a bare digest and verifies all 12 responses. The PowerShell finalizer uses `(Get-Date).ToUniversalTime()`, catches manifest/log failures without bypassing cleanup, and validates the isolated executable path using a directory-prefix comparison. Exact-head CI on `9b9d3d3b8c3b32c075c003385f253ec6986c707f`: 362 backend tests passed, preflight 7/7, all six standard workflows passed. This does not prove the live retry has succeeded. |
| MedGemma 12-case inference | BLOCKED | MedGemma pull is disabled on push runs. It requires explicit manual dispatch with `include_medgemma=true` and a separate HAI-DEF terms acceptance/authority attestation. No attestation or local model digest has been supplied; no MedGemma pull or inference has occurred. Commercial/legal clearance remains a separate gate. |
| Live-validation source-integrity quality gate | FAILED (run #9) | Run 43753957255 ended failed_resume_validation after completing R3 45/45 and saving Chair R4. The validator stopped on the R1/Round 1 label mismatch before integrity-gate evaluation; quality_gate_failures=[] in the JSON is an unexecuted default, not a pass. The inherited six R1 stage findings, 40 R2 range flags and run-9 R3 source/case findings remain open. SQLite integrity is ok; run is CPU-only. The corrected validator has CI but has not yet been rerun against the saved report. |
| Backend tests | VERIFIED | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Backend run `43783537385`: **362 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **7/7 passed**. Includes bare-digest normalization, full 12-case mocked runner, finalizer/cleanup and workflow guard regressions. JUnit diagnostics `14189221503`; preflight `14188599455`. No real model inference in CI. |
| Frontend build | VERIFIED | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Frontend run `43783537334` succeeded. |
| Browser registry/dashboard E2E | VERIFIED | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Browser E2E run `43783537341` succeeded. Dedicated flicker/stale-state investigation remains outstanding. |
| Packaging prerequisites | VERIFIED | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Packaging run `43783537331` succeeded. |
| Windows installer build/smoke test | VERIFIED | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Installer run `43783537343` completed build, install, smoke test, checksum and artifact upload; artifact `14189506990`. Optional Ollama/model bootstrap was not part of this workflow. |
| Dependency/security workflows | VERIFIED (analysis execution); alert closure pending | Exact application/test commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`; Security/Dependency/CodeQL run `43783537413` succeeded for Python and JS/TS CodeQL, full-history secret scan and dependency audit. Formal historical TNM alert closure remains unconfirmed. |
| Frontend flicker/blank screens/stale state | IN PROGRESS | Browser E2E passes; dedicated reproduction and console/network/lifecycle investigation outstanding. |
| Dashboard/API integration | IN PROGRESS | Baseline browser E2E passed; current-head acceptance outstanding. |
| Ollama context allocation | VERIFIED (hosted CPU stage-boundary scope) | In run `43698959463`, `api/ps` and `ollama ps` snapshots after R1/R2/R3/R4 showed loaded `qwen3.5:4b` at context lengths 4096/6144/8192/4096 respectively, processor 100% CPU and VRAM 0. These are stage-boundary/runtime snapshots, not per-request token-truncation proof and not GPU evidence. |
| R3 Ollama request-context propagation | IN PROGRESS | `_context_window_for_schema` maps the main adversarial draft to 8,192; the `80abe9e` no-inference test captures the actual `/api/generate` request and confirms `options.num_ctx=8192`. Live per-stage runtime allocation/truncation evidence remains outstanding. |
| Effective R3 context/truncation | IN PROGRESS | R3 schema/request regression asks for 8192. Live `api/ps` and `ollama ps` after R3 in run `43698959463` observed 8192 with the loaded model; R1/R2/R4 boundaries observed 4096/6144/4096. This verifies stage-boundary allocation on the hosted CPU run, but not every R3 request's effective context or whether inputs were truncated. |
| RTX 4060 active inference | IN PROGRESS | Historical laptop GPU measurements exist; current-head request-time GPU/offload verification outstanding. |
| Full live 45-role MDT | IN PROGRESS (historical R3/R4 saved; acceptance failed) | Source run #16 `43714529807` supplied R1/R2 45/45 each and R3 17/45; continuation run #9 `43753957255` completed R3 45/45 and saved Chair R4 but ended `failed_resume_validation` on the old `R1:` versus `Round 1:` validator mismatch. Artifact `14182277535`; simulator run `c4592dbb-ecc7-4007-9125-d0baaed9abb0`; old runtime source SHA `28fd7eccfa0e32200eefb995158e8788b0296c97`; qwen3.5:4b, CPU-only, concurrency 1. Validator fix and R2 citation/overclaim changes have no-inference CI; SO-06 historical false-positive mechanisms have targeted tests in current code commit `3ccbe1c`. No current-head live rerun; this does not establish clinical accuracy or RTX 4060 inference. |
| Live artefacts/reproducibility | IN PROGRESS | Run #9 artifact `14182277535`, ZIP SHA-256 `1fc370307f84f802a7749c8dae78a0eba20289c409a54c87feca8b1fc86c79b6`; SQLite SHA-256 `a38555f0a95ba0327941bd12f366479cfff2526d0c799ebbdeba68d50c97e6c0`, `PRAGMA integrity_check=ok`. Saved run ID `c4592dbb-ecc7-4007-9125-d0baaed9abb0`, R1/R2/R3 rows 45 each and R4 row 1. Report stopped before final summaries/quality gate; preserve immutable artifact and audit history. |
| Evidence retrieval/guideline verification | NOT STARTED | Retrieval is not connected; no guideline concordance is claimed. |
| Independent clinical review | NOT STARTED | Qualified clinical review/acceptance not performed. |
| Windows release/security acceptance | IN PROGRESS | All six standard code/test workflows passed on exact commit `9b9d3d3b8c3b32c075c003385f253ec6986c707f`: Backend `43783537385`, Frontend `43783537334`, Browser E2E `43783537341`, Packaging `43783537331`, Installer `43783537343`, Security/CodeQL `43783537413`. Historical TNM alert closure, live clinical-integrity acceptance, authentication/security hardening and qualified clinical review remain open. |
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
 
**Second continuation attempt — completed with validator failure**
- Trigger commit 28fd7eccfa0e32200eefb995158e8788b0296c97; workflow run [43753957255](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255), job 132933850581; artifact [14182277535](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255/artifacts/14182277535).
- Pinned Ollama 0.40.14 and qwen3.5:4b were provisioned; checkpoint model digest matched exactly. CPU inference ran for 7,400.74 seconds. The run saved 45/45 R3 contributions and one Chair R4 report, then returned failed_resume_validation with "Chair synthesis omits R1 position counts".
- Root cause: deterministic Chair prose labels distributions "Round 1:", "Round 2:" and "Round 3:", while the resume validator searched only for "R1:", "R2:" and "R3:". All 45/45 count tokens were present in the corresponding prose sections. The validator stopped before integrity-flag collection, so quality_gate_failures=[] is only the initial default and must not be read as acceptance.
- Chair R4 reports insufficient_information, no proposition-level consensus points and no treatment recommendation. The R3 audit has 269 raw source-reference flags across 27 roles and two SO-06 case-integrity flags; the Chair summary reports 247 distinct per-role findings; the 269 raw entries include 22 repeated same-role findings, so the deterministic aggregation is reconciled. Run #9 uses an older workflow SHA and does not contain the subsequent TNM/provenance corrections. CPU-only; no RTX telemetry.
- Current code/test commit de49d9c8d9c0398f8ece2faabcd2259cabbdd629 fixes the label mismatch, validates each count under its own round section, requires 45-role denominators, accepts both supported label forms, and has three regression tests. Exact-head backend CI: 320/320 passed. No new live inference was started.

## MO-07 false-positive case-integrity audit correction — 16 November 2026

The run-16 SQLite artifact was downloaded and inspected. The exact saved MO-07 R2 text at `response_to_other_perspectives` states:

> No peer proposes a definitive treatment pathway as indicated, nor do any claim that an option is contraindicated based on missing data alone.

This is a **negated peer-attribution statement**, not an assertion that chemotherapy or another option is contraindicated. The old case-integrity matcher nevertheless searched the substring `is contraindicated` and generated one treatment-safety/indication flag. The model repair then proposed generic wording that dropped the original R1 reference tokens; the deterministic anchor check correctly blocked the repair and retained the original text. The repair fallback itself was not evidence that the original sentence was a clinical contraindication claim.

**Corrective change**
- Commit `49730bd26f82b77f762885504c97385fc80e72f7` updates `attributed_status_report_pattern` in `backend/app/services/case_integrity.py` to recognise the explicit `nor do any claim` negated peer-attribution construction.
- Added regressions: the exact saved MO-07 wording must not trigger a treatment-safety flag; a separate positive assertion after a clause boundary (`however, surgery is contraindicated`) must still be flagged.
- The intervening categorical-status rewrite helper and its tests from commits `225a4d3` and `a86fa1b` were withdrawn in `49730bd`; they are not part of the current branch implementation. This is an explicit correction of the earlier diagnosis, not a silent history rewrite.

**Exact-head validation on `49730bd26f82b77f762885504c97385fc80e72f7`**
- Backend [43759314836](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314836): 315 passed, 0 failed/errors/skipped, 1 warning; deterministic preflight 6/6 passed. Both new negation/positive-control tests passed.
- Frontend [43759314812](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314812), browser E2E [43759314832](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314832), packaging prerequisites [43759314824](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314824), Windows installer [43759314815](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314815), and security/dependency/CodeQL [43759314861](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314861): all succeeded.
- Installer artifact [14179537651](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43759314815/artifacts/14179537651), 14,866,238 bytes. The optional clean-hosted Ollama/model bootstrap was skipped.
- The original run-16 SQLite/JSON remains unchanged, including its recorded flag and blocked repair metadata. The corrected matcher is unit/CI-tested; a no-inference re-audit of the saved artifact using current code and a new live run are still required before changing historical acceptance conclusions.

## R3 provenance prompt isolation and immutable source-evidence binding — 16 November 2026

Raw SQLite inspection of run #16 (`43714529807`) shows the 84 R3 source/provenance flags across eight roles split exactly into:
- 17 invalid range references (MO-04 2, MO-05 1, MO-06 5, MO-07 4, MO-08 1, RO-07 1, RO-08 3).
- 28 unsupplied individual round IDs (MO-04 4, MO-06 10, MO-07 6, RO-07 2, RO-08 6).
- 20 non-CASE / unregistered peer-review source IDs in MO-01.
- 19 invented or unbound CASE review flags in MO-08.

**Implementation sequence**
- `019243e92a146a83375085a33e04cc470bb24897` changes the R3 prompt-facing provenance flags and excerpts to pass through `_compact_r2_text`, neutralising embedded round IDs and role ranges while leaving saved R2 payloads unmodified. It preserves model-authored source-opinion reviews in `model_reported_source_opinion_reviews` and excludes them from canonical `source_opinion_reviews` when the server-owned case-summary opinion register is empty.
- `3fb39c9d49f0ba20431b95fba1e972024435f85d` updates an existing test to assert the new canonical-exclusion/raw-preservation contract. The first CI run correctly identified a stale assertion; the follow-up test was corrected without weakening the implementation.
- `ff636a22e23ce077ac1463252938535882e015d5` changes evidence quotation binding to select the original peer record from `peer_debate_views` and search its original saved R2 fields. The prompt-sanitised peer representation is never used as evidence for a canonical source citation. The new regression proves a sanitised-only phrase such as “the referenced role records” cannot be accepted as a quote from the original R2 record.
- Exact-head backend [43763432712](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432712): **317 passed**, zero failures/errors/skips, one warning; deterministic preflight **6/6 passed**. The raw-evidence binding and earlier sanitation/unregistered-review regressions passed.
- All other exact-head workflows passed: frontend [43763432696](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432696), browser E2E [43763432668](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432668), packaging prerequisites [43763432683](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432683), installer [43763432661](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432661), and security/CodeQL [43763432626](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43763432626).
- The original run-16 DB and JSON are unchanged. These fixes are unit/CI verified but not live-model verified. Run #9 [43753957255](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255) completed 45/45 R3 and Chair R4 on old workflow SHA 28fd7eccfa0e32200eefb995158e8788b0296c97, so it does **not** contain these fixes. Its 269 raw R3 flag entries across 27 roles de-duplicate to 247 role/finding pairs under the Chair algorithm; this count reconciliation is confirmed, but the underlying source flags remain unaccepted.
## R2 peer provenance prompt change — 16 November 2026

Run-16/R2 audit showed 40/45 roles with source-reference flags and 13 unique invalid range strings. For each flagged R2 output, the range endpoints corresponded to the first and last role in that response's server-selected `source_peer_ids` list. The previous prompt exposed every `R1:ROLE` source ID, then instructed the small model not to compress those IDs into ranges; the model repeatedly compressed the list.

**Change on current branch**
- Commit `534bbe1209d9c3f1b7869bd6ffc1a99b8a6c4ffb` removes `source` ID fields from R2 model-facing peer objects and removes the explicit enumerated allowed-ID list from the R2 prompt. Peer names and selected contribution content remain visible.
- The prompt now says peer provenance is recorded separately by the server, instructs the model not to emit round-qualified IDs in prose, and asks it to refer to peers by their exact supplied role names. This is a targeted reduction in range-compression prompting, not a guarantee of model compliance.
- The server still stores exact selected IDs in `RoundContribution.source_peer_ids`. The server-side `_audit_source_references(payload, allowed_sources)` remains active and flags generated ranges, unsupplied IDs or malformed references. Raw model output is retained; there is no automatic range expansion or historical rewrite.
- Commit `b8b6fe30ae2b248baf7cd4a5c8c0c2751c7f9fa1` updates prompt regressions to assert that R2 model input contains role names but no `R1:ROLE` IDs or allowed-ID list; the fake malformed response still verifies broad ranges and unsupplied IDs are flagged.
- Exact-head backend [43768624980](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768624980): 320 passed, zero failures/errors/skips, one warning; deterministic preflight 6/6 passed. Frontend [43768625002](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768625002), browser E2E [43768624989](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768624989), packaging [43768625042](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768625042), installer [43768625012](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768625012), and security/CodeQL [43768624991](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43768624991) all succeeded.
- This is no-inference CI only. The 40 historical R2 flags remain in the saved checkpoint. A new current-head live run is required to determine whether qwen3.5:4b stops compressing peer lists or still emits ranges.
## R2 citation and agreement audit remediation — 16 November 2026

**Historical evidence (run #16 / continuation #9):** R2 saved 45/45 completed roles, each with empty structured `agreements` and `substantive_challenges`. Raw R2 source-reference flags affected 40/45 roles and included 13 unique role-range forms. A forensic review found broad peer-agreement language in 44/45 R2 narratives, including claims of complete peer alignment/no substantive disagreement, despite role-specific options and no structured agreement proposition. Identical `insufficient_information` labels or shared missing-data observations are not substantive agreement.

**Current branch changes:**
- Commit `534bbe1209d9c3f1b7869bd6ffc1a99b8a6c4ffb` removes round-qualified source IDs from the R2 prompt-facing peer records and removes the enumerated allowed-ID list. Peer role names and selected content remain present. The exact server-selected IDs remain in `source_peer_ids`; generated ranges and unsupplied IDs continue to be flagged without range expansion or rewriting raw text.
- Code commit `1d28b9615d1c48d6cc05a0ee8a98e5b5ef5ce05b` adds an R2-only sentence-level detector for broad claims such as all selected peer positions align, no substantive disagreement exists, or complete agreement/consensus among peers. An explicitly worded rebuttal is not flagged; unrelated subsequent sentences cannot suppress a warning. The original generated narrative is preserved.
- The warning uses existing `source_reference_integrity_flags`; Chair reconciliation places per-role source-reference audit findings in `unresolved_disagreements`. It is intentionally not mislabelled as case-data integrity.
- Backend regressions cover unsupported claims, legitimate rebuttals, unrelated later uncertainty/reference sentences, generated range/unsupplied-ID negative controls, and Chair carry-through. Exact code/test HEAD `6229c1822978cf278faf14cd012e085b3194eb52` backend run `43771081852` passed 324/324 (1 warning); preflight 6/6. Other current-head CI: frontend `43771081814`, packaging `43771081881`, security `43771081802` passed; browser E2E `43771081851` and installer `43771081805` were still running at update time.
- These are no-inference code/test changes. They do not retroactively alter run #16 / #9 records and do not prove qwen3.5:4b will stop generating peer ranges or unanimity claims on a live run.
## R2 saved-output audit detail — 16 November 2026

A no-inference inspection of the preserved run-9 SQLite database (`c4592dbb-ecc7-4007-9125-d0baaed9abb0`) used the original `agent_round_results` rows without changing them:
- R2 saved rows: 45/45 completed; every R2 position was `insufficient_information`.
- 40/45 R2 roles had a saved source-reference flag; all 40 were non-attributable `R1:ROLE through R1:ROLE` range citations. There were 13 distinct range endpoint forms.
- 44/45 R2 `response_to_other_perspectives` narratives matched the new peer-wide agreement/absence-of-disagreement detector. They claimed that all selected peers align, no substantive disagreement exists, or consensus exists; one SV-02 narrative instead states that no substantive agreement or disagreement was identified.
- Structured `agreements`: **0/45 non-empty**. Structured `substantive_challenges`: **0/45 non-empty**. Identical `insufficient_information` position labels are not evidence of agreement on an educational option.
- This finding justifies retaining the R2 peer-agreement audit warning as a source-integrity finding and surfacing it in the Chair's unresolved section. The wording is preserved in the source row; no automatic rewriting or synthetic consensus is created.
- The new no-inference code path is unit-tested at `6229c18` (324/324 backend tests). It has not yet been run against a new live model response; historical R2 rows remain immutable.

## R1 TNM audit false-positive correction — 16 November 2026

The raw SQLite `agent_run_results` rows were inspected for all seven roles with R1 TNM flags. The original 11 flag instances (T1 x7, N0 x2, M0 x2) split as follows:

- **Five qualifier/negation false positives:** MO-06 “Review NCCN guidelines for T1/T2 glottic SCC once staging is confirmed”; RO-09 “Review standard-of-care guidelines for cT1 glottic SCC once staging data is provided”; SG-03 “does not automatically equal T1”; SG-04 “cannot be converted to T1”; SO-08 “T1 glottic cancer pending full workup”.
- **Six remaining unsupported references:** RO-01 and SG-07 each used unqualified `cT1N0M0` in the preferred educational option, without explicit conditional/hypothetical framing. Those remain flagged. RO-01's separate “Assume cT1N0M0 for guideline illustration only” discussion option is explicitly hypothetical and is not a positive stage assertion.

**Correction**
- Commit `11fa2fb3075431a35ab6e6e1beb8b09927760c79` extends the TNM-specific negative prefix patterns for “does not ... equal” and “cannot be converted”, and adds a bounded conditional suffix recogniser for staging-confirmed/provided and pending full work-up language.
- New no-inference regression exercises the five exact false-positive wordings and verifies that an unqualified patient-stage statement `cT1N0M0` remains flagged.
- Exact-head backend [43760995773](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995773): **316 passed**, 0 failures/errors/skips; deterministic preflight **6/6 passed**. All six standard workflows succeeded on this exact code/test commit: frontend [43760995797](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995797), browser E2E [43760995899](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995899), packaging [43760995796](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995796), installer [43760995836](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995836), and security/CodeQL [43760995774](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43760995774).
- This is regression evidence for the five exact phrase classes, not an in-place re-evaluation of the historical SQLite record. The raw DB/JSON remains unchanged with all 11 original stored flags. Six unqualified stage findings remain valid failures. The live run must be regenerated and fully audited before any acceptance status changes.

## Run #16 forensic record — 16 November 2026

Workflow [43714529807](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43714529807), run #16, runtime commit `4683b0767bf5cade408e85ec31ef248b34e5321e`; workflow conclusion `failure`. The sole job `132813068060` ran 14,356.24 seconds before the nested `Provision isolated portable Ollama and qwen3.5:4b` step reached its configured 240-minute timeout. Ollama 0.40.14 and `qwen3.5:4b` provisioned successfully (model digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`). The Python process was in `ensure_round(run_id, 3)` / `mdt_rounds.run_mdt_round`; cancellation propagated through `asyncio.gather` while agent tasks awaited the concurrency semaphore. This is evidence of workflow-step timeout and cancellation, not proof of a semaphore deadlock.

The saved SQLite database gives the precise work state: R1 45/45 complete (3,298.7s; 73.3s mean); R2 45/45 complete (6,455.6s; 143.5s mean); R3 17/45 completed, SO-01 running, 27 queued; R4 absent. The 17 R3 generations averaged 262.9s (4.38 min) each; their combined saved duration was 4,470s (74.5 min). A linear projection for 45 R3 calls is about 197.2 min. Adding observed R1/R2 time yields about 359.8 min before Chair synthesis and provisioning/cleanup overhead. This projection is approximate; remaining roles may take longer or shorter. Concurrency was explicitly 1; no concurrency increase is justified without a measured benchmark. GitHub documents a 6-hour maximum execution time per GitHub-hosted job ([Actions limits](https://docs.github.com/en/actions/reference/limits)). The current 240-minute step cut off the run; merely raising the timeout is not a reliable single-job remedy given the approximately six-hour projection and platform ceiling.

Artifact `14169603817` (`radonc-hosted-cpu-four-round-validation`) archive SHA-256 `73a7ece5be348e36a1458c9d6f3679fe694a6b5d08c03556a82988859f5e1392`; simulator run ID `c4592dbb-ecc7-4007-9125-d0baaed9abb0`. Artifact downloaded and inspected. SQLite `integrity_check` returned `ok`; `foreign_key_check` returned no rows. Case snapshot hash `8fdc3c2536c6c3487d3142498a1731e57ea4eefbb5a110b6ce98b105d069393f` matched both JSON and SQLite. It contains 1,032 CPU/Ollama process samples, 3 stage snapshots and no NVIDIA measurements; final `/api/ps` showed `context_length=8192`, `size_vram=0`, and CLI `100% CPU`. This is CPU-only telemetry, not GPU proof or per-request truncation proof.

**Live quality findings are separate from timeout:** R1 recorded 11 TNM flags across 7 roles. Raw-text review identifies five qualifier/negation false positives now covered by `11fa2fb` regressions, and six unqualified `cT1N0M0` option references in RO-01 and SG-07 that remain genuine findings; historical SQLite flags remain unchanged. R2 recorded 40 source-reference flags across 40 roles (13 unique strings), and one MO-07 case flag is now identified as a false-positive negated peer-attribution match corrected by `49730bd`. The 17 saved R3 outputs had 84 source-reference flags across 8 roles (50 unique strings), including unbound CASE opinion reviews and unsupplied/role-range references; 16 risk flags and 31 challenge entries were saved, but their provenance is not accepted. No R4 report exists. This incomplete run cannot be accepted after timeout remediation alone; remaining R1 stage findings and R2/R3 provenance defects require live revalidation.

## Updated immediate priorities — 16 November 2026

1. Preserve the exact-head CI baseline on application commit `3ccbe1c`: 324 backend tests and all six standard workflows passed; the hosted Ollama/model bootstrap was skipped.
2. Retain the run-9 no-inference audit: 6 genuine R1 `cT1N0M0` references in RO-01/SG-07; 40 R2 citation-range flags and 44/45 broad peer-alignment claims; 269 R3 source-reference entries across 27 roles, including 67 range, 107 unsupplied-ID, 82 case/source-review-binding and 13 other findings. Do not rewrite historical rows or flags.
3. SO-06's two old R3 case-integrity mechanisms have targeted current-code regression coverage; keep historical flags visible and require a new live run before declaring the issue resolved in model output.
4. Verify the R2 model-facing peer-ID removal and overclaim detector on live qwen3.5:4b; compare every narrative with exact server-owned `source_peer_ids`, saved structured agreements/challenges, and preserved raw output. Do not infer success from unit tests.
5. Keep the six genuine R1 stage assertions quarantined; no stage should be inferred or silently repaired. Review the affected option text and the Chair's saved handling before the next live run.
6. Only schedule one current-head resumable four-round live validation after static audit/acceptance assertions are ready; keep concurrency 1 and collect full audit artefacts.
7. Keep RTX 4060 request-time activity, effective context/truncation, incomplete-agent recovery, guideline retrieval, qualified clinical review, security and release acceptance as separate gates.

## Immediate priorities

1. Preserve and extend the no-inference re-audit of run #16/run #9; source DB/JSON and historical flags are immutable.
2. Verify R2 citation and peer-agreement behavior on a current-code qwen3.5:4b run; no automatic role-range expansion.
3. Verify that SO-06's current no-inference regressions match future model behavior; do not call the old saved flags retroactively cleared.
4. Prepare a single current-head four-round run only after acceptance assertions cover role coverage, source binding, unregistered review isolation, R2 overclaim handling, missing/failed agents, Chair counts and audit artefacts.
5. Do not claim GPU inference, clinical validation, guideline compliance or release readiness from CPU CI or run #9.

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
| AI-001 | Maintain model registry: provider, name, exact digest, quantisation, licence, version, runtime, hardware, parameters, prompt versions and supported purpose | IN PROGRESS | MedGemma Google ID/version and Ollama Q4_K_M package metadata identified; the local full digest, exact Ollama runtime, hardware measurements and per-run record remain outstanding. |
| AI-002 | Verify model licensing, commercial SaaS rights, acceptable-use terms, attribution, redistribution and hosting conditions for Qwen/Ollama and every alternative | BLOCKED | MedGemma is governed by HAI-DEF Terms of Use (open-weight, not open-source); redistribution/hosted-service conditions and regulatory provisions require documented legal review before packaging, hosting or commercial release. |
| AI-003 | Define provider privacy and security contracts: region, retention, training use, subprocessors, access, audit, incident notice and deletion | BLOCKED | Vendor due diligence, DPA/BAA where required and verified technical settings |
| AI-004 | Keep model calls local to approved infrastructure or use a contractually approved inference provider; block unapproved outbound transfer | IN PROGRESS | Network egress tests, endpoint allowlist and prompt-data flow audit |
| AI-005 | Keep R1 independent; enforce exact R2/R3 peer allowlists, source-bound quotes and R4 use of actual saved R1–R3 contributions | IN PROGRESS | Existing regression suite plus full-run audit and no cross-round leakage tests |
| AI-006 | Deterministically enforce counts, schema, state transitions, missing/failed agents, consensus, dissent, prerequisites and provenance outside the LLM | IN PROGRESS | Code-level validation and adversarial regression tests |
| AI-007 | Treat model output, retrieved documents, uploaded files, peer text and tool results as untrusted; prevent prompt injection and indirect instruction takeover | NOT STARTED | Threat model, hostile-source test corpus and fail-closed test results |
| AI-008 | Test hallucinated staging, fabricated investigations, unsupported negative findings, invented comorbidities, false consensus and loss of conditionality | IN PROGRESS | Synthetic integrity screening corpus added; still requires paired model runs and independent review. Zero tolerance for detected critical fabrication; no finite test can prove zero hallucinations for all future inputs. |
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
| AI-021 | Evaluate Google MedGemma as a candidate specialist reasoning model against the current Qwen baseline; verify exact official model artefact/tag, digest, quantisation, Ollama compatibility and licence before use | IN PROGRESS | Google model ID/version and Ollama tag identified. Hosted screening workflow and digest-capture path are CI-tested on `b69f1243708aa34853fefd5162f2d34ba8a12d56`; no local model digest, MedGemma pull or inference yet. Explicit HAI-DEF terms attestation is required before a MedGemma pull; legal/commercial clearance remains BLOCKED. |
| AI-022 | Benchmark MedGemma on the frozen RadOnc MDT failure corpus, including unsupported TNM/staging, R2 false agreement, citation fabrication/ranges, R3 provenance, conditionality, missing data and failed-agent cases | IN PROGRESS | The 12-case corpus and runner are implemented. Workflow guard/preflight tests pass on `b69f1243708aa34853fefd5162f2d34ba8a12d56` (355 backend tests, 7/7 deterministic preflight, six standard workflows). The hosted workflow is marker-gated; no Qwen or MedGemma generation output, model digest, paired comparison or independent review exists yet. |
| AI-023 | Measure MedGemma feasibility on RTX 4060 8GB with actual request-time GPU offload, VRAM, context/KV-cache, latency and CPU fallback; retain concurrency 1 | NOT STARTED | Captured nvidia-smi/Ollama request telemetry and repeatable resource/latency report |
| AI-024 | Define MedGemma promotion/rollback gate; retain Qwen as baseline until MedGemma demonstrates a meaningful, reproducible safety/quality improvement without unacceptable performance or licensing risk | NOT STARTED | Approved acceptance thresholds, model digest pinning, rollback test and documented go/no-go decision |


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


## R. Priority workstream — MedGemma model evaluation

**Priority: P1 — high priority candidate-model evaluation. Status: NOT STARTED.** This is the next planned model-evaluation workstream; it is not an approved model replacement and does not supersede the failed live-validation gate or deterministic safety controls.

### Required sequence

1. **Verify the exact model first.** Identify the current official Google MedGemma release, exact artefact and digest, supported quantisations, model card, intended-use limitations, licence and commercial/redistribution terms. Separately verify whether a maintained Ollama package/tag exists and whether its conversion/packaging is faithful. Do not invent or assume a tag such as `medgemma:4b` or `medgemma1.5:4b`.
2. **Freeze the evaluation corpus.** Include the historical RadOnc MDT failure patterns: unsupported T/N/M and comorbidity claims; R2 claims of agreement without shared propositions; invented/range citations; R3 fabricated or unbound source references; loss of conditional prerequisites; missing/failed agents; and incomplete staging. Preserve positive controls so fixes do not suppress genuine findings.
3. **Run paired inference.** Compare the pinned current Qwen model with the pinned MedGemma candidate using identical case inputs, role prompts, schemas, context budgets, decoding settings and sequential concurrency. Record exact model digests, prompt/schema versions, runtime and run IDs. No real-patient data.
4. **Evaluate clinical and data integrity separately.** Measure unsupported assertions, staging accuracy against supplied facts, proposition-level agreement fidelity, citation/source binding, conditionality, missing-data handling, output completeness and specialist-role performance. Obtain independent radiation-oncology/MDT review; automated scores alone are insufficient.
5. **Test hardware feasibility.** On the RTX 4060 8GB, measure actual request-time GPU utilisation, offloaded layers, VRAM, context/KV-cache, latency and CPU fallback. Model loading or allocated VRAM alone is not proof of GPU inference. Keep concurrency at 1 unless measured results justify a change.
6. **Make a documented go/no-go decision.** Promote MedGemma only if it provides a meaningful and repeatable quality/safety improvement, fits the target runtime, and passes licence/security review. Otherwise retain Qwen. Keep a tested rollback path and never silently change the model digest.

### Priority order and dependencies

- **P0 — ongoing safety gate:** continue remediation and revalidation of the historical R1/R2/R3/R4 failures. A better model cannot repair deterministic source binding, consensus calculation or audit integrity.
- **P1 — MedGemma evaluation:** begin exact artefact/licence verification and frozen-corpus preparation; proceed to paired inference only after those prerequisites are recorded.
- **P2 — model promotion:** only after paired evaluation, independent clinical review, GPU/performance verification and licence approval.
- **P3 — broader evidence retrieval/RAG:** develop separately with approved, current, versioned sources; do not treat model selection as a substitute for evidence retrieval.

**Current decision:** Qwen remains the baseline. MedGemma is a high-priority candidate for controlled evaluation, not yet selected, installed, benchmarked, GPU-verified or clinically validated.

## S. MedGemma candidate verification — 16 November 2026

**Priority:** P1 — high-priority candidate model screening. **Decision:** Qwen remains unchanged; MedGemma is not selected or production-approved.

### Verified candidate identity
- Google model ID: `google/medgemma-1.5-4b-it`; Google model version `1.5.0`; Google describes it as a 4B multimodal instruction-tuned model.
- Ollama Library tag: `medgemma1.5:4b-it-q4_K_M`. Ollama's public registry lists Gemma 3, 4.3B parameters, Q4_K_M, about 3.3 GB, text/image input and a 128K context listing.
- Ollama's public tag page displays short identifier `433252621ab1`. This is not recorded as a full immutable digest. Capture the full local `/api/tags` digest after model pull, plus `ollama show --modelfile`, Ollama version and full package record, before any benchmark.
- Google identifies the canonical upstream model as `google/medgemma-1.5-4b-it`. The Ollama registry listing does not, by itself, prove byte-for-byte identity of the converted package against the upstream weights; record and review packaging/conversion provenance.

### High-impact documented limitation
Google's MedGemma model card states that the model has not been evaluated or optimised for multi-turn applications. It also says outputs are preliminary, require independent verification/clinical correlation, and are not intended to directly inform clinical diagnosis, patient management or treatment recommendations. This is a direct evaluation risk for this simulator's R1–R4 multi-round workflow.

### Licence and hardware boundaries
- MedGemma is under the Health AI Developer Foundations Terms of Use. Google's FAQ states HAI-DEF models are open-weight, not open-source. Redistribution/hosted-service obligations and regulatory provisions require legal review. **No legal clearance is claimed.**
- Public Q4 package size/static weight footprint is approximately 3.3–3.4 GB, but runtime fit on the RTX 4060 8 GB is unverified; KV cache, context and runtime overhead are additional. Actual GPU activity requires request-time telemetry and Ollama offload evidence.

### Next controlled sequence
1. Freeze the Qwen baseline full digest and MedGemma full local digest in the same Ollama environment.
2. Review the 12-case synthetic software-integrity corpus and its structural test; this is not a clinical gold-standard dataset.
3. Conduct sequential, bounded candidate screening at concurrency 1, preserving immutable outputs and error records.
4. Apply deterministic source, schema, missing-data, conditionality, consensus and Chair integrity checks.
5. Obtain blinded independent clinical review before any wider live workflow.
6. Proceed to representative-role and full 136-contribution runs only if the critical gate is clean and runtime/legal prerequisites are met.

**Zero-hallucination requirement:** Zero tolerance for any detected critical fabrication during evaluation. No finite test corpus can prove that a generative model will never hallucinate. Do not claim absolute zero hallucinations; design the application so unverified model claims cannot become accepted facts or untraceable Chair conclusions, and fail closed on detected integrity failures.

**Current status:** model identity/tag and documented limitations verified; 12-case synthetic corpus, digest-gated paired-screening harness, strict output envelope, immutable artefact handling and raw-response preservation VERIFIED by exact-head CI on `a9415b5` (348 backend tests; six workflows pass). Full local digest NOT STARTED; legal clearance BLOCKED; model pull NOT STARTED; live Qwen/MedGemma screening NOT STARTED; RTX 4060 inference verification NOT STARTED; independent clinical validation NOT STARTED.

### MedGemma screening harness first CI attempt — corrective record

| Evidence | Status | Detail |
|---|---|---|
| Commit `5b7f7e653478ef276b83f7d4970782b3309b4b04` backend workflow `43777495870` | FAILED | 345 passed, 2 failed, 0 errors, 0 skipped; deterministic preflight 6/6 passed. The two failed tests are described in `docs/MODEL_BENCHMARK_PLAN.md`. No live model calls occurred. |
| Corrective change in `9280e52` | VERIFIED | Removed verbatim R4 oracle wording and case-folded the R1 assertion. A stale round-task expectation remained and was corrected in the next commit. The original failed CI record is retained. |

### MedGemma screening harness second CI attempt — corrective record

| Evidence | Status | Detail |
|---|---|---|
| Commit `9280e52687db054c15f634b27ea35eb2919577f7` backend workflow `43777711230` | FAILED | 346 passed, 1 failed, 0 errors, 0 skipped; deterministic preflight 6/6 passed. The remaining test asserted the old R1 instruction after the prompt had been changed to remove answer-key leakage. |
| Corrective change in `3768d57` and final hardening in `a9415b5` | VERIFIED | Updated tests for neutral round tasks; added raw-response retention on post-generation provenance failure. Final exact-head backend and all six workflows passed on `a9415b5`. |

### MedGemma screening harness exact-head verification — 16 November 2026

| Evidence | Status | Result |
|---|---|---|
| Commit `a9415b579108b26867ebf9a9670e48527b03ffb1` — Backend `43778122628` | VERIFIED | 348 passed, 0 failed, 0 errors, 0 skipped; 1 warning. Deterministic preflight 6/6 passed. Includes 12-case corpus validation, oracle non-disclosure, full SHA-256 gating, exact response envelope, and raw-response preservation test. |
| Frontend `43778122666` | VERIFIED | Success on the exact commit. |
| Browser E2E `43778122654` | VERIFIED | Real-browser patient registry and saved dashboard workflow passed. |
| Windows packaging prerequisites `43778122655` | VERIFIED | Success on the exact commit. |
| Windows installer `43778122683` | VERIFIED | Build/install/smoke/checksum/upload passed; artifact `14187730022`; installer SHA-256 `821f45d0806e9f6df9114433a4e93535ff28534a8386fb551b5bf0b6035166ae`. |
| Security/dependency/CodeQL `43778122625` | VERIFIED | Success on the exact commit. |
| Optional hosted Ollama/model bootstrap | NOT STARTED | Explicitly skipped by the Windows installer workflow. No Qwen or MedGemma model was pulled or run. No GPU proof is available from this CI. |

**Scope limitation:** This verification establishes the screening harness code, schema guards and CI build/test behavior only. It does not establish model accuracy, clinical reliability, zero hallucinations, MedGemma superiority, a local model digest, model pull success, GPU activity or full 45-role MDT acceptance.

## MedGemma screening runner orchestration regressions — 16 November 2026

**Current application/test commit:** `e4a0f381e22ee01712377302f75eefb2591e4709`.

The screening runner previously had helper-level tests but lacked no-inference coverage of the complete `run_screen` orchestration. Three tests were added to `backend/tests/test_medgemma_screening.py`:

- `test_run_screen_records_complete_immutable_case_set`: exercises the full 12-case sequence against a mocked Ollama API; checks exact model digest before/after calls, captured metadata and metrics, unique case records, pending-human-review status, and refusal to overwrite an existing evidence file.
- `test_run_screen_stops_before_generation_when_digest_changes`: proves generation is not called when the installed model digest changes between preflight and inference.
- `test_run_screen_preserves_raw_response_when_digest_changes_after_generation`: proves the raw generation response and available inference metrics remain in the evidence record when the post-generation digest check fails; the run remains incomplete.

**Exact-head CI:** all six PR workflows succeeded on `e4a0f381e22ee01712377302f75eefb2591e4709`: Backend `43779329766`, Frontend `43779329760`, Browser E2E `43779329708`, Packaging Prerequisites `43779329705`, Windows Installer `43779329711`, Security/Dependency/CodeQL `43779329877`. The backend workflow individually records all three new tests as passed; deterministic preflight was 6/6. Backend artifacts: JUnit diagnostics `14187731917` and preflight report `14187438637`.

**Scope limitation:** This is mocked-API software regression evidence, not a model inference run or quality evaluation. The installer workflow's optional hosted Ollama/model bootstrap was skipped. Qwen/MedGemma local digests, downloads, outputs and comparative results remain unavailable; GPU and independent clinical review remain outstanding.

## Model-screening workflow guard CI correction and first execution — 16 November 2026

**Retained failed CI attempt**
- Application/preflight commit: `61ec66de9c1866e2dca162f930d15d817e42d3dc`.
- Backend PR workflow: [43782131320](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782131320) — **FAILED**: 353 passed, 2 failed. The repository-level deterministic preflight itself passed 7/7; the failures were tests using a minimal synthetic repository fixture that omitted the exact manual-dispatch MedGemma terms condition and the second terms re-check inside the optional MedGemma branch.
- No model provisioning or inference occurred in this CI run. The underlying hosted workflow guard passed against the real repository.
- Correction: commit `b69f1243708aa34853fefd5162f2d34ba8a12d56` updated the minimal test fixture to represent the exact workflow gates; the safety guard was not weakened.

**Corrected exact-head verification**
- Backend run [43782354539](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354539): **355 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **7/7 passed**. New workflow guard tests and all three screening-runner orchestration tests passed.
- Frontend [43782354458](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354458), Browser E2E [43782354464](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354464), Packaging [43782354434](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354434), Installer [43782354454](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354454), Security/CodeQL [43782354467](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782354467): all succeeded on the same application/test commit.
- Backend artifacts: JUnit diagnostics `14188454566`, preflight `14188384627`; installer artifact `14188579519`.

**Live Qwen baseline trigger**
- Workflow [43782748488](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782748488), source SHA `38c65e2bf07b931c71497ef4a38bd655901ff0eb`, is a marker-qualified push on the development branch.
- At the latest check the hosted Windows job remained in its isolated Ollama provisioning/screening step. The terms-attestation step was skipped, so this is Qwen-only. No full model digest or JSONL evidence was yet available to inspect.
- Do not mark screening successful until the completed workflow manifest, full digest, 12 case records, raw outputs, per-call metrics, and summary are inspected. A completed set remains pending human review and is not a quality pass.
## First hosted Qwen screening attempt — failure analysis and correction — 16 November 2026

**Failed live attempt**
- Workflow [43782748488](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782748488), workflow source commit `38c65e2bf07b931c71497ef4a38bd655901ff0eb`, Qwen-only marker-qualified push.
- Hosted runner successfully provisioned the pinned Ollama `0.40.14` runtime on `127.0.0.1:11435`, verified the runtime, pulled `qwen3.5:4b`, and captured full digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` (3,324,173,934 bytes; Q4_K_M).
- The runner's separate `/api/tags` response returned the same complete 64-hex digest without a `sha256:` prefix. `require_installed_model_record` incorrectly required the prefix, so it aborted at preflight before the first `/api/generate` call. The JSONL records `execution_failed`, **0 responses / 0 of 12 cases**, with error: “does not have a full SHA-256 digest.” This is a digest representation compatibility bug, not a Qwen response or quality failure.
- Evidence artifact [14189605356](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43782748488/artifacts/14189605356) contains the run manifest and Qwen JSONL. The manifest records the full canonical digest; the runner JSONL records the preflight rejection. No model output was generated or available for human review.
- A second, independent PowerShell issue occurred during workflow finalization: `[DateTime]::UtcNow()` was parsed as a method call that does not exist. It interrupted manifest finalization and the remaining explicit Ollama cleanup statements. The hosted runner was ephemeral and the job ended; no local machine process was involved. Preserve this failed run and artifact unchanged.

**Corrective code and regression coverage**
- `backend/scripts/run_medgemma_screening.py` accepts either a bare 64-character hexadecimal digest or `sha256:<64 hex>`, validates the entire value, and canonicalizes to lowercase `sha256:<hex>` before all preflight, pre-generation and post-generation comparisons. Short identifiers, malformed hex and ambiguous model records remain rejected.
- The full mocked 12-case runner test now supplies the bare-digest form observed in the real Ollama runtime and asserts that all recorded per-call and pre/post digests are canonical and identical.
- Additional unit tests cover bare, uppercase, prefixed and uppercase-prefixed full digests, while malformed and short digests remain rejected.
- The PowerShell finalizer now uses `(Get-Date).ToUniversalTime().ToString("o")`; manifest/log finalization failures are caught so they cannot bypass isolated-process cleanup. Cleanup verifies the process executable is under the isolated Ollama directory before attempting to stop it, and stop failures are recorded as warnings.

**Corrected exact-head software verification**
- Application/test commit: `9b9d3d3b8c3b32c075c003385f253ec6986c707f`.
- Backend [43783537385](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537385): **362 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **7/7 passed**. The bare-digest full-run test and finalizer/cleanup regression passed.
- Frontend [43783537334](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537334), Browser E2E [43783537341](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537341), Packaging [43783537331](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537331), Windows Installer [43783537343](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537343), Security/CodeQL [43783537413](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783537413): all succeeded.
- Backend artifacts: JUnit `14189221503`, preflight `14188599455`; installer artifact `14189506990`.
- **Live retry has not yet been run.** Passing tests do not retroactively make run `43782748488` successful. Do not treat either model as screened until a new 12/12 run completes and its immutable manifest/JSONL is inspected.