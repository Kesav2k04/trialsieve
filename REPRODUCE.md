# Reproducing every number in this repository

Three commands, no API key, no network, no model. Then a fourth that proves the
first three were not theatre.

```bash
git clone https://github.com/Kesav2k04/trialsieve.git && cd trialsieve
python -m pip install pytest          # the only install, and only for the gate
python run.py reproduce
```

That is the whole thing. `run.py` works on Windows, macOS and Linux. There is a
`Makefile` too, but it only forwards to `run.py`, because a stock Windows box has
no `make` and the reproduction should not depend on one.

## What you need

| | |
|---|---|
| Python | 3.10 or newer. Developed on 3.14.2, CI runs 3.10 and 3.13. |
| Install | `pytest`, for the test gate. Nothing else. |
| Runtime dependencies | none, and no exception. Every import in `src/`, `evaluation/`, `scripts/` and `tools/` is standard library, and `tests/test_dependencies.py` fails if that stops being true. `pytest` is the only third-party package this repository declares at all. The video was rendered by a separate Node project, which is not part of this submission and is not reachable from anything here. |
| Network | not used by `reproduce`. Replay mode refuses to make a live call. |
| Disk | **57 MB of tracked files, and a fresh clone measured 72 MB** including history. Every figure in this row is decimal MB. `git ls-tree -r -l HEAD` prints bytes, so divide by a million to land on these numbers; dividing by 1024 squared instead reads 54 rather than 57, which looks like the row is wrong again and is not. The tracked bulk is `runs/` at 48 MB, the recorded cassettes and trajectories that make the replay possible, and then the vendored panel at 6.6 MB. Nothing else in the tree reaches one megabyte. The gap between 57 and 72 is history, and it is small because the one large binary this project produced, the video, is submitted as a link rather than carried here. Measure it yourself with `git ls-tree -r -l HEAD` and `git count-objects -vH`. This row has been wrong six times, first at 12 MB naming the panel as the bulk, then at 65 MB, 61 MB, 185 MB, 231 MB and 247 MB as a 19 MB render was rebuilt and recommitted, so it is worth measuring rather than reading. |
| API key | not needed to reproduce. Needed only to record new model calls. |

The patient panel and the trial records are committed, so there is no 95 MB
download and no Java runtime in the path. `data/vendor/panel_provenance.json`
carries the source URL and the sha256 of the archive they were built from.
[docs/DATA_FINDINGS.md](docs/DATA_FINDINGS.md) records what was found in that
corpus as it was found, which is where several evaluation choices come from: the
records are complete by construction, so the failure mode this system exists for
barely occurs at k=0 and had to be induced by the degradation harness rather than
waited for.

Which of those files has a generator, precisely, because "it can be rebuilt" is
the kind of sentence that goes stale without anyone noticing:

| file | rebuilt by |
|---|---|
| `panel.jsonl.gz`, `panel_provenance.json` | `python run.py panel`, from the pinned archive |
| `panel_code_counts.json` | `python scripts/build_panel_counts.py`, from the panel. `--check` recomputes and exits non-zero if the committed file disagrees. |
| `terminology_catalog.json` | **nothing in this repository.** It was derived from the same pinned archive, before the panel was cut, and the source patient bundles are not vendored. Its contents are checkable against the panel (every code the panel carries appears in it) but it cannot be regenerated here. |
| `trials/`, `trials_index.json` | `python scripts/fetch_trials.py`, from ClinicalTrials.gov API v2 |

That third row is a real gap and it is listed rather than glossed. A committed
artifact with no generator is the one that goes stale silently: `panel_code_counts.json`
did exactly that, listing 674 codes for a panel carrying 677, and the missing entry
was read as a count of zero by the document a reviewer signs.

## What `reproduce` does, in order

1. **`results/environment.json`** is written: Python version, platform, git commit,
   and whether the tree was dirty. A number that differs on your machine has
   somewhere to point.
2. **The engine gate runs.** The 52 semantic tests over the evaluation engine
   alone (`tests/test_engine.py`): Kleene truth tables, both boundaries of every
   date window, both directions of every unit conversion, absent distinguished
   from zero. The protocol makes this a precondition for a scored run, so
   `reproduce` stops here if it fails. It is only the engine, and that is the
   point: the full suite reads artifacts this command has not produced yet, so
   gating the run on it would mean requiring what the run creates. It did, until
   an independent reviewer cloned this repository and hit nineteen failures on
   the one command everything else is advertised on. The whole suite runs at
   step 8, where the things it reads exist.
3. **The compile is replayed** from `runs/tierA/cassettes/`. Each cassette is a
   recorded model call keyed on the sha256 of the full canonical request. Replay
   never falls through to a live call: a missing cassette raises `CassetteMiss`
   and stops the run.
