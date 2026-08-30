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
 "concept": "Obesity",
 "domain": "condition",
 "intent": "as a trial protocol would mean it"
}
```

### 3. llm_request -> granite3.1-dense:8b  cassette `a32e3a47fdfef502`

```
[system]
You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it.

[user]
Expand this clinical concept into concrete searchable names.

Concept: Obesity
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

### 4. llm_response (openai, 200 tok, 8.694s)

```
{
  "names": [
    "Body Mass Index (BMI)",
    "Waist-Hip Ratio (WHR)",
    "Waist Circumference",
    "Obesity Class I (BMI 30-34.9)",
    "Obesity Class II (BMI 35-39.9)",
    "Obesity Class III (BMI >= 40)",
    "Severe Obesity",
    "Morbid Obesity",
    "Superobesity",
    "Grade 2 Obesity",
    "Grade 3 Obesity",
    "Overweight",
    "Classical Obesity",
    "Central Obesity",
    "Android Obesity"
  ],
  "note": "These are common terms used to describe obesity in clinical practice. The specific term used may vary depending on the context and the healthcare provider's preference."
}
```

### 5. tool_call `terminology.search_any`

```json
{
 "domain": "condition",
 "limit": 12,
 "terms": [
  "Body Mass Index (BMI)",
  "Waist-Hip Ratio (WHR)",
  "Waist Circumference",
  "Obesity Class I (BMI 30-34.9)",
  "Obesity Class II (BMI 35-39.9)",
  "Obesity Class III (BMI >= 40)",
  "Severe Obesity",
  "Morbid Obesity",
  "Superobesity",
  "Grade 2 Obesity",
  "Grade 3 Obesity",
  "Overweight",
  "Classical Obesity",
  "Central Obesity",
  "Android Obesity"
 ]
}
```

### 6. tool_result `terminology.search_any`

```json
[
 {
  "code": "162864005",
  "display": "Body mass index 30+ - obesity (finding)",
  "domain": "condition",
  "n_resources": 209
 },
 {
  "code": "408512008",
  "display": "Body mass index 40+ - severely obese (finding)",
  "domain": "condition",
  "n_resources": 5
 },
 {
  "code": "80583007",
  "display": "Severe anxiety (panic) (finding",
  "domain": "condition",
  "n_resources": 59
 },
 {
  "code": "431856006",
  "display": "Chronic kidney disease stage 2 (disorder)",
  "domain": "condition",
  "n_resources": 1
 },
 {
  "code": "283385000",
  "display": "Laceration of thigh",
  "domain": "condition",
  "n_resources": 26
 },
 {
  "code": "284549007",
  "display": "Laceration of hand",
  "domain": "condition",
  "n_resources": 19
 },
 {
  "code": "370247008",
  "display": "Facial laceration",
  "domain": "condition",
  "n_resources": 16
 },
 {
  "code": "284551006",
  "display": "Laceration of foot",
  "domain": "condition",
  "n_resources": 15
 },
 {
  "code": "283371005",
  "display": "Laceration of forearm",
  "domain": "condition",
  "n_resources": 14
 },
 {
  "code": "368581000119106",
  "display": "Neuropathy due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 9
 },
 {
  "code": "239872002",
  "display": "Osteoarthritis of hip",
  "domain": "condition",
  "n_resources": 7
 },
 {
  "code": "90781000119102",
  "display": "Microalbuminuria due to type 2 diabetes mellitus (disorder)",
  "domain": "condition",
  "n_resources": 1
 }
]
```

### 7. llm_request -> granite3.1-dense:8b  cassette `ce0ac2f370075115`

```
[system]
You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match.

[user]
Concept: Obesity
Record domain: condition
Meaning required: as a trial protocol would mean it

Candidate entries from this site's vocabulary:
         162864005  Body mass index 30+ - obesity (finding)   (in 209 resources)
         408512008  Body mass index 40+ - severely obese (finding)   (in 5 resources)
          80583007  Severe anxiety (panic) (finding   (in 59 resources)
         431856006  Chronic kidney disease stage 2 (disorder)   (in 1 resources)
         283385000  Laceration of thigh   (in 26 resources)
         284549007  Laceration of hand   (in 19 resources)
         370247008  Facial laceration   (in 16 resources)
         284551006  Laceration of foot   (in 15 resources)
         283371005  Laceration of forearm   (in 14 resources)
   368581000119106  Neuropathy due to type 2 diabetes mellitus (disorder)   (in 9 resources)
         239872002  Osteoarthritis of hip   (in 7 resources)
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

### 8. llm_response (openai, 139 tok, 12.473s)

```
{
  "codes": ["162864005"],
  "broader_codes": [],
  "rejected": [],
  "confidence": "high"
}

Explanation: The concept is obesity, and the domain is condition. The candidate that genuinely represents this concept is "Body mass index 30+ - obesity (finding)" with the code "162864005". None of the other candidates represent obesity as a condition; they either refer to different conditions, measurements, or are broader in scope. Therefore, no codes were rejected, and the confidence level is high.
```

### 9. final

```json
{
 "broader_codes": [],
 "codes": [
  "162864005"
 ],
 "concept": "Obesity",
 "confidence": "high",
 "displays": [
  "Body mass index 30+ - obesity (finding)"
 ],
 "domain": "condition",
 "expanded_names": [
  "Body Mass Index (BMI)",
  "Waist-Hip Ratio (WHR)",
  "Waist Circumference",
  "Obesity Class I (BMI 30-34.9)",
  "Obesity Class II (BMI 35-39.9)",
  "Obesity Class III (BMI >= 40)",
  "Severe Obesity",
  "Morbid Obesity",
  "Superobesity",
  "Grade 2 Obesity",
  "Grade 3 Obesity",
  "Overweight",
  "Classical Obesity",
  "Central Obesity",
  "Android Obesity"
 ],
 "matched_names": [],
 "reason": "1 of 12 candidates selected",
 "status": "PARTIAL",
 "unmatched_names": [
  "Android Obesity",
  "Body Mass Index (BMI)",
  "Central Obesity",
  "Classical Obesity",
  "Grade 2 Obesity",
  "Grade 3 Obesity",
  "Morbid Obesity",
  "Obesity Class I (BMI 30-34.9)",
  "Obesity Class II (BMI 35-39.9)",
  "Obesity Class III (BMI >= 40)",
  "Overweight",
  "Severe Obesity",
  "Superobesity",
  "Waist Circumference",
  "Waist-Hip Ratio (WHR)"
 ]
}
```

