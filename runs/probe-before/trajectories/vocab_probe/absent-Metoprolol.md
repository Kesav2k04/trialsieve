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
 "concept": "Metoprolol",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `ada71590e63e0f5e`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Metoprolol
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

### 4. llm_response (cassette, 75 tok, 30.023s)

```
```json
{
  "names": [
    "metoprolol",
    "metoprolol succinate",
    "metoprolol tartrate",
    "Toprol-XL",
    "Lopressor",
    "Toprol XL",
    "Dutoprol",
    "Lopressor HCT"
  ],
  "note": "Includes generic base, standard salt forms (succinate and tartrate), and common brand names."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "metoprolol",
  "metoprolol succinate",
  "metoprolol tartrate",
  "Toprol-XL",
  "Lopressor",
  "Toprol XL",
  "Dutoprol",
  "Lopressor HCT"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "856987",
  "display": "Acetaminophen 300 MG / Hydrocodone Bitartrate 5 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 235
 },
 {
  "code": "857005",
  "display": "Acetaminophen 325 MG / HYDROcodone Bitartrate 7.5 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 11
 },
 {
  "code": "1860491",
  "display": "12 HR Hydrocodone Bitartrate 10 MG Extended Release Oral Capsule",
  "domain": "medication",
  "n_resources": 99
 },
 {
  "code": "1043400",
  "display": "Acetaminophen 21.7 MG/ML / Dextromethorphan Hydrobromide 1 MG/ML / doxylamine succinate 0.417 MG/ML Oral Solution",
  "domain": "medication",
  "n_resources": 64
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `ffe910146afc714d`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Metoprolol
Record domain: medication
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            856987  Acetaminophen 300 MG / Hydrocodone Bitartrate 5 MG Oral Tablet   (in 235 resources)
            857005  Acetaminophen 325 MG / HYDROcodone Bitartrate 7.5 MG Oral Tablet   (in 11 resources)
           1860491  12 HR Hydrocodone Bitartrate 10 MG Extended Release Oral Capsule   (in 99 resources)
           1043400  Acetaminophen 21.7 MG/ML / Dextromethorphan Hydrobromide 1 MG/ML / dox   (in 64 resources)

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

### 8. llm_response (cassette, 143 tok, 29.547s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "856987",
      "why": "different active ingredients (acetaminophen and hydrocodone bitartrate)"
    },
    {
      "code": "857005",
      "why": "different active ingredients (acetaminophen and hydrocodone bitartrate)"
    },
    {
      "code": "1860491",
      "why": "different active ingredient (hydrocodone bitartrate)"
    },
    {
      "code": "1043400",
      "why": "different active ingredients (acetaminophen, dextromethorphan, and doxylamine combination)"
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
 "concept": "Metoprolol",
 "confidence": "high",
 "domain": "medication",
 "expanded_names": [
  "metoprolol",
  "metoprolol succinate",
  "metoprolol tartrate",
  "Toprol-XL",
  "Lopressor",
  "Toprol XL",
  "Dutoprol",
  "Lopressor HCT"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "856987",
   "why": "different active ingredients (acetaminophen and hydrocodone bitartrate)"
  },
  {
   "code": "857005",
   "why": "different active ingredients (acetaminophen and hydrocodone bitartrate)"
  },
  {
   "code": "1860491",
   "why": "different active ingredient (hydrocodone bitartrate)"
  },
  {
   "code": "1043400",
   "why": "different active ingredients (acetaminophen, dextromethorphan, and doxylamine combination)"
  }
 ],
 "status": "UNMAPPABLE"
}
```

