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
 "concept": "Obesity",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `97f6cdce83e7bf11`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Obesity
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

### 4. llm_response (cassette, 118 tok, 18.560s)

```
{
  "names": [
    "Obesity",
    "Morbid obesity",
    "Severe obesity",
    "Class 1 obesity",
    "Class 2 obesity",
    "Class 3 obesity",
    "Extreme obesity",
    "Obesity due to excess calories",
    "Exogenous obesity",
    "Drug-induced obesity",
    "Childhood obesity",
    "Pediatric obesity",
    "Familial obesity"
  ],
  "note": "Includes standard diagnostic terms, severity classes (Class 1-3/morbid), etiologic variants, and pediatric presentations."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Obesity",
  "Morbid obesity",
  "Severe obesity",
  "Class 1 obesity",
  "Class 2 obesity",
  "Class 3 obesity",
  "Extreme obesity",
  "Obesity due to excess calories",
  "Exogenous obesity",
  "Drug-induced obesity",
  "Childhood obesity",
  "Pediatric obesity",
  "Familial obesity"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "162864005",
  "display": "Body mass index 30+ - obesity (finding)",
  "domain": "condition",
  "n_resources": 209
 },
 {
  "code": "233678006",
  "display": "Childhood asthma",
  "domain": "condition",
  "n_resources": 17
 },
 {
  "code": "80583007",
  "display": "Severe anxiety (panic) (finding",
  "domain": "condition",
  "n_resources": 59
 },
 {
  "code": "408512008",
  "display": "Body mass index 40+ - severely obese (finding)",
  "domain": "condition",
  "n_resources": 5
 },
 {
  "code": "230265002",
  "display": "Familial Alzheimer's disease of early onset (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "55680006",
  "display": "Drug overdose",
  "domain": "condition",
  "n_resources": 21
 },
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
  "code": "368581000119106",
  "display": "Neuropathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 9
 },
 {
  "code": "90781000119102",
  "display": "Microalbuminuria due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "1551000119108",
  "display": "Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 5
 },
 {
  
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `7f7978920fac79f8`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Obesity
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         162864005  Body mass index 30+ - obesity (finding)   (in 209 resources)
         233678006  Childhood asthma   (in 17 resources)
          80583007  Severe anxiety (panic) (finding   (in 59 resources)
         408512008  Body mass index 40+ - severely obese (finding)   (in 5 resources)
         230265002  Familial Alzheimer's disease of early onset (disorder)   (in 1 resources)
          55680006  Drug overdose   (in 21 resources)
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
         424132000  Non-small cell carcinoma of lung, TNM stage 1 (disorder)   (in 5 resources)

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

### 8. llm_response (cassette, 281 tok, 20.843s)

```
```json
{
  "codes": [
    "162864005",
    "408512008"
  ],
  "rejected": [
    {
      "code": "233678006",
      "why": "respiratory condition (asthma), not obesity"
    },
    {
      "code": "80583007",
      "why": "psychiatric condition (anxiety/panic), not obesity"
    },
    {
      "code": "230265002",
      "why": "neurodegenerative disorder (Alzheimer's disease), not obesity"
    },
    {
      "code": "55680006",
      "why": "acute toxicological event (drug overdose), not obesity"
    },
    {
      "code": "431855005",
      "why": "renal disorder (CKD stage 1), not obesity"
    },
    {
      "code": "431856006",
      "why": "renal disorder (CKD stage 2), not obesity"
    },
    {
      "code": "368581000119106",
      "why": "diabetic neuropathy, not obesity"
    },
    {
      "code": "90781000119102",
      "why": "diabetic microalbuminuria, not obesity"
    },
    {
      "code": "1551000119108",
      "why": "diabetic retinopathy, not obesity"
    },
    {
      "code": "424132000",
      "why": "oncologic disorder (lung carcinoma), not obesity"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "codes": [
  "162864005",
  "408512008"
 ],
 "concept": "Obesity",
 "confidence": "high",
 "displays": [
  "Body mass index 30+ - obesity (finding)",
  "Body mass index 40+ - severely obese (finding)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Obesity",
  "Morbid obesity",
  "Severe obesity",
  "Class 1 obesity",
  "Class 2 obesity",
  "Class 3 obesity",
  "Extreme obesity",
  "Obesity due to excess calories",
  "Exogenous obesity",
  "Drug-induced obesity",
  "Childhood obesity",
  "Pediatric obesity",
  "Familial obesity"
 ],
 "matched_names": [
  "obesity"
 ],
 "reason": "2 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Childhood obesity",
  "Class 1 obesity",
  "Class 2 obesity",
  "Class 3 obesity",
  "Drug-induced obesity",
  "Exogenous obesity",
  "Extreme obesity",
  "Familial obesity",
  "Morbid obesity",
  "Obesity due to excess calories",
  "Pediatric obesity",
  "Severe obesity"
 ]
}
```

