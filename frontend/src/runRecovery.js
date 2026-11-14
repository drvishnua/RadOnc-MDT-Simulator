export function hasValidatedCase(validation, validatedCase) {
  return validation?.valid === true && validatedCase !== null && validatedCase !== undefined;
}

export function hasCompletedIndependentAssessments(batchRun) {
  return Boolean(
    batchRun &&
    Number.isInteger(batchRun.total_agents) &&
    batchRun.total_agents > 0 &&
    batchRun.completed_count === batchRun.total_agents &&
    batchRun.failed_count === 0
  );
}

export function shouldShowBatchPanel(batchRun, validation, validatedCase) {
  // Saved-run visibility is independent of the session-only case validation state.
  return (batchRun !== null && batchRun !== undefined) || hasValidatedCase(validation, validatedCase);
}

export function shouldOfferIndependentBatchResume(batchRun, now = Date.now()) {
  if (!batchRun) return false;

  // A later MDT-stage failure is not an R1 agent failure. Its recovery action
  // belongs to the affected round, not to the independent-assessment runner.
  if (batchRun.status === "completed_with_errors") {
    return Number.isInteger(batchRun.failed_count) && batchRun.failed_count > 0;
  }

  if (batchRun.status !== "running" && batchRun.status !== "queued") {
    return false;
  }

  const updatedAt = Date.parse(batchRun.updated_at ?? "");
  return Number.isFinite(updatedAt) && now - updatedAt > 120000;
}
