export function readDraft<T extends Record<string, string>>(
  storage: Pick<Storage, "getItem">,
  key: string,
  legacyKey: string,
  defaults: T,
  migrateLegacy: (value: unknown) => T | null
): T;

export function writeDraft<T extends Record<string, string>>(
  storage: Pick<Storage, "setItem" | "removeItem">,
  key: string,
  legacyKey: string,
  draft: T
): boolean;

export function listToMultilineText(values: unknown): string;
export function multilineTextToList(value: string): string[];
