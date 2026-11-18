# RadOnc MDT Simulator — Master Development and Verification Checklist

**Current status as of 18 November 2026. This is the single authoritative checklist.**

### Latest deterministic R2/R4 patch — 18 November 2026

- R2 application/test head: `0bb85c1446ab16ecef90d89bcbda8f5b8204c197`; latest R4 application change: `c8448c93614728d4d55c552e95d791f7accab7b9`; latest regression-test correction: `df7b3d0cd7ddf4ef260cafb7a8979b65a640250c`. Exact-head PR validation is recorded below. PR #1 remains open/draft/unmerged and `main` is unchanged.
- `442b4ab28290057f4e2a2a5727905dd54b8186eb`: Chair finalizer now reports failed/unusable role rows and missing role rows against the configured 45-role input, without counting failed records.
- `5cf470855886c992bdad7011054b7ab0cc7e26b0`: Chair R4 prompt digest carries the saved R2 debate narrative and fuller server-bound source excerpt, analysis and comparison.
- `458b2522ec3616556694caad1a0d110971c5f70d` and `4225c73e57565a6f57624757eae939163a944803`: append the exact server-bound case-opinion register to saved R2 `response_to_other_perspectives`, explicitly labelled as verbatim source text and not specialist-authored conclusions, verified facts or endorsements; render it with real line breaks.
- `0efbfe1ca558742b012c06b228a7ca2b7e54531e`: raised the saved contribution narrative bound to 4,200 characters to accommodate at most four bounded source excerpts alongside the model narrative.
- `2269d80dbcf0b1046bc66ed521721b4db79f0245`, `65a573affcb6af8ccb98a163e2c17ebb191df2bd`, `d838382d7731353d306b73ec2b4ad9064d16d854`, and `0bb85c1446ab16ecef90d89bcbda8f5b8204c197`: regression coverage for missing/failed roles, R4 source retention, and R2 server-bound narrative/source excerpt fidelity. R4 follow-up `c8448c9` adds an attributed saved-contribution sample from each round to the deterministic Chair synthesis and places failed/absent-input disclosure in the primary Chair conclusion. Regression commits `dd44a38`, `8d53154` and final assertion correction `df7b3d0`. Intermediate fixture assertion failures on runs 44302382270 and 44302873061 are retained in CI history; the corrected exact-head suite passed 480/480.
- Exact PR-head CI on `df7b3d0` (application/test head; checklist-only descendants do not change code): Backend [44303234900](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234900) SUCCESS, 480/480 pytest passed, 0 failed/errors/skips; deterministic preflight 7/7. Frontend [44303234944](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234944) SUCCESS; Browser E2E [44303235009](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303235009) SUCCESS (patient registry, Mission Control, Development Monitor, four-round dashboard); Packaging Prerequisites [44303234914](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234914) SUCCESS. Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880) FAILED at npm audit with the same four HIGH `picomatch@4.0.7` findings; Python dependency audit, both CodeQL analyses and full-history secret scan passed. Windows Installer [44303234950](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234950) SUCCESS: installed health and silent uninstall/database preservation passed; installer SHA-256 `d0e3ab0c1b91874cf2f13450734746e70561abdff2d80ce5bfedd721b4f588a7`; artifact [14427096490](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234950/artifacts/14427096490). Clean-hosted Ollama/model bootstrap was SKIPPED. No Qwen/MedGemma inference, GPU verification or clinical validation.

Historical checkpoints below are immutable evidence and do not override this table.

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Development branch:** `feature/four-round-mdt-and-performance`  
**PR #1:** open, draft, unmerged; base `main`.  
**PR head verified before this checklist refresh:** `df7b3d0cd7ddf4ef260cafb7a8979b65a640250c` (R4 code and corrected regression suite; checklist update is a documentation-only descendant).  
**Latest application code commits:** `4225c73e57565a6f57624757eae939163a944803` (R2 exact server-bound attributed-opinion register) and `c8448c93614728d4d55c552e95d791f7accab7b9` (R4 deterministic saved-round highlight synthesis and primary-input completeness disclosure).  
**Latest backend regression-test commit:** `df7b3d0cd7ddf4ef260cafb7a8979b65a640250c` (R4 saved-contribution traceability and primary completeness disclosure; backend 480/480 passed).  
**Latest frontend provenance-visibility commit:** `afbe6af6ffbc463ad92457e5179545c92b55b398`; E2E selector corrections in `198c8be7dfa203fba51eec99f9a2151738dabc12` and `1e8d3559dc12e7aa1b7599f9bd076b3873f4e88b`.  
**Latest source-bound browser fixture correction:** `1c8a22b435e047f6524b9172ae3663d40a9d127c`; test excerpt is now literally embedded in the disposable `case_summary`, not merely stored as an unrelated string.  
**Main:** `39a356b8eb09399aa2da1b9b9085965999f5105a`; unchanged.  
**Current checklist update:** the one authorised Qwen-only v16/audit-v15 synthetic screen completed on push run [44263369594](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594), artifact [14409068927](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594/artifacts/14409068927). Execution succeeded, but 4 cases were automatically flagged with 6 deterministic review flags, plus 3 further manual audit observations. Acceptance remains PENDING_HUMAN_REVIEW; this is not a model pass. The one-run temporary risk acceptance is consumed. Audit-v16 code is CI-verified but has not been live-model screened. No further Qwen or MedGemma run is authorised without fresh explicit risk review and security disposition.

## Master Checklist — Current Status

| Workstream | Status | Evidence / boundary |
|---|---|---|
| Four-round R1–R4 architecture and persisted data flow | IN PROGRESS | Implemented; fresh full 45-role live acceptance is outstanding. |
| R1 independent specialist assessments | VERIFIED | Round implementation and saved contribution flow covered by backend tests; live model quality remains unverified. |
| R1 unknown/staging safeguards | IN PROGRESS | The audit-v16 deterministic checks now flag denial of the supplied diagnosis-field fact and omission of opposing Source A / Source B laterality statements. Exact tests passed in run 44267217866. No live audit-v16 screen has been run; the original R1 findings remain part of the audit-v15 historical result. |
| R2 saved-source identity and exact ordering | VERIFIED | Exact specialist-ID gate checks saved R1 records before R2, R2 before R3, and R3 before Chair R4. |
| R2 proposition-level consensus and conditionality | IN PROGRESS | Historical v16 narrative failures remain unresolved at model level. R2 now appends every server-identified attributed case opinion as an exact, labelled source excerpt with its conditions in the saved narrative; it is explicitly distinguished from the model-authored response and is not endorsement. R4 also receives fuller saved R2 material. Regression passed in exact-head backend run [44298209261](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44298209261), 479/479. Semantic correctness of model-authored R2 analysis remains unverified. |
| R3 adversarial review and source provenance | IN PROGRESS | Audit-v16 flags a JSON response containing the synthetic_input field; regression test passed in backend run 44267217866. This is a narrow output-echo check, not comprehensive R3 model validation. R3-FABRICATED-QUOTE-009 rejected the unsupported quote in the historical audit-v15 screen. |
| R4 Chair synthesis from actual saved R1–R3 | IN PROGRESS | Deterministic finalizer now includes failed/absent-role accounting in the primary Chair conclusion and appends safe, attributed, one-per-position examples from saved R1, R2 and R3 contributions to the overall synthesis. The examples are non-exhaustive and are explicitly not consensus or verified clinical facts. Exact regression run [44303234900](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234900): 480/480 passed. Historical v16 model-level synthesis/traceability failures remain unresolved; no live-model retest was run. |
| Cross-round minority-history regression | VERIFIED | New test `test_final_chair_boundary_retains_earlier_and_later_minority_histories` passed in backend run 44262841444; it verifies an earlier R1 minority remains visible alongside a different R3 minority. This is a deterministic regression test, not live-model acceptance. |
| Chair consensus, distinct-role counting, dissent and traceability | FAILED | Deterministic counts exist, but v15 model-level consensus/dissent findings remain unresolved by live retest. |
| Exact specialist-ID input gate | VERIFIED | Guard in `47dfa9d`; corrected regression in `8cde5dd`; exact regression-test-head backend run 44262841444 passed (473/473 pytest rows, re-counted from job logs). |
| Missing/failed-agent handling | IN PROGRESS | Deterministic Chair report identifies failed/unusable rows by status and reports absent rows against the configured 45-role roster; failed records remain excluded from distinct-role counts. Regression passed in exact-head backend run [44298209261](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44298209261). Entirely absent upstream rows cannot be individually named without a complete roster in the Chair input. |
| Clinical safety, staging and unknown data | IN PROGRESS | Deterministic safeguards exist; no clinical validation, guideline concordance or zero-hallucination guarantee. |
| Case integrity, contradiction preservation and audit history | IN PROGRESS | Historical raw outputs retained. Three audit-v16 deterministic checks now cover the three manual false negatives recorded from v16/audit-v15. Exact regression tests passed, but there is no live audit-v16 model rerun; raw case and audit history remain preserved. |
| Provenance and guideline/evidence retrieval | IN PROGRESS | Source-bound controls exist; current guideline retrieval/verification incomplete. |
| Backend tests — exact R4 regression head `df7b3d0` | VERIFIED | Exact-head backend run [44303234900](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234900): raw logs confirm 480/480 pytest passed, 0 failed/errors/skips; deterministic preflight 7/7. R2 source-register, Chair R2 digest, missing-agent primary disclosure and R1–R3 saved-example traceability regressions passed. |
| Frontend unit/build checks | VERIFIED | Exact-head Frontend Build [44303234944](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234944): succeeded. |
| Patient Registry / four-round Dashboard browser E2E | VERIFIED | Exact-head Browser E2E [44303235009](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303235009): passed patient registry, Mission Control, Development Monitor and four-round dashboard checks in headless Edge. No model inference was invoked. |
| R2/R3 provenance warnings and source-opinion visibility in role detail cards | VERIFIED | Frontend commit `afbe6af6ffbc463ad92457e5179545c92b55b398` renders saved `source_reference_integrity_flags`, server-bound R2 `source_opinion_responses`, and R3 `source_opinion_reviews` beside each original role response. The disposable fixture correction `1c8a22b` embeds the exact source excerpt in `case_summary`; browser assertions passed in exact-head run [44289875520](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875520). Visibility only; live model correctness and semantic interpretation remain unverified. |
| Mission Control / Development Monitor dashboard | VERIFIED | Exact audit-v16 code-head Browser E2E [44267217873](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217873) passed; prior dedicated refresh/error-resilience coverage remains in run 44257129743. |
| Dashboard/API error and last-good-state handling | VERIFIED | Prior browser checks cover 403/429, malformed metadata, recovery and valid empty state. |
| Ollama context handling and truncation resistance | IN PROGRESS | Long-run effective context behaviour has not been proven fixed. |
| Ollama performance and concurrency | IN PROGRESS | Concurrency remains 1; comparable local RTX 4060 timing evidence incomplete. |
| RTX 4060 request-time GPU inference | NOT STARTED | No current local request-time `nvidia-smi` and Ollama offload evidence. |
| Hosted v9–v15 model screens | FAILED | Historical bounded runs retain integrity failures; failures are preserved. |
| v16/audit-v15 code/schema/audit regression suite | FAILED | The 12-case v16 screen exposed three additional manual findings not caught by audit-v15: R1 diagnosis-field contradiction, R1 contradiction-display omission and R3 synthetic_input echo. Existing schema/fixture tests passed, but audit coverage is incomplete. |
| v16/audit-v16 deterministic false-negative checks and regression tests | VERIFIED | Audit version `radonc-mdt-integrity-audit-v16` is enforced by the workflow gate. New tests cover R1 denial of supplied diagnosis field, R1 omission of opposing laterality sources and R3 synthetic_input JSON echo. Exact backend run [44267217866](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217866) passed all three and 476/476 pytest rows. Deterministic checks only; no live Qwen audit-v16 screen. |
| v16/audit-v16 live model screen | BLOCKED | No live Qwen v16/audit-v16 run is authorised. The single temporary exception was consumed by run 44263369594 (which used audit-v15). New model inference requires a fresh explicit risk review, documented security disposition and renewed authorisation. |
| v16/audit-v15 live model screen | FAILED | Run [44263369594](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594) executed successfully, but the model integrity screen is not accepted: 12/12 outputs recorded, 4 cases automatically flagged / 6 review flags, plus 3 further manual observations. Summary: PENDING_HUMAN_REVIEW, automatic score null. Artifact [14409068927](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594/artifacts/14409068927). Execution success is not model pass. One-run exception consumed. |
| Qwen exact-version gate before MedGemma | VERIFIED | Workflow requires exact Qwen prompt/audit/script manifest checks before MedGemma pull. |
| Fresh full 45-role R1–R4 live validation | NOT STARTED | No current fresh full run accepted. |
| MedGemma HAI-DEF terms acceptance | VERIFIED | Prior explicit acceptance is recorded; this is not model validation. |
| MedGemma live evaluation | BLOCKED | Qwen-first sequence and security-gate disposition remain outstanding. |
| Independent blinded model-output review | NOT STARTED | No independent blinded review artefact; manifest remains PENDING_HUMAN_REVIEW. These deterministic/manual observations are not an independent review. |
| Guideline retrieval and verification | NOT STARTED | No current verified guideline source set linked to a run. |
| Independent qualified clinical review | NOT STARTED | No attributable qualified review artefact. |
| Windows packaging prerequisites | VERIFIED | Exact-head Packaging Prerequisites [44303234914](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234914) succeeded. |
| Windows installer build | VERIFIED | Exact-head installer [44303234950](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234950) succeeded. Installed health and silent uninstall/database preservation passed; installer SHA-256 `d0e3ab0c1b91874cf2f13450734746e70561abdff2d80ce5bfedd721b4f588a7`; artifact [14427096490](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234950/artifacts/14427096490). Clean-hosted Ollama/model bootstrap was SKIPPED; no model inference. |
| Full-history secret scan | VERIFIED | Exact-head Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880): passed. |
| Python CodeQL | VERIFIED | Exact-head Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880): passed. |
| JavaScript/TypeScript CodeQL | VERIFIED | Exact-head Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880): passed. |
| Python dependency audit | VERIFIED | Exact-head Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880): no known vulnerabilities found. |
| Node dependency audit | FAILED | Exact-head Security Audit [44303234880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44303234880): npm audit still reports four HIGH transitive `picomatch@4.0.7` findings. Python dependency audit, both CodeQL analyses and full-history secret scan passed. `npm audit fix --force` proposes a breaking Vite 7.3.8 → 6.2.7 downgrade; the GitHub advisory has no patched version listed. Do not force-downgrade, suppress or bypass the failure. |
| Dependency advisory applicability and risk disposition | IN PROGRESS | The one-run exception was consumed by Qwen run 44263369594. GitHub now marks GHSA-fc5q-39xc-vjpf Reviewed/High, affected through 4.0.7 with no patch listed; Snyk disputes this and has revoked its separate advisory. The repository's package graph shows picomatch only as a Vite transitive dev dependency; the checked Vite config does not define user-controlled glob input, but this is not proof of zero exploitability. npm audit remains FAILED and unsuppressed. No further model run or MedGemma evaluation is authorised before documented security-owner disposition and fresh explicit approval. |
| Release acceptance | BLOCKED | Temporary one-run development exception does not clear the Node audit. R2/R4 live failures, full 45-role run, GPU, evidence retrieval and independent clinical review remain outstanding. |

## Latest screen evidence — Qwen v16 / audit-v15, run 44263369594

**Workflow execution: SUCCESS. Model-integrity acceptance: FAILED / pending human review.**

- Run [44263369594](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594), trigger SHA 77d8969956cabaa9e83224180f954653b57039bb; artifact [14409068927](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594/artifacts/14409068927).
- ZIP SHA-256: 253f6c0066700ec7c0e0eeeabcd59305b796b472bce3ce3af60e6ca853068191. Model JSONL SHA-256: a6e1e2271414ed97839557b9d6cc212e750a533585c1aa0e742345b94fbaa4ea.
- Model run ID: 127be66d-7a19-41b3-a8db-23acf4281a32. Prompt radonc-mdt-integrity-screen-v16. Audit radonc-mdt-integrity-audit-v15. Script SHA-256: 7c25fdc46cecc1e4c3f14665fe6dc1ae9700b78b1e77db7fc3e34dd631729282.
- Model qwen3.5:4b; Ollama 0.40.14; model digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04.
- Hosted Windows CPU-only, concurrency 1; GPU measurement NOT_PERFORMED. MedGemma SKIPPED_NOT_REQUESTED.
- Summary: 12 expected, 12 responses, 0 malformed/failed, 4 cases flagged, 6 deterministic review flags, acceptance PENDING_HUMAN_REVIEW, automatic_quality_score null, clinical_accuracy_evaluated false.

Automatically flagged cases (6 flags): R2-PARTIAL-AGREEMENT-006 (narrative omitted source attribution for limited information agreement); R2-CONDITIONALITY-007 (conditional Option A/prerequisite X/unknown status omitted from narrative); R4-MISSING-AGENT-011 (required coverage details absent from main Chair response); R4-CHAIR-TRACEABILITY-012 (Chair synthesis and unresolved source omitted).

Additional manual audit observations not caught by audit-v15: R1-UNKNOWN-STAGE-001 denied that a supplied non-empty diagnosis field existed (TNM/stage remained unknown); R1-CONTRADICTION-003 did not display both opposing laterality source statements or flag the discrepancy; R3-INVALID-SOURCE-008 echoed JSON containing case_id and synthetic_input despite the instruction not to repeat the input. These are three manual observations, not additional deterministic flags or independent blinded review.

Positive controls: R2-FALSE-CONSENSUS-005 kept separate conditional options distinct; R3-FABRICATED-QUOTE-009 rejected the unsupplied MRI quote. This corpus is a synthetic software-integrity screen, not clinical cases or gold-standard oncology answers.

Follow-up: add narrow regressions for the three audit false negatives and strengthen R2/R4 narrative checks. No further model screen is authorised without fresh risk review and security clearance.
## Latest PR-head CI — PR head `e75616a3c24fa330e9fbc624340b64862afc6fce` (18 November 2026)

All six standard PR workflows completed on this exact head: five succeeded and the security/dependency workflow failed.

- Backend Tests [44263477537](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263477537): SUCCESS; raw job-log recount **473/473 pytest rows passed**, 0 failed, 0 errors and 0 skips. The cross-round minority-history regression is included and passed. JUnit artifact [14409715687](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263477537/artifacts/14409715687); preflight artifact [14409785131](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263477537/artifacts/14409785131).
- Frontend Build [44263476256](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263476256): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44263476208](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263476208): SUCCESS.
- Windows Packaging Prerequisites [44263476167](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263476167): SUCCESS.
- Windows Installer Build [44263476238](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263476238): SUCCESS; install/smoke test and checksum/upload steps completed. The separate clean-hosted Ollama/model bootstrap job was SKIPPED, so this is not live inference evidence.
- Security and Dependency Audit [44263476344](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263476344): FAILED. Python dependency audit reported no known vulnerabilities; Python and JavaScript/TypeScript CodeQL passed; full-history secret scan passed. Node npm audit failed with four HIGH picomatch@4.0.7 findings. The later checklist-only descendant has the same failure, recorded below.

This PR-head CI is software/build verification only. It does not prove model quality, clinical safety, guideline compliance, GPU inference or release readiness.

## Latest verification after checklist commit bfc06d3e94d8a9e7bceca73302e0ab1a6e196208

All six PR workflows on this exact checklist commit completed. Five succeeded; dependency/security failed:

- Backend [44264563350](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563350): SUCCESS, 473/473 pytest rows passed, zero failures/errors/skips; cross-round minority-history regression passed.
- Frontend [44264563043](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563043): SUCCESS.
- Browser E2E [44264563027](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563027): SUCCESS.
- Windows packaging prerequisites [44264563105](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563105): SUCCESS.
- Windows installer [44264563119](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563119): SUCCESS.
- Security/dependency audit [44264563041](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44264563041): FAILED at Node npm audit with four HIGH picomatch findings. Python dependency audit, Python and JS/TS CodeQL, and full-history secret scan passed.

These results are software/build verification only. They do not prove model integrity, clinical validity, GPU inference or release readiness.
## Latest exact PR-head CI — source-bound provenance fixture head `1c8a22b435e047f6524b9172ae3663d40a9d127c` (18 November 2026)

All six standard PR workflows completed on this exact head: five succeeded and Security/Dependency Audit failed.

- Backend [44289875570](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875570): SUCCESS; raw job logs confirm **476/476 pytest records passed**, zero failed/errors/skips.
- Frontend Build [44289875433](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875433): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44289875520](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875520): SUCCESS. It exercised the updated fixture whose exact R2 source excerpt is contained in the saved `case_summary`; assertions verified R2 provenance warning display, server-bound R2 attributed opinion display, and R3 option/condition review display. It also verified the saved 45-role round panels and Chair R4 report; no model inference.
- Windows Packaging Prerequisites [44289875422](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875422): SUCCESS.
- Windows Installer [44289875406](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875406): SUCCESS. Install/health/frontend/API 45-role smoke tests passed; silent uninstall preserved the user database. Artifact [14420343814](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289875406/artifacts/14420343814); installer SHA-256 `66c5d0418581ede3249b9b8eca0bf8098eb97371a940f14473964174fc31d20e`.
- Security and Dependency Audit [44289876314](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44289876314): FAILED at Node npm audit with four HIGH `picomatch@4.0.7` findings. Python audit, both CodeQL analyses, and full-history secret scan passed.

These checks verify build, packaging, and UI display only. The separate Ollama/model bootstrap job was skipped. The model's R2/R4 semantic performance, GPU inference, clinical accuracy, and guideline concordance remain unverified.
## Latest exact PR-head CI — provenance visibility UI change and browser fixture corrections, head `1e8d3559dc12e7aa1b7599f9bd076b3873f4e88b` (18 November 2026)

PR #1 remains open, draft and unmerged; base `main` remains `39a356b8eb09399aa2da1b9b9085965999f5105a`. All six standard PR workflows completed on this exact head: five succeeded, one failed.

