"""Concurrency lock for single-process GPU/Ollama operations.

The simulator must never run two inference jobs at the same time on the same GPU
or Ollama port. The simplest cross-process lock on Windows is a file-based mutex.
"""

import os
import pathlib
import time

_LOCALAPPDATA = os.getenv("LOCALAPPDATA")
if _LOCALAPPDATA:
    LOCK_FILE = pathlib.Path(_LOCALAPPDATA) / "RadOncMDT" / "run.lock"
else:
    LOCK_FILE = pathlib.Path.home() / "AppData" / "Local" / "RadOncMDT" / "run.lock"


def acquire_lock(timeout: float = 30) -> bool:
    """Create the lock file. Returns True if we got the lock, False if timeout.

    The file contains the PID that owns the lock.
    """
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    while True:
        try:
            # exclusive creation – fails if file exists
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.close(fd)
            return True
        except FileExistsError:
            # another process holds the lock – wait a bit or timeout
            if time.time() - start >= timeout:
                return False
            time.sleep(min(0.5, max(0.01, timeout - (time.time() - start))))


def release_lock() -> None:
    """Delete the lock file – only the owning process should call this."""
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass
