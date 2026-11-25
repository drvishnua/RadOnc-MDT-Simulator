import { useMemo, useState } from "react";
import type {
  Agent,
  BatchAgentResult,
  BatchRunSummary,
  FinalMDTReport,
  RoundAgentResult,
  RoundSummary,
} from "../types.js";

export interface LiveHiveMonitorProps {
  agents: Agent[];
  batchRun: BatchRunSummary | null;
  batchResults: BatchAgentResult[];
  roundSummaries: Record<number, RoundSummary | null>;
  roundResults: Record<number, RoundAgentResult[]>;
  finalReport: FinalMDTReport | null;
}

type HiveNodeStatus = "resting" | "active" | "done" | "failed";

interface HiveNode {
  agentId: string;
  name: string;
  category: string;
  status: HiveNodeStatus;
  position: string;
  snippet: string;
}

function positionColor(position: string, status: HiveNodeStatus): string {
  if (status === "failed") return "#f43f5e";
  if (status === "active") return "#38bdf8";
  if (status === "resting") return "#64748b";
  switch (position) {
    case "supports":
      return "#4ade80";
    case "conditional":
      return "#fbbf24";
    case "opposes":
      return "#fb7185";
    default:
      return "#94a3b8";
  }
}

function SpecialistBeeSvg({ color, active }: { color: string; active: boolean }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      className={`hive-bee-svg ${active ? "hive-bee-active" : ""}`}
      aria-hidden="true"
    >
      <ellipse cx="9" cy="7" rx="4" ry="2.5" fill="rgba(226,232,240,0.75)" />
      <ellipse cx="15" cy="7" rx="4" ry="2.5" fill="rgba(226,232,240,0.75)" />
      <ellipse cx="12" cy="14" rx="6" ry="5" fill={color} stroke="#0f172a" strokeWidth="1.5" />
      <line x1="8" y1="12" x2="16" y2="12" stroke="#0f172a" strokeWidth="1.5" />
      <line x1="8" y1="15.5" x2="16" y2="15.5" stroke="#0f172a" strokeWidth="1.5" />
      <circle cx="10" cy="11" r="1" fill="#0f172a" />
      <circle cx="14" cy="11" r="1" fill="#0f172a" />
    </svg>
  );
}

