import { useEffect, useMemo, useRef, useState } from "react";
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

type HiveNodeStatus = "resting" | "queued" | "active" | "done" | "failed";

interface HiveNode {
  agentId: string;
  name: string;
  category: string;
  status: HiveNodeStatus;
  position: string;
  snippet: string;
}

/* ── colour helpers ───────────────────────────────────────── */

function statusBorderColor(status: HiveNodeStatus): string {
  switch (status) {
    case "active":  return "#38bdf8";
    case "done":    return "#4ade80";
    case "failed":  return "#f43f5e";
    case "queued":  return "#fbbf24";
    default:        return "#334155";
  }
}

function positionColor(position: string, status: HiveNodeStatus): string {
  if (status === "failed")  return "#f43f5e";
  if (status === "active")  return "#38bdf8";
  if (status === "queued")  return "#fbbf24";
  if (status === "resting") return "#64748b";
  switch (position) {
    case "supports":    return "#4ade80";
    case "conditional": return "#fbbf24";
    case "opposes":     return "#fb7185";
    default:            return "#94a3b8";
  }
}

/* ── category icon (emoji shorthand) ─────────────────────── */

const CATEGORY_ICONS: Record<string, string> = {
  "Radiation Oncology":                 "☢️",
  "Medical Oncology":                   "💊",
  "Surgical Oncology":                  "🔪",
  "Diagnostic Specialties":             "🔬",
  "Patient Perspective Lenses":         "🤝",
  "Family, Social Care and Vulnerability": "🏠",
  "System, Evidence and Governance":    "⚖️",
};

/* ── SVG specialist icon ─────────────────────────────────── */

