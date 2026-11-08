from fastapi.testclient import TestClient

from app.agent_schemas import AgentAssessment
from app.main import app
from app.schemas import SyntheticCase
from app.services import run_store

client = TestClient(app)


def _case(title="Synthetic patient case", summary="Fictional case used only for patient persistence tests."):
    return {"scenario_title": title, "case_summary": summary, "primary_site": "Test site"}


def test_patient_creation_and_case_version_history_are_immutable(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patients.sqlite3")
    created = client.post("/api/patients", json=_case())
    assert created.status_code == 200
    patient = created.json()
    patient_id = patient["patient_id"]
    assert patient_id.startswith("SYN-")
    assert len(patient["versions"]) == 1
    first = patient["versions"][0]
    assert first["version_number"] == 1
    assert first["case"]["scenario_title"] == "Synthetic patient case"
    assert first["case_snapshot_sha256"]

    changed = _case("Synthetic patient case — updated", "A revised fictional case version for the same synthetic patient.")
    saved = client.post(f"/api/patients/{patient_id}/versions", json=changed)
    assert saved.status_code == 200
    detail = saved.json()
    assert len(detail["versions"]) == 2
    assert detail["versions"][0]["version_number"] == 2
    assert detail["versions"][0]["case"]["scenario_title"] == changed["scenario_title"]
    original_after = next(v for v in detail["versions"] if v["case_version_id"] == first["case_version_id"])
    assert original_after["case"] == first["case"]
    assert original_after["case_snapshot_sha256"] == first["case_snapshot_sha256"]

    listed = client.get("/api/patients")
    assert listed.status_code == 200
    assert listed.json()["patients"][0]["patient_id"] == patient_id
    assert listed.json()["patients"][0]["version_count"] == 2


def test_patient_run_uses_saved_version_and_keeps_legacy_runs_unlinked(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_runs.sqlite3")

    async def no_inference(run_id):
        return None

    monkeypatch.setattr("app.main.run_independent_assessments", no_inference)
    patient = client.post("/api/patients", json=_case()).json()
    version = patient["versions"][0]
    response = client.post(
        f"/api/patients/{patient['patient_id']}/runs",
        json={"case_version_id": version["case_version_id"]},
    )
    assert response.status_code == 200
    run = response.json()
    assert run["patient_id"] == patient["patient_id"]
    assert run["case_version_id"] == version["case_version_id"]
    assert run["case_version_number"] == 1
    restored = client.get(f"/api/runs/{run['run_id']}/case").json()
    assert restored["case_snapshot_sha256"] == version["case_snapshot_sha256"]
    assert restored["case"] == version["case"]

    legacy = run_store.create_run(SyntheticCase.model_validate(_case("Legacy unlinked run")))
    legacy_again = run_store.get_run(legacy["run_id"])
    assert legacy_again["patient_id"] is None
    assert legacy_again["case_version_id"] is None


def test_patient_run_rejects_a_version_owned_by_another_patient(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_scope.sqlite3")
    first = client.post("/api/patients", json=_case("Synthetic patient one")).json()
    second = client.post("/api/patients", json=_case("Synthetic patient two")).json()
    response = client.post(
        f"/api/patients/{first['patient_id']}/runs",
        json={"case_version_id": second["versions"][0]["case_version_id"]},
    )
    assert response.status_code == 404


def test_saved_ro01_assessment_is_attached_to_exact_patient_case_version(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_assessments.sqlite3")

    async def fake_generate(profile, case, round_number):
        assert profile["agent_id"] == "RO-01"
        assert case.scenario_title == "Synthetic patient case"
        return AgentAssessment(
            agent_id="RO-01", round_number=round_number, position="conditional",
            provisional_conclusion="A conditional educational assessment for a saved synthetic case.",
            preferred_educational_option="No option can be preferred until missing details are clarified.",
            perspective_summary="Mock assessment persisted for a patient case version.", confidence=0.5,
            evidence_gaps=["Evidence retrieval is not connected."],
        )

    monkeypatch.setattr("app.main.generate_agent_assessment", fake_generate)
    patient = client.post("/api/patients", json=_case()).json()
    version = patient["versions"][0]
    result = client.post(
        f"/api/patients/{patient['patient_id']}/versions/{version['case_version_id']}/assess/RO-01"
    )
    assert result.status_code == 200
    assert result.json()["patient_id"] == patient["patient_id"]
    assert result.json()["case_version_id"] == version["case_version_id"]
    assert result.json()["assessment"]["agent_id"] == "RO-01"
    history = client.get(
        f"/api/patients/{patient['patient_id']}/versions/{version['case_version_id']}/assessments"
    )
    assert history.status_code == 200
    assert len(history.json()["assessments"]) == 1


def test_old_database_gets_additive_patient_columns_without_losing_runs(monkeypatch, tmp_path):
    import sqlite3

    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute("""CREATE TABLE simulation_runs (
            run_id TEXT PRIMARY KEY, case_json TEXT NOT NULL, status TEXT NOT NULL,
            total_agents INTEGER NOT NULL, current_agent_id TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE agent_run_results (
            run_id TEXT NOT NULL, agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
            category_label TEXT NOT NULL, status TEXT NOT NULL, assessment_json TEXT,
            error_message TEXT, started_at TEXT, completed_at TEXT, duration_seconds REAL,
            PRIMARY KEY(run_id, agent_id)
        )""")
        db.execute(
            "INSERT INTO simulation_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("legacy-run", SyntheticCase.model_validate(_case()).model_dump_json(exclude_none=True),
             "completed", 0, None, "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
    monkeypatch.setattr(run_store, "DB_PATH", db_path)
    run_store.initialize_database()
    restored = run_store.get_run("legacy-run")
    assert restored["run_id"] == "legacy-run"
    assert restored["patient_id"] is None
    assert restored["case_version_id"] is None
