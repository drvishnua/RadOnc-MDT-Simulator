import test from "node:test";
import assert from "node:assert/strict";
import { patientVersionDisplayName } from "./patientVersionName.js";

test("uses the historical registry name saved with the selected case version", () => {
  assert.equal(
    patientVersionDisplayName({ patient_name: "Name at version 1" }, "Name at version 2"),
    "Name at version 1"
  );
});

test("falls back to current registry name only when a legacy version has no saved name", () => {
  assert.equal(
    patientVersionDisplayName({ patient_name: null }, "Current registry name"),
    "Current registry name"
  );
});

test("returns an empty display name when neither version nor profile contains one", () => {
  assert.equal(patientVersionDisplayName({ patient_name: null }, null), "");
});