function SpecialistBeeSvg({ color, active }: { color: string; active: boolean }) {
  return (
    <svg
      width="28"
      height="28"
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

/* ── category group sub-component ─────────────────────────── */

function CategoryGroup({
  category,
  nodes,
  selectedId,
  onSelect,
  defaultOpen,
  movedIds,
}: {
  category: string;
  nodes: HiveNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  defaultOpen: boolean;
  movedIds?: Set<string>;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const icon = CATEGORY_ICONS[category] ?? "📋";

  return (
    <div className="hive-cat-group">
      <button
        type="button"
        className="hive-cat-header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="hive-cat-icon">{icon}</span>
        <span className="hive-cat-name">{category}</span>
        <span className="hive-cat-count">{nodes.length}</span>
        <span className={`hive-cat-chevron ${open ? "is-open" : ""}`}>▸</span>
      </button>
      {open && (
        <div className="hive-cat-agents">
          {nodes.map((n) => (
            <button
              key={n.agentId}
              type="button"
              className={`hive-agent-chip hive-status-${n.status} ${selectedId === n.agentId ? "is-selected" : ""} ${movedIds?.has(n.agentId) ? "hive-just-moved" : ""}`}
              onClick={() => onSelect(n.agentId)}
              title={`${n.agentId} · ${n.name}`}
            >
              <SpecialistBeeSvg color={positionColor(n.position, n.status)} active={n.status === "active"} />
              <span className="hive-agent-id">{n.agentId}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── progress ring ────────────────────────────────────────── */

function ProgressRing({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? done / total : 0;
  const r = 16;
  const circ = 2 * Math.PI * r;
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" className="hive-progress-ring">
      <circle cx="20" cy="20" r={r} fill="none" stroke="#1e293b" strokeWidth="4" />
      <circle
        cx="20"
        cy="20"
        r={r}
        fill="none"
        stroke="#4ade80"
        strokeWidth="4"
        strokeDasharray={`${circ}`}
        strokeDashoffset={`${circ * (1 - pct)}`}
        strokeLinecap="round"
        transform="rotate(-90 20 20)"
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
      />
      <text x="20" y="24" textAnchor="middle" fill="#e2e8f0" fontSize="11" fontWeight="600">
        {Math.round(pct * 100)}%
      </text>
    </svg>
  );
}

/* ── zone panel ───────────────────────────────────────────── */

function ZonePanel({
  title,
  count,
  status,
  pulsing,
  children,
}: {
  title: string;
  count: number;
  status: HiveNodeStatus;
  pulsing?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`hive-zone hive-zone-${status} ${pulsing ? "is-pulsing" : ""}`}
      style={{ borderColor: statusBorderColor(status) }}
    >
      <div className="hive-zone-header">
        <span className="hive-zone-title">{title}</span>
        <span className="hive-zone-badge">{count}</span>
      </div>
      <div className="hive-zone-body">{children}</div>
    </div>
  );
}

/* ── group nodes by category ──────────────────────────────── */

function groupByCategory(nodes: HiveNode[]): Map<string, HiveNode[]> {
  const map = new Map<string, HiveNode[]>();
  for (const n of nodes) {
    const arr = map.get(n.category);
    if (arr) arr.push(n);
    else map.set(n.category, [n]);
  }
  return map;
}

/* ── MAIN COMPONENT ───────────────────────────────────────── */

export function LiveHiveMonitor({
  agents,
  batchRun,
  batchResults,
  roundSummaries,
  roundResults,
  finalReport,
}: LiveHiveMonitorProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [movedIds, setMovedIds] = useState<Set<string>>(new Set());
  const prevNodesRef = useRef<Map<string, HiveNodeStatus>>(new Map());

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

    /* Build an ordered list of agent IDs to determine queue position */
    const agentIds = agents.map((a) => a.agent_id);
    const roundStatus = activeRound === 1 ? batchRun?.status : roundSummaries[activeRound]?.status;
    const allowQueue = roundStatus === "running" || roundStatus === "queued";
    const currentIdx = currentId ? agentIds.indexOf(currentId) : -1;
    let queuedAssigned = 0;

    return agents.map((agent, idx) => {
      const rN = activeRound >= 2 ? rNMap.get(agent.agent_id) : undefined;
      const r1 = r1Map.get(agent.agent_id);
      const rawStatus = rN?.status ?? r1?.status ?? "queued";

      /*
       * BUG FIX: check completed/failed BEFORE currentId.
       * An agent whose rawStatus is "completed" is done even if
       * current_agent_id hasn't moved on yet.
       */
      let status: HiveNodeStatus;
      if (rawStatus === "completed") {
        status = "done";
      } else if (rawStatus === "failed") {
        status = "failed";
      } else if (currentId === agent.agent_id || rawStatus === "running") {
        status = "active";
      } else if (rawStatus === "queued" && allowQueue) {
        if (currentIdx >= 0) {
          status = idx > currentIdx && idx <= currentIdx + 3 ? "queued" : "resting";
        } else if (queuedAssigned < 3) {
          queuedAssigned += 1;
          status = "queued";
        } else {
          status = "resting";
        }
      } else {
        status = "resting";
      }

      const position =
        status === "failed"
          ? "failed"
          : (rN?.result?.position ?? r1?.assessment?.position ?? "insufficient_information");
      const snippet =
        status === "failed"
          ? (rN?.error_message ?? r1?.error_message ?? "Failed to generate specialist response.")
          : (rN?.result?.provisional_conclusion ??
            r1?.assessment?.provisional_conclusion ??
            (status === "active" ? "Generating specialist response…" :
             status === "queued" ? "Up next…" :
             "Waiting…"));

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

  /* Track which agents changed zone for animation classes */
  useEffect(() => {
    const moved = new Set<string>();
    const prev = prevNodesRef.current;
    for (const n of nodes) {
      const prevStatus = prev.get(n.agentId);
      if (prevStatus && prevStatus !== n.status) {
        moved.add(n.agentId);
      }
    }
    const next = new Map<string, HiveNodeStatus>();
    for (const n of nodes) next.set(n.agentId, n.status);
    prevNodesRef.current = next;

    if (moved.size === 0) return;
    setMovedIds(moved);
    const timer = window.setTimeout(() => setMovedIds(new Set()), 700);
    return () => window.clearTimeout(timer);
  }, [nodes]);

  const categories = useMemo(
    () => Array.from(new Set(nodes.map((n) => n.category))),
    [nodes]
  );

  const visibleNodes = useMemo(
    () =>
      categoryFilter === "ALL"
        ? nodes
        : nodes.filter((n) => n.category === categoryFilter),
    [nodes, categoryFilter]
  );

  const totalCompletedCount = nodes.filter((n) => n.status === "done").length;
  const totalFailedCount = nodes.filter((n) => n.status === "failed").length;
  const restingNodes   = visibleNodes.filter((n) => n.status === "resting");
  const queuedNodes    = visibleNodes.filter((n) => n.status === "queued");
  const activeNodes    = visibleNodes.filter((n) => n.status === "active");
  const completedNodes = visibleNodes.filter((n) => n.status === "done");
  const failedNodes    = visibleNodes.filter((n) => n.status === "failed");

  const isLive =
    batchRun?.status === "running" ||
    Object.values(roundSummaries).some((s) => s?.status === "running");

  const inspectedNode =
    nodes.find((n) => n.agentId === selectedId) ??
    activeNodes[0] ??
    failedNodes[failedNodes.length - 1] ??
    completedNodes[completedNodes.length - 1] ??
    null;

  if (!batchRun) return null;

  const restingGroups   = groupByCategory(restingNodes);
  const completedGroups = groupByCategory(completedNodes);
  const failedGroups    = groupByCategory(failedNodes);

  return (
    <section className="hive-monitor-card" aria-label="Live MDT Specialist Hive Monitor">
      {/* ── Header ───────────────────────────────── */}
      <div className="hive-monitor-header">
        <div className="hive-header-left">
          <ProgressRing done={totalCompletedCount} total={nodes.length} />
          <div>
            <strong>Live Specialist Hive · Round {activeRound}</strong>
            <span className="hive-meta">
              {totalCompletedCount} of {nodes.length} responded
              {totalFailedCount > 0 && (
                <span className="hive-meta-failed"> · {totalFailedCount} failed</span>
              )}
              {finalReport ? " · Chair Synthesis Ready" : ""}
            </span>
          </div>
        </div>
        <span className={`hive-live-pill ${isLive ? "is-live" : ""}`}>
          <span className="hive-live-dot" />
          {isLive ? "Live" : batchRun.status.replaceAll("_", " ")}
        </span>
      </div>

      {/* ── Interactive Specialty Filter ─────────── */}
      <div className="hive-filter-bar" role="toolbar" aria-label="Filter specialists by discipline">
        <button
          type="button"
          className={`hive-filter-pill ${categoryFilter === "ALL" ? "is-active" : ""}`}
          onClick={() => setCategoryFilter("ALL")}
        >
          All ({nodes.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`hive-filter-pill ${categoryFilter === cat ? "is-active" : ""}`}
            onClick={() => setCategoryFilter((prev) => (prev === cat ? "ALL" : cat))}
          >
            <span>{CATEGORY_ICONS[cat] ?? "📋"}</span>
            <span>{cat}</span>
          </button>
        ))}
      </div>

      {/* ── Four-zone grid ───────────────────────── */}
      <div className={`hive-four-grid ${totalFailedCount > 0 ? "has-failed" : ""}`}>
        {/* Resting */}
        <ZonePanel title="Resting" count={restingNodes.length} status="resting">
          {restingGroups.size === 0 ? (
            <p className="hive-zone-empty">All specialists engaged</p>
          ) : (
            Array.from(restingGroups.entries()).map(([cat, catNodes]) => (
              <CategoryGroup
                key={cat}
                category={cat}
                nodes={catNodes}
                selectedId={selectedId}
                onSelect={setSelectedId}
                defaultOpen={false}
                movedIds={movedIds}
              />
            ))
          )}
        </ZonePanel>

        {/* Queued */}
        <ZonePanel title="Queued" count={queuedNodes.length} status="queued">
          {queuedNodes.length === 0 ? (
            <p className="hive-zone-empty">—</p>
          ) : (
            queuedNodes.map((n) => (
              <button
                key={n.agentId}
                type="button"
                className={`hive-agent-chip hive-status-queued hive-enter-slide ${selectedId === n.agentId ? "is-selected" : ""} ${movedIds.has(n.agentId) ? "hive-just-moved" : ""}`}
                onClick={() => setSelectedId(n.agentId)}
                title={`${n.agentId} · ${n.name} — Up next`}
              >
                <SpecialistBeeSvg color="#fbbf24" active={false} />
                <span className="hive-agent-id">{n.agentId}</span>
              </button>
            ))
          )}
        </ZonePanel>

        {/* Active */}
        <ZonePanel title="Active" count={activeNodes.length} status="active" pulsing={isLive}>
          {activeNodes.length === 0 ? (
            <p className="hive-zone-empty">{finalReport ? "✓ All done" : "Idle"}</p>
          ) : (
            activeNodes.map((n) => (
              <button
                key={n.agentId}
                type="button"
                className={`hive-agent-chip hive-status-active is-active hive-enter-pop ${selectedId === n.agentId ? "is-selected" : ""} ${movedIds.has(n.agentId) ? "hive-just-moved" : ""}`}
                onClick={() => setSelectedId(n.agentId)}
                title={`${n.agentId} · ${n.name} (Responding)`}
              >
                <SpecialistBeeSvg color="#38bdf8" active={true} />
                <span className="hive-agent-id">{n.agentId}</span>
                <span className="hive-agent-name">{n.name}</span>
              </button>
            ))
          )}
        </ZonePanel>

        {/* Completed */}
        <ZonePanel title="Completed" count={completedNodes.length} status="done">
          {completedGroups.size === 0 ? (
            <p className="hive-zone-empty">—</p>
          ) : (
            Array.from(completedGroups.entries()).map(([cat, catNodes]) => (
              <CategoryGroup
                key={cat}
                category={cat}
                nodes={catNodes}
                selectedId={selectedId}
                onSelect={setSelectedId}
                defaultOpen={true}
                movedIds={movedIds}
              />
            ))
          )}
        </ZonePanel>

        {/* Failed */}
        {totalFailedCount > 0 && (
          <ZonePanel title="Failed" count={failedNodes.length} status="failed">
            {failedGroups.size === 0 ? (
              <p className="hive-zone-empty">—</p>
            ) : (
              Array.from(failedGroups.entries()).map(([cat, catNodes]) => (
                <CategoryGroup
                  key={cat}
                  category={cat}
                  nodes={catNodes}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  defaultOpen={true}
                  movedIds={movedIds}
                />
              ))
            )}
          </ZonePanel>
        )}
      </div>

      {/* ── Inspector panel ──────────────────────── */}
      {inspectedNode && (
        <div className={`hive-inspector hive-inspector-${inspectedNode.status}`}>
          <div className="hive-inspector-header">
            <SpecialistBeeSvg color={positionColor(inspectedNode.position, inspectedNode.status)} active={inspectedNode.status === "active"} />
            <div>
              <strong>{inspectedNode.agentId} · {inspectedNode.name}</strong>
              <span className="hive-inspector-cat">{inspectedNode.category}</span>
            </div>
            <span className={`hive-pos-tag hive-pos-${inspectedNode.position}`}>
              {inspectedNode.position.replaceAll("_", " ")}
            </span>
          </div>
          <p>{inspectedNode.snippet}</p>
        </div>
      )}

      {/* ── Legend ────────────────────────────────── */}
      <div className="hive-legend">
        <span><i style={{ background: "#4ade80" }} /> Supports / Completed</span>
        <span><i style={{ background: "#38bdf8" }} /> Active / Responding</span>
        <span><i style={{ background: "#fbbf24" }} /> Queued / Conditional</span>
        <span><i style={{ background: "#fb7185" }} /> Opposes / Failed</span>
        <span><i style={{ background: "#64748b" }} /> Resting</span>
      </div>
    </section>
  );
}
