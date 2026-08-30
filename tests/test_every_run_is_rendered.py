"""Every committed trajectory log has a page beside it, and the page is current.

`runs/checker_b/` shipped 180 raw JSONL and nothing else, and the three vocabulary
probes shipped 63 more. The scored run had 235 rendered pages and a sorted index,
and its index pointed a reader at the second labeller's directory as evidence that
the arm was recorded "to the same standard". It was recorded to the same standard
and published to a worse one: an arm this project is measured against was readable
only by somebody willing to parse JSONL.

`run.py reproduce` now renders every run git tracks. This checks the result rather
than the intention, and it checks freshness rather than presence, because a
rendered page that predates its log is the failure a presence check waves through.
"""
from __future__ import annotations

import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _tracked_runs() -> dict[str, list[Path]]:
    """Run directory -> its tracked trajectory logs, from git rather than disk.

    Disk here also holds development and smoke runs that `.gitignore` keeps out.
    Those are nobody else's problem; what a reader receives is what git tracks.
    """
    from _shipped import shipped
    out: dict[str, list[Path]] = {}
    for line in shipped("runs/*/trajectories/*.jsonl"):
        out.setdefault(line.split("/")[1], []).append(ROOT / line)
    return out


@pytest.fixture(scope="module")
def runs() -> dict[str, list[Path]]:
    found = _tracked_runs()
    if not found:
        pytest.skip("no trajectories tracked in this checkout")
    # The check that stops this file from passing by finding nothing. Five runs
    # ship logs; a resolver that returned one of them would pass every assertion
    # below while leaving four unrendered, which is the exact defect that was here.
    assert len(found) >= 5, (
        f"only {sorted(found)} carry tracked trajectories; if a run was removed on "
        f"purpose, lower this number, and if it was not, that is the bug")
    return found


def test_every_log_has_a_page(runs) -> None:
    missing = [str(j.relative_to(ROOT).as_posix())
               for logs in runs.values() for j in logs
               if not j.with_suffix(".md").is_file()]
    assert not missing, (
        f"{len(missing)} trajectory logs have no rendered page, first {missing[:3]}")


def test_every_run_has_an_index(runs) -> None:
    for name in runs:
        idx = ROOT / "runs" / name / "trajectories" / "index.md"
        assert idx.is_file(), f"runs/{name} has logs and no index"
        assert "read this one first" in idx.read_text(encoding="utf-8").lower() or \
               "read these" in idx.read_text(encoding="utf-8").lower(), (
            f"runs/{name}/trajectories/index.md names no exemplar, so a reader "
            f"arrives at a sorted list with no way in")


def _rerender(name: str, tmp: str) -> None:
    r = subprocess.run(
        [sys.executable, "scripts/trajectories.py",
         "--run", f"runs/{name}", "--out", tmp],
        cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, f"rendering runs/{name} failed: {r.stderr[-400:]}"


def _extra_logs(name: str, tracked: list[Path]) -> list[str]:
    """Trajectory logs on this disk that git does not have.

    `REPRODUCE.md` tells a reader to run the baseline arm under a tag of their
    choosing, and doing so writes new logs into a tracked directory. That is the
    guide working. A freshness check that then failed would be reporting the
    reader's own correct action as a defect, so what is committed is compared and
    what they added is named rather than counted against them.
    """
    live = ROOT / "runs" / name / "trajectories"
    known = {p.resolve() for p in tracked}
    return sorted(str(p.relative_to(live)).replace("\\", "/")
                  for p in live.rglob("*.jsonl") if p.resolve() not in known)


def test_the_pages_are_current(runs) -> None:
    """Re-render into a scratch directory and compare the committed pages, byte for byte."""
    for name, tracked in runs.items():
        with tempfile.TemporaryDirectory() as tmp:
            _rerender(name, tmp)
            live = ROOT / "runs" / name / "trajectories"
            stale = []
            for log in tracked:
                rel = log.relative_to(live).with_suffix(".md")
                fresh, committed = Path(tmp) / rel, live / rel
                if not fresh.is_file():
                    stale.append(f"{rel.as_posix()} (renders to nothing)")
                elif not committed.is_file() or not filecmp.cmp(
                        fresh, committed, shallow=False):
                    stale.append(rel.as_posix())
            assert not stale, (
                f"runs/{name}: {len(stale)} committed page(s) differ from what the "
                f"logs render to now, first {stale[:3]}. Run "
                f"`python scripts/trajectories.py --run runs/{name}`.")


def test_each_index_is_current(runs) -> None:
    """The index counts and sorts the whole directory, so it is checked separately.

    A scratch run adds a log and every total in the index moves, correctly. Where
    that has happened this says so and names the files rather than passing quietly
    on a comparison it did not make.
    """
    checked = 0
    for name, tracked in runs.items():
        extra = _extra_logs(name, tracked)
        if extra:
            print(f"runs/{name}: index not compared, {len(extra)} untracked log(s) "
                  f"in this checkout, first {extra[:3]}")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            _rerender(name, tmp)
            live = ROOT / "runs" / name / "trajectories" / "index.md"
            assert filecmp.cmp(Path(tmp) / "index.md", live, shallow=False), (
                f"runs/{name}/trajectories/index.md is not what these logs render "
                f"to. Run `python scripts/trajectories.py --run runs/{name}`.")
            checked += 1
    assert checked, (
        "every run directory holds an untracked log, so no index was compared. "
        "Move or delete the scratch runs and re-run this.")


def test_the_scored_run_is_the_only_one_claiming_the_six_agent_layout(runs) -> None:
    """That table names directories the other runs do not have.

    Generated into all five, it told a reader of the second labeller's index to
    look in `compiler/` and `critic/`, on the same page as a table listing the one
    agent that had actually run.
    """
    claiming = [n for n in runs
                if "## Which agent is where" in
                (ROOT / "runs" / n / "trajectories" / "index.md").read_text(
                    encoding="utf-8")]
    assert claiming == ["tierA"], (
        f"the six-agent layout is claimed by {claiming}; only the scored run has "
        f"those directories")
