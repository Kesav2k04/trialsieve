"""Everything the protocol registered has to appear in what a reader opens.

Two things were registered before the first scored run and then reported nowhere.
`resolved_correct_per_screen` is a co-primary outcome, in the protocol's own words
*so an arm cannot win by abstaining*; the scorer computed it from the first run, the
baseline wins it, and it appeared in no document at all while the coverage row was
being explained as lower on purpose. Four of the five registered predictions were
never compared to an outcome either.

Neither was hidden. Both were simply not carried forward, which is what makes this a
gate rather than a correction: a pre-registration is only worth the branch nobody
wanted, and nothing was checking that the unwanted branch arrived.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "EVAL_PROTOCOL.md"
RESULTS = ROOT / "results" / "RESULTS.md"
SCORECARD = ROOT / "docs" / "SCORECARD.md"
PUBLISHED = ROOT / "results" / "published" / "results.json"


def _registered_metrics() -> set[str]:
    """Metric names the protocol registers as primary or co-primary."""
    text = PROTOCOL.read_text(encoding="utf-8")
    names = set()
    for m in re.finditer(r"\*\*Co-primary\.\*\*\s*`([a-z_]+)`", text):
        names.add(m.group(1))
    return names


def test_the_protocol_still_registers_a_co_primary() -> None:
    """If this stops finding one, the test below passes on an empty set."""
    assert _registered_metrics(), (
        "no co-primary outcome parsed out of docs/EVAL_PROTOCOL.md, so the check "
        "below has nothing to look for. Either the protocol changed or the pattern "
        "did; fix whichever it is rather than letting this pass on silence.")


def test_every_registered_outcome_appears_in_the_reporting() -> None:
    if not RESULTS.is_file() or not SCORECARD.is_file():
        pytest.skip("no generated report in this checkout")
    results = RESULTS.read_text(encoding="utf-8")
    scorecard = SCORECARD.read_text(encoding="utf-8")
    missing = []
    for name in _registered_metrics():
        pretty = name.replace("_", " ")
        for doc, text in (("results/RESULTS.md", results),
                          ("docs/SCORECARD.md", scorecard)):
            if name not in text and pretty not in text:
                missing.append(f"{name} is missing from {doc}")
    assert not missing, (
        "the protocol registers these outcomes and the reporting does not carry "
        "them:\n  " + "\n  ".join(missing) +
        "\nA registered outcome that appears in no document is a guard that was "
        "computed and then dropped.")


def test_the_co_primary_is_reported_with_the_arm_that_wins_it() -> None:
    """Printing the number is not the same as saying who won. The point of the
    co-primary is that abstention has a cost, so the row has to name the arm."""
    if not PUBLISHED.is_file() or not RESULTS.is_file():
        pytest.skip("no published results in this checkout")
    published = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    paired = (published.get("groups") or {}).get("b2_10p") or {}
    cells = paired.get("cell_scores") or {}
    if "B2" not in cells or "TS" not in cells:
        pytest.skip("the paired group has no B2 in this run")
    b2 = cells["B2"]["resolved_correct_per_screen"]
    ts = cells["TS"]["resolved_correct_per_screen"]
    text = RESULTS.read_text(encoding="utf-8")
    winner = "B2" if b2 > ts else "TS"
    assert f"The co-primary goes to {winner}" in text, (
        f"B2 resolves {b2} correct per screen and TS resolves {ts}, so the "
        f"co-primary goes to {winner}, and results/RESULTS.md does not say so.")


def test_all_five_predictions_are_scored() -> None:
    if not PUBLISHED.is_file():
        pytest.skip("no published results in this checkout")
    preds = json.loads(PUBLISHED.read_text(encoding="utf-8")).get(
        "registered_predictions")
    assert preds and len(preds) == 5, (
        "results/published/results.json carries no five-row prediction scoring. "
        "Four of the five registered predictions were once never compared to an "
        "outcome, which is the failure this row count exists to stop.")
    for row in preds:
        assert row.get("held"), f"prediction {row.get('n')} has no verdict"
        assert row.get("measured"), f"prediction {row.get('n')} has no measurement"
    if RESULTS.is_file():
        assert "## The five registered predictions, scored" in RESULTS.read_text(
            encoding="utf-8"), "the prediction table is not in the report"
