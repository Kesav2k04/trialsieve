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

### 4. llm_response (cassette, 127 tok, 27.152s)

```
```json
{
  "names": [
    "Obesity",
    "Morbid obesity",
    "Severe obesity",
    "Class 1 obesity",
    "Class 2 obesity",
    "Class 3 obesity",
    "Extreme obesity",
    "Exogenous obesity",
    "Abdominal obesity",
    "Central obesity",
    "Childhood obesity",
    "Obesity due to excess calories",
    "Obesity complicating pregnancy",
    "Obesity hypoventilation syndrome"
  ],
  "note": "Includes standard diagnosis terms, severity classes, and clinical subtypes coded in EHR systems."
}
```
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
  "Exogenous obesity",
  "Abdominal obesity",
  "Central obesity",
  "Childhood obesity",
  "Obesity due to excess calories",
  "Obesity complicating pregnancy",
  "Obesity hypoventilation syndrome"
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
  "code": "72892002",
  "display": "Normal pregnancy",
  "domain": "condition",
  "n_resources": 258
 },
 {
  "code": "79586000",
  "display": "Tubal pregnancy",
  "domain": "condition",
  "n_resources": 13
 },
 {
  "code": "237602007",
  "display": "Metabolic syndrome X (disorder)",
  "domain": "condition",
  "n_resources": 29
 },
 {
  "code": "95417003",
  "display": "Primary fibromyalgia syndrome",
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
  "n_resources"
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `7d27e2a8732fe17c`

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
          72892002  Normal pregnancy   (in 258 resources)
          79586000  Tubal pregnancy   (in 13 resources)
         237602007  Metabolic syndrome X (disorder)   (in 29 resources)
          95417003  Primary fibromyalgia syndrome   (in 2 resources)
          67782005  Acute respiratory distress syndrome (disorder)   (in 2 resources)
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)

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

### 8. llm_response (cassette, 318 tok, 30.162s)

```
```json
{
  "codes": [
    "162864005",
    "408512008"
  ],
  "broader_codes": [],
  "rejected": [
    {
      "code": "233678006",
      "why": "childhood asthma is a respiratory disorder"
    },
    {
      "code": "80583007",
      "why": "severe anxiety is a psychiatric condition"
    },
    {
      "code": "72892002",
      "why": "normal pregnancy is an obstetric state"
    },
    {
      "code": "79586000",
      "why": "tubal pregnancy is an ectopic pregnancy condition"
    },
    {
      "code": "237602007",
      "why": "metabolic syndrome is a related cluster of metabolic risk factors, not obesity itself"
    },
    {
      "code": "95417003",
      "why": "primary fibromyalgia syndrome is a chronic musculoskeletal pain disorder"
    },
    {
      "code": "67782005",
      "why": "acute respiratory distress syndrome is a severe pulmonary disorder"
    },
    {
      "code": "431855005",
      "why": "chronic kidney disease stage 1 is a renal disorder"
    },
    {
      "code": "431856006",
      "why": "chronic kidney disease stage 2 is a renal disorder"
    },
    {
      "code": "368581000119106",
      "why": "neuropathy due to type 2 diabetes mellitus is a neurological complication of diabetes"
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
  "Exogenous obesity",
  "Abdominal obesity",
  "Central obesity",
  "Childhood obesity",
  "Obesity due to excess calories",
  "Obesity complicating pregnancy",
  "Obesity hypoventilation syndrome"
 ],
 "matched_names": [
  "obesity"
 ],
 "reason": "2 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Abdominal obesity",
  "Central obesity",
  "Childhood obesity",
  "Class 1 obesity",
  "Class 2 obesity",
  "Class 3 obesity",
  "Exogenous obesity",
  "Extreme obesity",
  "Morbid obesity",
  "Obesity complicating pregnancy",
  "Obesity due to excess calories",
  "Obesity hypoventilation syndrome",
  "Severe obesity"
 ]
}
```

