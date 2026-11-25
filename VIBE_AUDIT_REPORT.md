
## PHASE 4: Completed Fixes & Verification

- **Config & CORS (`backend/app/config.py`, `backend/app/main.py`):** Added validated `AppSettings` (`from_env()`), `CORS_ORIGINS` (rejecting `*`), `RADONC_AGENT_CONCURRENCY` (`1..2`), and `CIRCUIT_BREAKER_THRESHOLD` (`1..49`).
- **Input Bounds & Route Guards (`backend/app/schemas.py`, `backend/app/main.py`):** Enforced `AgentIdStr` (`^[A-Z]{2}-[0-9]{2}$`) and `1..60` bounds on `SelectedAgentsRequest` and `PatientRunRequest.selected_agent_ids`, capped `source_excerpt` at `100,000` chars and `IntakeEventRequest.event_type` at `64` chars, and added `422`/`404`/`409` lifecycle guards.
- **Orchestration & SQLite Hardening (`backend/app/services/batch_runner.py`, `mdt_rounds.py`, `run_store.py`, `intake_store.py`, `ollama.py`):** Added consecutive `OllamaUnavailable` circuit breaker + `<= 400`-char error truncation, SQLite WAL/busy-timeout + N+1 removal in `list_patients()` / `delete_patient()`, and fixed missing top-level `sys`/`subprocess`/`shutil`/`asyncio` imports in `ensure_ollama_service_and_model` (`ollama.py`).
- **Monolith Modularization:** Extracted `mdt_llm_client.py`, `mdt_chair_reconciler.py`, and `mdt_round_integrity.py` from `mdt_generation.py` (`3,018` -> `1,482` lines), and extracted `types.ts`, `caseFormHelpers.ts`, and `frontend/src/components/*` from `App.tsx` (`3,211` -> `2,381` lines) alongside `controlBusyKey`, `isMountedRef`, and request-sequence guards.
- **Verification (Latest Run):**
  - `python -m pytest backend/tests/ -q`: exited `0` (`[100%]`, `0` failures, `1` skipped), including `backend/tests/test_vibe_audit_hardening.py`.
  - `npm test --prefix frontend`: exited `0` (`36/36` passed, `0` failed).
  - `npm run build --prefix frontend`: exited `0` (`tsc --noEmit && vite build`, `43` modules transformed).

