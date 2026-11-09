import hashlib
import sqlite3
from pathlib import Path

import pytest

from app.services import run_store


def _create_database(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE preserved_data (value TEXT NOT NULL)")
        connection.execute("INSERT INTO preserved_data(value) VALUES (?)", (value,))


def _read_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT value FROM preserved_data").fetchone()[0]


def test_legacy_database_is_backed_up_without_changing_the_source(monkeypatch, tmp_path: Path) -> None:
    legacy_path = tmp_path / "legacy" / "simulation_runs.sqlite3"
    destination_path = tmp_path / "user-data" / "simulation_runs.sqlite3"
    _create_database(legacy_path, "existing training records")
    original_hash = hashlib.sha256(legacy_path.read_bytes()).hexdigest()

    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", legacy_path)
    monkeypatch.setattr(run_store, "DB_PATH", destination_path)

    assert run_store._migrate_legacy_database_if_needed() is True
    assert destination_path.is_file()
    assert _read_value(destination_path) == "existing training records"
    assert _read_value(legacy_path) == "existing training records"
    assert hashlib.sha256(legacy_path.read_bytes()).hexdigest() == original_hash


def test_existing_user_database_is_never_overwritten_by_legacy_copy(monkeypatch, tmp_path: Path) -> None:
    legacy_path = tmp_path / "legacy.sqlite3"
    destination_path = tmp_path / "user-data" / "simulation_runs.sqlite3"
    _create_database(legacy_path, "older source data")
    _create_database(destination_path, "already installed data")

    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", legacy_path)
    monkeypatch.setattr(run_store, "DB_PATH", destination_path)

    assert run_store._migrate_legacy_database_if_needed() is False
    assert _read_value(destination_path) == "already installed data"
    assert _read_value(legacy_path) == "older source data"


def test_corrupt_legacy_database_is_not_migrated_or_replaced(monkeypatch, tmp_path: Path) -> None:
    legacy_path = tmp_path / "corrupt.sqlite3"
    destination_path = tmp_path / "user-data" / "simulation_runs.sqlite3"
    legacy_bytes = b"not a SQLite database"
    legacy_path.write_bytes(legacy_bytes)

    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", legacy_path)
    monkeypatch.setattr(run_store, "DB_PATH", destination_path)

    with pytest.raises(sqlite3.DatabaseError):
        run_store._migrate_legacy_database_if_needed()

    assert not destination_path.exists()
    assert legacy_path.read_bytes() == legacy_bytes
