#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$SourceRoot = (Resolve-Path $SourceRoot).Path
$BackendDir = Join-Path $SourceRoot "backend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$DatabasePath = Join-Path $BackendDir "data\simulation_runs.sqlite3"
$LogDir = Join-Path $SourceRoot ".local-logs"

if (-not (Test-Path $VenvPython)) {
    throw "Backend virtual-environment Python was not found: $VenvPython"
}
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-ExpectedBackendProcess($Process) {
    if (-not $Process -or $Process.Name -ine "python.exe") { return $false }

    $expectedExe = [IO.Path]::GetFullPath($VenvPython)
    $command = [string]$Process.CommandLine
    if ([string]::IsNullOrWhiteSpace($command)) { return $false }

    # Verify the command-line executable is the exact backend venv Python.
    $commandExe = $null
    $arguments = $null
    if ($command.StartsWith('"')) {
        $closingQuote = $command.IndexOf('"', 1)
        if ($closingQuote -lt 2) { return $false }
        $commandExe = $command.Substring(1, $closingQuote - 1)
        $arguments = $command.Substring($closingQuote + 1)
    } else {
        $firstSpace = $command.IndexOf(" ")
        if ($firstSpace -lt 1) { return $false }
        $commandExe = $command.Substring(0, $firstSpace)
        $arguments = $command.Substring($firstSpace + 1)
    }
    try { $commandExe = [IO.Path]::GetFullPath($commandExe) } catch { return $false }
    if ($commandExe -ine $expectedExe) { return $false }

    # A Windows venv process can report the base interpreter as its image.
    # Accept only the venv Python or the base python.exe declared by pyvenv.cfg.
    if (-not [string]::IsNullOrWhiteSpace([string]$Process.ExecutablePath)) {
        try {
            $actualImage = [IO.Path]::GetFullPath([string]$Process.ExecutablePath)
            $allowedImages = @($expectedExe)
            $venvConfig = Join-Path $BackendDir ".venv\pyvenv.cfg"
            if (Test-Path $venvConfig) {
                foreach ($configLine in (Get-Content $venvConfig)) {
                    if ($configLine.StartsWith("home =")) {
                        $baseHome = $configLine.Substring($configLine.IndexOf("=") + 1).Trim()
                        $allowedImages += [IO.Path]::GetFullPath((Join-Path $baseHome "python.exe"))
                        break
                    }
                }
            }
            if (-not ($allowedImages | Where-Object { $_ -ieq $actualImage })) { return $false }
        } catch {
            return $false
        }
    }

    return (
        $arguments -match '(?i)(?:^|\s)-m\s+uvicorn\s+app\.main:app(?:\s|$)' -and
        $arguments -match '(?i)--host\s+127\.0\.0\.1(?:\s|$)' -and
        $arguments -match '(?i)--port\s+8000(?:\s|$)'
    )
}

Write-Host "=== GUARDED LOCAL BACKEND RESTART ==="
Write-Host "Source: $SourceRoot"
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)

if ($listenerPids.Count -gt 1) {
    throw "Multiple processes own port 8000. Refusing to stop any process."
}

if ($listenerPids.Count -eq 1) {
    if (-not (Test-Path $DatabasePath)) {
        throw "The simulation database is missing; active inference state cannot be checked. Refusing restart."
    }

    $databaseCheck = @'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
if not db_path.is_file():
    print("DATABASE_NOT_FOUND")
    sys.exit(2)

try:
    connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=5)
    try:
        running = []
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        for (table_name,) in tables:
            escaped_name = table_name.replace('"', '""')
            columns = {
                row[1] for row in connection.execute(f'PRAGMA table_info("{escaped_name}")').fetchall()
            }
            if "status" not in columns:
                continue
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{escaped_name}" WHERE LOWER(COALESCE(status, "")) = ?',
                ("running",),
            ).fetchone()[0]
            if count:
                running.append({"table": table_name, "running_rows": count})
        print("RUNNING_STATE=" + str(running))
        if running:
            sys.exit(3)
    finally:
        connection.close()
except Exception as error:
    print("DATABASE_CHECK_FAILED=" + repr(error))
    sys.exit(4)
