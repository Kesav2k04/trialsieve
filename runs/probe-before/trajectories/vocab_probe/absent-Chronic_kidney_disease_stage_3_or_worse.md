### 1. instructions (prompt grounder-v1)

```
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

Expand this clinical concept into concrete searchable names.

Concept: {concept}
Record domain: {domain}

For a drug class, list the generic ingredient names that belong to the class.
For a diagnosis, list the specific condition names, including the common
sub-types a record might code instead of the general term.
For a laboratory test, list the names and common synonyms of the measurement.

List what belongs to the concept in general clinical practice. Do NOT try to
guess what this particular site happens to record; that is looked up separately.

Return JSON only:
{{"names": ["empagliflozin", "dapagliflozin"], "note": "one short line"}}

Give between 1 and 15 names.

---

You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

Concept: {concept}
Record domain: {domain}
Meaning required: {intent}

Candidate entries from this site's vocabulary:
{candidates}

Select every candidate that genuinely represents the concept. Judge by what the
entry means, not by whether the words look similar. A different measurement that
shares a word is not a match: "Respiratory rate" is not a glomerular filtration
rate, and "Chronic sinusitis" is not chronic kidney disease.

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{{"codes": ["4548-4"], "rejected": [{{"code": "718-7", "why": "different analyte"}}],
  "confidence": "high"}}
```

### 2. input

```json
{
 "concept": "Chronic kidney disease stage 3 or worse",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `31f0b196bb8afe15`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Chronic kidney disease stage 3 or worse
Record domain: condition

For a drug class, list the generic ingredient names that belong to the class.
For a diagnosis, list the specific condition names, including the common
sub-types a record might code instead of the general term.
For a laboratory test, list the names and common synonyms of the measurement.

List what belongs to the concept in general clinical practice. Do NOT try to
guess what this particular site happens to record; that is looked up separately.

Return JSON only:
{"names": ["empagliflozin", "dapagliflozin"], "note": "one short line"}

Give between 1 and 15 names.
```

### 4. llm_response (openai, 149 tok, 252.434s)

```
```json
{
  "names": [
    "Chronic kidney disease, stage 3",
    "Chronic kidney disease, stage 3a",
    "Chronic kidney disease, stage 3b",
    "Chronic kidney disease, stage 4",
    "Chronic kidney disease, stage 5",
    "End stage renal disease",
    "Chronic renal failure, stage 3",
    "Chronic renal failure, stage 4",
    "Chronic renal failure, stage 5",
    "Severe chronic kidney disease",
    "Moderate chronic kidney disease",
    "Chronic kidney disease requiring chronic dialysis"
  ],
  "note": "Encompasses CKD stages 3 (3a/3b), 4, 5, and end-stage renal disease terms."
}
```
```

### 5. transport_retry

