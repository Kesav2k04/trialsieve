# TrialSieve

**The model reads the protocol once. It never reads a patient.**

Clinical trial prescreening, built so that ruling a patient out on a fact that is
missing from their record is a decision somebody has to make on purpose, in
writing, where a reviewer can see it. On this run one criterion made that
decision and it cost 358 wrong exclusions. That is measured below rather than
claimed away.

---

## Start here: what a per-cell model does with a missing lab

The criterion is from a real registered trial:

> Urine albumin-to-creatinine ratio below 30 mg/mmol.

In this panel, 359 of 385 patients have no UACR result at all, so a record with
nothing to compare against is the normal case rather than an unlucky one.

Ask a capable model directly, one cell at a time, giving it the criterion and the
patient's chart. Over all 400 cells of that arm it **commits to a verdict on 272
of them**, 68%, including cells where the record is silent. Nothing in the chart
contradicts the threshold, so the threshold appears satisfied. The reasoning is
fluent and the answer is confident, and on those same 400 cells it is wrong on
43.8% of what it commits to against TrialSieve's 3.2%.

TrialSieve answers:

```
INDETERMINATE
  no observation with code 14959-1 in the record
```

The difference is not accuracy on a hard case. It is that one of these systems can
represent "the record does not say" and the other cannot. A coordinator reading the
first output has no way to tell it apart from a real result, and the patient it
concerns is quietly dropped from consideration by a fact that was never there.

That failure is silent by construction: nobody audits the people who were screened
out, because nobody looks at them again.

**The worked pair is generated, not written, and it is not cherry-picked.**
`python scripts/counterexample.py` runs both arms on one patient and writes the
transcript to [docs/COUNTEREXAMPLE.md](docs/COUNTEREXAMPLE.md), using the same
baseline code path the evaluation scores. On the patient it picks, the baseline
abstained too, and the document says so rather than hiding it. That is the point
of publishing the rate instead of the anecdote: the failure is not that the model
is always wrong, it is that it cannot tell you when it does not know, and two
thirds of the time it does not tell you.

---

## What this is

A prescreening system that turns a panel of several hundred patients into a ranked
worklist: the people who are provably ineligible are removed with a dated citation
each, and everyone else is ordered by how few questions remain.

The bottleneck it targets is not the individual chart. A coordinator reading one
chart against one criterion is not the slow step, and this project has no
measurement of how long that takes, so it does not put a number on it. The slow
step is that the list is longer than the reading capacity, so candidates get worked
in whatever order the list arrives in.

What can be measured here is the shrink. The panel is 385 Synthea patients and the
held-out protocol is 40 criteria, giving 15,400 patient-criterion cells.
`results/RESULTS.md` reports what fraction of that grid the system settles and how
many of the settled cells it gets wrong. Both numbers come from
`scripts/report.py`, and the second one is the one that decides whether the first
is worth anything.

**And what is left is shaped like questions, not like patients.** On the published
worklist (one trial, the zero-false-exclusion operating point) the engine settles
187 of 385 screens and clears 8 to contact. The 190 that remain open contain **two
distinct questions**, and 188 of them are open on the same one, so it is answered
once and they resolve together. That is 1,155 cell judgements reduced to two
things a person has to find out. It follows from compiling once instead of asking
per cell: a predicate fails the same way for everyone it fails for, so its residue
sorts into questions, while a per-cell model answers each patient separately and
leaves a residue that sorts into patients with nothing to group. The counts are
generated into [docs/COST.md](docs/COST.md) from
[docs/sample_worklist.json](docs/sample_worklist.json), and the section there
states what does and does not generalise from one trial.

The job worth doing is to shrink the list **without a single false exclusion**.
That constraint is why the interesting number in this repository is not accuracy.
A system that removes nobody is safe and useless; a system that removes the wrong
person has done the one harm prescreening can do. Coverage and silent error are
reported as a pair for that reason, and neither is reported alone.

## The architecture, and why it is shaped this way

The obvious build puts the chart and the criteria in one prompt and asks for
verdicts. It is fast and it is wrong in a specific direction: it collapses "the
record does not say" into a verdict, and the output gives a reader no way to tell
which is which.

TrialSieve splits the problem at the point where the work is reusable:

```
protocol text ──▶ [segmenter] ──▶ [grounder] ──▶ [compiler] ──▶ [critic]
                                                                   │
                                                     typed predicate IR
                                                                   │
                                                  [human sign-off, enforced]
                                                                   │
   385 patients ────────────────────────────────▶ [engine, no model] ──▶ worklist
```

