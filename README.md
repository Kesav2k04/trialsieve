# TrialSieve

**The model reads the protocol once. It never reads a patient.**

**Reviewing this? Here is each deliverable and the one file that answers it.**

| | |
|---|---|
| Solution code | [`src/trialsieve/`](src/trialsieve/), six agents. Runs offline, no dependencies. |
| Agent instructions, verbatim | [`src/trialsieve/agents/`](src/trialsieve/agents/) as constants, and the first event of every trajectory. Mapped in [docs/AGENT_DESIGN.md](docs/AGENT_DESIGN.md). |
| Improvement changelog | [docs/IMPROVEMENT_CHANGELOG.md](docs/IMPROVEMENT_CHANGELOG.md), 56 entries. Its opening table is the whole arc. |
| Baseline comparison | [docs/SCORECARD.md](docs/SCORECARD.md), one page, four columns. |
| Reproduction guide | [REPRODUCE.md](REPRODUCE.md). One command from a clean clone, 174.5s measured, no key, no network. |
| The video | submitted as a link on the entry form, 4:54. It is not a file in this repository: it is one of the four deliverables rather than part of the solution, and nothing here needs it to run. |
| Agent trajectories | [runs/tierA/trajectories/index.md](runs/tierA/trajectories/index.md), every model call. Five named exemplars first, then the rest with the failures at the top. The four other arms are indexed the same way beside it. |
| Everything else, and the ground rules | [SUBMISSION.md](SUBMISSION.md), including what existed before this started. |

