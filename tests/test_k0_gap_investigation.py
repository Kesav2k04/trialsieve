"""The k = 0 investigation is recomputed from the cells and matched to the prose.

`docs/EVAL_PROTOCOL.md` prediction 4 registered that a large gap at k = 0 would be
investigated before it was reported. The gap is 42.75 points and the report went
out for weeks without the investigation, so the section now exists. A section that
exists is not the same as a section that is true, and its conclusion is the one
sentence in this repository that argues against its own headline, which is exactly
the sentence somebody would be tempted to soften later.

So the strata are recounted here from `runs/tierA/cells/`, and the direction of the
conclusion is checked rather than assumed: if the baseline ever stops being the
more accurate arm on cells with a definite answer, the sentence has to change with
it, and this fails until it does.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "runs" / "tierA" / "cells"
RESULTS = ROOT / "results" / "RESULTS.md"
PUBLISHED = ROOT / "results" / "published" / "results.json"


def _paired() -> list[dict]:
    b2 = CELLS / "cells_B2_b2_10p.jsonl"
    scored = CELLS / "cells_TS-B0-B1_k0_seed7.jsonl"
    if not b2.is_file() or not scored.is_file():
        pytest.skip("no evaluated cells in this checkout; `python run.py reproduce` "
                    "writes them and this recounts the report against them")
    by_key = {}
    with open(scored, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                by_key[(r["patient_id"], r["criterion_id"])] = r
    rows = []
    with open(b2, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            src = by_key.get((r["patient_id"], r["criterion_id"]))
            if src:
                rows.append({"gold": r["gold"], "B2": r["B2"], "TS": src["TS"]})
    return rows


def _split(rows: list[dict]) -> dict:
    def block(subset):
        out = {"cells": len(subset)}
        for arm in ("B2", "TS"):
            answered = [r for r in subset if r[arm] in ("MEETS", "FAILS")]
            out[arm] = {"answered": len(answered),
                        "wrong": sum(1 for r in answered if r[arm] != r["gold"])}
        return out
    return {"definite": block([r for r in rows if r["gold"] in ("MEETS", "FAILS")]),
            "indeterminate": block([r for r in rows if r["gold"] == "INDETERMINATE"])}


def test_the_published_strata_match_the_cells() -> None:
    if not PUBLISHED.is_file():
        pytest.skip("no published results to check the recount against")
    published = json.loads(PUBLISHED.read_text(encoding="utf-8")).get("k0_gap_by_stratum")
    assert published, ("results/published/results.json carries no k0_gap_by_stratum, "
                       "so the section prediction 4 required is not being computed")
    mine = _split(_paired())
    for stratum in ("definite", "indeterminate"):
        assert published[stratum] == mine[stratum], (
            f"the published {stratum} stratum is {published[stratum]} and recounting "
            f"the cells gives {mine[stratum]}")


def test_the_conclusion_matches_the_direction_of_the_numbers() -> None:
    """The sentence says the baseline is the more accurate arm where an answer
    exists. That is a claim about two rates, and it is only true while it is."""
    if not RESULTS.is_file():
        pytest.skip("no report in this checkout")
    d = _split(_paired())["definite"]
    if not d["B2"]["answered"] or not d["TS"]["answered"]:
        pytest.skip("one arm answered nothing in the definite stratum")
    b2 = d["B2"]["wrong"] / d["B2"]["answered"]
    ts = d["TS"]["wrong"] / d["TS"]["answered"]
    text = RESULTS.read_text(encoding="utf-8")
    m = re.search(r"the per-cell baseline is (more accurate than|no more accurate "
                  r"than) this system", text)
    assert m, ("the k = 0 section no longer states which arm is more accurate on "
               "cells with a definite answer. It is allowed to stop saying so, but "
               "delete this test deliberately rather than let it pass on silence.")
    said_better = m.group(1) == "more accurate than"
    assert said_better == (b2 < ts), (
        f"the report says the baseline is '{m.group(1)}' this system on cells with a "
        f"definite answer, and the cells give {b2:.1%} against {ts:.1%}")


def test_the_section_is_in_the_report() -> None:
    if not RESULTS.is_file():
        pytest.skip("no report in this checkout")
    text = RESULTS.read_text(encoding="utf-8")
    assert "## The k = 0 gap" in text, (
        "the report no longer carries the k = 0 investigation. Prediction 4 in "
        "docs/EVAL_PROTOCOL.md requires it before the gap is reported, and the gap "
        "is reported in the comparison tables above it.")
