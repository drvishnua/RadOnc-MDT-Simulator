import React from "react";
import { motion } from "framer-motion";
import Auditorium25D from "../components/vmdt/Auditorium25D.js";
import type { VmdtAgentConfig } from "../virtualMdtTypes.js";

interface Page1HallProps {
  agents: VmdtAgentConfig[];
  onSubmitCase: () => void;
}

export const Page1Hall: React.FC<Page1HallProps> = ({ agents, onSubmitCase }) => {
  return (
    <section
      aria-label="Conference Hall Home"
      className="relative flex flex-1 flex-col overflow-hidden"
    >
      {/* Upper-Center 2.5D Illuminated Stage (~38% height) */}
      <div className="relative flex h-[38%] min-h-[215px] w-full shrink-0 flex-col items-center justify-center overflow-hidden px-6">
        {/* Ambient clinical spotlights from above */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-12 left-1/4 h-64 w-72 -translate-x-1/2 rotate-12 bg-gradient-to-b from-sky-400/25 via-sky-400/5 to-transparent blur-2xl dark:from-sky-400/30"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-12 right-1/4 h-64 w-72 translate-x-1/2 -rotate-12 bg-gradient-to-b from-cyan-400/25 via-indigo-400/5 to-transparent blur-2xl dark:from-indigo-400/25"
        />

        {/* Architectural 2.5D Stage Backdrop & Stepped Side Wings */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-12 bottom-5 top-3 rounded-t-3xl border border-slate-200/90 bg-white/80 shadow-[0_20px_50px_rgba(15,23,42,0.08)] backdrop-blur-md dark:border-sky-400/18 dark:bg-slate-900/72 dark:shadow-[0_20px_60px_rgba(2,6,23,0.7)] sm:inset-x-20"
        >
          {/* Left & Right stepped wing accents */}
          <div className="absolute bottom-2 left-3 h-10 w-16 rounded-md border border-slate-300/60 bg-slate-100/70 dark:border-sky-400/15 dark:bg-slate-800/50" />
          <div className="absolute bottom-2 right-3 h-10 w-16 rounded-md border border-slate-300/60 bg-slate-100/70 dark:border-sky-400/15 dark:bg-slate-800/50" />
          {/* Curved stage lip */}
          <div className="absolute -bottom-2 inset-x-6 h-4 rounded-b-full border-b border-slate-300 bg-gradient-to-b from-slate-100/90 to-slate-200/70 dark:border-sky-400/30 dark:from-slate-800/90 dark:to-slate-950/90" />
        </div>

        {/* Hero Typography */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="relative z-10 -mt-3 text-center"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-600 dark:text-sky-400 sm:text-sm">
            Welcome to
          </p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl lg:text-5xl">
            Virtual Multidisciplinary Tumor Board
          </h1>
          <p className="mx-auto mt-2 max-w-2xl text-xs text-slate-600 dark:text-slate-400 sm:text-sm">
            Collaborative AI-driven case review across specialized oncology disciplines
          </p>
        </motion.div>

        {/* Podium CTA straddling stage lip */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.08 }}
          className="relative z-20 mt-4"
        >
          <button
            type="button"
            onClick={onSubmitCase}
            className="rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 px-8 py-2.5 text-sm font-semibold text-white shadow-[0_0_24px_rgba(16,185,129,0.5)] transition-all hover:-translate-y-0.5 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-[0_0_32px_rgba(16,185,129,0.75)] focus-visible:outline-2 focus-visible:outline-emerald-300 active:translate-y-0"
          >
            Submit Case
          </button>
        </motion.div>
      </div>

      {/* Lower Half: 2.5D Radial Tiered Auditorium Seating (~55%+ height) */}
      <Auditorium25D mode="hall" agents={agents} />
    </section>
  );
};

export default Page1Hall;
