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
 "concept": "Anaemia",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `9a40b61a4b23d545`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Anaemia
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

### 4. llm_response (openai, 164 tok, 3.104s)

```
{
  "names": [
    "Iron deficiency anemia",
    "Vitamin B12 deficiency anemia",
    "Folate deficiency anemia",
    "Aplastic anemia",
    "Hemolytic anemia",
    "Sickle cell anemia",
    "Thalassemia",
    "Anemia of chronic disease",
    "Anemia, aplastic",
    "Anemia, hemolytic",
    "Anemia, sickle cell",
    "Anemia, thalassemia"
  ],
  "note": "These are common sub-types of anemia that a medical record might code instead of the general term."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Iron deficiency anemia",
  "Vitamin B12 deficiency anemia",
  "Folate deficiency anemia",
  "Aplastic anemia",
  "Hemolytic anemia",
  "Sickle cell anemia",
  "Thalassemia",
  "Anemia of chronic disease",
  "Anemia, aplastic",
  "Anemia, hemolytic",
  "Anemia, sickle cell",
  "Anemia, thalassemia"
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
  "code": "271737000",
  "display": "Anemia (disorder)",
  "domain": "condition",
  "n_resources": 145
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
  "code": "127013003",
  "display": "Diabetic renal disease (disorder)",
  "domain": "condition",
  "n_resources": 11
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
 },
 {
  "code": "278860009",
  "display": "Chronic low back pain (finding)",
  "domain": "condition",
  "n_resources": 91
 }
]
```

### 7. llm_request -> granite3.1-dense:8b  cassette `9695e2ae874155c9`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Anaemia
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
         271737000  Anemia (disorder)   (in 145 resources)
          40055000  Chronic sinusitis (disorder)   (in 88 resources)
          82423001  Chronic pain   (in 22 resources)
     1121000119107  Chronic neck pain (finding)   (in 54 resources)
          53741008  Coronary Heart Disease   (in 25 resources)
          26929004  Alzheimer's disease (disorder)   (in 17 resources)
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
         185086009  Chronic obstructive bronchitis (disorder)   (in 2 resources)
         235595009  Gastroesophageal reflux disease (disorder)   (in 2 resources)
         278860009  Chronic low back pain (finding)   (in 91 resources)

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

### 8. llm_response (openai, 39 tok, 4.218s)

```
{
  "codes": ["271737000"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "271737000"
 ],
 "concept": "Anaemia",
 "confidence": "high",
 "displays": [
  "Anemia (disorder)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Iron deficiency anemia",
  "Vitamin B12 deficiency anemia",
  "Folate deficiency anemia",
  "Aplastic anemia",
  "Hemolytic anemia",
  "Sickle cell anemia",
  "Thalassemia",
  "Anemia of chronic disease",
  "Anemia, aplastic",
  "Anemia, hemolytic",
  "Anemia, sickle cell",
  "Anemia, thalassemia"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Anemia of chronic disease",
  "Anemia, aplastic",
  "Anemia, hemolytic",
  "Anemia, sickle cell",
  "Anemia, thalassemia",
  "Aplastic anemia",
  "Folate deficiency anemia",
  "Hemolytic anemia",
  "Iron deficiency anemia",
  "Sickle cell anemia",
  "Thalassemia",
  "Vitamin B12 deficiency anemia"
 ]
}
```

