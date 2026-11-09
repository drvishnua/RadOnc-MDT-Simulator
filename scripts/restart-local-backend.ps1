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
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction Stop)
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

$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")
$stdout = Join-Path $LogDir "backend.restart.$timestamp.stdout.log"
$stderr = Join-Path $LogDir "backend.restart.$timestamp.stderr.log"
$backendProcess = Start-Process -FilePath $VenvPython -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -Path (Join-Path $LogDir "backend.pid") -Value $backendProcess.Id -Encoding ASCII

$healthy = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    $backendProcess.Refresh()
    if ($backendProcess.HasExited) {
        throw "New backend exited with code $($backendProcess.ExitCode). See $stderr"
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
if (-not $healthy) {
    throw "New backend did not pass /health within 30 seconds. See $stderr"
}

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

Write-Host "BACKEND_RESTART_OK"
Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Health: HTTP 200"
Write-Host "Patient DELETE CORS preflight: HTTP 200; DELETE allowed"
Write-Host "Backend stderr log: $stderr"
 } | Select-Object -First 1
                if ($homeLine -and $homeLine -match '^\s*home\s*=\s*(.+?)\s*
        $arguments -match '(?i)(?:^|\s)-m\s+uvicorn\s+app\.main:app(?:\s|$)' -and
        $arguments -match '(?i)--host\s+127\.0\.0\.1(?:\s|$)' -and
        $arguments -match '(?i)--port\s+8000(?:\s|$)'
    )
}

Write-Host "=== GUARDED LOCAL BACKEND RESTART ==="
Write-Host "Source: $SourceRoot"
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction Stop)
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

$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")
$stdout = Join-Path $LogDir "backend.restart.$timestamp.stdout.log"
$stderr = Join-Path $LogDir "backend.restart.$timestamp.stderr.log"
$backendProcess = Start-Process -FilePath $VenvPython -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -Path (Join-Path $LogDir "backend.pid") -Value $backendProcess.Id -Encoding ASCII

$healthy = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    $backendProcess.Refresh()
    if ($backendProcess.HasExited) {
        throw "New backend exited with code $($backendProcess.ExitCode). See $stderr"
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
if (-not $healthy) {
    throw "New backend did not pass /health within 30 seconds. See $stderr"
}

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

Write-Host "BACKEND_RESTART_OK"
Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Health: HTTP 200"
Write-Host "Patient DELETE CORS preflight: HTTP 200; DELETE allowed"
Write-Host "Backend stderr log: $stderr"
) {
                    $basePython = Join-Path $Matches[1].Trim() "python.exe"
                    $allowedImages += [IO.Path]::GetFullPath($basePython)
                }
            }
            if (-not ($allowedImages | Where-Object { $_ -ieq $actualImage })) {
                return $false
            }
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
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction Stop)
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

$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")
$stdout = Join-Path $LogDir "backend.restart.$timestamp.stdout.log"
$stderr = Join-Path $LogDir "backend.restart.$timestamp.stderr.log"
$backendProcess = Start-Process -FilePath $VenvPython -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -Path (Join-Path $LogDir "backend.pid") -Value $backendProcess.Id -Encoding ASCII

$healthy = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    $backendProcess.Refresh()
    if ($backendProcess.HasExited) {
        throw "New backend exited with code $($backendProcess.ExitCode). See $stderr"
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
if (-not $healthy) {
    throw "New backend did not pass /health within 30 seconds. See $stderr"
}

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

Write-Host "BACKEND_RESTART_OK"
Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Health: HTTP 200"
Write-Host "Patient DELETE CORS preflight: HTTP 200; DELETE allowed"
Write-Host "Backend stderr log: $stderr"
