"""Properties the scoring must have, or the headline numbers mean nothing."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))

from score import (  # noqa: E402
    Cell, agreement, decide_screen, operating_curve, paired_bootstrap, score_arm,
    score_panel, seed_spread,
)


def cell(p, c, gold, sysv, h=None):
    return Cell(p, c, h or c, gold, sysv)


def test_abstaining_everywhere_gives_zero_ser_and_zero_coverage():
    """The reason SER is never reported without coverage beside it."""
    cells = [cell(f"p{i}", "NCT1-INC-01", "FAILS", "INDETERMINATE") for i in range(20)]
    s = score_arm("abstainer", cells, n_screens=20)
    assert s.ser == 0.0 and s.coverage == 0.0
    assert s.resolved_correct_per_screen == 0.0


def test_committing_where_gold_is_indeterminate_counts_as_a_silent_error():
    cells = [cell("p1", "NCT1-INC-01", "INDETERMINATE", "MEETS")]
    s = score_arm("overcommitter", cells, n_screens=1)
    assert s.n_silent == 1 and s.ser == 1.0


def test_false_fails_and_false_meets_partition_the_silent_errors():
    cells = [cell("p1", "c1", "MEETS", "FAILS"),
             cell("p2", "c2", "FAILS", "MEETS"),
             cell("p3", "c3", "INDETERMINATE", "FAILS"),
             cell("p4", "c4", "MEETS", "MEETS")]
    s = score_arm("mixed", cells, n_screens=4)
    assert s.n_silent == 3
    assert s.n_false_fails + s.n_false_meets == s.n_silent


def test_error_is_not_folded_into_abstention():
    """A broken arm must not inherit the abstaining arm's clean rate."""
    cells = [cell("p1", "c1", "MEETS", "ERROR")]
    s = score_arm("broken", cells, n_screens=1)
    assert s.n_error == 1 and s.n_committed == 0


def test_unmeasurable_cells_leave_the_denominator():
    cells = [cell("p1", "c1", "UNMEASURABLE", "MEETS"),
             cell("p2", "c2", "MEETS", "MEETS")]
    s = score_arm("a", cells, n_screens=2)
    assert s.n_scoreable == 1


def test_one_definite_failure_decides_a_screen():
    assert decide_screen(["MEETS", "INDETERMINATE", "FAILS"]) == "INELIGIBLE"
    assert decide_screen(["MEETS", "INDETERMINATE"]) == "NEEDS_REVIEW"
    assert decide_screen(["MEETS", "MEETS"]) == "ELIGIBLE"


def test_panel_reduction_counts_only_correct_exclusions_as_free():
    cells = [cell("p1", "NCT1-INC-01", "FAILS", "FAILS"),
             cell("p2", "NCT1-INC-01", "MEETS", "FAILS")]   # wrongly ruled out
    ps = score_panel("a", cells)
    assert ps.n_ineligible == 2 and ps.false_exclusions == 1
    assert ps.rule_of_three_upper is None, "no rule of three when the count is not zero"


def test_rule_of_three_replaces_a_bootstrapped_zero():
    cells = [cell(f"p{i}", f"NCT1-INC-{j:02d}", "FAILS", "FAILS")
             for i in range(50) for j in range(4)]
    ps = score_panel("a", cells)
    assert ps.false_exclusions == 0
    assert ps.n_eff_excluding_criteria == 4, "effective N is criteria, not the 200 cells"
    assert abs(ps.rule_of_three_upper - 0.75) < 1e-9


def test_operating_curve_trades_reduction_against_false_exclusions():
    safe = [cell(f"p{i}", "NCT1-INC-01", "FAILS", "FAILS") for i in range(30)]
    risky = [cell(f"p{i}", "NCT1-INC-02", "MEETS", "FAILS") for i in range(30, 33)]
    curve = operating_curve(safe + risky, budgets=(0, 5))
    at0 = [r for r in curve if r["false_exclusion_budget"] == 0][0]
    at5 = [r for r in curve if r["false_exclusion_budget"] == 5][0]
    assert at0["false_exclusions"] == 0
    assert at5["reduction"] >= at0["reduction"]


def test_bootstrap_resamples_criteria_not_cells():
    """Effective N must reflect unique criteria, not the cell count."""
    a = [cell(f"p{i}", "NCT1-INC-01", "MEETS", "FAILS") for i in range(100)]
    b = [cell(f"p{i}", "NCT1-INC-01", "MEETS", "MEETS") for i in range(100)]
    r = paired_bootstrap(a, b, metric="ser", b=200, seed=1)
    assert r["n_unique_criteria"] == 1
    assert r["n_shared_cells"] == 100


