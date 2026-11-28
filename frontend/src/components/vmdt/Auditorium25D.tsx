import React, { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Pause, Play, RotateCcw, Sparkles, X } from "lucide-react";
import DoctorAvatar from "./DoctorAvatar.js";
import { TEAM_DEFINITIONS } from "../../utils/vmdtRoster.js";
import {
  DEFAULT_TEAMS,
  type AgentSeatStatus,
  type TeamId,
  type VmdtAgentConfig,
} from "../../virtualMdtTypes.js";

export interface Auditorium25DProps {
  mode: "hall" | "live";
  agents: VmdtAgentConfig[];
  seatStatuses?: Record<string, AgentSeatStatus>;
  seatConclusions?: Record<string, string>;
  activeSpeakerId?: string | null;
  selectedAgentId?: string | null;
  onSelectAgent?: (agentId: string | null) => void;
  onRunFirst?: (agentId: string) => void;
  onRetryAgent?: (agentId: string) => void;
  onPauseAgent?: (agentId: string) => void;
  isSimulationRunning?: boolean;
}

interface PositionedSeat {
  agent: VmdtAgentConfig;
  xPercent: number;
  yPercent: number;
  scale: number;
  rowIndex: number;
}

const STATUS_STYLE: Record<
  AgentSeatStatus,
  { ring: string; beam: string; pillBg: string; label: string }
> = {
  idle: {
    ring: "border-emerald-400/75 shadow-[0_0_12px_rgba(16,185,129,0.5)] dark:border-sky-400/70 dark:shadow-[0_0_14px_rgba(56,189,248,0.55)]",
    beam: "from-sky-400/0 via-sky-400/10 to-transparent",
    pillBg: "bg-slate-700 text-slate-100",
    label: "ready",
  },
  queued: {
    ring: "border-amber-500 shadow-[0_0_14px_rgba(245,158,11,0.65)]",
    beam: "from-amber-400/35 via-amber-400/12 to-transparent",
    pillBg: "bg-amber-500 text-slate-950",
    label: "queued",
  },
  running: {
    ring: "border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.95)] dark:border-sky-400",
    beam: "from-blue-500/60 via-sky-400/25 to-transparent",
    pillBg: "bg-blue-600 text-white",
    label: "active speaker",
  },
  completed: {
    ring: "border-emerald-500 shadow-[0_0_14px_rgba(16,185,129,0.75)]",
    beam: "from-emerald-400/40 via-emerald-400/12 to-transparent",
    pillBg: "bg-emerald-600 text-white",
    label: "completed",
  },
  failed: {
    ring: "border-rose-500 shadow-[0_0_16px_rgba(239,68,68,0.85)]",
    beam: "from-rose-500/50 via-rose-500/15 to-transparent",
    pillBg: "bg-rose-600 text-white",
    label: "failed",
  },
  paused: {
    ring: "border-slate-400 shadow-[0_0_10px_rgba(148,163,184,0.45)]",
    beam: "from-slate-400/25 via-slate-400/10 to-transparent",
    pillBg: "bg-slate-600 text-white",
    label: "paused",
  },
};

function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

