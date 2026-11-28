"""Automated verification of standalone Windows packaging integrity and safety contracts.

Validates that:
1. `packaging/windows/radonc_mdt.spec` syntax and AST parse cleanly.
2. All dynamic backend services, schemas, and agent catalogue modules are accounted
   for in `hiddenimports` to eliminate PyInstaller runtime ModuleNotFoundError.
3. Required runtime assets (frontend bundle, reference catalogue, stress cases) are in `datas`.
4. Packaging launcher and verification scripts enforce the correct port configurations (8765/8000).
5. Educational simulation boundaries and `not_a_treatment_instruction: true` disclaimers
   are strictly enforced in schemas and endpoint definitions.
"""
from __future__ import annotations

import ast
import pathlib
import pytest
from pydantic import ValidationError

from app.agent_schemas import AgentAssessment
from app.round_schemas import FinalMDTReport, RoundContribution
from app.main import app


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "packaging" / "windows" / "radonc_mdt.spec"
START_SCRIPT_PATH = REPO_ROOT / "packaging" / "windows" / "Start-RadOnc-MDT.ps1"
VERIFY_SCRIPT_PATH = REPO_ROOT / "packaging" / "windows" / "Verify-Installed-Startup.ps1"
LAUNCH_INSTALLED_PATH = REPO_ROOT / "backend" / "launch_installed.py"
START_ALL_PATH = REPO_ROOT / "scripts" / "start-all.ps1"


def _extract_spec_ast() -> ast.AST:
    assert SPEC_PATH.is_file(), f"Spec file missing at {SPEC_PATH}"
    content = SPEC_PATH.read_text(encoding="utf-8")
    return ast.parse(content, filename=str(SPEC_PATH))


def _extract_spec_hiddenimports() -> list[str]:
    tree = _extract_spec_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Locate Analysis(...) call
            func_name = getattr(node.func, "id", None)
            if func_name == "Analysis":
                for kw in node.keywords:
                    if kw.arg == "hiddenimports" and isinstance(kw.value, ast.List):
                        imports: list[str] = []
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                imports.append(elt.value)
                        return imports
    raise ValueError("Could not find hiddenimports list in Analysis call in radonc_mdt.spec")


def _extract_spec_datas_targets() -> list[str]:
    tree = _extract_spec_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = getattr(node.func, "id", None)
            if func_name == "Analysis":
                for kw in node.keywords:
                    if kw.arg == "datas" and isinstance(kw.value, ast.List):
                        targets: list[str] = []
                        for elt in kw.value.elts:
                            # Each element is expected to be a tuple (source, dest)
                            if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2:
                                dest_node = elt.elts[1]
                                if isinstance(dest_node, ast.Constant) and isinstance(dest_node.value, str):
                                    targets.append(dest_node.value)
                        return targets
    raise ValueError("Could not find datas list in Analysis call in radonc_mdt.spec")


def test_spec_file_syntax_and_ast_parses_cleanly() -> None:
    """Verify that packaging/windows/radonc_mdt.spec parses cleanly without syntax errors."""
    tree = _extract_spec_ast()
    assert isinstance(tree, ast.Module)
    assert len(tree.body) > 0


def test_spec_hiddenimports_covers_all_backend_services() -> None:
    """Ensure all backend/app/services/*.py modules are in hiddenimports."""
    hiddenimports = set(_extract_spec_hiddenimports())
    services_dir = REPO_ROOT / "backend" / "app" / "services"
    assert services_dir.is_dir()

    expected_services: list[str] = []
    for file in services_dir.glob("*.py"):
        if file.stem == "__init__":
            expected_services.append("app.services")
        else:
            expected_services.append(f"app.services.{file.stem}")

    assert expected_services, "No services found in backend/app/services"
    for service_module in expected_services:
        assert service_module in hiddenimports, (
            f"Service module '{service_module}' is missing from radonc_mdt.spec hiddenimports!"
        )


def test_spec_hiddenimports_covers_all_schemas_and_agents() -> None:
    """Ensure all schemas, clinical_fields, and agent catalog modules are in hiddenimports."""
    hiddenimports = set(_extract_spec_hiddenimports())

    core_modules = [
        "app.main",
        "app.config",
        "app.schemas",
        "app.agent_schemas",
        "app.clinical_fields",
        "app.round_schemas",
        "app.agents.catalog",
    ]
    for mod in core_modules:
        assert mod in hiddenimports, f"Core module '{mod}' is missing from radonc_mdt.spec hiddenimports!"


