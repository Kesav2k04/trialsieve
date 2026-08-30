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
 "concept": "Essential hypertension",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `1d87974509beb331`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Essential hypertension
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

### 4. llm_response (cassette, 129 tok, 25.947s)

```
```json
{
  "names": [
    "Essential hypertension",
    "Primary hypertension",
    "Essential (primary) hypertension",
    "Benign essential hypertension",
    "Malignant essential hypertension",
    "Idiopathic hypertension",
    "Systemic arterial hypertension",
    "Isolated systolic hypertension",
    "Labile hypertension",
    "Hypertensive vascular disease"
  ],
  "note": "Includes primary/essential hypertension standard diagnostic terms, clinical subtypes, and common EHR condition descriptions."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Essential hypertension",
  "Primary hypertension",
  "Essential (primary) hypertension",
  "Benign essential hypertension",
  "Malignant essential hypertension",
  "Idiopathic hypertension",
  "Systemic arterial hypertension",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "Hypertensive vascular disease"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "59621000",
  "display": "Hypertension",
  "domain": "condition",
  "n_resources": 141
 },
 {
  "code": "95417003",
  "display": "Primary fibromyalgia syndrome",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "83664006",
  "display": "Idiopathic atrophic hypothyroidism",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "201834006",
  "display": "Localized, primary osteoarthritis of the hand",
  "domain": "condition",
  "n_resources": 11
 },
 {
  "code": "224295006",
  "display": "Only received primary school education (finding)",
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
  "code": "127013003",
  "display": "Diabetic renal disease (disorder)",
  "domain": "condition",
  "n_resources": 11
 },
 {
  "code": "254837009",
  "display": "Malignant neoplasm of breast (disorder)",
  "domain": "condition",
  "n_resources": 6
 },
 {
  "code": "363406005",
  "display": "Malignant tumor of colon",
  "domain": "condition",
  "n_resources": 4
 },
 {
  "code": "235595009",
  "display": "Gastroesophageal reflux disease (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "109838007",
  "display": "Overlapping malignant neoplasm of colon",
  "domain": "condition",
  "n_resources": 2
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `3aabaaac1996e58a`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Essential hypertension
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
          59621000  Hypertension   (in 141 resources)
          95417003  Primary fibromyalgia syndrome   (in 2 resources)
          83664006  Idiopathic atrophic hypothyroidism   (in 1 resources)
         201834006  Localized, primary osteoarthritis of the hand   (in 11 resources)
         224295006  Only received primary school education (finding)   (in 54 resources)
          53741008  Coronary Heart Disease   (in 25 resources)
          26929004  Alzheimer's disease (disorder)   (in 17 resources)
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
         254837009  Malignant neoplasm of breast (disorder)   (in 6 resources)
         363406005  Malignant tumor of colon   (in 4 resources)
         235595009  Gastroesophageal reflux disease (disorder)   (in 2 resources)
         109838007  Overlapping malignant neoplasm of colon   (in 2 resources)

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

### 8. llm_response (cassette, 394 tok, 30.161s)

```
```json
{
  "codes": ["59621000"],
  "broader_codes": [],
  "rejected": [
    {
      "code": "95417003",
      "why": "Primary fibromyalgia syndrome is a chronic pain disorder, not hypertension"
    },
    {
      "code": "83664006",
      "why": "Idiopathic atrophic hypothyroidism is a thyroid disorder, not hypertension"
    },
    {
      "code": "201834006",
      "why": "Localized, primary osteoarthritis of the hand is a joint disorder, not hypertension"
    },
    {
      "code": "224295006",
      "why": "Finding related to educational attainment, not a medical condition"
    },
    {
      "code": "53741008",
      "why": "Coronary heart disease is an ischemic cardiovascular disorder, distinct from essential hypertension"
    },
    {
      "code": "26929004",
      "why": "Alzheimer's disease is a neurodegenerative disorder, not hypertension"
    },
    {
      "code": "127013003",
      "why": "Diabetic renal disease is a nephropathy associated with diabetes, not hypertension"
    },
    {
      "code": "254837009",
      "why": "Malignant neoplasm of breast is an oncological condition, not hypertension"
    },
    {
      "code": "363406005",
      "why": "Malignant tumor of colon is an oncological condition, not hypertension"
    },
    {
      "code": "235595009",
      "why": "Gastroesophageal reflux disease is a gastrointestinal disorder, not hypertension"
    },
    {
      "code": "109838007",
      "why": "Overlapping malignant neoplasm of colon is an oncological condition, not hypertension"
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
 "codes": [
  "59621000"
 ],
 "concept": "Essential hypertension",
 "confidence": "high",
 "displays": [
  "Hypertension"
 ],
 "domain": "condition",
 "expanded_names": [
  "Essential hypertension",
  "Primary hypertension",
  "Essential (primary) hypertension",
  "Benign essential hypertension",
  "Malignant essential hypertension",
  "Idiopathic hypertension",
  "Systemic arterial hypertension",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "Hypertensive vascular disease"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Benign essential hypertension",
  "Essential (primary) hypertension",
  "Essential hypertension",
  "Hypertensive vascular disease",
  "Idiopathic hypertension",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "Malignant essential hypertension",
  "Primary hypertension",
  "Systemic arterial hypertension"
 ]
}
```

