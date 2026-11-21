/** Resolve the registry display name belonging to the selected immutable case version. */
export function patientVersionDisplayName(version, currentPatientName = null) {
  const savedName = version?.patient_name;
  if (typeof savedName === "string" && savedName.trim()) return savedName.trim();
  return typeof currentPatientName === "string" ? currentPatientName : "";
}
