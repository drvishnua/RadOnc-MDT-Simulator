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
