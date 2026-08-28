"""Checker A: the human-authored criterion set and gold predicates.

This file is the evaluation substrate. It is authored by hand from the raw
ClinicalTrials.gov text, committed before any system run, and used identically by
every arm, so that all arms answer the same questions and the comparison is
between verdicts rather than between segmentations.

Two things are recorded per criterion and both are decided before any model sees
the text:

  `checkable`  whether a structured record could settle this at all. Fixed in
               advance so the headline can be stated as "k of n criteria are
               record-checkable" instead of being read off whatever compiled.
  `gold`       a hand-written function over the engine-free plain view.

The functions are deliberately written in a different shape from the compiled
predicates: explicit, per-criterion, no shared interpreter, conversions spelled
out longhand. If both sides agree it should be because the clinical answer is the
same, not because they ran the same code.

Codes were verified present in the corpus vocabulary before use. Where a concept
has no code in this vocabulary the criterion says so, and that is the answer.
"""
from __future__ import annotations

from plainview import (  # type: ignore
    FAILS, INDET, MEETS, age_years, all_of, at_least, band, has_lab_at_all,
    latest_lab, orders_with, problems_with, to_kg_m2, to_mg_dl_creatinine,
    to_mg_per_mmol_uacr, to_ml_min_173, to_percent_hba1c,
)

# -- codes, all verified present in data/vendor/terminology_catalog.json -----
HBA1C = ["4548-4"]
CREAT = ["38483-4", "2160-0"]
EGFR = ["33914-3"]
BMI = ["39156-5"]
UACR = ["14959-1"]
SBP, DBP = ["8480-6"], ["8462-4"]
TRIG, HDL = ["2571-8"], ["2085-9"]

DIABETES = ["44054006"]
PREDIABETES = ["15777000"]
HYPERTENSION = ["59621000"]
MI = ["22298006", "399211009"]
STROKE = ["230690007"]
RETINOPATHY = ["422034002", "1551000119108", "97331000119101", "1501000119109"]
MALIGNANCY = ["254837009", "254637007", "424132000", "363406005", "109838007",
              "94260004", "314994000", "126906006"]
DIALYSIS_PROC = ["265764009", "302497006"]

METFORMIN = ["860975"]
INSULIN = ["106892"]
RAS_INHIBITOR = ["314076", "314077", "979492", "833036"]   # lisinopril, losartan, captopril
GLUCOCORTICOID_SYSTEMIC = ["312617", "312615"]              # prednisone 5 mg, 20 mg

#: Concepts with no representation at all in this site's vocabulary. Verified by
#: searching the catalog. A criterion that depends only on one of these cannot be
#: settled here, and that is a fact about the records, not a modelling choice.
ABSENT_FROM_VOCABULARY = [
    "SGLT2 inhibitors", "GLP-1 receptor agonists", "DPP-4 inhibitors",
    "sulfonylureas", "thiazolidinediones", "cystatin C", "FSH",
    "diabetic ketoacidosis", "transient ischaemic attack", "unstable angina",
    "lupus nephritis", "ANCA-associated vasculitis",
]


def _dialysis(p, within=None):
    rows = [r for r in p["procedures"] if r["code"] in DIALYSIS_PROC]
    if within is not None:
        import datetime as dt
        idx = dt.date.fromisoformat(p["index_date"])
        rows = [r for r in rows if r["date"]
                and 0 <= (idx - dt.date.fromisoformat(r["date"])).days <= within]
    return rows


def _egfr_recorded(p, within=None):
    """eGFR from the recorded value, converted longhand."""
    row = latest_lab(p, EGFR, within)
    if row is None or row.get("conflict"):
        return None
    return to_ml_min_173(row["value"], row["unit"])