'@

    $databaseCheck | & $VenvPython - $DatabasePath
    if ($LASTEXITCODE -ne 0) {
        throw "An MDT run may be active, or the database could not be inspected (Python exit $LASTEXITCODE). Backend was not stopped."
    }

    $allProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $processById = @{}
    foreach ($process in $allProcesses) {
        $processById[[int]$process.ProcessId] = $process
    }

    $listenerProcess = $processById[[int]$listenerPids[0]]
    if (-not (Test-ExpectedBackendProcess $listenerProcess)) {
        Write-Host "Port 8000 listener candidate did not match the guarded Source backend identity:"
        Write-Host "PID=$($listenerProcess.ProcessId) NAME=$($listenerProcess.Name) EXECUTABLE=$($listenerProcess.ExecutablePath)"
        Write-Host "COMMAND=$($listenerProcess.CommandLine)"
        throw "Port 8000 is not owned by the expected Source backend Uvicorn process. Refusing to stop it."
    }

    $rootProcess = $listenerProcess
    while ($true) {
        $parent = $processById[[int]$rootProcess.ParentProcessId]
        if (Test-ExpectedBackendProcess $parent) {
            $rootProcess = $parent
        } else {
            break
        }
    }

    $targets = @()
    $queue = New-Object 'System.Collections.Generic.Queue[object]'
    $queue.Enqueue(@{ ProcessId = [int]$rootProcess.ProcessId; Depth = 0 })
    $seen = @{}

    while ($queue.Count -gt 0) {
        $item = $queue.Dequeue()
        $processId = [int]$item.ProcessId
        if ($seen.ContainsKey($processId)) { continue }
        $seen[$processId] = $true

        $process = $processById[$processId]
        if (-not (Test-ExpectedBackendProcess $process)) {
            throw "Backend process ancestry changed during inspection. Refusing restart."
        }
        $targets += [PSCustomObject]@{ Process = $process; Depth = [int]$item.Depth }

        foreach ($candidate in $allProcesses) {
            if ([int]$candidate.ParentProcessId -eq $processId -and (Test-ExpectedBackendProcess $candidate)) {
                $queue.Enqueue(@{ ProcessId = [int]$candidate.ProcessId; Depth = ([int]$item.Depth + 1) })
            }
        }
    }

    if (-not ($targets.Process | Where-Object { [int]$_.ProcessId -eq [int]$listenerPids[0] })) {
        throw "The port listener was not included in the verified backend process tree."
    }

    Write-Host ("Verified backend process tree: " + (($targets.Process | ForEach-Object { $_.ProcessId }) -join ", "))
    foreach ($target in ($targets | Sort-Object Depth -Descending)) {
        Stop-Process -Id ([int]$target.Process.ProcessId) -Force -ErrorAction Stop
    }

    $portReleased = $false
    for ($attempt = 0; $attempt -lt 15; $attempt++) {
        Start-Sleep -Seconds 1
        $remaining = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)
        if ($remaining.Count -eq 0) {
            $portReleased = $true
            break
        }
    }
    if (-not $portReleased) {
        throw "Port 8000 did not become free after stopping the verified backend process tree."
    }
} else {
    Write-Host "No process is listening on port 8000; starting the backend without stopping anything."
}

# Use Win32_Process.Create to launch the venv interpreter directly, outside the
# current GitHub Actions job process tree. This avoids orphan cleanup killing it.
$backendCommandLine = '"' + $VenvPython + '" -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
$spawnResult = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $backendCommandLine
    CurrentDirectory = $BackendDir
}
if ([int]$spawnResult.ReturnValue -ne 0) {
    throw "Windows could not launch the backend (Win32_Process.Create=$($spawnResult.ReturnValue))."
}
$spawnedPid = [int]$spawnResult.ProcessId
Write-Host "Detached backend process PID: $spawnedPid"

$healthy = $false
$listenerPid = $null
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 1) {
        throw "Multiple processes are listening on port 8000 after backend startup."
    }
    if ($listeners.Count -eq 1) {
        $listenerPid = [int]$listeners[0].OwningProcess
        $listenerProcess = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $listenerPid) -ErrorAction Stop
        if (-not (Test-ExpectedBackendProcess $listenerProcess)) {
            throw "Port 8000 was acquired by a process other than the expected Source backend. Refusing to accept it."
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
            if ($health.status -eq "ok") {
                $healthy = $true
                break
            }
        } catch {
            # Continue polling until the startup window expires.
        }
    }
}
if (-not $healthy -or -not $listenerPid) {
    $spawnedProcess = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $spawnedPid) -ErrorAction SilentlyContinue
    $spawnedDetails = if ($spawnedProcess) { "NAME=$($spawnedProcess.Name) COMMAND=$($spawnedProcess.CommandLine) IMAGE=$($spawnedProcess.ExecutablePath)" } else { "The launched backend process exited before opening port 8000." }
    throw "New backend did not pass /health within 30 seconds. $spawnedDetails"
}
Set-Content -Path (Join-Path $LogDir "backend.pid") -Value $listenerPid -Encoding ASCII

