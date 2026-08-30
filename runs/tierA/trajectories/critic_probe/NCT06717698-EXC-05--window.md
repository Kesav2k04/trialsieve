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
 "criterion_id": "NCT06717698-EXC-05",
 "kind": "exclusion",
 "source_text": "Receiving immunosuppressive therapy for primary or secondary renal disease within 6 months prior to screening."
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `4e58ab7d0cea1928`

```
[system]
You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts.

[user]
Review this compiled criterion.

CRITERION (exclusion):
  Receiving immunosuppressive therapy for primary or secondary renal disease within 6 months prior to screening.

COMPILED PREDICATE:
{
 "op": "and",
 "args": [
  {
   "op": "exists",
   "query": {
    "domain": "medication",
    "codes": [
     "105585",
     "1734919",
     "312615",
     "312617"
    ],
    "within_days": 732,
    "absent_means": "unknown"
   }
  },
  {
   "op": "exists",
   "query": {
    "domain": "condition",
    "codes": [
     "127013003",
     "431855005",
     "431856006",
     "45816000"
    ],
    "within_days": null,
    "absent_means": "unknown"
   }
  }
 ]
}

CODES AVAILABLE (you may only use these):
105585, 127013003, 1734919, 312615, 312617, 431855005, 431856006, 45816000

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

### 4. llm_response (cassette, 201 tok, 19.870s)

```
```json
{
  "verdict": "REVISE",
  "findings": [
    {
      "issue": "The medication lookback window is set to 732 days (2 years) instead of 183 days (6 months).",
      "kind": "window",
      "severity": "high"
    }
  ],
  "counterexample": {
    "patient": {
      "age": 55,
      "sex": "female",
      "observations": [],
      "conditions": [
        {
          "code": "127013003",
          "days_ago": 300
        }
      ],
      "medications": [
        {
          "code": "105585",
          "days_ago": 300,
          "status": "active"
        }
      ],
      "procedures": []
    },
    "expected_truth": "FALSE",
    "why": "The patient received immunosuppressive therapy 300 days ago, which is outside the 6-month (183-day) window specified by the exclusion criterion."
  }
}
```
```

### 5. tool_call `execute_counterexample`

```json
{
 "expected_truth": "FALSE",
 "patient": {
  "age": 55,
  "conditions": [
   {
    "code": "127013003",
    "days_ago": 300
   }
  ],
  "medications": [
   {
    "code": "105585",
    "days_ago": 300,
    "status": "active"
   }
  ],
  "observations": [],
  "procedures": [],
  "sex": "female"
 }
}
```

### 6. tool_result `execute_counterexample`

```json
{
 "actual": "TRUE",
 "confirmed": true,
 "engine_reason": "every conjunct holds",
 "expected": "FALSE"
}
```

### 7. critic_finding

```json
{
 "counterexample": {
  "expected_truth": "FALSE",
  "patient": {
   "age": 55,
   "conditions": [
    {
     "code": "127013003",
     "days_ago": 300
    }
   ],
   "medications": [
    {
     "code": "105585",
     "days_ago": 300,
     "status": "active"
    }
   ],
   "observations": [],
   "procedures": [],
   "sex": "female"
  },
  "why": "The patient received immunosuppressive therapy 300 days ago, which is outside the 6-month (183-day) window specified by the exclusion criterion."
 },
 "finding": "The medication lookback window is set to 732 days (2 years) instead of 183 days (6 months).",
 "verdict": "CONFIRMED"
}
```

### 8. final

```json
{
 "executed": {
  "actual": "TRUE",
  "confirmed": true,
  "engine_reason": "every conjunct holds",
  "expected": "FALSE"
 },
 "n_findings": 1,
 "verdict": "REVISE"
}
```

