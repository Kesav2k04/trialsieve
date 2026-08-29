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

## 25. The one invariant the design calls its own sharp edge was never checked

**Found by** a reviewer reading `README.md:181` against the code that is supposed
to hold it up. The line is a promise: a code the site records more coarsely than
the criterion needs goes into `broader_codes`, and then "presence cannot settle
it. Absence still can." `docs/AGENT_DESIGN.md:71-77` restates it as a contract on
the compiler. The emit prompt spells it out to the model in full.

Nothing verified it. The reviewer's question was one sentence: what happens if the
model puts a broader-only code in `codes` anyway?

**What was wrong.** `src/trialsieve/agents/compiler.py:342-343` builds the emit
validator's allow-list of legal codes:

```python
allowed = {c for g in grounded for c in g["codes"]}
allowed |= {c for g in grounded for c in (g.get("broader_codes") or [])}
```

The union is right for deciding whether a code was hallucinated, which is what the
check was written to do. It is exactly wrong for deciding which slot a code belongs
in. A broader-only code emitted into `codes` is inside the allow-list, so it
validates, and the engine then reads it as an exact match and lets presence settle
the verdict. The rule was enforced by asking politely and checking nothing.

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
