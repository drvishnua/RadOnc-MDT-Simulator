#requires -Version 5.1
<#
Self-provisioning local Ollama runtime for RadOnc MDT.
- Reuses an existing local Ollama endpoint if available.
- Otherwise starts an existing Ollama CLI, or downloads a pinned portable
  Windows runtime into the RadOnc user-data directory.
- Keeps the model store separate from the application install folder.
- Never stops, upgrades, or overwrites an existing Ollama installation.
#>

$RadOncModelName = "qwen3.5:4b"
$RadOncOllamaVersion = "0.40.14"
$RadOncOllamaZipUrl = "https://github.com/ollama/ollama/releases/download/v0.40.14/ollama-windows-amd64.zip"
$RadOncOllamaZipSha256 = "65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29"
$RadOncDefaultOllamaUrl = "http://127.0.0.1:11434"
$RadOncBundledOllamaUrl = "http://127.0.0.1:11435"

function Get-RadOncOllamaVersion {
    param([Parameter(Mandatory = $true)][string]$BaseUrl)
    try {
        return Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/version") -TimeoutSec 5
    } catch {
        return $null
    }
}

function Get-RadOncOllamaTags {
    param([Parameter(Mandatory = $true)][string]$BaseUrl)
    try {
        return Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/tags") -TimeoutSec 10
    } catch {
        return $null
    }
}

