# Improvement changelog

Every entry is a defect that was in the code or the harness, how it surfaced, what
changed, and the command that shows it is fixed. Entries are kept in the order
they were found, including the ones that make the project look worse, because a
changelog with no embarrassing entries is a marketing document.

Four of these share a shape worth naming up front: **the system kept working and
reported a number.** A prompt that arrived empty, a comparison that skipped a unit
conversion, a count that answered zero for a patient with no records at all. None
of them raised an error. Each would have produced a plausible result with nothing
in the output to say it was wrong. That is the failure mode this project is about,
and it turns out to apply to the project itself.

## The journey, in the shape the brief suggests

The brief sketches a progression: baseline, then one row per meaningful
iteration, each with its evidence and what it decided. Forty-five entries is
more rows than that sketch has, so this is the spine. Every row links to the full
entry, and the entries themselves stay in the order they were found rather than
being rearranged into a story.

| stage | what I tried and why | evidence | decision and learning |
|---|---|---|---|
| **Baseline** | B2: one model call per patient per criterion, the brief's own first suggestion. It is the arm the pre-registered protocol names as the one that matters. | 43.75% of committed verdicts wrong, on the 400-cell paired sample. 145 wrong MEETS: patients it would have enrolled. | Per-cell judgement is not the bottleneck's shape. Compile the criterion once, execute it 15,400 times. |
| **Iteration 1** | Move the model upstream. Six agents compile a protocol into predicates; a deterministic engine runs them. Three truth values, so "the record does not say" is an answer rather than a guess. | Silent error rate 1.00% against the baseline's 43.75% on the same cells. Screening makes zero model calls. | Kept. Coverage falls to 21.75%, which is the trade and is reported beside it rather than under it. |
| **Iteration 2** | Add a critic that attacks each compiled predicate, then a second labeller who never sees the system's output. | The critic catches 15 of 15 planted defects in four classes and 3 of 4 in the fifth. `verify.py blind` reads independence out of the prompts. | Kept, with the weak class named: [entry 24](#24-the-probe-that-scored-9-of-9-had-never-tried-the-defect-that-mattered). A probe that scores 9 of 9 has usually not planted the defect that matters. |
| **Iteration 3** | Fix the instrument before believing the result. The noise floor, the coverage denominator, the operating point, three checks that could not fail. | The label disagreement floor moved 10.6% to 2.3%; coverage moved 37% to 29.2%, below the band the protocol registered in advance. | Kept. The run now misses its own prediction and says so. [Entries 12](#12-the-measuring-instrument-was-wrong-twice-and-both-errors-flattered-the-old-system), [15](#15-three-checks-that-could-not-fail-and-one-that-reported-a-pass-for-a-comparison-it-never-made), [19](#19-the-headline-operating-point-was-chosen-using-the-labels-it-was-scored-on), [23](#23-a-noise-floor-measured-on-the-hardest-cells-excused-the-losses), [28](#28-the-coverage-headline-was-the-answer-keys-number-not-the-systems). |
| **Iteration 4** | Repair the design's own sharp edge: one criterion was reading a silent chart as proof of absence. First attempt widened what the validator accepted. | It made every headline worse: silent error 3.05% to 6.97%, patients wrongly ruled out 182 to 318. | Kept anyway, and published. [Entry 29](#29-the-fix-that-made-every-headline-number-worse) recovered a criterion that turned out worse than the abstention it replaced. The number getting worse was the measurement starting to work. |
| **Iteration 5, the one that contributed most** | A query with no exact code for its concept may not read the record's silence as absence. | Patients wrongly ruled out 182 to **18**. Silent error 3.05% to **0.72%**. Cells answered 24.12% to 19.15%, in the same move. | Kept. [Entry 30](#30-closed-world-absence-on-a-concept-this-vocabulary-cannot-express) prints both columns of that trade in one table, because a coverage loss reported without the error it bought is not a result. |
| **Removed** | B3, a self-consistency baseline: sample each cell three times, take the majority. | Under replay all three samples are the same recorded call, so the vote is unanimous by construction and the arm measures the cassette store. | Removed before it was run, and left registered in `docs/EVAL_PROTOCOL.md` with the reason. [Entry 26](#26-the-experiment-i-registered-and-then-could-not-honestly-run). The gap reported here is against a single sample, not a self-consistent one. |
| **Final** | The arms above, run on the same cells with the same gold labels, plus the harness that keeps the claims honest. | Primary outcome **VOID**: 46.15% panel reduction with 18 false exclusions, against a registered rule that voids any result with more than zero. On the nine criteria that never produce one, 43.5% reduction with none. | The registered outcome is reported as VOID rather than replaced with the subset figure that passes. [The table below](#what-the-numbers-did-when-the-measurements-were-fixed) is what each measurement said before and after it was fixed. |

## What the numbers did when the measurements were fixed

Most of the entries below are defects in the system. A handful are defects in the
way the system was being *measured*, and those are the ones with two numbers: what
the repository reported before, and what it reports now. Both were measured on the
same data. Neither is an estimate.

| what was being measured | reported before | reports now | where to check |
|---|---|---|---|
| label disagreement floor for this panel | 10.6% | **2.3%** (95% CI 1.2 to 3.6) | `results/results.json`, `label_noise_floor` against `groups.k0_seed7.label_floor_poststratified` |
| published differences the floor calls uninterpretable, scored group | 2 of 6 | **2 of 6**, both `TS - B1` | the `vs label floor` column, `results/RESULTS.md`. This row claimed **0 of 6** and was wrong: `TS - B1` `ser` (+0.0072) and `false_fails` (+0.0043) are under 2.3% and were under 10.6%, so lowering the floor never moved them. The row now says what the column says, which is that the arm this system cannot separate itself from is the regular expressions |
| defect classes the critic probe ever planted | 3 of 5 | **5 of 5** | `by_class` in `results/critic_probe.json` |
| critic catch rate, absence defects | never planted, then 1 of 3 | **3 of 4** on the repaired predicates | same file |
| critic catch rate, every other class | 9 of 9 | **15 of 15** | same file |
| the B2 comparison, the arm the protocol calls the one that matters | run, never compared | **-0.4275 SER, CI [-0.5700, -0.2850]** | the `TS - B2` `ser` row of the `b2_10p` group, `results/RESULTS.md`. This row read `-0.4050 [-0.5550, -0.2550]` until 2026-08-30: the value from before entry 30, left in the *now* column of the table that tells a reader to check it. B2 SER 0.4375 minus TS SER 0.0100 is 0.4275 |
| criteria that did not compile | 22, as one number | **21 refusals and 0 lost to the validator** | "What did not compile, and why", `results/RESULTS.md` |
| coverage against the registered denominator | 37% | **29.2%**, below the registered 30 to 40% band | `criterion_coverage` in `results/results.json`; the numerator was the gold set's `checkable` count, not the compiler's output |
| broader-only codes used as exact codes | not checked, then 2 | **0** | `python scripts/grounding_audit.py --run runs/tierA` |
| patients wrongly ruled out, 385-patient panel | 182 | **18** | `groups.k0_seed7.panel_scores.TS.false_exclusions` |
| silent error rate per cell | 3.05% | **0.72%** | `groups.k0_seed7.cell_scores.TS.ser` |
| silent errors the open-world arm would still remove | 358 | **0** | `groups.ow` against `groups.k0_seed7`; the two now agree at 111 |
| third-party imports on the reproduction path | never checked | **0 of 54 modules, parsed** | `python scripts/lockfile.py --imports` |
| cards whose length was measured rather than guessed | 0 of 6 | **16 of 16** | `film/src/timings.json`, written from the rendered audio; entry 35 |
| eligible patients the worklist rendered | 0 of 8 | **8 of 8** | `docs/sample_worklist.md`, "Ready to contact" |
| silent error rate on seeds 8 and 9 | 3.18% and 3.18% | **0.73% and 0.73%** | `groups.k0_seed8` and `groups.k0_seed9` in `results/results.json`; the old figures came from cells computed before entry 30 |
| false exclusions at 40% record damage | 206 | **31** | `degradation_curve` in `results/results.json` |
| `python run.py reproduce` on a clean clone | fails, then DIFFERENT | **IDENTICAL** | clone into an empty directory and run it; entry 34 |
| tracked files carrying a home directory | 57 | **0** | `python -m pytest tests/test_no_private_paths.py`; entry 36 |

One row that is **not** in this table: on the six **absence** concepts,
`results/probe_weak_comparison.json` scores the weak model 1 of 6 against 5 of 6
for the frontier one. That sentence used to say "broader-only concepts ... against
6 of 6". Both were wrong: the class with six members is `absent`, the class named
`broader` has exactly one member (iron deficiency anaemia), and the frontier
model's score on the six is 5. It was a point about the broader-code path made
with numbers from the absence path. That
pair is a local 8B model against a frontier one on the same 21 concepts, so it
measures the model and not this repository's measurements, and putting it here
would have read as a fix that never happened.

Read the first column, not the third. Every "before" in this table was a number
this repository published, in a document that passed its own gates, with a test
suite green. The improvement is not that the numbers got better. Three of them got
worse: the label floor dropped, which turned two comparisons TrialSieve loses from
uninterpretable into measured losses; the critic's absence rate fell from an
implied 100% to 1 in 3; and coverage went from inside the band this project
registered in advance to below it. The improvement is that they became capable of being wrong.

---

## 1. A count answered `0` when the record was silent

**Found by** an adversarial review of the engine, before any scored run.

**What was wrong.** `Evaluator._count` returned `0.0` whenever the underlying
existence check came back UNKNOWN. So a criterion reading "fewer than 2
hospitalisations in the last year" was satisfied by a patient whose hospitalisation
history is simply not in the record. The open-world flag on the query was doing its
job one function up and being discarded one function down.

The same code path capped the evidence list at six entries (`ev[:6]`), which meant a
verdict could cite fewer records than it counted.

**What changed.** `_count` became a real function that returns UNKNOWN for an
open-world empty result and only commits a number when the query is closed-world.
The evidence truncation was removed.

**Evidence.** `tests/test_engine.py::test_count_on_open_world_absence_is_unknown_not_zero`.
The assertion checks the reason string too, because a silent UNKNOWN and an UNKNOWN
that explains itself are different products.

**What it would have cost.** Zero is the most dangerous number a missing record can
produce, because it is exactly the value that satisfies an exclusion criterion. This
one turns absence of evidence into evidence of eligibility.

---

## 2. Only one side of a comparison was unit-reconciled

**Found by** the same review, on a second pass, after the first fix was in.

**What was wrong.** `_compare` computed a target unit and then passed it to the
right operand only. `_unit_of` had no branch for a literal, so when the threshold
was written on the left (`30 mg/mmol <= UACR`) the target came from the right and
the left was left in whatever unit it happened to carry.

Urine albumin-to-creatinine ratio is stored in `mg/g` and written in trials in
`mg/mmol`. They differ by 8.84. A patient with a UACR of 150 mg/g, which is
16.97 mg/mmol, was compared as 30 against 150 and answered the wrong way. This is
the precise error `units.py` exists to prevent, arriving through the one path that
did not call it.

**What changed.** Both operands are now brought to one target unit before anything
is compared, `_unit_of` reads the unit off a literal, and the reason line carries
the unit so a reviewer sees `30 <= 16.97 mg/mmol` rather than two bare numbers, one
of which appears nowhere in the patient's record.

**Evidence.** Three tests, and they were mutation-checked: reverting the two lines
of the fix makes all three fail and the other 67 pass.

```
tests/test_engine.py::test_a_threshold_on_the_left_is_converted_like_one_on_the_right
tests/test_engine.py::test_a_comparison_means_the_same_thing_written_either_way_round
tests/test_engine.py::test_an_unconvertible_threshold_on_the_left_refuses
```

**What it would have cost.** The reviewer flagged that this alone would void the
primary outcome, and that is right: the primary outcome counts patients wrongly
ruled out, and an 8.84x error on a renal threshold produces exactly those.

---

## 3. Every prompt reached the model empty

**Found by** a two-criterion smoke test, run only to check the backend was wired up.

**What was wrong.** The local shim passed the rendered prompt to the codex CLI as a
positional argument. On Windows it arrived empty. The model, given a system prompt
and no task, replied:

```
Ready. What would you like to work on?
```

The harness did what it should with an unparseable reply: it retried three times
with the validator's error fed back, then recorded a refusal. So the pipeline
produced a clean, well-formed, entirely fictitious result. Three cassettes, three
retries, a complete trajectory, and a refusal reason that read like a considered
judgement about the criterion.

**What changed.** The prompt goes over stdin (`codex exec ... -` with the text
piped), which is the documented path and is not subject to argument mangling.

**Evidence.** `runs/*/cassettes` no longer contain a reply of that form. The two
criterion smoke run compiles one criterion and refuses the other for a reason that
quotes the site vocabulary.

**What it would have cost.** A refusal rate near 100% with a plausible-looking
explanation attached to each one. Every headline number would have been a
measurement of a broken pipe.

---

## 4. The operator's personal instructions were in every agent prompt

**Found by** reading the recorded cassettes from the run in entry 3. One reply
began "The referenced writing guide is not present at the specified path", which is
not a sentence about clinical trial criteria.

**What was wrong.** The codex CLI loads `$CODEX_HOME/AGENTS.md` into every request.
On this machine that file holds the operator's own working instructions. They were
being prepended to the grounder, the compiler and the critic.

Confirmed directly rather than assumed. Asked to quote the first line of any
instruction file it had been given, the model returned the first line of a local
integration note. With a clean home it returns `NONE`.

**What changed.** The shim builds a temporary `CODEX_HOME` holding the auth token
and nothing else, and removes it at exit. Recording with the operator's own config
now requires `--dirty-home` and says so.

**Evidence.** `python tools/cli_openai_shim.py ...` prints the clean home path on
startup. The probe is reproducible: ask any backend to quote its instruction files.

**What it would have cost.** Recorded output shaped by a file that is not in this
repository. Every cassette would replay identically for any reader, and every attempt
to re-record would produce something different, with no way to see why. It would
have been reproducible and wrong at the same time, which is worse than being
obviously broken.

All model calls recorded before this fix were discarded.

---

## 5. The trajectory index counted housekeeping as revision

**Found by** reading the index the renderer produced.

**What was wrong.** One event kind, `revision`, covered both "the compiler wrote
`laboratory_value` where the grammar says `observation` and the harness repaired it"
and "the critic built a patient this predicate gets wrong and the predicate was
rewritten". The first happens constantly and means little. The second is the
interesting thing the whole critic exists to produce. Summed into one column, the
second was invisible.

**What changed.** A separate `normalisation` event, counted in its own row.

**Evidence.** `python scripts/trajectories.py --run <run>` reports the two
separately, and the index sorts on the second.

**What it would have cost.** A claim of "N predicates revised after review" that was
mostly field-name typos.

---

## 6. The reviewer was told a code was on 1,079 charts when it was on none

**Found by** auditing the gold label distribution before any scored run. One
criterion, "chronic or intermittent haemodialysis within 90 days", returned
INDETERMINATE for all 385 patients. The corpus has 1,079 dialysis procedure rows,
so that looked like a bug in the gold rule.

**What was wrong.** It was not a bug in the gold rule. SNOMED 265764009 appears
1,079 times in the Synthea corpus and **zero times in the 385-patient panel**. The
panel is alive adults; the dialysis population is largely neither.

The terminology catalog is built from the whole corpus, so it carried the corpus
count. The predicate explainer printed that number with the words "in the panel"
next to it. A reviewer signing that predicate would have read "1079 in the panel"
about a code no patient in the panel carries.

Measured across the whole vocabulary: **47 of 724 catalog codes, 6.5%, appear in no
panel patient.** By domain: 19 of 136 medications, 16 of 191 conditions, 8 of 160
procedures, 4 of 237 observations.

**This paragraph said 50 and 7% until entry 16 recounted it.** The three-code
difference was the same defect this entry is about, sitting inside this entry's own
fix: the counts file it was read from listed 674 codes when the panel carries 677.
The corrected figures come from `python scripts/build_panel_counts.py --check`,
which recomputes from the panel and exits non-zero when the committed file
disagrees. There was no generator when this entry was first written, which is why
nothing caught it.

**Why it matters beyond the wrong label.** This is the UNMAPPABLE hazard one level
deeper. The grounder refuses a concept with no code at all, which is what stops an
"SGLT2 inhibitor" exclusion from clearing the panel. It cannot refuse a concept
whose code exists in the vocabulary and on nobody's chart, because from the
grounder's side that is a successful mapping. The criterion compiles, runs, returns
nothing for every patient, and under a closed-world query rules the same way for
all 385 of them. It looks like a result.

**What changed.**

1. Per-code panel counts are computed from the panel actually screened and vendored
   as `data/vendor/panel_code_counts.json`.
2. The reviewer view reports the panel count, not the corpus count.
3. A new check, `explain.empty_closed_world_codes`, puts a blocking notice in the
   review packet when a closed-world query rests on a code no panel patient carries.

**Evidence.**

```
$ python -c "from trialsieve import explain; ..."
STOP. These codes are in the site vocabulary but on no chart in this panel, and
the query treats their absence as proof. Every patient will come back the same
way, and it will look like a result:
  - 265764009 (Renal dialysis (procedure), 0 patients in this panel)
```

**What it would have cost.** A criterion that appeared to work, applied to every
patient in the panel, resting on evidence that could not exist. The gold set caught
it here because gold was written by hand and its distribution was audited. Nothing
in the system would have caught it.

---

## 7. The lexical search could not read British spelling

**Found by** a vocabulary probe, on a control entry rather than on the entry it
was built to test. Asked to ground "Anaemia", a concept this corpus definitely
codes, the grounder returned nothing at all and the criterion became UNMAPPABLE.

**What was wrong.** The candidate search is lexical on purpose: an embedding
search returns a plausible neighbour for a concept the vocabulary does not
contain, and a near miss on a drug class is indistinguishable from a hit until it
clears a patient. The cost of being lexical is that spelling is now a correctness
property, and nobody had paid it.

A protocol writes anaemia, haemoglobin, oedema, tumour. A US-built record system
writes Anemia, Hemoglobin, edema, tumor. The two never met.

This is the most expensive way to be wrong in this system, because it costs
coverage and leaves no trace: an empty shortlist and a genuinely absent concept
produce exactly the same output, and the second one is a feature.

**What changed.** An orthographic fold applied to the query and the vocabulary
entry alike, before matching. The symmetry is what makes it safe to be crude
about: folding "aerobic" to "erobic" is harmless when both sides fold the same
way, and the worst case is one spare candidate for the select step to reject.
Recall belongs to this step; precision belongs to the next one.

**Evidence.** `tests/test_terminology.py`, seven tests. Two of them exist to stop
the fold from becoming a different bug: a concept the vocabulary genuinely lacks
must still return nothing, and a word collision must still be shortlisted rather
than quietly dropped, because dropping it would hide from the select step exactly
the distinction it exists to make.

---

## 8. The primary model backend ran out of quota mid-project

**Found by** a 502 from the local shim, mid-run, with the CLI's own error attached:
a usage limit with a reset date a month away.

**Not a defect, but it is an engineering event and the changelog is where those go.**
Two runs died with it, and the interesting part is what the shim did rather than
what the vendor did.

**What was already right.** The shim returns a non-2xx status for a non-zero exit
rather than passing the error text through as a completion. So the failure arrived
at the agent as an exception, not as an unparseable model reply. Had it arrived as
a reply, the repair loop would have retried three times, the criterion would have
been recorded as a considered refusal, and the run would have finished with a
plausible number in it. That is failure mode 3 in this document, and the guard
against it held.

**What changed.** A second backend, the Antigravity CLI, behind the same
OpenAI-compatible shim. Nothing above the shim knew the difference: the same
`--provider shim` flag, the same cassette format, the same replay path.

Two smaller fixes came with it. Rate-limited calls now back off and retry, parsing
the vendor's own suggested delay, instead of surfacing as a failure. And a prompt
longer than the Windows command-line limit is **refused with a 413** rather than
truncated, because a silently truncated prompt means the model answers a question
it was shown only part of, and nothing downstream can tell.

**What it cost.** Every cassette recorded before the switch was discarded, and the
before-and-after comparisons in this document were re-recorded on the new backend
so that the two halves of each comparison share a model.

---

**Evidence.** `python scripts/costs.py`, which regenerates `docs/COST.md` from the recorded calls and reports each model's token and call counts separately, so the switch is visible as two rows rather than as a sentence here. `python -m pytest tests/test_recorded_call_counts.py -q` holds the per-model counts in `SUBMISSION.md` against the tracked cassettes.

## 9. A code can contain a concept without establishing it

**Found by** the same vocabulary probe, and it turned into a feature rather than a
fix.

**The situation.** A site can code a concept only at a coarser grain than the
criterion needs. The one anaemia code in this corpus is unqualified, so a
criterion asking about iron deficiency anaemia meets a code that contains the
answer without giving it. The two obvious handlings are both wrong:

- Treat the coarse code as a match. This manufactures MEETS verdicts for a
  criterion the record cannot settle.
- Call the concept UNMAPPABLE. This throws away the half of the information that
  is real, and it is the useful half: a patient with no anaemia code of any kind
  does not have iron deficiency anaemia either.

**What changed.** A query can now carry `broader_codes` beside `codes`, and the
engine treats them asymmetrically:

| what the record holds | verdict |
|---|---|
| a code from `codes` | TRUE |
| a code from `broader_codes` | **UNKNOWN**, naming the code and saying the site does not code the distinction |
| neither | whatever `absent_means` says, unchanged |

That asymmetry is the point. Presence cannot settle the criterion. Absence still
can, and absence is what removes people from the worklist.

The grounder gained a matching status, `BROADER_ONLY`, which is deliberately not
UNMAPPABLE: the criterion goes forward and the engine abstains per patient rather
than the whole criterion being refused for everyone.

**Evidence.** `tests/test_broader.py`, nine tests, including the two that keep it
honest: a query with no `broader_codes` behaves exactly as before, and a code
cannot appear in both lists, because deciding whether a code means the concept or
merely contains it is the entire content of the feature.

---

## 10. A dropped connection was being counted as a model failure

**Found by** a 502 in the middle of a 30-criterion scored run, which left one row
reading `ERROR HTTPError: HTTP Error 502: Bad Gateway` in a table whose other
rows were verdicts.

**Why it matters more than it looks.** That row is not wrong, it is unreadable. In
a summary it sits beside the criteria the model genuinely could not answer, and
nothing in the aggregate distinguishes them. A flaky evening on a local gateway
would then read as a worse system, and, worse in the other direction, a fix that
happened to coincide with a quieter network would read as an improvement. Any
before-and-after number in this document could have moved for that reason.

**What changed.** Two things, and the second is the one that matters.

The request layer now survives a transient failure: 429, 500, 502, 503, 504 and
529 are retried up to **six** attempts, backing off 2, 6, 15, 30 then 60 seconds.
A 4xx that is not 429 is not retried, because the request was rejected for being
wrong and sending it again sends the same wrong request.

This entry said four until it was audited. The budget was widened to six in
commit `7e0faaa`, after a `TransportError` still got through during the Checker B
run, and the entry was not updated with it. The code even carries a comment at
`src/trialsieve/llm.py` saying "Six attempts, not four" and explaining why, so
the change was documented in the place a reader is least likely to look and
contradicted in the place they are most likely to. `TRANSPORT_ATTEMPTS` and
`TRANSPORT_BACKOFF` are the authority.

And the retries are recorded as a **separate event kind**. A trajectory already
had `retry`, meaning the model returned something the validator rejected and was
handed the error text back. A gateway failure is now `transport_retry`, which
carries no information about the model at all. Summing the two would put network
weather into a number that is supposed to be about prompt quality.

This is the same distinction as entry 5, where housekeeping normalisations were
split out of predicate revisions, and for the same reason: two things that both
look like "the system had to try again" are measuring different things.

**What it cost.** The before-arm of the dev-split comparison was restarted, with
the transport fix applied to both arms so the comparison isolates the prompt
change. The already-recorded cassettes replayed for free, so the restart cost
minutes rather than hours.

**Evidence.** `tests/test_transport.py`, five tests: a 502 is retried and the call
then succeeds, a 400 is not retried at all, the budget is bounded, and the two
event kinds stay distinct in a trajectory.

---

## 11. Three registered trials is exactly where recall looks like reading

**Found by** asking what would happen if the model had simply memorised these
protocols. Every threshold in the output would still be right, and the evaluation
would report memorisation as compilation.

**What changed.** An audit, `scripts/contamination.py`, with three checks of
increasing strength, and a report that is generated rather than asserted.

1. **No identifier reaches a prompt.** Every prompt here is a `str.format`
   template, so the substitutions are enumerable without running anything. Six
   templates carry a slot; the slots are `text`, `kind`, `category`, `codes`,
   `concept`, `domain`, `candidates`, `record`, `index_date`, `grammar`,
   `grounded` and `examples`. None is an identifier or a title.

2. **No identifier is in any recorded request.** A template audit cannot see a
   string joined on by hand, so this reads what was actually sent. Every model
   call is recorded in full, and all of them are searched for the identifiers and
   for title-specific word sequences.

   The word *title-specific* is doing real work there. The first version of this
   check fired ten times on `'chronic kidney disease'`, which is in one
   registered title and also in the body of half the criteria the segmenter is
   given on purpose. A check that fires on the disease name returns positive on
   any corpus that mentions the disease, which makes it a check that cannot fail
   and therefore cannot pass. The fix is to subtract every word sequence
   occurring anywhere in the vendored eligibility text first, leaving 77
   sequences that only a title uses.

3. **The numbers move when the criterion moves.** The strongest of the three, and
   the one worth arguing with. A threshold is perturbed to a value the real
   protocol does not contain, the criterion is recompiled, and the emitted
   predicate has to carry the perturbed number. A predicate that reproduces the
   original threshold is reciting.

**Evidence.** `docs/CONTAMINATION.md` is generated output. `tests/test_contamination.py`,
nine tests, including one that makes the audit fail on purpose: without it, a
rename that made the template scan find nothing would report a clean pass forever.

---

## 12. The measuring instrument was wrong twice, and both errors flattered the old system

**Found by** reading the rows rather than the totals. The vocabulary probe scored
17 of 18 before a prompt change and 17 of 18 after it, which reads as no effect.
Two of the individual rows said something else.

**The first error: an accept list cannot say "or anything narrower".** For "type 2
diabetes mellitus" the grounder returned seven codes. The probe accepted one and
scored the answer as over-acceptance. The other six are, in this catalog,
`Proliferative diabetic retinopathy due to type II diabetes mellitus`,
`Nonproliferative diabetic retinopathy due to type 2 diabetes mellitus`,
`Neuropathy due to type 2 diabetes mellitus`, `Diabetic retinopathy associated with
type II diabetes mellitus`, `Microalbuminuria due to type 2 diabetes mellitus` and
`Macular edema and retinopathy due to type 2 diabetes mellitus`. Every one of them
entails type 2 diabetes. A patient carrying any of them has the disease.

The grounder was right and the probe was wrong. The acceptance rule is now
entailment rather than identity, and it is stated in the probe file.

**The second error: two different relations were sharing one class.** The probe
asked for "chronic kidney disease stage 3 or worse" to be answered with this
corpus's stage 1 and stage 2 codes, as broader codes. That is a design error.
`broader_codes` means presence yields UNKNOWN, which is right for containment: an
unqualified anaemia code might be iron deficiency anaemia. It is wrong for an
ordinal neighbour. A patient explicitly coded stage 1 is **not** stage 3 or worse,
and the correct verdict is FALSE. Answering UNKNOWN there would have thrown away a
correct answer on the eight panel patients who carry the stage 1 code.

The grounder returned UNMAPPABLE. The probe was asking for the worse answer.

**What changed.** The type 2 accept list was widened to the six entailing codes.
The kidney probe was reclassified from `broader` to `absent`. The earlier arm was
then given the three probes it had never been shown, so the comparison runs over
the whole set rather than over an intersection:

| class | what it tests | before | after |
|---|---|---|---|
| `gap` | display worded differently, code exact or entailing | 8 / 9 | **9 / 9** |
| `broader` | site codes it only at a coarser grain | 0 / 1 | **1 / 1** |
| `control` | display and concept already agree | 5 / 5 | 5 / 5 |
| `absent` | not in this vocabulary at any grain | **6 / 6** | 5 / 6 |
| | | **19 / 21** | **20 / 21** |

One net probe, bought with one regression. The controls did not move, which is
the line worth checking: a change that traded one error for another would show up
there and nowhere else.

**The disclosure that matters.** Both corrections were made after seeing a result,
and both moved the number in the new system's favour. That is exactly the shape of
an answer sheet being edited to fit, so:

- The widening cannot help the earlier run. It returned nothing at all for type 2
  diabetes, and an empty answer is not rescued by a longer accept list.
- The reclassification is checkable against the corpus rather than against taste:
  `data/vendor/terminology_catalog.json` contains CKD stage 1 and stage 2 and no
  stage 3, 4 or 5 code of any kind.
- Both are written into the probe file itself, at the top, where a reader meets
  them before the numbers.

**The honest negative that came with it.** `broader_codes` opened a new way to be
wrong, and the control probe caught it. Asked for **type 1** diabetes, the grounder
returned 44054006 as a broader code. 44054006 is type 2 specifically: a sibling,
not a parent. The cost is bounded and it is in the safe direction, because the
engine answers UNKNOWN rather than MEETS for a patient carrying it, so the failure
is an abstention where a correct FALSE was available. It costs coverage, not
correctness. It is not fixed, and it is reported in the results rather than left
for a reader to find.

---

**Evidence.** `python -m pytest tests/test_label_floor.py tests/test_coverage_numerator.py -q`. The first holds the noise floor to the post-stratified estimate over the population rather than over the hardest stratum; the second holds the coverage numerator to the compiler's output rather than to the gold set's. Both were the errors, and both flattered the old system.

## 13. A reproduction step that appears to hang is not reproducible

**Found by** running the scoring step for the first time on the full panel and
watching it print nothing for fifteen minutes before I killed it.

**Why this is a correctness problem and not a comfort one.** The whole
reproducibility claim is that a reader runs one command and gets the published
numbers. A step that produces no output for twenty minutes on a laptop is a step
a reader kills, and then the numbers are unchecked for a reason that has nothing
to do with the numbers. "It would have worked if you had waited" is not a
reproduction.

**Where the time went.** The paired bootstrap resampled criteria and patients,
then materialised the induced cell list and walked it. Forty criteria by three
hundred and eighty-five patients is fifteen thousand four hundred tuples built and
walked twice, ten thousand times, for each of three metrics and each arm
comparison.

**What changed.** The resample is counted rather than built. The design is crossed
and complete, so the count of a 0/1 indicator over a resample is

    sum over criteria c of  (times c was drawn)
                          * sum over patients p of (times p was drawn) * indicator(c, p)

and the indicator is sparse for the metric that matters: a silent error is rare,
so the list of patients where it fires is short and the inner sum runs over that
list rather than over the panel. Coverage is dense, so it is counted through its
complement instead. An incomplete design falls back to the original loop rather
than counting cells that do not exist.

**The measurement.** A multiplier with no conditions attached is not a measurement,
so here are the conditions. Metric `ser`, a forty criteria by three hundred and
eighty-five patient design, which is 15,400 cells, at 300 resamples, on Windows 11,
AMD64, CPython 3.14.2: the paired comparison runs in **0.131s against 3.942s**, a
ratio of **30.2**, with both implementations returning identical interval
endpoints. The figure this entry first published was 33, measured the same way on
the same machine on a different day, so treat the ratio as about thirty rather
than a constant. It depends on the metric, because the speedup comes from the
sparsity of the indicator, and a dense metric like coverage gains less.

End to end, the scoring step at 10,000 resamples went from **over fifteen minutes
without finishing** to **27 seconds**. That one is the original timing and has not
been re-measured here.

**What makes this safe to have done.** The random draws are the same calls in the
same order on the same seeded generator. Only the arithmetic over each draw
changed, so the two implementations can agree to the last digit, and
`tests/test_bootstrap.py` requires it: the old loop is kept in the test file as an
oracle and the interval endpoints are compared exactly. An optimisation that also
changed the draw order would have had to be argued statistically, which is a much
weaker thing to be able to say about a published confidence interval.

The same file also carries an A/A control: two identical arms must produce an
interval containing zero. A bootstrap that manufactured a difference out of
resampling noise would pass every speed test and fail that one.

**Evidence.** `python -m pytest tests/test_bootstrap.py -q`, which runs the resampler at the committed iteration count and fails if it stops printing progress. The wall-clock line `python run.py reproduce` prints as its last output is the end-to-end version of the same check.

## 14. The prediction about how this fails was wrong, and in the dangerous direction

**Found by** running the grounding probe against a local 8B model
(`granite3.1-dense:8b` through ollama) to turn a claim in the README into a number.

**The claim.** "How it fails" said the compiler degrades by refusing rather than
by lying: a weak model that cannot ground a concept should return UNMAPPABLE and
stop the criterion, so the architecture should lose coverage rather than gain
silent errors. It was labelled a design claim rather than a measurement, which was
honest about its status and did nothing about its truth.

**The measurement.** 21 concepts, same probe set, both runs rescored under today's
acceptance rule so the rule change cannot show up as a result.

| | gemini-3.7-flash-medium | granite3.1-dense:8b |
|---|---|---|
| correct, of 21 | 20 | 14 |
| wrong by accepting too much | 1 | 7 |
| wrong by accepting too little | 0 | 0 |

Every error in both runs is an over-acceptance. There is not one refusal in either
column. The prediction was not merely unsupported, it was backwards.

**The worst single case appears in both columns.** "Type 1 diabetes mellitus" has
no code in this Synthea site's vocabulary. The correct output is UNMAPPABLE, which
is the whole reason that status exists. Both models instead return `44054006`,
which is type 2. A criterion excluding type 1 patients would then exclude the type
2 population the trial is recruiting.

**Two things that make this worse rather than better.** Nothing was invented: the
grounder drops any code absent from the candidate list the vocabulary returned, and
that filter did not fire once across the weak run. Every wrong answer was a real
code from this site's own vocabulary that means something adjacent. So the
containment already in the code is aimed at a failure mode that did not occur, and
the failure that did occur walks around the UNMAPPABLE path rather than through it.

**What changed.** The README paragraph, which now states the measurement and drops
the prediction. `scripts/compare_probes.py` gained a markdown writer and an output
path, so the comparison is generated rather than transcribed, and it reports the
over-acceptance and under-acceptance counts separately instead of one accuracy
number. `docs/WEAK_MODEL.md` is that output.

**What did not change, on purpose.** The grounder prompt is frozen for the
evaluation and the held-out run was already compiling against it when this
measurement landed. Editing the prompt now would make the published numbers the
product of a prompt chosen after seeing a held-out result, which is the thing
`docs/EVAL_PROTOCOL.md` exists to prevent. The fix belongs to the next protocol
version and the shape of it is already visible: the selection step is asked which
candidates mean the concept and is not asked to justify the entailment in the
direction that matters, so a sibling code satisfies it.

**What is left holding this** is the human checkpoint rather than the model.
`explain.py` resolves every code to the display name the site's own records use, so
a predicate for "type 1 diabetes mellitus" puts the type 2 display in front of the
reviewer who has to sign it. That is a property of the artifact and it is checkable
by reading the file. It is not a measurement that a reviewer catches it, and this
changelog is not going to claim it is.

**Evidence.** `python scripts/compare_probes.py runs/probe-before/probe.json runs/probe-after/probe.json`, which prints both probes side by side and is the source of the numbers in `docs/WEAK_MODEL.md`. The prediction it falsified is in section 10 of `docs/EVAL_PROTOCOL.md`, *Predictions, registered before measuring*, which is kept as written rather than edited to match the outcome.

## 15. Three checks that could not fail, and one that reported a pass for a comparison it never made

**Found by** two reviewers reading the tree against its own claims rather than
running it. Every item here was a sentence in the writeup that the code did not
back. None of them showed up as a failing test, because each one failed by
returning success.

**`scripts/_verify_blind.py` searched for a key nothing writes.** The blindness
check reads every recorded Checker B prompt looking for anything the system
produced, and one of the four things it looks for is the predicate digest.
`_compiled_digests()` read `c["digest"]` and `c["predicate_digest"]`. The key is
`predicate_sha256`, and it has been since the compiler was written. So the digest
set was empty on every run, the loop over it did nothing, and the check printed
PASS. The only symptom was `"compiled_digests_searched": 0` in the JSON it prints,
which is exactly what a genuine clean result looks like. A second promise in the
same docstring, that the gold label text is searched, was declared as
`ANSWER_FILES` and never read at all.

**What changed.** The key is corrected. The answer-file search is implemented, and
it searches source lines rather than every long line, because the criterion text
legitimately appears in a Checker B prompt and matching on it would report a leak
on every cassette. It now searches 79 distinctive lines from the gold file. Most
importantly, `verify_blind` returns `empty_term_sets` and refuses to pass when any
term set is empty:

    NOT VERIFIED: compiled digests came back empty, so the search for it could
    not have found anything. This is reported as a failure rather than a pass
    because a check that searched nothing and a check that found nothing print
    the same zero.

That is the general fix. The bug was not that the key was wrong, it is that a
search over an empty set is indistinguishable from a search that found nothing,
and only one of those is a pass.

**`run.py diff` returned 0 when there was nothing to compare.** The reproduction
target ends by byte-comparing this machine's numbers against the published ones.
With no published baseline it printed "nothing to compare against yet" and
returned, so `python run.py reproduce` ran to the end and reported a clean run
having checked the one thing it exists to check. It now exits 1 and says NOT
COMPARED. A reproduction that compares nothing is not a reproduction, and it has
to say so in the same voice it would use to say the numbers differ.

**"`scripts/worklist.py` refuses, by exit code, and the refusal is tested" was
false.** `tests/test_signoff.py` tests `signoff.enforce()`, the library function.
That passes even if the script never calls it, calls it and ignores the result, or
catches the exception and carries on. Nothing invoked the script or read its exit
status. `tests/test_worklist_gate.py` now runs it as a subprocess and asserts exit
3, asserts no document was written, asserts the refusal names the command that
clears it, asserts `--allow-unsigned` stamps NOT FOR USE into the artifact, and
asserts no bulk approval flag is declared on `signoff.py`.

Two things about that last test are worth stating. It parses the `add_argument`
calls out of the source rather than grepping the file, because the first version
grepped and failed on the docstring sentence saying there is no `--approve-all`:
it flagged its own rule description as a violation of the rule. And it runs against
a small committed fixture rather than the scored run, because pointing it at the
scored run made all four tests skip on a clean checkout, which is precisely when a
reader checking the claim would run them. A skipped test backs no claim.

**The claim in `SUBMISSION.md` also omitted `--allow-unsigned`.** The README
disclosed the override and the submission document did not, so the two disagreed
about how strong the gate is. The submission now names it, says what it stamps on
the document, and points at `docs/GATE.md`.

**Evidence.** `python -m pytest tests/test_signoff.py tests/test_worklist_gate.py -q`, and `python scripts/verify.py blind --run runs/tierA` for the fourth. Each carries a positive control, which is the whole point of the entry: a check with no way to fail reports a pass for a comparison it never made.

## 16. A committed data file with no generator, and the check it broke

**Found by** a reviewer recomputing a published figure. `data/vendor/panel_code_counts.json`
holds rows and distinct patients per code for the 385-patient panel. It listed 674
codes. The panel carries 677.

**The three it omitted.** `2532-0` lactate dehydrogenase, on 9 patients.
`59408-5` oxygen saturation, on 35. And `8331-1` oral temperature, on **214 of the
385**.

**What that broke.** `explain.empty_closed_world_codes` warns a reviewer when a
predicate treats absence as proof over a code no panel patient carries, which is
the failure that returns the same answer for everyone and looks like a result. It
read a missing entry as a count of zero. So a reviewer building a predicate on
oral temperature was shown "STOP. These codes are in the site vocabulary but on no
chart in this panel" about a code most of the panel carries. A warning that fires
on a common code teaches a reviewer to click past it, which switches the check off
for the case it was built for.

**Why nobody caught it.** `grep -rn panel_code_counts --include=*.py` found one
reader and no writer. The file was produced once, by hand or by something that did
not survive, and after that there was no way to notice it had gone stale. A
committed artifact with no generator cannot be checked against the thing it
describes.

**What changed.** `scripts/build_panel_counts.py` generates it and, with `--check`,
recomputes from the panel and exits non-zero on any disagreement. Running it found
3 missing and 0 miscounted, so the file was truncated rather than wrong, which is
the kind of defect that survives a spot check of any individual number.
`empty_closed_world_codes` now reports only codes the table says are carried by
nobody, and a new `unknown_panel_codes` reports codes the table says nothing about,
under a heading that names it as a defect in the checkout rather than a fact about
the cohort. The two call for different actions and folding them together made a
build error read as a clinical finding.

**The recount changed a published figure.** Entry 6 said 50 of 724 catalog codes,
7%, appear in no panel patient. It is 47, 6.5%, and the observation domain is 4
rather than 7. Entry 6 is corrected in place with a note. The defect entry 6
describes was sitting inside entry 6's own fix.

**Evidence.** `python scripts/build_panel_counts.py --check`, which recomputes the file from the panel and exits non-zero if the committed copy disagrees. That mode did not exist before this entry, which is why the file could sit three codes short without anything noticing.

## 17. An event kind with a renderer, a counter, a column, and no call site

**Found by** checking one sentence in the trajectory index against the code:
"The signature is a `human_checkpoint` event, and it lives in the compiler
trajectory of the predicate that was signed."

**It was not.** `Trajectory.human_checkpoint()` existed in `trace.py`.
`render_markdown` had a branch for drawing it. `scripts/trajectories.py` counted
it, gave it a weight in the interest score, and printed a row for it in the
summary table. `grep -rn human_checkpoint --include=*.py` found every one of those
and no caller. `scripts/signoff.py` appended the decision to `runs/tierA/signoffs.jsonl` and
stopped there.

So the index printed `| human checkpoints | 0 |`, which was true, and true for a
reason nobody could see from the number. The brief names human checkpoints as a
required element of the trajectories. This project would have shipped a zero in
that column and an explanation that nothing had been signed yet, when the real
state was that signing would not have produced one either.

**Why it survived.** Every piece was individually correct. There is no test that
fails when a function is never called, no linter that flags a method with no
caller in another module, and the output was a plausible zero rather than a crash.
It is the same shape as the blind check in entry 15: the failure mode is a
truthful-looking number produced by a path that does not run.

**What changed.** `trace.append_human_checkpoint()` adds the event to a trajectory
that was written and closed in an earlier process, which is the actual situation:
a sign-off happens hours after the compile, from a different script, with no live
`Trajectory` object to call a method on. It continues the sequence numbering
rather than starting again, so the log stays one ordered record of everything that
happened to that criterion, including the part a human did. `scripts/signoff.py`
now writes to both places. The ledger is what the gate reads and the trajectory is
what a reader follows, and a decision belongs in both.

**Evidence.** `tests/test_human_checkpoint.py`, five tests, driving the script
over a temporary copy of a committed fixture with the answers on stdin. It asserts
the decision reaches the ledger and the trajectory, that the appended event
carries the reviewer's role and the digest it approved, that the sequence has no
gap, that a rejection is recorded exactly like an approval, that a run whose
trajectories were not kept still records the signature instead of losing it, and
that the index then counts one where it counted zero.

**It found a second defect on the way.** The fifth test builds a trajectory and
renders it, and `render_markdown` raised `KeyError: 'prompt_version'` on an
`instructions` event that did not carry one. That is a hard crash in the renderer
that builds every trajectory document, triggered by one field missing from one
event, in a function whose whole job is reading JSONL off disk that an earlier
version of the recorder may have written. It now degrades one heading instead of
stopping the build.

**And a third, which is the one worth keeping.** The new
`append_human_checkpoint` was first written as a module-level function placed
between two methods of `Trajectory`. In Python that ends the class body, so
`final`, `write` and `summary` stopped being methods. The full suite, 153 tests at
the time, stayed green. The break surfaced when a running job died on
`AttributeError: 'Trajectory' object has no attribute 'final'`.

A suite that cannot notice a core class losing three methods is not covering that
class, and `Trajectory` is the recorder every trajectory in this submission goes
through. `tests/test_trajectory_api.py` now records one trajectory using every
event kind the recorder offers, writes it, reads it back, and renders it: 24
tests covering the method surface, dense sequence numbering, LF line endings, the
`kind` payload collision that `_add` is positional-only to prevent, and that the
renderer emits every kind rather than silently dropping one.

## 18. The strongest check in the project had never once run

**Found by** running `scripts/contamination.py --counterfactual` for the first
time on the held-out run, and reading the last line of its own report:

    **0 of 0 follow the perturbation. 0 of 0 reproduce the original number.**

**Why that line is the whole problem.** Check 3 is the one this project leans on
hardest. Three registered trials with public identifiers is exactly the setup
where a compiler that memorised a protocol produces perfect output, so the
argument that the model reads rather than recites rests on moving a threshold and
requiring the predicate to move with it. "0 of 0" is a ratio over an empty
denominator. It renders as a clean result and it means nothing happened.

**Three defects, stacked, each hidden by the one in front of it.**

1. **The record had the wrong shape.** The counterfactual built its shadow
   criterion with `source_text` only. `compile_criterion` renders its plan prompt
   with `PLAN.format(**criterion)` and `PLAN` contains `{text}`. Every row raised
   `KeyError: 'text'`.

2. **The return value was a pair.** `compile_criterion` returns
   `(record, trajectory)`. The loop called `.get` on the tuple. With defect 1
   fixed, every row raised `'tuple' object has no attribute 'get'` instead. The
   `except Exception` around the call turned both into `status: error` and the
   report carried on.

3. **The edit broke words.** With both fixed, the first row came back `refused`,
   and the reason said the model could not code `T2.7DM`. The number regex had
   matched the `2` inside `T2DM`. A perturbation that damages a term tests the
   compiler's tolerance for nonsense rather than its willingness to read, and the
   refusal it earns is then counted against it. Candidates are now required to be
   flanked by non-letters, so `T2DM`, `HbA1c`, `CKD3` and `COVID19` are left alone.

**Why none of it was visible.** The loop caught every exception into a row and the
run exited 0, because the exit code only considered checks 1 and 2. So a script
whose headline check had never executed printed a report and returned success.
This is the third instance in this changelog of the same shape, after entry 15's
blind check and its `run.py diff`: **a check that did not run and a check that
found nothing print the same thing.**

**What changed.** Both bugs fixed. The perturbation skips numbers inside a term.
The failure path now records `traceback.format_exc()` rather than only
`type(exc).__name__: exc`, which is what turned defect 2 from an afternoon into a
minute. The progress line prints the reason as it goes instead of holding it until
the JSON is written at the end. When nothing compiles, the report says **NOT
MEASURED** and names how many attempts raised, instead of printing a ratio. And
the counterfactual is now part of the exit code, so a run that measured nothing
fails.

**Evidence.** `tests/test_perturb.py`, five tests: that a digit inside a term is
never moved, that a standalone threshold is, that the largest number is the one
chosen rather than an incidental small one, that text with no safe candidate
declines rather than guessing, and that the new value is never the old one.

## 19. The headline operating point was chosen using the labels it was scored on

**Found by** reading `operating_curve` in `evaluation/score.py` after the first
full report, and noticing what its selection loop counts:

    bad = sum(1 for r in fails if r.gold != "FAILS")

**The defect.** The curve ranks criteria by how many false exclusions each one
makes, keeps the safest until the budget runs out, and then scores the panel. The
gold labels driving that ranking belong to the same 385 patients the row then
reports on. So the top row, **43.5% panel reduction at zero false exclusions**,
said that a clean subset of criteria existed. It did not say a coordinator could
have found that subset in advance, which is the only version of the claim worth
anything, and it is the version a reader takes away. A number selected on the
evaluation set and read back as a result is the oldest way to be wrong in public.

**Why the obvious fix was not available.** The honest answer is to select on one
split and score on another. The dev split here is deliberately unlabelled, by
`docs/DEV_SPLIT.md`, so there is nothing on it to select against.

**What changed.** `operating_curve_cv` runs the identical greedy rule cross-fitted
over 5 folds of patients: each patient's verdict comes from a subset chosen on the
other four folds, so no patient contributes to the decision that scores them, and
the training budget is scaled by the training fraction so the tolerated rate per
patient matches rather than sitting `(k-1)/k` looser. Both curves are printed. The
in-sample one is now labelled an upper bound in its own docstring and in the
report.

**The result, and the reason it needed a control.** The two curves are identical
on every row. Zero optimism is the best outcome available, and it is also exactly
what a cross-fit that quietly reused the in-sample selection would print, which is
the failure shape this changelog has now recorded five times. So two things were
added rather than one.

First, the report computes and states why they agree: of the 12 criteria that ever
exclude a patient, **8 make no false exclusion anywhere in 385 patients** and the
other 4 make 358, 31, 31 and 4. Nothing sits near the threshold, so all five folds
select the same 8. The equality is a property of the separation, and the report
now says so with the numbers rather than leaving a reader to assume it.

Second, `tests/test_score.py` carries a positive control: a panel with one
criterion that excludes all 100 patients and is wrong about exactly one of them.
In sample it is dropped at budget 0 and the curve reports no false exclusion.
Cross-fitted, the fold holding that patient trains on a set where the criterion
looks perfect, keeps it, and excludes them, so the cross-fitted curve reports the
false exclusion the in-sample selection had hidden. The agreement on real data is
therefore a measurement. A negative control asserts the two curves agree when
there is genuinely nothing to find, and a third test asserts the fold assignment
partitions every patient exactly once, because a fold that dropped patients would
shrink the denominator and flatter both curves at once.

**Evidence.** `results/RESULTS.md`, both curves and the paragraph between them;
`results/results.json` under `crossfit`; three tests in `tests/test_score.py`.

## 20. A section guarded by `if exists()`, a key that nothing writes, and the two claims it cost

**Found by** looking for the label noise floor in `results/RESULTS.md` after a
full report run, and not finding it at all.

**Three defects in eleven lines.**

1. The whole section sat behind `if ag_path.exists():`. `evaluation/checker_b/agreement.json`
   had never been generated, so every report ever produced omitted the section
   silently. Nothing failed. The document simply went from the arm comparison
   straight to provenance, and a reader has no way to tell a section that was
   dropped from a section with nothing to report.

2. Had the file existed, the section would have died immediately: it read
   `ag['agreement']['cohens_kappa']` and `ag['agreement']['gwets_ac1']`, and
   `evaluation/score.py` writes `cohen_kappa` and `gwet_ac1`. A `KeyError` that
   could not fire because the guard in front of it never opened.

3. The prose promised something no code enforced: *"Any difference between arms
   smaller than that is reported as uninterpretable rather than as a finding."*
   Nothing compared anything. The comparison table printed six differences and
   said nothing about whether the labels could resolve them.

**What the floor turned out to be.** 180 cells labelled twice, independently, on a
different model family: 76.7% raw agreement, kappa 0.650, AC1 0.651.

**Why the disagreement rate is split rather than quoted whole.** 23.3% is not one
number. 19 of the 42 disagreements are contradictions, one labeller saying a
patient meets a criterion and the other saying they fail it, and on those cells at
least one label is wrong. The other 23 are one labeller committing where the other
abstained, which is a disagreement about how much a record has to say before it
counts as saying it. That is the judgement this entire system exists to make
explicit, so folding it into label error would mean scoring the question instead of
the answer. The bar a measured difference has to clear is therefore **10.6%**, not
23.3%. Quoting the larger number would have been the conservative-looking choice
and the wrong one.

**What it cost.** Two of the six published differences fail the rule the report had
been promising:

| comparison | difference | 95% CI excludes zero | vs 10.6% contradiction rate |
|---|---|---|---|
| TS - B1, SER | +0.0305 | yes | **below, uninterpretable** |
| TS - B1, false-FAILS | +0.0275 | yes | **below, uninterpretable** |
| TS - B1, coverage | +0.1662 | yes | above |

A confidence interval that excludes zero says the difference survives resampling.
It says nothing about whether the labels underneath could support a difference
that small, and those are separate questions that a single table had been letting
blur. So the surviving claim against B1 is the coverage one: TrialSieve answers
16.6 points more of the panel, and the error difference at which it does so is
smaller than these labels can resolve. That is a weaker statement than the one the
table implied yesterday and it is the one the evidence carries.

**What changed.** `load_label_floor()` returns `None` explicitly and the section
prints **NOT MEASURED** under its own heading rather than vanishing. The key names
are read with fallbacks and asserted. The contradiction rate is computed from the
disagreement pattern and every comparison row is annotated against it, in the row,
where it cannot be scrolled past.

**Evidence.** `results/RESULTS.md`, the `vs label floor` column and the section
below it; `results/results.json` under `label_noise_floor`; five tests in
`tests/test_label_floor.py`, one of which asserts every published comparison row
carries a verdict, so a future row cannot be added without one.

## 21. The system's worst error is the error it was built to prevent

**Found by** running `scripts/gate_demo.py` and reading the worklist it produces
under `--allow-unsigned`:

    {"nct_id": "NCT06983054", "panel": 385, "ruled_out": 385,
     "needs_review": 0, "eligible": 0, "reduction": 1.0}

A prescreening tool that rules out every patient in the panel is not a
prescreening tool. The headline says 43.5% reduction at zero false exclusions and
the flagship artifact says 100%, and both were true, because the headline runs at
an operating point and the worklist runs every compiled predicate.

**One field, 358 patients.** `NCT06983054-INC-01` is *"Adults with previously
diagnosed T2DM according to American Diabetes Association (ADA) criteria"*. It
compiles to an age bound and an existence check on SNOMED `44054006`, with
`absent_means` set to `"false"`. 27 patients in the panel carry that code and the
predicate is right about all 27. The other 358 do not carry it, and instead of
reporting that the record does not say, it rules them out. Gold says
INDETERMINATE for every one of those 358. That is **358 of the 424 false FAILS in
the entire scored run, from a single JSON field.**

This is the exact error the project exists to prevent. `absent_means` is the flag
that exists so that silence is not mistaken for an answer, and the model set it
the wrong way on the most consequential criterion in the set.

**Two guardrails had the information and neither fired.** The compiler prompt says
in as many words that a wrong `false` rules a patient out on the strength of a gap
in their record, and to choose `unknown` when in doubt. The critic's fourth review
rule is *"is any `absent_means` set to false for something that could easily have
happened at another hospital"*. Both are model-side. Both passed it. The critic
probe shows the critic catches 9 of 9 planted defects with 0 false alarms on 5
controls, so it is not broken in general; it did not catch this one.

**What was measured, and what was deliberately not done.** The predicate was not
edited. Instead the same compiled output was executed a second time with
`--absent-means-override unknown`, a flag that already existed, which discards
every closed-world decision the compiler made:

| | as compiled | absence forced to unknown | change |
|---|---|---|---|
| coverage | 24.1% | 18.6% | -5.5 points |
| silent errors | 469 | 111 | **-358, -76%** |
| false exclusions | 182 | 18 | **-164, -90%** |
| panel reduction | 60.4% | 41.1% | -19.2 points |

Three quarters of the system's silent errors and nine tenths of its false
exclusions are the model deciding that a silent record is an answer, and the
entire cost of not doing that is 5.5 points of coverage.

**Why the scored arm was left alone.** The override was run after seeing the
held-out failure. Retro-fitting the compiler and re-scoring would be tuning on the
evaluation set, whatever the fix's merits, so the pre-registered arm stands
unchanged, the sensitivity arm is published beside it, and the ordering is
recorded as amendment **A6** in `docs/EVAL_PROTOCOL.md`. The compiled file is
byte-identical to what it was before the arm existed and `predicate_sha256` shows
it. No model call was added: executing a compiled predicate is free, which is the
whole architecture, and it is why this cost nothing to measure.

**What actually stops it.** Not the prompt and not the critic. The sign-off gate:
no worklist exists until a named human has read each predicate rendered into
English, and `docs/GATE.md` is that refusal captured by exit code. A reviewer
reading *"the patient does NOT have type 2 diabetes, and the record is trusted to
be complete for this"* against a criterion that says *previously diagnosed T2DM*
rejects it in one line. The gate is not paperwork around a system that works. It
is the control that catches the failure the two model-side checks missed.

**Evidence.** `results/RESULTS.md`, the sensitivity section, every figure computed
from the two scored groups rather than typed; `results/results.json` under
`groups.ow`; `docs/GATE.md` for the refusal; `tests/test_sensitivity_section.py`,
four tests, one of which fails if any of those figures is ever hand-written back
into the prose.

## 22. Deleting a run that never happened is not enough

**Found by** rebuilding the trajectory index after the seed fix and reading its
totals: **15 critic findings, 3 revisions**. Both numbers had roughly tripled and
nothing in the system had changed to produce them.

**What had happened.** Entry 18's neighbour in this changelog records that `--seed`
never reached the model, so compilations under seeds 8 and 9 replayed seed 7's
cassettes and produced byte-identical predicates. When that was found, the fake
artifacts were deleted: `runs/tierA/compiled/criteria_seed8.json`, `criteria_seed9.json`, and
the cells tagged with those seeds. That felt complete. It was not. Each of those
runs had also written **114 trajectory files**, and the trajectory index reads the
directory rather than the compiled output, so it went on counting the findings of
a run that had made no model call. Every finding in seeds 8 and 9 was the same
seed 7 finding, recorded three times, and the index summed them.

**Why it mattered more than a wrong number.** The trajectory index is the artifact
the brief asks for by name. Three copies of one critic finding presented as three
findings is the difference between "the adversarial review fires occasionally" and
"it fires routinely", which is exactly the impression a reader would take from a
count they cannot easily audit. And it inflated in the flattering direction, which
is the direction that does not get questioned.

**The true counts**, after removing 228 stale files with an mtime predating the
real seed-8 run:

| | before | after |
|---|---|---|
| trajectories | 206 | 92 |
| model calls | 870 | 469 |
| critic findings, scored compile | 6 | **2** |
| critic findings, planted-defect probe | 9 | 9 |
| predicates revised | 3 | **1** |

**The general shape.** An artifact that derives from a run has more than one
output, and deleting the one you were looking at leaves the others behind still
being read. The compiled JSON was the obvious output. The trajectories, the
cassettes and the cells were all outputs of the same run, and only two of the four
were cleaned. `scripts/verify.py trajectories` would not have caught it either:
every one of those stale trajectories matched a real cassette byte for byte,
because the calls really had been replayed. They were internally consistent
records of a run that did not happen.

**What changed.** The stale files are gone and `SUBMISSION.md` now states the
counts as measured, separating the 2 findings in the scored run from the 9 in the
probe rather than summing them into one total. The 2 confirm the loop fires end to
end on real work: one finding confirmed by executing the counterexample, one
dismissed by executing it, and one predicate revised as a result.

**Evidence.** `runs/tierA/trajectories/index.md` and its per-agent counts;
`python scripts/trajectories.py --run runs/tierA`, which prints the JSON above
from the JSONL rather than from a stored total.

## 23. A noise floor measured on the hardest cells excused the losses

**Found by** a reviewer asking what population the label noise floor was a rate
of. It is quoted as a single percentage and used as a bar, so the question is
whether the cells it was measured on look like the cells it is applied to.

**What was wrong.** `evaluation/checker_b.stratified` draws the doubly-labelled
sample with **equal shares of each Checker A label**, and its docstring says why:
a uniform draw would have been almost entirely INDETERMINATE, and a second
labeller who abstained on everything would have scored high agreement while
knowing nothing. The same docstring warns that prevalence cannot be read off the
result. `load_label_floor` then computed the floor as contradictions divided by
sample size.

That is the contradiction rate in a population that is one third FAILS. No panel
is. Worse, FAILS is the stratum the two labellers contradict each other in most
often, by a factor of five:

| Checker A label | contradicted | share of the sample | share of the scored panel |
|---|---|---|---|
| FAILS | 16 of 60 = 26.7% | 33.3% | 5.2% |
| MEETS | 3 of 60 = 5.0% | 33.3% | 17.9% |
| INDETERMINATE | 0 of 60 = 0.0% | 33.3% | 76.9% |

Reweighting those rates to the panel's own mix gives **2.3%** (95% CI 1.2% to
3.6%). The published floor was **10.6%**, 4.6 times too high.

**Why it mattered.** The floor is not a footnote. Every row of every paired
comparison is marked against it, and a difference below it is printed **below,
uninterpretable**. A floor 4.6 times too high does not fail safe: it covers more
differences, and the differences it covered were not random. `TS - B1` on silent
error rate is **+0.0318**, which is TrialSieve committing to more wrong answers
than the baseline that mostly abstains. Under 10.6% that was uninterpretable.
Under the panel's own 2.3% it is above the floor and it stands as a measured
loss. `TS - B2` on false FAILS moved the same way.

An error that hides exactly the two comparisons the system loses is the kind that
survives review, because nobody checks the number that says there is nothing to
see.

**The fix.** `scripts/report.py` poststratifies: per-stratum contradiction rates,
reweighted to the label mix of the group being compared, with a 95% interval
resampled within stratum because the stratum carrying the estimate is 60 cells
wide. It is computed per group rather than once, since the ten-patient sample and
the full panel do not share a mix. Where a scored label never appeared in the
sample it returns nothing at all, because falling back to the unweighted rate is
the bug. The sample rate is still published, labelled as the sample's.

**What holds it.** `tests/test_label_floor.py` asserts the direction rather than
the number: a sample enriched in the hardest stratum must reweight **downward**,
an equal-share population must reproduce the sample rate exactly, and an
unweighable population must return nothing.

**Evidence.** `python -m pytest tests/test_label_floor.py -q`, which requires the floor to be post-stratified over the population and fails if it is read off the doubly-labelled stratum alone. `results/results.json` carries both, `label_noise_floor` and `groups.k0_seed7.label_floor_poststratified`, so the two can be compared rather than taken on trust.

## 24. The probe that scored 9 of 9 had never tried the defect that mattered

**Found by** a reviewer asking which defect classes the critic probe had actually
planted, rather than what fraction it caught. The summary read **caught 9 of 9
planted defects, 0 false alarms**, and the by-class table under it had three rows.
The mutator list has five.

**What was wrong.** `evaluation/critic_probe.py` took the first six compiled
predicates in file order. Boundary, threshold and direction defects apply to almost
any predicate, so those three were planted and caught. A window defect needs a
predicate with a time window and an absence defect needs one with `absent_means`
set to `unknown`. Four predicates admit the first and three admit the second, and
none of the seven were in the first six.

So two of the five classes were planted zero times, and the reporting loop skipped
any class with no plants, which meant nothing in the document said so. The
arithmetic was right. The denominator simply never contained the cases, and a ratio
cannot report a class that is missing from it.

**Why it mattered.** The untested class is `absence`: silence in the record
becoming proof of absence. That is the defect that produced **358 of the 424 wrong
exclusions** in the scored run, and the critic probe is the evidence that the
adversarial review works at all. "9 of 9" was standing in for the one class the
system's worst failure came from.

**The fix.** `cover()` selects predicates by greedy set cover over the mutation
classes, rarest first, then spends whatever budget is left on the least-tested
class rather than on file order. At the same limit of six predicates it now plants
every class three or more times. Classes with no plants get a row reading **0,
never planted** and a paragraph naming them, and the summary prints NOT MEASURED
beside the catch rate, so the absence of a measurement can no longer look like a
clean sweep.

**What it found immediately.** With all five classes planted the probe stopped
being saturated:

| defect class | planted | caught |
|---|---|---|
| boundary | 3 | 3 |
| threshold | 3 | 3 |
| window | 3 | 3 |
| direction | 6 | 6 |
| **absence** | **3** | **1** |

The critic catches **15 of 15** across four classes and **1 of 3** in the class
that matters most. It is not weak in general. It is weak in exactly one place, and
that place is the one where being weak is expensive. The scored run's worst failure
is no longer an anecdote about one predicate the critic happened to miss: it is the
measured behaviour of the reviewer, and `docs/CRITIC_PROBE.md` states it as such.

A probe that cannot fail is not a probe. This one scored 100% for as long as it
avoided the question.

---

**Evidence.** `python -m pytest tests/test_critic_probe.py -q`, which requires every declared defect class to have been planted at least once, and `results/critic_probe.json` for the per-class result. `by_class` is the field that makes 9 of 9 readable as a coverage gap rather than a score.

## 25. The one invariant the design calls its own sharp edge was never checked

**Found by** a reviewer reading the README's promise, *"Presence cannot settle
it. Absence still can."*, against the code that is supposed to hold it up. The line is a promise: a code the site records more coarsely than
the criterion needs goes into `broader_codes`, and then "presence cannot settle
it. Absence still can." `docs/AGENT_DESIGN.md:71-77` restates it as a contract on
the compiler. The emit prompt spells it out to the model in full.

Nothing verified it. The reviewer's question was one sentence: what happens if the
model puts a broader-only code in `codes` anyway?

**What was wrong.** The emit validator in `src/trialsieve/agents/compiler.py`
built its allow-list of legal codes as one set (entry 29 is where those lines
changed, so they no longer read this way):

```python
allowed = {c for g in grounded for c in g["codes"]}
allowed |= {c for g in grounded for c in (g.get("broader_codes") or [])}
```

The union is right for deciding whether a code was hallucinated, which is what the
check was written to do. It is exactly wrong for deciding which slot a code belongs
in. A broader-only code emitted into `codes` is inside the allow-list, so it
validates, and the engine then reads it as an exact match and lets presence settle
the verdict. The rule was enforced by asking politely and checking nothing.

One rule nearby does fire, and its shape is the tell. `src/trialsieve/ir.py:108`
rejects a code listed in `codes` and `broader_codes` of the *same query*. That
catches a model hedging out loud and cannot catch a model that simply moves the
code, because the intersection is then empty. Both violations below have
`broader_codes: []`. Entry 27 is the same code again, and it shows the schema
does not merely permit the promotion: on a concept with no exact code it makes
the promotion the only shape that validates at all.

**What the run actually contains.** Eight of the compilable criteria have grounding
that produced a broader-only code. Two of them then used it as an exact one:

| criterion | code promoted | `absent_means` |
|-------------------|-----------|-------|
| `NCT06983054-INC-01` | 44054006 | false |
| `NCT06717698-INC-07` | 44054006 | false |

Both halves matter. The promotion means presence settles the criterion as MEETS.
`absent_means: false` means absence settles it as FAILS. Together they close the
last exit: the criterion has no path to INDETERMINATE at all, on any patient,
which is the single outcome the design exists to preserve. SNOMED 44054006 is
unqualified diabetes mellitus, and `NCT06983054-INC-01` is the criterion behind
**358 of the 424 wrong exclusions** in the scored run.

Entry 21 named `absent_means` as that failure's cause. It was half the cause. The
other half was here, unmeasured, in the check that was meant to be the guardrail.

**The fix, and what was deliberately not fixed.** `scripts/grounding_audit.py`
audits any compiled run for the promotion and exits non-zero when it finds one.
`tests/test_grounding_audit.py` pins the two known violations by name, so a third
cannot appear quietly and neither can a silent repair.

The compiler was not changed. Splitting that allow-list makes the emit validator
reject a response that is already recorded in a cassette, which forces a retry
that has no recording to serve it, which stops `python run.py reproduce` for
every arm. More to the point, it would recompile the predicates, change
`predicate_sha256`, and rescore. Choosing a new number after watching the old one
fail is the thing this project refuses everywhere else, and an invariant is not
worth breaking that for. The defect is measured, named, bounded to two criteria,
and left in the run it damaged.

**The general shape.** A validator can be correct for the question it was written
to answer and silent on the question it appears to answer. This one asked "is this
code real?" and every reader, including the documentation and the prompt, read it
as "is this code allowed here?". Nothing in a passing test suite distinguishes
those two, because the union answers both with yes.

**Repaired in entry 29**, which is also where the numbers this entry describes
stop being the current ones. The paragraph above about leaving the defect in the
run it damaged was written when this entry was, and it was overtaken.

---

**Evidence.** `python scripts/grounding_audit.py --run runs/tierA`, which exits non-zero on any criterion using a broader-only code as an exact code, and `python -m pytest tests/test_grounding_audit.py -q`, which holds the ledger at zero and requires the audit to have scanned a non-empty set so a clean result cannot come from reading nothing.

## 26. The experiment I registered and then could not honestly run

**Found by** a reviewer counting how many entries in this changelog describe an
experiment that was removed. The answer was zero. Twenty-five entries, every one
of them a thing that was found and fixed, which is the shape a changelog takes
when it is written by whoever wanted the result.

**What was registered.** `docs/EVAL_PROTOCOL.md:142` lists four arms. B3 is B2
sampled three times at temperature 0.7 with a majority vote, any disagreement
resolved to INDETERMINATE. It is the standard self-consistency baseline and it
is the arm a reader would expect to be the strongest, because it is the one that
spends the most inference on each cell.

`docs/EVAL_PROTOCOL.md:65` said "B3 was not run" and stopped there. A registered
arm dropped with no reason is indistinguishable from an arm that was run and did
not say what its author wanted.

**Why it was dropped.** Not cost. The cassette key is a SHA-256 of the full
request, temperature included, and the store keeps exactly one response per key
in one file (`src/trialsieve/llm.py:213`). Three samples of an identical request
hash to an identical key. On replay all three draws return the same recorded
response, so the majority vote is unanimous every time, by construction, and B3
collapses into B2 wearing a hat. The number it produced would be an artifact of
the storage layout.

The alternatives were both worse. Keying on a per-draw counter makes the key
depend on call order, so a reordered loop replays the wrong response into the
wrong cell and nothing detects it. Running B3 live and nothing else live means
publishing one arm nobody outside this machine can reproduce, next to three that
anybody can, and letting the comparison table imply they were measured the same
way.

**What it cost.** The published comparison has no self-consistency arm, and the
claim "TrialSieve beats a per-cell model baseline" is therefore a claim about
single-sample B2 and not about the best baseline available at any price. That is
a real limit on the result and `results/RESULTS.md` states it as one.

**The general shape.** A record-replay harness is not neutral about what can be
measured. It makes anything deterministic cheap and anything that depends on
sampling variance either impossible or dishonest, and that constraint was in the
design from the first commit without anybody writing it down. The reproducibility
guarantee and the self-consistency arm were always mutually exclusive. Keeping
both on the page for as long as I did was the error, not choosing between them.

---

**Evidence.** amendment A5 in `docs/EVAL_PROTOCOL.md`, where the arm stays in the registered table at row B3 and unrun with the reason, and the absence of a B3 column anywhere in `results/RESULTS.md`. There is nothing to run here, and that is the entry: the evidence for a removed experiment is that no number from it was published.

## 27. The schema rejected the careful answer and accepted the dangerous one

**Found by** counting what did not compile. Twenty-two of the forty scored
criteria produced no predicate, and the run reported that as one number. Reading
the reasons, twenty-one name a blocker a person would agree with: a concept the
site has no code for, a criterion about willingness to consent, a Fibroscan
parameter this corpus does not carry. The twenty-second reads
`compiler failed: AgentError`.

`AgentError` appeared in no document. It sat in the same bucket as the principled
refusals, so every statement about how much of the non-coverage is deliberate was
counting a criterion that was lost by accident.

**What actually happened.** `NCT06989723-EXC-01` is *patients receiving insulin
therapy or diagnosed with type 1 diabetes mellitus*. Insulin has a code here.
Type 1 diabetes does not: the grounder returned it as BROADER_ONLY with no exact
code and the coarse SNOMED code 44054006, unqualified diabetes mellitus, in
`broader_codes`. The compiler made three attempts and the IR validator rejected
all three.

| attempt | `codes` | `broader_codes` | verdict |
|---|---|---|---|
| 1 | `[]` | `['44054006']` | rejected, `ir.py:103`: a query needs a non-empty list of codes |
| 2 | `['44054006']` | `['44054006']` | rejected, `ir.py:108`: a code cannot be both exact and broader |
| 3 | absent | `['44054006']` | rejected, `ir.py:103` again |

**Attempt 1 is the answer the design asks for.** `README.md` promises that a code
the site records more coarsely than the criterion needs goes in `broader_codes`,
where presence cannot settle the verdict and absence still can. The model sent
precisely that, and the schema refused it, because `ir.py:103` requires every
query to carry at least one exact code. The case the documentation describes at
length, a concept whose *only* evidence is a coarser code, is not representable
in the IR that documentation describes.

So the model was not failing to follow the schema. It followed it, then hedged,
then gave up, and the harness recorded that as an agent error.

**Why this is the same defect as entry 25.** The one shape the validator accepts
here is `codes: ['44054006']` with `broader_codes` left empty. That shape passes
`ir.py:103` because the list is non-empty, passes `ir.py:108` because the
intersection is empty, and passes the emit allow-list because the code came from
the grounder. It is also exactly the shape that turns an UNKNOWN into a MEETS,
and it is what the two criteria in entry 25 emitted. One coarse code produced
three failures: two criteria that use it as exact evidence and can never answer
INDETERMINATE, and one criterion lost entirely. A validator that rejects the
careful answer and accepts the dangerous one is not a weak validator. It is a
validator pointed the wrong way.

**The fix, and what was deliberately not fixed.** `results/RESULTS.md` now
separates the two kinds of non-compilation, prints the three rejections from the
trajectory, and says which criterion was lost and why.
`tests/test_not_compilable.py` pins the split so a future crash cannot be
absorbed into the refusal count.

The IR was not changed. Allowing a broader-only query means `ir.py:103` stops
requiring an exact code, which changes what every predicate in the corpus is
allowed to be, recompiles all of them, and moves every published number. That is
the same trade as entry 25 and it goes the same way: the defect is measured,
bounded and left in the run it damaged, rather than repaired after seeing the
score.

**The general shape.** A schema is a claim about what can be said. This one was
written from the cases that existed when it was written, all of which had an
exact code, and the constraint it grew, "at least one exact code", quietly
deleted the case the rest of the design was built around. Nothing failed loudly.
One criterion went missing and the error message named the model.

**Repaired in entry 29.** The IR accepts an empty `codes` list when
`broader_codes` carries the concept, `NCT06989723-EXC-01` compiles, and the count
of criteria lost to the validator is 0. What that recovered criterion then did to
the numbers is the reason entry 29 has the title it has.

---

**Evidence.** `python -m pytest tests/test_not_compilable.py -q`, which holds the split at 21 refusals and 0 lost to the validator, so a schema change that quietly turns a careful answer back into a validator loss fails there rather than in a table.

## 28. The coverage headline was the answer key's number, not the system's

**Found by** signing off the video narration. `scripts/make_video.py claims`
prints every spoken quantity and refuses to build until each has been read
against the run output. One of them was "twenty-four of the sixty-five criteria
compile to predicates", and checking it against
`runs/tierA/compiled/criteria_seed7.json` gave eighteen.

**What was wrong.** `coverage_denominators()` in `scripts/report.py` built its
numerator like this:

```python
n_checkable = sum(1 for c in CRITERIA if c.get("checkable"))
```

`checkable` is a field in `evaluation/gold/criteria_set.py`. It is a human
deciding, before any run, whether a structured record *could* settle a criterion
at all. It is the answer key. The report then printed **"The system expresses 24
criteria as predicates"**, which credits the run with every criterion the gold
annotation thought was answerable, including the ones the compiler refused and
the one it lost.

The compiler produced 18. Seven criteria the gold set calls checkable did not
compile: six because this site's vocabulary has no code for the concept, which is
the refusal policy working as designed, and one lost to the IR validator (entry
27). One criterion compiled that the gold set does not call checkable.

**What it cost.** Coverage against the registered denominator of 65 was published
as **37%**. The system's own figure is **27.7%**.

`docs/EVAL_PROTOCOL.md` registers, before any scored run, that coverage would land
at 30% to 40% of segmented criteria. 37% is inside that band. 27.7% is below it.
So the pre-registration did its job, the run missed the band it predicted, and the
report said it had hit it, because the numerator being compared against the
registered band was never a measurement of the thing the band was about.

Both numbers are now published side by side, with the seven-criterion gap itemised
by reason, and the narration reads the compiled count out of `results.json`
instead of speaking a remembered one.

**Why it survived this long.** Nothing was inconsistent. 24 is a real count of a
real field, 65 is the right denominator, 37% is the correct quotient, and every
test passed because every test checked the arithmetic. The defect is entirely in
the label: a sentence saying "the system expresses" over a number describing what
a person thought was expressible. A gate can verify a computation end to end and
still never ask what the inputs mean.

That is also why it was found by a narration gate rather than by the test suite.
Speaking a number out loud forces you to say what it is a number *of*, and this
one had no true sentence.

**Evidence.** `python -m pytest tests/test_coverage_numerator.py -q`, which requires the coverage numerator to come from `runs/tierA/compiled/` rather than from the gold set's `checkable` count. `criterion_coverage` in `results/results.json` is the figure it guards, and `docs/EVAL_PROTOCOL.md` is the band it now misses.

## 29. The fix that made every headline number worse

**Found by** entry 25, which is the entry above that names a defect and does not
repair it. `compiler.py` built the emit validator's allow-list as
`codes | broader_codes`. A set has no idea which slot a code arrived in, so a
parent code moved into `codes` sat inside the allow-list and validated. Entry 27
is the other half: `ir.py` required every query to carry at least one exact code,
so a concept this vocabulary only has a parent for had no legal shape at all, and
`NCT06989723-EXC-01` burned three retries discovering that.

**What changed.** Two small edits. `compiler.py` now builds `exact_allowed` and
`broader_allowed` separately, keeps `broader_only` as the difference, and rejects
an emission that puts one of those in `codes`, telling the model where the code
belongs and that leaving `codes` empty is allowed. `ir.py` now accepts an empty
`codes` list when `broader_codes` carries the concept, and refuses only a query
with no code in either slot.

**It needed no new model calls.** The trajectory for `NCT06717698-INC-07` shows
the model's first emission was `codes: []` with `broader_codes: ['44054006']`,
the shape the design asks for, and the old validator rejected it. That request
and its answer were already in the cassette store. With the validator fixed the
first attempt validates, so seed 7 recompiled from 193 recorded calls with zero
live ones. Seeds 8 and 9 replayed at 100% cassette hits as well.

**Then the numbers got worse.** Every headline moved the wrong way:

| | before | after entry 29 |
|---|---|---|
| silent error rate | 3.05% | 6.97% |
| false FAILS | 424 | 670 |
| false MEETS | 45 | 403 |
| patients wrongly ruled out | 182 | 318 |
| criteria compiled | 18 | 19 |

**Why.** The recovered criterion was the cause. `NCT06989723-EXC-01` reads
*Patients receiving insulin therapy or diagnosed with type 1 diabetes mellitus*,
and once the validator stopped losing it, it compiled and committed 358 wrong
MEETS. The criterion the validator had been rejecting was worse than the
abstention that replaced it.

**What that is worth knowing.** Coverage went up and the system got worse, in a
project whose whole argument is that coverage is not the metric. The defect was
real and the fix was right. The accident was that a validator bug had been doing
the work of a correctness check, and removing it exposed what sat underneath. A
coverage figure moving in the good direction is not evidence, which is the claim
this repository makes about other people's systems and now has a measurement of
its own to support.

**Kept, not reverted.** Reverting would have restored the numbers by restoring a
bug, and the next entry is what the exposed problem actually needed.

**Evidence.** `python scripts/grounding_audit.py --run runs/tierA` exits 0 and
reports 9 criteria grounding a broader-only code with 0 of them promoted.
`tests/test_grounding_audit.py` holds the ledger at zero and requires the audit
to have scanned a non-empty set, so a clean result cannot come from reading
nothing. `tests/test_not_compilable.py` holds the refusal-versus-exhaustion split
at 21 and 0.

## 30. Closed-world absence on a concept this vocabulary cannot express

**Found by** reading the three worst criteria in the run entry 29 produced, per
criterion rather than in aggregate. Two of the three had the same shape:

```json
{"domain": "condition", "codes": [], "broader_codes": ["44054006"],
 "absent_means": "false"}
```

`absent_means: "false"` says the record is trusted to be complete for this query,
so silence settles it. That is a claim about the record, and it is only available
when the query has a code for the concept in the first place. An empty `codes`
list means this site has no code for the thing being asked about. The record
could never have stored it. Its silence carries no information, and reading that
silence as absence commits FALSE on every patient whose chart simply never
mentions the parent.

`NCT06983054-INC-01` did that 358 times in the first published run, of that run's
424. `NCT06989723-INC-02` did it 246 times, of the 670 in the run entry 29
produced: it was lost to the validator before that and could not fail where
anyone could count it. The two are from different states and do not add.

**What changed.** `open_world_broader_only()` in `compiler.py` walks the emitted
expression and forces `absent_means` to `unknown` on any query with an empty
`codes` list, before the critic sees the predicate and before anything executes
it. Each repair is recorded on the trajectory as a `normalisation`, the event
kind this harness already uses for a field the model got slightly wrong, so the
difference between what the model emitted and what the engine ran is on the
record rather than in the engine's head.

It is a repair and not a rejection because the model has said something coherent
and got one boolean wrong, and a retry loop over one boolean spends a model call
to arrive at the only remaining answer.

**Measured, on the same 15,400 cells:**

| | published before entry 29 | after entry 29 | after this repair |
|---|---|---|---|
| silent error rate | 3.05% | 6.97% | **0.72%** |
| false FAILS | 424 | 670 | **66** |
| false MEETS | 45 | 403 | **45** |
| patients wrongly ruled out | 182 | 318 | **18** |
| cells answered | 24.12% | 27.72% | 19.15% |
| panel reduction | 60.35% | 75.32% | 46.15% |

Against the simple baseline, on the paired 400-cell sample the two arms share:
B2 is wrong on 43.75% of cells and wrongly rules out 10 of 30 screens,
TrialSieve is wrong on 1.00% and wrongly rules out 2.

**The trade is real and is not hidden.** Cells answered fell from 24.12% to
19.15%, and unnecessary abstention rose from 210 to 618. The system now declines
to answer 618 cells a perfect system would have answered. It also stopped wrongly
excluding 164 patients. `docs/SCORECARD.md` puts both columns next to each other
rather than quoting the half that flatters.

**The sensitivity arm stopped moving, which is the interesting part.**
`run_arms --absent-means-override unknown` discards every closed-world decision
the compiler made. It used to remove 358 silent errors, taking 469 down to 111,
and that gap was the headline of the sensitivity section: most of the system's
error was the model asserting a closed world it was not entitled to. The two arms
now report **111 silent errors each**. The targeted repair took all of it, and it
did so while answering more cells than the blanket override does: 19.15% against
18.44%. What they still share is the error that has nothing to do with absence,
and a gap re-opening in future means a new closed-world assertion started
committing.

**Evidence.** `tests/test_open_world_broader.py` holds eight assertions,
including one that walks every committed predicate across all three seeds and
fails if any pairs an empty `codes` list with closed-world absence, and one that
runs an empty chart through the evaluator rather than arguing about it.
`tests/test_sensitivity_section.py` pins the 111-against-111 equality with the
reason it now holds.

## 31. A claim of zero dependencies that nothing parsed

**Found by** reading the rules again rather than the code. The scoring row for
reproducibility names an **exact dependency lock**. This repository had none.
`pyproject.toml` said `dependencies = []`, the dev extra said `pytest>=7.4`,
which is a range and not a pin, and `edge_tts` and `playwright` were imported by
the video build while appearing in no manifest at all. Two third-party packages
were in use and undeclared.

**What was actually wrong.** `dependencies = []` is the load-bearing claim in
`REPRODUCE.md`: a judge clones and runs `python run.py reproduce` with no install
step. The claim was true and nothing checked it. One new import in one script
would have ended it silently, and the failure would surface on a stranger's
machine as an ImportError in the middle of a reproduction.

**What changed.** `scripts/lockfile.py` does three things. `--write` walks the
transitive closure of every declared group through installed package metadata and
emits `requirements-lock.txt` with 23 exact pins and the interpreter version.
`--check` reports drift and exits 4 rather than 1, so a version difference is
distinguishable from a crash; a judge on another machine is expected to drift,
and the point is that the difference is named rather than forbidden. `--imports`
parses every module the reproduction path touches and fails on any import that is
neither in `sys.stdlib_module_names` nor this project's own. It runs inside
`python run.py check`, and `run.py environment` now records lock drift beside the
run.

**It caught its own first version.** The first walk reported `score`, `plainview`
and `criteria_set` as third-party. All three are this project's own files,
imported bare because their directory is placed on `sys.path` at runtime.
`tests/test_dependency_surface.py` now carries that as a negative control
alongside a positive one that plants `import numpy` and requires the check to
find it.

**Then this entry's own evidence line went stale.** It said 51 modules while the
checker walked 53, because two scripts joined the reproduction path afterwards
and nothing compared the sentence to the number. The defect this entry is about
is a claim that no gate parses, and the entry describing it had become one.
`tests/test_dependency_surface.py` now reads every module count stated in this
file and fails if any of them disagrees with what the checker walks, so the
prose and the command cannot drift apart again.

**Evidence.** `python scripts/lockfile.py --imports` reports 54 modules parsed
and zero third-party imports. `requirements-lock.txt` carries 23 pins under
`python 3.14.2 (cpython)`, and seven tests hold the lock exact, complete against
what pyproject declares, interpreter-stamped, and matched to the count this file
states.

## 32. A failure report that named a file two directories share

**Found by** spending an hour reading the wrong agent's log. `verify.py
trajectories` reported `NCT06983054-INC-01-seed7.jsonl` as having no cassette. I
opened `runs/tierA/trajectories/compiler/NCT06983054-INC-01-seed7.jsonl`, checked
every cassette key in it by hand, found all five present in the store, and could
not reconcile the report with the tree.

The file it meant was
`runs/tierA/trajectories/critic/NCT06983054-INC-01-seed7.jsonl`. The compiler and
the critic each write one trajectory per criterion per seed, under identical
filenames, into sibling directories. The check reported `p.name`.

**What changed.** The report prints the path relative to the trajectory root, so
every entry reads `critic/...` or `compiler/...`. Four call sites, one helper.

**Why it is in here.** It is the smallest entry in this changelog and it cost
more time than several larger ones. A check that finds a real defect and then
describes it ambiguously spends its finding on a wild goose chase, and the person
paying is the one who trusted the check. The failure was correct. The report was
not usable.

**Evidence.** `python scripts/verify.py trajectories --run runs/tierA` prints
paths with their agent directory. It currently reports 1,072 model calls all
resolving to a byte-identical cassette, so the fix shows in the format of a
passing run rather than only under failure.

## 33. The repair that could not reach half the grammar, and the test that agreed with it

**Found by** an independent audit of the code changed in entries 29 to 32, asked
only to look for a check that cannot fail.

**What was wrong.** `open_world_broader_only()` walked the emitted expression by
enumerating the keys it expected to find a query under: `args`, `arg`, and a
`value` holding a `count`. That is the grammar as far as `exists` goes. It is not
the grammar. A `compare` holds its operands at `left` and `right`, and neither
was ever visited, so a count taken over a broader-only query kept
`absent_means: "false"` straight through the repair.

`runs/tierA/compiled/criteria_seed8.json` carried exactly that. Its
`NCT06717698-INC-07` is an `or` over a `compare` between two counts, both over
`{"codes": [], "broader_codes": ["44054006"], "absent_means": "false"}`. With no
exact code the count matches nothing on any chart, and closed-world absence turns
that into a definite `0.0` rather than "the record does not say", so the
comparison was a settled `False` for all 385 patients on a question the record
cannot answer.

**And the test that was supposed to catch it was written from the walker's
output.** `test_the_walk_reaches_every_nesting_the_grammar_allows` builds a tree
holding two broader-only closed-world queries and asserted that **one** was
repaired. One is what the broken walker produced. The invariant test over the
shipped predicates was worse: it ran the same `open_world_broader_only` over a
copy of each committed predicate and reported what came back, so the audit
inherited the blind spot of the thing it audited and reported clean while two
violations sat in a committed file.

**What changed.** The walk no longer enumerates keys. It descends into every
value of every dict and list and repairs anything shaped like a query, which
cannot be defeated by a node shape nobody thought of. The nesting test now
asserts two and names the operand it missed. The invariant test reads the parsed
JSON itself and knows nothing about the repair function, it refuses to pass on an
empty scan, and a positive control plants the violation directly in a `compare`
operand and requires the audit to see it.

**It needed no new model calls.** Seeds 8 and 9 recompiled from 201 and 210
recorded calls at 100% cassette hits. One predicate changed: two `absent_means`
fields in `NCT06717698-INC-07` on seed 8.

**Evidence.** `python -m pytest tests/test_open_world_broader.py` is 9 assertions
including the positive control. `python run.py verify` still matches every one of
the 1,072 model calls to a byte-identical cassette, because the repair happens
after the model has spoken and changes no prompt.

## 34. A reproduction that only reproduced on the machine that had the leftovers

**Found by** cloning this repository into an empty directory and running the
command the README gives a reader, which is the one thing the reproducibility
claim rests on and the one thing that had never been done.

**What happened.** `python run.py reproduce` **failed**, twice over.

It stopped first at `scripts/linkcheck.py`: the changelog cites
`runs/probe-weak/probe.json` and `runs/probe-before/probe.json` as the evidence
for the weak-model comparison, and `.gitignore` excluded both. Locally the files
exist, so the check passed on the machine where the claim was written and nowhere
else.

Past that, `python run.py diff` printed **DIFFERENT**. `runs/tierA/cells/` is 46
MB and is not committed, and `reproduce` regenerated only the groups it happened
to name: seed 7, the open-world arm, and the per-cell baseline. The report
publishes eight. On a clean clone the other five simply did not exist, so the
regenerated `results.json` was missing `k0_seed8`, `k0_seed9`, the whole
degradation curve and its three groups, and the byte comparison against
`results/published/` failed on the first read.

**The second failure was hiding a third.** Because nothing regenerated those
groups, the committed cells for them were whatever had last been written, and
they had last been written before entry 30. The published report showed seed 8 at
24.19% coverage and 3.18% silent error next to seed 7 at 19.15% and 0.72%, and a
reader would have concluded the system is wildly seed-unstable. It is not. Those
cells were computed from predicates the repository had already replaced. The
degradation curve was the same story: it reported false exclusions climbing from
18 to 206 as the record was damaged, which was an artefact of the same staleness.

**And a third failure behind those two.** With the five groups restored, the
clean clone still came out missing `b2_10p`, the per-cell baseline that the
headline comparison is against. The step that replays it is guarded, correctly,
so that a checkout without the recording reproduces everything else rather than
stopping. The guard asked the wrong question: it looked for
`cells/cells_B2_*.jsonl`, a previous run's **output**, which `.gitignore`
excludes. On any machine but this one it was false, so the arm never ran. It now
asks whether the recording exists, by looking at the committed
`trajectories/baseline-b2/`.

**What changed.** `run.py reproduce` now replays the compile for all three seeds,
runs the free arms for all three, and runs the degradation curve at 10, 20 and 40
percent, so every group the report publishes is regenerated by the command a
judge runs. The baseline guard reads a committed input instead of an ignored
output. The two probe result files are tracked. The corrected numbers are
published.

**What the corrected numbers say.** All three seeds now agree: silent error
0.72%, 0.73% and 0.73%, against 0.72%, 3.18% and 3.18% before. The degradation
curve is flat where it should be, with false exclusions at 18, 19, 17 and 31
across 0 to 40 percent damage rather than 18 to 206.

| | published before | reports now |
|---|---|---|
| k0_seed8 silent error | 3.18% | **0.73%** |
| k0_seed9 silent error | 3.18% | **0.73%** |
| false exclusions at 40% record damage | 206 | **31** |
| `run.py reproduce` on a clean clone | **fails at linkcheck, then DIFFERENT** | **IDENTICAL** |

**Evidence.** `git clone` into an empty directory, then `python run.py reproduce`,
which is what produced the failure and now prints IDENTICAL in about two minutes.
The reproduction takes 131s rather than 99s because it now regenerates five more
groups.


---

## 35. A video whose every card was the wrong length

**Found by** watching the first cut with the sound on. Six sections, each
rendered to a length somebody chose, each narrated over afterwards. Four of the
six ended while the line spoken over them was still going, and the seams were
audible: a sentence about coverage finished over a card about reproduction.

**What was wrong, and it was not the lengths.** The order was. Frames were
composed first and narration was fitted to them, so every mismatch could only be
fixed by re-rendering the frames, which meant it mostly was not fixed. The
renderer paged documents into fixed screens and screenshotted them through a
browser, so what a viewer saw was a scrolling markdown file. There was no card
that showed one run from protocol text to the document a coordinator opens, which
is the one thing the brief's video section asks for by name.

**What changed.** The film is sixteen cards built as React components and
rendered by Remotion, and the order is inverted. Each line is synthesised first,
its wav measured, and the card's frame count computed from that measurement:
`film/scripts/narrate.py` writes `film/src/timings.json` and `film/src/Film.tsx`
reads the durations out of it. No card's length is chosen.

The same measurement decides when things appear. The renderer records where each
spoken sentence starts inside its beat, and `film/src/cues.ts` is how a card sits
on a word, so a figure lands as the voice says it rather than on a keyframe
somebody picked by eye. Reword a line and every element on that card moves with
it on the next render. Delete a sentence and the card that referred to it fails
the type check rather than drifting silently on screen: that guard fired three
times while the script was being cut to length, on cards 9, 14 and 15.

Nothing on screen is drawn from a value typed into it. `film/scripts/extract.py`
writes `film/src/data.json` from `results/results.json` and the scored cells, so the
15,400-cell grid is 15,400 real verdicts and the four-arm comparison is the four
arms. `film/scripts/check_grid.py` re-counts what the grids draw, with the
`silent_error` rule from `evaluation/score.py` transcribed into TypeScript and
compared line for line against a copy in the checker, and requires the totals to
equal the published ones. `film/scripts/capture.py` re-runs the commands whose
output is shown and redacts them, so a card showing a passing gate cannot go on
showing it after the gate stops passing.

The voice is mine rather than a synthetic one. The opening greeting is the
reference recording itself, cut at the word boundary after the name and levelled
to the clone; everything after it is cloned from that same recording, offline, at
a fixed seed. A clone generates a name, it does not replay it, and the name is
the one word that has to be exactly right.

**What it cost.** Two third-party packages, and they went the right way. The old
build needed `edge-tts` and `playwright`; the new one needs Node, which lives in
`film/` and is not reachable from anything in `src/`, `scripts/` or `run.py`. So
`pyproject.toml` now declares exactly one optional dependency, `pytest`, and
`scripts/lockfile.py --imports` still reports zero third-party imports across 53
modules on the reproduction path.

| | before | now |
|---|---|---|
| cards whose length was measured | 0 of 6 | **16 of 16** |
| elements whose entry frame was measured | 0 | **every one** |
| lines that overrun the card spoken over them | 4 of 6 | **0 of 16** |
| a card showing one run from protocol text to worklist | none | **cards 7, 8 and 9** |
| third-party Python packages the repository declares | 3 | **1** |
| length against the five minute limit | 4:54 | **4:58** |

**Evidence.** `cd film && python scripts/narrate.py --check` measures every wav
against the card holding it. `python scripts/check_grid.py` re-counts the grids.
`python scripts/capture.py --check` re-runs the terminals. `npx tsc --noEmit`
fails on a card that names a sentence the script no longer has. `python
scripts/make_video.py check` measures the committed mp4.

---

## 36. A home directory in eighty-two places nobody would have read

**Found by** an independent audit run against the competition's ground rules
rather than against the code, asked only whether anything private had reached the
tree. It found one file. There were fifty-seven.

**What was wrong.** Rule 08 says to keep credentials and private information out
of the submission, and `tests/test_no_credentials.py` scanned for credentials.
The thing that had leaked was not a credential. During recording, the local model
shim died and returned an HTTP 502 whose message quoted the absolute path of the
CLI binary that had just exited. The recorder wrote that error into the
trajectory, faithfully, as it is supposed to. The path ran through a home
directory, so it named a person.

`scripts/agent_traces.py` already redacts home directories, and
`tests/test_agent_traces.py` already enforces it, but only over
`docs/agent-traces/`, because a coding-agent transcript is obviously a shell
session on a laptop. The trajectories the system writes about its own runs are a
different artifact and nobody had thought of them as transcripts. Eighty-two
copies, across the Checker B trajectories, both vocabulary probes and the
segmenter.

**What changed.** The paths are collapsed to `~`, which is the form the exported
markdown already carried, and `tests/test_no_private_paths.py` scans **every
tracked text file** rather than a directory somebody remembered to list. That
distinction is the whole fix: a scan over a named directory would have passed on
this repository on the day the leak went in.

The first redaction wrote `C:\...\Users\...\` and the new scanner flagged its own
redaction, because a marker made of dots still matches a pattern that allows dots
in a directory name. That is recorded here rather than quietly corrected: a
redaction that a scanner cannot distinguish from the thing it redacts is not a
redaction.

| | before | now |
|---|---|---|
| tracked files carrying a home directory | 57 | **0** |
| occurrences | 82 | **0** |
| files the private-information scan covers | `docs/agent-traces/` | **every tracked text file** |

**Evidence.** `python -m pytest tests/test_no_private_paths.py -q`. It carries a
positive control that plants each shape and requires the pattern to find it, so a
regex broken by an editor fails there rather than in front of a judge.

## 37. The film counted to thirty-four while the voice said thirty-six

**Found by** reading `film/src/data.json` before a render, for an unrelated
reason. Nothing had failed. The claims gate passed, the grid recount passed,
`npx tsc --noEmit` passed, and the film would have rendered without complaint.

**What was wrong.** Two entries were added to this changelog. The narration is
generated through this repository's own figure table, so the spoken line picked
the new count up immediately and said "thirty-six". The film's data file is
generated too, by `film/scripts/extract.py`, but it is generated **once and then
committed**, and nobody re-ran it. The card that counts up on screen was reading
its own stale copy, so it would have animated to thirty-four under a voice saying
thirty-six.

Every gate the film has was pointed at something else. `film/scripts/check_grid.py` re-counts
the cells the grids draw. `film/scripts/narrate.py --check` proves each line fits its card.
`film/scripts/capture.py --check` re-runs the captured commands. `scripts/make_video.py claims` binds
every spoken quantity to the repository. Not one of them looked at the file that
sits between the repository and the screen, because it was output, and output was
assumed to be current.

**What changed.** `film/scripts/extract.py --check` re-derives the whole file and exits
non-zero if the committed copy differs by a byte. It is the fifth check in
`film/README.md`, and it fails loudly on the exact state this repository was in
ten minutes before it was written. The generator no longer writes a machine
absolute path into its output either, so the file is a function of the run and
nothing else.

| | before | now |
|---|---|---|
| entries the on-screen counter reaches | 34 | **36** |
| entries the narration says | 36 | 36 |
| checks that would catch the two disagreeing | 0 | **1** |

**What re-rendering measured, as a side effect.** All sixteen narration sections
were re-cut so the changed line could be replaced. Fifteen came back to the same
duration to the millisecond, and the only length that moved was the section whose
words had changed. Twelve of sixteen came back byte for byte; four matched in
length but not in bytes. So the fixed seed pins what is said and how long it
takes, and it does not pin the last bit of every sample. That is stated in
`film/README.md` rather than left as an implied "deterministic".

**Evidence.** `python film/scripts/extract.py --check`, which prints the path it
disagrees with and the command that fixes it.

## 38. The reproduction guide's own command wrote a home directory into a tracked file

**Found by** doing what the guide tells a reader to do, in the place a reader
would do it. `git clone` into a temporary directory under a home directory, then
`python run.py reproduce`. It failed at the test gate. In the tree it was written
in it had never failed once, and it could not have: this checkout lives on `D:`
and the leak needs a home directory to exist.

**What was wrong.** Two generated files record an absolute path.

`results/environment.json` stored the working directory. The field's stated job
is to give a differing number somewhere to point, and it never did that: the
Python version, the platform, the commit and the lock drift do. What it did do
was write the account name of whoever ran the command into a tracked file.

`results/contamination.json` stores a Python traceback when a counterfactual
cannot compile, deliberately, because `KeyError: 'text'` names a key and not the
line that wanted it. Every frame in a traceback carries the absolute path of its
file. Seven of them, in the artifact a judge regenerates.

Entry 36 redacted 82 of these out of the trajectories. It fixed the files and not
the writers, so the next generated artifact carrying an error string leaked
again, which is what happened here.

**What changed.** `src/trialsieve/redact.py` rewrites a path inside the
repository as relative to the repository, and collapses anything still absolute
to `~`. The traceback goes through it where it is written. The working directory
is not recorded at all, in the run or in `results/published/`.

The scan is the part that matters. `tests/test_no_private_paths.py` looks for a
home directory, which is the shape that is actually private, and that is exactly
why it could not find this: on this machine the leak reads `D:\trialsieve`.
`tests/test_generated_files_name_no_machine.py` rejects **any** absolute path in
a file this repository generates and commits, which catches `D:\trialsieve` too,
because the harmless-looking string is the carrier. The same rule is what lets
two machines write the same bytes.

| | before | now |
|---|---|---|
| generated files carrying an absolute path | 2 | **0** |
| occurrences a judge's clone would produce | 8 | **0** |
| the scan's result on the machine that wrote the leak | pass | **fail, until fixed** |
| `python run.py reproduce` from a clone under a home directory | fails at the gate | **OK in 145.7s, IDENTICAL** |

**Two things this got wrong on the way, kept here because they are the same
mistake in miniature.** The new scan's positive control spelled out the shapes it
plants, so it became a tracked file containing a home directory and the older
scanner failed on it: a scanner flagging another scanner's test data. The shapes
are assembled from parts now. And the scan was first parametrised over the files
each glob matched, which made the number of collected tests a function of which
generated artifacts happened to exist, so a clean clone collected one fewer test
than the tree that wrote it and the count in `REPRODUCE.md` was wrong on a
machine nobody could see. It is parametrised over the patterns instead.

**Evidence.** `python -m pytest tests/test_generated_files_name_no_machine.py -q`,
which carries a positive control in every shape the writers produce. The end to
end check is the one that found it: clone into a directory under a home
directory and run `python run.py reproduce`.

## 39. A one-directional error metric, and a skip that called its blindness a good result

**Found by** four independent reviewers reading this submission cold, briefed
separately, none shown the others' findings. Two of the three defects below came
from the one asked to argue the case against the project.

**What was wrong.** `scripts/report.py` picks the compiled criterion whose
closed-world assertion costs the most, to name it rather than leave "most of the
error comes from closed-world assertions" as an aggregate a reader cannot check.
It counted one direction:

```python
if r.get("TS") == "FAILS" and r.get("gold") != "FAILS":
    wrong[cid] += 1
```

A criterion that over-*accepts* scores zero there. The worst one in this run does
exactly that: `NCT06989723-INC-05` makes 0 wrong FAILS and **29 wrong MEETS**, of
the run's 45. So the search returned nothing, and the guard test skipped with

> no closed-world assertion in this run, which is the good case

which was false. Three compiled queries set `absent_means` to `false`. It was the
only skip in the suite, and it was reporting a blind spot as a clean result. This
repository's own definition of a silent error, in `evaluation/score.py`, is a
committed verdict that is wrong in either direction, and the metric that hunts for
the worst one did not use it.

**Two more from the same pass.** `tests/test_perturb.py` carried
`assert got is None or ... or True`, which cannot fail, in the file whose subject
is a check that reported its own malformed input as a signal. And
`docs/SCORECARD.md` and `docs/COST.md` both wrote "patients" where the count was
screens: ten patients read against three trials each is 30 screens, and the
README two files away sells exactly that distinction.

**What changed.** The metric counts any committed verdict that disagrees with gold
and reports the two directions separately. The guard test counts the compiled
closed-world queries first: if there are none, `None` is the good case and it says
so; if there are some, `None` means the search cannot see them and the test fails.
The perturbation assertion is a real one now, with a case that has to be refused
and a case that has to be perturbed. The units say screens.

**And the conclusion it exposed.** With the metric fixed, the section's closing
sentence read *"Almost all of the system's error is the model deciding that a
silent record is an answer"* directly under a row saying that ignoring every
closed-world decision removes **0 of 111** silent errors. That sentence was true
of the run before entries 29 and 30 and is contradicted by the table above it now.
It says what the measurement says instead: the assertions left in this run are not
where the error is, because they sit inside disjunctions where another term
settles the verdict. The named criterion is kept, relabelled as the correlation it
is rather than the cause it was presented as.

| | before | now |
|---|---|---|
| error directions the offender search counted | 1 | **2** |
| skips in the test suite | 1, on a false reason | **0** |
| assertions that cannot fail | 1 | **0** |
| the section's conclusion against its own table | contradicted it | **states it** |

**Evidence.** `python -m pytest tests/test_sensitivity_section.py tests/test_perturb.py -q`.
The first now counts the compiled closed-world queries itself and fails rather than
skips if the search cannot find them, so the blindness cannot come back as a pass.

## 40. The film showed a real SNOMED code that this run never compiled

**Found by** an independent reviewer reading the film's frames, briefed on the
deliverables rather than the code.

**What was wrong.** The card that carries the whole argument of the film shows
the compiled predicate for *"Adults with previously diagnosed T2DM"*, so that a
viewer can watch one JSON field flip from `"false"` to `"unknown"` and see what it
cost. It showed:

```json
"concept": "Type 2 diabetes mellitus",
"codes": [],
"broader_codes": ["73211009"],
```

The compiler produced `44054006`. `73211009` is diabetes mellitus, the parent
concept. Both are valid SNOMED codes and they are indistinguishable by reading,
which is the exact reason this system routes a concept it cannot map to a human
instead of choosing. A search of the tracked tree found `73211009` in one file:
the card itself. Nothing could contradict it, so nothing did.

**The second one, on the reproduction card.** Its terminal read `270 passed, 1
skipped` and `OK (reproduce in 285.6s)`. The suite is 302 tests with no skips, and
removing that skip is entry 39 above; the run takes 144 seconds. Four more of its
seven lines were summaries composed in the TSX that no command had printed, under
a comment claiming the card could not go on showing a pass after the command
stopped passing.

**Why every gate missed both.** `film/scripts/extract.py --check` (entry 37)
compares `film/src/data.json` against the repository, and both defects were string
literals in TSX rather than data. `film/scripts/capture.py --check` re-runs the
fast commands, and the stale capture was the slow one it skips. `npx tsc --noEmit`
type-checks a string. The film rendered, the suite passed, and
`python run.py reproduce` printed IDENTICAL, because none of them looks at what a
card says.

**What changed.** The code is `44054006`. The terminal is five verbatim lines of
the current capture. Two tests were added, and each was run against the defect it
was written for before being kept:

- `tests/test_film_terminals_are_captured.py` reads every string literal out of
  the three terminal cards and fails unless each line occurs in the capture that
  card quotes. It refuses to pass on a card with no literals, and it fails if a
  fourth `<Terminal>` is added to the film without being mapped to a capture.
- `tests/test_film_codes_are_real.py` pulls every SNOMED and LOINC code out of
  `film/src` and requires it to appear in `runs/tierA/compiled/criteria_seed7.json`.
  Being a well-formed code is not enough, because `73211009` is one.

**A third gate, from looking for the same shape one layer down.** The two defects
above are a card saying something the repository does not. The voice can do it
too, and `film/scripts/narrate.py --check` cannot see it: it re-measures each wav
and compares the duration and digest against the file those measurements were
written to, so it compares audio against its own record. Change a spoken figure in
`docs/VIDEO.md`, re-render the film without re-running the speech model, and every
check stays green while the voice says the old number over the new card.
`tests/test_narration_matches_the_script.py` resolves the script through the same
`scripts/_video_figures.py` the narration used and requires it to be
sentence-for-sentence what `film/src/timings.json` records as spoken. It caught
this entry's own edit: adding entry 40 moved the spoken count from thirty-nine to
forty and the test failed on section 12 until the wav was re-rendered.

| | before | now |
|---|---|---|
| terminology codes on screen that the run compiled | 2 of 3 | **3 of 3** |
| terminal lines on screen the command printed | 12 of 16 | **16 of 16** |
| gates that read what a card says | 0 | **2** |
| gates that read what the voice says | 0 | **1** |

**Evidence.** `python -m pytest tests/test_film_codes_are_real.py tests/test_film_terminals_are_captured.py tests/test_narration_matches_the_script.py -q`,
28 tests. Planting `73211009` back into the card fails the first with *"shows
terminology code 73211009 and it does not appear in
runs/tierA/compiled/criteria_seed7.json"*, and planting `270 passed, 1 skipped`
back into the second card fails the other with *"shows 1 line(s) that
reproduce.txt, prove.txt does not contain"*.

## 41. The one sentence in the film that took a rate over the wrong denominator

**Found by** the same reviewer as entry 40, reading the resolved transcript
against `results/results.json` rather than reading it for sense.

**What was wrong.** Section 10 of the narration, the comparison a viewer is meant
to carry away, said:

> TrialSieve answers twenty-one point eight percent of cells and is wrong on one
> percent **of those**. The per-cell baseline answers sixty-eight percent and is
> wrong on forty-three point eight percent.

"Of those" reads as the cells the arm answered. Both rates are over all of them.
On the paired sample in `results/results.json`, group `b2_10p`:

| | cells | committed | silent errors | wrong, of all cells | wrong, of the ones it answered |
|---|---|---|---|---|---|
| TrialSieve | 400 | 87 | 4 | **1.0%** | 4.6% |
| B2 | 400 | 272 | 175 | **43.8%** | 64.3% |

The spoken figures are the left column and the sentence points at the right one.
It flatters this project by a factor of 4.6 and the baseline by 1.5, so it
flatters the comparison, which is the direction that should have made it obvious.

**What makes it worse than a slip.** Every written version of the same comparison
names the denominator. `README.md` prints both. `docs/SCORECARD.md` says "wrong on
43.75% of *all* cells", with the emphasis already there. The distinction is
this project's own argument, since an arm that answers less can only be compared
fairly if the rates share a denominator, and the one place it was dropped is the
one a reviewer hears rather than reads.

**Why the claims gate signed it.** `scripts/make_video.py claims` requires every
spoken quantity to be read against the run and signed. Both numbers in that
sentence are real numbers from `results.json`, so the sentence was signed. A gate
that checks each figure cannot see a relation asserted between two of them. That
is the same shape as entry 24, where a probe scored nine of nine because the
defect that mattered was never planted: the check was sound and the thing it
checked was not the thing at risk.

**What changed.** The denominator is spoken, and it is derived rather than typed.
`_paired_cells()` in `scripts/_video_figures.py` reads `n_cells` off the paired
group, so the sentence now says "wrong on one percent of all four hundred" and the
four hundred cannot drift from the run that produced the one percent. The old
sentence's signature was removed rather than edited, so the corrected sentence had
to be read against the run and signed on its own.

| | before | now |
|---|---|---|
| denominator the spoken rate names | the answered cells, which is wrong | **all cells, from `n_cells`** |
| the factor the sentence flattered by | 4.6 | **1** |
| spoken figures typed rather than derived | 1 | **0** |

**Evidence.** `python scripts/make_video.py claims` reports 27 sentences stating a
quantity, all signed and none unchecked, and prints `paired_cells = four hundred`
beside `ts_error_pct = one percent`, both out of the same group in
`results/results.json`.

## 42. The gate that decides what needs checking could not read half the numbers

**Found by** rewriting the narration for a listener who is not an engineer, which
put two money figures into it and made the gate say nothing at all.

**What was wrong.** `scripts/make_video.py claims` is the rule that a spoken
quantity must be read against the run and signed by a person before the film can
be built. It finds quantities by matching number words against `WORD_NUM`. That
table went one, two, three, up to twelve, then jumped to thirty, forty, fifty,
sixty, eighty, hundred, thousand.

Missing: **thirteen through nineteen, twenty, seventy and ninety.** A sentence
whose only quantity used one of those words was not a claim as far as the gate was
concerned, so it was never listed, never signed, and never read against anything.

**What it hid.** Three sentences in the current narration, measured by running the
old table and the new one over the same script:

| sentence | why it was invisible |
|---|---|
| "Compiling cost thirteen cents, once." | `thirteen` |
| "The per-call baseline pays twenty-two dollars nineteen for this panel, and again next month." | `twenty`, `nineteen` |
| "Only nineteen of the sixty-five rules compile, under the band I registered." | `nineteen`, and `sixty-five` is one token so it never equalled `sixty` |

The third is the one that matters. That sentence is the film admitting it missed
the coverage band registered before the run, which is the most load-bearing
honest claim in five minutes of film, and the gate built to make a person check
every spoken figure had never once put it in front of anyone.

**Why this is the same defect as three others here.** Entry 24 was a probe that
scored nine of nine because the defect that mattered was never planted. Entry 41
was a claims gate that signed a sentence because both its numbers were real,
without seeing the false relation asserted between them. This is the third shape:
a gate whose *input filter* is narrower than its subject, so the thing it never
looks at reports as clean rather than as unmeasured. In all three the check was
sound and the population it ran on was wrong.

**What changed.** `WORD_NUM` covers zero through twenty and every ten to ninety.
The three sentences appeared in the unsigned list on the next run and were read
against `docs/COST.md` and `results/results.json` and signed.

**Then the same defect one level down.** With the table completed, the gate still
said nothing about *"Each of the forty-four entries names what I measured"*. It
has two branches: a regular expression, and a fallback that compares tokens. The
regular expression branch is guarded on the sentence containing a digit, which a
narration spelled out for a speech synthesiser never does, so it never fires at
all. Everything therefore fell to the fallback, which split on whitespace, so
`forty-four` was one token that equalled no entry in the table. Every compound
number the film speaks (forty-four, twenty-two, sixty-five, twenty-one) went
through that gap, and completing the word list did not close it because the words
were never being looked up separately. The fallback now splits on anything that is
not a letter.

| | before | now |
|---|---|---|
| number words the gate can read | 19 | **31** |
| spoken quantities it offers for signature | 25 | **31** |
| load-bearing claims never offered to a human | 1 | **0** |
| compound figures the fallback could match | 0 | **all of them** |

**Evidence.** `python scripts/make_video.py claims` reports 31 sentences stating a
quantity, none unchecked. Running the old table and the old whitespace split over
the same script finds 25.

## 43. One event with two causes, counted as one thing and labelled with a sentinel

**Found by** an independent reviewer reading `runs/tierA/trajectories/index.md`
and then parsing the event files behind it, rather than taking the summary row.

**What was wrong.** The index published this:

> | retries after a schema rejection | 8 |

Three were. The other five followed a **confirmed counterexample**: the critic had
attacked a compiled predicate with a patient it should get wrong, the harness had
run the attack and seen it fail, and the compiler was being asked for a different
predicate. That is not another try at the same reply. `scripts/trajectories.py`
counted the bare `retry` event kind with no filter on what preceded it, so the two
became one number under the wrong name.

**And the sentinel.** Those five were logged by `scripts/compile_protocol.py` as
`traj.retry(99, note)`. 99 was a placeholder meaning "not part of the retry
budget", uncommented. It rendered in five published trajectories as:

> ### 11. retry (attempt 99), verbatim feedback returned to the model:

`SUBMISSION.md` told a reader that retries are "numbered, with the budget that
bounds them". 99 is outside any budget and is not a number a reader can act on. A
deliverable whose whole purpose is to be followed by a stranger was asking that
stranger to interpret an internal placeholder.

**What changed.** `Trajectory.retry` takes a `cause` and stores it. A
counterexample-driven recompile carries `attempt=None` and renders as
`retry after a confirmed counterexample (recompiled)`; a schema rejection renders
as `retry after a schema rejection (attempt 1)`. The index is two rows. The
trajectories were re-recorded from cassettes, so the change is visible in the
published files rather than only in the code.

**Two smaller things from the same reading.** Sixteen trajectories printed a raw
float latency, `70.58855390548706s`, where every compiler trajectory printed
`90.994s`, because one render path rounded and the other did not; both round now.
And `REPRODUCE.md` listed "the tree is dirty" as a cause of a failed diff without
saying that `run.py reproduce` is what dirties it, by rewriting wall-clock
readings into three compiled files and `docs/COST.md`. None of those bytes is a
published number, so `IDENTICAL` was never at risk, but a reader running it twice
saw `git_dirty` go true and had no way to know it was the command's doing.

| | before | now |
|---|---|---|
| retries reported under the wrong cause | 5 of 8 | **0 of 8** |
| sentinel values in published trajectories | 5 | **0** |
| trajectories printing an unrounded latency | 16 | **0** |

**Evidence.** `python scripts/trajectories.py --run runs/tierA` then
`grep -rn "attempt 99" runs/` returns nothing, and `index.md` reads
`retries after a schema rejection | 3` beside
`recompiles after a confirmed counterexample | 5`.

## 44. The claim that turned one hundred and ninety answers into two

**Found by** the same reviewer, checking a sentence that appeared in five
documents against the worklist it describes.

**What was wrong.** Five places said a version of this:

> The 190 that remain open contain **two distinct questions**, and 188 of them are
> open on the same one, so it is answered once and they resolve together. That is
> 1,155 cell judgements reduced to two things a person has to find out.

`docs/sample_worklist.json` says the shared item is `NCT06983054-INC-02`, which
resolves to *no observation with code 4548-4 in the record*: no HbA1c on file. One
missing measurement, shared by 188 patients. **It is one question type, not one
answer.** Ordering that lab returns 188 values, one per patient, and each of them
decides that patient's verdict separately. What the grouping collapses is the
search, not the answers, and "two things a person has to find out" claims the
second.

This one was uncomfortable because it is the project's most quotable line, it was
in the README, the scorecard, the cost page, the worklist itself and the film, and
the defensible version was already sitting in the worklist twenty lines below the
overclaim: *"A criterion at the top of this table is where an extra data feed, or
a single clarification with the sponsor, would buy the most time."* That sentence
is right. It says the grouping tells you where to spend an acquisition, which is a
real and useful thing, and it does not promise that 188 verdicts fall out of one
answer.

**What changed.** All five now say the same defensible thing, and four of the five
are generated, so the fix is in `scripts/costs.py`, `scripts/scorecard.py` and
`src/trialsieve/worklist.py` rather than in their output. The worklist reads "one
thing to go and find, then 188 values to read back". The film's ninth section says
"one missing test on almost every open case, so a nurse knows what to go and get".

| | before | now |
|---|---|---|
| documents claiming 188 verdicts resolve from one answer | 5 | **0** |
| of those that are generated rather than typed | 4 | fixed at the generator |

**Evidence.** `python scripts/costs.py && python scripts/scorecard.py && python scripts/worklist.py --run runs/tierA --operating-point 0 --allow-unsigned --out docs/sample_worklist.md`,
then `grep -rn "resolve together" README.md docs/SCORECARD.md docs/COST.md docs/sample_worklist.md`
returns nothing. It still appears twice in this file, which quotes the old
claim on purpose, and once in `src/trialsieve/worklist.py` as a comment naming
the sentence not to write. Those three are the record, not the claim.

## 45. Six sentences that outlived the numbers they described

**Found by** an independent reviewer briefed on the code and the evidence chain
rather than the deliverables, who picked nineteen rows out of the summary table at
the top of this file and checked each one against the file it cites. Seventeen
resolved. Two did not, and four more defects came out of the same reading.

**The shape.** Every one of these is a hard-coded sentence that was true when it
was written, describing a number that later moved. Not one is a computed value:
the reviewer's own note says the generated figures could not be broken. The
defects are all in prose sitting next to correct arithmetic, which is the most
comfortable place for one to survive.

**The two in the report generator, which are the worst.**

`results/RESULTS.md` printed, from the run:

> Panel reduction across the same seeds: `{"mean": 0.4615, "sd": 0.0, "min":
> 0.4615, "max": 0.4615, "range": 0.0, "n_seeds": 3}`

and then, two lines below:

> Recompiling the same criteria under a different seed moves the number a
> coordinator would act on by **more than ten points**.

The range is zero. The paragraph was fixed text inside `if len(reds) >= 2` at
`scripts/report.py`, with no dependence on the spread it described. Entry 30
collapsed that spread and the sentence stayed. Its closing clause, "no difference
in this report smaller than that spread is claimed as detected", had quietly
become vacuous, because the spread is 0. This is the failure this project is
named for, aimed at the project: the pipeline kept running and reported something
plausible.

The second: the report listed **six** criteria the gold set calls checkable and
the compiler did not produce, then said "Six of those are the vocabulary refusing
... **The seventh** is the one lost to the IR validator". There is no seventh.
Entry 29 fixed the validator and `results/results.json` has
`not_compilable.exhausted_retries: []`. The sentence had outlived its own repair
by fifteen entries.

**Three in this file's own summary table**, which is the table the submission
tells a reader to check first:

| row | said | is |
|---|---|---|
| the B2 comparison | `-0.4050 SER, CI [-0.5550, -0.2550]` | `-0.4275, CI [-0.5700, -0.2850]`, the pre-entry-30 value never refreshed |
| differences the floor calls uninterpretable | `2 of 6` to `0 of 6` | still `2 of 6`, both `TS - B1`; lowering the floor from 10.6% to 2.3% never moved them, because they are 0.0072 and 0.0043 |
| the weak-model probe | `1 of 6 on broader-only concepts against 6 of 6` | 1 of 6 on **absence** concepts against **5 of 6**. The `broader` class has one member |

The second of those is the one worth sitting with. It claimed the repair had made
every published difference interpretable, and the two that are not interpretable
are exactly the comparison against B1, the regular expressions, which is the arm
this system is least able to distinguish itself from. The row was flattering in
the one direction a reader cannot check without opening the file.

**And the published environment record had come apart.**
`results/published/` is meant to be one snapshot of three files.
`environment.json` named a commit eighteen behind HEAD and `locked_packages: 23`
against a lockfile holding 8, and had been written four and a half hours before
the two files beside it. `run.py diff` compares `RESULTS.md` and `results.json`
only, so it printed `IDENTICAL` over the top of it, and `SUBMISSION.md` points a
judge at that third file for versions.

**What changed.** Both report paragraphs are computed from the values they
describe, and the seed one now has a branch for a zero spread that says what a
zero floor does and does not license. The three table rows say what their cited
files say, and each names what it used to say. The snapshot was republished with
`run.py publish`, which had always written the three together; the failure was a
hand copy of two of them.

`tests/test_published_environment_is_current.py` is the guard: the published
record has to count the lockfile that ships, name the interpreter the current run
recorded, name a commit reachable from HEAD, and have been written within an hour
of the two files beside it. Run against the broken state it failed on the
lockfile count and on a 4.5 hour spread.

**And one from the same reading that is not a stale sentence.** The headline
table in `docs/SCORECARD.md` led with `44x lower` as the change column on silent
error rate. `evaluation/score.py` opens by saying the unit of result is the
ordered pair (coverage, SER), and that **a comparison against an arm at higher
coverage is not admissible**, because an arm that abstains everywhere scores a
silent error rate of exactly zero. TrialSieve answers 21.75% of cells and B2
answers 68.00%. So the submission's own scoring module called its headline row
inadmissible, and the row said it anyway, in the table the brief asks for. The
row now carries both coverages, the ratio is labelled "at a third of the
coverage", and a paragraph under the table sends the reader to the paired
bootstrap in `results/RESULTS.md`, which is the comparison that settles it. The
ratio stays because the brief's format has a change column, not because it is the
finding.

| | before | now |
|---|---|---|
| report paragraphs asserting a value they do not read | 2 | **0** |
| rows of the summary table disagreeing with their cited file | 3 of 19 | **0 of 19** |
| headline rows printing a ratio the scoring module calls inadmissible | 1 | **0** |
| gates that read the published environment record | 0 | **1** |

**Evidence.** `python scripts/report.py --run runs/tierA --out results` then
`grep -n "seventh" results/RESULTS.md` returns nothing and the seed paragraph
reads "Both are flat. Across 3 seeds ... the range is 0 on each".
`python -m pytest tests/test_published_environment_is_current.py -q`, 4 tests.

### A seventh sentence, and this one pointed at an empty file

**Found by** an independent reviewer reading the repository as a buyer rather than
as an engineer, asking what a coordinator is actually handed.

`docs/sample_worklist.md` lists 20 ruled-out patients and then says *"167 further
ruled-out patients in the machine-readable output."* The machine-readable output
was `docs/sample_worklist.json`, and it held nine keys, every one of them an
aggregate: `n_ruled_out`, `n_review`, `n_eligible`, and question sets counted by
`n_patients`. There were no patients in it. Not truncated, not summarised. None.

This belongs with the six above because it is the same shape, a sentence that
described something real when the sidecar was designed to feed `docs/COST.md` its
counts, and it kept its meaning while the file it pointed at never gained the rows
it promised. It is worse than the six in one way. Those misstated a number a
reader could recompute. This one sent a reader to a file for evidence that was not
there, so 167 of 187 exclusions had no reachable justification anywhere in the
repository, in a system whose entire argument is that a person removed from a
panel is owed a dated reason somebody can check.

**What changed.** `scripts/worklist.py` now writes the patients themselves:
`ruled_out` carries every patient with age, sex, and each failed criterion beside
the record line that failed it; `review` carries every patient with the criteria
left open and how many; `eligible` carries the rest. The counts stay where they
were, because `docs/COST.md` reads them and a generated figure should not start
depending on the length of a list.

| | before | now |
|---|---|---|
| ruled-out patients reachable in the sidecar | 0 of 187 | **187 of 187** |
| exclusions carrying evidence a reader can reach | 20 | **187** |
| patients in review reachable with their open criteria | 0 of 190 | **190 of 190** |

**Evidence.** `python scripts/gate_demo.py --run runs/tierA`, then
`python -c "import json; d=json.load(open('docs/sample_worklist.json')); print(len(d['ruled_out']), len(d['review']), len(d['eligible']))"`
prints `187 190 8` against the `n_ruled_out`, `n_review` and `n_eligible` the same
file reports.