def test_spec_hiddenimports_contains_v2_dynamic_service_dependencies() -> None:
    """Explicitly verify v2 runtime services to prevent runtime ModuleNotFoundError in PyInstaller."""
    hiddenimports = set(_extract_spec_hiddenimports())

    v2_dependencies = [
        "app.services.gpu_telemetry",
        "app.services.reference_catalogue",
        "app.services.chair_report_quality",
        "app.services.intake_screening",
        "app.services.intake_store",
        "app.services.execution_lock",
        "app.services.batch_runner",
        "app.services.case_integrity",
        "app.services.mdt_rounds",
        "app.services.mdt_generation",
        "app.services.ollama",
        "app.services.run_store",
        "app.services.stress_testing",
    ]
    for dep in v2_dependencies:
        assert dep in hiddenimports, f"Required v2 service '{dep}' is missing from hiddenimports!"


def test_spec_datas_includes_required_runtime_assets() -> None:
    """Verify that frontend dist and docs data files are included in datas."""
    datas_targets = set(_extract_spec_datas_targets())
    assert "frontend/dist" in datas_targets, "frontend/dist missing from spec datas"
    assert "docs" in datas_targets, "docs directory target missing from spec datas"


def test_packaging_launcher_port_configuration() -> None:
    """Verify launcher and packaging scripts configure ports correctly (8765 installed, 8000 dev)."""
    assert LAUNCH_INSTALLED_PATH.is_file()
    launch_installed_text = LAUNCH_INSTALLED_PATH.read_text(encoding="utf-8")
    assert 'os.environ.get("RADONC_PORT", "8765")' in launch_installed_text

    assert START_SCRIPT_PATH.is_file()
    start_script_text = START_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "$Port = 8765" in start_script_text
    assert "http://127.0.0.1:$Port/health" in start_script_text

    assert VERIFY_SCRIPT_PATH.is_file()
    verify_script_text = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "http://127.0.0.1:8765/health" in verify_script_text
    assert "http://127.0.0.1:8765/api/agents" in verify_script_text
    assert "http://127.0.0.1:8765/api/runtime" in verify_script_text

    if START_ALL_PATH.is_file():
        start_all_text = START_ALL_PATH.read_text(encoding="utf-8")
        assert "8000" in start_all_text, "start-all.ps1 should reference port 8000 for backend dev server"
        assert "5173" in start_all_text, "start-all.ps1 should reference port 5173 for frontend dev server"


def test_verify_installed_startup_script_contains_safety_assertions() -> None:
    """Verify Verify-Installed-Startup.ps1 asserts health, 45 roles, and safety disclaimers."""
    assert VERIFY_SCRIPT_PATH.is_file()
    verify_text = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")

    assert '$result.application -eq "RadOnc MDT Simulator"' in verify_text
    assert '$result.mode -eq "education_simulation_only"' in verify_text
    assert "45" in verify_text
    assert "qwen3.5:4b" in verify_text
    assert "SAFETY_BOUNDARY_EDUCATIONAL_SIMULATION_ONLY_OK" in verify_text
    assert "NO_INFERENCE_OR_PATIENT_WRITE_PERFORMED" in verify_text


def test_safety_disclaimers_enforced_across_backend_schemas() -> None:
    """Verify that safety disclaimers are structurally enforced across models and cannot be disabled."""
    # 1. AgentAssessment schema
    assert AgentAssessment.model_fields["not_a_treatment_instruction"].default is True
    assessment = AgentAssessment.model_construct(not_a_treatment_instruction=True)
    assert assessment.not_a_treatment_instruction is True

    with pytest.raises(ValidationError):
        AgentAssessment.model_validate({"not_a_treatment_instruction": False})

    # 2. RoundContribution schema
    assert RoundContribution.model_fields["not_a_treatment_instruction"].default is True
    assert RoundContribution.model_fields["safety_boundary"].default == "educational_simulation_only"
    with pytest.raises(ValidationError):
        RoundContribution.model_validate({"not_a_treatment_instruction": False})

    # 3. FinalMDTReport schema
    assert FinalMDTReport.model_fields["not_a_treatment_instruction"].default is True
    assert FinalMDTReport.model_fields["safety_boundary"].default == "educational_simulation_only"
    with pytest.raises(ValidationError):
        FinalMDTReport.model_validate({"not_a_treatment_instruction": False})

    # 4. FastAPI description
    assert "not clinical decision support" in app.description.lower() or "fictional" in app.description.lower()
