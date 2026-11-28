import type { Agent, SyntheticCasePayload } from "../types.js";
import type {
  ArchivedCase,
  AuditFinding,
  TeamDefinition,
  TeamId,
  VmdtAgentConfig,
} from "../virtualMdtTypes.js";

export const TEAM_DEFINITIONS: Record<TeamId, TeamDefinition> = {
  radiation_oncology: {
    id: "radiation_oncology",
    label: "Radiation Oncology",
    shortLabel: "Radiation Oncology",
    accentDark: "#38BDF8",
    accentLight: "#2563EB",
    backendCategories: ["radiation_oncology"],
  },
  medical_oncology: {
    id: "medical_oncology",
    label: "Medical Oncology",
    shortLabel: "Medical Oncology",
    accentDark: "#818CF8",
    accentLight: "#4F46E5",
    backendCategories: ["medical_oncology"],
  },
  surgical_oncology: {
    id: "surgical_oncology",
    label: "Surgical Oncology",
    shortLabel: "Surgical Oncology",
    accentDark: "#34D399",
    accentLight: "#059669",
    backendCategories: ["surgical_oncology"],
  },
  diagnostics_pathology: {
    id: "diagnostics_pathology",
    label: "Diagnostics & Pathology",
    shortLabel: "Diagnostics & Pathology",
    accentDark: "#2DD4BF",
    accentLight: "#0D9488",
    backendCategories: ["diagnostics_pathology"],
  },
  patient_perspective: {
    id: "patient_perspective",
    label: "Patient Perspective Lenses",
    shortLabel: "Patient Perspective",
    accentDark: "#F472B6",
    accentLight: "#DB2777",
    backendCategories: ["patient_perspective"],
  },
  system_governance: {
    id: "system_governance",
    label: "System, Evidence & Governance",
    shortLabel: "System & Governance",
    accentDark: "#FBBF24",
    accentLight: "#D97706",
    backendCategories: ["system_governance"],
  },
  family_social_vulnerability: {
    id: "family_social_vulnerability",
    label: "Family, Social Care & Vulnerability",
    shortLabel: "Family & Social Care",
    accentDark: "#A78BFA",
    accentLight: "#7C3AED",
    backendCategories: ["family_social_vulnerability"],
  },
};

const SCRUB_PALETTE = ["#38BDF8", "#10B981", "#818CF8", "#2DD4BF", "#F472B6", "#FBBF24", "#A78BFA"];
const PROPS: Array<"tablet" | "clipboard" | "stethoscope" | "none"> = [
  "tablet",
  "clipboard",
  "stethoscope",
  "none",
];

function resolveTeamForAgent(agent: Agent): TeamId {
  const cat = agent.category as TeamId;
  if (cat in TEAM_DEFINITIONS) return cat;
  const id = agent.agent_id.toUpperCase();
  if (id.startsWith("RO-")) return "radiation_oncology";
  if (id.startsWith("MO-")) return "medical_oncology";
  if (id.startsWith("SO-")) return "surgical_oncology";
  if (id.startsWith("DS-")) return "diagnostics_pathology";
  if (id.startsWith("PP-")) return "patient_perspective";
  if (id.startsWith("SG-")) return "system_governance";
  return "family_social_vulnerability";
}

function hashId(input: string): number {
  let acc = 0;
  for (let i = 0; i < input.length; i += 1) {
    acc = (acc * 31 + input.charCodeAt(i)) >>> 0;
  }
  return acc;
}