The main failure mode is in [How it fails](#how-it-fails) and the hot take is the
last section. Both are at the bottom because they are the end of the argument, not
because they are buried.

---

## Who this is for, and what it is

**The user is the clinical research coordinator at a trial site.** They are handed a
protocol and a panel of candidate patients, and they decide who is worth screening
in person. Nobody else in the process reads every criterion against every chart, and
nobody re-reads the people they rule out.

A prescreening system that turns a panel of several hundred patients into a ranked
worklist: the people who are provably ineligible are removed with a dated citation
each, and everyone else is ordered by how few questions remain.

The bottleneck it targets is not the individual chart. A coordinator reading one
chart against one criterion is not the slow step, and this project has no
measurement of how long that takes, so it does not put a number on it. The slow
step is that the list is longer than the reading capacity, so candidates get worked
in whatever order the list arrives in.

That last sentence is this project's premise rather than one of its findings, and
it is not measured here. No coordinator was observed and none was timed. It is
measured elsewhere: Ni et al., *Automated clinical trial eligibility prescreening*,
JAMIA 22(1):166-178, 2015 ([PMC4433376](https://europepmc.org/articles/PMC4433376),
doi:10.1136/amiajnl-2014-002887), ran automated prescreening against a
physician-generated gold standard across 13 trials and 202,795 emergency-department
patients and reports "the workload with automated ES was reduced by 92% on the gold
standard set". That is a different quantity from anything in this repository, on a
different population, and it is cited for the premise rather than as a comparison:
it establishes that screening workload is a real and published bottleneck, not that
92% is a bar this project clears. What is
measured is the consequence a system can be held to: how many of the 15,400 cells
a person is left holding, and how many of the answers they are handed are wrong in
a way they cannot see. If the premise is wrong, the numbers in this repository are
still what they say they are; they would simply matter less.

What can be measured here is the shrink. The panel is 385 Synthea patients and the
held-out protocol is 40 criteria, giving 15,400 patient-criterion cells.
`results/RESULTS.md` reports what fraction of that grid the system settles and how
many of the settled cells it gets wrong. Both numbers come from
`scripts/report.py`, and the second one is the one that decides whether the first
is worth anything.

**And what is left is shaped like questions, not like patients.** On the published
worklist (one trial, the zero-false-exclusion operating point) the engine settles
187 of 385 screens and clears 8 to contact. The 190 that remain open contain **two
distinct questions**, and 188 of them are open on the same one: no HbA1c on file.
So a coordinator has one thing to go and find rather than 190 charts to read.
Getting it still returns 188 separate values, one per patient. What collapses is
the search, not the answers, and that is the honest version of the claim: 1,155
readings become 2 things to go and get. It follows from compiling once instead of asking
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

---

## What it costs, and what that number is not an argument about

| 385 patients, 40 criteria, 15,400 judgements | today | TrialSieve |
|---|---|---|
| model spend per screening pass, at published rates | $22.19, asking per cell | **$0.13**, paid once per protocol |
| the same panel rescreened next month | $22.19 again | **$0.00**, the predicates are already compiled |
| wall clock for the pass | a nurse reading charts | under 5 seconds, zero model calls |
| what a coordinator is handed *(one trial, the 3 criteria the zero-false-exclusion operating point applies, so 1,155 of those judgements)* | 1,155 chart readings | 190 screens carrying 2 open questions, [grouped](docs/sample_worklist.md) |

Each row names the set it is counted over, because they are not the same set: the
cost rows are the whole 15,400-cell panel and the last row is one trial at one
operating point. Every money figure is read back out of
[docs/COST.md](docs/COST.md) by `tests/test_readme_cost_claims.py`, which is the
rule the rest of this repository runs on. A number that appears twice disagrees
with itself eventually, so the second copy is checked against the first. The two
costs cross at 2.2 patients, and past that the gap grows with every patient and
every rescreen, because one side of it is flat.

**The larger cost is not in that table, and it is a person.** Before this produces
any document, somebody qualified reads all 19 compiled predicates and signs them.
No clinician was timed here, so this repository does not put a rate on it. What it
can do is give you the quantity, measured rather than guessed: **19 predicates,
1,478 words in total** across their source text, expression, unit note and absence
note. Median 60 words each, longest 262. Price that at your own reviewer's rate.

Against the per-cell baseline that is the whole argument, because the baseline has
no reviewable artifact at all. To get the same assurance you would read 15,400
individual answers, and read them again next month. What compiling buys is not a
smaller bill. It is a review surface small enough that reviewing it is possible.

**And the cost table above is not the argument against the tool a site already
owns.** i2b2, ATLAS, TriNetX and the EHR query builders cost nothing more to run,
so on price they win and this table is beside the point. The case against them is
in [Prior art](#prior-art) and it is not about money: a filter cannot tell you who
it could not decide, and the patients it silently drops are the ones this project
exists to count. If price is what decides, buy neither; the incumbent is free.

---

## What a per-cell model does with a missing lab

The criterion is from a real registered trial:

> Urine albumin-to-creatinine ratio below 30 mg/mmol.

In this panel, 359 of 385 patients have no UACR result at all, so a record with
nothing to compare against is the normal case rather than an unlucky one.

Ask a capable model directly, one cell at a time, giving it the criterion and the
patient's chart. Over all 400 cells of that arm it **commits to a verdict on 272
of them**, 68%, including cells where the record is silent. Nothing in the chart
contradicts the threshold, so the threshold appears satisfied. The reasoning is
fluent and the answer is confident, and on those same 400 cells it is wrong on
43.75% of every cell against TrialSieve's 1.00%. Counted only over the cells each
one answers, that is 175 of 272 for the baseline and 4 of 87 here.

**Read that pair with its sample size.** Those 400 cells are **10 patients**
against 40 criteria, not 400 people. Ten is what the arm costs: $22.19 for a full
pass, which is the number the cost section is about. The 15,400-cell grid the rest
of this repository is scored on runs no per-cell model arm at all, so the 43.8%
figure does not appear there and nothing in this README claims it does. The
degenerate controls `B0` and `B1` do run on the full grid, and they are weaker
comparisons than B2, which is said here rather than left to be noticed.

TrialSieve answers:

```
INDETERMINATE
  no observation with code 14959-1 in the record
```

The difference is not accuracy on a hard case. It is that one of these systems
abstains as a rule and the other abstains as an exception: the baseline is told
to answer INDETERMINATE and shown how, and still commits on two thirds of its
cells. A coordinator reading the
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
  An earlier version of this file said absence never rules anyone out. The code says otherwise (`src/trialsieve/evaluator.py:233`) and so did the first
published run: one criterion compiled with `absent_means: "false"` produced 358
of the 424 wrong FAILS in the whole evaluation. The control that was supposed to catch it
  is the human reading the predicate in English before any worklist exists, and
  on that run it was not caught.
- **One case is no longer the model's to decide.** A query with an empty `codes`
  list is asking about a concept this site has no code for, so the record could
  never have stored it and its silence carries no information. The compiler now
  forces `absent_means` to `unknown` there and records the change on the
  trajectory as a `normalisation`. Silent errors fell from 469 to **111** and
  patients wrongly ruled out from 182 to **18**, at a cost of 5 points of
  coverage. Entry 30 of the changelog puts the gain and the cost in the same table, before
and after, and [docs/SCORECARD.md](docs/SCORECARD.md) puts the coverage cost
next to the baseline's.
- **Every other closed-world decision is still the model's, and the sensitivity
  arm is how you check it.** `--absent-means-override unknown` discards all of
  them at once. It used to remove 358 silent errors, taking 469 down to 111. It
  now removes **zero**: both arms report 111, so what is left has nothing to do
  with absence. The targeted repair reached the same error floor as the blanket
  override while answering more cells, 19.15% against 18.44%. A gap re-opening
  there means a new closed-world assertion started committing.

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

That is what the design promises, and the run this repository published first
broke it twice. The project found out by checking rather than by claiming. The
compiler's emit validator accepted any code the grounder returned, from either
slot, because it was written to catch invented codes and does that correctly. It
could not see a real code put in the wrong slot. Two criteria out of the eight
with broader-only grounding promoted SNOMED 44054006 into `codes`, and both also
carried `absent_means: false`, so presence settled them as MEETS and absence as
FAILS, and neither could return INDETERMINATE. One of the two was the criterion behind the 358 wrong exclusions above.

The validator is now slot-aware and the schema accepts the shape the design asks
for, which it had been rejecting. `python scripts/grounding_audit.py --run
runs/tierA` exits 0 and reports 9 criteria grounding a broader-only code with
**0** used as an exact code. `tests/test_grounding_audit.py` holds that at zero
and requires the audit to have scanned a non-empty set, so a clean result cannot
come from reading nothing. Entries 25, 27 and 29 of the improvement changelog
have the mechanism, the repair, and the intermediate state where fixing it made
every headline number worse.

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
ranks the rest by how little is left to check, and for each patient it cannot settle
it names the record entry it could not find, under the criterion that entry blocks:
`no observation with code 4548-4 in the record`, against `HbA1c 6.5-10%`. That is a
statement about the chart, not a question addressed to anyone, and calling it a
question would be the overclaim this repository keeps catching itself in. It ends by saying what it did **not** settle: this
trial has 15 criteria, the document answers 3, and the other 12 are still the
coordinator's on every patient it hands back, with the six the compiler refused
listed and its reason beside each one.

Three files, same run, same provenance header:
[docs/sample_worklist.md](docs/sample_worklist.md) to read,
[docs/sample_worklist.json](docs/sample_worklist.json) with the evidence behind
every decision rather than the first 25, and
[docs/sample_worklist.csv](docs/sample_worklist.csv), 1,155 rows of one patient per
criterion, which is the form a screening log or a CTMS takes.

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

- **The comparison against the baseline**, four columns and one page:
  [docs/SCORECARD.md](docs/SCORECARD.md). Start here. Every number in it is read
  out of `results/results.json`.
- **The Improvement Changelog**, 56 entries, each naming the evidence that found
  it and what moved afterwards:
  [docs/IMPROVEMENT_CHANGELOG.md](docs/IMPROVEMENT_CHANGELOG.md). Its opening
  table is the whole arc in one screen, baseline to final.
- **The agent instructions**, verbatim: the prompt constants live beside the code
  in [src/trialsieve/agents/](src/trialsieve/agents/), tagged with the
  `PROMPT_VERSION` each run recorded, and the same text appears as the first
  `instructions` event of every file under
  [runs/tierA/trajectories/](runs/tierA/trajectories/index.md).
- Every model call, sorted failures first:
  [runs/tierA/trajectories/index.md](runs/tierA/trajectories/index.md)
- The full generated report, 667 lines:
  [results/RESULTS.md](results/RESULTS.md), generated by `scripts/report.py`
- [docs/CONTAMINATION.md](docs/CONTAMINATION.md), generated by `scripts/contamination.py`

### Did the model read these trials, or remember them?

Three registered trials with public identifiers is exactly the setup where a
result can be produced by recall. A model that saw NCT06983054 in training can
emit its thresholds without the criterion in front of it, and every number would
still be right, and the evaluation would be measuring memorisation.

Three checks, and the third is the one worth arguing with. A threshold is changed
to a value the real protocol never contained, the criterion is recompiled, and the
predicate has to carry the new number. **15 criteria carried a perturbable
number. Six recompiled, and 6 of 6 carry the perturbed value with none carrying
the original.** Two refused, for concepts absent from the structured record at
all, menstrual history and dietary sodium intake, which is the same refusal they
give unperturbed. The remaining seven could not be run: their counterfactual
compile was never recorded, and replay refuses to make a live call rather than
quietly paying for one, so `results/contamination.json` marks them `error` with
the missing cassette key. Seven of fifteen unrun is the honest size of this
check, and it is a smaller check than the number 6 of 6 suggests on its own.

The first two checks are cheaper and run without a model: no prompt template has a
slot for a trial identifier or title, and no recorded request contains one. That
scan subtracts every word sequence the system is legitimately given, because
"chronic kidney disease" is in one of these titles and in half the criteria, and a
check that fires on the disease name can only ever return positive.

## Prior art

Criteria2Query, TrialGPT, RECTIFIER, and the CHIP 2025 shared task all attack
criteria-to-structured-query. HL7 CQL is the standards-track answer to executable
clinical logic, and it already has three-valued null semantics, so a third truth
value is not the novelty here and this file should not have implied it was.

**The thing to compare against is not a paper, it is the cohort tool the site
already owns.** i2b2, OMOP with ATLAS, TriNetX, and the query builders inside the
major EHRs all filter a population on structured fields, they are already connected
to real data inside an approved pathway, and they cost nothing more to run. On the
criteria this system actually compiles, mostly lab values and demographics, they do
the same job. Any honest reading has to start there.

What a filter cannot do is tell you who it could not decide. A patient with no
HbA1c on file does not match `HbA1c between 6.5 and 10`, so they leave the panel
without appearing anywhere, and nobody re-reads them. That is the same silent
exclusion this project spends its evaluation measuring, except it happens by
default rather than by decision.

The measured prior result is Ni et al. above: 92% workload reduction against a
physician gold standard, with mean average precision 62.9%. It is the number this
work should be read next to and it is not the number this work reports, because the
two are not the same quantity. That paper reduces the pool a person must screen and
is scored on how well the retained pool matches a physician's picks. This one
removes patients outright with a citation and is scored on how many of those
removals a label says were wrong: 46.15% panel reduction with 18 false exclusions,
registered as VOID, and 43.5% with none on the nine criteria that never produce
one. A reduction figure and a reduction-with-a-zero-false-exclusion-constraint
figure are not interchangeable, and quoting one against the other would be the
comparison this repository spends its evaluation section refusing to make.

So the difference is not the compilation step, which is well trodden. It is three
things. Absence is a per-query decision that a human signs, rather than a property
of the query language nobody was asked about. The patients the record cannot settle
come back as a grouped question, 188 of 190 open screens waiting on the same
missing lab, rather than as an absence from a result set. And the evaluation is
scored on a joint (coverage, silent error) pair, so abstaining everywhere cannot
win and neither can answering everything.

## Safety, scope and data

- Public and synthetic data only. Synthea (Apache-2.0, sha256 pinned) and
  ClinicalTrials.gov API v2 (US Government, public domain).
- No credential appears in this repository. The local model shim copies an auth
  token to a temporary directory outside the tree and deletes it at exit.
- No consequential action is taken. The system produces a document. It enrols
  nobody, contacts nobody, and writes to no clinical system.
- The sign-off gate is a human action and it is left to a human. Whether it has been
  cleared in this checkout is a fact in the repository rather than a claim in this
  file: `python scripts/signoff.py --run runs/tierA --list` prints it. It reads
  `runs/tierA/signoffs.jsonl`, which does not exist in this checkout, and that
  absence is the answer rather than an oversight. Any signature here is the author's,
  who is not a clinician, and the `reviewer_role` field records that rather than
  leaving it to be assumed. A deployment puts a qualified clinical reviewer in
  exactly that slot.
- Until the gate is cleared, `scripts/worklist.py` refuses with exit code 3, and
  that refusal is the demonstration. There is an `--allow-unsigned` flag for showing
  the document anyway, and using it stamps **NOT FOR USE** across every page.

### What running this on real patients would take, none of which is done here

Nothing below has been attempted. It is listed because a system that prescreens
patients is not a system whose deployment cost can be left implied, and because
every item is a reason the numbers above would not transfer unchanged.

| | |
|---|---|
| Data access | Synthea records are flat, complete and already normalised. Real charts are none of those. This reads one denormalised table; a site would need a FHIR or OMOP extract, and the coverage figure of 21.75% is measured on records that are complete by construction, so it is an upper bound rather than an estimate. |
| Local vocabulary | The grounder resolves concepts against **this** corpus's codes and refuses when it cannot. A site's codes are its own, including local non-standard ones, so the grounding step is per-deployment work, and 19 of the 40 criteria put to the compiler producing predicates is a number about this vocabulary rather than about the method. |
| Human review | Somebody qualified has to read all 19 compiled predicates before any document is produced. That is the sign-off gate, and it is the real unit cost. It is named beside the cost table at the top of this file, and it is not priced. |
| Regulatory posture | Prescreening from records generally runs under an IRB-approved protocol with a partial waiver of authorization, and none of that has been sought here. This project has no IRB, no data-use agreement, no validation package, and it makes no claim about 21 CFR Part 11, HIPAA or GCP. It produces a document a human acts on, which is the lightest posture available, and it is still a posture somebody has to establish. |
| Identity linkage | The worklist names patients by their Synthea UUID. A UUID is not somebody a coordinator can phone. Turning a row into a call means joining it to the site's own record number and then to a name, a chart and a treating clinician, and none of that is here: the CSV reserves an empty `site_mrn` column and nothing fills it. It is one join and it is also the step that turns a research artifact into something touching a person, so it carries the access review, the audit trail and the minimum-necessary argument that the rest of this table describes. |
| Record recency | Each patient is screened as of their own last encounter, and in this panel those run from 2019-02-23 to 2021-11-18. Two of the three criteria on the sample worklist carry no recency window, so a patient can clear them on a years-old lab. The worklist header says so. A real deployment either sets a window per criterion or accepts that the coordinator confirms currency at the call. |
| Liability | Nobody is enrolled or excluded by this document; the exclusions are recommendations with a dated citation each. The false-exclusion count is the number that matters and it is published rather than argued away: 18 patients at the operating point, 0 tolerated by the gate the curve is fitted to. |

### The corpus is one disease area

The three held-out trials are all type 2 diabetes and diabetic kidney disease,
against one synthetic vocabulary and 385 patients. The criteria that compile are
mostly lab values and demographics, which is the easiest shape this problem has.
A cardiology or oncology protocol leans on imaging, staging and performance status,
and there is no evidence here about any of them. Read every number in this
repository as a measurement of this corpus, not of the method.

## How it fails

The honest list, before anyone else writes it.

**Coverage is the binding constraint, not accuracy.** Most criteria in a real
protocol cannot be settled from a structured record at all. Köpcke et al., across
15 trials, 351 criteria and 5 tertiary centres, put it at 55% expressible times
64% present, so about 35% answerable. A system that answers a third of the
questions and abstains on the rest is only useful because the third it answers
removes people from the list. That figure is also a registered prediction here: `docs/EVAL_PROTOCOL.md` says
coverage should land at 30 to 40% and that a number far above it would suggest
the criteria were cherry-picked. **This run missed that band on the low side.**
19 of 65 segmented criteria compile, which is 29.2%, and the repair in changelog
entry 30 is most of why: it trades answered cells for abstentions on purpose.
The prediction was registered before the run and the run did not meet it, which
is recorded here rather than in a footnote.

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
