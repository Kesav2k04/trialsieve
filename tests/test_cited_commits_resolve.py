"""A commit hash quoted in prose has to name a commit this repository contains.

Two entries cited one. One of them, `7e0faaa`, had stopped resolving: the history
was rewritten between the sentence being written and the submission being
assembled, every hash moved, and nothing compared the prose to the repository. A
reader who ran `git show` on it got `unknown revision`, which is the worst way to
find out that a citation was decorative.

A hash in a document is a fixed point. It is only correct until the next rewrite,
and it cannot be regenerated from anything, so this gate exists rather than a
generator. It is deliberately narrow: it reads the explicit `commit \x60...\x60`
form, because that is the form a reader will paste into `git show`.

Skipped rather than failed when there is no git here. An unpacked source archive
carries the documents without the object database, and a gate that fails on a
reader following the reproduction guide is a broken gate.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: The form a reader can act on: the word, then the hash in backticks.
CITATION = re.compile(r"commit `([0-9a-f]{7,40})`")


def _has_git() -> bool:
    r = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                       capture_output=True, text=True)
    return r.returncode == 0


def _resolves(rev: str) -> bool:
    r = subprocess.run(["git", "cat-file", "-t", rev], cwd=ROOT,
                       capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "commit"


def _tracked_docs() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT,
                         capture_output=True, text=True, check=False).stdout
    return [ROOT / n for n in out.split("\n") if n.strip()]


def test_every_cited_commit_is_in_this_repository():
    if not _has_git():
        pytest.skip("no git object database here, so a hash cannot be resolved")
    dangling = []
    checked = 0
    for doc in _tracked_docs():
        if not doc.is_file():
            continue
        for rev in CITATION.findall(doc.read_text(encoding="utf-8")):
            checked += 1
            if not _resolves(rev):
                dangling.append(f"{doc.relative_to(ROOT).as_posix()} cites {rev}")
    assert not dangling, (
        "these documents cite a commit this repository does not contain:\n  "
        + "\n  ".join(dangling)
        + "\nA hash does not survive a history rewrite. Say what changed instead.")
    print(f"checked {checked} cited commit(s)")


def test_the_check_can_fail():
    """A gate over zero occurrences reports a pass it did not earn. This plants
    the shape and requires the resolver to reject it, so the check is known to
    work on the day somebody writes the next citation."""
    if not _has_git():
        pytest.skip("no git object database here, so a hash cannot be resolved")
    assert CITATION.findall("widened in commit `deadbee`, after a retry") == ["deadbee"]
    assert not _resolves("deadbee"), "a fabricated hash resolved, so this gate is blind"
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    assert _resolves(head), "HEAD did not resolve, so the resolver rejects everything"
