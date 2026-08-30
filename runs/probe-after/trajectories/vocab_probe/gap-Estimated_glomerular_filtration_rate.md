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

### 3. llm_request -> gemini-3.7-flash-medium  cassette `d7f9a50fc9c5a717`

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

### 4. llm_response (cassette, 121 tok, 29.655s)

```
```json
{
  "names": [
    "eGFR",
    "Estimated glomerular filtration rate",
    "Glomerular filtration rate, estimated",
    "eGFR (CKD-EPI)",
    "eGFR (MDRD)",
    "eGFR from creatinine",
    "eGFR from cystatin C",
    "eGFRcr",
    "eGFRcys",
    "eGFRcr-cys",
    "Calculated GFR",
    "Glomerular filtration rate/1.73 sq M.predicted"
  ],
  "note": "Includes standard clinical laboratory names, abbreviations, and equation/analyte-specific variants for estimated GFR."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "eGFR",
  "Estimated glomerular filtration rate",
  "Glomerular filtration rate, estimated",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from creatinine",
  "eGFR from cystatin C",
  "eGFRcr",
  "eGFRcys",
  "eGFRcr-cys",
  "Calculated GFR",
  "Glomerular filtration rate/1.73 sq M.predicted"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "33914-3",
  "display": "Glomerular filtration rate/1.73 sq M.predicted",
  "domain": "observation",
  "n_resources": 1583
 },
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
  "code": "14959-1",
  "display": "Microalbumin Creatinine Ratio",
  "domain": "observation",
  "n_resources": 695
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
  "code": "93034-7",
  "display": "Have you been discharged from the armed forces of the United States?",
  "domain": "observation",
  "n_resources": 3835
 },
 {
  "code": "99999-3",
  "display": "A great deal of time is spent in activities necessary to obtain the opioid, use the opioid, or recover from its effects",
  "domain": "observation",
  "n_resources": 5
 },
 {
  "code": "93030-5",
  "display": "Has lack of transportation kept you from medical appointments, meetings, work, or from getting things needed for daily living?",
  "domain": "observation",
  "n_resources": 3835
 },
 {
  "code": "1988-5",
  "display": "C reactive protein [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 72
 },
 {
  "code": "75626-2",
  "display": "Total score [
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `98eac9984f300b97`

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
           33914-3  Glomerular filtration rate/1.73 sq M.predicted   (in 1583 resources)
           38483-4  Creatinine   (in 2521 resources)
            2160-0  Creatinine [Mass/volume] in Serum or Plasma   (in 181 resources)
           14959-1  Microalbumin Creatinine Ratio   (in 695 resources)
            8867-4  Heart rate   (in 5870 resources)
            9279-1  Respiratory rate   (in 5870 resources)
           93034-7  Have you been discharged from the armed forces of the United States?   (in 3835 resources)
           99999-3  A great deal of time is spent in activities necessary to obtain the op   (in 5 resources)
           93030-5  Has lack of transportation kept you from medical appointments, meeting   (in 3835 resources)
            1988-5  C reactive protein [Mass/volume] in Serum or Plasma   (in 72 resources)
           75626-2  Total score [AUDIT-C]   (in 1202 resources)
           94040-3  Adenovirus A+B+C+D+E DNA [Presence] in Respiratory specimen by NAA wit   (in 28 resources)

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

### 8. llm_response (cassette, 314 tok, 28.960s)

```
```json
{
  "codes": [
    "33914-3"
  ],
  "broader_codes": [],
  "rejected": [
    {
      "code": "38483-4",
      "why": "measurement of creatinine, not estimated glomerular filtration rate"
    },
    {
      "code": "2160-0",
      "why": "measurement of serum/plasma creatinine, not estimated glomerular filtration rate"
    },
    {
      "code": "14959-1",
      "why": "urine microalbumin to creatinine ratio, not glomerular filtration rate"
    },
    {
      "code": "8867-4",
      "why": "heart rate vital sign measurement"
    },
    {
      "code": "9279-1",
      "why": "respiratory rate vital sign measurement"
    },
    {
      "code": "93034-7",
      "why": "military service survey assessment question"
    },
    {
      "code": "99999-3",
      "why": "substance use / behavioral survey question"
    },
    {
      "code": "93030-5",
      "why": "transportation needs survey assessment question"
    },
    {
      "code": "1988-5",
      "why": "C-reactive protein inflammatory marker measurement"
    },
    {
      "code": "75626-2",
      "why": "AUDIT-C alcohol consumption screening score"
    },
    {
      "code": "94040-3",
      "why": "adenovirus nucleic acid detection test"
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
  "33914-3"
 ],
 "concept": "Estimated glomerular filtration rate",
 "confidence": "high",
 "displays": [
  "Glomerular filtration rate/1.73 sq M.predicted"
 ],
 "domain": "observation",
 "expanded_names": [
  "eGFR",
  "Estimated glomerular filtration rate",
  "Glomerular filtration rate, estimated",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from creatinine",
  "eGFR from cystatin C",
  "eGFRcr",
  "eGFRcys",
  "eGFRcr-cys",
  "Calculated GFR",
  "Glomerular filtration rate/1.73 sq M.predicted"
 ],
 "matched_names": [
  "glomerular filtration rate/1.73 sq m.predicted"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Calculated GFR",
  "Estimated glomerular filtration rate",
  "Glomerular filtration rate, estimated",
  "eGFR",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from creatinine",
  "eGFR from cystatin C",
  "eGFRcr",
  "eGFRcr-cys",
  "eGFRcys"
 ]
}
```

