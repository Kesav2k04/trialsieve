"""The probe scorer, pinned by the cases that would otherwise flatter it.

A scoring rule is the one part of an evaluation nobody re-derives when reading
the result, so it is the easiest place to hide a number that only looks good. The
cases here are the ones where a lenient rule and a strict rule disagree.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation"))

from vocab_probe import PROBES, judge, score  # noqa: E402

BY_NAME = {p["concept"]: p for p in PROBES}


def j(concept, codes, broader=()):
    return judge(BY_NAME[concept], list(codes), list(broader))


def test_the_probe_set_covers_all_four_classes():
    classes = {p["class"] for p in PROBES}
    assert classes == {"gap", "control", "broader", "absent"}


def test_every_probe_declares_what_it_expects():
    for p in PROBES:
        if p["class"] in ("gap", "control"):
            assert p["codes"] and not p["broader"], p["concept"]
        elif p["class"] == "broader":
            assert p["broader"] and not p["codes"], p["concept"]
        else:
            assert not p["codes"] and not p["broader"], p["concept"]
        assert p["why"].strip(), f"{p['concept']} has no stated reason"


def test_a_coarse_code_returned_as_exact_is_the_dangerous_failure():
    """Presence of a broader code cannot settle the criterion, so calling it
    exact manufactures MEETS verdicts the record does not support."""
    v = j("Iron deficiency anaemia", ["271737000"])
    assert not v["correct"]
    assert v["over_accepted"]
    assert v["mark"] == "EXACT"


def test_a_coarse_code_returned_as_broader_is_the_right_answer():
    v = j("Iron deficiency anaemia", [], ["271737000"])
    assert v["correct"]
    assert not v["over_accepted"]


def test_a_sibling_concept_is_not_a_parent():
    """44054006 is type 2 specifically. Returning it for type 1, in either list,
    is over-acceptance rather than caution."""
    assert not j("Type 1 diabetes mellitus", [], ["44054006"])["correct"]
    assert not j("Type 1 diabetes mellitus", ["44054006"])["correct"]
    assert j("Type 1 diabetes mellitus", [])["correct"]


def test_abstaining_everywhere_does_not_score_well():
    """The failure mode a coverage-blind metric rewards. An empty answer is
    correct only for the concepts that really are absent."""
    rows = [{**p, **judge(p, [], [])} for p in PROBES]
    n_ok = sum(1 for r in rows if r["correct"])
    n_absent = sum(1 for p in PROBES if p["class"] == "absent")
    assert n_ok == n_absent, "silence scored on a probe that is not about silence"
    assert n_ok < len(PROBES) / 2


def test_returning_everything_does_not_score_well():
    every = sorted({c for p in PROBES for c in p["codes"] + p["broader"]})
    rows = [{**p, **judge(p, every, [])} for p in PROBES]
    assert sum(1 for r in rows if r["correct"]) == 0


def test_an_exact_code_parked_in_broader_is_counted():
    """It costs verdicts: the engine returns UNKNOWN for a broader code and TRUE
    for an exact one. Reported rather than scored, because the accept lists hold
    several defensible codes and the model may be drawing a finer distinction."""
    v = j("Haemodialysis", ["302497006"], ["265764009"])
    assert v["correct"]
    assert v["demoted"] == ["265764009"]
    assert v["mark"] == "ok- "
    assert score([{**BY_NAME["Haemodialysis"], **v}])["gap"]["demoted"] == 1


def test_a_transport_error_is_not_scored_as_a_wrong_answer():
    v = judge(BY_NAME["Metformin"], None, None)
    assert v["mark"] == "ERR "
    assert not v["correct"] and not v["over_accepted"]


@pytest.mark.parametrize("concept", ["Essential hypertension", "Metformin"])
def test_a_subset_of_the_accepted_codes_is_correct(concept):
    """Several codes can be defensible for one concept. Demanding an exact set
    would score a correct-but-different choice as a failure, and the fix for that
    failure would be a less careful grounder."""
    assert j(concept, BY_NAME[concept]["codes"][:1])["correct"]
