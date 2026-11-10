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
if ($bootstrap -notmatch '(?s)Get-FileHash.*?if\s*\(\$actualHash\s*-ne\s*\$RadOncOllamaZipSha256\)') {
    throw "Portable runtime checksum must be verified before extraction."
}
if ($bootstrap -notmatch "(?s)Invoke-RadOncModelPull.*?Get-RadOncOllamaTags.*?Test-RadOncModelInstalled") {
    throw "The model must be checked after the pull operation."
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
Write-Host "No Ollama process, model download, inference, or user database was touched by this static test."
