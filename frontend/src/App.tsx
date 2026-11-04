import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type Health = {
  status: string;
  application: string;
  version: string;
  mode: string;
};

type Runtime = {
  reachable: boolean;
  version?: string | null;
  configured_model: string;
  configured_model_installed: boolean;
  models: string[];
  error?: string;
};

type Agent = {
  agent_id: string;
  category: string;
  category_label: string;
  name: string;
  mandate: string;
};

type ValidationResult = {
  valid: boolean;
  mode: string;
  warnings: string[];
  note: string;
};

type SyntheticCasePayload = {
  scenario_title: string;
  case_summary: string;
  age_years: number | null;
  primary_site: string | null;
  histology: string | null;
};

type AgentAssessmentResult = {
  agent_id: string;
  round_number: number;
  position: "supports" | "opposes" | "conditional" | "insufficient_information";
  provisional_conclusion: string;
  preferred_educational_option: string;
  perspective_summary: string;
  discussion_options: string[];
  unknowns: string[];
  evidence_gaps: string[];
  uncertainty_notes: string[];
  confidence: number;
  evidence_claims: unknown[];
  safety_boundary: string;
  not_a_treatment_instruction: boolean;
};

type BatchRunSummary = {
  run_id: string;
  status: "queued" | "running" | "completed" | "completed_with_errors";
  total_agents: number;
  completed_count: number;
  failed_count: number;
  queued_count: number;
  running_count: number;
  finished_count: number;
  progress_percent: number;
  current_agent_id: string | null;
  created_at: string;
  updated_at: string;
};

type BatchAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed";
  assessment: AgentAssessmentResult | null;
  error_message: string | null;
  duration_seconds: number | null;
};

type RoundSummary = {
  run_id: string;
  round_number: number;
  status: "queued" | "running" | "completed" | "completed_with_errors";
  total_agents: number;
  completed_count: number;
  failed_count: number;
  queued_count: number;
  running_count: number;
  finished_count: number;
  progress_percent: number;
  current_agent_id: string | null;
  updated_at: string;
};

type RoundAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed";
  result: {
    position: string;
    provisional_conclusion: string;
    response_to_other_perspectives: string;
    agreements: string[];
    substantive_challenges: string[];
    position_changes: string[];
    remaining_unknowns: string[];
    risk_flags: string[];
    confidence: number;
  } | null;
  error_message: string | null;
  duration_seconds: number | null;
};

type FinalMDTReport = {
  run_id: string;
  round_number: 4;
  report_title: string;
  overall_position: string;
  chair_conclusion: string;
  overall_educational_synthesis: string;
  consensus_points: string[];
  unresolved_disagreements: string[];
  minority_and_dissenting_views: string[];
  major_uncertainties: string[];
  missing_information_before_real_world_review: string[];
  patient_and_family_considerations: string[];
  feasibility_and_resource_considerations: string[];
  governance_and_safeguarding_considerations: string[];
  evidence_limitations: string[];
  chair_reflection: string;
  evidence_retrieval_connected: false;
  not_a_treatment_instruction: true;
};

const emptyForm = {
  scenario_title: "Synthetic head-and-neck case",
  case_summary: "",
  age_years: "",
  primary_site: "",
  histology: ""
};

