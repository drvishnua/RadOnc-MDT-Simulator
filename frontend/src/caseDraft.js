/** Small, storage-agnostic persistence helpers for the editable case draft. */
function isDraft(value, defaults) {
  return value !== null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.keys(defaults).every((key) => typeof value[key] === "string");
}

export function readDraft(storage, key, legacyKey, defaults, migrateLegacy) {
  try {
    const rawDraft = storage.getItem(key);
    if (rawDraft !== null) {
      const parsed = JSON.parse(rawDraft);
      if (isDraft(parsed, defaults)) return parsed;
    }

    const rawLegacy = storage.getItem(legacyKey);
    if (rawLegacy !== null) {
      const migrated = migrateLegacy(JSON.parse(rawLegacy));
      if (isDraft(migrated, defaults)) return migrated;
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
