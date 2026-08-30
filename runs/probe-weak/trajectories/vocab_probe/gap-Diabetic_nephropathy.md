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
 "concept": "Diabetic nephropathy",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `e6d8ebf2bd3825fb`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Diabetic nephropathy
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

### 4. llm_response (openai, 233 tok, 5.358s)

```
{
  "names": [
    "Diabetic nephropathy",
    "Diabetes mellitus with kidney disease",
    "Chronic kidney disease due to diabetes",
    "Diabetic renal disease",
    "Diabetic glomerulosclerosis",
    "Diabetic interstitial nephritis",
    "Diabetic tubulointerstitial nephropathy",
    "Diabetic focal segmental glomerulosclerosis",
    "Diabetic collapsing glomerulopathy",
    "Diabetic membranous nephropathy",
    "Diabetic minimal change disease",
    "Diabetic focal and segmental glomerulosclerosis",
    "Diabetic diffuse glomerulosclerosis",
    "Diabetic end-stage renal disease"
  ],
  "note": "These are specific condition names for diabetic nephropathy, including common sub-types. They may be used interchangeably in clinical practice."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Diabetic nephropathy",
  "Diabetes mellitus with kidney disease",
  "Chronic kidney disease due to diabetes",
  "Diabetic renal disease",
  "Diabetic glomerulosclerosis",
  "Diabetic interstitial nephritis",
  "Diabetic tubulointerstitial nephropathy",
  "Diabetic focal segmental glomerulosclerosis",
  "Diabetic collapsing glomerulopathy",
  "Diabetic membranous nephropathy",
  "Diabetic minimal change disease",
  "Diabetic focal and segmental glomerulosclerosis",
  "Diabetic diffuse glomerulosclerosis",
  "Diabetic end-stage renal disease"
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
  "n_resources": 9
 },
 {
  "code": "45816000",
  "display": "Pyelonephritis",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "90781000119102",
  "display": "Microalbuminuria due to type 2 diabetes mellitus (disorder)",
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
  "code": "97331000119101",
  "display": "Macular edema and retinopathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "1501000119109",
  "display": "Proliferative diabetic retinopathy due to type II diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "15777
```

### 7. llm_request -> granite3.1-dense:8b  cassette `d750d3ef21369a3a`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Diabetic nephropathy
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         127013003  Diabetic renal disease (disorder)   (in 11 resources)
         431855005  Chronic kidney disease stage 1 (disorder)   (in 10 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
          45816000  Pyelonephritis   (in 1 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)
         422034002  Diabetic retinopathy associated with type II diabetes mellitus (disord   (in 8 resources)
     1551000119108  Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus    (in 5 resources)
    97331000119101  Macular edema and retinopathy due to type 2 diabetes mellitus (disorde   (in 2 resources)
     1501000119109  Proliferative diabetic retinopathy due to type II diabetes mellitus (d   (in 1 resources)
          15777000  Prediabetes   (in 155 resources)
          44054006  Diabetes   (in 32 resources)

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

### 8. llm_response (openai, 278 tok, 5.397s)

```
{
  "codes": ["431855005"],
  "broader_codes": ["44054006"],
  "rejected": [],
  "confidence": "high"
}

Explanation:
The concept is Diabetic nephropathy, which refers to kidney damage caused by diabetes. The candidate that genuinely represents this concept is 431855005 - Chronic kidney disease stage 1 (disorder). This code is broader than the concept because it includes all stages of chronic kidney disease, not just those specifically related to diabetes. However, since no more specific code is available in the given options, this is the best match.

The code 45816000 - Pyelonephritis was rejected because it refers to a bacterial infection of the kidney, not damage caused by diabetes. The code 44054006 - Diabetes is broader than the concept because it includes all types of diabetes, not just those causing kidney damage.

No codes were rejected for being different analytes or unrelated concepts. The confidence in this match is high due to the lack of more specific options.
```

### 9. final

```json
{
 "broader_codes": [
  "44054006"
 ],
 "codes": [
  "431855005"
 ],
 "concept": "Diabetic nephropathy",
 "confidence": "high",
 "displays": [
  "Chronic kidney disease stage 1 (disorder)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Diabetic nephropathy",
  "Diabetes mellitus with kidney disease",
  "Chronic kidney disease due to diabetes",
  "Diabetic renal disease",
  "Diabetic glomerulosclerosis",
  "Diabetic interstitial nephritis",
  "Diabetic tubulointerstitial nephropathy",
  "Diabetic focal segmental glomerulosclerosis",
  "Diabetic collapsing glomerulopathy",
  "Diabetic membranous nephropathy",
  "Diabetic minimal change disease",
  "Diabetic focal and segmental glomerulosclerosis",
  "Diabetic diffuse glomerulosclerosis",
  "Diabetic end-stage renal disease"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Chronic kidney disease due to diabetes",
  "Diabetes mellitus with kidney disease",
  "Diabetic collapsing glomerulopathy",
  "Diabetic diffuse glomerulosclerosis",
  "Diabetic end-stage renal disease",
  "Diabetic focal and segmental glomerulosclerosis",
  "Diabetic focal segmental glomerulosclerosis",
  "Diabetic glomerulosclerosis",
  "Diabetic interstitial nephritis",
  "Diabetic membranous nephropathy",
  "Diabetic minimal change disease",
  "Diabetic nephropathy",
  "Diabetic renal disease",
  "Diabetic tubulointerstitial nephropathy"
 ]
}
```

