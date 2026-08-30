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
 "concept": "Estimated glomerular filtration rate",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `bfbb80f913a495f0`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Estimated glomerular filtration rate
Record domain: observation

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

### 4. llm_response (openai, 248 tok, 4.552s)

```
{
  "names": [
    "Estimated Glomerular Filtration Rate (eGFR)",
    "Creatinine Clearance",
    "Serum Creatinine-based Calculation",
    "Modification of Diet in Renal Disease (MDRD) Study Equation",
    "Chronic Kidney Disease Epidemiology Collaboration (CKD-EPI) Equation",
    "Cockcroft-Gault Formula",
    "Simplified Modification of Diet in Renal Disease (sMDRD)",
    "Creatinine Clearance by CKD-EPI",
    "Creatinine Clearance by MDRD",
    "Creatinine Clearance by Cockcroft-Gault",
    "Serum Creatinine-based GFR Estimation",
    "eGFR by CKD-EPI",
    "eGFR by MDRD",
    "eGFR by Cockcroft-Gault"
  ],
  "note": "These are the various methods and equations used to estimate the glomerular filtration rate (GFR) in clinical practice."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Estimated Glomerular Filtration Rate (eGFR)",
  "Creatinine Clearance",
  "Serum Creatinine-based Calculation",
  "Modification of Diet in Renal Disease (MDRD) Study Equation",
  "Chronic Kidney Disease Epidemiology Collaboration (CKD-EPI) Equation",
  "Cockcroft-Gault Formula",
  "Simplified Modification of Diet in Renal Disease (sMDRD)",
  "Creatinine Clearance by CKD-EPI",
  "Creatinine Clearance by MDRD",
  "Creatinine Clearance by Cockcroft-Gault",
  "Serum Creatinine-based GFR Estimation",
  "eGFR by CKD-EPI",
  "eGFR by MDRD",
  "eGFR by Cockcroft-Gault"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "38483-4",
  "display": "Creatinine",
  "domain": "observation",
  "n_resources": 2521
 },
 {
  "code": "2160-0",
  "display": "Creatinine [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 181
 },
 {
  "code": "33914-3",
  "display": "Glomerular filtration rate/1.73 sq M.predicted",
  "domain": "observation",
  "n_resources": 1583
 },
 {
  "code": "14959-1",
  "display": "Microalbumin Creatinine Ratio",
  "domain": "observation",
  "n_resources": 695
 },
 {
  "code": "10834-0",
  "display": "Globulin [Mass/volume] in Serum by calculation",
  "domain": "observation",
  "n_resources": 703
 },
 {
  "code": "8867-4",
  "display": "Heart rate",
  "domain": "observation",
  "n_resources": 5870
 },
 {
  "code": "9279-1",
  "display": "Respiratory rate",
  "domain": "observation",
  "n_resources": 5870
 },
 {
  "code": "88021-1",
  "display": "Objective assessment of cardiovascular disease NYHA",
  "domain": "observation",
  "n_resources": 10
 }
]
```

### 7. llm_request -> granite3.1-dense:8b  cassette `a09e663c042cfac8`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Estimated glomerular filtration rate
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
           38483-4  Creatinine   (in 2521 resources)
            2160-0  Creatinine [Mass/volume] in Serum or Plasma   (in 181 resources)
           33914-3  Glomerular filtration rate/1.73 sq M.predicted   (in 1583 resources)
           14959-1  Microalbumin Creatinine Ratio   (in 695 resources)
           10834-0  Globulin [Mass/volume] in Serum by calculation   (in 703 resources)
            8867-4  Heart rate   (in 5870 resources)
            9279-1  Respiratory rate   (in 5870 resources)
           88021-1  Objective assessment of cardiovascular disease NYHA   (in 10 resources)

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

### 8. llm_response (openai, 175 tok, 4.640s)

```
{
  "codes": ["33914-3"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}

Explanation: The concept is "Estimated glomerular filtration rate", which refers to a measurement of kidney function. Among the candidates, "33914-3 Glomerular filtration rate/1.73 sq M.predicted" is the most appropriate match as it directly relates to the glomerular filtration rate. The other options either refer to different measurements (creatinine levels), related concepts (heart or respiratory rates), or broader categories of health conditions (cardiovascular disease assessment). Therefore, "33914-3" is the best match for this concept in this context.
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "33914-3"
 ],
 "concept": "Estimated glomerular filtration rate",
 "confidence": "high",
 "displays": [
  "Glomerular filtration rate/1.73 sq M.predicted"
 ],
 "domain": "observation",
 "expanded_names": [
  "Estimated Glomerular Filtration Rate (eGFR)",
  "Creatinine Clearance",
  "Serum Creatinine-based Calculation",
  "Modification of Diet in Renal Disease (MDRD) Study Equation",
  "Chronic Kidney Disease Epidemiology Collaboration (CKD-EPI) Equation",
  "Cockcroft-Gault Formula",
  "Simplified Modification of Diet in Renal Disease (sMDRD)",
  "Creatinine Clearance by CKD-EPI",
  "Creatinine Clearance by MDRD",
  "Creatinine Clearance by Cockcroft-Gault",
  "Serum Creatinine-based GFR Estimation",
  "eGFR by CKD-EPI",
  "eGFR by MDRD",
  "eGFR by Cockcroft-Gault"
 ],
 "matched_names": [],
 "reason": "1 of 8 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Chronic Kidney Disease Epidemiology Collaboration (CKD-EPI) Equation",
  "Cockcroft-Gault Formula",
  "Creatinine Clearance",
  "Creatinine Clearance by CKD-EPI",
  "Creatinine Clearance by Cockcroft-Gault",
  "Creatinine Clearance by MDRD",
  "Estimated Glomerular Filtration Rate (eGFR)",
  "Modification of Diet in Renal Disease (MDRD) Study Equation",
  "Serum Creatinine-based Calculation",
  "Serum Creatinine-based GFR Estimation",
  "Simplified Modification of Diet in Renal Disease (sMDRD)",
  "eGFR by CKD-EPI",
  "eGFR by Cockcroft-Gault",
  "eGFR by MDRD"
 ]
}
```

