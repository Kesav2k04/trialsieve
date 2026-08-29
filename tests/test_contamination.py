"""No trial identifier may reach a prompt, and the check must be able to fail.

The audit itself is in `scripts/contamination.py`. These tests pin the two
properties that make its verdict worth reading: it catches a leak when there is
one, and its title fingerprints are narrow enough that a passing result means
something.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import contamination as C  # noqa: E402


def test_no_prompt_template_takes_an_identifier():
    res = C.audit_templates()
    assert res["pass"], f"prompt templates with an identifier slot: {res['offending']}"
    assert res["templates"], "no templates found, the audit is looking in the wrong place"


def test_audit_would_catch_a_leak(monkeypatch):
    """The audit fails when a template does take an identifier.

    Without this, a rename that made `audit_templates` find nothing would report
    a clean pass forever.
    """
    from trialsieve.agents import segmenter
    monkeypatch.setattr(segmenter, "LEAKY_PROMPT_FOR_TEST",
                        "Trial {nct_id}, criteria: {text}", raising=False)
    res = C.audit_templates()
    assert not res["pass"]
    assert any("nct_id" in r["slots"] for r in res["offending"])


def test_disease_name_is_not_a_title_fingerprint():
    """A word sequence the criteria already contain cannot be evidence of a leak."""
    legit = {"chronic kidney disease"}
    grams = C.title_ngrams("A Study of Chronic Kidney Disease Progression", legit)
    assert "chronic kidney disease" not in grams
    assert grams, "subtracting one sequence should not empty the fingerprint set"


def test_stop_words_alone_are_not_a_fingerprint():
    assert C.title_ngrams("Safety and Efficacy of the Study", set()) == []


def test_legitimate_ngrams_are_read_from_the_vendored_criteria():
    legit = C.legitimate_ngrams()
    assert len(legit) > 500, f"only {len(legit)} sequences; the trial files were not read"


@pytest.mark.parametrize("text,expect_old,expect_new", [
    ("HbA1c between 7.0 and 10.5 percent", 10.5, 14.4),
    ("Age 18 years or older", 18, 24.7),
])
def test_perturbation_moves_the_largest_number(text, expect_old, expect_new):
    new_text, old, new = C.perturb(text)
    assert old == expect_old
    assert new == expect_new
    assert str(expect_new) in new_text
    assert new_text != text


def test_perturbation_declines_when_there_is_nothing_to_move():
    assert C.perturb("Willing and able to give informed consent") is None
    assert C.perturb("Zero prior lines: 0") is None


def test_literals_are_collected_from_a_nested_predicate():
    expr = {"op": "and", "args": [
        {"op": "compare", "left": {"val": "age"}, "cmp": ">=",
         "right": {"val": "literal", "number": 18}},
        {"op": "compare", "left": {"val": "observation", "codes": ["4548-4"],
                                   "unit": "%"}, "cmp": "<",
         "right": {"val": "literal", "number": 10.5}},
    ]}
    assert sorted(C.literals(expr)) == [10.5, 18.0]


def _res(**cf):
    base = {"templates": {"pass": True}, "cassettes": {"pass": True}}
    return dict(base, counterfactual=cf) if cf else base


def test_a_clean_counterfactual_passes():
    assert C.failures(_res(n_compiled=6, n_recites=0)) == []


def test_reciting_the_original_number_fails_the_run():
    """The report printed the recite count in bold and the exit code ignored it,
    so the check the protocol calls the strongest of the three could not fail a
    run. One predicate carrying the pre-perturbation threshold is enough."""
    out = C.failures(_res(n_compiled=6, n_recites=1))
    assert len(out) == 1
    assert "reproduce the original number" in out[0]


def test_a_counterfactual_that_measured_nothing_fails():
    out = C.failures(_res(n_compiled=0, n_recites=0))
    assert out and "nothing was measured" in out[0]


def test_no_counterfactual_key_is_not_a_failure():
    """--counterfactual is opt-in. Not asking for the check is not the same as
    the check finding something."""
    assert C.failures(_res()) == []
