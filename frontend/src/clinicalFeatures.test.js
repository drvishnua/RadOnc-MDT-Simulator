import test from "node:test";
import assert from "node:assert/strict";
import { LANDMARK_TRIALS, getSiteConstraints, findTrialByKeyword } from "./clinicalEvidence.js";
import { CLINICAL_PERTURBATIONS, applyPerturbation } from "./clinicalPerturbations.js";

test("LANDMARK_TRIALS contains authoritative oncology trials with required fields", () => {
  assert.ok(LANDMARK_TRIALS.length >= 8);
  const pacific = LANDMARK_TRIALS.find((t) => t.id === "PACIFIC");
  assert.ok(pacific);
  assert.strictEqual(pacific.phase, "Phase 3 Randomized");
  assert.strictEqual(pacific.primarySite, "Thorax");
  assert.ok(pacific.radOncTakeaway.includes("Durvalumab"));
  assert.ok(pacific.pmid.length > 0);
});

test("findTrialByKeyword locates trials by acronym, name, or primary site", () => {
  const rapido = findTrialByKeyword("rapido");
  assert.ok(rapido);
  assert.strictEqual(rapido.id, "RAPIDO");

  const gbm = findTrialByKeyword("glioblastoma");
  assert.ok(gbm);
  assert.strictEqual(gbm.id, "STUPP");
});

test("getSiteConstraints returns site-specific QUANTEC/PENTEC normal tissue limits", () => {
  const cnsLimits = getSiteConstraints("CNS");
  assert.ok(cnsLimits.length >= 5);
  const brainstem = cnsLimits.find((c) => c.organ === "Brainstem");
  assert.ok(brainstem);
  assert.strictEqual(brainstem.limitValue, 54);
  assert.strictEqual(brainstem.unit, "Gy");

  const thoraxLimits = getSiteConstraints("Thorax");
  assert.ok(thoraxLimits.length >= 5);
  const lung = thoraxLimits.find((c) => c.metric === "V20Gy");
  assert.ok(lung);
  assert.strictEqual(lung.limitValue, 30);

  const breastLimits = getSiteConstraints("Breast");
  assert.ok(breastLimits.length >= 4);
  const lad = breastLimits.find((c) => c.organ.includes("LAD"));
  assert.ok(lad);
});

test("applyPerturbation cleanly modifies clinical fields and appends narrative", () => {
  const baseForm = {
    case_summary: "Initial clinical case description.",
    performance_status_ecog: 0,
    clinical_n_stage: "N0"
  };

  const perturbedEcog = applyPerturbation(baseForm, "ecog_0_to_3");
  assert.strictEqual(perturbedEcog.performance_status_ecog, 3);
  assert.ok(perturbedEcog.case_summary.includes("PERTURBATION APPLIED: Acute functional decline"));
  assert.strictEqual(perturbedEcog.applied_perturbation_id, "ecog_0_to_3");

  const perturbedNode = applyPerturbation(baseForm, "node_n0_to_n1");
  assert.strictEqual(perturbedNode.clinical_n_stage, "N1");
  assert.ok(perturbedNode.case_summary.includes("PET-CT"));
});