const FALLBACK_BACKEND_AGENTS: Agent[] = [
  { agent_id: "RO-01", category: "radiation_oncology", category_label: "Radiation Oncology", name: "Guideline-focused Radiation Oncologist", mandate: "Evaluates case through published society guidelines (ASTRO, ESTRO, NCCN, AROI, JASTRO, ABS)." },
  { agent_id: "RO-02", category: "radiation_oncology", category_label: "Radiation Oncology", name: "Conservative & Time-Tested Radiation Oncologist", mandate: "Favors proven conventional fractionation and questions unproven high-tech dose extremes." },
  { agent_id: "RO-03", category: "radiation_oncology", category_label: "Radiation Oncology", name: "Aggressive Local Control Radiation Oncologist", mandate: "Evaluates conformal dose escalation and local control tradeoffs." },
  { agent_id: "MO-01", category: "medical_oncology", category_label: "Medical Oncology", name: "High-Dose Cisplatin & Guideline Purist", mandate: "Defends standard-of-care systemic regimens and organ-clearance criteria." },
  { agent_id: "MO-02", category: "medical_oncology", category_label: "Medical Oncology", name: "Pragmatic Weekly-Dosing Medical Oncologist", mandate: "Balances outpatient tolerability and treatment completion." },
  { agent_id: "SO-01", category: "surgical_oncology", category_label: "Surgical Oncology", name: "Guideline-Focused Surgical Oncologist", mandate: "Evaluates resectability, R0 margins, and selective nodal dissection." },
  { agent_id: "SO-02", category: "surgical_oncology", category_label: "Surgical Oncology", name: "Transoral & Minimally Invasive Surgeon", mandate: "Assesses robotic/minimally invasive resection vs primary RT tradeoffs." },
  { agent_id: "DS-01", category: "diagnostics_pathology", category_label: "Diagnostics & Pathology", name: "Histopathologist", mandate: "Confirms histologic subtype, margins, Ki-67, HER2, ER/PR, and p16." },
  { agent_id: "DS-02", category: "diagnostics_pathology", category_label: "Diagnostics & Pathology", name: "Onco-Radiologist", mandate: "Verifies anatomical invasion, nodal ENE, and staging imaging adequacy." },
  { agent_id: "DS-03", category: "diagnostics_pathology", category_label: "Diagnostics & Pathology", name: "Molecular & Biomarker Pathologist", mandate: "Audits predictive biomarkers and molecular assay turnaround." },
  { agent_id: "PP-01", category: "patient_perspective", category_label: "Patient Perspective Lenses", name: "Quality-of-Life & Functional Preservation Lens", mandate: "Centers swallowing, speech, cosmesis, and daily independence." },
  { agent_id: "PP-02", category: "patient_perspective", category_label: "Patient Perspective Lenses", name: "Treatment Burden & Adherence Lens", mandate: "Evaluates travel frequency, caregiver support, and schedule feasibility." },
  { agent_id: "SG-01", category: "system_governance", category_label: "System, Evidence & Governance", name: "Medical Physics & Dosimetry Lead", mandate: "Audits OAR constraints, machine QA, and delivery feasibility." },
  { agent_id: "SG-07", category: "system_governance", category_label: "System, Evidence & Governance", name: "Resource & Health Equity Auditor", mandate: "Flags drug/technology access barriers and out-of-pocket burden." },
  { agent_id: "SV-01", category: "family_social_vulnerability", category_label: "Family, Social Care & Vulnerability", name: "Family & Caregiver Support Specialist", mandate: "Evaluates caregiver capacity, transport, and home support." },
  { agent_id: "SV-02", category: "family_social_vulnerability", category_label: "Family, Social Care & Vulnerability", name: "Psychosocial & Financial Vulnerability Advocate", mandate: "Flags financial toxicity and psychosocial distress." },
];

