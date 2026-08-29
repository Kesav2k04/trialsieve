"""The task runner. `python run.py reproduce` is the whole reproduction.

There is no `make` here, and no `make` on a stock Windows box either, so the
entry point is a Python file that behaves identically on the three platforms a
judge might be sitting at. It has no dependencies. Neither does the project:
every import in `src/`, `evaluation/` and `scripts/` is from the standard
library, and `pytest` is needed only to run the test gate.

    python run.py check          the engine gate, about a second
    python run.py reproduce      the published numbers, offline, from cassettes
    python run.py verify         the four checks that make replay falsifiable
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
    """The engine gate. The protocol makes this a precondition for a scored run."""
    banner("engine gate")
    sh(PY, "-m", "pytest", "-q")


def t_environment() -> None:
    """Write down what this machine is, so a differing number has somewhere to point."""
    banner("environment")
    info = {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cwd": str(ROOT),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        info["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        info["git_dirty"] = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip())
    except OSError:
        pass
    out = ROOT / "results" / "environment.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(info, indent=1))


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

    banner("replay the compile")
    sh(PY, "scripts/compile_protocol.py", "--run", run, "--mode", "replay",
       "--provider", "shim", "--seed", "7")

    banner("run the arms")
    sh(PY, "scripts/run_arms.py", "--run", run, "--mode", "replay", "--arms", "TS,B0,B1")

    banner("audit for recall")
    sh(PY, "scripts/contamination.py", "--run", run)

    banner("regenerate the documents that quote numbers")
    sh(PY, "scripts/counterexample.py", "--run", run, "--mode", "replay")
    sh(PY, "scripts/gate_demo.py", "--run", run)
    sh(PY, "scripts/trajectories.py", "--run", run)

    banner("check every path a document points at")
    sh(PY, "scripts/linkcheck.py")

    banner("cost and runtime")
    sh(PY, "scripts/costs.py")

    banner("score and report")
    sh(PY, "scripts/report.py", "--run", run, "--out", "results")

    t_verify(run)
    t_diff()


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
        print(f"no published baseline at {theirs}; nothing to compare against yet")
        return
    if not mine.exists():
        print(f"missing {mine}", file=sys.stderr)
        raise SystemExit(1)
    a, b = _canonical(mine), _canonical(theirs)
    if a == b:
        print("IDENTICAL: every published number reproduced on this machine.")
        return
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
