import React, { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  Lock,
  Plus,
  RotateCcw,
  Sparkles,
  UserPlus,
  X,
} from "lucide-react";
import ConfirmDialog from "../components/vmdt/ConfirmDialog.js";
import DoctorAvatar from "../components/vmdt/DoctorAvatar.js";
import { TEAM_DEFINITIONS } from "../utils/vmdtRoster.js";
import {
  DEFAULT_TEAMS,
  RESOURCE_CATALOG,
  type TeamId,
  type VmdtAgentConfig,
} from "../virtualMdtTypes.js";

interface Page7AgentsProps {
  agents: VmdtAgentConfig[];
  availableModels: string[];
  onUpdateAgent: (id: string, patch: Partial<VmdtAgentConfig>) => void;
  onAddCustomAgent: (teamId: TeamId) => string;
  onResetDefaults: () => void;
  onBackToHall: () => void;
}

export const Page7Agents: React.FC<Page7AgentsProps> = ({
  agents,
  availableModels,
  onUpdateAgent,
  onAddCustomAgent,
  onResetDefaults,
  onBackToHall,
}) => {
  const [selectedTeam, setSelectedTeam] = useState<TeamId>("radiation_oncology");
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0]?.id ?? "RO-01");
  const [customResourceInput, setCustomResourceInput] = useState("");
  const [confirmAddOpen, setConfirmAddOpen] = useState(false);
  const [confirmResetOpen, setConfirmResetOpen] = useState(false);
  const [testSandboxOpen, setTestSandboxOpen] = useState(false);

  const teamAgents = useMemo(
    () => agents.filter((a) => a.teamId === selectedTeam),
    [agents, selectedTeam],
  );

  const selectedAgent =
    agents.find((a) => a.id === selectedAgentId) ?? teamAgents[0] ?? agents[0] ?? null;

  const modelChoices = useMemo(
    () => Array.from(new Set([...availableModels, "qwen3.5:4b", "qwen2.5-coder:7b", "llama3.1:8b"])),
    [availableModels],
  );

  const toggleResource = (agent: VmdtAgentConfig, resource: string) => {
    const isAvail = agent.availableResources.includes(resource);
    const nextAvail = isAvail
      ? agent.availableResources.filter((r) => r !== resource)
      : [...agent.availableResources, resource];
    const nextUnavail = isAvail
      ? Array.from(new Set([...agent.unavailableResources, resource]))
      : agent.unavailableResources.filter((r) => r !== resource);
    onUpdateAgent(agent.id, {
      availableResources: nextAvail,
      unavailableResources: nextUnavail,
    });
  };

  const handleAddCustomResource = (agent: VmdtAgentConfig) => {
    const val = customResourceInput.trim();
    if (!val) return;
    onUpdateAgent(agent.id, {
      resourceConstrained: true,
      availableResources: Array.from(new Set([...agent.availableResources, val])),
      unavailableResources: agent.unavailableResources.filter((r) => r !== val),
    });
    setCustomResourceInput("");
  };

  return (
    <section
      aria-label="Manage Agents and Teams"
      className="flex flex-1 flex-col overflow-hidden"
    >
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

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setConfirmAddOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-amber-500/40 bg-slate-900 px-3.5 py-1.5 text-xs font-semibold text-amber-300 shadow hover:bg-slate-800 dark:bg-slate-800"
          >
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            <UserPlus className="h-3.5 w-3.5" />
            Add Agent
          </button>
          <button
            type="button"
            onClick={() => setConfirmResetOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset Defaults
          </button>
        </div>
      </div>

      {/* 3-Column Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-4 px-6 pb-5">
        {/* Left Column (~20%): Fixed Specialty Teams Rail (NO add/rename/delete) */}
        <div className="mdt-scroll col-span-12 flex flex-col overflow-y-auto rounded-2xl border border-slate-200 bg-white p-3 shadow-lg dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-3 xl:col-span-2">
          <h2 className="px-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Teams Rail
          </h2>
          <p className="mb-3 px-2 text-[11px] text-slate-400">Fixed MDT Specialty Teams</p>

          <div className="space-y-1.5">
            {DEFAULT_TEAMS.map((teamId) => {
              const def = TEAM_DEFINITIONS[teamId];
              const list = agents.filter((a) => a.teamId === teamId);
              const activeCount = list.filter((a) => a.active).length;
              const isSelected = selectedTeam === teamId;
              return (
                <button
                  key={teamId}
                  type="button"
                  onClick={() => {
                    setSelectedTeam(teamId);
                    if (list[0]) setSelectedAgentId(list[0].id);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl border px-3 py-2.5 text-left text-xs transition-all ${
                    isSelected
                      ? "border-blue-600 bg-blue-50 font-semibold text-blue-700 shadow-sm dark:border-sky-400 dark:bg-sky-500/15 dark:text-sky-300"
                      : "border-transparent text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/70"
                  }`}
                >
                  <span className="truncate">{def.label}</span>
                  <span className="ml-2 shrink-0 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    {activeCount}/{list.length}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center Column (~42%): AI Agent Cards Grid */}
        <div className="mdt-scroll col-span-12 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 shadow-lg dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              AI Specialist Roster — {TEAM_DEFINITIONS[selectedTeam].label}
            </h2>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {teamAgents.length} Agents
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {teamAgents.map((agent) => {
              const isSelected = selectedAgent?.id === agent.id;
              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedAgentId(agent.id);
                    }
                  }}
                  className={`flex cursor-pointer flex-col justify-between rounded-2xl border p-3.5 transition-all ${
                    isSelected
                      ? "border-blue-600 bg-blue-50/40 shadow-[0_0_16px_rgba(37,99,235,0.16)] dark:border-sky-400 dark:bg-sky-500/10 dark:shadow-[0_0_18px_rgba(56,189,248,0.2)]"
                      : "border-slate-200 bg-slate-50/60 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <DoctorAvatar
                        variant={agent.avatarVariant}
                        scrubColor={agent.scrubColor}
                        hasGlasses={agent.hasGlasses}
                        propType={agent.propType}
                        size={46}
                      />
                      {agent.resourceConstrained && (
                        <span className="rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:text-amber-300">
                          Resource-Constrained
                        </span>
                      )}
                    </div>
                    <div className="mt-2 truncate text-xs font-bold text-slate-900 dark:text-white">
                      {agent.displayName}
                    </div>
                    <div className="mt-0.5 line-clamp-2 text-[11px] text-slate-500 dark:text-slate-400">
                      {agent.subspecialty}
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between border-t border-slate-200/70 pt-2.5 dark:border-slate-800">
                    <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                      {agent.active ? "Active in Hall" : "Inactive"}
                    </span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={agent.active}
                      aria-label={`Toggle ${agent.displayName} active`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onUpdateAgent(agent.id, { active: !agent.active });
                      }}
                      className={`relative h-5 w-9 rounded-full transition-colors ${
                        agent.active ? "bg-blue-600 dark:bg-sky-500" : "bg-slate-300 dark:bg-slate-700"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform ${
                          agent.active ? "translate-x-4" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (~38%): Agent Editor & Configuration */}
        <div className="mdt-scroll col-span-12 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-lg dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-4 xl:col-span-5">
          {selectedAgent ? (
            <div className="space-y-4">
              {/* Identity Header */}
              <div className="flex items-center gap-3 border-b border-slate-200 pb-4 dark:border-slate-800">
                <DoctorAvatar
                  variant={selectedAgent.avatarVariant}
                  scrubColor={selectedAgent.scrubColor}
                  hasGlasses={selectedAgent.hasGlasses}
                  propType={selectedAgent.propType}
                  size={58}
                />
                <div className="min-w-0 flex-1 space-y-1.5">
                  <input
                    type="text"
                    value={selectedAgent.displayName}
                    onChange={(e) =>
                      onUpdateAgent(selectedAgent.id, { displayName: e.target.value })
                    }
                    className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-bold dark:border-slate-700 dark:bg-slate-900"
                  />
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      value={selectedAgent.teamId}
                      onChange={(e) => {
                        const teamId = e.target.value as TeamId;
                        onUpdateAgent(selectedAgent.id, {
                          teamId,
                          specialty: TEAM_DEFINITIONS[teamId].label,
                        });
                      }}
                      className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-900"
                    >
                      {DEFAULT_TEAMS.map((tid) => (
                        <option key={tid} value={tid}>
                          {TEAM_DEFINITIONS[tid].label}
                        </option>
                      ))}
                    </select>
                    <div className="flex items-center gap-1">
                      {[0, 1, 2, 3, 4].map((v) => (
                        <button
                          key={v}
                          type="button"
                          onClick={() => onUpdateAgent(selectedAgent.id, { avatarVariant: v })}
                          className={`h-5 w-5 rounded-full border text-[10px] font-bold ${
                            selectedAgent.avatarVariant === v
                              ? "border-sky-400 bg-sky-500/20 text-sky-600 dark:text-sky-300"
                              : "border-slate-300 text-slate-400 dark:border-slate-700"
                          }`}
                        >
                          {v + 1}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Locked Innate Role & Personality (Read-Only) */}
              <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-3.5 dark:border-slate-700 dark:bg-slate-800/50">
                <div className="mb-1.5 flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-200">
                  <span className="inline-flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-slate-500" />
                    Innate Role &amp; Personality — Protected
                  </span>
                  <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                    Read-Only
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                  {selectedAgent.innatePersonality}
                </p>
              </div>

              {/* Institute Resource Availability */}
              <div className="rounded-xl border border-slate-200 p-3.5 dark:border-slate-800">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Institute Resource Availability
                  </span>
                  {selectedAgent.resourceConstrained && (
                    <span className="text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                      Injected into Context
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {Array.from(
                    new Set([
                      ...RESOURCE_CATALOG,
                      ...selectedAgent.availableResources,
                      ...selectedAgent.unavailableResources,
                    ]),
                  ).map((res) => {
                    const isAvail = selectedAgent.availableResources.includes(res);
                    return (
                      <button
                        key={res}
                        type="button"
                        onClick={() => toggleResource(selectedAgent, res)}
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                          isAvail
                            ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                            : "border-rose-500/40 bg-rose-500/15 text-rose-700 dark:text-rose-300"
                        }`}
                      >
                        {isAvail ? `✓ ${res}` : `✕ ${res}`}
                      </button>
                    );
                  })}
                </div>

                <div className="mt-2.5 flex gap-2">
                  <input
                    type="text"
                    value={customResourceInput}
                    onChange={(e) => setCustomResourceInput(e.target.value)}
                    placeholder="Add custom institute resource..."
                    className="flex-1 rounded-lg border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs dark:border-slate-700 dark:bg-slate-900"
                  />
                  <button
                    type="button"
                    onClick={() => handleAddCustomResource(selectedAgent)}
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-semibold hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                  >
                    <Plus className="h-3 w-3" />
                    Add
                  </button>
                </div>
              </div>

              {/* Model & Instructions */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                    LLM Model
                  </label>
                  <select
                    value={selectedAgent.model}
                    onChange={(e) => onUpdateAgent(selectedAgent.id, { model: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                  >
                    {modelChoices.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="flex justify-between text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                    <span>Temperature</span>
                    <span>{selectedAgent.temperature.toFixed(2)}</span>
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={selectedAgent.temperature}
                    onChange={(e) =>
                      onUpdateAgent(selectedAgent.id, { temperature: parseFloat(e.target.value) })
                    }
                    className="mt-2 w-full accent-blue-600 dark:accent-sky-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                  Additional Context / Notes (Appended Safely)
                </label>
                <textarea
                  rows={2}
                  value={selectedAgent.extraInstructions}
                  onChange={(e) =>
                    onUpdateAgent(selectedAgent.id, { extraInstructions: e.target.value })
                  }
                  placeholder="Optional institute protocols or phrasing reminders..."
                  className="mt-1 w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <button
                type="button"
                onClick={() => setTestSandboxOpen(true)}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-slate-50 py-2.5 text-xs font-semibold text-slate-800 transition-colors hover:bg-slate-100 dark:border-sky-400/30 dark:bg-slate-800 dark:text-sky-300 dark:hover:bg-slate-700"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Test Agent in Sandbox
              </button>
            </div>
          ) : (
            <div className="text-xs text-slate-500">Select an agent to inspect or configure.</div>
          )}
        </div>
      </div>

      {/* Modals */}
      <ConfirmDialog
        open={confirmAddOpen}
        variant="warning"
        title="Add Custom Agent (Not Recommended)"
        message="Adding custom agents is not recommended and may alter balanced 49-role tumor board dynamics. Continue anyway?"
        confirmLabel="Add Custom Agent"
        onCancel={() => setConfirmAddOpen(false)}
        onConfirm={() => {
          setConfirmAddOpen(false);
          const createdId = onAddCustomAgent(selectedTeam);
          setSelectedAgentId(createdId);
        }}
      />

      <ConfirmDialog
        open={confirmResetOpen}
        variant="danger"
        title="Reset Roster & Resources to Defaults?"
        message="This will restore all pre-loaded oncology specialists, remove custom agents, and reset institute resource tags."
        confirmLabel="Reset Defaults"
        onCancel={() => setConfirmResetOpen(false)}
        onConfirm={() => {
          setConfirmResetOpen(false);
          onResetDefaults();
        }}
      />

      <AnimatePresence>
        {testSandboxOpen && selectedAgent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-sky-400/25 dark:bg-slate-900"
            >
              <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
                <div className="text-sm font-bold">Sandbox Preview — {selectedAgent.displayName}</div>
                <button
                  type="button"
                  onClick={() => setTestSandboxOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-3 space-y-2 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                <p>
                  <strong>Active Model:</strong> {selectedAgent.model} (T={selectedAgent.temperature.toFixed(2)})
                </p>
                <p>
                  <strong>Resource Context:</strong> Available:{" "}
                  {selectedAgent.availableResources.join(", ") || "None specified"} | Unavailable:{" "}
                  {selectedAgent.unavailableResources.join(", ") || "None"}.
                </p>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 italic dark:border-slate-800 dark:bg-slate-950/60">
                  &ldquo;Under my protected {selectedAgent.specialty} mandate ({selectedAgent.personalitySummary}), any educational option must respect available facilities ({selectedAgent.availableResources.slice(0, 3).join(", ") || "standard clinic"}) and honor STG-00 locked staging.&rdquo;
                </div>
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={() => setTestSandboxOpen(false)}
                  className="rounded-xl bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white dark:bg-sky-500"
                >
                  Close Sandbox
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default Page7Agents;
