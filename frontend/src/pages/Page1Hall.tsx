import React from "react";
import { motion } from "framer-motion";
import Auditorium3D from "../components/vmdt/Auditorium3D.js";
import type { CameraPanMode, VmdtAgentConfig } from "../virtualMdtTypes.js";

interface Page1HallProps {
  agents: VmdtAgentConfig[];
  cameraPanMode?: CameraPanMode;
  hasActiveRun?: boolean;
  activeRunRound?: number;
  activeRunPaused?: boolean;
  onReturnToActiveRun?: () => void;
  onSubmitCase: () => void;
}

export const Page1Hall: React.FC<Page1HallProps> = ({
  agents,
  cameraPanMode = "auto",
  hasActiveRun = false,
  activeRunRound = 1,
  activeRunPaused = false,
  onReturnToActiveRun,
  onSubmitCase,
}) => {
  return (
    <section
      aria-label="Conference Hall Home"
      className="relative flex flex-1 flex-col overflow-hidden"
    >
      {/* Full-Viewport Seamless 3D Auditorium (Curved Stage + Stepped Amphitheater + 49 Seated Clinicians) */}
      <div className="absolute inset-0 z-0">
        <Auditorium3D mode="hall" agents={agents} cameraPanMode={cameraPanMode} />
      </div>

      {/* Upper-Center Hero Typography & Podium CTA Floating Over 3D Stage */}
      <div className="pointer-events-none relative z-10 flex h-[37%] min-h-[205px] w-full shrink-0 flex-col items-center justify-center px-6 pt-2">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center drop-shadow-[0_2px_12px_rgba(2,6,23,0.45)] dark:drop-shadow-[0_4px_18px_rgba(2,6,23,0.85)]"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-600 dark:text-sky-400 sm:text-sm">
            Welcome to
          </p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl lg:text-5xl">
            Virtual Multidisciplinary Tumor Board
          </h1>
          <p className="mx-auto mt-1.5 max-w-2xl text-xs font-medium text-slate-700 dark:text-slate-300 sm:text-sm">
            Collaborative AI-driven case review across specialized oncology disciplines
          </p>
        </motion.div>

        {/* Podium CTA Positioned Above Curved 3D Stage Lip */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.08 }}
          className="pointer-events-auto mt-3.5 flex flex-wrap items-center justify-center gap-3"
        >
          {hasActiveRun && onReturnToActiveRun && (
            <button
              type="button"
              onClick={onReturnToActiveRun}
              className={`inline-flex items-center gap-2 rounded-full px-6 py-2.5 text-sm font-semibold text-white transition-all hover:-translate-y-0.5 focus-visible:outline-2 focus-visible:outline-sky-300 active:translate-y-0 ${
                activeRunPaused
                  ? "bg-gradient-to-r from-amber-500 to-amber-600 shadow-[0_0_24px_rgba(245,158,11,0.5)] hover:from-amber-400 hover:to-amber-500"
                  : "bg-gradient-to-r from-blue-600 to-sky-500 shadow-[0_0_24px_rgba(56,189,248,0.55)] hover:from-blue-500 hover:to-sky-400"
              }`}
            >
              <span className="h-2 w-2 animate-pulse rounded-full bg-white" aria-hidden="true" />
              {activeRunPaused
                ? `Return to Paused Run (R${activeRunRound})`
                : `Return to Active Run (R${activeRunRound})`}
            </button>
          )}
          <button
            type="button"
            onClick={onSubmitCase}
            className="rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 px-8 py-2.5 text-sm font-semibold text-white shadow-[0_0_26px_rgba(16,185,129,0.55)] transition-all hover:-translate-y-0.5 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-[0_0_36px_rgba(16,185,129,0.8)] focus-visible:outline-2 focus-visible:outline-emerald-300 active:translate-y-0"
          >
            Submit Case
          </button>
        </motion.div>
      </div>
    </section>
  );
};

export default Page1Hall;
