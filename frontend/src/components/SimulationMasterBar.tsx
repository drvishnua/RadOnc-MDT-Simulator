import { shouldOfferIndependentBatchResume } from "../runRecovery.js";
import type { ActiveSavedCase, Agent, BatchAgentResult, BatchRunSummary, RoundSummary, Runtime } from "../types.js";

export interface SimulationMasterBarProps {
  activeSavedCase: ActiveSavedCase | null;
  batchRun: BatchRunSummary | null;
  batchResults: BatchAgentResult[];
  batchStarting: boolean;
  batchResuming: boolean;
  assessing: boolean;
  runtime: Runtime | null;
  agents: Agent[];
  singleAgentToRun: string;
  onSelectSingleAgent: (agentId: string) => void;
  roundSummaries: Record<number, RoundSummary | null>;
  controlBusyKey: string | null;
  onStartFullSimulation: () => void;
  onStartAllAgents: () => void;
  onStartSingleAgentRun: (agentId: string) => void;
  onDownloadBatchResults: () => void;
  onResumeAllAgents: () => void;
  onPauseSimulation: () => void;
  onResumeSimulation: () => void;
  onStopSimulation: () => void;
  onRestartSimulation: () => void;
}

export function SimulationMasterBar({
  activeSavedCase,
  batchRun,
  batchResults,
  batchStarting,
  batchResuming,
  assessing,
  runtime,
  agents,
  singleAgentToRun,
  onSelectSingleAgent,
  roundSummaries,
  controlBusyKey,
  onStartFullSimulation,
  onStartAllAgents,
  onStartSingleAgentRun,
  onDownloadBatchResults,
  onResumeAllAgents,
  onPauseSimulation,
  onResumeSimulation,
  onStopSimulation,
  onRestartSimulation,
}: SimulationMasterBarProps) {
  const isBatchBusy =
    !activeSavedCase?.intake_backed ||
    batchStarting ||
    batchResuming ||
    assessing ||
    !runtime?.reachable ||
    (batchRun !== null && ["queued", "running"].includes(batchRun.status));

  return (
    <>
      <div className="simulation-master-bar">
        {activeSavedCase && (
          <>
            <button
              className="button button-full-simulation"
              type="button"
              onClick={onStartFullSimulation}
              disabled={isBatchBusy}
              title="Execute all 4 MDT rounds (Independent Assessments, Debate, Adversarial Review, and Chair Synthesis) on a single click"
            >
              {batchStarting ? "Starting Full Simulation…" : "▶ Run Entire Simulation (All 4 Rounds)"}
            </button>

            <button
              className="button button-secondary"
              type="button"
              onClick={onStartAllAgents}
              disabled={isBatchBusy}
              title="Run only Round 1 (independent assessments)"
            >
              Run Round 1 Only
            </button>

            <div className="single-agent-launcher" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <select
                className="agent-select-dropdown"
                value={singleAgentToRun}
                onChange={(e) => onSelectSingleAgent(e.target.value)}
                disabled={batchStarting || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
                style={{ padding: "6px 8px", borderRadius: "6px", background: "rgba(18, 34, 52, 0.95)", color: "#e2e8f0", border: "1px solid rgba(82, 186, 213, 0.4)", fontSize: "12px", height: "34px" }}
              >
                {agents.map((a) => (
                  <option key={a.agent_id} value={a.agent_id}>
                    {a.agent_id} · {a.name}
                  </option>
                ))}
              </select>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => onStartSingleAgentRun(singleAgentToRun)}
                disabled={isBatchBusy}
                title={`Run ONLY ${singleAgentToRun} in Round 1`}
                style={{ borderColor: "#38bdf8", color: "#38bdf8", height: "34px", padding: "0 12px", fontSize: "12px" }}
              >
                ⚡ Run {singleAgentToRun} Only
              </button>
            </div>
          </>
        )}
        {!activeSavedCase && !batchRun && (
          <p className="batch-estimate-note">Complete and accept a pre-MDT intake to create an immutable patient case version before starting a new MDT run.</p>
        )}
        {batchRun && batchResults.length > 0 && (
          <button className="button button-quiet" type="button" onClick={onDownloadBatchResults}>
            Export JSON
          </button>
        )}
        {shouldOfferIndependentBatchResume(batchRun) && (
          <button
            className="button button-secondary"
            type="button"
            onClick={onResumeAllAgents}
            disabled={batchResuming || batchStarting}
          >
            {batchResuming ? "Resuming…" : batchRun?.status === "completed_with_errors" ? "Retry failed agents" : "Recover interrupted run"}
          </button>
        )}
        {batchRun && (
          <div className="simulation-lifecycle-controls">
            {(batchRun.status === "running" || Object.values(roundSummaries).some((s) => s?.status === "running")) && (
              <button className="button button-warning button-xs" type="button" disabled={controlBusyKey !== null} onClick={onPauseSimulation} title="Pause all simulation activity">
                ⏸ Pause Simulation
              </button>
            )}
            {(batchRun.status === "paused" || Object.values(roundSummaries).some((s) => s?.status === "paused")) && (
              <button className="button button-primary button-xs" type="button" disabled={controlBusyKey !== null} onClick={onResumeSimulation} title="Resume paused simulation">
                ▶ Resume Simulation
              </button>
            )}
            {(["running", "paused", "queued"].includes(batchRun.status) || Object.values(roundSummaries).some((s) => ["running", "paused", "queued"].includes(s?.status || ""))) && (
              <button className="button button-danger button-xs" type="button" disabled={controlBusyKey !== null} onClick={onStopSimulation} title="Stop and cancel simulation">
                ⏹ Stop Simulation
              </button>
            )}
            <button
              className="button button-quiet button-xs"
              type="button"
              disabled={controlBusyKey !== null || batchStarting}
              onClick={() => {
                if (window.confirm("Restart entire simulation from Round 1? All current round results will be reset.")) {
                  onRestartSimulation();
                }
              }}
              title="Reset and re-run all 4 rounds from scratch"
            >
              🔄 Restart Whole Simulation
            </button>
          </div>
        )}
      </div>
      {batchRun && (
        <div className="batch-status" aria-live="polite">
          <div className="batch-status-top">
            <strong>
              {batchRun.status === "queued"
                ? "Queued"
                : batchRun.status === "running"
                ? "Running independently"
                : batchRun.status === "completed"
                ? `All ${batchRun.total_agents} assessments completed`
                : "Completed with some errors"}
            </strong>
            <span>
              {batchRun.finished_count} / {batchRun.total_agents} finished
            </span>
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
            <p className="batch-estimate-note">
              This runs locally and sequentially. It may take several minutes. Keep the dashboard, backend and laptop running until it finishes.
            </p>
          )}
        </div>
      )}
    </>
  );
}
