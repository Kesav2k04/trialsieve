### 1. instructions (prompt checker-b-v1)

```
You decide whether one patient meets one clinical trial eligibility criterion,
using only the record you are shown.

There are three answers and the third one matters most.

MEETS          the record shows the criterion is satisfied
FAILS          the record shows the criterion is not satisfied
INDETERMINATE  the record does not settle it

Choose INDETERMINATE whenever the deciding fact is absent, is older than a window
the criterion specifies, or is recorded in a form you cannot convert with
confidence. An absent test result is not a normal test result. A patient with no
HbA1c on file has not been shown to have an HbA1c below any threshold.

Do not reason about what is likely. A record that does not mention smoking is not
a record of a non-smoker. Judge only what is written down.

Some criteria cannot be answered from a record at all: willingness to consent,
ability to attend visits, contraception intentions, enrolment in another study.
Answer INDETERMINATE for those and say so in the reason.

Units in this record are as the source system stored them. Convert only when you
are certain of the factor. If you are not, that is INDETERMINATE.

```

### 2. input

```json
{
 "criterion_id": "NCT06989723-INC-01",
 "kind": "inclusion",
 "patient_id": "7cfbccad-2a81-400a-4858-1d2f4b680960",
 "source_text": "Adults aged 20 years or older."
}
```

### 3. llm_request -> gpt-oss-120b-medium  cassette `083c6077bfb04473`

