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
 "concept": "Metformin",
 "domain": "medication",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `62776e4af62e3b46`

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

### 4. llm_response (cassette, 66 tok, 16.966s)

```
```json
{
  "names": [
    "metformin",
    "metformin hydrochloride",
    "Glucophage",
    "Glucophage XR",
    "Fortamet",
    "Glumetza",
    "Riomet"
  ],
  "note": "Generic ingredient, common salt form, and standard brand/extended-release formulations"
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "medication",
 "limit": 12,
 "terms": [
  "metformin",
  "metformin hydrochloride",
  "Glucophage",
  "Glucophage XR",
  "Fortamet",
  "Glumetza",
  "Riomet"
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

### 7. llm_request -> gemini-3.7-flash-medium  cassette `34476224ce530a2d`

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

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{"codes": ["4548-4"], "rejected": [{"code": "718-7", "why": "different analyte"}],
  "confidence": "high"}
```

### 8. llm_response (cassette, 283 tok, 19.688s)

```
```json
{
  "codes": [
    "860975"
  ],
  "rejected": [
    {
      "code": "897718",
      "why": "different active ingredient (verapamil)"
    },
    {
      "code": "835603",
      "why": "different active ingredient (tramadol)"
    },
    {
      "code": "1094107",
      "why": "different active ingredient (phenazopyridine)"
    },
    {
      "code": "861467",
      "why": "different active ingredient (meperidine)"
    },
    {
      "code": "1049630",
      "why": "different active ingredient (diphenhydramine)"
    },
    {
      "code": "1014676",
      "why": "different active ingredient (cetirizine)"
    },
    {
      "code": "997488",
      "why": "different active ingredient (fexofenadine)"
    },
    {
      "code": "997223",
      "why": "different active ingredient (donepezil)"
    },
    {
      "code": "997501",
      "why": "different active ingredient (fexofenadine)"
    },
    {
      "code": "1014678",
      "why": "different active ingredient (cetirizine)"
    },
    {
      "code": "1091392",
      "why": "different active ingredient (methylphenidate)"
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
  "860975"
 ],
 "concept": "Metformin",
 "confidence": "high",
 "displays": [
  "24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet"
 ],
 "domain": "medication",
 "expanded_names": [
  "metformin",
  "metformin hydrochloride",
  "Glucophage",
  "Glucophage XR",
  "Fortamet",
  "Glumetza",
  "Riomet"
 ],
 "matched_names": [
  "metformin",
  "metformin hydrochloride"
 ],
 "reason": "1 of 12 candidates selected",
 "status": "MAPPED",
 "unmatched_names": [
  "Fortamet",
  "Glucophage",
  "Glucophage XR",
  "Glumetza",
  "Riomet"
 ]
}
```

