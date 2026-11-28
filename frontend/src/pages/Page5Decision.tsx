import React, { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Check, Copy, FileDown, PlusCircle, Sparkles } from "lucide-react";
import type { ArchivedCase } from "../virtualMdtTypes.js";

interface Page5DecisionProps {
  caseRecord: ArchivedCase;
  onBackToSimulation: () => void;
  onExportPdf: () => void;
  onStartNewCase: () => void;
}

export const Page5Decision: React.FC<Page5DecisionProps> = ({
  caseRecord,
  onBackToSimulation,
  onExportPdf,
  onStartNewCase,
}) => {
  const [synthesizing, setSynthesizing] = useState(true);
  const [showWeighting, setShowWeighting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setSynthesizing(true);
    const t = window.setTimeout(() => setSynthesizing(false), 1100);
    return () => window.clearTimeout(t);
  }, [caseRecord.id]);

  const handleCopyReport = async () => {
    const text = [
      `Virtual MDT Final Consensus — ${caseRecord.caseCode}`,
      `Patient: ${caseRecord.patientName} (${caseRecord.ageSex}) | ${caseRecord.diagnosis} • ${caseRecord.stage}`,
      `Chair Consensus: ${caseRecord.consensusPercent}%`,
      "",
      `Primary Recommendation:\n${caseRecord.primaryRecommendation}`,
      "",
      `Clinical Rationale:\n${caseRecord.clinicalRationale.map((r) => `- ${r}`).join("\n")}`,
      "",
      `Follow-Up Plan & Next Steps:\n${caseRecord.followUpPlan.map((f) => `- ${f}`).join("\n")}`,
      "",
      `Radiation Plan: ${caseRecord.radiationPlan}`,
      `Systemic Therapy: ${caseRecord.systemicPlan}`,
      `Surgical Plan: ${caseRecord.surgicalPlan}`,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // ignore clipboard permission restriction in headless mode
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - Math.min(100, Math.max(0, caseRecord.consensusPercent)) / 100);

  return (
    <section
      aria-label="Final Decision and MDT Chair Consensus"
      className="flex flex-1 flex-col overflow-hidden"
    >
      {/* Sub-Header Bar */}
      <div className="flex shrink-0 items-center justify-between px-6 py-3">
        <button
          type="button"
          onClick={onBackToSimulation}
          className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Simulation
        </button>

        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/35 bg-emerald-500/12 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
          <Check className="h-3.5 w-3.5" />
          Saved to Past Cases
        </span>
      </div>

      {/* Two-Column Main Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-6 px-6 pb-5">
        {/* Left Column (~36%): Interactive 2.5D Winged Caduceus on Pedestal */}
        <div className="col-span-12 flex flex-col items-center justify-center lg:col-span-4">
          <div
            className="relative flex flex-col items-center"
            onMouseEnter={() => setShowWeighting(true)}
            onMouseLeave={() => setShowWeighting(false)}
          >
            {/* Light Rays & Halo */}
            <div
              aria-hidden="true"
              className={`pointer-events-none absolute -inset-8 rounded-full bg-gradient-to-t from-sky-400/25 via-amber-300/15 to-transparent blur-3xl transition-opacity duration-500 ${
                synthesizing ? "animate-pulse opacity-100" : "opacity-80"
              }`}
            />

            <motion.button
              type="button"
              whileHover={{ scale: 1.03, rotateY: 4 }}
              onClick={() => setShowWeighting((prev) => !prev)}
              aria-expanded={showWeighting}
              aria-label="Inspect MDT Chair specialty weighting"
              className="relative z-10 cursor-pointer rounded-3xl p-2 focus-visible:outline-2 focus-visible:outline-sky-400"
            >
              <svg viewBox="0 0 260 280" className="h-64 w-auto drop-shadow-2xl" fill="none">
                <defs>
                  <linearGradient id="wingGrad" x1="20" y1="40" x2="240" y2="120" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#38BDF8" />
                    <stop offset="50%" stopColor="#E2E8F0" />
                    <stop offset="100%" stopColor="#F59E0B" />
                  </linearGradient>
                  <linearGradient id="pedestalGrad" x1="50" y1="220" x2="210" y2="265" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#0284C7" stopOpacity="0.45" />
                    <stop offset="50%" stopColor="#38BDF8" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#1E293B" stopOpacity="0.9" />
                  </linearGradient>
                </defs>

                {/* Pedestal Rings */}
                <ellipse cx="130" cy="242" rx="88" ry="20" className="fill-slate-300/60 dark:fill-slate-800/90 stroke-sky-400/50" strokeWidth="2" />
                <ellipse cx="130" cy="233" rx="68" ry="14" fill="url(#pedestalGrad)" stroke="#38BDF8" strokeWidth="1.8" />
                <ellipse cx="130" cy="226" rx="48" ry="9" className="fill-sky-400/30 stroke-sky-300" strokeWidth="1.2" />

                {/* Wings */}
                <path
                  d="M124 72 C92 42, 42 46, 22 68 C52 72, 82 82, 114 96 C84 92, 54 92, 34 102 C64 106, 94 108, 120 112 Z"
                  fill="url(#wingGrad)"
                  opacity="0.95"
                />
                <path
                  d="M136 72 C168 42, 218 46, 238 68 C208 72, 178 82, 146 96 C176 92, 206 92, 226 102 C196 106, 166 108, 140 112 Z"
                  fill="url(#wingGrad)"
                  opacity="0.95"
                />

                {/* Central Staff & Orb */}
                <line x1="130" y1="54" x2="130" y2="225" stroke="#E2E8F0" strokeWidth="7" strokeLinecap="round" />
                <circle cx="130" cy="48" r="11" fill="#FBBF24" stroke="#FEF08A" strokeWidth="2" />

                {/* Intertwined Serpents */}
                <path
                  d="M130 92 C98 104, 162 126, 130 144 C98 162, 158 184, 130 205"
                  stroke="#38BDF8"
                  strokeWidth="5.5"
                  strokeLinecap="round"
                  fill="none"
                />
                <path
                  d="M130 92 C162 104, 98 126, 130 144 C162 162, 102 184, 130 205"
                  stroke="#F59E0B"
                  strokeWidth="5.5"
                  strokeLinecap="round"
                  fill="none"
                />
              </svg>
            </motion.button>

            <h2 className="mt-1 text-base font-bold text-slate-900 dark:text-slate-100">
              MDT Chair Consensus
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Hover or click emblem to inspect specialty weighting
            </p>

            {/* Specialty Weighting Popover */}
            <AnimatePresence>
              {showWeighting && (
                <motion.div
                  initial={{ opacity: 0, y: 6, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.96 }}
                  className="absolute -right-6 bottom-12 z-30 w-64 rounded-2xl border border-slate-200 bg-white/95 p-4 text-left shadow-2xl backdrop-blur-md dark:border-sky-400/30 dark:bg-slate-900/92"
                >
                  <div className="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-900 dark:text-slate-100">
                    <Sparkles className="h-3.5 w-3.5 text-blue-600 dark:text-sky-400" />
                    Specialty Weighting
                  </div>
                  <div className="space-y-2">
                    {caseRecord.specialtyWeighting.map((w) => (
                      <div key={w.team} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-700 dark:text-slate-200">{w.team}</span>
                          <span className="font-semibold text-slate-900 dark:text-white">{w.weight}%</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                          <div
                            style={{ width: `${w.weight}%`, backgroundColor: w.color }}
                            className="h-full rounded-full"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Right Column (~64%): Final Decision Report & 4-Card Breakdown */}
        <div className="col-span-12 flex min-h-0 flex-col lg:col-span-8">
          <div className="mb-2 flex items-baseline justify-between">
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              Final Decision
            </h1>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {caseRecord.caseCode} • {caseRecord.patientName} ({caseRecord.ageSex}) • {caseRecord.stage}
            </span>
          </div>

          {/* Main Consensus Report Card (Internal Scroll) */}
          <div className="mdt-scroll flex-1 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-lg dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md">
            {synthesizing ? (
              <div className="space-y-4">
                <div className="h-6 w-1/3 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800" />
                <div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/70" />
                <div className="h-28 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/70" />
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.25 }}
                className="space-y-4 text-sm"
              >
                <div>
                  <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-sky-400">
                    Primary Recommendation
                  </h2>
                  <p className="mt-1 font-semibold leading-relaxed text-slate-900 dark:text-slate-50">
                    {caseRecord.primaryRecommendation}
                  </p>
                </div>

                <div className="border-t border-slate-200/80 pt-3 dark:border-slate-800">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-sky-400">
                    Clinical Rationale
                  </h2>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                    {caseRecord.clinicalRationale.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>

                {caseRecord.dissentingViews.length > 0 && (
                  <div className="border-t border-slate-200/80 pt-3 dark:border-slate-800">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                      Dissenting / Alternative Views
                    </h2>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                      {caseRecord.dissentingViews.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="border-t border-slate-200/80 pt-3 dark:border-slate-800">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    Follow-Up Plan & Next Steps
                  </h2>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                    {caseRecord.followUpPlan.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            )}
          </div>

          {/* 4-Column Summary Grid */}
          <div className="mt-3 grid shrink-0 grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-sky-400/20 dark:bg-slate-900/75">
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100">Radiation Plan</div>
              <p className="mt-1 line-clamp-3 text-[11px] leading-snug text-slate-600 dark:text-slate-400">
                {caseRecord.radiationPlan}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-sky-400/20 dark:bg-slate-900/75">
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100">Systemic Therapy</div>
              <p className="mt-1 line-clamp-3 text-[11px] leading-snug text-slate-600 dark:text-slate-400">
                {caseRecord.systemicPlan}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-sky-400/20 dark:bg-slate-900/75">
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100">Surgical Plan</div>
              <p className="mt-1 line-clamp-3 text-[11px] leading-snug text-slate-600 dark:text-slate-400">
                {caseRecord.surgicalPlan}
              </p>
            </div>
            <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-sky-400/20 dark:bg-slate-900/75">
              <svg viewBox="0 0 48 48" className="h-11 w-11 shrink-0 -rotate-90">
                <circle cx="24" cy="24" r={radius} className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="4" fill="none" />
                <circle
                  cx="24"
                  cy="24"
                  r={radius}
                  stroke="#10B981"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  fill="none"
                />
              </svg>
              <div className="min-w-0">
                <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                  {caseRecord.consensusPercent}% Consensus
                </div>
                <p className="line-clamp-2 text-[10px] text-slate-500 dark:text-slate-400">
                  {caseRecord.evidenceSummary}
                </p>
              </div>
            </div>
          </div>

          {/* Bottom Action Bar */}
          <div className="mt-3 flex shrink-0 items-center justify-end gap-3">
            <button
              type="button"
              onClick={onExportPdf}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <FileDown className="h-3.5 w-3.5" />
              Export PDF
            </button>
            <button
              type="button"
              onClick={handleCopyReport}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? "Copied ✓" : "Copy Report"}
            </button>
            <button
              type="button"
              onClick={onStartNewCase}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2 text-xs font-semibold text-white shadow-[0_0_20px_rgba(16,185,129,0.4)] hover:from-emerald-400 hover:to-emerald-500"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              Start New Case
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Page5Decision;
