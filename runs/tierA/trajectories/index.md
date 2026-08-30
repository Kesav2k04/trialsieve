# Agent trajectories

235 trajectories from `runs/tierA`. Each markdown file below is a rendering of the JSONL beside it, and the JSONL is the source of truth. Every model call in every one of them is matched to a recorded cassette by `python scripts/verify.py trajectories`, so the prompt shown here is byte-identical to the prompt that was sent.

| | |
|---|---|
| model calls | 1077 |
| tool calls | 265 |
| schema rejections fed back to the model | 3 |
| retries after a schema rejection | 8 |
| requests resent after the endpoint failed | 1 |
| critic findings | 31 |
| predicates revised after a confirmed counterexample | 5 |
| malformed fields the harness repaired without a retry | 72 |
| human checkpoints | 0 |
| completion tokens | 148878 |

## The tools, and what calling one looks like in the log

| tool | calls | what it does, and why it is a tool rather than a prompt |
|---|---|---|
| `terminology.search_any` | 197 | lexical search over the codes this site's own records use. Deliberately not an embedding search: a near miss on a drug class is indistinguishable from a hit right up until it clears a patient. |
| `ground_cache.hit` | 37 | a concept already grounded for an earlier criterion, returned without a model call. Content-addressed on concept and domain. |
| `execute_counterexample` | 31 | the critic names a patient the predicate should get wrong; the harness builds that chart and **runs the predicate against it**. The finding is then confirmed or dismissed by execution, which is what stops a critic from being an opinion. |

## Which agent is where, and the two that have no trajectory

Six agents. Four of them make model calls and appear below. Two do not, and their absence is the design rather than a gap:

| agent | where its trajectory is |
|---|---|
| `segmenter` | `segmenter/`, one per trial. Recorded by `evaluation/segmentation.py`, because the scored pipeline uses the hand-authored criterion set so a gold label can stay attached to a stable identifier. |
| `grounder` | inside each `compiler/` trajectory, as its `tool_call` to the terminology search and the model calls either side of it. It is a step of compiling one criterion, not a separate run, and splitting it out would break the thread a reader is following. |
| `compiler` | `compiler/`, one per criterion per seed. |
| `critic` | `critic/`, one per compiled criterion. |
| `adjudicator` | **none, and this is the whole bet.** It makes zero model calls. It is a pure function of predicate, chart and unit policy, so there is no trajectory to record: run it twice and it returns the same bytes. Its behaviour is in `tests/`, not in a log. |
| `worklist` | **none.** It renders a document and refuses to render it without a signature. The signature is a `human_checkpoint` event, and it lives in the compiler trajectory of the predicate that was signed. |

The baselines and the second labeller are recorded the same way and to the same standard, under `baseline-b2/` and `checker_b/`, so an arm this project is measured against cannot be a weaker implementation than the one it is compared to.

Sorted so the trajectories that went wrong come first. Those are the ones worth reading: they show what the agent was told about its own output and what it did next.