- Backend Tests [44286353780](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353780): SUCCESS; raw job-log recount **476/476 pytest records passed**, zero failures, errors or skips. JUnit artifact 14418608884.
- Frontend Build [44286353769](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353769): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44286353782](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353782): SUCCESS. Headless Edge verified the new R2 source/provenance warning, exact server-bound R2 attributed-opinion excerpt/analysis, and R3 source-opinion option/conditions status in role detail cards. The same test retained the 45-role R2/R3 and Chair R4 rendering checks, and deleted the disposable patient fixture. No model inference was invoked.
- Windows Packaging Prerequisites [44286353756](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353756): SUCCESS.
- Windows Installer Build [44286353783](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353783): SUCCESS.
- Security and Dependency Audit [44286353760](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44286353760): FAILED at Node npm audit with four HIGH `picomatch@4.0.7` findings. Python dependency audit, Python/JavaScript CodeQL and full-history secret scan passed.

The browser regression proves that persisted structured warnings and source opinion records are visible to reviewers; it does not prove model responses are accurate, complete or clinically valid. No Qwen or MedGemma screening ran on this change.
## Latest exact PR-head CI — checklist/security reassessment commit `96b5612cacd676f8c8cdd774f7cf586c342f38bd` (18 November 2026)

All six standard PR workflows completed on this exact head. Five succeeded; Security and Dependency Audit failed. This was a documentation-only update; the application and regression-test code remain unchanged from audit-v16 commit `c1fb981`.

- Backend [44282879298](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282879298): SUCCESS; raw job logs confirm **476/476 pytest records passed**, 0 failed, 0 errors or skips. All three audit-v16 false-negative regressions passed.
- Frontend Build [44282879191](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282879191): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44282885742](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282885742): SUCCESS.
- Windows Packaging Prerequisites [44282879329](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282879329): SUCCESS.
- Windows Installer [44282879123](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282879123): SUCCESS.
- Security and Dependency Audit [44282879209](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44282879209): FAILED at Node npm audit with four HIGH picomatch findings. Python dependency audit, both CodeQL analyses and full-history secret scan passed.

No model-screen workflow ran on this documentation-only commit. These CI results do not establish audit-v16 model behaviour, local GPU use, clinical accuracy or guideline concordance.
## Latest exact PR-head CI — documentation-only head `b59c52d49e888473d751a600a126bfaeb3e17f5b` (18 November 2026)

This head changes only `docs/MASTER_DEVELOPMENT_CHECKLIST.md`; application code and tests are unchanged from audit-v16 regression commit `c1fb981`. All six standard PR workflows completed: five passed and Security/Dependency Audit failed.

- Backend [44268129179](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129179): SUCCESS; raw job-log recount **476/476 pytest records passed**, 0 failed, 0 errors or skips. The three new audit-v16 regressions are explicitly present and passed.
- Frontend Build [44268129231](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129231): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44268129197](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129197): SUCCESS.
- Windows Packaging Prerequisites [44268129383](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129383): SUCCESS.
- Windows Installer [44268129155](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129155): SUCCESS.
- Security/Dependency Audit [44268129380](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44268129380): FAILED at Node npm audit with four HIGH picomatch findings. Python dependency audit, both CodeQL analyses and full-history secret scan passed.

This confirms the exact current branch head. It does not constitute a live model, GPU, clinical or release validation.
## Latest exact-code-head CI — audit-v16 remediation commit `c1fb981e648b76429bc29403cd2febcf5e4739d0`

Five standard PR workflows succeeded; Security and Dependency Audit failed:

- Backend [44267217866](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217866): SUCCESS; 476/476 raw pytest rows passed, zero failures/errors/skips. All three audit-v16 false-negative regressions and the 12-case deterministic harness passed. JUnit artifact [14409834554](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217866/artifacts/14409834554); deterministic preflight artifact [14410892064](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217866/artifacts/14410892064).
- Frontend Build [44267218284](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267218284): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44267217873](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217873): SUCCESS; artifact [14411570079](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217873/artifacts/14411570079).
- Windows Packaging Prerequisites [44267217819](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217819): SUCCESS.
- Windows Installer Build [44267218391](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267218391): SUCCESS; artifact [14409849910](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267218391/artifacts/14409849910), SHA-256 `286acdfb8230fdac2ba0a8522dffbb107c3dc806bdd75d6abe97573655bb4fe3`. This is installer smoke verification, not model inference.
- Security and Dependency Audit [44267217685](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267217685): FAILED at Node npm audit with four HIGH `picomatch@4.0.7` findings. Python audit, Python and JS/TS CodeQL and full-history secret scan passed.

