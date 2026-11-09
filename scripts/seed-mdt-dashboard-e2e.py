"""Seed a disposable four-round record for a real-dashboard browser smoke test.

No Ollama calls are made. Every persisted contribution is deterministic test data.
The browser test must delete the temporary patient after verifying the rendered UI.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.agent_schemas import AgentAssessment
from app.agents.catalog import AGENT_PROFILES
from app.round_schemas import FinalMDTReport, RoundContribution
from app.schemas import SyntheticCase
from app.services import run_store


def main() -> int:
    patient_id: str | None = None
    try:
        case = SyntheticCase(
            scenario_title="Dashboard four-round browser smoke test",
            case_summary=(
                "Fictional training scenario used only to verify restoration and display "
                "of previously saved MDT round records in the local browser."
            ),
            known_unknowns=[
                "Clinical stage is not supplied.",
                "Patient goals are not supplied.",
            ],
        )
        patient = run_store.create_patient(
            "Disposable dashboard E2E " + uuid.uuid4().hex[:10],
            case,
        )
        patient_id = patient["patient_id"]
        version_id = patient["versions"][0]["case_version_id"]
        run = run_store.create_run_for_case_version(patient_id, version_id)
        run_id = run["run_id"]

        # R1: seed all distinct configured roles as completed independent assessments.
        for profile in AGENT_PROFILES:
            assessment = AgentAssessment(
                agent_id=profile["agent_id"],
                round_number=1,
                position="insufficient_information",
                provisional_conclusion=(
                    "The available fictional case information is insufficient for a "
                    "definitive educational conclusion."
                ),
                preferred_educational_option=(
                    "No educational option can be selected from the supplied information."
                ),
                perspective_summary=(
                    "Deterministic dashboard test contribution from " + profile["name"] + "."
                ),
                unknowns=["Clinical stage and patient goals are not supplied."],
                evidence_gaps=["Evidence retrieval is not connected in this test."],
                confidence=0.2,
            )
            run_store.save_agent_success(
                run_id, profile["agent_id"], assessment.model_dump_json(), 0.001
            )
        run_store.mark_run_finished(run_id)

        # R2 and R3: persist all 45 typed role contributions in each round.
        for round_number in (2, 3):
            run_store.create_round_job(run_id, round_number)
            run_store.mark_round_running(run_id, round_number)
            for profile in AGENT_PROFILES:
                contribution = RoundContribution(
                    agent_id=profile["agent_id"],
                    round_number=round_number,
                    position="insufficient_information",
                    provisional_conclusion=(
                        "The position remains insufficient-information because required "
                        "fictional case details have not been supplied."
                    ),
                    response_to_other_perspectives=(
                        "This stored test record preserves the peer-review stage without "
                        "claiming agreement on a clinical option."
                    ),
                    agreements=[
                        "Missing case information remains an unresolved educational limitation."
                    ],
                    substantive_challenges=[
                        "Do not infer stage, fitness, resectability, or patient preference."
                    ],
                    remaining_unknowns=[
                        "Clinical stage and patient goals remain unknown."
                    ],
                    risk_flags=[
                        "This is a browser test fixture, not a treatment instruction."
                    ],
                    confidence=0.2,
                )
                run_store.save_round_success(
                    run_id, round_number, profile["agent_id"],
                    contribution.model_dump_json(), 0.001,
                )
            run_store.mark_round_finished(run_id, round_number)

        # R4: a conservative Chair report with no proposition-level consensus.
        run_store.create_round_job(run_id, 4)
        run_store.mark_round_running(run_id, 4)
        chair = FinalMDTReport(
            run_id=run_id,
            report_title="MDT Chair Synthesis: Dashboard rendering check",
            consensus_status="insufficient_information",
            chair_conclusion=(
                "No treatment recommendation can be made from the supplied case details. "
                "Important clinical and patient-context information remains unknown."
            ),
            overall_educational_synthesis=(
                "This deterministic browser fixture verifies saved report rendering only. "
                "It does not represent model-generated specialist reasoning."
            ),
            consensus_points=[],
            recorded_agreements=[
                "Round 2 — RO-01: Recorded test agreement; not independently validated as a shared proposition."
            ],
            unresolved_disagreements=[
                "No proposition-level consensus is established in this test fixture."
            ],
            minority_and_dissenting_views=[
                "All role contributions remain individually available for inspection."
            ],
            major_uncertainties=[
                "Clinical stage and patient goals are not supplied."
            ],
            missing_information_before_real_world_review=[
                "Required clinical staging and patient-context information remain unknown."
            ],
            patient_and_family_considerations=[
                "Patient goals must be obtained rather than inferred."
            ],
            feasibility_and_resource_considerations=[
                "Local resources are not assessed by this browser fixture."
            ],
            governance_and_safeguarding_considerations=[
                "Educational simulation only; not clinical decision support."
            ],
            evidence_limitations=[
                "Evidence retrieval is not connected."
            ],
            chair_reflection=(
                "This is a deterministic stored test report. It verifies report display "
                "and persistence, not evidence quality or clinical accuracy."
            ),
        )
        run_store.save_round_success(
            run_id, 4, "SG-07", chair.model_dump_json(), 0.001
        )
        run_store.mark_round_finished(run_id, 4)

        print(json.dumps({
            "run_id": run_id,
            "patient_id": patient_id,
            "patient_identifier": patient["patient_identifier"],
            "case_snapshot_sha256": run_store.get_run(run_id)["case_snapshot_sha256"],
        }))
        return 0
    except Exception:
        if patient_id:
            try:
                run_store.delete_patient(patient_id)
            except Exception:
                pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
