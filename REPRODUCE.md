# Reproducing every number in this repository

Three commands, no API key, no network, no model. Then a fourth that proves the
first three were not theatre.

```bash
git clone <this repo> && cd trialsieve
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
| Runtime dependencies | none. Every import in `src/`, `evaluation/`, `scripts/` and `tools/` is standard library, and `tests/test_dependencies.py` fails if that stops being true. The one exception is the video build, `scripts/make_video.py`, which uses a speech synthesiser and a browser and is not on this path. |
| Network | not used by `reproduce`. Replay mode refuses to make a live call. |
| Disk | about 40 MB, most of it the vendored patient panel. |
| API key | not needed to reproduce. Needed only to record new model calls. |

The patient panel and the trial records are committed, so there is no 95 MB
download and no Java runtime in the path. `data/vendor/panel_provenance.json`
carries the source URL and the sha256 of the archive they were built from, and
`python run.py panel` rebuilds them from that archive if you want to check.

## What `reproduce` does, in order

1. **`results/environment.json`** is written: Python version, platform, git commit,
   and whether the tree was dirty. A number that differs on your machine has
   somewhere to point.
2. **The engine gate runs.** About 70 semantic tests over the evaluation engine:
   Kleene truth tables, both boundaries of every date window, both directions of
   every unit conversion, absent distinguished from zero. The protocol makes this
   a precondition for a scored run, so `reproduce` stops here if it fails.
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
8. **The five verification checks run** (see below).
9. **The report is compared** byte for byte against `results/published/results.json`,
   with timestamps and wall-clock fields removed. It prints `IDENTICAL` or a diff.

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
# HTTP the judge would, so recording and replay share one code path
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

**Reproducing costs nothing and takes minutes.** `python run.py reproduce` makes no
model call. Every recorded call replays from `runs/tierA/cassettes/`, and replay
never falls through to a live call.

**Screening is free, and that is the architecture showing up as a runtime fact.**
The step that touches all 385 patients across all 40 criteria makes zero model
calls and finishes in seconds. The model was spent upstream, once per protocol.

## If the diff is not identical

That is a result, not a crash, and it is worth reporting. The likely causes, in
the order they are worth checking:

1. A different Python version changed a float in the last decimal place. Compare
   `results/environment.json` against `results/published/environment.json`.
2. The tree is dirty. `git_dirty` in `environment.json` says so.
3. A cassette is missing, in which case the run stopped before the diff with a
   `CassetteMiss` naming the request.

The scoring code takes no wall-clock input and seeds every resample, so a
difference should not be possible from re-running alone. If you find one, the
diff output names the field.
