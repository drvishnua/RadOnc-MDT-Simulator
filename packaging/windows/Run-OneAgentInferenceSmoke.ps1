#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Assert-NoActiveRunsReadOnly {
    param([Parameter(Mandatory=$true)][string]$DatabasePath, [Parameter(Mandatory=$true)][string]$Label, [Parameter(Mandatory=$true)][string]$PythonExe)
    if (-not (Test-Path -LiteralPath $DatabasePath -PathType Leaf)) {
        Write-Host ("{0}: database not found; no persisted runs to inspect." -f $Label)
        return
    }

    $probe = @'
import json
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1]).resolve()
connection = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True, timeout=5)
active_values = {"running", "queued", "pending", "in_progress", "processing"}
try:
    result = connection.execute("PRAGMA quick_check").fetchone()[0]
    if result != "ok":
        print("DATABASE_INTEGRITY_FAILED=" + str(result))
        sys.exit(4)
    active = []
    for (table_name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
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
    print("ACTIVE_RUN_RECORDS=" + json.dumps(active, sort_keys=True))
    if active:
        sys.exit(3)
finally:
    connection.close()
'@

    $probe | & $PythonExe - $DatabasePath
    $code = $LASTEXITCODE
    if ($code -eq 3) { throw ("{0} contains an active/queued MDT record. Smoke inference was not started." -f $Label) }
    if ($code -ne 0) { throw ("Could not validate {0} read-only (Python exit {1})." -f $Label,$code) }
    Write-Host ("{0}: database integrity passed; no active/queued persisted run." -f $Label)
}

$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 5
if ($health.status -ne "ok" -or $health.application -ne "RadOnc MDT Simulator") {
    throw "Installed application health endpoint is not ready."
}
$runtime = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/runtime" -TimeoutSec 10
if (-not $runtime.ollama.reachable -or -not $runtime.ollama.configured_model_installed -or $runtime.ollama.configured_model -ne "qwen3.5:4b") {
    throw ("Required local model is unavailable: " + ($runtime.ollama | ConvertTo-Json -Compress -Depth 5))
}

$pythonExe = "C:\Python314\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) { $pythonExe = $python.Source }
}
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw "Python with sqlite3 is required for read-only active-run preflight."
}

$installedDb = Join-Path $localAppData "RadOncMDT\Data\simulation_runs.sqlite3"
Assert-NoActiveRunsReadOnly -DatabasePath $installedDb -Label "Installed database" -PythonExe $pythonExe
if ($env:GITHUB_WORKSPACE) {
    $projectRoot = (Resolve-Path (Join-Path $env:GITHUB_WORKSPACE "..\..\..\..")).Path
    $sourceDb = Join-Path $projectRoot "Source\backend\data\simulation_runs.sqlite3"
    if ([IO.Path]::GetFullPath($sourceDb) -ne [IO.Path]::GetFullPath($installedDb)) {
        Assert-NoActiveRunsReadOnly -DatabasePath $sourceDb -Label "Development database" -PythonExe $pythonExe
    }
}

$dbHashBefore = $null
if (Test-Path -LiteralPath $installedDb -PathType Leaf) {
    $dbHashBefore = (Get-FileHash -LiteralPath $installedDb -Algorithm SHA256).Hash.ToLowerInvariant()
}

$nvidiaSmi = (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue).Source
if (-not $nvidiaSmi) {
    $candidate = Join-Path $env:windir "System32\nvidia-smi.exe"
    if (Test-Path -LiteralPath $candidate) { $nvidiaSmi = $candidate }
}
if (-not $nvidiaSmi) { throw "nvidia-smi.exe is not available; active GPU attribution cannot be sampled." }

$ollamaExe = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $ollamaExe) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe")
    )
    $ollamaExe = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
}
if (-not $ollamaExe) { throw "Ollama CLI was not found for model-placement sampling." }

$case = @{
    scenario_title = "Fictional incomplete-data inference smoke test"
    case_summary = "Fictional educational test payload intentionally supplies no confirmed primary site, histology, pathology, imaging, TNM stage, performance status, comorbidities, prior treatment, or patient preference. These details are not reported; they are not confirmed absent. Do not infer staging, negative findings, resectability, or a treatment recommendation. This one-request payload is used only to verify structured model inference and GPU telemetry."
    known_unknowns = @(
        "Primary site and subsite not reported",
        "Histology and pathology not reported",
        "Imaging and investigations not reported",
        "Clinical T, N and M categories and stage group not reported",
        "Performance status, comorbidities and prior treatment not reported",
        "Patient goals and preferences not reported"
    )
}
$payload = @{
    case = $case
    round_number = 1
} | ConvertTo-Json -Depth 8 -Compress

Write-Host "ONE_AGENT_INFERENCE_BEGIN"
Write-Host "INFERENCE_ENDPOINT=http://127.0.0.1:8765/api/agents/RO-01/assess"
Write-Host "MODEL=qwen3.5:4b"
Write-Host "NO_PATIENT_REGISTRATION_OR_RUN_ENDPOINT_WILL_BE_CALLED"

Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(220)
$requestContent = New-Object System.Net.Http.StringContent($payload,[System.Text.Encoding]::UTF8,"application/json")
$task = $client.PostAsync("http://127.0.0.1:8765/api/agents/RO-01/assess",$requestContent)

