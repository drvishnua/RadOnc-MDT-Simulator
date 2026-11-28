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
}

interface WedgeMeta {
  teamId: TeamId;
  label: string;
  a0: number;
  a1: number;
  aMid: number;
  labelX: number;
  labelY: number;
}

const STATUS_STYLE: Record<
  AgentSeatStatus,
  { ring: string; beam: string; label: string }
> = {
  idle: {
    ring: "border-emerald-400/75 shadow-[0_0_10px_rgba(16,185,129,0.45)] dark:border-sky-400/70 dark:shadow-[0_0_12px_rgba(56,189,248,0.5)]",
    beam: "from-sky-400/0 via-sky-400/10 to-transparent",
    label: "ready",
  },
  queued: {
    ring: "border-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.65)]",
    beam: "from-amber-400/35 via-amber-400/12 to-transparent",
    label: "queued",
  },
  running: {
    ring: "border-blue-500 shadow-[0_0_18px_rgba(59,130,246,0.95)] dark:border-sky-400",
    beam: "from-blue-500/60 via-sky-400/25 to-transparent",
    label: "active speaker",
  },
  completed: {
    ring: "border-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.75)]",
    beam: "from-emerald-400/40 via-emerald-400/12 to-transparent",
    label: "completed",
  },
  failed: {
    ring: "border-rose-500 shadow-[0_0_14px_rgba(239,68,68,0.85)]",
    beam: "from-rose-500/50 via-rose-500/15 to-transparent",
    label: "failed",
  },
  paused: {
    ring: "border-slate-400 shadow-[0_0_10px_rgba(148,163,184,0.45)]",
    beam: "from-slate-400/25 via-slate-400/10 to-transparent",
    label: "paused",
  },
};

// Shared SVG + CSS projection (viewBox 1200 x 440) so seats NEVER cross radial divider lines
const SVG_W = 1200;
const SVG_H = 440;
const CX = 600;
const CY = 10;
const RX_MAX = 590;
const RY_MAX = 365;

function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function projectSvg(angleDeg: number, rNorm: number): { x: number; y: number } {
  const rad = degToRad(angleDeg);
  return {
    x: CX + Math.sin(rad) * RX_MAX * rNorm,
    y: CY + Math.cos(rad) * RY_MAX * rNorm,
  };
}

