"""The amendment list must count itself correctly.

`docs/EVAL_PROTOCOL.md` opens the amendments with a promise: "A reader comparing
this document to the repository will find these N differences and no others; if
they find a seventh, this list is the thing that is wrong." That promise is the
only thing standing between a pre-registered protocol and one quietly edited to
match what happened, and it was written as a word in prose beside a list that
grows. The list reached seven while the sentence still said six.

A count in prose next to the thing it counts is a claim the file can check about
itself, so it does.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "EVAL_PROTOCOL.md"

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def test_the_stated_number_of_amendments_is_the_number_of_amendments():
    text = PROTOCOL.read_text(encoding="utf-8")

    m = re.search(r"will find these (\w+) differences and no others", text)
    assert m, ("the sentence that promises the amendment list is complete has been "
               "reworded. It is the protocol's central integrity claim; update this "
               "test deliberately rather than deleting it.")
    claimed = WORDS.get(m.group(1).lower())
    assert claimed is not None, f"unrecognised number word {m.group(1)!r}"

    headings = re.findall(r"^\*\*A(\d+),", text, re.M)
    assert headings, "no amendment headings found; the A<n> format has changed"
    actual = len(headings)

    assert claimed == actual, (
        f"the protocol says {claimed} differences and lists {actual}. An amendment "
        f"list that miscounts itself is the one document a reader checks the "
        f"others against.")


def test_the_amendments_are_numbered_without_a_gap():
    """A missing A4 reads as an amendment that was deleted rather than renumbered."""
    text = PROTOCOL.read_text(encoding="utf-8")
    got = [int(n) for n in re.findall(r"^\*\*A(\d+),", text, re.M)]
    assert got == list(range(1, len(got) + 1)), (
        f"amendment numbers are {got}, which is not 1..{len(got)}")
