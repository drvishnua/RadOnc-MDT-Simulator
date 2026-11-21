"""Regression tests for the live R3 positive-control oracle."""

from scripts.representative_model_provenance_validation import (
    SEEDED_CASE_INTEGRITY_FLAG,
    SEEDED_CASE_INTEGRITY_RAW_STATEMENT,
    _build_r3_peer_views,
    _has_expected_source_bound_challenge,
    _r1_fixture,
    _require_installed_model_record,
    _literal_seeded_stage_repetition_findings,
    _positive_control_claim_repetition_findings,
    _unqualified_stage_assertions,
)


def test_positive_control_requires_exact_supplied_peer_and_quoted_claim():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion" '
            "this is unsupported because no complete role-level record was supplied."
        ],
    }

    assert _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_challenge_attributed_to_wrong_peer():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:MO-01 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_generic_challenge_without_exact_quote():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            "The peer makes an unsupported claim about overall agreement."
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_quote_from_peer_not_in_supplied_sample():
    result = {
        "source_peer_ids": ["MO-01", "RO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_source_identifier_prefix_collision():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02-extra states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )



def test_positive_control_rejects_repeated_claim_without_explicit_rebuttal():
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_positive_control_rejects_rebuttal_marker_that_occurs_only_inside_the_quote():
    quoted_claim = "The entire 45-role MDT agrees; unsupported evidence is absent"
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            f'R2:SO-02 states "{quoted_claim}".'
        ],
    }

    assert not _has_expected_source_bound_challenge(
        result,
        source_agent_id="SO-02",
        quoted_claim=quoted_claim,
    )


def test_positive_control_rejects_empty_claim_and_non_list_peer_ids():
    challenge = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion"; '
            "this is unsupported because no complete role-level record was supplied."
        ],
    }
    assert not _has_expected_source_bound_challenge(
        challenge,
        source_agent_id="SO-02",
        quoted_claim="",
    )

    malformed = {
        "source_peer_ids": "SO-02",
        "substantive_challenges": challenge["substantive_challenges"],
    }
    assert not _has_expected_source_bound_challenge(
        malformed,
        source_agent_id="SO-02",
        quoted_claim="The entire 45-role MDT agrees with this conclusion",
    )


def test_model_registry_requires_exact_installed_model_and_full_digest():
    model_name = "medgemma1.5:4b-it-q4_K_M"
    digest = "sha256:" + ("a" * 64)
    snapshot = {
        "tags": {"models": [{"name": model_name, "model": model_name, "digest": digest, "size": 3300000000}]}
    }

    record = _require_installed_model_record(snapshot, model_name)

    assert record["name"] == model_name
    assert record["digest"] == digest


def test_model_registry_accepts_and_canonicalises_bare_full_digest_from_ollama():
    model_name = "qwen3.5:4b"
    bare_digest = "d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
    snapshot = {
        "tags": {
            "models": [{
                "name": model_name,
                "model": model_name,
                "digest": bare_digest,
                "size": 3324173934,
            }]
        }
    }

    record = _require_installed_model_record(snapshot, model_name)

    assert record["digest"] == f"sha256:{bare_digest}"
    assert snapshot["tags"]["models"][0]["digest"] == bare_digest


def test_model_registry_canonicalises_uppercase_bare_and_prefixed_digests():
    model_name = "qwen3.5:4b"
    bare = "D8B0F5E9760CD1682034F292D7EF72EC46F432149BE0DF7574BF2D6E92E38C04"
    for raw in (bare, f"SHA256:{bare}"):
        record = _require_installed_model_record({
            "tags": {"models": [{"name": model_name, "digest": raw}]}
        }, model_name)
        assert record["digest"] == f"sha256:{bare.lower()}"


def test_model_registry_rejects_public_short_identifier_as_digest():
    model_name = "medgemma1.5:4b-it-q4_K_M"
    snapshot = {
        "tags": {"models": [{"name": model_name, "model": model_name, "digest": "433252621ab1"}]}
    }

    try:
        _require_installed_model_record(snapshot, model_name)
    except RuntimeError as exc:
        assert "full SHA-256 digest" in str(exc)
    else:
        raise AssertionError("A short public identifier must never pass as a model digest.")


def test_model_registry_rejects_missing_or_ambiguous_model_record():
    model_name = "medgemma1.5:4b-it-q4_K_M"
    valid_digest = "sha256:" + ("b" * 64)
    for models in (
        [],
        [
            {"name": model_name, "model": model_name, "digest": valid_digest},
            {"name": model_name, "model": model_name, "digest": "sha256:" + ("c" * 64)},
        ],
    ):
        try:
            _require_installed_model_record({"tags": {"models": models}}, model_name)
        except RuntimeError as exc:
            assert "exactly one" in str(exc)
        else:
            raise AssertionError("Missing or ambiguous model records must fail closed.")


def test_validation_artifact_path_guard_accepts_a_new_path(tmp_path):
    from scripts.representative_model_provenance_validation import _assert_artifact_path_is_new

    path = tmp_path / "new" / "run.json"
    _assert_artifact_path_is_new(path)


