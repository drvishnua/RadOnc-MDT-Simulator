import React, { useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Circle,
  FileUp,
  Mic,
  MicOff,
  Paperclip,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";
import { IntakeHostIllustration } from "../components/vmdt/DoctorAvatar.js";
import { PRESET_CASES } from "../presetCases.js";

interface Page2IntakeProps {
  form: Record<string, string>;
  onChangeField: (key: string, val: string) => void;
  onLoadPreset: (presetForm: Record<string, string>) => void;
  onResetForm: () => void;
  onBackToHall: () => void;
  onProceedToAudit: () => void;
  voiceLanguage: string;
}

type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

export const Page2Intake: React.FC<Page2IntakeProps> = ({
  form,
  onChangeField,
  onLoadPreset,
  onResetForm,
  onBackToHall,
  onProceedToAudit,
  voiceLanguage,
}) => {
  const [focusedSection, setFocusedSection] = useState<string>("welcome");
  const [activeInputKey, setActiveInputKey] = useState<string>("case_summary");
  const [isListening, setIsListening] = useState(false);
  const [autoFillOpen, setAutoFillOpen] = useState(false);
  const [rawNote, setRawNote] = useState("");
  const recognitionRef = useRef<SpeechRec | null>(null);

  const demoValid = Boolean((form.patient_name || form.age_years || form.sex_at_birth).trim());
  const stageValid = Boolean((form.primary_site || form.histology || form.scenario_title).trim());
  const workupValid = Boolean((form.pathology_summary || form.imaging_summary).trim());
  const historyValid = Boolean((form.case_summary || "").trim());

  const speechMessage = useMemo(() => {
    if (isListening) return "Listening... speak the patient history, staging, or board question now.";
    if (focusedSection === "demographics") {
      return "Capture patient name/ID, age, biological sex, and ECOG/KPS performance scale.";
    }
    if (focusedSection === "staging") {
      return "Specify primary site, histology, and any clinical TNM stage — STG-00 will audit it against imaging.";
    }
    if (focusedSection === "workup") {
      return "Include exact pathology biomarkers (p16, ER/PR/HER2, Ki-67) and cross-sectional imaging findings.";
    }
    if (focusedSection === "history") {
      return "Summarize comorbidities, prior treatment, and your key MDT board question!";
    }
    if (demoValid && stageValid && historyValid) {
      return "Looking sharp! Click 'Audit Case Details >' to run STG-00 & team readiness checks.";
    }
    return "Hello! Tell me about the patient's case, or use Voice-to-Text and AI Auto-Fill below!";
  }, [isListening, focusedSection, demoValid, stageValid, historyValid]);

  const toggleVoiceToText = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const win = window as unknown as {
      SpeechRecognition?: new () => SpeechRec;
      webkitSpeechRecognition?: new () => SpeechRec;
    };
    const SpeechCtor = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!SpeechCtor) {
      setIsListening(true);
      setTimeout(() => {
        const snippet =
          "61-year-old male with cT3 N1b M0 rectal adenocarcinoma; MRI pelvis shows mesorectal fat invasion and 3 mesorectal lymph nodes.";
        const cur = (form[activeInputKey] || "").trim();
        onChangeField(activeInputKey, cur ? `${cur} ${snippet}` : snippet);
        setIsListening(false);
      }, 1400);
      return;
    }

    const rec = new SpeechCtor();
    rec.lang = voiceLanguage || "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (ev) => {
      const spoken = ev.results?.[0]?.[0]?.transcript?.trim();
      if (spoken) {
        const cur = (form[activeInputKey] || "").trim();
        onChangeField(activeInputKey, cur ? `${cur} ${spoken}` : spoken);
      }
    };
    rec.onerror = () => setIsListening(false);
    rec.onend = () => setIsListening(false);
    recognitionRef.current = rec;
    setIsListening(true);
    rec.start();
  };

  const applyAiAutoFill = () => {
    const text = rawNote.trim();
    if (!text) {
      setAutoFillOpen(false);
      return;
    }
    onChangeField("case_summary", text);

    const ageMatch = text.match(/\b(\d{2})\s*(?:year[- ]?old|yo|y\/o|M|F)\b/i);
    if (ageMatch && !form.age_years) onChangeField("age_years", ageMatch[1]);
    if (/\bfemale\b|\bwoman\b|\b\d{2}F\b/i.test(text) && !form.sex_at_birth) {
      onChangeField("sex_at_birth", "Female");
    } else if (/\bmale\b|\bman\b|\b\d{2}M\b/i.test(text) && !form.sex_at_birth) {
      onChangeField("sex_at_birth", "Male");
    }
    const tnmMatch = text.match(/\b(?:c|p)?(T[0-4][a-c]?)\s*(N[0-3][a-c]?)\s*(M[01xX])\b/i);
    if (tnmMatch) {
      onChangeField("clinical_t_stage", tnmMatch[1].toUpperCase());
      onChangeField("clinical_n_stage", tnmMatch[2].toUpperCase());
      onChangeField("clinical_m_stage", tnmMatch[3].toUpperCase());
    }
    const siteMatch = text.match(
      /\b(oropharynx|tonsil|larynx|glottis|oral cavity|tongue|breast|rectum|rectal|cervix|cervical|lung|nsclc|prostate|glioblastoma)\b/i,
    );
    if (siteMatch) {
      onChangeField("primary_site", siteMatch[1]);
      if (!form.scenario_title || form.scenario_title === "Head-and-neck oncology case") {
        onChangeField("scenario_title", `${siteMatch[1]} oncology consultation`);
      }
    }
    const imgSentence = text
      .split(/[.!?]\s+/)
      .find((s) => /\b(mri|ct|cect|pet|node|nodal|invasion|imaging|scan)\b/i.test(s));
    if (imgSentence && !form.imaging_summary) {
      onChangeField("imaging_summary", imgSentence.trim());
    }
    const pathSentence = text
      .split(/[.!?]\s+/)
      .find((s) => /\b(carcinoma|adenocarcinoma|scc|biopsy|ki-67|her2|p16|er\+|grade)\b/i.test(s));
    if (pathSentence && !form.pathology_summary) {
      onChangeField("pathology_summary", pathSentence.trim());
    }

    setAutoFillOpen(false);
    setRawNote("");
  };

  const inputClass =
    "w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-sky-400 dark:focus:ring-sky-400/20";

  return (
    <section
      aria-label="Case Intake and Submission"
      className="flex flex-1 flex-col overflow-hidden"
    >
      {/* Sub-header Breadcrumb + Quick Preset Selector */}
      <div className="flex shrink-0 items-center justify-between px-6 py-3">
        <button
          type="button"
          onClick={onBackToHall}
          className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Hall
        </button>

        <div className="flex items-center gap-2">
          <label htmlFor="preset-select" className="text-xs font-medium text-slate-500 dark:text-slate-400">
            Load Sample Case:
          </label>
          <select
            id="preset-select"
            defaultValue=""
            onChange={(e) => {
              const found = PRESET_CASES.find((p) => p.id === e.target.value);
              if (found) onLoadPreset(found.form as unknown as Record<string, string>);
            }}
            className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            <option value="" disabled>
              Select synthetic preset...
            </option>
            {PRESET_CASES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.badge})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Two-Column Main Workspace */}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-6 px-6 pb-5">
        {/* Left Column (~58%): Scrollable Intake Form Card */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
          className="col-span-12 flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-sky-400/20 dark:bg-slate-900/78 dark:backdrop-blur-md lg:col-span-7"
        >
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
                Enter Case Details
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Synthetic clinical fields bound directly to the Virtual MDT staging & audit schema
              </p>
            </div>
          </div>

          <div className="mdt-scroll flex-1 space-y-4 overflow-y-auto px-6 py-4">
            {/* Section 1: Patient Summary & Demographics */}
            <div
              onFocus={() => setFocusedSection("demographics")}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/35"
            >
              <div className="mb-3 flex items-center gap-2">
                {demoValid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-400" />
                )}
                <h2 className="text-sm font-semibold">Patient Summary & Demographics</h2>
              </div>
              <div className="grid grid-cols-12 gap-3">
                <input
                  type="text"
                  value={form.patient_name || ""}
                  onFocus={() => setActiveInputKey("patient_name")}
                  onChange={(e) => onChangeField("patient_name", e.target.value)}
                  placeholder="Patient Name / ID (e.g., Synthetic Case 04)"
                  className={`${inputClass} col-span-5`}
                />
                <input
                  type="text"
                  value={form.age_years || ""}
                  onFocus={() => setActiveInputKey("age_years")}
                  onChange={(e) => onChangeField("age_years", e.target.value)}
                  placeholder="Age (e.g., 61)"
                  className={`${inputClass} col-span-2`}
                />
                <select
                  value={form.sex_at_birth || ""}
                  onChange={(e) => onChangeField("sex_at_birth", e.target.value)}
                  className={`${inputClass} col-span-2`}
                >
                  <option value="">Sex</option>
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                </select>
                <input
                  type="text"
                  value={form.performance_status || ""}
                  onFocus={() => setActiveInputKey("performance_status")}
                  onChange={(e) => onChangeField("performance_status", e.target.value)}
                  placeholder="ECOG / KPS (e.g., ECOG 1)"
                  className={`${inputClass} col-span-3`}
                />
              </div>
            </div>

            {/* Section 2: Diagnosis & Staging */}
            <div
              onFocus={() => setFocusedSection("staging")}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/35"
            >
              <div className="mb-3 flex items-center gap-2">
                {stageValid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-400" />
                )}
                <h2 className="text-sm font-semibold">Diagnosis & Staging</h2>
              </div>
              <div className="grid grid-cols-12 gap-3">
                <input
                  type="text"
                  value={form.scenario_title || ""}
                  onFocus={() => setActiveInputKey("scenario_title")}
                  onChange={(e) => onChangeField("scenario_title", e.target.value)}
                  placeholder="Case Title (e.g., Locally advanced rectal adenocarcinoma)"
                  className={`${inputClass} col-span-12`}
                />
                <input
                  type="text"
                  value={form.primary_site || ""}
                  onFocus={() => setActiveInputKey("primary_site")}
                  onChange={(e) => onChangeField("primary_site", e.target.value)}
                  placeholder="Primary Tumor Site (e.g., Right tonsil - oropharynx)"
                  className={`${inputClass} col-span-6`}
                />
                <input
                  type="text"
                  value={form.histology || ""}
                  onFocus={() => setActiveInputKey("histology")}
                  onChange={(e) => onChangeField("histology", e.target.value)}
                  placeholder="Histology (e.g., Squamous cell carcinoma)"
                  className={`${inputClass} col-span-6`}
                />
                <input
                  type="text"
                  value={form.clinical_t_stage || ""}
                  onChange={(e) => onChangeField("clinical_t_stage", e.target.value)}
                  placeholder="cT (e.g., T3)"
                  className={`${inputClass} col-span-3`}
                />
                <input
                  type="text"
                  value={form.clinical_n_stage || ""}
                  onChange={(e) => onChangeField("clinical_n_stage", e.target.value)}
                  placeholder="cN (e.g., N1b)"
                  className={`${inputClass} col-span-3`}
                />
                <input
                  type="text"
                  value={form.clinical_m_stage || ""}
                  onChange={(e) => onChangeField("clinical_m_stage", e.target.value)}
                  placeholder="cM (e.g., M0)"
                  className={`${inputClass} col-span-3`}
                />
                <input
                  type="text"
                  value={form.stage_group || ""}
                  onChange={(e) => onChangeField("stage_group", e.target.value)}
                  placeholder="Stage Group (e.g., IIIB)"
                  className={`${inputClass} col-span-3`}
                />
              </div>
            </div>

            {/* Section 3: Pathology & Imaging */}
            <div
              onFocus={() => setFocusedSection("workup")}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/35"
            >
              <div className="mb-3 flex items-center gap-2">
                {workupValid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-400" />
                )}
                <h2 className="text-sm font-semibold">Pathology & Staging Imaging</h2>
              </div>
              <div className="space-y-3">
                <input
                  type="text"
                  value={form.pathology_summary || ""}
                  onFocus={() => setActiveInputKey("pathology_summary")}
                  onChange={(e) => onChangeField("pathology_summary", e.target.value)}
                  placeholder="Pathology summary (e.g., p16-positive, Ki-67 28%, ER+/PR+/HER2-)"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={form.imaging_summary || ""}
                  onFocus={() => setActiveInputKey("imaging_summary")}
                  onChange={(e) => onChangeField("imaging_summary", e.target.value)}
                  placeholder="Imaging findings (e.g., CECT neck: 1.9 cm right level II node; chest CT negative)"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Section 4: Clinical History & Board Question */}
            <div
              onFocus={() => setFocusedSection("history")}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/35"
            >
              <div className="mb-3 flex items-center gap-2">
                {historyValid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-400" />
                )}
                <h2 className="text-sm font-semibold">Clinical History & Case Question</h2>
              </div>
              <textarea
                rows={3}
                value={form.case_summary || ""}
                onFocus={() => setActiveInputKey("case_summary")}
                onChange={(e) => onChangeField("case_summary", e.target.value)}
                placeholder="Summarize the patient history, comorbidities, prior treatments, and specific questions for the MDT board..."
                className={`${inputClass} resize-none`}
              />
              <div className="mt-3 grid grid-cols-3 gap-3">
                <input
                  type="text"
                  value={form.relevant_comorbidities || ""}
                  onChange={(e) => onChangeField("relevant_comorbidities", e.target.value)}
                  placeholder="Comorbidities (e.g., CKD, T2DM)"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={form.prior_treatment || ""}
                  onChange={(e) => onChangeField("prior_treatment", e.target.value)}
                  placeholder="Prior treatment"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={form.patient_goals || ""}
                  onChange={(e) => onChangeField("patient_goals", e.target.value)}
                  placeholder="Patient priorities / goals"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Future-Ready Upload Slot */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 opacity-75 dark:border-slate-800 dark:bg-slate-950/20">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                  Images & Documents Upload
                </span>
                <span className="rounded-full border border-sky-400/30 bg-sky-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-blue-600 dark:text-sky-300">
                  Coming Soon
                </span>
              </div>
              <div
                aria-disabled="true"
                className="flex cursor-not-allowed items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 py-5 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400"
              >
                <FileUp className="h-4 w-4" />
                <Paperclip className="h-4 w-4" />
                <span>DICOM imaging & pathology PDF ingestion disabled in current release</span>
              </div>
            </div>
          </div>

          {/* Sticky Bottom Action Bar */}
          <div className="flex shrink-0 items-center justify-between gap-3 border-t border-slate-200 bg-slate-50/90 px-6 py-3.5 rounded-b-2xl dark:border-slate-800 dark:bg-slate-900/90">
            <button
              type="button"
              onClick={onResetForm}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <RotateCcw className="h-4 w-4" />
              Reset Form
            </button>
            <button
              type="button"
              onClick={onProceedToAudit}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_rgba(16,185,129,0.35)] transition-all hover:from-emerald-400 hover:to-emerald-500"
            >
              <span>Audit Case Details</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </motion.div>

        {/* Right Column (~42%): Interactive 2.5D AI Intake Host */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
          className="col-span-12 flex min-h-0 flex-col items-center justify-end pb-2 lg:col-span-5"
        >
          {/* Dynamic Speech Bubble */}
          <div className="relative mb-4 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-lg dark:border-sky-400/25 dark:bg-slate-900/85 dark:backdrop-blur-md">
            <AnimatePresence mode="wait">
              <motion.p
                key={speechMessage}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.16 }}
                className="text-sm font-medium leading-relaxed text-slate-800 dark:text-slate-100"
              >
                {speechMessage}
              </motion.p>
            </AnimatePresence>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={toggleVoiceToText}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-all ${
                  isListening
                    ? "border-emerald-500 bg-emerald-500 text-white shadow-[0_0_16px_rgba(16,185,129,0.55)]"
                    : "border-slate-300 bg-slate-50 text-slate-700 hover:border-blue-400 hover:bg-blue-50 dark:border-sky-400/30 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-sky-400"
                }`}
              >
                {isListening ? <MicOff className="h-3.5 w-3.5 animate-pulse" /> : <Mic className="h-3.5 w-3.5" />}
                {isListening ? "Listening..." : "Voice-to-Text"}
              </button>
              <button
                type="button"
                onClick={() => setAutoFillOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-slate-50 px-3.5 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:border-blue-400 hover:bg-blue-50 dark:border-sky-400/30 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-sky-400"
              >
                <Sparkles className="h-3.5 w-3.5 text-blue-600 dark:text-sky-400" />
                AI Auto-Fill
              </button>
            </div>
          </div>

          <IntakeHostIllustration mode="intake" listening={isListening} className="min-h-0 flex-1 w-full" />
        </motion.div>
      </div>

      {/* Compact AI Auto-Fill Modal */}
      <AnimatePresence>
        {autoFillOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-sky-400/25 dark:bg-slate-900"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-blue-600 dark:text-sky-400" />
                  <h2 className="text-base font-bold">AI Auto-Fill from Unstructured Notes</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setAutoFillOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                Paste a synthetic clinical vignette below to extract demographics, primary site, TNM tokens, pathology, and imaging notes into the intake form.
              </p>
              <textarea
                rows={5}
                autoFocus
                value={rawNote}
                onChange={(e) => setRawNote(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") setAutoFillOpen(false);
                }}
                placeholder="e.g., 54-year-old male with cT2 N0 M0 squamous cell carcinoma of right lateral tongue. CECT neck shows 1.9 cm ipsilateral level II lymph node; chest CT negative..."
                className={`${inputClass} mt-3 resize-none`}
              />
              <div className="mt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setAutoFillOpen(false)}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-xs font-medium dark:border-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={applyAiAutoFill}
                  className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                >
                  Extract & Populate
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default Page2Intake;
