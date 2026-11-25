import { listToMultilineText, multilineTextToList } from "./caseDraft.js";
import type { BatchRunSummary, PendingIntake, SyntheticCasePayload } from "./types.js";

export const CASE_DRAFT_KEY = "radonc-mdt-case-draft-v1";
export const LEGACY_CASE_KEY = "radonc-mdt-last-case";
export const SINGLE_ASSESSMENT_KEY = "radonc-mdt-ro01-assessment-v1";
export const PENDING_INTAKE_KEY = "radonc-mdt-pending-intake-v1";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export const FOCUSED_PANELS: Record<string, { label: string; icon: string; agentIds: string[] }> = {
  all: {
    label: "All Perspectives (49 Roles)",
    icon: "🌐",
    agentIds: []
  },
  radonc: {
    label: "Radiation Oncology (RO-01 to RO-10)",
    icon: "☢️",
    agentIds: ["RO-01", "RO-02", "RO-03", "RO-04", "RO-05", "RO-06", "RO-07", "RO-08", "RO-09", "RO-10"]
  },
  medonc: {
    label: "Medical Oncology (MO-01 to MO-09)",
    icon: "💊",
    agentIds: ["MO-01", "MO-02", "MO-03", "MO-04", "MO-05", "MO-06", "MO-07", "MO-08", "MO-09"]
  },
  surgical: {
    label: "Surgical Oncology (SO-01 to SO-09)",
    icon: "🔪",
    agentIds: ["SO-01", "SO-02", "SO-03", "SO-04", "SO-05", "SO-06", "SO-07", "SO-08", "SO-09"]
  },
  diagnostics: {
    label: "Diagnostics & Pathology (DS-01 to DS-03)",
    icon: "🔬",
    agentIds: ["DS-01", "DS-02", "DS-03"]
  },
  advocacy: {
    label: "Patient & Social Context (PP / SV)",
    icon: "🤝",
    agentIds: ["PP-01", "PP-02", "PP-03", "PP-04", "PP-05", "PP-06", "SV-01", "SV-02", "SV-03"]
  },
  governance: {
    label: "Physics, Governance & QA (SG-01 to SG-09)",
    icon: "⚖️",
    agentIds: ["SG-01", "SG-02", "SG-03", "SG-04", "SG-05", "SG-06", "SG-07", "SG-08", "SG-09"]
  },
  contrarian: {
    label: "Contrarian / Critical Skeptics",
    icon: "⚡",
    agentIds: ["RO-10", "MO-09", "SO-09", "SG-09"]
  }
};

export const emptyForm = {
  patient_name: "",
  scenario_title: "Head-and-neck oncology case",
  case_summary: "",
  age_years: "",
  sex_at_birth: "",
  primary_site: "",
  histology: "",
  clinical_t_stage: "",
  clinical_n_stage: "",
  clinical_m_stage: "",
  stage_group: "",
  performance_status: "",
  pathology_summary: "",
  imaging_summary: "",
  current_medications: "",
  known_allergies: "",
  relevant_investigations: "",
  relevant_comorbidities: "",
  prior_treatment: "",
  patient_goals: "",
  social_context: "",
  resource_context: "",
  known_unknowns: ""
};

export function caseSnapshotToForm(snapshot: SyntheticCasePayload): typeof emptyForm {
  return {
    patient_name: "",
    scenario_title: snapshot.scenario_title ?? emptyForm.scenario_title,
    case_summary: snapshot.case_summary ?? "",
    age_years: snapshot.age_years === null || snapshot.age_years === undefined ? "" : String(snapshot.age_years),
    sex_at_birth: snapshot.sex_at_birth ?? "",
    primary_site: snapshot.primary_site ?? "",
    histology: snapshot.histology ?? "",
    clinical_t_stage: snapshot.clinical_t_stage ?? "",
    clinical_n_stage: snapshot.clinical_n_stage ?? "",
    clinical_m_stage: snapshot.clinical_m_stage ?? "",
    stage_group: snapshot.stage_group ?? "",
    performance_status: snapshot.performance_status ?? "",
    pathology_summary: snapshot.pathology_summary ?? "",
    imaging_summary: snapshot.imaging_summary ?? "",
    current_medications: listToMultilineText(snapshot.current_medications ?? []),
    known_allergies: listToMultilineText(snapshot.known_allergies ?? []),
    relevant_investigations: listToMultilineText(snapshot.relevant_investigations ?? []),
    relevant_comorbidities: listToMultilineText(snapshot.relevant_comorbidities ?? []),
    prior_treatment: listToMultilineText(snapshot.prior_treatment ?? []),
    patient_goals: listToMultilineText(snapshot.patient_goals ?? []),
    social_context: listToMultilineText(snapshot.social_context ?? []),
    resource_context: listToMultilineText(snapshot.resource_context ?? []),
    known_unknowns: listToMultilineText(snapshot.known_unknowns ?? [])
  };
}