4. **The arms are run** over the panel. This step calls no model at all. The
   compiled predicates are executed deterministically against every patient, which
   is the point of the architecture and the reason screening is free.
5. **The recall audit runs** into `docs/CONTAMINATION.md`. Three registered trials
   with public identifiers is the setup where a good result can come from having
   memorised the protocol rather than from having read it, so this enumerates the
   substitutions every prompt template accepts, searches every recorded request for
   the identifiers and for title-specific wording, and reports both.
6. **The documents that quote numbers are regenerated**: the worked counterexample,
   the sample worklist, and the trajectory index. They are output, not prose, so a
   number that moved shows up here rather than going stale in a committed file.
7. **The report is scored** into `results/results.json`.
8. **The full suite runs**, all 352 tests, now that every artifact they read
   exists. `python -m pytest -q` prints the current count, which is the number to
   trust if this sentence has drifted. Beyond the engine they cover the recorder,
   the sign-off gate, the cassette seal, the contamination perturbation, the
   mutation harness, and what the film's cards and narration say against what the
   run actually printed.
9. **The five verification checks run** (see below).
10. **The report is compared** byte for byte against `results/published/results.json`,
   with timestamps and wall-clock fields removed. It prints `IDENTICAL` or a diff.

## The solution, the baseline and the evaluation, as three separate commands

`python run.py reproduce` runs all of them in order and is the command to use if
you only run one thing. They are written out separately here because each is a
different claim, and a reader who wants to check one of them should not have to
read the task runner to find out how. All of these replay from
`runs/tierA/cassettes/` and call no model, so they need no key and no network.

**The solution.** Compile each criterion once, then execute the compiled
predicates against all 385 patients. The second command makes no model call at
all, which is the whole architecture in one line:

    python scripts/compile_protocol.py --run runs/tierA --mode replay --provider shim --seed 7
    python scripts/run_arms.py --run runs/tierA --mode replay --arms TS,B0,B1 --seed 7

`TS` is the solution. `B0`, which fails everyone, and `B1`, which answers only
what age and sex can decide, are the degenerate controls, and they ride along in
the same command because they are scored against the same cells. Each command
writes a JSON summary and then a path: `runs/tierA/compiled/` for the first,
`runs/tierA/cells/cells_TS-B0-B1_k0_seed7.jsonl` for the second. About four
seconds each on the machine recorded in `results/environment.json`.

Pass the arms exactly as written. `report.py` scores every `cells_*.jsonl` file it
finds, so running one arm under a new tag adds a row rather than replacing one,
and the comparison table changes.

**The baseline.** `B2` is the simple thing this is measured against: one model
call per patient per criterion, handed the same flattened facts the engine reads
and the criterion prose verbatim. It runs over 10 patients rather than 385
because at $22.19 for a full pass, paying per cell is the cost the compile exists
to avoid:

    python scripts/run_arms.py --run runs/tierA --mode replay --arms B2 --patients 10 --tag b2_10p --model gemini-3.7-flash-medium

It writes `runs/tierA/cells/cells_B2_b2_10p.jsonl`.

**The evaluation.** Score every arm into `results/results.json`, then run the five
checks that make the replay falsifiable rather than merely repeatable:

    python scripts/report.py --run runs/tierA --out results
    python scripts/verify.py all --run runs/tierA

`report.py` prints the comparison table that `results/RESULTS.md` is built from.
`verify.py` prints five lines, each beginning `PASS` or `FAIL`, and exits non-zero
on the first failure. About 85 seconds together, nearly all of it in `verify.py`
re-hashing 1,047 cassettes.

## What a successful run looks like

The last lines of a real run, copied out of
[`docs/reproduce_transcript.txt`](docs/reproduce_transcript.txt), which is
captured stdout rather than a sample typed into this file. The whole 1,925-line
transcript is in there, so there is more than a tail to compare against. Run the
command yourself and read your own last lines beside these:

    ========================================================================
    compare against the published numbers
    ========================================================================
    IDENTICAL: every published number reproduced on this machine, and results/RESULTS.md is byte-identical to the published copy.

    OK  (reproduce in 151.3s)

    exit 0

`IDENTICAL` is the whole result. If it prints a diff instead, the last section of
this file is what to do about it. Immediately above that line, `verify.py` will
have printed five results, each starting `PASS` or `FAIL`, the last of them:

    PASS: none of 181 recorded Checker B prompts contains a predicate, a digest, or any part of the compiled output. The two labellings are independent readings of the same record.

### The models these cassettes recorded

Replay needs none of them; they are here because "relevant versions" includes the
things that produced the recording, and because a re-record would drift if they
were not written down.