**The scored pipeline starts at the compiler, not at the segmenter.** The
segmenter runs and its output is measured in `docs/SEGMENTATION.md`, but the
criterion set every arm is scored on is hand-authored, in
`evaluation/gold/criteria_set.py`, so that arms are compared on verdicts rather
than on how each of them happened to cut the protocol into pieces. That choice
costs something and the cost is published: the segmenter produced 65 criteria
across the three trials and the gold set keeps 40, so coverage is reported against
both denominators in `results/RESULTS.md` and the registered one is 65.

**Compilation happens once per criterion. Execution happens once per patient and
calls no model at all.** Three things follow.

1. Every verdict is a predicate plus the dated resources it read. It is citable
   down to a FHIR resource id.
2. Adding a patient costs arithmetic. A bigger panel makes the economics better,
   not worse.
3. A human reviews the model's clinical judgement **once per criterion**, not once
   per patient per criterion. Sign-off scales with the protocol, which has about
   forty criteria, not with the queue, which has 385 people.

### The agents

| agent | job | model calls |
|---|---|---|
| `segmenter` | criteria blob to atomic, typed criteria | 1 per trial |
| `grounder` | clinical concept to codes in this site's vocabulary, or **UNMAPPABLE** | 2 per concept (expand, then select), cached across criteria |
| `compiler` | criterion prose to predicate IR, with a bounded repair loop | 2 per criterion |
| `critic` | build a patient the predicate gets wrong, then run it | 1 per criterion, plus 1 revision |
| `adjudicator` | execute predicates over the panel | **0** |
| `worklist` | rank and render what the coordinator opens | 0 |

The interesting row is the one with a zero in it. Everything downstream of the
compiler is deterministic, replayable and free.

### Three-valued logic, all the way down

The engine evaluates in Kleene's K3: TRUE, FALSE, UNKNOWN. `FALSE` dominates
conjunction, `TRUE` dominates disjunction, and UNKNOWN propagates otherwise. So a
patient with one proven disqualifier is ruled out even with ten questions still
open, and a patient with ten unknowns and no proven disqualifier is never ruled out
at all.

Two rules the code enforces rather than requests:

- **Absence is a modelled decision, not a default.** Every query into the record
  declares `absent_means` as `false` (this domain is trusted complete for these
  codes) or `unknown` (silence proves nothing). Under `unknown` a missing
  measurement returns INDETERMINATE and rules nobody out. Under `false` it
  returns FAILS, and the evidence it cites is an absence marker rather than a
  dated resource.
- **So absence can rule someone out, and that is the sharp edge of this design.**
  An earlier version of this file said absence never rules anyone out. The code
  says otherwise (`src/trialsieve/evaluator.py:233`) and so does the run: one
  criterion compiled with `absent_means: "false"` produced 358 of the 424 wrong
  exclusions in the whole evaluation. The control that is supposed to catch it is
  the human reading the predicate in English before any worklist exists, and on
  this run it was not caught. A single flag flips every query at once, and the
  sensitivity arm measures what that one field is worth: silent errors 469 down
  to 111, false exclusions 182 down to 18.

### A code can contain a concept without establishing it

A site codes at whatever grain it was built for, and it is rarely the grain a
protocol asks for. The one anaemia code in this corpus is unqualified, so a
criterion about iron deficiency anaemia meets a code that contains the answer
without giving it.

Both obvious handlings are wrong. Treat the coarse code as a match and you
manufacture MEETS verdicts the record cannot support. Call the concept unmappable
and you discard the half of the information that is real, which is the half that
removes people from the list.

So a query carries `broader_codes` beside `codes`, and they are read
asymmetrically:

| the record holds | verdict |
|---|---|
| a code from `codes` | TRUE |
| a code from `broader_codes` | UNKNOWN, naming the code and saying the site does not draw the distinction |
| neither | whatever `absent_means` says, unchanged |

Presence cannot settle it. Absence still can.

That is what the design promises. In the scored run it is false twice, and the
project found out by checking rather than by claiming. The compiler's emit
validator accepts any code the grounder returned, from either slot, because it
was written to catch invented codes and does that correctly. It cannot see a
real code put in the wrong slot. Two criteria out of the eight with broader-only
grounding promoted SNOMED 44054006 into `codes`, and both also carry
`absent_means: false`, so presence settles them as MEETS and absence settles
them as FAILS and neither can return INDETERMINATE. One of the two is the
criterion behind the 358 wrong exclusions above.

`python scripts/grounding_audit.py --run runs/tierA` reports it and exits 3.
`tests/test_grounding_audit.py` pins both by name. The compiler was left alone
on purpose: changing it recompiles the predicates and rescores the run, which is
picking a new number after seeing the old one fail. Entry 25 of the improvement
changelog has the reasoning and the cost.

