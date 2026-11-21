"""Fact Ledger schema and immutability validation test."""

import json
import pathlib
import re
import pytest

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "app" / "state" / "fact_ledger_schema.json"


def test_fact_ledger_schema_file_exists_and_is_valid_json():
    assert SCHEMA_PATH.is_file(), f"Schema file missing at {SCHEMA_PATH}"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema.get("title") == "Fact Ledger Schema"
    assert "patternProperties" in schema


def test_fact_ledger_schema_canonical_states_and_confirmed_absent():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prop = schema["patternProperties"]["^[a-zA-Z0-9_]+$"]
    allowed_states = set(prop["properties"]["state"]["enum"])

    # Must include confirmed_absent and CONFIRMED_ABSENT per AGENTS.md
    assert "CONFIRMED_ABSENT" in allowed_states
    assert "confirmed_absent" in allowed_states

    # Must include all canonical uppercase states from clinical_fields
    canonical_states = {"PRESENT", "CONFIRMED_ABSENT", "UNKNOWN", "NOT_REPORTED", "CONFLICTING"}
    assert canonical_states.issubset(allowed_states)


def test_fact_ledger_schema_provenance_hash_specification():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prop = schema["patternProperties"]["^[a-zA-Z0-9_]+$"]

    assert "provenance_hash" in prop["required"]
    hash_spec = prop["properties"]["provenance_hash"]
    assert hash_spec["type"] == "string"

    hash_pattern = re.compile(hash_spec["pattern"])
    assert hash_pattern.fullmatch("a" * 64) is not None
    assert hash_pattern.fullmatch("A" * 64) is not None
    assert hash_pattern.fullmatch("0123456789abcdefABCDEF" + "a" * 42) is not None
    assert hash_pattern.fullmatch("a" * 63) is None
    assert hash_pattern.fullmatch("a" * 65) is None
    assert hash_pattern.fullmatch("g" * 64) is None


def test_fact_ledger_schema_validation(tmp_path: pathlib.Path):
    jsonschema = pytest.importorskip("jsonschema")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    valid_ledger = {
        "case_001": {
            "field_id": "clinical_t_stage",
            "value": "T1",
            "state": "PRESENT",
            "source": "clinician_note",
            "timestamp": "2026-11-21T12:00:00Z",
            "provenance_hash": "a" * 64,
            "validation_status": "validated",
            "registry_version": "2.0.0",
        },
        "case_002": {
            "field_id": "distant_metastasis",
            "value": None,
            "state": "CONFIRMED_ABSENT",
            "source": "pet_ct_report",
            "timestamp": "2026-11-21T12:00:00Z",
            "provenance_hash": "b" * 64,
            "validation_status": "validated",
            "registry_version": "2.0.0",
        },
    }
    # Valid instance passes
    jsonschema.validate(instance=valid_ledger, schema=schema)

    # Tampered instance (invalid state) fails validation
    tampered_state = {
        "case_001": {
            "field_id": "clinical_t_stage",
            "value": "T1",
            "state": "invalid_state",
            "source": "clinician_note",
            "timestamp": "2026-11-21T12:00:00Z",
            "provenance_hash": "a" * 64,
            "registry_version": "2.0.0",
        }
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=tampered_state, schema=schema)

    # Tampered instance (missing provenance_hash) fails validation
    tampered_missing_hash = {
        "case_001": {
            "field_id": "clinical_t_stage",
            "value": "T1",
            "state": "PRESENT",
            "source": "clinician_note",
            "timestamp": "2026-11-21T12:00:00Z",
            "registry_version": "2.0.0",
        }
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=tampered_missing_hash, schema=schema)
