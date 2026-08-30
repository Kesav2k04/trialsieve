"""The task runner. `python run.py reproduce` is the whole reproduction.

There is no `make` here, and no `make` on a stock Windows box either, so the
entry point is a Python file that behaves identically on the three platforms a
judge might be sitting at. It has no dependencies. Neither does the project:
every import in `src/`, `evaluation/` and `scripts/` is from the standard
library, and `pytest` is needed only to run the test gate.

    python run.py check          the engine gate, about a second
    python run.py reproduce      the published numbers, offline, from cassettes
    python run.py verify         the five checks that make replay falsifiable
    python run.py live-smoke     two criteria against a real model
    python run.py live           a full recording run, needs a model backend

Every step prints the command it is about to run, so nothing here is a black
box you have to trust.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

RUN = "runs/tierA"

#: Patients in the per-cell baseline sample. The free arms use the whole panel.
B2_PATIENTS = 10
PUBLISHED = ROOT / "results" / "published"


def sh(*args: str, env_extra: dict | None = None, check: bool = True) -> int:
    """Run a command in the foreground, showing it first."""
    cmd = [str(a) for a in args]
    print(f"\n$ {' '.join(cmd)}", flush=True)
    env = dict(os.environ)
    # Windows consoles default to cp1252 and the reason lines carry mu, degree
    # and per-mille signs. Without this the run dies on a print statement.
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if env_extra:
        env.update(env_extra)
    rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
    if check and rc != 0:
        print(f"\nFAILED ({rc}): {' '.join(cmd)}", file=sys.stderr)
        raise SystemExit(rc)
    return rc


def banner(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}", flush=True)


# ---------------------------------------------------------------- targets ---

def t_check() -> None:
    """The engine gate. The protocol makes this a precondition for a scored run.

    This runs the engine's own semantics and nothing else, which is what the
    protocol names as the precondition and what this file's own help has always
    said it was. It used to run the whole suite, and that could not work from a
    clean clone: the suite includes tests that read `runs/tierA/cells/`, the
    directory `reproduce` regenerates several steps later and `.gitignore`
    excludes. Nineteen of them failed for everyone whose checkout did not already
    have the files, on the one command the whole evidence chain is advertised on.
    A gate cannot require what the run it gates produces. The full suite still
    runs inside `reproduce`, after the artifacts it describes exist.
    """
    banner("engine gate")
    sh(PY, "-m", "pytest", "-q", "tests/test_engine.py")
    # `dependencies = []` is the claim that lets a judge reproduce with no install
    # step. One new import would end it silently, so the claim is parsed rather
    # than trusted: every module the reproduction touches, checked against
    # `sys.stdlib_module_names`.
    banner("dependency surface")
    sh(PY, "scripts/lockfile.py", "--imports")


def t_suite() -> None:
    """The whole suite, run where every artifact it reads already exists."""
    banner("the full test suite")
    sh(PY, "-m", "pytest", "-q")


def t_environment() -> None:
    """Write down what this machine is, so a differing number has somewhere to point.

    The working directory is not recorded. It never explained a differing
    number, and it is the one field here that names the person running the
    command: a checkout under a home directory writes their account name into a
    tracked file, and `tests/test_no_private_paths.py` then fails on the second
    run. That failure is how this was found, in a clean clone under a home
    directory rather than in the tree it was written in.
    """
    banner("environment")
    info = {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    # The interpreter alone did not say enough. Two machines can both report
    # 3.14.2 and differ in the packages the test gate runs on,
    # so the lock is read back here and any drift is recorded beside the run
    # rather than left for a reader to discover.
    lock = ROOT / "requirements-lock.txt"
    if lock.exists():
        import importlib.metadata as _md
        pinned, drift = {}, {}
        for line in lock.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if "==" not in line:
                continue
            name, want = line.split("==", 1)
            pinned[name] = want.strip()
            try:
                have = _md.distribution(name).version
            except Exception:
                have = None
            if have != want.strip():
                drift[name] = {"locked": want.strip(), "installed": have}
        info["locked_packages"] = len(pinned)
        info["lock_drift"] = drift
    try:
        info["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        # `results/` is what this step writes, so a status that counts it reports
        # the run's own output as a modification of the tree that produced it,
        # and every published record said dirty on a clean checkout. What the
        # reader needs is whether the INPUTS matched the named commit, so the
        # output directory is excluded and the exclusion is named in the file.
        info["git_dirty"] = bool(subprocess.run(
            ["git", "status", "--porcelain", "--", ".", ":(exclude)results"],
            cwd=ROOT, capture_output=True, text=True
        ).stdout.strip())
        info["git_dirty_excludes"] = "results/"
    except OSError:
        pass
    out = ROOT / "results" / "environment.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(info, indent=1))


def _recorded_model(run: str, arm: str, tag: str) -> str | None:
    """Which model an arm was recorded under, read back from the recording.

    The model name sits inside the request that the cassette key hashes, so a
    replay naming a different one rebuilds every prompt and misses every
    cassette. `--provider` defaults to ollama, B2 was recorded on the shim, and
    `reproduce` passed neither: the published pipeline could not regenerate its
    own baseline arm. Taken from the recording rather than repeated as a
    constant here, because a constant is one more thing that can drift from what
    actually ran.
    """
    meta = ROOT / run / "cells" / f"meta_{arm}_{tag}.json"
    if meta.exists():
        named = json.loads(meta.read_text(encoding="utf-8")).get("model")
        if named:
            return named
    # Recorded before the meta carried it. The cassette a trajectory points at is
    # the recorded request itself, so the name in it is the one that ran.
    for traj in sorted((ROOT / run / "trajectories" / "baseline-b2").glob(f"*{tag}.jsonl")):
        for line in traj.read_text(encoding="utf-8").splitlines():
            key = json.loads(line).get("cassette_key")
            cas = ROOT / run / "cassettes" / f"{(key or '')[:16]}.json"
            if key and cas.exists():
                return json.loads(cas.read_text(encoding="utf-8"))["request"]["model"]
    return None


def _runs_with_trajectories(first: str) -> list[str]:
    """Every run directory whose trajectory logs ship, the scored one first.

    Discovered rather than listed, because a list is a second place a run has to
    be registered and the one that gets forgotten is the one nobody is watching.
    Scoped to what is committed: this machine also holds development and smoke
    runs that `.gitignore` keeps out, and rendering those would leave a reader's
    checkout with pages that are not in anybody else's. Asked of git, and if
    there is no git here (an unpacked source archive holds only tracked files
    anyway) the directory walk answers the same question.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "--", "runs/*/trajectories/*.jsonl"],
        cwd=ROOT, capture_output=True, text=True)
    if tracked.returncode == 0 and tracked.stdout.strip():
        names = {line.split("/")[1] for line in tracked.stdout.split()}
    else:
        names = {d.name for d in (ROOT / "runs").iterdir()
                 if any((d / "trajectories").rglob("*.jsonl"))}
    return [first] + sorted(f"runs/{n}" for n in names if f"runs/{n}" != first)


