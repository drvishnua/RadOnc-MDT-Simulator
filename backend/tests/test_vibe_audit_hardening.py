"""Phase 4 smoke tests for config/CORS, payload caps, fault tolerance, circuit breaker, and 4-round completion."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES
from app.config import AppSettings
from app.main import app
from app.services.ollama import OllamaUnavailable, ensure_ollama_service_and_model
import asyncio
from app.round_schemas import FinalMDTReport, RoundContribution
from app.services import batch_runner, mdt_rounds, ollama as ollama_service, run_store

client = TestClient(app)


def _valid_case_payload() -> dict[str, object]:
    return {
        "scenario_title": "Synthetic MDT Hardening Case",
        "case_summary": "A fictional oncology vignette used only for hardening smoke tests.",
        "age_years": 62,
        "primary_site": "Oropharynx",
        "histology": "Squamous cell carcinoma",
        "known_unknowns": ["p16 status not reported"],
    }


def _create_accepted_run_dependencies(monkeypatch, tmp_path) -> tuple[str, str]:
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "hardening.sqlite3")
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()

    intake = client.post("/api/intakes", json={"case": _valid_case_payload()})
    assert intake.status_code == 200
    session_id = intake.json()["session_id"]

    accept = client.post(f"/api/intakes/{session_id}/accept", json={"confirmed": True})
    assert accept.status_code == 200

    promote = client.post(
        f"/api/intakes/{session_id}/promote",
        json={"patient_name": "Hardening Smoke Patient"},
    )
    assert promote.status_code == 200
    patient = promote.json()
    return patient["patient_id"], patient["versions"][0]["case_version_id"]


def test_app_settings_validation_and_cors_rejection():
    valid = AppSettings(
        ollama_base_url="http://127.0.0.1:11434/",
        cors_origins=["http://127.0.0.1:5173", "https://mdt.local/"],
    )
    assert valid.ollama_base_url == "http://127.0.0.1:11434"
    assert valid.cors_origins == ["http://127.0.0.1:5173", "https://mdt.local"]

    with pytest.raises(ValueError):
        AppSettings(ollama_base_url="ftp://bad-host:11434")

    with pytest.raises(ValueError):
        AppSettings(cors_origins=["*"])


def test_oversized_and_invalid_payloads_return_422(monkeypatch, tmp_path):
    monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "payloads.sqlite3")
    monkeypatch.setattr(run_store, "LEGACY_DB_PATH", None)
    run_store.initialize_database()

    # 1. Oversized case_summary (>12,000 chars)
    oversized_case = _valid_case_payload()
    oversized_case["case_summary"] = "X" * 12005
    assert client.post("/api/cases/validate", json=oversized_case).status_code == 422

    # 2. Oversized clinical provenance source_excerpt (>100,000 chars)
    oversized_provenance_case = _valid_case_payload()
    oversized_provenance_case["clinical_field_provenance"] = {
        "case_summary": [
            {
                "source_type": "CASE_SUMMARY",
                "source_reference": "SyntheticCase.case_summary",
                "source_excerpt": "Y" * 100005,
            }
        ]
    }
    assert client.post("/api/cases/validate", json=oversized_provenance_case).status_code == 422

    # 3. Invalid / oversized selected_agent_ids on SelectedAgentsRequest & PatientRunRequest
    assert (
        client.post(
            "/api/runs/some-run/rounds/1/run-selected",
            json={"agent_ids": []},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/runs/some-run/rounds/1/run-selected",
            json={"agent_ids": ["not-an-agent"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/runs/some-run/rounds/1/run-selected",
            json={"agent_ids": ["RO-01"] * 61},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/patients/some-patient/runs",
            json={
                "case_version_id": "11111111-1111-4111-8111-111111111111",
                "selected_agent_ids": ["invalid"],
            },
        ).status_code
        == 422
    )


def test_single_role_failure_and_circuit_breaker_in_r1(monkeypatch, tmp_path):
    patient_id, version_id = _create_accepted_run_dependencies(monkeypatch, tmp_path)

    # Part A: Single role times out/errors -> other roles still finish cleanly
    async def one_role_fails(profile, case, round_number, max_tokens=1100):
        if profile["agent_id"] == "RO-02":
            raise OllamaUnavailable("Simulated single-role timeout")
        return AgentAssessment(
            agent_id=profile["agent_id"],
            round_number=round_number,
            position="conditional",
            provisional_conclusion="Provisional educational conclusion pending biomarker confirmation.",
            preferred_educational_option="Defer definitive selection pending missing p16 result.",
            perspective_summary=f"Perspective from {profile['name']}.",
            confidence=0.6,
            evidence_gaps=["p16 status not reported."],
        )

    monkeypatch.setattr(batch_runner, "generate_agent_assessment", one_role_fails)
    res = client.post(
        f"/api/patients/{patient_id}/runs",
        json={"case_version_id": version_id},
    )
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    summary = client.get(f"/api/runs/{run_id}").json()
    assert summary["status"] == "completed_with_errors"
    assert summary["completed_count"] == len(AGENT_PROFILES) - 1
    assert summary["failed_count"] == 1

    # Part B: Consecutive OllamaUnavailable failures trip the circuit breaker cleanly
    call_count = 0

    async def always_down(profile, case, round_number, max_tokens=1100):
        nonlocal call_count
        call_count += 1
        raise OllamaUnavailable("Simulated Ollama daemon offline")

    monkeypatch.setattr(batch_runner, "CIRCUIT_BREAKER_THRESHOLD", 3)
    monkeypatch.setattr(batch_runner, "generate_agent_assessment", always_down)

    res2 = client.post(
        f"/api/patients/{patient_id}/runs",
        json={"case_version_id": version_id},
    )
    assert res2.status_code == 200
    run_id2 = res2.json()["run_id"]

    assert call_count == 3
    results2 = client.get(f"/api/runs/{run_id2}/results").json()["results"]
    assert len(results2) == len(AGENT_PROFILES)
    assert all(row["status"] == "failed" for row in results2)
    assert any("CircuitBreakerOpen" in (row["error_message"] or "") for row in results2)


def test_mocked_four_round_debate_completes_end_to_end(monkeypatch, tmp_path):
    patient_id, version_id = _create_accepted_run_dependencies(monkeypatch, tmp_path)

    async def mock_assess(profile, case, round_number, max_tokens=1100):
        return AgentAssessment(
            agent_id=profile["agent_id"],
            round_number=round_number,
            position="conditional",
            provisional_conclusion="Provisional educational conclusion conditional on biomarker and fitness details.",
            preferred_educational_option="Evaluate organ-preservation pathway once workup completes.",
            perspective_summary=f"Synthetic perspective for {profile['name']}.",
            confidence=0.65,
            evidence_gaps=["p16 status pending."],
        )

    async def mock_debate(profile, case, own, peers, max_tokens=800):
        return RoundContribution(
            agent_id=profile["agent_id"],
            round_number=2,
            position="conditional",
            provisional_conclusion="Position remains conditional after peer review.",
            response_to_other_perspectives="Engages peer arguments and preserves unresolved unknowns.",
            agreements=["Missing biomarker confirmation limits finality."],
            substantive_challenges=["Challenges unverified assumptions in peer drafts."],
            remaining_unknowns=["p16 status remains unknown."],
            risk_flags=["Educational simulation only."],
            confidence=0.65,
        )

    async def mock_adversarial(profile, case, r1, r2, peers, max_tokens=1200):
        return RoundContribution(
            agent_id=profile["agent_id"],
            round_number=3,
            position="conditional",
            provisional_conclusion="Adversarial review highlights governance and evidence gaps.",
            response_to_other_perspectives="Audits assumptions, feasibility, and safety boundaries across peers.",
            agreements=["Preserves conditional safeguards."],
            substantive_challenges=["Flags lack of verified pathological p16 status."],
            remaining_unknowns=["p16 and baseline renal function unverified."],
            risk_flags=["Not a clinical treatment instruction."],
            confidence=0.6,
        )

    async def mock_chair(run_id, case, round1, round2, round3, max_tokens=1800):
        return FinalMDTReport(
            run_id=run_id,
            report_title="Synthetic Oropharynx MDT Educational Synthesis",
            consensus_status="insufficient_information",
            chair_conclusion="The simulated MDT remains conditional pending missing biomarker and baseline data.",
            overall_educational_synthesis="All four rounds preserved role dissent, explicit conditionals, and evidence boundaries.",
            consensus_points=["Missing baseline details must be clarified."],
            unresolved_disagreements=["Optimal modality depends on unverified workup."],
            minority_and_dissenting_views=["Conservative conventional RT boundaries preserved."],
            major_uncertainties=["p16 status not reported."],
            missing_information_before_real_world_review=["Confirm p16 and baseline organ function."],
            patient_and_family_considerations=["Confirm patient goals directly."],
            feasibility_and_resource_considerations=["Verify radiotherapy access."],
            governance_and_safeguarding_considerations=["Maintain educational simulation disclaimer."],
            evidence_limitations=["Mocked local LLM output."],
            chair_reflection="Educational synthesis complete with traceable round provenance.",
        )

    monkeypatch.setattr(batch_runner, "generate_agent_assessment", mock_assess)
    monkeypatch.setattr(mdt_rounds, "generate_debate_contribution", mock_debate)
    monkeypatch.setattr(mdt_rounds, "generate_adversarial_contribution", mock_adversarial)
    monkeypatch.setattr(mdt_rounds, "generate_chair_report", mock_chair)

    start_r1 = client.post(
        f"/api/patients/{patient_id}/runs",
        json={"case_version_id": version_id},
    )
    assert start_r1.status_code == 200
    run_id = start_r1.json()["run_id"]
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "completed"

    assert client.post(f"/api/runs/{run_id}/rounds/2").status_code == 200
    assert client.get(f"/api/runs/{run_id}/rounds/2").json()["status"] == "completed"

    assert client.post(f"/api/runs/{run_id}/rounds/3").status_code == 200
    assert client.get(f"/api/runs/{run_id}/rounds/3").json()["status"] == "completed"

    assert client.post(f"/api/runs/{run_id}/rounds/4").status_code == 200
    assert client.get(f"/api/runs/{run_id}/rounds/4").json()["status"] == "completed"

    report_res = client.get(f"/api/runs/{run_id}/report")
    assert report_res.status_code == 200
    assert report_res.json()["run_id"] == run_id
    assert report_res.json()["safety_boundary"] == "educational_simulation_only"
    assert report_res.json()["not_a_treatment_instruction"] is True


def test_ensure_ollama_service_and_model_spawns_on_win32(monkeypatch):
    import shutil
    import subprocess
    import sys

    probe_calls = 0
    popen_calls: list[dict[str, object]] = []

    async def fake_probe():
        nonlocal probe_calls
        probe_calls += 1
        if probe_calls == 1:
            return {"reachable": False, "configured_model_installed": False}
        return {"reachable": True, "configured_model_installed": True}

    async def fake_sleep(_seconds: float):
        return None

    def fake_popen(cmd, **kwargs):
        popen_calls.append({"cmd": cmd, "kwargs": kwargs})
        return object()

    monkeypatch.setattr(ollama_service, "_probe_ollama", fake_probe)
    monkeypatch.setattr(shutil, "which", lambda _name: "ollama")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(sys, "platform", "win32")

    status = asyncio.run(ensure_ollama_service_and_model(auto_pull=False))
    assert status["reachable"] is True
    assert len(popen_calls) == 1
    assert popen_calls[0]["cmd"] == ["ollama", "serve"]
    assert popen_calls[0]["kwargs"]["creationflags"] != 0


def test_agent_profiles_catalog_count():
    assert len(AGENT_PROFILES) == 49
