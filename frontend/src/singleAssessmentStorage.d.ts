export type StoredSingleAssessment = {
  version: 1;
  saved_at: string;
  case_snapshot: Record<string, unknown>;
  assessment: Record<string, unknown>;
};

export function readSavedSingleAssessment(
  storage: Pick<Storage, "getItem">,
  key: string
): StoredSingleAssessment | null;

export function writeSavedSingleAssessment(
  storage: Pick<Storage, "setItem">,
  key: string,
  caseSnapshot: Record<string, unknown>,
  assessment: Record<string, unknown>,
  savedAt: string
): boolean;
