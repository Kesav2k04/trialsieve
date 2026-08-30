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
 "concept": "Iron deficiency anaemia",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `20f2a2c968d1265a`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Iron deficiency anaemia
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

### 4. llm_response (cassette, 147 tok, 31.206s)

```
```json
{
  "names": [
    "Iron deficiency anaemia",
    "Iron deficiency anemia",
    "Microcytic hypochromic anaemia",
    "Microcytic hypochromic anemia",
    "Iron deficiency anaemia secondary to blood loss",
    "Iron deficiency anaemia due to inadequate dietary intake",
    "Iron deficiency anaemia due to malabsorption",
    "Iron-refractory iron deficiency anemia",
    "Plummer-Vinson syndrome",
    "Paterson-Kelly syndrome",
    "Chlorosis"
  ],
  "note": "Covers spelling variants, phenotypic descriptions, underlying etiologies, and associated clinical syndromes."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Iron deficiency anaemia",
  "Iron deficiency anemia",
  "Microcytic hypochromic anaemia",
  "Microcytic hypochromic anemia",
  "Iron deficiency anaemia secondary to blood loss",
  "Iron deficiency anaemia due to inadequate dietary intake",
  "Iron deficiency anaemia due to malabsorption",
  "Iron-refractory iron deficiency anemia",
  "Plummer-Vinson syndrome",
  "Paterson-Kelly syndrome",
  "Chlorosis"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "271737000",
  "display": "Anemia (disorder)",
  "domain": "condition",
  "n_resources": 145
 },
 {
  "code": "237602007",
  "display": "Metabolic syndrome X (disorder)",
  "domain": "condition",
  "n_resources": 29
 },
 {
  "code": "95417003",
  "display": "Primary fibromyalgia syndrome",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "67782005",
  "display": "Acute respiratory distress syndrome (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "36955009",
  "display": "Loss of taste (finding)",
  "domain": "condition",
  "n_resources": 19
 },
 {
  "code": "62564004",
  "display": "Concussion with loss of consciousness",
  "domain": "condition",
  "n_resources": 10
 },
 {
  "code": "62106007",
  "display": "Concussion with no loss of consciousness",
  "domain": "condition",
  "n_resources": 29
 },
 {
  "code": "443165006",
  "display": "Pathological fracture due to osteoporosis (disorder)",
  "domain": "condition",
  "n_resources": 10
 },
 {
  "code": "94260004",
  "display": "Secondary malignant neoplasm of colon",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "368581000119106",
  "display": "Neuropathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 9
 },
 {
  "code": "698754002",
  "display": "Chronic paralysis due to lesion of spinal cord",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "90781000119102",
  "display": "Microalbuminuria due to type 2 dia
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `fd6e47301b9e57f6`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Iron deficiency anaemia
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         271737000  Anemia (disorder)   (in 145 resources)
         237602007  Metabolic syndrome X (disorder)   (in 29 resources)
          95417003  Primary fibromyalgia syndrome   (in 2 resources)
          67782005  Acute respiratory distress syndrome (disorder)   (in 2 resources)
          36955009  Loss of taste (finding)   (in 19 resources)
          62564004  Concussion with loss of consciousness   (in 10 resources)
          62106007  Concussion with no loss of consciousness   (in 29 resources)
         443165006  Pathological fracture due to osteoporosis (disorder)   (in 10 resources)
          94260004  Secondary malignant neoplasm of colon   (in 2 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
         698754002  Chronic paralysis due to lesion of spinal cord   (in 1 resources)
    90781000119102  Microalbuminuria due to type 2 diabetes mellitus (disorder)   (in 1 resources)

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

### 8. llm_response (cassette, 409 tok, 31.190s)

```
{
  "codes": [],
  "broader_codes": [
    "271737000"
  ],
  "rejected": [
    {
      "code": "237602007",
      "why": "Metabolic syndrome X is a metabolic disorder, unrelated to anemia"
    },
    {
      "code": "95417003",
      "why": "Primary fibromyalgia syndrome is a chronic pain condition, unrelated to anemia"
    },
    {
      "code": "67782005",
      "why": "Acute respiratory distress syndrome is a pulmonary condition, unrelated to anemia"
    },
    {
      "code": "36955009",
      "why": "Loss of taste is a sensory finding, unrelated to anemia"
    },
    {
      "code": "62564004",
      "why": "Concussion with loss of consciousness is a traumatic brain injury, unrelated to anemia"
    },
    {
      "code": "62106007",
      "why": "Concussion with no loss of consciousness is a traumatic brain injury, unrelated to anemia"
    },
    {
      "code": "443165006",
      "why": "Pathological fracture due to osteoporosis is a bone disorder, unrelated to anemia"
    },
    {
      "code": "94260004",
      "why": "Secondary malignant neoplasm of colon is a metastatic neoplastic disorder, unrelated to anemia"
    },
    {
      "code": "368581000119106",
      "why": "Neuropathy due to type 2 diabetes mellitus is a diabetic complication, unrelated to anemia"
    },
    {
      "code": "698754002",
      "why": "Chronic paralysis due to lesion of spinal cord is a neuromuscular disorder, unrelated to anemia"
    },
    {
      "code": "90781000119102",
      "why": "Microalbuminuria due to type 2 diabetes mellitus is a diabetic renal finding, unrelated to anemia"
    }
  ],
  "confidence": "high"
}
```

### 9. final

```json
{
 "broader_codes": [
  "271737000"
 ],
 "codes": [],
 "concept": "Iron deficiency anaemia",
 "confidence": "high",
 "displays": [
  "Anemia (disorder)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Iron deficiency anaemia",
  "Iron deficiency anemia",
  "Microcytic hypochromic anaemia",
  "Microcytic hypochromic anemia",
  "Iron deficiency anaemia secondary to blood loss",
  "Iron deficiency anaemia due to inadequate dietary intake",
  "Iron deficiency anaemia due to malabsorption",
  "Iron-refractory iron deficiency anemia",
  "Plummer-Vinson syndrome",
  "Paterson-Kelly syndrome",
  "Chlorosis"
 ],
 "reason": "this vocabulary codes the concept only at a coarser grain; presence cannot settle the criterion and absence can",
 "rejected": [
  {
   "code": "237602007",
   "why": "Metabolic syndrome X is a metabolic disorder, unrelated to anemia"
  },
  {
   "code": "95417003",
   "why": "Primary fibromyalgia syndrome is a chronic pain condition, unrelated to anemia"
  },
  {
   "code": "67782005",
   "why": "Acute respiratory distress syndrome is a pulmonary condition, unrelated to anemia"
  },
  {
   "code": "36955009",
   "why": "Loss of taste is a sensory finding, unrelated to anemia"
  },
  {
   "code": "62564004",
   "why": "Concussion with loss of consciousness is a traumatic brain injury, unrelated to anemia"
  },
  {
   "code": "62106007",
   "why": "Concussion with no loss of consciousness is a traumatic brain injury, unrelated to anemia"
  },
  {
   "code": "443165006",
   "why": "Pathological fracture due to osteoporosis is a bone disorder, unrelated to anemia"
  },
  {
   "code": "94260004",
   "why": "Secondary malignant neoplasm of colon is a metastatic neoplastic disorder, unrelated to anemia"
  },
  {
   "code": "368581000119106",
   "why": "Neuropat
```

