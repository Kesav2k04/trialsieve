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
 "concept": "Glycated haemoglobin",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `b821381ee3c33f34`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Glycated haemoglobin
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

### 4. llm_response (openai, 210 tok, 3.667s)

```
{
  "names": [
    "Glycated Hemoglobin (HbA1c)",
    "Glycohemoglobin",
    "Hemoglobin A1C",
    "A1C Level",
    "Glycosylated Hemoglobin",
    "HbA1c Test",
    "Glucose-Hemoglobin",
    "HbA1c Value",
    "Glycated Red Blood Cells",
    "HbA1c Assay",
    "Glycated Erythrocytes",
    "HbA1c Measurement",
    "Glycosylated Hb",
    "HbA1c Screening"
  ],
  "note": "These are the various names and synonyms for Glycated Hemoglobin, a clinical concept used in laboratory tests to measure average blood glucose levels over the past 2-3 months."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Glycated Hemoglobin (HbA1c)",
  "Glycohemoglobin",
  "Hemoglobin A1C",
  "A1C Level",
  "Glycosylated Hemoglobin",
  "HbA1c Test",
  "Glucose-Hemoglobin",
  "HbA1c Value",
  "Glycated Red Blood Cells",
  "HbA1c Assay",
  "Glycated Erythrocytes",
  "HbA1c Measurement",
  "Glycosylated Hb",
  "HbA1c Screening"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "4548-4",
  "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
  "domain": "observation",
  "n_resources": 1874
 },
 {
  "code": "2339-0",
  "display": "Glucose",
  "domain": "observation",
  "n_resources": 2521
 },
 {
  "code": "718-7",
  "display": "Hemoglobin [Mass/volume] in Blood",
  "domain": "observation",
  "n_resources": 1398
 },
 {
  "code": "789-8",
  "display": "Erythrocytes [#/volume] in Blood by Automated count",
  "domain": "observation",
  "n_resources": 1391
 },
 {
  "code": "2345-7",
  "display": "Glucose [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 181
 },
 {
  "code": "5792-7",
  "display": "Glucose [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5797-6",
  "display": "Ketones [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5803-2",
  "display": "pH of Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5804-0",
  "display": "Protein [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "59461-4",
  "display": "Fall risk level [Morse Fall Scale]",
  "domain": "observation",
  "n_resources": 719
 },
 {
  "code": "20454-5",
  "display": "Protein [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "20505-4",
  "display": "Bilirubin.total [Mass/volume] in Urine by
```

### 7. llm_request -> granite3.1-dense:8b  cassette `aacf67307c49bfd5`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Glycated haemoglobin
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            4548-4  Hemoglobin A1c/Hemoglobin.total in Blood   (in 1874 resources)
            2339-0  Glucose   (in 2521 resources)
             718-7  Hemoglobin [Mass/volume] in Blood   (in 1398 resources)
             789-8  Erythrocytes [#/volume] in Blood by Automated count   (in 1391 resources)
            2345-7  Glucose [Mass/volume] in Serum or Plasma   (in 181 resources)
            5792-7  Glucose [Mass/volume] in Urine by Test strip   (in 254 resources)
            5797-6  Ketones [Mass/volume] in Urine by Test strip   (in 254 resources)
            5803-2  pH of Urine by Test strip   (in 254 resources)
            5804-0  Protein [Mass/volume] in Urine by Test strip   (in 254 resources)
           59461-4  Fall risk level [Morse Fall Scale]   (in 719 resources)
           20454-5  Protein [Presence] in Urine by Test strip   (in 254 resources)
           20505-4  Bilirubin.total [Mass/volume] in Urine by Test strip   (in 254 resources)

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

### 8. llm_response (openai, 62 tok, 3.275s)

```
{
  "codes": ["4548-4"],
  "broader_codes": [],
  "rejected": [
    {
      "code": "718-7",
      "why": "different analyte"
    }
  ],
  "confidence": "high"
}
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "4548-4"
 ],
 "concept": "Glycated haemoglobin",
 "confidence": "high",
 "displays": [
  "Hemoglobin A1c/Hemoglobin.total in Blood"
 ],
 "domain": "observation",
 "expanded_names": [
  "Glycated Hemoglobin (HbA1c)",
  "Glycohemoglobin",
  "Hemoglobin A1C",
  "A1C Level",
  "Glycosylated Hemoglobin",
  "HbA1c Test",
  "Glucose-Hemoglobin",
  "HbA1c Value",
  "Glycated Red Blood Cells",
  "HbA1c Assay",
  "Glycated Erythrocytes",
  "HbA1c Measurement",
  "Glycosylated Hb",
  "HbA1c Screening"
 ],
 "matched_names": [
  "hemoglobin a1c"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "A1C Level",
  "Glucose-Hemoglobin",
  "Glycated Erythrocytes",
  "Glycated Hemoglobin (HbA1c)",
  "Glycated Red Blood Cells",
  "Glycohemoglobin",
  "Glycosylated Hb",
  "Glycosylated Hemoglobin",
  "HbA1c Assay",
  "HbA1c Measurement",
  "HbA1c Screening",
  "HbA1c Test",
  "HbA1c Value"
 ]
}
```

