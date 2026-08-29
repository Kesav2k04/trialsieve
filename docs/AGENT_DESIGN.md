# The agents, and what each one is not allowed to do

Six agents. Two of them call no model, and those two are where the design pays.
Each has a contract narrow enough that a failure has somewhere to show up rather
than being absorbed by the next stage.

The rule the whole design follows: **an agent that cannot do its job must fail
loudly at its own stage, never approximately at the next one.** Approximate
failure is how a system stays fluent while going wrong, and fluent wrongness is
the thing this project exists to make visible and countable. It still happens
here, 111 times in 15,400 cells, and the number is published rather than
designed away.

---

## Where the model calls are

| agent | model calls | cached on | what its failure looks like |
|---|---|---|---|
| `segmenter` | 1 per trial | trial record | criteria split badly, visible as odd fragments |
| `grounder` | 2 per concept | concept name and domain | UNMAPPABLE, which stops the criterion |
| `compiler` | 2 per criterion, plus repairs | criterion content hash | refusal with a named blocker, or invalid IR that the validator rejects |
| `critic` | 1 per criterion, plus 1 revision | predicate digest | a counterexample that the engine then confirms or dismisses |
| `adjudicator` | **0** | nothing to cache, it is a pure function | a raised exception, never a verdict |
| `worklist` | 0 | nothing | a refusal to render without sign-off |

The grounder cache is the one that matters economically. Forty criteria across
three trials referenced far fewer distinct concepts than criteria, and every
repeat is free. In one development run two consecutive criteria cost 26 model
calls and then 1, because the second asked about concepts the first had already
grounded.

---

## `segmenter`

**Contract.** A registry eligibility blob goes in. Atomic criteria come out, each
with a kind (inclusion or exclusion), a category, and a content hash.

**Why the hash.** Two trials in a therapeutic area often state the same criterion.
The hash is what lets the evaluation deduplicate, so effective N in every interval
is unique criteria rather than repeated ones. Counting the same criterion three
times would narrow every confidence interval by a factor it has not earned.

**What it may not do.** Interpret. It splits and labels; it does not decide
whether anything is checkable.

---

## `grounder`

Three steps, and the middle one is not a model.

1. **Expand** (model). The concept as a protocol writes it, into the specific
   names a record would hold. "SGLT2 inhibitor" becomes a list of ingredients.
   This is world knowledge and the prompt says so: do not guess what this
   particular site records, that is looked up separately.
2. **Search** (local, deterministic). A lexical search over the site's own
   vocabulary, built from the corpus. Deliberately lexical: an embedding search
   returns a plausible neighbour for a concept the vocabulary does not contain,
   and a near miss on a drug class is indistinguishable from a hit right up until
   it silently clears a patient.
3. **Select** (model). Choose from the candidates. Never invent a code. Returning
   nothing is a documented, expected answer.

**The outcomes.** MAPPED, PARTIAL, BROADER_ONLY, and **UNMAPPABLE**. Unmappable is the one
that earns its place. This corpus contains no SGLT2 inhibitor, GLP-1 agonist,
DPP-4 inhibitor, thiazolidinedione or sulfonylurea code at all. A grounder that
returns an empty code list and lets the criterion compile hands a closed-world
query an empty result, which clears every patient on that exclusion. So an
unmappable concept stops the criterion and routes it to a person.

**A fourth outcome, BROADER_ONLY.** A candidate can contain the concept without
establishing it: an unqualified anaemia code where the criterion asks about iron
deficiency anaemia. Those go into `broader_codes` rather than `codes`, the
criterion still compiles, and the engine returns UNKNOWN for the patients who
carry the coarse code while absence continues to mean what it meant. This is
deliberately not UNMAPPABLE, because refusing the criterion for everyone would
discard every ruleout the coarse code supports.

**Hallucinated codes are dropped.** Anything the model returns that was not on the
shortlist it was given is discarded before it reaches the IR.

**What that check used to miss.** The allow-list it tested against was the union
of `codes` and `broader_codes`, so it established that a code is real and said
nothing about which of the two slots it belongs in. A broader-only code emitted
into `codes` passed. The asymmetry described above, the one the README calls this
design's sharp edge, was enforced by the prompt and by nothing else, and two
criteria in the published run broke it. The allow-list is now built per slot and
rejects the promotion by name, telling the model where the code belongs.
`scripts/grounding_audit.py` measures the result on any compiled run and
currently reports 9 criteria grounding a broader-only code with 0 promoted.
Changelog entries 25 and 29 have the defect and the repair.

