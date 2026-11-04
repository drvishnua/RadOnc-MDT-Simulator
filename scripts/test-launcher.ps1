#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  (Join-Path $PSScriptRoot "start-local.ps1"),
  [ref]$tokens,
  [ref]$errors
) | Out-Null
if ($errors.Count -gt 0) {
  $errors | ForEach-Object { Write-Error $_.Message }
  exit 1
}
$node = Get-Command node -ErrorAction Stop
$versionText = (& $node.Source --version).Trim()
$version = [version]$versionText.TrimStart("v")
if (-not (($version.Major -eq 20 -and $version -ge [version]"20.19.0") -or ($version.Major -eq 22 -and $version -ge [version]"22.12.0") -or $version.Major -gt 22)) {
  throw "CI Node version $versionText does not satisfy Vite 7 requirements."
}
Write-Host "Launcher syntax valid. CI Node $versionText is Vite-compatible."