def _egfr_from_creatinine(p, within=None):
    """CKD-EPI 2021, written out here independently of the engine."""
    row = latest_lab(p, CREAT, within)
    if row is None or row.get("conflict"):
        return None
    scr = to_mg_dl_creatinine(row["value"], row["unit"])
    if scr is None:
        return None
    a = age_years(p)
    s = (p["sex"] or "").lower()
    if a is None or s not in ("male", "female"):
        return None
    female = s == "female"
    kappa = 0.7 if female else 0.9
    alpha = -0.241 if female else -0.302
    ratio = scr / kappa
    lo = min(ratio, 1.0) ** alpha
    hi = max(ratio, 1.0) ** (-1.200)
    val = 142.0 * lo * hi * (0.9938 ** a)
    return val * 1.012 if female else val


def _egfr(p, within=None):
    """Prefer the recorded rate; fall back to the derived one."""
    v = _egfr_recorded(p, within)
    return v if v is not None else _egfr_from_creatinine(p, within)


def _hba1c(p, within=None):
    row = latest_lab(p, HBA1C, within)
    if row is None or row.get("conflict"):
        return None
    return to_percent_hba1c(row["value"], row["unit"])


def _bmi(p, within=None):
    row = latest_lab(p, BMI, within)
    if row is None or row.get("conflict"):
        return None
    return to_kg_m2(row["value"], row["unit"])


def _uacr_mg_mmol(p, within=None):
    row = latest_lab(p, UACR, within)
    if row is None or row.get("conflict"):
        return None
    return to_mg_per_mmol_uacr(row["value"], row["unit"])


def _uacr_mg_g(p, within=None):
    row = latest_lab(p, UACR, within)
    if row is None or row.get("conflict"):
        return None
    if row["unit"] in ("mg/g", "mg/gCr"):
        return row["value"]
    if row["unit"] == "mg/mmol":
        return row["value"] * 8.8402
    return None


def _present_or_unknown(rows, mappable_complete: bool) -> str:
    """Disjunction over a list where some members cannot be checked.

    Finding one settles it. Finding none settles it only when every member of the
    list could have been looked for. This is the whole reason a partly-groundable
    exclusion is not the same as a negative one.
    """
    if rows:
        return MEETS
    return FAILS if mappable_complete else INDET


# ---------------------------------------------------------------------------
# The criterion set. `gold` returns the verdict for the PATIENT, already
# accounting for inclusion versus exclusion polarity.
# ---------------------------------------------------------------------------

CRITERIA: list[dict] = []


def C(cid, nct, kind, category, text, checkable, gold, note=""):
    CRITERIA.append({"criterion_id": cid, "nct_id": nct, "kind": kind, "category": category,
                     "source_text": text, "checkable": checkable, "gold": gold,
                     "checkable_note": note})


# ===== NCT06983054: ertugliflozin and dietary sodium in T2DM ===============
N1 = "NCT06983054"

C(f"{N1}-INC-01", N1, "inclusion", "diagnosis",
  "Adults with previously diagnosed T2DM according to American Diabetes Association (ADA) criteria",
  True, lambda p: MEETS if problems_with(p, DIABETES) else INDET,
  "a coded diabetes diagnosis settles it; absence does not, since the code may sit "
  "in another system's problem list")

C(f"{N1}-INC-02", N1, "inclusion", "lab_value", "HbA1c 6.5-10%",
  True, lambda p: band(_hba1c(p), 6.5, 10.0))

C(f"{N1}-INC-03", N1, "inclusion", "demographic", "Age 18 - 85 years of age",
  True, lambda p: band(age_years(p), 18, 85))

C(f"{N1}-INC-04", N1, "inclusion", "lab_value", "Overweight or obese with BMI: >25 kg/m2",
  True, lambda p: INDET if _bmi(p) is None else (MEETS if _bmi(p) > 25 else FAILS))

C(f"{N1}-INC-05", N1, "inclusion", "reproductive",
  "Both sexes (females must be post-menopausal; no menses >1 year; in case of doubt, "
  "Follicle-Stimulating Hormone (FSH) will be determined with cut-off defined as >31 U/L)",
  False, lambda p: INDET,
  "menstrual history is not in the structured record and FSH has no code in this vocabulary")