def test_bootstrap_on_one_criterion_cannot_be_confident():
    """A single predicate repeated over many patients is one observation."""
    a = [cell(f"p{i}", "NCT1-INC-01", "MEETS", "FAILS") for i in range(200)]
    b = [cell(f"p{i}", "NCT1-INC-01", "MEETS", "MEETS") for i in range(200)]
    r = paired_bootstrap(a, b, metric="ser", b=400, seed=2)
    assert r["ci_low"] <= 0 <= r["ci_high"] or r["ci_low"] == r["ci_high"]


def test_seed_spread_is_the_noise_floor():
    s = seed_spread([0.10, 0.12, 0.11])
    assert s["n_seeds"] == 3 and abs(s["range"] - 0.02) < 1e-9


def test_kappa_collapses_under_a_dominant_category_but_ac1_does_not():
    """Why both are reported: 98 of 100 cells agree, on one category."""
    a = ["INDETERMINATE"] * 98 + ["MEETS", "FAILS"]
    b = ["INDETERMINATE"] * 98 + ["FAILS", "MEETS"]
    r = agreement(a, b)
    assert r["percent_agreement"] == 0.98
    assert r["cohen_kappa"] < r["gwet_ac1"]


# ---------------------------------------------------------------------------
# Positive control for the cross-fitted operating curve.
#
# On the scored panel the in-sample and cross-fitted curves agree on every row,
# and two identical tables are exactly what a cross-fit that silently reused the
# in-sample selection would also print. This builds a panel where the two must
# disagree, so the agreement on real data is a measurement rather than a no-op.
# ---------------------------------------------------------------------------

def _panel_with_one_lucky_criterion(n_patients=100, unlucky="p_bad"):
    """One criterion that excludes everybody and is wrong about exactly one.

    In sample it has a false exclusion and is dropped at budget 0. Cross-fitted,
    the fold holding the one patient it is wrong about trains on a set where it
    looks perfect, keeps it, and then excludes that patient. The optimism the
    in-sample curve hides is worth exactly that one patient.
    """
    cells = []
    ids = [f"p{i}" for i in range(n_patients - 1)] + [unlucky]
    for pid in ids:
        gold = "MEETS" if pid == unlucky else "FAILS"
        cells.append(Cell(pid, "T-C1", "sweeper", gold, "FAILS"))
    return cells


def test_crossfit_curve_reveals_selection_optimism():
    from score import operating_curve_cv
    cells = _panel_with_one_lucky_criterion()
    ins = {r["false_exclusion_budget"]: r for r in operating_curve(cells, budgets=(0,))}
    cv = {r["false_exclusion_budget"]: r for r in
          operating_curve_cv(cells, budgets=(0,), folds=5, seed=13)}
    assert ins[0]["false_exclusions"] == 0, "in-sample drops the criterion at budget 0"
    assert ins[0]["criteria_used"] == 0
    assert cv[0]["false_exclusions"] == 1, (
        "cross-fitting must surface the false exclusion the in-sample selection "
        "avoided by looking at the patient it was scored on")
    assert cv[0]["n_ineligible"] > ins[0]["n_ineligible"]


def test_crossfit_curve_agrees_when_criteria_are_cleanly_separated():
    """The other half of the control: no optimism to find, and none reported."""
    from score import operating_curve_cv
    cells = []
    for i in range(100):
        pid = f"p{i}"
        cells.append(Cell(pid, "T-C1", "clean", "FAILS" if i % 2 else "MEETS",
                          "FAILS" if i % 2 else "INDETERMINATE"))
        cells.append(Cell(pid, "T-C2", "filthy", "MEETS", "FAILS"))
    ins = operating_curve(cells, budgets=(0,))[0]
    cv = operating_curve_cv(cells, budgets=(0,), folds=5, seed=13)[0]
    assert ins["false_exclusions"] == cv["false_exclusions"] == 0
    assert ins["n_ineligible"] == cv["n_ineligible"]
    assert ins["criteria_used"] == cv["criteria_used"] == 1


def test_crossfit_folds_partition_every_patient_exactly_once():
    """A fold assignment that dropped patients would shrink the denominator and
    make both curves look better, which is the failure this guards."""
    from score import _fold_of
    ids = [f"p{i}" for i in range(97)]
    assign = _fold_of(ids * 3, folds=5, seed=13)
    assert set(assign) == set(ids)
    sizes = sorted(Counter(assign.values()).values())
    assert sizes[-1] - sizes[0] <= 1
