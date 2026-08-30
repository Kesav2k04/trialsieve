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

### 4. llm_response (cassette, 135 tok, 44.115s)

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
    "Chronic kidney disease stage 5 on dialysis",
    "Dependence on renal dialysis",
    "Moderate chronic kidney disease",
    "Severe chronic kidney disease"
  ],
  "note": "Includes CKD stages 3 (including 3a and 3b), 4, 5, and end-stage renal disease or dialysis dependence."
}
```
```

### 5. tool_call `terminology.search_any`

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
  "Chronic kidney disease stage 5 on dialysis",
  "Dependence on renal dialysis",
  "Moderate chronic kidney disease",
  "Severe chronic kidney disease"
 ]
}
```

### 6. tool_result `terminology.search_any`

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
 },
 {
  "code": "235595009",
  "display": "Gastroesophageal reflux disease (disorder)",
  "domain": "condition",
  "n_resources": 2
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `d81f54fac5c684d0`

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
          40055000  Chronic sinusitis (disorder)   (in 88 resources)
          82423001  Chronic pain   (in 22 resources)
          40095003  Injury of kidney (disorder)   (in 1 resources)
          80583007  Severe anxiety (panic) (finding   (in 59 resources)
     1121000119107  Chronic neck pain (finding)   (in 54 resources)
          53741008  Coronary Heart Disease   (in 25 resources)
          26929004  Alzheimer's disease (disorder)   (in 17 resources)
         185086009  Chronic obstructive bronchitis (disorder)   (in 2 resources)
         235595009  Gastroesophageal reflux disease (disorder)   (in 2 resources)

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

### 8. llm_response (cassette, 404 tok, 47.409s)

```
```json
{
  "codes": [],
  "broader_codes": [],
  "rejected": [
    {
      "code": "431855005",
      "why": "Chronic kidney disease stage 1 is less severe than the required stage 3 or worse"
    },
    {
      "code": "431856006",
      "why": "Chronic kidney disease stage 2 is less severe than the required stage 3 or worse"
    },
    {
      "code": "127013003",
      "why": "Diabetic renal disease indicates etiology rather than stage; does not establish stage 3 or worse nor fully subsume CKD stage 3+"
    },
    {
      "code": "40055000",
      "why": "Chronic sinusitis is an unrelated respiratory condition"
    },
    {
      "code": "82423001",
      "why": "Chronic pain is an unrelated condition"
    },
    {
      "code": "40095003",
      "why": "Injury of kidney refers to traumatic or acute renal injury, not chronic kidney disease stage 3 or worse"
    },
    {
      "code": "80583007",
      "why": "Severe anxiety is an unrelated psychiatric condition"
    },
    {
      "code": "1121000119107",
      "why": "Chronic neck pain is an unrelated musculoskeletal finding"
    },
    {
      "code": "53741008",
      "why": "Coronary heart disease is an unrelated cardiovascular condition"
    },
    {
      "code": "26929004",
      "why": "Alzheimer's disease is an unrelated neurological disorder"
    },
    {
      "code": "185086009",
      "why": "Chronic obstructive bronchitis is an unrelated pulmonary disorder"
    },
    {
      "code": "235595009",
      "why": "Gastroesophageal reflux disease is an unrelated gastrointestinal disorder"
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
  "Chronic kidney disease stage 5 on dialysis",
  "Dependence on renal dialysis",
  "Moderate chronic kidney disease",
  "Severe chronic kidney disease"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "431855005",
   "why": "Chronic kidney disease stage 1 is less severe than the required stage 3 or worse"
  },
  {
   "code": "431856006",
   "why": "Chronic kidney disease stage 2 is less severe than the required stage 3 or worse"
  },
  {
   "code": "127013003",
   "why": "Diabetic renal disease indicates etiology rather than stage; does not establish stage 3 or worse nor fully subsume CKD stage 3+"
  },
  {
   "code": "40055000",
   "why": "Chronic sinusitis is an unrelated respiratory condition"
  },
  {
   "code": "82423001",
   "why": "Chronic pain is an unrelated condition"
  },
  {
   "code": "40095003",
   "why": "Injury of kidney refers to traumatic or acute renal injury, not chronic kidney disease stage 3 or worse"
  },
  {
   "code": "80583007",
   "why": "Severe anxiety is an unrelated psychiatric condition"
  },
  {
   "code": "1121000119107",
   "why": "Chronic neck pain is an unrelated musculoskeletal finding"
  },
  {
   "code": "53741008",
   "why": "Coronary heart disease is an unrelated cardiovascular condition"
  },
  {
   "code": "26929004",
   "why": "Alzheimer's disease is an unrelated neurological disorde
```

