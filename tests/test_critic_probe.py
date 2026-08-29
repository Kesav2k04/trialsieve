"""A planted defect that did not plant is a critic failure that did not happen.

`evaluation/critic_probe.py` measures whether the critic catches deliberately
broken predicates. Every number it reports rests on an assumption nothing was
checking: that each mutation actually changed the predicate, and changed it in the
way its name says.

A mutation that silently returns the input would be reviewed as a correct
predicate, the critic would answer OK, and the probe would score that as a missed
defect. The catch rate would then be measuring the mutation function. That failure
is invisible in the output, because a missed defect and an unplanted defect print
the same row.

So these tests run each mutation over real compiled predicates from the committed
fixture and assert the change is real, is the named one, and is the only one.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from critic_probe import (  # noqa: E402
    FLIP_CMP, MUTATIONS, m_absence, m_boundary, m_direction, m_threshold, m_window)

#: Two committed compiled runs, because one is not enough to exercise five
#: mutations. The gate fixture carries a predicate with no threshold, no window
#: and no open-world query, so four of the five mutations declined on it and the
#: tests skipped. A skip here is indistinguishable from a pass and both leave the
#: mutation unchecked.
FIXTURES = (
    ROOT / "tests" / "fixtures" / "mutation_run" / "compiled" / "criteria_seed7.json",
    ROOT / "tests" / "fixtures" / "gate_run" / "compiled" / "criteria_seed7.json",
)


def predicates() -> list[dict]:
    out = []
    for f in FIXTURES:
        if not f.exists():
            continue
        blob = json.loads(f.read_text(encoding="utf-8"))
        out += [c["expr"] for c in blob["criteria"] if c.get("compilable")]
    return out


@pytest.fixture(scope="module")
def exprs() -> list[dict]:
    p = predicates()
    if not p:
        pytest.skip("the fixture carries no compilable predicate")
    return p


def nodes(e):
    """Every dict in the tree, so a change can be located rather than assumed."""
    if isinstance(e, dict):
        yield e
        for v in e.values():
            yield from nodes(v)
    elif isinstance(e, list):
        for v in e:
            yield from nodes(v)


def test_every_mutation_is_named_and_callable():
    assert [n for n, _ in MUTATIONS] == [
        "boundary", "threshold", "window", "direction", "absence"], (
        "the defect classes are the ones the critic's prompt claims to look for, "
        "in its order. Changing this list changes what the probe measures.")


def test_direction_always_applies(exprs):
    """The one mutation with no precondition. If this can no-op, nothing is safe."""
    for e in exprs:
        out, detail = m_direction(e)
        assert out != e, "negation returned the input"
        assert out["op"] == "not" and out["arg"] == e
        assert detail


@pytest.mark.parametrize("fn,name", [(m_boundary, "boundary"), (m_threshold, "threshold"),
                                     (m_window, "window"), (m_absence, "absence")])
def test_a_conditional_mutation_changes_the_tree_or_declines(fn, name, exprs):
    """Either it applies and the tree differs, or it returns None. Never both."""
    applied = 0
    for e in exprs:
        before = copy.deepcopy(e)
        got = fn(e)
        assert e == before, f"{name} mutated its argument in place"
        if got is None:
            continue
        out, detail = got
        applied += 1
        assert out != e, (
            f"{name} reported a mutation and returned an identical predicate. "
            f"The probe would review an unbroken predicate and score the OK as a "
            f"missed defect.")
        assert detail, f"{name} planted a defect it cannot describe"
    if not applied:
        pytest.skip(f"{name} applies to no predicate in the fixture")


def test_boundary_flips_exactly_one_comparison(exprs):
    for e in exprs:
        got = m_boundary(e)
        if got is None:
            continue
        out, _ = got
        before = [n["cmp"] for n in nodes(e) if n.get("op") == "compare" and "cmp" in n]
        after = [n["cmp"] for n in nodes(out) if n.get("op") == "compare" and "cmp" in n]
        assert len(before) == len(after)
        differ = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        assert len(differ) == 1, f"expected one flipped comparison, got {len(differ)}"
        i = differ[0]
        assert after[i] == FLIP_CMP[before[i]], "flipped to something not in the table"


def test_absence_only_ever_closes_the_world(exprs):
    """unknown becomes false. The reverse would make the predicate safer, not worse."""
    for e in exprs:
        got = m_absence(e)
        if got is None:
            continue
        out, _ = got
        vals = [n["absent_means"] for n in nodes(out) if "absent_means" in n]
        orig = [n["absent_means"] for n in nodes(e) if "absent_means" in n]
        assert vals.count("false") == orig.count("false") + 1
        assert vals.count("unknown") == orig.count("unknown") - 1


def test_threshold_moves_far_enough_to_matter(exprs):
    """Doubling, not nudging. A change inside measurement noise is not a defect."""
    for e in exprs:
        got = m_threshold(e)
        if got is None:
            continue
        out, _ = got
        b = [n["number"] for n in nodes(e) if n.get("val") == "literal" and "number" in n]
        a = [n["number"] for n in nodes(out) if n.get("val") == "literal" and "number" in n]
        differ = [(x, y) for x, y in zip(b, a) if x != y]
        assert len(differ) == 1
        old, new = differ[0]
        assert new == pytest.approx(old * 2.0), "the threshold did not double"


def test_window_widens_rather_than_narrows(exprs):
    """"Within 6 months" becoming 2 years admits people. Narrowing would only refuse."""
    for e in exprs:
        got = m_window(e)
        if got is None:
            continue
        out, _ = got
        b = [n["within_days"] for n in nodes(e) if isinstance(n.get("within_days"), int)]
        a = [n["within_days"] for n in nodes(out) if isinstance(n.get("within_days"), int)]
        differ = [(x, y) for x, y in zip(b, a) if x != y]
        assert len(differ) == 1
        old, new = differ[0]
        assert new == old * 4 and new > old
