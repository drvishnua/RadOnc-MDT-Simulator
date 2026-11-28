# Legal, Regulatory, Product-Safety and Data-Protection Risk Register

**Status:** Internal product-risk register; not legal advice, a compliance certification or an assurance that litigation cannot occur.  
**Jurisdiction reviewed:** India, as the initial development/distribution context.  
**Review date:** 12 November 2026.  
**Product boundary:** Local educational Radiation Oncology MDT simulator using fictional training cases only.  
**Release position:** Not approved for real-patient use, hospital deployment, clinical decision support or commercial clinical workflow integration.

## 1. Important assurance boundary

No software, disclaimer, contract or engineering process can guarantee that nobody will sue, that a court will accept a contractual limitation, or that no liability will arise. A disclaimer is only one control. The intended use, actual functionality, marketing, user instructions, data handling, defect controls, incident response and conduct after a complaint all matter.

The purpose of this register is to identify foreseeable exposure, assign controls and prevent unsupported claims. Applicability of each law depends on the actual developer, distributor, operator, customer, data flows and deployment model. An Indian lawyer with medical-device, privacy and product-liability experience must review the intended-use statement and release documents before any external distribution or institutional use.

## 2. Intended use must remain narrow and consistent

The product's intended purpose is **medical education and training using fictional, non-identifiable cases**. It is not intended to:

- diagnose, screen, triage, monitor or treat a real patient;
- recommend, select, rank or approve patient-specific treatment;
- prescribe medicines, doses, fractionation, contours, plans or treatment instructions;
- replace a qualified clinician, radiotherapy planning system or formal hospital MDT;
- ingest or connect to real hospital records, HIS, EHR, RIS, PACS, treatment-planning systems or patient identifiers;
- register real patients or issue hospital medical-record numbers;
- validate guideline concordance or provide externally verified evidence unless a later, separately governed feature actually retrieves and verifies sources.

This boundary must appear consistently in the application, installer, onboarding, README, website, presentations, training material, release notes, support responses and any advertising. Do not use claims such as “clinically validated”, “guideline compliant”, “safe treatment recommendation”, “hospital-ready”, “autonomous MDT” or “medical-grade” unless the relevant regulatory pathway and independent evidence actually support them.

Any proposed feature involving real patient data, clinical workflow, decision support, diagnosis, treatment selection, dose/planning or hospital integration triggers a mandatory product-intended-use and regulatory review before implementation or promotion.

## 3. Indian legal and regulatory issues to review

### 3.1 Medical-device software — CDSCO / Medical Devices Rules, 2017

The CDSCO *Guidance Document on Medical Device Software under MDR-2017*, Doc. No. CDSCO/MD/GD/MDSW/01/2026, dated 21 July 2026, explains that software intended for medical purposes may fall within medical-device software scope. Section 5.2 gives examples of software solely intended for medical teaching/training/educational purposes that are not covered where the software does not meet the medical-device definition described in Section 4.9. The guidance also emphasises the importance of a clear intended-use statement and product labelling/claims.

**Project control:** retain the fictional education-only intended use and prohibit conversion into real-patient decision support without a fresh CDSCO classification and regulatory assessment. A product label alone is not decisive if actual features, marketing or deployment indicate a medical purpose. Counsel/regulatory specialist must confirm the applicable position before distribution.

Official source: [CDSCO Guidance Document on Medical Device Software under MDR-2017 (2026)](https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf).

### 3.2 Personal data and health information — DPDP Act and transitional regime

The Digital Personal Data Protection Act, 2023 has a phased commencement under Gazette Notification G.S.R. 843(E), dated 13 November 2025:

- certain institutional/administrative provisions commenced on publication;
- Section 6(9) and Section 27(1)(d) are scheduled to commence one year after publication (13 November 2026);
- the main processing, notice, consent, data-principal rights, fiduciary-obligation and related provisions identified in clause (c) are scheduled to commence eighteen months after publication (13 May 2027).

The Digital Personal Data Protection Rules, 2025 also have a phased commencement. Do not describe the full DPDP regime as already operative on 12 November 2026, and do not assume that the future commencement dates remove the need to prepare now. Obtain counsel's view on the exact provisions and Rules applicable to the developer, installer distributor, hospital/educational institution and end user at the time of each release.

