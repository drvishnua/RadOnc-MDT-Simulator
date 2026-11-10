#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Get-InstalledAppHealth {
    try {
        $result = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 3
        if ($result.status -eq "ok" -and $result.application -eq "RadOnc MDT Simulator") {
            return $result
        }
    } catch {
        return $null
    }
    return $null
}

function Assert-NoActiveTrainingRuns {
    param(
        [Parameter(Mandatory = $true)][string]$DatabasePath,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$PythonExe
    )
    if (-not (Test-Path -LiteralPath $DatabasePath -PathType Leaf)) {
        Write-Host ("{0}: database not present; no saved run state to inspect." -f $Label)
        return
    }

    $probe = @'
import json
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1]).resolve()
uri = path.as_uri() + "?mode=ro"
connection = sqlite3.connect(uri, uri=True, timeout=5)
active_values = {"running", "queued", "pending", "in_progress", "processing"}
try:
    result = connection.execute("PRAGMA quick_check").fetchone()[0]
    if result != "ok":
        print("DATABASE_INTEGRITY_FAILED=" + str(result))
        sys.exit(4)
    active = []
    tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (table_name,) in tables:
        escaped = table_name.replace('"', '""')
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")')}
        if "status" not in columns:
            continue
        rows = connection.execute(
            f'SELECT status FROM "{escaped}" WHERE LOWER(TRIM(COALESCE(status, ""))) IN (?, ?, ?, ?, ?)',
            tuple(sorted(active_values)),
        ).fetchall()
        if rows:
            active.append({"table": table_name, "statuses": [row[0] for row in rows[:20]]})
    print("ACTIVE_RUNS=" + json.dumps(active, sort_keys=True))
    if active:
        sys.exit(3)
finally:
    connection.close()
'@

    $probe | & $PythonExe - $DatabasePath
    $resultCode = $LASTEXITCODE
    if ($resultCode -eq 3) {
        throw ("{0} contains active/queued run records. No application was started." -f $Label)
    }
    if ($resultCode -ne 0) {
        throw ("Could not validate {0} read-only (Python exit {1}). No application was started." -f $Label, $resultCode)
    }
    Write-Host ("{0}: SQLite quick_check passed and no active run status was found." -f $Label)
}

$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$installDir = Join-Path $localAppData "Programs\RadOncMDT"
try {
    $installedEntry = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -eq "RadOnc MDT Simulator" } |
        Select-Object -First 1
    if ($installedEntry -and $installedEntry.InstallLocation -and (Test-Path -LiteralPath $installedEntry.InstallLocation)) {
        $installDir = [string]$installedEntry.InstallLocation
    }
} catch {
    # Keep the documented per-user path.
}

$exe = Join-Path $installDir "RadOncMDT.exe"
$startScript = Join-Path $installDir "Start-RadOnc-MDT.ps1"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or -not (Test-Path -LiteralPath $startScript -PathType Leaf)) {
    throw "Installed RadOnc MDT executable or Start shortcut script is missing."
}

Write-Host ("INSTALL_ROOT={0}" -f $installDir)
Write-Host ("RUNNER_IDENTITY={0}\{1}" -f $env:USERDOMAIN, $env:USERNAME)
Write-Host ("RUNNER_SESSION_ID={0}" -f (Get-Process -Id $PID).SessionId)

$health = Get-InstalledAppHealth
if ($health) {
    Write-Host "APP_ALREADY_HEALTHY=True"
} else {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        $owners = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
        throw ("Port 8765 is occupied by process ID(s) {0}, but it does not identify as RadOnc MDT. Refusing to stop or replace it." -f ($owners -join ","))
    }

    $pythonExe = "C:\Python314\python.exe"
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($pythonCommand) { $pythonExe = $pythonCommand.Source }
    }
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw "A Python installation with sqlite3 is required for the read-only active-run preflight."
    }

    $dataDir = Join-Path $localAppData "RadOncMDT\Data"
    $installedDb = Join-Path $dataDir "simulation_runs.sqlite3"
    Assert-NoActiveTrainingRuns -DatabasePath $installedDb -Label "Installed-app database" -PythonExe $pythonExe

    if ($env:GITHUB_WORKSPACE) {
        $projectRoot = (Resolve-Path (Join-Path $env:GITHUB_WORKSPACE "..\..\..\..")).Path
        $sourceDb = Join-Path $projectRoot "Source\backend\data\simulation_runs.sqlite3"
        if ([IO.Path]::GetFullPath($sourceDb) -ne [IO.Path]::GetFullPath($installedDb)) {
            Assert-NoActiveTrainingRuns -DatabasePath $sourceDb -Label "Development-source database" -PythonExe $pythonExe
        }
    }

    $taskName = "RadOncMDT-StartupVerification-$env:GITHUB_RUN_ID"
    $taskPath = "\"
    $powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $startScript + '"'
    $action = New-ScheduledTaskAction -Execute $powershellExe -Argument $arguments -WorkingDirectory $installDir
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(10)
    $principal = New-ScheduledTaskPrincipal -UserId ("{0}\{1}" -f $env:USERDOMAIN, $env:USERNAME) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew

    $taskRegistered = $false
    $ready = $false
    try {
        Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
        $taskRegistered = $true
        Write-Host ("SCHEDULED_TASK_REGISTERED={0}" -f $taskName)
        Start-ScheduledTask -TaskName $taskName -TaskPath $taskPath

        for ($attempt = 0; $attempt -lt 75; $attempt++) {
            $health = Get-InstalledAppHealth
            if ($health) {
                $ready = $true
                break
            }
            Start-Sleep -Seconds 1
        }
        if (-not $ready) {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -TaskPath $taskPath -ErrorAction SilentlyContinue
            $stderr = Join-Path (Join-Path $localAppData "RadOncMDT\Logs") "backend.stderr.log"
            $details = if (Test-Path -LiteralPath $stderr) { (Get-Content -LiteralPath $stderr -Tail 40) -join [Environment]::NewLine } else { "No backend stderr log exists." }
            throw ("Scheduled startup did not produce a healthy endpoint. Task result={0}. {1}" -f $taskInfo.LastTaskResult, $details)
        }
    } catch {
        if ($taskRegistered) {
            Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false -ErrorAction SilentlyContinue
        }
        throw
    }

    Write-Host "SCHEDULED_TASK_STARTED_APP_HEALTHY=True"
    Write-Host ("SCHEDULED_TASK_NAME={0}" -f $taskName)
    "task_name=$taskName" | Add-Content -LiteralPath $env:GITHUB_OUTPUT -Encoding UTF8
}

$agents = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/agents" -TimeoutSec 10
if ($agents.returned_agent_count -ne 45) {
    throw ("Local app returned {0} role profiles, expected 45." -f $agents.returned_agent_count)
}
$runtime = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/runtime" -TimeoutSec 15
if (-not $runtime.ollama.reachable -or -not $runtime.ollama.configured_model_installed -or $runtime.ollama.configured_model -ne "qwen3.5:4b") {
    throw ("Local model status is not ready: " + ($runtime.ollama | ConvertTo-Json -Compress -Depth 5))
}
Write-Host "SAME_JOB_APP_HEALTH_OK"
Write-Host "LOCAL_MODEL_STATUS_OK"
Write-Host "ALL_45_ROLES_OK"
Write-Host "NO_INFERENCE_OR_PATIENT_WRITE_PERFORMED"
