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
 "concept": "Type 1 diabetes mellitus",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `8af73f4cecde0cee`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Type 1 diabetes mellitus
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

### 4. llm_response (openai, 178 tok, 60.299s)

```
```json
{
  "names": [
    "Type 1 diabetes mellitus",
    "Insulin-dependent diabetes mellitus",
    "Juvenile diabetes mellitus",
    "Latent autoimmune diabetes in adults",
    "Autoimmune diabetes mellitus",
    "Brittle diabetes mellitus",
    "Type 1 diabetes mellitus without complications",
    "Type 1 diabetes mellitus with ketoacidosis",
    "Type 1 diabetes mellitus with diabetic nephropathy",
    "Type 1 diabetes mellitus with diabetic neuropathy",
    "Type 1 diabetes mellitus with diabetic retinopathy",
    "Type 1 diabetes mellitus with hypoglycemia"
  ],
  "note": "Includes common clinical synonyms, historical designations, phenotypic variants, and manifestation-specific diagnoses."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Type 1 diabetes mellitus",
  "Insulin-dependent diabetes mellitus",
  "Juvenile diabetes mellitus",
  "Latent autoimmune diabetes in adults",
  "Autoimmune diabetes mellitus",
  "Brittle diabetes mellitus",
  "Type 1 diabetes mellitus without complications",
  "Type 1 diabetes mellitus with ketoacidosis",
  "Type 1 diabetes mellitus with diabetic nephropathy",
  "Type 1 diabetes mellitus with diabetic neuropathy",
  "Type 1 diabetes mellitus with diabetic retinopathy",
  "Type 1 diabetes mellitus with hypoglycemia"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
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
  "code": "1501000119109",
  "display": "Proliferative diabetic retinopathy due to type II diabetes mellitus (disorder)",
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
  "code": "97331000119101",
  "display": "Macular edema and retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
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
  "code": "431855005",
  "display": "Chronic kidney disease stage 1 (disorder)",
  "domain": "condition",
  "n_resources": 10
 },
 {
  "code": "424132000",
  "display": "Non-small cell carcinoma of lung, TNM stage 1 (disorder)",
  "domain": "condition",
  "n_resources": 5
 },
 {
  "code": "127013003",
  "di
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `1de9537e78d99287`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Type 1 diabetes mellitus
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
    97331000119101  Macular edema and retinopathy due to type 2 diabetes mellitus (disorde   (in 2 resources)
          15777000  Prediabetes   (in 155 resources)
          44054006  Diabetes   (in 32 resources)
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         424132000  Non-small cell carcinoma of lung, TNM stage 1 (disorder)   (in 5 resources)
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
   124171000119105  Chronic intractable migraine without aura   (in 26 resources)

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

### 8. llm_response (openai, 319 tok, 118.499s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "422034002",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "1551000119108",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "1501000119109",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "368581000119106",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "90781000119102",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "97331000119101",
      "why": "specific to type 2 diabetes mellitus"
    },
    {
      "code": "15777000",
      "why": "represents prediabetes, not type 1 diabetes mellitus"
    },
    {
      "code": "44054006",
      "why": "unspecified/generic diabetes mellitus, not specific to type 1"
    },
    {
      "code": "431855005",
      "why": "chronic kidney disease, not diabetes mellitus"
    },
    {
      "code": "424132000",
      "why": "lung carcinoma, not diabetes mellitus"
    },
    {
      "code": "127013003",
      "why": "generic diabetic renal complication without type specification"
    },
    {
      "code": "124171000119105",
      "why": "migraine disorder, unrelated"
    }
  ],
  "confidence": "high"
}
```
```

### 9. transport_retry

```json
{
 "attempt": 1,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 10. final

```json
{
 "codes": [],
 "concept": "Type 1 diabetes mellitus",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Type 1 diabetes mellitus",
  "Insulin-dependent diabetes mellitus",
  "Juvenile diabetes mellitus",
  "Latent autoimmune diabetes in adults",
  "Autoimmune diabetes mellitus",
  "Brittle diabetes mellitus",
  "Type 1 diabetes mellitus without complications",
  "Type 1 diabetes mellitus with ketoacidosis",
  "Type 1 diabetes mellitus with diabetic nephropathy",
  "Type 1 diabetes mellitus with diabetic neuropathy",
  "Type 1 diabetes mellitus with diabetic retinopathy",
  "Type 1 diabetes mellitus with hypoglycemia"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "422034002",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "1551000119108",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "1501000119109",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "368581000119106",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "90781000119102",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "97331000119101",
   "why": "specific to type 2 diabetes mellitus"
  },
  {
   "code": "15777000",
   "why": "represents prediabetes, not type 1 diabetes mellitus"
  },
  {
   "code": "44054006",
   "why": "unspecified/generic diabetes mellitus, not specific to type 1"
  },
  {
   "code": "431855005",
   "why": "chronic kidney disease, not diabetes mellitus"
  },
  {
   "code": "424132000",
   "why": "lung carcinoma, not diabetes mellitus"
  },
  {
   "code": "127013003",
   "why": "generic diabetic renal complication without type specification"
  },
  {
   "code": "124171000119105",
   "why":
```

