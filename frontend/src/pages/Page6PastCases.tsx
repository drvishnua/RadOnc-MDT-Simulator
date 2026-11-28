import React, { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  Copy,
  FileDown,
  FileText,
  History,
  Search,
  Trash2,
  X,
} from "lucide-react";
import ConfirmDialog from "../components/vmdt/ConfirmDialog.js";
import type { ArchivedCase } from "../virtualMdtTypes.js";

interface Page6PastCasesProps {
  cases: ArchivedCase[];
  onBackToHall: () => void;
  onOpenDecision: (c: ArchivedCase) => void;
  onReviewTranscript: (c: ArchivedCase) => void;
  onCloneRerun: (c: ArchivedCase) => void;
  onExportPdf: (c: ArchivedCase) => void;
  onDeleteCase: (id: string) => void;
}

export const Page6PastCases: React.FC<Page6PastCasesProps> = ({
  cases,
  onBackToHall,
  onOpenDecision,
  onReviewTranscript,
  onCloneRerun,
  onExportPdf,
  onDeleteCase,
}) => {
  const [search, setSearch] = useState("");
  const [siteFilter, setSiteFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [minConsensus, setMinConsensus] = useState<number>(0);
  const [dateOrder, setDateOrder] = useState<"desc" | "asc">("desc");
  const [selectedId, setSelectedId] = useState<string | null>(cases[0]?.id ?? null);
  const [deleteTarget, setDeleteTarget] = useState<ArchivedCase | null>(null);

  const siteOptions = useMemo(
    () => Array.from(new Set(cases.map((c) => c.primarySite))).sort(),
    [cases],
  );

  const filteredCases = useMemo(() => {
    const q = search.trim().toLowerCase();
    return cases
      .filter((c) => {
        const matchesQuery =
          !q ||
          c.caseCode.toLowerCase().includes(q) ||
          c.patientName.toLowerCase().includes(q) ||
          c.diagnosis.toLowerCase().includes(q) ||
          c.primarySite.toLowerCase().includes(q);
        const matchesSite = !siteFilter || c.primarySite === siteFilter;
        const matchesStatus = !statusFilter || c.status === statusFilter;
        const matchesConsensus = c.consensusPercent >= minConsensus;
        return matchesQuery && matchesSite && matchesStatus && matchesConsensus;
      })
      .sort((a, b) =>
        dateOrder === "desc"
          ? b.createdAt.localeCompare(a.createdAt)
          : a.createdAt.localeCompare(b.createdAt),
      );
  }, [cases, search, siteFilter, statusFilter, minConsensus, dateOrder]);

  const selectedCase =
    filteredCases.find((c) => c.id === selectedId) ?? filteredCases[0] ?? null;

  const hasActiveFilters = Boolean(search || siteFilter || statusFilter || minConsensus > 0);

  const handleListKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!filteredCases.length) return;
    const idx = filteredCases.findIndex((c) => c.id === selectedCase?.id);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = filteredCases[Math.min(filteredCases.length - 1, Math.max(0, idx) + 1)];
      if (next) setSelectedId(next.id);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = filteredCases[Math.max(0, (idx < 0 ? 0 : idx) - 1)];
      if (prev) setSelectedId(prev.id);
    }
  };

  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = selectedCase
    ? circumference * (1 - selectedCase.consensusPercent / 100)
    : circumference;

  return (
    <section
      aria-label="Past Cases Archive"
      className="flex flex-1 flex-col overflow-hidden"
    >
      {/* Toolbar & Filter Strip */}
      <div className="flex shrink-0 flex-wrap items-center gap-2.5 px-6 py-3">
        <button
          type="button"
          onClick={onBackToHall}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Hall
        </button>

        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Case ID, patient name, diagnosis..."
            className="w-full rounded-xl border border-slate-300 bg-white py-1.5 pl-9 pr-3 text-xs text-slate-900 focus:border-blue-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-sky-400"
          />
        </div>

        <select
          aria-label="Filter by Tumor Site"
          value={siteFilter}
          onChange={(e) => setSiteFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          <option value="">Tumor Site: All</option>
          {siteOptions.map((site) => (
            <option key={site} value={site}>
              {site}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter by Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          <option value="">Status: All</option>
          <option value="Completed">Completed</option>
          <option value="Stopped Early">Stopped Early</option>
        </select>

        <select
          aria-label="Filter by Minimum Consensus"
          value={minConsensus}
          onChange={(e) => setMinConsensus(Number(e.target.value))}
          className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          <option value={0}>Consensus %: Any</option>
          <option value={75}>≥ 75%</option>
          <option value={85}>≥ 85%</option>
          <option value={90}>≥ 90%</option>
        </select>

        <select
          aria-label="Sort by Date"
          value={dateOrder}
          onChange={(e) => setDateOrder(e.target.value as "asc" | "desc")}
          className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          <option value="desc">Date: Newest</option>
          <option value="asc">Date: Oldest</option>
        </select>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={() => {
              setSearch("");
              setSiteFilter("");
              setStatusFilter("");
              setMinConsensus(0);
            }}
            className="inline-flex items-center gap-1 rounded-xl border border-slate-300 bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
          >
            <X className="h-3 w-3" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Split Master-Detail Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-5 px-6 pb-5">
        {/* Left (~42%): Scrollable Master List */}
        <div
          tabIndex={0}
          onKeyDown={handleListKeyDown}
          aria-label="Archived cases list"
          className="mdt-scroll col-span-12 space-y-3 overflow-y-auto pr-1 focus:outline-none lg:col-span-5"
        >
          {filteredCases.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white/80 p-8 text-center dark:border-slate-800 dark:bg-slate-900/60">
              <History className="h-10 w-10 text-slate-400" />
              <p className="mt-2 text-sm font-semibold">No matching cases found</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Adjust search filters or convene a new tumor board simulation.
              </p>
            </div>
          ) : (
            filteredCases.map((c) => {
              const isSelected = selectedCase?.id === c.id;
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition-all ${
                    isSelected
                      ? "border-blue-600 bg-white shadow-[0_0_20px_rgba(37,99,235,0.18)] dark:border-sky-400 dark:bg-slate-900/90 dark:shadow-[0_0_22px_rgba(56,189,248,0.22)]"
                      : "border-slate-200 bg-white/90 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/65 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      {c.caseCode}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                        c.status === "Completed"
                          ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                          : "bg-amber-500/15 text-amber-700 dark:text-amber-300"
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>
                  <div className="mt-1 text-xs font-semibold text-slate-700 dark:text-slate-200">
                    {c.patientName} • {c.ageSex}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                    {c.diagnosis} • {c.stage}
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                    {c.primaryRecommendation}
                  </p>
                </button>
              );
            })
          )}
        </div>

        {/* Right (~58%): Selected Case Detail Preview */}
        <div className="col-span-12 flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-7">
          {selectedCase ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedCase.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="flex min-h-0 flex-1 flex-col"
              >
                {/* Preview Header */}
                <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-4 dark:border-slate-800">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h1 className="text-lg font-extrabold text-slate-900 dark:text-white">
                        {selectedCase.caseCode} • {selectedCase.patientName}, {selectedCase.ageSex}
                      </h1>
                      <span className="rounded-full border border-slate-300 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                        {selectedCase.stage}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {selectedCase.createdAt} • {selectedCase.primarySite} • {selectedCase.diagnosis}
                    </p>
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {selectedCase.participatingAgents.map((ag) => (
                        <span
                          key={ag.id}
                          className="rounded-full border border-sky-500/25 bg-sky-500/10 px-2.5 py-0.5 text-[11px] font-medium text-blue-700 dark:text-sky-300"
                        >
                          {ag.name} ({ag.specialty})
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Circular Consensus Progress Ring */}
                  <div className="flex shrink-0 flex-col items-center">
                    <div className="relative flex h-16 w-16 items-center justify-center">
                      <svg viewBox="0 0 64 64" className="h-16 w-16 -rotate-90">
                        <circle
                          cx="32"
                          cy="32"
                          r={radius}
                          className="stroke-slate-200 dark:stroke-slate-800"
                          strokeWidth="5"
                          fill="none"
                        />
                        <circle
                          cx="32"
                          cy="32"
                          r={radius}
                          stroke="#10B981"
                          strokeWidth="5"
                          strokeLinecap="round"
                          strokeDasharray={circumference}
                          strokeDashoffset={strokeDashoffset}
                          fill="none"
                        />
                      </svg>
                      <span className="absolute text-xs font-bold text-slate-900 dark:text-white">
                        {selectedCase.consensusPercent}%
                      </span>
                    </div>
                    <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400">
                      Consensus
                    </span>
                  </div>
                </div>

                {/* Scrollable Body */}
                <div className="mdt-scroll flex-1 space-y-4 overflow-y-auto px-6 py-4 text-sm">
                  <div>
                    <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-sky-400">
                      MDT Recommendation
                    </h2>
                    <p className="mt-1 text-sm leading-relaxed text-slate-800 dark:text-slate-100">
                      {selectedCase.primaryRecommendation}
                    </p>
                  </div>

                  <div>
                    <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-sky-400">
                      Clinical Rationale
                    </h2>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                      {selectedCase.clinicalRationale.map((r, idx) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                      Follow-Up Plan
                    </h2>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                      {selectedCase.followUpPlan.map((f, idx) => (
                        <li key={idx}>{f}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Sticky Bottom 5-Action Bar */}
                <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-slate-200 bg-slate-50/90 px-6 py-3 rounded-b-2xl dark:border-slate-800 dark:bg-slate-900/90">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onOpenDecision(selectedCase)}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 dark:bg-sky-500 dark:hover:bg-sky-400"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Open Final Decision
                    </button>
                    <button
                      type="button"
                      onClick={() => onReviewTranscript(selectedCase)}
                      className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                    >
                      Review Transcript
                    </button>
                    <button
                      type="button"
                      onClick={() => onCloneRerun(selectedCase)}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                    >
                      <Copy className="h-3.5 w-3.5" />
                      Clone &amp; Re-run
                    </button>
                    <button
                      type="button"
                      onClick={() => onExportPdf(selectedCase)}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                    >
                      <FileDown className="h-3.5 w-3.5" />
                      Export PDF
                    </button>
                  </div>

                  <button
                    type="button"
                    aria-label={`Delete ${selectedCase.caseCode}`}
                    onClick={() => setDeleteTarget(selectedCase)}
                    className="rounded-xl border border-rose-500/35 bg-rose-500/10 p-2 text-rose-600 transition-colors hover:bg-rose-500/20 dark:text-rose-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            </AnimatePresence>
          ) : (
            <div className="flex flex-1 items-center justify-center p-8 text-sm text-slate-500">
              Select a case to preview details.
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteTarget !== null}
        variant="danger"
        title={`Delete ${deleteTarget?.caseCode ?? "case"}?`}
        message="This will permanently remove the archived case and transcript from your Past Cases list."
        confirmLabel="Delete Case"
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) {
            onDeleteCase(deleteTarget.id);
          }
          setDeleteTarget(null);
        }}
      />
    </section>
  );
};

export default Page6PastCases;
