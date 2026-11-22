"""Unit and integration tests for Evidence Retrieval and Prompt Injection Engine.

Tests:
1. Clinical facet extraction across Head & Neck, Lung, Breast, and Prostate synthetic cases.
2. Regex word-boundary protection preventing substring collisions (e.g. 'anal' in 'analysis').
3. 45-persona remit domain routing covering all 7 specialist categories without unhandled roles.
4. Prompt context formatting: token length bounds, [source_id: <ID>] tags, empty handling.
5. End-to-end integration with MedicalLibraryIndexer and SQLite FTS5 search.
"""
from __future__ import annotations

import pytest

from app.agents.catalog import AGENT_PROFILES
from app.schemas import SyntheticCase
from app.services.library_indexer import (
    DOMAIN_PARTITIONS,
    MedicalLibraryIndexer,
)
from app.services.evidence_retrieval import (
    EvidenceRetrievalEngine,
    RetrievedPassage,
    get_evidence_retrieval_engine,
)


def _make_case(**kwargs) -> SyntheticCase:
    base = {
        "scenario_title": "Test Oncology Case",
        "case_summary": "Synthetic test patient presented for multi-disciplinary evaluation.",
    }
    base.update(kwargs)
    return SyntheticCase.model_validate(base)


def test_facet_extraction_head_and_neck() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    case = _make_case(
        primary_site="Larynx",
        anatomical_subsite="Glottic",
        histology="Squamous cell carcinoma",
        clinical_t_stage="T2",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
        relevant_comorbidities=["Hypertension", "Mild GERD"],
        performance_status="ECOG 0",
    )
    facets = engine.extract_case_facets(case)

    assert facets["primary_site"] == "head_and_neck"
    assert facets["raw_primary_site"] == "Larynx"
    assert facets["anatomical_subsite"] == "Glottic"
    assert facets["histology"] == "Squamous cell carcinoma"
    assert facets["stage"] == "T2 N0 M0"
    assert "parotid glands" in facets["oars"]
    assert "spinal cord" in facets["oars"]
    assert "Hypertension" in facets["comorbidities"]
    assert facets["performance_status"] == "ECOG 0"


def test_facet_extraction_lung() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    case = _make_case(
        primary_site="Lung",
        histology="Adenocarcinoma",
        stage_group="Stage IIIA",
        relevant_comorbidities=["COPD", "Tobacco use disorder"],
        case_summary="Patient with NSCLC involving the right upper lobe.",
    )
    facets = engine.extract_case_facets(case)

    assert facets["primary_site"] == "lung"
    assert facets["histology"] == "Adenocarcinoma"
    assert facets["stage"] == "Stage IIIA"
    assert "lungs (V20/MLD)" in facets["oars"]
    assert "esophagus" in facets["oars"]
    assert "COPD" in facets["comorbidities"]


def test_facet_extraction_breast() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    case = _make_case(
        primary_site="Breast",
        histology="Invasive ductal carcinoma",
        clinical_t_stage="T1c",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
    )
    facets = engine.extract_case_facets(case)

    assert facets["primary_site"] == "breast"
    assert facets["histology"] == "Invasive ductal carcinoma"
    assert facets["stage"] == "T1c N0 M0"
    assert "heart (LAD)" in facets["oars"]
    assert "ipsilateral lung" in facets["oars"]


def test_facet_extraction_prostate() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    case = _make_case(
        primary_site="Prostate",
        histology="Adenocarcinoma",
        clinical_stage_group="Stage IIB",
    )
    facets = engine.extract_case_facets(case)

    assert facets["primary_site"] == "prostate"
    assert facets["stage"] == "Stage IIB"
    assert "rectum" in facets["oars"]
    assert "bladder" in facets["oars"]
    assert "penile bulb" in facets["oars"]


def test_facet_extraction_prevents_substring_collision() -> None:
    """Verifies that words containing substrings (e.g. 'anal' in 'analysis') do NOT falsely collide."""
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    
    # Case with 'analysis' in summary, but stomach/gastric site
    case_gastric = _make_case(
        primary_site="Stomach",
        case_summary="Statistical analysis of molecular biomarkers shows HER2 overexpression.",
    )
    facets_gastric = engine.extract_case_facets(case_gastric)
    assert facets_gastric["primary_site"] == "gastrointestinal"
    assert facets_gastric["primary_site"] != "colorectal"

    # Case with true anal canal cancer
    case_anal = _make_case(
        primary_site="Anal canal",
        case_summary="Invasive squamous cell carcinoma of the anal margin.",
    )
    facets_anal = engine.extract_case_facets(case_anal)
    assert facets_anal["primary_site"] == "colorectal"