def t_verify(run: str = RUN) -> None:
    banner("verification")
    sh(PY, "scripts/verify.py", "all", "--run", run)


def t_reproduce(run: str = RUN) -> None:
    """Rebuild every published number from the recorded model calls, offline.

    Nothing in this path touches the network. `--mode replay` refuses to make a
    live call even if one were available, so a missing cassette stops the run
    rather than quietly producing a different number.
    """
    t_environment()
    t_check()

    # Every seed the report publishes, not only the scored one. `runs/*/cells/`
    # is 46 MB and is not committed, so a group this path does not regenerate is
    # a group a clean clone cannot produce: the report then omits it, the diff
    # against `results/published/` says DIFFERENT, and the reproduction claim is
    # false for everyone except the machine that happened to have the files.
    # That is what a clean clone did before these three lines existed.
    banner("replay the compile, every published seed")
    for seed in ("7", "8", "9"):
        sh(PY, "scripts/compile_protocol.py", "--run", run, "--mode", "replay",
           "--provider", "shim", "--seed", seed)

    banner("run the free arms over the whole panel, every published seed")
    for seed in ("7", "8", "9"):
        sh(PY, "scripts/run_arms.py", "--run", run, "--mode", "replay",
           "--arms", "TS,B0,B1", "--seed", seed)

    # The degradation curve. The engine reads a chart that has been damaged in a
    # seeded, reproducible way, so these arms cost nothing but are published and
    # therefore have to be regenerable here.
    banner("run the degradation curve")
    for k in ("0.1", "0.2", "0.4"):
        sh(PY, "scripts/run_arms.py", "--run", run, "--mode", "replay",
           "--arms", "TS,B0,B1", "--seed", "7", "--k", k, "--degrade-seed", "101")

    # The same compiled predicates again, with every closed-world decision the
    # compiler made discarded. It reports how much of the system's error is the
    # model treating a silent record as an answer, and the answer is most of it.
    # It runs here rather than being a step a reader has to know to take, because
    # a sensitivity analysis nobody runs is a sensitivity analysis nobody has.
    banner("run the open-world sensitivity arm")
    sh(PY, "scripts/run_arms.py", "--run", run, "--mode", "replay", "--arms", "TS",
       "--absent-means-override", "unknown", "--tag", "ow")

    # The per-cell baseline is the only arm that costs a model call per patient,
    # so it was recorded over a seeded sample rather than the panel. Replayed here
    # only if it was recorded: a checkout without those recordings should
    # reproduce everything else rather than stop.
    #
    # The condition asks whether the recording exists, not whether a previous
    # run's output is lying around. It used to look for `cells/cells_B2_*.jsonl`,
    # which `.gitignore` excludes, so on a clean clone the guard was false, the
    # baseline arm never ran, and the report came out missing the one group the
    # whole comparison rests on. The trajectories are committed, so they are what
    # it reads.
    if any((ROOT / run / "trajectories" / "baseline-b2").glob("*.jsonl")):
        banner("replay the per-cell baseline over its sample")
        tag = f"b2_{B2_PATIENTS}p"
        cmd = [PY, "scripts/run_arms.py", "--run", run, "--mode", "replay",
               "--arms", "B2", "--patients", str(B2_PATIENTS), "--tag", tag]
        model = _recorded_model(run, "B2", tag)
        if model:
            cmd += ["--model", model]
        sh(*cmd)

    banner("audit for recall")
    # Replay, not the record default. A reproduce step that can reach the network
    # is not a reproduce step: with a cassette missing it should stop and say so
    # rather than quietly pay for a new answer.
    sh(PY, "scripts/contamination.py", "--run", run, "--counterfactual",
       "--mode", "replay")

    banner("regenerate the documents that quote numbers")
    sh(PY, "scripts/counterexample.py", "--run", run, "--mode", "replay")
    sh(PY, "scripts/gate_demo.py", "--run", run)
    # Every run directory that holds a trajectory, not only the scored one. The
    # second labeller and the three vocabulary probes shipped 243 raw JSONL logs
    # with nothing rendered beside them, so an arm this project is measured
    # against was readable only by someone willing to parse it, while the arm
    # doing the measuring had 235 rendered pages and an index.
    for traj_run in _runs_with_trajectories(run):
        sh(PY, "scripts/trajectories.py", "--run", traj_run)

    banner("check every path a document points at")
    sh(PY, "scripts/linkcheck.py")

    banner("cost and runtime")
    sh(PY, "scripts/costs.py")

    banner("score and report")
    sh(PY, "scripts/report.py", "--run", run, "--out", "results")

    t_suite()
    t_verify(run)
    t_diff()


