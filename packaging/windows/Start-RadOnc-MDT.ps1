#requires -Version 5.1
$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Executable = Join-Path $AppRoot "RadOncMDT.exe"
$ProductDataRoot = Join-Path $env:LOCALAPPDATA "RadOncMDT"
$DataDir = Join-Path $ProductDataRoot "Data"
$LogDir = Join-Path $ProductDataRoot "Logs"
$Port = 8765
$HealthUri = "http://127.0.0.1:$Port/health"

if (-not (Test-Path $Executable)) {
    throw "RadOncMDT.exe was not found in the installed application folder."
}

New-Item -ItemType Directory -Force -Path $DataDir, $LogDir | Out-Null
$env:RADONC_DATA_DIR = $DataDir
$env:RADONC_PORT = [string]$Port

# Optional, explicit one-time legacy database source. The migration code
# integrity-checks and copies this file; it never deletes or edits the source.
$legacyPathFile = Join-Path $DataDir "legacy-db-path.txt"
$env:RADONC_LEGACY_DB_PATH = ""
if (Test-Path $legacyPathFile) {
    $legacyPath = (Get-Content -LiteralPath $legacyPathFile -Raw).Trim().Trim('"')
    if ($legacyPath -and (Test-Path -LiteralPath $legacyPath -PathType Leaf)) {
        $env:RADONC_LEGACY_DB_PATH = (Resolve-Path -LiteralPath $legacyPath).Path
        Write-Host "An explicit legacy database source was selected for safe first-run migration."
    } elseif ($legacyPath) {
        Write-Warning "The legacy database path file points to a file that does not exist. No migration will be attempted."
    }
}

$existing = $null
try {
    $existing = Invoke-RestMethod -Uri $HealthUri -TimeoutSec 2
} catch {
    $existing = $null
}

if ($existing) {
    if ($existing.application -ne "RadOnc MDT Simulator") {
        throw "Port $Port is already serving a different application. Nothing was stopped."
    }
    Start-Process "http://127.0.0.1:$Port"
    exit 0
}

$stdout = Join-Path $LogDir "backend.stdout.log"
$stderr = Join-Path $LogDir "backend.stderr.log"
$pidFile = Join-Path $LogDir "backend.pid"
$process = Start-Process -FilePath $Executable -WorkingDirectory $AppRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ASCII

$ready = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    $process.Refresh()
    if ($process.HasExited) {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        $details = if (Test-Path $stderr) { (Get-Content $stderr -Tail 30) -join [Environment]::NewLine } else { "No stderr log was created." }
        throw "RadOnc MDT exited before becoming ready (exit code $($process.ExitCode)). $details"
    }
    try {
        $health = Invoke-RestMethod -Uri $HealthUri -TimeoutSec 2
        if ($health.status -eq "ok" -and $health.application -eq "RadOnc MDT Simulator") {
            $ready = $true
            break
        }
    } catch {
        # The process is still starting; keep checking without restarting it.
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    $details = if (Test-Path $stderr) { (Get-Content $stderr -Tail 30) -join [Environment]::NewLine } else { "No stderr log was created." }
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    throw "RadOnc MDT did not become ready on port $Port. $details"
}

Start-Process "http://127.0.0.1:$Port"
Write-Host "RadOnc MDT is running at http://127.0.0.1:$Port"
Write-Host "User data: $DataDir"
Write-Host "Logs: $LogDir"
Write-Host "Ollama is managed separately and is not stopped by this launcher."
