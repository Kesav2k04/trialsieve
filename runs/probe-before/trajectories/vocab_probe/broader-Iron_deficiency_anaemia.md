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

### 4. llm_response (openai, 153 tok, 48.202s)

```
```json
{
  "names": [
    "Iron deficiency anemia",
    "Iron deficiency anaemia",
    "Microcytic hypochromic anemia",
    "Iron deficiency anemia secondary to blood loss",
    "Iron deficiency anemia secondary to inadequate dietary iron intake",
    "Iron deficiency anemia secondary to malabsorption",
    "Iron deficiency anemia in pregnancy",
    "Plummer-Vinson syndrome",
    "Sideropenic anemia",
    "Refractory iron deficiency anemia"
  ],
  "note": "Includes general iron deficiency anemia terms, etiologic subtypes (blood loss, dietary, malabsorption), and related syndromic presentations."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Iron deficiency anemia",
  "Iron deficiency anaemia",
  "Microcytic hypochromic anemia",
  "Iron deficiency anemia secondary to blood loss",
  "Iron deficiency anemia secondary to inadequate dietary iron intake",
  "Iron deficiency anemia secondary to malabsorption",
  "Iron deficiency anemia in pregnancy",
  "Plummer-Vinson syndrome",
  "Sideropenic anemia",
  "Refractory iron deficiency anemia"
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
  "code": "72892002",
  "display": "Normal pregnancy",
  "domain": "condition",
  "n_resources": 258
 },
 {
  "code": "79586000",
  "display": "Tubal pregnancy",
  "domain": "condition",
  "n_resources": 13
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
  "code": "94260004",
  "display": "Secondary malignant neoplasm of colon",
  "domain": "condition",
  "n_resources": 2
 }
]
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `be08cf578efa9667`

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
          72892002  Normal pregnancy   (in 258 resources)
          79586000  Tubal pregnancy   (in 13 resources)
          36955009  Loss of taste (finding)   (in 19 resources)
          62564004  Concussion with loss of consciousness   (in 10 resources)
          62106007  Concussion with no loss of consciousness   (in 29 resources)
          94260004  Secondary malignant neoplasm of colon   (in 2 resources)

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

### 8. llm_response (openai, 266 tok, 50.206s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "271737000",
      "why": "too broad; represents general anemia without specification of iron deficiency"
    },
    {
      "code": "237602007",
      "why": "unrelated condition (metabolic syndrome)"
    },
    {
      "code": "95417003",
      "why": "unrelated condition (fibromyalgia)"
    },
    {
      "code": "67782005",
      "why": "unrelated condition (acute respiratory distress syndrome)"
    },
    {
      "code": "72892002",
      "why": "unrelated condition (normal pregnancy)"
    },
    {
      "code": "79586000",
      "why": "unrelated condition (tubal pregnancy)"
    },
    {
      "code": "36955009",
      "why": "unrelated finding (loss of taste)"
    },
    {
      "code": "62564004",
      "why": "unrelated condition (concussion)"
    },
    {
      "code": "62106007",
      "why": "unrelated condition (concussion)"
    },
    {
      "code": "94260004",
      "why": "unrelated condition (secondary malignant neoplasm of colon)"
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
 "concept": "Iron deficiency anaemia",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Iron deficiency anemia",
  "Iron deficiency anaemia",
  "Microcytic hypochromic anemia",
  "Iron deficiency anemia secondary to blood loss",
  "Iron deficiency anemia secondary to inadequate dietary iron intake",
  "Iron deficiency anemia secondary to malabsorption",
  "Iron deficiency anemia in pregnancy",
  "Plummer-Vinson syndrome",
  "Sideropenic anemia",
  "Refractory iron deficiency anemia"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "271737000",
   "why": "too broad; represents general anemia without specification of iron deficiency"
  },
  {
   "code": "237602007",
   "why": "unrelated condition (metabolic syndrome)"
  },
  {
   "code": "95417003",
   "why": "unrelated condition (fibromyalgia)"
  },
  {
   "code": "67782005",
   "why": "unrelated condition (acute respiratory distress syndrome)"
  },
  {
   "code": "72892002",
   "why": "unrelated condition (normal pregnancy)"
  },
  {
   "code": "79586000",
   "why": "unrelated condition (tubal pregnancy)"
  },
  {
   "code": "36955009",
   "why": "unrelated finding (loss of taste)"
  },
  {
   "code": "62564004",
   "why": "unrelated condition (concussion)"
  },
  {
   "code": "62106007",
   "why": "unrelated condition (concussion)"
  },
  {
   "code": "94260004",
   "why": "unrelated condition (secondary malignant neoplasm of colon)"
  }
 ],
 "status": "UNMAPPABLE"
}
```