C(f"{N1}-INC-06", N1, "inclusion", "consent_or_capacity",
  "Ability to provide signed and dated, written informed consent prior to any study procedures",
  False, lambda p: INDET, "consent is established at the screening visit")

C(f"{N1}-INC-07", N1, "inclusion", "lab_value",
  "Estimated GFR 60-90 ml/min/1.73m2 by CKD-EPI matching the eGFR range of most "
  "participants in VERTIS-CV",
  True, lambda p: band(_egfr(p), 60, 90))

C(f"{N1}-INC-08", N1, "inclusion", "lifestyle_or_social",
  "Sodium intake at baseline < 200 mmol/day",
  False, lambda p: INDET, "dietary sodium intake is not recorded in a medical record")

C(f"{N1}-INC-09", N1, "inclusion", "lab_value", "UACR < 30 mg/mmol",
  True, lambda p: INDET if _uacr_mg_mmol(p) is None
  else (MEETS if _uacr_mg_mmol(p) < 30 else FAILS),
  "the record stores UACR in mg/g and the criterion is written in mg/mmol")

C(f"{N1}-INC-10", N1, "inclusion", "medication",
  "All participants need to be on a stable dose of diabetes medication, including "
  "Metformin, SU, DPP4-inhibitors, or insulin.",
  False, lambda p: INDET,
  "dose stability is not derivable from an order list, and SU and DPP-4 inhibitors "
  "have no code in this vocabulary")

C(f"{N1}-EXC-01", N1, "exclusion", "lab_value",
  "Estimated GFR <60 mL/min/1.73m2 or eGFR > 90 mL/min/1.73m2 determined by CKD-EPI",
  True, lambda p: INDET if _egfr(p) is None
  else (FAILS if (_egfr(p) < 60 or _egfr(p) > 90) else MEETS))

C(f"{N1}-EXC-02", N1, "exclusion", "lab_value", "UACR > 30 mg/mmol",
  True, lambda p: INDET if _uacr_mg_mmol(p) is None
  else (FAILS if _uacr_mg_mmol(p) > 30 else MEETS))

C(f"{N1}-EXC-03", N1, "exclusion", "medication",
  "Current/chronic use of the following medication: SGLT2 inhibitors, TZD, GLP-1RA, "
  "glucocorticoids, immune suppressants, antimicrobial agents, chemotherapeutics",
  True, lambda p: FAILS if orders_with(p, GLUCOCORTICOID_SYSTEMIC, active_only=True) else INDET,
  "a systemic glucocorticoid on the list settles it; SGLT2 inhibitors, TZDs and "
  "GLP-1 receptor agonists have no code in this vocabulary, so an empty result cannot "
  "clear the patient")

C(f"{N1}-EXC-04", N1, "exclusion", "temporal_event",
  "History of diabetic ketoacidosis (DKA) requiring medical intervention within 1 month "
  "prior to the Screening visit.",
  False, lambda p: INDET, "diabetic ketoacidosis has no code in this vocabulary")

C(f"{N1}-EXC-05", N1, "exclusion", "temporal_event",
  "Recent (<6 months) history of cardiovascular disease, including acute coronary "
  "syndrome, chronic heart failure, myocardial infarction or stroke",
  True, lambda p: FAILS if (problems_with(p, MI, within_days=183)
                            or problems_with(p, STROKE, within_days=183)) else INDET,
  "myocardial infarction and stroke are coded here; acute coronary syndrome and "
  "unstable angina are not, so silence cannot clear the patient")

# ===== NCT06989723: pioglitazone and empagliflozin in T2DM with steatosis ==
N2 = "NCT06989723"

C(f"{N2}-INC-01", N2, "inclusion", "demographic", "Adults aged 20 years or older.",
  True, lambda p: INDET if age_years(p) is None
  else (MEETS if age_years(p) >= 20 else FAILS))

