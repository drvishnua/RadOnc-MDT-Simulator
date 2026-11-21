"""Tests for concurrency lock utility."""
from __future__ import annotations

import pathlib
import pytest

from app.utils import concurrency_lock


def test_concurrency_lock_lifecycle(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    lock_file = tmp_path / "test.lock"
    monkeypatch.setattr(concurrency_lock, "LOCK_FILE", lock_file)

    # Initially acquiring the lock should succeed
    assert concurrency_lock.acquire_lock(timeout=1.0) is True
    assert lock_file.exists()

    # Second acquisition while held should fail (timeout)
    assert concurrency_lock.acquire_lock(timeout=0.1) is False

    # Releasing the lock deletes the file
    concurrency_lock.release_lock()
    assert not lock_file.exists()

    # After release, acquiring again succeeds
    assert concurrency_lock.acquire_lock(timeout=1.0) is True
    concurrency_lock.release_lock()

