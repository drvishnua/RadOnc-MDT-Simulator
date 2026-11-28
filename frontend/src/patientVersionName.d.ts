export type PatientVersionNameSource = {
  patient_name?: string | null;
} | null | undefined;

export function patientVersionDisplayName(
  version: PatientVersionNameSource,
  currentPatientName?: string | null
): string;