export function optionalText(value: string): string | null {
  const cleaned = value.trim();
  return cleaned ? cleaned : null;
}

export function linesToList(value: string): string[] {
  return multilineTextToList(value);
}

export function savedOptionalText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

export function savedStringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function readSavedCase(): SyntheticCasePayload | null {
  const key = "radonc-mdt-last-case";
  try {
    const saved = window.localStorage.getItem(key);
    if (!saved) return null;

    const parsed: unknown = JSON.parse(saved);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      window.localStorage.removeItem(key);
      return null;
    }

    const value = parsed as Record<string, unknown>;
    const valid =
      typeof value.scenario_title === "string" &&
      typeof value.case_summary === "string" &&
      (value.age_years === null ||
        (typeof value.age_years === "number" && Number.isFinite(value.age_years))) &&
      (value.primary_site === null || typeof value.primary_site === "string") &&
      (value.histology === null || typeof value.histology === "string");

    if (!valid) {
      console.warn("[RadOnc] Discarding an incompatible saved training case.");
      window.localStorage.removeItem(key);
      return null;
    }

    return {
      scenario_title: value.scenario_title as string,
      case_summary: value.case_summary as string,
      age_years: value.age_years as number | null,
      sex_at_birth: savedOptionalText(value.sex_at_birth),
      primary_site: value.primary_site as string | null,
      histology: value.histology as string | null,
      clinical_t_stage: savedOptionalText(value.clinical_t_stage),
      clinical_n_stage: savedOptionalText(value.clinical_n_stage),
      clinical_m_stage: savedOptionalText(value.clinical_m_stage),
      stage_group: savedOptionalText(value.stage_group),
      performance_status: savedOptionalText(value.performance_status),
      pathology_summary: savedOptionalText(value.pathology_summary),
      imaging_summary: savedOptionalText(value.imaging_summary),
      current_medications: savedStringList(value.current_medications),
      known_allergies: savedStringList(value.known_allergies),
      relevant_investigations: savedStringList(value.relevant_investigations),
      relevant_comorbidities: savedStringList(value.relevant_comorbidities),
      prior_treatment: savedStringList(value.prior_treatment),
      patient_goals: savedStringList(value.patient_goals),
      social_context: savedStringList(value.social_context),
      resource_context: savedStringList(value.resource_context),
      known_unknowns: savedStringList(value.known_unknowns)
    };
  } catch (error) {
    console.warn("[RadOnc] Could not restore the saved training case; starting clean.", error);
    try { window.localStorage.removeItem(key); } catch { /* Storage may be unavailable. */ }
    return null;
  }
}

export function legacySavedCaseToDraft(_value: unknown): typeof emptyForm | null {
  const saved = readSavedCase();
  return saved ? caseSnapshotToForm(saved) : null;
}

export function readSavedBatch(): BatchRunSummary | null {
  const key = "radonc-mdt-active-batch";
  try {
    const saved = window.localStorage.getItem(key);
    if (!saved) return null;

    const parsed: unknown = JSON.parse(saved);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      window.localStorage.removeItem(key);
      return null;
    }

    const value = parsed as Record<string, unknown>;
    const validStatuses = ["queued", "running", "completed", "completed_with_errors"];
    const valid =
      typeof value.run_id === "string" &&
      value.run_id.length > 0 &&
      typeof value.status === "string" &&
      validStatuses.includes(value.status) &&
      ["total_agents", "completed_count", "failed_count", "queued_count",
        "running_count", "finished_count", "progress_percent"].every(
          (field) => typeof value[field] === "number" && Number.isFinite(value[field])
        ) &&
      typeof value.updated_at === "string";

    if (!valid) {
      console.warn("[RadOnc] Discarding an incompatible saved run pointer; backend records are untouched.");
      window.localStorage.removeItem(key);
      return null;
    }
    return parsed as BatchRunSummary;
  } catch (error) {
    console.warn("[RadOnc] Could not restore the saved run pointer; starting without browser session state.", error);
    try { window.localStorage.removeItem(key); } catch { /* Storage may be unavailable. */ }
    return null;
  }
}

export function safeCaseDraftStorage(): Storage {
  try {
    return window.localStorage;
  } catch {
    return {
      length: 0,
      clear() {},
      getItem() { return null; },
      key() { return null; },
      removeItem() {},
      setItem() { throw new Error("Browser storage is unavailable."); }
    };
  }
}

export function readPendingIntakePointer(): PendingIntake | null {
  try {
    const raw = safeCaseDraftStorage().getItem(PENDING_INTAKE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Record<string, unknown>;
    if (typeof value.session_id !== "string" || typeof value.createNewPatient !== "boolean" ||
        typeof value.patientName !== "string") return null;
    return {
      session_id: value.session_id,
      createNewPatient: value.createNewPatient,
      patientName: value.patientName,
      patientId: typeof value.patientId === "string" ? value.patientId : undefined,
      screening: null
    };
  } catch {
    return null;
  }
}
