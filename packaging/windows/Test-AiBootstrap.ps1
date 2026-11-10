#requires -Version 5.1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapPath = Join-Path $root "Ensure-RadOnc-AIEngine.ps1"
$startPath = Join-Path $root "Start-RadOnc-MDT.ps1"
$installerPath = Join-Path $root "RadOnc-MDT.iss"

foreach ($path in @($bootstrapPath, $startPath, $installerPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required installer source file is missing: $path"
    }
}

foreach ($path in @($bootstrapPath, $startPath)) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count -gt 0) {
        foreach ($item in $parseErrors) {
            Write-Host ("PARSE_ERROR file={0} line={1} column={2} message={3}" -f $path, $item.Extent.StartLineNumber, $item.Extent.StartColumnNumber, $item.Message)
        }
        throw "PowerShell parser rejected $path."
    }
    Write-Host ("POWERSHELL_PARSE_OK {0}" -f (Split-Path -Leaf $path))
}

$bootstrap = Get-Content -LiteralPath $bootstrapPath -Raw
$start = Get-Content -LiteralPath $startPath -Raw
$installer = Get-Content -LiteralPath $installerPath -Raw

$requiredBootstrapTokens = @(
    "qwen3.5:4b",
    "ollama-windows-amd64.zip",
    "65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29",
    "Get-FileHash",
    "/api/version",
    "/api/tags",
    "/api/pull",
    "127.0.0.1:11435",
    "OLLAMA_MODELS",
    "Get-NetTCPConnection"
)
foreach ($token in $requiredBootstrapTokens) {
    if (-not $bootstrap.Contains($token)) {
        throw "AI bootstrap safety/verification token is missing: $token"
    }
}

if ($bootstrap -match "(?im)^\s*Stop-Process\b") {
    throw "AI bootstrap must not stop an existing Ollama or model process."
}
if ($bootstrap -notmatch '(?s)\$pullProcess\s*=\s*Start-Process.*?-PassThru.*?-RedirectStandardOutput.*?-RedirectStandardError') {
    throw "Ollama model pull must capture process output without PowerShell native stderr conversion."
}
if ($bootstrap -notmatch '(?s)\$pullProcess\.Refresh\(\).*?\$pullProcess\.HasExited.*?\$pullProcess\.Kill\(\).*?\$pullProcess\.WaitForExit\(\).*?\$pullProcess\.Refresh\(\).*?\$pullProcess\.ExitCode\s*-ne\s*0') {
    throw "Ollama model pull must wait for its owned process handle before validating the exit code."
}
if ($bootstrap -notmatch '(?s)\$downloadTimeoutSeconds\s*=\s*3600.*?HOSTED_CPU_RUNTIME_DOWNLOAD_HEARTBEAT') {
    throw "Portable Ollama runtime download must have a timeout and progress heartbeat."
}
if ($bootstrap -notmatch '(?s)\$pullTimeoutSeconds\s*=\s*5400.*?HOSTED_CPU_MODEL_PULL_HEARTBEAT') {
    throw "Ollama model pull must have a timeout and progress heartbeat."
}
if ($bootstrap -notmatch '(?s)Get-FileHash.*?if\s*\(\$actualHash\s*-ne\s*\$RadOncOllamaZipSha256\)') {
    throw "Portable runtime checksum must be verified before extraction."
}
if ($bootstrap -notmatch "(?s)Invoke-RadOncModelPull.*?Get-RadOncOllamaTags.*?Test-RadOncModelInstalled") {
    throw "The model must be checked after the pull operation."
}
if ($bootstrap -match '(?s)&\s*\$OllamaExecutable\s+pull.*?2>&1\s*\|') {
    throw "Ollama native progress stderr must not be piped through PowerShell's error stream."
}
if ($bootstrap -notmatch '(?s)\$pullProcess\.ExitCode\s*-ne\s*0') {
    throw "Ollama model pull must validate the native process exit code."
}
if ($start -notmatch "Ensure-RadOncAIEngine") {
    throw "The installed application launcher does not invoke the AI bootstrap."
}
if ($installer -notmatch "Ensure-RadOnc-AIEngine\.ps1") {
    throw "The Inno Setup package does not include the AI bootstrap."
}
if ($installer -notmatch 'AIEngine"; Flags: uninsneveruninstall' -or $installer -notmatch 'Models"; Flags: uninsneveruninstall') {
    throw "The user-owned AI runtime/model folders must be preserved by uninstall."
}

Write-Host "AI_BOOTSTRAP_STATIC_ACCEPTANCE_OK"
Write-Host "Verified: PowerShell syntax, pinned runtime checksum guard, loopback endpoints, model verification, non-destructive process handling, launcher wiring, and uninstall preservation."
Write-Host "No real Ollama process, model download, inference, or user database was touched by these static and mocked-path tests."


