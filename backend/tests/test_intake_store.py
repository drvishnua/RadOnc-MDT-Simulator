import sqlite3

import pytest

from app.schemas import SyntheticCase
from app.services import run_store
from app.services import intake_store


@pytest.fixture
def isolated_intake_database(tmp_path, monkeypatch):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "intake-test.sqlite3")


def make_case(**updates):
    data = {
        "scenario_title": "Synthetic intake persistence case",
        "case_summary": "Fictional case used to test append-only intake persistence.",
    }
    data.update(updates)
    return SyntheticCase.model_validate(data)


def test_intake_session_records_answers_and_corrections_as_immutable_events(isolated_intake_database):
    session = intake_store.create_intake_session(make_case())
    session_id = session["session_id"]
    assert session["state"] == "SCREENING"
    assert session["event_count"] == 1

    answered = intake_store.record_intake_event(
        session_id,
        event_type="ANSWER",
        field_id="age_years",
        value=64,
        source_text="Patient reports age 64.",
    )
    assert answered["case"]["age_years"] == 64
    assert answered["event_count"] == 2

    corrected = intake_store.record_intake_event(
        session_id,
        event_type="CORRECTION",
        field_id="age_years",
        value=65,
        source_text="Correction: age is 65 years.",
    )
    assert corrected["case"]["age_years"] == 65
    assert corrected["event_count"] == 3
    assert [event["event_type"] for event in corrected["events"]] == [
        "CASE_CREATED", "ANSWER", "CORRECTION"
    ]
    assert corrected["events"][1]["case_snapshot_sha256"] != corrected["events"][2]["case_snapshot_sha256"]
    assert corrected["events"][2]["previous_event_sha256"] == corrected["events"][1]["event_sha256"]


def test_decline_is_a_saved_event_and_does_not_mean_negative(isolated_intake_database):
    session = intake_store.create_intake_session(make_case())
    updated = intake_store.record_intake_event(
        session["session_id"],
        event_type="DECLINE_DOMAIN",
        domain="patient_preferences",
        source_text="User declined to provide preferences.",
    )
    domain = next(item for item in updated["screening"]["domains"] if item["domain"] == "patient_preferences")
    assert domain["status"] == "DECLINED"
    assert domain["missing_fields"] == ["patient_goals"]
    assert "patient_preferences" not in {item["domain"] for item in updated["screening"]["questions"]}
    assert updated["events"][-1]["payload"]["source_text"] == "User declined to provide preferences."


def test_accept_with_gaps_requires_confirmation_and_freezes_session(isolated_intake_database):
    session = intake_store.create_intake_session(make_case())
    with pytest.raises(ValueError, match="Explicit confirmation"):
        intake_store.accept_intake_with_gaps(session["session_id"], confirmed=False)

    accepted = intake_store.accept_intake_with_gaps(session["session_id"], confirmed=True)
    assert accepted["state"] == "ACCEPTED_WITH_GAPS"
    assert accepted["screening"]["gaps"]
    assert accepted["events"][-1]["event_type"] == "ACCEPTED_WITH_GAPS"
    with pytest.raises(ValueError, match="immutable"):
        intake_store.record_intake_event(
            session["session_id"], event_type="ANSWER",
            field_id="age_years", value=65,
        )


def test_intake_event_hash_chain_detects_tampering(isolated_intake_database):
    session = intake_store.create_intake_session(make_case())
    with sqlite3.connect(run_store.DB_PATH) as db:
        db.execute(
            "UPDATE intake_events SET payload_json = ? WHERE session_id = ? AND sequence_number = 1",
            ('{"tampered":true}', session["session_id"]),
        )
    with pytest.raises(ValueError, match="integrity verification"):
        intake_store.get_intake_session(session["session_id"])


def test_question_asked_is_saved_once_and_declined_domain_cannot_be_asked(isolated_intake_database):
    session = intake_store.create_intake_session(make_case())
    session_id = session["session_id"]
    asked = intake_store.record_intake_event(
        session_id,
        event_type="QUESTION_ASKED",
        domain="patient_preferences",
    )
    event = asked["events"][-1]
    assert event["event_type"] == "QUESTION_ASKED"
    assert event["payload"]["domain"] == "patient_preferences"
    assert "patient's stated goals" in event["payload"]["question"]

    with pytest.raises(ValueError, match="already been recorded"):
        intake_store.record_intake_event(
            session_id, event_type="QUESTION_ASKED", domain="patient_preferences"
        )

    intake_store.record_intake_event(
        session_id, event_type="DECLINE_DOMAIN", domain="staging_and_investigations"
    )
    with pytest.raises(ValueError, match="declined"):
        intake_store.record_intake_event(
            session_id, event_type="QUESTION_ASKED", domain="staging_and_investigations"
        )
