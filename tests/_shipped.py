"""The file set a reader received, whether they cloned or unpacked an archive.

Seven gates asked git for it with `check=True`. An unpacked source archive has no
object database, so the call raised, and `python run.py reproduce` failed with
thirteen errors for a judge who downloaded the zip instead of cloning. Following
the guide is not a way to fail a gate.

The question those gates ask is "what did the reader actually get". Git is the
better answer only where there is a git: a working tree can carry untracked files
that no clone contains, and that gap is what a plain `Path.exists()` walk misses.
An archive has no such gap, because unpacking it produces exactly what was packed.
So git first, then `MANIFEST.txt`, which is written from git and travels inside
the archive. The caller can ask whether there is a git when the distinction
changes what it should say.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.txt"


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


def _from_manifest(globs: tuple[str, ...]) -> list[str] | None:
    """MANIFEST.txt, written from git and carried inside the archive.

    A directory walk is not the same question. It picks up whatever the run just
    generated: `.pytest_cache/` and the uncommitted cells under `runs/` took one
    gate's byte total from 57 MB to 105 MB and made another report a carriage
    return in a file that does not ship.
    """
    if not MANIFEST.is_file():
        return None
    names = [ln for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln]
    if not names:
        return None
    return _filter(names, globs)


def _filter(names: list[str], globs: tuple[str, ...]) -> list[str]:
    if not globs:
        return names
    return [n for n in names if any(fnmatch.fnmatch(n, g) for g in globs)]


def shipped(*globs: str) -> list[str]:
    """Repository-relative names of what shipped, filtered by optional globs."""
    found = _from_git(globs)
    if found is not None:
        return found
    found = _from_manifest(globs)
    if found is not None:
        return found
    raise RuntimeError(
        "no git and no MANIFEST.txt, so there is no way to tell what shipped "
        "from what this directory happens to contain. Clone the repository or "
        "unpack the source archive rather than copying a working tree.")


def shipped_paths(*globs: str) -> list[Path]:
    return [ROOT / n for n in shipped(*globs)]