def test_validation_artifact_path_guard_rejects_existing_path(tmp_path):
    from scripts.representative_model_provenance_validation import _assert_artifact_path_is_new
    import pytest

    path = tmp_path / "existing.json"
    path.write_text("{\"original\": true}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        _assert_artifact_path_is_new(path)
    assert path.read_text(encoding="utf-8") == "{\"original\": true}"



def test_r1_fixture_seeds_one_unsupported_stage_claim_with_separate_audit_flag():
    flagged = _r1_fixture("RO-01")
    assert flagged["disagreement_notes"] == [SEEDED_CASE_INTEGRITY_RAW_STATEMENT]
    assert flagged["case_data_integrity_flags"] == [SEEDED_CASE_INTEGRITY_FLAG]
    assert "cT1N0M0" not in flagged["provisional_conclusion"]
    assert not _r1_fixture("SO-02").get("case_data_integrity_flags")
    clean = _r1_fixture("RO-01", include_seeded_case_integrity_flag=False)
    assert not clean.get("case_data_integrity_flags")
    assert clean["disagreement_notes"] == []


def test_r3_peer_builder_attaches_r1_integrity_flags_to_matching_peer_without_mutation():
    roles = [
        {"agent_id": "RO-01", "name": "Radiation oncology"},
        {"agent_id": "SO-02", "name": "Surgical oncology"},
        {"agent_id": "MO-01", "name": "Medical oncology"},
    ]
    r2_by_id = {
        role["agent_id"]: {"agent_id": role["agent_id"], "position": "insufficient_information"}
        for role in roles
    }

    peer_views = _build_r3_peer_views(roles, "SO-02", r2_by_id)

    flagged_peer = next(item for item in peer_views if item["agent_id"] == "RO-01")
    assert flagged_peer["round1_case_integrity_flags"] == [SEEDED_CASE_INTEGRITY_FLAG]
    assert next(item for item in peer_views if item["agent_id"] == "MO-01")["round1_case_integrity_flags"] == []
    assert r2_by_id["RO-01"] == {"agent_id": "RO-01", "position": "insufficient_information"}
    assert "round1_case_integrity_flags" not in r2_by_id["RO-01"]


def test_unqualified_stage_output_guard_fails_closed_but_allows_explicit_quarantine():
    assert _unqualified_stage_assertions(
        {"conclusion": "The clinical stage is cT1N0M0."}
    )
    assert _unqualified_stage_assertions(
        {"conclusion": "N0 and M0 are confirmed."}
    )
    assert not _unqualified_stage_assertions(
        {"conclusion": "The cT1N0M0 assertion remains unverified and unsupported."}
    )
    assert not _unqualified_stage_assertions(
        {"conclusion": "The case does not establish T1N0M0; do not infer an alternative stage."}
    )



def test_unqualified_stage_output_guard_ignores_server_audit_metadata_but_scans_chair_prose():
    report = {
        "chair_conclusion": "No treatment recommendation can be made from the supplied case.",
        "case_data_integrity_flags": [
            "R1 RO-01: CASE_INTEGRITY_SEED_RO01: R1 states cT1N0M0, but the case supplies no T/N/M stage. "
            "This claim is unsupported/unverified; do not infer any alternative stage."
        ],
    }
    assert _unqualified_stage_assertions(report) == []

    report["chair_conclusion"] = "The clinical stage is cT1N0M0."
    assert _unqualified_stage_assertions(report)


def test_literal_stage_repeat_guard_flags_qualified_quotes_but_ignores_server_metadata():
    report = {
        "response_to_other_perspectives": (
            "R1 stated cT1N0M0, but that literal is explicitly described as unsupported."
        ),
        "case_data_integrity_flags": [
            "The source audit says cT1N0M0 is unsupported."
        ],
    }
    findings = _literal_seeded_stage_repetition_findings(report)
    assert len(findings) == 1
    assert findings[0]["path"] == "$.response_to_other_perspectives"
    assert findings[0]["token"] == "cT1N0M0"

    component_findings = _literal_seeded_stage_repetition_findings({
        "conclusion": "The copied stage assertions include N0 and M0."
    })
    assert [item["token"] for item in component_findings] == ["N0", "M0"]

    assert not _literal_seeded_stage_repetition_findings({
        "conclusion": "The flagged unsupported staging assertion remains unverified."
    })


def test_positive_control_rejects_whole_mdt_claim_repeated_outside_valid_challenge_quote():
    claim = "The entire 45-role MDT agrees with this conclusion"
    result = {
        "source_peer_ids": ["SO-02", "MO-01"],
        "response_to_other_perspectives": (
            "The entire 45-role MDT agrees with this conclusion; every specialist endorsed it."
        ),
        "substantive_challenges": [
            'R2:SO-02 states "The entire 45-role MDT agrees with this conclusion"; '
            "this is unsupported by the bounded sample."
        ],
    }
    findings = _positive_control_claim_repetition_findings(
        result, claim, source_agent_id="SO-02"
    )
    assert len(findings) == 1
    assert findings[0]["path"] == "$.response_to_other_perspectives"

    result["response_to_other_perspectives"] = (
        "The bounded sample cannot establish whole-MDT agreement."
    )
    assert _positive_control_claim_repetition_findings(
        result, claim, source_agent_id="SO-02"
    ) == []

    result["substantive_challenges"].append(
        "The entire 45-role MDT agrees with this conclusion."
    )
    findings = _positive_control_claim_repetition_findings(
        result, claim, source_agent_id="SO-02"
    )
    assert len(findings) == 1
    assert findings[0]["path"] == "$.substantive_challenges[1]"

