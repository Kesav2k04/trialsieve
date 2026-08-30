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
 "concept": "Essential hypertension",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `1d87974509beb331`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Essential hypertension
Record domain: condition

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

### 4. llm_response (cassette, 125 tok, 18.120s)

```
```json
{
  "names": [
    "Essential hypertension",
    "Primary hypertension",
    "Essential (primary) hypertension",
    "Systemic arterial hypertension",
    "Benign essential hypertension",
    "Malignant essential hypertension",
    "Isolated systolic hypertension",
    "Labile hypertension",
    "High blood pressure",
    "Arterial hypertension"
  ],
  "note": "Includes primary/essential hypertension, its clinical variants, and common diagnostic descriptors found in EHR records."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Essential hypertension",
  "Primary hypertension",
  "Essential (primary) hypertension",
  "Systemic arterial hypertension",
  "Benign essential hypertension",
  "Malignant essential hypertension",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "High blood pressure",
  "Arterial hypertension"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "59621000",
  "display": "Hypertension",
  "domain": "condition",
  "n_resources": 141
 },
 {
  "code": "95417003",
  "display": "Primary fibromyalgia syndrome",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "201834006",
  "display": "Localized, primary osteoarthritis of the hand",
  "domain": "condition",
  "n_resources": 11
 },
 {
  "code": "5251000175109",
  "display": "Received certificate of high school equivalency (finding)",
  "domain": "condition",
  "n_resources": 116
 },
 {
  "code": "224295006",
  "display": "Only received primary school education (finding)",
  "domain": "condition",
  "n_resources": 54
 },
 {
  "code": "254837009",
  "display": "Malignant neoplasm of breast (disorder)",
  "domain": "condition",
  "n_resources": 6
 },
 {
  "code": "363406005",
  "display": "Malignant tumor of colon",
  "domain": "condition",
  "n_resources": 4
 },
 {
  "code": "109838007",
  "display": "Overlapping malignant neoplasm of colon",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "94260004",
  "display": "Secondary malignant neoplasm of colon",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "314994000",
  "display": "Metastasis from malignant tumor of prostate (disorder)",
  "domain": "condition",
  "n_resources": 1
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `2a6b73e5c94d858d`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Essential hypertension
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
          59621000  Hypertension   (in 141 resources)
          95417003  Primary fibromyalgia syndrome   (in 2 resources)
         201834006  Localized, primary osteoarthritis of the hand   (in 11 resources)
     5251000175109  Received certificate of high school equivalency (finding)   (in 116 resources)
         224295006  Only received primary school education (finding)   (in 54 resources)
         254837009  Malignant neoplasm of breast (disorder)   (in 6 resources)
         363406005  Malignant tumor of colon   (in 4 resources)
         109838007  Overlapping malignant neoplasm of colon   (in 2 resources)
          94260004  Secondary malignant neoplasm of colon   (in 2 resources)
         314994000  Metastasis from malignant tumor of prostate (disorder)   (in 1 resources)

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

### 8. llm_response (cassette, 252 tok, 20.746s)

```
```json
{
  "codes": [
    "59621000"
  ],
  "rejected": [
    {
      "code": "95417003",
      "why": "fibromyalgia syndrome, unrelated condition"
    },
    {
      "code": "201834006",
      "why": "osteoarthritis of the hand, unrelated condition"
    },
    {
      "code": "5251000175109",
      "why": "educational attainment finding, not a clinical condition"
    },
    {
      "code": "224295006",
      "why": "educational attainment finding, not a clinical condition"
    },
    {
      "code": "254837009",
      "why": "breast malignancy, unrelated condition"
    },
    {
      "code": "363406005",
      "why": "colon malignancy, unrelated condition"
    },
    {
      "code": "109838007",
      "why": "colon malignancy, unrelated condition"
    },
    {
      "code": "94260004",
      "why": "secondary colon neoplasm, unrelated condition"
    },
    {
      "code": "314994000",
      "why": "metastasis from prostate cancer, unrelated condition"
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
  "59621000"
 ],
 "concept": "Essential hypertension",
 "confidence": "high",
 "displays": [
  "Hypertension"
 ],
 "domain": "condition",
 "expanded_names": [
  "Essential hypertension",
  "Primary hypertension",
  "Essential (primary) hypertension",
  "Systemic arterial hypertension",
  "Benign essential hypertension",
  "Malignant essential hypertension",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "High blood pressure",
  "Arterial hypertension"
 ],
 "matched_names": [],
 "reason": "1 of 10 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Arterial hypertension",
  "Benign essential hypertension",
  "Essential (primary) hypertension",
  "Essential hypertension",
  "High blood pressure",
  "Isolated systolic hypertension",
  "Labile hypertension",
  "Malignant essential hypertension",
  "Primary hypertension",
  "Systemic arterial hypertension"
 ]
}
```

