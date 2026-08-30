"""MANIFEST.txt is what a reader without git is told shipped, so it has to be true.

Several gates ask what the reader actually received. In a clone git answers. In an
unpacked source archive there is no object database, and a directory walk answers a
different question: it counts whatever the run just generated, which took the disk
gate's byte total from 57 MB to 105 MB and made the line-endings gate report a
carriage return in `.pytest_cache/README.md`, a file that does not ship.

So the answer is written down once and carried inside the archive. A written-down
answer goes stale, which is what this checks. It compares the file to git rather
than regenerating it, because a gate that regenerates what it grades cannot fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import manifest  # noqa: E402
from _shipped import has_git  # noqa: E402


def test_it_lists_exactly_what_git_tracks() -> None:
    if not has_git():
        pytest.skip("no object database here, so there is nothing to compare against")
    listed, tracked = manifest.read(), manifest.from_git()
    added = sorted(set(tracked) - set(listed))
    gone = sorted(set(listed) - set(tracked))
    assert not added and not gone, (
        f"MANIFEST.txt has drifted from git: {len(added)} shipped and not listed, "
        f"{len(gone)} listed and not shipped. First few: {(added + gone)[:5]}. "
        f"Run `python scripts/manifest.py --write`.")


def test_it_lists_itself() -> None:
    """It is not a fixed point, and the way to show that is that it survives being
    in its own list. The content is the set of names; adding a name changes the set
    exactly once, and the bytes then settle."""
    assert "MANIFEST.txt" in manifest.read()


def test_the_comparison_can_fail() -> None:
    """A drop-one control. Without it this passes whenever both sides are read the
    same wrong way, which is the failure mode of every check written as an equality
    between two calls into the same module."""
    listed = manifest.read()
    assert listed, "MANIFEST.txt is empty, so the comparison above has no content"
    damaged = listed[1:]
    assert set(listed) - set(damaged), "removing an entry changed nothing"


def test_the_files_it_lists_are_here() -> None:
    """The list is only useful if it resolves. A name that does not is either a
    stale entry or an archive that unpacked short."""
    missing = [n for n in manifest.read() if not (ROOT / n).exists()]
    assert not missing, (
        f"{len(missing)} file(s) in MANIFEST.txt are not in this tree. "
        f"First few: {missing[:5]}")
