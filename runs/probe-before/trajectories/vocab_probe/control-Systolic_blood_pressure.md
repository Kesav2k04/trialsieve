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
 "concept": "Systolic blood pressure",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `d10860f21c70b9df`

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

### 4. llm_response (cassette, 131 tok, 28.037s)

```
```json
{
  "names": [
    "Systolic blood pressure",
    "Systolic BP",
    "SBP",
    "Blood pressure systolic",
    "Systolic arterial pressure",
    "Arterial blood pressure systolic",
    "Non-invasive systolic blood pressure",
    "Invasive systolic blood pressure",
    "Sitting systolic blood pressure",
    "Standing systolic blood pressure",
    "Supine systolic blood pressure"
  ],
  "note": "Common observation names and standard documentation synonyms for systolic arterial blood pressure measurements"
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Systolic blood pressure",
  "Systolic BP",
  "SBP",
  "Blood pressure systolic",
  "Systolic arterial pressure",
  "Arterial blood pressure systolic",
  "Non-invasive systolic blood pressure",
  "Invasive systolic blood pressure",
  "Sitting systolic blood pressure",
  "Standing systolic blood pressure",
  "Supine systolic blood pressure"
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
  "code": "59408-5",
  "display": "Oxygen saturation in Arterial blood by Pulse oximetry",
  "domain": "observation",
  "n_resources": 247
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `a6f66e32e230dd04`

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
            2744-1  pH of Arterial blood   (in 33 resources)
            2708-6  Oxygen saturation in Arterial blood   (in 247 resources)
            1960-4  Bicarbonate [Moles/volume] in Arterial blood   (in 33 resources)
           59408-5  Oxygen saturation in Arterial blood by Pulse oximetry   (in 247 resources)

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

### 8. llm_response (cassette, 247 tok, 30.227s)

```
```json
{
  "codes": ["8480-6"],
  "rejected": [
    {"code": "2703-7", "why": "arterial oxygen partial pressure measurement, not blood pressure"},
    {"code": "2019-8", "why": "arterial carbon dioxide partial pressure measurement, not blood pressure"},
    {"code": "85354-9", "why": "blood pressure panel/composite, not specific systolic measurement"},
    {"code": "55284-4", "why": "blood pressure panel/composite, not specific systolic measurement"},
    {"code": "8462-4", "why": "diastolic blood pressure, not systolic"},
    {"code": "8478-0", "why": "mean blood pressure, not systolic blood pressure"},
    {"code": "2744-1", "why": "arterial blood pH, different measurement"},
    {"code": "2708-6", "why": "arterial oxygen saturation, different measurement"},
    {"code": "1960-4", "why": "arterial bicarbonate concentration, different measurement"},
    {"code": "59408-5", "why": "pulse oximetry oxygen saturation, different measurement"}
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
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
  "Systolic BP",
  "SBP",
  "Blood pressure systolic",
  "Systolic arterial pressure",
  "Arterial blood pressure systolic",
  "Non-invasive systolic blood pressure",
  "Invasive systolic blood pressure",
  "Sitting systolic blood pressure",
  "Standing systolic blood pressure",
  "Supine systolic blood pressure"
 ],
 "matched_names": [
  "systolic blood pressure"
 ],
 "reason": "1 of 11 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Arterial blood pressure systolic",
  "Blood pressure systolic",
  "Invasive systolic blood pressure",
  "Non-invasive systolic blood pressure",
  "SBP",
  "Sitting systolic blood pressure",
  "Standing systolic blood pressure",
  "Supine systolic blood pressure",
  "Systolic BP",
  "Systolic arterial pressure"
 ]
}
```

