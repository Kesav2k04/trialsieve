"""Every headline figure in the prose, recomputed from `results/results.json`.

Three one-off gates already existed: the cost table, the changelog's size, the
sensitivity section. Each was written after a number in a document had drifted
from the artifact it came from, and each covers exactly the number that drifted.
Everything else was on trust: 21.75%, 19.15% against 18.44%, 29.2%, 43.8%, the
46.15% panel reduction and the 18 false exclusions behind its VOID all sat in
prose with nothing tying them to the run.

This is a register rather than a rule. A blanket "every number in markdown must
appear in results.json" would flag the many that legitimately come from somewhere
else, and would be silenced within a week. So each claim below names the sentence
it lives in, the path in the run that produces it, and how it is rendered. A claim
whose sentence stops matching fails rather than passing quietly, because a
reworded sentence is how a checked number becomes an unchecked one.

Every literal space in a pattern is written as a whitespace class. Markdown prose
wraps, and the first version of this register went red the moment a sentence it
anchors on was rewrapped across a line, which is a reformat rather than drift.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "results.json"


def _pcts(x: float) -> set[str]:
    """Every rendering of a rate this repository actually uses.

    `43.75%` and `43.8%` are the same measurement written for two audiences and
    both appear. Accepting either is not laxity: what is being checked is that
    the prose tracks the run, and a gate that forced one rounding everywhere
    would be enforcing a house style rather than a fact.
    """
    return {f"{x * 100:.2f}".rstrip("0").rstrip("."), f"{x * 100:.1f}",
            f"{x * 100:.2f}", f"{x * 100:.0f}"}


def _cell(run: dict, group: str, arm: str, field: str) -> set[str]:
    return _pcts(run["groups"][group]["cell_scores"][arm][field])


#: name, the documents it may appear in, the anchored pattern whose one group is
#: the figure, and a function from the run to the acceptable renderings.
CLAIMS: list[tuple] = [
    ("TS coverage on the paired 400-cell sample",
     ("README.md", "docs/EVAL_PROTOCOL.md", "docs/SCORECARD.md"),
     r"TrialSieve's\s+([\d.]+)%\s+on\s+the\s+paired\s+sample",
     lambda r: _cell(r, "b2_10p", "TS", "coverage")),
    ("B2 coverage on the paired sample",
     ("docs/EVAL_PROTOCOL.md",),
     r"B2\s+answers\s+([\d.]+)%\s+of\s+cells",
     lambda r: _cell(r, "b2_10p", "B2", "coverage")),
    ("B2 silent error on the paired sample",
     ("README.md", "docs/COST.md"),
     r"wrong\s+on\s+([\d.]+)%\s+of\s+every\s+cell",
     lambda r: _cell(r, "b2_10p", "B2", "ser")),
    ("TS coverage on the full grid",
     ("README.md", "docs/EVAL_PROTOCOL.md"),
     r"([\d.]+)%\s+against\s+18\.44%",
     lambda r: _cell(r, "k0_seed7", "TS", "coverage")),
    ("panel reduction",
     ("README.md",),
     r"([\d.]+)%\s+panel\s+reduction\s+with\s+\d+\s+false\s+exclusions",
     lambda r: _pcts(r["groups"]["k0_seed7"]["panel_scores"]["TS"]["reduction"])),
    ("false exclusions behind the VOID",
     ("README.md",),
     r"panel\s+reduction\s+with\s+(\d+)\s+false\s+exclusions",
     lambda r: {str(r["groups"]["k0_seed7"]["panel_scores"]["TS"]
                    ["false_exclusions"])}),
    ("compiled share of segmented criteria",
     ("README.md", "SUBMISSION.md"),
     r"which\s+is\s+([\d.]+)%,\s+and\s+the\s+repair",
     lambda r: _pcts(r["criterion_coverage"]["compiled_of_segmented"])),
    ("criteria compiled, of those segmented",
     ("README.md",),
     r"(\d+)\s+of\s+65\s+segmented\s+criteria\s+compile",
     lambda r: {str(r["criterion_coverage"]["n_compiled"])}),
    # The lead table in README.md. It is the first thing a reader sees and it
    # was the only table in the repository whose figures were typed rather than
    # read back, which is exactly the drift this register exists for.
    ("lead table, B2 silent error",
     ("README.md",),
     r"nothing\s+on\s+the\s+page\s+to\s+say\s+so\s+\|\s+([\d.]+)%",
     lambda r: _cell(r, "b2_10p", "B2", "ser")),
    ("lead table, TS silent error",
     ("README.md",),
     r"nothing\s+on\s+the\s+page\s+to\s+say\s+so\s+\|[^|]+\|\s+\*\*([\d.]+)%\*\*",
     lambda r: _cell(r, "b2_10p", "TS", "ser")),
    ("lead table, B2 false exclusions",
     ("README.md",),
     r"screens\s+wrongly\s+ruled\s+out,\s+of\s+30\s+\|\s+(\d+)\s+\|",
     lambda r: {str(r["groups"]["b2_10p"]["panel_scores"]["B2"]["false_exclusions"])}),
    ("lead table, TS false exclusions",
     ("README.md",),
     r"screens\s+wrongly\s+ruled\s+out,\s+of\s+30\s+\|[^|]+\|\s+\*\*(\d+)\*\*",
     lambda r: {str(r["groups"]["b2_10p"]["panel_scores"]["TS"]["false_exclusions"])}),
    ("lead table, B2 wrong MEETS",
     ("README.md",),
     r"who\s+do\s+not\s+qualify\s+\|\s+(\d+)\s+\|",
     lambda r: {str(r["groups"]["b2_10p"]["cell_scores"]["B2"]["n_false_meets"])}),
    ("lead table, B2 coverage",
     ("README.md",),
     r"cells\s+it\s+answers\s+at\s+all\s+\|\s+([\d.]+)%",
     lambda r: _cell(r, "b2_10p", "B2", "coverage")),
    ("lead table, TS coverage",
     ("README.md",),
     r"cells\s+it\s+answers\s+at\s+all\s+\|[^|]+\|\s+([\d.]+)%",
     lambda r: _cell(r, "b2_10p", "TS", "coverage")),
    ("lead table, B2 resolved correctly per screen",
     ("README.md",),
     r"the\s+registered\s+co-primary\s+\|\s+\*\*([\d.]+)\*\*",
     lambda r: {f"{r['groups']['b2_10p']['cell_scores']['B2']['resolved_correct_per_screen']:.2f}"}),
    ("lead table, TS resolved correctly per screen",
     ("README.md",),
     r"the\s+registered\s+co-primary\s+\|[^|]+\|\s+([\d.]+)\s*\|",
     lambda r: {f"{r['groups']['b2_10p']['cell_scores']['TS']['resolved_correct_per_screen']:.2f}"}),
    ("patients behind the paired sample",
     ("README.md",),
     r"Those\s+400\s+cells\s+are\s+\*\*(\d+)\s+patients\*\*",
     lambda r: {str(r["groups"]["b2_10p"]["cell_scores"]["B2"]["n_cells"]
                    // r["criterion_coverage"]["n_gold"])}),
]


@pytest.fixture(scope="module")
def run() -> dict:
    if not RESULTS.is_file():
        pytest.skip("no scored run in this checkout; nothing to check prose against")
    return json.loads(RESULTS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("claim", CLAIMS, ids=lambda c: c[0])
def test_the_prose_figure_is_the_run_figure(claim, run) -> None:
    name, docs, pattern, expected = claim
    want = expected(run)
    found: list[tuple[str, str]] = []
    for d in docs:
        path = ROOT / d
        if not path.is_file():
            continue
        for m in re.finditer(pattern, path.read_text(encoding="utf-8")):
            found.append((d, m.group(1)))
    assert found, (
        f"{name}: the sentence this gate anchors on is in none of {list(docs)}. "
        f"A reworded sentence turns a checked number into an unchecked one, so "
        f"this fails rather than passing. Pattern: {pattern!r}")
    wrong = [(d, got) for d, got in found if got not in want]
    assert not wrong, (
        f"{name}: prose says {sorted({g for _, g in wrong})} and the run gives "
        f"{sorted(want)}. Occurrences: {wrong}")


def test_the_register_would_notice_a_changed_run() -> None:
    """The control. Every assertion above is satisfied by a broken lookup too.

    If `expected` ignored its argument, or `_pcts` returned every string, this
    whole file would pass against any run at all. This feeds the register a run
    with one figure moved and requires the matching claim to reject it.
    """
    if not RESULTS.is_file():
        pytest.skip("no scored run in this checkout")
    real = json.loads(RESULTS.read_text(encoding="utf-8"))
    moved = json.loads(json.dumps(real))
    moved["groups"]["k0_seed7"]["panel_scores"]["TS"]["false_exclusions"] += 1
    _name, docs, pattern, expected = next(
        c for c in CLAIMS if c[0] == "false exclusions behind the VOID")
    got = re.search(pattern, (ROOT / docs[0]).read_text(encoding="utf-8"))
    assert got, "the anchor sentence is gone; the control checked nothing"
    assert got.group(1) in expected(real), "the control disagrees with the real run"
    assert got.group(1) not in expected(moved), (
        "moving the figure in the run did not change what this register expects, "
        "so it is not reading the run")