$preflightHeaders = @{
    Origin = "http://127.0.0.1:5173"
    "Access-Control-Request-Method" = "DELETE"
    "Access-Control-Request-Headers" = "content-type"
}
$preflight = Invoke-WebRequest -UseBasicParsing -Method Options -Uri "http://127.0.0.1:8000/api/patients/__cors_preflight_probe__" -Headers $preflightHeaders -TimeoutSec 5
if ([int]$preflight.StatusCode -ne 200) {
    throw "Backend is healthy, but the patient DELETE CORS preflight returned HTTP $([int]$preflight.StatusCode)."
}
if ($preflight.Headers["Access-Control-Allow-Origin"] -ne "http://127.0.0.1:5173") {
    throw "Backend is healthy, but the local Vite origin was not allowed by CORS."
}
if ([string]$preflight.Headers["Access-Control-Allow-Methods"] -notmatch '(?i)\bDELETE\b') {
    throw "Backend is healthy, but DELETE is absent from Access-Control-Allow-Methods."
}

# Keep the dashboard frontend available after the Actions job ends as well.
$FrontendDir = Join-Path $SourceRoot "frontend"
$ViteEntry = Join-Path $FrontendDir "node_modules\vite\bin\vite.js"
if (-not (Test-Path $ViteEntry)) {
    throw "Vite entry point was not found at $ViteEntry. Frontend dependencies must be installed before starting the dashboard."
}

$NodeCommand = Get-Command node -ErrorAction SilentlyContinue
$NodeExecutable = if ($NodeCommand) { $NodeCommand.Source } else { $null }
function Test-SupportedNodeForVite([string]$Executable) {
    if (-not $Executable -or -not (Test-Path $Executable)) { return $false }
    try {
        $versionText = (& $Executable --version 2>$null).Trim()
        $version = [version]$versionText.TrimStart("v")
        return (($version -ge [version]"20.19.0" -and $version.Major -eq 20) -or ($version -ge [version]"22.12.0" -and $version.Major -eq 22) -or $version.Major -gt 22)
    } catch {
        return $false
    }
}

if (-not (Test-SupportedNodeForVite $NodeExecutable)) {
    $runnerNodeCache = Join-Path (Split-Path -Parent $SourceRoot) "actions-runner\_work\_tool\node"
    $selectedNode = $null
    if (Test-Path $runnerNodeCache) {
        $nodeCandidates = Get-ChildItem $runnerNodeCache -Directory |
            Sort-Object { try { [version]$_.Name } catch { [version]"0.0" } } -Descending
        foreach ($candidate in $nodeCandidates) {
            $candidateNode = Join-Path (Join-Path $candidate.FullName "x64") "node.exe"
            if (Test-SupportedNodeForVite $candidateNode) {
                $selectedNode = $candidateNode
                break
            }
        }
    }
    if (-not $selectedNode) {
        throw "A supported Node.js runtime (20.19+ or 22.12+) was not found for Vite."
    }
    $NodeExecutable = $selectedNode
}

$viteListeners = @(Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue)
if ($viteListeners.Count -gt 1) {
    throw "Multiple processes are listening on port 5173; refusing to replace the dashboard frontend."
}
if ($viteListeners.Count -eq 0) {
    $viteCommandLine = '"' + $NodeExecutable + '" "' + $ViteEntry + '" --host 127.0.0.1 --port 5173 --strictPort'
    $viteSpawn = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $viteCommandLine
        CurrentDirectory = $FrontendDir
    }
    if ([int]$viteSpawn.ReturnValue -ne 0) {
        throw "Windows could not launch Vite (Win32_Process.Create=$($viteSpawn.ReturnValue))."
    }
    Write-Host "Detached Vite process PID: $($viteSpawn.ProcessId)"
}

