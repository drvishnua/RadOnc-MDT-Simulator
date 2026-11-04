# Implementation Status

Last updated: 2026-11-05

## Implemented and verified

| Area | Current state | Verification |
|---|---|---|
| GitHub self-hosted runner | Windows laptop runner connected | GitHub Actions jobs executed on RadOnc-Laptop |
| Local GPU | NVIDIA RTX 4060 visible | nvidia-smi succeeded |
| Ollama | Local server reachable; qwen3.5:4b installed | Local API and inference smoke tests passed |
| GPU inference | Model reported 100% GPU allocation | ollama ps and GPU diagnostic logs |
| Product design | Product specification and safety boundaries documented | docs/PRODUCT_SPEC.md |
| Agent catalogue | 45 role profiles in Markdown and Python | API count/category test |
| Backend | FastAPI foundation | Health, runtime, agent catalogue, case validation routes |
| Agent output contract | Evidence citations, uncertainty, assumptions, unknowns, and education-only boundary | Pydantic schema tests |
| Frontend | React + Vite dashboard | TypeScript check and production build passed |
| Backend tests | 11 passing tests | Backend Tests workflow |
| Frontend build | Passing | Frontend Build workflow |

## Current API

- GET /health
- GET /api/runtime
- GET /api/agents
- POST /api/cases/validate

The case-validation endpoint checks request structure only. It does not validate clinical correctness or recommend treatment.

## Not implemented yet

- Agent prompt/version management beyond the role catalogue
- Four-round orchestration and resumable run state
- Model-generated agent assessments validated against AgentAssessment
- Evidence retrieval adapters and citation verification
- Persistence of cases and simulation runs
- MDT report, evidence report, patient-reality report, and feasibility/risk report
- React simulation progress and report screens
- Formal evaluation of oncology accuracy, bias, reproducibility, and safety

## Next development sequence

1. Implement the Ollama generation client using structured output and the AgentAssessment schema.
2. Add a single-agent dry-run endpoint for a synthetic case, with evidence and uncertainty validation.
3. Implement all 45 agent calls with resumable persistence and independent first-round assessments.
4. Add the debate, adversarial review, and chair-synthesis rounds.
5. Add evidence source adapters and provenance validation.
6. Connect the browser UI to a full simulation lifecycle.
7. Evaluate using synthetic test cases and clinician review before any broader use.

## Safety boundary

This remains a research/education prototype. Use synthetic cases only. It must not be used for real-patient clinical decisions or as a substitute for a qualified MDT.