function describeArc(a0: number, a1: number, rNorm: number): string {
  const p0 = projectSvg(a0, rNorm);
  const p1 = projectSvg(a1, rNorm);
  const rx = RX_MAX * rNorm;
  const ry = RY_MAX * rNorm;
  return `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 0 ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
}

function describeAnnularSector(a0: number, a1: number, rInner: number, rOuter: number): string {
  const p0 = projectSvg(a0, rInner);
  const p1 = projectSvg(a1, rInner);
  const p2 = projectSvg(a1, rOuter);
  const p3 = projectSvg(a0, rOuter);
  const rxIn = RX_MAX * rInner;
  const ryIn = RY_MAX * rInner;
  const rxOut = RX_MAX * rOuter;
  const ryOut = RY_MAX * rOuter;
  return [
    `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)}`,
    `A ${rxIn.toFixed(1)} ${ryIn.toFixed(1)} 0 0 0 ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`,
    `L ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`,
    `A ${rxOut.toFixed(1)} ${ryOut.toFixed(1)} 0 0 1 ${p3.x.toFixed(1)} ${p3.y.toFixed(1)}`,
    "Z",
  ].join(" ");
}

function projectPercent(angleDeg: number, rNorm: number): { xPercent: number; yPercent: number } {
  const { x, y } = projectSvg(angleDeg, rNorm);
  return {
    xPercent: (x / SVG_W) * 100,
    yPercent: (y / SVG_H) * 100,
  };
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

  const { seats, wedgeMeta, dividerAngles, minAngle, maxAngle } = useMemo(() => {
    const teams = DEFAULT_TEAMS;
    const minAngle = -66;
    const maxAngle = 66;
    const totalSpan = maxAngle - minAngle;

    // Proportional weights (minimum weight 4.5 so 3-agent DS/SV wedges still have comfortable width & label room)
    const teamGroups = teams.map((teamId) => ({
      teamId,
      members: activeAgents.filter((a) => a.teamId === teamId),
    }));
    const weights = teamGroups.map((g) => Math.max(4.5, g.members.length + 1.8));
    const totalWeight = weights.reduce((acc, w) => acc + w, 0);

    const computedSeats: PositionedSeat[] = [];
    const meta: WedgeMeta[] = [];
    const dividers: number[] = [minAngle];

    let angleCursor = minAngle;
    teamGroups.forEach(({ teamId, members }, idx) => {
      const wedgeSpan = (weights[idx] / totalWeight) * totalSpan;
      const a0 = angleCursor;
      const a1 = a0 + wedgeSpan;
      const aMid = (a0 + a1) / 2;
      angleCursor = a1;
      dividers.push(a1);

      // Tapered amphitheater rows: fewer seats in narrower inner arc, more in wider outer arc
      const len = members.length;
      const rowCaps =
        len <= 2
          ? [len]
          : len === 3
            ? [1, 2]
            : len <= 6
              ? [2, len - 2]
              : [2, 3, len - 5];

      let seatCursor = 0;
      rowCaps.forEach((cap, rowIndex) => {
        const countInRow = Math.min(cap, Math.max(0, members.length - seatCursor));
        if (countInRow === 0) return;

        const depthT = rowCaps.length === 1 ? 0.5 : rowIndex / (rowCaps.length - 1);
        const rNorm = rowCaps.length === 1 ? 0.56 : 0.36 + depthT * 0.42; // 0.36..0.78 -> well above 0.935 label arc
        const marginDeg = Math.min(wedgeSpan * 0.16, 2.8);
        const usableSpan = Math.max(2, wedgeSpan - marginDeg * 2);

        for (let i = 0; i < countInRow; i += 1) {
          const agent = members[seatCursor];
          seatCursor += 1;
          const frac = countInRow === 1 ? 0.5 : i / (countInRow - 1);
          const seatAngle = a0 + marginDeg + frac * usableSpan;
          const { xPercent, yPercent } = projectPercent(seatAngle, rNorm);
          computedSeats.push({
            agent,
            xPercent,
            yPercent,
            scale: 0.78 + depthT * 0.22,
          });
        }
      });

      const labelPos = projectPercent(aMid, 0.935);
      meta.push({
        teamId,
        label: TEAM_DEFINITIONS[teamId].shortLabel,
        a0,
        a1,
        aMid,
        labelX: labelPos.xPercent,
        labelY: Math.min(95, labelPos.yPercent),
      });
    });

    return { seats: computedSeats, wedgeMeta: meta, dividerAngles: dividers, minAngle, maxAngle };
  }, [activeAgents]);

  const activePopoverId = pinnedAgentId ?? hoveredAgentId;
  const activeSeat = seats.find((s) => s.agent.id === activePopoverId) || null;

  return (
    <div
      className="relative flex-1 w-full overflow-hidden select-none isolate"
      onClick={() => setPinnedAgentId(null)}
    >
      {/* Semi-circular SVG Floor, Perspective Tier Arcs & Exact Wedge Divider Lines */}
      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
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

        <path
          d={describeAnnularSector(minAngle, maxAngle, 0.24, 1.02)}
          className="fill-[url(#floorLight)] dark:fill-[url(#floorDark)] transition-colors duration-300"
        />

        {/* Alternating Wedge Shading & Hover Illumination */}
        {wedgeMeta.map((w, idx) => {
          const isHot = hoveredTeam === w.teamId;
          return (
            <path
              key={w.teamId}
              d={describeAnnularSector(w.a0, w.a1, 0.25, 1.0)}
              className={
                isHot
                  ? "fill-blue-500/[0.08] dark:fill-sky-400/[0.10] transition-colors duration-200"
                  : idx % 2 === 0
                    ? "fill-slate-900/[0.025] dark:fill-white/[0.02] transition-colors duration-200"
                    : "fill-transparent transition-colors duration-200"
              }
            />
          );
        })}

        {/* Stepped Perspective Tier Arcs */}
        {[0.30, 0.47, 0.67, 0.87, 1.0].map((r, idx) => (
          <path
            key={r}
            d={describeArc(minAngle, maxAngle, r)}
            fill="none"
            className="stroke-slate-300/85 dark:stroke-indigo-400/25"
            strokeWidth={idx === 4 ? "2" : "1.2"}
          />
        ))}

        {/* Exact Proportional Radial Wedge Dividers */}
        {dividerAngles.map((angle, idx) => {
          const p1 = projectSvg(angle, 0.25);
          const p2 = projectSvg(angle, 1.0);
          const isHighlighted =
            hoveredTeam !== null &&
            ((idx > 0 && wedgeMeta[idx - 1]?.teamId === hoveredTeam) ||
              (idx < wedgeMeta.length && wedgeMeta[idx]?.teamId === hoveredTeam));
          return (
            <line
              key={`${angle}-${idx}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
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

      {/* Overlaid Specialty Team Labels Along Dedicated Outer Arc */}
      {wedgeMeta.map((w) => {
        const isHot = hoveredTeam === w.teamId;
        const rot = -w.aMid * 0.24;
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
            className={`absolute z-10 cursor-default whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide transition-all duration-200 sm:text-[11px] ${
              isHot
                ? "bg-blue-600/15 text-blue-700 dark:bg-sky-400/20 dark:text-sky-300 shadow-sm"
                : "text-slate-700/90 dark:text-indigo-200/85"
            }`}
          >
            {w.label}
          </div>
        );
      })}

      {/* Seated AI Doctor Avatars (Strictly bounded z-20 so overlay popover z-[999] is ALWAYS in front) */}
      {seats.map(({ agent, xPercent, yPercent, scale }) => {
        const rawStatus: AgentSeatStatus =
          mode === "hall"
            ? "idle"
            : activeSpeakerId === agent.id
              ? "running"
              : seatStatuses[agent.id] || "queued";
        const st = STATUS_STYLE[rawStatus];
        const isSelected = selectedAgentId === agent.id || pinnedAgentId === agent.id;
        const seatPx = Math.round(44 * scale);

        return (
          <div
            key={agent.id}
            style={{
              left: `${xPercent}%`,
              top: `${yPercent}%`,
              zIndex: isSelected ? 40 : Math.min(35, Math.max(12, Math.round(yPercent / 3))),
            }}
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
            {mode === "live" && (
              <div
                aria-hidden="true"
                className={`pointer-events-none absolute -top-20 left-1/2 h-24 w-10 -translate-x-1/2 bg-gradient-to-t ${st.beam} blur-[2px] transition-opacity ${
                  rawStatus === "running" ? "opacity-100" : "opacity-75"
                }`}
              />
            )}

            {mode === "live" && rawStatus === "running" && (
              <div className="pointer-events-none absolute -top-5 left-1/2 flex -translate-x-1/2 items-end gap-0.5 rounded-full bg-blue-600 px-1.5 py-0.5 shadow-md dark:bg-sky-500">
                {[0, 0.15, 0.3, 0.1, 0.25].map((delay, i) => (
                  <span
                    key={i}
                    style={{ animationDelay: `${delay}s` }}
                    className="wave-bar h-2 w-0.5 rounded-full bg-white"
                  />
                ))}
              </div>
            )}

            {mode === "live" && rawStatus === "failed" && (
              <span
                title="Agent execution failed — click to retry"
                className="pointer-events-none absolute -right-1 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow"
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
              <span
                className={`-mt-2 h-2 w-8 rounded-full border-2 bg-slate-950/15 transition-all dark:bg-slate-950/40 ${st.ring}`}
              />
            </button>
          </div>
        );
      })}

      {/* Top-Level Edge-Aware Floating Popover (z-[999] ALWAYS above every seated agent) */}
      <AnimatePresence>
        {activeSeat && (
          <motion.div
            key={activeSeat.agent.id}
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.96 }}
            transition={{ duration: 0.14 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              left: `${activeSeat.xPercent}%`,
              top: `${activeSeat.yPercent}%`,
              transform: `translate(${
                activeSeat.xPercent < 22 ? "0%" : activeSeat.xPercent > 78 ? "-100%" : "-50%"
              }, ${activeSeat.yPercent < 42 ? "24px" : "calc(-100% - 20px)"})`,
            }}
            className="pointer-events-auto absolute z-[999] w-80 rounded-2xl border border-slate-200 bg-white/98 p-3.5 text-left text-slate-900 shadow-2xl backdrop-blur-md dark:border-sky-400/35 dark:bg-slate-900/96 dark:text-slate-100"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800">
                  <DoctorAvatar
                    variant={activeSeat.agent.avatarVariant}
                    scrubColor={activeSeat.agent.scrubColor}
                    hasGlasses={activeSeat.agent.hasGlasses}
                    size={32}
                  />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold leading-snug">
                    {activeSeat.agent.displayName}
                  </div>
                  <div className="truncate text-[11px] font-medium text-blue-600 dark:text-sky-400">
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
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  Role Mandate &amp; Stance
                </div>
                <p className="line-clamp-3 leading-relaxed text-slate-600 dark:text-slate-300">
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
