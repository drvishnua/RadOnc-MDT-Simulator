"""Safety regressions for the isolated synthetic model-screening workflow."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "model-integrity-screening.yml"


def test_model_screening_is_limited_to_hosted_runner_and_development_branch():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "runs-on: windows-latest" in workflow
    assert "self-hosted" not in workflow
    assert "refs/heads/feature/four-round-mdt-and-performance" in workflow
    assert "[model-integrity-screen]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "cancel-in-progress: false" in workflow
    assert 'RADONC_AGENT_CONCURRENCY: "1"' in workflow
    assert 'RADONC_VALIDATION_CPU_ONLY: "1"' in workflow
    assert "timeout-minutes: 180" in workflow


def test_qwen_baseline_is_first_and_medgemma_requires_explicit_terms_attestation():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    qwen_call = workflow.index(
        'python backend/scripts/run_medgemma_screening.py --model "qwen3.5:4b"'
    )
    medgemma_gate = workflow.index(
        '$includeMed = ($env:MEDGEMMA_REQUESTED -eq "true")'
    )
    medgemma_pull = workflow.index('MODEL_SCREEN_MEDGEMMA_PULL_STARTED')
    medgemma_call = workflow.index(
        'python backend/scripts/run_medgemma_screening.py --model $medModel'
    )

    assert qwen_call < medgemma_gate < medgemma_pull < medgemma_call
    assert "inputs.include_medgemma == true" in workflow
    assert "inputs.hai_def_terms_accepted" in workflow
    assert "[hai-def-terms-accepted]" in workflow
    assert "[medgemma]" in workflow
    assert "github.event_name == 'push'" in workflow
    assert 'if ($env:HAI_DEF_TERMS_ACCEPTED -ne "true")' in workflow
    assert '$env:MEDGEMMA_REQUESTED -eq "true"' in workflow
    assert '$env:HAI_DEF_TERMS_ACCEPTED -eq "true"' in workflow
    assert "medgemma1.5:4b-it-q4_K_M" in workflow


def test_screening_workflow_uploads_raw_evidence_even_after_failure():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    upload_start = workflow.index("- name: Upload immutable model-screening evidence")
    upload_step = workflow[upload_start:]

    assert "if: always()" in upload_step
    assert "backend/validation_artifacts/model_screening/" in upload_step
    assert "retention-days: 30" in upload_step
    assert "manifest_" in workflow
    assert "gpu_measurement = \"NOT_PERFORMED\"" in workflow

def test_screening_finalizer_records_utc_time_and_attempts_safe_process_cleanup():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert '$manifest.execution.finished_at_utc = (Get-Date).ToUniversalTime().ToString("o")' in workflow
    assert "[DateTime]::UtcNow" not in workflow
    assert "Could not write final screening manifest state" in workflow
    assert "if ($ollamaStarted)" in workflow
    assert "$managedRootPrefix = $managedRoot + [IO.Path]::DirectorySeparatorChar" in workflow
    assert "StartsWith($managedRootPrefix,[StringComparison]::OrdinalIgnoreCase)" in workflow
    assert "Stop-Process -Id $ollamaPid -Force -ErrorAction Stop" in workflow
    assert "Could not stop the verified isolated Ollama process" in workflow


def test_medgemma_commit_trigger_markers_are_explicit():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "push:" in workflow
    assert "[model-integrity-screen]" in workflow
    assert "[medgemma]" in workflow
    assert "[hai-def-terms-accepted]" in workflow
    assert "workflow_dispatch" in workflow
    assert "pull_request:" not in workflow


def test_unaccepted_medgemma_push_is_rejected_before_ollama_provisioning():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    terms_start = workflow.index("- name: Reject unaccepted MedGemma terms before provisioning")
    provision_start = workflow.index("- name: Provision isolated Ollama and run sequential model screens")
    terms_step = workflow[terms_start:provision_start]

    assert (
        "if: ${{ (github.event_name == 'workflow_dispatch' && inputs.include_medgemma == true) || "
        "(github.event_name == 'push' && contains(github.event.head_commit.message, '[medgemma]')) }}"
    ) in terms_step
    assert (
        "HAI_DEF_TERMS_ACCEPTED: ${{ (github.event_name == 'workflow_dispatch' && inputs.hai_def_terms_accepted == true) || "
        "(github.event_name == 'push' && contains(github.event.head_commit.message, '[hai-def-terms-accepted]')) }}"
    ) in terms_step
    assert 'if ($env:HAI_DEF_TERMS_ACCEPTED -ne "true")' in terms_step
    assert "No model was provisioned." in terms_step


def test_combined_manifest_derives_and_cross_checks_versions_from_raw_model_manifests():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'prompt_version = "PENDING_FROM_MODEL_OUTPUT"' in workflow
    assert 'audit_version = "radonc-mdt-integrity-audit-v3"' in workflow
    assert 'script_sha256 = (Get-FileHash -LiteralPath "backend/scripts/run_medgemma_screening.py" -Algorithm SHA256).Hash.ToLowerInvariant()' in workflow
    assert "function Get-ModelScreenOutputManifest" in workflow
    assert '$qwenRunManifest = Get-ModelScreenOutputManifest -Path $qwenOutput' in workflow
    assert '$manifest.screening.prompt_version = [string]$qwenRunManifest.prompt_version' in workflow
    assert '$manifest.screening.audit_version = [string]$qwenRunManifest.audit_version' in workflow
    assert '$medgemmaRunManifest = Get-ModelScreenOutputManifest -Path $medOutput' in workflow
    assert 'foreach ($field in @("prompt_version", "audit_version", "screening_script_sha256"))' in workflow
    assert "Qwen and MedGemma JSONL manifest mismatch" in workflow
    assert 'prompt_version = "radonc-mdt-integrity-screen-v4"' not in workflow
