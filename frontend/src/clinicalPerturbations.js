export const CLINICAL_PERTURBATIONS = [
  {
    id: "ecog_0_to_3",
    label: "ECOG 0 → 3 (Deconditioned)",
    icon: "🦽",
    category: "Performance",
    description: "Patient experiences rapid performance decline, bedbound >50% waking hours, borderline for aggressive concurrent CRT.",
    fieldChanges: {
      performance_status_ecog: 3
    },
    narrativeAddition: "\n\n[PERTURBATION APPLIED: Acute functional decline. Patient now ECOG 3, bedbound >50% of the day with severe fatigue and inability to perform basic ADLs.]"
  },
  {
    id: "margin_r0_to_r1",
    label: "Margin R0 → R1 (Positive Ink)",
    icon: "🔬",
    category: "Pathology",
    description: "Surgical margin reported as microscopically positive with tumor cells directly at inked resection margin (R1).",
    fieldChanges: {
      margin_status: "R1"
    },
    narrativeAddition: "\n\n[PERTURBATION APPLIED: Pathology revision demonstrates microscopically positive ink resection margin (R1) with high risk of local failure.]"
  },
  {
    id: "node_n0_to_n1",
    label: "Nodal Stage N0 → N1/N2",
    icon: "🎯",
    category: "Staging",
    description: "PET-CT reveals previously unappreciated hypermetabolic regional lymph node metastasis (SUV 7.8).",
    fieldChanges: {
      clinical_n_stage: "N1"
    },
    narrativeAddition: "\n\n[PERTURBATION APPLIED: Staging updated to N1 due to 1.8 cm hypermetabolic regional node (SUVmax 7.8) on interval PET-CT.]"
  },
  {
    id: "medically_inoperable",
    label: "Operable → Medically Inoperable",
    icon: "🫁",
    category: "Operability",
    description: "Severe cardiopulmonary limitation: FEV1 38% predicted, severe CAD with EF 30%, prohibitive surgical mortality risk.",
    fieldChanges: {
      intent_direction: "Definitive Non-Surgical Radiation"
    },
    narrativeAddition: "\n\n[PERTURBATION APPLIED: Pulmonology and Cardiology deem patient medically inoperable due to severe COPD (FEV1 38%) and ischemic cardiomyopathy (LVEF 30%).]"
  }
];

export function applyPerturbation(form, perturbationId) {
  const p = CLINICAL_PERTURBATIONS.find((item) => item.id === perturbationId);
  if (!p) return form;
  const updated = { ...form, ...p.fieldChanges };

  const currentSummary = updated.case_summary || "";
  if (!currentSummary.includes(p.narrativeAddition.trim())) {
    updated.case_summary = currentSummary.trim() + p.narrativeAddition;
  }

  updated.applied_perturbation_id = perturbationId;
  return updated;
}
