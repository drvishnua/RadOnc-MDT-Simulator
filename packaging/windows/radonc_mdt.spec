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
    datas=[
        (str(frontend_dist), "frontend/dist"),
        (str(repo_root / "docs" / "reference_catalogue_v1.json"), "docs"),
        (str(repo_root / "docs" / "mdt_stress_case_inputs_v1.json"), "docs"),
        (str(repo_root / "docs" / "mdt_stress_cases_v1.json"), "docs"),
    ],
    hiddenimports=[
        # Core application and configuration
        "app",
        "app.config",
        "app.main",
        # Schemas and clinical fields contracts
        "app.schemas",
        "app.agent_schemas",
        "app.clinical_fields",
        "app.round_schemas",
        # Agent catalog and specialist profiles
        "app.agents",
        "app.agents.catalog",
        # Dynamic services introduced and expanded in v2
        "app.services",
        "app.services.batch_runner",
        "app.services.case_integrity",
        "app.services.chair_report_quality",
        "app.services.execution_lock",
        "app.services.gpu_telemetry",
        "app.services.intake_screening",
        "app.services.intake_store",
        "app.services.mdt_generation",
        "app.services.mdt_rounds",
        "app.services.ollama",
        "app.services.reference_catalogue",
        "app.services.run_store",
        "app.services.stress_testing",
        # Concurrency and locking utilities
        "app.utils",
        "app.utils.concurrency_lock",
        # Uvicorn and runtime infrastructure
        "uvicorn.logging",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan.on",
        "sqlite3",
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
