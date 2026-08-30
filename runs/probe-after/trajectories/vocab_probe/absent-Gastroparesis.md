### 1. instructions (prompt grounder-v3)

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

The display text beside each code is whatever the source system chose to store.
It is frequently abbreviated, locally worded, or vaguer than the code it labels,
and it is not the code's definition. Judge the concept the code denotes. Where you
recognise a code and its display disagree about how specific the concept is, the
code decides, and name the code you relied on in `why` for the ones you rejected.
This does not license guessing: a code you do not recognise is judged on its
display like any other candidate, and a display that is vaguer than the concept is
still a reason to reject a code you have no independent knowledge of.

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

A candidate can also be BROADER than the concept: it contains what the criterion
asks for and other things as well. A site that records every diabetes diagnosis
under one unspecified diabetes code has a code that is broader than "type 2
diabetes mellitus". A site whose only asthma code is "chronic lower respiratory
disease" has one that is broader than asthma.

Put those in `broader_codes`, not in `codes`. The difference decides what happens
to a patient. A code in `codes` proves the concept when it is present. A code in
`broader_codes` cannot prove it, and the criterion comes back undetermined for
that patient rather than satisfied. Its absence still counts: a patient with no
diabetes code of any kind does not have type 2 diabetes either.

Do not use `broader_codes` for a code that is merely related, or for a
complication of the concept, or for a different thing that shares a word. Only
for a code whose meaning genuinely contains the concept.

If no candidate represents the concept and none contains it, return both lists
empty. That is a normal and useful answer.

Return JSON only:
{{"codes": ["4548-4"], "broader_codes": [],
  "rejected": [{{"code": "718-7", "why": "different analyte"}}],
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

### 4. llm_response (cassette, 118 tok, 56.882s)

```
```json
{
  "names": [
    "Gastroparesis",
    "Diabetic gastroparesis",
    "Idiopathic gastroparesis",
    "Post-surgical gastroparesis",
    "Postvagotomy gastroparesis",
    "Post-viral gastroparesis",
    "Delayed gastric emptying",
    "Gastric atony",
    "Gastric hypomotility",
    "Gastric stasis"
  ],
  "note": "Includes primary gastroparesis, key etiologies (diabetic, post-surgical, post-viral, idiopathic), and synonymous motility diagnostic terms."
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
  "Postvagotomy gastroparesis",
  "Post-viral gastroparesis",
  "Delayed gastric emptying",
  "Gastric atony",
  "Gastric hypomotility",
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `1abf44799e69a8fd`

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

The display text beside each code is whatever the source system chose to store.
It is frequently abbreviated, locally worded, or vaguer than the code it labels,
and it is not the code's definition. Judge the concept the code denotes. Where you
recognise a code and its display disagree about how specific the concept is, the
code decides, and name the code you relied on in `why` for the ones you rejected.
This does not license guessing: a code you do not recognise is judged on its
display like any other candidate, and a display that is vaguer than the concept is
still a reason to reject a code you have no independent knowledge of.

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

A candidate can also be BROADER than the concept: it contains what the criterion
asks for and other things as well. A site that records every diabetes diagnosis
under one unspecified diabetes code has a code that is broader than "type 2
diabetes mellitus". A site whose only asthma code is "chronic lower respiratory
disease" has one that is broader than asthma.

Put those in `broader_codes`, not in `codes`. The difference decides what happens
to a patient. A code in `codes` proves the concept when it is present. A code in
`broader_codes` cannot prove it, and the criterion comes back undetermined for
that patient rather than satisfied. Its absence still counts: a patient with no
diabetes code of any kind does not have type 2 diabetes either.

Do not use `broader_codes` for a code that is merely related, or for a
complication of the concept, or for a different thing that shares a word. Only
for a code whose meaning genuinely contains the concept.

If no candidate represents the concept and none contains it, return both lists
empty. That is a normal and useful answer.

Return JSON only:
{"codes": ["4548-4"], "broader_codes": [],
  "rejected": [{"code": "718-7", "why": "different analyte"}],
  "confidence": "high"}
```

### 8. llm_response (cassette, 274 tok, 61.498s)

```
```json
{
  "codes": [],
  "broader_codes": [],
  "rejected": [
    {
      "code": "127013003",
      "why": "diabetic renal disease, not gastroparesis"
    },
    {
      "code": "83664006",
      "why": "idiopathic atrophic hypothyroidism, unrelated endocrine disorder"
    },
    {
      "code": "314994000",
      "why": "metastasis from malignant tumor of prostate, unrelated neoplastic disorder"
    },
    {
      "code": "422034002",
      "why": "diabetic retinopathy associated with type II diabetes mellitus, not gastroparesis"
    },
    {
      "code": "1551000119108",
      "why": "nonproliferative diabetic retinopathy due to type 2 diabetes mellitus, not gastroparesis"
    },
    {
      "code": "1501000119109",
      "why": "proliferative diabetic retinopathy due to type II diabetes mellitus, not gastroparesis"
    },
    {
      "code": "444814009",
      "why": "viral sinusitis, unrelated respiratory infection"
    },
    {
      "code": "195662009",
      "why": "acute viral pharyngitis, unrelated upper respiratory infection"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [],
 "concept": "Gastroparesis",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Gastroparesis",
  "Diabetic gastroparesis",
  "Idiopathic gastroparesis",
  "Post-surgical gastroparesis",
  "Postvagotomy gastroparesis",
  "Post-viral gastroparesis",
  "Delayed gastric emptying",
  "Gastric atony",
  "Gastric hypomotility",
  "Gastric stasis"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "127013003",
   "why": "diabetic renal disease, not gastroparesis"
  },
  {
   "code": "83664006",
   "why": "idiopathic atrophic hypothyroidism, unrelated endocrine disorder"
  },
  {
   "code": "314994000",
   "why": "metastasis from malignant tumor of prostate, unrelated neoplastic disorder"
  },
  {
   "code": "422034002",
   "why": "diabetic retinopathy associated with type II diabetes mellitus, not gastroparesis"
  },
  {
   "code": "1551000119108",
   "why": "nonproliferative diabetic retinopathy due to type 2 diabetes mellitus, not gastroparesis"
  },
  {
   "code": "1501000119109",
   "why": "proliferative diabetic retinopathy due to type II diabetes mellitus, not gastroparesis"
  },
  {
   "code": "444814009",
   "why": "viral sinusitis, unrelated respiratory infection"
  },
  {
   "code": "195662009",
   "why": "acute viral pharyngitis, unrelated upper respiratory infection"
  }
 ],
 "status": "UNMAPPABLE"
}
```

