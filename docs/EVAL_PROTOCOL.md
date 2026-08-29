# Evaluation protocol (pre-registered)

**Status: registered before any scored run.** The git commit that adds this file precedes
every commit that produces a scored result. That ordering is the point: it is checkable by
anyone with `git log`, and it is what stops the metric being chosen after the numbers are
known.

Anything this document does not authorise is exploratory and is labelled as such in the
report.

---

## Amendments

**Registering a protocol is worth nothing if the protocol is quietly edited to match
what happened.** So the body below is left as it was written, and every place the
build departed from it is recorded here instead, with the reason. A reader comparing
this document to the repository will find these five differences and no others; if
they find a sixth, this list is the thing that is wrong.

**A1, 2026-08-29. Blindness is no longer a git fact, and the claim it replaces was
weaker.** Section 6 says Checker B's labels are committed before any commit
containing system output, so the ordering is checkable with `git log`. That was true
when it was written and stopped being true: B and the scored compile ended up running
concurrently on one machine, so commit order now records which process finished first
and nothing else. The replacement is stronger rather than weaker. Blindness is not
about when a file was written, it is about what was in the prompt, and every one of
B's calls is recorded in full. `python scripts/verify.py blind` searches every
recorded B request for the predicate IR vocabulary, the predicate digests, and
distinctive source lines from the gold answer file, and refuses to report a pass if
any of those search sets comes back empty. Read that check, not section 6.

**A2, 2026-08-29. Three trials are segmented and scored, not eight.** Section 2 says
8 trials and "all criteria are segmented". Five of the eight were moved to a
development split, recorded in `docs/DEV_SPLIT.md` and committed before the first
prompt edit, so that prompts could be iterated against something without touching the
held-out set. Those five have no gold labels and never will. The held-out set is
three trials and 40 criteria. The change makes the evaluation smaller and the
held-out claim stronger, and it is the reason the coverage figure rests on 40
criteria rather than a larger number.

**A3, 2026-08-29. There is no hand-authored adversarial patient set, so there is no
adversarial stratum.** Sections 2 and 5 register one, and the bootstrap is described
as stratified by corpus across Synthea, adversarial and degraded. It was not built.
The bootstrap resamples unique criteria and patients over the Synthea panel only, and
`evaluation/score.py` does what is reported rather than what was registered. This is
a capability that was registered and not delivered, which is a smaller claim than the
protocol makes, and saying so is cheaper than the alternative.

**A4, 2026-08-29. Checker B labels are not human-adjudicated.** Section 6 says every
B label is human-adjudicated with a rationale logged per case. No human adjudicated
anything. `evaluation/checker_b.py` states the design plainly in its own docstring:
where A and B disagree, the disagreement is published as the label noise floor rather
than resolved. Adjudication would need a clinician, this project has none, and an
adjudication performed by the author would be one more model-shaped opinion wearing a
label it had not earned. The disagreement rate is reported as what it is.

**A5, 2026-08-29. B1 was added after registration and is labelled exploratory.** The
arm table below lists B0, B2, B3 and TS. A fourth baseline, B1 (demographics only),
was added because B0 turned out to be too weak to be informative: it fails everyone,
so beating it says almost nothing. B1 answers only the criteria that age and sex can
settle and abstains on the rest, which is the cheapest defensible system somebody
could actually build. It is not part of the registered primary comparison and
`results/RESULTS.md` reports it beside the registered arms rather than in place of
them. B3 was not run.

---

## 1. What is being claimed

A clinical research coordinator has a panel of candidate patients and a protocol. The
claim is that TrialSieve removes a large share of that panel from consideration **without
making a single false exclusion**, and that each removal is traceable to a dated resource
in the record.

The claim is not that it screens patients better than a clinician, and not that it decides
anything. Every surviving patient still goes to a human, and every indeterminate carries
the question a human has to answer.

## 2. Units, arms, and cases

**Cell:** one (patient, criterion) pair. **Screen:** one (patient, trial) pair.

**Arms.**