function Test-RadOncModelInstalled {
    param(
        [AllowNull()][object]$Tags,
        [Parameter(Mandatory = $true)][string]$ModelName
    )
    if ($null -eq $Tags -or $null -eq $Tags.models) { return $false }
    foreach ($model in @($Tags.models)) {
        $name = [string]$model.name
        if (-not $name) { $name = [string]$model.model }
        if ([string]::Equals($name, $ModelName, [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Find-RadOncOllamaExecutable {
    $command = Get-Command "ollama.exe" -ErrorAction SilentlyContinue
    if ($command -and (Test-Path -LiteralPath $command.Source -PathType Leaf)) {
        return [string]$command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return $candidate
        }
    }
    return $null
}

function Test-RadOncPortListening {
    param([Parameter(Mandatory = $true)][int]$Port)
    try {
        return (@(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop).Count -gt 0)
    } catch {
        return $false
    }
}

function Get-RadOncFreeBytes {
    param([Parameter(Mandatory = $true)][string]$Path)
    $root = [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Path))
    $driveName = $root.TrimEnd("\").TrimEnd(":")
    $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
    return [int64]$drive.Free
}

function Wait-RadOncOllamaReady {
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [AllowNull()][System.Diagnostics.Process]$Process
    )
    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        if ($Process) {
            $Process.Refresh()
            if ($Process.HasExited) {
                throw "Ollama exited before its API became ready. Check the Ollama log files."
            }
        }
        if (Get-RadOncOllamaVersion -BaseUrl $BaseUrl) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    throw "Ollama did not become ready at $BaseUrl within $TimeoutSeconds seconds."
}

function Start-RadOncOllamaServer {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [AllowNull()][string]$ModelDirectory,
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [switch]$ManagedRuntime
    )

    if (Get-RadOncOllamaVersion -BaseUrl $BaseUrl) { return $null }

    $port = [int]([Uri]$BaseUrl).Port
    if (Test-RadOncPortListening -Port $port) {
        throw "Port $port is occupied by a service that did not identify itself as Ollama. No process was stopped."
    }

    $env:OLLAMA_HOST = ("127.0.0.1:" + $port)
    if ($ModelDirectory) {
        New-Item -ItemType Directory -Force -Path $ModelDirectory | Out-Null
        $env:OLLAMA_MODELS = $ModelDirectory
    }

    $env:PATH = $WorkingDirectory + ";" + $env:PATH
    $stdout = Join-Path $LogDirectory "ollama.stdout.log"
    $stderr = Join-Path $LogDirectory "ollama.stderr.log"
    $process = Start-Process -FilePath $Executable -ArgumentList @("serve") -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr

    if ($ManagedRuntime) {
        $pidPath = Join-Path (Split-Path -Parent $ModelDirectory) "AIEngine\ollama-server.pid"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pidPath) | Out-Null
        Set-Content -LiteralPath $pidPath -Value $process.Id -Encoding ASCII
    }

    Wait-RadOncOllamaReady -BaseUrl $BaseUrl -TimeoutSeconds 45 -Process $process | Out-Null
    return $process
}

function Install-RadOncPortableOllama {
    param(
        [Parameter(Mandatory = $true)][string]$ProductDataRoot
    )

    $engineRoot = Join-Path $ProductDataRoot "AIEngine\Ollama"
    $ollamaExe = Join-Path $engineRoot "ollama.exe"
    if (Test-Path -LiteralPath $ollamaExe -PathType Leaf) {
        return $ollamaExe
    }

    $freeBytes = Get-RadOncFreeBytes -Path $ProductDataRoot
    $requiredBytes = 8GB
    if ($freeBytes -lt $requiredBytes) {
        throw ("At least 8 GB of free disk space is required to provision the local AI engine and model. Available: {0:N1} GB." -f ($freeBytes / 1GB))
    }

    $downloadDirectory = Join-Path $ProductDataRoot "AIEngine\Downloads"
    New-Item -ItemType Directory -Force -Path $downloadDirectory | Out-Null
    $archivePath = Join-Path $downloadDirectory "ollama-windows-amd64-v0.40.14.zip"
    $temporaryRoot = Join-Path $downloadDirectory "extract"
    if (Test-Path -LiteralPath $engineRoot) { Remove-Item -LiteralPath $engineRoot -Recurse -Force }
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }

    Write-Host ("Downloading the pinned Ollama {0} Windows runtime (about 1.5 GB)..." -f $RadOncOllamaVersion)
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $client = New-Object System.Net.WebClient
    try {
        $client.DownloadFile($RadOncOllamaZipUrl, $archivePath)
    } finally {
        $client.Dispose()
    }

    $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $RadOncOllamaZipSha256) {
        Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
        throw "The downloaded Ollama runtime failed its SHA-256 verification. It was not installed."
    }

    New-Item -ItemType Directory -Force -Path $temporaryRoot | Out-Null
    Expand-Archive -LiteralPath $archivePath -DestinationPath $temporaryRoot -Force
    $foundExecutable = Get-ChildItem -LiteralPath $temporaryRoot -Filter "ollama.exe" -File -Recurse | Select-Object -First 1
    if (-not $foundExecutable) {
        throw "The verified Ollama archive did not contain ollama.exe."
    }

    New-Item -ItemType Directory -Force -Path $engineRoot | Out-Null
    Get-ChildItem -LiteralPath $temporaryRoot -Force | Copy-Item -Destination $engineRoot -Recurse -Force
    $installedExecutable = Join-Path $engineRoot "ollama.exe"
    if (-not (Test-Path -LiteralPath $installedExecutable -PathType Leaf)) {
        $nestedExecutable = Get-ChildItem -LiteralPath $engineRoot -Filter "ollama.exe" -File -Recurse | Select-Object -First 1
        if (-not $nestedExecutable) {
            throw "Ollama runtime extraction did not produce a usable executable."
        }
        $installedExecutable = $nestedExecutable.FullName
    }

    Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host ("Ollama runtime installed and verified at {0}" -f $installedExecutable)
    return $installedExecutable
}

function Invoke-RadOncModelPull {
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [AllowNull()][string]$OllamaExecutable,
        [Parameter(Mandatory = $true)][string]$ProductDataRoot
    )

    $freeBytes = Get-RadOncFreeBytes -Path $ProductDataRoot
    if ($freeBytes -lt 5GB) {
        throw ("At least 5 GB of free disk space is required to download {0}. Available: {1:N1} GB." -f $RadOncModelName, ($freeBytes / 1GB))
    }

    Write-Host ""
    Write-Host ("The {0} model is not present. Downloading it now (approximately 3.4 GB)." -f $RadOncModelName)
    Write-Host "Keep this window open until the model download and verification finish."

    if ($OllamaExecutable -and (Test-Path -LiteralPath $OllamaExecutable -PathType Leaf)) {
        $env:OLLAMA_HOST = ([Uri]$BaseUrl).Host + ":" + ([Uri]$BaseUrl).Port
        & $OllamaExecutable pull $RadOncModelName
        if ($LASTEXITCODE -ne 0) {
            throw "Ollama model download failed with exit code $LASTEXITCODE."
        }
    } else {
        $body = @{ name = $RadOncModelName; stream = $false } | ConvertTo-Json -Compress
        $pullResult = Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/pull") -Method Post -ContentType "application/json" -Body $body -TimeoutSec 7200
        if ($pullResult.error) { throw ("Ollama model download failed: " + [string]$pullResult.error) }
    }
}

