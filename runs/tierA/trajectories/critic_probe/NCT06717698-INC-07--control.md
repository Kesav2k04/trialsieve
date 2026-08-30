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
 "criterion_id": "NCT06717698-INC-07",
 "kind": "inclusion",
 "source_text": "Diagnosed with type 2 diabetes mellitus greater than or equal to 180 days before screening, or not diagnosed with type 2 diabetes mellitus."
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `158d45b794ef85f2`

```
[system]
You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts.

[user]
Review this compiled criterion.

CRITERION (inclusion):
  Diagnosed with type 2 diabetes mellitus greater than or equal to 180 days before screening, or not diagnosed with type 2 diabetes mellitus.

COMPILED PREDICATE:
{
 "op": "not",
 "arg": {
  "op": "exists",
  "query": {
   "domain": "condition",
   "codes": [],
   "broader_codes": [
    "44054006"
   ],
   "within_days": 180,
   "active_only": false,
   "absent_means": "unknown"
  }
 }
}

CODES AVAILABLE (you may only use these):
(age and sex only)

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

### 4. llm_response (openai, 167 tok, 28.292s)

```
```json
{
  "verdict": "REVISE",
  "findings": [
    {
      "issue": "The query sets absent_means to 'unknown' inside a NOT operator, preventing patients without a type 2 diabetes diagnosis from evaluating to TRUE.",
      "kind": "absence",
      "severity": "high"
    }
  ],
  "counterexample": {
    "patient": {
      "age": 50,
      "sex": "female",
      "observations": [],
      "conditions": [],
      "medications": [],
      "procedures": []
    },
    "expected_truth": "TRUE",
    "why": "The patient has no diagnosis of type 2 diabetes mellitus, directly satisfying the 'not diagnosed with type 2 diabetes mellitus' branch of the criterion."
  }
}
```
```

### 5. tool_call `execute_counterexample`

```json
{
 "expected_truth": "TRUE",
 "patient": {
  "age": 50,
  "conditions": [],
  "medications": [],
  "observations": [],
  "procedures": [],
  "sex": "female"
 }
}
```

### 6. tool_result `execute_counterexample`

```json
{
 "actual": "UNKNOWN",
 "confirmed": true,
 "engine_reason": "negation of a UNKNOWN sub-result",
 "expected": "TRUE"
}
```

### 7. critic_finding

```json
{
 "counterexample": {
  "expected_truth": "TRUE",
  "patient": {
   "age": 50,
   "conditions": [],
   "medications": [],
   "observations": [],
   "procedures": [],
   "sex": "female"
  },
  "why": "The patient has no diagnosis of type 2 diabetes mellitus, directly satisfying the 'not diagnosed with type 2 diabetes mellitus' branch of the criterion."
 },
 "finding": "The query sets absent_means to 'unknown' inside a NOT operator, preventing patients without a type 2 diabetes diagnosis from evaluating to TRUE.",
 "verdict": "CONFIRMED"
}
```

### 8. final

```json
{
 "executed": {
  "actual": "UNKNOWN",
  "confirmed": true,
  "engine_reason": "negation of a UNKNOWN sub-result",
  "expected": "TRUE"
 },
 "n_findings": 1,
 "verdict": "REVISE"
}
```

