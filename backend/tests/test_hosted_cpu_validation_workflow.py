"""Regression checks for the hosted full-run validation workflow contract."""

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPOSITORY_ROOT
    / ".github"
    / "workflows"
    / "hosted-cpu-four-round-validation.yml"
)


def test_model_manifest_is_not_nested_under_model_missing_condition():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    start = workflow.index(
        "      - name: Provision isolated portable Ollama and qwen3.5:4b"
    )
    end = workflow.index(
        "      - name: Upload full four-round audit and isolated database",
        start,
    )
    provision_step = workflow[start:end]

    # The model-presence branch must close before digest/manifest generation.
    assert re.search(
        r'if \(-not \(Test-RadOncModelInstalled -Tags \$tags -ModelName "qwen3\.5:4b"\)\) \{'
        r'\s*throw "qwen3\.5:4b is not present after model pull\."'
        r'\s*\}\s*\$modelRecord =',
        provision_step,
    )

    presence_check = provision_step.index(
        'if (-not (Test-RadOncModelInstalled -Tags $tags -ModelName "qwen3.5:4b"))'
    )
    manifest_write = provision_step.index(
        "$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath"
    )
    app_setup = provision_step.index("$env:OLLAMA_BASE_URL = $ollamaUrl")
    assert presence_check < manifest_write < app_setup
    assert "if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf))" in provision_step
    assert "$verifiedManifest.source.commit_sha -ne $env:GITHUB_SHA" in provision_step
    assert "$verifiedManifest.model.digest -ne $modelDigest" in provision_step
    assert "[long]$verifiedManifest.model.size_bytes -ne $modelSizeBytes" in provision_step


def test_full_run_artifact_requires_json_sqlite_and_execution_manifest():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    start = workflow.index(
        "      - name: Upload full four-round audit and isolated database"
    )
    end = workflow.index(
        "      - name: Stop only the isolated Ollama process started by this job",
        start,
    )
    upload_step = workflow[start:end]

    required_files = (
        "backend/validation_artifacts/live_four_round_hosted_cpu_validation.json",
        "backend/validation_artifacts/live_four_round_hosted_cpu_validation.sqlite3",
        "backend/validation_artifacts/live_four_round_hosted_cpu_manifest.json",
    )
    for path in required_files:
        assert path in upload_step
    assert "if-no-files-found: error" in upload_step