def t_publish(run: str = RUN) -> None:
    """Freeze this machine's numbers as the ones the repository claims.

    Run once, after a recording run, by the author. A judge never runs this: they
    run `reproduce`, which regenerates the same files and byte-compares them
    against what this wrote. Kept as a separate target so that comparison cannot
    be won by quietly refreshing the baseline.
    """
    # Rewritten first, not copied as found. The published record is a provenance
    # claim about the numbers beside it, and the file on disk can predate them by
    # any number of commits: the first publish froze one naming a commit 15 ahead
    # of HEAD with a dirty flag, for numbers computed at neither.
    t_environment()
    for name in ("results.json", "RESULTS.md", "environment.json"):
        src, dst = ROOT / "results" / name, PUBLISHED / name
        if not src.exists():
            print(f"missing {src}; score a run first", file=sys.stderr)
            raise SystemExit(2)
        PUBLISHED.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"published {dst.relative_to(ROOT)}")
    print()
    print("now run `python run.py reproduce` and confirm it prints IDENTICAL.")


def t_links() -> None:
    """Every path the documents point at, checked. Free, no network."""
    sh(PY, "scripts/linkcheck.py")


def t_contamination() -> None:
    """The recall audit on its own. Free, deterministic, no model call."""
    sh(PY, "scripts/contamination.py", "--run", RUN)


