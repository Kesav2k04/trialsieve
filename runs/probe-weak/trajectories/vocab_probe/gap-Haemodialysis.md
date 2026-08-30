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
 "concept": "Haemodialysis",
 "domain": "procedure",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `f61f87cb30950265`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Haemodialysis
Record domain: procedure

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

### 4. llm_response (openai, 219 tok, 3.943s)

```
{
  "names": [
    "Haemodialysis",
    "Chronic Haemodialysis",
    "Acute Haemodialysis",
    "Haemodialysis Treatment",
    "In-Center Haemodialysis",
    "Home Haemodialysis",
    "Nocturnal Haemodialysis",
    "Sustained Low Efficiency Dialysis (SLED)",
    "Short Daily Haemodialysis (SDH)",
    "Daily Haemodialysis",
    "Haemodialysis Session",
    "Haemodialysis Procedure",
    "Haemodialysis Therapy",
    "Haemodialysis Access",
    "Vascular Access for Haemodialysis"
  ],
  "note": "These are general terms for haemodialysis procedures. The specific terms used may vary based on the clinical setting and patient's condition."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "procedure",
 "limit": 12,
 "terms": [
  "Haemodialysis",
  "Chronic Haemodialysis",
  "Acute Haemodialysis",
  "Haemodialysis Treatment",
  "In-Center Haemodialysis",
  "Home Haemodialysis",
  "Nocturnal Haemodialysis",
  "Sustained Low Efficiency Dialysis (SLED)",
  "Short Daily Haemodialysis (SDH)",
  "Daily Haemodialysis",
  "Haemodialysis Session",
  "Haemodialysis Procedure",
  "Haemodialysis Therapy",
  "Haemodialysis Access",
  "Vascular Access for Haemodialysis"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "302497006",
  "display": "Hemodialysis (procedure)",
  "domain": "procedure",
  "n_resources": 10
 },
 {
  "code": "33195004",
  "display": "Teleradiotherapy procedure (procedure)",
  "domain": "procedure",
  "n_resources": 68
 },
 {
  "code": "367336001",
  "display": "Chemotherapy (procedure)",
  "domain": "procedure",
  "n_resources": 56
 },
 {
  "code": "180256009",
  "display": "Subcutaneous immunotherapy",
  "domain": "procedure",
  "n_resources": 1160
 },
 {
  "code": "229064008",
  "display": "Movement therapy (regime/therapy)",
  "domain": "procedure",
  "n_resources": 430
 },
 {
  "code": "228557008",
  "display": "Cognitive and behavioral therapy",
  "domain": "procedure",
  "n_resources": 248
 },
 {
  "code": "703423002",
  "display": "Combined chemotherapy and radiation therapy (procedure)",
  "domain": "procedure",
  "n_resources": 235
 },
 {
  "code": "15081005",
  "display": "Pulmonary rehabilitation (regime/therapy)",
  "domain": "procedure",
  "n_resources": 81
 },
 {
  "code": "408919008",
  "display": "Psychosocial care (regime/therapy)",
  "domain": "procedure",
  "n_resources": 7
 },
 {
  "code": "26763009",
  "display": "Controlled ventilation procedure and therapy, initiation and management (procedure)",
  "domain": "procedure",
  "n_resources": 10
 },
 {
  "code": "76746007",
  "display": "Cardiovascular stress testing (procedure)",
  "domain": "procedure",
  "n_resources": 4
 },
 {
  "code": "265764009",
  "display": "Renal dialysis (
```

### 7. llm_request -> granite3.1-dense:8b  cassette `02e46daad598f905`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Haemodialysis
Record domain: procedure
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         302497006  Hemodialysis (procedure)   (in 10 resources)
          33195004  Teleradiotherapy procedure (procedure)   (in 68 resources)
         367336001  Chemotherapy (procedure)   (in 56 resources)
         180256009  Subcutaneous immunotherapy   (in 1160 resources)
         229064008  Movement therapy (regime/therapy)   (in 430 resources)
         228557008  Cognitive and behavioral therapy   (in 248 resources)
         703423002  Combined chemotherapy and radiation therapy (procedure)   (in 235 resources)
          15081005  Pulmonary rehabilitation (regime/therapy)   (in 81 resources)
         408919008  Psychosocial care (regime/therapy)   (in 7 resources)
          26763009  Controlled ventilation procedure and therapy, initiation and managemen   (in 10 resources)
          76746007  Cardiovascular stress testing (procedure)   (in 4 resources)
         265764009  Renal dialysis (procedure)   (in 1079 resources)

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

### 8. llm_response (openai, 129 tok, 2.702s)

```
{
  "codes": ["265764009"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}

Explanation: The concept is Haemodialysis, which is a type of Renal dialysis. The code 265764009 in the candidate list matches this concept as it denotes Renal dialysis (procedure). The other candidates either denote different procedures or are broader concepts. Therefore, no rejections are necessary, and the confidence level is high due to the clear match.
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "265764009"
 ],
 "concept": "Haemodialysis",
 "confidence": "high",
 "displays": [
  "Renal dialysis (procedure)"
 ],
 "domain": "procedure",
 "expanded_names": [
  "Haemodialysis",
  "Chronic Haemodialysis",
  "Acute Haemodialysis",
  "Haemodialysis Treatment",
  "In-Center Haemodialysis",
  "Home Haemodialysis",
  "Nocturnal Haemodialysis",
  "Sustained Low Efficiency Dialysis (SLED)",
  "Short Daily Haemodialysis (SDH)",
  "Daily Haemodialysis",
  "Haemodialysis Session",
  "Haemodialysis Procedure",
  "Haemodialysis Therapy",
  "Haemodialysis Access",
  "Vascular Access for Haemodialysis"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Acute Haemodialysis",
  "Chronic Haemodialysis",
  "Daily Haemodialysis",
  "Haemodialysis",
  "Haemodialysis Access",
  "Haemodialysis Procedure",
  "Haemodialysis Session",
  "Haemodialysis Therapy",
  "Haemodialysis Treatment",
  "Home Haemodialysis",
  "In-Center Haemodialysis",
  "Nocturnal Haemodialysis",
  "Short Daily Haemodialysis (SDH)",
  "Sustained Low Efficiency Dialysis (SLED)",
  "Vascular Access for Haemodialysis"
 ]
}
```

