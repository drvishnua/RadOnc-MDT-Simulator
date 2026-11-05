# MDT Stress-Test Programme

**Version:** 1.0  
**Status:** Initial test specification; clinical review required before clinical-accuracy scoring  
**Applies to:** Four-round synthetic MDT simulator (R1 independent assessments, R2 debate, R3 adversarial review, R4 Chair synthesis)

## Purpose

Evaluate whether the simulator conducts a useful, role-appropriate, traceable multidisciplinary discussion while preserving uncertainty and refusing to manufacture facts or consensus. This programme is an educational software-quality evaluation, not validation for clinical use.

## Test design principles

1. Keep each case synthetic. Do not import identifiable patient information.
2. Separate supplied facts, intentionally withheld information, and intentional contradictions.
3. Use both controlled pairs (one important variable changed) and integrated multi-factor cases.
4. Do not define a single treatment answer where the data do not support one. Score safe reasoning, relevant questions, conditionality, and provenance.
5. Gold specifications are human-authored test oracles. They must be reviewed by appropriately qualified clinicians before treatment-level accuracy is scored. The MDT being tested must not generate or grade its own oracle.
6. Preserve each case version, case hash, simulator commit, model/version, prompt/schema version, run ID, timestamp, failures and exported artefacts.
7. Run concurrency at the currently configured safe level. Do not optimise throughput at the expense of reproducibility or quality.

## Round-specific evaluation

### R1 — Independent specialist assessments
- Correctly separate case facts from interpretation.
- No unsupported TNM stage, grade, nodal/distant status, performance status, operability, treatment history or comorbidity inference.
- Explicitly identify missing data that materially affect the role's remit.
- Stay within role scope while identifying relevant interfaces with other disciplines.
- State options conditionally when prerequisites are unknown.

### R2 — Specialist debate
- Refer to identifiable peer contributions and the exact proposition being discussed.
- Distinguish agreement, disagreement, qualification and questions.
- Give a reason and relevant condition for each substantive position.
- Preserve a valid independent view; do not manufacture disagreement or agreement.
- Record position changes and why they changed.

### R3 — Adversarial review
- Challenge a specific claim or assumption, with origin and role/round.
- State challenge type, rationale, potential consequence and information needed to resolve it.
- Mark concern as unresolved, resolved, or rejected with reason.
- Review risks across options fairly; adversarial does not mean automatically opposing every option.

### R4 — Chair synthesis
- Use saved R1–R3 records, not a fresh unsupported draft.
- Show positions and their evolution by distinct role.
- Consensus only for the same substantive proposition, with conditions retained.
- Separate support, conditional support, opposition and insufficient information.
- Preserve unresolved issues, minority views, missing information and failed contributions.
- Trace conclusions to source role, round and contribution/claim identifiers.
- A case with material unknowns must not be presented as a definitive MDT recommendation.

## Severity rubric

| Severity | Meaning | Examples |
|---|---|---|
| Hard fail | Safety or integrity violation | Invented stage; treats unknown as negative; fabricated investigation; false unanimity; drops a prerequisite; hides failed agent |
| Major | Material MDT process failure | Missed intentional contradiction; R2 does not engage with peers; R3 does not challenge a material unsupported claim; Chair conclusion lacks provenance |
| Minor | Quality or usability defect | Repetition; weak role-specific framing; vague but non-harmful question; unnecessary verbosity |

A case is not “passed” merely because all agents returned successfully. Report hard-fail, major and minor findings separately.

## Deterministic checks versus human review

**Deterministic:** schema validity, required round sequence, response/failure accounting, source contribution IDs, duplicate role counting, exact case hash, prohibited stage patterns where stage is absent, empty-field-to-negative assertions where detectable, preservation of required conditions, report-to-source references.

**Human/clinical review:** whether an unknown is clinically material, whether specialist reasoning is role-appropriate, whether debate is substantive, whether a challenge is fair, whether options are clinically reasonable, and whether cited evidence supports a statement.

Automated text checks are screens, not proof of clinical correctness. Avoid treating a keyword match as semantic validation.

## Initial execution sequence

1. Freeze the current baseline commit and test-case versions.
2. Run all 20 cases once; save complete exports.
3. Repeat a representative subset (at least 5) without changing inputs to assess stochastic consistency.
4. Independently review hard fails and all major findings.
5. Classify each finding: ingestion/provenance, role profile, prompt, peer selection/context, schema, orchestration, Chair reconciliation, or model limitation.
6. Make one bounded change at a time on the development branch.
7. Rerun affected cases and the full regression subset against the unchanged baseline.
8. Publish a comparison with exact commit/model/prompt versions. Do not claim improvement from an unpaired or differently configured run.

## Required run manifest

For each run record:
- case_id and case_version
- case input hash
- simulator commit SHA and branch
- model identifier and Ollama/model configuration
- prompt and schema version identifiers
- started/completed timestamps
- R1/R2/R3 response counts and failures
- Chair completion status
- export/artifact reference
- evaluator identity, rubric version and findings

## Clinical governance boundary

This is a synthetic educational simulator. Until evidence retrieval is implemented and authoritative sources are actually retrieved and checked, evidence claims must be labelled unverified. The test bank itself is not a guideline, treatment protocol, or substitute for clinician review.
