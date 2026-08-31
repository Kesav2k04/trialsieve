# Reproducing every number in this repository

Three commands, no API key, no model. Then a fourth that proves the first three
were not theatre. The reproduction itself touches no network: the clone and the
one `pip install` do, and after those two nothing in this repository opens a
socket. If `pytest` is already installed, the whole thing is offline.

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
| Disk | **59 MB of tracked files, and a fresh clone measures 83 MB** including history, of which the pack is 13.7 MiB. Every figure in this row is decimal MB. `git ls-tree -r -l HEAD` prints bytes, so divide by a million to land on these numbers; dividing by 1024 squared instead reads 56 rather than 59, which looks like the row is wrong again and is not. The tracked bulk is `runs/` at 48 MB, the recorded cassettes and trajectories that make the replay possible, then the vendored panel at 6.6 MB, then `docs/img/` at 1.20 MB, the five frames the top-level README shows. Outside those three, nothing reaches one megabyte; inside `runs/` two
trajectory logs do, at 1.11 MB and 1.08 MB, and they are part of the 48 MB
already named. The gap between 58 and 88 is history, and it is small because the one large binary this project produced, the video, is submitted as a link rather than carried here. Measure it yourself with `git ls-tree -r -l HEAD` and `git count-objects -vH`. This row has been wrong six times, first at 12 MB naming the panel as the bulk, then at 65 MB, 61 MB, 185 MB, 231 MB and 247 MB as a 19 MB render was rebuilt and recommitted, so it is worth measuring rather than reading. |
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

### If you are holding the zip rather than a clone

Three instructions in this file need a git object database, and a source archive
carries the tree without one. Skip them, and nothing else changes:

| line | why it cannot run | what to do instead |
|---|---|---|
| the `git clone` above | you already have the tree | unpack the zip and start at `pip install pytest` |
| `git ls-tree -r -l HEAD` and `git count-objects -vH`, used below to check the disk figures | no object database | `python -c "import pathlib,sys; print(sum(p.stat().st_size for p in pathlib.Path('.').rglob('*') if p.is_file()))"` measures the unpacked tree |
| `git checkout -- .`, offered at the end for resetting between runs | no index to reset to | unpack the zip again into an empty directory |

Seven tests skip for the same reason and each prints why. That is the whole of
the difference: `python run.py reproduce` itself needs no git and prints
`IDENTICAL` either way. One line in its output says so, and it appears in the
archive and not in a clone:

    NOT COMPARED: the provenance block names the commit that last touched each
    prompt file, and this tree has no object database, so there is nothing here
    to compare it against.

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
3. **The dependency surface is walked.** `scripts/lockfile.py --imports` parses
   every module on this path and fails on any import that is not standard library
   or another file in this repository. The claim that there is nothing to install
   is checked here rather than asserted in prose.
4. **The compile is replayed** from `runs/tierA/cassettes/`. Each cassette is a
   recorded model call keyed on the sha256 of the full canonical request. Replay
   never falls through to a live call: a missing cassette raises `CassetteMiss`
   and stops the run.
5. **The arms are run** over the panel, in four passes: the free arms over every
   published seed, the degradation curve at k = 10, 20 and 40, the open-world
   sensitivity arm, and the per-cell baseline over its ten-patient sample. This
   step calls no model at all. The compiled predicates are executed
   deterministically against every patient, which is the point of the
   architecture and the reason screening is free.
6. **The recall audit runs** into `docs/CONTAMINATION.md`. Three registered trials
   with public identifiers is the setup where a good result can come from having
   memorised the protocol rather than from having read it, so this enumerates the
   substitutions every prompt template accepts, searches every recorded request for
   the identifiers and for title-specific wording, and reports both.
7. **The documents that quote numbers are regenerated**: the worked counterexample,
   the sample worklist, and the trajectory index. They are output, not prose, so a
   number that moved shows up here rather than going stale in a committed file.
