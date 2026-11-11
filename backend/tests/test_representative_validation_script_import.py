"""Import-path regression coverage for the hosted representative validation launcher."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_representative_validation_script_imports_from_repository_root_without_inference():
    backend_dir = Path(__file__).resolve().parents[1]
    repository_root = backend_dir.parent
    script_path = (
        backend_dir
        / "scripts"
        / "representative_model_provenance_validation.py"
    )
    probe = (
        "import runpy, sys\n"
        "runpy.run_path(sys.argv[1], run_name='representative_validation_import_probe')\n"
        "assert 'app.agents.catalog' in sys.modules\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", probe, str(script_path)],
        cwd=repository_root,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, (
        "The validation script must import the backend package when launched "
        "from the repository root, without starting Ollama inference.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
