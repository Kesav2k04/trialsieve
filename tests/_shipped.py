"""The file set a reader received, whether they cloned or unpacked an archive.

Seven gates asked git for it with `check=True`. An unpacked source archive has no
object database, so the call raised, and `python run.py reproduce` failed with
thirteen errors for a judge who downloaded the zip instead of cloning. Following
the guide is not a way to fail a gate.

The question those gates ask is "what did the reader actually get". Git is the
better answer only where there is a git: a working tree can carry untracked files
that no clone contains, and that gap is what a plain `Path.exists()` walk misses.
An archive has no such gap, because unpacking it produces exactly what was packed.
So git first, then the walk, and the caller can ask which one answered when the
distinction changes what it should say.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def has_git() -> bool:
    """Whether there is an object database here at all.

    A gate that needs history rather than a file list, such as one resolving a
    commit, has nothing to fall back to and should skip on this.
    """
    return subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                          capture_output=True).returncode == 0


def _from_git(globs: tuple[str, ...]) -> list[str] | None:
    r = subprocess.run(["git", "ls-files", "-z", *globs], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    names = [n for n in r.stdout.split(chr(0)) if n]
    return names or None


def _from_walk(globs: tuple[str, ...]) -> list[str]:
    names = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                   if p.is_file() and ".git" not in p.parts)
    if not globs:
        return names
    return [n for n in names if any(fnmatch.fnmatch(n, g) for g in globs)]


def shipped(*globs: str) -> list[str]:
    """Repository-relative names of what shipped, filtered by optional globs."""
    return _from_git(globs) or _from_walk(globs)


def shipped_paths(*globs: str) -> list[Path]:
    return [ROOT / n for n in shipped(*globs)]
