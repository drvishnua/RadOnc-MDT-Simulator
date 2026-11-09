import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { readDraft, writeDraft, listToMultilineText, multilineTextToList, createBlankDraft } from "./caseDraft.js";
import { readSavedSingleAssessment, writeSavedSingleAssessment } from "./singleAssessmentStorage.js";
import { hasCompletedIndependentAssessments, shouldOfferIndependentBatchResume, shouldShowBatchPanel } from "./runRecovery.js";
import { patientVersionDisplayName } from "./patientVersionName.js";
import { formatElapsedDuration } from "./roundTiming.js";

const CASE_DRAFT_KEY = "radonc-mdt-case-draft-v1";
const LEGACY_CASE_KEY = "radonc-mdt-last-case";
const SINGLE_ASSESSMENT_KEY = "radonc-mdt-ro01-assessment-v1";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type Health = {
  status: string;
  application: string;
  version: string;
  mode: string;
};

type Runtime = {
  reachable: boolean;
  version?: string | null;
  configured_model: string;
  configured_model_installed: boolean;
  models: string[];
  error?: string;
};

type Agent = {
  agent_id: string;
  category: string;
  category_label: string;
  name: string;
  mandate: string;
};

type ValidationResult = {
  valid: boolean;
  mode: string;
  warnings: string[];
  note: string;
};

type SyntheticCasePayload = {
  scenario_title: string;
  case_summary: string;
  age_years: number | null;
  sex_at_birth: string | null;
  primary_site: string | null;
  histology: string | null;
  clinical_t_stage: string | null;
  clinical_n_stage: string | null;
  clinical_m_stage: string | null;
  stage_group: string | null;
  performance_status: string | null;
  pathology_summary: string | null;
  imaging_summary: string | null;
  current_medications?: string[];
  known_allergies?: string[];
  relevant_investigations?: string[];
  relevant_comorbidities: string[];
  prior_treatment: string[];
  patient_goals: string[];
  social_context: string[];
  resource_context: string[];
  known_unknowns: string[];
};

type AgentAssessmentResult = {
  agent_id: string;
  round_number: number;
  position: "supports" | "opposes" | "conditional" | "insufficient_information";
  provisional_conclusion: string;
  preferred_educational_option: string;
  perspective_summary: string;
  discussion_options: string[];
  unknowns: string[];
  evidence_gaps: string[];
  uncertainty_notes: string[];
  confidence: number;
  evidence_claims: unknown[];
  case_facts?: string[];
  case_data_integrity_flags?: string[];
  safety_boundary: string;
  not_a_treatment_instruction: boolean;
};

type SavedSingleAssessment = {
  version: 1;
  saved_at: string;
  case_snapshot: SyntheticCasePayload;
  assessment: AgentAssessmentResult;
  patient_id?: string;
  case_version_id?: string;
};

type BatchRunSummary = {
  run_id: string;
  status: "queued" | "running" | "completed" | "completed_with_errors";
  total_agents: number;
  completed_count: number;
  failed_count: number;
  queued_count: number;
  running_count: number;
  finished_count: number;
  progress_percent: number;
  current_agent_id: string | null;
  created_at: string;
  updated_at: string;
  mdt_finished_at: string | null;
  case_snapshot_sha256: string;
  patient_id?: string | null;
  case_version_id?: string | null;
  case_version_number?: number | null;
};

type PatientRecordSummary = {
  patient_id: string;
  patient_identifier: string;
  patient_name: string | null;
  age_years: number | null;
  stage_group: string | null;
  created_at: string;
  updated_at: string;
  version_count: number;
  simulation_count: number;
  latest_case_version_id: string | null;
  latest_version_number: number | null;
  scenario_title: string;
};

type PatientCaseVersion = {
  case_version_id: string;
  patient_id: string;
  patient_name: string | null;
  version_number: number;
  case_snapshot_sha256: string;
  created_at: string;
  case: SyntheticCasePayload;
};

type PatientDetail = {
  patient_id: string;
  patient_identifier: string;
  patient_name: string | null;
  created_at: string;
  updated_at: string;
  versions: PatientCaseVersion[];
  runs: BatchRunSummary[];
};

type ActiveSavedCase = PatientCaseVersion & { patient_id: string; patient_identifier: string };

type PatientAssessmentRecord = {
  assessment_id: string;
  patient_id: string;
  case_version_id: string;
  agent_id: string;
  round_number: number;
  created_at: string;
  assessment: AgentAssessmentResult;
};

type BatchAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed";
  assessment: AgentAssessmentResult | null;
  error_message: string | null;
  duration_seconds: number | null;
};

type RoundSummary = {
  run_id: string;
  round_number: number;
  status: "queued" | "running" | "completed" | "completed_with_errors";
  total_agents: number;
  completed_count: number;
  failed_count: number;
  queued_count: number;
  running_count: number;
  finished_count: number;
  progress_percent: number;
  current_agent_id: string | null;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
};

type RoundAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed";
  result: {
    position: string;
    provisional_conclusion: string;
    response_to_other_perspectives: string;
    agreements: string[];
    substantive_challenges: string[];
    position_changes: string[];
    remaining_unknowns: string[];
    risk_flags: string[];
    case_data_integrity_flags?: string[];
    confidence: number;
  } | null;
  error_message: string | null;
  duration_seconds: number | null;
};

type FinalMDTReport = {
  run_id: string;
  round_number: 4;
  report_title: string;
  consensus_status: string;
  chair_conclusion: string;
  overall_educational_synthesis: string;
  consensus_points: string[];
  recorded_agreements?: string[];
  unresolved_disagreements: string[];
  minority_and_dissenting_views: string[];
  major_uncertainties: string[];
  missing_information_before_real_world_review: string[];
  patient_and_family_considerations: string[];
  feasibility_and_resource_considerations: string[];
  governance_and_safeguarding_considerations: string[];
  evidence_limitations: string[];
  chair_reflection: string;
  case_data_integrity_flags?: string[];
  evidence_retrieval_connected: false;
  not_a_treatment_instruction: true;
};

