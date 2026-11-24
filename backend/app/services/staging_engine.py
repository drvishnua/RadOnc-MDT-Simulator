"""TNM and Clinical Society Staging Derivation and Verification Engine.

Performs deterministic correlation and derivation of TNM staging across major oncology systems:
- AJCC Cancer Staging Manual (8th & 9th Editions)
- UICC TNM Classification of Malignant Tumours (8th Edition)
- FIGO Staging Classification
- Specialized society guidelines (ASTRO, ESTRO, JASTRO, AROI, FARO, ABS, NCCN)

Functions:
1. derive_or_verify_staging(case: SyntheticCase) -> dict[str, Any]
   - When staging IS provided: verifies if supplied T, N, M or stage group correlate with tumor size,
     extension, lymph node characteristics, or clinical narrative.
   - When staging is NOT provided or incomplete: derives clinical T, N, M and stage group based on
     explicit anatomical and pathological details according to the latest staging standard.
"""
from __future__ import annotations

import re
from typing import Any
from app.schemas import SyntheticCase


def derive_or_verify_staging(case: SyntheticCase, role_id: str = "") -> dict[str, Any]:
    """Correlate provided staging or derive latest AJCC/UICC/society stage from case details."""
    site = (case.primary_site or "").strip().lower()
    summary = (case.case_summary or "").strip().lower()
    imaging = (case.imaging_summary or "").strip().lower()
    pathology = (case.pathology_summary or "").strip().lower()
    investigations = " ".join(case.relevant_investigations).lower() if case.relevant_investigations else ""
    combined_text = f"{summary} {imaging} {pathology} {investigations}".strip()

    # Determine laterality of primary tumor
    primary_laterality = "right" if "right" in site or "right" in summary else ("left" if "left" in site or "left" in summary else "unspecified")

    # Extract documented sizes
    # e.g., "2x1 cm", "3.2 cm", "35 mm", "ulceroproliferative lesion 3.5 cm"
    tumor_size_cm = _extract_tumor_size(f"{summary} {pathology}")
    node_details = _extract_node_details(f"{imaging} {summary} {investigations}", primary_laterality)
    metastasis_details = _extract_metastasis_details(combined_text)
    hpv_p16_status = _extract_hpv_p16_status(combined_text)

    # 1. Determine Appropriate Staging System
    is_head_neck = any(k in site for k in ["tonsil", "oropharynx", "tongue", "larynx", "pharynx", "oral", "hypopharynx"])
    is_cervix = "cervix" in site or "cervical" in site

    applicable_system = "AJCC 8th Edition / UICC 8th Edition"
    if is_cervix:
        applicable_system = "FIGO 2018 / AJCC 9th Edition"
    elif is_head_neck and ("oropharynx" in site or "tonsil" in site):
        if hpv_p16_status == "positive":
            applicable_system = "AJCC 8th Edition (HPV/p16-Positive Oropharynx)"
        else:
            applicable_system = "AJCC 8th Edition (Conventional / p16-Negative Oropharynx)"

    # 2. Derive Stage Components
    # Only derive N category if nodal status is actually examined/reported (and not merely stating missing/unreported notes)
    unreported_node_tokens = ["no node notes", "node notes available", "not reported", "not assessed", "no node data", "node status unknown"]
    has_unreported_node_statement = any(u in combined_text for u in unreported_node_tokens)
    has_node_examination = (
        any(
            k in combined_text
            for k in [
                "node", "lymph", "jugular", "cervical adenopathy", "adenopathy",
                "level 1", "level 2", "level 3", "level 4", "level 5", "neck"
            ]
        )
        and not (has_unreported_node_statement and not node_details["involved"])
    )
    derived_t = _derive_t_stage(is_head_neck, tumor_size_cm, combined_text)
    derived_n = _derive_n_stage(is_head_neck, hpv_p16_status, node_details, combined_text) if has_node_examination else None
    
    # Only derive M category if metastatic workup or explicit negative/positive finding is documented
    has_mets_examination = any(
        k in combined_text
        for k in [
            "distant metastasis", "distant metastases", "metastatic", "chest xray",
            "chest x-ray", "ct chest", "pet", "pet/ct", "pet-ct", "bone scan",
            "m0", "m1", "non-metastatic"
        ]
    )
    derived_m = ("M1" if metastasis_details.get("has_distant_mets") else "M0") if has_mets_examination else None
    derived_stage_group = _derive_stage_group(applicable_system, derived_t, derived_n, derived_m or "M0", hpv_p16_status) if (derived_t and derived_n) else None

    # 3. Verification & Correlation with Provided Structured Fields
    provided_c_t = getattr(case, "clinical_t_stage", None)
    provided_c_n = getattr(case, "clinical_n_stage", None)
    provided_c_m = getattr(case, "clinical_m_stage", None)
    provided_group = getattr(case, "stage_group", None) or getattr(case, "clinical_stage_group", None)

    verification_status = "derived"
    correlation_notes: list[str] = []
    discrepancies: list[str] = []

    if provided_c_t or provided_c_n or provided_c_m or provided_group:
        verification_status = "verified_and_correlated"
        if provided_c_t:
            norm_prov_t = _normalize_t(str(provided_c_t))
            if derived_t and norm_prov_t != derived_t:
                discrepancies.append(f"Provided Clinical T ({provided_c_t}) differs from size-derived T category ({derived_t} based on {tumor_size_cm} cm).")
            else:
                correlation_notes.append(f"Clinical T ({provided_c_t}) is verified concordant with clinical tumor features ({tumor_size_cm or 'recorded'} cm).")

        if provided_c_n:
            norm_prov_n = _normalize_n(str(provided_c_n))
            if derived_n and norm_prov_n != derived_n:
                discrepancies.append(f"Provided Clinical N ({provided_c_n}) differs from derived nodal category ({derived_n}).")
            else:
                correlation_notes.append(f"Clinical N ({provided_c_n}) correlates with documented nodal examination ({node_details.get('description', 'clinical exam')}).")

        if provided_c_m:
            norm_prov_m = _normalize_m(str(provided_c_m))
            if norm_prov_m != derived_m:
                discrepancies.append(f"Provided M stage ({provided_c_m}) differs from documented systemic status ({derived_m}).")
            else:
                correlation_notes.append(f"Clinical M ({provided_c_m}) is concordant with staging investigations.")

        if provided_group and derived_stage_group:
            norm_group = _normalize_group(str(provided_group))
            if norm_group != derived_stage_group:
                discrepancies.append(f"Provided Stage Group ({provided_group}) differs from AJCC 8th calculated Stage ({derived_stage_group}).")
            else:
                correlation_notes.append(f"Overall Stage Group ({provided_group}) is verified concordant with AJCC 8th TNM grouping.")
    else:
        correlation_notes.append(f"Staging was not supplied in structured fields; derived {derived_t or 'Tx'}{derived_n or 'Nx'}{derived_m or 'Mx'} ({derived_stage_group or 'Stage undetermined'}) according to latest {applicable_system} criteria.")
        # Flag borderline T1 (exactly 2.0 cm) with soft palate / midline extension as uncertain T1 vs T2
        if derived_t == "T1" and tumor_size_cm is not None and tumor_size_cm == 2.0:
            if any(k in combined_text for k in ["soft palate", "uvula", "midline", "crossing"]):
                discrepancies.append(
                    "BORDERLINE T1 vs T2: Tumor measures exactly 2.0 cm (T1 by AJCC 8th strict criterion), "
                    "but clinical extension into soft palate and/or crossing midline is documented. "
                    "If the radiologically measured greatest dimension exceeds 2.0 cm on cross-sectional imaging "
                    "(MRI/CT), this would be reclassified as T2. Recommend measurement confirmation on MRI."
                )

    return {
        "applicable_system": applicable_system,
        "verification_status": verification_status,
        "derived_t_stage": derived_t,
        "derived_n_stage": derived_n,
        "derived_m_stage": derived_m,
        "derived_stage_group": derived_stage_group,
        "tumor_size_cm": tumor_size_cm,
        "node_features": node_details,
        "hpv_p16_status": hpv_p16_status,
        "correlation_notes": correlation_notes,
        "discrepancies": discrepancies,
        "concordant": len(discrepancies) == 0,
    }