export const Auditorium25D: React.FC<Auditorium25DProps> = ({
  mode,
  agents,
  seatStatuses = {},
  seatConclusions = {},
  activeSpeakerId = null,
  selectedAgentId = null,
  onSelectAgent,
  onRunFirst,
  onRetryAgent,
  onPauseAgent,
  isSimulationRunning = false,
}) => {
  const [hoveredTeam, setHoveredTeam] = useState<TeamId | null>(null);
  const [hoveredAgentId, setHoveredAgentId] = useState<string | null>(null);
  const [pinnedAgentId, setPinnedAgentId] = useState<string | null>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setPinnedAgentId(null);
        setHoveredAgentId(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const activeAgents = useMemo(() => agents.filter((a) => a.active), [agents]);

  const { seats, wedgeMeta } = useMemo(() => {
    const teams = DEFAULT_TEAMS;
    const n = teams.length;
    const minAngle = -78;
    const maxAngle = 78;
    const totalSpan = maxAngle - minAngle;
    const step = totalSpan / n;

    // Ellipse origin is slightly above the auditorium container so seats curve cleanly downward
    const originX = 50;
    const originY = -12;
    const radiusXBase = 47;
    const radiusYBase = 88;

    const computedSeats: PositionedSeat[] = [];
    const meta = teams.map((teamId, wedgeIdx) => {
      const a0 = minAngle + wedgeIdx * step;
      const a1 = a0 + step;
      const aMid = (a0 + a1) / 2;
      const teamAgents = activeAgents.filter((a) => a.teamId === teamId);

      // Arrange agents inside wedge cleanly in up to 3 concentric tiers
      const rowCapacities = teamAgents.length <= 3 ? [teamAgents.length] : teamAgents.length <= 7 ? [3, 4] : [3, 4, Math.max(4, teamAgents.length - 7)];
      let cursor = 0;
      rowCapacities.forEach((cap, rowIndex) => {
        const countInRow = Math.min(cap, Math.max(0, teamAgents.length - cursor));
        if (countInRow === 0) return;
        const depthT = rowCapacities.length === 1 ? 0.55 : rowIndex / Math.max(1, rowCapacities.length - 1);
        const rFactor = 0.42 + depthT * 0.43; // inner row 42%, outer row 85%
        const innerPad = 3.2;
        const spanStart = a0 + innerPad;
        const spanEnd = a1 - innerPad;

        for (let i = 0; i < countInRow; i += 1) {
          const agent = teamAgents[cursor];
          cursor += 1;
          const frac = countInRow === 1 ? 0.5 : i / (countInRow - 1);
          const angle = spanStart + frac * (spanEnd - spanStart);
          const rad = degToRad(angle);
          const xPercent = originX + Math.sin(rad) * radiusXBase * rFactor * 1.15;
          const yPercent = originY + Math.cos(rad) * radiusYBase * rFactor;
          computedSeats.push({
            agent,
            xPercent: Math.max(4, Math.min(96, xPercent)),
            yPercent: Math.max(10, Math.min(82, yPercent)),
            scale: 0.78 + depthT * 0.22,
            rowIndex,
          });
        }
      });

      const midRad = degToRad(aMid);
      const labelX = originX + Math.sin(midRad) * 49;
      const labelY = Math.min(93.5, originY + Math.cos(midRad) * 98);
      return {
        teamId,
        label: TEAM_DEFINITIONS[teamId].label,
        a0,
        a1,
        aMid,
        labelX,
        labelY,
        count: teamAgents.length,
      };
    });

    return { seats: computedSeats, wedgeMeta: meta };
  }, [activeAgents]);

  const activePopoverId = pinnedAgentId ?? hoveredAgentId;
  const activeSeat = seats.find((s) => s.agent.id === activePopoverId) || null;

  return (
    <div
      className="relative flex-1 w-full overflow-hidden select-none"
      onClick={() => setPinnedAgentId(null)}
    >
      {/* Semi-circular SVG Floor, Perspective Tier Arcs & Glowing Radial Aisle Dividers */}
      <svg
        viewBox="0 0 1200 440"
        preserveAspectRatio="none"
        className="pointer-events-none absolute inset-0 h-full w-full"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="floorDark" cx="50%" cy="-10%" r="98%">
            <stop offset="0%" stopColor="#0f172a" stopOpacity="0.9" />
            <stop offset="55%" stopColor="#111c33" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#070b14" stopOpacity="0.98" />
          </radialGradient>
          <radialGradient id="floorLight" cx="50%" cy="-10%" r="98%">
            <stop offset="0%" stopColor="#f8fafc" stopOpacity="0.95" />
            <stop offset="65%" stopColor="#e2e8f0" stopOpacity="0.92" />
            <stop offset="100%" stopColor="#cbd5e1" stopOpacity="0.9" />
          </radialGradient>
        </defs>

        {/* Auditorium Curved Floor */}
        <path
          d="M 20 80 Q 600 180 1180 80 L 1195 360 Q 600 475 5 360 Z"
          className="fill-[url(#floorLight)] dark:fill-[url(#floorDark)] transition-colors duration-300"
        />

        {/* Perspective Tier Rings */}
        {[0.38, 0.58, 0.78, 0.96].map((r, idx) => {
          const rx = 620 * r;
          const ry = 365 * r;
          return (
            <ellipse
              key={idx}
              cx="600"
              cy="-35"
              rx={rx}
              ry={ry}
              fill="none"
              className="stroke-slate-300/80 dark:stroke-indigo-400/20"
              strokeWidth={idx === 3 ? "2" : "1.2"}
            />
          );
        })}

        {/* Radial Wedge Dividers */}
        {[-78, -52, -26, 0, 26, 52, 78].map((angle, idx) => {
          const rad = degToRad(angle);
          const x1 = 600 + Math.sin(rad) * 210;
          const y1 = -35 + Math.cos(rad) * 140;
          const x2 = 600 + Math.sin(rad) * 610;
          const y2 = -35 + Math.cos(rad) * 395;
          const isHighlighted =
            hoveredTeam !== null &&
            ((idx > 0 && wedgeMeta[idx - 1]?.teamId === hoveredTeam) ||
              (idx < wedgeMeta.length && wedgeMeta[idx]?.teamId === hoveredTeam));
          return (
            <line
              key={angle}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              strokeWidth={isHighlighted ? "2.4" : "1.4"}
              className={
                isHighlighted
                  ? "stroke-blue-500 dark:stroke-sky-400 transition-all duration-200"
                  : "stroke-slate-300 dark:stroke-indigo-400/40 transition-all duration-200"
              }
            />
          );
        })}
      </svg>

      {/* Overlaid Full Specialty Team Labels Along Outer Arc */}
      {wedgeMeta.map((w) => {
        const isHot = hoveredTeam === w.teamId;
        const rot = -w.aMid * 0.28;
        return (
          <div
            key={w.teamId}
            onMouseEnter={() => setHoveredTeam(w.teamId)}
            onMouseLeave={() => setHoveredTeam(null)}
            style={{
              left: `${w.labelX}%`,
              top: `${w.labelY}%`,
              transform: `translate(-50%, -50%) rotate(${rot}deg)`,
            }}
            className={`absolute z-10 cursor-default rounded-full px-2.5 py-0.5 text-[11px] font-semibold tracking-wide transition-all duration-200 sm:text-xs ${
              isHot
                ? "bg-blue-600/15 text-blue-700 dark:bg-sky-400/20 dark:text-sky-300 shadow-sm"
                : "text-slate-700/90 dark:text-indigo-200/85"
            }`}
          >
            {w.label}
          </div>
        );
      })}

      {/* Seated AI Doctor Avatars in Tiered Chairs */}
      {seats.map(({ agent, xPercent, yPercent, scale }) => {
        const rawStatus: AgentSeatStatus =
          mode === "hall"
            ? "idle"
            : activeSpeakerId === agent.id
              ? "running"
              : seatStatuses[agent.id] || "queued";
        const st = STATUS_STYLE[rawStatus];
        const isSelected = selectedAgentId === agent.id || pinnedAgentId === agent.id;
        const seatPx = Math.round(40 * scale);

        return (
          <div
            key={agent.id}
            style={{ left: `${xPercent}%`, top: `${yPercent}%`, zIndex: Math.round(yPercent) }}
            className="absolute -translate-x-1/2 -translate-y-1/2"
            onMouseEnter={() => {
              setHoveredTeam(agent.teamId);
              setHoveredAgentId(agent.id);
            }}
            onMouseLeave={() => {
              setHoveredTeam(null);
              setHoveredAgentId((prev) => (prev === agent.id ? null : prev));
            }}
          >
            {/* Live 2.5D Vertical Spotlight Beam */}
            {mode === "live" && (
              <div
                aria-hidden="true"
                className={`pointer-events-none absolute -top-24 left-1/2 h-28 w-11 -translate-x-1/2 bg-gradient-to-t ${st.beam} blur-[2px] transition-opacity ${
                  rawStatus === "running" ? "opacity-100" : "opacity-75"
                }`}
              />
            )}

            {/* Live Status Mini Pill or Active Waveform Above Speaker */}
            {mode === "live" && rawStatus === "running" && (
              <div className="pointer-events-none absolute -top-6 left-1/2 flex -translate-x-1/2 items-end gap-0.5 rounded-full bg-blue-600 px-2 py-0.5 shadow-md dark:bg-sky-500">
                {[0, 0.15, 0.3, 0.1, 0.25].map((delay, i) => (
                  <span
                    key={i}
                    style={{ animationDelay: `${delay}s` }}
                    className="wave-bar h-2.5 w-0.5 rounded-full bg-white"
                  />
                ))}
              </div>
            )}

            {mode === "live" && rawStatus === "failed" && (
              <span
                title="Agent execution failed — click to retry"
                className="pointer-events-none absolute -right-1 -top-2 z-20 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow"
              >
                <AlertCircle className="h-3 w-3" />
              </span>
            )}

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setPinnedAgentId((prev) => (prev === agent.id ? null : agent.id));
                onSelectAgent?.(agent.id);
              }}
              aria-label={`${agent.displayName}, ${agent.specialty}, ${st.label}`}
              className={`group relative flex flex-col items-center rounded-full p-0.5 transition-transform duration-150 focus-visible:outline-2 focus-visible:outline-sky-400 ${
                isSelected ? "scale-115" : "hover:scale-110"
              }`}
            >
              <DoctorAvatar
                variant={agent.avatarVariant}
                scrubColor={agent.scrubColor}
                hasGlasses={agent.hasGlasses}
                propType={agent.propType}
                size={seatPx}
                seated
              />
              {/* Floor Perspective Glow Ring Under Chair */}
              <span
                className={`-mt-2 h-2.5 w-9 rounded-full border-2 bg-slate-950/15 transition-all dark:bg-slate-950/40 ${st.ring}`}
              />
            </button>
          </div>
        );
      })}

      {/* Edge-Aware Floating Popover Card */}
      <AnimatePresence>
        {activeSeat && (
          <motion.div
            key={activeSeat.agent.id}
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.96 }}
            transition={{ duration: 0.16 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              left: `${activeSeat.xPercent}%`,
              top: `${activeSeat.yPercent}%`,
              transform: `translate(${
                activeSeat.xPercent < 20 ? "0%" : activeSeat.xPercent > 80 ? "-100%" : "-50%"
              }, ${activeSeat.yPercent < 42 ? "26px" : "calc(-100% - 22px)"})`,
            }}
            className="absolute z-50 w-72 rounded-2xl border border-slate-200 bg-white/95 p-3.5 text-left text-slate-900 shadow-2xl backdrop-blur-md dark:border-sky-400/30 dark:bg-slate-900/92 dark:text-slate-100"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800">
                  <DoctorAvatar
                    variant={activeSeat.agent.avatarVariant}
                    scrubColor={activeSeat.agent.scrubColor}
                    hasGlasses={activeSeat.agent.hasGlasses}
                    size={32}
                  />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-bold leading-tight">
                    {activeSeat.agent.displayName}
                  </div>
                  <div className="truncate text-xs font-medium text-blue-600 dark:text-sky-400">
                    {activeSeat.agent.specialty}
                  </div>
                </div>
              </div>
              {pinnedAgentId === activeSeat.agent.id && (
                <button
                  type="button"
                  onClick={() => setPinnedAgentId(null)}
                  aria-label="Close agent popover"
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {mode === "hall" ? (
              <div className="mt-2.5 space-y-1 text-xs">
                <div className="font-semibold uppercase tracking-wider text-[10px] text-slate-400">
                  Personality / Stance
                </div>
                <p className="leading-relaxed text-slate-600 dark:text-slate-300">
                  {activeSeat.agent.personalitySummary}
                </p>
              </div>
            ) : (
              <div className="mt-2.5 space-y-2.5 text-xs">
                <div>
                  <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    <span>Simplified Conclusion</span>
                    <span className="inline-flex items-center gap-1 text-sky-500">
                      <Sparkles className="h-3 w-3" />
                      {seatStatuses[activeSeat.agent.id] || "queued"}
                    </span>
                  </div>
                  <p className="mt-1 line-clamp-3 leading-relaxed text-slate-700 dark:text-slate-300">
                    {seatConclusions[activeSeat.agent.id] ||
                      activeSeat.agent.personalitySummary}
                  </p>
                </div>

                {/* Per-Agent Direct Controls */}
                <div className="flex items-center gap-1.5 pt-1">
                  <button
                    type="button"
                    disabled={!isSimulationRunning}
                    onClick={() => onRunFirst?.(activeSeat.agent.id)}
                    className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-emerald-500/15 px-2 py-1.5 text-[11px] font-semibold text-emerald-700 transition-colors hover:bg-emerald-500/25 disabled:opacity-45 dark:text-emerald-300"
                  >
                    <Play className="h-3 w-3" />
                    Run First
                  </button>
                  <button
                    type="button"
                    onClick={() => onRetryAgent?.(activeSeat.agent.id)}
                    className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-blue-500/15 px-2 py-1.5 text-[11px] font-semibold text-blue-700 transition-colors hover:bg-blue-500/25 dark:text-sky-300"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Retry
                  </button>
                  <button
                    type="button"
                    onClick={() => onPauseAgent?.(activeSeat.agent.id)}
                    className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-slate-500/15 px-2 py-1.5 text-[11px] font-semibold text-slate-700 transition-colors hover:bg-slate-500/25 dark:text-slate-300"
                  >
                    <Pause className="h-3 w-3" />
                    Pause
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Auditorium25D;