| id | Arm | Description |
|---|---|---|
| B0 | always-FAILS | Degenerate control. Establishes what the label marginals alone buy. |
| B2 | per-cell prompt | One model call per cell. Receives the **same flattened facts** the engine reads, the criterion prose verbatim, an explicit instruction plus one worked example for returning INDETERMINATE, JSON out, temperature 0. |
| B3 | B2 self-consistent | B2 sampled 3x at temperature 0.7, majority vote, any disagreement to INDETERMINATE. |
| TS | TrialSieve | Compile once per criterion, execute deterministically per patient. |

B2 is the arm that matters. A baseline that has to read two megabytes of raw FHIR would
lose on context handling rather than on reasoning, and the gap would be a preprocessing
artifact. B2 is given the engine's own flattened view so the comparison is about the
verdict, not about plumbing.

**Cases.** 8 trials from ClinicalTrials.gov. All criteria are segmented; the
record-checkable classification is **committed before any compilation runs**, and the
headline is reported in the form "k of n criteria". Patients: a fixed panel drawn from
the 385 alive adults in the Synthea sample by a seeded, documented rule, plus a
hand-authored adversarial set placed on boundaries.

## 3. Metrics

Per cell, gold `g` in {MEETS, FAILS, INDET, UNMEASURABLE} and system `s` in
{MEETS, FAILS, INDET, ERROR}. UNMEASURABLE cells are dropped from every denominator,
carry a reason code, and are reported with a best-case / worst-case imputation
sensitivity so the reader can see what dropping them could have bought.

```
N        = scoreable cells
C        = { cells : s in {MEETS, FAILS} }          # cells where the system committed
coverage = |C| / N

silent_error(cell) = cell in C and [ (g in {MEETS,FAILS} and s != g) or g == INDET ]
SER      = |{ cells : silent_error }| / N
```

The `g == INDET` disjunct is the absence-of-evidence error, and it counts. A system that
commits to an answer the record cannot support is wrong even when it guesses correctly,
because the coordinator cannot tell the difference.

**SER is never reported alone.** The unit of result is the ordered pair
**(coverage, SER)**, and a comparison is admissible only against an arm at equal or lower
coverage. This appears in every table, every README line and every video frame.

**Directional split.** SER decomposes into `false_FAILS` (system rules out a patient who
should not be ruled out), `false_MEETS`, and `overcommit` (`g == INDET`). These are not
interchangeable. A false FAILS is the invisible harm: that patient is never looked at
again, and nobody discovers the error.

**Primary outcome.**

```
panel_reduction_at_zero_false_exclusion =
    (screens ruled INELIGIBLE) / (total screens)     if false_FAILS_screens == 0
    else VOID, reported with the false-exclusion count
```

Abstaining everywhere scores 0. Guessing voids the result. This is the number a
coordinator would actually act on.

**Co-primary.** `resolved_correct_per_screen`, so an arm cannot win by abstaining.

**Also reported.** The 3x3 confusion matrix per arm; `unnecessary_abstention_rate`, being
INDET cells where a forced answer would have been right; SER at matched coverage of 50%,
70% and 90% via an abstention sweep; model calls, wall time and dollars per additional
patient; and determinism as byte-identical output across two runs.

## 4. Noise floor, registered before the effect

The execution engine is deterministic and would report a floor of exactly 0.0, which would
be a meaningless number dressed as rigour. The randomness in this system lives in
compilation, so that is where the floor is measured.

**Every criterion is recompiled under at least 3 seeds**, the whole downstream evaluation
is rerun per seed, and the spread of the primary metric across seeds is published as the
floor. An effect smaller than that spread is reported as not detected.

Byte-identical cassette replay is a separate determinism claim and is not the noise floor.

## 5. Intervals

Criteria are deduplicated by content hash before anything is counted, because one
predicate serving many patients produces near-perfectly correlated errors and a cell-level
bootstrap would publish intervals several times too narrow. **Effective N is the number of
unique criteria, and is reported as such next to any cell count.**

Two-way (pigeonhole) bootstrap: draw unique criteria with replacement and patients with
replacement, form the induced cells, B = 10,000, stratified by corpus (Synthea /
adversarial / degraded). **Bootstrap the paired difference** on the same cells across
arms. Two confidence intervals are never compared by whether they overlap.

