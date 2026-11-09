from fastapi.testclient import TestClient

import pytest

from app.agent_schemas import AgentAssessment
from app.main import app
from app.schemas import SyntheticCase
from app.services import run_store

client = TestClient(app)


def _case(title="Training patient case", summary="Fictional case used only for patient persistence tests."):
    return {"scenario_title": title, "case_summary": summary, "primary_site": "Test site"}


def _registration(case=None, name="Training Example"):
    return {"patient_name": name, "case": case or _case()}


def test_patient_creation_and_case_version_history_are_immutable(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patients.sqlite3")
    created = client.post("/api/patients", json=_registration())
    assert created.status_code == 200
    patient = created.json()
    patient_id = patient["patient_id"]
    assert patient["patient_identifier"] == "RAD-000001"
    assert len(patient["versions"]) == 1
    first = patient["versions"][0]
    assert first["version_number"] == 1
    assert first["patient_name"] == "Training Example"
    assert first["case"]["scenario_title"] == "Training patient case"
    assert "patient_name" not in first["case"]
    assert patient["patient_name"] == "Training Example"
    assert first["case_snapshot_sha256"]

    changed = _case("Training patient case — updated", "A revised fictional case version for the same training patient.")
    saved = client.post(f"/api/patients/{patient_id}/versions", json=_registration(changed, "Training Example Updated"))
    assert saved.status_code == 200
    detail = saved.json()
    assert len(detail["versions"]) == 2
    assert detail["versions"][0]["version_number"] == 2
    assert detail["versions"][0]["patient_name"] == "Training Example Updated"
    assert detail["versions"][0]["case"]["scenario_title"] == changed["scenario_title"]
    original_after = next(v for v in detail["versions"] if v["case_version_id"] == first["case_version_id"])
    assert original_after["patient_name"] == "Training Example"
    assert original_after["case"] == first["case"]
    assert original_after["case_snapshot_sha256"] == first["case_snapshot_sha256"]

    listed = client.get("/api/patients")
    assert listed.status_code == 200
    assert listed.json()["patients"][0]["patient_id"] == patient_id
    assert listed.json()["patients"][0]["patient_name"] == "Training Example Updated"
    assert listed.json()["patients"][0]["version_count"] == 2


def test_patient_run_uses_saved_version_and_keeps_legacy_runs_unlinked(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_runs.sqlite3")

    async def no_inference(run_id):
        return None

    monkeypatch.setattr("app.main.run_independent_assessments", no_inference)
    patient = client.post("/api/patients", json=_registration()).json()
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
    first = client.post("/api/patients", json=_registration(_case("Training patient one"))).json()
    second = client.post("/api/patients", json=_registration(_case("Training patient two"))).json()
    response = client.post(
        f"/api/patients/{first['patient_id']}/runs",
        json={"case_version_id": second["versions"][0]["case_version_id"]},
    )
    assert response.status_code == 404


def test_saved_ro01_assessment_is_attached_to_exact_patient_case_version(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_assessments.sqlite3")

    async def fake_generate(profile, case, round_number):
        assert profile["agent_id"] == "RO-01"
        assert case.scenario_title == "Training patient case"
        return AgentAssessment(
            agent_id="RO-01", round_number=round_number, position="conditional",
            provisional_conclusion="A conditional educational assessment for a saved training case.",
            preferred_educational_option="No option can be preferred until missing details are clarified.",
            perspective_summary="Mock assessment persisted for a patient case version.", confidence=0.5,
            evidence_gaps=["Evidence retrieval is not connected."],
        )

    monkeypatch.setattr("app.main.generate_agent_assessment", fake_generate)
    patient = client.post("/api/patients", json=_registration()).json()
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


def test_patient_serials_are_sequential_never_reused_and_delete_cascades(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_delete.sqlite3")

    async def no_inference(run_id):
        return None

    monkeypatch.setattr("app.main.run_independent_assessments", no_inference)
    first = client.post("/api/patients", json=_registration(_case("First training case"))).json()
    second = client.post("/api/patients", json=_registration(_case("Second training case"))).json()
    assert first["patient_identifier"] == "RAD-000001"
    assert second["patient_identifier"] == "RAD-000002"

    version = first["versions"][0]
    run_response = client.post(
        f"/api/patients/{first['patient_id']}/runs",
        json={"case_version_id": version["case_version_id"]},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    deleted = client.delete(f"/api/patients/{first['patient_id']}")
    assert deleted.status_code == 200
    assert client.get(f"/api/patients/{first['patient_id']}").status_code == 404
    assert client.get(f"/api/runs/{run_id}").status_code == 404

    third = client.post("/api/patients", json=_registration(_case("Third training case"))).json()
    assert third["patient_identifier"] == "RAD-000003"
    remaining = client.get("/api/patients").json()["patients"]
    assert [item["patient_identifier"] for item in remaining] == ["RAD-000003", "RAD-000002"]



def test_patient_registration_requires_training_name(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "patient_name.sqlite3")
    response = client.post("/api/patients", json={"case": _case()})
    assert response.status_code == 422


def test_legacy_embedded_patient_name_migrates_out_of_case_payload(monkeypatch, tmp_path):
    import hashlib
    import json
    import sqlite3
    import uuid

    db_path = tmp_path / "legacy_patient_name.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_path)
    run_store.initialize_database()

    patient_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    now = "2026-01-01T00:00:00+00:00"
    legacy_case = {**_case(), "patient_name": "Legacy Training Name"}
    case_json = json.dumps(legacy_case, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(case_json.encode("utf-8")).hexdigest()
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO synthetic_patients(patient_id, patient_name, created_at, updated_at) VALUES (?, NULL, ?, ?)",
            (patient_id, now, now),
        )
        db.execute(
            "INSERT INTO patient_registry_numbers(patient_id, created_at) VALUES (?, ?)",
            (patient_id, now),
        )
        db.execute(
            """INSERT INTO patient_case_versions
            (case_version_id, patient_id, version_number, case_json, case_snapshot_sha256, created_at)
            VALUES (?, ?, 1, ?, ?, ?)""",
            (version_id, patient_id, case_json, digest, now),
        )

    restored = run_store.get_patient(patient_id)
    assert restored["patient_name"] == "Legacy Training Name"
    assert restored["versions"][0]["patient_name"] == "Legacy Training Name"
    assert "patient_name" not in restored["versions"][0]["case"]
    assert restored["versions"][0]["case_snapshot_sha256"] == digest


def test_existing_case_versions_migrate_with_their_best_available_registry_names(monkeypatch, tmp_path):
    import hashlib
    import json
    import sqlite3
    import uuid

    db_path = tmp_path / "legacy_version_names.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_path)
    patient_id = str(uuid.uuid4())
    first_version_id = str(uuid.uuid4())
    second_version_id = str(uuid.uuid4())
    now = "2026-01-01T00:00:00+00:00"
    historical_case = {**_case("Historical version"), "patient_name": "Historic Training Name"}
    current_case = _case("Current version")
    first_json = json.dumps(historical_case, separators=(",", ":"), sort_keys=True)
    second_json = json.dumps(current_case, separators=(",", ":"), sort_keys=True)

    with sqlite3.connect(db_path) as db:
        db.execute("""CREATE TABLE synthetic_patients (
            patient_id TEXT PRIMARY KEY, patient_name TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        # Reproduce the old schema, which had no per-version registry name.
        db.execute("""CREATE TABLE patient_case_versions (
            case_version_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL,
            version_number INTEGER NOT NULL CHECK(version_number > 0),
            case_json TEXT NOT NULL, case_snapshot_sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE(patient_id, version_number),
            FOREIGN KEY (patient_id) REFERENCES synthetic_patients(patient_id) ON DELETE CASCADE
        )""")
        db.execute(
            "INSERT INTO synthetic_patients VALUES (?, ?, ?, ?)",
            (patient_id, "Current Registry Name", now, now),
        )
        db.executemany(
            """INSERT INTO patient_case_versions
            (case_version_id, patient_id, version_number, case_json, case_snapshot_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (first_version_id, patient_id, 1, first_json,
                 hashlib.sha256(first_json.encode("utf-8")).hexdigest(), now),
                (second_version_id, patient_id, 2, second_json,
                 hashlib.sha256(second_json.encode("utf-8")).hexdigest(), now),
            ],
        )

    run_store.initialize_database()
    detail = run_store.get_patient(patient_id)
    first = next(v for v in detail["versions"] if v["case_version_id"] == first_version_id)
    second = next(v for v in detail["versions"] if v["case_version_id"] == second_version_id)

    assert detail["patient_name"] == "Current Registry Name"
    assert first["patient_name"] == "Historic Training Name"
    assert second["patient_name"] == "Current Registry Name"
    assert "patient_name" not in first["case"]
    assert first["case_snapshot_sha256"] == hashlib.sha256(first_json.encode("utf-8")).hexdigest()


def test_patient_registry_round_trips_every_case_field_across_versions_and_database_reopen(monkeypatch, tmp_path):
    import hashlib

    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "complete_patient_case.sqlite3")

    original_case = {
        "scenario_title": "TEST_ONLY complete case field roundtrip",
        "case_summary": (
            "Fixture narrative only. Every structured value in this payload is test-only "
            "and does not represent a real clinical finding."
        ),
        "age_years": 63,
        "sex_at_birth": "TEST_ONLY_SEX_AT_BIRTH",
        "primary_site": "TEST_ONLY_PRIMARY_SITE",
        "histology": "TEST_ONLY_HISTOLOGY",
        "clinical_t_stage": "TEST_ONLY_T_STAGE",
        # Deliberately unknown fields must remain absent after schema serialisation.
        "clinical_n_stage": None,
        "clinical_m_stage": None,
        "stage_group": None,
        "performance_status": None,
        "pathology_summary": "TEST_ONLY_PATHOLOGY_SUMMARY",
        "imaging_summary": "TEST_ONLY_IMAGING_SUMMARY",
        "current_medications": ["TEST_ONLY_MEDICATION_A", "TEST_ONLY_MEDICATION_B"],
        "known_allergies": ["TEST_ONLY_ALLERGY_A"],
        "relevant_investigations": ["TEST_ONLY_INVESTIGATION_A", "TEST_ONLY_INVESTIGATION_B"],
        "relevant_comorbidities": ["TEST_ONLY_COMORBIDITY_A"],
        "prior_treatment": ["TEST_ONLY_PRIOR_TREATMENT_A"],
        "patient_goals": ["TEST_ONLY_PATIENT_STATED_GOAL_A"],
        "social_context": ["TEST_ONLY_SOCIAL_CONTEXT_A"],
        "resource_context": ["TEST_ONLY_RESOURCE_CONTEXT_A"],
        "known_unknowns": ["TEST_ONLY_UNKNOWN_A", "TEST_ONLY_UNKNOWN_B"],
    }
    expected_original = SyntheticCase.model_validate(original_case).model_dump(exclude_none=True)
    original_hash = hashlib.sha256(
        SyntheticCase.model_validate(original_case).model_dump_json(exclude_none=True).encode("utf-8")
    ).hexdigest()

    created = client.post(
        "/api/patients",
        json=_registration(original_case, "Complete Field Training Example"),
    )
    assert created.status_code == 200
    patient_id = created.json()["patient_id"]
    first = created.json()["versions"][0]

    assert first["version_number"] == 1
    assert first["case"] == expected_original
    assert first["case_snapshot_sha256"] == original_hash
    assert "patient_name" not in first["case"]
    for unknown_field in ("clinical_n_stage", "clinical_m_stage", "stage_group", "performance_status"):
        assert unknown_field not in first["case"]

    # Change exactly one case property; all other scalar and list properties must survive.
    changed_case = {**original_case, "pathology_summary": "TEST_ONLY_PATHOLOGY_SUMMARY_UPDATED"}
    expected_changed = SyntheticCase.model_validate(changed_case).model_dump(exclude_none=True)
    changed_hash = hashlib.sha256(
        SyntheticCase.model_validate(changed_case).model_dump_json(exclude_none=True).encode("utf-8")
    ).hexdigest()
    saved = client.post(
        f"/api/patients/{patient_id}/versions",
        json=_registration(changed_case, "Complete Field Training Example"),
    )
    assert saved.status_code == 200
    versions = saved.json()["versions"]
    assert [version["version_number"] for version in versions] == [2, 1]
    second, preserved_first = versions

    assert second["case"] == expected_changed
    assert second["case_snapshot_sha256"] == changed_hash
    assert second["case_snapshot_sha256"] != first["case_snapshot_sha256"]
    assert preserved_first["case_version_id"] == first["case_version_id"]
    assert preserved_first["case"] == expected_original
    assert preserved_first["case_snapshot_sha256"] == original_hash

    # Every store operation uses a short-lived SQLite connection. Reinitialise the
    # schema and fetch again to exercise persistence across a fresh DB connection.
    run_store.initialize_database()
    reloaded = client.get(f"/api/patients/{patient_id}")
    assert reloaded.status_code == 200
    reloaded_versions = reloaded.json()["versions"]
    reloaded_second, reloaded_first = reloaded_versions

    assert reloaded_second["case"] == expected_changed
    assert reloaded_second["case_snapshot_sha256"] == changed_hash
    assert reloaded_first["case"] == expected_original
    assert reloaded_first["case_snapshot_sha256"] == original_hash
    assert reloaded_first["case_version_id"] == first["case_version_id"]

    restored_original = run_store.get_patient_case_version(patient_id, first["case_version_id"])
    assert restored_original["case"] == expected_original
    assert restored_original["case_snapshot_sha256"] == original_hash
    assert restored_original["case"] != reloaded_second["case"]


def test_patient_create_and_version_failures_roll_back_partial_registry_writes(monkeypatch, tmp_path):
    import sqlite3

    db_path = tmp_path / "patient_transaction_rollback.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_path)
    run_store.initialize_database()

    # Fail after the patient profile and serial allocation INSERTs have run.
    # The transaction must roll back both earlier writes as well.
    with sqlite3.connect(db_path) as db:
        db.execute(
            """CREATE TRIGGER reject_initial_case_version
            BEFORE INSERT ON patient_case_versions
            BEGIN
                SELECT RAISE(ABORT, 'injected initial-version failure');
            END"""
        )

    with pytest.raises(sqlite3.IntegrityError, match="injected initial-version failure"):
        run_store.create_patient("Rollback Training Example", SyntheticCase.model_validate(_case()))

    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM synthetic_patients").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM patient_registry_numbers").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM patient_case_versions").fetchone()[0] == 0
        db.execute("DROP TRIGGER reject_initial_case_version")

    # A successful registration after the failed transaction must still receive
    # the first serial; a failed operation must not consume a registry identifier.
    patient = run_store.create_patient("Rollback Training Example", SyntheticCase.model_validate(_case()))
    assert patient["patient_identifier"] == "RAD-000001"
    patient_id = patient["patient_id"]

    # Fail after the new immutable version INSERT but before the registry profile
    # name UPDATE. The failed update must not leave an orphaned extra version.
    with sqlite3.connect(db_path) as db:
        db.execute(
            """CREATE TRIGGER reject_registry_profile_update
            BEFORE UPDATE ON synthetic_patients
            BEGIN
                SELECT RAISE(ABORT, 'injected profile-update failure');
            END"""
        )

    with pytest.raises(sqlite3.IntegrityError, match="injected profile-update failure"):
        run_store.create_case_version(
            patient_id,
            "Changed Training Example",
            SyntheticCase.model_validate(
                _case("A second title", "A revised fictional test summary for transaction rollback.")
            ),
        )

    restored = run_store.get_patient(patient_id)
    assert restored["patient_name"] == "Rollback Training Example"
    assert len(restored["versions"]) == 1
    assert restored["versions"][0]["version_number"] == 1
    assert restored["versions"][0]["case"]["scenario_title"] == "Training patient case"
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM patient_case_versions").fetchone()[0] == 1
        db.execute("DROP TRIGGER reject_registry_profile_update")

