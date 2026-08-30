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

### 4. llm_response (cassette, 67 tok, 59.060s)

```
```json
{
  "names": [
    "metoprolol",
    "metoprolol succinate",
    "metoprolol tartrate",
    "Toprol-XL",
    "Lopressor",
    "Kapspargo"
  ],
  "note": "Includes common generic salt forms (succinate and tartrate) and standard brand-name formulations."
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
  "Kapspargo"
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `4c3764eeb001f719`

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

### 8. llm_response (openai, 166 tok, 270.011s)

```
```json
{
  "codes": [],
  "broader_codes": [],
  "rejected": [
    {
      "code": "856987",
      "why": "combination of acetaminophen and hydrocodone bitartrate, different active ingredient"
    },
    {
      "code": "857005",
      "why": "combination of acetaminophen and hydrocodone bitartrate, different active ingredient"
    },
    {
      "code": "1860491",
      "why": "extended-release hydrocodone bitartrate, different active ingredient"
    },
    {
      "code": "1043400",
      "why": "multi-ingredient cold/cough formulation (acetaminophen, dextromethorphan, doxylamine), different active ingredients"
    }
  ],
  "confidence": "high"
}
```
```

### 9. transport_retry

```json
{
 "attempt": 1,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 10. transport_retry

```json
{
 "attempt": 2,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 11. transport_retry

```json
{
 "attempt": 3,
 "error": "HTTP 502: {\"error\": {\"message\": \"~\\\\AppData\\\\Local\\\\agy\\\\bin\\\\agy.exe exited 1\", \"detail\": \"Error: Agent execution terminated due to error.\\n\"}}"
}
```

### 12. final

```json
{
 "broader_codes": [],
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
  "Kapspargo"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "856987",
   "why": "combination of acetaminophen and hydrocodone bitartrate, different active ingredient"
  },
  {
   "code": "857005",
   "why": "combination of acetaminophen and hydrocodone bitartrate, different active ingredient"
  },
  {
   "code": "1860491",
   "why": "extended-release hydrocodone bitartrate, different active ingredient"
  },
  {
   "code": "1043400",
   "why": "multi-ingredient cold/cough formulation (acetaminophen, dextromethorphan, doxylamine), different active ingredients"
  }
 ],
 "status": "UNMAPPABLE"
}
```

