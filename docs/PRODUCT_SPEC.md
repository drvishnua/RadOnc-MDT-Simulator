# Product Specification — RadOnc MDT Simulator

## 1. Product purpose
RadOnc MDT Simulator is a local, AI-assisted educational environment for simulating multidisciplinary oncology case discussions. The initial scenario set focuses on synthetic head-and-neck cancer cases.

It helps learners examine how clinical specialties, patient priorities, evidence quality, resources, feasibility, ethics, and uncertainty affect an MDT discussion. It is not intended to produce autonomous treatment decisions.

## 2. Intended users
- Radiation, medical, and surgical oncology trainees
- Oncology educators and MDT facilitators
- Researchers evaluating structured approaches to simulated MDT discussion

## 3. First-release boundaries
The first release should:
- Accept structured, synthetic case information.
- Identify missing, conflicting, and internally inconsistent case details.
- Run all 45 configured perspectives for every simulation.
- Preserve independent opinions before agents see the debate.
- Separate established standard-of-care from emerging and investigational approaches.
- Require evidence citations for material clinical claims.
- Preserve disagreement and document why consensus was or was not reached.
- Generate clearly labeled educational reports.

The first release must not:
- Accept identifiable patient records or real-world patient data.
- Connect to hospital information systems or treatment-planning systems.
- Generate or approve patient-specific prescriptions, dose constraints, contours, or treatment plans.
- Claim to replace a qualified clinician or formal MDT.
- Present legal, financial, or policy issue-spotting as professional advice.

## 4. Four-round simulation workflow

### Round 1 — Independent assessments
Each configured agent receives the same structured case and produces an independent assessment before seeing other agents' opinions. Agents identify relevant facts and assumptions, missing information, role-specific concerns, options worth discussing, evidence needed, and confidence/uncertainty.

### Round 2 — MDT discussion
Agents receive permitted prior discussion context and respond to relevant disagreements. The system distinguishes a change of opinion from a clarification and preserves the original independent position.

### Round 3 — Adversarial review
Evidence, feasibility, resource, patient-reality, and medico-legal perspectives challenge unsupported assumptions, omitted alternatives, unsafe extrapolations, and implementation barriers. Challenges must remain respectful and specific.

### Round 4 — Chair synthesis
The chair summarizes areas of agreement, unresolved disagreements, missing information, evidence limitations, feasibility and patient-context issues, and a transparent educational synthesis—not a clinical directive.

## 5. Required report outputs
1. **Simulated MDT discussion report** — case summary, specialty views, debate, synthesis, and dissent.
2. **Evidence and uncertainty report** — claims, sources, dates, evidence level, applicability, and gaps.
3. **Patient reality report** — patient priorities, family/caregiver perspectives, access barriers, affordability, communication, and support needs.
4. **Feasibility and risk review** — resource, logistics, policy, safeguarding, and medico-legal issues to verify.

## 6. Evidence presentation rules
Every material evidence-based claim must be traceable to a source. Capture source title and issuing organization, publication/update/access date, stable URL or identifier, relevant section, evidence type, and limitations where available.

Use explicit labels:
- **Established standard / guideline-supported**
- **Emerging evidence / evolving practice**
- **Investigational / experimental**

Do not infer that an intervention is standard merely because a paper reports favorable outcomes. Distinguish source availability from source quality, and freely accessible text from open licensing.

## 7. Patient perspective and persona rules
Personas are discussion lenses, not demographic stereotypes or clinical facts. Do not infer beliefs, adherence, finances, literacy, family support, or preferences from demographics. Represent only scenario details supplied in the synthetic case. When absent, ask or mark unknown.

## 8. Prototype success criteria
- All 45 agent roles are present in every simulation run.
- Independent assessments are stored before debate context is shared.
- Outputs distinguish evidence types and cite sources.
- Missing data and uncertainty are visible.
- Disagreement is retained rather than flattened into artificial consensus.
- Reports are reproducible from the saved synthetic case and run configuration.
- No real patient data is required for any demonstration.
