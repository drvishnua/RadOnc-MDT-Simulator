"""No-inference regression tests for hosted checkpoint continuation."""

from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _namespace():
    script = ROOT / "backend" / "scripts" / "resume_hosted_four_round_validation.py"
    return runpy.run_path(str(script), run_name="resume_hosted_validation_test")


def test_resume_script_imports_without_starting_inference():
    namespace = _namespace()
    assert callable(namespace["main"])
    assert namespace["EXPECTED_SOURCE_RUN"] == "43714529807"

def test_audit_only_round_gate_never_generates_missing_or_incomplete_rounds():
    namespace = _namespace()
    requires = namespace["_round_generation_required"]

    assert requires({"status": "completed"}, "R3", audit_only=True) is False
    assert requires({"status": "completed"}, "Chair R4", audit_only=True) is False
    assert requires({"status": "running"}, "R3", audit_only=False) is True

    for summary, label in (
        ({"status": "running"}, "R3"),
        ({"status": "queued"}, "Chair R4"),
        (None, "Chair R4"),
    ):
        try:
            requires(summary, label, audit_only=True)
        except RuntimeError as exc:
            assert "Inference is prohibited in audit-only mode" in str(exc)
        else:
            raise AssertionError("Audit-only mode accepted an incomplete round and could infer.")


def test_checkpoint_manifest_requires_original_lineage_and_exact_model_digest():
    validate = _namespace()["_validate_checkpoint"]
    manifest = {
        "source": {
            "workflow_run_id": "43714529807",
            "commit_sha": "4683b0767bf5cade408e85ec31ef248b34e5321e",
        },
        "execution": {
            "mode": "github_hosted_cpu_only",
            "gpu_measured": False,
            "agent_concurrency": 1,
            "expected_role_count": 45,
        },
        "model": {"digest": "sha256:abc"},
    }
    validate(manifest, "43714529807", "sha256:abc")

    invalid_cases = (
        (manifest, "999", "sha256:abc"),
        (manifest, "43714529807", "sha256:different"),
        (
            {
                **manifest,
                "source": {
                    **manifest["source"],
                    "commit_sha": "0" * 40,
                },
            },
            "43714529807",
            "sha256:abc",
        ),
        (
            {
                **manifest,
                "execution": {**manifest["execution"], "agent_concurrency": 2},
            },
            "43714529807",
            "sha256:abc",
        ),
        (
            {
                **manifest,
                "execution": {**manifest["execution"], "gpu_measured": True},
            },
            "43714529807",
            "sha256:abc",
        ),
    )
    for bad_manifest, run_id, digest in invalid_cases:
        try:
            validate(bad_manifest, run_id, digest)
        except RuntimeError:
            continue
        raise AssertionError("Invalid checkpoint identity or execution settings were accepted.")


def test_round_role_coverage_rejects_missing_duplicate_failed_and_extra_roles():
    namespace = _namespace()
    required_ids = namespace["ROLE_IDS"]
    validate = namespace["_require_roles"]
    first_two = sorted(required_ids)[:2]
    rows = [
        {"agent_id": first_two[0], "status": "completed", "result": {"position": "supports"}},
        {"agent_id": first_two[1], "status": "completed", "result": {"position": "conditional"}},
    ]

    try:
        validate(rows, "result", "R3")
    except RuntimeError as exc:
        assert "missing=" in str(exc)
    else:
        raise AssertionError("Incomplete 45-role coverage was accepted.")

    duplicated = rows + [rows[0]]
    try:
        validate(duplicated, "result", "R3")
    except RuntimeError as exc:
        assert "duplicates=" in str(exc)
    else:
        raise AssertionError("Duplicate role rows were accepted.")

    incomplete = [
        {"agent_id": role_id, "status": "completed", "result": {"position": "supports"}}
        for role_id in required_ids
    ]
    incomplete[0] = {"agent_id": incomplete[0]["agent_id"], "status": "running", "result": None}
    try:
        validate(incomplete, "result", "R3")
    except RuntimeError as exc:
        assert "incomplete=" in str(exc)
    else:
        raise AssertionError("An interrupted role row was accepted as complete.")

    extra = incomplete[1:] + [
        {"agent_id": "UNCONFIGURED", "status": "completed", "result": {"position": "supports"}}
    ]
    try:
        validate(extra, "result", "R3")
    except RuntimeError as exc:
        assert "extra=" in str(exc)
    else:
        raise AssertionError("An unconfigured role was accepted.")


def test_integrity_flags_remain_quality_gate_failures():
    collect = _namespace()["_collect_integrity_quality_gate_failures"]
    failures = collect([
        ("R1", [{
            "agent_id": "RO-01",
            "assessment": {
                "case_data_integrity_flags": ["Unsupported T1 label."],
                "source_reference_integrity_flags": [],
            },
        }], "assessment"),
        ("R2", [{
            "agent_id": "RO-02",
            "result": {
                "case_data_integrity_flags": [],
                "source_reference_integrity_flags": ["Invalid R1 role range."],
            },
        }], "result"),
        ("R3", [{
            "agent_id": "RO-03",
            "result": {
                "case_data_integrity_flags": [],
                "source_reference_integrity_flags": [],
            },
        }], "result"),
    ])
    assert len(failures) == 2
    assert {item["round"] for item in failures} == {"R1", "R2"}


