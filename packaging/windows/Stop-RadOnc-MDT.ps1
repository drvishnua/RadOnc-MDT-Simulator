#requires -Version 5.1
$ErrorActionPreference = "Continue"

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Executable = Join-Path $AppRoot "RadOncMDT.exe"
$LogDir = Join-Path (Join-Path $env:LOCALAPPDATA "RadOncMDT") "Logs"
$pidFile = Join-Path $LogDir "backend.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "No installed-app PID file exists. No process was stopped."
    exit 0
}

$storedPid = 0
if (-not [int]::TryParse((Get-Content -LiteralPath $pidFile -Raw).Trim(), [ref]$storedPid)) {
    Write-Warning "The installed-app PID file is invalid. No process was stopped."
    exit 1
}

$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $storedPid" -ErrorAction SilentlyContinue
if (-not $processInfo) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "RadOnc MDT is already stopped."
    exit 0
}

$expectedPath = [System.IO.Path]::GetFullPath($Executable)
$actualPath = [string]$processInfo.ExecutablePath
if (-not $actualPath -or -not [string]::Equals($expectedPath, $actualPath, [StringComparison]::OrdinalIgnoreCase)) {
    Write-Warning "PID $storedPid no longer points to the installed RadOncMDT.exe. It was not stopped."
    exit 1
}

Stop-Process -Id $storedPid -Force -ErrorAction Stop
Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "Stopped the installed RadOnc MDT application. Ollama was left running."
