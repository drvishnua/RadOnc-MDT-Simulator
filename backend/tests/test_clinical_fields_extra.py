# Additional regression tests for clinical_fields module
import sys
import os
import pytest

# Ensure the app package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import clinical_fields as cf

def test_normalize_clinical_tnm_valid():
    # Simple valid inputs
    assert cf.normalize_clinical_tnm_component(cf.CLINICAL_T_STAGE, "T1") == "T1"
    assert cf.normalize_clinical_tnm_component(cf.CLINICAL_N_STAGE, "N2") == "N2"
    assert cf.normalize_clinical_tnm_component(cf.CLINICAL_M_STAGE, "M0") == "M0"
    # Accept prefixes YC (clinical staging with Y prefix)
    assert cf.normalize_clinical_tnm_component(cf.CLINICAL_T_STAGE, "YC T3") == "YCT3"

def test_normalize_clinical_tnm_invalid_prefix():
    with pytest.raises(ValueError, match="Pathological staging cannot be normalized into a clinical field"):
        cf.normalize_clinical_tnm_component(cf.CLINICAL_T_STAGE, "pT2")

def test_normalize_clinical_tnm_wrong_component():
    with pytest.raises(ValueError, match="requires a N-component"):
        cf.normalize_clinical_tnm_component(cf.CLINICAL_N_STAGE, "T1")

def test_normalize_clinical_tnm_invalid_value():
    with pytest.raises(ValueError, match="Unrecognised N-component value"):
        cf.normalize_clinical_tnm_component(cf.CLINICAL_N_STAGE, "N5")

def test_normalize_pathological_tnm_valid():
    assert cf.normalize_pathological_tnm_component(cf.PATHOLOGICAL_T_STAGE, "pT2") == "PT2"
    assert cf.normalize_pathological_tnm_component(cf.PATHOLOGICAL_N_STAGE, "ypN1") == "YPN1"

def test_normalize_pathological_tnm_invalid_prefix():
    with pytest.raises(ValueError, match="A pathological TNM component must retain a p or yp prefix"):
        cf.normalize_pathological_tnm_component(cf.PATHOLOGICAL_T_STAGE, "cT2")

def test_normalize_pathological_tnm_wrong_component():
    with pytest.raises(ValueError, match="requires a N-component"):
        cf.normalize_pathological_tnm_component(cf.PATHOLOGICAL_N_STAGE, "pT1")

def test_normalize_stage_group_token_variants():
    assert cf.normalize_stage_group_token("Stage III") == "3"
    assert cf.normalize_stage_group_token("III") == "3"
    assert cf.normalize_stage_group_token("IVB") == "4B"
    assert cf.normalize_stage_group_token("2A") == "2A"
    # Roman numerals
    assert cf.normalize_stage_group_token("II") == "2"
    assert cf.normalize_stage_group_token("IV") == "4"

def test_normalize_stage_group_token_invalid():
    with pytest.raises(ValueError, match="Unrecognised stage-group syntax"):
        cf.normalize_stage_group_token("Stage X")

def test_require_supported_registry_version_ok():
    cf.require_supported_registry_version(cf.CLINICAL_FIELD_REGISTRY_VERSION)  # should not raise

def test_require_supported_registry_version_bad():
    with pytest.raises(ValueError, match="saved record uses clinical field registry version"):
        cf.require_supported_registry_version("1.0.0")

def test_clinical_field_registry_sha256_consistency():
    h1 = cf.clinical_field_registry_sha256()
    h2 = cf.clinical_field_registry_sha256()
    assert h1 == h2
    # Different version should change hash
    h_v1 = cf.clinical_field_registry_sha256("1.0.0")
    assert h_v1 != h1
    with pytest.raises(ValueError, match="Unsupported clinical field registry version"):
        cf.clinical_field_registry_sha256("999.0.0")

def test_build_registry_prompt_payload_includes_sha256():
    payload = cf.build_registry_prompt_payload()
    assert "sha256" in payload
    # Non-default version should not include sha256
    payload_v1 = cf.build_registry_prompt_payload(cf.HISTORICAL_CLINICAL_FIELD_REGISTRY_VERSION)
    assert "sha256" not in payload_v1