## 6. Gold labels

Gold is authored by two independent routes and adjudicated.

- **Checker A:** hand-authored gold predicates.
- **Checker B:** works from criterion prose and the flattened patient table only, with no
  access to the IR, to Checker A, or to any system output. Where a second human is not
  available, B is run through a **different model family** via the `make live` shim, and
  every B label is human-adjudicated.
- **Blindness is a git fact.** Checker B labels are committed in a commit that precedes
  any commit containing system output.
- **Adjudication** is done with arm identity stripped and case order shuffled, and a
  rationale is logged per adjudicated case.

Reported: raw percent agreement, Cohen's kappa, Gwet's AC1, and the label marginals.
Kappa alone collapses under the FAILS-heavy marginals expected here. Pre-adjudication
disagreement is published as the **label noise floor**, and any difference below it is
stated to be uninterpretable.

## 7. Engine gate

A defect in the shared execution engine would cancel between arms and score as agreement,
which would make the metric blind to exactly the failure modes this project claims to fix.
So the engine is tested separately, and the gate must pass before any scored run:

about 30 semantic tests covering both boundaries of every date window, both directions of
every unit conversion, a parent criterion satisfied by a child code, a missing resource
yielding INDETERMINATE rather than FALSE, null distinguished from zero, and K3 truth
tables including `UNKNOWN and FALSE == FALSE`.

The flattener used by Checker B does not import the engine.

## 8. Contamination

ClinicalTrials.gov text and Synthea are both plausibly in pretraining data.

1. NCT ids, trial titles and sponsor names are stripped from every prompt.
2. **Counterfactual threshold control.** Constants are perturbed on about 15 criteria
   (6 months becomes 11 months, `>= 60` becomes `>= 45`), gold is derived mechanically
   from the perturbation, and the rate at which each arm answers using the *original*
   threshold is measured. A non-zero rate is memorisation, quantified.

## 9. Degradation harness

Synthea records are complete by construction, so the absence-of-evidence failure mode
barely occurs naturally and any SER measured on raw Synthea is a lower bound. Real
missingness is not random: it tracks fragmented care and sicker patients, which is
precisely the correlation this harness cannot reproduce, and that limitation is stated in
the report rather than buried.

At k in {0, 10, 20, 40%}, applied to criterion-relevant resources: drop the observation,
flip the stored unit to a plausible alternative, strip the date that a window depends on,
or downgrade a coded condition to text only. Gold under degradation is derived by rule,
not re-annotated. Results are a curve over k. Every arm sees identical degraded charts,
selected by a seeded permutation committed with the protocol.

## 10. Predictions, registered before measuring

Stated now so that being wrong is visible.

1. **Coverage will land at 30-40%** of segmented criteria, following Köpcke et al.
   (15 trials, 351 criteria, 5 tertiary centres: 55% expressible x 64% present = 35%
   completeness). A number far above this would suggest the criteria were cherry-picked.
2. **B2 will be close to TS on plain numeric criteria** and will separate on unit traps,
   temporal windows, and degraded records.
3. **B2's headline weakness will be overcommitment**, not accuracy: it will answer cells
   where gold is INDET rather than get committed cells wrong.
4. **At k = 0 the gap will be small.** The design is built for missingness, and the corpus
   has almost none. If the gap at k = 0 is large, that is a suspicious result and will be
   investigated before it is reported.
5. TS panel reduction will be lower than B2's apparent reduction, and B2's will void on
   false exclusions.

## 11. Decision rule, fixed in advance

If B2 or B3 matches TS on (coverage, SER) within the noise floor, the headline claim
changes to amortised cost, determinism and review-per-criterion, with a stated crossover
panel size, and the accuracy claim is dropped. This is written down now so that the choice
cannot be made after seeing the numbers.

## 12. What would falsify the thesis

- TS shows no advantage over B2 at matched coverage under degradation.
- The false-exclusion count is non-zero, which voids the primary outcome outright.
- Coverage is so low that the panel reduction is trivially small.

Each of these is reported if it happens.
