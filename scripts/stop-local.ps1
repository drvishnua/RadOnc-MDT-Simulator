#requires -Version 5.1
$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$LogDir = Join-Path $RepoRoot ".local-logs"

function Stop-LauncherProcess([string]$Name, [string]$PidFile, [string]$ExpectedCommandPattern) {
    if (-not (Test-Path $PidFile)) {
        Write-Host "$Name was not started by this launcher (no PID file)."
        return
    }

    $storedPid = 0
    if (-not [int]::TryParse((Get-Content $PidFile -Raw).Trim(), [ref]$storedPid)) {
        Write-Warning "Invalid PID file for $Name; leaving processes untouched."
        return
    }

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $storedPid" -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "$Name is already stopped."
        return
    }

    if ($processInfo.CommandLine -match $ExpectedCommandPattern) {
        Stop-Process -Id $storedPid -Force -ErrorAction SilentlyContinue
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped $Name."
    } else {
        Write-Warning "$Name PID no longer matches the launcher command. It was not stopped."
    }
}

Stop-LauncherProcess "FastAPI backend" (Join-Path $LogDir "backend.pid") "uvicorn app\.main:app"
Stop-LauncherProcess "Vite frontend" (Join-Path $LogDir "frontend.pid") "vite[\\/]bin[\\/]vite\.js"

Write-Host "Ollama was left running so other local tools can continue using it."
