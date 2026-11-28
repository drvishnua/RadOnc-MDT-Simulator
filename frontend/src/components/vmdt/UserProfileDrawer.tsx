import React, { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Building2,
  Camera,
  Check,
  Edit3,
  LogOut,
  Mail,
  Moon,
  Save,
  Settings,
  Stethoscope,
  Sun,
  X,
} from "lucide-react";
import type { ResolvedTheme, UserProfile } from "../../virtualMdtTypes.js";
import ConfirmDialog from "./ConfirmDialog.js";
import DoctorAvatar from "./DoctorAvatar.js";

interface UserProfileDrawerProps {
  open: boolean;
  onClose: () => void;
  profile: UserProfile;
  onSaveProfile: (next: UserProfile) => void;
  stats: {
    convened: number;
    completed: number;
    avgConsensus: number;
  };
  resolvedTheme: ResolvedTheme;
  onToggleTheme: () => void;
  onOpenSettings: () => void;
  onSignOutReset: () => void;
}

export const UserProfileDrawer: React.FC<UserProfileDrawerProps> = ({
  open,
  onClose,
  profile,
  onSaveProfile,
  stats,
  resolvedTheme,
  onToggleTheme,
  onOpenSettings,
  onSignOutReset,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState<UserProfile>(profile);
  const [confirmSignOut, setConfirmSignOut] = useState(false);

  useEffect(() => {
    setDraft(profile);
  }, [profile, open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !confirmSignOut) {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose, confirmSignOut]);

  const handleSave = () => {
    onSaveProfile(draft);
    setIsEditing(false);
  };

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setDraft((prev) => ({ ...prev, customAvatarUrl: reader.result as string }));
      }
    };
    reader.readAsDataURL(file);
  };

  return (
    <>
      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-40 flex justify-end">
            {/* Dimmed Blur Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onClose}
              className="fixed inset-0 bg-slate-950/50 backdrop-blur-sm"
              aria-hidden="true"
            />

            {/* Slide-Over Panel */}
            <motion.aside
              id="vmdt-profile-drawer"
              aria-label="Clinician user profile"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 280 }}
              className="relative z-50 flex h-full w-[380px] max-w-[92vw] flex-col border-l border-slate-200 bg-white text-slate-900 shadow-2xl dark:border-sky-400/20 dark:bg-slate-900/95 dark:text-slate-100 dark:backdrop-blur-xl"
            >
              {/* Top Header */}
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
                <h2 className="text-base font-semibold">Clinician Profile</h2>
                <div className="flex items-center gap-2">
                  {!isEditing ? (
                    <button
                      type="button"
                      onClick={() => setIsEditing(true)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-sky-400/25 dark:bg-slate-800 dark:text-sky-300 dark:hover:bg-slate-700"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      Edit Profile
                    </button>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => {
                          setDraft(profile);
                          setIsEditing(false);
                        }}
                        className="rounded-lg px-2 py-1 text-xs text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleSave}
                        className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
                      >
                        <Save className="h-3.5 w-3.5" />
                        Save
                      </button>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={onClose}
                    aria-label="Close profile drawer"
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Scrollable Body */}
              <div className="mdt-scroll flex-1 space-y-5 overflow-y-auto p-5">
                {/* Identity Card */}
                <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-800/50">
                  <div className="relative h-16 w-16 shrink-0">
                    {draft.customAvatarUrl ? (
                      <img
                        src={draft.customAvatarUrl}
                        alt={draft.fullName}
                        className="h-16 w-16 rounded-full border-2 border-sky-400/50 object-cover"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full border-2 border-blue-500/30 bg-sky-500/10 dark:border-sky-400/40">
                        <DoctorAvatar variant={draft.avatarPreset} size={58} scrubColor="#0EA5E9" hasGlasses />
                      </div>
                    )}
                    {isEditing && (
                      <label
                        title="Change avatar"
                        className="absolute -bottom-1 -right-1 flex h-6 w-6 cursor-pointer items-center justify-center rounded-full bg-blue-600 text-white shadow hover:bg-blue-500 dark:bg-sky-500"
                      >
                        <Camera className="h-3 w-3" />
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleAvatarUpload}
                          className="sr-only"
                        />
                      </label>
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    {isEditing ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={draft.fullName}
                          onChange={(e) => setDraft({ ...draft, fullName: e.target.value })}
                          placeholder="Full Name"
                          className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-sm font-semibold dark:border-slate-700 dark:bg-slate-900"
                        />
                        <input
                          type="text"
                          value={draft.title}
                          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                          placeholder="Clinical Title"
                          className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs dark:border-slate-700 dark:bg-slate-900"
                        />
                      </div>
                    ) : (
                      <>
                        <h3 className="truncate text-base font-bold">{profile.fullName}</h3>
                        <p className="truncate text-xs font-medium text-blue-600 dark:text-sky-400">
                          {profile.title}
                        </p>
                        <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
                          {profile.institution}
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {isEditing && (
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-xs dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Avatar Preset:</span>
                    <div className="flex gap-1.5">
                      {[0, 1, 2, 3, 4].map((preset) => (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => setDraft({ ...draft, avatarPreset: preset, customAvatarUrl: undefined })}
                          className={`rounded-lg border p-0.5 ${
                            draft.avatarPreset === preset && !draft.customAvatarUrl
                              ? "border-sky-400 bg-sky-500/15"
                              : "border-transparent opacity-70 hover:opacity-100"
                          }`}
                        >
                          <DoctorAvatar variant={preset} size={26} />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3-Column Activity Stats Strip */}
                <div className="grid grid-cols-3 gap-2.5">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-800/50">
                    <div className="text-lg font-bold text-slate-900 dark:text-white">{stats.convened}</div>
                    <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Cases Convened</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-800/50">
                    <div className="flex items-center justify-center gap-1 text-lg font-bold text-emerald-600 dark:text-emerald-400">
                      {stats.completed}
                      <Check className="h-4 w-4" />
                    </div>
                    <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Completed</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-800/50">
                    <div className="text-lg font-bold text-blue-600 dark:text-sky-400">
                      {stats.avgConsensus}%
                    </div>
                    <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Avg Consensus</div>
                  </div>
                </div>

                {/* Clinician Details */}
                <div className="space-y-3 rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <div className="flex items-start gap-3">
                    <Mail className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Email
                      </div>
                      {isEditing ? (
                        <input
                          type="email"
                          value={draft.email}
                          onChange={(e) => setDraft({ ...draft, email: e.target.value })}
                          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
                        />
                      ) : (
                        <div className="truncate text-sm">{profile.email}</div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Stethoscope className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Primary Specialty
                      </div>
                      {isEditing ? (
                        <input
                          type="text"
                          value={draft.specialty}
                          onChange={(e) => setDraft({ ...draft, specialty: e.target.value })}
                          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
                        />
                      ) : (
                        <div className="truncate text-sm">{profile.specialty}</div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Institution
                      </div>
                      {isEditing ? (
                        <input
                          type="text"
                          value={draft.institution}
                          onChange={(e) => setDraft({ ...draft, institution: e.target.value })}
                          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
                        />
                      ) : (
                        <div className="truncate text-sm">{profile.institution}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Quick Actions */}
              <div className="space-y-2 border-t border-slate-200 p-4 dark:border-slate-800">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onOpenSettings();
                    }}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  >
                    <Settings className="h-3.5 w-3.5" />
                    Open Settings
                  </button>
                  <button
                    type="button"
                    onClick={onToggleTheme}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  >
                    {resolvedTheme === "dark" ? (
                      <>
                        <Sun className="h-3.5 w-3.5 text-amber-400" />
                        Light Mode
                      </>
                    ) : (
                      <>
                        <Moon className="h-3.5 w-3.5 text-indigo-600" />
                        Dark Mode
                      </>
                    )}
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => setConfirmSignOut(true)}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-600 transition-colors hover:bg-rose-500/20 dark:text-rose-400"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign Out / Switch Account
                </button>
              </div>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      <ConfirmDialog
        open={confirmSignOut}
        variant="danger"
        title="Sign Out / Switch Account?"
        message="This will switch back to the default clinician workspace profile. Your saved Past Cases archive will remain intact."
        confirmLabel="Switch Account"
        onCancel={() => setConfirmSignOut(false)}
        onConfirm={() => {
          setConfirmSignOut(false);
          onSignOutReset();
          onClose();
        }}
      />
    </>
  );
};

export default UserProfileDrawer;
