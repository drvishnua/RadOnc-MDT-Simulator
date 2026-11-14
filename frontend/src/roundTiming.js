/**
 * Format a persisted wall-clock interval.
 * Returns null until both timestamps exist or when the interval is invalid.
 */
export function formatElapsedDuration(startedAt, finishedAt) {
  if (typeof startedAt !== "string" || typeof finishedAt !== "string") return null;

  const startMs = Date.parse(startedAt);
  const finishMs = Date.parse(finishedAt);
  if (!Number.isFinite(startMs) || !Number.isFinite(finishMs) || finishMs < startMs) {
    return null;
  }

  const totalSeconds = Math.round((finishMs - startMs) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}
