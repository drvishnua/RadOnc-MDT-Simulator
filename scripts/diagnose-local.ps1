#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Continue"
$SourceRoot = (Resolve-Path $SourceRoot).Path
Write-Host "=== RADONC LOCAL APP DIAGNOSTIC ==="
Write-Host "SOURCE_ROOT=$SourceRoot"

$statePath = Join-Path $SourceRoot ".radonc-sync-state.json"
if (Test-Path $statePath) {
    try {
        $state = Get-Content -Path $statePath -Raw | ConvertFrom-Json
        Write-Host "SOURCE_COMMIT=$($state.commit)"
        Write-Host "SOURCE_BRANCH=$($state.branch)"
    } catch {
        Write-Warning "Could not parse the source sync manifest: $($_.Exception.Message)"
    }
}

foreach ($relative in @(
    "frontend\index.html",
    "frontend\src\main.tsx",
    "frontend\src\App.tsx",
    "frontend\src\styles.css",
    "frontend\node_modules\vite\bin\vite.js",
    "backend\app\main.py"
)) {
    Write-Host ("FILE {0} EXISTS={1}" -f $relative,(Test-Path (Join-Path $SourceRoot $relative)))
}

Write-Host "=== LISTENING SERVICES ==="
foreach ($port in @(5173,8000,11434)) {
    $connections = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
    if ($connections.Count -eq 0) {
        Write-Host "PORT $port NOT LISTENING"
        continue
    }
    foreach ($connection in $connections) {
        $proc = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $connection.OwningProcess) -ErrorAction SilentlyContinue
        Write-Host ("PORT {0} PID {1} PROCESS {2} COMMAND {3}" -f $port,$connection.OwningProcess,$proc.Name,$proc.CommandLine)
    }
}

function Test-Endpoint([string]$Name,[string]$Uri) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 12
        $body = [string]$response.Content
        Write-Host ("ENDPOINT {0} STATUS={1} TYPE={2} LENGTH={3}" -f $Name,[int]$response.StatusCode,$response.Headers["Content-Type"],$body.Length)
        if ($Name -eq "VITE_ROOT") {
            Write-Host ("VITE_ROOT_HTML=" + $body.Substring(0,[Math]::Min(900,$body.Length)))
        } elseif ($Name -eq "VITE_ENTRY" -or $Name -eq "VITE_APP_MODULE") {
            Write-Host ("{0}_HEAD={1}" -f $Name,$body.Substring(0,[Math]::Min(1800,$body.Length)))
        } elseif ($Name -like "BACKEND_*") {
            Write-Host ("{0}_BODY={1}" -f $Name,$body.Substring(0,[Math]::Min(1200,$body.Length)))
        }
        return $true
    } catch {
        Write-Host ("ENDPOINT {0} FAILED: {1}" -f $Name,$_.Exception.Message)
        if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
        return $false
    }
}

Write-Host "=== HTTP ENDPOINTS ==="
$viteOk = Test-Endpoint "VITE_ROOT" "http://127.0.0.1:5173/"
$entryOk = Test-Endpoint "VITE_ENTRY" "http://127.0.0.1:5173/src/main.tsx"
$appModuleOk = Test-Endpoint "VITE_APP_MODULE" "http://127.0.0.1:5173/src/App.tsx"
$stylesOk = Test-Endpoint "VITE_STYLES" "http://127.0.0.1:5173/src/styles.css"
$apiOk = Test-Endpoint "BACKEND_HEALTH" "http://127.0.0.1:8000/health"
$runtimeOk = Test-Endpoint "BACKEND_RUNTIME" "http://127.0.0.1:8000/api/runtime"
$agentsOk = Test-Endpoint "BACKEND_AGENTS" "http://127.0.0.1:8000/api/agents"

Write-Host "=== HEADLESS EDGE RENDER CHECK ==="
$edgeCandidates = @(
    (Join-Path ([Environment]::GetFolderPath("ProgramFilesX86")) "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path ([Environment]::GetFolderPath("ProgramFiles")) "Microsoft\Edge\Application\msedge.exe")
)
$edgeExe = $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$reactMounted = $null
if ($edgeExe) {
    $tempDir = Join-Path $env:RUNNER_TEMP ("radonc-edge-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    $domPath = Join-Path $tempDir "dom.html"
    $stderrPath = Join-Path $tempDir "edge.stderr.log"
    $profileDir = Join-Path $tempDir "profile"
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    # Quote the profile path because the Windows runner's user path contains spaces.
    $edgeArgs = "--headless=new --no-first-run --disable-gpu --disable-extensions --no-sandbox --disable-background-networking --remote-allow-origins=* --user-data-dir=`"$profileDir`" --virtual-time-budget=7000 --dump-dom http://127.0.0.1:5173/"
    $edgeProcess = Start-Process -FilePath $edgeExe -ArgumentList $edgeArgs -PassThru -NoNewWindow -RedirectStandardOutput $domPath -RedirectStandardError $stderrPath
    $edgeExited = $edgeProcess.WaitForExit(20000)
    if (-not $edgeExited) {
        Write-Warning "Headless Edge did not exit within 20 seconds; terminating only the diagnostic Edge process."
        Stop-Process -Id $edgeProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "EDGE_EXITED_WITHIN_LIMIT=$edgeExited"
    if ($edgeExited) { Write-Host "EDGE_EXIT_CODE=$($edgeProcess.ExitCode)" }
    if (Test-Path $domPath) {
        $dom = Get-Content -Path $domPath -Raw
        if ([string]::IsNullOrWhiteSpace($dom)) {
            Write-Host "EDGE_DOM_EMPTY"
        } else {
            $reactMounted = $dom.Contains('class="app-shell"')
            Write-Host "EDGE_DOM_LENGTH=$($dom.Length)"
            Write-Host "REACT_APP_SHELL_MOUNTED=$reactMounted"
            Write-Host "EDGE_DOM_HEAD=$($dom.Substring(0,[Math]::Min(3600,$dom.Length)))"
        }
    } else {
        Write-Host "EDGE_DOM_OUTPUT_MISSING"
    }
    if (Test-Path $stderrPath) {
        Write-Host "EDGE_STDERR_TAIL"
        Get-Content $stderrPath -Tail 60
    }
} else {
    Write-Host "EDGE_HEADLESS_CHECK_SKIPPED: Microsoft Edge executable not found."
}

Write-Host "=== LOCAL LOG TAILS ==="
$logDir = Join-Path $SourceRoot ".local-logs"
foreach ($name in @("frontend.stderr.log","frontend.stdout.log","backend.stderr.log","backend.stdout.log")) {
    $path = Join-Path $logDir $name
    Write-Host "--- $name ---"
    if (Test-Path $path) { Get-Content $path -Tail 25 } else { Write-Host "LOG_NOT_FOUND" }
}

Write-Host "=== OLLAMA ==="
try {
    $ollama = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 5
    Write-Host "OLLAMA_REACHABLE version=$($ollama.version)"
} catch {
    Write-Host "OLLAMA_UNREACHABLE: $($_.Exception.Message)"
}

if (-not ($viteOk -and $entryOk -and $appModuleOk -and $stylesOk)) {
    throw "The Vite frontend is not serving all expected modules."
}
if ($null -ne $reactMounted -and -not $reactMounted) {
    throw "Headless Edge loaded the page but React did not mount .app-shell. Inspect the DOM and browser errors above."
}
Write-Host "LOCAL_APP_DIAGNOSTIC_COMPLETED"