### UNMAPPABLE is load-bearing

This corpus contains no SGLT2 inhibitor, GLP-1 receptor agonist, DPP-4 inhibitor,
thiazolidinedione or sulfonylurea codes. Only metformin and insulin.

A grounder that maps "SGLT2 inhibitor" to an empty code list and then applies
closed-world logic clears every patient on that exclusion criterion, confidently
and wrongly. So a concept with no code in the site's vocabulary makes the criterion
non-compilable and routes it to a human, rather than flowing through as an
absence.

## What a coordinator gets

A worklist that recommends nobody. It removes the provably ineligible with evidence,
ranks the rest by how little is left to check, and writes every open question as a
question addressed to a person. Sample output: `docs/sample_worklist.md`.

The predicates behind it cannot run against anyone until a named human has read and
signed each one:

```bash
python scripts/signoff.py --run runs/tierA --reviewer "..." --role "..."
```

The signature is over the predicate digest, so recompiling invalidates it. There is
no `--approve-all`, because a gate you can clear without reading is not a gate.
Evaluation runs are exempt and say so: measuring your own error rate affects nobody.

## Reproducing it

```bash
python -m pip install pytest      # the only install
python run.py reproduce           # offline, no API key, no model
```

Zero runtime dependencies: every import in `src/`, `evaluation/`, `scripts/` and
`tools/` is standard library, and `tests/test_dependencies.py` fails if that stops
being true. The video build is the one exception and is not on this path. Full
guide, including what each verification step rules out:
[REPRODUCE.md](REPRODUCE.md).

The recorded model calls are cassettes keyed on the sha256 of the full canonical
request. `python scripts/verify.py prove-replay` adds one space to one prompt and
shows the run stop with `CassetteMiss` rather than return the previous answer.
`prove-sensitivity` edits one recorded predicate and shows a published number move.
Together they say the recordings are load-bearing and tamper-evident.

## Evaluation

The protocol was pre-registered and committed before the first scored run, with
predictions written down so that being wrong is visible:
[docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md).

Two things about it are worth knowing before the numbers:

**The corpus cannot show the failure mode on its own.** Synthea records are complete
by construction, so absence-of-evidence barely occurs naturally and any silent error
rate measured on raw Synthea is a lower bound. A degradation harness induces it:
drop k% of criterion-relevant observations, flip a stored unit to a plausible
alternative, strip a date a window depends on, downgrade a coded condition to text.
Results are a curve over k, not a number. Real missingness is not random and
correlates with fragmented care and sicker patients, which is exactly what this
harness cannot reproduce.

**Gold has two independent routes.** Checker A is hand-authored predicates that
share no execution code with the engine. Checker B labels from criterion prose and
a flattened patient table only, on a different model family, with no sight of the
IR, of A, or of any system output. The pre-adjudication disagreement between them is
published as the label noise floor, and any measured difference smaller than that
floor is reported as uninterpretable rather than as a finding.

Results, the improvement history, and the trajectories:

- [results/RESULTS.md](results/RESULTS.md), generated by `scripts/report.py`
- [docs/IMPROVEMENT_CHANGELOG.md](docs/IMPROVEMENT_CHANGELOG.md)
- [runs/tierA/trajectories/index.md](runs/tierA/trajectories/index.md)
- [docs/CONTAMINATION.md](docs/CONTAMINATION.md), generated by `scripts/contamination.py`

### Did the model read these trials, or remember them?

Three registered trials with public identifiers is exactly the setup where a
result can be produced by recall. A model that saw NCT06983054 in training can
emit its thresholds without the criterion in front of it, and every number would
still be right, and the evaluation would be measuring memorisation.

Three checks, and the third is the one worth arguing with. A threshold is changed
to a value the real protocol never contained, the criterion is recompiled, and the
predicate has to carry the new number. **8 criteria perturbed, 6 compiled, 6 of 6
carry the perturbed value and none carries the original.** The two that refused
did so for concepts absent from the structured record at all, menstrual history
and dietary sodium intake, which is the same refusal they give unperturbed.

The first two checks are cheaper and run without a model: no prompt template has a
slot for a trial identifier or title, and no recorded request contains one. That
scan subtracts every word sequence the system is legitimately given, because
"chronic kidney disease" is in one of these titles and in half the criteria, and a
check that fires on the disease name can only ever return positive.

## How it fails

The honest list, before anyone else writes it.

**Coverage is the binding constraint, not accuracy.** Most criteria in a real
protocol cannot be settled from a structured record at all. Köpcke et al., across
15 trials, 351 criteria and 5 tertiary centres, put it at 55% expressible times
64% present, so about 35% answerable. A system that answers a third of the
questions and abstains on the rest is only useful because the third it answers
removes people from the list. That figure is also a registered prediction here:
`docs/EVAL_PROTOCOL.md` says coverage should land at 30 to 40% and that a number
far above it would suggest the criteria were cherry-picked.

