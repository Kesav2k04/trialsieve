# Prescreening worklist: NCT06983054

**DiEtary Sodium Intake Effects on Ertugliflozin-induced Changes in GFR, reNal Oxygenation and Systemic Hemodynamics: the DESIGN Study, a Randomized, Placebo-controlled, Cross-over Study With Ertugliflozin in People With Type 2 Diabetes**

Panel of 385 patients, screened on 2026-08-31.

**Each patient is screened as of their own last encounter, not as of today.** In this panel those dates run from 2019-02-23 to 2021-11-18. Ages and lab values below are as of that patient's date. Where a criterion carries no recency window, an old result satisfies it, so a patient under *Ready to contact* may be resting on a years-old value that a coordinator has to confirm before the call.

**NOT FOR USE.** Every criterion behind this document carries an approval. The run it was compiled in does not: 2 other compiled criteria in the same run were REJECTED (NCT06989723-INC-02, NCT06989723-EXC-01), and a signature clears a run rather than a page of it. It was produced with the sign-off gate overridden, which is a thing you can only do on purpose.

> This list does not decide anything. It removes patients who are provably ineligible on a dated fact in their record, and it ranks everyone else by how much is left to check. Every remaining patient needs a human. Nobody is enrolled by this document.

|                            | count | share |
|----------------------------|-------|-------|
| Ruled out, with evidence   | 187   | 49%   |
| Needs review               | 190   | 49%   |
| All checkable criteria met | 8     | 2%    |

The coordinator's list is 198 patients rather than 385.

Two files sit beside this one and carry every patient, not the first 25 of each group: a `.json` with the evidence behind each decision, and a `.csv` of one row per patient per criterion, which is the form a screening log or a CTMS takes. Both carry the same trial, date and run as the heading above.

## Operating point: 0 tolerated false exclusions

This worklist runs 3 of the trial's compiled criteria, not all of them: `NCT06983054-INC-02`, `NCT06983054-INC-03`, `NCT06983054-INC-04`. They are the set the published operating curve keeps at a budget of 0 false exclusions.

Two things a reader should hold against this. The subset was chosen by counting each criterion's false exclusions on the same patients it is then applied to, so it reports that a clean subset existed rather than that it could have been picked in advance; the cross-fitted curve in `results/RESULTS.md`, headed *TrialSieve operating curve, cross-fitted*, is the answer to that and agrees with this row. And running every compiled criterion instead rules out more of the panel and wrongly removes patients the labels do not rule out, which is why the registered outcome for that configuration reads VOID. Both are in the report.

## What removed people

| criterion            | patients removed | text                                    |
|----------------------|------------------|-----------------------------------------|
| `NCT06983054-INC-02` | 131              | HbA1c 6.5-10%                           |
| `NCT06983054-INC-04` | 59               | Overweight or obese with BMI: >25 kg/m2 |
| `NCT06983054-INC-03` | 10               | Age 18 - 85 years of age                |

## Ready to contact

8 of 385 patients meet **every** criterion applied here, each on a dated fact already in the record, with nothing left open. Start here.

| patient    | age | sex    | HbA1c 6.5-10%                                                  | Age 18 - 85 years of age            | Overweight or obese with BMI: >25...       |
|------------|-----|--------|----------------------------------------------------------------|-------------------------------------|--------------------------------------------|
| `4b10c406` | 69  | female | Hemoglobin A1c/Hemoglobin.total in Blood = 6.86 % (2021-05-27) | Age at index date = 69 (2021-07-08) | Body Mass Index = 27.44 kg/m2 (2021-05-27) |
| `509f9a77` | 56  | female | Hemoglobin A1c/Hemoglobin.total in Blood = 7.46 % (2021-11-15) | Age at index date = 56 (2021-11-15) | Body Mass Index = 29.83 kg/m2 (2021-11-15) |
| `56cfe6a5` | 51  | male   | Hemoglobin A1c/Hemoglobin.total in Blood = 6.95 % (2021-03-06) | Age at index date = 51 (2021-03-06) | Body Mass Index = 33.82 kg/m2 (2021-03-06) |
| `76b289fd` | 36  | female | Hemoglobin A1c/Hemoglobin.total in Blood = 7.47 % (2019-05-19) | Age at index date = 36 (2021-10-03) | Body Mass Index = 29.88 kg/m2 (2019-05-19) |
| `80534c6c` | 26  | male   | Hemoglobin A1c/Hemoglobin.total in Blood = 6.6 % (2019-10-18)  | Age at index date = 26 (2021-04-16) | Body Mass Index = 26.75 kg/m2 (2019-10-18) |
| `83f922a9` | 57  | female | Hemoglobin A1c/Hemoglobin.total in Blood = 7 % (2020-12-12)    | Age at index date = 57 (2021-09-10) | Body Mass Index = 28.01 kg/m2 (2020-12-12) |
| `aade3c61` | 35  | male   | Hemoglobin A1c/Hemoglobin.total in Blood = 6.6 % (2020-04-01)  | Age at index date = 35 (2021-05-19) | Body Mass Index = 26.03 kg/m2 (2020-04-01) |
| `d362f4e5` | 47  | female | Hemoglobin A1c/Hemoglobin.total in Blood = 7.49 % (2021-09-10) | Age at index date = 47 (2021-09-10) | Body Mass Index = 29.99 kg/m2 (2021-09-10) |

