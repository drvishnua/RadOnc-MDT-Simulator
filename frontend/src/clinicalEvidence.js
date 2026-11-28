export const LANDMARK_TRIALS = [
  {
    id: "PACIFIC",
    name: "PACIFIC (NEJM 2017/2018)",
    citation: "Antonia SJ, et al. Durvalumab after Chemoradiotherapy in Stage III Non-Small-Cell Lung Cancer. N Engl J Med 2017;377:1919-1929.",
    phase: "Phase 3 Randomized",
    year: 2017,
    primarySite: "Thorax",
    population: "Unresectable Stage III NSCLC without progression after definitive concurrent CRT (54-66 Gy)",
    primaryEndpoint: "PFS and OS",
    outcome: "Durvalumab consolidation improved 5-year OS to 42.9% vs 33.4% placebo (HR 0.72, p=0.0025). Median PFS 16.9 vs 5.6 months.",
    radOncTakeaway: "Consolidation Durvalumab for 12 months is standard of care following concurrent platinum-based chemoradiotherapy in unresectable Stage III NSCLC.",
    pmid: "28885887",
    guidelineLevel: "Category 1 (NCCN / ASTRO)"
  },
  {
    id: "RAPIDO",
    name: "RAPIDO (Lancet Oncol 2021)",
    citation: "Bahadoer RR, et al. Short-course radiotherapy followed by chemotherapy before total mesorectal excision (RAPIDO). Lancet Oncol 2021;22:29-42.",
    phase: "Phase 3 Randomized",
    year: 2021,
    primarySite: "Pelvis / Rectum",
    population: "Locally advanced rectal cancer (cT4a/b, cN2, involved CRM, EMVI+)",
    primaryEndpoint: "Disease-related treatment failure (DrTF) at 3 years",
    outcome: "Short-course RT (5x5 Gy) + CAPOX/FOLFOX consolidation reduced 3-year DrTF to 23.7% vs 30.4% with standard CRT (HR 0.75, p=0.019); doubled pCR rate (28% vs 14%).",
    radOncTakeaway: "Total Neoadjuvant Therapy (TNT) with short-course RT + consolidation chemo is standard for high-risk LARC and facilitates organ preservation.",
    pmid: "33301740",
    guidelineLevel: "Category 1 (NCCN / ESMO)"
  },
  {
    id: "PRODIGE-23",
    name: "PRODIGE 23 (Lancet Oncol 2021)",
    citation: "Conroy T, et al. Neoadjuvant chemotherapy with FOLFIRINOX and preoperative chemoradiotherapy for patients with locally advanced rectal cancer (PRODIGE 23). Lancet Oncol 2021;22:70-80.",
    phase: "Phase 3 Randomized",
    year: 2021,
    primarySite: "Pelvis / Rectum",
    population: "cT3 or cT4 rectal adenocarcinoma",
    primaryEndpoint: "3-year disease-free survival (DFS)",
    outcome: "Induction FOLFIRINOX prior to preoperative CRT improved 3-year DFS (76% vs 69%, HR 0.69, p=0.034) and metastasis-free survival.",
    radOncTakeaway: "TNT with induction triplet chemotherapy followed by long-course chemoradiotherapy offers superior systemic control and high response rates.",
    pmid: "33301741",
    guidelineLevel: "Category 1 (NCCN)"
  },
  {
    id: "CROSS",
    name: "CROSS (NEJM 2012)",
    citation: "van Hagen P, et al. Preoperative chemoradiotherapy for esophageal or junctional cancer. N Engl J Med 2012;366:2074-2084.",
    phase: "Phase 3 Randomized",
    year: 2012,
    primarySite: "Thorax / Esophagus",
    population: "Resectable T1N1-3 or T2-3N0-3 esophageal or GEJ cancer",
    primaryEndpoint: "Overall survival",
    outcome: "Neoadjuvant CRT (41.4 Gy/23 fx + weekly Carboplatin/Paclitaxel) significantly improved median OS (49.4 vs 24.0 months, HR 0.657, p=0.003).",
    radOncTakeaway: "Preoperative CRT with 41.4 Gy + Carbo/Taxol is the benchmark neoadjuvant regimen for operable locally advanced esophageal and GEJ cancer.",
    pmid: "22646630",
    guidelineLevel: "Category 1 (NCCN / ASTRO)"
  },
  {
    id: "STUPP",
    name: "Stupp Protocol (NEJM 2005)",
    citation: "Stupp R, et al. Radiotherapy plus concomitant and adjuvant temozolomide for glioblastoma. N Engl J Med 2005;352:987-996.",
    phase: "Phase 3 Randomized",
    year: 2005,
    primarySite: "CNS",
    population: "Newly diagnosed Glioblastoma, age 18-70, WHO grade 4",
    primaryEndpoint: "Overall survival",
    outcome: "RT (60 Gy in 30 fx) + concurrent Temozolomide (75 mg/m2) + 6 cycles adjuvant TMZ improved 2-year survival (26.5% vs 10.4%, HR 0.63, p<0.001).",
    radOncTakeaway: "60 Gy/30 fx with concurrent daily TMZ followed by 6-12 maintenance cycles remains standard of care for newly diagnosed GBM (especially MGMT promoter methylated).",
    pmid: "15758009",
    guidelineLevel: "Category 1 (NCCN / ASTRO)"
  },
  {
    id: "RTOG-9111",
    name: "RTOG 91-11 (JCO 2013)",
    citation: "Forastiere AA, et al. Long-term results of RTOG 91-11: a comparison of three nonsurgical treatments for laryngeal preservation. J Clin Oncol 2013;31:845-852.",
    phase: "Phase 3 Randomized",
    year: 2013,
    primarySite: "Head and Neck",
    population: "Stage III/IV glottic or supraglottic squamous cell carcinoma",
    primaryEndpoint: "Larynx preservation survival",
    outcome: "Concurrent high-dose Cisplatin + RT achieved highest 10-year intact larynx rate (81.7% vs 67.5% induction vs 63.8% RT alone, p=0.005).",
    radOncTakeaway: "Concurrent CRT (70 Gy + Cisplatin 100 mg/m2 q3w) is the preferred organ-preservation standard for locally advanced laryngeal cancer.",
    pmid: "23358977",
    guidelineLevel: "Category 1 (ASTRO / NCCN)"
  },
  {
    id: "KEYNOTE-522",
    name: "KEYNOTE-522 (NEJM 2022)",
    citation: "Schmid P, et al. Event-free Survival with Neoadjuvant Pembrolizumab in Early Triple-Negative Breast Cancer. N Engl J Med 2022;386:556-567.",
    phase: "Phase 3 Randomized",
    year: 2022,
    primarySite: "Breast",
    population: "Early-stage high-risk TNBC (T1c N1-2 or T2-4 N0-2)",
    primaryEndpoint: "Pathological complete response (pCR) and Event-free survival (EFS)",
    outcome: "Neoadjuvant Pembrolizumab + chemo increased pCR to 64.8% vs 51.2% and significantly prolonged 36-month EFS (84.5% vs 76.8%, HR 0.63, p<0.001).",
    radOncTakeaway: "In TNBC with residual non-pCR after neoadjuvant chemo-immunotherapy, adjuvant post-mastectomy/post-lumpectomy RT is essential alongside adjuvant systemic therapy.",
    pmid: "35139272",
    guidelineLevel: "Category 1 (NCCN)"
  },
  {
    id: "BC2001",
    name: "BC2001 (NEJM 2012)",
    citation: "James ND, et al. Radiotherapy with or without chemotherapy in muscle-invasive bladder cancer. N Engl J Med 2012;366:1477-1488.",
    phase: "Phase 3 Randomized",
    year: 2012,
    primarySite: "Genitourinary / Bladder",
    population: "T2-T4a N0 M0 muscle-invasive bladder cancer undergoing organ-preserving treatment",
    primaryEndpoint: "Locoregional control",
    outcome: "Adding synchronous 5-FU + Mitomycin-C to RT significantly improved 2-year locoregional control (67% vs 54%, HR 0.68, p=0.03) without increasing late grade 3/4 toxicity.",
    radOncTakeaway: "Concurrent radiosensitizing chemotherapy with RT following maximal TURBT is standard of care for Trimodal Therapy (TMT) bladder preservation.",
    pmid: "22512481",
    guidelineLevel: "Category 1 (ASTRO / AUA)"
  }
];

