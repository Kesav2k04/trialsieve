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

### 4. llm_response (cassette, 103 tok, 18.560s)

```
```json
{
  "names": [
    "Hemoglobin A1c",
    "HbA1c",
    "Glycated hemoglobin",
    "Glycosylated hemoglobin",
    "Glycated haemoglobin",
    "Glycosylated haemoglobin",
    "Glycohemoglobin",
    "Total glycated hemoglobin",
    "GHb",
    "Hemoglobin A1c/Hemoglobin.total in Blood"
  ],
  "note": "Common laboratory names, abbreviations, and spelling variants for glycated hemoglobin measurements."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Hemoglobin A1c",
  "HbA1c",
  "Glycated hemoglobin",
  "Glycosylated hemoglobin",
  "Glycated haemoglobin",
  "Glycosylated haemoglobin",
  "Glycohemoglobin",
  "Total glycated hemoglobin",
  "GHb",
  "Hemoglobin A1c/Hemoglobin.total in Blood"
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `b101cf303951e813`

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

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{"codes": ["4548-4"], "rejected": [{"code": "718-7", "why": "different analyte"}],
  "confidence": "high"}
```

### 8. llm_response (cassette, 340 tok, 19.882s)

```
```json
{
  "codes": [
    "4548-4"
  ],
  "rejected": [
    {
      "code": "718-7",
      "why": "measures total blood hemoglobin concentration, not the glycated fraction (HbA1c)"
    },
    {
      "code": "5794-3",
      "why": "urine dipstick test for blood/hemoglobin, not glycated hemoglobin"
    },
    {
      "code": "57905-2",
      "why": "fecal occult blood test detecting gastrointestinal hemoglobin, not glycated hemoglobin"
    },
    {
      "code": "2093-3",
      "why": "different analyte (lipid measurement)"
    },
    {
      "code": "1975-2",
      "why": "different analyte (liver/biliary function marker)"
    },
    {
      "code": "76504-0",
      "why": "screening questionnaire score (HARK interpersonal violence screen)"
    },
    {
      "code": "72106-8",
      "why": "cognitive screening assessment score (Mini-Mental State Examination)"
    },
    {
      "code": "42719-5",
      "why": "different analyte (bilirubin assessment)"
    },
    {
      "code": "82667-7",
      "why": "screening questionnaire score (DAST-10 drug abuse screening test)"
    },
    {
      "code": "75626-2",
      "why": "screening questionnaire score (AUDIT-C alcohol consumption test)"
    },
    {
      "code": "2028-9",
      "why": "different analyte (electrolytes/acid-base balance measurement)"
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
  "4548-4"
 ],
 "concept": "Glycated haemoglobin",
 "confidence": "high",
 "displays": [
  "Hemoglobin A1c/Hemoglobin.total in Blood"
 ],
 "domain": "observation",
 "expanded_names": [
  "Hemoglobin A1c",
  "HbA1c",
  "Glycated hemoglobin",
  "Glycosylated hemoglobin",
  "Glycated haemoglobin",
  "Glycosylated haemoglobin",
  "Glycohemoglobin",
  "Total glycated hemoglobin",
  "GHb",
  "Hemoglobin A1c/Hemoglobin.total in Blood"
 ],
 "matched_names": [
  "hemoglobin a1c",
  "hemoglobin a1c/hemoglobin.total in blood"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "GHb",
  "Glycated haemoglobin",
  "Glycated hemoglobin",
  "Glycohemoglobin",
  "Glycosylated haemoglobin",
  "Glycosylated hemoglobin",
  "HbA1c",
  "Total glycated hemoglobin"
 ]
}
```