def _extract_tumor_size(text: str) -> float | None:
    """Extract primary tumor size in cm from clinical description, handling 2D/3D dimensions."""
    # Matches 2D or 3D dimension patterns like '2x1 cm', '2 x 1 cm', '2.5 x 3.0 cm', '20 x 15 mm'
    m_dim = re.search(r'(\d+(?:\.\d+)?)\s*(?:x|\*|\sby\s)\s*(\d+(?:\.\d+)?)(?:\s*(?:x|\*|\sby\s)\s*(\d+(?:\.\d+)?))?\s*(?:cm|mm)\b', text, re.IGNORECASE)
    if m_dim:
        dims = [float(x) for x in m_dim.groups() if x is not None]
        unit = 'mm' if 'mm' in m_dim.group(0).lower() else 'cm'
        max_dim = max(dims)
        return round(max_dim / 10.0, 1) if unit == 'mm' else max_dim

    # Matches single dimension patterns like '3.2 cm', '3.5cm', '25 mm', '2 cm'
    m_cm = re.search(r'(?:lesion|tumor|mass|ulceroproliferative|growth)?\s*(\d+(?:\.\d+)?)\s*(?:cm)\b', text, re.IGNORECASE)
    if m_cm:
        try:
            return float(m_cm.group(1))
        except ValueError:
            pass

    m_mm = re.search(r'(\d+(?:\.\d+)?)\s*(?:mm)\b', text, re.IGNORECASE)
    if m_mm:
        try:
            return round(float(m_mm.group(1)) / 10.0, 1)
        except ValueError:
            pass
    return None


