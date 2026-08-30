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
 "concept": "Simvastatin",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `c6072ee48beb3ad4`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Simvastatin
Record domain: medication

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

### 4. llm_response (cassette, 82 tok, 19.711s)

```
```json
{
  "names": [
    "simvastatin",
    "Zocor",
    "Flolipid",
    "simvastatin-ezetimibe",
    "Vytorin",
    "simvastatin-niacin",
    "Simcor",
    "simvastatin-sitagliptin",
    "Juvisync"
  ],
  "note": "Includes single-ingredient generic and brand names as well as common fixed-dose combination products."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "simvastatin",
  "Zocor",
  "Flolipid",
  "simvastatin-ezetimibe",
  "Vytorin",
  "simvastatin-niacin",
  "Simcor",
  "simvastatin-sitagliptin",
  "Juvisync"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "314231",
  "display": "Simvastatin 10 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 904
 },
 {
  "code": "312961",
  "display": "Simvastatin 20 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 268
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `c5f9ea2b54aab4be`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Simvastatin
Record domain: medication
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            314231  Simvastatin 10 MG Oral Tablet   (in 904 resources)
            312961  Simvastatin 20 MG Oral Tablet   (in 268 resources)

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

### 8. llm_response (cassette, 23 tok, 31.644s)

```
```json
{
  "codes": ["314231", "312961"],
  "rejected": [],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "codes": [
  "312961",
  "314231"
 ],
 "concept": "Simvastatin",
 "confidence": "high",
 "displays": [
  "Simvastatin 10 MG Oral Tablet",
  "Simvastatin 20 MG Oral Tablet"
 ],
 "domain": "medication",
 "expanded_names": [
  "simvastatin",
  "Zocor",
  "Flolipid",
  "simvastatin-ezetimibe",
  "Vytorin",
  "simvastatin-niacin",
  "Simcor",
  "simvastatin-sitagliptin",
  "Juvisync"
 ],
 "matched_names": [
  "simvastatin"
 ],
 "reason": "2 of 2 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Flolipid",
  "Juvisync",
  "Simcor",
  "Vytorin",
  "Zocor",
  "simvastatin-ezetimibe",
  "simvastatin-niacin",
  "simvastatin-sitagliptin"
 ]
}
```