export function mapBackendAgentsToVmdtConfigs(
  agents: Agent[],
  availableFacilities: string[],
  unavailableFacilities: string[],
  defaultModel = "qwen3.5:4b",
): VmdtAgentConfig[] {
  const source = agents.length > 0 ? agents : FALLBACK_BACKEND_AGENTS;
  return source.map((agent) => {
    const teamId = resolveTeamForAgent(agent);
    const seed = hashId(agent.agent_id);
    const combinedText = `${agent.mandate} ${agent.clinical_philosophy || ""}`.toLowerCase();
    const isResourceConstrained =
      ["RO-03", "RO-04", "RO-05", "MO-01", "MO-04", "MO-05", "SO-02", "DS-02", "SG-01", "SG-07"].includes(
        agent.agent_id,
      ) ||
      /imrt|proton|cyberknife|cisplatin|pet|ngs|resource|facility|genomic|robotic/.test(combinedText);

    return {
      id: agent.agent_id,
      backendAgentId: agent.agent_id,
      displayName: `${agent.agent_id} • ${agent.name}`,
      specialty: agent.category_label || TEAM_DEFINITIONS[teamId].label,
      subspecialty: agent.name,
      teamId,
      innatePersonality: `${agent.mandate}${agent.clinical_philosophy ? ` Philosophy: ${agent.clinical_philosophy}` : ""}`,
      personalitySummary:
        agent.clinical_philosophy ||
        agent.mandate.split(".")[0] ||
        "Guideline-grounded multidisciplinary specialist",
      active: true,
      resourceConstrained: isResourceConstrained,
      availableResources: isResourceConstrained ? [...availableFacilities] : [],
      unavailableResources: isResourceConstrained ? [...unavailableFacilities] : [],
      model: defaultModel,
      temperature: 0.25,
      extraInstructions: "",
      avatarVariant: seed % 8,
      scrubColor: SCRUB_PALETTE[seed % SCRUB_PALETTE.length],
      hasGlasses: seed % 3 === 0,
      propType: PROPS[seed % PROPS.length],
    };
  });
}

export function buildDefaultAuditFindings(
  caseData: SyntheticCasePayload,
  _activeAgents: VmdtAgentConfig[],
): AuditFinding[] {
  const findings: AuditFinding[] = [];

  if (!caseData.pathology_summary || !caseData.pathology_summary.trim()) {
    findings.push({
      id: "audit-pathology-summary",
      severity: "critical",
      specialty: "Diagnostics & Pathology",
      fieldKey: "pathology_summary",
      domain: "pathology",
      title: "Histopathology, receptor / biomarker panel, or Ki-67 status missing",
      description:
        "Confirm detailed histopathology, margin/grade markers (e.g., Ki-67, HER2, ER/PR, or p16/HPV status) so systemic and radiation plans align accurately.",
      placeholder: "Enter Ki-67 proliferation index, IHC/p16/HER2 status, or biopsy details...",
    });
  }

  if (!caseData.clinical_t_stage || !caseData.clinical_n_stage || !caseData.clinical_m_stage) {
    findings.push({
      id: "audit-tnm-stage",
      severity: "critical",
      specialty: "Radiation Oncology",
      fieldKey: "clinical_t_stage",
      domain: "staging",
      title: "Explicit clinical T / N / M staging fields incomplete",
      description:
        "Specify cT, cN, and cM categories so STG-00 can cross-verify clinical and imaging findings before locking stage.",
      placeholder: "e.g., cT2 N1 M0",
    });
  }

  if (!caseData.imaging_summary || !caseData.imaging_summary.trim()) {
    findings.push({
      id: "audit-imaging-summary",
      severity: "critical",
      specialty: "Diagnostics & Pathology",
      fieldKey: "imaging_summary",
      domain: "imaging",
      title: "Cross-sectional staging imaging (CT / MRI / PET-CT) not documented",
      description:
        "Document primary extent, nodal size/level/ENE, and distant metastasis workup so STG-00 and Radiology can validate nodal status.",
      placeholder: "Enter CECT / MRI / PET-CT findings and nodal status...",
    });
  }

  if (!caseData.performance_status || !caseData.performance_status.trim()) {
    findings.push({
      id: "audit-performance-status",
      severity: "recommended",
      specialty: "Medical Oncology",
      fieldKey: "performance_status",
      domain: "fitness",
      title: "Baseline performance status (ECOG / KPS) not recorded",
      description:
        "Provide ECOG or Karnofsky score with named scale to inform fitness for concurrent chemotherapy vs single-modality therapy.",
      placeholder: "e.g., ECOG 1",
    });
  }

  if (!caseData.relevant_comorbidities || caseData.relevant_comorbidities.length === 0) {
    findings.push({
      id: "audit-comorbidities",
      severity: "recommended",
      specialty: "Medical Oncology",
      fieldKey: "relevant_comorbidities",
      domain: "comorbidities",
      title: "Organ function, renal clearance & comorbidities not listed",
      description:
        "Specify baseline renal/cardiac/audiology history or state 'None reported' for cisplatin vs carboplatin eligibility.",
      placeholder: "e.g., Hypertension, eGFR 78 mL/min, no baseline neuropathy",
    });
  }

  if (!caseData.prior_treatment || caseData.prior_treatment.length === 0) {
    findings.push({
      id: "audit-prior-tx",
      severity: "recommended",
      specialty: "Radiation Oncology",
      fieldKey: "prior_treatment",
      domain: "prior_therapy",
      title: "Prior radiation dose records or systemic therapy history missing",
      description:
        "Document prior surgery, systemic regimens, or previous radiation fields (or confirm treatment-naive).",
      placeholder: "e.g., Treatment-naive; no prior RT or chemotherapy",
    });
  }

  if (!caseData.patient_goals || caseData.patient_goals.length === 0) {
    findings.push({
      id: "audit-patient-goals",
      severity: "recommended",
      specialty: "Patient Perspective Lenses",
      fieldKey: "patient_goals",
      domain: "patient_goals",
      title: "Documented patient priorities & organ-preservation goals",
      description:
        "Capture patient preferences regarding organ/voice/cosmetic preservation vs surgical cure and travel constraints.",
      placeholder: "e.g., Prioritizes organ and swallowing preservation",
    });
  }

  return findings;
}

