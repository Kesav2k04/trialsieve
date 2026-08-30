"""The transcript `REPRODUCE.md` quotes is a substring of the file it names.

That section opens by saying the block below is "captured stdout rather than a
sample typed into this file". It was typed into this file, once, and then the
capture was regenerated four times around it. By the time a reviewer read them
together the guide quoted `OK  (reproduce in 142.6s)` and the transcript said
151.3s, on the same page as a sentence promising they were the same bytes. A third
reading, 154.1s, sat eighty lines below in a different paragraph.

Three wall-clocks for one command, in a repository whose second paragraph is that a
number appearing twice disagrees with itself eventually. So the quoted block is now
compared against the file, line by line, and the line count in the prose is counted.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "REPRODUCE.md"
CAPTURE = ROOT / "docs" / "reproduce_transcript.txt"


@pytest.fixture(scope="module")
def quoted() -> list[str]:
    """The indented block under the heading that promises it is captured output."""
    text = GUIDE.read_text(encoding="utf-8")
    m = re.search(r"^## What a successful run looks like$(.*?)(?=^## |\Z)", text,
                  re.M | re.S)
    assert m, "the section this test anchors on was renamed"
    # The first indented run only. The section quotes the tail and then, a
    # paragraph later, indents one more line of output while explaining what to
    # do if the comparison fails. Folding the two together made the is-this-the
    # ending check compare a seven-line block against a six-line tail.
    block: list[str] = []
    for ln in m.group(1).split(chr(10)):
        if ln.startswith("    "):
            block.append(ln[4:])
        elif ln.strip() and block:
            break
    assert block, "the section carries no indented block, so nothing was compared"
    return block


def test_every_quoted_line_is_in_the_capture(quoted) -> None:
    if not CAPTURE.is_file():
        pytest.skip("no captured transcript in this checkout")
    have = set(CAPTURE.read_text(encoding="utf-8").split("\n"))
    missing = [ln for ln in quoted if ln.strip() and ln not in have]
    assert not missing, (
        f"{len(missing)} line(s) the guide presents as captured stdout are not in "
        f"{CAPTURE.relative_to(ROOT).as_posix()}: {missing}. Re-run "
        f"`python run.py reproduce` again, copy the real tail, or stop "
        f"calling it captured.")


def test_the_quoted_tail_is_the_tail(quoted) -> None:
    """Not just present somewhere: the last lines, in order."""
    if not CAPTURE.is_file():
        pytest.skip("no captured transcript in this checkout")
    have = CAPTURE.read_text(encoding="utf-8").split("\n")
    body = [ln for ln in quoted if ln.strip()]
    tail = [ln for ln in have if ln.strip()][-len(body):]
    assert body == tail, (
        "the guide quotes lines that are in the transcript but not its ending, so "
        "it is presenting a middle as an outcome")


def test_the_prose_counts_the_transcripts_lines() -> None:
    if not CAPTURE.is_file():
        pytest.skip("no captured transcript in this checkout")
    m = re.search(r"The whole ([\d,]+)-line", GUIDE.read_text(encoding="utf-8"))
    assert m, "the sentence stating the transcript's length was reworded"
    n = len(CAPTURE.read_text(encoding="utf-8").rstrip("\n").split("\n"))
    assert int(m.group(1).replace(",", "")) == n, (
        f"the guide says {m.group(1)} lines and the transcript has {n}")


def test_only_one_wall_clock_is_quoted_as_the_headline() -> None:
    """One figure for the clean run, and it is the one the capture recorded.

    The README said 154s, the transcript said 142.6s and a paragraph eighty lines
    down said 154.1s. Any of the three could have been right; a reader had no way
    to know which, which is the state this whole repository argues against. The
    figure is therefore taken out of the capture and both documents have to agree
    with the capture, rather than with each other.
    """
    if not CAPTURE.is_file():
        pytest.skip("no captured transcript in this checkout")
    ok = re.search(r"OK\s+\(reproduce in ([\d.]+)s\)",
                   CAPTURE.read_text(encoding="utf-8"))
    assert ok, "the transcript no longer ends with the runner's own timing line"
    measured = ok.group(1)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"One command from a clean clone, ([\d.]+)s captured", readme)
    assert m, "the README's reproduction row was reworded"
    assert m.group(1) == measured, (
        f"the README says {m.group(1)}s from a clean clone and the capture it "
        f"points at recorded {measured}s")

    guide = GUIDE.read_text(encoding="utf-8")
    assert f"**{measured} seconds** on a Windows laptop" in guide, (
        f"REPRODUCE.md does not give {measured}s as the reading its own capture "
        f"recorded")
