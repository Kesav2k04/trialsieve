### 1. instructions (prompt grounder-v1)

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

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{{"codes": ["4548-4"], "rejected": [{{"code": "718-7", "why": "different analyte"}}],
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

### 4. llm_response (cassette, 113 tok, 20.081s)

```
```json
{
  "names": [
    "eGFR",
    "Estimated glomerular filtration rate",
    "Glomerular filtration rate, estimated",
    "Estimated GFR",
    "eGFR (CKD-EPI)",
    "eGFR (MDRD)",
    "eGFR from serum creatinine",
    "eGFR from cystatin C",
    "eGFR from creatinine and cystatin C",
    "Glomerular filtration rate, calculated"
  ],
  "note": "Standard clinical laboratory lab test names and equation-specific synonyms for calculated GFR"
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
  "Estimated GFR",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from serum creatinine",
  "eGFR from cystatin C",
  "eGFR from creatinine and cystatin C",
  "Glomerular filtration rate, calculated"
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `9a396c7fc2caf2c0`

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

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{"codes": ["4548-4"], "rejected": [{"code": "718-7", "why": "different analyte"}],
  "confidence": "high"}
```

### 8. llm_response (cassette, 298 tok, 21.239s)

```
```json
{
  "codes": [
    "33914-3"
  ],
  "rejected": [
    {
      "code": "38483-4",
      "why": "measures creatinine concentration, not estimated glomerular filtration rate"
    },
    {
      "code": "2160-0",
      "why": "measures creatinine concentration in serum or plasma, not estimated glomerular filtration rate"
    },
    {
      "code": "14959-1",
      "why": "measures urine microalbumin to creatinine ratio, not glomerular filtration rate"
    },
    {
      "code": "8867-4",
      "why": "measures heart rate"
    },
    {
      "code": "9279-1",
      "why": "measures respiratory rate"
    },
    {
      "code": "93034-7",
      "why": "military service status question"
    },
    {
      "code": "99999-3",
      "why": "substance use / behavioral survey question"
    },
    {
      "code": "93030-5",
      "why": "social determinants of health transportation question"
    },
    {
      "code": "1988-5",
      "why": "measures C-reactive protein"
    },
    {
      "code": "75626-2",
      "why": "AUDIT-C alcohol screening score"
    },
    {
      "code": "94040-3",
      "why": "measures adenovirus DNA presence"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
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
  "Estimated GFR",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from serum creatinine",
  "eGFR from cystatin C",
  "eGFR from creatinine and cystatin C",
  "Glomerular filtration rate, calculated"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Estimated GFR",
  "Estimated glomerular filtration rate",
  "Glomerular filtration rate, calculated",
  "Glomerular filtration rate, estimated",
  "eGFR",
  "eGFR (CKD-EPI)",
  "eGFR (MDRD)",
  "eGFR from creatinine and cystatin C",
  "eGFR from cystatin C",
  "eGFR from serum creatinine"
 ]
}
```

