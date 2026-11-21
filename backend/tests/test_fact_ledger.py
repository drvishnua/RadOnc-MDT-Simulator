"""Fact Ledger schema and immutability validation test."""

import json
import pathlib
import pytest

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "app" / "state" / "fact_ledger_schema.json"


def test_fact_ledger_schema_file_exists_and_is_valid_json():
    assert SCHEMA_PATH.is_file(), f"Schema file missing at {SCHEMA_PATH}"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema.get("title") == "Fact Ledger Schema"
    assert "patternProperties" in schema


def test_fact_ledger_schema_validation(tmp_path: pathlib.Path):
    jsonschema = pytest.importorskip("jsonschema")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    valid_ledger = {
        "case_001": {
            "field_id": "clinical_t_stage",
            "value": "T1",
            "state": "present",
            "source": "clinician_note",
            "timestamp": "2026-11-21T12:00:00Z",
            "provenance_hash": "a" * 64,
            "validation_status": "validated",
            "registry_version": "2.0.0",
        }
    }
    # Valid instance passes
    jsonschema.validate(instance=valid_ledger, schema=schema)

    # Tampered instance (invalid state) fails validation
    tampered_ledger = {
        "case_001": {
            "field_id": "clinical_t_stage",
            "value": "T1",
            "state": "invalid_state",
            "source": "clinician_note",
            "timestamp": "2026-11-21T12:00:00Z",
            "registry_version": "2.0.0",
        }
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=tampered_ledger, schema=schema)
