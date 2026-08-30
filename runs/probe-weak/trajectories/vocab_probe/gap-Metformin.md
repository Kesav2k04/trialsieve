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
 "concept": "Metformin",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `0fdb72887cd74953`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Metformin
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

### 4. llm_response (openai, 90 tok, 4.856s)

```
{
  "names": [
    "metformin hydrochloride",
    "glucophage",
    "glumetza",
    "fortamet",
    "riomet",
    "metformin er",
    "metformin xr"
  ],
  "note": "These are the generic and brand names of metformin, a medication commonly used to manage type 2 diabetes."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "metformin hydrochloride",
  "glucophage",
  "glumetza",
  "fortamet",
  "riomet",
  "metformin er",
  "metformin xr"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "860975",
  "display": "24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet",
  "domain": "medication",
  "n_resources": 1030
 },
 {
  "code": "897718",
  "display": "Verapamil Hydrochloride 40 MG",
  "domain": "medication",
  "n_resources": 702
 },
 {
  "code": "835603",
  "display": "tramadol hydrochloride 50 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 93
 },
 {
  "code": "1094107",
  "display": "Phenazopyridine hydrochloride 100 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 35
 },
 {
  "code": "861467",
  "display": "Meperidine Hydrochloride 50 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 24
 },
 {
  "code": "1049630",
  "display": "diphenhydrAMINE Hydrochloride 25 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 21
 },
 {
  "code": "1014676",
  "display": "cetirizine hydrochloride 5 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 12
 },
 {
  "code": "997488",
  "display": "Fexofenadine hydrochloride 30 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 12
 },
 {
  "code": "997223",
  "display": "Donepezil hydrochloride 10 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 3
 },
 {
  "code": "997501",
  "display": "Fexofenadine hydrochloride 60 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 3
 },
 {
  "code": "1014678",
  "display": "cetirizine hydrochloride 10 MG Oral Tablet",
  "domain": "medication",
  "n_resources": 2
 },
 {
  "code": "1091392
```

### 7. llm_request -> granite3.1-dense:8b  cassette `8040a3ad801916b9`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Metformin
Record domain: medication
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            860975  24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet   (in 1030 resources)
            897718  Verapamil Hydrochloride 40 MG   (in 702 resources)
            835603  tramadol hydrochloride 50 MG Oral Tablet   (in 93 resources)
           1094107  Phenazopyridine hydrochloride 100 MG Oral Tablet   (in 35 resources)
            861467  Meperidine Hydrochloride 50 MG Oral Tablet   (in 24 resources)
           1049630  diphenhydrAMINE Hydrochloride 25 MG Oral Tablet   (in 21 resources)
           1014676  cetirizine hydrochloride 5 MG Oral Tablet   (in 12 resources)
            997488  Fexofenadine hydrochloride 30 MG Oral Tablet   (in 12 resources)
            997223  Donepezil hydrochloride 10 MG Oral Tablet   (in 3 resources)
            997501  Fexofenadine hydrochloride 60 MG Oral Tablet   (in 3 resources)
           1014678  cetirizine hydrochloride 10 MG Oral Tablet   (in 2 resources)
           1091392  Methylphenidate Hydrochloride 20 MG Oral Tablet   (in 2 resources)

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

### 8. llm_response (openai, 156 tok, 3.553s)

```
{
  "codes": ["860975"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}

Explanation: The concept is Metformin, a medication used to treat type 2 diabetes. Among the candidates, only "860975 24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet" matches this description. Therefore, it is selected as the correct code. No other codes are broader than this concept, and no candidates were rejected because they did not match the concept or were different analytes. The confidence level is high due to the clear match between the concept and the chosen code.
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "860975"
 ],
 "concept": "Metformin",
 "confidence": "high",
 "displays": [
  "24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet"
 ],
 "domain": "medication",
 "expanded_names": [
  "metformin hydrochloride",
  "glucophage",
  "glumetza",
  "fortamet",
  "riomet",
  "metformin er",
  "metformin xr"
 ],
 "matched_names": [
  "metformin hydrochloride"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "fortamet",
  "glucophage",
  "glumetza",
  "metformin er",
  "metformin xr",
  "riomet"
 ]
}
```

