import test from "node:test";
import assert from "node:assert/strict";
import { formatElapsedDuration } from "./roundTiming.js";

test("formats short round durations", () => {
  assert.equal(
    formatElapsedDuration("2026-11-09T10:00:00Z", "2026-11-09T10:02:05Z"),
    "2m 5s"
  );
});

test("formats long durations with hours", () => {
  assert.equal(
    formatElapsedDuration("2026-11-09T10:00:00Z", "2026-11-09T11:01:01Z"),
    "1h 1m 1s"
  );
});

test("formats a zero-length interval", () => {
  const timestamp = "2026-11-09T10:00:00Z";
  assert.equal(formatElapsedDuration(timestamp, timestamp), "0s");
});

test("returns null for missing or invalid timestamps", () => {
  assert.equal(formatElapsedDuration(null, "2026-11-09T10:00:00Z"), null);
  assert.equal(formatElapsedDuration("not-a-date", "2026-11-09T10:00:00Z"), null);
  assert.equal(formatElapsedDuration("2026-11-09T10:00:00Z", null), null);
});

test("returns null for a negative interval", () => {
  assert.equal(
    formatElapsedDuration("2026-11-09T10:01:00Z", "2026-11-09T10:00:00Z"),
    null
  );
});