**The compiler does not degrade by refusing. It degrades by accepting.** An
earlier version of this file predicted the opposite, that a weak model would lose
coverage rather than gain silent errors, because a model that cannot ground a
concept produces UNMAPPABLE and stops the criterion. The measurement went the other
way, so the prediction is gone and the number is here. On a local 8B model the
grounding probe scores 14 of 21 against 20 of 21 on the model used for the results.
All seven errors are over-acceptance and none is a refusal. The capable model's
single error has the same shape: both map "type 1 diabetes mellitus", which this
site's vocabulary cannot express, onto the type 2 code.
[docs/WEAK_MODEL.md](docs/WEAK_MODEL.md) has the per-concept table.

Two details make that worse rather than better. Nothing was invented: the grounder
drops any code that is not on the candidate list the vocabulary returned, and that
filter did not fire once in the weak run. Every wrong answer was a real code from
this site's own vocabulary that means something adjacent. And the UNMAPPABLE path,
which exists so a concept the site cannot express stops the criterion instead of
clearing everyone, is the path these errors walk around.

What is left holding this is the checkpoint rather than the model. `explain.py`
resolves every code to the display name the site's own records use, so a predicate
for "type 1 diabetes mellitus" shows the type 2 display to the reviewer who has to
sign it. That is a property of the artifact. It is not a measurement that a reviewer
catches it.

**The registry text is not the protocol.** ClinicalTrials.gov's eligibility field is
the sponsor's summary. A site screens against a document with more structure and
more specificity than this.

**Synthea is not a hospital.** Its absences mean a generator module did not fire.
Its terminology is a fraction of a real site's, its patients have no outside
records, and its diabetes cohort is coded with a single unspecified code.

## Prior art

Criteria2Query, TrialGPT, RECTIFIER, and the CHIP 2025 shared task all attack
criteria-to-structured-query. HL7 CQL is the standards-track answer to executable
clinical logic. What is different here is not the compilation step, which is well
trodden, but that the executable form carries an explicit third truth value and an
explicit per-query decision about what absence means, and that the evaluation is
scored on a joint (coverage, silent error) pair so that abstaining everywhere cannot
win.

## Hot take

Most agent evaluations report accuracy on the cases where the agent answered, and
the cases it should not have answered at all do not appear anywhere in the number.
That is backwards for anything that acts on people. The question that matters is not
how often a system is right, it is how often it is confidently wrong in a way nobody
can see. Until an agent can say "the record does not say" as a first-class output,
and be scored on it, its accuracy figure is a measure of its willingness to guess.

This project can put a number on that rather than only assert it, and the number
came out against the design. In the grounding probe, a local 8B model answered 21
concepts and got 7 wrong. Every one of the 7 was an over-acceptance: a real code
from the site's own vocabulary that means something adjacent to the concept asked
for. Not one was a refusal. The stronger model got 6 of those 7 right and made the
same mistake on the seventh. An accuracy score of 14 of 21 and 20 of 21 makes those
two failures look like the same kind of thing at different rates. They are not: the
errors are entirely on the side that costs a patient and entirely absent from the
side that costs coverage, and that asymmetry is invisible in any single figure.
[docs/WEAK_MODEL.md](docs/WEAK_MODEL.md) reports both columns for that reason, and
the headline results report coverage and silent error as a pair for the same one.

## Safety, scope and data

- Public and synthetic data only. Synthea (Apache-2.0, sha256 pinned) and
  ClinicalTrials.gov API v2 (US Government, public domain).
- No credential appears in this repository. The local model shim copies an auth
  token to a temporary directory outside the tree and deletes it at exit.
- No consequential action is taken. The system produces a document. It enrols
  nobody, contacts nobody, and writes to no clinical system.
- The sign-off gate is a human action and it is left to a human. Whether it has been
  cleared in this checkout is a fact in the repository rather than a claim in this
  file: `python scripts/signoff.py --run runs/tierA --list` prints it, and
  `runs/tierA/signoffs.jsonl` is where it lives. Any signature here is the author's,
  who is not a clinician, and the `reviewer_role` field records that rather than
  leaving it to be assumed. A deployment puts a qualified clinical reviewer in
  exactly that slot.
- Until the gate is cleared, `scripts/worklist.py` refuses with exit code 3, and
  that refusal is the demonstration. There is an `--allow-unsigned` flag for showing
  the document anyway, and using it stamps **NOT FOR USE** across every page.
