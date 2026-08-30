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

### 3. llm_request -> gemini-3.7-flash-medium  cassette `787e3f9c7cb36216`

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

### 4. llm_response (cassette, 100 tok, 26.585s)

```
```json
{
  "names": [
    "HbA1c",
    "Hemoglobin A1c",
    "Haemoglobin A1c",
    "Glycated hemoglobin",
    "Glycated haemoglobin",
    "Glycosylated hemoglobin",
    "Glycosylated haemoglobin",
    "Glycohemoglobin",
    "A1c",
    "Hemoglobin A1c/Hemoglobin.total"
  ],
  "note": "Standard measurement names, synonyms, and spelling variations for glycated haemoglobin laboratory tests."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "HbA1c",
  "Hemoglobin A1c",
  "Haemoglobin A1c",
  "Glycated hemoglobin",
  "Glycated haemoglobin",
  "Glycosylated hemoglobin",
  "Glycosylated haemoglobin",
  "Glycohemoglobin",
  "A1c",
  "Hemoglobin A1c/Hemoglobin.total"
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
  "code": "718-7",
  "display": "Hemoglobin [Mass/volume] in Blood",
  "domain": "observation",
  "n_resources": 1398
 },
 {
  "code": "5794-3",
  "display": "Hemoglobin [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "57905-2",
  "display": "Hemoglobin.gastrointestinal [Presence] in Stool by Immunologic method",
  "domain": "observation",
  "n_resources": 25
 },
 {
  "code": "2093-3",
  "display": "Total Cholesterol",
  "domain": "observation",
  "n_resources": 2044
 },
 {
  "code": "1975-2",
  "display": "Bilirubin.total [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 880
 },
 {
  "code": "76504-0",
  "display": "Total score [HARK]",
  "domain": "observation",
  "n_resources": 1156
 },
 {
  "code": "72106-8",
  "display": "Total score [MMSE]",
  "domain": "observation",
  "n_resources": 41
 },
 {
  "code": "42719-5",
  "display": "Total Bilirubin (Elevated)",
  "domain": "observation",
  "n_resources": 2
 },
 {
  "code": "82667-7",
  "display": "Total score [DAST-10]",
  "domain": "observation",
  "n_resources": 1208
 },
 {
  "code": "75626-2",
  "display": "Total score [AUDIT-C]",
  "domain": "observation",
  "n_resources": 1202
 },
 {
  "code": "2028-9",
  "display": "Carbon dioxide, total [Moles/volume] in Serum or Plasma",
  "domain": "observation",
  
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `c79874b18a016978`

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
             718-7  Hemoglobin [Mass/volume] in Blood   (in 1398 resources)
            5794-3  Hemoglobin [Presence] in Urine by Test strip   (in 254 resources)
           57905-2  Hemoglobin.gastrointestinal [Presence] in Stool by Immunologic method   (in 25 resources)
            2093-3  Total Cholesterol   (in 2044 resources)
            1975-2  Bilirubin.total [Mass/volume] in Serum or Plasma   (in 880 resources)
           76504-0  Total score [HARK]   (in 1156 resources)
           72106-8  Total score [MMSE]   (in 41 resources)
           42719-5  Total Bilirubin (Elevated)   (in 2 resources)
           82667-7  Total score [DAST-10]   (in 1208 resources)
           75626-2  Total score [AUDIT-C]   (in 1202 resources)
            2028-9  Carbon dioxide, total [Moles/volume] in Serum or Plasma   (in 181 resources)

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

### 8. llm_response (cassette, 347 tok, 32.286s)

```
```json
{
  "codes": [
    "4548-4"
  ],
  "broader_codes": [],
  "rejected": [
    {
      "code": "718-7",
      "why": "measures total hemoglobin mass concentration in blood, not glycated hemoglobin (HbA1c)"
    },
    {
      "code": "5794-3",
      "why": "measures presence of hemoglobin in urine, not glycated hemoglobin"
    },
    {
      "code": "57905-2",
      "why": "measures fecal occult blood / gastrointestinal hemoglobin in stool, not glycated hemoglobin"
    },
    {
      "code": "2093-3",
      "why": "different analyte (total cholesterol)"
    },
    {
      "code": "1975-2",
      "why": "different analyte (total bilirubin)"
    },
    {
      "code": "76504-0",
      "why": "screening assessment tool score (HARK questionnaire for intimate partner violence)"
    },
    {
      "code": "72106-8",
      "why": "cognitive assessment score (Mini-Mental State Examination)"
    },
    {
      "code": "42719-5",
      "why": "different analyte/finding (elevated total bilirubin)"
    },
    {
      "code": "82667-7",
      "why": "screening assessment tool score (DAST-10 drug abuse screening)"
    },
    {
      "code": "75626-2",
      "why": "screening assessment tool score (AUDIT-C alcohol use screening)"
    },
    {
      "code": "2028-9",
      "why": "different analyte (total carbon dioxide / bicarbonate)"
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
  "4548-4"
 ],
 "concept": "Glycated haemoglobin",
 "confidence": "high",
 "displays": [
  "Hemoglobin A1c/Hemoglobin.total in Blood"
 ],
 "domain": "observation",
 "expanded_names": [
  "HbA1c",
  "Hemoglobin A1c",
  "Haemoglobin A1c",
  "Glycated hemoglobin",
  "Glycated haemoglobin",
  "Glycosylated hemoglobin",
  "Glycosylated haemoglobin",
  "Glycohemoglobin",
  "A1c",
  "Hemoglobin A1c/Hemoglobin.total"
 ],
 "matched_names": [
  "a1c",
  "hemoglobin a1c",
  "hemoglobin a1c/hemoglobin.total"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "MAPPED",
 "unmatched_names": [
  "Glycated haemoglobin",
  "Glycated hemoglobin",
  "Glycohemoglobin",
  "Glycosylated haemoglobin",
  "Glycosylated hemoglobin",
  "Haemoglobin A1c",
  "HbA1c"
 ]
}
```

