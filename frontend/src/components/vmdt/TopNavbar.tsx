import React from "react";
import { Moon, Sun } from "lucide-react";
import type { ResolvedTheme, UserProfile, VmdtPageId } from "../../virtualMdtTypes.js";

interface TopNavbarProps {
  currentPage: VmdtPageId;
  onNavigate: (page: VmdtPageId) => void;
  resolvedTheme: ResolvedTheme;
  onToggleTheme: () => void;
  userProfile: UserProfile;
  onOpenProfile: () => void;
  profileOpen: boolean;
  hasActiveRun?: boolean;
  activeRunRound?: number;
  activeRunPaused?: boolean;
  onReturnToActiveRun?: () => void;
}

const NAV_ITEMS: Array<{ id: VmdtPageId; label: string }> = [
  { id: "past-cases", label: "Past Cases" },
  { id: "agents", label: "Manage Agents / Teams" },
  { id: "settings", label: "Settings" },
];

export const TopNavbar: React.FC<TopNavbarProps> = ({
  currentPage,
  onNavigate,
  resolvedTheme,
  onToggleTheme,
  userProfile,
  onOpenProfile,
  profileOpen,
  hasActiveRun = false,
  activeRunRound = 1,
  activeRunPaused = false,
  onReturnToActiveRun,
}) => {
  const initials =
    userProfile.fullName
      .replace(/^Dr\.?\s*/i, "")
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("") || "MD";

  const isDark = resolvedTheme === "dark";

  return (
    <header className="relative z-30 flex h-14 w-full shrink-0 items-center justify-between border-b border-slate-300/90 bg-white/85 px-5 backdrop-blur-md transition-colors duration-300 dark:border-sky-400/20 dark:bg-slate-900/75">
      {/* Left Brand */}
      <button
        type="button"
        onClick={() => onNavigate("hall")}
        className="group flex items-center gap-2.5 rounded-xl px-2 py-1 text-left transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-sky-400"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-blue-500/25 bg-gradient-to-br from-sky-500/15 to-indigo-500/20 dark:border-sky-400/30 dark:from-sky-400/20 dark:to-emerald-400/15">
          <svg
            viewBox="0 0 32 32"
            className="h-5 w-5 text-blue-600 dark:text-sky-400"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M16 4v24M10 10c2.2-2.2 9.8-2.2 12 0M8 14c3.5 1.8 12.5 1.8 16 0M11 20c2 2.2 8 2.2 10 0"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <circle cx="16" cy="5.5" r="2.2" fill="currentColor" />
            <path
              d="M6 10.5c2.2-3 5.8-4 10-3.2 4.2-.8 7.8.2 10 3.2"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              opacity="0.7"
            />
          </svg>
        </div>
        <span className="text-base font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Virtual MDT
        </span>
      </button>

      {/* Center Nav Links */}
      <nav aria-label="Primary navigation" className="flex h-full items-center gap-2 sm:gap-6">
        {NAV_ITEMS.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`relative flex h-full items-center px-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "text-blue-600 dark:text-sky-400"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
              }`}
            >
              <span>{item.label}</span>
              {isActive && (
                <span className="absolute inset-x-1 bottom-0 h-0.5 rounded-full bg-blue-600 shadow-[0_0_10px_rgba(37,99,235,0.6)] dark:bg-sky-400 dark:shadow-[0_0_10px_rgba(56,189,248,0.8)]" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Right Active Run Pill, Theme Switch & Profile Trigger */}
      <div className="flex items-center gap-3">
        {hasActiveRun && currentPage !== "simulation" && (
          <button
            type="button"
            onClick={() => onReturnToActiveRun?.()}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold shadow-sm transition-all hover:scale-[1.02] focus-visible:outline-2 focus-visible:outline-sky-400 ${
              activeRunPaused
                ? "border-amber-500/40 bg-amber-500/15 text-amber-800 hover:bg-amber-500/25 dark:border-amber-400/40 dark:bg-amber-500/20 dark:text-amber-200 dark:hover:bg-amber-500/30"
                : "border-emerald-500/40 bg-emerald-500/15 text-emerald-800 hover:bg-emerald-500/25 dark:border-emerald-400/40 dark:bg-emerald-500/20 dark:text-emerald-200 dark:hover:bg-emerald-500/30"
            }`}
          >
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                  activeRunPaused ? "bg-amber-500" : "bg-emerald-500"
                }`}
              />
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${
                  activeRunPaused ? "bg-amber-500" : "bg-emerald-500"
                }`}
              />
            </span>
            <span className="whitespace-nowrap">
              {activeRunPaused
                ? `Return to Paused Run (R${activeRunRound})`
                : `Return to Active Run (R${activeRunRound})`}
            </span>
          </button>
        )}
        <button
          type="button"
          role="switch"
          aria-checked={isDark}
          aria-label="Toggle dark and light mode"
          onClick={onToggleTheme}
          className="relative flex h-8 w-16 items-center justify-between rounded-full border border-slate-300 bg-slate-100 px-1.5 transition-colors hover:border-slate-400 dark:border-sky-400/25 dark:bg-slate-800/90 dark:hover:border-sky-400/50"
        >
          <Sun
            className={`relative z-10 h-3.5 w-3.5 transition-colors ${
              !isDark ? "text-amber-600" : "text-slate-400"
            }`}
          />
          <Moon
            className={`relative z-10 h-3.5 w-3.5 transition-colors ${
              isDark ? "text-sky-300" : "text-slate-400"
            }`}
          />
          <span
            className={`absolute top-1 h-6 w-6 rounded-full bg-white shadow-sm transition-transform duration-200 dark:bg-slate-700 ${
              isDark ? "translate-x-8" : "translate-x-0"
            }`}
          />
        </button>

        <button
          type="button"
          onClick={onOpenProfile}
          aria-expanded={profileOpen}
          aria-controls="vmdt-profile-drawer"
          aria-label="Open clinician profile drawer"
          className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-300 bg-gradient-to-br from-blue-600 to-indigo-600 text-xs font-bold text-white shadow-sm transition-transform hover:scale-105 dark:border-sky-400/40 dark:from-sky-500 dark:to-indigo-600"
        >
          {userProfile.customAvatarUrl ? (
            <img
              src={userProfile.customAvatarUrl}
              alt={userProfile.fullName}
              className="h-full w-full rounded-full object-cover"
            />
          ) : (
            <span>{initials}</span>
          )}
          <span
            className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500 dark:border-slate-900"
            aria-hidden="true"
          />
        </button>
      </div>
    </header>
  );
};

export default TopNavbar;
