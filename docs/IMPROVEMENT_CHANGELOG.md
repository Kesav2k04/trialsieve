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
repository. Every cassette would replay identically for a judge, and every attempt
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

Measured across the whole vocabulary: **50 of 724 catalog codes, 7%, appear in no
panel patient.** By domain: 19 of 136 medications, 16 of 191 conditions, 8 of 160
procedures, 7 of 237 observations.

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
