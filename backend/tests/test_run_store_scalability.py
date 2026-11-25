"""Regression tests for SQLite WAL mode and N+1 elimination in run_store."""

from app.schemas import SyntheticCase
from app.services import intake_store, run_store


def _make_case(title: str, age: int = 58) -> SyntheticCase:
    return SyntheticCase(
        scenario_title=title,
        case_summary="Fictional radiation oncology training case.",
        age_years=age,
        primary_site="Oropharynx",
        stage_group="Stage III",
        known_unknowns=["p16 status not reported"],
    )


def test_list_patients_avoids_n_plus_one_and_preserves_counts(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "scale.sqlite3")
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()

    p1 = run_store.create_patient("Case Alpha", _make_case("Alpha V1", age=55))
    p1_id = p1["patient_id"]
    run_store.create_case_version(p1_id, "Case Alpha", _make_case("Alpha V2", age=56))

    p2 = run_store.create_patient("Case Beta", _make_case("Beta V1", age=64))
    p2_id = p2["patient_id"]

    # Attach one simulation run to p1 without going through intake provenance helper
    p1_detail = run_store.get_patient(p1_id)
    latest_v_id = p1_detail["versions"][0]["case_version_id"]
    with run_store._connect() as db:
        db.execute(
            """
            INSERT INTO simulation_runs
            (run_id, case_json, status, total_agents, patient_id, case_version_id, case_version_number, created_at, updated_at, clinical_field_registry_version)
            VALUES (?, ?, 'completed', 45, ?, ?, 2, ?, ?, ?)
            """,
            (
                "run-alpha-1",
                _make_case("Alpha V2", age=56).model_dump_json(),
                p1_id,
                latest_v_id,
                run_store._now(),
                run_store._now(),
                "1.0.0",
            ),
        )

    # Assert list_patients never calls get_patient or get_run in an N+1 loop
    def _forbid(*args, **kwargs):
        raise AssertionError("N+1 query helper should not be called by list_patients")

    monkeypatch.setattr(run_store, "get_patient", _forbid)
    monkeypatch.setattr(run_store, "get_run", _forbid)

    rows = run_store.list_patients()
    assert len(rows) == 2

    by_id = {row["patient_id"]: row for row in rows}
    assert by_id[p1_id]["version_count"] == 2
    assert by_id[p1_id]["simulation_count"] == 1
    assert by_id[p1_id]["latest_version_number"] == 2
    assert by_id[p1_id]["scenario_title"] == "Alpha V2"
    assert by_id[p1_id]["age_years"] == 56
    assert by_id[p1_id]["stage_group"] == "Stage III"
    assert by_id[p1_id]["patient_identifier"].startswith("RAD-")

    assert by_id[p2_id]["version_count"] == 1
    assert by_id[p2_id]["simulation_count"] == 0
    assert by_id[p2_id]["scenario_title"] == "Beta V1"


def test_delete_patient_and_wal_mode(monkeypatch, tmp_path):
    db_path = tmp_path / "wal_check.sqlite3"
    monkeypatch.setattr(run_store, "DB_PATH", db_path)
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()

    with run_store._connect() as db:
        mode = db.execute("PRAGMA journal_mode").fetchone()[0]
    assert str(mode).lower() == "wal"

    with intake_store._connect() as db:
        intake_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
    assert str(intake_mode).lower() == "wal"

    p = run_store.create_patient("Delete Me", _make_case("To Delete"))
    pid = p["patient_id"]
    run_store.delete_patient(pid)
    assert run_store.list_patients() == []