$viteReady = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    Start-Sleep -Seconds 1
    $viteListeners = @(Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue)
    if ($viteListeners.Count -gt 1) {
        throw "Multiple processes are listening on port 5173 after Vite startup."
    }
    if ($viteListeners.Count -eq 1) {
        $vitePid = [int]$viteListeners[0].OwningProcess
        $viteProcess = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $vitePid) -ErrorAction Stop
        $viteProcessCommand = [string]$viteProcess.CommandLine
        if ($viteProcess.Name -ine "node.exe" -or
            $viteProcessCommand -notmatch [regex]::Escape($ViteEntry) -or
            $viteProcessCommand -notmatch '(?i)--host\s+127\.0\.0\.1(?:\s|$)' -or
            $viteProcessCommand -notmatch '(?i)--port\s+5173(?:\s|$)') {
            throw "Port 5173 is not owned by the expected Source Vite process. Refusing to accept it."
        }
        try {
            $viteRoot = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:5173/" -TimeoutSec 3
            $viteAppModule = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:5173/src/App.tsx" -TimeoutSec 5
            if ([int]$viteRoot.StatusCode -eq 200 -and [int]$viteAppModule.StatusCode -eq 200) {
                $viteReady = $true
                break
            }
        } catch {
            # Continue polling while Vite completes its initial dependency scan.
        }
    }
}
if (-not $viteReady) {
    throw "Vite did not serve both / and /src/App.tsx successfully within 45 seconds. Inspect the local frontend stderr log."
}
Set-Content -Path (Join-Path $LogDir "frontend.pid") -Value $vitePid -Encoding ASCII
Write-Host "VITE_FRONTEND_READY"
Write-Host "Vite PID: $vitePid"
Write-Host "Dashboard root and transformed App.tsx: HTTP 200"

# Exercise the real registry DELETE route using one uniquely named disposable
# record. No simulation run or model inference is started.
$smokeName = "RADONC-DELETE-SMOKE-" + [Guid]::NewGuid().ToString("N")
$smokePayload = @{
    patient_name = $smokeName
    case = @{
        scenario_title = "Disposable registry deletion check"
        case_summary = "Temporary non-clinical placeholder created only to verify registry save, retrieval, and deletion."
    }
} | ConvertTo-Json -Depth 8
$smokePatient = $null
try {
    $smokePatient = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/patients" -ContentType "application/json" -Body $smokePayload -TimeoutSec 10
    $smokePatientId = [string]$smokePatient.patient_id
    if ([string]::IsNullOrWhiteSpace($smokePatientId)) { throw "Patient creation did not return a patient_id." }
    $savedSmokePatient = Invoke-RestMethod -Uri ("http://127.0.0.1:8000/api/patients/" + $smokePatientId) -TimeoutSec 10
    if ($savedSmokePatient.patient_name -ne $smokeName -or $savedSmokePatient.versions.Count -ne 1) {
        throw "Disposable patient retrieval did not match the created record."
    }
    $deletedSmokePatient = Invoke-WebRequest -UseBasicParsing -Method Delete -Uri ("http://127.0.0.1:8000/api/patients/" + $smokePatientId) -TimeoutSec 10
    if ([int]$deletedSmokePatient.StatusCode -ne 200) { throw "Disposable patient DELETE returned HTTP $([int]$deletedSmokePatient.StatusCode)." }

    $notFoundConfirmed = $false
    try {
        $null = Invoke-RestMethod -Uri ("http://127.0.0.1:8000/api/patients/" + $smokePatientId) -TimeoutSec 10
    } catch {
        $response = $_.Exception.Response
        if ($response -and [int]$response.StatusCode -eq 404) {
            $notFoundConfirmed = $true
        } else {
            throw
        }
    }
    if (-not $notFoundConfirmed) { throw "Deleted disposable patient remained retrievable." }
    $registry = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/patients" -TimeoutSec 10
    if (@($registry.patients | Where-Object { $_.patient_id -eq $smokePatientId }).Count -gt 0) {
        throw "Deleted disposable patient remains in the registry list."
    }
    Write-Host "PATIENT_DELETE_SMOKE_OK"
    Write-Host "Disposable patient identifier: $($smokePatient.patient_identifier)"
    Write-Host "Create, retrieve, DELETE HTTP 200, detail 404, and registry absence verified."
} catch {
    if ($smokePatient -and $smokePatient.patient_id) {
        try {
            Invoke-WebRequest -UseBasicParsing -Method Delete -Uri ("http://127.0.0.1:8000/api/patients/" + $smokePatient.patient_id) -TimeoutSec 10 | Out-Null
        } catch {
            # Preserve the original failure; cleanup is best effort only for this unique smoke record.
        }
    }
    throw
}

Write-Host "BACKEND_RESTART_OK"
Write-Host "Backend PID: $listenerPid"
Write-Host "Health: HTTP 200"
Write-Host "Patient DELETE CORS preflight: HTTP 200; DELETE allowed"
Write-Host "Backend stderr log: $stderr"
