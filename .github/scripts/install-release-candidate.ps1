#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedSha256
)

$ErrorActionPreference = "Stop"

function Write-Stage([string]$Message) {
    Write-Host ""
    Write-Host ("=== {0} ===" -f $Message) -ForegroundColor Cyan
}

function Assert-NoActiveMdtRuns([string]$DatabasePath, [string]$Label, [string]$PythonExe) {
    if (-not (Test-Path -LiteralPath $DatabasePath -PathType Leaf)) {
        Write-Host ("{0}: no database found; no saved runs to inspect." -f $Label)
        return
    }

    $probe = @'
import json
import sqlite3
import sys

path = sys.argv[1]
active_values = {"running", "queued", "pending", "in_progress", "processing"}
connection = sqlite3.connect(f"file:{path.replace(chr(92), '/') }?mode=ro", uri=True, timeout=5)
try:
    check = connection.execute("PRAGMA quick_check").fetchone()[0]
    if check != "ok":
        print("DATABASE_INTEGRITY_FAILED=" + str(check))
        sys.exit(4)
    active = []
    tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (table_name,) in tables:
        escaped = table_name.replace('"', '""')
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")').fetchall()}
        if "status" not in columns:
            continue
        rows = connection.execute(
            f'SELECT status FROM "{escaped}" WHERE LOWER(TRIM(COALESCE(status, ""))) IN (?, ?, ?, ?, ?)',
            tuple(sorted(active_values)),
        ).fetchall()
        if rows:
            active.append({"table": table_name, "active_status_rows": [row[0] for row in rows[:20]]})
    print("ACTIVE_MDT_ROWS=" + json.dumps(active, sort_keys=True))
    if active:
        sys.exit(3)
finally:
    connection.close()
'@

    $probe | & $PythonExe - $DatabasePath
    $code = $LASTEXITCODE
    if ($code -eq 3) {
        throw ("{0} contains running/queued MDT records. Installation was aborted before stopping or changing the app." -f $Label)
    }
    if ($code -ne 0) {
        throw ("Could not integrity-check and inspect {0} (Python exit {1}). Installation was aborted." -f $Label, $code)
    }
    Write-Host ("{0}: database integrity and no-active-run check passed." -f $Label)
}

Write-Stage "Verify installer artifact"
if (-not (Test-Path -LiteralPath $InstallerPath -PathType Leaf)) {
    throw "The downloaded Windows Setup.exe is missing: $InstallerPath"
}
$actualSha = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha -ne $ExpectedSha256.ToLowerInvariant()) {
    throw ("Setup.exe checksum mismatch. Expected {0}; actual {1}. Nothing was installed." -f $ExpectedSha256, $actualSha)
}
Write-Host ("SETUP_EXE_SHA256_OK={0}" -f $actualSha)

$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
if ([string]::IsNullOrWhiteSpace($localAppData)) {
    throw "Windows did not return a LocalAppData path."
}
$installDir = Join-Path $localAppData "Programs\RadOncMDT"
$dataDir = Join-Path $localAppData "RadOncMDT\Data"
$logDir = Join-Path $localAppData "RadOncMDT\Logs"
$databasePath = Join-Path $dataDir "simulation_runs.sqlite3"

# Prefer the actual Inno Setup location if a previous version was installed
# somewhere other than the default per-user directory.
try {
    $installedEntry = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -eq "RadOnc MDT Simulator" } |
        Select-Object -First 1
    if ($installedEntry -and $installedEntry.InstallLocation -and (Test-Path -LiteralPath $installedEntry.InstallLocation)) {
        $installDir = [string]$installedEntry.InstallLocation
    }
} catch {
    # Use the documented per-user default when the registry entry is absent.
}

Write-Stage "Preflight existing app and databases"
$pythonExe = "C:\Python314\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonExe = $pythonCommand.Source }
}
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw "Python with sqlite3 is required for the read-only active-run guard. No installation changes were made."
}

Assert-NoActiveMdtRuns -DatabasePath $databasePath -Label "Installed-app database" -PythonExe $pythonExe

# Also inspect the separate development database. Never restart or stop its
# processes; this guard simply prevents an installer bootstrap from sharing
# Ollama while a development MDT batch is still running.
$workspace = $env:GITHUB_WORKSPACE
if ($workspace) {
    $projectRoot = (Resolve-Path (Join-Path $workspace "..\..\..\..")).Path
    $sourceDatabase = Join-Path $projectRoot "Source\backend\data\simulation_runs.sqlite3"
    if ([IO.Path]::GetFullPath($sourceDatabase) -ne [IO.Path]::GetFullPath($databasePath)) {
        Assert-NoActiveMdtRuns -DatabasePath $sourceDatabase -Label "Development-source database" -PythonExe $pythonExe
    }
}

$dbHashBefore = $null
if (Test-Path -LiteralPath $databasePath -PathType Leaf) {
    $dbHashBefore = (Get-FileHash -LiteralPath $databasePath -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Host ("EXISTING_DATABASE_SHA256_BEFORE_INSTALL={0}" -f $dbHashBefore)
} else {
    Write-Host "NO_EXISTING_INSTALLED_DATABASE"
}

$portListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue)
if ($portListeners.Count -gt 1) {
    throw "Multiple listeners own port 8765. Installation was aborted."
}
if ($portListeners.Count -eq 1) {
    $stopScript = Join-Path $installDir "Stop-RadOnc-MDT.ps1"
    if (-not (Test-Path -LiteralPath $stopScript -PathType Leaf)) {
        throw "Port 8765 is occupied but the installed app's guarded stop script is unavailable. No process was stopped."
    }
    Write-Stage "Safely stop the previous RadOnc application only"
    $stop = Start-Process -FilePath "powershell.exe" -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $stopScript + '"') -Wait -PassThru -WindowStyle Hidden
    if ($stop.ExitCode -ne 0) {
        throw ("The guarded app stop script refused to stop the process (exit {0}). Installation was aborted." -f $stop.ExitCode)
    }

    $released = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Seconds 1
        $remaining = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue)
        if ($remaining.Count -eq 0) {
            $released = $true
            break
        }
    }
    if (-not $released) {
        throw "Port 8765 did not become free. No installer was run."
    }
}
Write-Host "Only the previous RadOnc application process was eligible for stop. Ollama was not stopped or modified."

