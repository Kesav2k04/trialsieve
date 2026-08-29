"""The fast paired bootstrap must return the slow one's numbers, exactly.

The inner loop was rewritten to count the resample instead of materialising it,
which took the report from about twenty minutes to seconds. An optimisation to
the code that produces a published confidence interval is the last place to take
"it looks about right" as evidence, so the two implementations are run against
each other on the same seed and required to agree to the last digit.

They can agree exactly, and that is the point of how the rewrite was done: the
random draws are the same calls in the same order on the same seeded generator.
Only the arithmetic over each draw changed. An optimisation that also changed the
draw order would have to be argued statistically, and would be a worse trade.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation"))

from score import Cell, paired_bootstrap  # noqa: E402


def _panel(n_crit: int, n_pat: int, seed: int, err_a: float, err_b: float):
    """A crossed, complete design, which is what the fast path assumes."""
    rng = random.Random(seed)
    a, b = [], []
    for ci in range(n_crit):
        ch = f"hash{ci:03d}"
        for pi in range(n_pat):
            pid = f"p{pi:03d}"
            cid = f"NCT00000000-INC-{ci:02d}"
            gold = rng.choice(["MEETS", "FAILS", "INDETERMINATE"])
            sa = gold if rng.random() > err_a else "MEETS" if gold != "MEETS" else "FAILS"
            sb = gold if rng.random() > err_b else "MEETS" if gold != "MEETS" else "FAILS"
            a.append(Cell(pid, cid, ch, gold, sa))
            b.append(Cell(pid, cid, ch, gold, sb))
    return a, b


def _slow(cells_a, cells_b, metric, b, seed):
    """The implementation the fast path replaced, kept here as the oracle."""
    idx_a = {(c.patient_id, c.criterion_id): c for c in cells_a}
    idx_b = {(c.patient_id, c.criterion_id): c for c in cells_b}
    shared = sorted(set(idx_a) & set(idx_b))
    crits = sorted({idx_a[k].criterion_hash for k in shared})
    pats = sorted({k[0] for k in shared})
    by_ch = {(idx_a[k].criterion_hash, k[0]): (idx_a[k], idx_b[k]) for k in shared}

    def flag(cell):
        return {"ser": cell.silent_error, "coverage": cell.committed,
                "false_fails": cell.false_fails}[metric]

    def stat(pairs):
        if not pairs:
            return 0.0
        va = sum(1 for p in pairs if flag(p[0])) / len(pairs)
        vb = sum(1 for p in pairs if flag(p[1])) / len(pairs)
        return va - vb

    rng = random.Random(seed)
    draws = []
    for _ in range(b):
        cs = [crits[rng.randrange(len(crits))] for _ in range(len(crits))]
        ps = [pats[rng.randrange(len(pats))] for _ in range(len(pats))]
        draws.append(stat([by_ch[(c, p)] for c in cs for p in ps if (c, p) in by_ch]))
    draws.sort()
    alpha = 0.05
    return {"ci_low": round(draws[int(alpha / 2 * b)], 5),
            "ci_high": round(draws[min(b - 1, int((1 - alpha / 2) * b))], 5)}


@pytest.mark.parametrize("metric", ["ser", "coverage", "false_fails"])
def test_fast_bootstrap_matches_the_slow_one(metric):
    a, b = _panel(n_crit=8, n_pat=25, seed=3, err_a=0.05, err_b=0.30)
    fast = paired_bootstrap(a, b, metric=metric, b=300, seed=11)
    slow = _slow(a, b, metric, b=300, seed=11)
    assert fast["ci_low"] == slow["ci_low"]
    assert fast["ci_high"] == slow["ci_high"]


def test_an_arm_against_itself_is_exactly_zero():
    """A plumbing check, not a control. The same cells on both sides can only
    give zero, so this proves the pairing lines up and nothing else. It was
    written as the A/A control, where it could not have failed: the arms were
    the same list, so no amount of resampling noise could have moved it."""
    a, _ = _panel(n_crit=8, n_pat=25, seed=5, err_a=0.2, err_b=0.2)
    r = paired_bootstrap(a, list(a), metric="ser", b=400, seed=11)
    assert r["observed_difference"] == 0
    assert r["crosses_zero"], r


def test_two_arms_of_equal_quality_cross_zero():
    """The real A/A control: two arms drawn independently at the same error
    rate, which differ only by noise. If these intervals excluded zero the
    method would be manufacturing differences out of resampling noise.

    The bar is a rate over ten panels rather than a single one, because a 95
    percent interval is supposed to miss about one time in twenty and a
    single-panel assertion would just be a seed that happened to pass."""
    crossed = 0
    for seed in range(20, 30):
        a, b = _panel(n_crit=8, n_pat=25, seed=seed, err_a=0.2, err_b=0.2)
        r = paired_bootstrap(a, b, metric="ser", b=400, seed=11)
        crossed += bool(r["crosses_zero"])
    assert crossed >= 8, f"only {crossed} of 10 equal-quality panels crossed zero"


def test_an_incomplete_design_still_works():
    """The fast path assumes every criterion meets every patient. When that is not
    true it must fall back rather than count cells that do not exist."""
    a, b = _panel(n_crit=5, n_pat=12, seed=7, err_a=0.05, err_b=0.4)
    drop = {(a[3].patient_id, a[3].criterion_id)}
    a2 = [c for c in a if (c.patient_id, c.criterion_id) not in drop]
    b2 = [c for c in b if (c.patient_id, c.criterion_id) not in drop]
    r = paired_bootstrap(a2, b2, metric="ser", b=200, seed=11)
    assert r["n_shared_cells"] == len(a) - 1
    assert r["ci_low"] <= r["observed_difference"] <= r["ci_high"]


def test_a_real_difference_is_detected():
    a, b = _panel(n_crit=10, n_pat=30, seed=9, err_a=0.02, err_b=0.45)
    r = paired_bootstrap(a, b, metric="ser", b=400, seed=11)
    assert r["observed_difference"] < 0
    assert not r["crosses_zero"], r