C(f"{N2}-INC-02", N2, "inclusion", "lab_value",
  "Patients with inadequately controlled type 2 diabetes mellitus, defined as HbA1c "
  "between 7% and 10%",
  True, lambda p: band(_hba1c(p), 7.0, 10.0))

C(f"{N2}-INC-03", N2, "inclusion", "medication",
  "currently treated with metformin monotherapy, metformin and a sulfonylurea, "
  "metformin and a DPP-4 inhibitor, or triple therapy including metformin",
  True, lambda p: MEETS if orders_with(p, METFORMIN, active_only=True) else INDET,
  "metformin is coded here; every listed partner drug class is not, so an empty "
  "result cannot rule the patient out")

C(f"{N2}-INC-04", N2, "inclusion", "procedure",
  "Evidence of hepatic steatosis within the past 3 months, confirmed by Fibroscan with "
  "a controlled attenuation parameter (CAP) >= 268 dB/m",
  False, lambda p: INDET,
  "transient elastography is not represented in this record")

C(f"{N2}-INC-05", N2, "inclusion", "vital_sign",
  "Presence of at least one of the following metabolic abnormalities: blood pressure "
  ">=130 mmHg systolic or >=85 mmHg diastolic or use of antihypertensive medication; "
  "serum triglycerides >=150 mg/dL or current use of lipid-lowering agents; "
  "HDL-cholesterol <=45 mg/dL for men or <=50 mg/dL for women",
  True, lambda p: at_least(1, [_bp_or_antihypertensive(p), _trig_high(p), _hdl_low(p)]),
  "waist circumference, HOMA-IR and CRP are not recorded, so only three of the six "
  "listed abnormalities can be checked; one proven abnormality still settles it")

C(f"{N2}-EXC-01", N2, "exclusion", "medication",
  "Patients receiving insulin therapy or diagnosed with type 1 diabetes mellitus.",
  True, lambda p: FAILS if orders_with(p, INSULIN, active_only=True) else INDET,
  "an insulin order settles it; type 1 diabetes is not separately coded here")

C(f"{N2}-EXC-02", N2, "exclusion", "medication",
  "Use of the following medications within the past 3 months: GLP-1 receptor agonists, "
  "SGLT2 inhibitors, rosiglitazone (TZD), vitamin E, or ursodeoxycholic acid (UDCA).",
  False, lambda p: INDET,
  "none of these drug classes has a code in this vocabulary")

C(f"{N2}-EXC-03", N2, "exclusion", "lab_value",
  "Renal failure: Serum creatinine >= 2.0 mg/dL, estimated glomerular filtration rate "
  "(eGFR) < 30 mL/min/1.73 m2 (CKD-EPI formula), or patients with end-stage renal "
  "disease or on dialysis.",
  True, lambda p: _renal_failure(p))

C(f"{N2}-EXC-04", N2, "exclusion", "diagnosis",
  "Presence of hepatocellular carcinoma, active malignancy, or metastatic cancer",
  True, lambda p: FAILS if problems_with(p, MALIGNANCY, active_only=True) else INDET,
  "coded malignancies settle it; hepatocellular carcinoma specifically has no code here")

C(f"{N2}-EXC-05", N2, "exclusion", "investigator_judgement",
  "No changes in anti-diabetic or metabolic medications within the past 3 months, "
  "unless the changes are deemed by the investigator not to affect study outcomes.",
  False, lambda p: INDET, "turns on the investigator's judgement")

# ===== NCT06717698: kidney impairment with albuminuria =====================
N3 = "NCT06717698"

C(f"{N3}-INC-01", N3, "inclusion", "demographic",
  "Age 18 years or above at the time of signing the informed consent.",
  True, lambda p: INDET if age_years(p) is None
  else (MEETS if age_years(p) >= 18 else FAILS))

C(f"{N3}-INC-02", N3, "inclusion", "reproductive",
  "Female of non-childbearing potential, or male.",
  False, lambda p: INDET, "childbearing potential is not recorded in the structured record")

