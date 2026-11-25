export interface PresetCase {
  id: string;
  name: string;
  badge: string;
  site: string;
  age: string;
  histology: string;
  description: string;
  form: {
    patient_name: string;
    scenario_title: string;
    case_summary: string;
    age_years: string;
    sex_at_birth: string;
    primary_site: string;
    histology: string;
    clinical_t_stage: string;
    clinical_n_stage: string;
    clinical_m_stage: string;
    stage_group: string;
    performance_status: string;
    pathology_summary: string;
    imaging_summary: string;
    current_medications: string;
    known_allergies: string;
    relevant_investigations: string;
    relevant_comorbidities: string;
    prior_treatment: string;
    patient_goals: string;
    social_context: string;
    resource_context: string;
    known_unknowns: string;
  };
}

export const PRESET_CASES: PresetCase[] = [
  {
    id: "pediatric-cns",
    name: "Child (Age 8) — Posterior Fossa Medulloblastoma",
    badge: "PEDIATRIC CNS",
    site: "Central Nervous System",
    age: "8 years",
    histology: "Medulloblastoma (Group 4)",
    description: "Post-resection 4th ventricular tumor with neurocognitive sparing and craniospinal irradiation de-escalation controversies.",
    form: {
      patient_name: "Leo (Fictional Training Child)",
      scenario_title: "Pediatric Posterior Fossa Medulloblastoma",
      case_summary: "8-year-old male with 4 weeks of morning headache and gait ataxia. Underwent gross total resection of 3.8 cm midline fourth ventricular mass. Spine MRI with contrast shows no leptomeningeal seeding. Day-15 post-op CSF cytology negative. MDT deliberation on craniospinal RT (CSI) dose de-escalation, vincristine toxicity, and PENTEC neurocognitive OAR sparing.",
      age_years: "8",
      sex_at_birth: "male",
      primary_site: "cns",
      histology: "Medulloblastoma",
      clinical_t_stage: "T2",
      clinical_n_stage: "N0",
      clinical_m_stage: "M0",
      stage_group: "Standard Risk M0",
      performance_status: "Lansky 80",
      pathology_summary: "Classic medulloblastoma, synaptophysin positive, INI-1 retained, non-WNT/non-SHH (Group 4).",
      imaging_summary: "Pre-op brain MRI: 3.8 cm 4th ventricular mass with hydrocephalus. Post-op brain MRI: Gross total resection, no residual enhancement > 1.5 cm^2. Spine MRI: Entire spine clear. CSF: Negative for malignant cells.",
      current_medications: "Dexamethasone tapering, Levetiracetam",
      known_allergies: "NKDA",
      relevant_investigations: "Audiometry baseline normal, endocrine growth hormone baseline normal",
      relevant_comorbidities: "None",
      prior_treatment: "Suboccipital craniotomy and gross total tumor resection",
      patient_goals: "Cure with maximal long-term neurocognitive and growth preservation",
      social_context: "Lives with parents, supportive family, attends primary school",
      resource_context: "Access to regional pediatric proton therapy center and pediatric oncology support",
      known_unknowns: "Formal molecular cytogenetics (17p status pending)"
    }
  },
  {
    id: "aya-ewing-sarcoma",
    name: "Youth (Age 19) — Femoral Diaphyseal Ewing Sarcoma",
    badge: "AYA SARCOMA",
    site: "Musculoskeletal / Bone",
    age: "19 years",
    histology: "Ewing Sarcoma",
    description: "College athlete with diaphyseal femur destructive lesion; limb-sparing resection vs high-dose definitive RT and fertility protection.",
    form: {
      patient_name: "Jordan (Fictional Training Youth)",
      scenario_title: "Adolescent Diaphyseal Ewing Sarcoma of Femur",
      case_summary: "19-year-old college soccer player with 3 months of right thigh pain. MRI reveals a 7.5 cm diaphyseal destructive lesion with soft tissue component. Baseline PET/CT: isolated femoral uptake (SUVmax 11.2), chest CT negative for lung metastases. Completed 6 cycles neoadjuvant VDC/IE with 75% volumetric response. Local control debate: Limb-salvage excision vs definitive radiation (55.8 Gy).",
      age_years: "19",
      sex_at_birth: "male",
      primary_site: "bone",
      histology: "Ewing sarcoma",
      clinical_t_stage: "T2",
      clinical_n_stage: "N0",
      clinical_m_stage: "M0",
      stage_group: "Stage II",
      performance_status: "ECOG 0",
      pathology_summary: "Core biopsy right femur: Small round blue cell tumor, CD99 diffuse positive, EWSR1-FLI1 rearranged.",
      imaging_summary: "Post-chemo MRI: Residual 2.8 cm diaphyseal abnormality, soft tissue component reduced to 0.8 cm. Margins to femoral vessels > 1.5 cm. PET/CT: SUVmax decreased to 2.4. Chest CT: Clear.",
      current_medications: "Filgrastim, Ondansetron",
      known_allergies: "NKDA",
      relevant_investigations: "Echocardiogram: LVEF 60%",
      relevant_comorbidities: "None",
      prior_treatment: "6 cycles neoadjuvant VDC/IE chemotherapy",
      patient_goals: "Preserve athletic limb function; ensure long-term survivorship and fertility",
      social_context: "Undergraduate student, highly motivated athlete, strong family support",
      resource_context: "Tertiary sarcoma center with specialized orthopedic oncology reconstruction",
      known_unknowns: "Sperm banking completion confirmation"
    }
  },
  {
    id: "ya-cervix",
    name: "Young Adult (Age 32) — Locally Advanced Cervical Carcinoma",
    badge: "GYNECOLOGIC",
    site: "Cervix uteri",
    age: "32 years",
    histology: "Squamous Cell Carcinoma",
    description: "Nulliparous woman with 4.2 cm cervical lesion seeking ovarian transposition prior to definitive chemoradiation + 3D brachytherapy.",
    form: {
      patient_name: "Maya (Fictional Training Patient)",
      scenario_title: "Locally Advanced Cervical Carcinoma in Young Nulliparous Woman",
      case_summary: "32-year-old nulliparous female presenting with post-coital bleeding. Pelvic MRI reveals a 4.2 cm exophytic cervical tumor invading upper 2/3 of vagina with supple parametria (FIGO IIA2). PET/CT shows intense cervical uptake; pelvic and para-aortic nodes are PET-negative. Patient strongly desires ovarian transposition prior to definitive concurrent chemoradiotherapy + 3D brachytherapy to preserve endocrine function.",
      age_years: "32",
      sex_at_birth: "female",
      primary_site: "cervix",
      histology: "Squamous cell carcinoma",
      clinical_t_stage: "T2a2",
      clinical_n_stage: "N0",
      clinical_m_stage: "M0",
      stage_group: "FIGO IIA2",
      performance_status: "ECOG 0",
      pathology_summary: "Cervical biopsy: Invasive non-keratinizing squamous cell carcinoma, p16 diffuse positive.",
      imaging_summary: "Pelvic MRI: 4.2 cm mass restricted to cervix and upper vagina. Parametria supple. PET/CT: Highly avid primary tumor; no pelvic, para-aortic, or distant metastases.",
      current_medications: "Tranexamic acid as needed for spotting",
      known_allergies: "NKDA",
      relevant_investigations: "Baseline eGFR 98 mL/min, Hemoglobin 11.8 g/dL",
      relevant_comorbidities: "None",
      prior_treatment: "Diagnostic colposcopy and cervical biopsy",
      patient_goals: "Cure disease while preserving endocrine ovarian function and sexual health",
      social_context: "Married, plans for future family via gestational surrogacy if uterus is treated",
      resource_context: "Access to high-dose-rate (HDR) MRI-guided brachytherapy and minimally invasive gynecology",
      known_unknowns: "Ovarian transposition surgical scheduling timeline before RT"
    }
  },
  {
    id: "breast-tnbc",
    name: "Middle-Age (Age 48) — Triple-Negative Breast Cancer Post-Mastectomy",
    badge: "BREAST ONCOLOGY",
    site: "Breast",
    age: "48 years",
    histology: "Invasive Ductal Carcinoma (Triple-Negative)",
    description: "Residual nodal disease post-neoadjuvant chemo-immunotherapy requiring comprehensive PMRT with DIBH cardiac sparing.",
    form: {
      patient_name: "Elena (Fictional Training Patient)",
      scenario_title: "Locally Advanced Triple-Negative Breast Cancer Post-Mastectomy with Residual Disease",
      case_summary: "48-year-old premenopausal female initially presented with 4.5 cm left inner quadrant breast mass and cN1 nodal disease. Completed neoadjuvant pembrolizumab + carboplatin/paclitaxel followed by AC. Mastectomy revealed residual 1.4 cm IDC (ypT1c) and 2/14 positive lymph nodes (ypN1a). Deep inspiration breath-hold (DIBH) planned for left anterior descending (LAD) coronary protection during comprehensive PMRT.",
      age_years: "48",
      sex_at_birth: "female",
      primary_site: "breast",
      histology: "Invasive ductal carcinoma",
      clinical_t_stage: "ypT1c",
      clinical_n_stage: "ypN1a",
      clinical_m_stage: "cM0",
      stage_group: "Stage IIA",
      performance_status: "ECOG 0",
      pathology_summary: "Left mastectomy: Residual invasive ductal carcinoma grade 3, ypT1c (1.4 cm), 2/14 nodes positive (ypN1a, largest 3.5 mm without ENE). ER 0%, PR 0%, HER2 0, Ki-67 80%. Margins negative.",
      imaging_summary: "Post-op CT/PET: No residual axillary or internal mammary adenopathy, no distant metastases.",
      current_medications: "Pembrolizumab maintenance",
      known_allergies: "Penicillin (rash)",
      relevant_investigations: "Echocardiogram: LVEF 62%, normal cardiac function",
      relevant_comorbidities: "Mild asthma",
      prior_treatment: "Neoadjuvant chemo-immunotherapy, Left modified radical mastectomy",
      patient_goals: "Minimize locoregional recurrence while protecting heart and lung tissue",
      social_context: "Employed professional, active lifestyle, two teenage children",
      resource_context: "Linear accelerator equipped with surface-guided radiation therapy (SGRT) and DIBH",
      known_unknowns: "BRCA1/2 germline genetic testing results pending"
    }
  },
  {
    id: "head-neck-p16",
    name: "Adult (Age 57) — HPV-Positive Oropharyngeal Carcinoma",
    badge: "HEAD & NECK",
    site: "Oropharynx (Left Tonsil)",
    age: "57 years",
    histology: "Squamous Cell Carcinoma (p16+)",
    description: "T2N1 tonsillar carcinoma evaluating definitive IMRT vs TORS, bilateral vs unilateral neck RT, and swallow constrictor sparing.",
    form: {
      patient_name: "Arthur (Fictional Training Patient)",
      scenario_title: "HPV-Positive Oropharyngeal Carcinoma with Unilateral Nodal Disease",
      case_summary: "57-year-old male non-smoker with 6-week history of painless left neck lump. Nasopharyngoscopy shows 2.4 cm left palatine tonsil mass. FNA confirms p16+ squamous cell carcinoma. Contrast CT / PET shows solitary 2.6 cm left level IIA lymph node without extranodal extension (ENE). Contralateral neck and distant organs clear. Excellent ECOG 0 and completed preventive dental clearance.",
      age_years: "57",
      sex_at_birth: "male",
      primary_site: "oropharynx",
      histology: "Squamous cell carcinoma",
      clinical_t_stage: "T2",
      clinical_n_stage: "N1",
      clinical_m_stage: "M0",
      stage_group: "Stage I (AJCC 8th p16+)",
      performance_status: "ECOG 0",
      pathology_summary: "Tonsil biopsy & FNA: Non-keratinizing squamous cell carcinoma, p16 diffuse positive (>70%).",
      imaging_summary: "Neck CT / PET: 2.4 cm left tonsillar lesion, solitary left level IIA node 2.6 cm (ENE negative). Contralateral neck clean. Staging CT chest/abdomen negative.",
      current_medications: "None",
      known_allergies: "NKDA",
      relevant_investigations: "Full dental oncology clearance completed with fluoridated trays fabricated",
      relevant_comorbidities: "None",
      prior_treatment: "Diagnostic tonsillar biopsy and ultrasound-guided FNA neck node",
      patient_goals: "High cure rate with preservation of speech and swallowing function (avoid late xerostomia/dysphagia)",
      social_context: "High-school teacher, relies heavily on clear voice and vocal stamina",
      resource_context: "High-precision volumetric modulated arc therapy (VMAT) with daily cone-beam CT",
      known_unknowns: "Baseline speech-language pathology (SLP) swallowing video-fluoroscopy pending"
    }
  },
  {
    id: "rectal-tnt",
    name: "Senior (Age 66) — Mid-Rectal Adenocarcinoma with Threatened CRM",
    badge: "GI / COLORECTAL",
    site: "Rectum",
    age: "66 years",
    histology: "Adenocarcinoma (pMMR/MSS)",
    description: "Locally advanced rectal tumor seeking Total Neoadjuvant Therapy (TNT) and Watch-and-Wait organ preservation to avoid permanent stoma.",
    form: {
      patient_name: "Robert (Fictional Training Patient)",
      scenario_title: "Locally Advanced Mid-Rectal Adenocarcinoma with Threatened CRM",
      case_summary: "66-year-old male presenting with rectal bleeding and altered bowel habits. Flexible sigmoidoscopy shows ulcerated tumor 6 cm from anal verge. Pelvic MRI demonstrates tumor invading mesorectal fat by 7 mm (T3c) with threatened mesorectal fascia (distance 0.8 mm) and 3 suspicious mesorectal nodes (N1b). Staging CT negative for distant metastasis. Patient strongly desires to avoid permanent colostomy through TNT and Watch-and-Wait.",
      age_years: "66",
      sex_at_birth: "male",
      primary_site: "rectum",
      histology: "Adenocarcinoma",
      clinical_t_stage: "T3c",
      clinical_n_stage: "N1b",
      clinical_m_stage: "M0",
      stage_group: "Stage IIIB",
      performance_status: "ECOG 0",
      pathology_summary: "Rectal biopsy: Moderately differentiated adenocarcinoma, pMMR/MSS, KRAS wild-type, BRAF wild-type.",
      imaging_summary: "High-resolution Pelvic MRI: 4.2 cm mid-rectal tumor, mesorectal fat invasion 7 mm (T3c), CRM 0.8 mm (threatened), EMVI positive, 3 mesorectal nodes (N1b). CT chest/abdomen/pelvis: No metastases.",
      current_medications: "Atorvastatin, Lisinopril",
      known_allergies: "NKDA",
      relevant_investigations: "Colonoscopy complete to cecum, CEA 6.4 ng/mL",
      relevant_comorbidities: "Controlled hypertension, mild hyperlipidemia",
      prior_treatment: "Colonoscopy and biopsy",
      patient_goals: "Avoid permanent colostomy; pursue non-operative management (Watch-and-Wait) if clinical complete response achieved",
      social_context: "Retired accountant, active walker, supportive spouse",
      resource_context: "Multidisciplinary colorectal tumor board with dedicated high-resolution rectal MRI protocol",
      known_unknowns: "Formal digital rectal exam mapping of sphincter involvement"
    }
  },
  {
    id: "bladder-tmt",
    name: "Elderly (Age 74) — Muscle-Invasive Bladder Urothelial Carcinoma",
    badge: "GENITOURINARY",
    site: "Urinary Bladder",
    age: "74 years",
    histology: "High-Grade Urothelial Carcinoma",
    description: "Trimodal bladder preservation candidate refusing radical cystectomy; managing radiosensitizer choice in moderate renal impairment.",
    form: {
      patient_name: "Eleanor (Fictional Training Patient)",
      scenario_title: "Muscle-Invasive Urothelial Bladder Carcinoma Seeking Organ Preservation",
      case_summary: "74-year-old female with baseline eGFR 48 mL/min/1.73m^2 presenting with gross hematuria. Visually complete TURBT resected a 3.5 cm right lateral wall mass. Pathology confirms detrusor muscle invasion (cT2a). Pelvic MRI and CT urogram show no extravesical extension or hydronephrosis. Patient adamantly refuses radical cystectomy with urostomy bag and requests trimodal bladder preservation (TMT: maximal TURBT + concurrent chemoradiation).",
      age_years: "74",
      sex_at_birth: "female",
      primary_site: "bladder",
      histology: "Urothelial carcinoma",
      clinical_t_stage: "cT2a",
      clinical_n_stage: "cN0",
      clinical_m_stage: "cM0",
      stage_group: "Stage II",
      performance_status: "ECOG 1",
      pathology_summary: "TURBT right lateral wall: High-grade invasive urothelial carcinoma invading deep muscularis propria. LVI negative.",
      imaging_summary: "Pelvic MRI: Focal wall thickening at resection site without extravesical fat stranding. Pelvic nodes < 8 mm. CT Urogram: Normal upper tracts. Chest CT: Clear.",
      current_medications: "Amlodipine, Hydrochlorothiazide",
      known_allergies: "Sulfa drugs",
      relevant_investigations: "eGFR 48 mL/min (moderate renal impairment, borderline for high-dose cisplatin)",
      relevant_comorbidities: "Hypertension, Stage 3a chronic kidney disease",
      prior_treatment: "Visually complete transurethral resection of bladder tumor (TURBT)",
      patient_goals: "Bladder preservation; avoid stoma or urostomy bag while ensuring curative-intent local control",
      social_context: "Lives independently in senior community, avid gardener, values urinary autonomy",
      resource_context: "Adaptive radiotherapy clinic with daily bladder filling protocol verification",
      known_unknowns: "Nephrology assessment for concurrent radiosensitizing agent suitability"
    }
  },
  {
    id: "geriatric-lung-sbrt",
    name: "Geriatric (Age 81) — Medically Inoperable Peripheral Lung Adenocarcinoma",
    badge: "THORACIC SBRT",
    site: "Lung (Right Upper Lobe Peripheral)",
    age: "81 years",
    histology: "Adenocarcinoma",
    description: "Octogenarian with severe COPD on home oxygen; definitive curative SBRT (54 Gy in 3 fx) avoiding operative cardiopulmonary mortality.",
    form: {
      patient_name: "Harold (Fictional Training Patient)",
      scenario_title: "Early Stage Peripheral NSCLC in Medically Inoperable Octogenarian",
      case_summary: "81-year-old male with severe COPD (FEV1 32% predicted, on 2 L/min home oxygen) and prior CABG. Surveillance CT reveals a 2.5 cm solid peripheral right upper lobe pulmonary nodule located 1.8 cm from parietal pleura. PET/CT confirms intense FDG uptake (SUVmax 9.2); mediastinal nodes negative. Biopsy proved invasive adenocarcinoma. Thoracic surgery declared patient medically inoperable. Referral for definitive Stereotactic Body Radiotherapy (SBRT / SABR).",
      age_years: "81",
      sex_at_birth: "male",
      primary_site: "lung",
      histology: "Adenocarcinoma",
      clinical_t_stage: "cT1c",
      clinical_n_stage: "cN0",
      clinical_m_stage: "cM0",
      stage_group: "Stage IA3",
      performance_status: "ECOG 2",
      pathology_summary: "CT-guided lung biopsy: Invasive adenocarcinoma, acinar predominant, TTF-1 positive, p40 negative.",
      imaging_summary: "Chest CT & PET/CT: 2.5 cm peripheral RUL nodule (SUVmax 9.2), > 3 cm from proximal bronchial tree. Hilar/mediastinal nodes PET-negative. Brain MRI: No metastases.",
      current_medications: "Tiotropium, Budesonide/Formoterol inhaler, Aspirin, Metoprolol, Home Oxygen (2 L/min)",
      known_allergies: "Codeine (nausea)",
      relevant_investigations: "Pulmonary Function Tests: FEV1 0.85 L (32% predicted), DLCO 38%",
      relevant_comorbidities: "Severe COPD (GOLD Stage 4), Coronary Artery Disease post-CABG, Heart failure with preserved ejection fraction",
      prior_treatment: "Diagnostic CT-guided transthoracic needle biopsy",
      patient_goals: "Non-invasive cure without hospitalization, preserving remaining lung capacity",
      social_context: "Lives with elderly spouse, receives family caregiver assistance for heavy chores",
      resource_context: "4D-CT simulation with respiratory gating / compression for target motion management",
      known_unknowns: "Motion amplitude on 4D-CT simulation (respiratory excursion evaluation)"
    }
  }
];
