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
 "concept": "Hydrochlorothiazide",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `d82633ba144b34b8`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Hydrochlorothiazide
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

### 4. llm_response (cassette, 60 tok, 18.614s)

```
```json
{
  "names": [
    "hydrochlorothiazide",
    "HCTZ",
    "Microzide",
    "Esidrix",
    "HydroDIURIL",
    "Oretic"
  ],
  "note": "Generic ingredient, standard abbreviations, and common brand names for hydrochlorothiazide"
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "hydrochlorothiazide",
  "HCTZ",
  "Microzide",
  "Esidrix",
  "HydroDIURIL",
  "Oretic"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "310798",
  "display": "Hydrochlorothiazide 25 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 3281
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `f9d1adf8144f0146`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Hydrochlorothiazide
Record domain: medication
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            310798  Hydrochlorothiazide 25 MG Oral Tablet   (in 3281 resources)

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

### 8. llm_response (cassette, 20 tok, 18.226s)

```
```json
{
  "codes": ["310798"],
  "rejected": [],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "codes": [
  "310798"
 ],
 "concept": "Hydrochlorothiazide",
 "confidence": "high",
 "displays": [
  "Hydrochlorothiazide 25 MG Oral Tablet"
 ],
 "domain": "medication",
 "expanded_names": [
  "hydrochlorothiazide",
  "HCTZ",
  "Microzide",
  "Esidrix",
  "HydroDIURIL",
  "Oretic"
 ],
 "matched_names": [
  "hydrochlorothiazide"
 ],
 "reason": "1 of 1 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Esidrix",
  "HCTZ",
  "HydroDIURIL",
  "Microzide",
  "Oretic"
 ]
}
```

