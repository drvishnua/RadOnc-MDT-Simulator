import React, { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { IntakeHostIllustration } from "../components/vmdt/DoctorAvatar.js";
import type { AuditFinding } from "../virtualMdtTypes.js";

interface Page3AuditProps {
  findings: AuditFinding[];
  isScanning: boolean;
  onBackToIntake: () => void;
  onReAudit: () => void;
  onResolveFinding: (id: string, fieldKey: string, value: string, markNA?: boolean) => void;
  onConveneBoard: () => void;
}

export const Page3Audit: React.FC<Page3AuditProps> = ({
  findings,
  isScanning,
  onBackToIntake,
  onReAudit,
  onResolveFinding,
  onConveneBoard,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(findings[0]?.id ?? null);
  const [draftInputs, setDraftInputs] = useState<Record<string, string>>({});

  const unresolvedFindings = useMemo(
    () => findings.filter((f) => !f.resolvedValue && !f.markedNA),
    [findings],
  );
  const unresolvedCount = unresolvedFindings.length;
  const criticalRemaining = unresolvedFindings.some((f) => f.severity === "critical");

  const speechBubbleText = isScanning
    ? "Let me audit your case first..."
    : unresolvedCount === 0
      ? "Everything looks complete! Ready to convene the board."
      : `I found ${unresolvedCount} item${unresolvedCount > 1 ? "s" : ""} that will sharpen the board's review.`;

  return (
    <section
      aria-label="Case Audit and Readiness Check"
      className="flex flex-1 flex-col overflow-hidden"
    >
      {/* Sub-header Breadcrumb */}
      <div className="flex shrink-0 items-center justify-between px-6 py-3">
        <button
          type="button"
          onClick={onBackToIntake}
          className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Case Details
        </button>
      </div>

      {/* Two-Column Main Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-6 px-6 pb-5">
        {/* Left Column (~42%): Intake Host in Audit Mode */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
          className="col-span-12 flex min-h-0 flex-col items-center justify-end lg:col-span-5"
        >
          <div className="relative mb-4 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-lg dark:border-sky-400/25 dark:bg-slate-900/85 dark:backdrop-blur-md">
            <AnimatePresence mode="wait">
              <motion.p
                key={speechBubbleText}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.16 }}
                className="text-sm font-medium leading-relaxed text-slate-800 dark:text-slate-100"
              >
                {speechBubbleText}
              </motion.p>
            </AnimatePresence>
          </div>
          <IntakeHostIllustration mode="audit" className="min-h-0 flex-1 w-full" />
        </motion.div>

        {/* Right Column (~58%): Interactive Audit Card */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
          className="col-span-12 flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-7"
        >
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
                Here are the things missing
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Pre-MDT completeness audit across active oncology disciplines & STG-00 staging checks
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                unresolvedCount === 0
                  ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                  : "bg-amber-500/15 text-amber-700 dark:text-amber-300"
              }`}
            >
              {unresolvedCount === 0 ? "All Resolved" : `${unresolvedCount} Pending`}
            </span>
          </div>

          <div className="mdt-scroll flex-1 space-y-3 overflow-y-auto px-6 py-4">
            {isScanning ? (
              <div className="space-y-3">
                {[0, 1, 2].map((idx) => (
                  <div
                    key={idx}
                    className="h-20 animate-pulse rounded-xl border border-slate-200 bg-slate-100/80 dark:border-sky-400/15 dark:bg-slate-800/60"
                  />
                ))}
              </div>
            ) : findings.length === 0 || unresolvedCount === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-8 text-center"
              >
                <ShieldCheck className="h-12 w-12 text-emerald-500" />
                <h2 className="mt-3 text-lg font-bold text-emerald-700 dark:text-emerald-300">
                  Case Ready for Tumor Board
                </h2>
                <p className="mt-1 max-w-md text-xs text-slate-600 dark:text-slate-300">
                  All critical and recommended clinical fields have been verified or marked N/A. Click Convene Tumor Board below to open the live simulation hall.
                </p>
              </motion.div>
            ) : (
              findings.map((finding, idx) => {
                const isResolved = Boolean(finding.resolvedValue || finding.markedNA);
                const isExpanded = expandedId === finding.id && !isResolved;
                const draftVal = draftInputs[finding.id] ?? finding.resolvedValue ?? "";

                return (
                  <motion.div
                    key={finding.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`overflow-hidden rounded-xl border transition-colors ${
                      isResolved
                        ? "border-emerald-500/40 bg-emerald-500/5"
                        : isExpanded
                          ? "border-blue-500/60 bg-slate-50/90 shadow-sm dark:border-sky-400/60 dark:bg-slate-800/60"
                          : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedId((prev) => (prev === finding.id ? null : finding.id))}
                      className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
                    >
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                              finding.severity === "critical"
                                ? "bg-rose-500/15 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300"
                                : "bg-blue-500/15 text-blue-700 dark:bg-sky-500/20 dark:text-sky-300"
                            }`}
                          >
                            {finding.severity === "critical" ? "Critical" : "Recommended"}
                          </span>
                          <span className="rounded-full border border-slate-300 bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
                            {finding.specialty}
                          </span>
                          {isResolved && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              {finding.markedNA ? "Marked N/A" : "Provided"}
                            </span>
                          )}
                        </div>
                        <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {finding.title}
                        </div>
                        {!isExpanded && (
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            {finding.resolvedValue ? `Supplied: ${finding.resolvedValue}` : finding.description}
                          </p>
                        )}
                      </div>
                      {!isResolved && (
                        <span className="text-slate-400">
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </span>
                      )}
                    </button>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.18 }}
                          className="border-t border-slate-200 px-4 py-3 dark:border-slate-700/80"
                        >
                          <p className="mb-2.5 text-xs text-slate-600 dark:text-slate-300">
                            {finding.description}
                          </p>
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={draftVal}
                              onChange={(e) =>
                                setDraftInputs((prev) => ({ ...prev, [finding.id]: e.target.value }))
                              }
                              placeholder={finding.placeholder}
                              className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-sky-400"
                            />
                            <button
                              type="button"
                              onClick={() => {
                                onResolveFinding(finding.id, finding.fieldKey, draftVal.trim() || "Provided", false);
                                setExpandedId(null);
                              }}
                              className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                onResolveFinding(finding.id, finding.fieldKey, "", true);
                                setExpandedId(null);
                              }}
                              className="rounded-xl border border-slate-300 bg-slate-100 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            >
                              Mark N/A
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })
            )}
          </div>

          {/* Sticky Bottom Action Bar */}
          <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-slate-200 bg-slate-50/90 px-6 py-3.5 rounded-b-2xl dark:border-slate-800 dark:bg-slate-900/90">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onBackToIntake}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                Edit Case
              </button>
              <button
                type="button"
                onClick={onReAudit}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isScanning ? "animate-spin" : ""}`} />
                Re-Audit
              </button>
            </div>
            <button
              type="button"
              onClick={onConveneBoard}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all hover:from-emerald-400 hover:to-emerald-500"
            >
              <span>{criticalRemaining ? "Proceed Anyway" : "Convene Tumor Board"}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Page3Audit;