def test_resume_workflow_downloads_prior_run_and_reuploads_database_checkpoint():
    workflow_path = (
        ROOT
        / ".github"
        / "workflows"
        / "resume-hosted-cpu-four-round-validation.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    assert "actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3" in workflow
    assert "run-id: ${{ env.RADONC_CHECKPOINT_RUN_ID }}" in workflow
    assert "actions: read" in workflow
    assert "RADONC_AGENT_CONCURRENCY: \"1\"" in workflow
    assert "RADONC_VALIDATION_CPU_ONLY: \"1\"" in workflow
    assert "if: always()" in workflow
    assert "live_four_round_hosted_cpu_validation.sqlite3" in workflow
    assert "live_four_round_hosted_cpu_resume_manifest.json" in workflow

def test_saved_checkpoint_audit_workflow_is_bound_to_run9_and_forbids_inference():
    workflow_path = (
        ROOT
        / ".github"
        / "workflows"
        / "audit-saved-hosted-cpu-four-round-checkpoint.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")

    assert 'default: "43753957255"' in workflow
    assert 'RADONC_AUDIT_ONLY: "1"' in workflow
    assert "run-id: ${{ env.RADONC_CHECKPOINT_RUN_ID }}" in workflow
    assert "actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3" in workflow
    assert "if: always()" in workflow
    assert "Ensure-RadOnc-AIEngine" not in workflow
    assert "OLLAMA_BASE_URL" not in workflow
    assert "python backend/scripts/resume_hosted_four_round_validation.py" in workflow
    assert "GITHUB_ENV" in workflow
    assert "RADONC_CHECKPOINT_MANIFEST=" in workflow
    assert "RADONC_MODEL_DIGEST=" in workflow

def test_resume_workflow_is_bound_to_run_16_checkpoint_lineage():
    workflow_path = (
        ROOT
        / ".github"
        / "workflows"
        / "resume-hosted-cpu-four-round-validation.yml"
    )
    script_path = ROOT / "backend" / "scripts" / "resume_hosted_four_round_validation.py"
    workflow = workflow_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")
    expected_run = "43714529807"
    expected_sha = "4683b0767bf5cade408e85ec31ef248b34e5321e"

    assert "EXPECTED_SOURCE_RUN" in script and expected_run in script
    assert "EXPECTED_SOURCE_SHA" in script and expected_sha in script
    assert "default: \"43714529807\"" in workflow
    assert "|| '43714529807'" in workflow
    assert expected_sha in workflow
    assert "[resume-hosted-cpu-r3]" in workflow
    assert "backend/tests/test_resume_hosted_four_round_validation.py" in workflow

def test_resume_workflow_normalizes_ollama_digest_before_exact_checkpoint_match():
    workflow_path = (
        ROOT
        / ".github"
        / "workflows"
        / "resume-hosted-cpu-four-round-validation.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    assert '$hexDigest = $reportedDigest' in workflow
    assert '$hexDigest.StartsWith("sha256:"' in workflow
    assert '$hexDigest.Substring(7)' in workflow
    assert 'if ($hexDigest.Length -ne 64)' in workflow
    assert '[Uri]::IsHexDigit($hexChar)' in workflow
    assert '$modelDigest = "sha256:" + $hexDigest.ToLowerInvariant()' in workflow
    assert 'if ($modelDigest -ne [string]$manifest.model.digest)' in workflow



def test_chair_position_count_validator_accepts_human_readable_round_labels_and_exact_counts():
    namespace = _namespace()
    validate = namespace["_validate_chair_position_counts"]
    total = len(namespace["ROLE_IDS"])
    counts = {
        "R1": {"insufficient_information": total - 1, "conditional": 1},
        "R2": {"insufficient_information": total - 2, "supports": 2},
        "R3": {"insufficient_information": total - 3, "opposes": 3},
    }
    synthesis = (
        "Recorded position distribution — "
        f"Round 1: {total - 1}/{total} insufficient-information, 1/{total} conditional; "
        f"Round 2: {total - 2}/{total} insufficient-information, 2/{total} supports; "
        f"Round 3: {total - 3}/{total} insufficient-information, 3/{total} opposes. "
        "These are role-level labels, not votes."
    )
    validate(synthesis, counts)


def test_chair_position_count_validator_accepts_short_labels_but_rejects_misplaced_counts():
    namespace = _namespace()
    validate = namespace["_validate_chair_position_counts"]
    total = len(namespace["ROLE_IDS"])
    counts = {
        "R1": {"insufficient_information": total},
        "R2": {"supports": total},
        "R3": {"conditional": total},
    }
    valid = (
        "Recorded position distribution — "
        f"R1: {total}/{total} insufficient-information; "
        f"R2: {total}/{total} supports; "
        f"R3: {total}/{total} conditional."
    )
    validate(valid, counts)

    invalid = (
        "Recorded position distribution — "
        f"R1: {total}/{total} insufficient-information; "
        f"R2: {total}/{total} conditional; "
        f"R3: {total}/{total} supports."
    )
    try:
        validate(invalid, counts)
    except RuntimeError as exc:
        assert "R2 count" in str(exc)
    else:
        raise AssertionError("A position count placed under the wrong round was accepted.")


def test_chair_position_count_validator_rejects_missing_round_and_incomplete_distribution():
    namespace = _namespace()
    validate = namespace["_validate_chair_position_counts"]
    total = len(namespace["ROLE_IDS"])
    counts = {
        "R1": {"insufficient_information": total},
        "R2": {"insufficient_information": total},
        "R3": {"insufficient_information": total},
    }
    missing_round = (
        "Recorded position distribution — "
        f"Round 1: {total}/{total} insufficient-information; "
        f"Round 3: {total}/{total} insufficient-information."
    )
    for synthesis in (
        missing_round,
        "The report describes all positions but omits the deterministic distribution.",
        (
            "Recorded position distribution — "
            f"Round 1: {total - 1}/{total} insufficient-information; "
            f"Round 2: {total}/{total} insufficient-information; "
            f"Round 3: {total}/{total} insufficient-information."
        ),
    ):
        try:
            validate(synthesis, counts)
        except RuntimeError:
            continue
        raise AssertionError("An incomplete Chair position distribution was accepted.")
