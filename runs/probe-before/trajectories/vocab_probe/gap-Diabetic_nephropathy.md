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
 "concept": "Diabetic nephropathy",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `5cfb5561684178c2`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Diabetic nephropathy
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

### 4. llm_response (cassette, 170 tok, 18.910s)

```
```json
{
  "names": [
    "Diabetic nephropathy",
    "Diabetic kidney disease",
    "Diabetic glomerulosclerosis",
    "Kimmelstiel-Wilson syndrome",
    "Type 1 diabetes mellitus with diabetic nephropathy",
    "Type 2 diabetes mellitus with diabetic nephropathy",
    "Type 1 diabetes mellitus with chronic kidney disease",
    "Type 2 diabetes mellitus with chronic kidney disease",
    "Diabetic chronic kidney disease",
    "Diabetic renal disease",
    "Microalbuminuria due to diabetes mellitus",
    "Proteinuria due to diabetes mellitus"
  ],
  "note": "Includes specific diagnostic terms, eponyms, and EHR/ICD combo codes for diabetes with renal manifestations."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Diabetic nephropathy",
  "Diabetic kidney disease",
  "Diabetic glomerulosclerosis",
  "Kimmelstiel-Wilson syndrome",
  "Type 1 diabetes mellitus with diabetic nephropathy",
  "Type 2 diabetes mellitus with diabetic nephropathy",
  "Type 1 diabetes mellitus with chronic kidney disease",
  "Type 2 diabetes mellitus with chronic kidney disease",
  "Diabetic chronic kidney disease",
  "Diabetic renal disease",
  "Microalbuminuria due to diabetes mellitus",
  "Proteinuria due to diabetes mellitus"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "127013003",
  "display": "Diabetic renal disease (disorder)",
  "domain": "condition",
  "n_resources": 11
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
  "code": "97331000119101",
  "display": "Macular edema and retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "1501000119109",
  "display": "Proliferative diabetic retinopathy due to type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "422034002",
  "display": "Diabetic retinopathy associated with type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 8
 },
 {
  "code": "15777000",
  "display": "Prediabetes",
  "domain": "condition",
  "n_resources": 155
 },
 {
  "code": "440540
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `61a466b282a05665`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Diabetic nephropathy
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
    97331000119101  Macular edema and retinopathy due to type 2 diabetes mellitus (disorde   (in 2 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
          15777000  Prediabetes   (in 155 resources)
          44054006  Diabetes   (in 32 resources)
          40095003  Injury of kidney (disorder)   (in 1 resources)

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

### 8. llm_response (cassette, 356 tok, 21.164s)

```
```json
{
  "codes": [
    "127013003"
  ],
  "rejected": [
    {
      "code": "90781000119102",
      "why": "Specific finding/sign (microalbuminuria) rather than the clinical disorder of diabetic nephropathy"
    },
    {
      "code": "1551000119108",
      "why": "Diabetic retinopathy (eye disease), not kidney disease"
    },
    {
      "code": "431855005",
      "why": "Chronic kidney disease stage 1 without specified diabetic etiology"
    },
    {
      "code": "431856006",
      "why": "Chronic kidney disease stage 2 without specified diabetic etiology"
    },
    {
      "code": "368581000119106",
      "why": "Diabetic neuropathy (nerve disease), not nephropathy (kidney disease)"
    },
    {
      "code": "97331000119101",
      "why": "Diabetic retinopathy and macular edema (eye disease), not kidney disease"
    },
    {
      "code": "1501000119109",
      "why": "Proliferative diabetic retinopathy (eye disease), not kidney disease"
    },
    {
      "code": "422034002",
      "why": "Diabetic retinopathy (eye disease), not kidney disease"
    },
    {
      "code": "15777000",
      "why": "Prediabetes, not diabetic nephropathy"
    },
    {
      "code": "44054006",
      "why": "General diabetes mellitus without kidney involvement specified"
    },
    {
      "code": "40095003",
      "why": "General kidney injury, not diabetic nephropathy"
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
  "127013003"
 ],
 "concept": "Diabetic nephropathy",
 "confidence": "high",
 "displays": [
  "Diabetic renal disease (disorder)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Diabetic nephropathy",
  "Diabetic kidney disease",
  "Diabetic glomerulosclerosis",
  "Kimmelstiel-Wilson syndrome",
  "Type 1 diabetes mellitus with diabetic nephropathy",
  "Type 2 diabetes mellitus with diabetic nephropathy",
  "Type 1 diabetes mellitus with chronic kidney disease",
  "Type 2 diabetes mellitus with chronic kidney disease",
  "Diabetic chronic kidney disease",
  "Diabetic renal disease",
  "Microalbuminuria due to diabetes mellitus",
  "Proteinuria due to diabetes mellitus"
 ],
 "matched_names": [
  "diabetic renal disease"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Diabetic chronic kidney disease",
  "Diabetic glomerulosclerosis",
  "Diabetic kidney disease",
  "Diabetic nephropathy",
  "Kimmelstiel-Wilson syndrome",
  "Microalbuminuria due to diabetes mellitus",
  "Proteinuria due to diabetes mellitus",
  "Type 1 diabetes mellitus with chronic kidney disease",
  "Type 1 diabetes mellitus with diabetic nephropathy",
  "Type 2 diabetes mellitus with chronic kidney disease",
  "Type 2 diabetes mellitus with diabetic nephropathy"
 ]
}
```

