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
  FinalMDTReport,
  IntakeScreening,
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
const AGENT_OVERRIDES_KEY = "vmdt-agent-overrides-v1";

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
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

  // Page 4 simulation state
  const [simState, setSimState] = useState<"idle" | "running" | "paused" | "completed" | "stopped">("idle");
  const [activeRound, setActiveRound] = useState<1 | 2 | 3 | 4>(1);
  const [completedRounds, setCompletedRounds] = useState<number[]>([]);
  const [seatStatuses, setSeatStatuses] = useState<Record<string, AgentSeatStatus>>({});
  const [seatConclusions, setSeatConclusions] = useState<Record<string, string>>({});
  const [seatArguments, setSeatArguments] = useState<Record<string, string>>({});
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [selectedSimAgentId, setSelectedSimAgentId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [isTranscriptReadOnly, setIsTranscriptReadOnly] = useState(false);
  const [activeDecisionCase, setActiveDecisionCase] = useState<ArchivedCase>(
    archivedCases[0] ?? SEED_ARCHIVED_CASES[0],
  );

  const demoTimerRef = useRef<number | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const priorityQueueRef = useRef<string[]>([]);

  // Persist local stores automatically
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

  // Fetch live agents & Ollama runtime on startup
  useEffect(() => {
    let active = true;
    void Promise.all([
      fetch(`${API_BASE}/api/agents`).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_BASE}/api/runtime`).then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([agentsRes, runtimeRes]) => {
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
      })
      .catch(() => {
        // Offline / preview mode cleanly uses mapped fallback roster
      });
    return () => {
      active = false;
    };
  }, []);

  // Build backend-compatible SyntheticCasePayload from form state
  const buildCasePayload = useCallback(
    (sourceForm: Record<string, string> = form): SyntheticCasePayload => {
      const ageRaw = Number(sourceForm.age_years);
      return {
        scenario_title: (sourceForm.scenario_title || "MDT Educational Oncology Consultation").trim(),
        case_summary:
          (sourceForm.case_summary || "").trim() ||
          `${sourceForm.primary_site || "Primary oncology"} case submitted for multidisciplinary review.`,
        age_years: Number.isFinite(ageRaw) && ageRaw > 0 ? ageRaw : null,
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

  // Page 2 -> Page 3 Audit logic (backend screen-intake + deterministic team rules)
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
                description: `Requested by intake screening (${q.domain}) before convening MDT rounds.`,
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
        window.setTimeout(() => setIsScanningAudit(false), 1100);
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

  // Auto-save helper when simulation completes or stops
  const finalizeAndArchiveCase = useCallback(
    (
      status: "Completed" | "Stopped Early",
      conclusionsMap: Record<string, string>,
      statusesMap: Record<string, AgentSeatStatus>,
      backendReport?: FinalMDTReport | null,
      runId?: string | null,
    ) => {
      const payload = buildCasePayload();
      const activeList = agents.filter((a) => a.active);
      const completedCount = activeList.filter((a) => statusesMap[a.id] === "completed").length;
      const consensusPct =
        status === "Completed"
          ? Math.max(82, Math.min(97, Math.round(settings.consensusThreshold + 12)))
          : Math.max(45, Math.round((completedCount / Math.max(1, activeList.length)) * 85));

      const stageStr =
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
        id: `case-${Date.now()}`,
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
          `Multidisciplinary consensus for ${payload.scenario_title} (${stageStr}) recommends coordinated multimodal organ-preserving evaluation anchored by STG-00 locked staging and guideline-concordant QA.`,
        clinicalRationale:
          backendReport?.consensus_points?.length
            ? backendReport.consensus_points
            : [
                `Reviewed across ${activeList.length} active specialists across ${settings.rounds} structured MDT round(s).`,
                `Respects institution resource baseline (${settings.availableFacilities.slice(0, 4).join(", ") || "standard facilities"}).`,
              ],
        followUpPlan:
          backendReport?.missing_information_before_real_world_review?.length
            ? backendReport.missing_information_before_real_world_review
            : [
                "Verify pathology biomarkers and imaging node measurements prior to final clinical sign-off.",
                "Monitor acute mucosal/organ-at-risk toxicity thresholds and nutritional reserve weekly.",
              ],
        dissentingViews: backendReport?.minority_and_dissenting_views ?? [],
        radiationPlan:
          conclusionsMap["RO-01"] ||
          conclusionsMap["RO-02"] ||
          "Conformal definitive or adjuvant radiotherapy respecting serial OAR dose bounds.",
        systemicPlan:
          conclusionsMap["MO-01"] ||
          conclusionsMap["MO-02"] ||
          "Cisplatin-based concurrent or induction chemotherapy per organ clearance & biomarkers.",
        surgicalPlan:
          conclusionsMap["SO-01"] ||
          "Surgical resectability vs organ-preservation balance aligned with R0 margin criteria.",
        evidenceSummary: `${consensusPct}% agreement across ${completedCount}/${activeList.length} specialists (${status}).`,
        specialtyWeighting: [
          { team: "Radiation Oncology", weight: 34, color: "#38BDF8" },
          { team: "Medical Oncology", weight: 28, color: "#818CF8" },
          { team: "Surgical Oncology", weight: 22, color: "#34D399" },
          { team: "Diagnostics & Genetics", weight: 16, color: "#F472B6" },
        ],
        participatingAgents: activeList.slice(0, 12).map((a) => ({
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
    [agents, buildCasePayload, form.patient_name, settings],
  );

  // Stop background simulation loops on unmount
  const clearTimers = useCallback(() => {
    if (demoTimerRef.current !== null) {
      window.clearInterval(demoTimerRef.current);
      demoTimerRef.current = null;
    }
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => clearTimers(), [clearTimers]);

  // Fast responsive step engine (works seamlessly with live backend or standalone demo fallback)
  const startOrResumeStandaloneStepper = useCallback(
    (initialStatuses: Record<string, AgentSeatStatus>, startRound: 1 | 2 | 3 | 4) => {
      clearTimers();
      const activeList = agents.filter((a) => a.active);
      let currentStatuses = { ...initialStatuses };
      let currentConclusions: Record<string, string> = { ...seatConclusions };
      let currentRound = startRound;

      demoTimerRef.current = window.setInterval(() => {
        // Respect priority queue if user clicked "Run First"
        const priorityId = priorityQueueRef.current.shift();
        const queued = activeList.filter((a) => currentStatuses[a.id] === "queued");
        const nextAgent =
          (priorityId && activeList.find((a) => a.id === priorityId && currentStatuses[a.id] === "queued")) ||
          queued[0];

        if (!nextAgent) {
          // Mark round complete only when all active agents finished
          setCompletedRounds((prev) => (prev.includes(currentRound) ? prev : [...prev, currentRound]));
          if (currentRound < settings.rounds) {
            currentRound = (currentRound + 1) as 1 | 2 | 3 | 4;
            setActiveRound(currentRound);
            const resetForNext: Record<string, AgentSeatStatus> = {};
            activeList.forEach((a) => {
              resetForNext[a.id] = "queued";
            });
            currentStatuses = resetForNext;
            setSeatStatuses(resetForNext);
            return;
          }

          clearTimers();
          setActiveSpeakerId(null);
          setSimState("completed");
          finalizeAndArchiveCase("Completed", currentConclusions, currentStatuses, null, activeRunId);
          return;
        }

        // Complete any previously running speaker first, or step next speaker
        const runningPrev = activeList.find((a) => currentStatuses[a.id] === "running");
        if (runningPrev) {
          currentStatuses[runningPrev.id] = "completed";
        }

        currentStatuses[nextAgent.id] = "running";
        setActiveSpeakerId(nextAgent.id);
        const payload = buildCasePayload();
        const conc = `[Round ${currentRound}] ${nextAgent.specialty} (${nextAgent.subspecialty}): Recommends guideline-aligned plan for ${payload.primary_site || "tumor"} respecting STG-00 staging (${payload.clinical_t_stage || "cTx"} ${payload.clinical_n_stage || "cNx"} ${payload.clinical_m_stage || "cMx"}) and ${
          nextAgent.availableResources.length
            ? `available resources (${nextAgent.availableResources.slice(0, 2).join(", ")})`
            : "patient functional priorities"
        }.`;
        currentConclusions[nextAgent.id] = conc;

        setSeatStatuses({ ...currentStatuses });
        setSeatConclusions((prev) => ({ ...prev, [nextAgent.id]: conc }));
        setSeatArguments((prev) => ({
          ...prev,
          [nextAgent.id]: `${conc}\n\nReasoning basis: ${nextAgent.innatePersonality} Evaluated comorbidities (${payload.relevant_comorbidities.join(", ") || "none specified"}) and imaging summary (${payload.imaging_summary || "pending"}).`,
        }));
        window.setTimeout(() => {
          currentStatuses[nextAgent.id] = "completed";
          setSeatStatuses((prev) => ({ ...prev, [nextAgent.id]: "completed" }));
        }, 120);
      }, 170);
    },
    [
      activeRunId,
      agents,
      buildCasePayload,
      clearTimers,
      finalizeAndArchiveCase,
      seatConclusions,
      settings.rounds,
    ],
  );

  const handleStartSimulation = async () => {
    setIsTranscriptReadOnly(false);
    const activeList = agents.filter((a) => a.active);
    const initStatuses: Record<string, AgentSeatStatus> = {};
    activeList.forEach((a) => {
      initStatuses[a.id] = "queued";
    });
    setSeatStatuses(initStatuses);
    setSeatConclusions({});
    setSeatArguments({});
    setCompletedRounds([]);
    setActiveRound(1);
    setSimState("running");

    // Attempt backend batch run; fall back cleanly to local responsive simulation if offline
    try {
      const payload = buildCasePayload();
      const createRes = await fetch(`${API_BASE}/api/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (createRes.ok) {
        const runBody = (await createRes.json()) as { run_id: string };
        setActiveRunId(runBody.run_id);
        await fetch(`${API_BASE}/api/runs/${runBody.run_id}/run-full`, { method: "POST" });

        // Poll backend round 1..N while alive
        pollTimerRef.current = window.setInterval(async () => {
          try {
            const [roundRes, resultsRes] = await Promise.all([
              fetch(`${API_BASE}/api/runs/${runBody.run_id}/rounds/${activeRound}`),
              fetch(`${API_BASE}/api/runs/${runBody.run_id}/rounds/${activeRound}/results`),
            ]);
            if (!roundRes.ok || !resultsRes.ok) return;
            const summary = (await roundRes.json()) as RoundSummary;
            const resultsBody = (await resultsRes.json()) as { results?: RoundAgentResult[] };
            const statusPatch: Record<string, AgentSeatStatus> = {};
            const concPatch: Record<string, string> = {};
            const argPatch: Record<string, string> = {};
            for (const row of resultsBody.results || []) {
              statusPatch[row.agent_id] =
                row.status === "stopped" ? "paused" : row.status;
              if (row.result?.provisional_conclusion) {
                concPatch[row.agent_id] = row.result.provisional_conclusion;
                argPatch[row.agent_id] =
                  `${row.result.provisional_conclusion}\n\n${row.result.response_to_other_perspectives || ""}`.trim();
              }
            }
            setSeatStatuses((prev) => ({ ...prev, ...statusPatch }));
            setSeatConclusions((prev) => ({ ...prev, ...concPatch }));
            setSeatArguments((prev) => ({ ...prev, ...argPatch }));
            setActiveSpeakerId(summary.current_agent_id);
            if (summary.status === "completed") {
              setCompletedRounds((prev) => (prev.includes(activeRound) ? prev : [...prev, activeRound]));
              if (activeRound >= settings.rounds) {
                clearTimers();
                setSimState("completed");
                const repRes = await fetch(`${API_BASE}/api/runs/${runBody.run_id}/report`);
                const rep = repRes.ok ? ((await repRes.json()) as FinalMDTReport) : null;
                finalizeAndArchiveCase("Completed", concPatch, statusPatch, rep, runBody.run_id);
              }
            }
          } catch {
            // keep polling or let standalone continue
          }
        }, 1800);
        return;
      }
    } catch {
      // Backend unreachable -> run local interactive simulation engine cleanly
    }

    startOrResumeStandaloneStepper(initStatuses, 1);
  };

  const handlePauseToggle = () => {
    if (simState === "running") {
      clearTimers();
      setSimState("paused");
      if (activeRunId) {
        void fetch(`${API_BASE}/api/runs/${activeRunId}/pause`, { method: "POST" }).catch(() => {});
      }
    } else if (simState === "paused") {
      setSimState("running");
      if (activeRunId) {
        void fetch(`${API_BASE}/api/runs/${activeRunId}/unpause`, { method: "POST" }).catch(() => {});
      } else {
        startOrResumeStandaloneStepper(seatStatuses, activeRound);
      }
    }
  };

  const handleStopSimulation = () => {
    clearTimers();
    if (activeRunId) {
      void fetch(`${API_BASE}/api/runs/${activeRunId}/stop`, { method: "POST" }).catch(() => {});
    }
    if (Object.keys(seatConclusions).length > 0) {
      finalizeAndArchiveCase("Stopped Early", seatConclusions, seatStatuses, null, activeRunId);
    }
    setActiveRunId(null);
    setSimState("idle");
    setActiveRound(1);
    setCompletedRounds([]);
    setSeatStatuses({});
    setSeatConclusions({});
    setSeatArguments({});
    setActiveSpeakerId(null);
    setSelectedSimAgentId(null);
  };

  const handleRestartSimulation = () => {
    clearTimers();
    if (activeRunId) {
      void fetch(`${API_BASE}/api/runs/${activeRunId}/restart`, { method: "POST" }).catch(() => {});
    }
    void handleStartSimulation();
  };

  const handleRunFirst = (agentId: string) => {
    priorityQueueRef.current = [agentId, ...priorityQueueRef.current.filter((id) => id !== agentId)];
  };

  const handleRetryAgent = (agentId: string) => {
    setSeatStatuses((prev) => ({ ...prev, [agentId]: "queued" }));
    priorityQueueRef.current = [agentId, ...priorityQueueRef.current];
    if (activeRunId) {
      void fetch(`${API_BASE}/api/runs/${activeRunId}/rounds/${activeRound}/agents/${agentId}/run`, {
        method: "POST",
      }).catch(() => {});
    } else if (simState === "completed" || simState === "paused") {
      setSimState("running");
      startOrResumeStandaloneStepper({ ...seatStatuses, [agentId]: "queued" }, activeRound);
    }
  };

  const handlePauseAgent = (agentId: string) => {
    setSeatStatuses((prev) => ({ ...prev, [agentId]: "paused" }));
    if (activeRunId) {
      void fetch(`${API_BASE}/api/runs/${activeRunId}/rounds/${activeRound}/agents/${agentId}/stop`, {
        method: "POST",
      }).catch(() => {});
    }
  };

  // Page 7 Agent management handlers
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

  // Profile Drawer KPI stats
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

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-gradient-to-br from-[#F8FAFC] to-[#E2E8F0] text-[#0F172A] transition-colors duration-300 dark:from-[#070B14] dark:to-[#0D1526] dark:text-[#F8FAFC]">
      <TopNavbar
        currentPage={currentPage}
        onNavigate={(page) => setCurrentPage(page)}
        resolvedTheme={resolvedTheme}
        onToggleTheme={toggleTheme}
        userProfile={userProfile}
        onOpenProfile={() => setProfileOpen(true)}
        profileOpen={profileOpen}
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
              <Page1Hall agents={agents} onSubmitCase={() => setCurrentPage("intake")} />
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
                  setSimState("idle");
                  setCurrentPage("simulation");
                }}
              />
            )}

            {currentPage === "simulation" && (
              <Page4Simulation
                agents={agents}
                simState={simState}
                activeRound={activeRound}
                maxRounds={settings.rounds}
                completedRounds={completedRounds}
                seatStatuses={seatStatuses}
                seatConclusions={seatConclusions}
                seatArguments={seatArguments}
                activeSpeakerId={activeSpeakerId}
                selectedAgentId={selectedSimAgentId}
                isReadOnly={isTranscriptReadOnly}
                onSelectAgent={setSelectedSimAgentId}
                onSelectRound={(r) => setActiveRound(r)}
                onStart={() => void handleStartSimulation()}
                onPauseToggle={handlePauseToggle}
                onRestart={handleRestartSimulation}
                onStop={handleStopSimulation}
                onRunFirst={handleRunFirst}
                onRetryAgent={handleRetryAgent}
                onPauseAgent={handlePauseAgent}
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
                  setSeatStatuses(stMap);
                  setSeatConclusions(concMap);
                  setSeatArguments(concMap);
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
