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
 "concept": "Systolic blood pressure",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `b4c29c05277c197f`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Systolic blood pressure
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

### 4. llm_response (openai, 177 tok, 4.004s)

```
{
  "names": [
    "Systolic blood pressure",
    "SBP",
    "Blood Pressure, Systolic",
    "Systolic Arterial Pressure",
    "Systolic Blood Pressure Measurement",
    "Systolic BP",
    "Systolic Aortic Pressure",
    "Systolic Peripheral Pressure",
    "Systolic Vascular Pressure",
    "Systolic Cardiac Output Pressure",
    "Systolic Blood Flow Pressure",
    "Systolic Hemodynamic Pressure",
    "Systolic Arterial Pulse Pressure"
  ],
  "note": "These are general terms used to describe systolic blood pressure in clinical practice. The specific term used may vary depending on the context and the recording system."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Systolic blood pressure",
  "SBP",
  "Blood Pressure, Systolic",
  "Systolic Arterial Pressure",
  "Systolic Blood Pressure Measurement",
  "Systolic BP",
  "Systolic Aortic Pressure",
  "Systolic Peripheral Pressure",
  "Systolic Vascular Pressure",
  "Systolic Cardiac Output Pressure",
  "Systolic Blood Flow Pressure",
  "Systolic Hemodynamic Pressure",
  "Systolic Arterial Pulse Pressure"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "8480-6",
  "display": "Systolic Blood Pressure",
  "domain": "observation",
  "n_resources": 6103
 },
 {
  "code": "2703-7",
  "display": "Oxygen [Partial pressure] in Arterial blood",
  "domain": "observation",
  "n_resources": 33
 },
 {
  "code": "2019-8",
  "display": "Carbon dioxide [Partial pressure] in Arterial blood",
  "domain": "observation",
  "n_resources": 33
 },
 {
  "code": "85354-9",
  "display": "Blood Pressure",
  "domain": "observation",
  "n_resources": 6071
 },
 {
  "code": "55284-4",
  "display": "Blood Pressure",
  "domain": "observation",
  "n_resources": 32
 },
 {
  "code": "8462-4",
  "display": "Diastolic Blood Pressure",
  "domain": "observation",
  "n_resources": 6103
 },
 {
  "code": "8478-0",
  "display": "Mean blood pressure",
  "domain": "observation",
  "n_resources": 6
 },
 {
  "code": "59408-5",
  "display": "Oxygen saturation in Arterial blood by Pulse oximetry",
  "domain": "observation",
  "n_resources": 247
 },
 {
  "code": "2744-1",
  "display": "pH of Arterial blood",
  "domain": "observation",
  "n_resources": 33
 },
 {
  "code": "2708-6",
  "display": "Oxygen saturation in Arterial blood",
  "domain": "observation",
  "n_resources": 247
 },
 {
  "code": "1960-4",
  "display": "Bicarbonate [Moles/volume] in Arterial blood",
  "domain": "observation",
  "n_resources": 33
 },
 {
  "code": "88021-1",
  "display": "Objective assessment of cardiovascular disease NYHA",
  "domain": "observation",
  "n_resources": 10
 }
]
```

### 7. llm_request -> granite3.1-dense:8b  cassette `b55d8f8f0d02d76a`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Systolic blood pressure
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            8480-6  Systolic Blood Pressure   (in 6103 resources)
            2703-7  Oxygen [Partial pressure] in Arterial blood   (in 33 resources)
            2019-8  Carbon dioxide [Partial pressure] in Arterial blood   (in 33 resources)
           85354-9  Blood Pressure   (in 6071 resources)
           55284-4  Blood Pressure   (in 32 resources)
            8462-4  Diastolic Blood Pressure   (in 6103 resources)
            8478-0  Mean blood pressure   (in 6 resources)
           59408-5  Oxygen saturation in Arterial blood by Pulse oximetry   (in 247 resources)
            2744-1  pH of Arterial blood   (in 33 resources)
            2708-6  Oxygen saturation in Arterial blood   (in 247 resources)
            1960-4  Bicarbonate [Moles/volume] in Arterial blood   (in 33 resources)
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

### 8. llm_response (openai, 36 tok, 1.567s)

```
{
  "codes": ["8480-6"],
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
  "8480-6"
 ],
 "concept": "Systolic blood pressure",
 "confidence": "high",
 "displays": [
  "Systolic Blood Pressure"
 ],
 "domain": "observation",
 "expanded_names": [
  "Systolic blood pressure",
  "SBP",
  "Blood Pressure, Systolic",
  "Systolic Arterial Pressure",
  "Systolic Blood Pressure Measurement",
  "Systolic BP",
  "Systolic Aortic Pressure",
  "Systolic Peripheral Pressure",
  "Systolic Vascular Pressure",
  "Systolic Cardiac Output Pressure",
  "Systolic Blood Flow Pressure",
  "Systolic Hemodynamic Pressure",
  "Systolic Arterial Pulse Pressure"
 ],
 "matched_names": [
  "systolic blood pressure"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Blood Pressure, Systolic",
  "SBP",
  "Systolic Aortic Pressure",
  "Systolic Arterial Pressure",
  "Systolic Arterial Pulse Pressure",
  "Systolic BP",
  "Systolic Blood Flow Pressure",
  "Systolic Blood Pressure Measurement",
  "Systolic Cardiac Output Pressure",
  "Systolic Hemodynamic Pressure",
  "Systolic Peripheral Pressure",
  "Systolic Vascular Pressure"
 ]
}
```

