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
 "concept": "Haemodialysis",
 "domain": "procedure",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `423eca26e9f97289`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Haemodialysis
Record domain: procedure

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

### 4. llm_response (cassette, 137 tok, 19.612s)

```
```json
{
  "names": [
    "hemodialysis",
    "haemodialysis",
    "intermittent hemodialysis",
    "maintenance hemodialysis",
    "chronic hemodialysis",
    "acute hemodialysis",
    "home hemodialysis",
    "nocturnal hemodialysis",
    "in-center hemodialysis",
    "hemodiafiltration",
    "continuous venovenous hemodialysis",
    "continuous venovenous hemodiafiltration",
    "renal hemodialysis"
  ],
  "note": "Includes standard American/British spellings, acute/chronic regimens, and continuous/hybrid extracorporeal modalities."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "procedure",
 "limit": 12,
 "terms": [
  "hemodialysis",
  "haemodialysis",
  "intermittent hemodialysis",
  "maintenance hemodialysis",
  "chronic hemodialysis",
  "acute hemodialysis",
  "home hemodialysis",
  "nocturnal hemodialysis",
  "in-center hemodialysis",
  "hemodiafiltration",
  "continuous venovenous hemodialysis",
  "continuous venovenous hemodiafiltration",
  "renal hemodialysis"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "302497006",
  "display": "Hemodialysis (procedure)",
  "domain": "procedure",
  "n_resources": 10
 },
 {
  "code": "313191000",
  "display": "Injection of adrenaline",
  "domain": "procedure",
  "n_resources": 6
 },
 {
  "code": "265764009",
  "display": "Renal dialysis (procedure)",
  "domain": "procedure",
  "n_resources": 1079
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `1a030f9406c383f1`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Haemodialysis
Record domain: procedure
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         302497006  Hemodialysis (procedure)   (in 10 resources)
         313191000  Injection of adrenaline   (in 6 resources)
         265764009  Renal dialysis (procedure)   (in 1079 resources)

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

### 8. llm_response (cassette, 89 tok, 19.137s)

```
```json
{
  "codes": ["302497006"],
  "rejected": [
    {
      "code": "313191000",
      "why": "different procedure (injection of adrenaline)"
    },
    {
      "code": "265764009",
      "why": "broader concept (renal dialysis encompasses peritoneal dialysis and other modalities, not specific to hemodialysis)"
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
  "302497006"
 ],
 "concept": "Haemodialysis",
 "confidence": "high",
 "displays": [
  "Hemodialysis (procedure)"
 ],
 "domain": "procedure",
 "expanded_names": [
  "hemodialysis",
  "haemodialysis",
  "intermittent hemodialysis",
  "maintenance hemodialysis",
  "chronic hemodialysis",
  "acute hemodialysis",
  "home hemodialysis",
  "nocturnal hemodialysis",
  "in-center hemodialysis",
  "hemodiafiltration",
  "continuous venovenous hemodialysis",
  "continuous venovenous hemodiafiltration",
  "renal hemodialysis"
 ],
 "matched_names": [
  "hemodialysis"
 ],
 "reason": "1 of 3 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "acute hemodialysis",
  "chronic hemodialysis",
  "continuous venovenous hemodiafiltration",
  "continuous venovenous hemodialysis",
  "haemodialysis",
  "hemodiafiltration",
  "home hemodialysis",
  "in-center hemodialysis",
  "intermittent hemodialysis",
  "maintenance hemodialysis",
  "nocturnal hemodialysis",
  "renal hemodialysis"
 ]
}
```

