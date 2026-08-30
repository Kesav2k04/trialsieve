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
 "concept": "Oral glucose tolerance test",
 "domain": "observation",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `881778f3fa3a8cdd`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Oral glucose tolerance test
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

### 4. llm_response (cassette, 146 tok, 62.138s)

```
{
  "names": [
    "Oral glucose tolerance test",
    "OGTT",
    "Glucose tolerance test",
    "GTT",
    "Glucose challenge test",
    "Glucose 2 hr post 75g glucose PO",
    "Glucose 1 hr post 50g glucose PO",
    "Glucose 1 hr post 75g glucose PO",
    "Glucose 2 hr post 100g glucose PO",
    "Glucose 3 hr post 100g glucose PO",
    "75g oral glucose tolerance test",
    "100g oral glucose tolerance test",
    "Gestational glucose tolerance test",
    "Post-load glucose"
  ],
  "note": "Includes standard, gestational, and timed post-challenge plasma glucose measurements."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "observation",
 "limit": 12,
 "terms": [
  "Oral glucose tolerance test",
  "OGTT",
  "Glucose tolerance test",
  "GTT",
  "Glucose challenge test",
  "Glucose 2 hr post 75g glucose PO",
  "Glucose 1 hr post 50g glucose PO",
  "Glucose 1 hr post 75g glucose PO",
  "Glucose 2 hr post 100g glucose PO",
  "Glucose 3 hr post 100g glucose PO",
  "75g oral glucose tolerance test",
  "100g oral glucose tolerance test",
  "Gestational glucose tolerance test",
  "Post-load glucose"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "5792-7",
  "display": "Glucose [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "25428-4",
  "display": "Glucose [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "2339-0",
  "display": "Glucose",
  "domain": "observation",
  "n_resources": 2521
 },
 {
  "code": "2345-7",
  "display": "Glucose [Mass/volume] in Serum or Plasma",
  "domain": "observation",
  "n_resources": 181
 },
 {
  "code": "5797-6",
  "display": "Ketones [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5803-2",
  "display": "pH of Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5804-0",
  "display": "Protein [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "74006-8",
  "display": "Weight difference [Mass difference] --pre dialysis - post dialysis",
  "domain": "observation",
  "n_resources": 1079
 },
 {
  "code": "20454-5",
  "display": "Protein [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "20505-4",
  "display": "Bilirubin.total [Mass/volume] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "2514-8",
  "display": "Ketones [Presence] in Urine by Test strip",
  "domain": "observation",
  "n_resources": 254
 },
 {
  "code": "5794-3",
  "display":
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `b4b4564e8d962dd3`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Oral glucose tolerance test
Record domain: observation
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
            5792-7  Glucose [Mass/volume] in Urine by Test strip   (in 254 resources)
           25428-4  Glucose [Presence] in Urine by Test strip   (in 254 resources)
            2339-0  Glucose   (in 2521 resources)
            2345-7  Glucose [Mass/volume] in Serum or Plasma   (in 181 resources)
            5797-6  Ketones [Mass/volume] in Urine by Test strip   (in 254 resources)
            5803-2  pH of Urine by Test strip   (in 254 resources)
            5804-0  Protein [Mass/volume] in Urine by Test strip   (in 254 resources)
           74006-8  Weight difference [Mass difference] --pre dialysis - post dialysis   (in 1079 resources)
           20454-5  Protein [Presence] in Urine by Test strip   (in 254 resources)
           20505-4  Bilirubin.total [Mass/volume] in Urine by Test strip   (in 254 resources)
            2514-8  Ketones [Presence] in Urine by Test strip   (in 254 resources)
            5794-3  Hemoglobin [Presence] in Urine by Test strip   (in 254 resources)

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

### 8. llm_response (cassette, 356 tok, 60.321s)

```
```json
{
  "codes": [],
  "broader_codes": [],
  "rejected": [
    {
      "code": "5792-7",
      "why": "urine test strip glucose; different specimen and not an oral glucose tolerance test"
    },
    {
      "code": "25428-4",
      "why": "urine test strip glucose presence; different specimen and not an oral glucose tolerance test"
    },
    {
      "code": "2339-0",
      "why": "isolated blood glucose measurement; does not denote an oral glucose challenge or tolerance protocol"
    },
    {
      "code": "2345-7",
      "why": "isolated serum/plasma glucose measurement; does not denote an oral glucose challenge or tolerance protocol"
    },
    {
      "code": "5797-6",
      "why": "different analyte (ketones in urine)"
    },
    {
      "code": "5803-2",
      "why": "different analyte (urine pH)"
    },
    {
      "code": "5804-0",
      "why": "different analyte (protein in urine)"
    },
    {
      "code": "74006-8",
      "why": "unrelated measurement (pre/post dialysis weight difference)"
    },
    {
      "code": "20454-5",
      "why": "different analyte (protein in urine)"
    },
    {
      "code": "20505-4",
      "why": "different analyte (bilirubin in urine)"
    },
    {
      "code": "2514-8",
      "why": "different analyte (ketones in urine)"
    },
    {
      "code": "5794-3",
      "why": "different analyte (hemoglobin in urine)"
    }
  ],
  "confidence": "high"
}
```
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [],
 "concept": "Oral glucose tolerance test",
 "confidence": "high",
 "domain": "observation",
 "expanded_names": [
  "Oral glucose tolerance test",
  "OGTT",
  "Glucose tolerance test",
  "GTT",
  "Glucose challenge test",
  "Glucose 2 hr post 75g glucose PO",
  "Glucose 1 hr post 50g glucose PO",
  "Glucose 1 hr post 75g glucose PO",
  "Glucose 2 hr post 100g glucose PO",
  "Glucose 3 hr post 100g glucose PO",
  "75g oral glucose tolerance test",
  "100g oral glucose tolerance test",
  "Gestational glucose tolerance test",
  "Post-load glucose"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "5792-7",
   "why": "urine test strip glucose; different specimen and not an oral glucose tolerance test"
  },
  {
   "code": "25428-4",
   "why": "urine test strip glucose presence; different specimen and not an oral glucose tolerance test"
  },
  {
   "code": "2339-0",
   "why": "isolated blood glucose measurement; does not denote an oral glucose challenge or tolerance protocol"
  },
  {
   "code": "2345-7",
   "why": "isolated serum/plasma glucose measurement; does not denote an oral glucose challenge or tolerance protocol"
  },
  {
   "code": "5797-6",
   "why": "different analyte (ketones in urine)"
  },
  {
   "code": "5803-2",
   "why": "different analyte (urine pH)"
  },
  {
   "code": "5804-0",
   "why": "different analyte (protein in urine)"
  },
  {
   "code": "74006-8",
   "why": "unrelated measurement (pre/post dialysis weight difference)"
  },
  {
   "code": "20454-5",
   "why": "different analyte (protein in urine)"
  },
  {
   "code": "20505-4",
   "why": "different analyte (bilirubin in urine)"
  },
  {
   "code": "2514-8",
   "why": "different analyte (ke
```

