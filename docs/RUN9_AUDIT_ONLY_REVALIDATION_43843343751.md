# Run #9 audit-only revalidation — saved four-round MDT checkpoint

**Audit date:** 16 November 2026  
**Repository:** `drvishnua/RadOnc-MDT-Simulator`  
**Branch:** `feature/four-round-mdt-and-performance`  
**Audit workflow:** [43843343751](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43843343751)  
**Audit source commit:** `fd4c39cf53b82a514aaa850e76f33d46798c4aff`  
**Audit artifact:** [14213174048](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43843343751/artifacts/14213174048)  
**Audit artifact ZIP SHA-256:** `06dee81413116848ca1477d67441ae6047d2128d4747b1e300fa7a24882cade4`  
**New audit JSON SHA-256:** `488285886f16ea928ff15888b172437144ec45a340cc688b141dc08b33f718fa`

## Lineage and immutability

The audit uses the exact immutable checkpoint artifact [14182277535](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255/artifacts/14182277535) produced by continuation run [43753957255](https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/43753957255).

- Original source run: `43714529807`, source SHA `4683b0767bf5cade408e85ec31ef248b34e5321e`.
- Checkpoint continuation run: `43753957255`, continuation SHA `28fd7eccfa0e32200eefb995158e8788b0296c97`.
- Simulator run ID: `c4592dbb-ecc7-4007-9125-d0baaed9abb0`.
- Frozen model identity: `qwen3.5:4b`, Q4_K_M, full digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
- Original checkpoint ZIP SHA-256: `1fc370307f84f802a7749c8dae78a0eba20289c409a54c87feca8b1fc86c79b6`.
- SQLite database SHA-256: `a38555f0a95ba0327941bd12f366479cfff2526d0c799ebbdeba68d50c97e6c0`.
- The previous run-9 report contained this same SQLite hash; the audit workflow verified the downloaded database against it before execution.
- `PRAGMA integrity_check`: `ok`. The re-audit recorded the same database SHA-256 before and after; `checkpoint_database_unchanged=true`.
- The original checkpoint and previous failed report were retained byte-for-byte. The new report and copied checkpoint are separate files in artifact `14213174048`.

## Audit execution

<badge>Audit-only — no inference</badge>

- `audit_only=true`; `inference_performed=false`.
- No Ollama process was provisioned or contacted; no model was pulled; no model generation occurred.
- The script completed deterministic validation in **0.13 seconds** after workflow setup.
- R1: 45/45 completed roles.
- R2: 45/45 completed roles.
- R3: 45/45 completed roles.
- Chair R4: one completed Chair report.
- Total saved contributions: **136**.
- R1, R2 and R3 position distributions each contain 45 `insufficient_information` positions; the saved Chair consensus status is `insufficient_information`.
- Structural role-count, round-completion, source-case snapshot, position-transition, Chair title/safety/evidence, consensus and Chair position-count checks ran to completion. In particular, the former “Chair synthesis omits R1 position counts” label-format failure no longer stops validation.

The workflow concluded **failure intentionally at the deterministic integrity quality gate**. The audit report status is `completed_with_quality_gate_failures`; `quality_gate_passed=false`. This is not a workflow provisioning failure and is not a model-quality pass.

## Deterministic integrity findings

<badge color="danger">Quality gate failed — 343 entries</badge>

| Saved round | Gate findings | Principal issue |
|---|---:|---|
| R1 | 11 | Unsupported T/N/M staging assertions |
| R2 | 41 | 40 role-range citation findings and one categorical contraindication statement |
| R3 | 271 | 269 source-reference findings and two unsupported clinical assertions |
| Chair R4 | 20 | Aggregated source/provenance and quarantined contribution findings |
| **Total** | **343** | **Integrity gate remains failed** |

These are deterministic gate entries, not 343 proven independent clinical errors; Chair R4 includes audit summaries/quarantines of upstream findings.

### R1 — 11 case-integrity findings across 7 roles

The case snapshot does not supply structured T, N or M stage. The saved R1 contributions nevertheless contain:
- T1 assertions by RO-01, RO-09, MO-06, SO-08, SG-03, SG-04 and SG-07.
- N0 and M0 assertions by RO-01 and SG-07.

