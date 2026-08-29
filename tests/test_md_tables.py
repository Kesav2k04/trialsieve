"""Generated markdown tables must line up in a monospace reader.

The report emitted `| TS | 30 | 18 | 60.0% |` under a wider heading row, which a
repository page renders into a neat grid and every other reader does not. The two
readers that matter most here get the characters as written: a person opening the
raw `.md`, and a viewer watching a table go past on a video frame at reading
speed. Under a ragged header, finding which number sits under which column is a
lookup rather than a reading.

`scripts/_md_tables.py` pads them once at the point a document is written. These
tests hold the two properties that make that safe to apply blindly (it changes
only spacing, and running it twice changes nothing) and then check the documents
the repository actually ships, so a new generator that forgets the call fails
here rather than showing up ragged in the video.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _md_tables import align  # noqa: E402

RAGGED = (
    "| arm | screens | reduction |\n"
    "|---|---|---|\n"
    "| TS | 30 | 60.0% |\n"
    "| B0 | 30 | 100.0% |\n"
)


def test_it_pads_the_columns_to_one_width():
    out = align(RAGGED).splitlines()
    assert len({len(l) for l in out}) == 1, (
        f"rows still differ in width: {[len(l) for l in out]}")


def test_it_changes_nothing_but_spacing():
    """The safety property. Padding must never move a number to another column."""
    def cells(text):
        return [[c.strip() for c in l.strip().strip("|").split("|")]
                for l in text.strip().splitlines()]

    before, after = cells(RAGGED), cells(align(RAGGED))
    assert len(before) == len(after)
    for b, a in zip(before, after):
        if set("".join(b)) <= set("-:"):
            continue  # the separator row is the one line allowed to change
        assert b == a, f"a cell changed: {b} became {a}"


def test_running_it_twice_changes_nothing():
    once = align(RAGGED)
    assert align(once) == once


def test_it_keeps_alignment_colons():
    src = "| a | b |\n|:---|---:|\n| 1 | 2 |\n"
    sep = align(src).splitlines()[1]
    assert sep.startswith("|:") and sep.endswith(":|"), sep


def test_it_leaves_a_fenced_table_alone():
    """A table inside a fence is being shown as text, not used as one."""
    src = "```\n| a | bbbb |\n|---|---|\n```\n"
    assert align(src) == src


def test_it_leaves_a_ragged_table_alone():
    """Padding a row with a missing cell would invent one, and inventing one
    would move every number after it under the wrong heading."""
    src = "| a | b | c |\n|---|---|---|\n| 1 | 2 |\n"
    assert align(src) == src


def test_every_generated_document_is_aligned():
    """The gate. A generator that forgets the call fails here, not in the video."""
    generated = [
        "results/RESULTS.md", "docs/COUNTEREXAMPLE.md", "docs/COST.md",
        "docs/sample_worklist.md", "docs/CONTAMINATION.md",
    ]
    ragged = []
    for rel in generated:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if align(text) != text:
            ragged.append(rel)
    assert not ragged, (
        f"these are generated with unaligned tables: {ragged}. The writer that "
        f"produces each one should pass its text through `_md_tables.align`.")