def test_45_persona_domain_routing_covers_all_catalog_roles() -> None:
    """Ensure all 45 specialist personas are mapped to clinical domain partitions."""
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    assert len(AGENT_PROFILES) == 49

    valid_domains = set(DOMAIN_PARTITIONS)

    for profile in AGENT_PROFILES:
        role_id = profile["agent_id"]
        category = profile["category"]
        domains = engine.get_role_domains(role_id)

        assert domains, f"Role {role_id} returned empty domain list!"
        assert all(d in valid_domains for d in domains), f"Role {role_id} has invalid domain: {domains}"

        # Subspecialty remit assertions
        if category == "radiation_oncology":
            assert "guidelines" in domains
            assert "organ_tolerances" in domains
            assert "textbooks_radiobiology" in domains
        elif category == "medical_oncology":
            assert "trials_systemic" in domains
            assert "guidelines" in domains
        elif category == "surgical_oncology":
            assert "guidelines" in domains
            assert "staging_anatomy" in domains
        elif role_id == "DS-01":
            assert "staging_anatomy" in domains
        elif role_id == "DS-02":
            assert "staging_anatomy" in domains
        elif role_id == "DS-03":
            assert "general_medicine" in domains
            assert "organ_tolerances" in domains
        elif category == "patient_perspective":
            assert "guidelines" in domains
            assert "organ_tolerances" in domains
        elif role_id == "SG-05":
            # Evidence auditor must cover all domains
            assert len(domains) == len(DOMAIN_PARTITIONS)
        elif role_id == "SG-07":
            # MDT Chair
            assert "guidelines" in domains
            assert "trials_systemic" in domains
        elif category == "family_social_vulnerability":
            assert "general_medicine" in domains


def test_prompt_injection_formatting_empty_and_bounded() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))

    # Empty list returns empty string
    assert engine.format_prompt_injection([]) == ""

    # Populate 3 mock passages
    passages = [
        RetrievedPassage(
            source_id="NCCN-HN-2024",
            title="NCCN Clinical Practice Guidelines in Oncology: Head and Neck Cancers",
            domain="guidelines",
            snippet="For T2N0 glottic larynx cancer, definitive radiotherapy (66-70 Gy in 2.0 Gy/fx or 65.25 Gy in 2.25 Gy/fx) achieves 85-90% local control with organ preservation.",
            relevance_score=9.5,
        ),
        RetrievedPassage(
            source_id="QUANTEC-PAROTID-2010",
            title="QUANTEC Parotid Gland Tolerance Monograph",
            domain="organ_tolerances",
            snippet="Mean dose to at least one parotid gland < 20 Gy, or combined mean dose < 25 Gy significantly reduces long-term severe xerostomia risk.",
            relevance_score=8.7,
        ),
        RetrievedPassage(
            source_id="RTOG-9111",
            title="RTOG 9111 Landmark Laryngeal Preservation Trial",
            domain="trials_systemic",
            snippet="Concurrent cisplatin with radiotherapy significantly improved laryngeal preservation over induction chemotherapy followed by RT or RT alone.",
            relevance_score=8.2,
        ),
    ]

    formatted = engine.format_prompt_injection(passages)
    assert "VERIFIED CLINICAL EVIDENCE CONTEXT:" in formatted
    assert "[source_id: NCCN-HN-2024]" in formatted
    assert "[source_id: QUANTEC-PAROTID-2010]" in formatted
    assert "[source_id: RTOG-9111]" in formatted
    assert "Instruction: You may cite only verified sources" in formatted

    # Token/character length boundary check (300-600 tokens ~ 1200-2400 chars)
    assert len(formatted) < 2400
    assert len(formatted) > 300


