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
 "concept": "Urine albumin to creatinine ratio",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `b162ddf4be917154`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Urine albumin to creatinine ratio
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

### 4. llm_response (cassette, 127 tok, 18.672s)

```
```json
{
  "names": [
    "Albumin/creatinine ratio, urine",
    "Urine albumin to creatinine ratio",
    "uACR",
    "Urine ACR",
    "Microalbumin/creatinine ratio, urine",
    "Urine microalbumin to creatinine ratio",
    "Albumin to creatinine ratio",
    "Microalbumin/creatinine ratio",
    "Random urine albumin/creatinine ratio",
    "Albumin/Creatinine, Spot Urine"
  ],
  "note": "Common lab test names, abbreviations, and synonyms for spot urine albumin-to-creatinine ratio measurements."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Albumin/creatinine ratio, urine",
  "Urine albumin to creatinine ratio",
  "uACR",
  "Urine ACR",
  "Microalbumin/creatinine ratio, urine",
  "Urine microalbumin to creatinine ratio",
  "Albumin to creatinine ratio",
  "Microalbumin/creatinine ratio",
  "Random urine albumin/creatinine ratio",
  "Albumin/Creatinine, Spot Urine"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "14959-1",
  "display": "Microalbumin Creatinine Ratio",
  "domain": "observation",
  "n_resources": 695
 },
 {
  "code": "5767-9",
  "display": "Appearance of Urine",
  "domain": "observation",
  "n_resources": 508
 },
 {
  "code": "32167-9",
  "display": "Clarity of Urine",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5778-6",
  "display": "Color of Urine",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "38483-4",
  "display": "Creatinine",
  "domain": "observation",
  "n_resources": 2521
 },
 {
  "code": "1751-7",
  "display": "Albumin [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 882
 },
 {
  "code": "2160-0",
  "display": "Creatinine [Mass/volume] in Serum or Plasma",
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
  "code": "20454-5",
  "display": "Protein [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `b9f4c25ded9b9375`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Urine albumin to creatinine ratio
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
           14959-1  Microalbumin Creatinine Ratio   (in 695 resources)
            5767-9  Appearance of Urine   (in 508 resources)
           32167-9  Clarity of Urine   (in 254 resources)
            5778-6  Color of Urine   (in 254 resources)
           38483-4  Creatinine   (in 2521 resources)
            1751-7  Albumin [Mass/volume] in Serum or Plasma   (in 882 resources)
            2160-0  Creatinine [Mass/volume] in Serum or Plasma   (in 181 resources)
            5792-7  Glucose [Mass/volume] in Urine by Test strip   (in 254 resources)
            5797-6  Ketones [Mass/volume] in Urine by Test strip   (in 254 resources)
            5803-2  pH of Urine by Test strip   (in 254 resources)
            5804-0  Protein [Mass/volume] in Urine by Test strip   (in 254 resources)
           20454-5  Protein [Presence] in Urine by Test strip   (in 254 resources)

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

### 8. llm_response (cassette, 373 tok, 19.881s)

```
```json
{
  "codes": [
    "14959-1"
  ],
  "rejected": [
    {
      "code": "5767-9",
      "why": "measures physical appearance of urine rather than albumin to creatinine ratio"
    },
    {
      "code": "32167-9",
      "why": "measures urine clarity rather than albumin to creatinine ratio"
    },
    {
      "code": "5778-6",
      "why": "measures urine color rather than albumin to creatinine ratio"
    },
    {
      "code": "38483-4",
      "why": "measures isolated creatinine rather than albumin to creatinine ratio"
    },
    {
      "code": "1751-7",
      "why": "measures albumin mass concentration in serum or plasma, not urine albumin to creatinine ratio"
    },
    {
      "code": "2160-0",
      "why": "measures creatinine mass concentration in serum or plasma, not urine albumin to creatinine ratio"
    },
    {
      "code": "5792-7",
      "why": "measures urine glucose rather than albumin to creatinine ratio"
    },
    {
      "code": "5797-6",
      "why": "measures urine ketones rather than albumin to creatinine ratio"
    },
    {
      "code": "5803-2",
      "why": "measures urine pH rather than albumin to creatinine ratio"
    },
    {
      "code": "5804-0",
      "why": "measures urine total protein by dipstick rather than quantitative albumin to creatinine ratio"
    },
    {
      "code": "20454-5",
      "why": "measures qualitative urine protein presence rather than albumin to creatinine ratio"
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
  "14959-1"
 ],
 "concept": "Urine albumin to creatinine ratio",
 "confidence": "high",
 "displays": [
  "Microalbumin Creatinine Ratio"
 ],
 "domain": "observation",
 "expanded_names": [
  "Albumin/creatinine ratio, urine",
  "Urine albumin to creatinine ratio",
  "uACR",
  "Urine ACR",
  "Microalbumin/creatinine ratio, urine",
  "Urine microalbumin to creatinine ratio",
  "Albumin to creatinine ratio",
  "Microalbumin/creatinine ratio",
  "Random urine albumin/creatinine ratio",
  "Albumin/Creatinine, Spot Urine"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Albumin to creatinine ratio",
  "Albumin/Creatinine, Spot Urine",
  "Albumin/creatinine ratio, urine",
  "Microalbumin/creatinine ratio",
  "Microalbumin/creatinine ratio, urine",
  "Random urine albumin/creatinine ratio",
  "Urine ACR",
  "Urine albumin to creatinine ratio",
  "Urine microalbumin to creatinine ratio",
  "uACR"
 ]
}
```

