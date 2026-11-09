import test from "node:test";
import assert from "node:assert/strict";
import { hasCompletedIndependentAssessments, hasValidatedCase, shouldShowBatchPanel } from "./runRecovery.js";

const savedRun = { run_id: "synthetic-run-001", status: "running" };
const validCase = { scenario_title: "Synthetic test case" };
const validResult = { valid: true };

test("restored run stays visible when validation resets after refresh", () => {
  assert.equal(hasValidatedCase(null, null), false);
  assert.equal(shouldShowBatchPanel(savedRun, null, null), true);
});

test("saved run remains visible while the user edits an unvalidated draft", () => {
  assert.equal(shouldShowBatchPanel(savedRun, { valid: false }, null), true);
});

test("a new batch panel is available after the current case is validated", () => {
  assert.equal(hasValidatedCase(validResult, validCase), true);
  assert.equal(shouldShowBatchPanel(null, validResult, validCase), true);
});

test("an unvalidated draft alone cannot expose a run-launch panel", () => {
  assert.equal(hasValidatedCase(null, validCase), false);
  assert.equal(shouldShowBatchPanel(null, null, validCase), false);
  assert.equal(shouldShowBatchPanel(null, { valid: false }, validCase), false);
});

test("an invalid validation result never authorises a new batch", () => {
  assert.equal(hasValidatedCase({ valid: false }, validCase), false);
});


test("MDT rounds are available only after every independent assessment succeeds", () => {
  const completeR1 = {
    total_agents: 45,
    completed_count: 45,
    failed_count: 0
  };
  assert.equal(hasCompletedIndependentAssessments(completeR1), true);
  assert.equal(hasCompletedIndependentAssessments({
    ...completeR1,
    completed_count: 44
  }), false);
  assert.equal(hasCompletedIndependentAssessments({
    ...completeR1,
    failed_count: 1
  }), false);
  assert.equal(hasCompletedIndependentAssessments(null), false);
});

test("a terminal Chair error does not erase completed R1 readiness", () => {
  const parentAfterChairFailure = {
    status: "completed_with_errors",
    total_agents: 45,
    completed_count: 45,
    failed_count: 0
  };
  assert.equal(hasCompletedIndependentAssessments(parentAfterChairFailure), true);
});
