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
 "concept": "Oral glucose tolerance test",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `881778f3fa3a8cdd`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Oral glucose tolerance test
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

### 4. llm_response (cassette, 162 tok, 30.751s)

```
```json
{
  "names": [
    "Oral glucose tolerance test",
    "Glucose tolerance test",
    "OGTT",
    "GTT",
    "2-hour oral glucose tolerance test",
    "1-hour oral glucose tolerance test",
    "3-hour oral glucose tolerance test",
    "Oral glucose challenge test",
    "OGCT",
    "Glucose post 75g glucose PO",
    "Glucose post 100g glucose PO",
    "Glucose post 50g glucose PO",
    "Glucose tolerance test fasting",
    "2 hour post glucose load",
    "Gestational glucose tolerance screen"
  ],
  "note": "Includes standard diagnostic panels, challenge screens, timed post-load measurements, and standard clinical abbreviations."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Oral glucose tolerance test",
  "Glucose tolerance test",
  "OGTT",
  "GTT",
  "2-hour oral glucose tolerance test",
  "1-hour oral glucose tolerance test",
  "3-hour oral glucose tolerance test",
  "Oral glucose challenge test",
  "OGCT",
  "Glucose post 75g glucose PO",
  "Glucose post 100g glucose PO",
  "Glucose post 50g glucose PO",
  "Glucose tolerance test fasting",
  "2 hour post glucose load",
  "Gestational glucose tolerance screen"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "5792-7",
  "display": "Glucose [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "25428-4",
  "display": "Glucose [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "2339-0",
  "display": "Glucose",
  "domain": "observation",
  "n_resources": 2521
 },
 {
  "code": "2345-7",
  "display": "Glucose [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 181
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
 },
 {
  "code": "20505-4",
  "display": "Bilirubin.total [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "2514-8",
  "display": "Ketones [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5794-3",
  "display": "Hemoglobin [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5802-4",
  "display": "Nitrite [Presence] in 
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `7c1687e0c6f05f6d`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Oral glucose tolerance test
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            5792-7  Glucose [Mass/volume] in Urine by Test strip   (in 254 resources)
           25428-4  Glucose [Presence] in Urine by Test strip   (in 254 resources)
            2339-0  Glucose   (in 2521 resources)
            2345-7  Glucose [Mass/volume] in Serum or Plasma   (in 181 resources)
            5797-6  Ketones [Mass/volume] in Urine by Test strip   (in 254 resources)
            5803-2  pH of Urine by Test strip   (in 254 resources)
            5804-0  Protein [Mass/volume] in Urine by Test strip   (in 254 resources)
           20454-5  Protein [Presence] in Urine by Test strip   (in 254 resources)
           20505-4  Bilirubin.total [Mass/volume] in Urine by Test strip   (in 254 resources)
            2514-8  Ketones [Presence] in Urine by Test strip   (in 254 resources)
            5794-3  Hemoglobin [Presence] in Urine by Test strip   (in 254 resources)
            5802-4  Nitrite [Presence] in Urine by Test strip   (in 254 resources)

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

### 8. llm_response (cassette, 321 tok, 30.980s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "5792-7",
      "why": "Urinalysis glucose measurement, not an oral glucose tolerance test"
    },
    {
      "code": "25428-4",
      "why": "Urinalysis glucose presence test, not an oral glucose tolerance test"
    },
    {
      "code": "2339-0",
      "why": "Single/unspecified glucose measurement, not an oral glucose tolerance test"
    },
    {
      "code": "2345-7",
      "why": "Single serum or plasma glucose measurement, not an oral glucose tolerance test"
    },
    {
      "code": "5797-6",
      "why": "different analyte (ketones in urine)"
    },
    {
      "code": "5803-2",
      "why": "different analyte (urine pH)"
    },
    {
      "code": "5804-0",
      "why": "different analyte (protein in urine)"
    },
    {
      "code": "20454-5",
      "why": "different analyte (protein in urine)"
    },
    {
      "code": "20505-4",
      "why": "different analyte (bilirubin in urine)"
    },
    {
      "code": "2514-8",
      "why": "different analyte (ketones in urine)"
    },
    {
      "code": "5794-3",
      "why": "different analyte (hemoglobin in urine)"
    },
    {
      "code": "5802-4",
      "why": "different analyte (nitrite in urine)"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "codes": [],
 "concept": "Oral glucose tolerance test",
 "confidence": "high",
 "domain": "observation",
 "expanded_names": [
  "Oral glucose tolerance test",
  "Glucose tolerance test",
  "OGTT",
  "GTT",
  "2-hour oral glucose tolerance test",
  "1-hour oral glucose tolerance test",
  "3-hour oral glucose tolerance test",
  "Oral glucose challenge test",
  "OGCT",
  "Glucose post 75g glucose PO",
  "Glucose post 100g glucose PO",
  "Glucose post 50g glucose PO",
  "Glucose tolerance test fasting",
  "2 hour post glucose load",
  "Gestational glucose tolerance screen"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "5792-7",
   "why": "Urinalysis glucose measurement, not an oral glucose tolerance test"
  },
  {
   "code": "25428-4",
   "why": "Urinalysis glucose presence test, not an oral glucose tolerance test"
  },
  {
   "code": "2339-0",
   "why": "Single/unspecified glucose measurement, not an oral glucose tolerance test"
  },
  {
   "code": "2345-7",
   "why": "Single serum or plasma glucose measurement, not an oral glucose tolerance test"
  },
  {
   "code": "5797-6",
   "why": "different analyte (ketones in urine)"
  },
  {
   "code": "5803-2",
   "why": "different analyte (urine pH)"
  },
  {
   "code": "5804-0",
   "why": "different analyte (protein in urine)"
  },
  {
   "code": "20454-5",
   "why": "different analyte (protein in urine)"
  },
  {
   "code": "20505-4",
   "why": "different analyte (bilirubin in urine)"
  },
  {
   "code": "2514-8",
   "why": "different analyte (ketones in urine)"
  },
  {
   "code": "5794-3",
   "why": "different analyte (hemoglobin in urine)"
  },
  {
   "code": "5802-4",
   "why": "different analyte (nitrite in urine)"
  }
 ],
 "status": "UNMAPPAB
```

