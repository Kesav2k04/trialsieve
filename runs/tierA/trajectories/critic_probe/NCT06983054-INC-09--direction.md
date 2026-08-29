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
 "criterion_id": "NCT06983054-INC-09",
 "kind": "inclusion",
 "source_text": "UACR < 30 mg/mmol"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `b873d9f295e0d76b`

```
[system]
You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts.

[user]
Review this compiled criterion.

CRITERION (inclusion):
  UACR < 30 mg/mmol

COMPILED PREDICATE:
{
 "op": "not",
 "arg": {
  "op": "compare",
  "cmp": "<",
  "left": {
   "val": "observation",
   "codes": [
    "14959-1"
   ],
   "unit": "mg/mmol",
   "agg": "latest",
   "within_days": null
  },
  "right": {
   "val": "literal",
   "number": 30,
   "unit": "mg/mmol"
  }
 }
}

CODES AVAILABLE (you may only use these):
14959-1

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

### 4. llm_response (cassette, 195 tok, 21.572s)

```
```json
{
  "verdict": "REVISE",
  "findings": [
    {
      "issue": "The predicate incorrectly wraps the comparison in a 'not' operator for an inclusion criterion, causing patients with UACR < 30 mg/mmol to evaluate to FALSE instead of TRUE.",
      "kind": "direction",
      "severity": "high"
    }
  ],
  "counterexample": {
    "patient": {
      "age": 55,
      "sex": "female",
      "observations": [
        {
          "code": "14959-1",
          "value": 20,
          "unit": "mg/mmol",
          "days_ago": 14
        }
      ],
      "conditions": [],
      "medications": [],
      "procedures": []
    },
    "expected_truth": "TRUE",
    "why": "The patient has a UACR of 20 mg/mmol, which satisfies the inclusion criterion of UACR < 30 mg/mmol."
  }
}
```
```

### 5. tool_call `execute_counterexample`

```json
{
 "expected_truth": "TRUE",
 "patient": {
  "age": 55,
  "conditions": [],
  "medications": [],
  "observations": [
   {
    "code": "14959-1",
    "days_ago": 14,
    "unit": "mg/mmol",
    "value": 20
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
 "engine_reason": "negation of a TRUE sub-result",
 "expected": "TRUE"
}
```

### 7. critic_finding

```json
{
 "counterexample": {
  "expected_truth": "TRUE",
  "patient": {
   "age": 55,
   "conditions": [],
   "medications": [],
   "observations": [
    {
     "code": "14959-1",
     "days_ago": 14,
     "unit": "mg/mmol",
     "value": 20
    }
   ],
   "procedures": [],
   "sex": "female"
  },
  "why": "The patient has a UACR of 20 mg/mmol, which satisfies the inclusion criterion of UACR < 30 mg/mmol."
 },
 "finding": "The predicate incorrectly wraps the comparison in a 'not' operator for an inclusion criterion, causing patients with UACR < 30 mg/mmol to evaluate to FALSE instead of TRUE.",
 "verdict": "CONFIRMED"
}
```

### 8. final

```json
{
 "executed": {
  "actual": "FALSE",
  "confirmed": true,
  "engine_reason": "negation of a TRUE sub-result",
  "expected": "TRUE"
 },
 "n_findings": 1,
 "verdict": "REVISE"
}
```

