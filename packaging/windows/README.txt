RadOnc MDT Simulator — local educational software
Version 0.1.0

FIRST START — AUTOMATIC LOCAL AI SETUP
- Launch "RadOnc MDT Simulator" from the Start menu or desktop shortcut.
- The first start checks for a local Ollama service and the configured qwen3.5:4b model.
- If an existing Ollama already has qwen3.5:4b, it is reused without downloading a second runtime or model.
- If Ollama is present but the model is missing, the launcher downloads qwen3.5:4b into that Ollama installation's configured model store.
- If Ollama is not installed, the launcher downloads the pinned Ollama 0.40.14 portable Windows runtime, verifies its SHA-256 checksum, and stores it under %LOCALAPPDATA%\RadOncMDT\AIEngine.
- The standalone runtime uses its own local model store at %LOCALAPPDATA%\RadOncMDT\Models and port 11435; it does not replace or stop another Ollama installation using port 11434.
- The qwen3.5:4b model is downloaded automatically on first start when it is not already available. Model download is approximately 3.4 GB. A fresh runtime download is approximately 1.5 GB.
- Internet access is required for first-time runtime/model provisioning. After the runtime and model are present, inference runs locally and does not require internet access.
- Allow at least 8 GB of free disk space for first-time provisioning when no Ollama runtime is installed.
- Keep the launcher window open during model download. If setup is interrupted, launch the application again to resume/complete provisioning.
- Python and Node.js are not required to run the installed application.
- The local application opens at http://127.0.0.1:8765.
- The app's Stop shortcut stops the RadOnc application only. Ollama remains a separate localhost service and is not stopped or upgraded by the app shortcut.

AI ENGINE LICENCES AND VERSIONS
- Portable Ollama runtime: version 0.40.14, obtained from the official Ollama GitHub release and verified against its published SHA-256. Ollama is MIT-licensed: https://github.com/ollama/ollama/blob/master/LICENSE
- Model: qwen3.5:4b, obtained from the Ollama model registry. The upstream Qwen3.5-4B model is listed under Apache License 2.0: https://huggingface.co/Qwen/Qwen3.5-4B
- Qwen model card and associated licence terms: https://huggingface.co/Qwen/Qwen3.5-4B

DATA HANDLING AND LOCAL SECURITY LIMITS
- This application is for fictional, non-identifiable training records only. Do not enter real patient names, dates of birth, hospital/MRN numbers, contact details, photographs/scans, medical-record extracts, or real patient health information.
- The sequential RAD identifiers are local training identifiers only. They are not hospital identifiers and do not register a person with a hospital.
- The registry display name is stored separately from the clinical case snapshot and is not sent to specialist agents. Case summaries and structured clinical fields are stored in the local SQLite database and supplied to the configured model for the educational simulation.
- The packaged launcher is designed to use Ollama on the local computer. Do not configure the model endpoint to a remote/cloud service or connect this application to an external model unless the data-flow, privacy, security and legal implications have been reviewed and explicitly approved.
- The backend is intended to bind only to 127.0.0.1. It has no user login or application-level authentication. Do not expose its port through LAN binding, a reverse proxy, port forwarding, remote desktop gateway or firewall rule; do not treat browser CORS restrictions as authentication.
- The SQLite database is stored in the current Windows user's local application-data directory. This version has not been verified as encrypted at rest. Protect the Windows account and device; do not store sensitive or real patient information in this application.
- Deleting a training record removes it from the application's active database through its normal deletion flow. It is not a guarantee of forensic erasure from SSD storage, operating-system backups, copied database files, logs or exported reports.
- Keep the app and its data on a trusted, access-controlled device. Back up data before upgrades or migrations. Complete backup/restore and secure-erasure guarantees are not currently claimed.

DATA LOCATION AND PRESERVATION
- The application database is stored under %LOCALAPPDATA%\RadOncMDT\Data.
- Logs are stored under %LOCALAPPDATA%\RadOncMDT\Logs.
- A self-provisioned Ollama runtime is stored under %LOCALAPPDATA%\RadOncMDT\AIEngine.
- The self-provisioned model store is stored under %LOCALAPPDATA%\RadOncMDT\Models.
- Uninstalling the application preserves the database, logs, local runtime and model files.
- The installer does not remove, overwrite, or import any existing project database automatically.
- When an existing Ollama installation is reused, its existing settings and model files are not moved or deleted; the required qwen3.5:4b model is added only when absent.

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