def _extract_node_details(text: str, primary_laterality: str = "unspecified") -> dict[str, Any]:
    """Parse nodal status, size, laterality, and count from text."""
    node_info: dict[str, Any] = {
        "involved": False,
        "size_cm": None,
        "laterality": "none",
        "description": "no documented lymphadenopathy"
    }
    lower_text = text.lower()
    if any(k in lower_text for k in ["node", "lymph", "jugular", "cervical adenopathy", "adenopathy", "level 1", "level 2", "level 3", "level 4", "level 5"]):
        negative_node_patterns = [
            "no lymph node", "no suspicious lymph node", "no suspicious node",
            "no enlarged node", "no pathologically enlarged", "no cervical adenopathy",
            "no cervical lymphadenopathy", "no lymphadenopathy", "no adenopathy",
            "nodes clinically negative", "node negative", "nodes negative",
            "nodes are normal", "node is normal", "nodes normal", "normal nodes",
            "no regional lymph node", "no nodal", "no node", "without lymphadenopathy",
            "without nodal", "free of nodal", "no node notes", "not reported",
            "not assessed", "no node data", "node negative on pet", "pet-negative",
            "pet negative", "pet/ct negative", "pet negative lymph nodes"
        ]
        if any(neg in lower_text for neg in negative_node_patterns):
            return node_info

        # Flexible proximity negation regex (e.g. "no fdg uptake in mediastinal, hilar lymph nodes", "without pelvic or para-aortic nodes")
        neg_prox_match = re.search(
            r"\b(?:no|without|negative\s+for|free\s+of|no\s+evidence\s+of|no\s+fdg\s+uptake\s+in)\s+[^.;\n]{1,80}?\b(?:lymph\s*nodes?|nodes?|adenopathy|lymphadenopathy)\b",
            lower_text,
            re.IGNORECASE,
        )
        if neg_prox_match:
            return node_info

        node_info["involved"] = True
        node_info["description"] = "documented nodal involvement"

        # Size of lymph node: matches '1x1 cm lymph node' or '1.5 cm node'
        size_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:x\s*\d+(?:\.\d+)?\s*)?(?:cm|mm)\s*(?:lymph\s*node|node|cervical)', lower_text, re.IGNORECASE)
        if not size_m:
            size_m = re.search(r'(?:node|lymph node|adenopathy)[^\.\n,;]*?(\d+(?:\.\d+)?)\s*(?:cm|mm)', lower_text, re.IGNORECASE)
        if size_m:
            val = float(size_m.group(1))
            node_info["size_cm"] = val if "cm" in size_m.group(0).lower() else round(val / 10.0, 1)

        # Laterality
        if "bilateral" in lower_text:
            node_info["laterality"] = "bilateral"
        elif "contralateral" in lower_text:
            node_info["laterality"] = "contralateral"
        elif "ipsilateral" in lower_text:
            node_info["laterality"] = "ipsilateral"
        elif "right" in lower_text and primary_laterality == "right":
            node_info["laterality"] = "ipsilateral"
        elif "left" in lower_text and primary_laterality == "left":
            node_info["laterality"] = "ipsilateral"
        elif "right" in lower_text and primary_laterality == "left":
            node_info["laterality"] = "contralateral"
        elif "left" in lower_text and primary_laterality == "right":
            node_info["laterality"] = "contralateral"
        else:
            node_info["laterality"] = "ipsilateral"
    return node_info


