import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Pause,
  Play,
  RotateCcw,
  Square,
} from "lucide-react";
import Auditorium25D from "../components/vmdt/Auditorium25D.js";
import ConfirmDialog from "../components/vmdt/ConfirmDialog.js";
import DoctorAvatar from "../components/vmdt/DoctorAvatar.js";
import type { PreMDTStagingAssessment } from "../types.js";
import type { AgentSeatStatus, VmdtAgentConfig } from "../virtualMdtTypes.js";

interface Page4SimulationProps {
  preMdtStaging?: PreMDTStagingAssessment | null;
  simError?: string | null;

  agents: VmdtAgentConfig[];
  simState: "idle" | "running" | "paused" | "completed" | "stopped";
  activeRound: 1 | 2 | 3 | 4;
  maxRounds: number;
  completedRounds: number[];
  seatStatuses: Record<string, AgentSeatStatus>;
  seatConclusions: Record<string, string>;
  seatArguments: Record<string, string>;
  activeSpeakerId: string | null;
  selectedAgentId: string | null;
  isReadOnly?: boolean;
  onSelectAgent: (id: string | null) => void;
  onSelectRound: (round: 1 | 2 | 3 | 4) => void;
  onStart: () => void;
  onPauseToggle: () => void;
  onRestart: () => void;
  onStop: () => void;
  onRunFirst: (id: string) => void;
  onRetryAgent: (id: string) => void;
  onPauseAgent: (id: string) => void;
  onBackToAudit: () => void;
  onViewConsensus: () => void;
}

const ROUND_LABELS: Record<number, string> = {
  1: "Independent Assessment",
  2: "MDT Debate",
  3: "Adversarial Review",
  4: "Chair Consensus",
};