| model | what it did |
|---|---|
| `gemini-3.7-flash-medium` | the compiler, grounder, critic and segmenter, and the B2 baseline |
| `gpt-oss-120b-medium` | Checker B, the independent second labeller |
| `granite3.1-dense:8b` | the weak-model probe |

The per-model call counts are in [`SUBMISSION.md`](SUBMISSION.md), counted there
rather than here so the same quantity does not get two homes and drift apart;
`python -m pytest tests/test_recorded_call_counts.py -q` recounts them from the
tracked cassettes. To re-record rather than replay, `--backend codex` maps to
`gpt-5.6-terra`, which is why that name appears further down this file.

The video toolchain, which no reproduction step touches and which is not part of
this submission: Remotion 4.0.489, React 19.1.1, Chatterbox 0.1.7.

## The five checks, and what each one rules out

```bash
python scripts/verify.py all --run runs/tierA
```

| check | the objection it answers |
|---|---|
| `cassettes` | "the recordings could have been edited." Every cassette is re-hashed and compared against its own filename key. |
| `trajectories` | "the trajectories could be a nicer story than what ran." Every recorded model call in every trajectory is matched to a cassette whose stored request is byte-identical to the prompt shown in the trajectory. |
| `prove-replay` | "a cassette store is just a saved answer file." One space is added to one prompt. The key changes, the lookup misses, and the run stops with `CassetteMiss` instead of returning the previous answer. |
| `prove-sensitivity` | "the numbers might be stored next to the cassettes rather than computed from them." One comparison in one compiled predicate is flipped and the verdict counts move. |
| `blind` | "the second labeller could have seen the system's answer." Every recorded Checker B prompt is searched for predicate vocabulary, predicate digests and compiled output. Blindness is read out of the prompt rather than argued from commit order. |

The third and fourth are the ones worth watching. Together they say the recorded
model output is both load-bearing and tamper-evident.

## Recording new model calls

Only needed if you want to re-run the model rather than replay it.

```bash
# any OpenAI-compatible endpoint works
ollama serve && ollama pull granite3.1-dense:8b
python run.py live-smoke      # two criteria, to check the wiring

# or front an authenticated CLI with the local shim, which speaks the same
# HTTP a reader would, so recording and replay share one code path
python tools/cli_openai_shim.py --port 8100 --cli codex --backend codex \
    --default-model gpt-5.6-terra --concurrency 3
python run.py live
```

`run.py live` writes new cassettes beside the existing ones. It never overwrites
one: a request that already has a cassette is served from it, so re-running is
cheap and idempotent.

## Cost and runtime

[docs/COST.md](docs/COST.md), generated by `python scripts/costs.py` from the files
each run wrote: recorded call counts, recorded token counts, recorded wall clock,
and an estimate of what the same work would cost at published per-token rates.

Two numbers are worth reading before the rest.

**Reproducing costs nothing and takes under three minutes.** `python run.py
reproduce` makes no model call, so it costs $0.00 in tokens and needs no key.
Every recorded call replays from `runs/tierA/cassettes/`, and replay never falls
through to a live call. Measured end to end on this machine, a Windows laptop
with a 14-core CPU: **169.8 seconds from a fresh clone into an empty directory**,
151.3 seconds in place with the artifacts already warm, and 285.6 seconds on a
second run while the same machine was busy rendering video. Every one of those is
printed by the command itself as its last line, so the figure a judge sees is the
one their own run measured rather than this one. Three readings of the same
command are given because the spread is the honest answer to "how long does it
take": a cold clone pays for reading 57 MB off disk, and a busy machine pays
twice.

**Screening is free, and that is the architecture showing up as a runtime fact.**
The step that touches all 385 patients across all 40 criteria makes zero model
calls and finishes in seconds. The model was spent upstream, once per protocol.

## If the diff is not identical

That is a result, not a crash, and it is worth reporting. The likely causes, in
the order they are worth checking:

1. A different Python version changed a float in the last decimal place. Compare
   `results/environment.json` against `results/published/environment.json`.
2. The tree is dirty. `git_dirty` in `environment.json` says so. Note that
   `reproduce` dirties it itself: it rewrites the three compiled criteria
   files and `docs/COST.md`, whose only changed bytes are wall-clock
   readings (`"wall_s": 1.1` against `1.3`, "finishes in 2 s" against
   3 s). None of it is a published number, so `IDENTICAL` is unaffected,
   but a second run reports `git_dirty` true and it is this command's
   doing rather than yours. `git checkout -- .` between runs if you want
   the field to mean something.
3. A cassette is missing, in which case the run stopped before the diff with a
   `CassetteMiss` naming the request.

The scoring code takes no wall-clock input and seeds every resample, so a
difference should not be possible from re-running alone. If you find one, the
diff output names the field.