```
[system]
You decide whether one patient meets one clinical trial eligibility criterion,
using only the record you are shown.

There are three answers and the third one matters most.

MEETS          the record shows the criterion is satisfied
FAILS          the record shows the criterion is not satisfied
INDETERMINATE  the record does not settle it

Choose INDETERMINATE whenever the deciding fact is absent, is older than a window
the criterion specifies, or is recorded in a form you cannot convert with
confidence. An absent test result is not a normal test result. A patient with no
HbA1c on file has not been shown to have an HbA1c below any threshold.

Do not reason about what is likely. A record that does not mention smoking is not
a record of a non-smoker. Judge only what is written down.

Some criteria cannot be answered from a record at all: willingness to consent,
ability to attend visits, contraception intentions, enrolment in another study.
Answer INDETERMINATE for those and say so in the reason.

Units in this record are as the source system stored them. Convert only when you
are certain of the factor. If you are not, that is INDETERMINATE.


[user]
Criterion (inclusion): Adults aged 20 years or older.

Patient record, as of 2021-11-06:

Demographics: age 27, sex male, index date 2021-11-06

Laboratory and vital measurements (364 rows, 56 distinct):
  [21000-5] Erythrocyte distribution width [Entitic volume] by Automated count: 40.936 fL on 2020-12-26; 45.494 fL on 2015-11-28
  [29463-7] Body Weight: 89.4 kg on 2020-12-26; 87.4 kg on 2019-12-21 (+7 earlier)
  [32207-3] Platelet distribution width [Entitic volume] in Blood by Automated count: 456.47 fL on 2020-12-26; 482.61 fL on 2015-11-28
  [32623-1] Platelet mean volume [Entitic volume] in Blood by Automated count: 10.637 fL on 2020-12-26; 12.145 fL on 2015-11-28
  [32624-9] Which race(s) are you?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [39156-5] Body Mass Index: 25.62 kg/m2 on 2020-12-26; 25.04 kg/m2 on 2019-12-21 (+7 earlier)
  [44261-6] Patient Health Questionnaire 9 item (PHQ-9) total score [Reported]: 15 {score} on 2015-11-28; 18 {score} on 2013-11-16
  [4544-3] Hematocrit [Volume Fraction] of Blood by Automated count: 40.606 % on 2020-12-26; 44.811 % on 2015-11-28
  [54899-0] What language are you most comfortable speaking?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [55758-7] Patient Health Questionnaire 2 item (PHQ-2) total score [Reported]: 2 {score} on 2020-12-26; 0 {score} on 2019-12-21 (+4 earlier)
  [56051-6] Are you Hispanic or Latino?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [56799-0] What address do you live at?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [59576-9] Body mass index (BMI) [Percentile] Per age and gender: 48.55 % on 2013-11-16; 28.047 % on 2012-11-10
  [63512-8] How many family members, including yourself, do you currently live with?: 5 {#} on 2020-12-26; 5 {#} on 2019-12-21 (+7 earlier)
  [63586-2] During the past year, what was the total combined income for you and the family members you live with? This information will help us determine if you are eligible for any benefits.: 182840 /a on 2020-12-26; 182840 /a on 2019-12-21 (+7 earlier)
  [65750-2] Drugs of abuse 5 panel - Urine by Screen method: None  on 2014-11-19; None  on 2014-07-23 (+2 earlier)
  [6690-2] Leukocytes [#/volume] in Blood by Automated count: 4.0158 10*3/uL on 2020-12-26; 9.9524 10*3/uL on 2015-11-28
  [67875-5] What is your current work situation?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [70274-6] Generalized anxiety disorder 7 item (GAD-7) total score [Reported.PHQ]: 0 {score} on 2020-12-26; 7 {score} on 2019-12-21 (+3 earlier)
  [718-7] Hemoglobin [Mass/volume] in Blood: 15.609 g/dL on 2020-12-26; 15.82 g/dL on 2015-11-28
  [71802-3] What is your housing situation today?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [72166-2] Tobacco smoking status NHIS: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [72514-3] Pain severity - 0-10 verbal numeric rating [Score] - Reported: 1 {score} on 2020-12-26; 1 {score} on 2019-12-21 (+7 earlier)
  [75626-2] Total score [AUDIT-C]: 1 {score} on 2020-12-26; 2 {score} on 2015-11-28 (+1 earlier)
  [75893-8] What number best describes your pain on average in the past week?: 4.2646 {score} on 2014-11-19; 5.6347 {score} on 2014-09-21 (+4 earlier)
  [76437-3] What is your main insurance?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [76501-6] In the past year, have you been afraid of your partner or ex-partner?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [76504-0] Total score [HARK]: 0 {score} on 2020-12-26; 0 {score} on 2018-12-15 (+2 earlier)
  [777-3] Platelets [#/volume] in Blood by Automated count: 243.7 10*3/uL on 2020-12-26; 442.71 10*3/uL on 2015-11-28
  [785-6] MCH [Entitic mass] by Automated count: 32.378 pg on 2020-12-26; 31.215 pg on 2015-11-28
  [786-4] MCHC [Mass/volume] by Automated count: 34.221 g/dL on 2020-12-26; 34.296 g/dL on 2015-11-28
  [787-2] MCV [Entitic volume] by Automated count: 92.581 fL on 2020-12-26; 80.051 fL on 2015-11-28
  [789-8] Erythrocytes [#/volume] in Blood by Automated count: 5.385 10*6/uL on 2020-12-26; 4.214 10*6/uL on 2015-11-28
  [82589-3] What is the highest level of school that you have finished?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [82667-7] Total score [DAST-10]: 1 {score} on 2016-12-03; 10 {score} on 2014-11-22 (+1 earlier)
  [8302-2] Body Height: 186.8 cm on 2020-12-26; 186.8 cm on 2019-12-21 (+7 earlier)
  [8310-5] Body temperature: 37.824 Cel on 2018-04-02
  [8462-4] Diastolic Blood Pressure: 86 mm[Hg] on 2020-12-26; 79 mm[Hg] on 2019-12-21 (+7 earlier)
  [8480-6] Systolic Blood Pressure: 110 mm[Hg] on 2020-12-26; 128 mm[Hg] on 2019-12-21 (+7 earlier)
  [85354-9] Blood Pressure: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [8867-4] Heart rate: 73 /min on 2020-12-26; 82 /min on 2019-12-21 (+7 earlier)
  [91145-3] What number best describes how, during the past week, pain has interfered with your enjoyment of life?: 3.9018 {score} on 2014-11-19; 5.1053 {score} on 2014-09-21 (+4 earlier)
  [91146-1] What number best describes how, during the past week, pain has interfered with your general activity?: 1.1907 {score} on 2014-11-19; 1.9392 {score} on 2014-09-21 (+4 earlier)
  [91148-7] Pain intensity, Enjoyment of life, General activity (PEG) 3 item pain scale: None  on 2014-11-19; None  on 2014-09-21 (+4 earlier)
  [9279-1] Respiratory rate: 15 /min on 2020-12-26; 13 /min on 2019-12-21 (+7 earlier)
  [93025-5] Protocol for Responding to and Assessing Patients' Assets, Risks, and Experiences [PRAPARE]: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93026-3] Do you feel physically and emotionally safe where you currently live?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93027-1] Are you a refugee?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93028-9] In the past year, have you spent more than 2 nights in a row in a jail, prison, detention center, or juvenile correctional facility?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93029-7] How often do you see or talk to people that you care about and feel close to (For example: talking to friends on the phone, visiting friends or family, going to church or club meetings)?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93030-5] Has lack of transportation kept you from medical appointments, meetings, work, or from getting things needed for daily living?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93031-3] In the past year, have you or any family members you live with been unable to get any of the following when it was really needed?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93033-9] Are you worried about losing your housing?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93034-7] Have you been discharged from the armed forces of the United States?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93035-4] At any point in the past 2 years, has season or migrant farm work been your or your family's main source of income?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)
  [93038-8] Stress is when someone feels tense, nervous, anxious or can't sleep at night because their mind is troubled. How stressed are you?: None  on 2020-12-26; None  on 2019-12-21 (+7 earlier)

Problem list (29):
  [160903007] Full-time employment (finding): onset 2020-12-26, status active
  [160903007] Full-time employment (finding): onset 2019-12-21, status resolved, resolved 2020-12-26
  [423315002] Limited social contact (finding): onset 2019-12-21, status active
  [73595000] Stress (finding): onset 2019-12-21, status resolved, resolved 2020-12-26
  [424393004] Reports of violence in the environment (finding): onset 2019-12-21, status resolved, resolved 2020-12-26
  [160903007] Full-time employment (finding): onset 2018-12-15, status resolved, resolved 2019-12-21
  [195662009] Acute viral pharyngitis (disorder): onset 2018-04-02, status resolved, resolved 2018-04-10
  [160903007] Full-time employment (finding): onset 2017-12-09, status resolved, resolved 2018-12-15
  [422650009] Social isolation (finding): onset 2017-12-09, status resolved, resolved 2018-12-15
  [424393004] Reports of violence in the environment (finding): onset 2017-12-09, status resolved, resolved 2018-12-15
  [160903007] Full-time employment (finding): onset 2016-12-03, status resolved, resolved 2017-12-09
  [446654005] Refugee (person): onset 2016-12-03, status active
  [160903007] Full-time employment (finding): onset 2015-11-28, status resolved, resolved 2016-12-03
  [423315002] Limited social contact (finding): onset 2015-11-28, status resolved, resolved 2016-12-03
  [444814009] Viral sinusitis (disorder): onset 2015-09-04, status resolved, resolved 2015-09-12
  [160903007] Full-time employment (finding): onset 2014-11-22, status resolved, resolved 2015-11-28
  [361055000] Misuses drugs (finding): onset 2014-11-22, status resolved, resolved 2016-12-03
  [65363002] Otitis media: onset 2014-04-05, status resolved, resolved 2014-11-22
  [278860009] Chronic low back pain (finding): onset 2014-02-03, status active
  [1121000119107] Chronic neck pain (finding): onset 2014-02-03, status active
  [160903007] Full-time employment (finding): onset 2013-11-16, status resolved, resolved 2014-11-22
  [370247008] Facial laceration: onset 2012-11-18, status resolved, resolved 2012-12-07
  [105531004] Housing unsatisfactory (finding): onset 2012-11-10, status active
  [224299000] Received higher education (finding): onset 2012-11-10, status active
  [741062008] Not in labor force (finding): onset 2012-11-10, status resolved, resolved 2013-11-16
  [423315002] Limited social contact (finding): onset 2012-11-10, status resolved, resolved 2014-11-22
  [73595000] Stress (finding): onset 2012-11-10, status resolved, resolved 2013-11-16
  [424393004] Reports of violence in the environment (finding): onset 2012-11-10, status resolved, resolved 2013-11-16
  [706893006] Victim of intimate partner abuse (finding): onset 2012-11-10, status resolved, resolved 2013-11-16

Medication orders (41):
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2020-12-26, active
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2020-12-26, active
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2020-12-26, active
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2020-12-26, active
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2019-12-21, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2019-12-21, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2019-12-21, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2019-12-21, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2018-12-15, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2018-12-15, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2018-12-15, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2018-12-15, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2017-12-09, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2017-12-09, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2017-12-09, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2017-12-09, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2016-12-03, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2016-12-03, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2016-12-03, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2016-12-03, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2015-11-28, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2015-11-28, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2015-11-28, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2015-11-28, stopped
  [562251] Amoxicillin 250 MG / Clavulanate 125 MG Oral Tablet: 2015-09-04, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2014-11-22, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2014-11-22, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2014-11-22, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2014-11-22, stopped
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2014-11-22, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2014-11-22, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2014-11-22, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2014-11-22, stopped
  [856987] Acetaminophen 300 MG / Hydrocodone Bitartrate 5 MG Oral Tablet: 2014-11-19, active
  [993770] Acetaminophen 300 MG / Codeine Phosphate 15 MG Oral Tablet: 2014-09-21, stopped
  [1049625] Acetaminophen 325 MG / Oxycodone Hydrochloride 10 MG Oral Tablet [Percocet]: 2014-05-21, stopped
  [308182] Amoxicillin 250 MG Oral Capsule: 2014-04-05, stopped
  [313782] Acetaminophen 325 MG Oral Tablet: 2014-04-05, stopped
  [835603] tramadol hydrochloride 50 MG Oral Tablet: 2014-03-22, stopped
  [209387] Acetaminophen 325 MG Oral Tablet [Tylenol]: 2014-02-03, stopped
  [313782] Acetaminophen 325 MG Oral Tablet: 2012-11-18, stopped

Procedures (49):
  [710824005] Assessment of health and social care needs (procedure): 2020-12-26
  [710841007] Assessment of anxiety (procedure): 2020-12-26
  [866148006] Screening for domestic abuse (procedure): 2020-12-26
  [171207006] Depression screening (procedure): 2020-12-26
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2020-12-26
  [428211000124100] Assessment of substance use (procedure): 2020-12-26
  [763302001] Assessment using Alcohol Use Disorders Identification Test - Consumption (procedure): 2020-12-26
  [710824005] Assessment of health and social care needs (procedure): 2019-12-21
  [710841007] Assessment of anxiety (procedure): 2019-12-21
  [171207006] Depression screening (procedure): 2019-12-21
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2019-12-21
  [710824005] Assessment of health and social care needs (procedure): 2018-12-15
  [866148006] Screening for domestic abuse (procedure): 2018-12-15
  [171207006] Depression screening (procedure): 2018-12-15
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2018-12-15
  [117015009] Throat culture (procedure): 2018-04-02
  [710824005] Assessment of health and social care needs (procedure): 2017-12-09
  [710841007] Assessment of anxiety (procedure): 2017-12-09
  [710824005] Assessment of health and social care needs (procedure): 2016-12-03
  [428211000124100] Assessment of substance use (procedure): 2016-12-03
  [713106006] Screening for drug abuse (procedure): 2016-12-03
  [710824005] Assessment of health and social care needs (procedure): 2015-11-28
  [430193006] Medication Reconciliation (procedure): 2015-11-28
  [171207006] Depression screening (procedure): 2015-11-28
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2015-11-28
  [715252007] Depression screening using Patient Health Questionnaire Nine Item score (procedure): 2015-11-28
  [428211000124100] Assessment of substance use (procedure): 2015-11-28
  [763302001] Assessment using Alcohol Use Disorders Identification Test - Consumption (procedure): 2015-11-28
  [710824005] Assessment of health and social care needs (procedure): 2014-11-22
  [710841007] Assessment of anxiety (procedure): 2014-11-22
  [866148006] Screening for domestic abuse (procedure): 2014-11-22
  [171207006] Depression screening (procedure): 2014-11-22
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2014-11-22
  [428211000124100] Assessment of substance use (procedure): 2014-11-22
  [713106006] Screening for drug abuse (procedure): 2014-11-22
  [710824005] Assessment of health and social care needs (procedure): 2013-11-16
  [171207006] Depression screening (procedure): 2013-11-16
  [454711000124102] Depression screening using Patient Health Questionnaire Two-Item score (procedure): 2013-11-16
  [715252007] Depression screening using Patient Health Questionnaire Nine Item score (procedure): 2013-11-16
  [428211000124100] Assessment of substance use (procedure): 2013-11-16
  [763302001] Assessment using Alcohol Use Disorders Identification Test - Consumption (procedure): 2013-11-16
  [288086009] Suture open wound: 2012-11-18
  [384700001] Injection of tetanus antitoxin: 2012-11-18
  [710824005] Assessment of health and social care needs (procedure): 2012-11-10
  [430193006] Medication Reconciliation (procedure): 2012-11-10
  [710841007] Assessment of anxiety (procedure): 2012-11-10
  [866148006] Screening for domestic abuse (procedure): 2012-11-10
  [428211000124100] Assessment of substance use (procedure): 2012-11-10
  [713106006] Screening for drug abuse (procedure): 2012-11-10

Return JSON only:
{"label": "MEETS" | "FAILS" | "INDETERMINATE",
  "reason": "one sentence naming the specific value or the specific absence"}

```

### 4. llm_response (openai, 26 tok, 40.605s)

```
{
  "label": "MEETS",
  "reason": "Patient age is 27 years, which meets the ≥20 years requirement."
}
```

### 5. final

```json
{
 "label": "MEETS",
 "reason": "Patient age is 27 years, which meets the \u226520 years requirement."
}
```

