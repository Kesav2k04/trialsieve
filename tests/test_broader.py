"""A code that contains the concept is not the concept.

This corpus records every diabetes diagnosis as SNOMED 44054006, displayed as
"Diabetes", and has no code for type 2 specifically. A trial that asks for type 2
diabetes therefore gets two different answers from the same vocabulary depending
on which way the record points, and both of them are correct:

  present : undetermined. The patient has diabetes of an unstated type.
  absent  : the criterion fails. A patient with no diabetes code has no type 2
            diabetes either, so absence carries all the way down.

Collapsing that into one answer is wrong in both directions. Treating the broader
code as a match invents MEETS verdicts the record cannot support. Refusing the
concept entirely throws away the half of the information that is real, and it is
the half that removes people from the worklist.
"""
from __future__ import annotations

import pytest

from conftest import chart, cond, med  # noqa: F401
from trialsieve.evaluator import Evaluator
from trialsieve.ir import IRError, validate_query
from trialsieve.logic import F, T, U

T2DM_BROAD = "44054006"
T2DM_EXACT = "1481000119100"          # not present in this vocabulary
NEUROPATHY_T2 = "368581000119106"


def q(**kw):
    base = {"domain": "condition", "codes": [T2DM_EXACT],
            "broader_codes": [T2DM_BROAD], "absent_means": "unknown"}
    base.update(kw)
    return {"op": "exists", "query": base}


def test_an_exact_match_still_wins():
    c = chart(conditions=[cond(T2DM_EXACT)])
    r = Evaluator(c).eval_expr(q())
    assert r.value is T


def test_a_broader_code_alone_is_undetermined():
    c = chart(conditions=[cond(T2DM_BROAD)])
    r = Evaluator(c).eval_expr(q())
    assert r.value is U
    assert "do not establish it" in r.reason
    assert r.evidence and r.evidence[0].code == T2DM_BROAD


def test_absence_of_the_broader_code_still_means_what_absence_meant():
    """The asymmetry. Present is undetermined; absent is unchanged."""
    empty = chart()
    assert Evaluator(empty).eval_expr(q(absent_means="unknown")).value is U
    assert Evaluator(empty).eval_expr(q(absent_means="false")).value is F


def test_a_broader_code_does_not_override_a_closed_world_false_when_it_is_there():
    """Present beats absent. A closed-world query still cannot say false here."""
    c = chart(conditions=[cond(T2DM_BROAD)])
    assert Evaluator(c).eval_expr(q(absent_means="false")).value is U


def test_a_different_condition_does_not_count_as_broader():
    c = chart(conditions=[cond(NEUROPATHY_T2)])
    assert Evaluator(c).eval_expr(q()).value is U       # absent, open world
    assert Evaluator(c).eval_expr(q(absent_means="false")).value is F


def test_the_window_applies_to_the_broader_code_too():
    c = chart(conditions=[cond(T2DM_BROAD, days_ago=900)])
    assert Evaluator(c).eval_expr(q(within_days=365)).value is U
    inside = chart(conditions=[cond(T2DM_BROAD, days_ago=100)])
    r = Evaluator(inside).eval_expr(q(within_days=365))
    assert r.value is U and "include this concept" in r.reason


def test_a_code_cannot_be_both_exact_and_broader():
    with pytest.raises(IRError, match="both exact and broader"):
        validate_query({"domain": "condition", "codes": ["x"], "broader_codes": ["x"],
                        "absent_means": "unknown"})


def test_broader_codes_must_be_strings():
    with pytest.raises(IRError, match="list of string codes"):
        validate_query({"domain": "condition", "codes": ["x"], "broader_codes": [7],
                        "absent_means": "unknown"})


def test_a_query_without_broader_codes_behaves_exactly_as_before():
    c = chart(conditions=[cond(T2DM_BROAD)])
    plain = {"op": "exists", "query": {"domain": "condition", "codes": [T2DM_EXACT],
                                       "absent_means": "false"}}
    assert Evaluator(c).eval_expr(plain).value is F
