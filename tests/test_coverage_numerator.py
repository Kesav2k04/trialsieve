"""Coverage is a claim about the system, so its numerator has to come from the system.

`evaluation/gold/criteria_set.py` marks 24 of the 40 gold criteria `checkable`.
That is a person deciding, before any run, whether a structured record could
settle the criterion at all. It is a ceiling. `scripts/report.py` used it as the
numerator and printed "the system expresses 24 criteria as predicates", which is
the answer key wearing the system's name.

The compiler produced 18 the day this was written. The difference is seven
criteria the vocabulary refused plus one lost to the IR validator, minus one that
compiled without being marked checkable. Against the registered denominator of 65
that was 27.7% rather than 37%, and the pre-registered band is 30 to 40%, so the
label decided whether the run is reported as inside or below its own prediction.

The predicates have moved since. The run in this checkout compiles 19 and reports
29.2%, still below the band. Those two figures are read out of the artifact by
the tests below rather than out of this paragraph, which is the whole point: a
docstring is prose and prose is what drifts.

These tests hold the numerator to the compiled artifact and hold both figures in
the document, so a future edit cannot quietly go back to the flattering one.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "results.json"
COMPILED = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"


def _cov() -> dict | None:
    if not RESULTS.exists():
        return None
    return json.loads(RESULTS.read_text(encoding="utf-8")).get("criterion_coverage")


def test_the_numerator_is_what_the_compiler_produced():
    cov = _cov()
    if cov is None or not COMPILED.exists():
        pytest.skip("no scored run in this checkout; criterion_coverage is not "
                    "published here, so the numerator was never checked")
    crit = json.loads(COMPILED.read_text(encoding="utf-8"))["criteria"]
    assert cov["n_compiled"] == sum(1 for c in crit if c.get("compilable")), (
        "criterion_coverage.n_compiled does not match the compiled run, so the "
        "published coverage is not a measurement of this system")


def test_the_ceiling_and_the_result_are_not_the_same_number():
    """If they ever coincide the distinction is untested, so say so out loud."""
    cov = _cov()
    if cov is None:
        pytest.skip("no scored run in this checkout; the ceiling and the result "
                    "were never compared")
    assert cov["n_checkable"] >= cov["n_compiled"], (
        "more criteria compiled than the gold set calls checkable, which means "
        "`checkable` is not the ceiling this report says it is")
    if cov["n_checkable"] == cov["n_compiled"]:
        raise AssertionError(
            "the checkable count and the compiled count are equal on this run. "
            "That may be legitimate, but it makes the two indistinguishable in "
            "every downstream number, so it has to be stated deliberately rather "
            "than passing quietly.")


def test_the_report_publishes_both_and_names_the_band_it_missed():
    md = ROOT / "results" / "RESULTS.md"
    cov = _cov()
    if cov is None or not md.exists():
        pytest.skip("no scored run or no RESULTS.md here; the report was never read")
    text = md.read_text(encoding="utf-8")
    assert f"{cov['compiled_of_segmented']:.1%}" in text, (
        "the compiled coverage figure is not in the report")
    assert "below it" in text or "inside it" in text, (
        "the report gives a coverage figure without saying which side of the "
        "registered band it falls on")
    assert len(cov["checkable_but_not_compiled"]) > 0
    for row in cov["checkable_but_not_compiled"]:
        assert row["criterion_id"] in text, (
            f"{row['criterion_id']} is in the gap between the ceiling and the "
            f"result and the report never names it")