```json
{
 "attempt": 1,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 6. transport_retry

```json
{
 "attempt": 2,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 7. transport_retry

```json
{
 "attempt": 3,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 8. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Chronic kidney disease, stage 3",
  "Chronic kidney disease, stage 3a",
  "Chronic kidney disease, stage 3b",
  "Chronic kidney disease, stage 4",
  "Chronic kidney disease, stage 5",
  "End stage renal disease",
  "Chronic renal failure, stage 3",
  "Chronic renal failure, stage 4",
  "Chronic renal failure, stage 5",
  "Severe chronic kidney disease",
  "Moderate chronic kidney disease",
  "Chronic kidney disease requiring chronic dialysis"
 ]
}
```

### 9. tool_result `terminology.search_any`

```json
[
 {
  "code": "431855005",
  "display": "Chronic kidney disease stage 1 (disorder)",
  "domain": "condition",
  "n_resources": 10
 },
 {
  "code": "431856006",
  "display": "Chronic kidney disease stage 2 (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "127013003",
  "display": "Diabetic renal disease (disorder)",
  "domain": "condition",
  "n_resources": 11
 },
 {
  "code": "88805009",
  "display": "Chronic congestive heart failure (disorder)",
  "domain": "condition",
  "n_resources": 10
 },
 {
  "code": "40055000",
  "display": "Chronic sinusitis (disorder)",
  "domain": "condition",
  "n_resources": 88
 },
 {
  "code": "82423001",
  "display": "Chronic pain",
  "domain": "condition",
  "n_resources": 22
 },
 {
  "code": "40095003",
  "display": "Injury of kidney (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "80583007",
  "display": "Severe anxiety (panic) (finding",
  "domain": "condition",
  "n_resources": 59
 },
 {
  "code": "1121000119107",
  "display": "Chronic neck pain (finding)",
  "domain": "condition",
  "n_resources": 54
 },
 {
  "code": "53741008",
  "display": "Coronary Heart Disease",
  "domain": "condition",
  "n_resources": 25
 },
 {
  "code": "26929004",
  "display": "Alzheimer's disease (disorder)",
  "domain": "condition",
  "n_resources": 17
 },
 {
  "code": "185086009",
  "display": "Chronic obstructive bronchitis (disorder)",
  "domain": "condition",
  "n_resources": 2
 }
]
```

### 10. llm_request -> gemini-3.7-flash-medium  cassette `084ee6326a37ea72`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Chronic kidney disease stage 3 or worse
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
          88805009  Chronic congestive heart failure (disorder)   (in 10 resources)
          40055000  Chronic sinusitis (disorder)   (in 88 resources)
          82423001  Chronic pain   (in 22 resources)
          40095003  Injury of kidney (disorder)   (in 1 resources)
          80583007  Severe anxiety (panic) (finding   (in 59 resources)
     1121000119107  Chronic neck pain (finding)   (in 54 resources)
          53741008  Coronary Heart Disease   (in 25 resources)
          26929004  Alzheimer's disease (disorder)   (in 17 resources)
         185086009  Chronic obstructive bronchitis (disorder)   (in 2 resources)

Select every candidate that genuinely represents the concept. Judge by what the
entry means, not by whether the words look similar. A different measurement that
shares a word is not a match: "Respiratory rate" is not a glomerular filtration
rate, and "Chronic sinusitis" is not chronic kidney disease.

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{"codes": ["4548-4"], "rejected": [{"code": "718-7", "why": "different analyte"}],
  "confidence": "high"}
```

### 11. llm_response (openai, 335 tok, 58.756s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "431855005",
      "why": "Chronic kidney disease stage 1 is milder than stage 3"
    },
    {
      "code": "431856006",
      "why": "Chronic kidney disease stage 2 is milder than stage 3"
    },
    {
      "code": "127013003",
      "why": "Diabetic renal disease does not specify or require stage 3 or worse"
    },
    {
      "code": "88805009",
      "why": "Cardiac condition, not chronic kidney disease"
    },
    {
      "code": "40055000",
      "why": "Sinus condition, not chronic kidney disease"
    },
    {
      "code": "82423001",
      "why": "Pain condition, not chronic kidney disease"
    },
    {
      "code": "40095003",
      "why": "Acute/traumatic kidney injury, not chronic kidney disease stage 3 or worse"
    },
    {
      "code": "80583007",
      "why": "Psychiatric/anxiety condition, not kidney disease"
    },
    {
      "code": "1121000119107",
      "why": "Musculoskeletal condition, not kidney disease"
    },
    {
      "code": "53741008",
      "why": "Coronary artery disease, not kidney disease"
    },
    {
      "code": "26929004",
      "why": "Neurological disorder, not kidney disease"
    },
    {
      "code": "185086009",
      "why": "Respiratory condition, not kidney disease"
    }
  ],
  "confidence": "high"
}
```
```

### 12. final

```json
{
 "codes": [],
 "concept": "Chronic kidney disease stage 3 or worse",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Chronic kidney disease, stage 3",
  "Chronic kidney disease, stage 3a",
  "Chronic kidney disease, stage 3b",
  "Chronic kidney disease, stage 4",
  "Chronic kidney disease, stage 5",
  "End stage renal disease",
  "Chronic renal failure, stage 3",
  "Chronic renal failure, stage 4",
  "Chronic renal failure, stage 5",
  "Severe chronic kidney disease",
  "Moderate chronic kidney disease",
  "Chronic kidney disease requiring chronic dialysis"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "431855005",
   "why": "Chronic kidney disease stage 1 is milder than stage 3"
  },
  {
   "code": "431856006",
   "why": "Chronic kidney disease stage 2 is milder than stage 3"
  },
  {
   "code": "127013003",
   "why": "Diabetic renal disease does not specify or require stage 3 or worse"
  },
  {
   "code": "88805009",
   "why": "Cardiac condition, not chronic kidney disease"
  },
  {
   "code": "40055000",
   "why": "Sinus condition, not chronic kidney disease"
  },
  {
   "code": "82423001",
   "why": "Pain condition, not chronic kidney disease"
  },
  {
   "code": "40095003",
   "why": "Acute/traumatic kidney injury, not chronic kidney disease stage 3 or worse"
  },
  {
   "code": "80583007",
   "why": "Psychiatric/anxiety condition, not kidney disease"
  },
  {
   "code": "1121000119107",
   "why": "Musculoskeletal condition, not kidney disease"
  },
  {
   "code": "53741008",
   "why": "Coronary artery disease, not kidney disease"
  },
  {
   "code": "26929004",
   "why": "Neurological disorder, not kidney disease"
  },
  {
   "code": "185086009",
   "why": "Respir
```

