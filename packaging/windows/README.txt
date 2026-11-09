RadOnc MDT Simulator — local educational software
Version 0.1.0

FIRST START
- Install Ollama separately. Ollama and model weights are not included in this installer.
- Download the configured model separately with: ollama pull qwen3.5:4b
- Launch "RadOnc MDT Simulator" from the Start menu or desktop shortcut.
- The local application opens at http://127.0.0.1:8765.
- Python and Node.js are not required to run the installed application.
- Use "Stop RadOnc MDT Simulator" before uninstalling or moving its data.

DATA LOCATION AND PRESERVATION
- The application database is stored under %LOCALAPPDATA%\RadOncMDT\Data.
- Logs are stored under %LOCALAPPDATA%\RadOncMDT\Logs.
- Uninstalling the application preserves this user data.
- The installer does not remove, overwrite, or import any existing project database automatically.

OPTIONAL LEGACY DATABASE COPY
1. Stop the older local application.
2. Make a separate backup of the old simulation_runs.sqlite3 file.
3. Create this text file:
   %LOCALAPPDATA%\RadOncMDT\Data\legacy-db-path.txt
4. Put the full path to the old simulation_runs.sqlite3 file on its first line.
5. Start the installed application.
6. The application will copy the selected database only when the new destination database does not yet exist. It checks SQLite integrity before and after the copy. The original database is retained unchanged.
7. If the target database already exists, it is never replaced by the legacy copy.

SAFETY
- Use fictional training cases only.
- This educational simulator is not clinical decision support and is not validated for patient-care decisions.
- Evidence retrieval and independent guideline verification are not included.
- Model output can be incomplete, incorrect, or unsupported and must not be treated as a clinical recommendation.
