# Development split, declared before any prompt is changed

Prompts are going to change. A compiler that refuses a criterion it should have
handled is a prompt defect, and fixing those is most of what the Improvement
Changelog will contain. The hazard is obvious: if the prompts are edited while
watching the scored criteria, the final number measures how well the prompts were
fitted to the answer sheet rather than how well the system works.

So the corpus is split, and the split is committed before the first edit.

## The two halves

| split | trials | used for |
|---|---|---|
| development | NCT06338553, NCT07065383, NCT07588256, NCT06578078, NCT06998862 | prompt iteration, agent design, failure analysis |
| held out | NCT06983054, NCT06989723, NCT06717698 | every scored run, every published number |

The three held-out trials are the ones with hand-authored gold labels in
`evaluation/gold/criteria_set.py`. The five development trials have no gold
labels and never will. Development is measured on things that need no answer key:
how many criteria compile, what the refusals say, how often the critic confirms a
counterexample, and whether a predicate crashes.

## The freeze

The prompt-carrying files are:

- `src/trialsieve/agents/segmenter.py`
- `src/trialsieve/agents/grounder.py`
- `src/trialsieve/agents/compiler.py`
- `src/trialsieve/agents/critic.py`

Every scored run reports the commit that last touched each of them. If that commit
is later than the commit that produced the scored output, the run is invalid and
is rerun. The ordering is a git fact, not a promise.

## One disclosure

The first defect in the changelog was not found on the development split. A two
criterion smoke test on 2026-08-29, run to check that the model backend was
wired up at all, returned a refusal on `NCT06983054-INC-01`, which is a held-out
criterion. The refusal reason was visible in the trajectory before this split
existed.

That is recorded here rather than quietly absorbed. The fix for it was developed
and measured on the development trials, and the held-out set was not compiled
again until the prompts were frozen. The knowledge that the defect exists is a
leak of one bit; pretending otherwise would be a larger one.

## What this does not protect against

The five development trials come from the same disease area and the same registry
as the held-out three. A prompt tuned on development still transfers assumptions
about how these particular sponsors write criteria. The split bounds tuning on the
answer key. It does not make the held-out set an independent sample of clinical
trials in general, and the report says so.
