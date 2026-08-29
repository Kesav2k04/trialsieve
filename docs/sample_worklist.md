# Prescreening worklist: NCT06983054

**DiEtary Sodium Intake Effects on Ertugliflozin-induced Changes in GFR, reNal Oxygenation and Systemic Hemodynamics: the DESIGN Study, a Randomized, Placebo-controlled, Cross-over Study With Ertugliflozin in People With Type 2 Diabetes**

Panel of 385 patients screened on 2026-08-29.

**NOT FOR USE.** No human has reviewed the compiled criteria behind this document. It was produced with the sign-off gate overridden, which is a thing you can only do on purpose.

> This list does not decide anything. It removes patients who are provably ineligible on a dated fact in their record, and it ranks everyone else by how much is left to check. Every remaining patient needs a human. Nobody is enrolled by this document.

|                            | count | share |
|----------------------------|-------|-------|
| Ruled out, with evidence   | 187   | 49%   |
| Needs review               | 190   | 49%   |
| All checkable criteria met | 8     | 2%    |

The coordinator's list is 198 patients rather than 385.

## Operating point: 0 tolerated false exclusions

This worklist runs 3 of the trial's compiled criteria, not all of them: `NCT06983054-INC-02`, `NCT06983054-INC-03`, `NCT06983054-INC-04`. They are the set the published operating curve keeps at a budget of 0 false exclusions.

Two things a reader should hold against this. The subset was chosen by counting each criterion's false exclusions on the same patients it is then applied to, so it reports that a clean subset existed rather than that it could have been picked in advance; `operating_curve_cv` in `results/RESULTS.md` is the cross-fitted answer to that. And running every compiled criterion instead removes almost the whole panel, because one of them treats a silent record as a negative. That configuration is measured in the report and is not what a deployment would run.

## What removed people

| criterion            | patients removed | text                                    |
|----------------------|------------------|-----------------------------------------|
| `NCT06983054-INC-02` | 131              | HbA1c 6.5-10%                           |
| `NCT06983054-INC-04` | 59               | Overweight or obese with BMI: >25 kg/m2 |
| `NCT06983054-INC-03` | 10               | Age 18 - 85 years of age                |

## Ruled out

Each line names the criterion that removed the patient and the record entry it read. A blank here would be an assertion; there are none.

| patient    | age | sex    | failed criterion     | evidence from the record                                       |
|------------|-----|--------|----------------------|----------------------------------------------------------------|
| `01d78eb5` | 20  | female | `NCT06983054-INC-04` | Body Mass Index = 22.75 kg/m2 (2020-02-12)                     |
| `02b1604a` | 61  | male   | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.09 % (2021-08-27) |
| `03a870d0` | 65  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.25 % (2021-08-10) |
| `05877654` | 27  | female | `NCT06983054-INC-04` | Body Mass Index = 22.97 kg/m2 (2021-05-23)                     |
| `060e72d3` | 52  | male   | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 3.6 % (2021-08-13)  |
| `07a1f80c` | 64  | male   | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.15 % (2020-12-14) |
| `07fc8824` | 67  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.18 % (2021-11-07) |
| `09faca51` | 56  | male   | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.34 % (2021-07-02) |
| `0a168e32` | 22  | male   | `NCT06983054-INC-04` | Body Mass Index = 22.88 kg/m2 (2021-02-24)                     |
| `0afb59a5` | 40  | male   | `NCT06983054-INC-04` | Body Mass Index = 23.83 kg/m2 (2020-12-11)                     |
| `0c821314` | 45  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 5.89 % (2021-03-27) |
| `0cb8b8f9` | 20  | male   | `NCT06983054-INC-04` | Body Mass Index = 20.29 kg/m2 (2021-06-24)                     |
| `0f235c70` | 29  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 5.91 % (2021-02-14) |
| `0f444cf3` | 66  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.32 % (2021-05-26) |
| `1293efbb` | 61  | male   | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.12 % (2021-02-07) |
| `165a4435` | 48  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.12 % (2021-03-25) |
| `18022a84` | 54  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.02 % (2021-08-30) |
| `1a4f3136` | 43  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 5.92 % (2019-12-31) |
| `1ab85caa` | 42  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 6.33 % (2021-07-12) |
| `1cfa5a70` | 62  | female | `NCT06983054-INC-02` | Hemoglobin A1c/Hemoglobin.total in Blood = 5.84 % (2021-01-13) |

_167 further ruled-out patients in the machine-readable output._

## Needs review, cheapest first

Ranked by how few questions remain. The questions are the ones the record could not settle, written out so they can be answered without reopening the chart from the beginning.

### `0288c42c`  (41, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `03777c32`  (53, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `03b291e7`  (82, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `03bb882e`  (64, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `03e502b6`  (54, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `055bcb42`  (40, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `05801c88`  (27, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `065e8a3d`  (24, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0896b0af`  (64, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0ad457cc`  (25, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0ae08855`  (35, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0b43ab26`  (33, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0b48bf9b`  (47, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0bbf4179`  (40, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0d281c81`  (46, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0d61d17e`  (29, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0e78dfee`  (57, male) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0ee91088`  (35, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `0fc183b2`  (50, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

### `122d96b5`  (65, female) - 1 open, 2 already met

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

_170 further patients in the machine-readable output._

## Where the review time goes

| criterion            | patients needing a human | text                                    |
|----------------------|--------------------------|-----------------------------------------|
| `NCT06983054-INC-02` | 190                      | HbA1c 6.5-10%                           |
| `NCT06983054-INC-04` | 2                        | Overweight or obese with BMI: >25 kg/m2 |

A criterion at the top of this table is where an extra data feed, or a single clarification with the sponsor, would buy the most time.