export const Page4Simulation: React.FC<Page4SimulationProps> = ({
  agents,
  simState,
  activeRound,
  maxRounds,
  completedRounds,
  preMdtStaging,
  simError,
  seatStatuses,
  seatConclusions,
  seatArguments,
  activeSpeakerId,
  selectedAgentId,
  isReadOnly = false,
  onSelectAgent,
  onSelectRound,
  onStart,
  onPauseToggle,
  onRestart,
  onStop,
  onRunFirst,
  onRetryAgent,
  onPauseAgent,
  onBackToAudit,
  onViewConsensus,
}) => {
  const [confirmAction, setConfirmAction] = useState<"restart" | "stop" | null>(null);

  const displayAgentId = selectedAgentId || activeSpeakerId;
  const displayAgent = agents.find((a) => a.id === displayAgentId) || null;
  const displayText =
    (displayAgentId && seatArguments[displayAgentId]) ||
    (displayAgentId && seatConclusions[displayAgentId]) ||
    (displayAgent
      ? `${displayAgent.displayName} (${displayAgent.specialty}) is synthesizing ${ROUND_LABELS[activeRound] || "clinical reasoning"}...`
      : "Select any seated specialist below to inspect their round-by-round reasoning.");

  return (
    <section
      aria-label="Live Tumor Board Simulation"
      className="relative flex flex-1 flex-col overflow-hidden"
    >
      {/* Upper Stage Console (~38% height) */}
      <div className="relative flex h-[38%] min-h-[215px] w-full shrink-0 flex-col justify-between border-b border-slate-200/80 bg-white/55 px-6 py-3 backdrop-blur-md dark:border-sky-400/20 dark:bg-slate-900/60">
        {/* Top Row: Back Link + Round 1-4 Stepper + Playback Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={onBackToAudit}
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              {isReadOnly ? "Back to Archive" : "Back to Audit"}
            </button>

            {/* Round 1 / 2 / 3 / 4 Stepper */}
            <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/90 px-2.5 py-1 shadow-sm dark:border-sky-400/20 dark:bg-slate-900/90">
              {([1, 2, 3, 4] as const)
                .filter((r) => r <= maxRounds)
                .map((roundNum) => {
                  const isDone = completedRounds.includes(roundNum);
                  const isActive = activeRound === roundNum;
                  return (
                    <button
                      key={roundNum}
                      type="button"
                      onClick={() => onSelectRound(roundNum)}
                      title={`Round ${roundNum}: ${ROUND_LABELS[roundNum]}`}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-all ${
                        isActive
                          ? "bg-blue-600 text-white shadow-[0_0_12px_rgba(37,99,235,0.5)] dark:bg-sky-500"
                          : isDone
                            ? "bg-emerald-500/15 text-emerald-700 hover:bg-emerald-500/25 dark:text-emerald-300"
                            : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                      }`}
                    >
                      {roundNum === 1 ? `Round ${roundNum}` : roundNum}
                      {isDone && !isActive && <Check className="h-3 w-3" />}
                    </button>
                  );
                })}
            </div>

            {preMdtStaging && (
              <span
                title={preMdtStaging.summary}
                className="rounded-full border border-sky-400/35 bg-sky-500/10 px-3 py-1 text-[11px] font-semibold text-blue-700 dark:text-sky-300"
              >
                STG-00 Locked: {preMdtStaging.provisional_stage_label}
              </span>
            )}
          </div>

          {/* Right Global Playback Controls */}
          <div className="flex items-center gap-2">
            {simState !== "idle" && !isReadOnly && (
              <>
                {simState !== "completed" && (
                  <button
                    type="button"
                    onClick={onPauseToggle}
                    className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/40 bg-blue-500/15 px-3.5 py-1.5 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-500/25 dark:text-sky-300"
                  >
                    {simState === "paused" ? (
                      <>
                        <Play className="h-3.5 w-3.5" />
                        Resume
                      </>
                    ) : (
                      <>
                        <Pause className="h-3.5 w-3.5" />
                        Pause
                      </>
                    )}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setConfirmAction("restart")}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Restart
                </button>
                {simState !== "completed" && (
                  <button
                    type="button"
                    onClick={() => setConfirmAction("stop")}
                    className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-500/15 px-3.5 py-1.5 text-xs font-semibold text-rose-700 transition-colors hover:bg-rose-500/25 dark:text-rose-300"
                  >
                    <Square className="h-3.5 w-3.5" />
                    Stop
                  </button>
                )}
              </>
            )}

            {(simState === "completed" || isReadOnly) && (
              <button
                type="button"
                onClick={onViewConsensus}
                className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-1.5 text-xs font-semibold text-white shadow-[0_0_18px_rgba(16,185,129,0.45)] hover:from-emerald-400 hover:to-emerald-500"
              >
                <span>View Final Consensus</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Center Stage: Pre-Start OR Live Argument Feed */}
        <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 py-2">
          {simError && (
            <div className="w-full max-w-2xl rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-xs font-medium text-rose-700 dark:text-rose-300">
              {simError}
            </div>
          )}
          <AnimatePresence mode="wait">
            {simState === "idle" && !isReadOnly ? (
              <motion.div
                key="prestart"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className="flex flex-col items-center text-center"
              >
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-sky-400">
                  All Specialists Seated • Stage Verified by STG-00
                </p>
                <h1 className="mt-1 text-2xl font-extrabold text-slate-900 dark:text-white sm:text-3xl">
                  Let&apos;s Start!
                </h1>
                <button
                  type="button"
                  onClick={onStart}
                  className="mt-3 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 px-9 py-2.5 text-sm font-bold tracking-wider text-white shadow-[0_0_26px_rgba(16,185,129,0.55)] transition-transform hover:scale-105 hover:from-emerald-400 hover:to-emerald-500"
                >
                  <Play className="h-4 w-4 fill-current" />
                  START
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="livefeed"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="flex h-full w-full max-w-2xl flex-col rounded-2xl border border-slate-200 bg-white/95 p-3.5 shadow-lg dark:border-sky-400/25 dark:bg-slate-900/85 dark:backdrop-blur-md"
              >
                <div className="flex items-center justify-between gap-2 border-b border-slate-200/80 pb-2 dark:border-slate-800">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {displayAgent && (
                      <DoctorAvatar
                        variant={displayAgent.avatarVariant}
                        scrubColor={displayAgent.scrubColor}
                        hasGlasses={displayAgent.hasGlasses}
                        size={30}
                      />
                    )}
                    <div className="truncate text-xs font-bold text-slate-900 dark:text-slate-100">
                      {displayAgent
                        ? `${displayAgent.displayName} • ${displayAgent.specialty}`
                        : `Round ${activeRound}: ${ROUND_LABELS[activeRound]}`}
                    </div>
                  </div>
                  <span className="shrink-0 text-[11px] font-medium text-blue-600 dark:text-sky-400">
                    Round {activeRound} / {maxRounds}
                  </span>
                </div>

                <div className="mdt-scroll mt-2 flex-1 overflow-y-auto pr-1 text-xs leading-relaxed text-slate-700 dark:text-slate-200">
                  {displayText}
                </div>

                {/* Live Animated Waveform Bar */}
                <div className="mt-2 flex h-4 items-end justify-center gap-1" aria-hidden="true">
                  {Array.from({ length: 28 }).map((_, idx) => (
                    <span
                      key={idx}
                      style={{
                        animationDelay: `${(idx % 7) * 0.11}s`,
                        animationPlayState: simState === "running" ? "running" : "paused",
                      }}
                      className={`wave-bar w-1 rounded-full ${
                        simState === "running"
                          ? "h-3.5 bg-blue-500 dark:bg-sky-400"
                          : "h-1.5 bg-slate-300 dark:bg-slate-700"
                      }`}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Lower Half: 2.5D Live Conference Hall Seating */}
      <Auditorium25D
        mode="live"
        agents={agents}
        seatStatuses={seatStatuses}
        seatConclusions={seatConclusions}
        activeSpeakerId={activeSpeakerId}
        selectedAgentId={selectedAgentId}
        onSelectAgent={onSelectAgent}
        onRunFirst={onRunFirst}
        onRetryAgent={onRetryAgent}
        onPauseAgent={onPauseAgent}
        isSimulationRunning={simState === "running"}
      />

      {/* Native <dialog> Confirmation Modals */}
      <ConfirmDialog
        open={confirmAction === "stop"}
        variant="danger"
        title="Stop simulation and discard all current arguments?"
        message="Stopping will halt the active simulation queue and discard all unfinalized round arguments, returning to the pre-start stage."
        confirmLabel="Stop & Discard"
        onCancel={() => setConfirmAction(null)}
        onConfirm={() => {
          setConfirmAction(null);
          onStop();
        }}
      />
      <ConfirmDialog
        open={confirmAction === "restart"}
        variant="warning"
        title="Restart from Round 1 and discard all current arguments?"
        message="All existing arguments across completed rounds will be cleared and the board will restart from Round 1."
        confirmLabel="Restart from Round 1"
        onCancel={() => setConfirmAction(null)}
        onConfirm={() => {
          setConfirmAction(null);
          onRestart();
        }}
      />
    </section>
  );
};

export default Page4Simulation;