Write-Stage "Install verified Windows release candidate"
$setup = Start-Process -FilePath $InstallerPath -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") -Wait -PassThru
if ($setup.ExitCode -ne 0) {
    throw ("Setup.exe failed with exit code {0}." -f $setup.ExitCode)
}
$expectedExe = Join-Path $installDir "RadOncMDT.exe"
$startScript = Join-Path $installDir "Start-RadOnc-MDT.ps1"
$stopScript = Join-Path $installDir "Stop-RadOnc-MDT.ps1"
if (-not (Test-Path -LiteralPath $expectedExe -PathType Leaf)) {
    throw "Installed RadOncMDT.exe was not found at the per-user installation path."
}
if (-not (Test-Path -LiteralPath $startScript -PathType Leaf)) {
    throw "The installed first-run AI bootstrap launcher was not found."
}

if ($dbHashBefore) {
    $dbHashAfterSetup = (Get-FileHash -LiteralPath $databasePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($dbHashAfterSetup -ne $dbHashBefore) {
        throw "The setup operation changed the existing SQLite database before application startup."
    }
    Write-Host "INSTALLER_LEFT_DATABASE_BYTE_FOR_BYTE_UNCHANGED=True"
}

Write-Stage "Start installed app and first-run AI bootstrap"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$bootstrapStdout = Join-Path $logDir "release-candidate-bootstrap.stdout.log"
$bootstrapStderr = Join-Path $logDir "release-candidate-bootstrap.stderr.log"
$startArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $startScript + '"'
$bootstrapProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $startArguments -WorkingDirectory $installDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $bootstrapStdout -RedirectStandardError $bootstrapStderr
$completed = $bootstrapProcess.WaitForExit(5400000)
if (-not $completed) {
    Stop-Process -Id $bootstrapProcess.Id -Force -ErrorAction SilentlyContinue
    throw "First-run bootstrap exceeded 90 minutes. Inspect the RadOnc bootstrap logs; no Ollama process was stopped."
}
$bootstrapProcess.Refresh()
if ($bootstrapProcess.ExitCode -ne 0) {
    $details = if (Test-Path -LiteralPath $bootstrapStderr) { (Get-Content $bootstrapStderr -Tail 80) -join [Environment]::NewLine } else { "No bootstrap stderr log was created." }
    throw ("First-run bootstrap failed with exit code {0}. {1}" -f $bootstrapProcess.ExitCode, $details)
}

Write-Stage "Verify installed application endpoints"
$health = $null
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 3
        if ($health.status -eq "ok" -and $health.application -eq "RadOnc MDT Simulator") { break }
    } catch {
        $health = $null
    }
    Start-Sleep -Seconds 1
}
if (-not $health -or $health.status -ne "ok" -or $health.application -ne "RadOnc MDT Simulator") {
    throw "The installed application did not return its expected localhost health response."
}

$webClient = New-Object System.Net.WebClient
try {
    $page = $webClient.DownloadString("http://127.0.0.1:8765/")
    if ($page -notmatch 'id="root"') { throw "The installed frontend root element was not served." }
    $assetMatch = [regex]::Match($page, 'src="(?<asset>/assets/[^"]+\.js)"')
    if (-not $assetMatch.Success) { throw "The installed frontend JavaScript bundle was not referenced." }
    $bundle = $webClient.DownloadString("http://127.0.0.1:8765" + $assetMatch.Groups["asset"].Value)
    if ($bundle.Length -lt 1000) { throw "The installed frontend JavaScript bundle was empty or truncated." }
} finally {
    $webClient.Dispose()
}

$agents = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/agents" -TimeoutSec 10
if ($agents.returned_agent_count -ne 45) {
    throw ("Installed API returned {0} specialist roles, expected 45." -f $agents.returned_agent_count)
}

$runtime = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/runtime" -TimeoutSec 15
if (-not $runtime.ollama.reachable -or -not $runtime.ollama.configured_model_installed) {
    throw ("Installed app cannot verify its configured local model: " + ($runtime.ollama | ConvertTo-Json -Depth 6 -Compress))
}
if ($runtime.ollama.configured_model -ne "qwen3.5:4b") {
    throw ("Installed app is configured for unexpected model: " + [string]$runtime.ollama.configured_model)
}

Write-Host "TARGET_LAPTOP_INSTALL_OK"
Write-Host "INSTALLED_APP_HEALTH_OK"
Write-Host "INSTALLED_FRONTEND_ASSETS_OK"
Write-Host "INSTALLED_45_SPECIALIST_ROLES_OK"
Write-Host "LOCAL_OLLAMA_REACHABLE_OK"
Write-Host ("LOCAL_OLLAMA_VERSION={0}" -f $runtime.ollama.version)
Write-Host ("CONFIGURED_MODEL_PRESENT_OK={0}" -f $runtime.ollama.configured_model)
Write-Host "No MDT run, patient record, agent assessment, or model inference was created by this installation check."
Write-Host "RadOnc MDT is left running at http://127.0.0.1:8765."
