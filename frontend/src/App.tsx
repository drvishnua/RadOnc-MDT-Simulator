import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { readDraft, writeDraft, createBlankDraft } from "./caseDraft.js";
import { readSavedSingleAssessment, writeSavedSingleAssessment } from "./singleAssessmentStorage.js";
import { hasCompletedIndependentAssessments, shouldShowBatchPanel } from "./runRecovery.js";
import { patientVersionDisplayName } from "./patientVersionName.js";
import { formatElapsedDuration } from "./roundTiming.js";
import { PRESET_CASES } from "./presetCases.js";
import type { LandmarkTrial } from "./clinicalEvidence.js";
import { applyPerturbation } from "./clinicalPerturbations.js";
import type {
  ActiveSavedCase,
  Agent,
  AgentAssessmentResult,
  BatchAgentResult,
  BatchRunSummary,
  FinalMDTReport,
  Health,
  IntakeScreening,
  PatientAssessmentRecord,
  PatientDetail,
  PatientRecordSummary,
  PendingIntake,
  RoundAgentResult,
  RoundQualityAudit,
  RoundSummary,
  Runtime,
  SavedSingleAssessment,
  SyntheticCasePayload,
  ValidationResult,
} from "./types.js";
import {
  API_BASE,
  CASE_DRAFT_KEY,
  FOCUSED_PANELS,
  LEGACY_CASE_KEY,
  PENDING_INTAKE_KEY,
  SINGLE_ASSESSMENT_KEY,
  caseSnapshotToForm,
  emptyForm,
  legacySavedCaseToDraft,
  linesToList,
  optionalText,
  readPendingIntakePointer,
  readSavedBatch,
  safeCaseDraftStorage,
} from "./caseFormHelpers.js";
import { SystemHealthTab } from "./components/SystemHealthTab.js";
import { ChairReportTab } from "./components/ChairReportTab.js";
import { SpecialistsTab } from "./components/SpecialistsTab.js";
import { CasePresetPerturbationPanel } from "./components/CasePresetPerturbationPanel.js";
import { PreMdtIntakeReviewCard } from "./components/PreMdtIntakeReviewCard.js";
import { SimulationMasterBar } from "./components/SimulationMasterBar.js";
import { EvidenceDrawerModal } from "./components/EvidenceDrawerModal.js";

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
  const [pendingIntake, setPendingIntake] = useState<PendingIntake | null>(() => readPendingIntakePointer());
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
  const [roundAudits, setRoundAudits] = useState<Record<number, RoundQualityAudit | null>>({});
  const [finalReport, setFinalReport] = useState<FinalMDTReport | null>(null);
  const [roundActionBusy, setRoundActionBusy] = useState<number | null>(null);
  const [controlBusyKey, setControlBusyKey] = useState<string | null>(null);
  const [roundError, setRoundError] = useState("");
  const isMountedRef = useRef(true);
  const activeRunIdRef = useRef<string | null>(batchRun?.run_id ?? null);
  const batchRefreshSeqRef = useRef(0);
  const roundRefreshSeqRef = useRef<Record<number, number>>({});
  activeRunIdRef.current = batchRun?.run_id ?? null;
  const [agentFilter, setAgentFilter] = useState("All perspectives");
  const [activeTab, setActiveTab] = useState<"case" | "simulation" | "chair" | "specialists" | "system">(() => (batchRun ? "simulation" : "case"));
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");
  const [activePerturbationId, setActivePerturbationId] = useState<string | null>(null);
  const [focusedPanelKey, setFocusedPanelKey] = useState<string>("all");
  const [inspectingTrial, setInspectingTrial] = useState<LandmarkTrial | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState(false);
  const [selectedAgentIds, setSelectedAgentIds] = useState<Record<number, string[]>>({
    1: [],
    2: [],
    3: [],
    4: []
  });
  const [singleAgentToRun, setSingleAgentToRun] = useState<string>("RO-01");

  function loadPresetCase(presetId: string) {
    const preset = PRESET_CASES.find((p) => p.id === presetId);
    if (!preset) return;
    const newForm = { ...preset.form };
    setForm(newForm);
    writeDraft(safeCaseDraftStorage(), CASE_DRAFT_KEY, LEGACY_CASE_KEY, newForm);
    setActivePerturbationId(null);
    setValidation(null);
    setValidatedCase(null);
    setValidationError("");
    setPatientError("");
    setAssessmentError("");
  }

  function handleApplyPerturbation(perturbationId: string) {
    if (activePerturbationId === perturbationId) {
      if (selectedPresetId) {
        loadPresetCase(selectedPresetId);
      }
      setActivePerturbationId(null);
      return;
    }
    const updatedForm = applyPerturbation(form, perturbationId);
    setForm(updatedForm);
    setActivePerturbationId(perturbationId);
    writeDraft(safeCaseDraftStorage(), CASE_DRAFT_KEY, LEGACY_CASE_KEY, updatedForm);
    setValidation(null);
    setValidatedCase(null);
  }

  function handleResetPerturbations() {
    if (selectedPresetId) {
      loadPresetCase(selectedPresetId);
    }
    setActivePerturbationId(null);
  }




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
      if (!isMountedRef.current) return;
      setHealth(healthData);
      setRuntime(runtimeData.ollama);
      setAgents(agentData.agents);
      setConnectionState("connected");
    } catch {
      if (!isMountedRef.current) return;
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
      if (!isMountedRef.current) return;
      setPatientRecords(body.patients);
    } catch (error) {
      if (!isMountedRef.current) return;
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
      activeRunIdRef.current = latestRun.run_id;
      await refreshBatchRun(latestRun.run_id);
    } else {
      activeRunIdRef.current = null;
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
      const body = await readJsonResponse<PatientDetail>(response, "Unable to load the selected patient.");
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
    setPendingIntake(null);
    try {
      const patientName = form.patient_name.trim();
      if (patientName.length < 2) throw new Error("Enter a fictional training name before screening.");
      const response = await fetch(API_BASE + "/api/intakes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case: validatedCase })
      });
      const body = await readJsonResponse<{ session_id: string; screening: IntakeScreening }>(
        response,
        "The pre-MDT intake could not be started."
      );
      const pending: PendingIntake = {
        session_id: body.session_id,
        createNewPatient,
        patientName,
        patientId: createNewPatient ? undefined : loadedPatient!.patient_id,
        screening: body.screening
      };
      setPendingIntake(pending);
      for (const question of body.screening.questions) {
        const questionResponse = await fetch(API_BASE + "/api/intakes/" + body.session_id + "/events", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event_type: "QUESTION_ASKED", domain: question.domain })
        });
        await readJsonResponse<unknown>(questionResponse, "An intake question could not be recorded.");
      }
      const refreshed = await fetch(API_BASE + "/api/intakes/" + body.session_id);
      const refreshedBody = await readJsonResponse<{ screening: IntakeScreening }>(
        refreshed,
        "The intake review could not be loaded."
      );
      setPendingIntake({ ...pending, screening: refreshedBody.screening });
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to start pre-MDT intake screening.");
    } finally {
      setPatientBusy(false);
    }
  }

  async function declineIntakeQuestion(domain: string) {
    if (!pendingIntake) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      const response = await fetch(API_BASE + "/api/intakes/" + pendingIntake.session_id + "/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_type: "DECLINE_DOMAIN", domain, source_text: "User explicitly declined this intake question." })
      });
      const body = await readJsonResponse<{ screening: IntakeScreening }>(
        response,
        "The declined question could not be recorded."
      );
      setPendingIntake({ ...pendingIntake, screening: body.screening });
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to record the declined question.");
    } finally {
      setPatientBusy(false);
    }
  }

  async function acceptAndPromoteIntake() {
    if (!pendingIntake) return;
    setPatientBusy(true);
    setPatientError("");
    try {
      const sessionResponse = await fetch(API_BASE + "/api/intakes/" + pendingIntake.session_id);
      const sessionBody = await readJsonResponse<{
        state?: string; patient_id?: string | null; case_version_id?: string | null
      }>(sessionResponse, "The saved intake could not be restored.");
      if (sessionBody.patient_id && sessionBody.case_version_id) {
        const patientResponse = await fetch(API_BASE + "/api/patients/" + sessionBody.patient_id);
        const patient = await readJsonResponse<PatientDetail>(
          patientResponse,
          "The promoted patient record could not be restored."
        );
        setPendingIntake(null);
        await refreshPatients();
        await loadPatientVersion(patient, sessionBody.case_version_id);
        return;
      }
      if (sessionBody.state !== "ACCEPTED_WITH_GAPS") {
        const acceptedResponse = await fetch(API_BASE + "/api/intakes/" + pendingIntake.session_id + "/accept", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ confirmed: true })
        });
        await readJsonResponse<unknown>(acceptedResponse, "The intake could not be accepted.");
      }
      const promotionResponse = await fetch(API_BASE + "/api/intakes/" + pendingIntake.session_id + "/promote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_name: pendingIntake.patientName,
          ...(pendingIntake.patientId ? { patient_id: pendingIntake.patientId } : {})
        })
      });
      const patient = await readJsonResponse<PatientDetail>(
        promotionResponse,
        "The accepted intake could not be saved as a patient case version."
      );
      const latest = patient.versions[0];
      if (!latest) throw new Error("The accepted intake did not return a saved case version.");
      setPendingIntake(null);
      await refreshPatients();
      await loadPatientVersion(patient, latest.case_version_id);
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to accept and save the intake.");
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
    setPendingIntake(null);
    setSelectedPatientId("");
    setLoadedPatient(null);
    setSelectedCaseVersionId("");
    setActiveSavedCase(null);
    setSelectedPatientRunId("");
    setAssessmentError("");
    setAssessmentPersistenceWarning("");
    if (clearLinkedResults) {
      setSavedSingleAssessment(null);
      activeRunIdRef.current = null;
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
      activeRunIdRef.current = selectedPatientRunId;
      await refreshBatchRun(selectedPatientRunId);
      setActiveTab("simulation");
    } catch (error) {
      setPatientError(error instanceof Error ? error.message : "Unable to load the selected simulation.");
    } finally {
      setPatientBusy(false);
    }
  }


  useEffect(() => {
    const storage = safeCaseDraftStorage();
    if (!pendingIntake) {
      storage.removeItem(PENDING_INTAKE_KEY);
      return;
    }
    storage.setItem(PENDING_INTAKE_KEY, JSON.stringify({
      session_id: pendingIntake.session_id,
      createNewPatient: pendingIntake.createNewPatient,
      patientName: pendingIntake.patientName,
      patientId: pendingIntake.patientId
    }));
  }, [pendingIntake?.session_id, pendingIntake?.createNewPatient, pendingIntake?.patientName, pendingIntake?.patientId]);

  useEffect(() => {
    if (!pendingIntake || pendingIntake.screening) return;
    let active = true;
    void fetch(API_BASE + "/api/intakes/" + pendingIntake.session_id)
      .then(async (response) => {
        const body = await response.json() as { screening?: IntakeScreening; detail?: string };
        if (!response.ok || !body.screening) throw new Error(body.detail ?? "Pending intake could not be restored.");
        if (active) setPendingIntake((current) => current?.session_id === pendingIntake.session_id
          ? { ...current, screening: body.screening! } : current);
      })
      .catch((error) => {
        if (active) setPatientError(error instanceof Error ? error.message : "Pending intake could not be restored.");
      });
    return () => { active = false; };
  }, [pendingIntake?.session_id, pendingIntake?.screening]);

  useEffect(() => {
    isMountedRef.current = true;
    void refreshStatus();
    void refreshPatients();
    return () => {
      isMountedRef.current = false;
    };
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
      let body: { detail?: Array<{ msg?: string }> | string } | ValidationResult | null = null;
      try {
        body = await response.json();
      } catch {
        if (!response.ok) throw new Error("The case could not be validated.");
        throw new Error("Server returned an unexpected non-JSON validation response.");
      }
      if (!response.ok) {
        const detail = body && typeof body === "object" && "detail" in body ? body.detail : null;
        const details = Array.isArray(detail)
          ? detail.map((item: { msg?: string }) => item.msg ?? "Invalid input").join("; ")
          : typeof detail === "string" ? detail : "The case could not be validated.";
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
    if (!activeSavedCase.intake_backed) {
      setAssessmentError("This saved version has no accepted pre-MDT intake. Start and accept an intake before running R1.");
      return;
    }
    setAssessing(true);
    setAssessmentError("");
    setAssessmentPersistenceWarning("");
    try {
      const response = await fetch(
        API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/versions/" + activeSavedCase.case_version_id + "/assess/RO-01",
        { method: "POST" }
      );
      const savedResponse = await readJsonResponse<{ assessment: AgentAssessmentResult; created_at: string }>(
        response,
        "The local model could not produce a valid assessment."
      );
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
    const seq = (roundRefreshSeqRef.current[roundNumber] ?? 0) + 1;
    roundRefreshSeqRef.current[roundNumber] = seq;
    try {
      const [summaryResponse, resultResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber),
        fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber + "/results")
      ]);
      if (seq !== roundRefreshSeqRef.current[roundNumber] || (activeRunIdRef.current && activeRunIdRef.current !== runId)) {
        return;
      }
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
      if (seq !== roundRefreshSeqRef.current[roundNumber] || (activeRunIdRef.current && activeRunIdRef.current !== runId)) {
        return;
      }
      setRoundSummaries((current) => ({ ...current, [roundNumber]: summary }));
      setRoundResults((current) => ({ ...current, [roundNumber]: body.results }));

      // Fetch quality audit asynchronously when round is completed
      if (summary.status === "completed") {
        try {
          const auditResponse = await fetch(API_BASE + "/api/runs/" + runId + "/rounds/" + roundNumber + "/quality-audit");
          if (auditResponse.ok) {
            const auditData = (await auditResponse.json()) as { quality_audit: RoundQualityAudit | null };
            setRoundAudits((current) => ({ ...current, [roundNumber]: auditData.quality_audit }));
          }
        } catch {
          // Quality audit is non-blocking
        }
      }
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
      const body = await readJsonResponse<RoundSummary>(response, "Unable to start Round " + roundNumber + ".");
      setRoundSummaries((current) => ({ ...current, [roundNumber]: body }));
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
      (summary) => summary?.status === "queued" || summary?.status === "running" || summary?.status === "paused"
    );
    if (!active) return;
    const timer = window.setInterval(() => {
      for (const roundNumber of [2, 3, 4]) {
        const summary = roundSummaries[roundNumber];
        if (summary?.status === "queued" || summary?.status === "running" || summary?.status === "paused") {
          void refreshMdtRound(roundNumber, batchRun.run_id);
        }
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, roundSummaries]);

  async function refreshBatchRun(runId: string) {
    const seq = ++batchRefreshSeqRef.current;
    try {
      const [runResponse, resultsResponse] = await Promise.all([
        fetch(API_BASE + "/api/runs/" + runId),
        fetch(API_BASE + "/api/runs/" + runId + "/results")
      ]);
      if (seq !== batchRefreshSeqRef.current || (activeRunIdRef.current && activeRunIdRef.current !== runId)) {
        return;
      }
      if (!runResponse.ok || !resultsResponse.ok) {
        throw new Error("Unable to refresh the MDT run.");
      }
      const runData = (await runResponse.json()) as BatchRunSummary;
      const resultsData = (await resultsResponse.json()) as { results: BatchAgentResult[] };
      if (seq !== batchRefreshSeqRef.current || (activeRunIdRef.current && activeRunIdRef.current !== runId)) {
        return;
      }
      setBatchRun(runData);
      setBatchResults(resultsData.results);
    } catch (error) {
      if (seq === batchRefreshSeqRef.current) {
        setBatchError(error instanceof Error ? error.message : "Unable to refresh batch progress.");
      }
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
    if (!batchRun) return;
    const isAnyRoundActive = Object.values(roundSummaries).some(
      (s) => s?.status === "queued" || s?.status === "running" || s?.status === "paused"
    );
    const isTerminalBatch =
      batchRun.status === "completed" ||
      batchRun.status === "completed_with_errors" ||
      batchRun.status === "stopped";
    if (isTerminalBatch && !isAnyRoundActive) {
      return;
    }
    const runId = batchRun.run_id;
    const timer = window.setInterval(() => {
      void refreshBatchRun(runId);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [batchRun?.run_id, batchRun?.status, roundSummaries]);

  async function startSingleAgentRun(agentId: string) {
    if (!activeSavedCase) return;
    if (!activeSavedCase.intake_backed) {
      setBatchError("This saved version has no accepted pre-MDT intake. Start and accept an intake before running.");
      return;
    }
    setBatchStarting(true);
    setBatchError("");
    try {
      if (!batchRun || batchRun.case_version_id !== activeSavedCase.case_version_id) {
        const response = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/runs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            case_version_id: activeSavedCase.case_version_id,
            selected_agent_ids: [agentId]
          })
        });
        const body = await response.json();
        if (!response.ok) {
          throw new Error(typeof body.detail === "string" ? body.detail : "Unable to start simulation for agent.");
        }
        const createdRun = body as BatchRunSummary;
        activeRunIdRef.current = createdRun.run_id;
        setBatchRun(createdRun);
        setBatchResults([]);
        setRoundSummaries({});
        setRoundResults({});
        setFinalReport(null);
        setSelectedPatientRunId(createdRun.run_id);
        const patientResponse = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id);
        if (patientResponse.ok) setLoadedPatient(await patientResponse.json() as PatientDetail);
        await refreshPatients();
        await refreshBatchRun(createdRun.run_id);
      } else {
        await runIndividualAgent(1, agentId);
      }
      setActiveTab("simulation");
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : `Failed to run agent ${agentId}.`);
    } finally {
      setBatchStarting(false);
    }
  }

  async function startAllAgents() {
    if (!activeSavedCase) return;
    if (!activeSavedCase.intake_backed) {
      setBatchError("This saved version has no accepted pre-MDT intake. Start and accept an intake before running R1.");
      return;
    }
    setBatchStarting(true);
    setBatchError("");
    try {
      const response = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_version_id: activeSavedCase.case_version_id })
      });
      const createdRun = await readJsonResponse<BatchRunSummary>(response, "Unable to start the MDT run.");
      activeRunIdRef.current = createdRun.run_id;
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
      setActiveTab("simulation");
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to start the MDT run.");
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
      const body = await readJsonResponse<BatchRunSummary>(response, "Unable to resume the run.");
      setBatchRun(body);
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to resume the run.");
    } finally {
      setBatchResuming(false);
    }
  }

  function toggleAgentSelection(roundNumber: number, agentId: string) {
    setSelectedAgentIds((prev) => {
      const current = prev[roundNumber] || [];
      const updated = current.includes(agentId)
        ? current.filter((id) => id !== agentId)
        : [...current, agentId];
      return { ...prev, [roundNumber]: updated };
    });
  }

  function selectAllAgentsForRound(roundNumber: number, agentIds: string[]) {
    setSelectedAgentIds((prev) => ({ ...prev, [roundNumber]: [...agentIds] }));
  }

  function clearSelectedAgentsForRound(roundNumber: number) {
    setSelectedAgentIds((prev) => ({ ...prev, [roundNumber]: [] }));
  }

  async function startFullSimulation() {
    if (!activeSavedCase) return;
    if (!activeSavedCase.intake_backed) {
      setBatchError("This saved version has no accepted pre-MDT intake. Start and accept an intake before running.");
      return;
    }
    setBatchStarting(true);
    setBatchError("");
    try {
      const response = await fetch(API_BASE + "/api/patients/" + activeSavedCase.patient_id + "/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_version_id: activeSavedCase.case_version_id, full_simulation: true })
      });
      const createdRun = await readJsonResponse<BatchRunSummary>(response, "Unable to start the full MDT simulation.");
      activeRunIdRef.current = createdRun.run_id;
      setBatchRun(createdRun);
      setBatchResults([]);
      setRoundSummaries({});
      setRoundResults({});
      setFinalReport(null);
      setRoundError("");
      setSelectedPatientRunId(createdRun.run_id);
      await refreshPatients();
      await refreshBatchRun(createdRun.run_id);
      setActiveTab("simulation");
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Unable to start the full MDT simulation.");
    } finally {
      setBatchStarting(false);
    }
  }

  async function readJsonResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      if (!response.ok) throw new Error(fallbackMessage);
      throw new Error("Server returned an unexpected non-JSON response.");
    }
    if (!response.ok) {
      const detail = (body && typeof body === "object" && "detail" in body && typeof (body as { detail?: unknown }).detail === "string")
        ? (body as { detail: string }).detail
        : fallbackMessage;
      throw new Error(detail);
    }
    return body as T;
  }

  async function postControlAction(path: string, fallbackMessage: string, payload?: unknown, busyKey?: string) {
    if (busyKey) setControlBusyKey(busyKey);
    try {
      const response = await fetch(API_BASE + path, {
        method: "POST",
        ...(payload !== undefined
          ? { headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
          : {})
      });
      if (!response.ok) {
        let detail = fallbackMessage;
        try {
          const body = await response.json() as { detail?: string };
          if (body.detail) detail = body.detail;
        } catch {
          // Ignore non-JSON error bodies and use fallbackMessage.
        }
        throw new Error(detail);
      }
    } finally {
      if (busyKey && isMountedRef.current) setControlBusyKey(null);
    }
  }

  async function pauseSimulation() {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/pause", "Failed to pause simulation.", undefined, "sim-pause");
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Failed to pause simulation.");
    }
  }

  async function resumeSimulation() {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/unpause", "Failed to resume simulation.", undefined, "sim-resume");
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Failed to resume simulation.");
    }
  }

  async function stopSimulation() {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/stop", "Failed to stop simulation.", undefined, "sim-stop");
      await refreshBatchRun(batchRun.run_id);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Failed to stop simulation.");
    }
  }

  async function restartSimulation() {
    if (!batchRun || controlBusyKey !== null) return;
    setBatchStarting(true);
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/restart", "Failed to restart simulation.", undefined, "sim-restart");
      await refreshBatchRun(batchRun.run_id);
      setRoundSummaries({});
      setRoundResults({});
      setFinalReport(null);
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : "Failed to restart simulation.");
    } finally {
      setBatchStarting(false);
    }
  }

  async function pauseRound(roundNumber: number) {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/pause", `Failed to pause Round ${roundNumber}.`, undefined, `round-pause-${roundNumber}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to pause Round ${roundNumber}.`);
    }
  }

  async function resumeRound(roundNumber: number) {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/unpause", `Failed to resume Round ${roundNumber}.`, undefined, `round-resume-${roundNumber}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to resume Round ${roundNumber}.`);
    }
  }

  async function stopRound(roundNumber: number) {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/stop", `Failed to stop Round ${roundNumber}.`, undefined, `round-stop-${roundNumber}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to stop Round ${roundNumber}.`);
    }
  }

  async function restartRound(roundNumber: number) {
    if (!batchRun || controlBusyKey !== null) return;
    setRoundActionBusy(roundNumber);
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/restart", `Failed to restart Round ${roundNumber}.`, undefined, `round-restart-${roundNumber}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to restart Round ${roundNumber}.`);
    } finally {
      setRoundActionBusy(null);
    }
  }

  async function runIndividualAgent(roundNumber: number, agentId: string) {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/agents/" + agentId + "/run", `Failed to run agent ${agentId}.`, undefined, `agent-run-${roundNumber}-${agentId}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to run agent ${agentId}.`);
    }
  }

  async function stopIndividualAgent(roundNumber: number, agentId: string) {
    if (!batchRun || controlBusyKey !== null) return;
    try {
      await postControlAction("/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/agents/" + agentId + "/stop", `Failed to stop agent ${agentId}.`, undefined, `agent-stop-${roundNumber}-${agentId}`);
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to stop agent ${agentId}.`);
    }
  }

  async function runSelectedAgents(roundNumber: number) {
    if (!batchRun || controlBusyKey !== null) return;
    const selected = selectedAgentIds[roundNumber] || [];
    if (selected.length === 0) return;
    try {
      await postControlAction(
        "/api/runs/" + batchRun.run_id + "/rounds/" + roundNumber + "/run-selected",
        `Failed to run selected agents in Round ${roundNumber}.`,
        { agent_ids: selected },
        `round-selected-${roundNumber}`
      );
      if (roundNumber === 1) await refreshBatchRun(batchRun.run_id);
      else await refreshMdtRound(roundNumber, batchRun.run_id);
    } catch (error) {
      setRoundError(error instanceof Error ? error.message : `Failed to run selected agents in Round ${roundNumber}.`);
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

      <nav className="guided-stepper" aria-label="Workflow Navigation">
        <button
          className={`step-item ${activeTab === "case" ? "active" : ""}`}
          onClick={() => setActiveTab("case")}
          type="button"
        >
          <span className="step-num">1</span>
          <span className="step-label">Case Workspace</span>
        </button>
        <span className="step-arrow">→</span>
        <button
          className={`step-item ${activeTab === "simulation" ? "active" : ""}`}
          onClick={() => setActiveTab("simulation")}
          type="button"
        >
          <span className="step-num">2</span>
          <span className="step-label">MDT Simulation</span>
          {batchRun && <span className="step-badge">{batchRun.status.replaceAll("_", " ")}</span>}
        </button>
        <span className="step-arrow">→</span>
        <button
          className={`step-item ${activeTab === "chair" ? "active" : ""}`}
          onClick={() => setActiveTab("chair")}
          type="button"
        >
          <span className="step-num">3</span>
          <span className="step-label">Chair Report</span>
          {finalReport && <span className="step-badge ready">Ready</span>}
        </button>
        <div className="step-separator" />
        <button
          className={`step-item ${activeTab === "specialists" ? "active" : ""}`}
          onClick={() => setActiveTab("specialists")}
          type="button"
        >
          <span>👥 49 Specialists</span>
        </button>
        <button
          className={`step-item ${activeTab === "system" ? "active" : ""}`}
          onClick={() => setActiveTab("system")}
          type="button"
        >
          <span>⚙️ System Health</span>
        </button>
      </nav>

      <main className="main-content">
        <section className="safety-banner" role="note">
          <span className="safety-icon">!</span>
          <div>
            <strong>Educational simulation only</strong>
            <p>Use fictional training records only. Do not enter real patient information. This prototype is not a hospital registration system, medical device, or clinical decision-support system; it is not a substitute for a qualified MDT.</p>
          </div>
        </section>

        {activeTab === "system" && (
          <SystemHealthTab
            agents={agents}
            connectionState={connectionState}
            health={health}
            runtime={runtime}
          />
        )}

        <div className="workspace-grid">
          {activeTab === "case" && (
            <section className="panel case-panel tab-view-container" style={{ width: "100%", maxWidth: "100%" }}>
              <CasePresetPerturbationPanel
                selectedPresetId={selectedPresetId}
                onSelectPreset={setSelectedPresetId}
                onLoadPreset={loadPresetCase}
                activePerturbationId={activePerturbationId}
                onApplyPerturbation={handleApplyPerturbation}
                onResetPerturbations={handleResetPerturbations}
              />

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
                <strong>Pre-MDT intake required before saving</strong>
                <p>Start a persisted completeness review first. You can review missing information, explicitly decline questions, or accept with gaps. Acceptance creates an immutable patient case version; it does not certify clinical completeness.</p>
                <div className="batch-actions">
                  <button className="button button-primary" type="button" onClick={() => void savePatientCase(true)} disabled={patientBusy}>
                    Start intake for new patient
                  </button>
                  {loadedPatient && (
                    <button className="button button-secondary" type="button" onClick={() => void savePatientCase(false)} disabled={patientBusy || selectedPatientId !== loadedPatient.patient_id || activeSavedCase !== null}>
                      Start intake for new version of {loadedPatient.patient_identifier}
                    </button>
                  )}
                </div>
              </div>
            )}


            {pendingIntake && (
              <PreMdtIntakeReviewCard
                pendingIntake={pendingIntake}
                patientBusy={patientBusy}
                onDeclineQuestion={(domain) => void declineIntakeQuestion(domain)}
                onReturnToForm={() => setPendingIntake(null)}
                onAcceptAndPromote={() => void acceptAndPromoteIntake()}
              />
            )}

            {validation && (
              <div className="result-card result-success" role="status">
                <strong>Case structure valid</strong>
                <p>{validation.note}</p>
                {validation.warnings.length > 0 && (
                  <ul>{validation.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                )}
                <p className="result-footnote">Case structure is validated. Once all {agents.length || 49} independent assessments finish, the debate, adversarial review and Chair synthesis stages become available below.</p>
              </div>
            )}
            {activeSavedCase && (
              <div className="assessment-launch">
                <div>
                  <strong>Try one local agent</strong>
                  <p>Run the guideline-focused Radiation Oncology perspective (RO-01) on {activeSavedCase.patient_identifier}, case version {activeSavedCase.version_number}. The result is saved in the patient record.</p>
                  {!activeSavedCase.intake_backed && <p className="error-text">This older/manual case version has no accepted intake provenance. Create a new accepted intake version before running an agent.</p>}
                </div>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => void runAgentAssessment()}
                  disabled={!activeSavedCase.intake_backed || assessing || !runtime?.reachable || (batchRun !== null && ["queued", "running"].includes(batchRun.status))}
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
                <p className="assessment-summary-text">{agentAssessment.perspective_summary}</p>
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
            {activeSavedCase && (
              <div className="batch-actions" style={{ marginTop: "24px", padding: "16px", background: "rgba(56, 189, 248, 0.08)", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.25)" }}>
                <div>
                  <strong style={{ color: "#38bdf8" }}>✓ Case Saved & Validated</strong>
                  <p style={{ margin: "4px 0 12px 0", fontSize: "13px", color: "#94a3b8" }}>
                    Version {activeSavedCase.version_number} is ready. Proceed to the MDT Deliberation workspace to run the 4-round simulation.
                  </p>
                </div>
                <button
                  className="button button-primary"
                  type="button"
                  onClick={() => setActiveTab("simulation")}
                >
                  Proceed to MDT Simulation (Step 2) →
                </button>
              </div>
            )}
            {validationError && (
              <div className="result-card result-error" role="alert" style={{ marginTop: "16px" }}>
                <strong>Validation failed</strong>
                <p>{validationError}</p>
              </div>
            )}
          </section>
        )}

        {activeTab === "simulation" && (
          <section className="panel tab-view-container" style={{ width: "100%", maxWidth: "100%" }}>
            <div className="focused-panel-bar">
              <span className="focused-panel-label">🎯 Filter Deliberation by Perspective:</span>
              {Object.entries(FOCUSED_PANELS).map(([key, p]) => (
                <button
                  key={key}
                  type="button"
                  className={`focused-panel-chip ${focusedPanelKey === key ? "active" : ""}`}
                  onClick={() => setFocusedPanelKey(key)}
                >
                  {p.icon} {p.label}
                </button>
              ))}
            </div>
            {(shouldShowBatchPanel(batchRun, validation, validatedCase) || activeSavedCase !== null) && (
              <section className="batch-run-panel">
                <div className="batch-heading">
                  <div>
                    <p className="eyebrow">03 / INDEPENDENT ASSESSMENTS</p>
                    <h3>Run all {agents.length || 49} MDT perspectives</h3>
                  </div>
                  <span className="count-chip">{agents.length || 49} REQUIRED</span>
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
                <SimulationMasterBar
                  activeSavedCase={activeSavedCase}
                  batchRun={batchRun}
                  batchResults={batchResults}
                  batchStarting={batchStarting}
                  batchResuming={batchResuming}
                  assessing={assessing}
                  runtime={runtime}
                  agents={agents}
                  singleAgentToRun={singleAgentToRun}
                  onSelectSingleAgent={setSingleAgentToRun}
                  roundSummaries={roundSummaries}
                  controlBusyKey={controlBusyKey}
                  onStartFullSimulation={() => void startFullSimulation()}
                  onStartAllAgents={() => void startAllAgents()}
                  onStartSingleAgentRun={(id) => void startSingleAgentRun(id)}
                  onDownloadBatchResults={() => void downloadBatchResults()}
                  onResumeAllAgents={() => void resumeAllAgents()}
                  onPauseSimulation={() => void pauseSimulation()}
                  onResumeSimulation={() => void resumeSimulation()}
                  onStopSimulation={() => void stopSimulation()}
                  onRestartSimulation={() => void restartSimulation()}
                />
                {batchError && <div className="result-card result-error" role="alert">{batchError}</div>}
                {batchResults.length > 0 && (
                  <div className="batch-results">
                    <div className="batch-results-title">
                      <strong>Agent results · Round 1</strong>
                      <span>{batchResults.length} records saved locally</span>
                      <div className="selective-controls">
                        <button
                          className="button button-xs button-secondary"
                          type="button"
                          onClick={() => selectAllAgentsForRound(1, batchResults.map((b) => b.agent_id))}
                        >
                          Select All
                        </button>
                        <button
                          className="button button-xs button-quiet"
                          type="button"
                          onClick={() => clearSelectedAgentsForRound(1)}
                        >
                          Clear
                        </button>
                        {(selectedAgentIds[1]?.length || 0) > 0 && (
                          <button
                            className="button button-xs button-primary"
                            type="button"
                            disabled={controlBusyKey !== null}
                            onClick={() => void runSelectedAgents(1)}
                          >
                            ⚡ Run Selected ({selectedAgentIds[1]?.length})
                          </button>
                        )}
                      </div>
                    </div>
                    {(focusedPanelKey === "all" ? batchResults : batchResults.filter((item) => FOCUSED_PANELS[focusedPanelKey]?.agentIds.includes(item.agent_id))).map((item) => (
                      <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                        <summary>
                          <input
                            type="checkbox"
                            className="agent-checkbox"
                            checked={selectedAgentIds[1]?.includes(item.agent_id) || false}
                            onClick={(e) => e.stopPropagation()}
                            onChange={() => toggleAgentSelection(1, item.agent_id)}
                            title={`Select ${item.agent_id} for Round 1 run`}
                          />
                          <span className="agent-id">{item.agent_id}</span>
                          <strong>{item.agent_name}</strong>
                          <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                          {item.duration_seconds !== null && <span className="agent-duration">{item.duration_seconds.toFixed(1)}s</span>}
                          <div className="agent-item-quick-actions" onClick={(e) => e.stopPropagation()}>
                            <button
                              className="button-link-action"
                              type="button"
                              disabled={controlBusyKey !== null}
                              onClick={() => void runIndividualAgent(1, item.agent_id)}
                              title={`Run/Re-run ${item.agent_id} in Round 1`}
                            >
                              🔄 Run
                            </button>
                            {(item.status === "running" || item.status === "queued") && (
                              <button
                                className="button-link-action text-danger"
                                type="button"
                                disabled={controlBusyKey !== null}
                                onClick={() => void stopIndividualAgent(1, item.agent_id)}
                                title={`Stop ${item.agent_id}`}
                              >
                                ⏹ Stop
                              </button>
                            )}
                          </div>
                        </summary>
                        {item.assessment ? (
                          <div className="batch-agent-body">
                            <div className="assessment-conclusion">
                              <strong>Provisional conclusion · {item.assessment.position.replaceAll("_", " ")}</strong>
                              <p>{item.assessment.provisional_conclusion}</p>
                              <strong>Preferred educational option</strong>
                              <p>{item.assessment.preferred_educational_option}</p>
                            </div>
                            <p className="assessment-summary-text">{item.assessment.perspective_summary}</p>
                            
                            {item.assessment.evidence_claims && item.assessment.evidence_claims.length > 0 && (
                              <div className="assessment-citations">
                                <strong>Active Clinical References & Guideline Citations</strong>
                                <ul>
                                  {item.assessment.evidence_claims.map((claim, cIdx) => (
                                    <li key={cIdx}>
                                      {claim.sources.map((s, sIdx) => (
                                        <span key={sIdx} className="evidence-badge" title={s.applicability_and_limitations}>
                                          [{s.source_id}] {s.title}
                                        </span>
                                      ))}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {item.assessment.conditional_options && item.assessment.conditional_options.length > 0 && (
                              <div className="assessment-branches">
                                <strong>Clinical Decision Branches (IF-Clauses)</strong>
                                <ul>
                                  {item.assessment.conditional_options.map((opt, oIdx) => (
                                    <li key={oIdx}>
                                      <span className="branch-condition">{opt.condition}:</span> {opt.educational_option}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {item.assessment.discussion_options.length > 0 && (
                              <details className="meta-audit-accordion">
                                <summary>Discussion points & unknowns ({item.assessment.discussion_options.length + item.assessment.unknowns.length})</summary>
                                <strong>Discussion topics</strong>
                                <ul>{item.assessment.discussion_options.map((option, index) => <li key={index}>{option}</li>)}</ul>
                                {item.assessment.unknowns.length > 0 && (
                                  <>
                                    <strong>Unknowns</strong>
                                    <ul>{item.assessment.unknowns.map((unknown, index) => <li key={index}>{unknown}</li>)}</ul>
                                  </>
                                )}
                              </details>
                            )}

                            <p className="result-footnote">
                              Model self-reported confidence: {Math.round(item.assessment.confidence * 100)}%.
                              Active guideline citations: {item.assessment.evidence_claims.length}.
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
                  <span className="count-chip">{agents.length || 49} ROLES</span>
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
                    ? `All ${agents.length || 49} roles respond to selected peer positions, state agreements and challenges, and explain any change in position.`
                    : roundNumber === 3
                    ? `All ${agents.length || 49} roles challenge unsupported assumptions, evidence gaps, patient-context issues, feasibility and governance risks.`
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
                      <div className="round-controls-bar">
                        {!summary && (
                          <button
                            className="button button-primary button-xs"
                            type="button"
                            disabled={!isPreviousComplete || roundActionBusy !== null}
                            onClick={() => void startMdtRound(roundNumber)}
                          >
                            {roundActionBusy === roundNumber ? "Starting…" : roundNumber === 4 ? "Generate final MDT report" : "Start Round " + roundNumber}
                            <span aria-hidden="true">→</span>
                          </button>
                        )}
                        {summary && summary.status === "running" && (
                          <button className="button button-warning button-xs" type="button" disabled={controlBusyKey !== null} onClick={() => void pauseRound(roundNumber)}>
                            ⏸ Pause Round
                          </button>
                        )}
                        {summary && summary.status === "paused" && (
                          <button className="button button-primary button-xs" type="button" disabled={controlBusyKey !== null} onClick={() => void resumeRound(roundNumber)}>
                            ▶ Resume Round
                          </button>
                        )}
                        {summary && (summary.status === "running" || summary.status === "paused") && (
                          <button className="button button-danger button-xs" type="button" disabled={controlBusyKey !== null} onClick={() => void stopRound(roundNumber)}>
                            ⏹ Stop Round
                          </button>
                        )}
                        {summary && (
                          <button
                            className="button button-quiet button-xs"
                            type="button"
                            disabled={controlBusyKey !== null || roundActionBusy !== null}
                            onClick={() => {
                              if (window.confirm(`Restart Round ${roundNumber}? Current results for this round will be reset.`)) {
                                void restartRound(roundNumber);
                              }
                            }}
                          >
                            🔄 Restart Round {roundNumber}
                          </button>
                        )}
                        {roundNumber !== 4 && results.length > 0 && (
                          <div className="selective-controls">
                            <button className="button button-xs button-secondary" type="button" onClick={() => selectAllAgentsForRound(roundNumber, results.map(r => r.agent_id))}>
                              Select All
                            </button>
                            <button className="button button-xs button-quiet" type="button" onClick={() => clearSelectedAgentsForRound(roundNumber)}>
                              Clear
                            </button>
                            {(selectedAgentIds[roundNumber]?.length || 0) > 0 && (
                              <button className="button button-xs button-primary" type="button" disabled={controlBusyKey !== null} onClick={() => void runSelectedAgents(roundNumber)}>
                                ⚡ Run Selected ({selectedAgentIds[roundNumber]?.length})
                              </button>
                            )}
                          </div>
                        )}
                      </div>
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
                          {roundAudits[roundNumber] && (
                            <div className="round-quality-audit-banner" role="status">
                              <div className="audit-header">
                                <strong>Safety &amp; reasoning audit · Round {roundNumber}</strong>
                                <span className={roundAudits[roundNumber]!.total_flags === 0 ? "audit-badge audit-pass" : "audit-badge audit-warn"}>
                                  {roundAudits[roundNumber]!.total_flags === 0 ? "Verified · 0 flags" : roundAudits[roundNumber]!.total_flags + " review flags"}
                                </span>
                              </div>
                              {roundAudits[roundNumber]!.role_differentiation && !roundAudits[roundNumber]!.role_differentiation!.valid && (
                                <p className="audit-note">⚠️ Anti-duplication/delegation warning: specialist opinions showed high lexical overlap or ungrounded agreement.</p>
                              )}
                              {roundAudits[roundNumber]!.citation_audit && (
                                <p className="audit-note">
                                  📚 Guideline citations: {roundAudits[roundNumber]!.citation_audit!.verified_count}/{roundAudits[roundNumber]!.citation_audit!.total_citations} verified against canonical reference catalogue ({Math.round(roundAudits[roundNumber]!.citation_audit!.concordance_rate * 100)}% concordance).
                                </p>
                              )}
                            </div>
                          )}
                          {roundNumber !== 4 && results.length > 0 && (
                            <div className="round-agent-list">
                              {(focusedPanelKey === "all" ? results : results.filter((item) => FOCUSED_PANELS[focusedPanelKey]?.agentIds.includes(item.agent_id))).map((item) => (
                                <details className={"batch-agent-result status-" + item.status} key={item.agent_id}>
                                  <summary>
                                    <input
                                      type="checkbox"
                                      className="agent-checkbox"
                                      checked={selectedAgentIds[roundNumber]?.includes(item.agent_id) || false}
                                      onClick={(e) => e.stopPropagation()}
                                      onChange={() => toggleAgentSelection(roundNumber, item.agent_id)}
                                      title={`Select ${item.agent_id} for Round ${roundNumber}`}
                                    />
                                    <span className="agent-id">{item.agent_id}</span>
                                    <strong>{item.agent_name}</strong>
                                    <span className={"agent-status status-text-" + item.status}>{item.status}</span>
                                    <div className="agent-item-quick-actions" onClick={(e) => e.stopPropagation()}>
                                      <button
                                        className="button-link-action"
                                        type="button"
                                        disabled={controlBusyKey !== null}
                                        onClick={() => void runIndividualAgent(roundNumber, item.agent_id)}
                                        title={`Run/Re-run ${item.agent_id} in Round ${roundNumber}`}
                                      >
                                        🔄 Run
                                      </button>
                                      {(item.status === "running" || item.status === "queued") && (
                                        <button
                                          className="button-link-action text-danger"
                                          type="button"
                                          disabled={controlBusyKey !== null}
                                          onClick={() => void stopIndividualAgent(roundNumber, item.agent_id)}
                                          title={`Stop ${item.agent_id}`}
                                        >
                                          ⏹ Stop
                                        </button>
                                      )}
                                    </div>
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
                                      {(item.result.source_reference_integrity_flags ?? []).length > 0 && (
                                        <div className="result-card result-error" role="status">
                                          <strong>Source/provenance integrity flags · review required</strong>
                                          <ul>{(item.result.source_reference_integrity_flags ?? []).map((flag, index) => <li key={index}>{flag}</li>)}</ul>
                                        </div>
                                      )}
                                      {(item.result.source_opinion_responses ?? []).length > 0 && (
                                        <div className="report-section">
                                          <strong>Attributed case-summary opinion responses · source-bound</strong>
                                          {(item.result.source_opinion_responses ?? []).map((opinion, index) => (
                                            <div key={opinion.source_id + "-" + index}>
                                              <strong>{opinion.source_id}</strong>
                                              <p><em>Exact saved source excerpt:</em> {opinion.source_excerpt}</p>
                                               <p><em>Model-reported position on this exact opinion:</em> {opinion.position_on_source_opinion ?? "not reported"}</p>
                                              <p><em>Role analysis:</em> {opinion.analysis}</p>
                                              <p><em>Comparison:</em> {opinion.comparison}</p>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                      {(item.result.source_opinion_reviews ?? []).length > 0 && (
                                        <div className="report-section">
                                          <strong>R3 source-opinion reviews · representation status only</strong>
                                          {(item.result.source_opinion_reviews ?? []).map((review, index) => (
                                            <div key={review.source_id + "-" + index}>
                                              <strong>{review.source_id}{review.opinion_label ? " · " + review.opinion_label : ""}</strong>
                                              {review.source_excerpt && <p><em>Exact saved source excerpt:</em> {review.source_excerpt}</p>}
                                              <p>Option: {review.option_status}; conditions: {review.conditions_status}</p>
                                              {review.review_basis && <p><em>Review basis:</em> {review.review_basis}</p>}
                                              {review.evidence_validation_status && <p>Peer evidence validation: {review.evidence_validation_status}</p>}
                                              {review.evidence_peer_id && review.evidence_excerpt && <p><em>Bound peer excerpt ({review.evidence_peer_id}):</em> {review.evidence_excerpt}</p>}
                                              {review.challenge && <p><em>Recorded challenge:</em> {review.challenge}</p>}
                                            </div>
                                          ))}
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
                      ["R2 positions on attributed source opinions · model-reported, not votes or consensus", finalReport.source_opinion_position_summary ?? []],
                      ["R3 source-opinion review coverage · distinct roles; representation only", finalReport.source_opinion_review_coverage ?? []],
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
            {!shouldShowBatchPanel(batchRun, validation, validatedCase) && !activeSavedCase && !hasCompletedIndependentAssessments(batchRun) && (
              <div className="result-card" style={{ padding: "40px", textAlign: "center" }}>
                <span style={{ fontSize: "40px", display: "block", marginBottom: "16px" }}>⚡</span>
                <h3 style={{ fontSize: "18px", color: "#f8fafc" }}>No Case Active for Simulation</h3>
                <p style={{ color: "#94a3b8", maxWidth: "520px", margin: "12px auto", lineHeight: "1.5" }}>
                  Please load a patient case in the Case Workspace or choose one of the pre-loaded example cases before starting the MDT deliberation.
                </p>
                <button className="button button-primary" type="button" onClick={() => setActiveTab("case")}>
                  ← Go to Case Workspace (Step 1)
                </button>
              </div>
            )}
          </section>
        )}

        {activeTab === "chair" && (
          <ChairReportTab
            finalReport={finalReport}
            primarySite={form.primary_site}
            onGoToSimulation={() => setActiveTab("simulation")}
            onOpenEvidenceDrawer={() => setIsEvidenceDrawerOpen(true)}
          />
        )}

        {activeTab === "specialists" && (
          <SpecialistsTab
            agents={agents}
            filteredAgents={filteredAgents}
            agentFilter={agentFilter}
            categories={categories}
            onFilterChange={setAgentFilter}
          />
        )}
        </div>

        {(isEvidenceDrawerOpen || inspectingTrial) && (
          <EvidenceDrawerModal
            inspectingTrial={inspectingTrial}
            onSelectTrial={setInspectingTrial}
            onClose={() => {
              setIsEvidenceDrawerOpen(false);
              setInspectingTrial(null);
            }}
          />
        )}

        <footer className="footer">
          <span>RADONC MDT SIMULATOR <span className="footer-separator">/</span> LOCAL-FIRST PROTOTYPE</span>
          <span>Research and education only · Fictional training data only</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
