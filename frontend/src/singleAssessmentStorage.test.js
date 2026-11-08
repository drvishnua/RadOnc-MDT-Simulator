import test from "node:test";
import assert from "node:assert/strict";
import {
  readSavedSingleAssessment,
  writeSavedSingleAssessment
} from "./singleAssessmentStorage.js";

const caseSnapshot = {
  scenario_title: "Synthetic persistence test",
  case_summary: "A fictional training case with staging information intentionally incomplete.",
  age_years: null,
  sex_at_birth: null,
  primary_site: "Unknown",
  histology: null,
  clinical_t_stage: null,
  clinical_n_stage: null,
  clinical_m_stage: null,
  stage_group: null,
  performance_status: null,
  pathology_summary: null,
  imaging_summary: null,
  relevant_comorbidities: [],
  prior_treatment: [],
  patient_goals: [],
  social_context: [],
  resource_context: [],
  known_unknowns: ["Distant staging has not been supplied."]
};

const assessment = {
  agent_id: "RO-01",
  round_number: 1,
  position: "insufficient_information",
  provisional_conclusion: "The supplied synthetic case is insufficient for a definitive conclusion.",
  preferred_educational_option: "No preferred option can be established from the supplied information.",
  perspective_summary: "The assessment preserves missing staging and does not infer negative findings.",
  case_facts: [],
  case_data_integrity_flags: [],
  assumptions: [],
  unknowns: ["Distant staging is not supplied."],
  discussion_options: [],
  evidence_claims: [],
  evidence_gaps: ["No evidence retrieval is connected."],
  uncertainty_notes: [],
  disagreement_notes: [],
  confidence: 0.25,
  safety_boundary: "educational_simulation_only",
  not_a_treatment_instruction: true
};

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, value); },
    values
  };
}

test("round-trips the RO-01 assessment with its exact case snapshot", () => {
  const storage = memoryStorage();
  const savedAt = "2026-11-09T10:00:00.000Z";
  assert.equal(writeSavedSingleAssessment(storage, "assessment", caseSnapshot, assessment, savedAt), true);
  assert.deepEqual(readSavedSingleAssessment(storage, "assessment"), {
    version: 1,
    saved_at: savedAt,
    case_snapshot: caseSnapshot,
    assessment
  });
});

test("rejects a stored result for another role or round", () => {
  const storage = memoryStorage({
    assessment: JSON.stringify({
      version: 1,
      saved_at: "2026-11-09T10:00:00.000Z",
      case_snapshot: caseSnapshot,
      assessment: { ...assessment, agent_id: "MO-01" }
    })
  });
  assert.equal(readSavedSingleAssessment(storage, "assessment"), null);
});

test("rejects incompatible versions and incomplete case snapshots", () => {
  const storage = memoryStorage({
    assessment: JSON.stringify({
      version: 2,
      saved_at: "2026-11-09T10:00:00.000Z",
      case_snapshot: caseSnapshot,
      assessment
    })
  });
  assert.equal(readSavedSingleAssessment(storage, "assessment"), null);
  assert.equal(writeSavedSingleAssessment(
    storage, "assessment", { scenario_title: "Missing fields" }, assessment,
    "2026-11-09T10:00:00.000Z"
  ), false);
});

test("does not throw when browser storage is unavailable or full", () => {
  const unavailable = {
    getItem() { throw new Error("storage unavailable"); },
    setItem() { throw new Error("quota exceeded"); }
  };
  assert.equal(readSavedSingleAssessment(unavailable, "assessment"), null);
  assert.equal(writeSavedSingleAssessment(
    unavailable, "assessment", caseSnapshot, assessment, "2026-11-09T10:00:00.000Z"
  ), false);
});
