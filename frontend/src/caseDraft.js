/** Small, storage-agnostic persistence helpers for the editable case draft. */
function isDraft(value, defaults) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const allowed = Object.keys(defaults);
  const entries = Object.entries(value);
  // Accept a previous form schema when most original fields still exist, but reject tiny fragments.
  return entries.length >= Math.ceil(allowed.length * 0.7) &&
    entries.every(([key, item]) => allowed.includes(key) && typeof item === "string");
}

export function readDraft(storage, key, legacyKey, defaults, migrateLegacy) {
  try {
    const rawDraft = storage.getItem(key);
    if (rawDraft !== null) {
      const parsed = JSON.parse(rawDraft);
      if (isDraft(parsed, defaults)) return { ...defaults, ...parsed };
    }

    const rawLegacy = storage.getItem(legacyKey);
    if (rawLegacy !== null) {
      const migrated = migrateLegacy(JSON.parse(rawLegacy));
      if (isDraft(migrated, defaults)) return { ...defaults, ...migrated };
    }
  } catch {
    // Storage may be unavailable or contain malformed/incompatible data.
  }
  return { ...defaults };
}

export function writeDraft(storage, key, legacyKey, draft) {
  try {
    storage.setItem(key, JSON.stringify(draft));
    // Remove the old validated-case cache only after the draft is safely written.
    storage.removeItem(legacyKey);
    return true;
  } catch {
    return false;
  }
}
