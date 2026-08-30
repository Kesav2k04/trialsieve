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
 "concept": "Prediabetes",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `8aed46ccb36294f8`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Prediabetes
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

### 4. llm_response (cassette, 100 tok, 17.212s)

```
```json
{
  "names": [
    "Prediabetes",
    "Pre-diabetes",
    "Impaired fasting glucose",
    "Impaired glucose tolerance",
    "Borderline diabetes",
    "Latent diabetes",
    "Elevated fasting glucose",
    "Hyperglycemia, postprandial",
    "Abnormal glucose tolerance"
  ],
  "note": "Includes diagnostic terms and standard clinical designations for early impaired glucose metabolism."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Prediabetes",
  "Pre-diabetes",
  "Impaired fasting glucose",
  "Impaired glucose tolerance",
  "Borderline diabetes",
  "Latent diabetes",
  "Elevated fasting glucose",
  "Hyperglycemia, postprandial",
  "Abnormal glucose tolerance"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "15777000",
  "display": "Prediabetes",
  "domain": "condition",
  "n_resources": 155
 },
 {
  "code": "44054006",
  "display": "Diabetes",
  "domain": "condition",
  "n_resources": 32
 },
 {
  "code": "80394007",
  "display": "Hyperglycemia (disorder)",
  "domain": "condition",
  "n_resources": 19
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
  "code": "422034002",
  "display": "Diabetic retinopathy associated with type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 8
 },
 {
  "code": "1551000119108",
  "display": "Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 5
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
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `f0f0adeaf9e73c53`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Prediabetes
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
          15777000  Prediabetes   (in 155 resources)
          44054006  Diabetes   (in 32 resources)
          80394007  Hyperglycemia (disorder)   (in 19 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
    97331000119101  Macular edema and retinopathy due to type 2 diabetes mellitus (disorde   (in 2 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)

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

### 8. llm_response (cassette, 268 tok, 21.390s)

```
```json
{
  "codes": [
    "15777000"
  ],
  "rejected": [
    {
      "code": "44054006",
      "why": "represents overt diabetes mellitus rather than the distinct clinical stage of prediabetes"
    },
    {
      "code": "80394007",
      "why": "nonspecific elevated blood glucose sign/disorder, not the specific clinical diagnostic entity of prediabetes"
    },
    {
      "code": "368581000119106",
      "why": "complication of established type 2 diabetes mellitus"
    },
    {
      "code": "90781000119102",
      "why": "complication of established type 2 diabetes mellitus"
    },
    {
      "code": "422034002",
      "why": "complication of established type 2 diabetes mellitus"
    },
    {
      "code": "1551000119108",
      "why": "complication of established type 2 diabetes mellitus"
    },
    {
      "code": "97331000119101",
      "why": "complication of established type 2 diabetes mellitus"
    },
    {
      "code": "1501000119109",
      "why": "complication of established type 2 diabetes mellitus"
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
  "15777000"
 ],
 "concept": "Prediabetes",
 "confidence": "high",
 "displays": [
  "Prediabetes"
 ],
 "domain": "condition",
 "expanded_names": [
  "Prediabetes",
  "Pre-diabetes",
  "Impaired fasting glucose",
  "Impaired glucose tolerance",
  "Borderline diabetes",
  "Latent diabetes",
  "Elevated fasting glucose",
  "Hyperglycemia, postprandial",
  "Abnormal glucose tolerance"
 ],
 "matched_names": [
  "prediabetes"
 ],
 "reason": "1 of 9 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Abnormal glucose tolerance",
  "Borderline diabetes",
  "Elevated fasting glucose",
  "Hyperglycemia, postprandial",
  "Impaired fasting glucose",
  "Impaired glucose tolerance",
  "Latent diabetes",
  "Pre-diabetes"
 ]
}
```