def _canonical(p: Path) -> str:
    """Compare the numbers, not the timestamps."""
    d = json.loads(p.read_text(encoding="utf-8"))
    for k in ("generated_at", "wall_s", "environment", "elapsed_s"):
        d.pop(k, None)
    return json.dumps(d, sort_keys=True, indent=1)


def t_diff() -> None:
    """Byte-compare this machine's numbers against the ones in the writeup."""
    banner("compare against the published numbers")
    mine = ROOT / "results" / "results.json"
    theirs = PUBLISHED / "results.json"
    if not theirs.exists():
        # Not a pass. A reproduction step whose comparison did not happen has to
        # say so in the same voice it would use to say the numbers differ,
        # because the reader's question is "did the numbers reproduce" and the
        # honest answer here is "nothing was compared", not silence. Returning 0
        # made `reproduce` print a clean run having checked nothing.
        print(f"NOT COMPARED: there is no published baseline at {theirs}.\n"
              f"The author freezes one with `python run.py publish`. Until that "
              f"file is committed there is nothing for this step to check, and a "
              f"reproduction that compares nothing is not a reproduction.",
              file=sys.stderr)
        raise SystemExit(1)
    if not mine.exists():
        print(f"missing {mine}", file=sys.stderr)
        raise SystemExit(1)
    a, b = _canonical(mine), _canonical(theirs)

    # `publish` freezes three files and this compared one of them. RESULTS.md is
    # the document a reader actually reads, and every sentence in it is generated
    # from the same run, so a prose or table change that no number in
    # results.json can express would have reproduced "IDENTICAL" while the report
    # said something else. Compared byte for byte, because unlike results.json it
    # carries no timestamp to canonicalise away.
    # An absent published copy used to satisfy this: `not md_theirs.exists()`
    # short-circuited the whole comparison to true, so deleting the file being
    # compared against printed IDENTICAL. The missing `results.json` beside it was
    # already a hard exit, and these two are the same claim, so they now fail the
    # same way. Absence is not agreement.
    md_mine, md_theirs = ROOT / "results" / "RESULTS.md", PUBLISHED / "RESULTS.md"
    for path in (md_theirs, md_mine):
        if not path.exists():
            print(f"missing {path.relative_to(ROOT)}, so there is nothing to "
                  f"compare and nothing to claim")
            raise SystemExit(1)
    md_same = md_mine.read_bytes() == md_theirs.read_bytes()

    if a == b and md_same:
        print("IDENTICAL: every published number reproduced on this machine, and "
              "results/RESULTS.md is byte-identical to the published copy.")
        return
    if a == b and not md_same:
        print("DIFFERENT: every number in results.json reproduced, but "
              "results/RESULTS.md does not match the published copy byte for "
              "byte. Something the report says changed without a number "
              "changing.", file=sys.stderr)
        import difflib
        for line in list(difflib.unified_diff(
                md_theirs.read_text(encoding="utf-8").splitlines(),
                md_mine.read_text(encoding="utf-8").splitlines(),
                fromfile="published/RESULTS.md", tofile="this machine",
                lineterm=""))[:40]:
            print(line, file=sys.stderr)
        raise SystemExit(1)
    import difflib
    print("DIFFERENT. The first 40 differing lines:\n", file=sys.stderr)
    for line in list(difflib.unified_diff(
            b.splitlines(), a.splitlines(),
            fromfile="published", tofile="this machine", lineterm=""))[:40]:
        print(line, file=sys.stderr)
    raise SystemExit(1)


