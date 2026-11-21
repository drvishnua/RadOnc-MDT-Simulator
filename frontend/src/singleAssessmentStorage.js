/** Versioned browser persistence for the standalone RO-01 Round 1 assessment. */
const STORAGE_VERSION = 1;
const VALID_POSITIONS = new Set([
  "supports",
  "opposes",
  "conditional",
  "insufficient_information"
]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isCaseSnapshot(value) {
  if (!isRecord(value)) return false;
  const nullableTextFields = [
    "sex_at_birth",
    "primary_site",
    "histology",
    "clinical_t_stage",
    "clinical_n_stage",
    "clinical_m_stage",
    "stage_group",
    "performance_status",
    "pathology_summary",
    "imaging_summary"
  ];
  const listFields = [
    "relevant_comorbidities",
    "prior_treatment",
    "patient_goals",
    "social_context",
    "resource_context",
    "known_unknowns"
  ];
  return typeof value.scenario_title === "string" &&
    typeof value.case_summary === "string" &&
    (value.age_years === null ||
      (typeof value.age_years === "number" && Number.isFinite(value.age_years))) &&
    nullableTextFields.every((field) => value[field] === null || typeof value[field] === "string") &&
    listFields.every((field) =>
      Array.isArray(value[field]) && value[field].every((item) => typeof item === "string")
    );
}

function isRo01Assessment(value) {
  return isRecord(value) &&
    value.agent_id === "RO-01" &&
    value.round_number === 1 &&
    VALID_POSITIONS.has(value.position) &&
    typeof value.provisional_conclusion === "string" &&
    typeof value.preferred_educational_option === "string" &&
    typeof value.perspective_summary === "string" &&
    ["case_facts", "case_data_integrity_flags", "assumptions", "unknowns",
      "discussion_options", "evidence_claims", "evidence_gaps",
      "uncertainty_notes", "disagreement_notes"].every((field) => Array.isArray(value[field])) &&
    typeof value.confidence === "number" &&
    Number.isFinite(value.confidence) && value.confidence >= 0 && value.confidence <= 1 &&
    value.safety_boundary === "educational_simulation_only" &&
    value.not_a_treatment_instruction === true;
}

export function readSavedSingleAssessment(storage, key) {
  try {
    const raw = storage.getItem(key);
    if (raw === null) return null;
    const parsed = JSON.parse(raw);
    if (!isRecord(parsed) ||
        parsed.version !== STORAGE_VERSION ||
        typeof parsed.saved_at !== "string" ||
        !Number.isFinite(Date.parse(parsed.saved_at)) ||
        !isCaseSnapshot(parsed.case_snapshot) ||
        !isRo01Assessment(parsed.assessment)) {
      return null;
    }
    return parsed;
  } catch {
    // Preserve malformed or inaccessible storage; never erase it as a side effect of reading.
    return null;
  }
}

export function writeSavedSingleAssessment(storage, key, caseSnapshot, assessment, savedAt) {
  if (!isCaseSnapshot(caseSnapshot) || !isRo01Assessment(assessment) ||
      typeof savedAt !== "string" || !Number.isFinite(Date.parse(savedAt))) {
    return false;
  }
  try {
    storage.setItem(key, JSON.stringify({
      version: STORAGE_VERSION,
      saved_at: savedAt,
      case_snapshot: caseSnapshot,
      assessment
    }));
    return true;
  } catch {
    return false;
  }
}