# Exercise both decision paths with mocked endpoints/process launchers. These
# tests do not invoke a real Ollama executable, download a model, or make HTTP calls.
$testRoot = Join-Path $env:TEMP ("radonc-ai-bootstrap-test-" + [Guid]::NewGuid().ToString("N"))
$productRoot = Join-Path $testRoot "RadOncMDT"
$dataDirectory = Join-Path $productRoot "Data"
$logDirectory = Join-Path $productRoot "Logs"
New-Item -ItemType Directory -Force -Path $dataDirectory, $logDirectory | Out-Null

. $bootstrapPath

$global:RadOncMockPortableStarted = $false
$global:RadOncMockModelReady = $true
$global:RadOncMockModelPullCalled = $false
$global:RadOncMockPortableInstallCalled = $false

function Get-RadOncOllamaVersion {
    param([string]$BaseUrl)
    if ($BaseUrl -eq "http://127.0.0.1:11434") {
        return [PSCustomObject]@{ version = "mock-existing-ollama" }
    }
    return $null
}
function Get-RadOncOllamaTags {
    param([string]$BaseUrl)
    if ($global:RadOncMockModelReady) {
        return [PSCustomObject]@{ models = @([PSCustomObject]@{ name = "qwen3.5:4b" }) }
    }
    return [PSCustomObject]@{ models = @() }
}
function Find-RadOncOllamaExecutable { return $null }
function Test-RadOncPortListening {
    param([int]$Port)
    return $false
}

$existingEndpoint = Ensure-RadOncAIEngine -DataDirectory $dataDirectory -LogDirectory $logDirectory
if ($existingEndpoint -ne "http://127.0.0.1:11434") {
    throw "Existing-Ollama path did not retain the standard loopback endpoint."
}
if ($global:RadOncMockPortableInstallCalled -or $global:RadOncMockModelPullCalled) {
    throw "Existing installed model path unexpectedly attempted runtime installation or model pull."
}
Write-Host "AI_BOOTSTRAP_REUSE_EXISTING_MODEL_OK"

# Reset function behaviour to model an unavailable standard Ollama endpoint.
$global:RadOncMockPortableStarted = $false
$global:RadOncMockModelReady = $false
$global:RadOncMockModelPullCalled = $false
$global:RadOncMockPortableInstallCalled = $false

function Get-RadOncOllamaVersion {
    param([string]$BaseUrl)
    if ($BaseUrl -eq "http://127.0.0.1:11435" -and $global:RadOncMockPortableStarted) {
        return [PSCustomObject]@{ version = "mock-portable-ollama" }
    }
    return $null
}
function Get-RadOncOllamaTags {
    param([string]$BaseUrl)
    if ($global:RadOncMockModelReady) {
        return [PSCustomObject]@{ models = @([PSCustomObject]@{ name = "qwen3.5:4b" }) }
    }
    return [PSCustomObject]@{ models = @() }
}
function Install-RadOncPortableOllama {
    param([string]$ProductDataRoot)
    $global:RadOncMockPortableInstallCalled = $true
    $fakeExecutable = Join-Path $testRoot "mock-ollama.exe"
    Set-Content -LiteralPath $fakeExecutable -Value "mock executable" -Encoding ASCII
    return $fakeExecutable
}
function Start-RadOncOllamaServer {
    param(
        [string]$Executable,
        [string]$BaseUrl,
        [string]$WorkingDirectory,
        [AllowNull()][string]$ModelDirectory,
        [string]$LogDirectory,
        [switch]$ManagedRuntime
    )
    if ($BaseUrl -ne "http://127.0.0.1:11435" -or -not $ManagedRuntime) {
        throw "Portable fallback did not use the isolated 11435 endpoint and managed-runtime flag."
    }
    $global:RadOncMockPortableStarted = $true
}
function Invoke-RadOncModelPull {
    param(
        [string]$BaseUrl,
        [AllowNull()][string]$OllamaExecutable,
        [string]$ProductDataRoot,
        [switch]$RequireLocalDiskSpace
    )
    if ($BaseUrl -ne "http://127.0.0.1:11435" -or -not $RequireLocalDiskSpace) {
        throw "Portable fallback did not enforce its disk-space preflight."
    }
    $global:RadOncMockModelPullCalled = $true
    $global:RadOncMockModelReady = $true
}

try {
    $portableEndpoint = Ensure-RadOncAIEngine -DataDirectory $dataDirectory -LogDirectory $logDirectory
    if ($portableEndpoint -ne "http://127.0.0.1:11435") {
        throw "Portable fallback did not return its isolated loopback endpoint."
    }
    if (-not $global:RadOncMockPortableInstallCalled -or -not $global:RadOncMockModelPullCalled) {
        throw "Portable fallback did not request runtime installation and model pull."
    }
    Write-Host "AI_BOOTSTRAP_PORTABLE_FALLBACK_OK"
} finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "AI_BOOTSTRAP_MOCKED_BRANCH_TESTS_OK"