def test_end_to_end_retrieval_with_in_memory_indexer() -> None:
    """Test full pipeline: index text chunks -> query for role -> format prompt context."""
    indexer = MedicalLibraryIndexer(library_dir=".", db_path=":memory:")

    # Index sample documents across domains
    indexer.index_text_chunks(
        doc_id="NCCN-LARYNX-V1-2024",
        title="NCCN Larynx Cancer Guidelines v1.2024",
        domain="guidelines",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "T2 N0 glottic carcinoma treatment options include definitive radiotherapy (66-70 Gy) or transoral laser microsurgery. Radiotherapy preserves vocal cord anatomy.",
            "T3-T4a disease requires concurrent chemoradiotherapy or total laryngectomy based on cartilage invasion and functional larynx status.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="QUANTEC-SPINAL-CORD-2010",
        title="QUANTEC Spinal Cord Dose-Volume Constraints",
        domain="organ_tolerances",
        disease_sites=["general", "head_and_neck", "lung"],
        text_chunks=[
            "Spinal cord max point dose Dmax should be kept strictly below 45-50 Gy in conventional 2 Gy fractions to maintain myelopathy risk < 0.2%.",
        ],
    )
    indexer.index_text_chunks(
        doc_id="RTOG-9111-TRIAL",
        title="RTOG 9111 Laryngeal Preservation Trial",
        domain="trials_systemic",
        disease_sites=["head_and_neck"],
        text_chunks=[
            "Concurrent cisplatin (100 mg/m2 days 1, 22, 43) with definitive radiotherapy demonstrated superior larynx preservation rates compared with RT alone in stage III-IV glottic and supraglottic cancer.",
        ],
    )

    engine = EvidenceRetrievalEngine(indexer=indexer)
    case = _make_case(
        primary_site="Larynx",
        anatomical_subsite="Glottic",
        histology="Squamous cell carcinoma",
        clinical_t_stage="T2",
        clinical_n_stage="N0",
        clinical_m_stage="M0",
    )

    # 1. Radiation Oncologist (RO-01) retrieval
    ro_passages = engine.retrieve_evidence_for_role("RO-01", case, limit=3)
    assert ro_passages
    ro_source_ids = {p.source_id for p in ro_passages}
    assert any("NCCN-LARYNX" in sid or "QUANTEC" in sid for sid in ro_source_ids)

    # Format RO prompt injection
    ro_prompt_context = engine.format_prompt_injection(ro_passages)
    assert "[source_id:" in ro_prompt_context
    assert "VERIFIED CLINICAL EVIDENCE CONTEXT:" in ro_prompt_context

    # 2. Medical Oncologist (MO-01) retrieval
    mo_passages = engine.retrieve_evidence_for_role("MO-01", case, limit=3)
    assert mo_passages
    mo_source_ids = {p.source_id for p in mo_passages}
    assert any("RTOG-9111" in sid or "NCCN" in sid for sid in mo_source_ids)

    # 3. Surgical Oncologist (SO-01) retrieval
    so_passages = engine.retrieve_evidence_for_role("SO-01", case, limit=3)
    assert so_passages


def test_unknown_role_fallback_is_safe() -> None:
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))
    domains = engine.get_role_domains("UNKNOWN-ROLE-99")
    assert "guidelines" in domains
    assert "general_medicine" in domains


def test_facet_extraction_precedence_ignores_incidental_summary_mention() -> None:
    """Verifies strict hierarchical disease site resolution: raw_site takes precedence over summary."""
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))

    # Incidental mention of 'lung cancer' in family history/summary for a prostate cancer patient
    case_prostate = _make_case(
        primary_site="Prostate",
        case_summary="Patient presented with elevated PSA. Father died of lung cancer. Biopsy confirms adenocarcinoma.",
    )
    facets_prostate = engine.extract_case_facets(case_prostate)
    assert facets_prostate["primary_site"] == "prostate"
    assert facets_prostate["primary_site"] != "lung"

    # Incidental mention of 'colon cancer' in breast cancer case
    case_breast = _make_case(
        primary_site="Breast",
        case_summary="Patient with palpable breast mass. Sister had colon cancer. Staging CT shows no distant metastases.",
    )
    facets_breast = engine.extract_case_facets(case_breast)
    assert facets_breast["primary_site"] == "breast"
    assert facets_breast["primary_site"] != "colorectal"

    # Subsite takes precedence over summary when raw_site is not a recognized cancer pattern
    case_subsite = _make_case(
        primary_site="Primary Tumor",
        anatomical_subsite="Glottic",
        case_summary="Patient also noted an incidental skin lesion on the shoulder.",
    )
    facets_subsite = engine.extract_case_facets(case_subsite)
    assert facets_subsite["primary_site"] == "head_and_neck"
    assert facets_subsite["primary_site"] != "skin"


