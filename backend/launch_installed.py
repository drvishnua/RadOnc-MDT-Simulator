"""Entry point for the packaged Windows application."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        default_data_dir = Path(local_app_data) / "RadOncMDT" / "Data"
    else:
        default_data_dir = Path.home() / "AppData" / "Local" / "RadOncMDT" / "Data"

    # Set this before importing the application: run_store reads the data path
    # during module import so the installed database never lives beside the EXE.
    os.environ.setdefault("RADONC_DATA_DIR", str(default_data_dir))

    from app.main import app
    import uvicorn

    port = int(os.environ.get("RADONC_PORT", "8765"))
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False,
        workers=1,
        loop="asyncio",
        http="h11",
        ws="none",
    )


if __name__ == "__main__":
    main()
