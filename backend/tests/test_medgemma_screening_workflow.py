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
        '$includeMed = ($env:GITHUB_EVENT_NAME -eq "workflow_dispatch"'
    )
    medgemma_pull = workflow.index('MODEL_SCREEN_MEDGEMMA_PULL_STARTED')
    medgemma_call = workflow.index(
        'python backend/scripts/run_medgemma_screening.py --model $medModel'
    )

    assert qwen_call < medgemma_gate < medgemma_pull < medgemma_call
    assert "inputs.include_medgemma == true" in workflow
    assert "inputs.hai_def_terms_accepted" in workflow
    assert "HAI_DEF_TERMS_ACCEPTED: ${{ inputs.hai_def_terms_accepted }}" in workflow
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