Push-triggered Synthetic Model Integrity Screening [44267204599](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44267204599) (run #82) was SKIPPED because the code commit message had no `[model-integrity-screen]` marker. No model inference occurred. Audit-v16 is software-tested, not live-model-tested.

Audit-v16 commits: `77dcf81e14565cb43f89e63bb83e80caa0aa0d1b` (new audit/tests/workflow gate), `2e46a1bd781c6a5e0e8f5ca2230d36e9cf5cb749` (corrected regex escaping), `c1fb981e648b76429bc29403cd2febcf5e4739d0` (corrected passing fixture; current code head).

## Temporary development-only risk acceptance — 18 November 2026

The project owner replied “Ok” to the explicit request for a temporary, documented exception for the disputed development-only transitive `picomatch` advisory. Scope was limited to **one** bounded Qwen v16/audit-v15 synthetic screening run on the isolated GitHub-hosted CPU runner at concurrency 1. Run 44263369594 is complete; the exception is consumed and does not provide continuing authority.

- The automated npm audit remains failed and visible; no suppression, allowlist, lockfile modification, or claim of a passed security audit is permitted.
- MedGemma is excluded. The workflow commit message contains `[model-integrity-screen]` only and does not contain the `[medgemma]` or `[hai-def-terms-accepted]` trigger markers.
- This does not authorise production deployment, release, clinical use, GPU claims, additional model runs, or general acceptance of the dependency risk.
- Reassess the advisory immediately after this single run. A further run requires a fresh explicit risk review.
- Workflow trigger commit: `77d8969956cabaa9e83224180f954653b57039bb`. Run [44263369594](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594) (#79) completed successfully and uploaded artifact [14409068927](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44263369594/artifacts/14409068927). Qwen produced 12/12 outputs with exact model digest. MedGemma was not requested. Model-integrity screen did not pass; detailed findings are recorded above.

## Latest exact-head CI — regression-test commit `a8863f9caa28479599d9b9f10722d2afafa29bb0`

All six standard PR workflows completed. Five succeeded; the security workflow failed solely because the Node dependency audit failed.

- Backend Tests [44262841444](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841444): SUCCESS; raw job-log recount confirms 473 pytest rows passed, 0 failed, 0 errors or skips. The cross-round minority-history test is explicitly present and passed. The previous 480-row figure was incorrect and is superseded by this recount. Diagnostics artifact [14409301267](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841444/artifacts/14409301267).
- Frontend Build [44262841436](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841436): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44262841821](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841821): SUCCESS; registry, Mission Control, Development Monitor and four-round dashboard checks passed. Artifact [14409580293](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841821/artifacts/14409580293).
- Windows Packaging Prerequisites [44262841556](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841556): SUCCESS.
- Windows Installer Build [44262841453](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841453): SUCCESS; install/uninstall smoke test passed. Artifact [14408632519](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841453/artifacts/14408632519); installer SHA256 `d245f20ef146898e09b3f6de873c5a44412a90c1ef033eb573199df812e85bf3`. AI bootstrap paths used mocked Ollama/model endpoints; no real Ollama request or model inference occurred.
- Security / Dependency / CodeQL [44262841543](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44262841543): FAILED. Python dependency audit found no known vulnerabilities; Python CodeQL, JavaScript/TypeScript CodeQL and full-history secret scan passed. Node `npm audit --audit-level=high` again failed on four HIGH `picomatch` findings. This confirms the security blocker persists on the exact regression-test commit.

This commit changes tests only; no production application code was changed. The CI results do not establish live model behaviour, local GPU use, clinical accuracy or guideline concordance.

## Exact-head CI evidence — PR head `07e0abafc3baedf16d588eaf9e50eed3dc812dc7`

The application/test tree was unchanged from `8cde5dd`; the two commits between those SHAs changed only this checklist. All six standard PR workflows completed: five succeeded and the security workflow failed.

- Backend Tests [44261206592](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206592): SUCCESS; 479 recorded passing pytest rows, 0 failed; diagnostics artifact [14408530437](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206592/artifacts/14408530437).
- Frontend Build [44261206517](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206517): SUCCESS.
- Patient Registry / Four-Round Dashboard Browser E2E [44261206525](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206525): SUCCESS.
- Windows Packaging Prerequisites [44261206570](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206570): SUCCESS.
- Windows Installer Build [44261206474](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206474): SUCCESS; hosted Ollama/model bootstrap not established.
- Security / Dependency / CodeQL [44261206545](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44261206545): FAILED because Node `npm audit --audit-level=high` returned four HIGH `picomatch` findings. Python audit, both CodeQL analyses and full-history secret scan passed.

The screenshot's job ID `134652860736` is from backend workflow 44260641959. Its logs show successful pytest diagnostics/preflight artifact uploads and completion. It was not a live inference job.

## Dependency security investigation — 18 November 2026

**Repository lockfile evidence:** `frontend/package-lock.json` resolves `picomatch@4.0.7` as a development dependency; it is reached through `tinyglobby@0.2.17` and `fdir@6.5.0`. It is not listed as a direct application runtime dependency in `frontend/package.json`.

**Current dependency-path check on the development branch:** `frontend/package.json` lists only React and React DOM as direct application dependencies; Vite 7.3.8 and the React Vite plugin are in `devDependencies`. The lockfile marks Vite, `tinyglobby@0.2.17`, `fdir@6.5.0` and `picomatch@4.0.7` as development dependencies. Vite reaches picomatch through its `tinyglobby`/`fdir` dependency graph. The inspected `vite.config.ts` configures the React plugin and loopback API/health proxies; it contains no user-controlled glob patterns. This narrows the observed use to build/development tooling, but does not prove the vulnerable code path is unreachable in every build/development execution and does not satisfy the repository's full-lockfile audit.

**External evidence reviewed:**
- GitHub Advisory Database: GHSA-fc5q-39xc-vjpf is now marked **GitHub Reviewed** (updated 17 November 2026), severity High (CVSS v4 8.7), affected versions `<=4.0.7`, with **no patched versions listed**. Its description identifies a possible ReDoS through single-branch repeated extglob patterns. [Advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
- NVD: CVE-2026-112366 remains **Awaiting Enrichment**; NVD has not supplied its own assessment, while the displayed CNA assessment from VulnCheck is CVSS v4 8.7 High. [NVD record](https://nvd.nist.gov/vuln/detail/CVE-2026-112366)
- Snyk states that its advisory was revoked and amended as “not a vulnerability”, citing the maintainer dispute and advising against patterns/untrusted user-defined glob input. This conflicts with the reviewed GitHub Advisory; it does not clear npm audit. [Snyk amendment](https://security.snyk.io/vuln/SNYK-JS-PICOMATCH-21248802)
- Upstream picomatch PR #235, proposing a mitigation, was closed; the maintainer disputed the report and stated a position that applications should not allow untrusted users to define glob patterns. [Upstream PR #235](https://github.com/micromatch/picomatch/pull/235)
- The npm registry and official release list still show `4.0.7` as latest; no patched release above the affected range was verified. [npm versions](https://www.npmjs.com/package/picomatch?activeTab=versions) · [official releases](https://github.com/micromatch/picomatch/releases)
- Upstream picomatch PR [#194](https://github.com/micromatch/picomatch/pull/194) remains OPEN and UNMERGED. It is a parser-behaviour change, not a released security fix; its own description explicitly says `+(*a)` remains exponential (~53 seconds on the stated input) and is out of scope. Do not treat this PR as remediation.

**Disposition (reassessed 18 November 2026):** the finding is no longer labelled unreviewed: GitHub marks it reviewed/high and identifies `<=4.0.7` as affected, with no patch listed. Snyk has revoked its separate advisory as not a vulnerability, and the upstream PR it references is still unmerged and does not fix the reported `+(*a)` behaviour. The transitive package remains in the frontend development/build dependency tree rather than being a direct runtime dependency, but the full-lockfile npm audit fails. Exposure in this application's own execution path has not been proven; neither has exploitability in the deployed app. Keep the automated security gate FAILED and unsuppressed. Do not omit development dependencies, force a breaking downgrade, install an unmerged fork, or claim the advisory is fixed. Require an auditable security-owner disposition and a verified official remediation or formal advisory withdrawal before clearing the gate.

## Next controlled actions

1. Obtain an auditable security-owner disposition for the conflicting reviewed GitHub advisory and Snyk revocation. Keep npm audit FAILED and visible until an official fix or formal withdrawal/clarification is verified.
2. The single authorised Qwen v16 run has completed and its exception is consumed. Do not start another Qwen screen or any MedGemma live inference while the security gate remains unresolved. Any future model run requires a fresh explicit risk review and documented security disposition.
3. Continue deterministic R2/R4 Chair and consensus work against exact saved failures. Audit-v16 covers three additional false negatives and passed software CI, but has no live-model validation. Preserve source identity, conditions, dissent and minority histories.
4. After the security gate is resolved, rerun all CI on the exact new application commit, then perform bounded Qwen live corrective validation at concurrency 1.
5. Only after bounded corrective acceptance, plan the fresh full 45-role R1–R4 run and inspect all saved round records, Chair traceability and audit hashes.
6. Separately verify local RTX 4060 request-time inference with `nvidia-smi`, Ollama offload details, request-time activity and latency.
7. Retrieve and verify current authoritative guidelines; arrange independent blinded output review and qualified clinical review.
8. Keep release acceptance BLOCKED until all required software, security, model, provenance, GPU, evidence and clinical-review gates have explicit evidence.

---

## Historical implementation checkpoint — specialist identity gate (18 November 2026; evidence retained)

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Development branch:** `feature/four-round-mdt-and-performance`  
**Latest application/test commit:** `8cde5dd847d1c656e195ac9239f39fb75b51691f` (the latest verified PR head recorded below, `ef40def`, is a checklist-only descendant; this checklist refresh follows it).  
**Application guard commit:** `47dfa9d7576d545b5d1acc574f9597c4bc7bd3fc`  
**Regression expectation correction:** `8cde5dd847d1c656e195ac9239f39fb75b51691f`  
**PR #1:** open, draft, unmerged; base `main`.  
**`main`:** `39a356b8eb09399aa2da1b9b9085965999f5105a`; unchanged.

### Change implemented

- Added `_require_exact_completed_role_payloads` in `backend/app/services/mdt_rounds.py`.
- The guard is applied to saved R1 records before R2, saved R2 records before R3, and saved R3 records before Chair R4.
- It requires one and only one completed, structured contribution from every expected specialist ID. It fails closed on missing IDs, duplicate completed rows, unexpected IDs, unidentified completed records or a malformed payload.
- The guard only checks saved-row identity and payload structure. It does not synthesize missing contributions, alter clinical text or replace the actual saved inputs.
- Regression test `test_round_input_gate_requires_exactly_one_structured_record_per_expected_specialist` covers a valid 45-role set and duplicate, missing, unexpected and malformed cases.
- The first attempt at commit `47dfa9d` failed one new assertion because the test hard-coded `RO-45`; the actual last catalog role is `SV-03`. The guard correctly reported `SV-03` as missing. The test now derives the expected missing ID from `AGENT_PROFILES`. The initial failed run is preserved below; it is not counted as passing.

### Exact-head CI — `8cde5dd847d1c656e195ac9239f39fb75b51691f`

All six PR workflows completed:
- Backend Tests [44259969900](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969900): SUCCESS; **472/472 recorded pytest cases passed**, zero failed and zero errors. Deterministic preflight artifact [14407034056](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969900/artifacts/14407034056).
- Frontend Build [44259969941](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969941): SUCCESS.
- Patient Registry and Four-Round Dashboard Browser E2E [44259969935](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969935): SUCCESS.
- Windows Packaging Prerequisites [44259969894](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969894): SUCCESS.
- Windows Installer Build [44259969919](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969919): SUCCESS. Clean-hosted first-run Ollama/model bootstrap: SKIPPED.
- Security and Dependency Audit [44259969880](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259969880): WORKFLOW FAILED. Python dependency audit found no known vulnerabilities; Python CodeQL, JavaScript/TypeScript CodeQL and full-history secret scan passed. Node audit failed with four high-severity `picomatch` findings (GHSA-fc5q-39xc-vjpf / CVE-2026-112366).

The preceding application/test attempt `47dfa9d7576d545b5d1acc574f9597c4bc7bd3fc` had Backend Tests run [44259683869](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44259683869) fail solely because of the incorrect hard-coded role ID in the new regression assertion. The correction on `8cde5dd` passed the backend suite. The earlier failure remains recorded and was not rewritten.

### Checklist-only descendant verification — `ef40defe38c5e6f3db299b660f6f40d7a952fa94`

This commit changed only `docs/MASTER_DEVELOPMENT_CHECKLIST.md`; the application/test tree remained the same as `8cde5dd`. Its six PR workflows completed:
- Backend [44260641959](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641959): SUCCESS; 472/472 pytest records passed; preflight artifact [14407942037](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641959/artifacts/14407942037).
- Frontend [44260641958](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641958): SUCCESS.
- Browser E2E [44260641988](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641988): SUCCESS.
- Packaging prerequisites [44260641942](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641942): SUCCESS.
- Windows installer [44260641950](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641950): SUCCESS; clean-hosted first-run Ollama/model bootstrap SKIPPED.
- Security audit [44260641962](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44260641962): FAILED at Node `npm audit` with the same four high picomatch findings. Python dependency audit, Python/JavaScript CodeQL and full-history secret scan passed.

### Dependency security disposition

- The current advisory still describes the ReDoS issue through `picomatch 4.0.7`; the GitHub Advisory page has no affected or patched version range specified. [GitHub Advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
- npm lists `4.0.7` as the current latest version, and the official picomatch release page lists `4.0.7` as latest. No official patched npm release was verified. [npm package versions](https://www.npmjs.com/package/picomatch) · [official releases](https://github.com/micromatch/picomatch/releases)
- The dependency is in the Vite/fdir/tinyglobby development/build-tool tree. This reduces direct shipped-runtime exposure, but does not satisfy the required full dependency audit.
- Do not suppress the finding, exclude development dependencies from the required audit, install an unmerged fork, apply an unreviewed override or force a breaking Vite downgrade.
- Keep the v16/audit-v15 model screen and MedGemma live evaluation BLOCKED until the security gate is resolved.

The status table and next-action list in this historical checkpoint have been superseded by the single current checklist at the top of this file. Implementation details and exact-head CI evidence above are retained.

## Historical checkpoint — Development Monitor acceptance and CI (18 November 2026; superseded by 8cde5dd)

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Development branch:** `feature/four-round-mdt-and-performance`  
**Latest application/test commit:** `e3dbc3b60a3f2f8c369c31ecf1ba51c7055e9712` (later commits in this sequence update only the checklist).  
**PR #1:** open, draft, unmerged; base `main`.  
**`main`:** `39a356b8eb09399aa2da1b9b9085965999f5105a`; unchanged.

### Development Monitor implementation and regression coverage

- Application commit `860703eafe9a39450820fdf8598aa5e5d6e5d3e0` now validates GitHub Actions API `total_count` and `workflow_runs` consistency. It rejects missing/inconsistent counts, non-empty counts with no records, and non-empty results containing no usable workflow records. Invalid responses leave the last successfully retrieved snapshot untouched and display an error. A genuine zero-count/empty-list response remains a valid empty state.
- Browser regression commit `df55558b2b4b835bfee191ef52be32bfc51fead8` extended the existing isolated headless Edge workflow with deterministic GitHub API fixtures: duplicate runs for the same workflow, an earlier-commit run, HTTP 403/429, inconsistent/invalid metadata, recovery and a legitimate empty state.
- The first attempt on `df55558` failed because the test's generic button helper could select a different page-level “Refresh” button. This was a test-selector defect; the browser run stopped before the rate-limit assertion. Commit `e3dbc3b` scopes the click to the Development Monitor panel. The corrected exact-head browser E2E passed.
- Exact-head browser run [44257129743](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129743) emitted `DEVELOPMENT_MONITOR_BROWSER_E2E_OK`. It verified newest-run-per-workflow selection, current-HEAD matching, 403/429 handling, last-good snapshot retention, malformed/incomplete metadata rejection, recovery and valid empty-state rendering. It also passed the existing Patient Registry, Mission Control role drill-down and four-round saved-dashboard checks. This is UI/software verification, not model or clinical validation.

### Exact-head CI — `e3dbc3b60a3f2f8c369c31ecf1ba51c7055e9712`

All six standard PR workflows completed:
- Backend Tests [44257129798](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129798): **471 passed, 0 failed, 0 errors, 0 skipped, 0 inconclusive**; deterministic preflight **7/7 passed**. Preflight artifact [14406780194](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129798/artifacts/14406780194).
- Frontend Build [44257129844](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129844): SUCCESS.
- Patient Registry and Four-Round Dashboard Browser E2E [44257129743](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129743): SUCCESS; see Development Monitor coverage above.
- Windows Packaging Prerequisites [44257129933](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129933): SUCCESS.
- Windows Installer Build [44257129757](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129757): SUCCESS. The separate clean-hosted first-run Ollama/model bootstrap job was SKIPPED; no model inference was performed by this workflow.
- Security and Dependency Audit [44257129843](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129843): WORKFLOW FAILED. Python dependency audit reported no known vulnerabilities; Python CodeQL, JavaScript/TypeScript CodeQL and full-history secret scan all passed. Node `npm audit --audit-level=high` failed with **four high-severity picomatch findings** through the Vite/fdir/tinyglobby dependency tree. Dependency audit job [134641397382](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257129843) is the failing job. No forced downgrade, unmerged fork, override or audit suppression was applied.

### Confirmed repeat CI after the checklist refresh — docs-only commit a16a923

The checklist-only commit `a16a92301f5e513d123027275705c4700f75c224` left the application/test tree unchanged from `e3dbc3b`. All six PR workflows associated with `a16a923` have since completed:
- Backend [44257698125](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698125): SUCCESS; 471/471 tests, preflight 7/7; artifacts [14406706313](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698125/artifacts/14406706313) (preflight) and [14406308611](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698125/artifacts/14406308611) (JUnit diagnostics).
- Frontend [44257698093](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698093): SUCCESS.
- Browser E2E [44257698053](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698053): SUCCESS; all five browser acceptance markers emitted, including `DEVELOPMENT_MONITOR_BROWSER_E2E_OK`.
- Packaging prerequisites [44257698026](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698026): SUCCESS.
- Windows installer [44257697944](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257697944): SUCCESS; optional clean-hosted first-run Ollama/model bootstrap SKIPPED.
- Security [44257698007](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44257698007): WORKFLOW FAILED solely at the Node dependency audit; Python dependency audit, both CodeQL jobs and full-history secret scan passed.
- This repeat run confirms the same software tree, but the dependency-security failure remains unchanged. No live model inference was performed.

### Dependency-security disposition — still a release blocker

- The latest exact-head audit still reports `picomatch 4.0.7`, GHSA-fc5q-39xc-vjpf / CVE-2026-112366, as HIGH. The package is in the frontend build-tool dependency tree and marked dev-only in the lockfile; that narrows direct runtime exposure but does not satisfy the required full dependency audit.
- Newly opened upstream picomatch PR [#269](https://github.com/micromatch/picomatch/pull/269) was checked on 18 November: it remains OPEN and UNMERGED, is from a contributor fork, has no GitHub check-runs and no maintainer review at the inspected head. Its own description says it does not change a package version and does not claim an official npm release. It is a proposal, not a usable released remediation.
- The GitHub Advisory remains published HIGH with affected/patched package versions unspecified on its page; do not state it has been formally withdrawn or fixed. Keep dependency audit FAILED until an official advisory clarification/withdrawal or an official released, verified fix resolves the complete audit.
- Do not install PR #269's fork, use an unreviewed override, ignore dev dependencies, suppress the finding, or downgrade Vite with `npm audit fix --force`.

### Current validation boundary

- The exact-head software CI above does not establish clinical correctness, model behavior, guideline compliance, RTX 4060 GPU inference, or release readiness.
- Latest completed model-screen run remains [44113146755](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44113146755): FAILED (prompt v15/audit-v14), immutable artifact [14343725249](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44113146755/artifacts/14343725249). The v16/audit-v15 live screen remains BLOCKED by the failed dependency-security gate; do not trigger it while the gate remains failed.
- Latest environment evidence remains hosted Windows CPU, concurrency 1. RTX 4060 request-time GPU telemetry: NOT PERFORMED. Clinical accuracy: NOT EVALUATED. Guideline retrieval and independent qualified clinical review remain outstanding.

This is a superseded status snapshot. The authoritative current checklist is the new section at the top of this file.

## Latest exact-head CI — ffac5043b7bc986996ba9f4ae20c852e1ca38d9f

All six PR workflows associated with this exact documentation-only commit have completed:
- Backend run 44142134948: SUCCESS; 471/471 tests passed, deterministic preflight 7/7, diagnostic errors 0.
- Frontend build run 44142134991: SUCCESS.
- Patient registry and saved MDT dashboard browser E2E run 44142134881: SUCCESS; isolated real-browser acceptance completed.
- Windows packaging prerequisites run 44142134831: SUCCESS.
- Windows installer run 44142134823: SUCCESS; installer build, install/smoke test, checksum and artifact upload all passed. Clean-hosted first-run Ollama/model bootstrap job: SKIPPED.
- Security/dependency run 44142134877: WORKFLOW FAILED because the frontend lockfile audit step failed. Python dependency audit: SUCCESS; full-history secret scan: SUCCESS; Python CodeQL: SUCCESS; JavaScript/TypeScript CodeQL: SUCCESS.
- Overall: five workflows SUCCESS, one workflow FAILED. The security failure remains a release gate. This is software/build verification only, not model acceptance, GPU verification, clinical validation or release approval.
- PR #1 remains open/draft/unmerged; development branch head is ffac5043b7bc986996ba9f4ae20c852e1ca38d9f; main remains 39a356b8eb09399aa2da1b9b9085965999f5105a and was not modified.


## Verification refresh — 18 November 2026 (checklist commit dc0ab4eb5766cefb9d529efe1b83c5ad7b3a9214)

Exact-tip PR workflows associated with the preceding checklist commit dc0ab4eb5766cefb9d529efe1b83c5ad7b3a9214:
- Backend run 44255058599: SUCCESS; deterministic preflight, compilation and pytest job completed successfully. Do not state an exact test count without checking its job log.
- Frontend build run 44255058617: SUCCESS.
- Patient registry/four-round dashboard browser E2E run 44255058600: SUCCESS. This does not demonstrate dedicated Development Monitor browser tests.
- Windows packaging prerequisites run 44255058601: SUCCESS.
- Windows installer run 44255058612: SUCCESS; clean-hosted Ollama/model bootstrap not independently confirmed.
- Security/dependency audit run 44255058618: FAILED. Python dependency audit SUCCESS; Node npm audit FAILED with four high picomatch findings via fdir/tinyglobby/Vite. npm audit fix --force proposes a breaking Vite 6.2.7 downgrade; not applied.
- Full-history secret scan, Python CodeQL and JavaScript/TypeScript CodeQL jobs in prior exact-tip security run 44145921274 all SUCCESS.
- Overall: five standard workflows SUCCESS, security/dependency workflow FAILED. Security disposition unchanged.
- The subsequent checklist-only update is not yet CI-associated; these run IDs refer to dc0ab4e, not the new documentation commit.

### Status corrections
Backend tests, frontend build, patient registry/dashboard browser E2E, packaging prerequisites, installer build/smoke, full-history secret scan and both CodeQL analyses are VERIFIED on exact tip dc0ab4eb5766cefb9d529efe1b83c5ad7b3a9214. Dependency audit remains FAILED. Development Monitor dedicated browser acceptance remains IN PROGRESS. Model screen remains held; GPU and clinical validation remain NOT STARTED / NOT EVALUATED.

## Dependency-security investigation — CVE-2026-112366

- Resolved frontend lockfile has one picomatch 4.0.7 occurrence, marked dev=true. It is reached through fdir and tinyglobby, which are used by Vite 7.3.8. The finding is in the build-tool dependency tree, not the declared React runtime dependencies. Full dependency audit still remains a required security gate and is FAILED.
- npm audit --force proposes downgrading Vite to 6.2.7, a breaking downgrade from 7.3.8; not applied.
- GitHub Advisory GHSA-fc5q-39xc-vjpf remains published and HIGH (CVSS 8.7). Its current public advisory page displays affected versions UNKNOWN and patched versions UNKNOWN (no package listed); do not attribute an explicit range to the GHSA page. The linked NVD/CNA record separately lists picomatch <=4.0.7 as affected and has no fixed version. NVD enrichment remains pending. This uncertainty is not a withdrawal or remediation.
- Upstream picomatch PR #237 (head 1bf0d04563cb9ce568cf36efc5f6b7187d9911d5) and PR #238 (head 44f192261f312ddf236cb7bdc05d8f22663f98f9) remain OPEN and UNMERGED. PR #238 was updated 17 Nov 2026 and proposes a narrow leading-bare-quantifier guard; its author explicitly documents an uncovered nested-extglob shape (+(*(ab)c)). The PR reports its own 2,000-test result, but the inspected head has zero GitHub check-runs and no maintainer approval. PR #237 likewise remains unmerged and has no verified release/check-run acceptance. PR #246 targets the v2 branch (picomatch 2.x), not the v4 dependency used by this project. These are proposals, not released packages.
- Important conflicting evidence: upstream PR #235, which proposed a broader CVE fix, is CLOSED without merge. The picomatch maintainer commented that they consider the reported pattern not a vulnerability and advised not using such patterns or allowing untrusted users to define regex/glob patterns. PR #238's author explicitly referenced that maintainer objection. This is a maintainer dispute, not a formal withdrawal of the GitHub Advisory. Issues #239 and #247 remain OPEN without a maintainer response in the inspected comments. Issue #247 points to #246 and #238; #246 is a v2-only proposal. The #247 author of PR #238 says they are waiting for repository-owner review; that is contributor commentary, not maintainer confirmation.
- Current disposition: keep the Node dependency audit FAILED until the advisory is formally withdrawn/clarified or a defensible official remediation is published and verified. Do not install unmerged forks, use private unreviewed overrides, suppress audit severity, omit dev dependencies from the required full audit, or downgrade Vite to manufacture a green result.
- The committed frontend package.json declares only React and React DOM as runtime dependencies; Vite 7.3.8 is a devDependency. The lockfile records picomatch 4.0.7, fdir 6.5.0 and tinyglobby 0.2.17 as dev=true; tinyglobby and Vite both depend on picomatch. This confirms the reported dependency is in the build-tool/development tree, not the declared shipped React runtime dependency set. It reduces direct runtime exposure but does not nullify the full dependency-audit finding or prove the package safe. No project source currently declares picomatch as a direct dependency.

## Model-screen trigger and execution gate

- `.github/workflows/model-integrity-screening.yml` listens to pushes affecting selected model-screen files, but its job condition additionally requires commit message marker `[model-integrity-screen]`; MedGemma additionally requires `[medgemma]` and `[hai-def-terms-accepted]`. Ordinary relevant pushes without markers are skipped.
- The workflow is deliberately sequential: Qwen 3.5 4B must complete and pass exact prompt-v16/audit-v15 manifest and script-digest checks before MedGemma is pulled. Concurrency is 1 and hosted run is CPU-only.
- Do not trigger v16/audit-v15 while the required dependency-security gate remains failed. After security disposition is resolved, create a separate marker-qualified trigger commit and inspect immutable raw outputs, manifest, model digests, logs and audit findings. Qwen failure/truncation must keep MedGemma NOT_REQUESTED.
- The user's prior HAI-DEF terms acceptance remains recorded; it does not make a model screen clinical validation.

## Historical status snapshot — superseded by 8cde5dd

| Workstream | Status | Evidence / boundary |
|---|---|---|
| R1–R4 architecture and persisted data flow | IN PROGRESS | Four-round pipeline exists; full live 45-role R1–R4 acceptance outstanding. |
| R1 independent assessments and unknown/staging safeguards | IN PROGRESS | Deterministic safeguards/regressions exist; broad model adherence not established. |
| R2 saved-source identity, exact text and row ordering | VERIFIED | Backend 471/471 on exact branch head e3dbc3b; backend run 44257129798. |
| R2 option/prerequisite normalization and proposition-level consensus | FAILED | v15 run 44113146755 exposed model narrative/position contradictions and MedGemma source-ID misattribution; v16 live retest remains blocked. |
| R3 adversarial provenance and fabricated-quote review | IN PROGRESS | Source-bound audit regressions pass; broad model adherence not established. |
| R4 Chair synthesis from actual saved R1–R3 | FAILED | v15 MedGemma echoed input; models overclaimed missing-agent consensus from counts-only evidence; v16 live retest remains blocked. |
| Clinical safety, staging and unknown data | IN PROGRESS | No clinical validation, guideline concordance or zero-hallucination claim; independent review outstanding. |
| Case integrity, contradiction preservation and audit history | IN PROGRESS | Historical failed raw runs and immutable artifacts retained; live-model remediation not established. |
| Provenance and guideline/evidence retrieval | IN PROGRESS | Screening harness has source text/IDs; in-app guideline retrieval and linked evidence incomplete. |
| Chair consensus, dissent and traceability | FAILED | v15 partial-agreement contradiction and R4 source-echo failures await live retest. |
| Missing/failed-agent handling | FAILED | v15 MedGemma omitted counts/role identity; deterministic guards are regression-tested, not live-model verified. |
| Backend tests — exact head e3dbc3b | VERIFIED | Run 44257129798: 471/471 passed; deterministic preflight 7/7; artifact 14406780194. |
| Frontend build — exact head e3dbc3b | VERIFIED | Run 44257129844 passed. |
| Patient Registry / Four-Round / Development Monitor browser E2E — exact head e3dbc3b | VERIFIED | Run 44257129743 passed. Development Monitor explicitly tests latest-run deduplication, HEAD matching, HTTP 403/429, last-good snapshot retention, malformed metadata, recovery and empty state. |
| Mission Control read-only run/role drill-down | VERIFIED | Same real-browser E2E verifies 45 R2 role metadata rows and Chair-only R4 drill-down, with existing saved four-round dashboard fixture. |
| Development Monitor refresh/error resilience | VERIFIED | App validation commit 860703e; selector correction e3dbc3b; exact browser acceptance run 44257129743 passed. |
| Ollama context handling | IN PROGRESS | Historical 6,144/8,192 allocation only; long-run context truncation not proven fixed. |
| Ollama performance and concurrency | IN PROGRESS | Hosted screening concurrency 1; comparable local RTX 4060 timings incomplete. |
| RTX 4060 request-time GPU inference | NOT STARTED | Requires real local inference with request-time nvidia-smi and Ollama offload evidence. |
| Hosted v9–v15 model screens | FAILED | Historical bounded runs retain recorded integrity failures. |
| v16/audit-v15 code/schema/audit regression suite | VERIFIED | Backend 471/471; model behaviour remains a separate unverified gate. |
| v16/audit-v15 live model screen | BLOCKED | Held because the exact-head dependency audit remains FAILED; no v16 inference. |
| Qwen exact-version gate before MedGemma | VERIFIED | Workflow checks Qwen manifest prompt/audit version and script digest before MedGemma pull; live v16 gate pending. |
| Fresh full 45-role R1–R4 validation | NOT STARTED | No fresh complete end-to-end live run accepted. |
| MedGemma HAI-DEF acceptance | VERIFIED | Prior explicit user attestation retained; v15 run recorded terms gate true. |
| MedGemma live evaluation | BLOCKED | Same dependency-security gate; no current inference. |
| Independent blinded model-output review | NOT STARTED | Required independent review not completed. |
| Guideline retrieval and verification | NOT STARTED | No current authoritative evidence set retrieved and linked to simulator conclusions. |
| Independent qualified clinical review | NOT STARTED | No attributable clinical review artifact. |
| Packaging prerequisites — exact head e3dbc3b | VERIFIED | Run 44257129933 passed. |
| Windows installer — exact head e3dbc3b | VERIFIED | Run 44257129757 passed; clean-hosted first-run Ollama/model bootstrap was SKIPPED. |
| Full-history secret scan — exact head e3dbc3b | VERIFIED | Run 44257129843, job 134641397632 passed. |
| CodeQL — exact head e3dbc3b | VERIFIED | Python job 134641397111 and JavaScript/TypeScript job 134641397459 passed in run 44257129843. |
| Python dependency audit — exact head e3dbc3b | VERIFIED | No known vulnerabilities found in run 44257129843, job 134641397382. |
| Node dependency audit — exact head e3dbc3b | FAILED | Run 44257129843, job 134641397382: four high picomatch 4.0.7 findings; GHSA-fc5q-39xc-vjpf / CVE-2026-112366. Upstream PR #269 is open/unmerged, with no checks/review/release. |
| Release acceptance | BLOCKED | Dependency audit failed; v15 model screen failed; v16 screen held; full 45-role run, GPU telemetry, evidence verification and independent clinical review outstanding. |

## Next controlled actions

1. Preserve the passing Development Monitor browser regression and exact-head CI evidence. Do not weaken its metadata validation or last-good snapshot behavior.
2. Continue monitoring official GHSA and upstream picomatch maintainer resolution, including PR #269. A fork PR without checks, maintainer review, merge and official npm release is not remediation.
3. Do not weaken or bypass npm audit. Once an official fixed picomatch release or formal advisory resolution exists, update the dependency through a normal reviewed lockfile change and require the complete npm audit to pass.
4. Keep v16/audit-v15 and MedGemma inference blocked until the dependency-security gate is resolved. Then run Qwen first with the existing prompt/audit/script-digest gates; MedGemma remains conditional on the exact Qwen result and terms gate.
5. Correct live model behavior against the preserved v15 findings before starting a fresh full 45-role R1–R4 run.
6. Complete local RTX 4060 request-time inference telemetry, current evidence retrieval, independent blinded output review and qualified clinical review as separate acceptance gates.


# Historical checkpoint — previous Master Development and Verification Checklist, 17 November 2026

Repository: drvishnua/RadOnc-MDT-Simulator  
Development branch: feature/four-round-mdt-and-performance  
Current branch/PR head before this checklist refresh: 23bf384e487f5f85c80a598a16e0de18463d6f31  
Latest application-code implementation: 65ac2d5a602d31fce0b79e4079b0d203447edcae  
PR #1: open, draft, unmerged; base main  
main: 39a356b8eb09399aa2da1b9b9085965999f5105a, unchanged  
Latest completed model-screen run: 44113146755 — FAILED; prompt v15/audit-v14; artifact 14343725249  
Latest corrective-code push screen workflow: 44137110065 — SKIPPED by commit-message marker guard; no model provision or inference.  
Latest run host: GitHub-hosted Windows CPU; concurrency 1; GPU measurement NOT_PERFORMED; clinical accuracy NOT_EVALUATED.

This is the single authoritative Master Development and Verification Checklist. Earlier dated sections below are retained as historical evidence; this current section supersedes older status snapshots.

Continuity files: PROJECT_STATUS.md, TASK_CHECKLIST.md, DECISIONS.md, EXECUTION_LOG.md, RECOVERY_STATE.md, KNOWN_ISSUES.md.

## Current checkpoint — v16/audit-v15 code regression suite green; dependency security finding remains open

**Latest exact-head CI — PR head 23bf384e487f5f85c80a598a16e0de18463d6f31**
- Backend run 44139377473: success; 471/471 tests passed; deterministic preflight 7/7; compilation passed.
- Frontend build run 44139377463: success.
- Patient registry and saved MDT dashboard browser E2E run 44139377662: IN PROGRESS at checklist refresh.
- Packaging prerequisites run 44139377471: success.
- Windows installer run 44139377483: IN PROGRESS at checklist refresh.
- Security/dependency run 44139377659: npm audit FAILED on four high findings for picomatch 4.0.7; full-history secret scan passed; both CodeQL jobs IN PROGRESS at checklist refresh.
- At checklist refresh: backend, frontend, packaging prerequisites passed; security audit failed; E2E, installer and CodeQL still running. This is a docs-only commit; these are software/build checks only, not model or clinical validation.

**Security finding — exact dependency path**
- npm audit log: picomatch 4.0.7 at node_modules/picomatch; fdir and tinyglobby depend on it; Vite depends on fdir/tinyglobby/picomatch. Lockfile contains one picomatch occurrence, marked dev=true; Vite/fdir/tinyglobby are build-tool dependencies. This is not a production runtime dependency, but the full dependency audit remains a required security gate and is FAILED.
- npm audit fix --force proposes installing Vite 6.2.7, a breaking downgrade from Vite 7.3.8. This option was not used.
- Advisory: GHSA-fc5q-39xc-vjpf / CVE-2026-112366, high-severity ReDoS in single-branch repeated extglobs.
- Upstream PR #237 is open/unmerged at commit 1bf0d04563cb9ce568cf36efc5f6b7187d9911d5. It proposes collapsing selected self-repeating single-branch star extglobs; PR description reports 1,999 upstream tests pass, but this is maintainer-branch evidence, not a released npm package or independent local verification.
- Upstream PR #238 is open/unmerged at commit 44f192261f312ddf236cb7bdc05d8f22663f98f9. It proposes literalizing a leading bare quantifier in repeated extglob branches; also not a released package or independently verified here.
- Neither upstream PR commit has an npm release, and neither has completed check-run evidence surfaced through the inspected commit check-runs endpoint. Do not pin an unmerged upstream branch, mask the advisory, or claim the vulnerability fixed. Wait for an official patched release or conduct a separately isolated, fully tested vendored patch review with an explicit supply-chain decision.
- No dependency files or security workflow have been modified to bypass the finding.

**Failed v15/audit-v14 model screen — immutable historical record**
- Run 44113146755; source SHA 011dda99dc8de4783a10448a12c02dc24a346660.
- Qwen qwen3.5:4b: 12/12 generations, 0 malformed, 2 flagged cases / 2 findings: R2 partial-agreement narrative contradicted structured limited information-sufficiency agreement; R2 conditionality wording strengthened an undocumented prerequisite to absent and omitted unknown/unverified status.
- MedGemma medgemma1.5:4b-it-q4_K_M: 12 generations, 1 empty required R2 response, 4 flagged cases / 5 findings: blank R2 narrative; denied limited information-sufficiency agreement; R2 structured source-ID misattribution; missing-agent counts/identity omission; R4 input echo rather than Chair synthesis.
- Both model digests captured, Qwen first then MedGemma. HAI-DEF terms pre-provision gate passed. Immutable artifact 14343725249 preserves raw outputs and logs. No rewriting or relaxed acceptance.
- Hosted CPU only; GPU NOT_PERFORMED. Clinical accuracy NOT_EVALUATED. No model promoted.

**Corrective v16/audit-v15 code**
- Commit 1fa4e58fc100e911a819709fe02b85d4b043aadc introduced dedicated R4 saved-source inventory, exact source/coverage schema, counts-only insufficient-data guard, updated fixture and exact prompt-version gate.
- Commit 2e1cb5b2c3770e770c2c2609731490f73a0172ce corrected audit use of extracted response text and R4 test/mocked-output contracts.
- Commit 65ac2d5a602d31fce0b79e4079b0d203447edcae restored explicit R4 contradiction/source-separation safeguards and exact insufficient-data outcome in the regression fixture.
- Backend suite is 471/471 passing on implementation SHA 65ac2d5 and subsequent documentation-only heads. This verifies code/schema/audit regressions only. No v16 live model screen has completed.

### Master Checklist — Current Status

| Workstream | Status | Evidence / boundary |
|---|---|---|
| R1–R4 architecture and persisted data flow | IN PROGRESS | Four-round pipeline exists; full live 45-role R1–R4 acceptance outstanding. |
| R1 independent assessments and unknown/staging safeguards | IN PROGRESS | Deterministic safeguards and regression suite; broad model adherence not established. |
| R2 saved-source identity, exact text and row ordering | VERIFIED | Backend tests 471/471 on implementation SHA 65ac2d5 and docs-only PR head ffac504 pass. |
| R2 option/prerequisite normalization and proposition-level consensus | FAILED | v15 run 44113146755: both models failed narrative/position requirements; MedGemma misattributed structured IDs. v16 live retest not run. |
| R3 adversarial provenance and fabricated-quote review | IN PROGRESS | Source-bound audit regressions pass; v15 had no flagged R3 cases, broader adherence unverified. |
| R4 Chair synthesis from actual saved R1–R3 | FAILED | v15 MedGemma echoed input; both models overclaimed missing-agent consensus from counts-only evidence. v16 code regressions pass, model behaviour not retested. |
| Clinical safety, staging and unknown data | IN PROGRESS | No clinical validation, guideline concordance or zero-hallucination claim; independent review outstanding. |
| Case integrity, contradiction preservation and audit history | IN PROGRESS | Raw failed run and immutable artifact retained; historical integrity failures remain unresolved. |
| Provenance and guideline/evidence retrieval | IN PROGRESS | Exact source text/IDs in screening harness; guideline retrieval and source-linked evidence in app not complete. |
| Chair consensus, dissent and traceability | FAILED | v15 partial-agreement contradiction and R4 source-echo failures pending live retest. |
| Missing/failed-agent handling | FAILED | v15 MedGemma omitted counts/role ID; new count-only guard regression-tested but not live-model verified. |
| Backend CI — PR head 23bf384 | VERIFIED | Run 44139377473: 471/471 passed; deterministic preflight 7/7; compilation passed. |
| Frontend build — PR head 23bf384 | VERIFIED | Run 44139377463 passed. |
| Patient registry/dashboard browser E2E — PR head 23bf384 | IN PROGRESS | Run 44139377662 running at checklist refresh. This is not full 45-role clinical simulation. |
| Mission Control development-process monitor | IN PROGRESS | Backend Mission Control tests pass; dedicated browser E2E/operational acceptance for complete live development monitor not established. |
| Ollama context handling | IN PROGRESS | Historical 6,144/8,192 allocation only; long-run context truncation not proven fixed. |
| Ollama performance and concurrency | IN PROGRESS | Hosted screening concurrency 1; comparable local RTX 4060 timings incomplete. |
| RTX 4060 request-time GPU inference | NOT STARTED | Requires real local inference with request-time nvidia-smi and Ollama offload evidence. |
| Hosted v9–v15 model screens | FAILED | Historical bounded runs retain recorded integrity failures. |
| v16/audit-v15 code/schema/audit regression suite | VERIFIED | Backend 471/471; live model behaviour remains a separate unverified gate. |
| v16/audit-v15 live model screen | NOT STARTED | No v16 inference has been started. Release only after agreed security/build gates and separate marker-triggered run. |
| Qwen exact-version gate before MedGemma | VERIFIED | Workflow has strict Qwen manifest version/script digest check before MedGemma pull; live v16 gate awaits execution. |
| Fresh full 45-role R1–R4 validation | NOT STARTED | No fresh complete end-to-end live run accepted. |
| MedGemma HAI-DEF acceptance | VERIFIED | Prior explicit user attestation retained; v15 run records terms gate true. |
| Independent blinded model-output review | NOT STARTED | Required independent review not completed. |
| Guideline retrieval and verification | NOT STARTED | No currently retrieved authoritative evidence set linked to simulator conclusions. |
| Independent qualified clinical review | NOT STARTED | No attributable clinical review artifact. |
| Packaging prerequisites — PR head 23bf384 | VERIFIED | Run 44139377471 passed. |
| Windows installer — PR head 23bf384 | IN PROGRESS | Run 44139377483 running at checklist refresh. Clean-hosted first-run Ollama/model bootstrap remains NOT VERIFIED if skipped by workflow. |
| Full-history secret scan — PR head 23bf384 | VERIFIED | Run 44139377659 passed. |
| CodeQL static analysis — PR head 23bf384 | IN PROGRESS | Python and JavaScript/TypeScript jobs running in run 44139377659 at checklist refresh. |
| Dependency audit — PR head 23bf384 | FAILED | Run 44139377659: four high findings via picomatch 4.0.7, GHSA-fc5q-39xc-vjpf / CVE-2026-112366; full audit still fails despite dev-only scope. No downgrade or override applied. |
| Release acceptance | BLOCKED | v15 model screen failed; v16 live screen pending; npm audit fails; full 45-role run, GPU telemetry, authoritative evidence and independent clinical review outstanding. |

**Next controlled action:** wait for an official patched picomatch release, or separately approve a controlled local patch experiment with pinned source, full picomatch upstream test suite, RadOnc frontend build/E2E and complete npm audit. Do not alter dependency audit severity/omission settings to manufacture a green gate. After the security gate is genuinely clean, trigger v16/audit-v15 separately and inspect immutable Qwen/MedGemma artefacts. Full 45-role, GPU and independent clinical validation remain separate gates.

## Historical checkpoint — 17 November 2026 — d836076 exact-head CI green; v15 screen authorised

**Current repository state**
- Verified checkpoint commit: d836076f1f6f7543c6b226957e85249d76548a5b; this commit changes only the master checklist.
- Development branch: feature/four-round-mdt-and-performance. PR #1 remains open, draft and unmerged; target main. main remains 39a356b8eb09399aa2da1b9b9085965999f5105a.
- Prompt-v15/audit-v14 source: 9a4e9f6bac63ef4b471037f5166b21deeb3aab3a; regression tests: ae6f1f8f44708e98ecd3ffe59e048b4030bbeb48.
- All six standard PR workflows passed on exact SHA d836076f1f6f7543c6b226957e85249d76548a5b:
  - Backend 44093599360 — success.
  - Frontend 44093599332 — success.
  - Browser E2E 44093599376 — success.
  - Security/dependency 44093599364 — success.
  - Packaging prerequisites 44093599358 — success.
  - Windows installer 44093599558 — success.
- These are software/build checks only; they do not establish model acceptance, GPU inference, clinical accuracy, guideline concordance or release approval.
- v15/audit-v14 bounded screen remains NOT STARTED. v14/audit-v13 run 44061072616 remains FAILED for both models.

**Next controlled action**
- Trigger the v15/audit-v14 synthetic screen from a separate commit that touches the model-screen workflow and includes the required commit-message markers [model-integrity-screen], [medgemma], and [hai-def-terms-accepted].
- Preserve the sequential Qwen-first gate. If Qwen fails or truncates, MedGemma must remain NOT_REQUESTED. Inspect the immutable artifact, manifest, hashes, logs and every generated case before any human acceptance decision.

**Current repository state**
- Branch HEAD before this checklist-only reconciliation: a40ac2964b2c37e666e3f4fc4f4a57a6fdc965ad.
- PR #1: open, draft, unmerged; base main. Main SHA 39a356b8eb09399aa2da1b9b9085965999f5105a unchanged.
- Prompt-v15/audit-v14 source: 9a4e9f6bac63ef4b471037f5166b21deeb3aab3a; regression tests: ae6f1f8f44708e98ecd3ffe59e048b4030bbeb48.
- Model-screen workflow v15/audit-v14 has NOT yet been triggered. Last completed model screen is v14/audit-v13 run 44061072616, which failed for both models.

**All six standard checks passed on exact SHA a40ac2964b2c37e666e3f4fc4f4a57a6fdc965ad**
- Backend run [44083286208](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286208): 463/463 passed; 0 failures/errors/skips/inconclusive; deterministic preflight 7/7. Job 134039086800.
- Frontend run [44083286292](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286292): success.
- Browser E2E run [44083286320](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286320): success.
- Security/dependency run [44083286648](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286648): success.
- Packaging prerequisites [44083286163](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286163): success.
- Windows installer [44083286286](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44083286286): success; job 134039090991 completed package build, installer installation/smoke test, checksum and artifact upload. Artifact 14328805373 (RadOnc-MDT-Simulator-Windows-x64, 14,882,190 bytes). Hosted first-run Ollama/model bootstrap job 134040005934 was skipped; this is not model execution evidence.
- This is software/build verification only; not model acceptance, clinical validation, GPU verification or release approval.

**Next controlled action**
- After this checklist-only commit's standard CI is green, create a separate commit touching only the model-screen workflow (or another explicitly allowed push-path file), with the three required marker tokens in its commit message: model-integrity-screen, medgemma, hai-def-terms-accepted. This uses the user's prior personal HAI-DEF acceptance attestation and preserves the sequential Qwen-first gate. Inspect all immutable artefacts and all 24 outputs; if Qwen fails/truncates, MedGemma must remain NOT_REQUESTED.

## Historical checkpoint — 17 November 2026 — prompt-v15/audit-v14 ready for bounded screen

**Repository / branch**
- Development branch HEAD: 10f530d397a3a82785bd86929baa1e91e6ec19b8 (documentation-only checklist commit; no source changes in this commit).
- Latest prompt-v15/audit-v14 source commit: 9a4e9f6bac63ef4b471037f5166b21deeb3aab3a.
- Latest prompt-v15/audit-v14 regression-test commit: ae6f1f8f44708e98ecd3ffe59e048b4030bbeb48.
- Latest model-screen trigger remains v14/audit-v13 SHA 9583e15671d3d8bdca7f88d383bc0e2fbfb9b60b; v15 screen has NOT been triggered.
- PR #1 remains open, draft, unmerged, base main. Main SHA 39a356b8eb09399aa2da1b9b9085965999f5105a remains unchanged.

**Exact branch-head CI — 10f530d397a3a82785bd86929baa1e91e6ec19b8**
- Backend run [44070168040](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070168040): 463 passed, 0 failed, 0 errors, 0 skipped; deterministic preflight 7 passed, 0 failed, 0 inconclusive. JUnit artifact 14322645718; preflight artifact 14322640818.
- Frontend run [44070168039](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070168039): passed.
- Browser E2E run [44070167975](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070167975): passed.
- Security/dependency run [44070168390](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070168390): passed.
- Windows packaging prerequisites [44070168162](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070168162): passed.
- Windows installer [44070168142](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44070168142): passed build, installation, health/frontend/API smoke tests, 45-role profile check, synthetic registry persistence, uninstall-preservation check, checksum and artifact upload. Installer artifact 14321943253; Setup.exe SHA-256 a5d31d19bedede5333b733e63e7125ca7c67ddd813b81c951d1cf4a0b1efe004. Hosted installer job explicitly performed no Ollama inference.
- These six runs are associated with exact branch HEAD 10f530d. CI is software/build evidence, not model or clinical validation.

**Prompt-v15/audit-v14 implementation and regression scope**
- R2 audit now flags certainty strengthening of a case-supplied unknown/not-documented prerequisite to absent, missing, unmet, failed, negative or ruled out. “Not present in the supplied record” remains an acceptable documentation-status statement.
- R3 audit now flags refusal to compare the supplied synthetic quote with the exact saved source text.
- Regression tests cover both invalid outputs and valid counterexamples. Source and test changes are committed; exact branch-head CI above passed.
- v14/audit-v13 model screen [44061072616](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44061072616) remains failed for both models: Qwen 1 finding; MedGemma 8 findings. Preserve its artifact and failure.
- Next: create one separate marker-qualified model-screen trigger commit from this CI-green branch head; run the existing sequential Qwen-first/MedGemma-second fail-closed workflow; inspect all 24 outputs and artifact provenance. If Qwen fails or truncates, MedGemma must remain NOT_REQUESTED. No model promotion or clinical claim from workflow success.






## Historical checkpoint — 17 November 2026 — prompt-v14/audit-v13 bounded retest

**Repository / branch**
- Development branch: feature/four-round-mdt-and-performance.
- Latest tested application/test SHA: f038f109b2219e14ea0974e5f721fc66f335bf42.
- Latest model-screen trigger SHA: 9583e15671d3d8bdca7f88d383bc0e2fbfb9b60b.
- Current branch head at this checkpoint: 9583e15671d3d8bdca7f88d383bc0e2fbfb9b60b.
- PR #1: open, draft, unmerged, targets main.
- main SHA: 39a356b8eb09399aa2da1b9b9085965999f5105a; unchanged.
- The single authoritative checklist was read from the development branch before this update.

### Previous bounded screens

**v12 / audit-v11 — run 44045424408**
- Workflow completed SUCCESS; artifact 14312436697; archive SHA-256 f1445173f0349843a6718e2de3bb6e2472cd45a136f402d74530307cb724c877.
- Qwen 12/12, 3 flagged cases / 6 findings. MedGemma 12/12, 5 flagged cases / 11 findings.
- Both summaries PENDING_HUMAN_REVIEW; clinical accuracy not evaluated; hosted CPU only; GPU NOT_PERFORMED.
- Bounded acceptance FAILED for both.

**v12 / audit-v12 — run 44055332966**
- Workflow FAILURE; artifact 14316193116; archive SHA-256 4448fe17c075172902620cff8ffc6597a8964c4fdd9ddab6de3ea85e45a409a7.
- Qwen produced 12 generations; 11 parseable structured responses and one truncated JSON response on R2-CONDITIONALITY-007 at eval_count=500 / num_predict=500.
- No deterministic flags among the 11 parseable responses; do not treat this as a model pass.
- MedGemma was NOT_REQUESTED because sequential fail-closed gating stopped after Qwen's malformed response.
- HAI-DEF pre-provision gate passed; CPU-only; GPU NOT_PERFORMED.

**v13 / audit-v12 — run 44057996924**
- Workflow FAILURE; artifact 14317890819; 7,478,846 bytes; archive SHA-256 ff2e3b514f1dd3904055615562db1e8e283c090cd9c3117ab2b0e8b5ab509abb.
- Prompt radonc-mdt-integrity-screen-v13; audit radonc-mdt-integrity-audit-v12; frozen 12-case corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3.
- Ollama 0.40.14; concurrency 1; CPU-only; Qwen and MedGemma digests remained identifiable and stable. MedGemma pull exit code 0; terms gate passed.
- Qwen 12/12 responses; 0 malformed; 2 flagged cases / 2 findings:
  - R2 partial agreement: structured ledger source positions were source-normalized, but proposition remained not_shared despite two exact affirmative sources; narrative wrongly said only one source agreed.
  - R2 conditionality: source MO-01 prerequisite status remained not_applicable despite case-supplied status unknown.
- MedGemma 12 generations; 1 malformed/empty; 4 flagged cases / 5 findings:
  - R2 false consensus: empty response field; structured Option A/Option B values were not retained.
  - R2 conditionality: source IDs were populated while proposition status was not_shared; source attribution was unsupported.
  - R3 invalid-source case: refusal to audit an explicitly supplied synthetic identifier inventory.
  - R4 missing-agent case: omitted expected 45 / saved 44 counts, missing role ID and null response status.
  - R4 Chair case: echoed input JSON rather than synthesizing saved contributions.
- Both summaries PENDING_HUMAN_REVIEW; automatic score null; clinical_accuracy_evaluated=false. Bounded acceptance FAILED. CPU-only; GPU NOT_PERFORMED.

### Prompt-v14 / audit-v13 corrective changes

- Implementation sequence: 6c689ffb204d7c1f294bcc730af40295fac4556b, 7ab7fdc20a5f87d4334212b652819a6fe3e1ce7f, and final source commit 5ac3e09d3ae174923b33deaa881aeb6709807452.
- Prompt version is now radonc-mdt-integrity-screen-v14; audit version radonc-mdt-integrity-audit-v13.
- Exact-source normalization now restores prerequisite_status=unknown when the case metadata explicitly says unknown and the saved source names the prerequisite. The change is provenance-logged.
- When at least two exact saved R1 statements explicitly say they agree that additional information is required, the server may correct only a not_shared / empty-ID structured information proposition to shared with the exact affirmative source IDs. The correction is recorded in server_derived.proposition_normalizations.
- The raw model response remains preserved. New audits separately flag narratives that deny or omit this limited information agreement, fail to name the supporting sources, or omit Option A / prerequisite X / unknown status. The narrative is not silently rewritten.
- Conflicting option values, ambiguous source labels, treatment consensus and unsupported source IDs are not repaired by these changes.
- Regression tests added for prerequisite-status normalization, exact-source shared-information derivation, preservation of contradictory narrative as an audit failure, and R2 conditionality language.
- Test-only correction commits included 10d87f00194e6100b470a588e03581725ea8fdb8, 8ad3cbcb8eed85ed76777b5d5a0cfc40c7f84232, and final exact-SHA test commit f038f109b2219e14ea0974e5f721fc66f335bf42.
- An intervening backend run on 10d87f failed 2/461 on stale/case-sensitive test assertions; both were inspected and corrected. That failed run is preserved.
- Exact-SHA Backend run 44060579022 on f038f109: 461 passed, 0 failed, 0 errors, 0 skipped; 1 warning. Deterministic preflight 7/7 passed.
- All six standard PR checks passed on exact SHA f038f109: Backend 44060579022; Frontend 44060579045; Browser E2E 44060579149; Security/Dependency 44060579131; Packaging Prerequisites 44060579083; Windows Installer 44060579122.
- Push Windows Installer run 44060569668 also passed.

### Latest bounded model screen — prompt-v14 / audit-v13 — COMPLETED; BOTH MODELS FAILED ACCEPTANCE

- Workflow 44061072616 completed SUCCESS on immutable trigger SHA 9583e15671d3d8bdca7f88d383bc0e2fbfb9b60b. This is execution success only, not model acceptance.
- Artifact 14320435156, name radonc-synthetic-model-screening-44061072616, 7,479,380 bytes; archive SHA-256 4ec9421c9b295a28b5994d34eac873bfb64ac135d5975f394141f4c18932e513.
- Manifest confirms prompt radonc-mdt-integrity-screen-v14; audit radonc-mdt-integrity-audit-v13; script SHA-256 efb2876bcf02105a0a6f9d16b9ff1de0d3e3973247dbae4cf20524763569c3b0; corpus SHA-256 5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3.
- Ollama 0.40.14; hosted Windows CPU only; concurrency 1; GPU measurement NOT_PERFORMED. Qwen digest sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma digest sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c.
- Qwen: 12/12 responses; 0 malformed; 1 flagged case / 1 finding. R2-PARTIAL-AGREEMENT-006 structured limited information proposition was repaired to shared with exact source IDs, but narrative omitted the source IDs. R2-CONDITIONALITY-007 narrative said prerequisite X was absent despite source/case status being unknown; previous audit did not flag this certainty strengthening. No automatic quality score; human review pending.
- MedGemma: 12/12 responses; 0 malformed; 5 flagged cases / 8 findings. R2-FALSE-CONSENSUS-005: 3 structured source-ID/false-consensus findings; R2-PARTIAL-AGREEMENT-006: 1 narrative source-attribution finding; R2-CONDITIONALITY-007: 2 structured source-ID/misattribution findings; R4-MISSING-AGENT-011: 1 completeness finding (omitted 45 expected / 44 saved / PT-ROLE-UNAVAILABLE / null response); R4-CHAIR-TRACEABILITY-012: 1 Chair JSON-echo finding. R3-FABRICATED-QUOTE-009 refused the supplied quote audit but this refusal was not flagged by audit-v13. No automatic quality score; human review pending.
- Both summaries have clinical_accuracy_evaluated=false and acceptance_status PENDING_HUMAN_REVIEW. For engineering acceptance, both models fail the frozen screen. No clinical accuracy or zero-hallucination claim.
- All six standard PR checks passed on trigger SHA 9583e156: Backend 44061081762; Frontend 44061081774; Packaging Prerequisites 44061081644; Browser E2E 44061081798; Security/Dependency 44061081822; Windows Installer 44061081909.
- Raw model JSONL, prompt hashes, request bodies, response metrics, Ollama logs, manifest and artifact retained in artifact 14320435156.

### Prompt-v15 / audit-v14 corrective work — IN PROGRESS

- Source changes: commit 9a4e9f6bac63ef4b471037f5166b21deeb3aab3a (following initial implementation commit f37cafcb11d48f6499fccdf7dabcdbfb06c7d1c2).
- Audit change 1: R2 conditionality narrative audit now flags a model that strengthens unknown/not-documented prerequisite X to absent, missing, unmet, failed, negative or ruled out. Exact wording "not present in the supplied record" remains a valid unknown status.
- Audit change 2: R3 fabricated-quote case now independently flags refusal to compare the supplied model-claimed quote with exact saved source text. Existing structured quote fields remain unchanged; no model prose is repaired.
- Regression tests added in commit ae6f1f8f44708e98ecd3ffe59e048b4030bbeb48 for both new audit findings and valid counterexamples.
- Current branch HEAD at checklist update: ae6f1f8f44708e98ecd3ffe59e048b4030bbeb48. Backend/other CI for this new source/test head not yet verified. No v15 screen triggered until exact-head CI passes.
- The source regex was inspected after commit and corrected to use actual regex word boundaries; final implementation commit is 9a4e9f6bac63ef4b471037f5166b21deeb3aab3a.

### Current CI and repository state

- PR #1 remains open, draft, unmerged, targets main. main SHA 39a356b8eb09399aa2da1b9b9085965999f5105a unchanged.
- Previous checklist heads 4c017999 and e309a879 each passed all six standard PR workflows. The v14 trigger SHA 9583e156 also passed all six standard checks.
- This checklist update will trigger a fresh six-check PR cycle. The next v15 model screen must be a separate explicitly marked commit after the implementation/test head has all required checks green.

### Historical checklist snapshot superseded by the active table above

The preceding status table is superseded; use the current table near the beginning of this file.

## Immediate next actions

1. Create one separate marker-qualified model-screen trigger commit from the CI-green branch head 10f530d; do not change source files or start a second overlapping model run.
2. Inspect the v15/audit-v14 workflow, model identity/digests, corpus/prompt/audit hashes, all 24 outputs, completion reasons, normalization provenance, flags and raw artefacts.
3. Preserve the Qwen-first fail-closed gate: if Qwen fails or truncates, MedGemma remains NOT_REQUESTED.
4. Check R2 unknown-prerequisite certainty, R3 fabricated-quote refusal, R4 missing-agent completeness and Chair synthesis from actual saved R1–R3 contributions.
5. Treat any bounded pass as engineering evidence only; no clinical validation, guideline compliance, zero-hallucination or GPU claim.
5. Arrange independent blinded review of retained v10–v14 outputs before model promotion.
6. Only after bounded acceptance and human review, prepare fresh full 45-role R1–R4 validation with failed-agent injection and Chair synthesis from saved contributions.
7. Complete local RTX 4060 request-time telemetry, authoritative guideline retrieval and independent qualified clinical review.

**Cloud/device boundary:** GitHub repository work, CI, packaging and hosted CPU screens do not require the user's PC to be online. Only local RTX 4060 request-time inference verification requires the local device powered on. Hosted CPU execution does not prove GPU use or clinical validity.


## Historical checkpoint — v11/audit-v10 and initial v12/audit-v11 planning (superseded by the current checkpoint above)

### v10 / audit-v9 model screen — workflow 44037072649

- Exact screening commit: 274dad69af048c511dfa86ab179e4bf496833580.
- Workflow: https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/44037072649
- Evidence artifact: 14308901197, SHA-256 `825dd4878e1db8dd53b4bf252cd639c33749fdf7a7627e23151eacd73eaa3006`.
- Artifact was downloaded and its manifest, both JSONL outputs, Ollama logs and pull diagnostics inspected.
- Prompt version: `radonc-mdt-integrity-screen-v10`; audit version: `radonc-mdt-integrity-audit-v9`.
- Frozen corpus: 12 unique synthetic cases; unchanged corpus SHA-256 `5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3`.
- Ollama 0.40.14, concurrency 1. Model digests stayed stable before/after every generation.

**Qwen 3.5 4B**
- Model digest: `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
- 12/12 responses recorded; 0 malformed/failed.
- 3 cases flagged; 4 deterministic integrity findings.
- Findings: R2 false-consensus case (Option A omitted in structured ledger); R2 partial-agreement case (shared information-sufficiency proposition omitted from structured fields); R2 conditionality case (option shorthand and no-option sentinel not canonically represented in structured ledger).
- Manual output inspection: R1 unknown staging and missing-status responses did not assert a definite stage or patient status; R4 missing-agent response preserved 45 expected / 44 saved / exact missing role and did not invent a missing position. The R3 invalid-source response narrative contradicted its own correct structured inventory by labelling supplied IDs as unsupplied/malformed; this was not flagged by audit-v9 and is now covered by audit-v10 regression tests.
- Total case wall time approximately 464.9 seconds; CPU-hosted only.

**MedGemma 1.5 4B**
- Model digest: `sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c`.
- 12/12 responses recorded; 0 malformed/failed.
- 4 cases flagged; 18 deterministic integrity findings.
- Findings: R2 false-consensus (both conditional options omitted); R2 partial-agreement (source positions misclassified and shared information proposition omitted); R2 conditionality (conditional option/prerequisite not retained); R3 fabricated quotation accepted as present/supported despite being absent.
- Manual output inspection: MedGemma declined several intentionally synthetic classification tasks; its R4 responses echoed case/input JSON rather than providing a Chair synthesis. Audit-v9 did not reliably reject these R4 echoes because echoed input contained the words used by the audit. Audit-v10 now detects these echoes.
- Total case wall time approximately 385.6 seconds; CPU-hosted only.

**Execution boundary**
- Workflow success means the two sequential screens completed and artifacts were uploaded; it is not a model-quality pass.
- Both JSONL manifests explicitly say `PENDING_HUMAN_REVIEW`; automatic quality score is null and clinical accuracy was not evaluated.
- Hosted Windows logs show CPU inference backend and CPU buffers; GPU measurement is `NOT_PERFORMED`. This is not RTX 4060 evidence.
- MedGemma HAI-DEF pre-provision acceptance gate passed; model pull exit code was 0 and the exact MedGemma digest was captured.

### Corrective implementation after v10 review

- Commit 055e5cc9cf2e8e9ab4f56cba8b1b2d46565757da introduced prompt v11/audit v10: independent R2 information-sufficiency vs treatment-consensus instructions; source-bound normalization of unambiguous conditional option shorthand and explicit no-option sentinels; explicit synthetic-task/no-refusal instruction; explicit distinction between model-claimed quote and locked saved text; R4 no-input-echo instruction and deterministic JSON-echo detection.
- That commit's first backend CI attempt failed 2 of 449 tests due to a case-sensitive prompt assertion and an incomplete expected normalization list. The JUnit artifact was inspected; these were test expectation defects, not hidden or ignored.
- Commit 57d6064087c63ccb94eeec43aa670891fe3792c8 corrected those test expectations and added R3 narrative-vs-structured identifier contradiction and synthetic audit-refusal checks.
- Exact-SHA backend run 44040195517: **451 passed, 0 failed, 0 errors, 0 skipped**. JUnit artifact 14309136871 downloaded and inspected; diagnostics report passed.
- Exact-SHA Frontend Build 44040195520: VERIFIED.
- Exact-SHA Browser E2E 44040195519: VERIFIED.
- Exact-SHA Security/Dependency/Secret Scan/CodeQL 44040195526: VERIFIED.
- Exact-SHA Windows Packaging Prerequisites 44040195720: VERIFIED.
- Exact-SHA PR Windows Installer 44040195512: VERIFIED; installed-app smoke test and artifact upload completed.
- Exact-SHA push Windows Installer 44040185771: VERIFIED; build/install/smoke/upload passed.
- Model screening push run 44040185706: SKIPPED as expected because code commit 57d6064 did not include a model-screen marker.
- Documentation checkpoint d65534e837c141f88e7268b29e7b2b75f7bec2e0 did not change application code. All six PR checks on that exact head passed: Backend 44040716001; Frontend 44040715987; Browser E2E 44040716041; Windows Packaging Prerequisites 44040716022; Windows Installer 44040716081; Security/Dependency/CodeQL 44040715993.
- Latest checklist reconciliation commit da07b1d0ae2f9fb6cec61c1ff3988646967cde6e changes documentation only. On that exact SHA, Backend 44041146885, Frontend 44041146868, Windows Packaging Prerequisites 44041147002, Browser E2E 44041146870 and Security/Dependency/CodeQL 44041146896 passed; Windows Installer 44041146854 remained IN PROGRESS at the later check.
- Current documentation-only branch head f4948e351d4a580643cca52d14e0474ef7966ac6 has a fresh six-check PR cycle: Backend 44041294229, Frontend 44041294224, Browser E2E 44041294378, Packaging Prerequisites 44041294222, Security/CodeQL 44041294235 and Windows Installer 44041294340. All were IN PROGRESS or queued at the latest exact-head check. These changes do not modify the application/test source SHA 57d6064.
- The documentation-only marker commit f1cf9e0a5579122277c2eec241250fb5db1c6156 did NOT start the screen because docs are excluded by the workflow push-path filter. No v11 model run was assumed.
- Workflow-file trigger commit 07548081f2b41ee1ed9db652e78156e2b65cc9be matched the push-path filter and started Synthetic Model Integrity Screening **44040631649** on that exact SHA.
- Workflow 44040631649 completed SUCCESS on trigger SHA 07548081f2b41ee1ed9db652e78156e2b65cc9be. Evidence artifact 14310935167, 7,479,717 bytes, archive SHA-256 51f6c00c8ad3c1ea2e59c0a891d6848828d33a5cf983f77cf44b6521636edd60.
- HAI-DEF gate passed; Qwen and MedGemma both completed 12/12 sequential responses. Artifact, manifest, both JSONL files, Ollama logs and pull diagnostics were downloaded and inspected; model digests stayed stable before/after each generation.
- Qwen 3.5 4B: 2/12 cases flagged, 4 integrity findings; 0 malformed/failed. All findings were R2: partial-agreement had three unsupported prerequisite labels; conditionality omitted Option A from the structured ledger. No flags in R1, false-consensus, R3, or either R4 case.
- MedGemma 1.5 4B: 6/12 cases flagged, 18 integrity findings; 0 malformed/failed. Findings: R2 false-consensus (2 conditional-option omissions); R2 partial-agreement (9 source-position/unsupported option/prerequisite findings); R2 conditionality (4 option/prerequisite findings); R3 invalid-source audit refusal (1); R4 missing-agent completeness (1); R4 Chair input echo (1). Fabricated-quote case correctly classified the claimed quote absent/unsupported with no deterministic flag.
- Both summaries remain PENDING_HUMAN_REVIEW; automatic quality score is null and clinical accuracy was not evaluated. Workflow success is execution/artifact success, not model-quality acceptance.
- Wall time: Qwen approximately 593.9 seconds; MedGemma approximately 412.3 seconds. Ollama logs explicitly show CPU backend/buffers on hosted Xeon; GPU measurement NOT_PERFORMED. Not RTX 4060 evidence.
- Exact digests: Qwen sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04; MedGemma sha256:433252621ab154668b5d8be6aff6c1b771bacba045e46e6193da8d6ad1630f2c. MedGemma HAI-DEF gate and pull passed.
- v11 bounded acceptance is FAILED for both models; preserve raw outputs and do not promote either.
- v12/audit-v11 changes on aa6dac: R2 prompt explicitly requires exact source labels and empty strings for absent options/prerequisites; source-bound normalization handles Option_A (conditional), not_shared no-option sentinels and no-prerequisite sentinels, logging every change in server_derived.field_normalizations; R3 audit checks nested JSON-object inventory contradictions as well as list-style output.
- First v12 test attempt failed one new normalization regression due to over-escaped regex. Failure was inspected and corrected; exact-SHA backend run 44045273632 passed 453 tests, 0 failed/errors/skipped. Earlier failed run 44045174509 remains preserved.
- Trigger commit eb75b076459a4f5da62758b631c59ca2fef1232f contains [model-integrity-screen], [medgemma] and [hai-def-terms-accepted]. Screening run 44045424408 passed its HAI-DEF pre-provision gate and is IN PROGRESS in the combined Ollama provisioning/inference step; no v12 outputs/artifact yet.
- On exact trigger SHA eb75b076, Backend 44045430442, Frontend 44045430218, Browser E2E 44045430256, Security/Dependency/CodeQL 44045430170 and Packaging Prerequisites 44045430220 passed; PR Windows Installer 44045430183 and push Windows Installer 44045424397 remained IN PROGRESS at latest check.
- Checklist reconciliation commit 984f259944b0341b8f0ce70bc665da5ccc5e34b7 is documentation-only. Its Backend 44045682142, Frontend 44045682255 and Packaging Prerequisites 44045682155 passed; Browser E2E 44045682137, Security/CodeQL 44045682129 and Windows Installer 44045682163 were cancelled when the next docs commit superseded that head.
- Current documentation-only branch head 57e6beb4b6a433de60ca5137b08627e8c4448fd5: Backend 44045771155 passed 453/453; Frontend 44045771203, Browser E2E 44045771259, Security/CodeQL 44045771201 and Packaging Prerequisites 44045771220 were IN PROGRESS; Windows Installer 44045771149 was queued. PR #1 remains open/draft/unmerged against main; main SHA remains 39a356b8eb09399aa2da1b9b9085965999f5105a.

### Historical v11 status table — superseded by the current checklist above

| Workstream | Status | Evidence / boundary |
|---|---|---|
| R1–R4 architecture and persisted data flow | IN PROGRESS | Four-round pipeline exists; fresh full 45-role end-to-end acceptance outstanding. |
| R1 independent assessments and unknown/staging safeguards | IN PROGRESS | v10 synthetic outputs manually inspected; no clinical validity claim; broader adversarial review remains. |
| R2 saved-source identity, exact text and row ordering | VERIFIED | Screening-harness contract: exact saved IDs/text validated; source order server-derived from saved R1 order. |
| R2 conditionality and proposition-level consensus | IN PROGRESS | v11 live screen: Qwen still had 4 R2 findings; MedGemma 15 R2 findings. v12 prompt adds exact source-label/empty-field requirements and bounded source-derived normalizations; backend regression tests pass on exact SHA aa6dac. v12 live retest pending. |
| R3 adversarial provenance and fabricated-quote review | IN PROGRESS | v11: Qwen had no R3 flags; MedGemma refused the supplied identifier audit; fabricated-quote rejection was correctly represented. Audit-v11 adds nested JSON-object contradiction regression; v12 live retest pending. |
| R4 Chair synthesis from actual saved R1–R3 | IN PROGRESS | v11: Qwen passed both bounded R4 cases; MedGemma failed missing-agent completeness and Chair synthesis (input echo). v12 live retest pending; full production Chair acceptance outstanding. |
| Clinical safety, staging and unknown data | IN PROGRESS | No zero-hallucination or clinical-validity claim; independent qualified review outstanding. |
| Case integrity, contradiction preservation and audit history | IN PROGRESS | Original v9/v10 outputs and artifacts preserved; historical run-9 still has 343 integrity findings. |
| Provenance and guideline/evidence retrieval | IN PROGRESS | Screening manifests and source-bound transformations recorded; current guideline retrieval and claim linkage not integrated. |
| Chair consensus, dissent and traceability | IN PROGRESS | Deterministic safeguards and audit tests pass; live model adherence and full 45-role review outstanding. |
| Missing/failed-agent handling | IN PROGRESS | Missing-agent synthetic case outputs inspected; full 45-role failure-injection acceptance outstanding. |
| Backend tests | VERIFIED | 453 passed, 0 failed, 0 errors, 0 skipped on aa6dac run 44045273632; repeated on current docs-only head 57e6 run 44045771155 with 453/453. JUnit artifact 14311247409 and deterministic preflight artifact 14311386191 from the aa6dac run. No model inference or clinical accuracy evaluation in these test runs. |
| Frontend build | VERIFIED | Run 44040195520 on exact SHA 57d6064. |
| Browser E2E | VERIFIED | Run 44040195519 on exact SHA 57d6064. |
| Dashboard and read-only API validation | VERIFIED | Mission Control and Developer Monitor previously browser-verified; broader production API testing remains IN PROGRESS. |
| Mission Control phase 1 and phase 2 | VERIFIED | Read-only persisted run overview and metadata-only per-role drill-down tested. |
| Development Monitor dashboard | VERIFIED | Read-only branch/PR/Actions dashboard tested; no automatic dispatch authority. |
| Ollama context handling | VERIFIED | Historical 6,144/8,192 allocation probes only; does not prove live long-output integrity. |
| Ollama performance and concurrency | IN PROGRESS | Concurrency 1 retained; CPU screening metrics captured; comparative local performance incomplete. |
| RTX 4060 request-time GPU inference | NOT STARTED | Local Windows PC must run real Ollama inference with request-time nvidia-smi/offload evidence. |
| Hosted Qwen/MedGemma v9 screen | FAILED | Run 44031253593, artifact 14304964550; preserved. |
| Hosted Qwen/MedGemma v10/audit-v9 screen | FAILED | Run 44037072649, artifact 14308901197; both models completed 12/12, but Qwen had 4 integrity findings and MedGemma 18; bounded acceptance failed. Raw outputs preserved; independent review remains outstanding. |
| Hosted Qwen/MedGemma v11/audit-v10 screen | FAILED | Run 44040631649; artifact 14310935167; Qwen 12/12, 4 findings in 2 cases; MedGemma 12/12, 18 findings in 6 cases. Both PENDING_HUMAN_REVIEW; bounded acceptance failed. Hosted CPU only; GPU NOT_PERFORMED. |
| Hosted Qwen/MedGemma v12/audit-v11 screen | IN PROGRESS | Run 44045424408 on trigger SHA eb75b076459a4f5da62758b631c59ca2fef1232f. HAI-DEF gate passed; combined Ollama provisioning/inference active; Qwen first then MedGemma after Qwen gate. No outputs/artifact yet. Hosted CPU only; GPU NOT_PERFORMED. |
| Current full 45-role R1–R4 validation | NOT STARTED | No fresh complete model execution accepted. |
| Historical full 45-role run-9 acceptance | FAILED | Audit found 343 integrity findings; originals preserved. |
| MedGemma HAI-DEF pre-provision gate | VERIFIED | Previously accepted personally by user; v10 gate passed. New workflow retains same gate. |
| Independent blinded model-output review | NOT STARTED | v10 outputs preserved; blinded review not yet completed. |
| Guideline retrieval and verification | NOT STARTED | No current verified authoritative source set integrated. |
| Independent qualified clinical review | NOT STARTED | No signed/attributable clinical review artifact. |
| Packaging prerequisites | VERIFIED | Run 44040195720 passed. |
| Windows installer | VERIFIED | PR installer 44040195512 and push installer 44040185771 passed build/install/smoke/upload. |
| Security, dependency audit and CodeQL | VERIFIED | Run 44040195526 passed. |
| Release acceptance | BLOCKED | Full-run integrity, model adherence, clinical review, guideline/evidence and GPU gates outstanding. |

## Immediate next actions

1. Continue monitoring workflow 44040631649 on trigger SHA 07548081f2b41ee1ed9db652e78156e2b65cc9be; do not launch a competing run. Inspect its exact manifest, model digests, 12 outputs per model, completion reasons, token metrics, normalization records and deterministic flags when the immutable artifact is published.
2. Specifically verify R2 partial agreement (information sufficiency independent of treatment), R2 conditional option labels, R3 narrative/structured identifier consistency, fabricated-quote rejection, and R4 echo detection.
3. If Qwen exits non-zero, MedGemma must remain NOT_REQUESTED. If Qwen completes but integrity flags remain, preserve them and do not call the model a pass.
4. Arrange independent blinded review of all v10 and v11 raw outputs before model promotion.
5. After bounded screening acceptance, plan a fresh full 45-role R1–R4 run with missing/failed-agent tests.
6. Complete local RTX 4060 request-time telemetry, authoritative guideline retrieval and independent qualified clinical review.

**Cloud/device boundary:** GitHub development, CI, installer and hosted CPU model screens do not require the user's PC online. Only local RTX 4060 request-time inference proof requires it powered on. Hosted model screens do not establish GPU performance or clinical validity.

---

## Mission Control phase 1 and phase 2 — VERIFIED (bounded scope)

**Phase 1:** read-only recent-run overview sourced from saved SQLite R1–R4 state, deterministic counts, progress, run timestamps and case-snapshot hash prefix. It excludes raw case text and model prose.

**Phase 2:** read-only per-role drill-down:
- Endpoint: `GET /api/mission-control/{run_id}/rounds/{round_number}/roles`.
- Exposes role ID/name/category, persisted status, start/completion timestamps and duration only.
- Expected roles derive from the server-side catalogue. R1/R2/R3 show 45 roles; R4 shows only Chair `SG-07`.
- Uncreated rounds are `not_started`; absent rows in an existing round are `missing_record`; failed roles remain failed.
- The UI provides per-round expand/collapse and manual role-status refresh. The endpoint excludes patient/case text, generated contributions and raw error messages.
- No agent starts/retries, automatic decisions, DB schema migration, model inference, agent-to-agent messaging or concurrency changes were introduced.

## Latest application/test commit CI — `51cdbea` (documentation-only follow-on)

All six standard PR workflows passed on this exact SHA:
- Backend Tests [43917157450](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157450): **400 passed, 0 failed, 0 errors, 0 skipped; 1 warning**. Deterministic preflight: **7/7 passed**.
- Frontend Build [43917157432](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157432): type-check and production build passed.
- Browser E2E [43917157793](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157793): passed. Logs contain `PATIENT_REGISTRY_BROWSER_E2E_OK`, `MISSION_CONTROL_BROWSER_E2E_OK`, `MISSION_CONTROL_ROLE_DRILLDOWN_E2E_OK` and `FOUR_ROUND_DASHBOARD_BROWSER_E2E_OK`. Headless Edge verified R2 shows 45 metadata-only role rows and R4 shows only the completed Chair SG-07 role. Artifact [14250421643](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157793/artifacts/14250421643). No model inference was invoked.
- Packaging prerequisites [43917157442](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157442): success.
- Windows Installer [43917157498](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157498): build, install, smoke test, checksum and upload succeeded. Optional Ollama/model bootstrap was **skipped**.
- Security and Dependency Audit [43917157444](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157444): full-history secret scan, dependency audit, Python CodeQL and JavaScript/TypeScript CodeQL all succeeded.

## Corrected E2E failure history — retained

The initial targeted browser attempt [43916746386](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43916746386) retrieved 45 R2 rows and rendered RO-01 as uppercase `COMPLETED`, but the new test compared case-sensitively against lowercase `completed`. The assertion was corrected to compare status text case-insensitively. Corrected E2E [43917157793](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43917157793) passed with the explicit role-drill-down marker. The historical failed attempt remains recorded and is not treated as a pass.

## Verification boundary

Mission Control phase 1 and 2 are **VERIFIED** for the read-only operational overview, role metadata states and seeded browser-rendering scope. This does **not** establish live Ollama model reliability, clinical accuracy, guideline concordance, clinical safety or GPU inference. No live 45-role Ollama simulation was run. The optional installer workflow model bootstrap was skipped. No local laptop sync/runtime reload, RTX 4060 request-time GPU measurement or clinical validation is claimed.

**Next development priority:** resolve outstanding P0 clinical data provenance, unsupported TNM/staging and full-run integrity findings before expanding orchestration. Mission Control is not authority to introduce autonomous dispatch or alter the four-round algorithm.


## Mission Control phase-2 E2E correction history

The first targeted browser run [43916746386](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43916746386) failed in the newly added assertion after successfully retrieving all 45 R2 roles. The log showed RO-01 status rendered as uppercase `COMPLETED`; the test compared it case-sensitively with lowercase `completed`. This is a browser-test assertion defect, not an endpoint/data failure. The assertions are now case-insensitive. The original failed run remains recorded; the corrected E2E passed on 51cdbea with `MISSION_CONTROL_ROLE_DRILLDOWN_E2E_OK`.


## Mission Control phase 2 — per-role drill-down implementation

Added a read-only endpoint `GET /api/mission-control/{run_id}/rounds/{round_number}/roles` and frontend expansion controls on each R1–R4 round card. The response is restricted to role ID, role name, category, persisted status, start/completion timestamps and duration. It deliberately excludes all assessment/contribution content, raw error messages, case details and patient identifiers. Expected roles come from the server-side 45-role catalogue; R4 is restricted to Chair role `SG-07`. An uncreated R2/R3/R4 round is shown as `not_started`; an absent row after a round exists is shown as `missing_record`. Regression tests cover these states, failures, timing, R4 cardinality, invalid rounds and unknown runs. Targeted browser E2E assertions passed on `51cdbea2c0f42d758b8b7ab1fd2190d5c094bbb2`: R2 has 45 role rows and R4 has one Chair row. Phase 2 is VERIFIED within the tested read-only metadata scope.


# Current Mission Control checkpoint — 16 November 2026

**Live repository state:** Development branch `feature/four-round-mdt-and-performance`, current application/test commit `7674f35c349bf290bbcce31f5b744176b5c5b25a`. PR #1 remains open, draft and unmerged, targeting `main`. `main` remains `39a356b8eb09399aa2da1b9b9085965999f5105a` and is untouched. The Mission Control implementation and targeted browser assertion are on the development branch only.

## Mission Control phase 1 — VERIFIED

Read-only operational overview implemented:
- Backend `GET /api/mission-control?limit=12`, bounded to 1–50.
- Aggregates actual persisted SQLite R1–R4 stage summaries and computes counts from saved role rows.
- Returns run ID, status/timestamps, immutable case-snapshot SHA-256, progress and role-state counts. It omits raw case text, patient names, generated assessment/round prose and detailed error strings.
- Missing round rows display `not_started`; no missing agent outputs or completions are fabricated.
- Failures are separately counted and remain distinguishable from successful completions.
- Read-only React dashboard panel, manual refresh and five-second polling; existing case workspace, round controls and Chair synthesis paths are unchanged.
- No autonomous agent framework, model-to-model messaging, LLM calls, DB schema changes or concurrency increases.

## Exact corrected-commit verification — `7674f35`

All six standard PR workflows completed successfully on this exact source SHA:
- Backend Tests [43901312982](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901312982): **395 passed, 0 failed, 0 errors, 0 skipped; 1 warning**. Deterministic preflight **7/7 passed**. New Mission Control API tests are included. No inference or clinical accuracy was evaluated by this suite.
- Frontend Build [43901313184](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901313184): type-check and production build passed.
- Browser E2E [43901312963](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901312963): passed in headless Edge. Log contains `MISSION_CONTROL_BROWSER_E2E_OK`, `FOUR_ROUND_DASHBOARD_BROWSER_E2E_OK` and `PATIENT_REGISTRY_BROWSER_E2E_OK`. The seeded run appeared in the Mission Control panel with **R1 45/45, R2 45/45, R3 45/45 and Chair R4 1/1**, and displayed the case snapshot hash prefix. Existing registry and saved Chair-report rendering checks also passed. No model inference was invoked.
- Packaging prerequisites [43901312883](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901312883): success.
- Windows Installer Build [43901312862](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901312862): installer build, install, smoke test, checksum and upload succeeded. Optional clean-hosted Ollama/model bootstrap was **skipped**.
- Security and Dependency Audit [43901312877](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43901312877): secret scan, dependency checks, Python and JavaScript/TypeScript CodeQL all succeeded.

## Corrected-test failure history — retained

- Initial direct Mission Control E2E attempt on `3caee960deacb28040c27e03dd186811a72ec195` failed because the new browser assertion double-serialized the seeded run ID. The browser test code was corrected in `7674f35c349bf290bbcce31f5b744176b5c5b25a`.
- The corrected browser E2E on `7674f35` passed with the explicit Mission Control success marker and four-round role counts above. The historical failed run [43900803448](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900803448) remains recorded; it is not represented as a successful run.

## Verification boundary and next phase

Mission Control phase 1 is **VERIFIED** for the bounded read-only summary and seeded browser-rendering scope. This does not establish live model reliability, clinical safety, guideline concordance, RTX 4060 inference, or release acceptance. The new dashboard has not been validated against a live Ollama 45-role simulation. No local laptop sync or runtime reload is claimed.

**Next planned phase 2:** per-role operational drill-down from persisted records (R1–R4), showing role ID/name/category, queued/running/completed/failed state, persisted timing, and clear not-started states. This should use a separate minimal read-only endpoint and avoid returning case text, model prose or raw error messages. Add tests for all four rounds and role failure/missing states before UI expansion. Phase 2 is **NOT STARTED**. No orchestration changes are authorised or implied.

## Historical Master Checklist snapshot — superseded 17 November 2026

| Workstream | Status | Current evidence / limitation |
|---|---|---|
| R1–R4 architecture and data flow | IN PROGRESS | Four-round structure exists; representative full live acceptance remains outstanding |
| Clinical safety and staging integrity | IN PROGRESS | Historical unsupported TNM and integrity findings remain open |
| Case integrity and audit history | VERIFIED | Historical DB integrity check only; full-run quality acceptance failed |
| Provenance and evidence retrieval | IN PROGRESS | Provenance issues and guideline retrieval remain unresolved |
| Chair consensus, dissent and traceability | IN PROGRESS | Historical run #9 failed integrity gate; current live 45-role reconciliation unverified |
| Missing/failed-agent handling | IN PROGRESS | Deterministic paths covered in tests; current complete live simulation outstanding |
| Backend tests | VERIFIED | 400 passed, 0 failed on application/test SHA a8ccaae; deterministic preflight 7/7 |
| Frontend and dashboard build | VERIFIED | Type-check, frontend tests and production build passed on application/test SHA a8ccaae |
| Browser E2E | VERIFIED | Headless Edge run 43923437915 on a8ccaae; five success markers including DEVELOPMENT_MONITOR_BROWSER_E2E_OK; R2 45 roles/R4 SG-07 verified |
| API validation | IN PROGRESS | Mission Control endpoint regressions passed; full API/live surface not fully verified |
| Ollama context handling | VERIFIED | 6,144/8,192 allocation probe only; no proof of full R3 truncation resolution |
| Ollama performance and concurrency | IN PROGRESS | Concurrency 1 retained; repeatable comparative metrics incomplete |
| RTX 4060 request-time GPU verification | NOT STARTED | No current measured inference-time GPU/offload proof |
| Hosted bounded R2/R3/R4 validation | FAILED | Run 43866946205 failed at combined bootstrap/live-validation step |
| Historical full 45-role acceptance | FAILED | Audit-only validation found 343 integrity entries |
| Qwen 12-case synthetic screens | VERIFIED | Execution/digest verification only; human review pending, no quality/clinical pass |
| MedGemma HAI-DEF acceptance statement | VERIFIED | User confirmation recorded; not independent legal advice |
| MedGemma workflow dispatch | IN PROGRESS | No connected dispatch/write capability for workflow_dispatch |
| MedGemma pull and inference | BLOCKED | Dispatch not performed |
| Independent qualified clinical review | NOT STARTED | No formal qualified review artefact |
| Guideline retrieval and verification | NOT STARTED | No validated source-retrieval corpus |
| Packaging and security CI | VERIFIED | Installer build/install/smoke/checksum, prerequisites, secret scan, dependency audit and both CodeQL jobs passed on a8ccaae; model bootstrap skipped |
| Mission Control phase 1 | VERIFIED | Read-only persisted summaries; six exact-commit CI workflows succeeded; direct E2E marker passed |
| Mission Control phase 2 role drill-down | VERIFIED | Role endpoint and per-round UI drill-down remain browser-verified; exact current dashboard E2E passed on a8ccaae |
| Mission Control development monitor | VERIFIED | Read-only GitHub PR/branch/Actions panel; explicit headless Edge marker on a8ccaae; six standard workflows passed |
| Paperclip third-party integration | NOT APPLICABLE | Reviewed as agent-operations control plane; not installed; native read-only monitor selected |
| Release acceptance | BLOCKED | Clinical, live-model, GPU and evidence gates remain outstanding |

---


## Mission Control phase-1 verification checkpoint — 16 November 2026

**Implementation commit:** `b063c52d7168194eb884d01b91dc1031fabb4e88` on the development branch added `GET /api/mission-control?limit=12`, deterministic persisted R1–R4 stage summaries, a read-only UI with five-second refresh, three backend regressions, and this checklist's phase-1 scope. No LLM calls, autonomous orchestration, schema changes, or concurrency changes were introduced.

**Exact-commit CI on `b063c52`:**
- Backend [43900046100](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900046100): **395 passed, 0 failed, 0 errors, 0 skipped; 1 warning**. Deterministic preflight: **7/7 passed**. This includes the three new Mission Control API regressions.
- Frontend [43900046020](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900046020): passed type-check and production build.
- Browser E2E [43900045851](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900045851): passed patient-registry and existing saved four-round Chair/dashboard checks. Artifact [14240648728](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900045851/artifacts/14240648728). **The initial E2E version did not explicitly assert the new Mission Control panel.** A targeted assertion is now added in the next commit and is awaiting its own E2E result.
- Packaging prerequisites [43900046180](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900046180): passed.
- Windows installer PR workflow [43900046099](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900046099): build, install, smoke test, checksum and upload passed; optional Ollama/model bootstrap was skipped. Push installer workflow [43900032529](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900032529) also passed; optional model bootstrap skipped.
- Security/dependency/CodeQL [43900045949](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43900045949): secret scan, dependency checks and both language CodeQL jobs passed.

**Acceptance boundary:** backend aggregation and UI type/build are CI-verified. The old browser E2E preserves existing functionality, but direct Mission Control rendering still requires the new targeted E2E. No local runtime verification, laptop sync, live Ollama inference, RTX 4060 GPU test, clinical validation, or release acceptance is claimed. Phase 1 remains **IN PROGRESS** pending the targeted browser run.


## Mission Control phase 1 — read-only persisted run overview

**Implementation scope:** add `GET /api/mission-control?limit=12` using the existing SQLite run and round tables; return only run ID, immutable case-snapshot hash, run timestamps/status, and deterministic role counts for R1–R4. Do not return raw case text, patient names, agent prose or error-body contents. Add a read-only frontend panel with recent runs, four-round completion/failure/queued/running counts, current role ID where persisted, snapshot-hash prefix and five-second polling. No run creation/resume/delete controls are added to this panel. Existing case workspace and R1→R4 controls remain unchanged.

**Safety boundary:** dashboard status is derived from persisted rows; missing R2/R3/R4 rows display `not_started`, not fabricated completion. Failed role counts remain visible and count as finished for progress, but never as completed. The endpoint is an operational summary, not a clinical validation result. It introduces no autonomous agent manager, no arbitrary agent-to-agent messaging, no new model calls and no concurrency change.

**Regression coverage added:** new `backend/tests/test_mission_control.py` checks no-case-text/no-prose response, default unstarted round states, 45/45/1 role denominators, persisted mixed R2 states, failed-role visibility, current role and query-limit rejection. Tests are pending CI execution; no test pass is claimed at commit time.

**Status:** Mission Control concept assessment — VERIFIED (concept only); Mission Control phase-1 implementation — IN PROGRESS until exact-commit CI and browser E2E complete. No laptop sync or local runtime verification is claimed.

# Current authoritative checkpoint — 16 November 2026 (supersedes stale branch/CI summaries below)

**Repository recheck:** `feature/four-round-mdt-and-performance` HEAD is the documentation-only checklist commit containing this checkpoint; its exact SHA is taken from the live branch ref during each report. The pre-refresh parent was `2061236c2177c142f53cda64f5729808392122fd`.. PR #1 is open, draft and unmerged, targeting `main`. `main` remains `39a356b8eb09399aa2da1b9b9085965999f5105a` and is untouched. This checkpoint is documentation-only; latest application/test commit remains `358bc1a2575318cb6c8509b090a34e9fae2a3c98`.

**Latest completed standard CI:** all six standard workflows completed successfully on the immediately preceding documentation-only head `fc332c8`. The pre-refresh documentation-only HEAD `2061236c2177c142f53cda64f5729808392122fd` had no associated GitHub Actions runs. This checkpoint is also documentation-only; no application code changed. The latest six successful standard workflows therefore remain those on `fc332c8`; do not imply exact-current-HEAD CI unless new runs are found:
- Backend Tests: [43888295808](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888295808) — success.
- Browser E2E: [43888295726](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888295726) — success.
- Windows Packaging Prerequisites: [43888296075](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888296075) — success.
- Frontend Build: [43888295679](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888295679) — success.
- Security and Dependency Audit: [43888295752](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888295752) — success.
- Windows Installer Build: [43888295671](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43888295671) — success.
These verify standard software/build/security workflows only; they do not establish successful live model inference, clinical validation, guideline concordance or GPU inference.

**Latest bounded live-validation failure:** [workflow 43866946205](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866946205) is terminal. Installer job succeeded; clean-hosted Windows Ollama/model-bootstrap/live-validation job failed at its combined provisioning/validation step. Preserve this failure. It is not a successful live validation.

**Reel review — AI-agent “Mission Control” pattern:** the newly supplied 65.88-second recording visibly demonstrates a central role/agent graph around a CEO-like node, status/activity panels, task/log activity and a workload/team graph. The reel caption says the creator's working style changed after hiring AI agents. The precise underlying product, orchestration framework, model, code, measured productivity and reliability are **not established by the recording**. This is a concept-level review, not product verification.

**Recommendation:** adopt the *bounded mission-control/observability concept for evaluation*, not an unrestricted autonomous-agent organisation and not an unverified third-party product. A RadOnc implementation should use a deterministic Run Controller as the orchestrator; specialist roles remain constrained tasks within the existing R1→R2→R3→R4 state machine. The Chair is the R4 synthesizer, not a CEO-style agent that can dispatch arbitrary clinical work or alter earlier saved contributions. The dashboard may show each role's queued/running/saved/failed/skipped state, round progress, timestamps, model/digest, token/time metrics, validation warnings, source links and immutable artifact history. The event/audit record—not the LLM or the dashboard—must remain the source of truth. R2/R3/R4 must consume only the correct persisted earlier-round records. Missing/failed work remains visible and blocks any claim of a complete review. Concurrency remains 1 unless measured tests justify otherwise. Human approvals remain necessary for sensitive actions; no automatic clinical decision or model promotion.

**Scope boundary:** no third-party Mission Control product has been identified or selected; no autonomous-agent framework has been installed; no architecture/code change has been made from this Reel. The proposed dashboard/orchestration refinement is **NOT STARTED** pending repository design review and a separate implementation decision. This pattern can improve operational visibility and accountability, but it does not itself prevent hallucinations, false consensus, unsupported staging or fabricated provenance.

## Historical Master Checklist snapshot — superseded 17 November 2026

| Workstream | Status | Evidence / boundary |
|---|---|---|
| R1–R4 architecture and data flow | IN PROGRESS | Existing implementation; live acceptance outstanding |
| Clinical safety and staging integrity | IN PROGRESS | Historical and bounded findings remain open |
| Case integrity and audit history | VERIFIED | Historical DB integrity only; full-run acceptance failed |
| Provenance and evidence retrieval | IN PROGRESS | Provenance findings and guideline retrieval remain open |
| Chair consensus, dissent and traceability | IN PROGRESS | Historical run has no proposition consensus; audit gate failed |
| Missing/failed-agent handling | IN PROGRESS | Must be revalidated in current live pipeline |
| Backend tests | VERIFIED | Latest completed backend workflow on prior documentation-only head `fc332c8`: 43888295808 succeeded |
| Frontend and dashboard build | VERIFIED | Latest completed frontend workflow on prior documentation-only head `fc332c8`: 43888295679 succeeded |
| Browser E2E | VERIFIED | Latest completed E2E workflow on prior documentation-only head `fc332c8`: 43888295726 succeeded |
| API validation | IN PROGRESS | Not all API/live cases verified |
| Ollama context handling | VERIFIED | 6,144/8,192 allocation probe only; does not prove no truncation |
| Ollama performance and concurrency | IN PROGRESS | Concurrency 1 retained; comparative performance evidence incomplete |
| RTX 4060 request-time GPU verification | NOT STARTED | No measured inference-time GPU proof |
| Hosted bounded R2/R3/R4 validation | FAILED | Workflow 43866946205 |
| Historical full 45-role acceptance | FAILED | Audit-only revalidation found 343 integrity entries |
| Qwen synthetic 12-case screens | VERIFIED | Execution/digest verification only; human review pending, no model pass |
| MedGemma HAI-DEF acceptance statement | VERIFIED | User statement recorded; not independent legal verification |
| MedGemma workflow dispatch | BLOCKED | No authorised workflow-dispatch action available in the connected GitHub tools |
| MedGemma pull and inference | BLOCKED | Requires successful authorised dispatch |
| MedGemma raw-output review | NOT STARTED | No MedGemma outputs |
| Independent qualified clinical review | NOT STARTED | No review evidence |
| Guideline retrieval and verification | NOT STARTED | No checked source corpus in current evidence |
| Packaging and security CI | VERIFIED | Latest completed workflows on prior documentation-only head `fc332c8`: 43888295671, 43888296075, 43888295752 succeeded |
| Mission-Control concept assessment | VERIFIED | Reel-level concept inspected; not a product or technical verification |
| Mission-Control architecture/design | NOT STARTED | Proposed only; no implementation authorised or committed |
| Release acceptance | BLOCKED | Clinical, live-model, GPU and evidence gates remain open |

---

## Historical MedGemma acceptance checkpoint — superseded 17 November 2026

**User acceptance recorded:** The user explicitly confirmed in this conversation: “I confirm that I have reviewed and accept Google's HAI-DEF Terms of Use personally, in my own legal capacity. Proceed with the synthetic-only MedGemma benchmark.” This records the user's statement; it is not independent legal verification or acceptance by the project on the user's behalf. Scope remains synthetic-only offline evaluation, with no patient data, clinical deployment, or model promotion.

**Current branch/PR/CI recheck:** Development branch head at review: `1476471e77c63247745aa94fe9418b5bcba23be7`. PR #1 remains open, draft and unmerged, targeting `main`; `main` remains `39a356b8eb09399aa2da1b9b9085965999f5105a`. All six standard PR workflows on `1476471` completed successfully: Backend `43868966242`, Packaging Prerequisites `43868966234`, Browser E2E `43868966126`, Security/Dependency `43868966042`, Windows Installer `43868966025`, Frontend `43868966105`.

**Previous hosted bounded validation:** Workflow [43866946205](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866946205) is now terminal. Installer job `133297818731` succeeded. Clean-hosted Windows Ollama/model-bootstrap job `133298583867` failed at its combined provisioning/live-validation step. The saved R2/R3/R4 provenance report upload step succeeded, but this does not mean the overall model-validation job passed. This run is no longer active and does not block a new run on concurrency grounds. Preserve its failure and inspect the report/logs separately.

**MedGemma workflow dispatch:** Workflow file `.github/workflows/model-integrity-screening.yml` (blob `c5902be287a9195f32109ebfc7243ff93c96bb28`) requires a manual `workflow_dispatch` with both `include_medgemma=true` and `hai_def_terms_accepted=true`. The configured GitHub integration in this session exposes read-only workflow retrieval and job/artifact inspection, but no workflow-dispatch/write action. Therefore no dispatch, model download, or inference has occurred. Do not substitute a push-triggered Qwen-only run or alter the workflow to bypass the explicit dispatch gate. **Next operational step:** use an authorised GitHub Actions workflow-dispatch capability to start this exact workflow on `feature/four-round-mdt-and-performance` with both booleans true; then record run ID, source SHA, Qwen and MedGemma full digests, Ollama version, corpus hash, all raw outputs/errors, manifest and artifact. The synthetic benchmark script remains configured for 12 cases, sequential concurrency 1, digest checks before/after each generation, and pending human review; it reports GPU measurement NOT_PERFORMED and clinical validation false.

**Updated MedGemma statuses:** HAI-DEF user acceptance statement — VERIFIED (statement recorded only); workflow dispatch — BLOCKED (no write/dispatch capability in connected GitHub tool); MedGemma pull/inference — BLOCKED pending dispatch; raw-output review — NOT STARTED; human/clinical review — NOT STARTED. No model promotion.

# Master Development and Verification Checklist

**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**PR:** [#1](https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1) — open, draft, unmerged; base `main`.  
**Current `main`:** `39a356b8eb09399aa2da1b9b9085965999f5105a` (untouched).  
**Branch-head tracking:** PR #1's live head is authoritative; documentation-only checklist commits also advance this development branch and trigger its standard PR workflows.  
**Latest verified application/test commit:** 358bc1a2575318cb6c8509b090a34e9fae2a3c98 (component-level R1/R2/R3 flagged-stage prompt redaction and stricter seeded integrity/whole-MDT positive-control acceptance; validation-script docstring updated). Six standard PR workflows passed on this exact application SHA: backend 392/392, preflight 7/7; frontend, Browser E2E, packaging, installer and Security/Dependency/CodeQL succeeded. Exact-head runs: Backend 43866956949, Frontend 43866957077, Browser E2E 43866956958 (superseded/cancelled), Packaging 43866956959, Installer 43866957094, Security 43866956960. Separate hosted model workflow 43866946205 remains active; standard PR CI does not cover its model inference.
**Latest branch head before this checklist refresh:** efc4bf140aa6d37a7ad05b44ba9247a9f849c12d (documentation-only checkpoint commit). All six standard PR workflows passed on this exact head: Backend 43867083075 (392/392, preflight 7/7), Frontend 43867083250, Browser E2E 43867083314, Packaging 43867083111, Installer 43867083149, Security 43867083132. PR #1 remains open/draft/unmerged; main remains untouched.

**Run #9 checkpoint audit:** audit-only workflow [43843343751](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43843343751), artifact [14213174048](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43843343751/artifacts/14213174048), report [RUN9_AUDIT_ONLY_REVALIDATION_43843343751.md](RUN9_AUDIT_ONLY_REVALIDATION_43843343751.md). It rechecked the original `c4592dbb-ecc7-4007-9125-d0baaed9abb0` 136-contribution run without Ollama or inference; saved R1/R2/R3 45/45 each, Chair R4 1/1, SQLite hash unchanged and integrity check OK. The corrected Chair count validator passed; the deterministic integrity gate then failed with **343 entries** (R1 11, R2 41, R3 271, R4 20). No original DB/report/artifact was changed. Run #9 remains failed acceptance.

**Synthetic Qwen screening — four runs complete:** v1 [43783994924](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783994924), v2 [43818887883](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43818887883), v3 [43833903911](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43833903911), and v4 [43836440298](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43836440298) each completed 12/12 response records on isolated hosted Windows CPU with the exact Qwen digest verified pre/post every generation. Artifacts: v1 `14188968641`; v2 `14202989381`; v3 `14210177854`; v4 `14211715869`; case-by-case reviews retained under `docs/QWEN_SCREENING_REVIEW_*.md`. V4 has zero deterministic reviewer flags in the bounded corpus, but all screens remain `completed_pending_human_review`; no automatic score, clinical validation or model promotion.

**Evidence limits:** all four model screens and the historical full run were CPU-only hosted Windows runs; no current RTX 4060 request-time GPU/offload proof. Independent qualified clinical review, guideline evidence retrieval, guideline concordance, full new live 45-role acceptance, and zero-hallucination assurance remain outstanding. MedGemma was not pulled. Official HAI-DEF Terms, Prohibited Use Policy and MedGemma 1.5 model card were reviewed on 16 November 2026. Synthetic-only offline development/evaluation appears within the published developer-use scope, subject to the restrictions below; acceptance by a legally capable person (and authority to bind any represented entity) is not recorded, so no pull/inference has occurred.
Statuses: **NOT STARTED**, **IN PROGRESS**, **BLOCKED**, **VERIFIED**, **FAILED**, **NOT APPLICABLE**. VERIFIED applies only to the stated scope and evidence.

## Qwen 12-case live output — preliminary integrity review (16 November 2026)

**Execution evidence:** Workflow [43783994924](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783994924), job `133027407524`, trigger/runtime commit `359fb69cd7c6b5f18d61d655fcf1a230a01b0ae1`. The isolated hosted Windows CPU runner provisioned pinned Ollama `0.40.14`, pulled `qwen3.5:4b` (Q4_K_M, 4.2B; 3,324,173,934 bytes), verified digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`, and recorded the same digest before and after every generation. Frozen corpus SHA-256: `5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3`. Twelve unique case IDs were recorded; each has `status=response_recorded`, `parse_error=null`; summary has 12/12, 0 failed/malformed, no automatic score, and `PENDING_HUMAN_REVIEW`. Ollama was stopped by verified isolated-process cleanup. CPU-only; GPU measurement explicitly `NOT_PERFORMED`.

**Immutable artifact:** [14188968641](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43783994924/artifacts/14188968641), 2,771,183 bytes, ZIP SHA-256 `84c3d2bdf419c85c4d9d628d63c83089f4d0df0af37112cd69492422e25494e7`. Manifest and raw/parsed JSONL were downloaded and inspected; source artifact remains unchanged.

**Preliminary behaviour audit (not a quality pass):**
- R1 unknown staging, unsupplied status, contradiction handling and prompt-injection cases: no definite critical fabrication observed; missing TNM/status remained unknown and the contradiction was not resolved.
- R2 false proposition consensus and limited shared agreement: no treatment consensus/unanimity was invented; distinct options and the limited data-needed agreement were retained.
- R2 conditionality: **PARTIAL REVIEW FINDING** — the response says prerequisite X is unknown and keeps Option A conditional, but also paraphrases MO-01 as claiming X is absent. The input says it is not present in the supplied record, while the explicit status is unknown; wording should distinguish “not documented” from “confirmed absent.”
- R3 invalid provenance: **PARTIAL REVIEW FINDING** — the response treats the unsupplied ID as missing and the range as unverified, but does not explicitly identify/reject the malformed range or state that raw invalid reference text must remain flagged. Server-side provenance validation remains essential.
- R3 negation: no reversal or positive contraindication was generated; the response treats the sentence as a meta-statement about the absence of peer claims. It could name the negated attribution structure more explicitly, but this is a wording caveat, not a demonstrated negation-reversal failure.
- R3 fabricated quote and R4 missing-agent/Chair traceability cases: no definite critical fabrication observed; the quote was rejected, the missing role was not fabricated, and the unsupported unanimity claim was rejected.

These are model-output observations from one deterministic-temperature run, not a blinded clinical review or a statistically reliable performance estimate. The full case-by-case engineering review, including response SHA-256 fingerprints, is recorded in [docs/QWEN_SCREENING_REVIEW_43783994924.md](QWEN_SCREENING_REVIEW_43783994924.md). No clinical accuracy, guideline concordance, live 45-role acceptance, GPU inference, or zero-hallucination guarantee is established. Required next steps: independently review all 12 outputs; correct and add positive/negative regressions for the R2 “not documented versus absent” distinction and exact raw malformed-range handling; then decide whether prompt/model changes and a repeat screen are needed. Keep all original records and findings immutable.

## Qwen v2 12-case live output — preliminary engineering review (16 November 2026)

**Execution:** [Workflow 43818887883](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43818887883), job `133137131770`, workflow source SHA `66947529e3b32c17b968fc4d4d361b621aa64df5`; isolated hosted Windows CPU runner, Ollama `0.40.14`, `qwen3.5:4b` Q4_K_M. Prompt version `radonc-mdt-integrity-screen-v2`; simulator screen run ID `702682a2-f645-4e7f-9dcb-9158dcd34f14`. Model digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` matched before and after all 12 generations. Frozen corpus SHA-256 `5fe333969035e403366272f6d3012809059d0be7ce1ce06efb16b6c6493fdeb3`. All 12 unique responses parsed; no failed/malformed records. Summary remains `completed_pending_human_review`, no automatic score, clinical accuracy false, GPU measurement not performed. Aggregate: 5,152 prompt tokens; 1,807 generated tokens; 268.561 seconds summed per-case wall time.

**Artifact:** [14202989381](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43818887883/artifacts/14202989381), 2,771,128 bytes; ZIP SHA-256 `666a01dbc6f1d1c9a2f322b7ff472ceaca972ff59d6bf0ba5db50d402d198257`. Full raw output hashes and case-by-case findings are in [QWEN_SCREENING_REVIEW_43818887883.md](QWEN_SCREENING_REVIEW_43818887883.md). The artifact was downloaded and all 12 raw responses reviewed; original data are unchanged.

**Observed v2 behaviour:** R2 conditionality explicitly distinguishes lack of documentation from a confirmed negative finding and retains conditional Option A. R3 explicitly rejects malformed `R2:RO-01-RO-09`; it recognises the “No peer claimed…” negation correctly. It still falsely labels supplied `R2:MO-01` malformed in the fabricated-quote case, treats a case ID as an external source identifier, refuses a bounded Chair summary despite three saved contributions, and uses awkward “record contains an absent field” wording for missing R1 fields. The fabricated MRI claim was rejected; no negative imaging result was invented. The R4 response rejects unsupported Option Z unanimity but fails to synthesize the actual saved R1/R2/R3 statements.

**Interpretation:** v2 is a completed synthetic engineering screen, not a quality pass. Two source/identifier classification errors and the R4 synthesis omission are material integrity findings. No definite clinical staging/result fabrication was observed in this limited sample, but absence of those findings in 12 cases is not a safety guarantee. Independent qualified review remains outstanding.

## Qwen v3/v4 synthetic screen sequence — completed review, 16 November 2026

### V3 review — [run 43833903911](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43833903911)

Prompt version `radonc-mdt-integrity-screen-v3`; screen ID `36e4c6fd-d53e-4352-8e11-d87d731a7959`; artifact [14210177854](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43833903911/artifacts/14210177854), ZIP SHA-256 `8aff02affa024925b7b501f39cc341d9bf4f8c5cdf2f117e489339366e623cc7`. Hosted Windows CPU-only, Ollama 0.40.14, Qwen digest verified pre/post every generation. 12/12 valid, 0 failed/malformed; 6,209 prompt and 1,467 generated tokens; 328.443 seconds summed wall time. It still produced an R2 unknown-but-unmet statement and cross-case R3 prompt contamination; one deterministic case-ID warning was a false positive. Full review: [QWEN_SCREENING_REVIEW_43833903911.md](QWEN_SCREENING_REVIEW_43833903911.md). One raw response fingerprint in that report was corrected against the downloaded immutable JSONL; artifact unchanged.

### V4 review — [run 43836440298](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43836440298)

Prompt version `radonc-mdt-integrity-screen-v4`; screen ID `3e804f9e-32be-44b0-aa3e-c34febdc1809`; artifact [14211715869](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43836440298/artifacts/14211715869), ZIP SHA-256 `b7499a24c26cdac5b6eb3fa81033ef375768e12b7c8b11e3b92d209eed8e823c`; JSONL SHA-256 `4d9c6c59774ecfdc0bb2217fcc91aa36dba6f3c39b43703a4f00402ab830ee3c`. Hosted Windows CPU-only, Ollama 0.40.14, Qwen digest verified pre/post every generation. 12/12 valid, 0 failed/malformed, 0 deterministic reviewer flags; 6,450 prompt and 1,215 generated tokens; 148.596 seconds summed wall time. In this small sample, R2 retains unknown prerequisite status and conditional support; R3 distinguishes malformed ranges and deliberately unsupplied IDs from supplied source IDs without expansion; the fabricated MRI quote remains unsupported; negation is retained; and R4 synthesizes saved contributions while rejecting unsupported Option Z unanimity. One wording caveat: R3 calls the unbound MRI claim a “contradiction”; it is unsupported by the saved source, not a verified source statement. Full review and fingerprints: [QWEN_SCREENING_REVIEW_43836440298.md](QWEN_SCREENING_REVIEW_43836440298.md).

### CI and decision boundary

V4 runner change: `2dab0d89562a0c1db54fec5563aaf71f8a84a711`; subsequent test-only prompt assertion updates: `00a72ec0e92bdbb53b89a1baa848e1d8f1ff1f66` and `8d78d6630cc6a19101088cd04b5f002b256b953f`. All six standard CI workflows subsequently passed on branch HEAD `0c3f5293110d8af0fe99066a40b97e099e7dcd82`: Backend 377/377 and preflight 7/7; Frontend, Browser E2E, Packaging Prerequisites, Windows Installer and Security/Dependency/CodeQL all succeeded.

**Interpretation:** V4 is the best result in this bounded 12-case prompt series. It is not a model-quality pass or clinical validation. These screens use reduced round-specific prompts, not the full production persisted 45-role pipeline. Independent qualified review and representative current-head live R1-R4 application validation remain outstanding. Qwen remains baseline; no model promotion. MedGemma terms review is complete for the stated synthetic-only offline evaluation scope; the model pull remains gated pending an authorised person’s acceptance of the Agreement and implementation of the stated use boundaries. No blanket separate commercial clearance is identified for local synthetic R&D by the published FAQ; redistribution/hosted-service and applicable regulatory duties remain to be assessed before those activities. No RTX 4060 request-time GPU evidence.
## Cross-round case-integrity audit-warning propagation — 16 November 2026

**Implementation:** `dd6a617ed1714dcdfa9dad77bc810fb922e72407`; test-only assertion correction: `fde2d02495cd05fa402c8b2822387fa8869d70d0`.

- R2 now receives the server-generated R1 `case_data_integrity_flags` for its own independent assessment and selected peer R1 assessments as separate `case_integrity_audit_flags` prompt metadata.
- R3 now receives its own R1 and R2 case-integrity flags, each selected peer's R2 case-integrity flags, and the selected peer's R1 flags joined server-side by role ID from the saved R1 records.
- Later-round instructions identify these as audit warnings, not new case facts or proof of the opposite finding. They tell the model not to repeat them as clinical facts, infer the opposite, or silently rewrite saved contributions. The immutable case remains the authority.
- The warning payload is bounded to the first six non-empty flags per source, each compacted to 220 characters. Full original contribution text and saved audit arrays are unchanged; this bounded prompt context is not a substitute for deterministic validation or Chair aggregation.
- Regression coverage: `test_r2_prompt_distinguishes_not_documented_from_clinically_absent` now verifies own/peer R1 warning delivery; `test_r3_receives_server_computed_peer_provenance_flags_and_exact_excerpt` verifies own/peer R1/R2 case warning delivery alongside provenance flags; `test_r3_peer_context_carries_r1_audit_flags_without_mutating_saved_r1` verifies server-side role mapping without mutating stored R1.
- Exact-head CI on `fde2d02`: Backend 380/380, deterministic preflight 7/7, and all six standard PR workflows passed (run IDs recorded above). The first `dd6a617` backend attempt failed only the stale prompt-boundary assertion; `fde2d02` corrected the assertion and the full backend suite passed.
- **Validation boundary:** this is implementation and regression-test evidence only. No Ollama inference, new live R2/R3 output, 45-role R1–R4 run, clinical accuracy review, RTX 4060 verification, or zero-hallucination assurance has been established. Historical run #9 remains immutable and its 343-entry quality gate remains FAILED.

## Hosted live-validation digest regression — 16 November 2026

**Current application/test commit:** `b9a61b90c3417e263cc4695584534e052cb651c7`.

- Failed hosted bounded-validation run [43849604050](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43849604050), artifact [14217006890](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43849604050/artifacts/14217006890), was downloaded and inspected. It records Ollama 0.40.14, Qwen `qwen3.5:4b`, exact 64-hex digest `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` in both `/api/tags` and `/api/ps`, and CPU-only execution (`size_vram=0`, CLI `100% CPU`). No generation calls occurred; rounds attempted/completed are empty.
- Root cause: the bounded validation helper `_require_installed_model_record` accepted only `sha256:<64 hex>`, despite Ollama returning a valid bare 64-hex digest. This repeated a digest-normalisation defect already corrected in the Qwen screening runner. It was not a missing digest, failed model pull, or model-quality result.
- Correction in `b9a61b9`: accept only bare 64-hex or optional `sha256:`-prefixed 64-hex, canonicalise to lowercase `sha256:<hex>`, preserve the original snapshot, and continue rejecting short/malformed/ambiguous records. Added regressions for the exact observed Qwen digest and uppercase bare/prefixed forms.
- Exact-head backend workflow [43850553847](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850553847): **385 passed, 0 failed, 0 errors, 0 skipped; 1 warning**; deterministic preflight **7/7 passed**. Frontend [43850553957](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850553957), Browser E2E [43850553945](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850553945), Packaging Prerequisites [43850554119](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850554119), and Security/Dependency/CodeQL [43850553989](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850553989) succeeded. The PR Windows Installer workflow [43850553913](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850553913) was still running at checklist update.
- Retry workflow [43850544644](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850544644), source commit `b9a61b9`, completed with `failed_quality_gates`, not an infrastructure failure. It successfully installed the packaged app, provisioned Ollama 0.40.14, pulled Qwen `qwen3.5:4b`, verified full digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`, and completed a CPU inference warm-up. Eight generation calls completed (R2 3, R3 3, separate R3 positive control 1, Chair R4 1); zero generation failures. Artifact [14218458120](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850544644/artifacts/14218458120) was downloaded and inspected. It reports four quality-gate findings: R2 SO-02 and MO-01, and R3 RO-01, repeat literal unsupported TNM values in attributed/rebuttal text and are conservatively flagged by the case-data scanner; the lexical model-output screen also incorrectly scans the Chair's server-authored quarantine metadata. Chair R4 structural validation itself PASSED (3/3 saved contributions per round, insufficient_information, no proposition-level consensus), and the separate unsupported whole-MDT consensus positive control PASSED. The original R1 quarantine warning was delivered to all own/peer R2 and R3 contexts. The failed acceptance is retained; it is not a model-quality pass.
- Acceptance scope is only the bounded three-role synthetic R2/R3 and Chair R4 check with one deliberately seeded unsupported R1 `cT1N0M0` statement and separate server audit warning. The deterministic lexical stage screen is narrow and is not a proof of absence of hallucinations or clinical validation. The 45-role live run remains gated.

## Current status

| Workstream | Status | Evidence and limits |
|---|---|---|
| R1–R4 architecture and persisted data flow | IN PROGRESS | Four-round architecture exists; fresh 45-role end-to-end acceptance outstanding. |
| R1 independent assessment and staging | IN PROGRESS | Unknown/staging safeguards tested; full-run review outstanding. |
| R2 debate, proposition agreement and conditionality | FAILED — MODEL ADHERENCE | Audit-v7 paired screen flags R2 conditionality omissions in both models and MedGemma false consensus across distinct conditional options. |
| R2 source provenance and exact row order | FAILED — MODEL ADHERENCE | Qwen rows out of saved order; MedGemma omitted exact source rows and source-specific positions. |
| R3 adversarial review and source provenance | FAILED — MODEL ADHERENCE | Both models copied exact source text but omitted explicit statement that fabricated quote was absent/unsupported; Qwen also omitted R3 identifier inventory. |
| R4 Chair synthesis, consensus and dissent | IN PROGRESS | Both models passed one no-treatment-proposition Chair scenario; full R4 acceptance outstanding. |
| Clinical safety and unsupported claims | IN PROGRESS | Deterministic controls exist; independent clinical review and broader model validation not complete. |
| Case integrity, contradictions and audit history | IN PROGRESS | Original data and 343 historical findings preserved. |
| Provenance and evidence traceability | IN PROGRESS | Audit-v7 exact R2 ledger/order checks pass software suite; models still fail them. |
| Missing/failed-agent handling | IN PROGRESS | Bounded missing-agent case covered; full 45-role failure injection outstanding. |
| Backend tests | VERIFIED | 437 passed, 0 failed/errors/skipped on SHA 90186c2. Run 44020149041; JUnit 14300457106. |
| Deterministic preflight | VERIFIED | Preflight artifact 14300053331; 7/7. |
| Frontend and dashboard build | VERIFIED | Run 44020148873 passed on exact SHA 90186c2. |
| Browser E2E | VERIFIED | Run 44020148938 passed on exact SHA 90186c2. |
| Dashboard/API validation | IN PROGRESS | Fixture-backed E2E passes; live GitHub public API remains subject to network/rate limits. |
| Ollama context handling | VERIFIED — BOUNDED | Historical context probes passed; no full-run generation guarantee. |
| Ollama performance and concurrency | IN PROGRESS | Concurrency 1, hosted CPU; no RTX 4060 inference telemetry. |
| RTX 4060 request-time GPU inference | NOT STARTED | Local Windows PC required during a real Ollama inference request and telemetry capture. |
| Prompt-v6/audit-v6 paired screen | VERIFIED — BOUNDED | Run 44011921822: Qwen 12/12, 0 flags; MedGemma 12/12, 4 flags. |
| Prompt-v7/audit-v6 paired screen | VERIFIED — BOUNDED / SUPERSEDED | Run 44015305202: Qwen 12/12, 2 flags; MedGemma 12/12, 3 flags. |
| Prompt-v8/audit-v6 paired screen | VERIFIED — BOUNDED | Run 44016121962: Qwen 12/12, 3 flags; MedGemma 12/12, 3 flags. |
| Prompt-v8/audit-v7 paired screen | VERIFIED — BOUNDED | Run 44018644704: Qwen 12/12, 5 flags; MedGemma 12/12, 6 flags. R2/R3 model adherence not accepted. |
| Audit-v7 deterministic reviewer | VERIFIED — SOFTWARE | Commit 91b7283; exact row coverage/order and incompatible-option consensus regressions pass Backend 437/437 on 90186c2. |
| Prompt-v8 R2/R3/R4 instructions | VERIFIED — CODE ONLY | R4 bounded example improved; material R2/R3 model failures persist. |
| Automatic model-screen commit trigger | VERIFIED | Marker commit 91b7283 triggered run 44018644704 automatically. |
| HAI-DEF terms gate | VERIFIED | Personal-capacity acceptance recorded; terms gate passed. Not independent legal advice. |
| Cloud execution independent of user's PC | VERIFIED | GitHub cloud workflows run without PC online; local GPU task separate. |
| Historical full 45-role acceptance | FAILED | Run 43843343751: 343 findings (R1 11, R2 41, R3 271, R4 20); original data unchanged. |
| Current full 45-role validation | NOT STARTED | No current-head full four-round acceptance passed. |
| Qwen model-output review | IN PROGRESS | 5 audit-v7 flags, independent blinded human review pending. |
| Qwen vs MedGemma model quality | IN PROGRESS | MedGemma 6 flags, false consensus and source-ledger omissions; neither model accepted. |
| Packaging prerequisites | VERIFIED | Run 44020149274 passed. |
| Windows installer | VERIFIED | PR Installer 44020148842 and Push Installer 44020142573 passed. |
| Security, dependency audit and CodeQL | VERIFIED | Run 44020148777 passed. |
| Guideline retrieval and verification | NOT STARTED | No verified current authoritative guideline set integrated. |
| Independent qualified clinical review | NOT STARTED | No review artifact. |
| Persistent continuity documentation | VERIFIED | Six supporting records maintained; this is the single detailed checklist. |
| Release acceptance | BLOCKED | R2/R3 model failures, historical 45-role failure, fresh run, GPU, guideline and clinical-review gates remain. |
| Authoritative repository checklist | VERIFIED | One current status table; historical dated entries retained as evidence. |


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
| AI-002 | Verify model licensing, commercial SaaS rights, acceptable-use terms, attribution, redistribution and hosting conditions for Qwen/Ollama and every alternative | IN PROGRESS | MedGemma HAI-DEF Terms, Prohibited Use Policy and model card reviewed on 16 Nov 2026 for synthetic-only offline evaluation; conditional scope assessment recorded in section S. No blanket commercial prohibition appears in the FAQ. Still assess the actual distribution/hosting architecture and applicable regulatory duties before model weights/derivatives are redistributed or model functionality is offered as a Hosted Service; other model/Ollama licensing review remains outstanding. |
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
| AI-021 | Evaluate Google MedGemma as a candidate specialist reasoning model against the current Qwen baseline; verify exact official model artefact/tag, digest, quantisation, Ollama compatibility and licence before use | IN PROGRESS | Google model ID/version and Ollama tag identified; exact digest, pull and runtime compatibility remain unverified. User's explicit personal-capacity HAI-DEF acceptance is recorded. This session lacks a GitHub Actions workflow-dispatch action, so the guarded MedGemma run has not started. Synthetic-only offline evaluation only; clinical use and hosted/redistributed deployment are not cleared. |
| AI-022 | Benchmark MedGemma on the frozen RadOnc MDT failure corpus, including unsupported TNM/staging, R2 false agreement, citation fabrication/ranges, R3 provenance, conditionality, missing data and failed-agent cases | IN PROGRESS | Frozen 12-case corpus and digest-gated sequential runner are implemented and CI-tested. Qwen v1-v4 screens exist; MedGemma has not been pulled or run because manual workflow dispatch is unavailable in this session. No paired comparison, independent review, RTX 4060 feasibility result or promotion decision exists. |
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
- MedGemma is governed by HAI-DEF Terms of Use; models are open-weight, not open-source. The official terms and prohibited-use policy have now been reviewed for the narrow synthetic-only offline evaluation use case. This is a scoped document assessment, not legal advice or acceptance on behalf of the user or an organisation. Distribution/Hosted Service and applicable regulatory requirements remain conditional future gates.
- Public Q4 package size/static weight footprint is approximately 3.3–3.4 GB, but runtime fit on the RTX 4060 8 GB is unverified; KV cache, context and runtime overhead are additional. Actual GPU activity requires request-time telemetry and Ollama offload evidence.

### HAI-DEF terms assessment — official-source review (16 November 2026)

**Sources checked:** [HAI-DEF Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms) (page states last modified 15 Nov 2024; footer updated 23 Nov 2024); [Prohibited Use Policy](https://developers.google.com/health-ai-developer-foundations/prohibited-use-policy) (last modified 14 Nov 2024; footer updated 23 Nov 2024); [MedGemma 1.5 model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card) (last updated 6 Nov 2026); [HAI-DEF FAQ](https://developers.google.com/health-ai-developer-foundations/faqs) (crawled/reviewed 16 Nov 2026).

1. **Development/evaluation permission:** the published terms permit use subject to the agreement and prohibited-use restrictions. The FAQ explicitly says HAI-DEF models may be used to develop commercial products subject to those terms. No blanket prohibition on controlled offline model evaluation with wholly synthetic cases was identified. This is a textual scope assessment, not a formal legal opinion.
2. **Clinical-use boundary:** the Terms define "Clinical Use" as use in diagnosis or treatment of patients, including as part of a research study. The present project scope is synthetic educational simulation only. Do not use real patient records or let MedGemma outputs inform diagnosis, patient management, treatment decisions or real MDT care. The Prohibited Use Policy bars illegal/unlicensed medical practice, misleading claims of medical expertise and automated decisions affecting healthcare rights/well-being; applicable law must also be followed.
3. **Model-card limitation directly relevant to this product:** MedGemma outputs are preliminary, require independent verification and clinical correlation, and are not intended to directly inform diagnosis, patient management or treatment recommendations. The model card also says MedGemma has not been evaluated or optimised for multi-turn applications. The simulator's sequential R1-R4 debates therefore require specific synthetic stress testing; no claim of model suitability or clinical reliability may be inferred from the model's medical training.
4. **Acceptance and authority:** the Agreement commences on acceptance, and acceptance includes use, modification or distribution. A person must have legal capacity. If using on behalf of a legal entity, that person represents they have authority to bind that entity. The project has not recorded such an acceptance/authority attestation; do not pull or run MedGemma until the authorised person knowingly accepts the terms and records the required project attestation.
5. **Risk allocation:** outputs are provided "AS IS"; the user/developer is responsible for determining appropriateness and subsequent output use. The terms include broad indemnification obligations (subject to applicable law) and California law / Santa Clara County exclusive venue language. These are material terms for the accepting person/entity to review.
6. **Redistribution and hosting:** if HAI-DEF or Model Derivatives are reproduced/distributed, Section 3.1 requires enforceable use restrictions in downstream agreements, notice to recipients, a copy of the Agreement, prominent notices on modified files, a Notice file for non-Hosted-Service distribution, and Health Regulatory Authorization when applicable. The defined Distribution also includes making model functionality available as a Hosted Service. The current proposed benchmark does not bundle or redistribute weights/derivatives and is not a hosted model service; reassess before packaging weights/derivatives, distilling another model from MedGemma, or exposing MedGemma inference remotely.
7. **Scoped decision:** **CONDITIONAL GO** for isolated synthetic-only offline benchmarking after authorised acceptance/attestation and with the controls above. **NO-GO** for real-patient diagnosis/treatment use, automated clinical decisions, or allowing outputs to inform actual patient care. This review does not clear commercial/hosted redistribution, regulated deployment, patient-data processing, or clinical validation.

### Next controlled sequence
1. Freeze the Qwen baseline full digest and MedGemma full local digest in the same Ollama environment.
2. Review the 12-case synthetic software-integrity corpus and its structural test; this is not a clinical gold-standard dataset.
3. Conduct sequential, bounded candidate screening at concurrency 1, preserving immutable outputs and error records.
4. Apply deterministic source, schema, missing-data, conditionality, consensus and Chair integrity checks.
5. Obtain blinded independent clinical review before any wider live workflow.
6. Proceed to representative-role and full 136-contribution runs only if the critical gate is clean and runtime/legal prerequisites are met.

**Zero-hallucination requirement:** Zero tolerance for any detected critical fabrication during evaluation. No finite test corpus can prove that a generative model will never hallucinate. Do not claim absolute zero hallucinations; design the application so unverified model claims cannot become accepted facts or untraceable Chair conclusions, and fail closed on detected integrity failures.

**Current status:** model identity/tag and documented limitations verified; 12-case synthetic corpus, digest-gated paired-screening harness, strict output envelope, immutable artefact handling and raw-response preservation VERIFIED by exact-head CI on `a9415b5` (348 backend tests; six workflows pass). HAI-DEF terms reviewed for synthetic-only offline evaluation; authorised acceptance NOT RECORDED. Full local digest NOT STARTED; MedGemma pull BLOCKED pending acceptance; live Qwen/MedGemma screening NOT STARTED; RTX 4060 inference verification NOT STARTED; independent clinical validation NOT STARTED.

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

## Resume checkpoint — hosted seeded case-integrity validation (16 November 2026)

**Repository state rechecked:** PR #1 remains open/draft/unmerged, targeting `main`; `main` remains `39a356b8eb09399aa2da1b9b9085965999f5105a`. Branch head at checkpoint: `3cd95b479a3467ddf4ed89d680c03ba7533bd331`. No changes to `main`, no merge, no force-push.

**Latest exact-head CI evidence:** all six standard workflows passed on documentation-only head `3cd95b4`. Backend: 385/385, 0 failures/errors/skips, 1 warning; deterministic preflight 7/7. Browser E2E, frontend build, packaging prerequisites, installer build/smoke, security/dependency audit and both CodeQL analyses succeeded. The standard installer run's optional hosted Ollama bootstrap was skipped; it is distinct from the marker-qualified validation job below.

**Digest correction:** application/test commit `b9a61b90c3417e263cc4695584534e052cb651c7` accepts only full 64-hex SHA-256 digests, with optional `sha256:` prefix; canonicalises to lowercase `sha256:<hex>`; preserves raw digest for audit; rejects short/malformed IDs. Backend exact-head CI on that application commit passed 385 tests and preflight 7/7. The failed preceding run [43849604050](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43849604050), artifact [14217006890](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43849604050/artifacts/14217006890), remains preserved: bare full digest was returned by Ollama; validator rejected only its representation; zero R2/R3/R4 generation calls occurred.

**Current live retry:** [workflow 43850544644](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850544644), job `133242264903`, runs the bounded three-role synthetic validation with one deliberately seeded unsupported R1 `cT1N0M0` assertion and separate server audit flag. GitHub last reported the job `in_progress` at its combined clean-hosted install/provision/inference step; setup, Python/dependencies and installer download completed. The next two steps (context allocation probe upload and representative R2/R3/R4 Chair provenance report upload) remain pending. There is no verified evidence yet that the digest preflight cleared, that any generation call occurred, or that the seeded warning reached generated rounds. Logs and final artifacts must be retrieved after the combined step exits. Do not start a competing hosted model run while this run is still active; if it remains stale, first inspect workflow timeout and runner state, then make an explicit evidence-based decision to cancel/retry.

### Historical checklist snapshot — 16 November 2026 (superseded)

| Workstream | Status | Evidence / boundary |
|---|---|---|
| R1–R4 architecture and persisted data flow | IN PROGRESS | Four-round storage/orchestration and Chair reconciliation exist; historical 45-role integrity failure remains unresolved. |
| R1 independent assessments and unknown staging | IN PROGRESS | Deterministic case-integrity audit and prompt safeguards exist; historical six unqualified full-stage assertions remain quarantined. No new 45-role R1 regeneration has been accepted. |
| R2 debate, source fidelity and conditionality | IN PROGRESS | Source-specific flagged-stage redaction and warning propagation have regression coverage; new live-model adherence remains unverified. |
| R3 adversarial review and source provenance | IN PROGRESS | R1/R2 flag redaction, provenance checks and stricter false-consensus positive control have regression coverage; live-model adherence remains unverified. |
| R4 Chair synthesis and saved-contribution traceability | FAILED | Historical run #9 integrity gate has 343 findings. The later bounded Chair reload was structurally successful but overall seeded model validation failed; a new live acceptance run is still required. |
| Clinical safety, staging and unsupported claims | IN PROGRESS | Deterministic gates and prompt safeguards are implemented; no zero-hallucination assurance, clinical validation or guideline concordance is claimed. |
| Contradictions, missing data and unknowns | IN PROGRESS | Unknown remains unknown and contradiction warnings are preserved; new live 45-role behaviour has not been revalidated. |
| Case data, hashes, run IDs, timestamps and immutable audit | VERIFIED | Historical run #9 database hash and SQLite integrity check were unchanged; new prompt redaction tests verify input dictionaries are not mutated. |
| Provenance, source IDs, consensus and dissent | IN PROGRESS | Deterministic source/role checks and no-consensus reconciliation are tested; live model adherence to the strengthened positive control remains unverified. |
| Missing/failed agent handling | IN PROGRESS | Existing failure-handling tests remain; no new full live failure-injection run has been completed. |
| Prompt-only flagged-stage redaction | VERIFIED | Exact-head backend tests cover R2/R3/R4 prompt views, preservation of saved inputs, and partial redaction that retains unflagged TNM components. This is software evidence, not model-behaviour evidence. |
| Backend tests | VERIFIED | Exact head 5cec1b3: 392 passed, 0 failed, 0 errors, 0 skipped; workflow [43866040873](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040873); preflight 7/7. JUnit diagnostics artifact 14225536830; preflight artifact 14225551766. |
| Frontend build and dashboard/API | VERIFIED | Frontend [43866040955](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040955) and Browser E2E [43866040828](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040828) passed on exact head. A dedicated refresh-flicker investigation remains IN PROGRESS. |
| Browser E2E | VERIFIED | Exact-head real-browser registry and saved MDT dashboard workflow [43866040828](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040828) succeeded; this is not a 45-role clinical simulation. |
| Ollama model identity and digest handling | VERIFIED | Full-digest validation/canonicalisation has regression coverage and prior exact hosted-runtime digest evidence; the current prompt-redaction validation run has not yet been triggered. |
| Ollama context allocation | VERIFIED | Historical context probe allocated 6,144 and 8,192 contexts; this does not prove absence of truncation during a full 45-role run. |
| Ollama concurrency, latency and request-time GPU/offload | IN PROGRESS | Concurrency remains 1. Historical seeded run was CPU-only; no request-time RTX 4060 telemetry or GPU offload proof. |
| New hosted seeded R2/R3/R4 validation | IN PROGRESS | Push workflow [43866946205](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866946205) on source commit 358bc1a; installer prerequisite job 133297818731 succeeded. Clean-hosted model job 133298583867 remains IN PROGRESS in `Install on a clean hosted VM and verify real Ollama/model provisioning`; no verified digest, generation count, model output or validation artefact yet. |
| Historical 45-role live acceptance | FAILED | Run #9 audit-only revalidation [43843343751](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43843343751): 343 integrity findings (R1 11, R2 41, R3 271, Chair R4 20). Original rows, report and database remain preserved. |
| Synthetic Qwen v1–v4 screening | VERIFIED | Four hosted CPU executions each recorded 12/12 response records and matching model digest; all remain pending human review and are not model promotion or clinical validation. |
| MedGemma inference | IN PROGRESS | User's explicit personal-capacity HAI-DEF acceptance is recorded in the 16 Nov 2026 checkpoint. Model remains unpulled: this session's GitHub connector has no Actions workflow-dispatch/write action. Do not bypass the workflow's manual-dispatch gate. Clinical use remains prohibited/out of scope; evaluation is synthetic-only. |
| Guideline evidence retrieval and verification | NOT STARTED | No retrieved-and-checked current guideline evidence is connected to the simulator. |
| Independent qualified clinical review | NOT STARTED | Required before any clinical-quality acceptance. |
| Security, dependency audit and CodeQL | VERIFIED | Exact branch-head workflow [43867759450](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43867759450) passed on `1706869977724319d777a4623c48aef860d87557`. |
| Packaging and Windows installer | VERIFIED | Exact branch-head packaging prerequisites [43867759142](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43867759142) and installer [43867759318](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43867759318) succeeded on `1706869977724319d777a4623c48aef860d87557`. Separate push workflow 43866946205 still has its hosted Ollama/model bootstrap job running. |
| Release acceptance | BLOCKED | Historical integrity failure, new live validation, evidence retrieval, clinical review, GPU verification and product governance gates remain outstanding. |

**Next action:** monitor only push workflow [43866946205](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866946205), triggered from source commit 358bc1a with concurrency 1. The installer build prerequisite is still running; the hosted model job and inference are not yet confirmed as started. Once the workflow completes, inspect all eight generation calls, R2/R3/R4 literal-repeat findings, Chair saved-input reconciliation, the stricter whole-MDT positive control, saved artefacts and CPU/GPU telemetry. Do not alter historical records or start a second overlapping hosted model run.


## Hosted seeded TNM-warning validation — failure analysis and corrective retry (16 November 2026)

**Failed live run:** [43850544644](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850544644), job `133242264903`, artifact [14218458120](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43850544644/artifacts/14218458120). The artifact was downloaded and inspected. Ollama 0.40.14 and Qwen `qwen3.5:4b` were installed on a clean hosted Windows VM; full digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` verified. CPU warm-up inference succeeded; GPU measurement was not performed.

**Actual generation:** 8/8 calls completed, 0 failed: R2 three roles, R3 three roles, a separate R3 whole-MDT consensus positive control, and Chair R4. Aggregate generation wall time 1059.938 seconds. R1 was deterministic fixture input, not a live model call.

**Findings from the saved report:**
- R2 SO-02 and MO-01 repeated the exact seeded unsupported TNM value while explicitly attributing it to R1 and describing it as unsupported/unverified. The existing deterministic case-data scanner conservatively flagged those literal values because it does not whitelist attributed quotations.
- R3 RO-01 also repeated the literal TNM value while describing it as an unsupported R1 assertion; the scanner flagged it. R3 SO-02 and MO-01 did not repeat the values.
- The additional lexical screen flagged the Chair's `case_data_integrity_flags` entry. That field is server-generated quarantine metadata, not model-authored clinical prose; this was a scope error in the validation screen.
- The R1 warning was delivered to all three roles in both R2 and R3 via own/selected-peer contexts. The separate R3 positive control detected and challenged the unsupported “entire 45-role MDT agrees” assertion.
- Chair R4 structural validation PASSED: it reloaded 3/3 R2 and 3/3 R3 saved roles, reported `insufficient_information`, no proposition-level consensus, and preserved the server audit warnings. Source-opinion coverage-integrity findings were empty. Overall workflow correctly FAILED because the round outputs still contained the literal unsupported stage values and the lexical screen misclassified the Chair audit field.

**Corrective application/test commit:** `2c3d35fc00df7ffd90fa6fceccf4876d815ba619`.
- R2 and R3 prompts now prohibit reproducing or quoting literal TNM/stage values from flagged assertions even when attributing or rebutting them; they must refer generically to “the flagged unsupported staging assertion”. This is stricter than merely attributing the value and reduces downstream repetition.
- The seeded-output lexical screen now excludes only server-authored audit metadata fields (`case_data_integrity_flags`, `source_reference_integrity_flags`, `integrity_repair_flags`, `integrity_repair_original_flags`) while continuing to scan model-authored text, including Chair prose. It does not weaken the production deterministic case-data audit.
- Added prompt regression assertions and a test proving that a server quarantine flag containing a TNM value is excluded, while an unqualified Chair conclusion containing a TNM value is still flagged.

**Exact-head software CI:** all six standard PR workflows passed on `2c3d35f`. Backend [43854315663](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315663): **386 passed, 0 failed, 0 errors, 0 skipped**, 1 warning; deterministic preflight **7/7 passed**, artifact `14220665983`. Frontend [43854315582](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315582), Browser E2E [43854315619](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315619), Packaging Prerequisites [43854315586](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315586), Windows Installer [43854315556](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315556), Security/Dependency/CodeQL [43854315595](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854315595), and push installer [43854303934](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854303934) succeeded.

**Next:** trigger one new marker-qualified clean-hosted bounded validation from this exact application/test commit. Inspect the full report, not just workflow status. Acceptance requires no literal unsupported TNM repetition in model-authored R2/R3/R4 prose, preserved R1 quarantine metadata, correct saved-contribution Chair reconciliation, positive/negative controls, and no new integrity failures. A pass remains a bounded engineering result, not clinical validation or proof of zero hallucinations.


### Completed hosted retry — marker commit dadf6bb (16 November 2026)

- Workflow [43854920258](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854920258) completed the installer build/smoke step and bounded hosted model validation. Model job: 133257565020; representative report artifact: [14221827825](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854920258/artifacts/14221827825).
- Eight generation calls completed: three R2, three R3, the separate whole-MDT positive control, and Chair R4. The run correctly FAILED its seeded integrity acceptance. R2 SO-02 and MO-01 repeated the flagged value; R3 RO-01 also repeated it. The output included unsupported values even while explaining they were unverified. Chair R4 successfully reloaded 3/3 R2 and 3/3 R3 saved rows, reported insufficient_information, and retained the audit warnings. Overall acceptance remained failed.
- The positive control exposed a detector gap: a valid source-bound challenge was present, but the model repeated the false whole-MDT agreement claim elsewhere in its response and was incorrectly counted as detected. The later deterministic gate now rejects repetition outside the qualifying challenge.
- The run was CPU-only. No request-time RTX 4060/GPU inference proof was collected. Preserve its report and failure; do not reinterpret it as a pass.

## Resume checkpoint — prompt redaction hardening and exact-head CI (16 November 2026)

**Commits on the development branch (all retained):**
- b33e2e657e99cc5c79316f9b3cd2abe98891f0ac — introduced source-specific prompt-view redaction for R2/R3/Chair, a literal flagged-stage repetition gate, a stricter whole-MDT positive-control acceptance check, and regression tests.
- 2851ddb7867fcb774e8a957b3ae5f18a775999d3 — updated existing prompt tests to expect audit-flag identity and redaction rather than raw unsupported stage literals.
- 2d9c9c97c7c991e24f246aecb8257c1de63735cd — removed numeric staging examples from the common case-context prompt so the model is not re-exposed to the flagged tokens through generic guidance.
- 5cec1b3596beee66c85f8c32f354550a0342e801 — refined redaction to replace only flagged components of combined TNM expressions, preserving components not named by the audit flag.

**Prompt and data-integrity contract:** R1/R2/R3 saved records and server audit flags are not rewritten. Only prompt-display copies are redacted. R2 applies the originating R1 flags; R3 applies the relevant originating R1 and R2 flags to own and peer context; Chair R4 redacts its model-facing digest while deterministic reconciliation continues to consume the actual saved records. Component-level redaction must not hide unflagged T/N/M components. Regression coverage checks prompt redaction, no-op when there is no matching flag, partial-component preservation, and preservation of original input dictionaries.

**Deterministic acceptance strengthening:** the bounded seeded output audit now separately scans model-authored R2/R3/R4 prose for literal repetitions of the seeded stage components even when called unsupported; server-authored audit metadata remains excluded from model-authored prose scans. The whole-MDT positive control allows its exact source-bound challenge quote but fails if the same false claim is repeated outside that qualifying challenge. These are bounded lexical/provenance tests, not comprehensive hallucination detection.

**Exact-head software verification on 5cec1b3:** all six standard PR workflows succeeded:
- Backend [43866040873](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040873): 392 passed, 0 failed, 0 errors, 0 skipped; deterministic preflight 7/7. JUnit diagnostics artifact 14225536830; preflight artifact 14225551766.
- Frontend [43866040955](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040955) succeeded.
- Browser E2E [43866040828](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040828) succeeded.
- Windows packaging prerequisites [43866040822](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040822) succeeded.
- PR installer [43866040819](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040819) and push installer [43866031907](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866031907) built and smoke-tested successfully. Their optional hosted Ollama/model bootstrap jobs were skipped.
- Security/dependency/CodeQL [43866040821](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866040821) succeeded, including Python and JavaScript/TypeScript CodeQL, dependency audit and secret scan.

**Boundaries and outstanding work:** the exact-head CI on application/test commit 5cec1b3 verifies software behaviour only. The previous live model failure [43854920258](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43854920258) remains failed and immutable. A new bounded retry has been triggered as push workflow [43866946205](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43866946205) from marker commit 358bc1a; at this checklist update its installer prerequisite remains in progress and no model inference result is available. The run must inspect all eight calls, source-flag delivery, R2/R3/R4 saved contribution provenance, literal-repeat results, the stricter positive control, Chair reconciliation and artefact hashes. It is not clinical validation and cannot establish zero hallucinations. GPU/request-time offload, guideline retrieval, independent clinical review, MedGemma clearance and release gates remain outstanding.



## Historical resume checkpoint — superseded 17 November 2026

**Repository recheck:** PR #1 remains open/draft/unmerged, base main; development branch head before this checklist refresh was efc4bf140aa6d37a7ad05b44ba9247a9f849c12d. Main remains 39a356b8eb09399aa2da1b9b9085965999f5105a and has not been modified. Application/test SHA is 358bc1a2575318cb6c8509b090a34e9fae2a3c98; efc4bf1 is documentation-only.

**Latest exact-head CI:** six standard PR workflows passed on efc4bf1; backend 392/392 and preflight 7/7; frontend, real-browser E2E, packaging prerequisites, Windows installer smoke test, dependency audit, both CodeQL analyses and full-history secret scan succeeded. Software/build/security evidence only.

**Current live retry:** workflow 43866946205 is a push-triggered, marker-qualified clean-hosted Windows CPU validation from source SHA 358bc1a. Installer build/smoke job 133297818731 passed. Model bootstrap/inference job 133298583867 remains active in one combined provisioning/validation step. Setup, Python dependencies and installer download completed. No final job result, verified generation count, model output or audit artifact is available yet. Do not infer a hang from the combined step or launch a competing model run.

**Corrective software under test:** 358bc1a includes source-specific prompt redaction for flagged TNM components across R2/R3/Chair model views, preserving actual saved contributions and audit arrays; a deterministic model-authored-output repeat gate; and a stronger whole-MDT false-consensus positive control. Preceding live run 43854920258 failed: R2 SO-02/MO-01 and R3 RO-01 repeated seeded unsupported staging literals; Chair structurally reconciled 3/3 saved R2 and 3/3 saved R3 contributions but overall acceptance failed. Earlier failure 43850544644 also remains immutable.

**Next action:** monitor only job 133298583867 until completion. Retrieve complete logs and artifacts; verify model identity/digest, actual generation calls, R2/R3/R4 model-authored text for flagged-component repetition, warning propagation, Chair use of actual saved contributions, deterministic position/consensus counts, false-consensus positive control, failures and JSON/SQLite/report hashes. Record CPU-only telemetry as CPU-only; do not claim RTX 4060 GPU inference. If this bounded run fails, preserve artifacts, classify the failure and add targeted regressions before one new retry. Even a bounded pass is not full 45-role acceptance, clinical validation, guideline verification or zero-hallucination assurance.