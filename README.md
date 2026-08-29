# TrialSieve

**The model reads the protocol once. It never reads a patient.**

Clinical trial prescreening, built so that a patient can never be ruled out by a
fact that is missing from their record.

---

## Start here: one patient, one criterion

The criterion is from a real registered trial:

> Urine albumin-to-creatinine ratio below 30 mg/mmol.

The patient's record contains no UACR result at all.

Ask a capable model directly, giving it the criterion and the patient's chart, and
it answers **MEETS**. Nothing in the chart contradicts the threshold, so the
threshold appears satisfied. The reasoning is fluent and the answer is confident.

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

This example is generated, not written. `python scripts/counterexample.py` runs
both arms on that patient and writes the transcript to
[docs/COUNTEREXAMPLE.md](docs/COUNTEREXAMPLE.md), using the same baseline code
path the evaluation scores. If the baseline abstains, the script says so and this
section is wrong. In this panel, 359 of 385 patients have no UACR result at all,
so the case is the normal one rather than a chosen one.

---

## What this is

A prescreening system that turns a panel of several hundred patients into a ranked
worklist: the people who are provably ineligible are removed with a dated citation
each, and everyone else is ordered by how few questions remain.

The bottleneck it targets is not the individual chart. A coordinator is already
fast at one chart, roughly two minutes to check a few cheap disqualifiers and move
on. The problem is that a site with 400 candidates cannot look at 400 charts, so
candidates get worked in whatever order the list arrives in and enrolment stalls.

The job worth doing is to shrink the list **without a single false exclusion**.

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

**Compilation happens once per criterion. Execution happens once per patient and
calls no model at all.** Three things follow.

1. Every verdict is a predicate plus the dated resources it read. It is citable
   down to a FHIR resource id.
2. Adding a patient costs arithmetic. A bigger panel makes the economics better,
   not worse.
3. A human reviews the model's clinical judgement **once per criterion**, not once
   per patient per criterion. Sign-off scales with the protocol, which has about
   thirty criteria, not with the queue, which has four hundred people.

### The agents

| agent | job | model calls |
|---|---|---|
| `segmenter` | criteria blob to atomic, typed criteria | 1 per trial |
| `grounder` | clinical concept to codes in this site's vocabulary, or **UNMAPPABLE** | 1 per concept, cached across criteria |
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

- **FAILS requires positive evidence.** A ruleout names a dated resource. Absence
  never rules anyone out.
- **Absence is a modelled decision, not a default.** Every query into the record
  declares `absent_means` as `false` (this domain is trusted complete for these
  codes) or `unknown` (silence proves nothing). The reviewer sees the choice, and a
  single flag flips every query at once so the ablation can measure what it is
  worth.

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

Zero runtime dependencies: every import in `src/`, `evaluation/` and `scripts/` is
standard library. Full guide, including what each verification step rules out:
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

## How it fails

The honest list, before anyone else writes it.

**Coverage is the binding constraint, not accuracy.** Most criteria in a real
protocol cannot be settled from a structured record at all, and the published
estimate for expressible-and-present is around 35%. A system that answers a third
of the questions and abstains on the rest is only useful because the third it
answers removes people from the list.

**The compiler degrades by refusing, not by lying.** Run against a weak model, the
architecture loses coverage rather than gaining silent errors, which is the right
direction to fail in but is still a failure. The same run on a capable model and on
a local 8B is in the results.

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
