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
