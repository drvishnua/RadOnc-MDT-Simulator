export type Health = {
  status: string;
  application: string;
  version: string;
  mode: string;
};

export type Runtime = {
  reachable: boolean;
  version?: string | null;
  configured_model: string;
  configured_model_installed: boolean;
  models: string[];
  error?: string;
};

export type Agent = {
  agent_id: string;
  category: string;
  category_label: string;
  name: string;
  mandate: string;
  clinical_philosophy?: string;
  communication_style?: string;
  key_evidence_sources?: string[];
  risk_appetite?: string;
};

export type ValidationResult = {
  valid: boolean;
  mode: string;
  warnings: string[];
  note: string;
};

export type SyntheticCasePayload = {
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

export type EvidenceSourceItem = {
  source_id: string;
  title: string;
  organization?: string | null;
  source_kind: string;
  applicability_and_limitations: string;
};

export type EvidenceClaimItem = {
  claim_text: string;
  evidence_maturity: string;
  sources: EvidenceSourceItem[];
};

export type ConditionalOptionItem = {
  condition: string;
  educational_option: string;
  prerequisites?: string[];
  unresolved_unknowns?: string[];
  limitations?: string[];
};

export type AgentAssessmentResult = {
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
  evidence_claims: EvidenceClaimItem[];
  conditional_options?: ConditionalOptionItem[];
  case_facts?: string[];
  case_data_integrity_flags?: string[];
  safety_boundary: string;
  not_a_treatment_instruction: boolean;
};

export type SavedSingleAssessment = {
  version: 1;
  saved_at: string;
  case_snapshot: SyntheticCasePayload;
  assessment: AgentAssessmentResult;
  patient_id?: string;
  case_version_id?: string;
};

export type BatchRunSummary = {
  run_id: string;
  status: "queued" | "running" | "completed" | "completed_with_errors" | "paused" | "stopped";
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

export type PatientRecordSummary = {
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

export type PatientCaseVersion = {
  case_version_id: string;
  patient_id: string;
  patient_name: string | null;
  version_number: number;
  case_snapshot_sha256: string;
  created_at: string;
  intake_backed: boolean;
  intake_session_id: string | null;
  case: SyntheticCasePayload;
};

export type IntakeQuestion = { domain: string; question: string };
export type IntakeGap = { domain: string; field_id: string; status: string };
export type IntakeScreening = {
  questions: IntakeQuestion[];
  gaps: IntakeGap[];
  domains: { domain: string; status: string; missing_fields: string[] }[];
  case_snapshot: SyntheticCasePayload;
  disclaimer: string;
};
export type PendingIntake = {
  session_id: string;
  createNewPatient: boolean;
  patientName: string;
  patientId?: string;
  screening: IntakeScreening | null;
};

export type PatientDetail = {
  patient_id: string;
  patient_identifier: string;
  patient_name: string | null;
  created_at: string;
  updated_at: string;
  versions: PatientCaseVersion[];
  runs: BatchRunSummary[];
};

export type ActiveSavedCase = PatientCaseVersion & {
  patient_id: string;
  patient_identifier: string;
};

export type PatientAssessmentRecord = {
  assessment_id: string;
  patient_id: string;
  case_version_id: string;
  agent_id: string;
  round_number: number;
  created_at: string;
  assessment: AgentAssessmentResult;
};

export type BatchAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed" | "stopped";
  assessment: AgentAssessmentResult | null;
  error_message: string | null;
  duration_seconds: number | null;
};

export type RoundSummary = {
  run_id: string;
  round_number: number;
  status: "queued" | "running" | "completed" | "completed_with_errors" | "paused" | "stopped";
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

export type RoundAgentResult = {
  agent_id: string;
  agent_name: string;
  category_label: string;
  status: "queued" | "running" | "completed" | "failed" | "stopped";
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
    source_reference_integrity_flags?: string[];
    source_opinion_responses?: {
      source_id: string;
      source_excerpt: string;
      position_on_source_opinion?: string | null;
      analysis: string;
      comparison: string;
    }[];
    source_opinion_reviews?: {
      source_id: string;
      opinion_label?: string;
      source_excerpt?: string;
      option_status: string;
      conditions_status: string;
      review_basis?: string;
      evidence_peer_id?: string;
      evidence_excerpt?: string;
      evidence_validation_status?: string;
      challenge?: string;
    }[];
    confidence: number;
  } | null;
  error_message: string | null;
  duration_seconds: number | null;
};

export type RoundQualityAudit = {
  run_id: string;
  round_number: number;
  total_flags: number;
  reasoning_depth_flags?: Record<string, string[]>;
  role_differentiation?: {
    valid: boolean;
    flags: string[];
    pairwise_duplicates?: Array<{ role_1: string; role_2: string; similarity: number }>;
    delegation_flags?: Array<{ role_id: string; issue: string; text: string }>;
  };
  citation_audit?: {
    valid: boolean;
    total_citations: number;
    verified_count: number;
    unverified_count: number;
    concordance_rate: number;
    unverified_citations?: Array<{ role_id: string; source_id: string; claim: string }>;
  };
};

export type FinalMDTReport = {
  run_id: string;
  round_number: 4;
  report_title: string;
  consensus_status: string;
  chair_conclusion: string;
  overall_educational_synthesis: string;
  consensus_points: string[];
  recorded_agreements?: string[];
  source_opinion_review_coverage?: string[];
  source_opinion_position_summary?: string[];
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
