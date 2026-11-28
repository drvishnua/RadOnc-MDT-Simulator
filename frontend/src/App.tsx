import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  API_BASE,
  CASE_DRAFT_KEY,
  caseSnapshotToForm,
  emptyForm,
  linesToList,
  optionalText,
} from "./caseFormHelpers.js";
import TopNavbar from "./components/vmdt/TopNavbar.js";
import UserProfileDrawer from "./components/vmdt/UserProfileDrawer.js";
import { useVmdtTheme } from "./hooks/useVmdtTheme.js";
import Page1Hall from "./pages/Page1Hall.js";
import Page2Intake from "./pages/Page2Intake.js";
import Page3Audit from "./pages/Page3Audit.js";
import Page4Simulation from "./pages/Page4Simulation.js";
import Page5Decision from "./pages/Page5Decision.js";
import Page6PastCases from "./pages/Page6PastCases.js";
import Page7Agents from "./pages/Page7Agents.js";
import Page8Settings from "./pages/Page8Settings.js";
import type {
  Agent,
  BatchAgentResult,
  BatchRunSummary,
  FinalMDTReport,
  IntakeScreening,
  PatientDetail,
  PreMDTStagingAssessment,
  RoundAgentResult,
  RoundSummary,
  Runtime,
  SyntheticCasePayload,
} from "./types.js";
import {
  buildDefaultAuditFindings,
  exportCaseAsPdf,
  mapBackendAgentsToVmdtConfigs,
  SEED_ARCHIVED_CASES,
  TEAM_DEFINITIONS,
} from "./utils/vmdtRoster.js";
import {
  DEFAULT_PROFILE,
  DEFAULT_SETTINGS,
  type AgentSeatStatus,
  type ArchivedCase,
  type AuditFinding,
  type TeamId,
  type UserProfile,
  type VmdtAgentConfig,
  type VmdtPageId,
  type VmdtSettings,
} from "./virtualMdtTypes.js";

const SETTINGS_KEY = "vmdt-settings-v1";
const PROFILE_KEY = "vmdt-profile-v1";
const ARCHIVE_KEY = "vmdt-archived-cases-v1";
const AGENT_OVERRIDES_KEY = "vmdt-agent-overrides-v2";

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown; message?: string };
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object") {
            const rec = item as { loc?: unknown[]; msg?: string };
            const loc = Array.isArray(rec.loc) ? rec.loc.filter((p) => p !== "body").join(".") : "";
            return loc && rec.msg ? `${loc}: ${rec.msg}` : rec.msg || JSON.stringify(item);
          }
          return String(item);
        })
        .join("; ");
    }
    if (detail && typeof detail === "object") {
      const rec = detail as { message?: string; msg?: string };
      return rec.message || rec.msg || JSON.stringify(detail);
    }
    return body.message || fallback;
  } catch {
    return fallback;
  }
}

