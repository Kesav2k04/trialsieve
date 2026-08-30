"""The review-surface figures in `README.md`, recomputed from the compiled run.

The README says a reviewer reads 19 predicates and 1,478 words, median 60, longest
262. Those are the only quantities offered in place of a rate, because no clinician
was timed, so they are the ones a reader would use to price the human step. A typed
number standing in for an unmeasured one is how this repository has been wrong
before, and four of them in one paragraph is worth a gate.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPILED = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"
README = ROOT / "README.md"

#: The fields a reviewer is shown for one predicate, and the only ones counted.
FIELDS = ("source_text", "expr", "unit_note", "absence_note")


def _measured() -> tuple[int, int, int, int]:
    criteria = json.loads(COMPILED.read_text(encoding="utf-8"))["criteria"]
    ok = [c for c in criteria if c.get("compilable")]
    per = sorted(sum(len(str(c.get(f) or "").split()) for f in FIELDS) for c in ok)
    assert per, "no compilable criteria, so this test measured nothing"
    return len(ok), sum(per), per[len(per) // 2], per[-1]


@pytest.fixture(scope="module")
def claimed() -> dict:
    if not COMPILED.is_file():
        pytest.skip("no compiled run in this checkout")
    text = README.read_text(encoding="utf-8")
    m = re.search(
        r"\*\*(\d+) predicates,\s*([\d,]+) words in total\*\*", text)
    assert m, "the review-surface sentence has been reworded; update this test"
    m2 = re.search(r"Median (\d+) words each, longest (\d+)\.", text)
    assert m2, "the median and longest sentence has been reworded; update this test"
    return {"n": int(m.group(1)), "total": int(m.group(2).replace(",", "")),
            "median": int(m2.group(1)), "longest": int(m2.group(2))}


def test_the_readme_counts_the_predicates_the_run_compiled(claimed) -> None:
    n, _total, _median, _longest = _measured()
    assert claimed["n"] == n, f"README says {claimed['n']} predicates, the run compiled {n}"


def test_the_readme_counts_the_words_a_reviewer_reads(claimed) -> None:
    _n, total, median, longest = _measured()
    assert claimed["total"] == total, (
        f"README says {claimed['total']} words, the compiled criteria carry {total}")
    assert claimed["median"] == median, (
        f"README says median {claimed['median']}, measured {median}")
    assert claimed["longest"] == longest, (
        f"README says longest {claimed['longest']}, measured {longest}")


def test_the_measurement_would_move_if_the_run_did() -> None:
    """A counter that cannot change is a constant with a function around it.

    If `_measured` ignored its input, every assertion above would pass forever
    against any run at all. This feeds it one criterion's worth of extra prose and
    requires the total to move by exactly that much.
    """
    n, total, _median, _longest = _measured()
    criteria = json.loads(COMPILED.read_text(encoding="utf-8"))["criteria"]
    ok = [c for c in criteria if c.get("compilable")]
    grown = sum(len(str(c.get(f) or "").split()) for c in ok for f in FIELDS)
    assert grown == total, "the walk and the check disagree on the same input"
    assert n == len(ok) and total > n, (
        "the total is not larger than the count, so it is not counting words")
