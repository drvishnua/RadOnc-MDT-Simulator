import json
import os

entries = [
    # MAIN & RADONC
    {
        "id": "PEREZ-BRADY-8TH",
        "title": "Perez and Brady's Principles and Practice of Radiation Oncology",
        "authors": ["Halperin EC", "Wazer DE", "Perez CA", "Brady LW"],
        "edition": "8th Edition (2026)",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "principles", "head_neck", "technique", "dose_fractionation", "oropharynx", "definitive_radiotherapy"],
        "relative_path": "MAIN/2026_Edward_C_Halperin,_David_E_Wazer_Perez,_Brady,_Halperin,_and.pdf",
        "summary": "Authoritative radiation oncology treatise covering anatomy, staging, target definition, normal tissue tolerances, clinical trials, and multi-agent chemoradiotherapy schedules for head, neck, and pelvic malignancies."
    },
    {
        "id": "GUNDERSON-TEPPER-5TH",
        "title": "Clinical Radiation Oncology",
        "authors": ["Gunderson LL", "Tepper JE", "Bogart JA"],
        "edition": "5th Edition (2021)",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "clinical_management", "organ_preservation", "combined_modality", "oropharynx", "chemoradiation"],
        "relative_path": "MAIN/gun-tep-cli-rad-onc-5th.pdf",
        "summary": "Standard reference for disease site-specific clinical management, multidisciplinary care, organ preservation protocols, concurrent systemic therapy integration, and contouring."
    },
    {
        "id": "ESSENTIALS-CLIN-RADONC-2026",
        "title": "Essentials of Clinical Radiation Oncology",
        "authors": ["Dawson LA", "Kavanagh BD", "Marks LB"],
        "edition": "2026 Edition",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "clinical_practice", "dose_constraints", "fractionation", "rapid_reference"],
        "relative_path": "MAIN/2026 Essentials of Clinical Rad Onco.pdf",
        "summary": "High-yield clinical radiation oncology text detailing treatment algorithms, contouring pearls, organ-at-risk dose constraints, and definitive fractionation regimens."
    },
    {
        "id": "DECISION-MAKING-RADONC",
        "title": "Decision Making in Radiation Oncology",
        "authors": ["Lu JJ", "Brady LW"],
        "edition": "Comprehensive Edition",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "clinical_decisions", "treatment_algorithms", "evidence_based"],
        "relative_path": "VCR/Decision Making in Radiation Oncology.pdf",
        "summary": "Algorithm-driven clinical decision pathways for evaluating surgical versus definitive radiation pathways across stages and performance statuses."
    },
    {
        "id": "HANDBOOK-EVIDENCE-RADONC",
        "title": "Handbook of Evidence-Based Radiation Oncology",
        "authors": ["Hansen EK", "Roach M"],
        "edition": "4th Edition",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "evidence_based", "clinical_trials", "randomized_data"],
        "relative_path": "VCR/Handbook of Evidence-Based Radiation Oncology.pdf",
        "summary": "Evidence syntheses of landmark randomized controlled trials supporting current radiation doses, fractionation regimens, and concurrent systemic combinations."
    },
    {
        "id": "RADONC-QUESTION-BASED-REVIEW",
        "title": "Radiation Oncology: A Question-Based Review & Study Guide",
        "authors": ["Chandra RA", "Ord CB", "Rana S", "Hansen EK"],
        "edition": "2021 Edition",
        "category": "Radiation Oncology",
        "tags": ["radiation_oncology", "board_review", "clinical_vignettes", "toxicity_management"],
        "relative_path": "VCR/Radiation Oncology Study Guide (2021, Springer) - libgen.li.pdf",
        "summary": "Socratic case reviews and consensus protocols for organ sparing, dose specification, and definitive radiotherapy technique."
    },
    # MEDICAL ONCOLOGY & CHEMOTHERAPY
    {
        "id": "DEVITA-12TH",
        "title": "DeVita, Hellman, and Rosenberg's Cancer: Principles and Practice of Oncology",
        "authors": ["DeVita VT Jr", "Lawrence TS", "Rosenberg SA"],
        "edition": "12th Edition (2023)",
        "category": "Medical Oncology",
        "tags": ["medical_oncology", "cancer_biology", "systemic_therapy", "head_neck", "concurrent_chemoradiation", "cisplatin"],
        "relative_path": "Clinical Oncology/DeVita, Hellman and Rosenberg's Cancer_ Principles and Practice of Oncology, 12th Edition (HQ PDF) - Vi.pdf",
        "summary": "The gold standard oncology reference for biological principles, clinical oncology management, chemotherapy mechanisms, radiosensitization schedules, and immunotherapies."
    },
    {
        "id": "ABELOFF-6TH",
        "title": "Abeloff's Clinical Oncology",
        "authors": ["Niederhuber JE", "Armitage JO", "Doroshow JH", "Kastan MB", "Tepper JE"],
        "edition": "6th Edition (2020)",
        "category": "Medical Oncology",
        "tags": ["clinical_oncology", "multidisciplinary_care", "systemic_therapy", "targeted_therapy", "toxicities"],
        "relative_path": "Clinical Oncology/(Egitim Tanrisi) John E. Niederhuber, James O. Armitage, Michael B. Kastan, James H. Doroshow, Joel E. Tepper - Abeloff's Clinical Oncology (2020).pdf",
        "summary": "Comprehensive textbook synthesizing molecular biology, clinical pharmacology, toxicities, and integrated systemic plus locoregional modalities."
    },
    {
        "id": "TATA-MEMORIAL-ONC-2024",
        "title": "Tata Memorial Centre Textbook of Oncology",
        "authors": ["Badwe RA", "Gupta S", "Shrikhande SV", "Laskar S"],
        "edition": "2024 Edition",
        "category": "Oncology",
        "tags": ["oncology", "evidence_based_management", "resource_stratified", "head_neck_cancer", "multidisciplinary"],
        "relative_path": "VCR/Rajendra A. Badwe, Sudeep Gupta, Shailesh V. Shrikhande, Siddhar - Tata Memorial Centre Textbook of Oncology (2024, Springer) - libgen.li.pdf",
        "summary": "Authoritative oncology textbook with pragmatic, evidence-based management strategies, clinical decision trees, and organ preservation algorithms tailored to varied clinical scenarios."
    },
    {
        "id": "BETHESDA-CLIN-ONC-2018",
        "title": "The Bethesda Handbook of Clinical Oncology",
        "authors": ["Abraham J", "Gulley JL"],
        "edition": "5th Edition (2018)",
        "category": "Medical Oncology",
        "tags": ["chemotherapy", "regimens", "supportive_care", "antiemetics", "hydration_protocols"],
        "relative_path": "Chemotherapy/The Bethesda Handbook of Clinical Oncology (2018).pdf",
        "summary": "Clinical handbook of systemic chemotherapy regimens, supportive care guidelines, dosing adjustments for organ dysfunction, and acute toxicity protocols."
    },
    {
        "id": "DEVITA-CHEMO-MANUAL-2024",
        "title": "Physicians' Cancer Chemotherapy Drug Manual",
        "authors": ["Chu E", "DeVita VT Jr"],
        "edition": "2024 Edition",
        "category": "Chemotherapy Pharmacology",
        "tags": ["chemotherapy", "pharmacology", "cisplatin", "carboplatin", "cetuximab", "dosing", "emetogenicity"],
        "relative_path": "Chemotherapy/Physicians Cancer Chemotherapy Drug Manual 2024.pdf",
        "summary": "Definitive drug manual for antineoplastic agents, including cisplatin dosing (100 mg/m2 q3w vs 40 mg/m2 weekly), creatinine clearance thresholds, and pre/post hydration requirements."
    },
    # SURGERY & GYNAECOLOGY
    {
        "id": "SABISTON-SURGERY-21ST",
        "title": "Sabiston Textbook of Surgery: The Biological Basis of Modern Surgical Practice",
        "authors": ["Townsend CM", "Beauchamp RD", "Evers BM", "Mattox KL"],
        "edition": "21st Edition (2021)",
        "category": "Surgical Oncology",
        "tags": ["surgery", "surgical_oncology", "head_neck_surgery", "margins", "neck_dissection", "transoral_robotic_surgery"],
        "relative_path": "VCR/Courtney M. Townsend Jr., R. Daniel Beauchamp, B. Mark Evers, Ke - Sabiston Textbook of Surgery_ The Biological Basis of Modern Surgical Practice (2021, Elsevier) - libgen.li.pdf",
        "summary": "Foremost surgical textbook providing operative standards, surgical margin assessments, neck dissection indications, and surgical candidacy evaluation."
    },
    {
        "id": "DAS-CLINICAL-SURGERY",
        "title": "A Manual On Clinical Surgery",
        "authors": ["Das S"],
        "edition": "13th Edition (2018)",
        "category": "Surgical Examination",
        "tags": ["surgery", "physical_examination", "cervical_lymphadenopathy", "oral_cavity", "head_neck_exam"],
        "relative_path": "Examination/S. Das - A Manual On Clinical Surgery (2018, S Das Publication) - libgen.li.pdf",
        "summary": "Seminal physical examination manual for evaluating primary tumor extension, fixation, trismus, and discrete versus matted cervical lymph node stations."
    },
    # PATHOLOGY & STAGING
    {
        "id": "AJCC-STAGING-MANUAL-8TH",
        "title": "AJCC Cancer Staging Manual",
        "authors": ["Amin MB", "Edge SB", "Greene FL", "Schilsky RL", "Gress DM"],
        "edition": "8th Edition (2018)",
        "category": "Pathology & Staging",
        "tags": ["tnm_staging", "ajcc", "uicc", "hpv_p16", "oropharynx", "cervical_nodes", "stage_grouping"],
        "relative_path": "AJCC/Frederick L Greene_ Stephen Edge_ Richard L Schilsky_ Lauri E Ga - Ajcc Cancer Staging Manual (2018, Springer) - libgen.li.pdf",
        "summary": "Official global staging classification standard defining clinical and pathological T, N, M staging categories and separate prognostic staging for HPV/p16-positive vs negative oropharyngeal carcinoma."
    },
    {
        "id": "ROBBINS-PATHOLOGY-10TH",
        "title": "Robbins & Cotran Pathologic Basis of Disease",
        "authors": ["Kumar V", "Abbas AK", "Aster JC"],
        "edition": "10th Edition (2020)",
        "category": "Pathology",
        "tags": ["pathology", "histopathology", "squamous_cell_carcinoma", "p16_ihc", "hpv", "perineural_invasion", "lymphovascular_space_invasion"],
        "relative_path": "Pathology/[Robbins Pathology] Vinay Kumar MBBS MD FRCPath, Abul K. Abbas MBBS, Jon C. Aster MD - Robbins & Cotran Pathologic Basis of Disease (Robbins Pathology) (2020, Elsevier) - libgen.li.pdf",
        "summary": "The definitive reference for molecular and cellular basis of disease, histological grading of squamous cell carcinoma, p16 overexpression as surrogate for HPV infection, and invasive margins."
    },
    # MEDICAL PHYSICS & TREATMENT PLANNING
    {
        "id": "KHAN-PHYSICS-6TH",
        "title": "Khan's The Physics of Radiation Therapy",
        "authors": ["Gibbons JP", "Khan FM"],
        "edition": "6th Edition (2020)",
        "category": "Medical Physics",
        "tags": ["medical_physics", "beam_teletherapy", "imrt", "vmat", "linac", "dosimetry", "beam_quality"],
        "relative_path": "Physics/Khan's The Physics of Radiation Therapy.pdf",
        "summary": "Foundational textbook on radiation physics, photon and electron interactions, linear accelerator beam characteristics, IMRT/VMAT inverse planning, and monitor unit verification."
    },
    {
        "id": "KHAN-TREATMENT-PLANNING",
        "title": "Khan's Treatment Planning in Radiation Oncology",
        "authors": ["Khan FM", "Gerbi BJ"],
        "edition": "4th Edition",
        "category": "Treatment Planning",
        "tags": ["treatment_planning", "dosimetry", "imrt", "vmat", "dose_volume_histogram", "isodose_distributions"],
        "relative_path": "Planning/Khan's Treatment Planning in Radiation Oncology.pdf",
        "summary": "Standard reference for 3D-CRT and IMRT/VMAT treatment planning, beam angles, optimization constraints, dose-volume histograms, and organ-at-risk prioritization."
    },
    {
        "id": "DOBBS-PLANNING-4TH",
        "title": "Practical Radiotherapy Planning",
        "authors": ["Dobbs J", "Barrett A", "Ash D"],
        "edition": "4th Edition (2009)",
        "category": "Treatment Planning",
        "tags": ["radiotherapy_planning", "field_borders", "target_delineation", "simulation_technique", "immobilization"],
        "relative_path": "Planning/Dobbs - Practical Radiotherapy Planning, Fourth Edition (2009).pdf",
        "summary": "Essential guide to patient immobilization, thermoplastic mask fabrication, CT simulation parameters, field shaping, and target volume delineation for clinical radiotherapy."
    },
    {
        "id": "NANCY-LEE-TARGET-VOLUMES-2022",
        "title": "Target Volume Delineation and Conformal Radiotherapy: Head and Neck",
        "authors": ["Lee NY", "Lu JJ", "Puckett LL"],
        "edition": "2022 Edition",
        "category": "Contouring & Target Delineation",
        "tags": ["contouring", "target_delineation", "head_neck", "ctv_high_risk", "ctv_elective", "oropharynx", "nodal_levels"],
        "relative_path": "Planning/Nancy Lee 2022 new.pdf",
        "summary": "Standard atlas and guidelines for defining high-risk and elective clinical target volumes (CTV1, CTV2) and organ-at-risk contouring in head and neck carcinomas."
    },
    {
        "id": "CONTOURING-GUIDELINES-ALL-SITES",
        "title": "Contouring Guidelines For All Sites: Anatomic Atlas",
        "authors": ["Radiation Oncology Quality Assurance Committee"],
        "edition": "Comprehensive Reference",
        "category": "Contouring Guidelines",
        "tags": ["contouring", "anatomic_atlas", "head_neck_levels", "normal_tissue_constraints", "ctv_margins"],
        "relative_path": "Contouring guidelines/CONTOURING GUIDELINES FOR ALL SITES BOOK.pdf",
        "summary": "Visual contouring manual with step-by-step CT axial cuts demonstrating cranial nerve exit foramina, cervical lymph node stations (Levels I-VI), and critical serial/parallel organs."
    },
    # RADIOBIOLOGY
    {
        "id": "HALL-RADIOBIOLOGY-8TH",
        "title": "Radiobiology for the Radiologist",
        "authors": ["Hall EJ", "Giaccia AJ"],
        "edition": "8th Edition (2018)",
        "category": "Radiobiology",
        "tags": ["radiobiology", "4_rs_of_radiobiology", "linear_quadratic_model", "alpha_beta_ratio", "oxygen_effect", "fractionation"],
        "relative_path": "RadioBiology/Radiobiology for the Radiologist.pdf",
        "summary": "Foundational radiobiology text covering the linear-quadratic formulation, BED calculations, alpha/beta ratios for tumors vs late reacting normal tissues, and repopulation kinetics."
    },
    {
        "id": "KOGEL-CLINICAL-RADIOBIOLOGY-2019",
        "title": "Basic Clinical Radiobiology",
        "authors": ["Joiner MC", "van der Kogel AJ"],
        "edition": "5th Edition (2019)",
        "category": "Radiobiology",
        "tags": ["radiobiology", "bed_eqd2", "altered_fractionation", "hypofractionation", "normal_tissue_response"],
        "relative_path": "RadioBiology/Kogel - Basic clinical radiobiology (2019).pdf",
        "summary": "Clinical radiobiology manual for deriving EQD2 schedules, calculating biologically effective dose during treatment interruptions, and comparing conventional versus accelerated fractionation."
    },
    # NORMAL TISSUE TOLERANCES (QUANTEC & PENTEC)
    {
        "id": "QUANTEC-COMPREHENSIVE-2010",
        "title": "QUANTEC: Quantitative Analyses of Normal Tissue Effects in the Clinic",
        "authors": ["Marks LB", "Yorke ED", "Jackson A", "Ten Haken RK", "Constine LS", "Eisbruch A"],
        "edition": "Red Journal Special Issue / Compendium",
        "category": "Normal Tissue Tolerances",
        "tags": ["quantec", "dose_constraints", "parotid_gland", "spinal_cord", "larynx_pharynx", "brainstem", "mandible_orn"],
        "relative_path": "QUANTEC/Quantitative-Analyses-of-Normal-Tissue-Effects-in-.pdf",
        "summary": "The definitive clinical compendium for organ-at-risk dose-volume constraints: mean parotid dose < 26 Gy, spinal cord max < 45-50 Gy, constrictor muscles mean < 50 Gy to minimize severe dysphagia."
    },
    {
        "id": "PENTEC-PEDIATRIC-2022",
        "title": "PENTEC: Pediatric Normal Tissue Effects in the Clinic",
        "authors": ["Constine LS", "Ronckers CM", "Hua CH", "Olch A"],
        "edition": "Compendium Collection",
        "category": "Normal Tissue Tolerances",
        "tags": ["pentec", "pediatric_radiation", "late_effects", "growth_impairment", "neurocognitive", "second_malignancies"],
        "relative_path": "PENTEC/A-User's-Guide-and-Summary-of-Pediatric-Normal-Tis.pdf",
        "summary": "Landmark pediatric radiation oncology consensus detailing age-specific dose thresholds, organ maturation factors, endocrine disruption, and secondary cancer risks."
    },
    # TOXICITIES & SUPPORTIVE CARE
    {
        "id": "OZYIGIT-TOXICITIES-RADONC-2020",
        "title": "Prevention and Management of Acute and Late Toxicities in Radiation Oncology",
        "authors": ["Ozyigit G", "Selek U"],
        "edition": "Springer (2020)",
        "category": "Toxicity & Supportive Care",
        "tags": ["toxicity", "radiation_dermatitis", "mucositis", "osteoradionecrosis", "xerostomia", "supportive_care"],
        "relative_path": "Toxicity/Gokhan Ozyigit, Ugur Selek - Prevention and Management of Acute and Late Toxicities in Radiation Oncology_ Management of Toxicities in Radiation Oncology (2020, Springer) [10.1007_978-3-030-37798-4] - libgen.li.pdf",
        "summary": "Dedicated clinical manual for diagnosing, preventing, and managing acute and late radiation side effects, including mouthwashes, enteral tube feeding indications, and hyperbaric oxygen."
    },
    {
        "id": "CTCAE-V5-CRITERIA",
        "title": "Common Terminology Criteria for Adverse Events (CTCAE v5.0)",
        "authors": ["National Cancer Institute (NCI)"],
        "edition": "Version 5.0",
        "category": "Toxicity Grading",
        "tags": ["ctcae", "toxicity_grading", "mucositis", "dysphagia", "neutropenia", "adverse_events"],
        "relative_path": "Toxicity/CTCAE_v5_Quick_Reference_8.5x11.pdf",
        "summary": "The universal oncology grading system for classifying acute and chronic treatment toxicities from Grade 1 (mild) to Grade 5 (death)."
    },
    # ANATOMY & IMAGING
    {
        "id": "GRAYS-ANATOMY-41ST",
        "title": "Gray's Anatomy: The Anatomical Basis of Clinical Practice",
        "authors": ["Standring S"],
        "edition": "41st Edition (2016)",
        "category": "Human Anatomy",
        "tags": ["anatomy", "pharynx", "oropharynx", "cranial_nerves", "fascial_spaces", "cervical_lymphatics"],
        "relative_path": "Anatomy/Gray's Anatomy_ The Anatomical Basis of Clinical Practice (c2016).pdf",
        "summary": "The world reference for human surgical and cross-sectional anatomy, describing mucosal spaces, lymphatic drainage pathways, and muscular walls of the oropharynx."
    },
    {
        "id": "HUSBAND-REZNEK-IMAGING-4TH",
        "title": "Husband & Reznek's Imaging in Oncology",
        "authors": ["Sahdev A", "Vinnicombe SJ"],
        "edition": "4th Edition (2020)",
        "category": "Diagnostic Imaging",
        "tags": ["imaging", "ct_mri_pet", "head_neck_imaging", "nodal_extracapsular_spread", "perineural_spread", "recist"],
        "relative_path": "Anju Sahdev, Sarah J. Vinnicombe - Husband & Reznek's Imaging in Oncology (2020, CRC Press) - libgen.li.pdf",
        "summary": "Premier oncologic radiology treatise on multi-modality CT, MRI, and PET/CT staging, differential diagnosis of lymphadenopathy, and treatment response evaluation."
    },
    {
        "id": "LANDMARK-TRIALS-ONC-2019",
        "title": "Landmark Trials in Oncology",
        "authors": ["Yajnik S"],
        "edition": "Springer (2019)",
        "category": "Clinical Trials Reference",
        "tags": ["landmark_trials", "randomized_trials", "head_neck", "rtog_9111", "rtog_0129", "rtog_0522", "mach_nc"],
        "relative_path": "TRIALS/Yajnik. - Landmark Trials in Oncology-Springer (2019).pdf",
        "summary": "Curated collection of pivotal randomized Phase III trials in oncology, analyzing evidence bases for concurrent platinum chemoradiotherapy, altered fractionation, and organ preservation."
    }
]

out_path = "backend/app/evidence_catalogues/textbooks_radiobiology_catalogue.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2)

print(f"Successfully wrote {len(entries)} textbooks to {out_path}")