C(f"{N3}-INC-03", N3, "inclusion", "lab_value",
  "BMI greater than or equal to 27.0 kg/m^2 at screening.",
  True, lambda p: INDET if _bmi(p) is None else (MEETS if _bmi(p) >= 27.0 else FAILS))

C(f"{N3}-INC-04", N3, "inclusion", "lab_value",
  "Kidney impairment defined by serum creatinine and cystatin C-based eGFR greater than "
  "or equal to 15 and less than 90 mL/min/1.73 m^2.",
  False, lambda p: INDET,
  "the criterion specifies a creatinine-and-cystatin-C equation; cystatin C has no code "
  "in this vocabulary, and a creatinine-only eGFR is a different quantity")

C(f"{N3}-INC-05", N3, "inclusion", "lab_value",
  "Albuminuria defined by Urine Albumin-to-Creatinine Ratio (UACR) greater than or equal "
  "to 100 and less than 5000 mg/g.",
  True, lambda p: INDET if _uacr_mg_g(p) is None
  else (MEETS if 100 <= _uacr_mg_g(p) < 5000 else FAILS),
  "stated in mg/g, which is the unit the record already uses")

C(f"{N3}-INC-06", N3, "inclusion", "medication",
  "Treatment with maximum labelled or tolerated dose of an ACE inhibitor or an ARB, "
  "unless contraindicated or not tolerated in the opinion of the investigator. Treatment "
  "dose must be stable for at least 30 days prior to screening.",
  False, lambda p: INDET,
  "maximum tolerated dose and dose stability are not derivable from an order list, and "
  "the exception turns on investigator judgement")

C(f"{N3}-INC-07", N3, "inclusion", "diagnosis",
  "Diagnosed with type 2 diabetes mellitus greater than or equal to 180 days before "
  "screening, or not diagnosed with type 2 diabetes mellitus.",
  True, lambda p: _t2d_180_or_absent(p),
  "a disjunction that is satisfied either way as long as the timing is legible")

C(f"{N3}-EXC-01", N3, "exclusion", "temporal_event",
  "Myocardial infarction, stroke, transient ischaemic attack, or hospitalization for "
  "unstable angina pectoris within 180 days before screening.",
  True, lambda p: FAILS if (problems_with(p, MI, within_days=180)
                            or problems_with(p, STROKE, within_days=180)) else INDET,
  "myocardial infarction and stroke are coded; transient ischaemic attack and unstable "
  "angina are not, so an empty result cannot clear the patient")

C(f"{N3}-EXC-02", N3, "exclusion", "procedure",
  "Chronic or intermittent haemodialysis or peritoneal dialysis within 90 days before "
  "screening.",
  True, lambda p: FAILS if _dialysis(p, within=90) else INDET,
  "a dialysis procedure settles it; peritoneal dialysis has no separate code here")

C(f"{N3}-EXC-03", N3, "exclusion", "medication",
  "Use of any GLP-1 RA (including medication with GLP-1 RA activity) within 90 days "
  "prior to screening.",
  False, lambda p: INDET,
  "GLP-1 receptor agonists have no code in this vocabulary")

C(f"{N3}-EXC-04", N3, "exclusion", "diagnosis",
  "Lupus nephritis or antineutrophil cytoplasmic antibody (ANCA)-associated vasculitis.",
  False, lambda p: INDET, "neither condition has a code in this vocabulary")

C(f"{N3}-EXC-05", N3, "exclusion", "temporal_event",
  "Receiving immunosuppressive therapy for primary or secondary renal disease within "
  "6 months prior to screening.",
  False, lambda p: INDET,
  "immunosuppressive agents have no code in this vocabulary, and the indication "
  "qualifier is not derivable from an order")

C(f"{N3}-EXC-06", N3, "exclusion", "diagnosis",
  "Only applicable for participants with type 2 diabetes: uncontrolled and potentially "
  "unstable diabetic retinopathy or diabetic maculopathy, verified by an eye examination "
  "performed within 90 days before screening.",
  False, lambda p: INDET,
  "the record codes diabetic retinopathy but carries no grading, and 'uncontrolled and "
  "potentially unstable' is a clinical judgement made at an eye examination")