8. **Every path a document points at is checked**, and every anchor, by
   `scripts/linkcheck.py`. A link into a file that moved is the cheapest kind of
   rot and the one a reader hits first.
9. **The cost table is rebuilt** into `docs/COST.md` from the recorded call and
   token counts, so the money figures in the prose come from the run rather than
   from a memory of it.
10. **The report is scored** into `results/results.json`.
11. **The full suite runs**, all 400 tests, now that every artifact they read
   exists. `python -m pytest -q` prints the current count, which is the number to
   trust if this sentence has drifted. From a clone that is 400 passed, once
   this command has run: a clone measured before it reports 396 passed and 4
   skipped, because four tests read an artifact step 10 writes. From an
   unpacked source archive it is 393 passed and 7 skipped, because seven of them
   resolve a commit or read history and an archive carries the tree without an
   object database. Run `pytest` in an archive *before* this command rather than
   after it and you get 389 passed and 11 skipped instead: four more tests read
   an artifact that step 10 above regenerates, and they skip rather than fail
   when it is not there yet. All three numbers add up to 400. The pre-registration freeze is no longer among them:
   `docs/protocol_registration.json` carries the registering commit and the
   digest of each frozen section, so an archive checks the freeze against that
   file and a clone additionally checks the file against git. Each prints the reason it skipped rather than passing
   quietly. Beyond the engine they cover the recorder,
   the sign-off gate, the cassette seal, the contamination perturbation, the
   mutation harness, and every figure a shipped document quotes against the run
   that produced it. The film's own checks are not among them: the film is built
   by a separate project that is not in this repository, so nothing here can
   verify it and nothing here claims to.
12. **The five verification checks run** (see below).
13. **The report is compared** byte for byte against `results/published/results.json`,
   with timestamps and wall-clock fields removed. It prints `IDENTICAL` or a diff.

## The solution, the baseline and the evaluation, as three separate commands

`python run.py reproduce` runs all of them in order. They are written out
separately below because each is a different claim. All replay from
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
on the first failure. About 85 seconds together, and **almost all of it is
`report.py`**: it measured 82 seconds against `verify.py`'s 5. `report.py` prints
nothing at all while it resamples the bootstrap, which is the one place in this
run where a reader has good reason to think the thing has hung. It has not. This
sentence used to attribute the time to `verify.py`, which is the worse mistake to
make, because it points at the command that is not the one you are waiting for.

## What a successful run looks like

The last lines of a real run, copied out of
[`docs/reproduce_transcript.txt`](docs/reproduce_transcript.txt), which is
captured stdout rather than a sample typed into this file. The whole 2,006-line
transcript is in there, so there is more than a tail to compare against. Run the
command yourself and read your own last lines beside these:

    ========================================================================
    compare against the published numbers
    ========================================================================
    IDENTICAL: every published number reproduced on this machine, and results/RESULTS.md is byte-identical to the published copy.

    OK  (reproduce in 155.0s)

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

**Reproducing costs nothing and takes about two and a half minutes.** `python
run.py reproduce` makes no model call, so it costs $0.00 in tokens and needs no
key. Every recorded call replays from `runs/tierA/cassettes/`, and replay never
falls through to a live call. The reading you can check rather than take on trust
is the last line of
[`docs/reproduce_transcript.txt`](docs/reproduce_transcript.txt), which is
captured stdout from a clean tree: **155.0 seconds** on a Windows laptop with a
14-core CPU. Repeated runs landed between 143 and 188 seconds, and the spread is
the honest answer to "how long does it take": a cold clone pays to read 59 MB off
disk, and a machine that is busy pays twice. The 188 is a reading from an
unpacked archive on the same OS build and the same Python, taken while this
machine was doing something else, so treat the top of that range rather than the
bottom as what to expect. Every one of them
is printed by the command itself as its last line, so the figure a judge sees is
the one their own run measured rather than this one.

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
