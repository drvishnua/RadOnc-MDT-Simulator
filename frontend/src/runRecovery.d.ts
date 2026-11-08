type ValidationState = { valid: boolean } | null;

export function hasValidatedCase(
  validation: ValidationState,
  validatedCase: unknown
): boolean;

export function shouldShowBatchPanel(
  batchRun: unknown,
  validation: ValidationState,
  validatedCase: unknown
): boolean;
