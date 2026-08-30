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

### 4. llm_response (cassette, 84 tok, 32.414s)

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
  "note": "Includes generic ingredient, brand names, and common fixed-dose combination formulations containing simvastatin."
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `1a360cbddbe01124`

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

### 8. llm_response (cassette, 28 tok, 28.811s)

```
```json
{
  "codes": ["314231", "312961"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "broader_codes": [],
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

