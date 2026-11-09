import test from "node:test";
import assert from "node:assert/strict";
import { readDraft, writeDraft } from "./caseDraft.js";

const defaults = {
  scenario_title: "Synthetic head-and-neck case",
  case_summary: "",
  age_years: "",
  known_unknowns: ""
};

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, value); },
    removeItem(key) { values.delete(key); },
    values
  };
}

test("round-trips exact draft strings including whitespace and multiline text", () => {
  const storage = memoryStorage();
  const draft = {
    ...defaults,
    case_summary: "  First line\nSecond line  ",
    known_unknowns: "\nMRI pending\n"
  };
  assert.equal(writeDraft(storage, "draft", "legacy", draft), true);
  assert.deepEqual(readDraft(storage, "draft", "legacy", defaults, () => null), draft);
});

test("migrates the legacy validated case without treating it as validated", () => {
  const legacy = { case_summary: "legacy summary" };
  const storage = memoryStorage({ legacy: JSON.stringify(legacy) });
  const migrated = readDraft(storage, "draft", "legacy", defaults, (value) => ({
    ...defaults,
    case_summary: value.case_summary
  }));
  assert.equal(migrated.case_summary, "legacy summary");
  assert.equal(storage.getItem("legacy") !== null, true);
  assert.equal(writeDraft(storage, "draft", "legacy", migrated), true);
  assert.equal(storage.getItem("legacy"), null);
});

test("rejects malformed or incomplete drafts and falls back to defaults", () => {
  const storage = memoryStorage({ draft: JSON.stringify({ case_summary: "partial" }) });
  assert.deepEqual(readDraft(storage, "draft", "legacy", defaults, () => null), defaults);
});

test("does not discard the legacy record if saving the new draft fails", () => {
  const storage = {
    setItem() { throw new Error("quota exceeded"); },
    removeItem() { throw new Error("must not be called"); }
  };
  assert.equal(writeDraft(storage, "draft", "legacy", defaults), false);
});

test("storage access failures return defaults without throwing", () => {
  const storage = { getItem() { throw new Error("storage disabled"); } };
  assert.deepEqual(readDraft(storage, "draft", "legacy", defaults, () => null), defaults);
});

test("preserves a previous form schema and fills newly added fields from defaults", () => {
  const expandedDefaults = {
    ...defaults,
    patient_name: "",
    sex_at_birth: "",
    primary_site: "",
    histology: "",
    clinical_t_stage: "",
    clinical_n_stage: "",
    clinical_m_stage: "",
    stage_group: "",
    performance_status: "",
    pathology_summary: "",
    imaging_summary: "",
    relevant_comorbidities: "",
    prior_treatment: "",
    patient_goals: "",
    social_context: "",
    resource_context: "",
    current_medications: "",
    known_allergies: "",
    relevant_investigations: ""
  };
  const previousDraft = { ...expandedDefaults };
  delete previousDraft.patient_name;
  delete previousDraft.current_medications;
  delete previousDraft.known_allergies;
  delete previousDraft.relevant_investigations;
  previousDraft.case_summary = "unsaved case text";
  const storage = memoryStorage({ draft: JSON.stringify(previousDraft) });
  const restored = readDraft(storage, "draft", "legacy", expandedDefaults, () => null);
  assert.equal(restored.case_summary, "unsaved case text");
  assert.equal(restored.patient_name, "");
  assert.equal(restored.current_medications, "");
  assert.equal(restored.known_allergies, "");
  assert.equal(restored.relevant_investigations, "");
});

test("round-trips structured case lists through actual newline-delimited form text", async () => {
  const { listToMultilineText, multilineTextToList } = await import("./caseDraft.js");
  const values = ["Diabetes", "Hypertension", "Prior surgery"];
  const formText = listToMultilineText(values);
  assert.equal(formText, "Diabetes\nHypertension\nPrior surgery");
  assert.deepEqual(multilineTextToList(formText), values);
});

test("renders an empty structured list as empty form text", async () => {
  const { listToMultilineText, multilineTextToList } = await import("./caseDraft.js");
  assert.equal(listToMultilineText([]), "");
  assert.deepEqual(multilineTextToList(""), []);
});
