#requires -Version 5.1
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$LogDir = Join-Path $RepoRoot ".local-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Stage([string]$Message) {
    Write-Host ""
    Write-Host "== $Message ==" -ForegroundColor Cyan
}

function Test-HttpEndpoint([string]$Uri) {
    try {
        $null = Invoke-RestMethod -Uri $Uri -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

Write-Stage "Check local prerequisites"
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    $PythonPath = [string](& py -3 -c "import sys; print(sys.executable)")
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python 3.11 or newer is required. Install Python, then rerun this script."
    }
    $PythonPath = [string](& python -c "import sys; print(sys.executable)")
}

$PythonVersion = [string](& $PythonPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if ([version]$PythonVersion -lt [version]"3.11") {
    throw "Python 3.11 or newer is required. Found $PythonVersion."
}
Write-Host "Python $PythonVersion : $PythonPath"

$NodeCommand = Get-Command node -ErrorAction SilentlyContinue
$NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
$NodeExecutable = if ($NodeCommand) { $NodeCommand.Source } else { $null }
$NpmExecutable = if ($NpmCommand) { $NpmCommand.Source } else { $null }

function Test-SupportedNode([string]$Executable) {
    if (-not $Executable -or -not (Test-Path $Executable)) { return $false }
    try {
        $versionText = (& $Executable --version 2>$null).Trim()
        $version = [version]$versionText.TrimStart("v")
        return (($version -ge [version]"20.19.0" -and $version.Major -eq 20) -or ($version -ge [version]"22.12.0" -and $version.Major -eq 22) -or $version.Major -gt 22)
    } catch {
        return $false
    }
}

# Vite 7 needs Node 20.19+ or 22.12+. Prefer the runner's cached Node 22
# whenever the Node already on Windows PATH is too old.
if (-not (Test-SupportedNode $NodeExecutable)) {
    $runnerNodeCache = Join-Path (Split-Path -Parent $RepoRoot) "actions-runner\_work\_tool\node"
    $selectedNodeBin = $null

    if (Test-Path $runnerNodeCache) {
        $nodeCandidates = Get-ChildItem $runnerNodeCache -Directory |
            Sort-Object { try { [version]$_.Name } catch { [version]"0.0" } } -Descending

        foreach ($candidate in $nodeCandidates) {
            $candidateBin = Join-Path $candidate.FullName "x64"
            $candidateNode = Join-Path $candidateBin "node.exe"
            $candidateNpm = Join-Path $candidateBin "npm.cmd"

            if ((Test-SupportedNode $candidateNode) -and (Test-Path $candidateNpm)) {
                $selectedNodeBin = $candidateBin
                $NodeExecutable = $candidateNode
                $NpmExecutable = $candidateNpm
                break
            }
        }
    }

    if ($selectedNodeBin) {
        # Put the supported cached Node first for child processes launched by npm.
        $env:PATH = $selectedNodeBin + ";" + $env:PATH
    } else {
        throw "Unsupported Node.js version '$(& $NodeExecutable --version 2>$null)'. Vite 7 requires Node 20.19+ or 22.12+. No compatible cached Node.js was found under actions-runner\_work\_tool\node."
    }
} elseif (-not $NpmExecutable) {
    throw "Node.js is supported, but npm.cmd was not found. Install/repair the matching Node.js distribution."
}

Write-Host "Using Node: $NodeExecutable"
Write-Host (& $NodeExecutable --version)
Write-Host "Using npm: $NpmExecutable"
Write-Host (& $NpmExecutable --version)

Write-Stage "Prepare backend environment"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating backend virtual environment..."
    & $PythonPath -m venv (Join-Path $BackendDir ".venv")
}
Write-Host "Installing/verifying backend dependencies..."
& $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $BackendDir "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Backend dependency installation failed."
}

Write-Stage "Prepare frontend dependencies"
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    try {
        & $NpmExecutable install --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
    } finally {
        Pop-Location
    }
}