export function LiveHiveMonitor({
  agents,
  batchRun,
  batchResults,
  roundSummaries,
  roundResults,
  finalReport,
}: LiveHiveMonitorProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const activeRound = useMemo(() => {
    for (const r of [4, 3, 2]) {
      if (roundSummaries[r] && ["running", "paused", "queued", "completed", "completed_with_errors"].includes(roundSummaries[r]!.status)) {
        return r;
      }
    }
    return 1;
  }, [roundSummaries]);

  const nodes = useMemo<HiveNode[]>(() => {
    const r1Map = new Map(batchResults.map((r) => [r.agent_id, r]));
    const rNMap = new Map((roundResults[activeRound] ?? []).map((r) => [r.agent_id, r]));
    const currentId =
      activeRound === 1 ? batchRun?.current_agent_id : roundSummaries[activeRound]?.current_agent_id;

    return agents.map((agent) => {
      const rN = activeRound >= 2 ? rNMap.get(agent.agent_id) : undefined;
      const r1 = r1Map.get(agent.agent_id);
      const rawStatus = rN?.status ?? r1?.status ?? "queued";

      let status: HiveNodeStatus = "resting";
      if (currentId === agent.agent_id || rawStatus === "running") {
        status = "active";
      } else if (rawStatus === "completed") {
        status = "done";
      } else if (rawStatus === "failed") {
        status = "failed";
      }

      const position =
        rN?.result?.position ?? r1?.assessment?.position ?? "insufficient_information";
      const snippet =
        rN?.result?.provisional_conclusion ??
        r1?.assessment?.provisional_conclusion ??
        (status === "active" ? "Generating specialist response…" : "Waiting in queue…");

      return {
        agentId: agent.agent_id,
        name: agent.name,
        category: agent.category_label,
        status,
        position,
        snippet,
      };
    });
  }, [agents, batchResults, roundResults, activeRound, batchRun, roundSummaries]);

  const restingNodes = nodes.filter((n) => n.status === "resting");
  const activeNodes = nodes.filter((n) => n.status === "active");
  const doneNodes = nodes.filter((n) => n.status === "done" || n.status === "failed");
  const isLive =
    batchRun?.status === "running" ||
    Object.values(roundSummaries).some((s) => s?.status === "running");

  const inspectedNode =
    nodes.find((n) => n.agentId === selectedId) ?? activeNodes[0] ?? doneNodes[doneNodes.length - 1] ?? null;

  if (!batchRun) return null;

  return (
    <section className="hive-monitor-card" aria-label="Live MDT Specialist Hive Monitor">
      <div className="hive-monitor-header">
        <div>
          <strong>Live Specialist Hive · Round {activeRound}</strong>
          <span className="hive-meta">
            {doneNodes.length} of {nodes.length} responded
            {finalReport ? " · Chair Synthesis Ready" : ""}
          </span>
        </div>
        <span className={`hive-live-pill ${isLive ? "is-live" : ""}`}>
          <span className="hive-live-dot" />
          {isLive ? "Live" : batchRun.status.replaceAll("_", " ")}
        </span>
      </div>

      <div className="hive-hex-grid">
        <div className="hive-hex hive-hex-resting">
          <div className="hive-hex-title">Resting</div>
          <div className="hive-hex-count">{restingNodes.length}</div>
          <div className="hive-bee-cluster">
            {restingNodes.slice(0, 6).map((n) => (
              <button
                key={n.agentId}
                type="button"
                className={`hive-bee-btn ${selectedId === n.agentId ? "is-selected" : ""}`}
                onClick={() => setSelectedId(n.agentId)}
                title={`${n.agentId} · ${n.name}`}
              >
                <SpecialistBeeSvg color={positionColor(n.position, n.status)} active={false} />
                <span>{n.agentId}</span>
              </button>
            ))}
            {restingNodes.length > 6 && (
              <span className="hive-overflow-badge">+{restingNodes.length - 6}</span>
            )}
          </div>
        </div>

        <div className={`hive-hex hive-hex-coordinator ${isLive ? "is-pulsing" : ""}`}>
          <div className="hive-hex-title">Coordinator</div>
          <div className="hive-hex-count">
            {doneNodes.length} of {nodes.length} done
          </div>
          <div className="hive-bee-cluster">
            {activeNodes.length > 0 ? (
              activeNodes.map((n) => (
                <button
                  key={n.agentId}
                  type="button"
                  className="hive-bee-btn is-active"
                  onClick={() => setSelectedId(n.agentId)}
                  title={`${n.agentId} · ${n.name} (Responding)`}
                >
                  <SpecialistBeeSvg color="#38bdf8" active={true} />
                  <span>{n.agentId}</span>
                </button>
              ))
            ) : (
              <SpecialistBeeSvg color={finalReport ? "#4ade80" : "#fbbf24"} active={false} />
            )}
          </div>
        </div>

        <div className="hive-hex hive-hex-done">
          <div className="hive-hex-title">Done</div>
          <div className="hive-hex-count">{doneNodes.length}</div>
          <div className="hive-bee-cluster">
            {doneNodes.slice(0, 8).map((n) => (
              <button
                key={n.agentId}
                type="button"
                className={`hive-bee-btn ${selectedId === n.agentId ? "is-selected" : ""}`}
                onClick={() => setSelectedId(n.agentId)}
                title={`${n.agentId} · ${n.name} (${n.position})`}
              >
                <SpecialistBeeSvg color={positionColor(n.position, n.status)} active={false} />
                <span>{n.agentId}</span>
              </button>
            ))}
            {doneNodes.length > 8 && (
              <span className="hive-overflow-badge">+{doneNodes.length - 8}</span>
            )}
          </div>
        </div>
      </div>

      {inspectedNode && (
        <div className="hive-inspector">
          <strong>
            {inspectedNode.agentId} · {inspectedNode.name}
          </strong>
          <span className="hive-pos-tag">{inspectedNode.position.replaceAll("_", " ")}</span>
          <p>{inspectedNode.snippet}</p>
        </div>
      )}

      <div className="hive-legend">
        <span><i style={{ background: "#4ade80" }} /> Supports / Done</span>
        <span><i style={{ background: "#38bdf8" }} /> Active / Responding</span>
        <span><i style={{ background: "#fbbf24" }} /> Conditional</span>
        <span><i style={{ background: "#fb7185" }} /> Opposes / Failed</span>
        <span><i style={{ background: "#64748b" }} /> Resting / Insufficient</span>
      </div>
    </section>
  );
}
