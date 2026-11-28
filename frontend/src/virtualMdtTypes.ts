export type VmdtPageId = 'hall' | 'intake' | 'audit' | 'simulation' | 'decision' | 'past-cases' | 'agents' | 'settings';
export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';
export type TeamId =
  | 'radiation_oncology'
  | 'medical_oncology'
  | 'surgical_oncology'
  | 'diagnostics_pathology'
  | 'patient_perspective'
  | 'system_governance'
  | 'family_social_vulnerability';

export interface TeamDefinition {
  id: TeamId;
  label: string;
  shortLabel: string;
  accentDark: string;
  accentLight: string;
  backendCategories: string[];
}

export type AgentSeatStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'paused';

export interface VmdtAgentConfig {
  id: string;
  backendAgentId: string;
  displayName: string;
  specialty: string;
  subspecialty: string;
  teamId: TeamId;
  innatePersonality: string;
  personalitySummary: string;
  active: boolean;
  resourceConstrained: boolean;
  availableResources: string[];
  unavailableResources: string[];
  model: string;
  temperature: number;
  extraInstructions: string;
  avatarVariant: number;
  scrubColor: string;
  hasGlasses: boolean;
  propType: 'tablet' | 'clipboard' | 'stethoscope' | 'none';
  isCustom?: boolean;
}

export interface AuditFinding {
  id: string;
  severity: 'critical' | 'recommended';
  specialty: string;
  fieldKey: string;
  domain: string;
  title: string;
  description: string;
  placeholder: string;
  resolvedValue?: string;
  markedNA?: boolean;
}

export interface ArchivedCase {
  id: string;
  caseCode: string;
  patientName: string;
  ageSex: string;
  primarySite: string;
  diagnosis: string;
  stage: string;
  status: 'Completed' | 'Stopped Early';
  consensusPercent: number;
  createdAt: string;
  primaryRecommendation: string;
  clinicalRationale: string[];
  followUpPlan: string[];
  dissentingViews: string[];
  radiationPlan: string;
  systemicPlan: string;
  surgicalPlan: string;
  evidenceSummary: string;
  specialtyWeighting: Array<{ team: string; weight: number; color: string }>;
  participatingAgents: Array<{ id: string; name: string; specialty: string; position: string; conclusion: string; status: AgentSeatStatus; roundOutputs?: Record<number, string> }>;
  caseSnapshot: Record<string, unknown>;
  runId?: string | null;
}

export interface VmdtSettings {
  rounds: 1 | 2 | 3 | 4;
  verbosity: 'concise' | 'standard' | 'detailed';
  pauseBetweenRounds: boolean;
  consensusThreshold: number;
  institutionName: string;
  institutionTier: string;
  availableFacilities: string[];
  unavailableFacilities: string[];
  defaultModel: string;
  apiKey: string;
  agentTimeoutSeconds: number;
  maxAutoRetries: number;
  voiceLanguage: string;
  defaultTheme: ThemeMode;
  pdfBranding: boolean;
}

export interface UserProfile {
  fullName: string;
  title: string;
  specialty: string;
  institution: string;
  email: string;
  avatarPreset: number;
  customAvatarUrl?: string;
}

export const DEFAULT_TEAMS: TeamId[] = [
  'radiation_oncology',
  'medical_oncology',
  'surgical_oncology',
  'diagnostics_pathology',
  'patient_perspective',
  'system_governance',
  'family_social_vulnerability',
];

export const RESOURCE_CATALOG: string[] = [
  'IMRT/VMAT',
  'CyberKnife',
  'Proton Beam',
  'Heavy Ion Therapy',
  'Cisplatin',
  'Immunotherapy / ICI',
  'PET-CT Scanner',
  'MRI Simulator',
  'NGS Genomic Panel',
  'Brachytherapy Suite',
  'Clinical Trials Office'
];

export const DEFAULT_SETTINGS: VmdtSettings = {
  rounds: 4,
  verbosity: 'standard',
  pauseBetweenRounds: true,
  consensusThreshold: 80,
  institutionName: 'Metropolitan Cancer Center',
  institutionTier: 'Tertiary Comprehensive Cancer Center',
  availableFacilities: [
    'IMRT/VMAT',
    'Cisplatin',
    'PET-CT Scanner',
    'MRI Simulator',
    'Onsite Path Lab',
    'Radiotherapy Wing',
  ],
  unavailableFacilities: ['Proton Beam', 'Heavy Ion Therapy', 'Clinical Trials Office'],
  defaultModel: 'qwen3.5:4b',
  apiKey: '',
  agentTimeoutSeconds: 300,
  maxAutoRetries: 3,
  voiceLanguage: 'en-US',
  defaultTheme: 'dark',
  pdfBranding: true,
};

export const DEFAULT_PROFILE: UserProfile = {
  fullName: 'Dr. Vishnu A',
  title: 'Consultant Radiation Oncologist',
  specialty: 'Radiation Oncology',
  institution: 'Metropolitan Cancer Center',
  email: 'clinician@virtualmdt.local',
  avatarPreset: 1,
};
