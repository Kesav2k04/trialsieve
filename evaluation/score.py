"""Scoring, intervals, and the operating curve.

Three decisions here are not conventional and each has a reason.

**SER never travels alone.** The unit of result is the ordered pair
(coverage, SER). A system that abstains on every cell has a silent error rate of
exactly zero and is worthless, so a rate reported without the coverage it was
achieved at is not interpretable, and a comparison against an arm at higher
coverage is not admissible.

**The bootstrap resamples criteria, not cells.** One compiled predicate serves
every patient in the panel, so its errors repeat across hundreds of cells that
are nowhere near independent. Resampling cells would publish an interval several
times too narrow. Effective N is the number of unique criteria.

**The zero is not bootstrapped.** The primary outcome is conditioned on making no
false exclusion, and resampling a set of zeros returns an interval of exactly
[0, 0], which asserts certainty that was never measured. A zero numerator gets
the rule of three instead, over the number of unique criteria that ever produced
a definite exclusion.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

DEFINITE = ("MEETS", "FAILS")
VERDICTS = ("MEETS", "FAILS", "INDETERMINATE", "ERROR", "UNMEASURABLE")


@dataclass
class Cell:
    patient_id: str
    criterion_id: str
    criterion_hash: str
    gold: str
    system: str
    stratum: str = "synthea"

    @property
    def scoreable(self) -> bool:
        return self.gold != "UNMEASURABLE"

    @property
    def committed(self) -> bool:
        return self.system in DEFINITE

    @property
    def silent_error(self) -> bool:
        """A confident verdict that contradicts gold, including confidence the
        record could not support."""
        if not self.committed:
            return False
        if self.gold in DEFINITE:
            return self.system != self.gold
        return self.gold == "INDETERMINATE"

    @property
    def false_fails(self) -> bool:
        """Ruled a patient out when gold does not. The harm nobody audits."""
        return self.system == "FAILS" and self.gold != "FAILS"

    @property
    def false_meets(self) -> bool:
        return self.system == "MEETS" and self.gold != "MEETS"


@dataclass
class ArmScore:
    arm: str
    n_cells: int
    n_scoreable: int
    n_committed: int
    coverage: float
    ser: float
    n_silent: int
    n_false_fails: int
    n_false_meets: int
    n_error: int
    unnecessary_abstention: int
    resolved_correct_per_screen: float
    n_unique_criteria: int
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = dict(vars(self))
        for k in ("coverage", "ser", "resolved_correct_per_screen"):
            d[k] = round(d[k], 4)
        return d

    def headline(self) -> str:
        return (f"{self.arm}: coverage {self.coverage:.1%}, SER {self.ser:.1%} "
                f"({self.n_silent} silent, {self.n_false_fails} false-FAILS)")


def score_arm(arm: str, cells: Iterable[Cell], n_screens: int) -> ArmScore:
    cells = [c for c in cells if c.scoreable]
    n = len(cells)
    committed = [c for c in cells if c.committed]
    silent = [c for c in cells if c.silent_error]
    conf: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in cells:
        conf[c.gold][c.system] += 1
    unnecessary = sum(1 for c in cells
                      if c.system == "INDETERMINATE" and c.gold in DEFINITE)
    resolved_correct = sum(1 for c in committed if c.system == c.gold and c.gold in DEFINITE)
    return ArmScore(
        arm=arm, n_cells=n, n_scoreable=n, n_committed=len(committed),
        coverage=(len(committed) / n) if n else 0.0,
        ser=(len(silent) / n) if n else 0.0,
        n_silent=len(silent),
        n_false_fails=sum(1 for c in silent if c.false_fails),
        n_false_meets=sum(1 for c in silent if c.false_meets),
        n_error=sum(1 for c in cells if c.system == "ERROR"),
        unnecessary_abstention=unnecessary,
        resolved_correct_per_screen=(resolved_correct / n_screens) if n_screens else 0.0,
        n_unique_criteria=len({c.criterion_hash for c in cells}),
        confusion={g: dict(v) for g, v in sorted(conf.items())},
    )


# ---------------------------------------------------------------------------
# Screen level
# ---------------------------------------------------------------------------

def decide_screen(verdicts: Iterable[str]) -> str:
    vs = list(verdicts)
    if any(v == "FAILS" for v in vs):
        return "INELIGIBLE"
    if any(v in ("INDETERMINATE", "ERROR") for v in vs):
        return "NEEDS_REVIEW"
    return "ELIGIBLE"


@dataclass
class PanelScore:
    arm: str
    n_screens: int
    n_ineligible: int
    reduction: float
    false_exclusions: int
    false_exclusion_examples: list[dict]
    n_eff_excluding_criteria: int
    rule_of_three_upper: float | None

    def as_dict(self) -> dict[str, Any]:
        d = dict(vars(self))
        d["reduction"] = round(d["reduction"], 4)
        if d["rule_of_three_upper"] is not None:
            d["rule_of_three_upper"] = round(d["rule_of_three_upper"], 5)
        return d


def score_panel(arm: str, cells: Iterable[Cell]) -> PanelScore:
    """Panel reduction, and the false exclusions that qualify it."""
    by_screen: dict[tuple[str, str], list[Cell]] = defaultdict(list)
    for c in cells:
        trial = c.criterion_id.split("-")[0]
        by_screen[(c.patient_id, trial)].append(list_cell(c))
    sysd, goldd = {}, {}
    for key, rows in by_screen.items():
        sysd[key] = decide_screen(r.system for r in rows)
        goldd[key] = decide_screen(r.gold for r in rows)

    ineligible = [k for k, v in sysd.items() if v == "INELIGIBLE"]
    false_ex = [k for k in ineligible if goldd[k] != "INELIGIBLE"]

    # Effective N for the rule of three: the number of distinct criteria that
    # ever produced a definite exclusion. Using the screen count would treat
    # hundreds of patients sharing one predicate as independent evidence.
    excl_criteria = {c.criterion_hash for c in cells if c.system == "FAILS"}
    n_eff = len(excl_criteria)
    upper = (3.0 / n_eff) if (not false_ex and n_eff) else None

    examples = []
    for k in false_ex[:8]:
        rows = by_screen[k]
        bad = [r for r in rows if r.system == "FAILS" and r.gold != "FAILS"]
        examples.append({"patient_id": k[0], "trial": k[1],
                         "gold_decision": goldd[k],
                         "criteria": [{"criterion_id": r.criterion_id, "gold": r.gold}
                                      for r in bad]})
    return PanelScore(arm=arm, n_screens=len(by_screen), n_ineligible=len(ineligible),
                      reduction=len(ineligible) / len(by_screen) if by_screen else 0.0,
                      false_exclusions=len(false_ex), false_exclusion_examples=examples,
                      n_eff_excluding_criteria=n_eff, rule_of_three_upper=upper)


def list_cell(c: Cell) -> Cell:
    return c


def operating_curve(cells: Iterable[Cell], budgets=(0, 1, 2, 5, 10)) -> list[dict]:
    """Reduction achievable at each tolerated number of false exclusions.

    A single all-or-nothing gate at zero rewards compiling fewer criteria: one bad
    cell in a hundred thousand would void the headline. The curve shows the whole
    trade instead, with zero highlighted rather than mandatory.

    **This is an in-sample curve and the protocol treats it as an upper bound.**
    The subset is chosen by counting each criterion's false exclusions on the same
    patients the row then scores, so the zero row reports that a clean subset
    existed, not that it could have been picked in advance. `operating_curve_cv`
    is the cross-fitted answer to the second question, and both are printed.
    """
    cells = list(cells)
    out = []
    for b in budgets:
        keep = _select_criteria(cells, b)
        ps = score_panel(f"budget<={b}", _muted(cells, keep))
        out.append({"false_exclusion_budget": b, "reduction": round(ps.reduction, 4),
                    "n_ineligible": ps.n_ineligible, "false_exclusions": ps.false_exclusions,
                    "criteria_used": len(keep), "in_sample": True})
    return out


# ---------------------------------------------------------------------------
# Two-way paired bootstrap
# ---------------------------------------------------------------------------

def paired_bootstrap(cells_a: list[Cell], cells_b: list[Cell], metric: str = "ser",
                     b: int = 10000, seed: int = 11,
                     alpha: float = 0.05) -> dict[str, Any]:
    """Confidence interval on the PAIRED difference between two arms.

    Criteria and patients are both resampled with replacement and the induced
    cells are taken, because the design is crossed: the same predicate meets every
    patient and the same patient meets every predicate. Two separate intervals
    compared by whether they overlap would be a different and weaker test, so the
    difference is bootstrapped directly on cells the two arms share.
    """
    idx_a = {(c.patient_id, c.criterion_id): c for c in cells_a}
    idx_b = {(c.patient_id, c.criterion_id): c for c in cells_b}
    shared = sorted(set(idx_a) & set(idx_b))
    if not shared:
        return {"error": "no shared cells between arms"}

    crits = sorted({idx_a[k].criterion_hash for k in shared})
    pats = sorted({k[0] for k in shared})
    by_ch: dict[tuple[str, str], tuple[Cell, Cell]] = {}
    for k in shared:
        by_ch[(idx_a[k].criterion_hash, k[0])] = (idx_a[k], idx_b[k])

    def stat(pairs: list[tuple[Cell, Cell]]) -> float:
        if not pairs:
            return 0.0
        aa = [p[0] for p in pairs]
        bb = [p[1] for p in pairs]
        if metric == "ser":
            va = sum(1 for c in aa if c.silent_error) / len(aa)
            vb = sum(1 for c in bb if c.silent_error) / len(bb)
        elif metric == "coverage":
            va = sum(1 for c in aa if c.committed) / len(aa)
            vb = sum(1 for c in bb if c.committed) / len(bb)
        elif metric == "false_fails":
            va = sum(1 for c in aa if c.false_fails) / len(aa)
            vb = sum(1 for c in bb if c.false_fails) / len(bb)
        else:
            raise ValueError(metric)
        return va - vb

    base_pairs = list(by_ch.values())
    observed = stat(base_pairs)

    # -- the same resample, counted instead of materialised --------------------
    #
    # The obvious loop builds the resampled cell list and walks it: for forty
    # criteria and three hundred and eighty-five patients that is fifteen
    # thousand tuples per draw, and ten thousand draws of it takes about twenty
    # minutes. A reproduction step that appears to hang for twenty minutes is one
    # a reader kills, so the numbers stop being checkable for a reason that has
    # nothing to do with the numbers.
    #
    # The design is crossed and complete: every criterion meets every patient. So
    # the count of a 0/1 indicator over the resample is
    #
    #     sum over criteria c of  (times c was drawn) * sum over patients p of
    #                             (times p was drawn) * indicator(c, p)
    #
    # and the indicator is sparse for the metrics that matter. A silent error is
    # rare, so the list of patients where it fires is short, and the inner sum
    # runs over that list rather than over the panel. Coverage is dense, so it is
    # counted through its complement.
    #
    # The random draws are byte-for-byte the ones the slow loop made: the same
    # calls in the same order on the same seeded generator. Only the arithmetic
    # changed. `tests/test_bootstrap.py` asserts the two agree.
    p_index = {p: i for i, p in enumerate(pats)}
    c_index = {c: i for i, c in enumerate(crits)}
    complete = len(by_ch) == len(crits) * len(pats)

    def _flag(cell) -> bool:
        if metric == "ser":
            return cell.silent_error
        if metric == "coverage":
            return cell.committed
        if metric == "false_fails":
            return cell.false_fails
        raise ValueError(metric)

    #: For each arm and criterion, the patient indices where the indicator is 1,
    #: unless that is the majority, in which case the zeros are stored instead and
    #: the count is taken from the complement.
    def _sparse(which: int):
        rows, inverted = [], []
        for c in crits:
            hits = [p_index[p] for p in pats
                    if (c, p) in by_ch and _flag(by_ch[(c, p)][which])]
            if len(hits) * 2 > len(pats):
                rows.append([p_index[p] for p in pats
                             if (c, p) in by_ch and not _flag(by_ch[(c, p)][which])])
                inverted.append(True)
            else:
                rows.append(hits)
                inverted.append(False)
        return rows, inverted

    rng = random.Random(seed)
    draws = []
    if complete:
        rows_a, inv_a = _sparse(0)
        rows_b, inv_b = _sparse(1)
        n_c, n_p = len(crits), len(pats)
        for _ in range(b):
            cs = [crits[rng.randrange(len(crits))] for _ in range(len(crits))]
            ps = [pats[rng.randrange(len(pats))] for _ in range(len(pats))]
            pmult = [0] * n_p
            for p in ps:
                pmult[p_index[p]] += 1
            cmult = [0] * n_c
            for c in cs:
                cmult[c_index[c]] += 1
            total = n_c * n_p
            na = nb = 0
            for i in range(n_c):
                m = cmult[i]
                if not m:
                    continue
                ra = sum(pmult[j] for j in rows_a[i])
                rb = sum(pmult[j] for j in rows_b[i])
                na += m * ((n_p - ra) if inv_a[i] else ra)
                nb += m * ((n_p - rb) if inv_b[i] else rb)
            draws.append(na / total - nb / total)
    else:
        for _ in range(b):
            cs = [crits[rng.randrange(len(crits))] for _ in range(len(crits))]
            ps = [pats[rng.randrange(len(pats))] for _ in range(len(pats))]
            pairs = [by_ch[(c, p)] for c in cs for p in ps if (c, p) in by_ch]
            draws.append(stat(pairs))
    draws.sort()
    lo = draws[int(alpha / 2 * b)]
    hi = draws[min(b - 1, int((1 - alpha / 2) * b))]
    return {"metric": metric, "observed_difference": round(observed, 5),
            "ci_low": round(lo, 5), "ci_high": round(hi, 5),
            "b": b, "n_unique_criteria": len(crits), "n_patients": len(pats),
            "n_shared_cells": len(shared),
            "crosses_zero": bool(lo <= 0 <= hi)}


def seed_spread(values: list[float]) -> dict[str, float]:
    """The noise floor: spread of a metric across recompilation seeds."""
    if not values:
        return {}
    m = sum(values) / len(values)
    var = sum((v - m) ** 2 for v in values) / max(1, len(values) - 1)
    return {"mean": round(m, 5), "sd": round(math.sqrt(var), 5),
            "min": round(min(values), 5), "max": round(max(values), 5),
            "range": round(max(values) - min(values), 5), "n_seeds": len(values)}


def agreement(a: list[str], b: list[str]) -> dict[str, float]:
    """Percent agreement, Cohen's kappa and Gwet's AC1.

    Kappa alone is misleading when one category dominates, which it does here:
    most cells are INDETERMINATE, so chance agreement is high and kappa collapses
    even when the raters agree almost everywhere. AC1 is reported beside it.
    """
    assert len(a) == len(b) and a
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = sorted(set(a) | set(b))
    pa = {c: a.count(c) / n for c in cats}
    pb = {c: b.count(c) / n for c in cats}
    pe_k = sum(pa[c] * pb[c] for c in cats)
    kappa = (po - pe_k) / (1 - pe_k) if pe_k < 1 else 1.0
    q = len(cats)
    pi = {c: (pa[c] + pb[c]) / 2 for c in cats}
    pe_g = sum(pi[c] * (1 - pi[c]) for c in cats) / (q - 1) if q > 1 else 0.0
    ac1 = (po - pe_g) / (1 - pe_g) if pe_g < 1 else 1.0
    return {"percent_agreement": round(po, 4), "cohen_kappa": round(kappa, 4),
            "gwet_ac1": round(ac1, 4), "n": n,
            "marginals_a": {c: round(pa[c], 4) for c in cats},
            "marginals_b": {c: round(pb[c], 4) for c in cats}}


def _fold_of(patients: list[str], folds: int, seed: int) -> dict[str, int]:
    """Deterministic patient-to-fold assignment, stable across runs and platforms."""
    order = sorted(set(patients))
    random.Random(seed).shuffle(order)
    return {p: i % folds for i, p in enumerate(order)}


def _select_criteria(cells: Iterable[Cell], budget: float) -> set[str]:
    """The greedy subset `operating_curve` uses, factored out so the cross-fitted
    version can run exactly the same selection rule on a different set of cells."""
    by_crit: dict[str, list[Cell]] = defaultdict(list)
    for c in cells:
        by_crit[c.criterion_hash].append(c)
    stats = []
    for h, rows in by_crit.items():
        fails = [r for r in rows if r.system == "FAILS"]
        if not fails:
            continue
        bad = sum(1 for r in fails if r.gold != "FAILS")
        stats.append((h, len(fails), bad))
    stats.sort(key=lambda x: (x[2], -x[1]))          # safest first, then most useful
    keep, spent = set(), 0
    for h, _, bad in stats:
        if spent + bad <= budget:
            keep.add(h)
            spent += bad
    return keep


def _muted(cells: Iterable[Cell], keep: set[str]) -> list[Cell]:
    """Every FAILS from a criterion outside `keep` becomes an abstention."""
    return [c if c.criterion_hash in keep else
            Cell(c.patient_id, c.criterion_id, c.criterion_hash, c.gold,
                 "INDETERMINATE" if c.system == "FAILS" else c.system, c.stratum)
            for c in cells]


def operating_curve_cv(cells: Iterable[Cell], budgets=(0, 1, 2, 5, 10),
                       folds: int = 5, seed: int = 13) -> list[dict]:
    """The operating curve, cross-fitted over patients.

    `operating_curve` picks which criteria to trust by counting how often each one
    excludes a patient it should not have, using the gold labels of the same cells
    it then scores. The zero in its first row is therefore a hindsight optimum: it
    says a subset with no false exclusions existed, not that a coordinator could
    have found it. Reported without that qualification it is a selection made on
    the evaluation set and read back as a result.

    This runs the identical greedy rule, but the subset for each patient is chosen
    from the other folds only, so no patient contributes to the decision that
    scores them. Reduction and false exclusions are then pooled over all patients,
    giving a pair directly comparable to the in-sample row above it. The gap
    between the two curves is the selection's optimism, and it is worth printing.

    The training budget is scaled by the training fraction so the tolerated rate
    per patient is the same in both curves rather than (folds-1)/folds looser.
    """
    cells = list(cells)
    assign = _fold_of([c.patient_id for c in cells], folds, seed)
    n_pat = len(assign)
    out = []
    for b in budgets:
        train_budget = b * (folds - 1) / folds
        scored: list[Cell] = []
        kept_any: set[str] = set()
        for f in range(folds):
            train = [c for c in cells if assign[c.patient_id] != f]
            test = [c for c in cells if assign[c.patient_id] == f]
            if not test:
                continue
            keep = _select_criteria(train, train_budget)
            kept_any |= keep
            scored.extend(_muted(test, keep))
        ps = score_panel(f"cv-budget<={b}", scored)
        out.append({"false_exclusion_budget": b, "reduction": round(ps.reduction, 4),
                    "n_ineligible": ps.n_ineligible, "false_exclusions": ps.false_exclusions,
                    "criteria_used": len(kept_any), "folds": folds, "n_patients": n_pat})
    return out