function Ensure-RadOncAIEngine {
    param(
        [Parameter(Mandatory = $true)][string]$DataDirectory,
        [Parameter(Mandatory = $true)][string]$LogDirectory
    )

    $productDataRoot = Split-Path -Parent $DataDirectory
    $modelDirectory = Join-Path $productDataRoot "Models"
    New-Item -ItemType Directory -Force -Path $productDataRoot, $modelDirectory, $LogDirectory | Out-Null

    # Prefer a pre-existing user Ollama service on its standard port. This avoids
    # downloading a second runtime or duplicating a model already on the laptop.
    $baseUrl = $RadOncDefaultOllamaUrl
    $version = Get-RadOncOllamaVersion -BaseUrl $baseUrl
    $ollamaExecutable = Find-RadOncOllamaExecutable

    if (-not $version -and $ollamaExecutable -and -not (Test-RadOncPortListening -Port 11434)) {
        Start-RadOncOllamaServer -Executable $ollamaExecutable -BaseUrl $baseUrl -WorkingDirectory (Split-Path -Parent $ollamaExecutable) -ModelDirectory $null -LogDirectory $LogDirectory | Out-Null
        $version = Get-RadOncOllamaVersion -BaseUrl $baseUrl
    }

    # If the default port is occupied by something other than Ollama, or Ollama
    # is not installed, use a dedicated portable runtime on port 11435.
    if (-not $version) {
        $baseUrl = $RadOncBundledOllamaUrl
        $version = Get-RadOncOllamaVersion -BaseUrl $baseUrl

        if (-not $version) {
            $ollamaExecutable = Install-RadOncPortableOllama -ProductDataRoot $productDataRoot
            $engineDirectory = Split-Path -Parent $ollamaExecutable
            Start-RadOncOllamaServer -Executable $ollamaExecutable -BaseUrl $baseUrl -WorkingDirectory $engineDirectory -ModelDirectory $modelDirectory -LogDirectory $LogDirectory -ManagedRuntime | Out-Null
            $version = Get-RadOncOllamaVersion -BaseUrl $baseUrl
        } else {
            $portableExecutable = Join-Path $productDataRoot "AIEngine\Ollama\ollama.exe"
            if (Test-Path -LiteralPath $portableExecutable -PathType Leaf) {
                $ollamaExecutable = $portableExecutable
            }
        }
    }

    if (-not $version) {
        throw "No working local Ollama service could be started. See the Ollama logs under %LOCALAPPDATA%\RadOncMDT\Logs."
    }

    $tags = Get-RadOncOllamaTags -BaseUrl $baseUrl
    if (-not (Test-RadOncModelInstalled -Tags $tags -ModelName $RadOncModelName)) {
        if ($baseUrl -eq $RadOncBundledOllamaUrl) {
            Invoke-RadOncModelPull -BaseUrl $baseUrl -OllamaExecutable $ollamaExecutable -ProductDataRoot $productDataRoot -RequireLocalDiskSpace
        } else {
            Invoke-RadOncModelPull -BaseUrl $baseUrl -OllamaExecutable $ollamaExecutable -ProductDataRoot $productDataRoot
        }
        $modelFound = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            $tags = Get-RadOncOllamaTags -BaseUrl $baseUrl
            if (Test-RadOncModelInstalled -Tags $tags -ModelName $RadOncModelName) {
                $modelFound = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        if (-not $modelFound) {
            throw ("Ollama completed the pull command, but {0} was not listed by /api/tags." -f $RadOncModelName)
        }
    }

    Write-Host ("AI engine ready: Ollama {0}; model {1}; endpoint {2}" -f $version.version, $RadOncModelName, $baseUrl)
    Write-Host ("Model files: {0}" -f $modelDirectory)
    return $baseUrl
}
