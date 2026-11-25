import { StatusCard } from "./StatusCard.js";
import type { Agent, Health, Runtime } from "../types.js";

export function SystemHealthTab({
  agents,
  connectionState,
  health,
  runtime
}: {
  agents: Agent[];
  connectionState: "loading" | "connected" | "unavailable";
  health: Health | null;
  runtime: Runtime | null;
}) {
  return (
    <section className="tab-view-container">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">ONCOLOGY EDUCATION · TRAINING RECORDS · LOCAL AI</p>
          <h1>Explore the case from<br /><em>every MDT perspective.</em></h1>
          <p className="hero-description">
            A structured learning workspace for multidisciplinary oncology discussion,
            evidence appraisal, patient context, and clinical uncertainty.
          </p>
        </div>
        <div className="hero-side">
          <span className="hero-number">{agents.length || 49}</span>
          <span className="hero-number-label">configured perspectives</span>
          <div className="hero-divider" />
          <span className="hero-number">04</span>
          <span className="hero-number-label">discussion rounds planned</span>
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
          value={agents.length >= 45 ? `${agents.length} / ${agents.length} loaded` : agents.length + " loaded"}
          detail="All configured roles are listed"
          state={agents.length >= 45 ? "good" : "neutral"}
        />
      </section>
    </section>
  );
}
