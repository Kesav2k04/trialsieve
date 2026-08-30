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
 "concept": "Simvastatin",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `f57fd160022637b4`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Simvastatin
Record domain: medication

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

### 4. llm_response (openai, 122 tok, 2.591s)

```
{
  "names": [
    "simvastatin",
    "Zocor",
    "generic simvastatin",
    "40 mg simvastatin",
    "simvastatin 20 mg tablet",
    "simvastatin 80 mg tablet",
    "simvastatin/ezetimibe combination"
  ],
  "note": "Simvastatin is a medication used to lower cholesterol and triglyceride levels in the blood. It belongs to the class of drugs known as statins."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "simvastatin",
  "Zocor",
  "generic simvastatin",
  "40 mg simvastatin",
  "simvastatin 20 mg tablet",
  "simvastatin 80 mg tablet",
  "simvastatin/ezetimibe combination"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "312961",
  "display": "Simvastatin 20 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 268
 },
 {
  "code": "314231",
  "display": "Simvastatin 10 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 904
 },
 {
  "code": "313988",
  "display": "Furosemide 40 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 34
 },
 {
  "code": "259255",
  "display": "Atorvastatin 80 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 4
 },
 {
  "code": "312615",
  "display": "predniSONE 20 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 1
 },
 {
  "code": "314077",
  "display": "lisinopril 20 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 1
 },
 {
  "code": "897718",
  "display": "Verapamil Hydrochloride 40 MG",
  "domain": "medication",
  "n_resources": 702
 },
 {
  "code": "1860480",
  "display": "1 ML DOCEtaxel 20 MG/ML Injection",
  "domain": "medication",
  "n_resources": 7
 },
 {
  "code": "1091392",
  "display": "Methylphenidate Hydrochloride 20 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 2
 },
 {
  "code": "596926",
  "display": "duloxetine 20 MG Delayed Release Oral Capsule",
  "domain": "medication",
  "n_resources": 3
 }
]
```

### 7. llm_request -> granite3.1-dense:8b  cassette `7aba4f4f5a9048a0`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Simvastatin
Record domain: medication
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            312961  Simvastatin 20 MG Oral Tablet   (in 268 resources)
            314231  Simvastatin 10 MG Oral Tablet   (in 904 resources)
            313988  Furosemide 40 MG Oral Tablet   (in 34 resources)
            259255  Atorvastatin 80 MG Oral Tablet   (in 4 resources)
            312615  predniSONE 20 MG Oral Tablet   (in 1 resources)
            314077  lisinopril 20 MG Oral Tablet   (in 1 resources)
            897718  Verapamil Hydrochloride 40 MG   (in 702 resources)
           1860480  1 ML DOCEtaxel 20 MG/ML Injection   (in 7 resources)
           1091392  Methylphenidate Hydrochloride 20 MG Oral Tablet   (in 2 resources)
            596926  duloxetine 20 MG Delayed Release Oral Capsule   (in 3 resources)

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

### 8. llm_response (openai, 141 tok, 2.957s)

```
{
  "codes": ["312961", "314231"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}

Explanation: The concept is Simvastatin, a medication. Both "Simvastatin 20 MG Oral Tablet" (code 312961) and "Simvastatin 10 MG Oral Tablet" (code 314231) are matches as they contain the ingredient Simvastatin. No codes were rejected, and the confidence is high due to the clear match with the concept.
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "312961",
  "314231"
 ],
 "concept": "Simvastatin",
 "confidence": "high",
 "displays": [
  "Simvastatin 20 MG Oral Tablet",
  "Simvastatin 10 MG Oral Tablet"
 ],
 "domain": "medication",
 "expanded_names": [
  "simvastatin",
  "Zocor",
  "generic simvastatin",
  "40 mg simvastatin",
  "simvastatin 20 mg tablet",
  "simvastatin 80 mg tablet",
  "simvastatin/ezetimibe combination"
 ],
 "matched_names": [
  "simvastatin"
 ],
 "reason": "2 of 10 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "40 mg simvastatin",
  "Zocor",
  "generic simvastatin",
  "simvastatin 20 mg tablet",
  "simvastatin 80 mg tablet",
  "simvastatin/ezetimibe combination"
 ]
}
```

