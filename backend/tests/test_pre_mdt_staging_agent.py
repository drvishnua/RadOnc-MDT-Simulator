import asyncio
import json

from app.schemas import SyntheticCase
from app.services import ollama
from app.services.pre_mdt_staging_agent import run_pre_mdt_staging_agent


def test_staging_agent_never_invents_n0_when_nodal_imaging_missing():
    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsillar fossa",
        case_summary="2x1 cm ulceroproliferative growth in right tonsillar fossa.",
        age_years=50,
        sex_at_birth="Male",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        relevant_investigations=["chest xray - normal", "CBC, RLE - normal"],
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.agent_id == "STG-00"
    assert res.staging_locked is True
    assert "UICC-AJCC-TNM-GENERAL-RULES" in res.staging_reference_ids
    assert "AJCC-8TH-NONHPV-OROPHARYNX" in res.staging_reference_ids
    assert res.staging_rules_applied
    assert res.mode == "provisional_derived"
    assert res.provisional_tnm["t"] == "T1"
    assert res.provisional_tnm["n"] is None
    assert "Nx" in res.provisional_stage_label
    assert "N0" not in res.provisional_stage_label
    assert any("Nx" in m for m in res.missing_for_complete_staging)


def test_staging_agent_derives_node_from_imaging_summary_and_investigation_records():
    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsil",
        case_summary="2x1 cm growth in right tonsillar fossa.",
        age_years=50,
        sex_at_birth="Male",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        imaging_summary="CECT neck shows 1.5 cm right level II cervical lymph node; no distant metastasis.",
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.mode == "provisional_derived"
    assert res.provisional_tnm["n"] == "N1"
    assert "N1" in res.provisional_stage_label
    assert "N0" not in res.provisional_stage_label


def test_staging_agent_flags_discrepancy_when_provided_n0_conflicts_with_imaging_node():
    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsil",
        case_summary="2x1 cm growth in right tonsillar fossa.",
        age_years=50,
        sex_at_birth="Male",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        clinical_t_stage="T1",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        imaging_summary="MRI neck demonstrates a 1.8 cm ipsilateral right level II lymph node.",
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.mode == "discrepancy_detected"
    assert any("N0" in d and "N1" in d for d in res.discrepancies)


def test_staging_agent_verifies_concordant_provided_staging():
    case = SyntheticCase(
        scenario_title="Ca oropharynx - right tonsil",
        case_summary="2x1 cm growth in right tonsillar fossa.",
        age_years=50,
        sex_at_birth="Male",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        clinical_t_stage="T1",
        clinical_n_stage="N1",
        clinical_m_stage="M0",
        imaging_summary="CECT neck shows a 1.5 cm right level II lymph node; chest CT negative for distant metastasis.",
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.mode == "verified_concordant"
    assert not res.discrepancies


def test_ollama_prompt_includes_pre_mdt_staging_agent_report(monkeypatch):
    draft = {
        "position": "supports",
        "provisional_conclusion": "Provisional staging cT1 N1 M0 noted from STG-00.",
        "preferred_educational_option": "Consider definitive chemoradiation.",
        "perspective_summary": "Conservative radiotherapy perspective.",
        "assumptions": [],
        "unknowns": ["p16 status is not supplied."],
        "discussion_options": [],
        "conditional_options": [],
        "evidence_gaps": [],
        "uncertainty_notes": [],
        "disagreement_notes": [],
        "confidence": 0.8,
    }
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": json.dumps(draft)}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, path, json=None):
            captured["request"] = json
            return FakeResponse()

    monkeypatch.setattr(ollama.httpx, "AsyncClient", FakeAsyncClient)
    case = SyntheticCase(
        scenario_title="Ca oropharynx",
        case_summary="2x1 cm right tonsillar growth.",
        primary_site="Right tonsil - oropharynx",
        histology="Squamous cell carcinoma",
        imaging_summary="CECT neck shows a 1.5 cm right level II lymph node.",
    )
    profile = {
        "agent_id": "RO-02",
        "name": "Conservative & Time-Tested Radiation Oncologist",
        "mandate": "Recommend conservative radiotherapy.",
    }
    asyncio.run(ollama.generate_agent_assessment(profile, case, 1))
    assert "PRE-MDT STAGING AGENT REPORT (STG-00 — LOCKED FOR SIMULATION)" in captured["request"]["prompt"]
    assert "STAGING LOCK MANDATE" in captured["request"]["prompt"]
    assert "No other agent may rethink, re-stage" in captured["request"]["prompt"]
    assert "cT1 N1" in captured["request"]["prompt"]


def test_build_case_prompt_context_redacts_discordant_n_stage():
    from app.services.case_integrity import build_case_prompt_context

    case = SyntheticCase(
        scenario_title="Ca larynx with nodal discrepancy",
        case_summary="3.0 cm glottic mass with vocal cord fixation.",
        primary_site="Glottic larynx",
        histology="Squamous cell carcinoma",
        imaging_summary="CECT neck shows a 2.0 cm right level II lymph node; chest CT negative.",
        clinical_t_stage="T3",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.mode == "discrepancy_detected"
    ctx = build_case_prompt_context(case)
    assert ctx["case_snapshot"]["clinical_n_stage"] is None
    assert "clinical_n_stage" in ctx["case_snapshot_redacted_conflicting_fields"]


def test_build_case_prompt_context_preserves_concordant_n_stage():
    from app.services.case_integrity import build_case_prompt_context

    case = SyntheticCase(
        scenario_title="Ca tonsil concordant N1",
        clinical_t_stage="T1",
        clinical_n_stage="N1",
        clinical_m_stage="M0",
        primary_site="Right tonsil - oropharynx",
        case_summary="1.8 cm right tonsillar growth.",
        imaging_summary="CECT neck shows a 1.5 cm right level II lymph node; chest CT negative.",
        histology="Squamous cell carcinoma",
    )
    res = run_pre_mdt_staging_agent(case)
    assert res.mode != "discrepancy_detected"
    ctx = build_case_prompt_context(case)
    assert ctx["case_snapshot"]["clinical_n_stage"] == "N1"
    assert "clinical_n_stage" not in ctx["case_snapshot_redacted_conflicting_fields"]


def test_staging_agent_grounds_figo_cervix_rules():
    case = SyntheticCase(
        scenario_title="Ca cervix with pelvic nodes",
        case_summary="3.5 cm cervical lesion with parametrial invasion and pelvic lymph node.",
        primary_site="Cervix",
        histology="Squamous cell carcinoma",
        imaging_summary="MRI pelvis shows parametrial invasion and 1.4 cm right external iliac lymph node; chest CT negative.",
    )
    res = run_pre_mdt_staging_agent(case)
    assert "FIGO-2018-AJCC-CERVIX" in res.staging_reference_ids
    assert res.provisional_tnm["t"] == "T2b"
    assert res.provisional_tnm["n"] == "N1"
    assert res.staging_locked is True
