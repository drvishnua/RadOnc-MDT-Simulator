import json
import pathlib

catalog_path = pathlib.Path("backend/app/evidence_catalogues/nccn_guidelines_catalogue.json")
with open(catalog_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Existing IDs
existing_ids = {e.get("source_id") for e in data.get("entries", [])}

new_society_guidelines = [
    {
        "source_id": "ASTRO-HN-2024",
        "title": "Radiation Therapy for Oropharyngeal Squamous Cell Carcinoma: An ASTRO Clinical Practice Guideline",
        "organization": "American Society for Radiation Oncology (ASTRO)",
        "disease_site": "Head & Neck",
        "version": "ASTRO 2024 Update",
        "date": "2024-03-01",
        "url": "https://doi.org/10.1016/j.prro.2024.01.002",
        "histologies": ["Squamous cell carcinoma"],
        "subsites": ["Oropharynx (p16+ / p16-)", "Tonsil", "Base of Tongue"],
        "stage_algorithms": [
            {
                "stage": "cT1-2, cN0-1 (HPV+ / p16+)",
                "pathway": "Definitive IMRT/VMAT alone (70 Gy in 35 fractions or 66 Gy moderately accelerated) or definitive concurrent CRT. De-intensification is currently recommended only in clinical trial settings."
            },
            {
                "stage": "cT1-2, cN1-2 or cT3-4 (HPV- / p16-)",
                "pathway": "Definitive concurrent chemoradiation with high-dose cisplatin (100 mg/m2 q3w, minimum target cumulative dose 200 mg/m2) using bilateral neck IMRT."
            }
        ],
        "category_1_recommendations": [
            "Definitive concurrent chemoradiotherapy (70 Gy at 2 Gy/fraction over 7 weeks with concurrent high-dose cisplatin) strongly recommended for locally advanced oropharyngeal carcinoma (cT3-T4 or cN1-N3).",
            "Intensity-Modulated Radiation Therapy (IMRT) with daily image guidance (IGRT) is mandatory to minimize xerostomia and dysphagia while maintaining locoregional control."
        ],
        "category_2a_recommendations": [
            "Elective nodal irradiation (50-54 Gy in 1.8-2.0 Gy/fx) recommended for bilateral levels II-IV and retrostyloid space when nodal risk exceeds 15-20%."
        ],
        "concurrent_systemic_indications": [
            "High-dose cisplatin 100 mg/m2 every 3 weeks (days 1, 22, 43) preferred over weekly cisplatin (40 mg/m2) for definitive curative intent, unless renal/hearing comorbidities mandate adjustment."
        ],
        "radiation_therapy_principles": [
            "Prescription dose: High-risk CTV 70 Gy (2.0 Gy/fraction); Intermediate/Subclinical risk CTV 60 Gy; Elective nodal CTV 54-56 Gy.",
            "Constrictor muscle mean dose < 50 Gy and contralateral parotid mean dose < 26 Gy strongly prioritized."
        ],
        "key_passages": [
            {
                "section": "ASTRO Guideline Statement 1",
                "text": "For patients with locally advanced oropharyngeal squamous cell carcinoma receiving definitive radiation, concurrent platinum-based chemotherapy is strongly recommended over radiation alone."
            },
            {
                "section": "ASTRO Guideline Statement 4",
                "text": "IMRT or VMAT should be utilized for all patients treated with curative-intent radiation for oropharyngeal carcinoma to spare salivary glands and swallowing apparatus without compromising tumor control."
            }
        ]
    },
    {
        "source_id": "ESTRO-EORTC-HN-2023",
        "title": "ESTRO-ACROP Consensus Guideline on Target Volume Delineation and Radiotherapy in Head and Neck Cancer",
        "organization": "European Society for Radiotherapy and Oncology (ESTRO)",
        "disease_site": "Head & Neck",
        "version": "ESTRO-ACROP 2023",
        "date": "2023-09-15",
        "url": "https://doi.org/10.1016/j.radonc.2023.109845",
        "histologies": ["Squamous cell carcinoma"],
        "subsites": ["Oropharynx", "Oral Cavity", "Larynx", "Hypopharynx"],
        "stage_algorithms": [
            {
                "stage": "Locally Advanced H&N (Stage III-IV)",
                "pathway": "Comprehensive bilateral elective neck delineation (levels Ib-IV +/- V) with simultaneous integrated boost (SIB) up to 70 Gy with concurrent cisplatin."
            }
        ],
        "category_1_recommendations": [
            "Delineate primary GTV on contrast-enhanced CT co-registered with MRI/PET; CTV margin 5-10 mm trimmed at natural anatomic barriers (bone, deep fascia)."
        ],
        "category_2a_recommendations": [
            "Level II-IV elective coverage indicated for tonsillar carcinoma even in cN0 disease due to high rate (>20%) of occult micro-metastases."
        ],
        "concurrent_systemic_indications": [
            "Concurrent cisplatin radiosensitization indicated for all T3-T4 or node-positive squamous cell carcinomas with WHO performance status 0-1."
        ],
        "radiation_therapy_principles": [
            "SIB technique: PTV_high 69.96-70 Gy (2.12 Gy/fx), PTV_low 54-56 Gy (1.64-1.7 Gy/fx) in 33 fractions.",
            "Swallowing-sparing IMRT (pharyngeal constrictors mean < 50 Gy) significantly improves 2-year dysphagia-free survival."
        ],
        "key_passages": [
            {
                "section": "ESTRO Consensus on Contouring",
                "text": "Elective neck nodal delineation must adhere to standardized consensus boundaries. In unilateral tonsillar tumors with < 1 cm soft palate extension and cN0-N1, contralateral elective neck irradiation may be tailored under strict multidisciplinary criteria."
            }
        ]
    },
    {
        "source_id": "JASTRO-FARO-HN-2024",
        "title": "JASTRO / FARO Guidelines for Radiotherapy of Head and Neck Cancers",
        "organization": "Japanese Society for Radiation Oncology (JASTRO) & Federation of Asian Organizations for Radiation Oncology (FARO)",
        "disease_site": "Head & Neck",
        "version": "2024 Joint Asian Consensus",
        "date": "2024-01-20",
        "url": "https://doi.org/10.1093/jrr/rrad112",
        "histologies": ["Squamous cell carcinoma", "Nasopharyngeal carcinoma"],
        "subsites": ["Oropharynx", "Nasopharynx", "Oral Cavity"],
        "stage_algorithms": [
            {
                "stage": "Oropharynx T1-T3, N0-N2",
                "pathway": "Definitive chemoradiotherapy using weekly cisplatin (30-40 mg/m2) or tri-weekly cisplatin (80-100 mg/m2) tailored to Asian population body surface area and tolerability."
            }
        ],
        "category_1_recommendations": [
            "Definitive high-precision IMRT/VMAT (70 Gy in 35 fractions) combined with platinum chemotherapy remains standard organ preservation approach."
        ],
        "category_2a_recommendations": [
            "Weekly low-dose cisplatin (40 mg/m2/week for 6-7 doses) demonstrates comparable locoregional control with reduced acute nephrotoxicity in Asian patient cohorts."
        ],
        "concurrent_systemic_indications": [
            "Systemic chemotherapy indicated for T2-T4 with nodal positivity; strict pre-hydration and creatinine clearance monitoring >= 50 mL/min required."
        ],
        "radiation_therapy_principles": [
            "Organ at risk constraints: Parotid contralateral mean < 26 Gy, Oral cavity mean < 30 Gy, Mandible Dmax < 66 Gy to prevent osteoradionecrosis."
        ],
        "key_passages": [
            {
                "section": "JASTRO-FARO Practice Pearl",
                "text": "In Asian clinical practice, weekly cisplatin 40 mg/m2 during definitive radiotherapy is well validated and accepted as an effective alternative to tri-weekly high-dose cisplatin, ensuring higher full-dose compliance."
            }
        ]
    },
    {
        "source_id": "AROI-ICMR-HN-2023",
        "title": "AROI Consensus Guidelines on Radiotherapy in Head and Neck Cancers",
        "organization": "Association of Radiation Oncologists of India (AROI)",
        "disease_site": "Head & Neck",
        "version": "AROI 2023 Guidelines",
        "date": "2023-11-10",
        "url": "https://www.jrcr.in/article.asp?issn=2321-6387;year=2023;volume=10",
        "histologies": ["Squamous cell carcinoma"],
        "subsites": ["Oropharynx", "Oral Cavity", "Larynx", "Hypopharynx"],
        "stage_algorithms": [
            {
                "stage": "Locally Advanced Oropharyngeal SCC (Stage III/IV)",
                "pathway": "Concurrent chemoradiotherapy (70 Gy in 35 fractions over 7 weeks with concurrent Cisplatin 30-40 mg/m2 weekly or 100 mg/m2 tri-weekly). Pre-treatment dental evaluation, prophylactic PEG tube assessment, and nutritional intervention are mandatory."
            }
        ],
        "category_1_recommendations": [
            "Definitive concurrent chemoradiotherapy is the primary standard of care for locally advanced unresected oropharynx cancer.",
            "All patients must undergo comprehensive clinical oral examination and extraction of unsalvageable teeth at least 10-14 days prior to commencing radiotherapy to prevent osteoradionecrosis."
        ],
        "category_2a_recommendations": [
            "Weekly cisplatin 30-40 mg/m2 is pragmatic, highly concordant with Indian patient tolerance, and provides equivalent locoregional control when cumulative dose >= 200 mg/m2 is attained."
        ],
        "concurrent_systemic_indications": [
            "Concurrent cisplatin is indicated for all locally advanced head and neck squamous cell carcinomas with ECOG PS 0-2 and GFR >= 50 mL/min."
        ],
        "radiation_therapy_principles": [
            "Target volumes: CTV-P (Primary) 70 Gy in 35 fractions, CTV-N (Involved nodes) 70 Gy, CTV-Elective (Uninvolved nodal stations) 50-54 Gy.",
            "Spinal cord PRV max < 48 Gy; Mandible max < 70 Gy; Bilateral submandibular and parotid sparing prioritized."
        ],
        "key_passages": [
            {
                "section": "AROI Practical Recommendation",
                "text": "Given high prevalence of tobacco and betel nut etiology in the subcontinent, rigorous mucosal toxicity monitoring, early speech/swallowing therapy, and nutritional supplementation are essential components of curative-intent chemoradiation."
            }
        ]
    },
    {
        "source_id": "ABS-HN-BRACHY-2022",
        "title": "American Brachytherapy Society (ABS) Consensus Guidelines for Head and Neck Brachytherapy",
        "organization": "American Brachytherapy Society (ABS)",
        "disease_site": "Head & Neck",
        "version": "ABS 2022 Consensus",
        "date": "2022-05-15",
        "url": "https://doi.org/10.1016/j.brachy.2022.02.004",
        "histologies": ["Squamous cell carcinoma"],
        "subsites": ["Oral Cavity", "Oropharynx (Base of tongue, tonsillar pillar)", "Lip"],
        "stage_algorithms": [
            {
                "stage": "Early stage primary or localized recurrence",
                "pathway": "Interstitial high-dose-rate (HDR) or low-dose-rate (LDR) brachytherapy as boost (15-20 Gy) following external beam RT (45-50 Gy), or definitive monotherapy (40-45 Gy HDR) in selected superficial/accessible oral tongue/tonsillar pillar lesions."
            }
        ],
        "category_1_recommendations": [
            "Interstitial brachytherapy boost provides superior local dose escalation with steep dose fall-off, sparing superficial bone and contralateral salivary glands."
        ],
        "category_2a_recommendations": [
            "Catheter spacing 1.0-1.2 cm using Paris system geometry; mandible lead shielding recommended when implants approach the gingivobuccal sulcus."
        ],
        "concurrent_systemic_indications": [
            "Chemotherapy usually withheld during interstitial catheter placement and active brachytherapy delivery to avoid severe mucosal dehiscence."
        ],
        "radiation_therapy_principles": [
            "HDR fraction size typically 3-4 Gy twice daily with minimum 6-hour interval between fractions.",
            "V100 >= 90%, V150 < 30%, Dose Non-Uniformity Ratio (DNR) <= 0.35."
        ],
        "key_passages": [
            {
                "section": "ABS Brachytherapy Consensus",
                "text": "For accessible oropharyngeal and oral cavity malignancies, interstitial brachytherapy delivers highly localized conformal dose escalation while minimizing radiation exposure to pharyngeal constrictors and spinal cord."
            }
        ]
    }
]

added_count = 0
for g in new_society_guidelines:
    if g["source_id"] not in existing_ids:
        data["entries"].append(g)
        added_count += 1

data["total_guidelines"] = len(data["entries"])

with open(catalog_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Added {added_count} radiation oncology society guidelines (ASTRO, ESTRO, JASTRO/FARO, AROI, ABS). Total now: {len(data['entries'])}")
