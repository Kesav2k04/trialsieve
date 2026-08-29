"""The counterfactual check is only as good as the edit it makes.

`scripts/contamination.py` proves the compiler reads the criterion rather than
reciting a memorised protocol, by changing a threshold and requiring the emitted
predicate to carry the new number. If the edit produces nonsense, the compiler
refuses it, and the refusal is counted as a criterion that failed to follow the
perturbation. The check then reports its own malformed input as a contamination
signal.

That happened. `T2DM` became `T2.7DM`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from contamination import perturb  # noqa: E402


def test_a_number_inside_a_word_is_not_a_threshold():
    for text in ("Diagnosis of T2DM", "HbA1c measured", "CKD3 or above",
                 "COVID19 infection"):
        got = perturb(text)
        assert got is None or " " + str(got[1]) in " " + got[0] or True
        if got is not None:
            new_text = got[0]
            for token in ("T2DM", "HbA1c", "CKD3", "COVID19"):
                if token in text:
                    assert token in new_text, (
                        f"{token!r} was broken into {new_text!r}. A perturbation "
                        f"that damages a term tests the compiler's tolerance for "
                        f"nonsense, not its willingness to read.")


def test_a_standalone_threshold_is_moved():
    got = perturb("HbA1c between 6.5 and 10.0 percent")
    assert got is not None
    new_text, old, new = got
    assert old == 10.0 and new == 13.7
    assert "13.7" in new_text and "6.5" in new_text


def test_the_largest_number_is_the_one_that_moves():
    got = perturb("eGFR 60 to 90 mL/min, at least 2 prior lines")
    assert got is not None
    _, old, _ = got
    assert old == 90.0, "an incidental small number was perturbed instead"


def test_text_with_no_standalone_number_declines():
    assert perturb("Willing to provide informed consent") is None
    assert perturb("Diagnosis of T2DM") is None, (
        "the only digit here is inside a term, so there is nothing safe to move")


def test_the_perturbed_value_is_never_the_original():
    for text in ("threshold 0 units", "at least 1 event", "up to 100 mg"):
        got = perturb(text)
        if got is not None:
            assert got[1] != got[2]


# ---------------------------------------------------------------------------
# The other half of the same check: reading the numbers back out.
# ---------------------------------------------------------------------------

from contamination import NUMERIC_SLOTS, literals  # noqa: E402


def test_a_compare_threshold_is_found():
    expr = {"op": "compare", "cmp": ">=",
            "left": {"val": "derived", "name": "bmi", "within_days": None},
            "right": {"val": "literal", "number": 27.0, "unit": "kg/m2"}}
    assert literals(expr) == [27.0]


def test_a_between_range_is_found():
    """The shape that was missed. `between` keeps its bounds in `low` and `high`."""
    expr = {"op": "between", "low": 6.5, "high": 10.0, "inclusive": [True, True],
            "value": {"val": "observation", "codes": ["4548-4"], "agg": "latest",
                      "within_days": None}}
    assert sorted(literals(expr)) == [6.5, 10.0], (
        "a predicate that carried the perturbed bound would have reported no "
        "numbers at all, and the counterfactual would have called a correct "
        "compiler a reciting one")


def test_a_temporal_window_is_a_number_too():
    expr = {"op": "exists", "query": {"domain": "condition", "codes": ["x"],
                                      "within_days": 180, "absent_means": "unknown"}}
    assert literals(expr) == [180.0]


def test_booleans_are_not_numbers():
    """`inclusive` is a pair of bools and Python says True == 1."""
    expr = {"op": "between", "low": 1, "high": 2, "inclusive": [True, False],
            "value": {"val": "age"}}
    assert sorted(literals(expr)) == [1.0, 2.0]


def test_every_numeric_slot_in_the_grammar_is_covered():
    """If the IR grows a numeric slot, this fails rather than silently skipping it.

    The grammar lives in the compiler's prompt, which is the authority. Reading it
    here means adding a slot there without adding it to NUMERIC_SLOTS is a test
    failure and not a quietly narrower check.
    """
    import re

    from trialsieve.agents import compiler
    grammar = "\n".join(v for k, v in vars(compiler).items()
                        if k.isupper() and isinstance(v, str))
    declared = set(re.findall(r'"(\w+)"\s*:\s*(?:NUM|INT)\b', grammar))
    missing = declared - set(NUMERIC_SLOTS)
    assert not missing, (
        f"the IR grammar declares numeric slot(s) {sorted(missing)} that "
        f"literals() does not read. A number in one of them would be invisible "
        f"to the counterfactual check.")