$gpuSamples = New-Object System.Collections.Generic.List[object]
$ollamaPsSamples = New-Object System.Collections.Generic.List[string]
$started = [DateTime]::UtcNow
$sampleIndex = 0
try {
    while (-not $task.IsCompleted -and (([DateTime]::UtcNow - $started).TotalSeconds -lt 210)) {
        $snapshot = & $nvidiaSmi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits 2>&1
        if ($LASTEXITCODE -eq 0 -and $snapshot) {
            $line = (@($snapshot) | Select-Object -First 1).ToString().Trim()
            $parts = $line.Split(",") | ForEach-Object { $_.Trim() }
            if ($parts.Count -ge 4) {
                $sample = [PSCustomObject]@{
                    elapsed_seconds = [Math]::Round(([DateTime]::UtcNow - $started).TotalSeconds,2)
                    gpu_utilization_percent = $parts[0]
                    memory_used_mib = $parts[1]
                    memory_total_mib = $parts[2]
                    power_watts = $parts[3]
                }
                $gpuSamples.Add($sample)
                Write-Host ("GPU_SAMPLE_{0} elapsed={1}s util={2}% mem={3}/{4}MiB power={5}W" -f $sampleIndex,$sample.elapsed_seconds,$sample.gpu_utilization_percent,$sample.memory_used_mib,$sample.memory_total_mib,$sample.power_watts)
            }
        }

        if (($sampleIndex % 2) -eq 0) {
            $psOutput = & $ollamaExe ps 2>&1
            $psText = (@($psOutput) -join " | ").Trim()
            if ($psText) {
                $ollamaPsSamples.Add($psText)
                Write-Host ("OLLAMA_PS_SAMPLE_{0}={1}" -f $sampleIndex,$psText)
            }
        }
        $sampleIndex++
        Start-Sleep -Milliseconds 400
    }

    if (-not $task.IsCompleted) {
        $client.CancelPendingRequests()
        throw "Single-agent inference exceeded 210 seconds and was cancelled."
    }

    $response = $task.GetAwaiter().GetResult()
    $responseText = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $response.IsSuccessStatusCode) {
        throw ("Single-agent endpoint returned HTTP {0}: {1}" -f [int]$response.StatusCode,$responseText)
    }
    $assessment = $responseText | ConvertFrom-Json
} finally {
    $requestContent.Dispose()
    $client.Dispose()
}

$elapsed = [Math]::Round(([DateTime]::UtcNow - $started).TotalSeconds,2)
if ($assessment.agent_id -ne "RO-01" -or $assessment.round_number -ne 1) {
    throw "Returned assessment did not match the requested RO-01/R1 identity."
}
if ($assessment.safety_boundary -ne "educational_simulation_only" -or $assessment.not_a_treatment_instruction -ne $true) {
    throw "The model response did not preserve the required educational safety metadata."
}
if ($assessment.evidence_claims.Count -gt 0) {
    throw "The model returned evidence claims despite evidence retrieval being unavailable; review the result."
}
if (@("supports","opposes","conditional","insufficient_information") -notcontains $assessment.position) {
    throw "The model returned an invalid position."
}

Write-Host "ONE_AGENT_REAL_INFERENCE_OK"
Write-Host "ASSESSMENT_SCHEMA_VALID=True"
Write-Host ("INFERENCE_ELAPSED_SECONDS={0}" -f $elapsed)
Write-Host ("POSITION={0}" -f $assessment.position)
Write-Host ("CONFIDENCE={0}" -f $assessment.confidence)
Write-Host ("PROVISIONAL_CONCLUSION={0}" -f $assessment.provisional_conclusion)
Write-Host ("PREFERRED_EDUCATIONAL_OPTION={0}" -f $assessment.preferred_educational_option)
Write-Host ("UNKNOWN_FIELDS={0}" -f (@($assessment.unknowns) -join " || "))
Write-Host ("CASE_DATA_INTEGRITY_FLAGS={0}" -f (@($assessment.case_data_integrity_flags) -join " || "))
Write-Host ("EVIDENCE_CLAIMS_COUNT={0}" -f @($assessment.evidence_claims).Count)

$numericUtil = @($gpuSamples | ForEach-Object { try { [int]$_.gpu_utilization_percent } catch { 0 } })
$gpuPositiveSamples = @($numericUtil | Where-Object { $_ -gt 0 }).Count
$maxUtil = if ($numericUtil.Count) { ($numericUtil | Measure-Object -Maximum).Maximum } else { 0 }
Write-Host ("GPU_SAMPLE_COUNT={0}" -f $gpuSamples.Count)
Write-Host ("GPU_NONZERO_UTILIZATION_SAMPLE_COUNT={0}" -f $gpuPositiveSamples)
Write-Host ("GPU_MAX_UTILIZATION_PERCENT={0}" -f $maxUtil)
Write-Host ("OLLAMA_PS_SAMPLE_COUNT={0}" -f $ollamaPsSamples.Count)
Write-Host ("OLLAMA_PS_GPU_PLACEMENT_OBSERVED={0}" -f [bool](@($ollamaPsSamples | Where-Object { $_ -match "GPU" }).Count))

$afterPs = & $ollamaExe ps 2>&1
Write-Host ("OLLAMA_PS_AFTER_INFERENCE={0}" -f ((@($afterPs) -join " | ").Trim()))

if ($dbHashBefore) {
    $dbHashAfter = (Get-FileHash -LiteralPath $installedDb -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($dbHashAfter -ne $dbHashBefore) {
        throw "The installed SQLite database changed during the non-persisted agent assessment."
    }
    Write-Host "PATIENT_DATABASE_BYTE_FOR_BYTE_UNCHANGED=True"
} else {
    Write-Host "PATIENT_DATABASE_NOT_PRESENT_AND_NOT_CREATED=True"
}
Write-Host "NO_MDT_RUN_CREATED=True"
