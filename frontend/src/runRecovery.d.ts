type ValidationState = { valid: boolean } | null;

export function hasValidatedCase(
  validation: ValidationState,
  validatedCase: unknown
): boolean;

export function hasCompletedIndependentAssessments(batchRun: {
  total_agents: number;
  completed_count: number;
  failed_count: number;
} | null | undefined): boolean;

export function shouldShowBatchPanel(
  batchRun: unknown,
  validation: ValidationState,
  validatedCase: unknown
): boolean;

export function shouldOfferIndependentBatchResume(
  batchRun: {
    status: "queued" | "running" | "completed" | "completed_with_errors";
    failed_count?: number;
    updated_at?: string;
  } | null | undefined,
  now?: number
): boolean;