## What this document does not settle

This trial has **15 criteria**. This document answers **3** of them. The remaining **12** are unchanged by running it, and every one of the 198 patients above still needs them checked by a person.

|                       | count | why, and what it means for you                                                                                                                                    |
|-----------------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Answered here         | 3     | Compiled into a checkable predicate and run against every chart in the panel.                                                                                     |
| Compiled, not applied | 6     | Compiled successfully and held back by the operating point above, because applying them wrongly removes patients on this panel. Reviewable in `runs/*/compiled/`. |
| Not compiled          | 6     | The compiler declined to express them and said why. They were never going to be automated by this system and are listed below so they are not forgotten.          |

The ones the compiler refused, with its reason:

| criterion            | text                                                         | why it was left to you                                                                                                   |
|----------------------|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `NCT06983054-INC-05` | Both sexes (females must be post-menopausal; no menses >1... | Menstrual history (no menses for >1 year) is not tracked in structured coded medical records, and resolving postmenopaus |
| `NCT06983054-INC-06` | Ability to provide signed and dated, written informed...     | Evaluating a participant's ability or willingness to provide informed consent requires assessing consent and capacity, w |
| `NCT06983054-INC-08` | Sodium intake at baseline < 200 mmol/day                     | Dietary sodium intake is a lifestyle and nutritional assessment that is not routinely captured in structured medical rec |
| `NCT06983054-INC-10` | All participants need to be on a stable dose of diabetes...  | cannot be represented in this site's vocabulary. Sulfonylurea: no entry in this site's medication vocabulary matches any |
| `NCT06983054-EXC-03` | Current/chronic use of the following medication: SGLT2...    | cannot be represented in this site's vocabulary. SGLT2 inhibitor: no entry in this site's medication vocabulary matches  |
| `NCT06983054-EXC-04` | History of diabetic ketoacidosis (DKA) requiring medical...  | cannot be represented in this site's vocabulary. Diabetic ketoacidosis: the vocabulary returned candidates but none of t |

The shrink this document reports is a shrink in the panel, not in the protocol. It is the difference between reading 385 charts against 3 questions and reading 198 charts against 12.

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

### 188 patients, 1 open

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record

The same question for all 188: one thing to go and find, then 188 values to read back.

`0288c42c` (41, female), `03777c32` (53, female), `03b291e7` (82, male), `03bb882e` (64, female), `03e502b6` (54, female), `055bcb42` (40, male), `05801c88` (27, female), `065e8a3d` (24, male), `0896b0af` (64, female), `0ad457cc` (25, male), `0ae08855` (35, female), `0b43ab26` (33, male) and 176 more in the machine-readable output.

### 2 patients, 2 open

- **HbA1c 6.5-10%**  
  no observation with code 4548-4 in the record
- **Overweight or obese with BMI: >25 kg/m2**  
  no observation with code 39156-5 in the record

`094c294d` (30, female), `355a3cad` (30, female).


## Where the review time goes

| criterion            | patients needing a human | text                                    |
|----------------------|--------------------------|-----------------------------------------|
| `NCT06983054-INC-02` | 190                      | HbA1c 6.5-10%                           |
| `NCT06983054-INC-04` | 2                        | Overweight or obese with BMI: >25 kg/m2 |

A criterion at the top of this table is where an extra data feed, or a single clarification with the sponsor, would buy the most time.