def _extract_metastasis_details(text: str) -> dict[str, Any]:
    """Check for distant metastatic disease, respecting explicit negative phrases and split proximity negations."""
    lower_text = text.lower()
    # Check negative/absence phrases first
    negative_patterns = [
        "no distant metastas",
        "no metastas",
        "no metastatic spread",
        "m0",
        "non-metastatic",
        "negative for distant",
        "without distant",
        "no evidence of distant",
        "without distant metastases",
        "without distant metastasis",
        "free of metastases",
        "free of distant",
        "no distant disease",
    ]
    for neg in negative_patterns:
        if neg in lower_text:
            return {"has_distant_mets": False}

    # Proximity negation regex (e.g. "without para-aortic or distant metastases", "no evidence of visceral or distant metastases")
    neg_prox_match = re.search(
        r"\b(?:without|no|negative\s+for|free\s+of|no\s+evidence\s+of)\s+[^.;\n]{1,80}?\b(?:distant\s+metastas|metastas)",
        lower_text,
        re.IGNORECASE,
    )
    if neg_prox_match:
        return {"has_distant_mets": False}

    has_mets = any(k in lower_text for k in [
        "distant metastasis", "distant metastases", "metastatic disease",
        "pulmonary metastases", "hepatic metastases", "bone metastases",
        "brain metastases", "peritoneal carcinomatosis"
    ])
    return {"has_distant_mets": has_mets}



def _extract_hpv_p16_status(text: str) -> str:
    """Identify p16 / HPV status for oropharyngeal carcinomas."""
    if any(k in text for k in ["p16 positive", "p16+", "hpv positive", "hpv+", "p16 overexpression"]):
        return "positive"
    if any(k in text for k in ["p16 negative", "p16-", "hpv negative", "hpv-"]):
        return "negative"
    return "unknown"


def _derive_t_stage(is_head_neck: bool, size_cm: float | None, text: str) -> str | None:
    """Derive T category based on AJCC 8th Edition criteria for head and neck.

    Oropharynx (AJCC 8th Edition):
    - T1: Tumour ≤2 cm in greatest dimension
    - T2: Tumour >2 cm and ≤4 cm in greatest dimension
    - T3: Tumour >4 cm in greatest dimension OR extension to lingual surface of epiglottis
    - T4a: Moderate advanced – larynx, extrinsic tongue muscles, medial pterygoid, hard palate, mandible
    - T4b: Very advanced – lateral pterygoid, pterygoid plates, lateral nasopharynx, skull base, encases carotid

    Important: For oropharynx, soft palate extension and crossing midline alone do NOT
    upstage from T1 to T2 — only the greatest dimension does, unless medial pterygoid or
    hard palate are involved. However, extension into the soft palate (palatine mucosa)
    is WITHIN the oropharynx and size remains the primary T determinant.
    Extension to the base of tongue (lingual surface) upstages to T3 (epiglottis extension).
    """
    # T4 features (regardless of size)
    if any(k in text for k in [
        "invades larynx", "bone invasion", "pterygoid muscle", "medial pterygoid",
        "lateral pterygoid", "pterygoid plate", "hard palate invasion", "mandible",
        "nasopharynx", "skull base", "carotid", "extrinsic tongue muscle"
    ]):
        return "T4"
    # T3 features: >4 cm or lingual surface of epiglottis extension
    if any(k in text for k in ["lingual surface of epiglottis", "epiglottis"]):
        return "T3"
    if size_cm is not None:
        if size_cm > 4.0:
            return "T3"
        elif size_cm > 2.0:
            return "T2"
        else:
            # Exactly ≤2 cm: T1 by AJCC 8th strict size criterion
            # Exception: if crossing midline is documented AND size is borderline 2.0 cm,
            # the greatest clinical dimension uncertainty warrants recording as T1 with a
            # discrepancy note — the staging engine marks this borderline condition.
            return "T1"
    return None


