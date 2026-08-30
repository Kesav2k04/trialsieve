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
 "concept": "Gastroparesis",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `9ff56e97b2583abf`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Gastroparesis
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

### 4. llm_response (cassette, 120 tok, 31.581s)

```
```json
{
  "names": [
    "Gastroparesis",
    "Diabetic gastroparesis",
    "Idiopathic gastroparesis",
    "Post-surgical gastroparesis",
    "Post-vagotomy gastroparesis",
    "Post-viral gastroparesis",
    "Delayed gastric emptying",
    "Gastric atony",
    "Gastric hypomotility",
    "Gastroparalysis",
    "Gastric stasis"
  ],
  "note": "Includes primary, etiologic subtypes (diabetic, postsurgical, post-viral, idiopathic), and synonymous motility descriptions."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Gastroparesis",
  "Diabetic gastroparesis",
  "Idiopathic gastroparesis",
  "Post-surgical gastroparesis",
  "Post-vagotomy gastroparesis",
  "Post-viral gastroparesis",
  "Delayed gastric emptying",
  "Gastric atony",
  "Gastric hypomotility",
  "Gastroparalysis",
  "Gastric stasis"
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
  "code": "83664006",
  "display": "Idiopathic atrophic hypothyroidism",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "314994000",
  "display": "Metastasis from malignant tumor of prostate (disorder)",
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
  "code": "1501000119109",
  "display": "Proliferative diabetic retinopathy due to type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "444814009",
  "display": "Viral sinusitis (disorder)",
  "domain": "condition",
  "n_resources": 585
 },
 {
  "code": "195662009",
  "display": "Acute viral pharyngitis (disorder)",
  "domain": "condition",
  "n_resources": 347
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `c4e6c76832599446`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Gastroparesis
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
          83664006  Idiopathic atrophic hypothyroidism   (in 1 resources)
         314994000  Metastasis from malignant tumor of prostate (disorder)   (in 1 resources)
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)
         444814009  Viral sinusitis (disorder)   (in 585 resources)
         195662009  Acute viral pharyngitis (disorder)   (in 347 resources)

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

### 8. llm_response (cassette, 279 tok, 31.204s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "127013003",
      "why": "refers to diabetic renal disease/nephropathy, not gastroparesis"
    },
    {
      "code": "83664006",
      "why": "refers to idiopathic atrophic hypothyroidism, an endocrine disorder unrelated to gastroparesis"
    },
    {
      "code": "314994000",
      "why": "refers to metastasis from prostate cancer, not gastroparesis"
    },
    {
      "code": "422034002",
      "why": "refers to diabetic retinopathy, an ocular complication of diabetes rather than gastric motility disorder"
    },
    {
      "code": "1551000119108",
      "why": "refers to nonproliferative diabetic retinopathy, not gastroparesis"
    },
    {
      "code": "1501000119109",
      "why": "refers to proliferative diabetic retinopathy, not gastroparesis"
    },
    {
      "code": "444814009",
      "why": "refers to viral sinusitis, an upper respiratory condition unrelated to gastroparesis"
    },
    {
      "code": "195662009",
      "why": "refers to acute viral pharyngitis, not gastroparesis"
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
 "concept": "Gastroparesis",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Gastroparesis",
  "Diabetic gastroparesis",
  "Idiopathic gastroparesis",
  "Post-surgical gastroparesis",
  "Post-vagotomy gastroparesis",
  "Post-viral gastroparesis",
  "Delayed gastric emptying",
  "Gastric atony",
  "Gastric hypomotility",
  "Gastroparalysis",
  "Gastric stasis"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "127013003",
   "why": "refers to diabetic renal disease/nephropathy, not gastroparesis"
  },
  {
   "code": "83664006",
   "why": "refers to idiopathic atrophic hypothyroidism, an endocrine disorder unrelated to gastroparesis"
  },
  {
   "code": "314994000",
   "why": "refers to metastasis from prostate cancer, not gastroparesis"
  },
  {
   "code": "422034002",
   "why": "refers to diabetic retinopathy, an ocular complication of diabetes rather than gastric motility disorder"
  },
  {
   "code": "1551000119108",
   "why": "refers to nonproliferative diabetic retinopathy, not gastroparesis"
  },
  {
   "code": "1501000119109",
   "why": "refers to proliferative diabetic retinopathy, not gastroparesis"
  },
  {
   "code": "444814009",
   "why": "refers to viral sinusitis, an upper respiratory condition unrelated to gastroparesis"
  },
  {
   "code": "195662009",
   "why": "refers to acute viral pharyngitis, not gastroparesis"
  }
 ],
 "status": "UNMAPPABLE"
}
```

