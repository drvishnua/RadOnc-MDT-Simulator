# Product Specification — RadOnc MDT Simulator

## 1. Product purpose

RadOnc MDT Simulator is a local AI-assisted educational environment for synthetic oncology MDT discussions, initially focused on head-and-neck cancer cases. It helps learners examine specialty perspectives, patient realities, evidence quality, feasibility, ethics, uncertainty, and disagreement. It is not intended to make autonomous treatment decisions.

## 2. Intended users

- Radiation, medical, and surgical oncology trainees
- Oncology educators and MDT facilitators
- Researchers evaluating structured simulated MDT discussions

## 3. First-release boundaries

The first release accepts synthetic cases, runs all 45 configured perspectives, preserves independent opinions, records uncertainty and disagreement, and produces labeled educational reports. It must not accept identifiable patient data, connect to hospital/treatment-planning systems, create patient-specific prescriptions/doses/contours/plans, replace a qualified clinician or formal MDT, or present issue-spotting as professional advice.

## 4. Four-round workflow

### Round 1 — Independent assessments

All 45 configured agents receive the same immutable case snapshot and their own role profile, without seeing other agents' outputs. Every agent must provide:
- A position (supports, opposes, conditional, or insufficient information)
- A provisional conclusion
- A preferred educational option or why no option can yet be preferred
- Perspective summary, facts, assumptions, unknowns, discussion topics, evidence gaps, uncertainty, and confidence

### Round 2 — MDT debate

All 45 roles receive their own Round-1 output and a compact selection of cross-specialty peer views. Each records agreements, substantive challenges, and any position changes. Original Round-1 views are never overwritten.

### Round 3 — Adversarial review

All 45 roles challenge unsupported assumptions, overclaims, missing information, patient/context assumptions, feasibility, resources, safeguarding, governance, and medico-legal documentation issues. Challenges are specific and respectful; legal issue-spotting is not legal advice.

### Round 4 — Chair synthesis

The MDT Chair summarizes the complete stored discussion and review. The report requires:
- A consensus status (consensus, qualified consensus, no consensus, or insufficient information)
- A clear 2–4 sentence Chair conclusion
- Overall educational synthesis
- Consensus points, unresolved disagreements, and minority/dissenting views
- Major uncertainties and missing information
- Patient/family, feasibility/resource, governance/safeguarding considerations
- Evidence limitations and Chair reflection

No artificial majority or forced consensus is allowed. The Chair report is educational synthesis, not a treatment directive.

## 5. Required reports

The current Chair report captures the consolidated debate, dissent, uncertainty, patient/context, feasibility, governance, and evidence limitations. Separate evidence/provenance and expanded patient-reality reports remain future work after source retrieval and validation are implemented.

## 6. Evidence presentation

Evidence retrieval and citation verification are not connected yet. Material evidence claims must remain disabled until sources can be traced to title, issuing organization, date, stable URL/identifier, relevant locator, evidence type, and limitations. Distinguish established standard, emerging evidence, and investigational approaches only when supported by a verified source.

## 7. Patient perspective and persona rules

Personas are discussion lenses, not demographic stereotypes or clinical facts. Do not infer beliefs, adherence, finances, literacy, family support, or preferences from demographics. Use only case-supplied details; otherwise ask or mark unknown.

## 8. Prototype success criteria

- All 45 roles appear in each of Rounds 1–3.
- Independent positions are preserved before debate context is shared.
- Every agent has an explicit conclusion and role-specific contribution.
- The Chair records consensus status and preserves dissent.
- Run exports include the exact synthetic case snapshot and checksum.
- Missing data and evidence limitations remain visible.
- No real-patient data is required.