export function getSiteConstraints(site) {
  const s = (site || "").toLowerCase();
  if (s.includes("cns") || s.includes("brain") || (s.includes("head") && s.includes("medullo"))) {
    return [
      { id: "cns_brainstem", anatomicalSite: "CNS", organ: "Brainstem", metric: "Dmax", limitValue: 54, unit: "Gy", operator: "<=", endpoint: "Cranial neuropathy / necrosis", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "cns_optic_chiasm", anatomicalSite: "CNS", organ: "Optic Chiasm", metric: "Dmax", limitValue: 50, unit: "Gy", operator: "<=", endpoint: "Optic neuropathy / blindness", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "cns_hippocampus", anatomicalSite: "CNS", organ: "Bilateral Hippocampi", metric: "D40%", limitValue: 7.3, unit: "Gy", operator: "<=", endpoint: "Neurocognitive decline (PENTEC)", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "cns_cochlea", anatomicalSite: "CNS", organ: "Cochlea", metric: "Dmean", limitValue: 35, unit: "Gy", operator: "<=", endpoint: "Sensorineural hearing loss", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "cns_spinal_cord", anatomicalSite: "CNS", organ: "Spinal Cord", metric: "Dmax", limitValue: 45, unit: "Gy", operator: "<=", endpoint: "Radiation myelopathy", riskLevel: "standard_safe", fractionationType: "conventional" }
    ];
  }
  if (s.includes("thor") || s.includes("lung") || s.includes("esoph")) {
    return [
      { id: "thx_spinal_cord", anatomicalSite: "Thorax", organ: "Spinal Cord", metric: "Dmax", limitValue: 45, unit: "Gy", operator: "<=", endpoint: "Radiation myelopathy", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "thx_lungs", anatomicalSite: "Thorax", organ: "Total Lungs (Lungs - GTV)", metric: "V20Gy", limitValue: 30, unit: "%", operator: "<=", endpoint: "Symptomatic pneumonitis", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "thx_lungs_mld", anatomicalSite: "Thorax", organ: "Mean Lung Dose (MLD)", metric: "Dmean", limitValue: 20, unit: "Gy", operator: "<=", endpoint: "Radiation pneumonitis", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "thx_heart", anatomicalSite: "Thorax", organ: "Heart", metric: "V50Gy", limitValue: 25, unit: "%", operator: "<=", endpoint: "Late cardiac mortality / pericarditis", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "thx_esophagus", anatomicalSite: "Thorax", organ: "Esophagus", metric: "Dmean", limitValue: 34, unit: "Gy", operator: "<=", endpoint: "Grade 3+ esophagitis / stricture", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "thx_brachial_plexus", anatomicalSite: "Thorax", organ: "Brachial Plexus", metric: "Dmax", limitValue: 60, unit: "Gy", operator: "<=", endpoint: "Plexopathy / neuropathy", riskLevel: "standard_safe", fractionationType: "conventional" }
    ];
  }
  if (s.includes("breast")) {
    return [
      { id: "br_heart_mean", anatomicalSite: "Breast", organ: "Heart (Whole)", metric: "Dmean", limitValue: 2.5, unit: "Gy", operator: "<=", endpoint: "Major coronary events (Darby 2013)", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "br_lad", anatomicalSite: "Breast", organ: "Left Anterior Descending (LAD)", metric: "Dmean", limitValue: 5, unit: "Gy", operator: "<=", endpoint: "Ischemic heart disease / infarction", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "br_ipsi_lung", anatomicalSite: "Breast", organ: "Ipsilateral Lung", metric: "V20Gy", limitValue: 15, unit: "%", operator: "<=", endpoint: "Pneumonitis", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "br_contra_breast", anatomicalSite: "Breast", organ: "Contralateral Breast", metric: "Dmax", limitValue: 3, unit: "Gy", operator: "<=", endpoint: "Secondary breast malignancy", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "br_humeral_head", anatomicalSite: "Breast", organ: "Humeral Head", metric: "Dmax", limitValue: 50, unit: "Gy", operator: "<=", endpoint: "Osteoradionecrosis / pain", riskLevel: "standard_safe", fractionationType: "conventional" }
    ];
  }
  if (s.includes("head") || s.includes("neck") || s.includes("oropharynx") || s.includes("larynx")) {
    return [
      { id: "hn_parotid_ipsi", anatomicalSite: "Head and Neck", organ: "Contralateral Parotid", metric: "Dmean", limitValue: 20, unit: "Gy", operator: "<=", endpoint: "Severe xerostomia", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "hn_constrictors", anatomicalSite: "Head and Neck", organ: "Pharyngeal Constrictors", metric: "Dmean", limitValue: 50, unit: "Gy", operator: "<=", endpoint: "Severe dysphagia / aspiration", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "hn_larynx", anatomicalSite: "Head and Neck", organ: "Larynx (Glottic)", metric: "Dmean", limitValue: 45, unit: "Gy", operator: "<=", endpoint: "Vocal cord edema / hoarseness", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "hn_cord", anatomicalSite: "Head and Neck", organ: "Spinal Cord", metric: "Dmax", limitValue: 45, unit: "Gy", operator: "<=", endpoint: "Myelopathy", riskLevel: "standard_safe", fractionationType: "conventional" },
      { id: "hn_mandible", anatomicalSite: "Head and Neck", organ: "Mandible", metric: "Dmax", limitValue: 66, unit: "Gy", operator: "<=", endpoint: "Osteoradionecrosis", riskLevel: "standard_safe", fractionationType: "conventional" }
    ];
  }
  return [
    { id: "pel_bowel_bag", anatomicalSite: "Pelvis", organ: "Bowel Bag (Small Bowel)", metric: "V45Gy", limitValue: 195, unit: "cc", operator: "<=", endpoint: "Grade 3+ acute/late diarrhea or obstruction", riskLevel: "standard_safe", fractionationType: "conventional" },
    { id: "pel_rectum", anatomicalSite: "Pelvis", organ: "Rectum", metric: "V50Gy", limitValue: 50, unit: "%", operator: "<=", endpoint: "Late proctitis / rectal bleeding", riskLevel: "standard_safe", fractionationType: "conventional" },
    { id: "pel_bladder", anatomicalSite: "Pelvis", organ: "Bladder", metric: "V65Gy", limitValue: 50, unit: "%", operator: "<=", endpoint: "Late cystitis / hematuria", riskLevel: "standard_safe", fractionationType: "conventional" },
    { id: "pel_femur_heads", anatomicalSite: "Pelvis", organ: "Femoral Heads", metric: "V50Gy", limitValue: 5, unit: "%", operator: "<=", endpoint: "Femoral neck necrosis / fracture", riskLevel: "standard_safe", fractionationType: "conventional" },
    { id: "pel_cauda_equina", anatomicalSite: "Pelvis", organ: "Cauda Equina", metric: "Dmax", limitValue: 55, unit: "Gy", operator: "<=", endpoint: "Neuropathy / sphincter dysfunction", riskLevel: "standard_safe", fractionationType: "conventional" }
  ];
}

export function findTrialByKeyword(query) {
  const q = (query || "").toLowerCase();
  return LANDMARK_TRIALS.find((t) =>
    t.id.toLowerCase().includes(q) ||
    t.name.toLowerCase().includes(q) ||
    t.primarySite.toLowerCase().includes(q) ||
    t.citation.toLowerCase().includes(q)
  );
}