RO-01 and SG-07 each trigger three findings (T1/N0/M0). These are unsupported stage claims and remain quarantined. No N0/M0 or T1 status may be treated as established.

### R2 — 41 findings

- **40 source-reference findings across 40/45 roles:** generated R2 prose contains role ranges such as `R1:MO-01 through R1:RO-04`, `R1:SO-01 through R1:MO-04`, `R1:DS-01 through R1:SO-04`, and similar ranges. These are not attributable individual source IDs. The original prose remains stored; the server audit flags it.
- **One case-integrity finding (MO-07):** the generated narrative categorically calls an option “contraindicated” despite missing information not establishing contraindication, safety or indication.

### R3 — 271 findings

- **269 source-reference/provenance findings across 27/45 roles**, broken down as:
  - 67 malformed or unsupported role-range citations.
  - 104 individual source identifiers not supplied to the contribution.
  - 78 invalid `CASE` source identifiers inside source-opinion reviews (the server expected `CASE:case_summary#N` identifiers).
  - 20 source-opinion reviews excluded because a server-bound case-summary opinion register was unavailable.
- **Two case-integrity findings (SO-06):**
  - staging/performance prerequisites described as unmet/not met without a matching documented assessment finding;
  - categorical “no option is indicated” assertion based on missing information.

The audit does not normalise ranges, invent intermediate roles, convert missing data into negative findings, or rewrite saved R3 contributions.

### Chair R4 — 20 aggregated/quarantined findings

The saved Chair output records, among other items:
- R2 source-reference audit: 40/45 distinct completed roles with 40 unique findings.
- R3 source-reference audit: 27/45 roles with 247 unique saved findings (269 raw R3 findings less repeated same-role findings).
- R3 exact-excerpt review problems: 16 findings across MO-08, SG-01, SO-06 and SV-03; one MO-08 `CASE:case_summary#1` review lacks an exact contiguous excerpt.
- R3 source-identifier audit: four findings from MO-01; invalid examples include `R2:SO-01`, `R2:DS-01` and `R2:PP-01`.
- Quarantined SO-04 positive model-authored consensus assertion because proposition-level consensus was not established.
- Quarantined SO-06 unmet-prerequisite assertion.
- Repeated quarantine findings for the R1 T1/N0/M0 assertions.

The Chair is not promoted to a valid clinical recommendation merely because its report and counts are structurally saved.

## Interpretation and next work

**What is verified:** the previously saved 136-contribution database is structurally intact; all R1/R2/R3/R4 rows are completed; the corrected deterministic validator now gets past the prior Chair count-label error; and the saved database was not modified by the audit.

**What failed:** the integrity quality gate has 343 findings. Unsupported staging, unsupported contraindication/negative-indication language, role-range/unsupplied source identifiers, invalid case-opinion IDs, source excerpt failures and quarantined Chair inputs remain.

**What this does not establish:** clinical accuracy, guideline concordance, independent clinical acceptance, statistical model reliability, zero hallucinations or GPU inference. The historical run was hosted CPU-only. This audit-only workflow performed no inference.

**Next development priorities:**
1. Resolve R1 staging assertions at generation/audit level without deleting or changing the historic records.
2. Strengthen R2 peer-source handling so model prose cannot substitute ranges or unprovided role identifiers for server-owned structured source IDs; preserve the original raw text and flags.
3. Correct R3 source-opinion boundaries: only server-bound `CASE:case_summary#N` opinions may enter that register; peer R2 IDs must remain peer references. Repair exact-excerpt binding and invalid source IDs.
4. Prevent unsupported “unmet”, “contraindicated” and “no option is indicated” assertions when prerequisite status is unknown.
5. Keep Chair R4 fail-closed and trace each aggregate/quarantine item to its actual R1-R3 saved contribution.

Do not modify the historical checkpoint to make it pass. After deterministic fixes and regression tests pass, a new, lineage-distinct full live validation is required to evaluate the changed application behavior. The run-9 audit result remains failed and immutable.
