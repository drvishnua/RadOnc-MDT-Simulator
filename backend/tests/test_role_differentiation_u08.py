"""Tests for U08 anti-duplication, role differentiation, and adversarial controls."""

import pytest
from app.services.case_integrity import (
    validate_role_differentiation_and_anti_duplication,
    audit_adversarial_controls,
)


def test_anti_duplication_flags_identical_outputs():
    identical_text = "The patient requires definitive concurrent chemoradiotherapy using standard fractionated IMRT with cisplatin."
    assessments = [
        {
            "role_id": "radiation_oncologist",
            "perspective_summary": "Radiation oncology viewpoint.",
            "provisional_conclusion": identical_text,
            "preferred_educational_option": "Concurrent CRT",
        },
        {
            "role_id": "medical_oncologist",
            "perspective_summary": "Radiation oncology viewpoint.",
            "provisional_conclusion": identical_text,
            "preferred_educational_option": "Concurrent CRT",
        },
    ]

    report = validate_role_differentiation_and_anti_duplication(assessments, similarity_threshold=0.8)
    assert not report["valid"]
    assert len(report["pairwise_duplicates"]) == 1
    assert report["pairwise_duplicates"][0]["role_1"] == "radiation_oncologist"
    assert report["pairwise_duplicates"][0]["role_2"] == "medical_oncologist"


def test_anti_duplication_allows_differentiated_outputs():
    assessments = [
        {
            "role_id": "radiation_oncologist",
            "perspective_summary": "Evaluate primary laryngeal lesion geometry and organ preservation feasibility.",
            "provisional_conclusion": "Offer 70 Gy in 35 fractions with IMRT/VMAT sparing contralateral parotid.",
            "preferred_educational_option": "Definitive IMRT",
        },
        {
            "role_id": "speech_language_pathologist",
            "perspective_summary": "Pre-treatment baseline swallowing evaluation and prophylactic swallowing exercises.",
            "provisional_conclusion": "Perform modified barium swallow study (MBSS) prior to radiation to establish baseline dysphagia risk.",
            "preferred_educational_option": "Prophylactic pharyngeal strengthening",
        },
    ]

    report = validate_role_differentiation_and_anti_duplication(assessments, similarity_threshold=0.8)
    assert report["valid"]
    assert len(report["pairwise_duplicates"]) == 0
    assert len(report["delegation_flags"]) == 0


def test_delegation_detection_flags_lazy_agreement():
    assessments = [
        {
            "role_id": "medical_oncologist",
            "perspective_summary": "I agree with Dr. Smith.",
            "provisional_conclusion": "I concur with Dr. Smith and recommend same.",
            "preferred_educational_option": "Same as above",
        }
    ]

    report = validate_role_differentiation_and_anti_duplication(assessments)
    assert not report["valid"]
    assert len(report["delegation_flags"]) == 1
    assert report["delegation_flags"][0]["role_id"] == "medical_oncologist"


def test_adversarial_controls_positive_and_negative():
    planted_facts = ["Stage IVc with hepatic metastases confirmed on PET"]

    # Positive control: challenge correctly flags the planted fact
    r3_challenges_with_hit = [
        {
            "challenge": "Unsupported metastasis claim",
            "target_claim": "Stage IVc with hepatic metastases confirmed on PET",
            "target_role": "medical_oncologist",
            "reasoning": "No abdominal imaging or PET report exists in intake data.",
        }
    ]

    result = audit_adversarial_controls(r3_challenges_with_hit, planted_unsupported_facts=planted_facts)
    assert result["passed_positive_control"]
    assert result["passed_negative_control"]
    assert len(result["detected_planted_facts"]) == 1

    # Positive control failure: planted fact ignored
    r3_challenges_miss = [
        {
            "challenge": "Dental assessment missing",
            "target_claim": "Dentition cleared",
            "target_role": "dentist",
            "reasoning": "No panorex available.",
        }
    ]
    result_miss = audit_adversarial_controls(r3_challenges_miss, planted_unsupported_facts=planted_facts)
    assert not result_miss["passed_positive_control"]
    assert "Stage IVc with hepatic metastases confirmed on PET" in result_miss["unflagged_planted_facts"]