def test_facet_extraction_pathological_staging_fallback() -> None:
    """Verifies fallback to pathological staging when clinical staging is not reported."""
    engine = EvidenceRetrievalEngine(indexer=MedicalLibraryIndexer(library_dir=".", db_path=":memory:"))

    # Case with pathological stage group when clinical staging is absent
    case_path_group = _make_case(
        primary_site="Prostate",
        pathological_stage_group="Stage IIIC",
    )
    facets = engine.extract_case_facets(case_path_group)
    assert facets["stage"] == "Stage IIIC"

    # Case with pathological TNM components when clinical staging is absent
    case_path_tnm = _make_case(
        primary_site="Breast",
        pathological_t_stage="pT2",
        pathological_n_stage="pN1a",
        pathological_m_stage="cM0",
    )
    facets_tnm = engine.extract_case_facets(case_path_tnm)
    assert facets_tnm["stage"] == "pT2 pN1a cM0"


def test_logger_defined_in_ollama_and_mdt_generation() -> None:
    """Verifies that logger is properly defined at module level in both ollama and mdt_generation."""
    import logging
    import app.services.ollama as ollama_svc
    import app.services.mdt_generation as mdt_gen_svc

    assert hasattr(ollama_svc, "logger")
    assert isinstance(ollama_svc.logger, logging.Logger)
    assert hasattr(mdt_gen_svc, "logger")
    assert isinstance(mdt_gen_svc.logger, logging.Logger)


@pytest.mark.anyio
async def test_evidence_retrieval_exception_fallback_in_ollama_and_mdt_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies that exceptions in evidence retrieval are caught and logged without NameError."""
    from unittest.mock import AsyncMock, MagicMock
    import app.services.ollama as ollama_svc
    import app.services.mdt_generation as mdt_gen_svc

    # Configure mock engine to raise an exception
    def _exploding_engine():
        raise RuntimeError("Simulated medical library database lock")

    monkeypatch.setattr(
        "app.services.evidence_retrieval.get_evidence_retrieval_engine",
        _exploding_engine,
    )

    case = _make_case(primary_site="Prostate")
    profile = {"agent_id": "RO-01", "name": "Radiation Oncologist", "mandate": "Evaluate radiation"}

    # Track logger.debug calls
    debug_calls: list[str] = []
    monkeypatch.setattr(
        ollama_svc.logger,
        "debug",
        lambda msg, *args: debug_calls.append(msg % args if args else msg),
    )
    monkeypatch.setattr(
        mdt_gen_svc.logger,
        "debug",
        lambda msg, *args: debug_calls.append(msg % args if args else msg),
    )

    # 1. Test generate_agent_assessment fallback in ollama.py
    mock_post_response = MagicMock()
    mock_post_response.json.return_value = {
        "response": '{"position": "supports", "provisional_conclusion": "Curative RT indicated.", "preferred_educational_option": "EBRT 78 Gy", "perspective_summary": "Standard curative pathway.", "assumptions": [], "unknowns": [], "discussion_options": [], "conditional_options": [], "evidence_gaps": [], "uncertainty_notes": [], "disagreement_notes": [], "confidence": 0.85}'
    }
    mock_post_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_post_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)

    assessment = await ollama_svc.generate_agent_assessment(profile, case, round_number=1)
    assert assessment.position == "supports"
    assert any("Evidence retrieval omitted in generate_agent_assessment" in call for call in debug_calls)

    # 2. Test generate_debate_contribution fallback in mdt_generation.py
    from app.round_schemas import Round2ContributionDraft
    fake_r2_draft = Round2ContributionDraft(
        position="supports",
        provisional_conclusion="Definitive radiation therapy is supported by clinical presentation.",
        response_to_other_perspectives="Agrees with the general multidisciplinary management approach.",
        agreements=[],
        substantive_challenges=[],
        position_changes=[],
        remaining_unknowns=[],
        risk_flags=[],
        confidence=0.85,
        source_opinion_responses=[],
    )
    monkeypatch.setattr(
        mdt_gen_svc,
        "_generate_structured",
        AsyncMock(return_value=fake_r2_draft),
    )

    own_r1 = {"position": "supports", "provisional_conclusion": "RT indicated."}
    r2_contribution = await mdt_gen_svc.generate_debate_contribution(
        profile=profile,
        case=case,
        own_independent_assessment=own_r1,
        peer_views=[],
    )
    assert r2_contribution.position == "supports"
    assert any("Evidence retrieval omitted in generate_debate_contribution" in call for call in debug_calls)