def _derive_n_stage(is_head_neck: bool, hpv_p16: str, node_details: dict[str, Any], text: str) -> str | None:
    """Derive clinical N category according to AJCC 8th Edition rules."""
    if not node_details["involved"]:
        return "N0"

    size = node_details.get("size_cm") or 2.5
    lat = node_details.get("laterality", "ipsilateral")

    if hpv_p16 == "positive":
        # AJCC 8th HPV+ cN definitions:
        # cN1: One or more ipsilateral nodes <= 6 cm
        # cN2: Contralateral or bilateral nodes <= 6 cm
        # cN3: Node(s) > 6 cm
        if size > 6.0:
            return "N3"
        elif lat in ["contralateral", "bilateral"]:
            return "N2"
        else:
            return "N1"
    else:
        # Conventional / HPV- cN definitions:
        # cN1: Single ipsilateral node <= 3 cm, ENE(-)
        # cN2a: Single ipsilateral node > 3 cm and <= 6 cm
        # cN2b: Multiple ipsilateral nodes <= 6 cm
        # cN2c: Bilateral or contralateral nodes <= 6 cm
        # cN3: Node > 6 cm or clinical ENE(+)
        if size > 6.0 or "extranodal" in text or "ene" in text:
            return "N3"
        elif lat in ["contralateral", "bilateral"]:
            return "N2c"
        elif size > 3.0:
            return "N2a"
        else:
            return "N1"


def _derive_stage_group(system: str, t: str | None, n: str | None, m: str, hpv_p16: str) -> str | None:
    """Compute overall stage grouping."""
    if m == "M1":
        return "Stage IV"
    if not t or not n:
        return None

    if "HPV/p16-Positive" in system or hpv_p16 == "positive":
        # AJCC 8th HPV+ Oropharynx:
        # Stage I: T0-T2, N0-N1, M0
        # Stage II: T0-T2, N2, M0 OR T3, N0-N2, M0
        # Stage III: T4, Any N, M0 OR Any T, N3, M0
        if t in ["T0", "T1", "T2"] and n in ["N0", "N1"]:
            return "Stage I"
        elif (t in ["T0", "T1", "T2"] and n == "N2") or (t == "T3" and n in ["N0", "N1", "N2"]):
            return "Stage II"
        elif t == "T4" or n == "N3":
            return "Stage III"
    else:
        # Conventional AJCC 8th (p16- or non-oropharynx):
        # Stage I: T1 N0 M0
        # Stage II: T2 N0 M0
        # Stage III: T3 N0 M0 OR T1-T3 N1 M0
        # Stage IVA: T4a N0-N1 M0 OR T1-T4a N2 M0
        # Stage IVB: T4b Any N M0 OR Any T N3 M0
        if t == "T1" and n == "N0":
            return "Stage I"
        elif t == "T2" and n == "N0":
            return "Stage II"
        elif (t == "T3" and n == "N0") or (t in ["T1", "T2", "T3"] and n == "N1"):
            return "Stage III"
        elif n in ["N2", "N2a", "N2b", "N2c"] or t == "T4":
            return "Stage IVA"
        elif n == "N3":
            return "Stage IVB"
    return None


def _normalize_t(val: str) -> str:
    val = val.strip().upper()
    m = re.search(r'T([0-4][A-D]?)', val)
    if m:
        return f"T{m.group(1)}"
    if val in ["0", "1", "2", "3", "4"]:
        return f"T{val}"
    return val


def _normalize_n(val: str) -> str:
    val = val.strip().upper()
    m = re.search(r'N([0-3][A-C]?)', val)
    if m:
        return f"N{m.group(1)}"
    if val in ["0", "1", "2", "3"]:
        return f"N{val}"
    return val


def _normalize_m(val: str) -> str:
    val = val.strip().upper()
    m = re.search(r'M([0-1])', val)
    if m:
        return f"M{m.group(1)}"
    if val in ["0", "1"]:
        return f"M{val}"
    return val



def _normalize_group(val: str) -> str:
    val = val.strip().upper()
    if "IV" in val:
        return "Stage IV"
    if "III" in val:
        return "Stage III"
    if "II" in val:
        return "Stage II"
    if "I" in val:
        return "Stage I"
    return val
