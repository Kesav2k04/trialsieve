"""A criterion lost to a validator is not a criterion the system refused.

`reason_not_compilable` holds both. Every entry in the scored run now names a
blocker a person would agree with, and none reads `compiler failed`.

For one run that was not true. `NCT06989723-EXC-01` had a second concept that
grounds to a broader-only code with no exact code at all, and the IR had no shape
for it: `ir.py` demanded a non-empty `codes` list, so the answer the README asks
for could not be written down. The model sent the design-correct shape first, was
rejected, hedged, was rejected again, and ran out of retries. It was counted as a
refusal, which made a validator defect look like the system exercising judgment.

The IR now accepts an empty `codes` list when `broader_codes` carries the
concept, and the criterion compiles. `EXHAUSTED` is empty rather than deleted:
these tests hold the split, so a future crash cannot be absorbed into the refusal
count the way that one was.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPILED = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"

#: Criteria in the scored run that ran out of retries, by name. Empty now.
EXHAUSTED: set[str] = set()

CRASH_PREFIX = "compiler failed:"


def _criteria() -> list[dict]:
    return json.loads(COMPILED.read_text(encoding="utf-8"))["criteria"]


def test_the_split_between_refusal_and_exhaustion_is_what_the_report_says():
    if not COMPILED.exists():
        pytest.skip("no compiled run in this checkout; nothing to count")
    nope = [c for c in _criteria() if not c.get("compilable")]
    crashed = {c["criterion_id"] for c in nope
               if str(c.get("reason_not_compilable", "")).startswith(CRASH_PREFIX)}
    assert crashed == EXHAUSTED, (
        f"the criteria that ran out of retries are {sorted(crashed)}, and this "
        f"test records {sorted(EXHAUSTED)}. A new one is a criterion lost to the "
        f"validator and it has to be named in results/RESULTS.md, not counted "
        f"beside the refusals.")
    assert len(nope) - len(crashed) == 21


def test_every_principled_refusal_says_something_a_person_can_check():
    """A refusal with no reason is indistinguishable from a crash with a label."""
    if not COMPILED.exists():
        pytest.skip("no compiled run in this checkout; nothing to count")
    for c in _criteria():
        if c.get("compilable") or c["criterion_id"] in EXHAUSTED:
            continue
        reason = str(c.get("reason_not_compilable", "")).strip()
        assert len(reason) > 30, f"{c['criterion_id']} refuses with {reason!r}"
        assert not reason.startswith(CRASH_PREFIX)


def test_the_lost_criterion_is_disclosed_by_name_in_the_report():
    """The report is the artifact a reader sees. The name has to be in it."""
    md = (ROOT / "results" / "RESULTS.md")
    if not md.exists():
        pytest.skip("no compiled run or no RESULTS.md here; nothing to compare")
    text = md.read_text(encoding="utf-8")
    assert "What did not compile, and why" in text
    for cid in EXHAUSTED:
        assert cid in text, f"{cid} was lost to the validator and the report never names it"
    # With nothing lost, the report still has to say so rather than go quiet. A
    # section that simply stops mentioning the split reads identically to one
    # where the split was never computed.
    if not EXHAUSTED:
        assert "ran out of retries" in text or "exhausted" in text.lower(), (
            "no criterion was lost to the validator and the report does not say "
            "so, which is indistinguishable from the report not checking")
    assert "ir.py:103" in text, (
        "the report gives the rejection counts without the rule that caused them, "
        "which leaves the reader thinking the model failed")