export const SEED_ARCHIVED_CASES: ArchivedCase[] = [
  {
    id: "case-seed-0412",
    caseCode: "MDT-2026-0412",
    patientName: "Synthetic Case 0412",
    ageSex: "62F",
    primarySite: "Left Breast (Upper Outer Quadrant)",
    diagnosis: "Invasive Ductal Carcinoma",
    stage: "Stage IIB",
    status: "Completed",
    consensusPercent: 94,
    createdAt: "2026-11-26 10:42",
    primaryRecommendation:
      "Neoadjuvant AC-T chemotherapy followed by breast-conserving surgery, sentinel lymph node biopsy / axillary evaluation, and adjuvant whole-breast hypofractionated radiotherapy with tumor bed boost.",
    clinicalRationale: [
      "Receptor profile (ER+/PR+/HER2-) and nodal burden favor downstaging with neoadjuvant systemic therapy to optimize breast conservation.",
      "Diagnostics & Pathology confirmed unifocal disease amenable to hypofractionated WBI (40 Gy / 15 fractions + sequential boost) following margin-negative resection.",
      "NCCN and ESTRO guidelines support endocrine maintenance post-radiotherapy for durable locoregional and distant control.",
    ],
    followUpPlan: [
      "Complete baseline echocardiogram & hepatic/renal panel before neoadjuvant AC-T cycle 1.",
      "Restaging breast MRI after 4 cycles to confirm partial/complete response for surgical planning.",
      "Deep-inspiration breath hold (DIBH) CT simulation post-operatively for cardiac sparing.",
    ],
    dissentingViews: [
      "SO-01 noted upfront mastectomy remains an alternative if post-neoadjuvant MRI reveals multifocal residual disease.",
    ],
    radiationPlan: "Hypofractionated WBI 40.05 Gy / 15 fx + 10 Gy boost with DIBH cardiac sparing",
    systemicPlan: "Neoadjuvant ddAC x4 -> Paclitaxel x12 followed by adjuvant AI endocrine therapy",
    surgicalPlan: "Breast-conserving lumpectomy + SLNB post-NAT with R0 margin confirmation",
    evidenceSummary: "94% MDT consensus grounded in NCCN Breast v2026 & ESTRO/START-B hypofractionation data.",
    specialtyWeighting: [
      { team: "Medical Oncology", weight: 35, color: "#818CF8" },
      { team: "Radiation Oncology", weight: 30, color: "#38BDF8" },
      { team: "Surgical Oncology", weight: 20, color: "#34D399" },
      { team: "Diagnostics & Pathology", weight: 15, color: "#2DD4BF" },
    ],
    participatingAgents: [
      { id: "MO-01", name: "MO-01 • High-Dose Cisplatin & Guideline Purist", specialty: "Medical Oncology", position: "supports", conclusion: "Endorses neoadjuvant ddAC-T prior to breast conservation.", status: "completed" },
      { id: "RO-01", name: "RO-01 • Guideline-focused Radiation Oncologist", specialty: "Radiation Oncology", position: "supports", conclusion: "Recommends DIBH hypofractionated WBI 40.05 Gy / 15 fx.", status: "completed" },
      { id: "SO-01", name: "SO-01 • Guideline-Focused Surgical Oncologist", specialty: "Surgical Oncology", position: "conditional", conclusion: "Supports BCS + SLNB conditional on post-NAT MRI response.", status: "completed" },
      { id: "DS-01", name: "DS-01 • Histopathologist", specialty: "Diagnostics & Pathology", position: "supports", conclusion: "ER+/PR+/HER2- Grade 2 confirmed; Ki-67 28%.", status: "completed" },
    ],
    caseSnapshot: {
      scenario_title: "Left Breast Invasive Ductal Carcinoma — Stage IIB",
      case_summary: "62-year-old female with 3.2 cm left breast IDC, clinically cT2 N1 M0, ER+/PR+/HER2-.",
      age_years: 62,
      sex_at_birth: "Female",
      primary_site: "Left breast",
      histology: "Invasive ductal carcinoma",
      clinical_t_stage: "T2",
      clinical_n_stage: "N1",
      clinical_m_stage: "M0",
      stage_group: "IIB",
      performance_status: "ECOG 0",
    },
  },
  {
    id: "case-seed-0411",
    caseCode: "MDT-2026-0411",
    patientName: "Synthetic Case 0411",
    ageSex: "54M",
    primarySite: "Right Temporal Lobe",
    diagnosis: "Glioblastoma Multiforme, IDH-wildtype",
    stage: "WHO Grade 4",
    status: "Stopped Early",
    consensusPercent: 72,
    createdAt: "2026-11-25 16:18",
    primaryRecommendation:
      "Simulation stopped during Round 2 pending MGMT promoter methylation assay completion; provisional consensus favors maximal safe resection followed by Stupp chemoradiation (60 Gy / 30 fx + temozolomide).",
    clinicalRationale: [
      "Post-operative MRI confirms >90% resection of enhancing tumor without new motor deficit.",
      "MGMT promoter methylation status remains pending for elderly/borderline temozolomide benefit stratification.",
    ],
    followUpPlan: [
      "Expedite MGMT methylation & IDH/1p19q molecular report from Diagnostics & Pathology.",
      "Re-run simulation once molecular report arrives before locking concurrent TMZ.",
    ],
    dissentingViews: [
      "MO-03 recommends withholding concurrent temozolomide until MGMT methylation returns if hepatic transaminases rise.",
    ],
    radiationPlan: "60 Gy in 30 fractions (IMRT/VMAT) with 2 cm CTV margin respecting optic chiasm <=54 Gy",
    systemicPlan: "Concurrent daily temozolomide 75 mg/m² + 6 adjuvant cycles (pending MGMT)",
    surgicalPlan: "Maximal safe craniotomy achieved; post-op MRI within 48h reviewed",
    evidenceSummary: "72% partial consensus — stopped early in Round 2 awaiting MGMT assay.",
    specialtyWeighting: [
      { team: "Radiation Oncology", weight: 35, color: "#38BDF8" },
      { team: "Medical Oncology", weight: 30, color: "#818CF8" },
      { team: "Surgical Oncology", weight: 20, color: "#34D399" },
      { team: "Diagnostics & Pathology", weight: 15, color: "#2DD4BF" },
    ],
    participatingAgents: [
      { id: "RO-01", name: "RO-01 • Guideline-focused Radiation Oncologist", specialty: "Radiation Oncology", position: "supports", conclusion: "Stupp 60 Gy/30 fx with tight brainstem/chiasm sparing.", status: "completed" },
      { id: "MO-03", name: "MO-03 • Geriatric & Organ-Reserve Oncologist", specialty: "Medical Oncology", position: "conditional", conclusion: "TMZ conditional on MGMT methylation result.", status: "completed" },
      { id: "DS-01", name: "DS-01 • Histopathologist", specialty: "Diagnostics & Pathology", position: "insufficient_information", conclusion: "MGMT assay pending.", status: "paused" },
    ],
    caseSnapshot: {
      scenario_title: "Right Temporal Glioblastoma, IDH-wildtype",
      case_summary: "54-year-old male status post right temporal craniotomy for IDH-wt GBM; MGMT pending.",
      age_years: 54,
      sex_at_birth: "Male",
      primary_site: "Brain - right temporal lobe",
      histology: "Glioblastoma, IDH-wildtype, WHO Grade 4",
      stage_group: "Grade IV",
      performance_status: "KPS 90",
    },
  },
  {
    id: "case-seed-0410",
    caseCode: "MDT-2026-0410",
    patientName: "Synthetic Case 0410",
    ageSex: "47F",
    primarySite: "Mid-Rectum",
    diagnosis: "Colorectal Adenocarcinoma",
    stage: "Stage IIIB",
    status: "Completed",
    consensusPercent: 91,
    createdAt: "2026-11-24 14:05",
    primaryRecommendation:
      "Total Neoadjuvant Therapy (TNT) with long-course chemoradiotherapy (50.4 Gy in 28 fractions + capecitabine) followed by consolidation CAPEOX/FOLFOX and TME evaluation.",
    clinicalRationale: [
      "MRI pelvis demonstrates cT3b mesorectal invasion with 3 suspicious mesorectal lymph nodes (cN1b) and threatened CRM.",
      "pMMR / MSS status excludes upfront single-agent PD-1 checkpoint blockade; RAPIDO/OPRA TNT paradigm supports high R0 & organ-preservation potential.",
    ],
    followUpPlan: [
      "Complete dihydropyrimidine dehydrogenase (DPD) testing prior to capecitabine.",
      "Endoscopic + MRI restaging 8 weeks post-TNT to evaluate cCR vs TME resection.",
    ],
    dissentingViews: [
      "RO-02 favors conventional long-course 50.4 Gy over short-course 25 Gy/5 fx given threatened CRM.",
    ],
    radiationPlan: "Long-course pelvic IMRT 45 Gy + 5.4 Gy mesorectal boost (50.4 Gy / 28 fx)",
    systemicPlan: "Concurrent capecitabine 825 mg/m² BID + consolidation CAPEOX x4-6 cycles",
    surgicalPlan: "Delayed TME assessment after TNT completion and MRI restaging",
    evidenceSummary: "91% MDT consensus under AJCC 8th Edition cT3 N1b M0 (Stage IIIB).",
    specialtyWeighting: [
      { team: "Radiation Oncology", weight: 32, color: "#38BDF8" },
      { team: "Surgical Oncology", weight: 28, color: "#34D399" },
      { team: "Medical Oncology", weight: 25, color: "#818CF8" },
      { team: "Diagnostics & Pathology", weight: 15, color: "#2DD4BF" },
    ],
    participatingAgents: [
      { id: "RO-02", name: "RO-02 • Conservative & Time-Tested Radiation Oncologist", specialty: "Radiation Oncology", position: "supports", conclusion: "Long-course CRT 50.4 Gy preferred for CRM protection.", status: "completed" },
      { id: "MO-01", name: "MO-01 • High-Dose Cisplatin & Guideline Purist", specialty: "Medical Oncology", position: "supports", conclusion: "Consolidation TNT improves distant control.", status: "completed" },
      { id: "SO-01", name: "SO-01 • Guideline-Focused Surgical Oncologist", specialty: "Surgical Oncology", position: "supports", conclusion: "Plan TME or watch-and-wait contingent on MRI.", status: "completed" },
    ],
    caseSnapshot: {
      scenario_title: "Mid-Rectal Adenocarcinoma — Stage IIIB (cT3 N1b M0)",
      case_summary: "47-year-old female with pMMR mid-rectal adenocarcinoma invading mesorectal fat with 3 mesorectal nodes.",
      age_years: 47,
      sex_at_birth: "Female",
      primary_site: "Rectum",
      histology: "Adenocarcinoma (pMMR/MSS)",
      clinical_t_stage: "T3",
      clinical_n_stage: "N1b",
      clinical_m_stage: "M0",
      stage_group: "IIIB",
      performance_status: "ECOG 0",
    },
  },
];

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function exportCaseAsPdf(
  item: ArchivedCase,
  institutionName: string,
  includeBranding: boolean,
): void {
  const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(item.caseCode)} — Virtual MDT Consensus Report</title>
  <style>
    body { font-family: "Segoe UI", system-ui, sans-serif; color: #0f172a; margin: 36px; line-height: 1.5; }
    .header { border-bottom: 2px solid #0284c7; padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }
    .brand { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #0369a1; font-weight: 700; }
    h1 { margin: 4px 0 0; font-size: 22px; }
    .meta { color: #475569; font-size: 13px; margin-top: 4px; }
    .pill { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 13px; }
    .card { border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px 18px; margin-bottom: 14px; background: #f8fafc; }
    h2 { font-size: 15px; margin: 0 0 8px; color: #0f172a; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
    .footer { margin-top: 24px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 10px; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      ${includeBranding ? `<div class="brand">Virtual MDT • ${escapeHtml(institutionName)}</div>` : ""}
      <h1>${escapeHtml(item.caseCode)} — ${escapeHtml(item.patientName)} (${escapeHtml(item.ageSex)})</h1>
      <div class="meta">${escapeHtml(item.diagnosis)} • ${escapeHtml(item.stage)} • ${escapeHtml(item.createdAt)}</div>
    </div>
    <div class="pill">${item.consensusPercent}% Chair Consensus</div>
  </div>
  <div class="card">
    <h2>Primary Recommendation</h2>
    <p>${escapeHtml(item.primaryRecommendation)}</p>
  </div>
  <div class="card">
    <h2>Clinical Rationale</h2>
    <ul>${item.clinicalRationale.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
  </div>
  <div class="grid">
    <div class="card"><h2>Radiation Plan</h2><p>${escapeHtml(item.radiationPlan)}</p></div>
    <div class="card"><h2>Systemic Therapy</h2><p>${escapeHtml(item.systemicPlan)}</p></div>
    <div class="card"><h2>Surgical Plan</h2><p>${escapeHtml(item.surgicalPlan)}</p></div>
    <div class="card"><h2>Follow-Up Plan</h2><ul>${item.followUpPlan.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul></div>
  </div>
  <div class="footer">
    Educational simulation record only — not a clinical treatment instruction or medical order.
  </div>
</body>
</html>`;

  const win = window.open("", "_blank", "width=920,height=720");
  if (win) {
    win.document.open();
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 250);
  } else {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.caseCode}-report.html`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
