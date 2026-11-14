# Windows installer

The Windows x64 installer is a local-first educational build. It packages the FastAPI service and compiled Vite frontend in a PyInstaller one-directory bundle, then wraps that bundle with Inno Setup 6.

## Build prerequisites

- Python 3.11
- Node.js 22
- Inno Setup 6
- Dependencies in backend/requirements.txt and frontend/package.json
- PyInstaller 6.x (installed in the isolated packaging environment)

## Build

From the repository root:

1. Build the frontend from the frontend directory:
   npm install --no-audit --no-fund
   npm test
   npm run build
2. Return to the repository root and install backend/build dependencies:
   python -m pip install -r backend/requirements.txt "pyinstaller>=6.11,<7"
3. Build the one-directory application:
   python -m PyInstaller --noconfirm --clean --distpath dist --workpath build/pyinstaller packaging/windows/radonc_mdt.spec
4. Compile the installer:
   ISCC.exe packaging/windows/RadOnc-MDT.iss

The installer is written to dist/installer/RadOnc-MDT-Simulator-Setup.exe.

## Runtime model and data

The installer does not bundle Python, Node.js, Ollama, or model weights into separate machine services. The executable includes its Python runtime and application dependencies. Ollama must be installed separately, and qwen3.5:4b must be downloaded separately.

The installed application binds only to 127.0.0.1:8765. User data is stored under %LOCALAPPDATA%\\RadOncMDT\\Data; logs are under %LOCALAPPDATA%\\RadOncMDT\\Logs. Uninstall preserves both folders.

The optional legacy-db-path.txt procedure in the installed README enables a deliberate, integrity-checked SQLite copy from the old source database. The source file is never deleted or modified, and an existing destination is never overwritten.

This beta is for fictional educational training cases only. Evidence retrieval, guideline verification, clinical validation, and real-patient workflows are not included.
