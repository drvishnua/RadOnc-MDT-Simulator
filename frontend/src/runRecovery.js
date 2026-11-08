export function hasValidatedCase(validation, validatedCase) {
  return validation?.valid === true && validatedCase !== null && validatedCase !== undefined;
}

export function shouldShowBatchPanel(batchRun, validation, validatedCase) {
  // Saved-run visibility is independent of the session-only case validation state.
  return (batchRun !== null && batchRun !== undefined) || hasValidatedCase(validation, validatedCase);
}