Until the transition is complete, assess the continuing applicability of the Information Technology Act, 2000 and the SPDI Rules, 2011. The SPDI Rules identify physical, physiological and mental-health information and medical records/history as sensitive personal data and information, and include privacy-policy, purpose/consent, retention and security-practice requirements for covered body corporates. The staged commencement of DPDP Act Section 44(2), which omits IT Act Section 43A, is relevant to the transition; legal counsel must confirm the interaction and timing rather than assuming the older regime has already disappeared.

**Project control:** no real patient data. Minimise collection, explain local storage, document purposes and retention, provide deletion/export/complaint routes where legally required, protect the database and logs, document all outbound data flows and obtain the appropriate institutional permissions before any controlled pilot. If a future release allows personal/health data, complete a data-protection impact assessment and lawful-basis/notice/consent review before enabling it.

Official sources:
- [DPDP Act commencement notification, G.S.R. 843(E), 13 November 2025](https://egazette.gov.in/WriteReadData/2025/267647.pdf).
- [Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_45_76_00001_200021_1517807324077&filename=GSR313E_10511%281%29_0.pdf&type=rule).

### 3.3 Consumer Protection Act, 2019 — product/service liability

Sections 82–87 of the Consumer Protection Act, 2019 address product-liability claims. Section 83 provides for an action against a product manufacturer, product service provider or product seller for harm caused by a defective product. Section 84 lists manufacturer-liability grounds that include manufacturing defect, defective design, deviation from specifications, failure to conform to express warranty, and inadequate instructions or warnings.

Whether and how these provisions apply to this software, its distribution model, the developer, a reseller, a service provider or an institutional deployment is fact-specific and requires Indian counsel. Do not assume that an educational label, open-source distribution or a disclaimer automatically excludes statutory duties or product/service liability.

**Project control:** maintain a defect-reporting and response process; preserve release artefacts and test evidence; issue accurate installation/use instructions; warn clearly about model limitations and unsupported use; correct critical defects; retain version history and notices; and avoid express warranties or marketing claims that cannot be substantiated.

Official source: [Consumer Affairs — Consumer Protection Act, 2019](https://consumeraffairs.gov.in/public/upload/files/CP%20Act%202019_1732700731.pdf).

### 3.4 CERT-In cyber incident directions

CERT-In Directions No. 20(3)/2022, dated 28 April 2022, include cyber-incident reporting timelines (including six-hour reporting for covered entities) and secure retention of ICT system logs for a rolling 180 days in India for the specified classes of entities. Applicability depends on whether the relevant developer/operator is within the covered categories and on the incident type. Do not assume every individual end user of a local desktop program has identical obligations.

**Project control:** designate an incident contact, maintain a triage/escalation process, retain required logs where applicable, record incident decisions and have a counsel-reviewed notification procedure before commercial/institutional operation.

Official source: [CERT-In Directions under Section 70B, 28 April 2022](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf).

## 4. Current implementation risks that must not be hidden

| Risk | Current evidence / limitation | Required control before external or institutional release |
|---|---|---|
| Accidental real-patient/identifiable data entry | UI repeatedly instructs “fictional training records only”, but free-text fields cannot reliably classify or guarantee detection of PHI. | Synthetic-case attestation, strong just-in-time warnings, misuse controls, documented data-handling policy and privacy review. Do not claim an automated detector can guarantee safe de-identification. |
| Local database confidentiality | SQLite data is stored in the user's local data directory. Current review has not established database encryption at rest. | Security review of encryption, key management, Windows ACLs, retention, backups and recovery. |
| Local API access | Packaged backend binds to 127.0.0.1 and CORS origins are restricted, but there is no application authentication. CORS is not an access-control boundary against other local processes. | Threat-model local browser and process access; test origin/CSRF/DNS-rebinding cases; implement a reviewed local request-authentication or equivalent control before any shared/network deployment. |
| Model-generated clinical error | Live R2/R3 tests have found provenance and representation failures; clinical accuracy is not established and evidence retrieval is not connected. | Keep synthetic-only boundary; retain fail-closed provenance; human-reviewed rubric and qualified clinical review; no clinical reliance. |
| Audit immutability | Snapshot hashes and run/round records support traceability, but a local user with filesystem access can modify or delete the SQLite database. Hashes are not a tamper-proof audit service. | Describe hashes accurately; consider signed/exported audit manifests and backup controls if audit-grade records are later required. |
| Data deletion and retention | Patient deletion cascades through database relationships, but secure erasure from SSDs, SQLite journals, OS backups or copied exports is not guaranteed. | Publish realistic deletion/retention explanation; test backup and restore; do not promise forensic erasure. |
| Network/model endpoint | Default inference is local Ollama; configuration/environment overrides and future connectors require review to ensure case text is not sent to third parties. | Pin/validate local endpoint in packaged mode; disclose every external transfer; no cloud inference without privacy, security and contractual approval. |
| Supply chain and publisher authenticity | Ollama archive SHA-256 is pinned; dependency audits exist. The installer is not yet Authenticode-signed; backend dependency ranges are not fully locked; SBOM/provenance are incomplete. | Backend lock/constraints, SBOM, provenance, verified checksums, code signing/timestamping and third-party licence review. |
| Recovery | Installer uninstall preserves user-data directories, but complete backup/restore, upgrade/rollback and crash recovery are not yet release-verified. | End-to-end backup/restore, migration, power-loss and upgrade/rollback tests with hash and SQLite integrity checks. |
| Misleading product claims | Product and frontend disclaimers exist. They must remain aligned with future features, website copy, support and demonstrations. | Counsel-approved intended use, warnings, privacy notice, EULA and acceptable-use policy; review each release's marketing and product claims. |

## 5. Mandatory product and user-facing documents

Before any external distribution beyond a controlled fictional-data evaluation, prepare and obtain legal review of:

1. **Intended-use statement and product description** — define users, education-only purpose, prohibited clinical use, inputs/outputs and limitations.
2. **End-user licence / terms of use** — permitted use, no real patient data, no clinical reliance, user responsibilities, update/support terms, warranties and limitation-of-liability language to the extent legally permissible.
3. **Privacy notice** — data inventory, data categories, local storage paths, model/API data flows, retention, deletion, logs, backups, third-party components, complaint/grievance route and any applicable data-principal rights.
4. **Acceptable-use policy** — synthetic/de-identified training cases only; no patient identifiers, real case summaries, hospital MRNs, images or exports unless separately approved.
5. **Safety and limitation notice** — model outputs can be incomplete, incorrect or inconsistent; no guideline retrieval/verification where disconnected; no real-world treatment recommendations.
6. **Security and incident procedure** — vulnerability intake, incident triage, preservation of evidence, patch/release workflow and legally required notifications where applicable.
7. **Third-party notices and licence register** — Ollama runtime, Qwen model, Python/Node packages, fonts/assets and any future framework or dataset licence.

A limitation-of-liability clause, indemnity or disclaimer must be drafted by counsel. Do not write a clause purporting to waive non-waivable statutory rights or to excuse deliberate misconduct, negligence or mandatory safety obligations. A checkbox or disclaimer does not replace safe design and testing.

## 6. Release blockers and sign-off

The following are blockers for any real-patient, clinical, hospital or institutional deployment:

- no regulatory classification and written intended-use review by qualified Indian counsel/regulatory specialist;
- no privacy/data-protection assessment for the actual deployment and data-controller/processor roles;
- no approval to collect or process real patient information;
- no independent clinical validation and evidence-source verification;
- unresolved hard failures in live model provenance/Chair synthesis;
- no current-head clean-host install/model quality gate;
- no backup/restore and upgrade/rollback acceptance;
- no reviewed local API threat model and authentication decision;
- no approved EULA, privacy notice, acceptable-use policy, incident process and release warnings;
- no verified installer signature/SBOM/release provenance.

**Sign-off record:** Product owner: TBD; Indian regulatory/healthcare counsel: not obtained; privacy counsel/DPO review: not obtained; qualified clinical safety reviewer: not obtained; security penetration test: not completed.

## 7. Review trigger

Re-open this register before any change to intended use, user population, data fields, real-patient import, imaging, EHR/HIS/PACS integrations, treatment recommendation, dose/planning, guideline retrieval, cloud inference, telemetry, multi-user/network exposure, monetisation, distribution outside India or marketing claims. Record decision, reviewer, date, source version and evidence before release.

**No zero-lawsuit, zero-defect, compliance-certified or risk-free claim is authorised by this document.**
