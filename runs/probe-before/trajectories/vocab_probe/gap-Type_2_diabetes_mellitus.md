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
 "concept": "Type 2 diabetes mellitus",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `7801bb3c923a91fc`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Type 2 diabetes mellitus
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

### 4. llm_response (cassette, 177 tok, 19.244s)

```
```json
{
  "names": [
    "Type 2 diabetes mellitus",
    "Type 2 diabetes mellitus without complications",
    "Type 2 diabetes mellitus with diabetic nephropathy",
    "Type 2 diabetes mellitus with diabetic retinopathy",
    "Type 2 diabetes mellitus with diabetic neuropathy",
    "Type 2 diabetes mellitus with peripheral angiopathy",
    "Type 2 diabetes mellitus with foot ulcer",
    "Type 2 diabetes mellitus with hyperosmolarity",
    "Type 2 diabetes mellitus with ketoacidosis",
    "Non-insulin-dependent diabetes mellitus",
    "Adult-onset diabetes mellitus"
  ],
  "note": "Includes standard diagnosis terms, legacy synonyms, and common complication-specific coded clinical sub-types."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Type 2 diabetes mellitus",
  "Type 2 diabetes mellitus without complications",
  "Type 2 diabetes mellitus with diabetic nephropathy",
  "Type 2 diabetes mellitus with diabetic retinopathy",
  "Type 2 diabetes mellitus with diabetic neuropathy",
  "Type 2 diabetes mellitus with peripheral angiopathy",
  "Type 2 diabetes mellitus with foot ulcer",
  "Type 2 diabetes mellitus with hyperosmolarity",
  "Type 2 diabetes mellitus with ketoacidosis",
  "Non-insulin-dependent diabetes mellitus",
  "Adult-onset diabetes mellitus"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "1551000119108",
  "display": "Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 5
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
  "code": "422034002",
  "display": "Diabetic retinopathy associated with type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 8
 },
 {
  "code": "1501000119109",
  "display": "Proliferative diabetic retinopathy due to type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
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
  "code": "431856006",
  "display": "Chronic kidney disease stage 2 (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "284551006",
  "display": "Laceration of foot",
  "domain": "condition",
  "n_resources": 15
 },
 {
  "code": "230265002",
  "display": "Familial Alzheimer's disease 
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `b72ea93972d05796`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Type 2 diabetes mellitus
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
    97331000119101  Macular edema and retinopathy due to type 2 diabetes mellitus (disorde   (in 2 resources)
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)
          15777000  Prediabetes   (in 155 resources)
          44054006  Diabetes   (in 32 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
         284551006  Laceration of foot   (in 15 resources)
         230265002  Familial Alzheimer's disease of early onset (disorder)   (in 1 resources)
         127013003  Diabetic renal disease (disorder)   (in 11 resources)

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

### 8. llm_response (cassette, 472 tok, 21.738s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "1551000119108",
      "why": "specific secondary complication (diabetic retinopathy) rather than the primary diagnosis of type 2 diabetes mellitus"
    },
    {
      "code": "368581000119106",
      "why": "specific secondary complication (diabetic neuropathy) rather than the primary diagnosis of type 2 diabetes mellitus"
    },
    {
      "code": "90781000119102",
      "why": "specific secondary manifestation/complication (microalbuminuria) rather than type 2 diabetes mellitus"
    },
    {
      "code": "97331000119101",
      "why": "specific secondary complication (macular edema and retinopathy) rather than type 2 diabetes mellitus"
    },
    {
      "code": "422034002",
      "why": "specific secondary complication (diabetic retinopathy) rather than the primary condition of type 2 diabetes mellitus"
    },
    {
      "code": "1501000119109",
      "why": "specific secondary complication (proliferative diabetic retinopathy) rather than type 2 diabetes mellitus"
    },
    {
      "code": "15777000",
      "why": "represents prediabetes (impaired glucose tolerance), not established type 2 diabetes mellitus"
    },
    {
      "code": "44054006",
      "why": "general/unspecified diabetes mellitus, which lacks the type-specific classification required by a trial protocol"
    },
    {
      "code": "431856006",
      "why": "unrelated renal condition (chronic kidney disease stage 2)"
    },
    {
      "code": "284551006",
      "why": "unrelated traumatic injury (laceration of foot)"
    },
    {
      "code": "230265002",
      "why": "unrelated neurodegenerative condition (familial Alzheimer's disease)"
    },
    {
      "code": "127013003",
      "why": "diabetic renal complication rather than the primary diagnosis of type 2 diabetes mellitus"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "codes": [],
 "concept": "Type 2 diabetes mellitus",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Type 2 diabetes mellitus",
  "Type 2 diabetes mellitus without complications",
  "Type 2 diabetes mellitus with diabetic nephropathy",
  "Type 2 diabetes mellitus with diabetic retinopathy",
  "Type 2 diabetes mellitus with diabetic neuropathy",
  "Type 2 diabetes mellitus with peripheral angiopathy",
  "Type 2 diabetes mellitus with foot ulcer",
  "Type 2 diabetes mellitus with hyperosmolarity",
  "Type 2 diabetes mellitus with ketoacidosis",
  "Non-insulin-dependent diabetes mellitus",
  "Adult-onset diabetes mellitus"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "1551000119108",
   "why": "specific secondary complication (diabetic retinopathy) rather than the primary diagnosis of type 2 diabetes mellitus"
  },
  {
   "code": "368581000119106",
   "why": "specific secondary complication (diabetic neuropathy) rather than the primary diagnosis of type 2 diabetes mellitus"
  },
  {
   "code": "90781000119102",
   "why": "specific secondary manifestation/complication (microalbuminuria) rather than type 2 diabetes mellitus"
  },
  {
   "code": "97331000119101",
   "why": "specific secondary complication (macular edema and retinopathy) rather than type 2 diabetes mellitus"
  },
  {
   "code": "422034002",
   "why": "specific secondary complication (diabetic retinopathy) rather than the primary condition of type 2 diabetes mellitus"
  },
  {
   "code": "1501000119109",
   "why": "specific secondary complication (proliferative diabetic retinopathy) rather than type 2 diabetes mellitus"
  },
  {
   "code": "15777000",
   "why": "represents prediabetes (impaired glucose tolera
```

