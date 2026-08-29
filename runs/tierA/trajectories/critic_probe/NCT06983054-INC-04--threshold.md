### 1. instructions (prompt critic-v1)

```
You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts.

Review this compiled criterion.

CRITERION ({kind}):
  {text}

COMPILED PREDICATE:
{expr}

CODES AVAILABLE (you may only use these):
{codes}

Look specifically for:
  1. Window errors. Is `within_days` right, and does an event just inside or just
     outside the window behave correctly? "within 6 months" is 183 days.
  2. Boundary errors. Should the comparison be > or >=? Does the criterion say
     "between 6.5 and 10" (inclusive) or "above 6.5"?
  3. Direction errors. For an EXCLUSION, the predicate must be TRUE for a patient
     who should be EXCLUDED. A predicate that is true for eligible patients is
     inverted.
  4. Absence errors. Is any `absent_means` set to "false" for something that
     could easily have happened at another hospital, or that is acute or recent?
     Ruling a patient out because their record is silent is the worst failure
     available here.
  5. Missing or added conditions. Does the predicate check everything the
     criterion states, and nothing it does not?

If you find a problem, construct a patient that demonstrates it and say what
truth value the CRITERION TEXT should take for that patient.

Truth values: TRUE means the patient satisfies the criterion text, FALSE means
they do not, UNKNOWN means the record shown cannot settle it.

Patient facts use days before the screening date. `days_ago: 30` is a month ago.
Include only facts you want the record to contain; anything you omit is absent
from the record.

Return JSON only:

{{"verdict": "OK" | "REVISE",
  "findings": [{{"issue": "one sentence", "kind": "window|boundary|direction|absence|scope",
                 "severity": "high|medium|low"}}],
  "counterexample": {{
     "patient": {{"age": 62, "sex": "female",
                  "observations": [{{"code":"4548-4","value":7.2,"unit":"%","days_ago":30}}],
                  "conditions": [{{"code":"22298006","days_ago":200}}],
                  "medications": [{{"code":"860975","days_ago":20,"status":"active"}}],
                  "procedures": []}},
     "expected_truth": "TRUE|FALSE|UNKNOWN",
     "why": "one sentence explaining what the criterion text says for this patient"}}}}

When the predicate is faithful, return verdict "OK", an empty findings list, and
counterexample null. Do not invent a problem to look useful.
```

### 2. input

```json
{
 "criterion_id": "NCT06983054-INC-04",
 "kind": "inclusion",
 "source_text": "Overweight or obese with BMI: >25 kg/m2"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `9c7080325221a010`

```
[system]
You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts.

[user]
Review this compiled criterion.

CRITERION (inclusion):
  Overweight or obese with BMI: >25 kg/m2

COMPILED PREDICATE:
{
 "op": "compare",
 "cmp": ">",
 "left": {
  "val": "derived",
  "name": "bmi",
  "within_days": null
 },
 "right": {
  "val": "literal",
  "number": 50.0,
  "unit": "kg/m2"
 }
}

CODES AVAILABLE (you may only use these):
39156-5

Look specifically for:
  1. Window errors. Is `within_days` right, and does an event just inside or just
     outside the window behave correctly? "within 6 months" is 183 days.
  2. Boundary errors. Should the comparison be > or >=? Does the criterion say
     "between 6.5 and 10" (inclusive) or "above 6.5"?
  3. Direction errors. For an EXCLUSION, the predicate must be TRUE for a patient
     who should be EXCLUDED. A predicate that is true for eligible patients is
     inverted.
  4. Absence errors. Is any `absent_means` set to "false" for something that
     could easily have happened at another hospital, or that is acute or recent?
     Ruling a patient out because their record is silent is the worst failure
     available here.
  5. Missing or added conditions. Does the predicate check everything the
     criterion states, and nothing it does not?

If you find a problem, construct a patient that demonstrates it and say what
truth value the CRITERION TEXT should take for that patient.

Truth values: TRUE means the patient satisfies the criterion text, FALSE means
they do not, UNKNOWN means the record shown cannot settle it.

Patient facts use days before the screening date. `days_ago: 30` is a month ago.
Include only facts you want the record to contain; anything you omit is absent
from the record.

Return JSON only:

{"verdict": "OK" | "REVISE",
  "findings": [{"issue": "one sentence", "kind": "window|boundary|direction|absence|scope",
                 "severity": "high|medium|low"}],
  "counterexample": {
     "patient": {"age": 62, "sex": "female",
                  "observations": [{"code":"4548-4","value":7.2,"unit":"%","days_ago":30}],
                  "conditions": [{"code":"22298006","days_ago":200}],
                  "medications": [{"code":"860975","days_ago":20,"status":"active"}],
                  "procedures": []},
     "expected_truth": "TRUE|FALSE|UNKNOWN",
     "why": "one sentence explaining what the criterion text says for this patient"}}

When the predicate is faithful, return verdict "OK", an empty findings list, and
counterexample null. Do not invent a problem to look useful.
```

### 4. llm_response (openai, 196 tok, 43.10185360908508s)

```
```json
{
  "verdict": "REVISE",
  "findings": [
    {
      "issue": "The predicate sets the BMI threshold to 50.0 kg/m2 instead of 25.0 kg/m2 specified in the criterion text.",
      "kind": "boundary",
      "severity": "high"
    }
  ],
  "counterexample": {
    "patient": {
      "age": 45,
      "sex": "female",
      "observations": [
        {
          "code": "39156-5",
          "value": 30.0,
          "unit": "kg/m2",
          "days_ago": 10
        }
      ],
      "conditions": [],
      "medications": [],
      "procedures": []
    },
    "expected_truth": "TRUE",
    "why": "The patient's BMI is 30 kg/m2, which is greater than 25 kg/m2 and satisfies the inclusion criterion, but the predicate evaluates to FALSE due to the 50.0 kg/m2 threshold."
  }
}
```
```

### 5. tool_call `execute_counterexample`

```json
{
 "expected_truth": "TRUE",
 "patient": {
  "age": 45,
  "conditions": [],
  "medications": [],
  "observations": [
   {
    "code": "39156-5",
    "days_ago": 10,
    "unit": "kg/m2",
    "value": 30.0
   }
  ],
  "procedures": [],
  "sex": "female"
 }
}
```

### 6. tool_result `execute_counterexample`

```json
{
 "actual": "FALSE",
 "confirmed": true,
 "engine_reason": "30 > 50 kg/m2 is False",
 "expected": "TRUE"
}
```

### 7. critic_finding

```json
{
 "counterexample": {
  "expected_truth": "TRUE",
  "patient": {
   "age": 45,
   "conditions": [],
   "medications": [],
   "observations": [
    {
     "code": "39156-5",
     "days_ago": 10,
     "unit": "kg/m2",
     "value": 30.0
    }
   ],
   "procedures": [],
   "sex": "female"
  },
  "why": "The patient's BMI is 30 kg/m2, which is greater than 25 kg/m2 and satisfies the inclusion criterion, but the predicate evaluates to FALSE due to the 50.0 kg/m2 threshold."
 },
 "finding": "The predicate sets the BMI threshold to 50.0 kg/m2 instead of 25.0 kg/m2 specified in the criterion text.",
 "verdict": "CONFIRMED"
}
```

### 8. final

```json
{
 "executed": {
  "actual": "FALSE",
  "confirmed": true,
  "engine_reason": "30 > 50 kg/m2 is False",
  "expected": "TRUE"
 },
 "n_findings": 1,
 "verdict": "REVISE"
}
```