function readSavedCase(): SyntheticCasePayload | null {
  try {
    const saved = window.localStorage.getItem("radonc-mdt-last-case");
    return saved ? (JSON.parse(saved) as SyntheticCasePayload) : null;
  } catch {
    return null;
  }
}

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [runtime, setRuntime] = useState<Runtime | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [connectionState, setConnectionState] = useState<"loading" | "connected" | "unavailable">("loading");
  const [form, setForm] = useState(() => {
    const saved = readSavedCase();
    return saved ? {
      scenario_title: saved.scenario_title,
      case_summary: saved.case_summary,
      age_years: saved.age_years === null ? "" : String(saved.age_years),
      primary_site: saved.primary_site ?? "",
      histology: saved.histology ?? ""
    } : emptyForm;
  });
  const [validation, setValidation] = useState<ValidationResult | null>(() => (
    readSavedCase()
      ? {
          valid: true,
          mode: "synthetic_educational_case",
          warnings: [],
          note: "This synthetic case was previously validated in this browser."
        }
      : null
  ));
  const [validatedCase, setValidatedCase] = useState<SyntheticCasePayload | null>(() => readSavedCase());
  const [validationError, setValidationError] = useState("");
  const [validating, setValidating] = useState(false);
  const [agentAssessment, setAgentAssessment] = useState<AgentAssessmentResult | null>(null);
  const [assessmentError, setAssessmentError] = useState("");
  const [assessing, setAssessing] = useState(false);
  const [batchRun, setBatchRun] = useState<BatchRunSummary | null>(() => {
    try {
      const saved = window.localStorage.getItem("radonc-mdt-active-batch");
      return saved ? (JSON.parse(saved) as BatchRunSummary) : null;
    } catch {
      return null;
    }
  });
  const [batchResults, setBatchResults] = useState<BatchAgentResult[]>([]);
  const [batchError, setBatchError] = useState("");
  const [batchStarting, setBatchStarting] = useState(false);
  const [batchResuming, setBatchResuming] = useState(false);
  const [roundSummaries, setRoundSummaries] = useState<Record<number, RoundSummary | null>>({});
  const [roundResults, setRoundResults] = useState<Record<number, RoundAgentResult[]>>({});
  const [finalReport, setFinalReport] = useState<FinalMDTReport | null>(null);
  const [roundActionBusy, setRoundActionBusy] = useState<number | null>(null);
  const [roundError, setRoundError] = useState("");
  const [agentFilter, setAgentFilter] = useState("All perspectives");

  async function refreshStatus() {
    setConnectionState("loading");
    try {
      const [healthResponse, runtimeResponse, agentsResponse] = await Promise.all([
        fetch(API_BASE + "/health"),
        fetch(API_BASE + "/api/runtime"),
        fetch(API_BASE + "/api/agents")
      ]);
      if (!healthResponse.ok || !runtimeResponse.ok || !agentsResponse.ok) {
        throw new Error("The local API returned an unsuccessful status.");
      }
      const healthData = (await healthResponse.json()) as Health;
      const runtimeData = (await runtimeResponse.json()) as { ollama: Runtime };
      const agentData = (await agentsResponse.json()) as { agents: Agent[] };
      setHealth(healthData);
      setRuntime(runtimeData.ollama);
      setAgents(agentData.agents);
      setConnectionState("connected");
    } catch {
      setHealth(null);
      setRuntime(null);
      setAgents([]);
      setConnectionState("unavailable");
    }
  }

  useEffect(() => {
    void refreshStatus();
  }, []);

  const categories = useMemo(
    () => ["All perspectives", ...Array.from(new Set(agents.map((agent) => agent.category_label)))],
    [agents]
  );

  const filteredAgents = useMemo(
    () => agentFilter === "All perspectives"
      ? agents
      : agents.filter((agent) => agent.category_label === agentFilter),
    [agentFilter, agents]
  );

  async function validateSyntheticCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidation(null);
    setValidationError("");
    setValidating(true);

    const payload: SyntheticCasePayload = {
      scenario_title: form.scenario_title,
      case_summary: form.case_summary,
      age_years: form.age_years.trim() === "" ? null : Number(form.age_years),
      primary_site: form.primary_site || null,
      histology: form.histology || null
    };

    try {
      const response = await fetch(API_BASE + "/api/cases/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) {
        const details = Array.isArray(body.detail)
          ? body.detail.map((item: { msg?: string }) => item.msg ?? "Invalid input").join("; ")
          : "The case could not be validated.";
        throw new Error(details);
      }
      setValidation(body as ValidationResult);
      setValidatedCase(payload);
      setAgentAssessment(null);
      setAssessmentError("");
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : "Unable to reach the local API.");
    } finally {
      setValidating(false);
    }
  }

  async function runAgentAssessment() {
    if (!validatedCase) return;
    setAssessing(true);
    setAssessmentError("");
    setAgentAssessment(null);
    try {
      const response = await fetch(API_BASE + "/api/agents/RO-01/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case: validatedCase, round_number: 1 })
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "The local model could not produce a valid assessment.");
      }
      setAgentAssessment(body as AgentAssessmentResult);
    } catch (error) {
      setAssessmentError(error instanceof Error ? error.message : "Unable to complete the local assessment.");
    } finally {
      setAssessing(false);
    }
  }

  useEffect(() => {
    try {
      if (validatedCase) {
        window.localStorage.setItem("radonc-mdt-last-case", JSON.stringify(validatedCase));
      } else {
        window.localStorage.removeItem("radonc-mdt-last-case");
      }
    } catch {
      // Case and run data remain persisted by the local backend once a batch starts.
    }
  }, [validatedCase]);

  async function refreshMdtRound(roundNumber: number, runId = batchRun?.run_id) {
    if (!runId) return;
    try {
      const [summaryResponse, resultResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber),
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber + "/results")
      ]);
      if (summaryResponse.status === 404) {
        setRoundSummaries((current) => ({ ...current, [roundNumber]: null }));
        setRoundResults((current) => ({ ...current, [roundNumber]: [] }));
        return;
      }
      if (!summaryResponse.ok || !resultResponse.ok) {
        throw new Error("Unable to refresh Round " + roundNumber + ".");
      }
      const summary = (await summaryResponse.json()) as RoundSummary;
      const body = (await resultResponse.json()) as { results: RoundAgentResult[] };
      setRoundSummaries((current) => ({ ...current, [roundNumber]: summary }));
      setRoundResults((current) => ({ ...current, [roundNumber]: body.results }));
      if (roundNumber === 4 && summary.status === "completed") {
        const reportResponse = await fetch(API_BASE + "/api/runs/" + runId + "/report");
        if (reportResponse.ok) setFinalReport((await reportResponse.json()) as FinalMDTReport);
      }
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : "Unable to refresh MDT round.");
    }
  }

  async function startMdtRound(roundNumber: number, resume = false) {
    if (!batchRun) return;
    setRoundActionBusy(roundNumber);
    setRoundError("");
    try {
      const suffix = resume ? "/resume" : "";
      const response = await fetch(
        API_BASE + "/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + suffix,
        { method: "POST" }
      );
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to start Round " + roundNumber + ".");
      }
      setRoundSummaries((current) => ({ ...current, [roundNumber]: body as RoundSummary }));
      await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : "Unable to start MDT round.");
    } finally {
      setRoundActionBusy(null);
    }
  }

  useEffect(() => {
    if (batchRun?.status === "completed") {
      void refreshMdtRound(2, batchRun.run_id);
      void refreshMdtRound(3, batchRun.run_id);
      void refreshMdtRound(4, batchRun.run_id);
    }
  }, [batchRun?.run_id, batchRun?.status]);

  useEffect(() => {
    if (!batchRun) return;
    const active = Object.values(roundSummaries).some(
      (summary) => summary?.status === "queued" || summary?.status === "running"
    );
    if (!active) return;
    const timer = window.setInterval(() => {
      for (const roundNumber of [2, 3, 4]) {
        const summary = roundSummaries[roundNumber];
        if (summary?.status === "queued" || summary?.status === "running") {
          void refreshMdtRound(roundNumber, batchRun.run_id);
        }
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, roundSummaries]);

  async function refreshBatchRun(runId: string) {
    try {
      const [runResponse, resultsResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId),
        fetch(API_BASE + "/api/runs/" + runId + "/results")
      ]);
      if (!runResponse.ok || !resultsResponse.ok) {
        throw new Error("Unable to refresh the 45-agent run.");
      }
      const runData = (await runResponse.json()) as BatchRunSummary;
      const resultsData = (await resultsResponse.json()) as { results: BatchAgentResult[] };
      setBatchRun(runData);
      setBatchResults(resultsData.results);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to refresh batch progress.");
    }
  }

  useEffect(() => {
    try {
      if (batchRun) {
        window.localStorage.setItem("radonc-mdt-active-batch", JSON.stringify(batchRun));
      } else {
        window.localStorage.removeItem("radonc-mdt-active-batch");
      }
    } catch {
      // The run remains persisted on the local backend even if browser storage is unavailable.
    }
  }, [batchRun]);

  useEffect(() => {
    if (batchRun) {
      void refreshBatchRun(batchRun.run_id);
    }
  }, []);

  useEffect(() => {
    if (!batchRun || batchRun.status === "completed" || batchRun.status === "completed_with_errors") {
      return;
    }
    const runId = batchRun.run_id;
    const timer = window.setInterval(() => {
      void refreshBatchRun(runId);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, batchRun?.status]);

  async function startAllAgents() {
    if (!validatedCase) return;
    setBatchStarting(true);
    setBatchError("");
    setBatchRun(null);
    setBatchResults([]);
    try {
      const response = await fetch(API_BASE + "/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case: validatedCase })
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to start the 45-agent run.");
      }
      setBatchRun(body as BatchRunSummary);
      await refreshBatchRun((body as BatchRunSummary).run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to start the 45-agent run.");
    } finally {
      setBatchStarting(false);
    }
  }

  async function resumeAllAgents() {
    if (!batchRun) return;
    setBatchResuming(true);
    setBatchError("");
    try {
      const response = await fetch(API_BASE + "/api/runs/" + batchRun.run_id + "/resume", {
        method: "POST"
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to resume the run.");
      }
      setBatchRun(body as BatchRunSummary);
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to resume the run.");
    } finally {
      setBatchResuming(false);
    }
  }

  function downloadBatchResults() {
    if (!batchRun || batchResults.length === 0) return;
    const exportData = {
      simulator: "RadOnc MDT Simulator",
      mode: "four_round_educational_mdt_simulation",
      run: batchRun,
      independent_assessments: batchResults,
      debate: roundResults[2] ?? [],
      adversarial_review: roundResults[3] ?? [],
      chair_synthesis: finalReport,
      round_status: roundSummaries,
      notice: "Synthetic educational simulation only. Evidence retrieval is not connected; no clinical decision support is provided."
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "radonc-mdt-" + batchRun.run_id + "-independent-assessments.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function updateField(field: keyof typeof emptyForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setValidation(null);
    setValidatedCase(null);
    setAgentAssessment(null);
    setAssessmentError("");
    setBatchRun(null);
    setBatchResults([]);
    setBatchError("");
    setRoundSummaries({});
    setRoundResults({});
    setFinalReport(null);
    setRoundError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="RadOnc MDT Simulator home">
          <span className="brand-mark">RO</span>
          <span>
            <strong>RadOnc MDT</strong>
            <small>SIMULATOR</small>
          </span>
        </a>
        <div className="topbar-right">
          <span className="environment-pill"><span className="status-dot" /> LOCAL ENVIRONMENT</span>
          <button className="button button-quiet" onClick={() => void refreshStatus()} disabled={connectionState === "loading"}>
            {connectionState === "loading" ? "Checking…" : "Refresh status"}
          </button>
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">EDUCATION · SYNTHETIC CASES · LOCAL AI</p>
            <h1>Explore the case from<br /><em>every MDT perspective.</em></h1>
            <p className="hero-description">
              A structured learning workspace for multidisciplinary oncology discussion,
              evidence appraisal, patient context, and clinical uncertainty.
            </p>
          </div>
          <div className="hero-side">
            <span className="hero-number">45</span>
            <span className="hero-number-label">configured perspectives</span>
            <div className="hero-divider" />
            <span className="hero-number">04</span>
            <span className="hero-number-label">discussion rounds planned</span>
          </div>
        </section>

        <section className="safety-banner" role="note">
          <span className="safety-icon">!</span>
          <div>
            <strong>Educational simulation only</strong>
            <p>Use synthetic cases only. This prototype is not a medical device, clinical decision-support system, or substitute for a qualified MDT.</p>
          </div>
        </section>

        <section className="status-grid" aria-label="Local system status">
          <StatusCard
            label="Backend API"
            value={connectionState === "connected" ? "Connected" : connectionState === "loading" ? "Checking" : "Unavailable"}
            detail={health ? health.application + " · v" + health.version : "Start the local FastAPI service"}
            state={connectionState === "connected" ? "good" : connectionState === "loading" ? "neutral" : "bad"}
          />
          <StatusCard
            label="Ollama runtime"
            value={runtime?.reachable ? "Reachable" : runtime ? "Unavailable" : "Not checked"}
            detail={runtime?.reachable ? "Ollama " + runtime.version : "Expected at 127.0.0.1:11434"}
            state={runtime?.reachable ? "good" : "neutral"}
          />
          <StatusCard
            label="Local model"
            value={runtime?.configured_model_installed ? "Installed" : "Not verified"}
            detail={runtime?.configured_model ?? "qwen3.5:4b"}
            state={runtime?.configured_model_installed ? "good" : "neutral"}
          />
          <StatusCard
            label="Agent catalogue"
            value={agents.length === 45 ? "45 / 45 loaded" : agents.length + " loaded"}
            detail="All configured roles are listed"
            state={agents.length === 45 ? "good" : "neutral"}
          />
        </section>

        <div className="workspace-grid">
          <section className="panel case-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">01 / CASE WORKSPACE</p>
                <h2>Prepare a synthetic case</h2>
              </div>
              <span className="panel-index">CASE INPUT</span>
            </div>
            <p className="panel-intro">
              Enter fictional training details. Validation checks the data structure only; it does not assess diagnosis or treatment.
            </p>

            <form onSubmit={validateSyntheticCase} className="case-form">
              <label>
                Scenario title
                <input
                  required
                  minLength={3}
                  maxLength={160}
                  value={form.scenario_title}
                  onChange={(event) => updateField("scenario_title", event.target.value)}
                  placeholder="e.g. Synthetic oropharyngeal case"
                />
              </label>

              <label>
                Case summary <span className="required-mark">*</span>
                <textarea
                  required
                  minLength={10}
                  maxLength={12000}
                  rows={5}
                  value={form.case_summary}
                  onChange={(event) => updateField("case_summary", event.target.value)}
                  placeholder="Describe the fictional presentation and relevant context. Do not include real patient information."
                />
              </label>

              <div className="field-row">
                <label>
                  Age (optional)
                  <input
                    type="number"
                    min="0"
                    max="120"
                    value={form.age_years}
                    onChange={(event) => updateField("age_years", event.target.value)}
                    placeholder="Unknown"
                  />
                </label>
                <label>
                  Primary site
                  <input
                    value={form.primary_site}
                    onChange={(event) => updateField("primary_site", event.target.value)}
                    placeholder="e.g. Oropharynx"
                  />
                </label>
              </div>

              <label>
                Histology
                <input
                  value={form.histology}
                  onChange={(event) => updateField("histology", event.target.value)}
                  placeholder="e.g. Squamous cell carcinoma"
                />
              </label>

              <div className="form-footer">
                <span className="form-note">No patient name or medical record number fields are provided.</span>
                <button className="button button-primary" type="submit" disabled={validating || connectionState !== "connected"}>
                  {validating ? "Validating…" : "Validate synthetic case"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </form>

            {validation && (
              <div className="result-card result-success" role="status">
                <strong>Case structure valid</strong>
                <p>{validation.note}</p>
                {validation.warnings.length > 0 && (
                  <ul>{validation.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                )}
                <p className="result-footnote">Case structure is validated. Once all 45 independent assessments finish, the debate, adversarial review and Chair synthesis stages become available below.</p>
              </div>
            )}
            {validation && validatedCase && (
              <div className="assessment-launch">
                <div>
                  <strong>Try one local agent</strong>
                  <p>Run the guideline-focused Radiation Oncology perspective (RO-01) on this synthetic case using Ollama on this laptop.</p>
                </div>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => void runAgentAssessment()}
                  disabled={assessing || !runtime?.reachable || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
                >
                  {assessing ? "Generating locally…" : "Run RO-01 assessment"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            )}
            {assessmentError && (
              <div className="result-card result-error" role="alert">
                <strong>Local assessment failed</strong>
                <p>{assessmentError}</p>
              </div>
            )}
            {agentAssessment && (
              <div className="result-card result-success agent-assessment" role="status">
                <div className="assessment-header">
                  <strong>RO-01 · Guideline-focused Radiation Oncologist</strong>
                  <span>Round {agentAssessment.round_number}</span>
                </div>
                <div className="assessment-conclusion">
                  <strong>Provisional conclusion · {agentAssessment.position.replaceAll("_", " ")}</strong>
                  <p>{agentAssessment.provisional_conclusion}</p>
                  <strong>Preferred educational option</strong>
                  <p>{agentAssessment.preferred_educational_option}</p>
                </div>
                <p>{agentAssessment.perspective_summary}</p>
                {agentAssessment.discussion_options.length > 0 && (
                  <>
                    <strong>Topics for MDT discussion</strong>
                    <ul>{agentAssessment.discussion_options.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                {agentAssessment.unknowns.length > 0 && (
                  <>
                    <strong>Unknowns identified</strong>
                    <ul>{agentAssessment.unknowns.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                {agentAssessment.evidence_gaps.length > 0 && (
                  <>
                    <strong>Evidence gaps</strong>
                    <ul>{agentAssessment.evidence_gaps.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                <p className="result-footnote">
                  Model self-reported confidence: {Math.round(agentAssessment.confidence * 100)}%.
                  Evidence claims accepted: {agentAssessment.evidence_claims.length}.
                  No evidence retrieval is connected yet; this is not a treatment recommendation.
                </p>
              </div>
            )}
            {validation && validatedCase && (
              <section className="batch-run-panel">
                <div className="batch-heading">
                  <div>
                    <p className="eyebrow">03 / INDEPENDENT ASSESSMENTS</p>
                    <h3>Run all 45 MDT perspectives</h3>
                  </div>
                  <span className="count-chip">45 REQUIRED</span>
                </div>
                <p className="panel-intro">
                  Each agent receives only the original synthetic case and its own role profile. Agents do not see one another's assessments. Results are saved locally as they finish.
                </p>
                <div className="batch-actions">
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => void startAllAgents()}
                    disabled={batchStarting || batchResuming || assessing || !runtime?.reachable || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
                  >
                    {batchStarting ? "Starting…" : "Run all 45 agents"}
                    <span aria-hidden="true">→</span>
                  </button>
                  {batchRun && batchResults.length > 0 && (
                    <button className="button button-quiet" type="button" onClick={downloadBatchResults}>
                      Export JSON
                    </button>
                  )}
                  {(batchRun?.status === "completed_with_errors" ||
                    (batchRun?.status === "running" && Date.now() - Date.parse(batchRun.updated_at) > 120000) ||
                    (batchRun?.status === "queued" && Date.now() - Date.parse(batchRun.updated_at) > 120000)) && (
                    <button
                      className="button button-secondary"
                      type="button"
                      onClick={() => void resumeAllAgents()}
                      disabled={batchResuming || batchStarting}
                    >
                      {batchResuming ? "Resuming…" : batchRun.status === "completed_with_errors" ? "Retry failed agents" : "Recover interrupted run"}
                    </button>
                  )}
                </div>
                {batchRun && (
                  <div className="batch-status" aria-live="polite">
                    <div className="batch-status-top">
                      <strong>
                        {batchRun.status === "queued" ? "Queued" :
                          batchRun.status === "running" ? "Running independently" :
                          batchRun.status === "completed" ? "All 45 assessments completed" :
                          "Completed with some errors"}
                      </strong>
                      <span>{batchRun.finished_count} / {batchRun.total_agents} finished</span>
                    </div>
                    <div className="batch-progress-track">
                      <div className="batch-progress-fill" style={{ width: batchRun.progress_percent + "%" }} />
                    </div>
                    <div className="batch-counts">
                      <span className="count-complete">{batchRun.completed_count} completed</span>
                      <span className="count-failed">{batchRun.failed_count} failed</span>
                      <span>{batchRun.queued_count + batchRun.running_count} remaining</span>
                      {batchRun.current_agent_id && <span>Now: {batchRun.current_agent_id}</span>}
                    </div>
                    {batchRun.status === "running" && (
                      <p className="batch-estimate-note">This runs locally and sequentially. It may take several minutes. Keep the dashboard, backend and laptop running until it finishes.</p>
                    )}
                  </div>
                )}
                {batchError && <div className="result-card result-error" role="alert">{batchError}</div>}
                {batchResults.length > 0 && (
                  <div className="batch-results">
                    <div className="batch-results-title">
                      <strong>Agent results</strong>
                      <span>{batchResults.length} records saved locally</span>
                    </div>
                    {batchResults.map((item) => (
                      <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                        <summary>
                          <span className="agent-id">{item.agent_id}</span>
                          <strong>{item.agent_name}</strong>
                          <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                          {item.duration_seconds !== null && <span className="agent-duration">{item.duration_seconds.toFixed(1)}s</span>}
                        </summary>
                        {item.assessment ? (
                          <div className="batch-agent-body">
                            <div className="assessment-conclusion">
                              <strong>Provisional conclusion · {item.assessment.position.replaceAll("_", " ")}</strong>
                              <p>{item.assessment.provisional_conclusion}</p>
                              <strong>Preferred educational option</strong>
                              <p>{item.assessment.preferred_educational_option}</p>
                            </div>
                            <p>{item.assessment.perspective_summary}</p>
                            {item.assessment.discussion_options.length > 0 && (
                              <>
                                <strong>Discussion topics</strong>
                                <ul>{item.assessment.discussion_options.map((option, index) => <li key={index}>{option}</li>)}</ul>
                              </>
                            )}
                            {item.assessment.unknowns.length > 0 && (
                              <>
                                <strong>Unknowns</strong>
                                <ul>{item.assessment.unknowns.map((unknown, index) => <li key={index}>{unknown}</li>)}</ul>
                              </>
                            )}
                            {item.assessment.evidence_gaps.length > 0 && (
                              <>
                                <strong>Evidence gaps</strong>
                                <ul>{item.assessment.evidence_gaps.map((gap, index) => <li key={index}>{gap}</li>)}</ul>
                              </>
                            )}
                            <p className="result-footnote">
                              Model self-reported confidence: {Math.round(item.assessment.confidence * 100)}%.
                              Evidence claims accepted: {item.assessment.evidence_claims.length}.
                            </p>
                          </div>
                        ) : item.error_message ? (
                          <div className="batch-agent-body"><p className="error-text">{item.error_message}</p></div>
                        ) : (
                          <div className="batch-agent-body"><p>Waiting for this independent assessment.</p></div>
                        )}
                      </details>
                    ))}
                  </div>
                )}
                <p className="result-footnote">All outputs are simulated educational perspectives, not clinician opinions or treatment instructions. No evidence retrieval is connected yet.</p>
              </section>
            )}
            {batchRun?.status === "completed" && (
              <section className="mdt-rounds-panel">
                <div className="batch-heading">
                  <div>
                    <p className="eyebrow">04 / MDT DISCUSSION</p>
                    <h3>Four-round MDT workflow</h3>
                  </div>
                  <span className="count-chip">45 ROLES</span>
                </div>
                <p className="panel-intro">The debate and review stages ask each role to respond independently to a compact digest of other perspectives. Round 4 produces a chair synthesis that retains dissent and states the evidence limitations.</p>
                {[2, 3, 4].map((roundNumber) => {
                  const summary = roundSummaries[roundNumber];
                  const isPreviousComplete = roundNumber === 2
                    ? batchRun.status === "completed" && batchRun.completed_count === 45 && batchRun.failed_count === 0
                    : roundSummaries[roundNumber - 1]?.status === "completed";
                  const isActive = summary?.status === "queued" || summary?.status === "running";
                  const isRetryable = summary?.status === "completed_with_errors";
                  const title = roundNumber === 2 ? "MDT debate" : roundNumber === 3 ? "Adversarial review" : "MDT Chair synthesis";
                  const description = roundNumber === 2
                    ? "All 45 roles respond to selected peer positions, state agreements and challenges, and explain any change in position."
                    : roundNumber === 3
                    ? "All 45 roles challenge unsupported assumptions, evidence gaps, patient-context issues, feasibility and governance risks."
                    : "The MDT Chair assembles consensus, unresolved disagreements, minority views, uncertainties and missing information.";
                  const results = roundResults[roundNumber] ?? [];
                  return (
                    <div className="round-stage" key={roundNumber}>
                      <div className="round-stage-heading">
                        <div>
                          <span className="round-number">ROUND {roundNumber}</span>
                          <strong>{title}</strong>
                          <p>{description}</p>
                        </div>
                        {summary && <span className={"round-state state-" + summary.status}>{summary.status.replaceAll("_", " ")}</span>}
                      </div>
                      {!summary && (
                        <button
                          className="button button-secondary"
                          type="button"
                          disabled={!isPreviousComplete || roundActionBusy !== null}
                          onClick={() => void startMdtRound(roundNumber)}
                        >
                          {roundActionBusy === roundNumber ? "Starting…" : roundNumber === 4 ? "Generate final MDT report" : "Start Round " + roundNumber}
                          <span aria-hidden="true">→</span>
                        </button>
                      )}
                      {summary && (
                        <>
                          <div className="batch-status">
                            <div className="batch-status-top">
                              <strong>{summary.status === "completed" ? "Stage completed" : summary.status === "completed_with_errors" ? "Completed with errors" : "Stage running"}</strong>
                              <span>{summary.finished_count} / {summary.total_agents} finished</span>
                            </div>
                            <div className="batch-progress-track">
                              <div className="batch-progress-fill" style={{ width: summary.progress_percent + "%" }} />
                            </div>
                            <div className="batch-counts">
                              <span className="count-complete">{summary.completed_count} completed</span>
                              <span className="count-failed">{summary.failed_count} failed</span>
                              <span>{summary.queued_count + summary.running_count} remaining</span>
                              {summary.current_agent_id && <span>Now: {summary.current_agent_id}</span>}
                            </div>
                          </div>
                          {(isRetryable || (summary.status === "running" && Date.now() - Date.parse(summary.updated_at) > 120000)) && (
                            <button
                              className="button button-secondary"
                              type="button"
                              disabled={roundActionBusy !== null}
                              onClick={() => void startMdtRound(roundNumber, true)}
                            >
                              {roundActionBusy === roundNumber ? "Resuming…" : "Resume failed/interrupted work"}
                            </button>
                          )}
                          {roundNumber !== 4 && results.length > 0 && (
                            <div className="round-agent-list">
                              {results.map((item) => (
                                <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                                  <summary>
                                    <span className="agent-id">{item.agent_id}</span>
                                    <strong>{item.agent_name}</strong>
                                    <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                                  </summary>
                                  {item.result && (
                                    <div className="batch-agent-body">
                                      <strong>Position · {item.result.position.replaceAll("_", " ")}</strong>
                                      <p>{item.result.provisional_conclusion}</p>
                                      <strong>Response to other perspectives</strong>
                                      <p>{item.result.response_to_other_perspectives}</p>
                                      {item.result.agreements.length > 0 && <><strong>Agreements</strong><ul>{item.result.agreements.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                      {item.result.substantive_challenges.length > 0 && <><strong>Challenges</strong><ul>{item.result.substantive_challenges.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                      {item.result.risk_flags.length > 0 && <><strong>Risk flags</strong><ul>{item.result.risk_flags.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                    </div>
                                  )}
                                  {item.error_message && <div className="batch-agent-body"><p className="error-text">{item.error_message}</p></div>}
                                </details>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
                {roundError && <div className="result-card result-error" role="alert">{roundError}</div>}
                {finalReport && (
                  <div className="final-mdt-report">
                    <div className="assessment-conclusion">
                      <p className="eyebrow">ROUND 4 · CHAIR SYNTHESIS</p>
                      <h4>{finalReport.report_title}</h4>
                      <strong>Chair conclusion · {finalReport.overall_position.replaceAll("_", " ")}</strong>
                      <p>{finalReport.chair_conclusion}</p>
                      <strong>Overall educational synthesis</strong>
                      <p>{finalReport.overall_educational_synthesis}</p>
                    </div>
                    {([
                      ["Consensus", finalReport.consensus_points],
                      ["Unresolved disagreements", finalReport.unresolved_disagreements],
                      ["Minority and dissenting views", finalReport.minority_and_dissenting_views],
                      ["Major uncertainties", finalReport.major_uncertainties],
                      ["Missing information before real-world review", finalReport.missing_information_before_real_world_review],
                      ["Patient and family considerations", finalReport.patient_and_family_considerations],
                      ["Feasibility and resource considerations", finalReport.feasibility_and_resource_considerations],
                      ["Governance and safeguarding considerations", finalReport.governance_and_safeguarding_considerations],
                      ["Evidence limitations", finalReport.evidence_limitations]
                    ] as [string, string[]][]).map(([heading, items]) => (
                      <div className="report-section" key={heading}>
                        <strong>{heading}</strong>
                        {items.length > 0 ? <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>None recorded in this simulation.</p>}
                      </div>
                    ))}
                    <div className="report-section">
                      <strong>Chair reflection</strong>
                      <p>{finalReport.chair_reflection}</p>
                    </div>
                    <p className="result-footnote">Evidence retrieval is not connected. This report is an educational synthesis, not a clinical recommendation or treatment instruction.</p>
                  </div>
                )}
              </section>
            )}
            {validationError && (
              <div className="result-card result-error" role="alert">
                <strong>Validation failed</strong>
                <p>{validationError}</p>
              </div>
            )}
          </section>

          <section className="panel agents-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">02 / MDT PERSPECTIVES</p>
                <h2>Agent directory</h2>
              </div>
              <span className="count-chip">{agents.length || 45} ROLES</span>
            </div>
            <p className="panel-intro">
              Every role is intended to participate in each simulation. These are role profiles, not separate AI models or real clinician opinions.
            </p>

            <label className="filter-label">
              Filter by perspective
              <select value={agentFilter} onChange={(event) => setAgentFilter(event.target.value)}>
                {categories.map((category) => <option key={category}>{category}</option>)}
              </select>
            </label>

            <div className="agent-list">
              {filteredAgents.map((agent) => (
                <article className="agent-item" key={agent.agent_id}>
                  <span className="agent-id">{agent.agent_id}</span>
                  <div className="agent-copy">
                    <strong>{agent.name}</strong>
                    <p>{agent.mandate}</p>
                  </div>
                </article>
              ))}
              {agents.length === 0 && (
                <p className="empty-state">The agent catalogue will appear when the backend API is running.</p>
              )}
            </div>
            <p className="directory-footnote">Showing {filteredAgents.length} of {agents.length} configured perspectives.</p>
          </section>
        </div>

        <footer className="footer">
          <span>RADONC MDT SIMULATOR <span className="footer-separator">/</span> LOCAL-FIRST PROTOTYPE</span>
          <span>Research and education only · Synthetic data only</span>
        </footer>
      </main>
    </div>
  );
}

function StatusCard({
  label,
  value,
  detail,
  state
}: {
  label: string;
  value: string;
  detail: string;
  state: "good" | "bad" | "neutral";
}) {
  return (
    <article className="status-card">
      <div className="status-card-top">
        <span>{label}</span>
        <span className={"status-light " + state} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export default App;
