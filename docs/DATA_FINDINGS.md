# Data findings

Recorded as they were discovered, so the evaluation design can be traced back to
properties of the data rather than to guesses.

## Corpus

- **Patients:** Synthea sample data, FHIR R4, `synthea_sample_data_fhir_r4_nov2021.zip`,
  sha256 `6d3c5433bcae4791bc5c30469d1445b430fb4894d5c13bda15fee0584bbd7778`,
  94,887,125 bytes, from `https://synthetichealth.github.io/synthea-sample-data/downloads/`.
  555 patient bundles. 500 alive, 385 alive and adult at their index date.
- **Mean bundle size: 2.0 MB** (1.13 GB total). This is the single most consequential
  property of the corpus: a full chart is on the order of 500K tokens, so
  "paste the chart into one prompt" is not a baseline anyone could actually run.
  The baseline has to receive a chart digest, and the digest becomes a design
  decision that must be held identical across arms.
- **Trials:** ClinicalTrials.gov API v2 (US Government, public domain). 144 recruiting
  interventional trials retrieved across six cardiometabolic conditions and ranked by
  how much of their criteria text is record-checkable.

## Cohort depth (alive, adult, n=385)

| Condition | n | | Lab | n |
|---|---|---|---|---|
| Obesity | 182 | | BMI | 383 |
| Diabetes | 139 | | HbA1c | 139 |
| Prediabetes | 129 | | Lipid panel | 291 |
| Hypertension | 129 | | Creatinine | 158 |
| Anemia | 125 | | eGFR | present |
| Stroke | 18 | | UACR | present |
| Atrial fibrillation | 14 | | | |
| CKD | 8 | | | |

Cardiometabolic is the only place in this corpus with enough depth to support a
real evaluation. Heart failure (2), COPD (3) and MI (0) are too thin to use.

## Code vocabulary actually present

193 Condition codes, 259 Observation codes, 167 Procedure codes, 140 Medication codes.
Full catalog at `data/vendor/terminology_catalog.json`.

Key codes: HbA1c `4548-4`, creatinine `38483-4` (and `2160-0`, rare), eGFR `33914-3`,
BMI `39156-5`, UACR `14959-1`, LDL `18262-6`, triglycerides `2571-8`, HDL `2085-9`,
systolic `8480-6`, diastolic `8462-4`, ALT `1742-6`, AST `1920-8`, albumin `1751-7`,
platelets `777-3`. Conditions: diabetes `44054006`, prediabetes `15777000`,
hypertension `59621000`, hyperlipidemia `55822004`, coronary heart disease `53741008`,
MI `22298006`, history of MI `399211009`, CKD stage 1 `431855005`, CHF `88805009`.

## Two unit hazards that are in the data, not invented

1. **eGFR is recorded under two different units in the same corpus.**
   `33914-3` appears 695 times as `mL/min/{1.73_m2}` and 888 times as plain `mL/min`.
   Any criterion phrased "eGFR 60-90 mL/min/1.73m2" is being compared against a column
   where the majority of rows do not carry the body-surface normalisation. A reader
   that trusts the number and ignores the unit gets the wrong answer on 56% of rows.

2. **UACR is stored in `mg/g`; trials state the threshold in `mg/mmol`.**
   `14959-1` is recorded in `mg/g`. NCT06983054 sets "UACR < 30 mg/mmol". The
   conversion is roughly 8.84 mg/g per mg/mmol, so 30 mg/mmol is about 265 mg/g.
   Comparing the bare numbers rejects nearly every patient who should pass.

Both hazards were found by reading the corpus, and both appear in criteria of trials
that were selected before the units were checked. They are used as evaluation cases
rather than as illustrations.

## Trial fit

NCT06983054 (ertugliflozin / dietary sodium, T2DM) is an unusually good fit: its
inclusion criteria reference HbA1c 6.5-10%, age 18-85, BMI > 25, eGFR 60-90
mL/min/1.73m2, UACR < 30 mg/mmol, and stable metformin / sulfonylurea / DPP-4 /
insulin, all of which exist in the corpus vocabulary. Its exclusions reference drug
classes (SGLT2 inhibitors, TZD, GLP-1RA, glucocorticoids, NSAIDs) and temporal windows
(DKA within 1 month, cardiovascular disease within 6 months).