Write-Stage "Start local Ollama if needed"
if (-not (Test-HttpEndpoint "http://127.0.0.1:11434/api/version")) {
    $OllamaCommand = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if ($OllamaCommand) {
        Start-Process -FilePath $OllamaCommand.Source -ArgumentList @("serve") -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir "ollama.stdout.log") -RedirectStandardError (Join-Path $LogDir "ollama.stderr.log")
        for ($i = 0; $i -lt 15; $i++) {
            Start-Sleep -Seconds 2
            if (Test-HttpEndpoint "http://127.0.0.1:11434/api/version") { break }
        }
    }
}
if (Test-HttpEndpoint "http://127.0.0.1:11434/api/version") {
    Write-Host "Ollama API is reachable."
} else {
    Write-Warning "Ollama is not reachable. The dashboard can still open, but local inference will be unavailable."
}

Write-Stage "Start FastAPI backend"
if (Test-HttpEndpoint "http://127.0.0.1:8000/health") {
    Write-Host "Backend is already responding at http://127.0.0.1:8000"
} else {
    $backendProcess = Start-Process -FilePath $VenvPython -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogDir "backend.stdout.log") -RedirectStandardError (Join-Path $LogDir "backend.stderr.log")
    Set-Content -Path (Join-Path $LogDir "backend.pid") -Value $backendProcess.Id
    $BackendReady = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-HttpEndpoint "http://127.0.0.1:8000/health") {
            $BackendReady = $true
            break
        }
    }
    if (-not $BackendReady) {
        throw "Backend did not start. Check .local-logs/backend.stderr.log."
    }
}

Write-Stage "Start Vite frontend"
if (Test-HttpEndpoint "http://127.0.0.1:5173") {
    Write-Host "Frontend is already responding at http://127.0.0.1:5173"
} else {
    $viteEntry = Join-Path $FrontendDir "node_modules\vite\bin\vite.js"
    if (-not (Test-Path $viteEntry)) {
        throw "Vite entry point was not found at $viteEntry. Check the frontend dependency installation."
    }

    # Quote the Vite entry path: the research folder contains spaces (for example, "Post MD").
    $viteArguments = "`"$viteEntry`" --host 127.0.0.1 --port 5173 --strictPort"
    $frontendProcess = Start-Process -FilePath $NodeExecutable -ArgumentList $viteArguments -WorkingDirectory $FrontendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogDir "frontend.stdout.log") -RedirectStandardError (Join-Path $LogDir "frontend.stderr.log")
    Set-Content -Path (Join-Path $LogDir "frontend.pid") -Value $frontendProcess.Id
    $FrontendReady = $false
    for ($i = 0; $i -lt 45; $i++) {
        Start-Sleep -Seconds 1
        $frontendProcess.Refresh()
        if ($frontendProcess.HasExited) {
            $frontendError = ""
            $frontendLog = Join-Path $LogDir "frontend.stderr.log"
            if (Test-Path $frontendLog) {
                $frontendError = (Get-Content $frontendLog -Tail 30) -join [Environment]::NewLine
            }
            throw "Vite exited before becoming ready (exit code $($frontendProcess.ExitCode)). $frontendError"
        }
        if (Test-HttpEndpoint "http://127.0.0.1:5173") {
            $FrontendReady = $true
            break
        }
    }
    if (-not $FrontendReady) {
        $frontendLog = Join-Path $LogDir "frontend.stderr.log"
        $frontendError = if (Test-Path $frontendLog) { (Get-Content $frontendLog -Tail 30) -join [Environment]::NewLine } else { "No Vite stderr log was created." }
        throw "Frontend did not start within 45 seconds. $frontendError"
    }
}

Write-Stage "Ready"
Write-Host "Dashboard:  http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "API docs:   http://127.0.0.1:8000/docs"
Write-Host "Logs:       $LogDir"
Write-Host "The services are bound to localhost only."
Start-Process "http://127.0.0.1:5173"
