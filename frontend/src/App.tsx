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

const emptyForm = {
  scenario_title: "Synthetic head-and-neck case",
  case_summary: "",
  age_years: "",
  primary_site: "",
  histology: ""
};

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [runtime, setRuntime] = useState<Runtime | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [connectionState, setConnectionState] = useState<"loading" | "connected" | "unavailable">("loading");
  const [form, setForm] = useState(emptyForm);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validationError, setValidationError] = useState("");
  const [validating, setValidating] = useState(false);
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

    const payload = {
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
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : "Unable to reach the local API.");
    } finally {
      setValidating(false);
    }
  }

  function updateField(field: keyof typeof emptyForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
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
                <p className="result-footnote">Full MDT simulation is not implemented yet.</p>
              </div>
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
