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
 "concept": "Acute pancreatitis",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> gemini-3.7-flash-medium  cassette `a04e191ceabd3a4b`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Acute pancreatitis
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

### 4. llm_response (cassette, 147 tok, 30.137s)

```
```json
{
  "names": [
    "Acute pancreatitis",
    "Acute biliary pancreatitis",
    "Gallstone pancreatitis",
    "Acute alcoholic pancreatitis",
    "Acute necrotizing pancreatitis",
    "Acute edematous pancreatitis",
    "Acute interstitial pancreatitis",
    "Acute hemorrhagic pancreatitis",
    "Severe acute pancreatitis",
    "Infected pancreatic necrosis",
    "Post-ERCP acute pancreatitis",
    "Drug-induced acute pancreatitis",
    "Idiopathic acute pancreatitis"
  ],
  "note": "Includes general presentation, morphologic subtypes, and common etiologic variants."
}
```
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Acute pancreatitis",
  "Acute biliary pancreatitis",
  "Gallstone pancreatitis",
  "Acute alcoholic pancreatitis",
  "Acute necrotizing pancreatitis",
  "Acute edematous pancreatitis",
  "Acute interstitial pancreatitis",
  "Acute hemorrhagic pancreatitis",
  "Severe acute pancreatitis",
  "Infected pancreatic necrosis",
  "Post-ERCP acute pancreatitis",
  "Drug-induced acute pancreatitis",
  "Idiopathic acute pancreatitis"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "10509002",
  "display": "Acute bronchitis (disorder)",
  "domain": "condition",
  "n_resources": 266
 },
 {
  "code": "65275009",
  "display": "Acute Cholecystitis",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "195662009",
  "display": "Acute viral pharyngitis (disorder)",
  "domain": "condition",
  "n_resources": 347
 },
 {
  "code": "75498004",
  "display": "Acute bacterial sinusitis (disorder)",
  "domain": "condition",
  "n_resources": 38
 },
 {
  "code": "241929008",
  "display": "Acute allergic reaction",
  "domain": "condition",
  "n_resources": 6
 },
 {
  "code": "706870000",
  "display": "Acute pulmonary embolism (disorder)",
  "domain": "condition",
  "n_resources": 4
 },
 {
  "code": "65710008",
  "display": "Acute respiratory failure (disorder)",
  "domain": "condition",
  "n_resources": 2
 },
 {
  "code": "132281000119108",
  "display": "Acute deep venous thrombosis (disorder)",
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
  "code": "80583007",
  "display": "Severe anxiety (panic) (finding",
  "domain": "condition",
  "n_resources": 59
 },
 {
  "code": "83664006",
  "display": "Idiopathic atrophic hypothyroidism",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "408512008",
  "display": "Body mass index 40+ - severely obese (finding)",
  "domain": "condition",
  "n_resources": 5
```

### 7. llm_request -> gemini-3.7-flash-medium  cassette `18ca0d0ab854943b`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Acute pancreatitis
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
          10509002  Acute bronchitis (disorder)   (in 266 resources)
          65275009  Acute Cholecystitis   (in 2 resources)
         195662009  Acute viral pharyngitis (disorder)   (in 347 resources)
          75498004  Acute bacterial sinusitis (disorder)   (in 38 resources)
         241929008  Acute allergic reaction   (in 6 resources)
         706870000  Acute pulmonary embolism (disorder)   (in 4 resources)
          65710008  Acute respiratory failure (disorder)   (in 2 resources)
   132281000119108  Acute deep venous thrombosis (disorder)   (in 2 resources)
          67782005  Acute respiratory distress syndrome (disorder)   (in 2 resources)
          80583007  Severe anxiety (panic) (finding   (in 59 resources)
          83664006  Idiopathic atrophic hypothyroidism   (in 1 resources)
         408512008  Body mass index 40+ - severely obese (finding)   (in 5 resources)

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

### 8. llm_response (cassette, 384 tok, 32.055s)

```
```json
{
  "codes": [],
  "rejected": [
    {
      "code": "10509002",
      "why": "refers to acute bronchitis (inflammation of the bronchi), not acute pancreatitis"
    },
    {
      "code": "65275009",
      "why": "refers to acute cholecystitis (gallbladder inflammation), not acute pancreatitis"
    },
    {
      "code": "195662009",
      "why": "refers to acute viral pharyngitis, not acute pancreatitis"
    },
    {
      "code": "75498004",
      "why": "refers to acute bacterial sinusitis, not acute pancreatitis"
    },
    {
      "code": "241929008",
      "why": "refers to an acute allergic reaction, not acute pancreatitis"
    },
    {
      "code": "706870000",
      "why": "refers to acute pulmonary embolism, not acute pancreatitis"
    },
    {
      "code": "65710008",
      "why": "refers to acute respiratory failure, not acute pancreatitis"
    },
    {
      "code": "132281000119108",
      "why": "refers to acute deep venous thrombosis, not acute pancreatitis"
    },
    {
      "code": "67782005",
      "why": "refers to acute respiratory distress syndrome, not acute pancreatitis"
    },
    {
      "code": "80583007",
      "why": "refers to severe anxiety/panic finding, lexical overlap with 'panic' in pancreatitis"
    },
    {
      "code": "83664006",
      "why": "refers to idiopathic atrophic hypothyroidism, not acute pancreatitis"
    },
    {
      "code": "408512008",
      "why": "refers to severe obesity finding, not acute pancreatitis"
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
 "concept": "Acute pancreatitis",
 "confidence": "high",
 "domain": "condition",
 "expanded_names": [
  "Acute pancreatitis",
  "Acute biliary pancreatitis",
  "Gallstone pancreatitis",
  "Acute alcoholic pancreatitis",
  "Acute necrotizing pancreatitis",
  "Acute edematous pancreatitis",
  "Acute interstitial pancreatitis",
  "Acute hemorrhagic pancreatitis",
  "Severe acute pancreatitis",
  "Infected pancreatic necrosis",
  "Post-ERCP acute pancreatitis",
  "Drug-induced acute pancreatitis",
  "Idiopathic acute pancreatitis"
 ],
 "reason": "the vocabulary returned candidates but none of them represents the concept",
 "rejected": [
  {
   "code": "10509002",
   "why": "refers to acute bronchitis (inflammation of the bronchi), not acute pancreatitis"
  },
  {
   "code": "65275009",
   "why": "refers to acute cholecystitis (gallbladder inflammation), not acute pancreatitis"
  },
  {
   "code": "195662009",
   "why": "refers to acute viral pharyngitis, not acute pancreatitis"
  },
  {
   "code": "75498004",
   "why": "refers to acute bacterial sinusitis, not acute pancreatitis"
  },
  {
   "code": "241929008",
   "why": "refers to an acute allergic reaction, not acute pancreatitis"
  },
  {
   "code": "706870000",
   "why": "refers to acute pulmonary embolism, not acute pancreatitis"
  },
  {
   "code": "65710008",
   "why": "refers to acute respiratory failure, not acute pancreatitis"
  },
  {
   "code": "132281000119108",
   "why": "refers to acute deep venous thrombosis, not acute pancreatitis"
  },
  {
   "code": "67782005",
   "why": "refers to acute respiratory distress syndrome, not acute pancreatitis"
  },
  {
   "code": "80583007",
   "why": "refers to severe anxiety/panic finding, lexical overlap with 'panic' in pancreatitis"
  },
  {
   "code": 
```

