# Agent trajectories

29 trajectories from `runs\tierA`. Each markdown file below is a rendering of the JSONL beside it, and the JSONL is the source of truth. Every model call in every one of them is matched to a recorded cassette by `python scripts/verify.py trajectories`, so the prompt shown here is byte-identical to the prompt that was sent.

| | |
|---|---|
| model calls | 80 |
| tool calls | 24 |
| schema rejections fed back to the model | 2 |
| retries after a schema rejection | 2 |
| requests resent after the endpoint failed | 19 |
| critic findings | 0 |
| predicates revised after a confirmed counterexample | 0 |
| malformed fields the harness repaired without a retry | 6 |
| human checkpoints | 0 |
| completion tokens | 15151 |

## The tools, and what calling one looks like in the log

| tool | calls | what it does, and why it is a tool rather than a prompt |
|---|---|---|
| `terminology.search_any` | 22 | lexical search over the codes this site's own records use. Deliberately not an embedding search: a near miss on a drug class is indistinguishable from a hit right up until it clears a patient. |
| `ground_cache.hit` | 2 | a concept already grounded for an earlier criterion, returned without a model call. Content-addressed on concept and domain. |

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
| compiler | [NCT06983054-INC-01-seed7](compiler/NCT06983054-INC-01-seed7.md) | 6 | 2 | 2 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-01-seed7](compiler/NCT06983054-EXC-01-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-02-seed7](compiler/NCT06983054-EXC-02-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-EXC-03-seed7](compiler/NCT06983054-EXC-03-seed7.md) | 12 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. SGLT2 inhib |
| compiler | [NCT06983054-EXC-04-seed7](compiler/NCT06983054-EXC-04-seed7.md) | 3 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Diabetic ke |
| compiler | [NCT06983054-EXC-05-seed7](compiler/NCT06983054-EXC-05-seed7.md) | 12 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-02-seed7](compiler/NCT06983054-INC-02-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-03-seed7](compiler/NCT06983054-INC-03-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-04-seed7](compiler/NCT06983054-INC-04-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-05-seed7](compiler/NCT06983054-INC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Menstrual history (no menses for >1 year) is not tracked in  |
| compiler | [NCT06983054-INC-06-seed7](compiler/NCT06983054-INC-06-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Evaluating a participant's ability or willingness to provide |
| compiler | [NCT06983054-INC-07-seed7](compiler/NCT06983054-INC-07-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-08-seed7](compiler/NCT06983054-INC-08-seed7.md) | 1 | 0 | 0 | 0 | 0 | refused: Dietary sodium intake is a lifestyle and nutritional assessm |
| compiler | [NCT06983054-INC-09-seed7](compiler/NCT06983054-INC-09-seed7.md) | 4 | 0 | 0 | 0 | 0 | compiled |
| compiler | [NCT06983054-INC-10-seed7](compiler/NCT06983054-INC-10-seed7.md) | 7 | 0 | 0 | 0 | 0 | refused: cannot be represented in this site's vocabulary. Sulfonylure |
| compiler | [NCT06989723-INC-01-seed7](compiler/NCT06989723-INC-01-seed7.md) | 2 | 0 | 0 | 0 | 0 | compiled |
| critic | [NCT06983054-EXC-01-seed7](critic/NCT06983054-EXC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-02-seed7](critic/NCT06983054-EXC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-EXC-05-seed7](critic/NCT06983054-EXC-05-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-01-seed7](critic/NCT06983054-INC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-02-seed7](critic/NCT06983054-INC-02-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-03-seed7](critic/NCT06983054-INC-03-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-04-seed7](critic/NCT06983054-INC-04-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-07-seed7](critic/NCT06983054-INC-07-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06983054-INC-09-seed7](critic/NCT06983054-INC-09-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| critic | [NCT06989723-INC-01-seed7](critic/NCT06989723-INC-01-seed7.md) | 1 | 0 | 0 | 0 | 0 | OK |
| segmenter | [NCT06717698](segmenter/NCT06717698.md) | 1 | 0 | 0 | 0 | 0 | done |
| segmenter | [NCT06983054](segmenter/NCT06983054.md) | 1 | 0 | 0 | 0 | 0 | done |
| segmenter | [NCT06989723](segmenter/NCT06989723.md) | 1 | 0 | 0 | 0 | 0 | done |