| agent | subject | calls | rejections | retries | critic | revised | outcome |
|---|---|---|---|---|---|---|---|
| compiler | [NCT06717698-EXC-01-seed7](compiler/NCT06717698-EXC-01-seed7.md) | 8 | 1 | 1 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Transient i |
| compiler | [NCT06717698-EXC-01-seed9](compiler/NCT06717698-EXC-01-seed9.md) | 8 | 1 | 1 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Transient i |
| compiler | [NCT06717698-INC-07-seed7](compiler/NCT06717698-INC-07-seed7.md) | 6 | 0 | 1 | 0 | 1 | compiled |
| compiler | [NCT06717698-INC-07-seed8](compiler/NCT06717698-INC-07-seed8.md) | 6 | 0 | 1 | 0 | 1 | compiled |
| compiler | [NCT06717698-INC-07-seed9](compiler/NCT06717698-INC-07-seed9.md) | 6 | 0 | 1 | 0 | 1 | compiled |
| compiler | [NCT06989723-EXC-01-seed8](compiler/NCT06989723-EXC-01-seed8.md) | 12 | 0 | 1 | 0 | 1 | compiled |
| compiler | [NCT06989723-EXC-01-seed9](compiler/NCT06989723-EXC-01-seed9.md) | 10 | 0 | 1 | 0 | 1 | compiled |
| compiler | [NCT06717698-EXC-01-seed8](compiler/NCT06717698-EXC-01-seed8.md) | 5 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Transient i |
| compiler | [NCT06717698-EXC-03-seed7](compiler/NCT06717698-EXC-03-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06717698-EXC-03-seed8](compiler/NCT06717698-EXC-03-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06717698-EXC-03-seed9](compiler/NCT06717698-EXC-03-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06717698-EXC-04-seed7](compiler/NCT06717698-EXC-04-seed7.md) | 5 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Lupus nephr |
| compiler | [NCT06717698-EXC-04-seed8](compiler/NCT06717698-EXC-04-seed8.md) | 5 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Lupus nephr |
| compiler | [NCT06717698-EXC-04-seed9](compiler/NCT06717698-EXC-04-seed9.md) | 5 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Lupus nephr |
| compiler | [NCT06717698-EXC-06-seed7](compiler/NCT06717698-EXC-06-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Determining whether diabetic retinopathy or maculopathy is ' |
| compiler | [NCT06717698-EXC-06-seed8](compiler/NCT06717698-EXC-06-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Determining whether diabetic retinopathy or maculopathy is ' |
| compiler | [NCT06717698-EXC-06-seed9](compiler/NCT06717698-EXC-06-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: Determining whether diabetic retinopathy or maculopathy is ' |
| compiler | [NCT06717698-EXC-07-seed7](compiler/NCT06717698-EXC-07-seed7.md) | 13 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Basal cell  |
| compiler | [NCT06717698-EXC-07-seed8](compiler/NCT06717698-EXC-07-seed8.md) | 15 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Basal cell  |
| compiler | [NCT06717698-EXC-07-seed9](compiler/NCT06717698-EXC-07-seed9.md) | 13 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Basal cell  |
| compiler | [NCT06717698-EXC-08-seed7](compiler/NCT06717698-EXC-08-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Not checkable because assessing whether a participant intend |
| compiler | [NCT06717698-EXC-08-seed8](compiler/NCT06717698-EXC-08-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion requires assessing future pregnancy intention, |
| compiler | [NCT06717698-EXC-08-seed9](compiler/NCT06717698-EXC-08-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion is not checkable because a patient's intention |
| compiler | [NCT06717698-INC-02-seed7](compiler/NCT06717698-INC-02-seed7.md) | 9 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Hysterectom |
| compiler | [NCT06717698-INC-02-seed8](compiler/NCT06717698-INC-02-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Determining whether a female is of non-childbearing potentia |
| compiler | [NCT06717698-INC-02-seed9](compiler/NCT06717698-INC-02-seed9.md) | 9 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Postmenopau |
| compiler | [NCT06717698-INC-04-seed7](compiler/NCT06717698-INC-04-seed7.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. eGFR based  |
| compiler | [NCT06717698-INC-04-seed8](compiler/NCT06717698-INC-04-seed8.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Creatinine  |
| compiler | [NCT06717698-INC-04-seed9](compiler/NCT06717698-INC-04-seed9.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. eGFR based  |
| compiler | [NCT06717698-INC-06-seed7](compiler/NCT06717698-INC-06-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion requires clinical judgment regarding the inves |
| compiler | [NCT06717698-INC-06-seed8](compiler/NCT06717698-INC-06-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion requires the investigator's opinion and clinic |
| compiler | [NCT06717698-INC-06-seed9](compiler/NCT06717698-INC-06-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion relies on the investigator's opinion regarding |
| compiler | [NCT06983054-EXC-03-seed7](compiler/NCT06983054-EXC-03-seed7.md) | 12 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. SGLT2 inhib |
| compiler | [NCT06983054-EXC-03-seed8](compiler/NCT06983054-EXC-03-seed8.md) | 12 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. SGLT2 inhib |
| compiler | [NCT06983054-EXC-03-seed9](compiler/NCT06983054-EXC-03-seed9.md) | 12 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. SGLT2 inhib |
| compiler | [NCT06983054-EXC-04-seed7](compiler/NCT06983054-EXC-04-seed7.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Diabetic ke |
| compiler | [NCT06983054-EXC-04-seed8](compiler/NCT06983054-EXC-04-seed8.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Diabetic ke |
| compiler | [NCT06983054-EXC-04-seed9](compiler/NCT06983054-EXC-04-seed9.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. diabetic ke |
| compiler | [NCT06983054-INC-05-seed7](compiler/NCT06983054-INC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Menstrual history (no menses for >1 year) is not tracked in  |
| compiler | [NCT06983054-INC-05-seed8](compiler/NCT06983054-INC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Menstrual history ('no menses >1 year') is not available in  |
| compiler | [NCT06983054-INC-05-seed9](compiler/NCT06983054-INC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: Menstrual history (no menses for >1 year) is not reliably ca |
| compiler | [NCT06983054-INC-06-seed7](compiler/NCT06983054-INC-06-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Evaluating a participant's ability or willingness to provide |
| compiler | [NCT06983054-INC-06-seed8](compiler/NCT06983054-INC-06-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Evaluating a participant's ability and willingness to provid |
| compiler | [NCT06983054-INC-06-seed9](compiler/NCT06983054-INC-06-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: Ability to provide informed consent reflects participant wil |
| compiler | [NCT06983054-INC-08-seed7](compiler/NCT06983054-INC-08-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Dietary sodium intake is a lifestyle and nutritional assessm |
| compiler | [NCT06983054-INC-08-seed8](compiler/NCT06983054-INC-08-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Daily dietary sodium intake is a lifestyle/nutritional asses |
| compiler | [NCT06983054-INC-08-seed9](compiler/NCT06983054-INC-08-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: Daily dietary sodium intake is dietary/lifestyle assessment  |
| compiler | [NCT06983054-INC-10-seed7](compiler/NCT06983054-INC-10-seed7.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Sulfonylure |
| compiler | [NCT06983054-INC-10-seed8](compiler/NCT06983054-INC-10-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: The requirement for a 'stable dose' lacks a defined time win |
| compiler | [NCT06983054-INC-10-seed9](compiler/NCT06983054-INC-10-seed9.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Sulfonylure |
| compiler | [NCT06989723-EXC-02-seed7](compiler/NCT06989723-EXC-02-seed7.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06989723-EXC-02-seed8](compiler/NCT06989723-EXC-02-seed8.md) | 8 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06989723-EXC-02-seed9](compiler/NCT06989723-EXC-02-seed9.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. GLP-1 recep |
| compiler | [NCT06989723-EXC-03-seed7](compiler/NCT06989723-EXC-03-seed7.md) | 9 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. end-stage r |
| compiler | [NCT06989723-EXC-03-seed8](compiler/NCT06989723-EXC-03-seed8.md) | 9 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. End-stage r |
| compiler | [NCT06989723-EXC-03-seed9](compiler/NCT06989723-EXC-03-seed9.md) | 9 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. End-stage r |
| compiler | [NCT06989723-EXC-04-seed7](compiler/NCT06989723-EXC-04-seed7.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Hepatocellu |
| compiler | [NCT06989723-EXC-04-seed8](compiler/NCT06989723-EXC-04-seed8.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. hepatocellu |
| compiler | [NCT06989723-EXC-04-seed9](compiler/NCT06989723-EXC-04-seed9.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Hepatocellu |
| compiler | [NCT06989723-EXC-05-seed7](compiler/NCT06989723-EXC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion requires investigator judgement to determine w |
| compiler | [NCT06989723-EXC-05-seed8](compiler/NCT06989723-EXC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion depends on an investigator's subjective judgem |
| compiler | [NCT06989723-EXC-05-seed9](compiler/NCT06989723-EXC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: The criterion is not checkable because it requires investiga |
| compiler | [NCT06989723-INC-03-seed7](compiler/NCT06989723-INC-03-seed7.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Sulfonylure |
| compiler | [NCT06989723-INC-03-seed8](compiler/NCT06989723-INC-03-seed8.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Sulfonylure |
| compiler | [NCT06989723-INC-03-seed9](compiler/NCT06989723-INC-03-seed9.md) | 5 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. sulfonylure |
| compiler | [NCT06989723-INC-04-seed7](compiler/NCT06989723-INC-04-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Fibroscan Controlled Attenuation Parameter (CAP) is an elast |
| compiler | [NCT06989723-INC-04-seed8](compiler/NCT06989723-INC-04-seed8.md) | 1 | 0 | 0 | 0 | 0 | refused: Requires FibroScan elastography and controlled attenuation p |
| compiler | [NCT06989723-INC-04-seed9](compiler/NCT06989723-INC-04-seed9.md) | 1 | 0 | 0 | 0 | 0 | refused: FibroScan controlled attenuation parameter (CAP) is an elast |
| contamination | [NCT06983054-INC-01-CF](contamination/NCT06983054-INC-01-CF.md) | 1 | 0 | 0 | 0 | 0 | refused: T2.7DM is not a standardized coded condition in electronic h |
| contamination | [NCT06983054-INC-05-CF](contamination/NCT06983054-INC-05-CF.md) | 1 | 0 | 0 | 0 | 0 | refused: Menstrual history (no menses >1 year) is not available in st |
| contamination | [NCT06983054-INC-08-CF](contamination/NCT06983054-INC-08-CF.md) | 1 | 0 | 0 | 0 | 0 | refused: Dietary sodium intake is a lifestyle and nutritional measure |
| compiler | [NCT06989723-INC-05-seed8](compiler/NCT06989723-INC-05-seed8.md) | 15 | 1 | 1 | 0 | 0 | compiled |
| critic | [NCT06717698-INC-03-seed7](critic/NCT06717698-INC-03-seed7.md) | 1 | 0 | 0 | 1 | 0 | OK |
| critic | [NCT06717698-INC-03-seed9](critic/NCT06717698-INC-03-seed9.md) | 1 | 0 | 0 | 1 | 0 | OK |
| critic | [NCT06717698-INC-07-seed7](critic/NCT06717698-INC-07-seed7.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic | [NCT06717698-INC-07-seed8](critic/NCT06717698-INC-07-seed8.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic | [NCT06717698-INC-07-seed9](critic/NCT06717698-INC-07-seed9.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic | [NCT06989723-EXC-01-seed8](critic/NCT06989723-EXC-01-seed8.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic | [NCT06989723-EXC-01-seed9](critic/NCT06989723-EXC-01-seed9.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-EXC-02--absence](critic_probe/NCT06717698-EXC-02--absence.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-EXC-02--direction](critic_probe/NCT06717698-EXC-02--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-EXC-02--window](critic_probe/NCT06717698-EXC-02--window.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-EXC-05--direction](critic_probe/NCT06717698-EXC-05--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-EXC-05--window](critic_probe/NCT06717698-EXC-05--window.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-INC-07--absence](critic_probe/NCT06717698-INC-07--absence.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-INC-07--control](critic_probe/NCT06717698-INC-07--control.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-INC-07--direction](critic_probe/NCT06717698-INC-07--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06717698-INC-07--window](critic_probe/NCT06717698-INC-07--window.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-EXC-05--absence](critic_probe/NCT06983054-EXC-05--absence.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-EXC-05--direction](critic_probe/NCT06983054-EXC-05--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-EXC-05--window](critic_probe/NCT06983054-EXC-05--window.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-01--boundary](critic_probe/NCT06983054-INC-01--boundary.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-01--direction](critic_probe/NCT06983054-INC-01--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-01--threshold](critic_probe/NCT06983054-INC-01--threshold.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-02--direction](critic_probe/NCT06983054-INC-02--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-03--direction](critic_probe/NCT06983054-INC-03--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-04--boundary](critic_probe/NCT06983054-INC-04--boundary.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-04--direction](critic_probe/NCT06983054-INC-04--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-04--threshold](critic_probe/NCT06983054-INC-04--threshold.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-07--direction](critic_probe/NCT06983054-INC-07--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-09--boundary](critic_probe/NCT06983054-INC-09--boundary.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-09--direction](critic_probe/NCT06983054-INC-09--direction.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| critic_probe | [NCT06983054-INC-09--threshold](critic_probe/NCT06983054-INC-09--threshold.md) | 1 | 0 | 0 | 1 | 0 | REVISE |
| counterexample | [NCT06983054-INC-09--03e502b6](counterexample/NCT06983054-INC-09--03e502b6.md) | 1 | 0 | 0 | 0 | 0 | INDETERMINATE |
| segmenter | [NCT06989723](segmenter/NCT06989723.md) | 1 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [0bbf4179-b2_10p](baseline-b2/0bbf4179-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [0fc183b2-b2_10p](baseline-b2/0fc183b2-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [219ddc63-b2_10p](baseline-b2/219ddc63-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [319372b8-b2_10p](baseline-b2/319372b8-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [60b0873c-b2_10p](baseline-b2/60b0873c-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [72b71d33-b2_10p](baseline-b2/72b71d33-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [75bfc8f4-b2_10p](baseline-b2/75bfc8f4-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [aade3c61-b2_10p](baseline-b2/aade3c61-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [d19face0-b2_10p](baseline-b2/d19face0-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| baseline-b2 | [d29560ea-b2_10p](baseline-b2/d29560ea-b2_10p.md) | 40 | 0 | 0 | 0 | 0 | done |
| compiler | [NCT06717698-EXC-02-seed7](compiler/NCT06717698-EXC-02-seed7.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-EXC-02-seed8](compiler/NCT06717698-EXC-02-seed8.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-EXC-02-seed9](compiler/NCT06717698-EXC-02-seed9.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-EXC-05-seed7](compiler/NCT06717698-EXC-05-seed7.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-EXC-05-seed8](compiler/NCT06717698-EXC-05-seed8.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-EXC-05-seed9](compiler/NCT06717698-EXC-05-seed9.md) | 6 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-01-seed7](compiler/NCT06717698-INC-01-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-01-seed8](compiler/NCT06717698-INC-01-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-01-seed9](compiler/NCT06717698-INC-01-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-03-seed7](compiler/NCT06717698-INC-03-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-03-seed8](compiler/NCT06717698-INC-03-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-03-seed9](compiler/NCT06717698-INC-03-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-05-seed7](compiler/NCT06717698-INC-05-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-05-seed8](compiler/NCT06717698-INC-05-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06717698-INC-05-seed9](compiler/NCT06717698-INC-05-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-01-seed7](compiler/NCT06983054-EXC-01-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-01-seed8](compiler/NCT06983054-EXC-01-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-01-seed9](compiler/NCT06983054-EXC-01-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-02-seed7](compiler/NCT06983054-EXC-02-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-02-seed8](compiler/NCT06983054-EXC-02-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-02-seed9](compiler/NCT06983054-EXC-02-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-05-seed7](compiler/NCT06983054-EXC-05-seed7.md) | 12 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-05-seed8](compiler/NCT06983054-EXC-05-seed8.md) | 12 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-05-seed9](compiler/NCT06983054-EXC-05-seed9.md) | 12 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-01-seed7](compiler/NCT06983054-INC-01-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-01-seed8](compiler/NCT06983054-INC-01-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-01-seed9](compiler/NCT06983054-INC-01-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-02-seed7](compiler/NCT06983054-INC-02-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-02-seed8](compiler/NCT06983054-INC-02-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-02-seed9](compiler/NCT06983054-INC-02-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-03-seed7](compiler/NCT06983054-INC-03-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-03-seed8](compiler/NCT06983054-INC-03-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-03-seed9](compiler/NCT06983054-INC-03-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-04-seed7](compiler/NCT06983054-INC-04-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-04-seed8](compiler/NCT06983054-INC-04-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-04-seed9](compiler/NCT06983054-INC-04-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-07-seed7](compiler/NCT06983054-INC-07-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-07-seed8](compiler/NCT06983054-INC-07-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-07-seed9](compiler/NCT06983054-INC-07-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-09-seed7](compiler/NCT06983054-INC-09-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-09-seed8](compiler/NCT06983054-INC-09-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-09-seed9](compiler/NCT06983054-INC-09-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-EXC-01-seed7](compiler/NCT06989723-EXC-01-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-01-seed7](compiler/NCT06989723-INC-01-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-01-seed8](compiler/NCT06989723-INC-01-seed8.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-01-seed9](compiler/NCT06989723-INC-01-seed9.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-02-seed7](compiler/NCT06989723-INC-02-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-02-seed8](compiler/NCT06989723-INC-02-seed8.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-02-seed9](compiler/NCT06989723-INC-02-seed9.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-05-seed7](compiler/NCT06989723-INC-05-seed7.md) | 14 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06989723-INC-05-seed9](compiler/NCT06989723-INC-05-seed9.md) | 14 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-EXC-01-CF](contamination/NCT06983054-EXC-01-CF.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-INC-02-CF](contamination/NCT06983054-INC-02-CF.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-INC-03-CF](contamination/NCT06983054-INC-03-CF.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-INC-04-CF](contamination/NCT06983054-INC-04-CF.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-INC-07-CF](contamination/NCT06983054-INC-07-CF.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| contamination | [NCT06983054-INC-09-CF](contamination/NCT06983054-INC-09-CF.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| critic | [NCT06717698-EXC-02-seed7](critic/NCT06717698-EXC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-EXC-02-seed8](critic/NCT06717698-EXC-02-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-EXC-02-seed9](critic/NCT06717698-EXC-02-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-EXC-05-seed7](critic/NCT06717698-EXC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-EXC-05-seed8](critic/NCT06717698-EXC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-EXC-05-seed9](critic/NCT06717698-EXC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-01-seed7](critic/NCT06717698-INC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-01-seed8](critic/NCT06717698-INC-01-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-01-seed9](critic/NCT06717698-INC-01-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-03-seed8](critic/NCT06717698-INC-03-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-05-seed7](critic/NCT06717698-INC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-05-seed8](critic/NCT06717698-INC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06717698-INC-05-seed9](critic/NCT06717698-INC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-01-seed7](critic/NCT06983054-EXC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-01-seed8](critic/NCT06983054-EXC-01-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-01-seed9](critic/NCT06983054-EXC-01-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-02-seed7](critic/NCT06983054-EXC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-02-seed8](critic/NCT06983054-EXC-02-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-02-seed9](critic/NCT06983054-EXC-02-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-05-seed7](critic/NCT06983054-EXC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-05-seed8](critic/NCT06983054-EXC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-05-seed9](critic/NCT06983054-EXC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-01-seed7](critic/NCT06983054-INC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-01-seed8](critic/NCT06983054-INC-01-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-01-seed9](critic/NCT06983054-INC-01-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-02-seed7](critic/NCT06983054-INC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-02-seed8](critic/NCT06983054-INC-02-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-02-seed9](critic/NCT06983054-INC-02-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-03-seed7](critic/NCT06983054-INC-03-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-03-seed8](critic/NCT06983054-INC-03-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-03-seed9](critic/NCT06983054-INC-03-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-04-seed7](critic/NCT06983054-INC-04-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-04-seed8](critic/NCT06983054-INC-04-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-04-seed9](critic/NCT06983054-INC-04-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-07-seed7](critic/NCT06983054-INC-07-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-07-seed8](critic/NCT06983054-INC-07-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-07-seed9](critic/NCT06983054-INC-07-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-09-seed7](critic/NCT06983054-INC-09-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-09-seed8](critic/NCT06983054-INC-09-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-09-seed9](critic/NCT06983054-INC-09-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-EXC-01-seed7](critic/NCT06989723-EXC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-01-seed7](critic/NCT06989723-INC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-01-seed8](critic/NCT06989723-INC-01-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-01-seed9](critic/NCT06989723-INC-01-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-02-seed7](critic/NCT06989723-INC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-02-seed8](critic/NCT06989723-INC-02-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-02-seed9](critic/NCT06989723-INC-02-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-05-seed7](critic/NCT06989723-INC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-05-seed8](critic/NCT06989723-INC-05-seed8.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-05-seed9](critic/NCT06989723-INC-05-seed9.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06717698-EXC-02--control](critic_probe/NCT06717698-EXC-02--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06717698-EXC-05--absence](critic_probe/NCT06717698-EXC-05--absence.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06717698-EXC-05--control](critic_probe/NCT06717698-EXC-05--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-EXC-05--control](critic_probe/NCT06983054-EXC-05--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-01--absence](critic_probe/NCT06983054-INC-01--absence.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-01--control](critic_probe/NCT06983054-INC-01--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-02--control](critic_probe/NCT06983054-INC-02--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-03--control](critic_probe/NCT06983054-INC-03--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-04--control](critic_probe/NCT06983054-INC-04--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-07--control](critic_probe/NCT06983054-INC-07--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic_probe | [NCT06983054-INC-09--control](critic_probe/NCT06983054-INC-09--control.md) | 1 | 0 | 0 | 0 | 0 | OK |
| segmenter | [NCT06717698](segmenter/NCT06717698.md) | 1 | 0 | 0 | 0 | 0 | done |
| segmenter | [NCT06983054](segmenter/NCT06983054.md) | 1 | 0 | 0 | 0 | 0 | done |

