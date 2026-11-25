# RadOnc MDT Simulator — Immediate Quality Milestone (P0, P1, P2) Verification Report

**Date**: 24 November 2026  
**Repository**: `drvishnua/RadOnc-MDT-Simulator`  
**Development Branch**: `feature/four-round-mdt-and-performance`  
**PR Status**: PR #1 (Draft, Base: `main`)  
**Hardware & Environment**: Windows 11, NVIDIA RTX 4060 Laptop GPU (8 GB VRAM), Ollama 0.40.14, `qwen3.5:4b`, Concurrency 1.  

---

## Executive Summary

In adherence to `AGENTS.md` and the supervisor-worker architecture ("Cloud Boss, Local Builders"), the immediate quality milestone objectives (P0, P1, and P2) have been implemented, tested, and verified against a live multi-round simulation running on the local GPU.

All 839 backend unit and integration tests are passing with 0 failures:
- `839 passed, 1 skipped` in 55.4 seconds.

---

## Milestone Breakdown & Implementation Details

### 1. P0: Case-Fact Provenance & Grounded Staging Engine
- **Objective**: Prevent unsupported TNM staging or demographic claims. Enforce that missing or not-reported fields are never promoted to confirmed absences.
- **Implementation**:
  - `backend/app/services/staging_engine.py`: Multi-site TNM derivation engine grounded in AJCC 8th Edition guidelines for Head & Neck, Lung, GI, Breast, Prostate, and CNS malignancies.
  - Strict classification: requires explicit anatomical criteria (tumor dimensions, subsite extension, nodal size, laterality, extranodal extension) before deriving T/N/M stage; flags `insufficient_information` whenever critical measurements are omitted.
  - Case integrity guards ensure raw case text provenance is strictly preserved without hallucinated stages.

### 2. P1: Structured Debate Position Traceability & Chair Minority Selection
- **Objective**: Preserve exact model-authored rationale when roles shift stances; segregate genuine dissent from stable uncertainty; ensure fact-grounded title generation.
- **Implementation**:
  - `backend/app/services/mdt_generation.py`: Preserves stance changes with formatted transition strings:  
    `Round X → Round Y: <old_position> → <new_position>. Rationale: <reason>`.
  - `backend/app/services/chair_report_quality.py`: `_minority_history` accurately isolates genuine distinct views and challenges. Stable `insufficient_information` roles are channeled to `major_uncertainties` and `missing_information_before_real_world_review`, preventing dilution of minority opinions.
  - `backend/app/services/case_integrity.py`: `build_case_report_title(case)` produces strictly verified fact titles:  
    `MDT Chair Synthesis: <primary_site> — <histology>`. Unsupported stage tokens (e.g. `T3N2`) are prevented.
  - `backend/app/services/run_store.py`: `get_run(run_id)` exposes `completed_at` (mapped to `mdt_finished_at`), `round_status` dictionary `{round_number: status}`, and calculated `wall_clock_runtime_seconds`.

### 3. P2: Evidence Retrieval, Inline Citation Audit & Rich Telemetry
- **Objective**: Eliminate unverified references; attach rich telemetry to post-round quality gates.
- **Implementation**:
  - `backend/app/services/mdt_rounds.py`: Post-round quality gates extract inline citations (`[source_id: ...]`, `[source: ...]`, `[ref: ...]`) from all narrative assessment fields and audit them against canonical evidence indices.
  - Full audit metrics stored in `quality_audits`:
    - `inline_citations_audited`
    - `verified_inline_citations`
    - `unverified_inline_citations`
    - `inline_citation_concordance_rate`
  - Telemetry summaries captured: `total_prompt_tokens`, `total_output_tokens`, `avg_tokens_per_second`, `total_retries`, `total_schema_failures`, and `wall_clock_seconds`.

