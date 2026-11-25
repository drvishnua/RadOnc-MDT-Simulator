export interface ClinicalPerturbation {
  id: string;
  label: string;
  icon: string;
  description: string;
  category: "Performance" | "Pathology" | "Staging" | "Operability";
  fieldChanges: Record<string, unknown>;
  narrativeAddition: string;
}

export const CLINICAL_PERTURBATIONS: ClinicalPerturbation[];

export function applyPerturbation<T extends Record<string, unknown>>(
  form: T,
  perturbationId: string
): T & { applied_perturbation_id?: string };