const emptyForm = {
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

function caseSnapshotToForm(snapshot: SyntheticCasePayload): typeof emptyForm {
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

function optionalText(value: string): string | null {
  const cleaned = value.trim();
  return cleaned ? cleaned : null;
}

function linesToList(value: string): string[] {
  return multilineTextToList(value);
}

function savedOptionalText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function savedStringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function readSavedCase(): SyntheticCasePayload | null {
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

function legacySavedCaseToDraft(_value: unknown): typeof emptyForm | null {
  const saved = readSavedCase();
  return saved ? caseSnapshotToForm(saved) : null;
}

function readSavedBatch(): BatchRunSummary | null {
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

function safeCaseDraftStorage(): Storage {
  try {
    return window.localStorage;
  } catch {
    // Accessing the localStorage property itself can throw in restricted browser contexts.
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

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [runtime, setRuntime] = useState<Runtime | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [connectionState, setConnectionState] = useState<"loading" | "connected" | "unavailable">("loading");
  const [patientRecords, setPatientRecords] = useState<PatientRecordSummary[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [loadedPatient, setLoadedPatient] = useState<PatientDetail | null>(null);
  const [selectedCaseVersionId, setSelectedCaseVersionId] = useState("");
  const [activeSavedCase, setActiveSavedCase] = useState<ActiveSavedCase | null>(null);
  const [selectedPatientRunId, setSelectedPatientRunId] = useState("");
  const [patientBusy, setPatientBusy] = useState(false);
  const [patientError, setPatientError] = useState("");
  const [form, setForm] = useState<typeof emptyForm>(() =>
    readDraft(safeCaseDraftStorage(), CASE_DRAFT_KEY, LEGACY_CASE_KEY, emptyForm, legacySavedCaseToDraft)
  );
  // Validation is intentionally session-only: a restored draft must be revalidated.
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validatedCase, setValidatedCase] = useState<SyntheticCasePayload | null>(null);
  const [validationError, setValidationError] = useState("");
  const [validating, setValidating] = useState(false);
  const [savedSingleAssessment, setSavedSingleAssessment] = useState<SavedSingleAssessment | null>(() =>
    readSavedSingleAssessment(safeCaseDraftStorage(), SINGLE_ASSESSMENT_KEY) as SavedSingleAssessment | null
  );
  const [assessmentPersistenceWarning, setAssessmentPersistenceWarning] = useState("");
  const agentAssessment = savedSingleAssessment && activeSavedCase &&
    JSON.stringify(savedSingleAssessment.case_snapshot) === JSON.stringify(activeSavedCase.case)
      ? savedSingleAssessment.assessment
      : null;
  const [assessmentError, setAssessmentError] = useState("");
  const [assessing, setAssessing] = useState(false);
  const [batchRun, setBatchRun] = useState<BatchRunSummary | null>(() => readSavedBatch());
  const [batchResults, setBatchResults] = useState<BatchAgentResult[]>([]);
  const [batchError, setBatchError] = useState("");
  const [batchStarting, setBatchStarting] = useState(false);
  const [batchResuming, setBatchResuming] = useState(false);
  const [roundSummaries, setRoundSummaries] = useState<Record<number, RoundSummary | null>>({});
  const [roundResults, setRoundResults] = useState<Record<number, RoundAgentResult[]>>({});
  const [finalReport, setFinalReport] = useState<FinalMDTReport | null>(null);
  const [roundActionBusy, setRoundActionBusy] = useState<number | null>(null);
  const [roundError, setRoundError] = useState("");
  const [agentFilter, setAgentFilter] = useState("All perspectives");

  async function refreshStatus() {
    setConnectionState("loading");
    try {
      const [healthResponse, runtimeResponse, agentsResponse] = await Promise.all([
        fetch(API_BASE + "/health"),
        fetch(API_BASE + "/api/runtime"),
        fetch(API_BASE + "/api/agents")
      ]);
      if (!healthResponse.ok || !runtimeResponse.ok || !agentsResponse.ok) {
        throw new Error("The local API returned an unsuccessful status.");
      }
      const healthData = (await healthResponse.json()) as Health;
      const runtimeData = (await runtimeResponse.json()) as { ollama: Runtime };
      const agentData = (await agentsResponse.json()) as { agents: Agent[] };
      setHealth(healthData);
      setRuntime(runtimeData.ollama);
      setAgents(agentData.agents);
      setConnectionState("connected");
    } catch {
      setHealth(null);
      setRuntime(null);
      setAgents([]);
      setConnectionState("unavailable");
    }
  }



  async function refreshPatients() {
    try {
      const response = await fetch(API_BASE + "/api/patients");
      if (!response.ok) throw new Error("Unable to load the patient registry.");
      const body = await response.json() as { patients: PatientRecordSummary[] };
      setPatientRecords(body.patients);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to load patient records.");
    }
  }

  async function loadPatientVersion(detail: PatientDetail, versionId: string) {
    const version = detail.versions.find((item) => item.case_version_id === versionId);
    if (!version) throw new Error("The selected saved case version was not found for this patient.");
    setLoadedPatient(detail);
    setSelectedPatientId(detail.patient_id);
    setSelectedCaseVersionId(version.case_version_id);
    setActiveSavedCase({ ...version, patient_id: detail.patient_id, patient_identifier: detail.patient_identifier });
    setForm({
      ...caseSnapshotToForm(version.case),
      patient_name: patientVersionDisplayName(version, detail.patient_name)
    });
    setValidation(null);
    setValidatedCase(null);
    setValidationError("");
    setAssessmentError("");
    setAssessmentPersistenceWarning("");

    const assessmentResponse = await fetch(
      API_BASE + "/api/patients/" + detail.patient_id + "/versions/" + version.case_version_id + "/assessments"
    );
    if (!assessmentResponse.ok) throw new Error("The saved RO-01 assessment history could not be loaded.");
    const assessmentBody = await assessmentResponse.json() as { assessments: PatientAssessmentRecord[] };
    const latestRo01 = assessmentBody.assessments.find((item) => item.agent_id === "RO-01");
    setSavedSingleAssessment(latestRo01 ? {
      version: 1,
      saved_at: latestRo01.created_at,
      case_snapshot: version.case,
      assessment: latestRo01.assessment,
      patient_id: detail.patient_id,
      case_version_id: version.case_version_id
    } : null);

    const matchingRuns = detail.runs.filter((run) => run.case_version_id === version.case_version_id);
    const latestRun = matchingRuns[0];
    setSelectedPatientRunId(latestRun?.run_id ?? "");
    if (latestRun) {
      await refreshBatchRun(latestRun.run_id);
    } else {
      setBatchRun(null);
      setBatchResults([]);
      setRoundSummaries({});
      setRoundResults({});
      setFinalReport(null);
      setBatchError("");
      setRoundError("");
    }
  }

  async function loadSelectedPatient() {
    if (!selectedPatientId) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      const response = await fetch(API_BASE + "/api/patients/" + selectedPatientId);
      const body = await response.json() as PatientDetail & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Unable to load the selected patient.");
      const latest = body.versions[0];
      if (!latest) throw new Error("This patient has no saved case versions.");
      await loadPatientVersion(body, latest.case_version_id);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to load the selected patient.");
    } finally {
      setPatientBusy(false);
    }
  }

  async function loadSelectedCaseVersion() {
    if (!loadedPatient || !selectedCaseVersionId) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      await loadPatientVersion(loadedPatient, selectedCaseVersionId);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to load the selected case version.");
    } finally {
      setPatientBusy(false);
    }
  }

  async function savePatientCase(createNewPatient: boolean) {
    if (!validation?.valid || !validatedCase || (!createNewPatient && !loadedPatient)) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      const patientName = form.patient_name.trim();
      if (patientName.length < 2) throw new Error("Enter a fictional training name before saving.");
      const url = createNewPatient
        ? API_BASE + "/api/patients"
        : API_BASE + "/api/patients/" + loadedPatient!.patient_id + "/versions";
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_name: patientName, case: validatedCase })
      });
      const body = await response.json() as PatientDetail & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "The patient case could not be saved.");
      const latest = body.versions[0];
      if (!latest) throw new Error("The saved patient record did not return a case version.");
      await refreshPatients();
      await loadPatientVersion(body, latest.case_version_id);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to save the patient case.");
    } finally {
      setPatientBusy(false);
    }
  }

  function clearPatientEntry(clearLinkedResults = false) {
    setForm(createBlankDraft(emptyForm));
    setValidation(null);
    setValidatedCase(null);
    setValidationError("");
    setPatientError("");
    setSelectedPatientId("");
    setLoadedPatient(null);
    setSelectedCaseVersionId("");
    setActiveSavedCase(null);
    setSelectedPatientRunId("");
    setAssessmentError("");
    setAssessmentPersistenceWarning("");
    if (clearLinkedResults) {
      setSavedSingleAssessment(null);
      setBatchRun(null);
      setBatchResults([]);
      setRoundSummaries({});
      setRoundResults({});
      setFinalReport(null);
      setBatchError("");
      setRoundError("");
      try { window.localStorage.removeItem("radonc-mdt-active-batch"); } catch { /* Storage may be unavailable. */ }
    }
    try { window.localStorage.removeItem(CASE_DRAFT_KEY); } catch { /* Storage may be unavailable. */ }
  }

  async function deleteSelectedPatient() {
    if (!loadedPatient || patientBusy) return;
    const patientId = loadedPatient.patient_id;
    const clearCurrentRun = batchRun?.patient_id === patientId || savedSingleAssessment?.patient_id === patientId;
    const confirmed = window.confirm(
      `Permanently delete ${loadedPatient.patient_identifier}? This also removes its saved case versions and all linked MDT simulation results. The serial number will not be reused.`
    );
    if (!confirmed) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      const response = await fetch(API_BASE + "/api/patients/" + patientId, { method: "DELETE" });
      const body = await response.json() as { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Unable to delete the patient record.");
      clearPatientEntry(clearCurrentRun);
      await refreshPatients();
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to delete the patient record.");
    } finally {
      setPatientBusy(false);
    }
  }

  async function loadSelectedPatientRun() {
    if (!selectedPatientRunId) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      await refreshBatchRun(selectedPatientRunId);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to load the selected simulation.");
    } finally {
      setPatientBusy(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
    void refreshPatients();
  }, []);

  const categories = useMemo(
    () => ["All perspectives", ...Array.from(new Set(agents.map((agent) => agent.category_label)))],
    [agents]
  );

  const filteredAgents = useMemo(
    () => agentFilter === "All perspectives"
      ? agents
      : agents.filter((agent) => agent.category_label === agentFilter),
    [agentFilter, agents]
  );

  async function validateSyntheticCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidation(null);
    setValidationError("");
    setValidating(true);

    const payload: SyntheticCasePayload = {
      scenario_title: form.scenario_title,
      case_summary: form.case_summary,
      age_years: form.age_years.trim() === "" ? null : Number(form.age_years),
      sex_at_birth: optionalText(form.sex_at_birth),
      primary_site: optionalText(form.primary_site),
      histology: optionalText(form.histology),
      clinical_t_stage: optionalText(form.clinical_t_stage),
      clinical_n_stage: optionalText(form.clinical_n_stage),
      clinical_m_stage: optionalText(form.clinical_m_stage),
      stage_group: optionalText(form.stage_group),
      performance_status: optionalText(form.performance_status),
      pathology_summary: optionalText(form.pathology_summary),
      imaging_summary: optionalText(form.imaging_summary),
      current_medications: linesToList(form.current_medications),
      known_allergies: linesToList(form.known_allergies),
      relevant_investigations: linesToList(form.relevant_investigations),
      relevant_comorbidities: linesToList(form.relevant_comorbidities),
      prior_treatment: linesToList(form.prior_treatment),
      patient_goals: linesToList(form.patient_goals),
      social_context: linesToList(form.social_context),
      resource_context: linesToList(form.resource_context),
      known_unknowns: linesToList(form.known_unknowns)
    };

    try {
      const response = await fetch(API_BASE + "/api/cases/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) {
        const details = Array.isArray(body.detail)
          ? body.detail.map((item: { msg?: string }) => item.msg ?? "Invalid input").join("; ")
          : "The case could not be validated.";
        throw new Error(details);
      }
      setValidation(body as ValidationResult);
      setValidatedCase(payload);
      setAssessmentError("");
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : "Unable to reach the local API.");
    } finally {
      setValidating(false);
    }
  }

  async function runAgentAssessment() {
    if (!activeSavedCase) return;
    setAssessing(true);
    setAssessmentError("");
    setAssessmentPersistenceWarning("");
    try {
      const response = await fetch(
        API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/versions/" + activeSavedCase.case_version_id + "/assess/RO-01",
        { method: "POST" }
      );
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "The local model could not produce a valid assessment.");
      }
      const savedResponse = body as { assessment: AgentAssessmentResult; created_at: string };
      const assessment = savedResponse.assessment;
      const savedAt = savedResponse.created_at;
      const savedRecord: SavedSingleAssessment = {
        version: 1,
        saved_at: savedAt,
        case_snapshot: activeSavedCase.case,
        assessment,
        patient_id: activeSavedCase.patient_id,
        case_version_id: activeSavedCase.case_version_id
      };
      setSavedSingleAssessment(savedRecord);
      const persisted = writeSavedSingleAssessment(
        safeCaseDraftStorage(),
        SINGLE_ASSESSMENT_KEY,
        activeSavedCase.case,
        assessment,
        savedAt
      );
      setAssessmentPersistenceWarning(
        persisted ? "" : "The assessment is saved in the backend patient record; the optional browser cache was unavailable."
      );
    } catch (error) {
      setAssessmentError(error instanceof Error ? error.message : "Unable to complete the local assessment.");
    } finally {
      setAssessing(false);
    }
  }

  useEffect(() => {
    // Persist editable raw strings independently of the validation snapshot.
    // If browser storage is unavailable, editing and validation remain usable in-session.
    writeDraft(safeCaseDraftStorage(), CASE_DRAFT_KEY, LEGACY_CASE_KEY, form);
  }, [form]);

  async function refreshMdtRound(roundNumber: number, runId = batchRun?.run_id) {
    if (!runId) return;
    try {
      const [summaryResponse, resultResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber),
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber + "/results")
      ]);
      if (summaryResponse.status === 404) {
        setRoundSummaries((current) => ({ ...current, [roundNumber]: null }));
        setRoundResults((current) => ({ ...current, [roundNumber]: [] }));
        return;
      }
      if (!summaryResponse.ok || !resultResponse.ok) {
        throw new Error("Unable to refresh Round " + roundNumber + ".");
      }
      const summary = (await summaryResponse.json()) as RoundSummary;
      const body = (await resultResponse.json()) as { results: RoundAgentResult[] };
      setRoundSummaries((current) => ({ ...current, [roundNumber]: summary }));
      setRoundResults((current) => ({ ...current, [roundNumber]: body.results }));
      if (roundNumber === 4 && ["completed", "completed_with_errors"].includes(summary.status)) {
        // R1 marks the parent run complete before the remaining MDT rounds finish.
        // Refresh the parent only at the terminal Chair stage to capture mdt_finished_at
        // and the correct overall status without losing the R2–R4 retry panel.
        await refreshBatchRun(runId);
        if (summary.status === "completed") {
          const reportResponse = await fetch(API_BASE + "/api/runs/" + runId + "/report");
          if (reportResponse.ok) setFinalReport((await reportResponse.json()) as FinalMDTReport);
        }
      }
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : "Unable to refresh MDT round.");
    }
  }

  async function startMdtRound(roundNumber: number, resume = false) {
    if (!batchRun) return;
    setRoundActionBusy(roundNumber);
    setRoundError("");
    try {
      const suffix = resume ? "/resume" : "";
      const response = await fetch(
        API_BASE + "/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + suffix,
        { method: "POST" }
      );
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to start Round " + roundNumber + ".");
      }
      setRoundSummaries((current) => ({ ...current, [roundNumber]: body as RoundSummary }));
      await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : "Unable to start MDT round.");
    } finally {
      setRoundActionBusy(null);
    }
  }

  useEffect(() => {
    if (!batchRun || !hasCompletedIndependentAssessments(batchRun)) return;
    const runId = batchRun.run_id;
    void refreshMdtRound(2, runId);
    void refreshMdtRound(3, runId);
    void refreshMdtRound(4, runId);
  }, [batchRun?.run_id, batchRun?.status]);

  useEffect(() => {
    if (!batchRun) return;
    const active = Object.values(roundSummaries).some(
      (summary) => summary?.status === "queued" || summary?.status === "running"
    );
    if (!active) return;
    const timer = window.setInterval(() => {
      for (const roundNumber of [2, 3, 4]) {
        const summary = roundSummaries[roundNumber];
        if (summary?.status === "queued" || summary?.status === "running") {
          void refreshMdtRound(roundNumber, batchRun.run_id);
        }
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, roundSummaries]);

  async function refreshBatchRun(runId: string) {
    try {
      const [runResponse, resultsResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId),
        fetch(API_BASE + "/api/runs/" + runId + "/results")
      ]);
      if (!runResponse.ok || !resultsResponse.ok) {
        throw new Error("Unable to refresh the 45-agent run.");
      }
      const runData = (await runResponse.json()) as BatchRunSummary;
      const resultsData = (await resultsResponse.json()) as { results: BatchAgentResult[] };
      setBatchRun(runData);
      setBatchResults(resultsData.results);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to refresh batch progress.");
    }
  }

  useEffect(() => {
    try {
      if (batchRun) {
        window.localStorage.setItem("radonc-mdt-active-batch", JSON.stringify(batchRun));
      } else {
        window.localStorage.removeItem("radonc-mdt-active-batch");
      }
    } catch {
      // The run remains persisted on the local backend even if browser storage is unavailable.
    }
  }, [batchRun]);

  useEffect(() => {
    if (batchRun) {
      void refreshBatchRun(batchRun.run_id);
    }
  }, []);

  useEffect(() => {
    if (!batchRun || batchRun.status === "completed" || batchRun.status === "completed_with_errors") {
      return;
    }
    const runId = batchRun.run_id;
    const timer = window.setInterval(() => {
      void refreshBatchRun(runId);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, batchRun?.status]);

  async function startAllAgents() {
    if (!activeSavedCase) return;
    setBatchStarting(true);
    setBatchError("");
    try {
      const response = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_version_id: activeSavedCase.case_version_id })
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to start the 45-agent run.");
      }
      const createdRun = body as BatchRunSummary;
      setBatchRun(createdRun);
      setBatchResults([]);
      setRoundSummaries({});
      setRoundResults({});
      setFinalReport(null);
      setRoundError("");
      setSelectedPatientRunId(createdRun.run_id);
      const patientResponse = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id);
      if (patientResponse.ok) setLoadedPatient(await patientResponse.json() as PatientDetail);
      await refreshPatients();
      await refreshBatchRun(createdRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to start the 45-agent run.");
    } finally {
      setBatchStarting(false);
    }
  }

  async function resumeAllAgents() {
    if (!batchRun) return;
    setBatchResuming(true);
    setBatchError("");
    try {
      const response = await fetch(API_BASE + "/api/runs/" + batchRun.run_id + "/resume", {
        method: "POST"
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Unable to resume the run.");
      }
      setBatchRun(body as BatchRunSummary);
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to resume the run.");
    } finally {
      setBatchResuming(false);
    }
  }

  async function downloadBatchResults() {
    if (!batchRun || batchResults.length === 0) return;
    setBatchError("");
    try {
      const caseResponse = await fetch(API_BASE + "/api/runs/" + batchRun.run_id + "/case");
      if (!caseResponse.ok) throw new Error("The saved case snapshot could not be retrieved.");
      const caseSnapshot = await caseResponse.json();
      const exportData = {
        simulator: "RadOnc MDT Simulator",
        mode: "four_round_educational_mdt_simulation",
        run: batchRun,
        case_snapshot: caseSnapshot.case,
        case_snapshot_json: caseSnapshot.case_snapshot_json,
        case_snapshot_sha256: caseSnapshot.case_snapshot_sha256,
        independent_assessments: batchResults,
        debate: roundResults[2] ?? [],
        adversarial_review: roundResults[3] ?? [],
        chair_synthesis: finalReport,
        round_status: roundSummaries,
        notice: "Fictional training simulation only. Evidence retrieval is not connected; no clinical decision support is provided."
      };
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "radonc-mdt-" + batchRun.run_id + "-simulation-export.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Could not export the simulation.");
    }
  }

  function updateField(field: keyof typeof emptyForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setValidation(null);
    setValidatedCase(null);
    setActiveSavedCase(null);
    setSelectedCaseVersionId("");
    setAssessmentError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="RadOnc MDT Simulator home">
          <span className="brand-mark">RO</span>
          <span>
            <strong>RadOnc MDT</strong>
            <small>SIMULATOR</small>
          </span>
        </a>
        <div className="topbar-right">
          <span className="environment-pill"><span className="status-dot" /> LOCAL ENVIRONMENT</span>
          <button className="button button-quiet" onClick={() => void refreshStatus()} disabled={connectionState === "loading"}>
            {connectionState === "loading" ? "Checking…" : "Refresh status"}
          </button>
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">ONCOLOGY EDUCATION · TRAINING RECORDS · LOCAL AI</p>
            <h1>Explore the case from<br /><em>every MDT perspective.</em></h1>
            <p className="hero-description">
              A structured learning workspace for multidisciplinary oncology discussion,
              evidence appraisal, patient context, and clinical uncertainty.
            </p>
          </div>
          <div className="hero-side">
            <span className="hero-number">45</span>
            <span className="hero-number-label">configured perspectives</span>
            <div className="hero-divider" />
            <span className="hero-number">04</span>
            <span className="hero-number-label">discussion rounds planned</span>
          </div>
        </section>

        <section className="safety-banner" role="note">
          <span className="safety-icon">!</span>
          <div>
            <strong>Educational simulation only</strong>
            <p>Use fictional training records only. Do not enter real patient information. This prototype is not a hospital registration system, medical device, or clinical decision-support system; it is not a substitute for a qualified MDT.</p>
          </div>
        </section>

        <section className="status-grid" aria-label="Local system status">
          <StatusCard
            label="Backend API"
            value={connectionState === "connected" ? "Connected" : connectionState === "loading" ? "Checking" : "Unavailable"}
            detail={health ? health.application + " · v" + health.version : "Start the local FastAPI service"}
            state={connectionState === "connected" ? "good" : connectionState === "loading" ? "neutral" : "bad"}
          />
          <StatusCard
            label="Ollama runtime"
            value={runtime?.reachable ? "Reachable" : runtime ? "Unavailable" : "Not checked"}
            detail={runtime?.reachable ? "Ollama " + runtime.version : "Expected at 127.0.0.1:11434"}
            state={runtime?.reachable ? "good" : "neutral"}
          />
          <StatusCard
            label="Local model"
            value={runtime?.configured_model_installed ? "Installed" : "Not verified"}
            detail={runtime?.configured_model ?? "qwen3.5:4b"}
            state={runtime?.configured_model_installed ? "good" : "neutral"}
          />
          <StatusCard
            label="Agent catalogue"
            value={agents.length === 45 ? "45 / 45 loaded" : agents.length + " loaded"}
            detail="All configured roles are listed"
            state={agents.length === 45 ? "good" : "neutral"}
          />
        </section>

        <div className="workspace-grid">
          <section className="panel case-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">01 / CASE WORKSPACE</p>
                <h2>Patient registration and case entry</h2>
              </div>
              <span className="panel-index">CASE INPUT</span>
            </div>
            <p className="panel-intro">
              Enter fictional training details. Validation checks the data structure only; it does not assess diagnosis or treatment.
            </p>

            <div className="result-card patient-library" aria-label="Training patient registry">
              <strong>Patient Registry</strong>
              <p>Register or load a fictional training patient. Its local ID is generated sequentially (RAD-000001, RAD-000002, …); it is not a hospital medical-record number and does not register anyone with a hospital.</p>
              <div className="field-row">
                <label>
                  Registered patient
                  <select value={selectedPatientId} onChange={(event) => setSelectedPatientId(event.target.value)}>
                    <option value="">Select a patient record</option>
                    {patientRecords.map((patient) => (
                      <option key={patient.patient_id} value={patient.patient_id}>
                        {patient.patient_identifier} · {patient.patient_name ?? "Name not recorded"} · {patient.age_years ?? "Age unknown"} · {patient.scenario_title} · {patient.stage_group ?? "Stage not recorded"} · v{patient.latest_version_number ?? "—"}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="button button-secondary" type="button" onClick={() => void loadSelectedPatient()} disabled={!selectedPatientId || patientBusy}>
                  {patientBusy ? "Loading…" : "Load patient"}
                </button>
              </div>
              {loadedPatient && (
                <>
                  <p className="result-footnote">Loaded patient: {loadedPatient.patient_identifier} · {loadedPatient.versions.length} immutable case version(s) · {loadedPatient.runs.length} linked simulation(s).</p>
                  <div className="field-row">
                    <label>
                      Saved case version
                      <select value={selectedCaseVersionId} onChange={(event) => setSelectedCaseVersionId(event.target.value)}>
                        {loadedPatient.versions.map((version) => (
                          <option key={version.case_version_id} value={version.case_version_id}>
                            Version {version.version_number} · {version.case.scenario_title}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button className="button button-secondary" type="button" onClick={() => void loadSelectedCaseVersion()} disabled={!selectedCaseVersionId || patientBusy}>
                      Load version
                    </button>
                  </div>
                  {loadedPatient.runs.length > 0 && (
                    <div className="field-row">
                      <label>
                        Simulation history
                        <select value={selectedPatientRunId} onChange={(event) => setSelectedPatientRunId(event.target.value)}>
                          <option value="">Select a linked simulation</option>
                          {loadedPatient.runs.map((run) => (
                            <option key={run.run_id} value={run.run_id}>
                              {run.run_id.slice(0, 8)} · Version {run.case_version_number ?? "legacy"} · {run.status}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button className="button button-secondary" type="button" onClick={() => void loadSelectedPatientRun()} disabled={!selectedPatientRunId || patientBusy}>
                        Open results
                      </button>
                    </div>
                  )}
                </>
              )}
              {activeSavedCase && (
                <p className="result-footnote">Active simulation snapshot: {activeSavedCase.patient_identifier} · Version {activeSavedCase.version_number} · SHA-256 {activeSavedCase.case_snapshot_sha256}. Editing this form detaches it from this saved version until you save a new version.</p>
              )}
              {loadedPatient && (
                <div className="batch-actions">
                  <button className="button button-secondary" type="button" onClick={() => void deleteSelectedPatient()} disabled={patientBusy}>
                    {patientBusy ? "Working…" : "Delete patient and linked results"}
                  </button>
                </div>
              )}
              <div className="batch-actions">
                <button className="button button-quiet" type="button" onClick={() => clearPatientEntry()} disabled={patientBusy}>Clear unsaved form and selection</button>
              </div>
              {patientError && <p className="error-text" role="alert">{patientError}</p>}
              {patientRecords.length === 0 && <p className="result-footnote">No training patients registered yet. Complete the fictional patient and clinical details below, validate, then save the record.</p>}
            </div>

            <form onSubmit={validateSyntheticCase} className="case-form">
              <label>
                Fictional patient name <span className="required-mark">*</span>
                <input required minLength={2} maxLength={120} value={form.patient_name} onChange={(event) => updateField("patient_name", event.target.value)} placeholder="Use a fictional name or training alias" />
              </label>

              <label>
                Diagnosis / MDT case title
                <input
                  required
                  minLength={3}
                  maxLength={160}
                  value={form.scenario_title}
                  onChange={(event) => updateField("scenario_title", event.target.value)}
                  placeholder="e.g. Oropharyngeal carcinoma"
                />
              </label>

              <label>
                Clinical summary <span className="required-mark">*</span>
                <textarea
                  required
                  minLength={10}
                  maxLength={12000}
                  rows={5}
                  value={form.case_summary}
                  onChange={(event) => updateField("case_summary", event.target.value)}
                  placeholder="Describe the training presentation and relevant context. Do not include real patient information."
                />
              </label>

              <div className="field-row">
                <label>
                  Age (optional)
                  <input
                    type="number"
                    min="0"
                    max="120"
                    step="1"
                    value={form.age_years}
                    onChange={(event) => updateField("age_years", event.target.value)}
                    placeholder="Unknown"
                  />
                </label>
                <label>
                  Primary site
                  <input
                    value={form.primary_site}
                    onChange={(event) => updateField("primary_site", event.target.value)}
                    placeholder="e.g. Oropharynx"
                  />
                </label>
              </div>

              <label>
                Histology
                <input
                  value={form.histology}
                  onChange={(event) => updateField("histology", event.target.value)}
                  placeholder="e.g. Squamous cell carcinoma"
                />
              </label>

              <details className="structured-fields">
                <summary>Additional structured case details (optional)</summary>
                <p>
                  Enter only documented information. Blank means not reported, not negative.
                  Keep the original narrative above unchanged; discrepancies are flagged rather
                  than automatically reconciled. Do not infer stage, fitness or patient goals.
                </p>
                <div className="structured-fields-grid">
                  <label>
                    Sex at birth
                    <input value={form.sex_at_birth} onChange={(event) => updateField("sex_at_birth", event.target.value)} placeholder="Not reported" />
                  </label>
                  <label>
                    Performance status
                    <input value={form.performance_status} onChange={(event) => updateField("performance_status", event.target.value)} placeholder="e.g. ECOG 1, if documented" />
                  </label>
                  <label>
                    Clinical T stage
                    <input value={form.clinical_t_stage} onChange={(event) => updateField("clinical_t_stage", event.target.value)} placeholder="e.g. cT2, if documented" />
                  </label>
                  <label>
                    Clinical N stage
                    <input value={form.clinical_n_stage} onChange={(event) => updateField("clinical_n_stage", event.target.value)} placeholder="e.g. cN1, if documented" />
                  </label>
                  <label>
                    Clinical M stage
                    <input value={form.clinical_m_stage} onChange={(event) => updateField("clinical_m_stage", event.target.value)} placeholder="e.g. cM1, if documented" />
                  </label>
                  <label>
                    Stage group
                    <input value={form.stage_group} onChange={(event) => updateField("stage_group", event.target.value)} placeholder="Only if explicitly documented" />
                  </label>
                  <label className="full-width">
                    Pathology summary
                    <textarea rows={3} value={form.pathology_summary} onChange={(event) => updateField("pathology_summary", event.target.value)} placeholder="Documented pathology details only; leave blank if not supplied." />
                  </label>
                  <label className="full-width">
                    Imaging summary
                    <textarea rows={3} value={form.imaging_summary} onChange={(event) => updateField("imaging_summary", event.target.value)} placeholder="Documented imaging findings only; do not infer N or M status." />
                  </label>
                  <label>
                    Current medications
                    <textarea className="structured-list-input" rows={2} value={form.current_medications} onChange={(event) => updateField("current_medications", event.target.value)} placeholder="Documented medicines only; one per line" />
                  </label>
                  <label>
                    Known allergies
                    <textarea className="structured-list-input" rows={2} value={form.known_allergies} onChange={(event) => updateField("known_allergies", event.target.value)} placeholder="Documented allergies only; one per line" />
                  </label>
                  <label className="full-width">
                    Relevant investigations
                    <textarea className="structured-list-input" rows={3} value={form.relevant_investigations} onChange={(event) => updateField("relevant_investigations", event.target.value)} placeholder="Investigation name, date and documented result; one per line" />
                  </label>
                  <label>
                    Relevant comorbidities
                    <textarea className="structured-list-input" rows={2} value={form.relevant_comorbidities} onChange={(event) => updateField("relevant_comorbidities", event.target.value)} placeholder="One documented item per line" />
                  </label>
                  <label>
                    Prior treatment
                    <textarea className="structured-list-input" rows={2} value={form.prior_treatment} onChange={(event) => updateField("prior_treatment", event.target.value)} placeholder="One documented item per line" />
                  </label>
                  <label>
                    Patient goals
                    <textarea className="structured-list-input" rows={2} value={form.patient_goals} onChange={(event) => updateField("patient_goals", event.target.value)} placeholder="Patient-stated goals only; one per line" />
                  </label>
                  <label>
                    Social context
                    <textarea className="structured-list-input" rows={2} value={form.social_context} onChange={(event) => updateField("social_context", event.target.value)} placeholder="One documented item per line" />
                  </label>
                  <label>
                    Resource context
                    <textarea className="structured-list-input" rows={2} value={form.resource_context} onChange={(event) => updateField("resource_context", event.target.value)} placeholder="One documented item per line" />
                  </label>
                  <label className="full-width">
                    Known unknowns
                    <textarea className="structured-list-input" rows={2} value={form.known_unknowns} onChange={(event) => updateField("known_unknowns", event.target.value)} placeholder="One outstanding question or missing investigation per line" />
                  </label>
                </div>
              </details>

              <div className="form-footer">
                <span className="form-note">Use fictional training aliases only. Do not enter real names, medical record numbers, contact details or other identifying information.</span>
                <button className="button button-primary" type="submit" disabled={validating || connectionState !== "connected"}>
                  {validating ? "Validating…" : "Validate patient details"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </form>

            {validation && validatedCase && (
              <div className="patient-save-actions result-card">
                <strong>Save patient record</strong>
                <p>MDT simulation is enabled only for a saved patient record. Saving changes creates a new immutable version; previous versions and results remain unchanged.</p>
                <div className="batch-actions">
                  <button className="button button-primary" type="button" onClick={() => void savePatientCase(true)} disabled={patientBusy}>
                    Register new patient
                  </button>
                  {loadedPatient && (
                    <button className="button button-secondary" type="button" onClick={() => void savePatientCase(false)} disabled={patientBusy || selectedPatientId !== loadedPatient.patient_id || activeSavedCase !== null}>
                      Save new version of {loadedPatient.patient_identifier}
                    </button>
                  )}
                </div>
              </div>
            )}

            {validation && (
              <div className="result-card result-success" role="status">
                <strong>Case structure valid</strong>
                <p>{validation.note}</p>
                {validation.warnings.length > 0 && (
                  <ul>{validation.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                )}
                <p className="result-footnote">Case structure is validated. Once all 45 independent assessments finish, the debate, adversarial review and Chair synthesis stages become available below.</p>
              </div>
            )}
            {activeSavedCase && (
              <div className="assessment-launch">
                <div>
                  <strong>Try one local agent</strong>
                  <p>Run the guideline-focused Radiation Oncology perspective (RO-01) on {activeSavedCase.patient_identifier}, case version {activeSavedCase.version_number}. The result is saved in the patient record.</p>
                </div>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => void runAgentAssessment()}
                  disabled={assessing || !runtime?.reachable || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
                >
                  {assessing ? "Generating locally…" : "Run RO-01 assessment"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            )}
            {assessmentError && (
              <div className="result-card result-error" role="alert">
                <strong>Local assessment failed</strong>
                <p>{assessmentError}</p>
              </div>
            )}
            {agentAssessment && (
              <div className="result-card result-success agent-assessment" role="status">
                <div className="assessment-header">
                  <strong>RO-01 · Guideline-focused Radiation Oncologist</strong>
                  <span>Round {agentAssessment.round_number}</span>
                </div>
                {savedSingleAssessment && (
                  <>
                    <p className="result-footnote">
                      Saved {new Date(savedSingleAssessment.saved_at).toLocaleString()} · assessed case:
                      {" "}{savedSingleAssessment.case_snapshot.scenario_title}. This result remains tied to
                      its saved case snapshot; editing the current draft does not alter the assessment.
                    </p>
                    <details className="structured-fields">
                      <summary>View the exact case snapshot used for this assessment</summary>
                      <p>{savedSingleAssessment.case_snapshot.case_summary}</p>
                    </details>
                    {assessmentPersistenceWarning && (
                      <p className="error-text" role="status">{assessmentPersistenceWarning}</p>
                    )}
                    <p className="result-footnote">Backend record: {loadedPatient?.patient_identifier ?? "legacy saved result"} · case version {savedSingleAssessment.case_version_id ?? "not linked"}.</p>
                  </>
                )}
                <div className="assessment-conclusion">
                  <strong>Provisional conclusion · {agentAssessment.position.replaceAll("_", " ")}</strong>
                  <p>{agentAssessment.provisional_conclusion}</p>
                  <strong>Preferred educational option</strong>
                  <p>{agentAssessment.preferred_educational_option}</p>
                </div>
                <p>{agentAssessment.perspective_summary}</p>
                {agentAssessment.discussion_options.length > 0 && (
                  <>
                    <strong>Topics for MDT discussion</strong>
                    <ul>{agentAssessment.discussion_options.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                {agentAssessment.unknowns.length > 0 && (
                  <>
                    <strong>Unknowns identified</strong>
                    <ul>{agentAssessment.unknowns.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                {agentAssessment.evidence_gaps.length > 0 && (
                  <>
                    <strong>Evidence gaps</strong>
                    <ul>{agentAssessment.evidence_gaps.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </>
                )}
                <p className="result-footnote">
                  Model self-reported confidence: {Math.round(agentAssessment.confidence * 100)}%.
                  Evidence claims accepted: {agentAssessment.evidence_claims.length}.
                  No evidence retrieval is connected yet; this is not a treatment recommendation.
                </p>
              </div>
            )}
            {(shouldShowBatchPanel(batchRun, validation, validatedCase) || activeSavedCase !== null) && (
              <section className="batch-run-panel">
                <div className="batch-heading">
                  <div>
                    <p className="eyebrow">03 / INDEPENDENT ASSESSMENTS</p>
                    <h3>Run all 45 MDT perspectives</h3>
                  </div>
                  <span className="count-chip">45 REQUIRED</span>
                </div>
                <p className="panel-intro">
                  Each agent receives only the saved training case snapshot and its own role profile. Agents do not see one another's assessments. Results are saved locally as they finish.
                </p>
                {batchRun && (
                  <div className="result-card" role="note">
                    <strong>Saved MDT run · {batchRun.status.replaceAll("_", " ")}</strong>
                    <p>Displayed contributions belong to the immutable case snapshot saved with this run. Editing the current draft does not change the saved run.</p>
                    <p className="result-footnote">Run ID: {batchRun.run_id} · Patient: {loadedPatient?.patient_identifier ?? (batchRun.patient_id ? "linked patient" : "legacy unlinked run")} · Case version: {batchRun.case_version_number ?? "not linked"} · SHA-256: {batchRun.case_snapshot_sha256}</p>
                  </div>
                )}
                <div className="batch-actions">
                  {activeSavedCase && (
                    <button
                      className="button button-primary"
                      type="button"
                      onClick={() => void startAllAgents()}
                      disabled={batchStarting || batchResuming || assessing || !runtime?.reachable || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
                    >
                      {batchStarting ? "Starting…" : "Run all 45 agents"}
                      <span aria-hidden="true">→</span>
                    </button>
                  )}
                  {!activeSavedCase && !batchRun && (
                    <p className="batch-estimate-note">Save a validated patient record, or load an existing patient and case version, before starting a new 45-agent run.</p>
                  )}
                  {batchRun && batchResults.length > 0 && (
                    <button className="button button-quiet" type="button" onClick={downloadBatchResults}>
                      Export JSON
                    </button>
                  )}
                  {shouldOfferIndependentBatchResume(batchRun) && (
                    <button
                      className="button button-secondary"
                      type="button"
                      onClick={() => void resumeAllAgents()}
                      disabled={batchResuming || batchStarting}
                    >
                      {batchResuming ? "Resuming…" : batchRun.status === "completed_with_errors" ? "Retry failed agents" : "Recover interrupted run"}
                    </button>
                  )}
                </div>
                {batchRun && (
                  <div className="batch-status" aria-live="polite">
                    <div className="batch-status-top">
                      <strong>
                        {batchRun.status === "queued" ? "Queued" :
                          batchRun.status === "running" ? "Running independently" :
                          batchRun.status === "completed" ? "All 45 assessments completed" :
                          "Completed with some errors"}
                      </strong>
                      <span>{batchRun.finished_count} / {batchRun.total_agents} finished</span>
                    </div>
                    <div className="batch-progress-track">
                      <div className="batch-progress-fill" style={{ width: batchRun.progress_percent + "%" }} />
                    </div>
                    <div className="batch-counts">
                      <span className="count-complete">{batchRun.completed_count} completed</span>
                      <span className="count-failed">{batchRun.failed_count} failed</span>
                      <span>{batchRun.queued_count + batchRun.running_count} remaining</span>
                      {batchRun.current_agent_id && <span>Now: {batchRun.current_agent_id}</span>}
                    </div>
                    {batchRun.status === "running" && (
                      <p className="batch-estimate-note">This runs locally and sequentially. It may take several minutes. Keep the dashboard, backend and laptop running until it finishes.</p>
                    )}
                  </div>
                )}
                {batchError && <div className="result-card result-error" role="alert">{batchError}</div>}
                {batchResults.length > 0 && (
                  <div className="batch-results">
                    <div className="batch-results-title">
                      <strong>Agent results</strong>
                      <span>{batchResults.length} records saved locally</span>
                    </div>
                    {batchResults.map((item) => (
                      <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                        <summary>
                          <span className="agent-id">{item.agent_id}</span>
                          <strong>{item.agent_name}</strong>
                          <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                          {item.duration_seconds !== null && <span className="agent-duration">{item.duration_seconds.toFixed(1)}s</span>}
                        </summary>
                        {item.assessment ? (
                          <div className="batch-agent-body">
                            <div className="assessment-conclusion">
                              <strong>Provisional conclusion · {item.assessment.position.replaceAll("_", " ")}</strong>
                              <p>{item.assessment.provisional_conclusion}</p>
                              <strong>Preferred educational option</strong>
                              <p>{item.assessment.preferred_educational_option}</p>
                            </div>
                            <p>{item.assessment.perspective_summary}</p>
                            {(item.assessment.case_facts ?? []).length > 0 && (
                              <>
                                <strong>Source case facts · snapshot-derived</strong>
                                <ul>{(item.assessment.case_facts ?? []).map((fact, index) => <li key={index}>{fact}</li>)}</ul>
                              </>
                            )}
                            {(item.assessment.case_data_integrity_flags ?? []).length > 0 && (
                              <div className="result-card result-error" role="status">
                                <strong>Case-data integrity flags · review required</strong>
                                <ul>{(item.assessment.case_data_integrity_flags ?? []).map((flag, index) => <li key={index}>{flag}</li>)}</ul>
                              </div>
                            )}
                            {item.assessment.discussion_options.length > 0 && (
                              <>
                                <strong>Discussion topics</strong>
                                <ul>{item.assessment.discussion_options.map((option, index) => <li key={index}>{option}</li>)}</ul>
                              </>
                            )}
                            {item.assessment.unknowns.length > 0 && (
                              <>
                                <strong>Unknowns</strong>
                                <ul>{item.assessment.unknowns.map((unknown, index) => <li key={index}>{unknown}</li>)}</ul>
                              </>
                            )}
                            {item.assessment.evidence_gaps.length > 0 && (
                              <>
                                <strong>Evidence gaps</strong>
                                <ul>{item.assessment.evidence_gaps.map((gap, index) => <li key={index}>{gap}</li>)}</ul>
                              </>
                            )}
                            <p className="result-footnote">
                              Model self-reported confidence: {Math.round(item.assessment.confidence * 100)}%.
                              Evidence claims accepted: {item.assessment.evidence_claims.length}.
                            </p>
                          </div>
                        ) : item.error_message ? (
                          <div className="batch-agent-body"><p className="error-text">{item.error_message}</p></div>
                        ) : (
                          <div className="batch-agent-body"><p>Waiting for this independent assessment.</p></div>
                        )}
                      </details>
                    ))}
                  </div>
                )}
                <p className="result-footnote">All outputs are simulated educational perspectives, not clinician opinions or treatment instructions. No evidence retrieval is connected yet.</p>
              </section>
            )}
            {hasCompletedIndependentAssessments(batchRun) && (
              <section className="mdt-rounds-panel">
                <div className="batch-heading">
                  <div>
                    <p className="eyebrow">04 / MDT DISCUSSION</p>
                    <h3>Four-round MDT workflow</h3>
                  </div>
                  <span className="count-chip">45 ROLES</span>
                </div>
                <p className="panel-intro">The debate and review stages ask each role to respond independently to a compact digest of other perspectives. Round 4 produces a chair synthesis that retains dissent and states the evidence limitations.</p>
                {formatElapsedDuration(batchRun?.created_at, batchRun?.mdt_finished_at) && (
                  <p className="result-footnote">
                    Full MDT elapsed time: {formatElapsedDuration(batchRun?.created_at, batchRun?.mdt_finished_at)} from run creation to the end of Round 4, including any pauses between rounds.
                  </p>
                )}
                {[2, 3, 4].map((roundNumber) => {
                  const summary = roundSummaries[roundNumber];
                  const roundElapsed = formatElapsedDuration(summary?.started_at, summary?.finished_at);
                  const isPreviousComplete = roundNumber === 2
                    ? hasCompletedIndependentAssessments(batchRun)
                    : roundSummaries[roundNumber - 1]?.status === "completed";
                  const isRetryable = summary?.status === "completed_with_errors";
                  const title = roundNumber === 2 ? "MDT debate" : roundNumber === 3 ? "Adversarial review" : "MDT Chair synthesis";
                  const description = roundNumber === 2
                    ? "All 45 roles respond to selected peer positions, state agreements and challenges, and explain any change in position."
                    : roundNumber === 3
                    ? "All 45 roles challenge unsupported assumptions, evidence gaps, patient-context issues, feasibility and governance risks."
                    : "The MDT Chair assembles consensus, unresolved disagreements, minority views, uncertainties and missing information.";
                  const results = roundResults[roundNumber] ?? [];
                  return (
                    <div className="round-stage" key={roundNumber}>
                      <div className="round-stage-heading">
                        <div>
                          <span className="round-number">ROUND {roundNumber}</span>
                          <strong>{title}</strong>
                          <p>{description}</p>
                        </div>
                        {summary && <span className={"round-state state-" + summary.status}>{summary.status.replaceAll("_", " ")}</span>}
                      </div>
                      {!summary && (
                        <button
                          className="button button-secondary"
                          type="button"
                          disabled={!isPreviousComplete || roundActionBusy !== null}
                          onClick={() => void startMdtRound(roundNumber)}
                        >
                          {roundActionBusy === roundNumber ? "Starting…" : roundNumber === 4 ? "Generate final MDT report" : "Start Round " + roundNumber}
                          <span aria-hidden="true">→</span>
                        </button>
                      )}
                      {summary && (
                        <>
                          <div className="batch-status">
                            <div className="batch-status-top">
                              <strong>{summary.status === "completed" ? "Stage completed" : summary.status === "completed_with_errors" ? "Completed with errors" : "Stage running"}</strong>
                              <span>{summary.finished_count} / {summary.total_agents} finished</span>
                            </div>
                            <div className="batch-progress-track">
                              <div className="batch-progress-fill" style={{ width: summary.progress_percent + "%" }} />
                            </div>
                            <div className="batch-counts">
                              <span className="count-complete">{summary.completed_count} completed</span>
                              <span className="count-failed">{summary.failed_count} failed</span>
                              <span>{summary.queued_count + summary.running_count} remaining</span>
                              {summary.current_agent_id && <span>Now: {summary.current_agent_id}</span>}
                              {roundElapsed && <span>Attempt duration: {roundElapsed}</span>}
                            </div>
                          </div>
                          {(isRetryable || (summary.status === "running" && Date.now() - Date.parse(summary.updated_at) > 120000)) && (
                            <button
                              className="button button-secondary"
                              type="button"
                              disabled={roundActionBusy !== null}
                              onClick={() => void startMdtRound(roundNumber, true)}
                            >
                              {roundActionBusy === roundNumber ? "Resuming…" : "Resume failed/interrupted work"}
                            </button>
                          )}
                          {roundNumber !== 4 && results.length > 0 && (
                            <div className="round-agent-list">
                              {results.map((item) => (
                                <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                                  <summary>
                                    <span className="agent-id">{item.agent_id}</span>
                                    <strong>{item.agent_name}</strong>
                                    <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                                  </summary>
                                  {item.result && (
                                    <div className="batch-agent-body">
                                      <strong>Position · {item.result.position.replaceAll("_", " ")}</strong>
                                      <p>{item.result.provisional_conclusion}</p>
                                      <strong>Response to other perspectives</strong>
                                      <p>{item.result.response_to_other_perspectives}</p>
                                      {(item.result.position_changes ?? []).length > 0 && <><strong>Recorded position change</strong><ul>{(item.result.position_changes ?? []).map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                      {(item.result.case_data_integrity_flags ?? []).length > 0 && (
                                        <div className="result-card result-error" role="status">
                                          <strong>Case-data integrity flags · review required</strong>
                                          <ul>{(item.result.case_data_integrity_flags ?? []).map((flag, index) => <li key={index}>{flag}</li>)}</ul>
                                        </div>
                                      )}
                                      {item.result.agreements.length > 0 && <><strong>Agreements</strong><ul>{item.result.agreements.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                      {item.result.substantive_challenges.length > 0 && <><strong>Challenges</strong><ul>{item.result.substantive_challenges.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                      {item.result.risk_flags.length > 0 && <><strong>Risk flags</strong><ul>{item.result.risk_flags.map((value, index) => <li key={index}>{value}</li>)}</ul></>}
                                    </div>
                                  )}
                                  {item.error_message && <div className="batch-agent-body"><p className="error-text">{item.error_message}</p></div>}
                                </details>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
                {roundError && <div className="result-card result-error" role="alert">{roundError}</div>}
                {finalReport && (
                  <div className="final-mdt-report">
                    <div className="assessment-conclusion">
                      <p className="eyebrow">ROUND 4 · CHAIR SYNTHESIS</p>
                      <h4>{finalReport.report_title}</h4>
                      <strong>Consensus status · {finalReport.consensus_status.replaceAll("_", " ")}</strong>
                      <p>{finalReport.chair_conclusion}</p>
                      <strong>Overall educational synthesis</strong>
                      <p>{finalReport.overall_educational_synthesis}</p>
                    </div>
                    {([
                      ["Proposition-level consensus", finalReport.consensus_points],
                      ["Recorded agreements · attributed, not consensus", finalReport.recorded_agreements ?? []],
                      ["Unresolved disagreements", finalReport.unresolved_disagreements],
                      ["Minority and dissenting views", finalReport.minority_and_dissenting_views],
                      ["Major uncertainties", finalReport.major_uncertainties],
                      ["Missing information before real-world review", finalReport.missing_information_before_real_world_review],
                      ["Patient and family considerations", finalReport.patient_and_family_considerations],
                      ["Feasibility and resource considerations", finalReport.feasibility_and_resource_considerations],
                      ["Governance and safeguarding considerations", finalReport.governance_and_safeguarding_considerations],
                      ["Evidence limitations", finalReport.evidence_limitations],
                      ["Case-data integrity flags", finalReport.case_data_integrity_flags ?? []]
                    ] as [string, string[]][]).map(([heading, items]) => (
                      <div className="report-section" key={heading}>
                        <strong>{heading}</strong>
                        {items.length > 0 ? <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>None recorded in this simulation.</p>}
                      </div>
                    ))}
                    <div className="report-section">
                      <strong>Chair reflection</strong>
                      <p>{finalReport.chair_reflection}</p>
                    </div>
                    <p className="result-footnote">Evidence retrieval is not connected. This report is an educational synthesis, not a clinical recommendation or treatment instruction.</p>
                  </div>
                )}
              </section>
            )}
            {validationError && (
              <div className="result-card result-error" role="alert">
                <strong>Validation failed</strong>
                <p>{validationError}</p>
              </div>
            )}
          </section>

          <section className="panel agents-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">02 / MDT PERSPECTIVES</p>
                <h2>Agent directory</h2>
              </div>
              <span className="count-chip">{agents.length || 45} ROLES</span>
            </div>
            <p className="panel-intro">
              Every role is intended to participate in each simulation. These are role profiles, not separate AI models or real clinician opinions.
            </p>

            <label className="filter-label">
              Filter by perspective
              <select value={agentFilter} onChange={(event) => setAgentFilter(event.target.value)}>
                {categories.map((category) => <option key={category}>{category}</option>)}
              </select>
            </label>

            <div className="agent-list">
              {filteredAgents.map((agent) => (
                <article className="agent-item" key={agent.agent_id}>
                  <span className="agent-id">{agent.agent_id}</span>
                  <div className="agent-copy">
                    <strong>{agent.name}</strong>
                    <p>{agent.mandate}</p>
                  </div>
                </article>
              ))}
              {agents.length === 0 && (
                <p className="empty-state">The agent catalogue will appear when the backend API is running.</p>
              )}
            </div>
            <p className="directory-footnote">Showing {filteredAgents.length} of {agents.length} configured perspectives.</p>
          </section>
        </div>

        <footer className="footer">
          <span>RADONC MDT SIMULATOR <span className="footer-separator">/</span> LOCAL-FIRST PROTOTYPE</span>
          <span>Research and education only · Fictional training data only</span>
        </footer>
      </main>
    </div>
  );
}

function StatusCard({
  label,
  value,
  detail,
  state
}: {
  label: string;
  value: string;
  detail: string;
  state: "good" | "bad" | "neutral";
}) {
  return (
    <article className="status-card">
      <div className="status-card-top">
        <span>{label}</span>
        <span className={"status-light " + state} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export default App;
