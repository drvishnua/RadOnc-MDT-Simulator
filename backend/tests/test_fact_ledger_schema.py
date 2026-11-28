"""Regression tests for fact ledger JSON schema and canonical alignment."""
from __future__ import annotations

import json
import pathlib
import re
from typing import get_args

from app.clinical_fields import DataState

SCHEMA_PATH = pathlib.Path(__file__).parents[1] / "app" / "state" / "fact_ledger_schema.json"


def test_fact_ledger_schema_is_valid_json() -> None:
    assert SCHEMA_PATH.is_file()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert "^[a-zA-Z0-9_]+$" in schema["patternProperties"]


def test_fact_ledger_schema_aligns_with_canonical_data_states() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prop = schema["patternProperties"]["^[a-zA-Z0-9_]+$"]
    schema_states = set(prop["properties"]["state"]["enum"])

    # All canonical DataState members must be accepted
    canonical_states = set(get_args(DataState))
    assert canonical_states.issubset(schema_states)


def test_fact_ledger_schema_requires_sha256_provenance_hash() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prop = schema["patternProperties"]["^[a-zA-Z0-9_]+$"]

    assert "provenance_hash" in prop["required"]
    hash_spec = prop["properties"]["provenance_hash"]
    assert hash_spec["type"] == "string"

    hash_pattern = re.compile(hash_spec["pattern"])
    # 64-character hex string (SHA-256)
    valid_sha256 = "a" * 64
    assert hash_pattern.fullmatch(valid_sha256) is not None
    # Invalid lengths or non-hex characters must fail
    assert hash_pattern.fullmatch("a" * 63) is None
    assert hash_pattern.fullmatch("a" * 65) is None
    assert hash_pattern.fullmatch("g" * 64) is None