export function App() {
  const { resolvedTheme, setThemeMode, toggleTheme } = useVmdtTheme();

  const [currentPage, setCurrentPage] = useState<VmdtPageId>("hall");
  const [profileOpen, setProfileOpen] = useState(false);

  const [settings, setSettings] = useState<VmdtSettings>(() =>
    loadJson<VmdtSettings>(SETTINGS_KEY, DEFAULT_SETTINGS),
  );
  const [userProfile, setUserProfile] = useState<UserProfile>(() =>
    loadJson<UserProfile>(PROFILE_KEY, DEFAULT_PROFILE),
  );
  const [archivedCases, setArchivedCases] = useState<ArchivedCase[]>(() =>
    loadJson<ArchivedCase[]>(ARCHIVE_KEY, SEED_ARCHIVED_CASES),
  );

  const [availableModels, setAvailableModels] = useState<string[]>(["qwen3.5:4b", "qwen2.5-coder:7b"]);
  const [agents, setAgents] = useState<VmdtAgentConfig[]>(() => {
    const base = mapBackendAgentsToVmdtConfigs(
      [],
      settings.availableFacilities,
      settings.unavailableFacilities,
      settings.defaultModel,
    );
    const saved = loadJson<Record<string, Partial<VmdtAgentConfig>>>(AGENT_OVERRIDES_KEY, {});
    return base.map((a) => (saved[a.id] ? { ...a, ...saved[a.id] } : a));
  });

  const [form, setForm] = useState<Record<string, string>>(() => ({
    ...emptyForm,
    ...loadJson<Record<string, string>>(CASE_DRAFT_KEY, {}),
  }));

  const [auditFindings, setAuditFindings] = useState<AuditFinding[]>([]);
  const [isScanningAudit, setIsScanningAudit] = useState(false);

  // Page 4 real simulation state
  const [simState, setSimState] = useState<"idle" | "running" | "paused" | "completed" | "stopped">("idle");
  const [simError, setSimError] = useState<string | null>(null);
  const [activeRound, setActiveRound] = useState<1 | 2 | 3 | 4>(1);
  const [completedRounds, setCompletedRounds] = useState<number[]>([]);
  const [preMdtStaging, setPreMdtStaging] = useState<PreMDTStagingAssessment | null>(null);
  const [roundSeatStatuses, setRoundSeatStatuses] = useState<Record<number, Record<string, AgentSeatStatus>>>({});
  const [roundSeatConclusions, setRoundSeatConclusions] = useState<Record<number, Record<string, string>>>({});
  const [roundSeatArguments, setRoundSeatArguments] = useState<Record<number, Record<string, string>>>({});
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [selectedSimAgentId, setSelectedSimAgentId] = useState<string | null>(null);
  const [isTranscriptReadOnly, setIsTranscriptReadOnly] = useState(false);
  const [activeDecisionCase, setActiveDecisionCase] = useState<ArchivedCase>(
    archivedCases[0] ?? SEED_ARCHIVED_CASES[0],
  );

  const pollTimerRef = useRef<number | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const archivedRunIdsRef = useRef<Set<string>>(new Set());
  const lastAutoRoundRef = useRef<number>(1);

  useEffect(() => {
    try {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      // ignore
    }
  }, [settings]);

  useEffect(() => {
    try {
      window.localStorage.setItem(PROFILE_KEY, JSON.stringify(userProfile));
    } catch {
      // ignore
    }
  }, [userProfile]);

  useEffect(() => {
    try {
      window.localStorage.setItem(ARCHIVE_KEY, JSON.stringify(archivedCases));
    } catch {
      // ignore
    }
  }, [archivedCases]);

  useEffect(() => {
    try {
      window.localStorage.setItem(CASE_DRAFT_KEY, JSON.stringify(form));
    } catch {
      // ignore
    }
  }, [form]);

  // Fetch live 49 agents, Ollama runtime & any active run on startup
  useEffect(() => {
    let active = true;
    void Promise.all([
      fetch(`${API_BASE}/api/agents`).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_BASE}/api/runtime`).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_BASE}/api/runs/active`).then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([agentsRes, runtimeRes, activeRunRes]) => {
        if (!active) return;
        const rawAgents = (agentsRes as { agents?: Agent[] } | null)?.agents ?? [];
        const runtime = runtimeRes as Runtime | null;
        if (runtime?.models?.length) {
          setAvailableModels(runtime.models);
        }
        if (rawAgents.length > 0) {
          const mapped = mapBackendAgentsToVmdtConfigs(
            rawAgents,
            settings.availableFacilities,
            settings.unavailableFacilities,
            settings.defaultModel,
          );
          const overrides = loadJson<Record<string, Partial<VmdtAgentConfig>>>(AGENT_OVERRIDES_KEY, {});
          setAgents(mapped.map((a) => (overrides[a.id] ? { ...a, ...overrides[a.id] } : a)));
        }
        const activePayload = activeRunRes as { active?: boolean; run?: BatchRunSummary | null } | null;
        const activeRun = activePayload?.run;
        if (activePayload?.active && activeRun?.run_id && !activeRunIdRef.current) {
          activeRunIdRef.current = activeRun.run_id;
          setSimState(activeRun.status === "paused" ? "paused" : "running");
          void pollBackendRun(activeRun.run_id);
          if (pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current);
          }
          pollTimerRef.current = window.setInterval(() => {
            void pollBackendRun(activeRun.run_id);
          }, 1500);
        }
      })
      .catch(() => {
        // Keep initial mapped roster when backend is offline
      });
    return () => {
      active = false;
    };
  }, []);

  const buildCasePayload = useCallback(
    (sourceForm: Record<string, string> = form): SyntheticCasePayload => {
      const ageRaw = Number(sourceForm.age_years);
      const rawTitle = (sourceForm.scenario_title || "").trim();
      const scenarioTitle =
        rawTitle.length >= 3
          ? rawTitle.slice(0, 160)
          : `${rawTitle ? `${rawTitle} — ` : ""}MDT Educational Oncology Consultation`.slice(0, 160);
      const rawSummary = (sourceForm.case_summary || "").trim();
      const fallbackSummary = `${sourceForm.primary_site || "Primary oncology"} case (${scenarioTitle}) submitted for multidisciplinary review.`;
      const caseSummary = rawSummary.length >= 10 ? rawSummary : rawSummary ? `${rawSummary} — ${fallbackSummary}` : fallbackSummary;
      return {
        scenario_title: scenarioTitle,
        case_summary: caseSummary,
        age_years: Number.isFinite(ageRaw) && ageRaw > 0 ? Math.min(120, Math.round(ageRaw)) : null,
        sex_at_birth: optionalText(sourceForm.sex_at_birth || ""),
        primary_site: optionalText(sourceForm.primary_site || ""),
        histology: optionalText(sourceForm.histology || ""),
        clinical_t_stage: optionalText(sourceForm.clinical_t_stage || ""),
        clinical_n_stage: optionalText(sourceForm.clinical_n_stage || ""),
        clinical_m_stage: optionalText(sourceForm.clinical_m_stage || ""),
        stage_group: optionalText(sourceForm.stage_group || ""),
        performance_status: optionalText(sourceForm.performance_status || ""),
        pathology_summary: optionalText(sourceForm.pathology_summary || ""),
        imaging_summary: optionalText(sourceForm.imaging_summary || ""),
        relevant_comorbidities: linesToList(sourceForm.relevant_comorbidities || ""),
        prior_treatment: linesToList(sourceForm.prior_treatment || ""),
        patient_goals: linesToList(sourceForm.patient_goals || ""),
        social_context: linesToList(sourceForm.social_context || ""),
        resource_context: [...settings.availableFacilities],
        known_unknowns: linesToList(sourceForm.known_unknowns || ""),
      };
    },
    [form, settings.availableFacilities],
  );

  // Page 2 -> Page 3 Audit logic (/api/cases/screen-intake + deterministic team checks)
  const runCaseAudit = useCallback(
    async (customForm?: Record<string, string>) => {
      setIsScanningAudit(true);
      const payload = buildCasePayload(customForm ?? form);
      const localFindings = buildDefaultAuditFindings(payload, agents);

      try {
        const res = await fetch(`${API_BASE}/api/cases/screen-intake`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ case: payload, declined_domains: [] }),
        });
        if (res.ok) {
          const screening = (await res.json()) as IntakeScreening;
          const merged = [...localFindings];
          for (const q of screening.questions || []) {
            if (!merged.some((m) => m.fieldKey === q.field_id)) {
              merged.push({
                id: `screen-${q.domain}-${q.field_id || q.question.slice(0, 12)}`,
                severity: q.priority === "high" ? "critical" : "recommended",
                specialty: q.domain.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                fieldKey: q.field_id || "case_summary",
                domain: q.domain,
                title: q.question,
                description: `Requested by pre-MDT intake screening (${q.domain}) before convening rounds.`,
                placeholder: `Provide ${q.field_id || q.domain} details...`,
              });
            }
          }
          setAuditFindings(merged);
        } else {
          setAuditFindings(localFindings);
        }
      } catch {
        setAuditFindings(localFindings);
      } finally {
        window.setTimeout(() => setIsScanningAudit(false), 900);
      }
    },
    [agents, buildCasePayload, form],
  );

  const handleResolveFinding = (
    id: string,
    fieldKey: string,
    value: string,
    markNA = false,
  ) => {
    setAuditFindings((prev) =>
      prev.map((f) =>
        f.id === id ? { ...f, resolvedValue: markNA ? undefined : value, markedNA: markNA } : f,
      ),
    );
    if (!markNA && value) {
      if (fieldKey === "clinical_t_stage" && /\bT[0-4]/i.test(value)) {
        const t = value.match(/\b(?:c|p)?(T[0-4][a-c]?)/i)?.[1];
        const n = value.match(/\b(N[0-3][a-c]?)/i)?.[1];
        const m = value.match(/\b(M[01xX])/i)?.[1];
        setForm((prev) => ({
          ...prev,
          ...(t ? { clinical_t_stage: t.toUpperCase() } : {}),
          ...(n ? { clinical_n_stage: n.toUpperCase() } : {}),
          ...(m ? { clinical_m_stage: m.toUpperCase() } : {}),
        }));
      } else {
        setForm((prev) => ({ ...prev, [fieldKey]: value }));
      }
    }
  };

  const finalizeAndArchiveCase = useCallback(
    (
      status: "Completed" | "Stopped Early",
      conclusionsMap: Record<string, string>,
      statusesMap: Record<string, AgentSeatStatus>,
      backendReport?: FinalMDTReport | null,
      runId?: string | null,
      staging?: PreMDTStagingAssessment | null,
    ) => {
      if (runId && archivedRunIdsRef.current.has(runId)) return;
      if (runId) archivedRunIdsRef.current.add(runId);

      const payload = buildCasePayload();
      const activeList = agents.filter((a) => a.active);
      const completedCount = Object.values(statusesMap).filter((s) => s === "completed").length;
      const consensusPct =
        status === "Completed"
          ? backendReport?.consensus_status?.toLowerCase().includes("broad") ||
            backendReport?.consensus_status?.toLowerCase().includes("strong")
            ? 92
            : 84
          : Math.max(40, Math.round((completedCount / Math.max(1, activeList.length)) * 80));

      const stageStr =
        staging?.provisional_stage_label ||
        [payload.clinical_t_stage, payload.clinical_n_stage, payload.clinical_m_stage]
          .filter(Boolean)
          .join(" ") ||
        payload.stage_group ||
        "Stage Pending";

      const caseCode = `MDT-${new Date().getFullYear()}-${String(
        Math.floor(1000 + Math.random() * 8999),
      )}`;
      const nowStr = new Date().toISOString().slice(0, 16).replace("T", " ");

      const newRecord: ArchivedCase = {
        id: runId ? `run-${runId}` : `case-${Date.now()}`,
        caseCode,
        patientName: (form.patient_name || "").trim() || "Synthetic Patient",
        ageSex: `${payload.age_years ?? "--"}${
          payload.sex_at_birth?.toUpperCase().startsWith("F")
            ? "F"
            : payload.sex_at_birth?.toUpperCase().startsWith("M")
              ? "M"
              : ""
        }`,
        primarySite: payload.primary_site || "Primary Site Unspecified",
        diagnosis: payload.histology || payload.scenario_title,
        stage: stageStr,
        status,
        consensusPercent: consensusPct,
        createdAt: nowStr,
        primaryRecommendation:
          backendReport?.chair_conclusion ||
          backendReport?.overall_educational_synthesis ||
          "Simulation stopped before Chair synthesis completed.",
        clinicalRationale:
          backendReport?.consensus_points?.length
            ? backendReport.consensus_points
            : backendReport?.recorded_agreements?.slice(0, 4) ?? [
                `STG-00 Stage: ${stageStr}`,
                `${completedCount} specialists recorded round outputs.`,
              ],
        followUpPlan:
          backendReport?.missing_information_before_real_world_review?.length
            ? backendReport.missing_information_before_real_world_review
            : backendReport?.major_uncertainties ?? [
                "Verify missing diagnostic biomarkers and imaging findings prior to clinical review.",
              ],
        dissentingViews: backendReport?.minority_and_dissenting_views ?? [],
        radiationPlan:
          conclusionsMap["RO-01"] ||
          conclusionsMap["RO-02"] ||
          "Review Radiation Oncology R1–R3 outputs in transcript.",
        systemicPlan:
          conclusionsMap["MO-01"] ||
          conclusionsMap["MO-02"] ||
          "Review Medical Oncology R1–R3 outputs in transcript.",
        surgicalPlan:
          conclusionsMap["SO-01"] ||
          "Review Surgical Oncology R1–R3 outputs in transcript.",
        evidenceSummary:
          backendReport?.consensus_status ||
          `${consensusPct}% agreement across ${completedCount} specialists (${status}).`,
        specialtyWeighting: [
          { team: "Radiation Oncology", weight: 34, color: "#38BDF8" },
          { team: "Medical Oncology", weight: 28, color: "#818CF8" },
          { team: "Surgical Oncology", weight: 22, color: "#34D399" },
          { team: "Diagnostics & Genetics", weight: 16, color: "#F472B6" },
        ],
        participatingAgents: activeList.map((a) => ({
          id: a.id,
          name: a.displayName,
          specialty: a.specialty,
          position: statusesMap[a.id] === "completed" ? "supports" : "conditional",
          conclusion: conclusionsMap[a.id] || a.personalitySummary,
          status: statusesMap[a.id] || "completed",
        })),
        caseSnapshot: payload as unknown as Record<string, unknown>,
        runId,
      };

      setArchivedCases((prev) => [newRecord, ...prev.filter((p) => p.id !== newRecord.id)]);
      setActiveDecisionCase(newRecord);
      return newRecord;
    },
    [agents, buildCasePayload, form.patient_name],
  );

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  // Real backend polling across R1 (/api/runs/{id}) -> R2/R3/R4 (/api/runs/{id}/rounds/{r}) -> /report
  const pollBackendRun = useCallback(
    async (runId: string) => {
      if (activeRunIdRef.current !== runId) return;
      try {
        const [r1Res, r1ResultsRes] = await Promise.all([
          fetch(`${API_BASE}/api/runs/${runId}`),
          fetch(`${API_BASE}/api/runs/${runId}/results`),
        ]);
        if (!r1Res.ok) return;

        const r1Summary = (await r1Res.json()) as BatchRunSummary;
        if (r1Summary.pre_mdt_staging) {
          setPreMdtStaging(r1Summary.pre_mdt_staging);
        }

        if (r1ResultsRes.ok) {
          const r1Body = (await r1ResultsRes.json()) as { results?: BatchAgentResult[] };
          const st1: Record<string, AgentSeatStatus> = {};
          const conc1: Record<string, string> = {};
          const arg1: Record<string, string> = {};
          for (const row of r1Body.results || []) {
            st1[row.agent_id] = row.status === "stopped" ? "paused" : row.status;
            if (row.assessment) {
              conc1[row.agent_id] = row.assessment.provisional_conclusion;
              arg1[row.agent_id] =
                `${row.assessment.provisional_conclusion}\n\nPreferred option: ${row.assessment.preferred_educational_option}\n\n${row.assessment.perspective_summary}`.trim();
            } else if (row.error_message) {
              arg1[row.agent_id] = `Error: ${row.error_message}`;
            }
          }
          setRoundSeatStatuses((prev) => ({ ...prev, 1: st1 }));
          setRoundSeatConclusions((prev) => ({ ...prev, 1: conc1 }));
          setRoundSeatArguments((prev) => ({ ...prev, 1: arg1 }));
        }

        const roundStatusMap = (
          r1Summary as BatchRunSummary & { round_status?: Record<string, string> }
        ).round_status;
        const hasRound2Plus = Boolean(
          roundStatusMap && Object.keys(roundStatusMap).some((k) => Number(k) >= 2),
        );
        const allR1Finished =
          r1Summary.total_agents > 0 &&
          r1Summary.completed_count + r1Summary.failed_count >= r1Summary.total_agents;
        const r1Done =
          r1Summary.status === "completed" ||
          r1Summary.status === "completed_with_errors" ||
          hasRound2Plus ||
          allR1Finished;
        const doneRounds: number[] = r1Done ? [1] : [];
        let liveRound: 1 | 2 | 3 | 4 = 1;
        let currentSpeaker: string | null = r1Summary.current_agent_id;
        let latestStatus = r1Summary.status;

        if (r1Done) {
          for (const roundNum of [2, 3, 4] as const) {
            const roundRes = await fetch(`${API_BASE}/api/runs/${runId}/rounds/${roundNum}`);
            if (!roundRes.ok) break;
            const roundSum = (await roundRes.json()) as RoundSummary;
            liveRound = roundNum;
            latestStatus = roundSum.status;
            if (roundSum.current_agent_id) {
              currentSpeaker = roundSum.current_agent_id;
            }

            const rrRes = await fetch(`${API_BASE}/api/runs/${runId}/rounds/${roundNum}/results`);
            if (rrRes.ok) {
              const rrBody = (await rrRes.json()) as { results?: RoundAgentResult[] };
              const stR: Record<string, AgentSeatStatus> = {};
              const concR: Record<string, string> = {};
              const argR: Record<string, string> = {};
              for (const row of rrBody.results || []) {
                stR[row.agent_id] = row.status === "stopped" ? "paused" : row.status;
                if (row.result) {
                  concR[row.agent_id] = row.result.provisional_conclusion;
                  argR[row.agent_id] =
                    `${row.result.provisional_conclusion}\n\n${row.result.response_to_other_perspectives}`.trim();
                } else if (row.error_message) {
                  argR[row.agent_id] = `Error: ${row.error_message}`;
                }
              }
              setRoundSeatStatuses((prev) => ({ ...prev, [roundNum]: stR }));
              setRoundSeatConclusions((prev) => ({ ...prev, [roundNum]: concR }));
              setRoundSeatArguments((prev) => ({ ...prev, [roundNum]: argR }));
            }

            if (roundSum.status === "completed" || roundSum.status === "completed_with_errors") {
              doneRounds.push(roundNum);
            } else {
              break;
            }
          }
        }

        setCompletedRounds(doneRounds);
        if (liveRound !== lastAutoRoundRef.current) {
          lastAutoRoundRef.current = liveRound;
          setActiveRound(liveRound);
        }
        setActiveSpeakerId(currentSpeaker);

        if (latestStatus === "paused") {
          setSimState("paused");
        } else if (latestStatus === "stopped") {
          stopPolling();
          setSimState("stopped");
        } else if (doneRounds.includes(4)) {
          stopPolling();
          setSimState("completed");
          setActiveSpeakerId(null);
          const repRes = await fetch(`${API_BASE}/api/runs/${runId}/report`);
          const rep = repRes.ok ? ((await repRes.json()) as FinalMDTReport) : null;
          finalizeAndArchiveCase(
            "Completed",
            roundSeatConclusions[1] ?? {},
            roundSeatStatuses[1] ?? {},
            rep,
            runId,
            r1Summary.pre_mdt_staging ?? preMdtStaging,
          );
        }
      } catch {
        // Transient network hiccup; keep polling
      }
    },
    [finalizeAndArchiveCase, preMdtStaging, roundSeatConclusions, roundSeatStatuses, stopPolling],
  );

  // Real pipeline: /api/intakes -> /accept -> /promote -> /api/patients/{id}/runs (full_simulation: true)
  const handleStartSimulation = async () => {
    setSimError(null);
    setIsTranscriptReadOnly(false);
    stopPolling();

    const activeList = agents.filter((a) => a.active);
    const initStatuses: Record<string, AgentSeatStatus> = {};
    activeList.forEach((a) => {
      initStatuses[a.id] = "queued";
    });
    setRoundSeatStatuses({ 1: initStatuses });
    setRoundSeatConclusions({});
    setRoundSeatArguments({});
    setCompletedRounds([]);
    lastAutoRoundRef.current = 1;
    setActiveRound(1);
    setPreMdtStaging(null);
    setSimState("running");

    try {
      const payload = buildCasePayload();
      // 1. Create intake session
      const intakeRes = await fetch(`${API_BASE}/api/intakes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case: payload }),
      });
      if (!intakeRes.ok) {
        throw new Error(await readApiError(intakeRes, "Failed to create pre-MDT intake session."));
      }
      const intakeData = (await intakeRes.json()) as { session_id: string };

      // 2. Accept intake (with any preserved gaps)
      const acceptRes = await fetch(`${API_BASE}/api/intakes/${intakeData.session_id}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed: true }),
      });
      if (!acceptRes.ok) {
        throw new Error(await readApiError(acceptRes, "Failed to accept pre-MDT intake."));
      }

      // 3. Promote to immutable patient case version
      const rawName = (form.patient_name || "").trim();
      const patientName =
        rawName.length >= 2 ? rawName : payload.scenario_title.slice(0, 80) || "Synthetic Patient";
      const promoteRes = await fetch(`${API_BASE}/api/intakes/${intakeData.session_id}/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_name: patientName }),
      });
      if (!promoteRes.ok) {
        throw new Error(await readApiError(promoteRes, "Failed to promote case to patient version."));
      }
      const patientDetail = (await promoteRes.json()) as PatientDetail;
      const versionId = patientDetail.versions?.[0]?.case_version_id;
      if (!patientDetail.patient_id || !versionId) {
        throw new Error("Promoted patient record did not return a case_version_id.");
      }

      // 4. Launch full 4-round simulation (STG-00 + R1 -> R2 -> R3 -> R4 Chair)
      const runRes = await fetch(`${API_BASE}/api/patients/${patientDetail.patient_id}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_version_id: versionId,
          full_simulation: true,
        }),
      });
      if (!runRes.ok) {
        throw new Error(await readApiError(runRes, "Failed to start 4-round MDT simulation."));
      }
      const runSummary = (await runRes.json()) as BatchRunSummary;
      activeRunIdRef.current = runSummary.run_id;
      if (runSummary.pre_mdt_staging) {
        setPreMdtStaging(runSummary.pre_mdt_staging);
      }

      void pollBackendRun(runSummary.run_id);
      pollTimerRef.current = window.setInterval(() => {
        void pollBackendRun(runSummary.run_id);
      }, 1500);
    } catch (err) {
      setSimState("idle");
      setSimError(
        err instanceof Error
          ? err.message
          : "Unable to reach the FastAPI/Ollama simulation backend.",
      );
    }
  };

  const handlePauseToggle = async () => {
    const runId = activeRunIdRef.current;
    if (!runId) return;
    if (simState === "running") {
      setSimState("paused");
      await fetch(`${API_BASE}/api/runs/${runId}/pause`, { method: "POST" }).catch(() => {});
    } else if (simState === "paused") {
      setSimState("running");
      await fetch(`${API_BASE}/api/runs/${runId}/unpause`, { method: "POST" }).catch(() => {});
    }
  };

  const handleStopSimulation = async () => {
    const runId = activeRunIdRef.current;
    stopPolling();
    if (runId) {
      await fetch(`${API_BASE}/api/runs/${runId}/stop`, { method: "POST" }).catch(() => {});
      const r1Conc = roundSeatConclusions[1] ?? {};
      const r1Stat = roundSeatStatuses[1] ?? {};
      if (Object.keys(r1Conc).length > 0) {
        finalizeAndArchiveCase("Stopped Early", r1Conc, r1Stat, null, runId, preMdtStaging);
      }
    }
    activeRunIdRef.current = null;
    setSimState("idle");
    setActiveRound(1);
    setCompletedRounds([]);
    setRoundSeatStatuses({});
    setRoundSeatConclusions({});
    setRoundSeatArguments({});
    setActiveSpeakerId(null);
    setSelectedSimAgentId(null);
  };

  const handleRestartSimulation = async () => {
    const runId = activeRunIdRef.current;
    stopPolling();
    if (runId) {
      await fetch(`${API_BASE}/api/runs/${runId}/restart`, { method: "POST" }).catch(() => {});
    }
    await handleStartSimulation();
  };

  const handleRetryAgent = async (agentId: string) => {
    const runId = activeRunIdRef.current;
    if (!runId) return;
    setRoundSeatStatuses((prev) => ({
      ...prev,
      [activeRound]: { ...(prev[activeRound] || {}), [agentId]: "queued" },
    }));
    await fetch(`${API_BASE}/api/runs/${runId}/rounds/${activeRound}/agents/${agentId}/run`, {
      method: "POST",
    }).catch(() => {});
  };

  const handlePauseAgent = async (agentId: string) => {
    const runId = activeRunIdRef.current;
    if (!runId) return;
    setRoundSeatStatuses((prev) => ({
      ...prev,
      [activeRound]: { ...(prev[activeRound] || {}), [agentId]: "paused" },
    }));
    await fetch(`${API_BASE}/api/runs/${runId}/rounds/${activeRound}/agents/${agentId}/stop`, {
      method: "POST",
    }).catch(() => {});
  };

  const handleUpdateAgent = (id: string, patch: Partial<VmdtAgentConfig>) => {
    setAgents((prev) => {
      const next = prev.map((a) => (a.id === id ? { ...a, ...patch } : a));
      const overrides: Record<string, Partial<VmdtAgentConfig>> = {};
      next.forEach((a) => {
        overrides[a.id] = {
          displayName: a.displayName,
          teamId: a.teamId,
          specialty: a.specialty,
          active: a.active,
          avatarVariant: a.avatarVariant,
          availableResources: a.availableResources,
          unavailableResources: a.unavailableResources,
          model: a.model,
          temperature: a.temperature,
          extraInstructions: a.extraInstructions,
        };
      });
      try {
        window.localStorage.setItem(AGENT_OVERRIDES_KEY, JSON.stringify(overrides));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const handleAddCustomAgent = (teamId: TeamId): string => {
    const newId = `CUSTOM-${Math.floor(100 + Math.random() * 899)}`;
    const newAgent: VmdtAgentConfig = {
      id: newId,
      backendAgentId: newId,
      displayName: `Dr. Custom Specialist (${newId})`,
      specialty: TEAM_DEFINITIONS[teamId].label,
      subspecialty: "Custom User-Added Consultant",
      teamId,
      innatePersonality: "Custom multidisciplinary advisory lens added by clinic lead.",
      personalitySummary: "Custom Specialty Advisor • Local Clinic Context",
      active: true,
      resourceConstrained: true,
      availableResources: [...settings.availableFacilities],
      unavailableResources: [...settings.unavailableFacilities],
      model: settings.defaultModel,
      temperature: 0.25,
      extraInstructions: "",
      avatarVariant: Math.floor(Math.random() * 8),
      scrubColor: TEAM_DEFINITIONS[teamId].accentDark,
      hasGlasses: false,
      propType: "tablet",
      isCustom: true,
    };
    setAgents((prev) => [...prev, newAgent]);
    return newId;
  };

  const handleResetAgentsToDefaults = () => {
    try {
      window.localStorage.removeItem(AGENT_OVERRIDES_KEY);
    } catch {
      // ignore
    }
    setAgents(
      mapBackendAgentsToVmdtConfigs(
        [],
        settings.availableFacilities,
        settings.unavailableFacilities,
        settings.defaultModel,
      ),
    );
  };

  const profileStats = useMemo(() => {
    const convened = archivedCases.length;
    const completedList = archivedCases.filter((c) => c.status === "Completed");
    const avgConsensus =
      completedList.length > 0
        ? Math.round(
            completedList.reduce((acc, c) => acc + c.consensusPercent, 0) / completedList.length,
          )
        : 0;
    return { convened, completed: completedList.length, avgConsensus };
  }, [archivedCases]);

  const handleExportAllCasesJson = () => {
    const blob = new Blob([JSON.stringify(archivedCases, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `virtual-mdt-archive-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const currentSeatStatuses = roundSeatStatuses[activeRound] ?? roundSeatStatuses[1] ?? {};
  const currentSeatConclusions =
    roundSeatConclusions[activeRound] ?? roundSeatConclusions[1] ?? {};
  const currentSeatArguments = roundSeatArguments[activeRound] ?? roundSeatArguments[1] ?? {};

  return (
    <div className="flex h-dvh w-screen flex-col overflow-hidden bg-gradient-to-br from-[#F8FAFC] to-[#E2E8F0] text-[#0F172A] transition-colors duration-300 dark:from-[#070B14] dark:to-[#0D1526] dark:text-[#F8FAFC]">
      <TopNavbar
        currentPage={currentPage}
        onNavigate={(page) => setCurrentPage(page)}
        resolvedTheme={resolvedTheme}
        onToggleTheme={toggleTheme}
        userProfile={userProfile}
        onOpenProfile={() => setProfileOpen(true)}
        profileOpen={profileOpen}
        hasActiveRun={simState === "running" || simState === "paused"}
        activeRunRound={activeRound}
        activeRunPaused={simState === "paused"}
        onReturnToActiveRun={() => setCurrentPage("simulation")}
      />

      <main className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
            className="flex min-h-0 flex-1 flex-col overflow-hidden"
          >
            {currentPage === "hall" && (
              <Page1Hall
                agents={agents}
                cameraPanMode={settings.cameraPanMode ?? "auto"}
                hasActiveRun={simState === "running" || simState === "paused"}
                activeRunRound={activeRound}
                activeRunPaused={simState === "paused"}
                onReturnToActiveRun={() => setCurrentPage("simulation")}
                onSubmitCase={() => setCurrentPage("intake")}
              />
            )}

            {currentPage === "intake" && (
              <Page2Intake
                form={form}
                voiceLanguage={settings.voiceLanguage}
                onChangeField={(k, v) => setForm((prev) => ({ ...prev, [k]: v }))}
                onLoadPreset={(presetForm) => setForm({ ...emptyForm, ...presetForm })}
                onResetForm={() => setForm({ ...emptyForm })}
                onBackToHall={() => setCurrentPage("hall")}
                onProceedToAudit={() => {
                  setCurrentPage("audit");
                  void runCaseAudit();
                }}
              />
            )}

            {currentPage === "audit" && (
              <Page3Audit
                findings={auditFindings}
                isScanning={isScanningAudit}
                onBackToIntake={() => setCurrentPage("intake")}
                onReAudit={() => void runCaseAudit()}
                onResolveFinding={handleResolveFinding}
                onConveneBoard={() => {
                  setIsTranscriptReadOnly(false);
                  setSimError(null);
                  setSimState("idle");
                  setCurrentPage("simulation");
                }}
              />
            )}

            {currentPage === "simulation" && (
              <Page4Simulation
                agents={agents}
                cameraPanMode={settings.cameraPanMode ?? "auto"}
                simState={simState}
                activeRound={activeRound}
                maxRounds={settings.rounds}
                completedRounds={completedRounds}
                preMdtStaging={preMdtStaging}
                simError={simError}
                seatStatuses={currentSeatStatuses}
                seatConclusions={currentSeatConclusions}
                seatArguments={currentSeatArguments}
                activeSpeakerId={activeSpeakerId}
                selectedAgentId={selectedSimAgentId}
                isReadOnly={isTranscriptReadOnly}
                onSelectAgent={setSelectedSimAgentId}
                onSelectRound={(r) => setActiveRound(r)}
                onStart={() => void handleStartSimulation()}
                onPauseToggle={() => void handlePauseToggle()}
                onRestart={() => void handleRestartSimulation()}
                onStop={() => void handleStopSimulation()}
                onRunFirst={(id) => void handleRetryAgent(id)}
                onRetryAgent={(id) => void handleRetryAgent(id)}
                onPauseAgent={(id) => void handlePauseAgent(id)}
                onBackToAudit={() =>
                  setCurrentPage(isTranscriptReadOnly ? "past-cases" : "audit")
                }
                onViewConsensus={() => setCurrentPage("decision")}
              />
            )}

            {currentPage === "decision" && (
              <Page5Decision
                caseRecord={activeDecisionCase}
                onBackToSimulation={() => setCurrentPage("simulation")}
                onExportPdf={() =>
                  exportCaseAsPdf(
                    activeDecisionCase,
                    settings.institutionName,
                    settings.pdfBranding,
                  )
                }
                onStartNewCase={() => {
                  setForm({ ...emptyForm });
                  setSimState("idle");
                  setCurrentPage("intake");
                }}
              />
            )}

            {currentPage === "past-cases" && (
              <Page6PastCases
                cases={archivedCases}
                onBackToHall={() => setCurrentPage("hall")}
                onOpenDecision={(c) => {
                  setActiveDecisionCase(c);
                  setCurrentPage("decision");
                }}
                onReviewTranscript={(c) => {
                  const stMap: Record<string, AgentSeatStatus> = {};
                  const concMap: Record<string, string> = {};
                  c.participatingAgents.forEach((p) => {
                    stMap[p.id] = p.status;
                    concMap[p.id] = p.conclusion;
                  });
                  setRoundSeatStatuses({ 1: stMap, 2: stMap, 3: stMap, 4: stMap });
                  setRoundSeatConclusions({ 1: concMap, 2: concMap, 3: concMap, 4: concMap });
                  setRoundSeatArguments({ 1: concMap, 2: concMap, 3: concMap, 4: concMap });
                  setCompletedRounds([1, 2, 3, 4]);
                  setActiveRound(4);
                  setSimState("completed");
                  setIsTranscriptReadOnly(true);
                  setActiveDecisionCase(c);
                  setCurrentPage("simulation");
                }}
                onCloneRerun={(c) => {
                  setForm(caseSnapshotToForm(c.caseSnapshot as unknown as SyntheticCasePayload));
                  setCurrentPage("intake");
                }}
                onExportPdf={(c) =>
                  exportCaseAsPdf(c, settings.institutionName, settings.pdfBranding)
                }
                onDeleteCase={(id) =>
                  setArchivedCases((prev) => prev.filter((item) => item.id !== id))
                }
              />
            )}

            {currentPage === "agents" && (
              <Page7Agents
                agents={agents}
                availableModels={availableModels}
                onUpdateAgent={handleUpdateAgent}
                onAddCustomAgent={handleAddCustomAgent}
                onResetDefaults={handleResetAgentsToDefaults}
                onBackToHall={() => setCurrentPage("hall")}
              />
            )}

            {currentPage === "settings" && (
              <Page8Settings
                settings={settings}
                availableModels={availableModels}
                onUpdateSettings={(patch) => {
                  setSettings((prev) => ({ ...prev, ...patch }));
                  if (patch.defaultTheme) {
                    setThemeMode(patch.defaultTheme);
                  }
                }}
                onExportAllCases={handleExportAllCasesJson}
                onClearAllCases={() => setArchivedCases([])}
                onResetAllSettings={() => {
                  setSettings(DEFAULT_SETTINGS);
                  setThemeMode(DEFAULT_SETTINGS.defaultTheme);
                }}
                onBackToHall={() => setCurrentPage("hall")}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      <UserProfileDrawer
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        profile={userProfile}
        onSaveProfile={(next) => setUserProfile(next)}
        stats={profileStats}
        resolvedTheme={resolvedTheme}
        onToggleTheme={toggleTheme}
        onOpenSettings={() => setCurrentPage("settings")}
        onSignOutReset={() => setUserProfile(DEFAULT_PROFILE)}
      />
    </div>
  );
}

export default App;
