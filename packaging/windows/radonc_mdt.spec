# PyInstaller one-directory build. Run from the repository root.
from pathlib import Path

repo_root = Path(SPECPATH).resolve().parents[1]
backend_dir = repo_root / "backend"
frontend_dist = repo_root / "frontend" / "dist"

if not (frontend_dist / "index.html").is_file():
    raise RuntimeError("Frontend build not found. Run the Vite production build first.")

a = Analysis(
    [str(backend_dir / "launch_installed.py")],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[(str(frontend_dist), "frontend/dist")],
    hiddenimports=[
        "app.main",
        "app.services.run_store",
        "uvicorn.logging",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RadOncMDT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RadOncMDT",
)
