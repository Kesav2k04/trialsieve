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
 "concept": "Acute pancreatitis",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `a04e191ceabd3a4b`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Acute pancreatitis
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

### 4. llm_response (openai, 150 tok, 72.742s)

```
```json
{
  "names": [
    "Acute pancreatitis",
    "Acute interstitial edematous pancreatitis",
    "Acute necrotizing pancreatitis",
    "Acute hemorrhagic pancreatitis",
    "Acute biliary pancreatitis",
    "Gallstone pancreatitis",
    "Alcohol-induced acute pancreatitis",
    "Idiopathic acute pancreatitis",
    "Drug-induced acute pancreatitis",
    "Hypertriglyceridemia-induced acute pancreatitis",
    "Acute pancreatitis with infected necrosis"
  ],
  "note": "Includes primary acute pancreatitis and common etiologic or pathological subtypes recorded in clinical coding systems."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Acute pancreatitis",
  "Acute interstitial edematous pancreatitis",
  "Acute necrotizing pancreatitis",
  "Acute hemorrhagic pancreatitis",
  "Acute biliary pancreatitis",
  "Gallstone pancreatitis",
  "Alcohol-induced acute pancreatitis",
  "Idiopathic acute pancreatitis",
  "Drug-induced acute pancreatitis",
  "Hypertriglyceridemia-induced acute pancreatitis",
  "Acute pancreatitis with infected necrosis"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "10509002",
  "display": "Acute bronchitis (disorder)",
  "domain": "condition",
  "n_resources": 266
 },
 {
  "code": "65275009",
  "display": "Acute Cholecystitis",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "195662009",
  "display": "Acute viral pharyngitis (disorder)",
  "domain": "condition",
  "n_resources": 347
 },
 {
  "code": "75498004",
  "display": "Acute bacterial sinusitis (disorder)",
  "domain": "condition",
  "n_resources": 38
 },
 {
  "code": "241929008",
  "display": "Acute allergic reaction",
  "domain": "condition",
  "n_resources": 6
 },
 {
  "code": "706870000",
  "display": "Acute pulmonary embolism (disorder)",
  "domain": "condition",
  "n_resources": 4
 },
 {
  "code": "65710008",
  "display": "Acute respiratory failure (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "132281000119108",
  "display": "Acute deep venous thrombosis (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "67782005",
  "display": "Acute respiratory distress syndrome (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "302870006",
  "display": "Hypertriglyceridemia (disorder)",
  "domain": "condition",
  "n_resources": 31
 },
 {
  "code": "7200002",
  "display": "Alcoholism",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "83664006",
  "display": "Idiopathic atrophic hypothyroidism",
  "domain": "condition",
  "n_resources": 1
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `4fcf7fa84c0ab47f`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Acute pancreatitis
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
          10509002  Acute bronchitis (disorder)   (in 266 resources)
          65275009  Acute Cholecystitis   (in 2 resources)
         195662009  Acute viral pharyngitis (disorder)   (in 347 resources)
          75498004  Acute bacterial sinusitis (disorder)   (in 38 resources)
         241929008  Acute allergic reaction   (in 6 resources)
         706870000  Acute pulmonary embolism (disorder)   (in 4 resources)
          65710008  Acute respiratory failure (disorder)   (in 2 resources)
   132281000119108  Acute deep venous thrombosis (disorder)   (in 2 resources)
          67782005  Acute respiratory distress syndrome (disorder)   (in 2 resources)
         302870006  Hypertriglyceridemia (disorder)   (in 31 resources)
           7200002  Alcoholism   (in 2 resources)
          83664006  Idiopathic atrophic hypothyroidism   (in 1 resources)

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

### 8. llm_response (openai, 431 tok, 68.191s)

```
```json
{
  "codes": [],
  "broader_codes": [],
  "rejected": [
    {
      "code": "10509002",
      "why": "acute bronchitis affects the lower respiratory tract, not the pancreas"
    },
    {
      "code": "65275009",
      "why": "acute cholecystitis is inflammation of the gallbladder, not the pancreas"
    },
    {
      "code": "195662009",
      "why": "acute viral pharyngitis affects the pharynx, not the pancreas"
    },
    {
      "code": "75498004",
      "why": "acute bacterial sinusitis affects the paranasal sinuses, not the pancreas"
    },
    {
      "code": "241929008",
      "why": "acute allergic reaction is an immune-mediated hypersensitivity response, not acute pancreatitis"
    },
    {
      "code": "706870000",
      "why": "acute pulmonary embolism is a pulmonary vascular disorder, not acute pancreatitis"
    },
    {
      "code": "65710008",
      "why": "acute respiratory failure is a respiratory system dysfunction, not acute pancreatitis"
    },
    {
      "code": "132281000119108",
      "why": "acute deep venous thrombosis is a venous thromboembolic condition, not acute pancreatitis"
    },
    {
      "code": "67782005",
      "why": "acute respiratory distress syndrome is a form of lung injury, not acute pancreatitis"
    },
    {
      "code": "302870006",
      "why": "hypertriglyceridemia is a lipid disorder / potential etiology, not acute pancreatitis"
    },
    {
      "code": "7200002",
      "why": "alcoholism is a substance use disorder / potential etiology, not acute pancreatitis"
    },
    {
      "code": "83664006",
      "why": "idiopathic atrophic hypothyroidism is a thyroid disorder, not acute pancreatitis"
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
 "concept": "Acute pancreatitis",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Acute pancreatitis",
  "Acute interstitial edematous pancreatitis",
  "Acute necrotizing pancreatitis",
  "Acute hemorrhagic pancreatitis",
  "Acute biliary pancreatitis",
  "Gallstone pancreatitis",
  "Alcohol-induced acute pancreatitis",
  "Idiopathic acute pancreatitis",
  "Drug-induced acute pancreatitis",
  "Hypertriglyceridemia-induced acute pancreatitis",
  "Acute pancreatitis with infected necrosis"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "10509002",
   "why": "acute bronchitis affects the lower respiratory tract, not the pancreas"
  },
  {
   "code": "65275009",
   "why": "acute cholecystitis is inflammation of the gallbladder, not the pancreas"
  },
  {
   "code": "195662009",
   "why": "acute viral pharyngitis affects the pharynx, not the pancreas"
  },
  {
   "code": "75498004",
   "why": "acute bacterial sinusitis affects the paranasal sinuses, not the pancreas"
  },
  {
   "code": "241929008",
   "why": "acute allergic reaction is an immune-mediated hypersensitivity response, not acute pancreatitis"
  },
  {
   "code": "706870000",
   "why": "acute pulmonary embolism is a pulmonary vascular disorder, not acute pancreatitis"
  },
  {
   "code": "65710008",
   "why": "acute respiratory failure is a respiratory system dysfunction, not acute pancreatitis"
  },
  {
   "code": "132281000119108",
   "why": "acute deep venous thrombosis is a venous thromboembolic condition, not acute pancreatitis"
  },
  {
   "code": "67782005",
   "why": "acute respiratory distress syndrome is a form of lung injury, not acute pancreatitis"
  },
  {
   "code"
```