def _backend_or_die() -> None:
    import urllib.error
    import urllib.request
    for url in ("http://127.0.0.1:8100/v1/models", "http://127.0.0.1:11434/v1/models"):
        try:
            urllib.request.urlopen(url, timeout=2).read()
            print(f"model backend reachable at {url}")
            return
        except (urllib.error.URLError, OSError):
            continue
    print("No model backend is listening.\n"
          "  ollama:  ollama serve && ollama pull granite3.1-dense:8b\n"
          "  or CLI:  python tools/cli_openai_shim.py --port 8100 --cli codex "
          "--backend codex --default-model gpt-5.6-terra\n"
          "  or set --base-url to any OpenAI-compatible endpoint.\n"
          "Recording is optional. `python run.py reproduce` needs no backend at all.",
          file=sys.stderr)
    raise SystemExit(2)


def t_live_smoke() -> None:
    """Two criteria against a real model, to prove the live path still works."""
    _backend_or_die()
    banner("live smoke, 2 criteria")
    sh(PY, "scripts/compile_protocol.py", "--run", "runs/smoke", "--mode", "record",
       "--provider", "shim", "--seed", "7", "--limit", "2")


def t_live() -> None:
    """A full recording run. This is the only step that costs anything."""
    _backend_or_die()
    banner("live recording run")
    sh(PY, "scripts/compile_protocol.py", "--run", RUN, "--mode", "record",
       "--provider", "shim", "--seed", "7")
    sh(PY, "scripts/run_arms.py", "--run", RUN, "--mode", "record", "--arms", "TS,B0,B1")


def t_panel() -> None:
    """Rebuild the vendored panel from the Synthea archive. Not needed to reproduce."""
    banner("rebuild the panel from source")
    z = ROOT / "data" / "raw" / "synthea_r4.zip"
    if not z.exists():
        print(f"expected the archive at {z}\n"
              "  https://synthetichealth.github.io/synthea-sample-data/downloads/"
              "synthea_sample_data_fhir_r4_nov2021.zip\n"
              "  sha256 6d3c5433bcae4791bc5c30469d1445b430fb4894d5c13bda15fee0584bbd7778",
              file=sys.stderr)
        raise SystemExit(2)
    sh(PY, "scripts/build_panel.py")


def t_clean() -> None:
    """Remove derived output. Cassettes and vendored data survive on purpose."""
    banner("clean")
    for p in [ROOT / "results" / "results.json", ROOT / "results" / "RESULTS.md",
              ROOT / "runs" / "tierA" / "compiled",
              ROOT / "runs" / "tierA" / "cells"]:
        if p.is_dir():
            shutil.rmtree(p)
            print(f"removed {p}")
        elif p.exists():
            p.unlink()
            print(f"removed {p}")


TARGETS = {
    "check": t_check,
    "contamination": t_contamination,
    "links": t_links,
    "publish": t_publish,
    "environment": t_environment,
    "reproduce": t_reproduce,
    "verify": t_verify,
    "diff": t_diff,
    "live-smoke": t_live_smoke,
    "live": t_live,
    "panel": t_panel,
    "clean": t_clean,
}


def main() -> int:
    args = sys.argv[1:] or ["help"]
    if args[0] in ("help", "-h", "--help"):
        print(__doc__)
        print("targets: " + ", ".join(sorted(TARGETS)))
        return 0
    unknown = [a for a in args if a not in TARGETS]
    if unknown:
        print(f"unknown target(s): {', '.join(unknown)}\n"
              f"targets: {', '.join(sorted(TARGETS))}", file=sys.stderr)
        return 2
    t0 = time.time()
    for a in args:
        TARGETS[a]()
    print(f"\nOK  ({', '.join(args)} in {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