### 4. Persona Deepening (All 49 MDT Specialists)
- Deepened all 49 distinct specialist personas in `backend/app/agents/catalog.py`:
  - **Radiation Oncology (RO-01..RO-10)**: Guideline IMRT, conservative OAR preservation (QUANTEC), dose escalation/SIB, re-irradiation, palliative SRS/SBRT, brachytherapy, pediatrics, particle therapy, biology/hypoxia, adaptive replanning.
  - **Medical Oncology (MO-01..MO-09)**: High-dose cisplatin purist, weekly cisplatin, carboplatin/frailty, biomarker (p16/PD-L1), irAE management, TPF induction, ADCs, ESMO-MCBS value, and trial skepticism.
  - **Surgical Oncology (SO-01..SO-09)**: Guideline resection, TORS, radical flap, TLM endoscopy, EUA mapping, NOM watch-and-wait, ICG fluorescence, NSQIP prehab, and salvage morbidity audit.
  - **Diagnostic Specialties (DS-01..DS-03)**: ACR Appropriateness radiologist, CAP histology/p16 clone E6H4 pathologist, and NGS molecular pathologist.
  - **Patient Perspective Lenses (PP-01..PP-06)**: MDADI swallowing/speech, functional independence, financial toxicity (COST), caregiver burden (ZBI), procedure hesitancy, health literacy (Ask Me 3).
  - **Governance & Vulnerability (SG-01..SG-09, SV-01..SV-03)**: Health economics, physics QA (TG-142), treatment package time, prior-auth, GRADE evidence auditor, risk management, MDT Chair consensus facilitator, clinical ethics, independent ombudsman, and SDOH navigators.

---

## Live Multi-Round GPU Verification Results

A full 4-round pipeline test was executed live against local Ollama (`qwen3.5:4b`) on an oropharyngeal SCC synthetic case:

| Round | Stage | Roles Evaluated | Wall-Clock Time | Citation Concordance | Key Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Round 1** | Independent Assessment | 8 roles | 124.7s (~15.5s/role) | **100.0%** (8/8 verified, 0 unverified) | Structured positions with explicit unknowns |
| **Round 2** | Cross-Disciplinary Debate | RO-01, RO-02, SO-01, SO-02 | 56.97s (~14.2s/role) | 100.0% | Stance maintained with rationale |
| **Round 3** | Adversarial Review | RO-01, RO-02, SO-01 | 36.83s (~12.3s/role) | 100.0% | Structured challenge audit |
| **Round 4** | Chair Synthesis | SG-07 (MDT Chair) | 13.55s | 100.0% | Consensus: `insufficient_information` |

### Verified Output Excerpt
- **Report Title**: `MDT Chair Synthesis: oropharynx — Squamous cell carcinoma`
- **Consensus Status**: `insufficient_information` (no manufactured consensus)
- **Chair Conclusion**:  
  > *"No treatment recommendation can be made from the supplied case. No proposition-level consensus or proposition-specific disagreement can be established because the saved structured contributions do not identify a shared proposition. Recorded role positions are preserved separately for review."*
- **Minority & Dissenting Views**: 1 entry (isolated genuine distinct views, did not dump stable uncertainty into dissent).
- **Major Uncertainties**: 20 entries (systematic cataloging of missing dental clearance, swallow evaluation, and tumor measurements).

---

## Integration Test Verification

Added test suites:
1. `backend/tests/test_p1_milestone_integrity.py`: Unit tests for position change tracking, Chair minority filtering, title generation, and database contracts.
2. `backend/tests/test_api_milestone_telemetry.py`: End-to-end FastAPI endpoint tests for `/api/runs/{run_id}`, `/api/runs/{run_id}/rounds/{round_number}/quality-audit`, and `/api/runs/{run_id}/report`.

Test suite command:
```bash
pytest backend/tests/test_p1_milestone_integrity.py backend/tests/test_api_milestone_telemetry.py -v
```
Result: **6 passed in 1.14s**.

---

## Conclusion & Next Steps
- Quality Milestones P0, P1, and P2 are complete, robustly tested, and verified on local GPU.
- PR #1 remains draft; `main` branch remains untouched.