**Its known blind spot.** A code that is in the vocabulary but on no patient's
chart looks like a successful mapping. That is caught downstream, in the review
packet, not here. See entry 6 of the improvement changelog.

---

## `compiler`

Two calls: **plan**, then **emit**.

**Plan** decides whether the criterion is checkable at all and lists the concepts
it needs. The prompt spends more space on what is *not* checkable than on what is,
because the default failure of a language model here is to produce a confident
predicate for a criterion about willingness to consent.

**Emit** writes the predicate against a grammar included verbatim in the prompt,
using only the codes the grounder returned.

**The repair loop.** Output is parsed and validated against the IR grammar. On
failure the model gets the validator's error **verbatim** and one more attempt,
twice. Every rejection and every piece of feedback is in the trajectory, so the
repair loop is inspectable rather than a retry count.

**Normalisation versus repair.** Some errors are trivial: a model writing
`laboratory_value` where the grammar says `observation`. Those are normalised by
the harness and recorded as `normalisation` events, kept separate from `revision`
events, which mean a predicate was rewritten after a confirmed counterexample.
Summing the two would make a housekeeping number look like a review result.

**What it may not do.** Emit a code it was not given. Emit a predicate for a
criterion its own plan step called uncheckable.

---

## `critic`

The one that is falsifiable.

A critic that returns an opinion is worth nothing: a talkative model manufactures
findings and a lazy one hides behind general remarks. So this critic is required
to produce a **counterexample**: a specific patient described in facts, plus the
truth value the criterion should take for that patient.

The harness then **builds that patient into a chart and runs the predicate against
it**.

- Predicate returns what the critic predicted: the critic was wrong. The finding
  is **DISMISSED** and recorded as dismissed.
- Predicate returns something else: prose and predicate genuinely disagree, and
  the exact patient that exposes it goes back to the compiler as feedback.

The revision budget is one. A predicate that survives one confirmed counterexample
and its correction goes forward; anything more is a criterion that needs a human,
not another loop.

What it looks for, in the prompt's own order: window errors (is "within 6 months"
183 days, and does an event just inside the boundary behave), boundary errors
(`>` against `>=`), direction errors (an exclusion predicate must be TRUE for the
patient who should be excluded), and absence errors (is `absent_means` set to `false` for something that
routinely lives at another hospital). That fourth one is the class it is weakest
at, and the weakness is measured rather than suspected: `docs/CRITIC_PROBE.md`
plants defects of each class and the critic catches 15 of 15 across the other
three and **3 of 4** on absence. It also passed the real one, the criterion
behind changelog entries 25 and 30. A reviewer that is worst at the defect this
design cares most about is the reason the human sign-off gate is not decoration.

---

## `adjudicator`

**Zero model calls.** This is the whole bet.

It takes compiled predicates and a chart and returns a verdict, a reason, and the
dated resources it read. It is a pure function of (predicate, chart, unit policy).
Run it twice and you get the same bytes. Run it on four hundred patients and it
costs four hundred times nothing.

Everything the model contributed is upstream and frozen in a signed predicate. The
consequence a coordinator cares about: two patients with the same relevant facts
get the same answer, always, and the answer does not change because a model was
sampled again.

**What it may not do.** Guess. Every operation that cannot be performed exactly,
a unit that cannot be reconciled, a value dated outside a window, two conflicting
values on the same day, returns UNKNOWN with the reason attached, and the reason
names the specific obstacle.

---

## `worklist`

Renders the coordinator-facing document. Refuses to render unless every compiled
predicate carries a human signature over its digest.

Recompiling changes the digest and invalidates the signature. There is no
`--approve-all`. There is an `--allow-unsigned` flag for demonstrating the gate,
and using it stamps **NOT FOR USE** across the top of the output.

---

## How they are wired together

Sequential, not a swarm. Every stage consumes the previous stage's typed output
and every stage can refuse. There is no planner deciding which agent to call,
because the pipeline shape is known and a planner would only add a way for it to
go wrong.

The parts that look like orchestration and are not:

- **Caching** is content-addressed, not a coordination protocol. A grounded
  concept is reused because the concept name and domain are the same string.
- **Retries** are bounded, and the bound is a budget rather than a timeout. When
  it runs out the criterion is refused, not approximated.
- **Feedback** is always a fact, never a nudge. The validator's error text, or a
  patient the predicate demonstrably gets wrong. No stage tells another stage to
  try harder.

Every one of these steps is in the trajectories, including the failed ones:
[`runs/tierA/trajectories/index.md`](../runs/tierA/trajectories/index.md), sorted
so the trajectories that went wrong come first.
