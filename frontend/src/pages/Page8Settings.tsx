import React, { useRef, useState } from "react";
import {
  ArrowLeft,
  Building2,
  Check,
  Cpu,
  Database,
  Download,
  Eye,
  EyeOff,
  Mic,
  RotateCcw,
  Sliders,
  Trash2,
} from "lucide-react";
import ConfirmDialog from "../components/vmdt/ConfirmDialog.js";
import {
  RESOURCE_CATALOG,
  type ThemeMode,
  type VmdtSettings,
} from "../virtualMdtTypes.js";

interface Page8SettingsProps {
  settings: VmdtSettings;
  availableModels: string[];
  onUpdateSettings: (patch: Partial<VmdtSettings>) => void;
  onExportAllCases: () => void;
  onClearAllCases: () => void;
  onResetAllSettings: () => void;
  onBackToHall: () => void;
}

type CategoryId = "defaults" | "institute" | "models" | "voice" | "danger";

export const Page8Settings: React.FC<Page8SettingsProps> = ({
  settings,
  availableModels,
  onUpdateSettings,
  onExportAllCases,
  onClearAllCases,
  onResetAllSettings,
  onBackToHall,
}) => {
  const [activeCategory, setActiveCategory] = useState<CategoryId>("defaults");
  const [showKey, setShowKey] = useState(false);
  const [savedToast, setSavedToast] = useState(false);
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);
  const [confirmResetOpen, setConfirmResetOpen] = useState(false);

  const sectionRefs = {
    defaults: useRef<HTMLDivElement>(null),
    institute: useRef<HTMLDivElement>(null),
    models: useRef<HTMLDivElement>(null),
    voice: useRef<HTMLDivElement>(null),
    danger: useRef<HTMLDivElement>(null),
  };

  const updateWithFeedback = (patch: Partial<VmdtSettings>) => {
    onUpdateSettings(patch);
    setSavedToast(true);
    window.setTimeout(() => setSavedToast(false), 1600);
  };

  const jumpTo = (id: CategoryId) => {
    setActiveCategory(id);
    sectionRefs[id].current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const toggleFacility = (facility: string) => {
    const isAvail = settings.availableFacilities.includes(facility);
    const availableFacilities = isAvail
      ? settings.availableFacilities.filter((f) => f !== facility)
      : [...settings.availableFacilities, facility];
    const unavailableFacilities = isAvail
      ? Array.from(new Set([...settings.unavailableFacilities, facility]))
      : settings.unavailableFacilities.filter((f) => f !== facility);
    updateWithFeedback({ availableFacilities, unavailableFacilities });
  };

  const categories: Array<{ id: CategoryId; label: string; icon: React.ReactNode }> = [
    { id: "defaults", label: "Simulation Defaults", icon: <Sliders className="h-4 w-4" /> },
    { id: "institute", label: "Institute & Resources", icon: <Building2 className="h-4 w-4" /> },
    { id: "models", label: "AI Models & API Keys", icon: <Cpu className="h-4 w-4" /> },
    { id: "voice", label: "Voice & Exports", icon: <Mic className="h-4 w-4" /> },
    { id: "danger", label: "Data & Danger Zone", icon: <Database className="h-4 w-4" /> },
  ];

  const modelChoices = Array.from(
    new Set([...availableModels, "qwen3.5:4b", "qwen2.5-coder:7b", "llama3.1:8b"]),
  );

  return (
    <section aria-label="Application Settings" className="flex flex-1 flex-col overflow-hidden">
      {/* Sub-Header Toolbar */}
      <div className="flex shrink-0 items-center justify-between px-6 py-3">
        <button
          type="button"
          onClick={onBackToHall}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Hall
        </button>

        <div className="flex items-center gap-2">
          {savedToast && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500 px-2.5 py-1 text-xs font-semibold text-white shadow">
              <Check className="h-3 w-3" />
              Saved
            </span>
          )}
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/35 bg-emerald-500/12 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            All changes auto-saved
          </span>
        </div>
      </div>

      {/* 2-Column Settings Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-5 px-6 pb-5">
        {/* Left Category Rail (~24%) */}
        <aside className="col-span-12 rounded-2xl border border-slate-200 bg-white p-3 shadow-lg dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-3">
          <div className="space-y-1.5">
            {categories.map((cat) => {
              const isActive = activeCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => jumpTo(cat.id)}
                  className={`flex w-full items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left text-xs font-medium transition-all ${
                    isActive
                      ? "border-blue-600 bg-blue-50 font-semibold text-blue-700 dark:border-sky-400 dark:bg-sky-500/15 dark:text-sky-300"
                      : "border-transparent text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/70"
                  }`}
                >
                  {cat.icon}
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>
        </aside>

        {/* Right Scrollable Settings Cards (~76%) */}
        <div className="mdt-scroll col-span-12 space-y-5 overflow-y-auto pr-1 lg:col-span-9">
          {/* 1. Simulation Defaults */}
          <div
            ref={sectionRefs.defaults}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md"
          >
            <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">
              Simulation Defaults
            </h2>
            <div className="space-y-4 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-medium text-slate-700 dark:text-slate-300">Simulation Rounds</span>
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1 dark:border-slate-700 dark:bg-slate-800">
                  {([1, 2, 3, 4] as const).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => updateWithFeedback({ rounds: r })}
                      className={`rounded-lg px-3 py-1 font-semibold transition-all ${
                        settings.rounds === r
                          ? "bg-white text-blue-600 shadow dark:bg-sky-500 dark:text-white"
                          : "text-slate-600 dark:text-slate-300"
                      }`}
                    >
                      {r} {r === 1 ? "Round" : "Rounds"}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <span className="font-medium text-slate-700 dark:text-slate-300">Agent Verbosity</span>
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1 dark:border-slate-700 dark:bg-slate-800">
                  {(["concise", "standard", "detailed"] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => updateWithFeedback({ verbosity: v })}
                      className={`rounded-lg px-3 py-1 capitalize font-semibold transition-all ${
                        settings.verbosity === v
                          ? "bg-white text-blue-600 shadow dark:bg-sky-500 dark:text-white"
                          : "text-slate-600 dark:text-slate-300"
                      }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Pause Between Rounds
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={settings.pauseBetweenRounds}
                  onClick={() =>
                    updateWithFeedback({ pauseBetweenRounds: !settings.pauseBetweenRounds })
                  }
                  className={`relative h-6 w-11 rounded-full transition-colors ${
                    settings.pauseBetweenRounds ? "bg-blue-600 dark:bg-sky-500" : "bg-slate-300 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                      settings.pauseBetweenRounds ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Consensus Threshold ({settings.consensusThreshold}%)
                </span>
                <input
                  type="range"
                  min={50}
                  max={100}
                  step={5}
                  value={settings.consensusThreshold}
                  onChange={(e) =>
                    updateWithFeedback({ consensusThreshold: Number(e.target.value) })
                  }
                  className="w-60 accent-blue-600 dark:accent-sky-400"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <div>
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    3D Auditorium Camera Panning
                  </span>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Auto uses Slider Pan on mobile/tablet and Mouse Pan on desktop/laptop.
                  </p>
                </div>
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1 dark:border-slate-700 dark:bg-slate-800">
                  {(
                    [
                      { id: "auto", label: "Auto" },
                      { id: "mouse", label: "Mouse" },
                      { id: "slider", label: "Slider" },
                    ] as const
                  ).map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => updateWithFeedback({ cameraPanMode: opt.id })}
                      className={`rounded-lg px-3 py-1 font-semibold transition-all ${
                        (settings.cameraPanMode ?? "auto") === opt.id
                          ? "bg-white text-blue-600 shadow dark:bg-sky-500 dark:text-white"
                          : "text-slate-600 dark:text-slate-300"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 2. Institute & Global Resources */}
          <div
            ref={sectionRefs.institute}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md"
          >
            <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">
              Institute &amp; Global Resources
            </h2>
            <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Primary Institution Name
                </label>
                <input
                  type="text"
                  value={settings.institutionName}
                  onChange={(e) => updateWithFeedback({ institutionName: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Institution Tier
                </label>
                <input
                  type="text"
                  value={settings.institutionTier}
                  onChange={(e) => updateWithFeedback({ institutionTier: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                Available Facilities / Global Resource Baseline
              </div>
              <div className="flex flex-wrap gap-2">
                {RESOURCE_CATALOG.map((fac) => {
                  const isAvail = settings.availableFacilities.includes(fac);
                  return (
                    <button
                      key={fac}
                      type="button"
                      onClick={() => toggleFacility(fac)}
                      className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                        isAvail
                          ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                          : "border-rose-500/40 bg-rose-500/15 text-rose-700 dark:text-rose-300"
                      }`}
                    >
                      {isAvail ? `● ${fac}` : `⊘ ${fac}`}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 3. AI Models & API Keys */}
          <div
            ref={sectionRefs.models}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md"
          >
            <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">
              AI Models &amp; API Keys
            </h2>
            <div className="grid grid-cols-1 gap-4 text-xs sm:grid-cols-2">
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Default LLM Model (Ollama Local Runtime)
                </label>
                <select
                  value={settings.defaultModel}
                  onChange={(e) => updateWithFeedback({ defaultModel: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
                >
                  {modelChoices.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Optional External API Key
                </label>
                <div className="relative mt-1">
                  <input
                    type={showKey ? "text" : "password"}
                    value={settings.apiKey}
                    onChange={(e) => updateWithFeedback({ apiKey: e.target.value })}
                    placeholder="sk-... (optional for local Ollama)"
                    className="w-full rounded-xl border border-slate-300 bg-slate-50 py-2 pl-3 pr-9 dark:border-slate-700 dark:bg-slate-900"
                  />
                  <button
                    type="button"
                    aria-label={showKey ? "Hide API key" : "Show API key"}
                    onClick={() => setShowKey((prev) => !prev)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  >
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Agent Timeout (seconds)
                </label>
                <input
                  type="number"
                  min={30}
                  max={900}
                  value={settings.agentTimeoutSeconds}
                  onChange={(e) =>
                    updateWithFeedback({ agentTimeoutSeconds: Number(e.target.value) || 300 })
                  }
                  className="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-600 dark:text-slate-300">
                  Max Auto-Retries
                </label>
                <input
                  type="number"
                  min={0}
                  max={6}
                  value={settings.maxAutoRetries}
                  onChange={(e) =>
                    updateWithFeedback({ maxAutoRetries: Number(e.target.value) || 0 })
                  }
                  className="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>
          </div>

          {/* 4. Voice & Exports */}
          <div
            ref={sectionRefs.voice}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md"
          >
            <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">
              Voice &amp; Exports
            </h2>
            <div className="space-y-4 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Voice-to-Text Language
                </span>
                <select
                  value={settings.voiceLanguage}
                  onChange={(e) => updateWithFeedback({ voiceLanguage: e.target.value })}
                  className="rounded-xl border border-slate-300 bg-slate-50 px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900"
                >
                  <option value="en-US">English (US)</option>
                  <option value="en-GB">English (UK)</option>
                  <option value="en-IN">English (India)</option>
                </select>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <span className="font-medium text-slate-700 dark:text-slate-300">Default Theme</span>
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1 dark:border-slate-700 dark:bg-slate-800">
                  {(["dark", "light", "system"] as ThemeMode[]).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => updateWithFeedback({ defaultTheme: t })}
                      className={`rounded-lg px-3 py-1 capitalize font-semibold transition-all ${
                        settings.defaultTheme === t
                          ? "bg-white text-blue-600 shadow dark:bg-sky-500 dark:text-white"
                          : "text-slate-600 dark:text-slate-300"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-200/70 pt-3 dark:border-slate-800">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  PDF Export Branding &amp; Consensus Summary
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={settings.pdfBranding}
                  onClick={() => updateWithFeedback({ pdfBranding: !settings.pdfBranding })}
                  className={`relative h-6 w-11 rounded-full transition-colors ${
                    settings.pdfBranding ? "bg-blue-600 dark:bg-sky-500" : "bg-slate-300 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                      settings.pdfBranding ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* 5. Data & Danger Zone */}
          <div
            ref={sectionRefs.danger}
            className="rounded-2xl border border-rose-500/25 bg-white p-5 shadow-md dark:bg-slate-900/78 dark:backdrop-blur-md"
          >
            <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">
              Data &amp; Danger Zone
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <button
                type="button"
                onClick={onExportAllCases}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-slate-50 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <Download className="h-3.5 w-3.5" />
                Export All Cases (JSON)
              </button>
              <button
                type="button"
                onClick={() => setConfirmClearOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 font-semibold text-rose-700 hover:bg-rose-500/25 dark:text-rose-300"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear All Past Cases
              </button>
              <button
                type="button"
                onClick={() => setConfirmResetOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 font-semibold text-rose-700 hover:bg-rose-500/25 dark:text-rose-300"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Reset All Settings to Defaults
              </button>
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirmClearOpen}
        variant="danger"
        title="Clear All Past Cases?"
        message="This permanently clears your saved Past Cases archive from local storage. Export a JSON backup first if needed."
        confirmLabel="Clear All Cases"
        onCancel={() => setConfirmClearOpen(false)}
        onConfirm={() => {
          setConfirmClearOpen(false);
          onClearAllCases();
        }}
      />

      <ConfirmDialog
        open={confirmResetOpen}
        variant="warning"
        title="Reset All Settings to Defaults?"
        message="All simulation defaults, institute facilities, and export preferences will revert to factory defaults."
        confirmLabel="Reset Settings"
        onCancel={() => setConfirmResetOpen(false)}
        onConfirm={() => {
          setConfirmResetOpen(false);
          onResetAllSettings();
        }}
      />
    </section>
  );
};

export default Page8Settings;
