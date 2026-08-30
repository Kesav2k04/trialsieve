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

### 4. llm_response (cassette, 134 tok, 29.904s)

```
```json
{
  "names": [
    "Albumin/Creatinine Ratio, Urine",
    "Urine Albumin to Creatinine Ratio",
    "Microalbumin/Creatinine Ratio, Urine",
    "Urine Microalbumin to Creatinine Ratio",
    "UACR",
    "Albumin/Creatinine [Mass Ratio] in Urine",
    "Albumin to Creatinine Ratio, Spot Urine",
    "Urine Albumin/Creatinine (Random)",
    "Microalbumin/Creatinine, Urine Random"
  ],
  "note": "Includes standard laboratory test names, LOINC descriptions, common abbreviations, and spot/random microalbumin ratio synonyms."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Albumin/Creatinine Ratio, Urine",
  "Urine Albumin to Creatinine Ratio",
  "Microalbumin/Creatinine Ratio, Urine",
  "Urine Microalbumin to Creatinine Ratio",
  "UACR",
  "Albumin/Creatinine [Mass Ratio] in Urine",
  "Albumin to Creatinine Ratio, Spot Urine",
  "Urine Albumin/Creatinine (Random)",
  "Microalbumin/Creatinine, Urine Random"
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
  "code": "2713-6",
  "display": "Oxygen Saturation",
  "domain": "observation",
  "n_resources": 6
 },
 {
  "code": "2708-6",
  "display": "Oxygen saturation in Arterial blood",
  "domain": "observation",
  "n_resources": 247
 },
 {
  "code": "2502-3",
  "display": "Iron saturation [Mass Fraction] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 54
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
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `d37d14862b8eb2ef`

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
           38483-4  Creatinine   (in 2521 resources)
            1751-7  Albumin [Mass/volume] in Serum or Plasma   (in 882 resources)
            2160-0  Creatinine [Mass/volume] in Serum or Plasma   (in 181 resources)
            5767-9  Appearance of Urine   (in 508 resources)
           32167-9  Clarity of Urine   (in 254 resources)
            5778-6  Color of Urine   (in 254 resources)
            2713-6  Oxygen Saturation   (in 6 resources)
            2708-6  Oxygen saturation in Arterial blood   (in 247 resources)
            2502-3  Iron saturation [Mass Fraction] in Serum or Plasma   (in 54 resources)
            5792-7  Glucose [Mass/volume] in Urine by Test strip   (in 254 resources)
            5797-6  Ketones [Mass/volume] in Urine by Test strip   (in 254 resources)

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

### 8. llm_response (cassette, 333 tok, 30.236s)

```
```json
{
  "codes": [
    "14959-1"
  ],
  "broader_codes": [],
  "rejected": [
    {
      "code": "38483-4",
      "why": "measures creatinine alone, not the urine albumin-to-creatinine ratio"
    },
    {
      "code": "1751-7",
      "why": "measures albumin in serum or plasma, not urine albumin-to-creatinine ratio"
    },
    {
      "code": "2160-0",
      "why": "measures creatinine in serum or plasma, not urine albumin-to-creatinine ratio"
    },
    {
      "code": "5767-9",
      "why": "measures visual appearance of urine, not a quantitative analyte ratio"
    },
    {
      "code": "32167-9",
      "why": "measures urine clarity, not a quantitative analyte ratio"
    },
    {
      "code": "5778-6",
      "why": "measures urine color, not a quantitative analyte ratio"
    },
    {
      "code": "2713-6",
      "why": "measures oxygen saturation, unrelated analyte"
    },
    {
      "code": "2708-6",
      "why": "measures arterial oxygen saturation, unrelated analyte"
    },
    {
      "code": "2502-3",
      "why": "measures serum iron saturation, unrelated analyte"
    },
    {
      "code": "5792-7",
      "why": "measures glucose in urine, different analyte"
    },
    {
      "code": "5797-6",
      "why": "measures ketones in urine, different analyte"
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
  "14959-1"
 ],
 "concept": "Urine albumin to creatinine ratio",
 "confidence": "high",
 "displays": [
  "Microalbumin Creatinine Ratio"
 ],
 "domain": "observation",
 "expanded_names": [
  "Albumin/Creatinine Ratio, Urine",
  "Urine Albumin to Creatinine Ratio",
  "Microalbumin/Creatinine Ratio, Urine",
  "Urine Microalbumin to Creatinine Ratio",
  "UACR",
  "Albumin/Creatinine [Mass Ratio] in Urine",
  "Albumin to Creatinine Ratio, Spot Urine",
  "Urine Albumin/Creatinine (Random)",
  "Microalbumin/Creatinine, Urine Random"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Albumin to Creatinine Ratio, Spot Urine",
  "Albumin/Creatinine Ratio, Urine",
  "Albumin/Creatinine [Mass Ratio] in Urine",
  "Microalbumin/Creatinine Ratio, Urine",
  "Microalbumin/Creatinine, Urine Random",
  "UACR",
  "Urine Albumin to Creatinine Ratio",
  "Urine Albumin/Creatinine (Random)",
  "Urine Microalbumin to Creatinine Ratio"
 ]
}
```

