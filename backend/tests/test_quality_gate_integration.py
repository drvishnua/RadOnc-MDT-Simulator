"""Tests for U05-U08 quality gate integration into the round pipeline."""

import json
import pytest
from unittest.mock import patch

from app.services.mdt_rounds import _run_post_round_quality_gates
from app.services import run_store


def _make_r1_row(agent_id: str, perspective: str, conclusion: str, preferred: str = "") -> dict:
    return {
        "agent_id": agent_id,
        "agent_name": f"Dr. {agent_id}",
        "status": "completed",
        "assessment": {
            "agent_id": agent_id,
            "round_number": 1,
            "role_id": agent_id,
            "perspective_summary": perspective,
            "provisional_conclusion": conclusion,
            "preferred_educational_option": preferred,
            "discussion_options": ["Option A"],
            "conditional_options": [],
        },
    }


def _make_r2_row(agent_id: str, perspective: str, conclusion: str, preferred: str = "") -> dict:
    return {
        "agent_id": agent_id,
        "agent_name": f"Dr. {agent_id}",
        "status": "completed",
        "result": {
            "agent_id": agent_id,
            "round_number": 2,
            "role_id": agent_id,
            "perspective_summary": perspective,
            "provisional_conclusion": conclusion,
            "preferred_educational_option": preferred,
            "discussion_options": ["Option A"],
            "conditional_options": [],
        },
    }


class TestPostRoundQualityGates:
    """Integration tests for _run_post_round_quality_gates."""

    def test_clean_r1_produces_zero_flags(self):
        rows = [
            _make_r1_row(
                "RADIATION_ONCOLOGIST",
                "Evaluate primary lesion geometry and organ preservation feasibility.",
                "Offer 70 Gy in 35 fractions with IMRT/VMAT.",
                "Definitive IMRT",
            ),
            _make_r1_row(
                "SPEECH_LANGUAGE_PATHOLOGIST",
                "Pre-treatment baseline swallowing evaluation and prophylactic exercises.",
                "Perform modified barium swallow study prior to radiation.",
                "Prophylactic pharyngeal strengthening",
            ),
        ]
        audit = _run_post_round_quality_gates("test-run", 1, rows)
        assert audit["total_flags"] == 0
        assert audit["role_differentiation"]["valid"]

    def test_duplicate_outputs_flagged_in_r1(self):
        same_text = "The patient requires definitive concurrent chemoradiotherapy with IMRT and cisplatin."
        rows = [
            _make_r1_row("RADIATION_ONCOLOGIST", "Radiation viewpoint.", same_text, "Concurrent CRT"),
            _make_r1_row("MEDICAL_ONCOLOGIST", "Radiation viewpoint.", same_text, "Concurrent CRT"),
        ]
        audit = _run_post_round_quality_gates("test-run", 1, rows)
        assert audit["total_flags"] > 0
        assert not audit["role_differentiation"]["valid"]
        assert len(audit["role_differentiation"]["pairwise_duplicates"]) == 1

    def test_shallow_reasoning_flagged_in_r1(self):
        rows = [
            {
                "agent_id": "RADIATION_ONCOLOGIST",
                "agent_name": "Dr. RADIATION_ONCOLOGIST",
                "status": "completed",
                "assessment": {
                    "agent_id": "RADIATION_ONCOLOGIST",
                    "round_number": 1,
                    "role_id": "RADIATION_ONCOLOGIST",
                    "perspective_summary": "Insufficient information available to make a recommendation.",
                    "provisional_conclusion": "Cannot provide any recommendation.",
                    # No discussion_options, conditional_options, or preferred option
                    "discussion_options": [],
                    "conditional_options": [],
                    "preferred_educational_option": "",
                },
            },
        ]
        audit = _run_post_round_quality_gates("test-run", 1, rows)
        assert len(audit["reasoning_depth_flags"].get("RADIATION_ONCOLOGIST", [])) >= 1

    def test_delegation_flagged_in_r2(self):
        rows = [
            _make_r2_row(
                "MEDICAL_ONCOLOGIST",
                "I agree with Dr. Smith.",
                "I concur with Dr. Smith and recommend same.",
                "Same as above",
            ),
            _make_r2_row(
                "RADIATION_ONCOLOGIST",
                "Evaluate primary lesion geometry and organ preservation feasibility.",
                "Offer 70 Gy in 35 fractions with IMRT/VMAT.",
                "Definitive IMRT",
            ),
        ]
        audit = _run_post_round_quality_gates("test-run", 2, rows)
        assert audit["total_flags"] > 0
        assert len(audit["role_differentiation"]["delegation_flags"]) == 1

    def test_quality_gates_skip_for_r3_r4(self):
        """R3 and R4 do not run R1/R2-specific quality gates."""
        rows = [
            {
                "agent_id": "RADIATION_ONCOLOGIST",
                "status": "completed",
                "result": {"agent_id": "RADIATION_ONCOLOGIST", "round_number": 3},
            },
        ]
        audit = _run_post_round_quality_gates("test-run", 3, rows)
        assert audit["total_flags"] == 0

    def test_failed_rows_are_skipped(self):
        rows = [
            {
                "agent_id": "RADIATION_ONCOLOGIST",
                "status": "failed",
                "assessment": None,
            },
        ]
        audit = _run_post_round_quality_gates("test-run", 1, rows)
        assert audit["total_flags"] == 0


class TestQualityAuditPersistence:
    """Tests for save/get round quality audit in run_store."""

    def test_save_and_retrieve_quality_audit(self, tmp_path, monkeypatch):
        monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "test.db")
        run_store.initialize_database()

        # Create a minimal run to satisfy foreign key
        from app.schemas import SyntheticCase
        case = SyntheticCase(
            scenario_title="Test Scenario",
            case_summary="A 60-year-old with laryngeal squamous cell carcinoma presenting with hoarseness.",
            primary_site="Larynx",
            histology="SCC",
        )
        run = run_store.create_run(case)
        run_id = run["run_id"]

        audit_data = {
            "run_id": run_id,
            "round_number": 1,
            "reasoning_depth_flags": {},
            "role_differentiation": {"valid": True, "flags": []},
            "total_flags": 0,
        }
        run_store.save_round_quality_audit(run_id, 1, audit_data)

        retrieved = run_store.get_round_quality_audit(run_id, 1)
        assert retrieved is not None
        assert retrieved["total_flags"] == 0
        assert retrieved["role_differentiation"]["valid"]

    def test_get_nonexistent_audit_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(run_store, "DB_PATH", tmp_path / "test.db")
        run_store.initialize_database()

        result = run_store.get_round_quality_audit("nonexistent", 1)
        assert result is None