C(f"{N3}-EXC-07", N3, "exclusion", "diagnosis",
  "Presence or history of malignant neoplasms or in situ carcinomas (other than basal or "
  "squamous cell skin cancer, low-risk prostate cancer, or in-situ carcinomas of the "
  "cervix or high grade prostatic intraepithelial neoplasia) within 5 years before "
  "screening.",
  True, lambda p: FAILS if problems_with(p, MALIGNANCY, within_days=1826) else INDET,
  "the carve-outs for prostate and in-situ disease are coded here and are excluded from "
  "the code list, so a hit is a genuine hit")

C(f"{N3}-EXC-08", N3, "exclusion", "reproductive",
  "Female who is pregnant, breast-feeding or intends to become pregnant.",
  False, lambda p: INDET,
  "intent is not recorded, and a pregnancy code describes a past episode rather than "
  "current status at screening")


# -- helpers used above, defined after the codes they need ------------------

def _bp_or_antihypertensive(p) -> str:
    s = latest_lab(p, SBP)
    d = latest_lab(p, DBP)
    if s and not s.get("conflict") and s["value"] >= 130:
        return MEETS
    if d and not d.get("conflict") and d["value"] >= 85:
        return MEETS
    if orders_with(p, RAS_INHIBITOR, active_only=True):
        return MEETS
    if (s is None or s.get("conflict")) and (d is None or d.get("conflict")):
        return INDET
    return FAILS


def _trig_high(p) -> str:
    r = latest_lab(p, TRIG)
    if r is None or r.get("conflict"):
        return INDET
    if r["unit"] not in ("mg/dL", "mg/dl"):
        return INDET
    return MEETS if r["value"] >= 150 else FAILS


def _hdl_low(p) -> str:
    r = latest_lab(p, HDL)
    if r is None or r.get("conflict"):
        return INDET
    if r["unit"] not in ("mg/dL", "mg/dl"):
        return INDET
    s = (p["sex"] or "").lower()
    if s == "male":
        return MEETS if r["value"] <= 45 else FAILS
    if s == "female":
        return MEETS if r["value"] <= 50 else FAILS
    return INDET


def _renal_failure(p) -> str:
    if _dialysis(p):
        return FAILS
    row = latest_lab(p, CREAT)
    scr = None if (row is None or row.get("conflict")) else to_mg_dl_creatinine(
        row["value"], row["unit"])
    if scr is not None and scr >= 2.0:
        return FAILS
    e = _egfr(p)
    if e is not None and e < 30:
        return FAILS
    if scr is None and e is None:
        return INDET
    return MEETS


def _t2d_180_or_absent(p) -> str:
    """Either diagnosed at least 180 days ago, or not diagnosed at all."""
    old = problems_with(p, DIABETES)
    if not old:
        return MEETS                      # the "or not diagnosed" branch
    recent_only = all(
        (r["onset"] is None) for r in old)
    if recent_only:
        return INDET                      # diagnosed, but the record cannot date it
    import datetime as dt
    idx = dt.date.fromisoformat(p["index_date"])
    ages = [(idx - dt.date.fromisoformat(r["onset"])).days for r in old if r["onset"]]
    return MEETS if max(ages) >= 180 else FAILS


BY_ID = {c["criterion_id"]: c for c in CRITERIA}


def summary() -> dict:
    n = len(CRITERIA)
    ck = sum(1 for c in CRITERIA if c["checkable"])
    trials = sorted({c["nct_id"] for c in CRITERIA})
    return {"criteria": n, "checkable": ck, "not_checkable": n - ck,
            "checkable_fraction": round(ck / n, 3), "trials": trials,
            "by_category": {k: sum(1 for c in CRITERIA if c["category"] == k)
                            for k in sorted({c["category"] for c in CRITERIA})}}
