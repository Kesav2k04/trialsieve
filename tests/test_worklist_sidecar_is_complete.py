"""The machine-readable half of the worklist, checked against what the document says.

`docs/sample_worklist.md` lists 20 ruled-out patients and then sends the reader to
`docs/sample_worklist.json` for the rest. That file used to hold nine keys, every
one of them a count, so 167 of 187 exclusions had no reachable evidence anywhere in
a repository whose whole argument is that a person removed from a panel is owed a
dated reason somebody can check.

`docs/GATE.md` separately says the unsigned override "leaves a mark in the artifact
rather than only in a shell history". The markdown stamped NOT FOR USE on every
page and the sidecar carried no trace of it, so the half a person reads was marked
and the half a machine reads was not.

Both are claims about a file, so both are checked against the file.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "docs" / "sample_worklist.json"
DOC = ROOT / "docs" / "sample_worklist.md"


@pytest.fixture(scope="module")
def side() -> dict:
    if not SIDECAR.is_file():
        pytest.skip("no sample worklist in this checkout; run scripts/gate_demo.py")
    return json.loads(SIDECAR.read_text(encoding="utf-8"))


def test_it_holds_patients_and_not_only_counts(side) -> None:
    """The rows the document promises are here, in the number it promises."""
    for group in ("ruled_out", "review", "eligible"):
        rows = side.get(group)
        assert isinstance(rows, list), f"{group} is not a list of patients"
        claimed = side[f"n_{group}"]
        assert len(rows) == claimed, (
            f"{group}: the sidecar counts {claimed} and carries {len(rows)}. A "
            f"reader sent here for the rest of them arrives at a shorter list.")
        assert claimed > 0, f"{group} is empty, so this test checked nothing"


def test_every_exclusion_carries_its_evidence(side) -> None:
    """A patient removed from the panel is owed a reason that can be read."""
    bare = [r["patient_id"] for r in side["ruled_out"]
            if not r.get("failed") or not all(f.get("evidence", "").strip()
                                              for f in r["failed"])]
    assert not bare, (
        f"{len(bare)} ruled-out patients carry no evidence, first {bare[:3]}")


def test_the_people_who_get_a_phone_call_carry_theirs(side) -> None:
    """The eligible are the only rows this document says to act on."""
    bare = [r["patient_id"] for r in side["eligible"]
            if not r.get("met") or not all(m.get("evidence", "").strip()
                                           for m in r["met"])]
    assert not bare, f"{len(bare)} eligible patients carry no evidence"


def test_the_questions_are_written_out_rather_than_named(side) -> None:
    """`NCT06983054-INC-02` is an identifier. The text is what makes it a question."""
    text = side.get("criterion_text") or {}
    used = set(side["criteria_used"])
    assert set(text) == used, (
        f"criterion_text covers {sorted(set(text))}, criteria_used is {sorted(used)}")
    empty = sorted(k for k, v in text.items() if not v.strip())
    assert not empty, f"criterion text is present but empty for {empty}"


def test_the_unsigned_mark_is_in_the_machine_half_too(side) -> None:
    """`docs/GATE.md` claims the override marks the artifact. This is the artifact."""
    assert "not_for_use" in side, (
        "the sidecar carries no not_for_use field, so an unsigned worklist is "
        "byte-indistinguishable from a signed one to anything that reads JSON")
    assert side["not_for_use"] is (side.get("reviewer") in (None, "")), (
        "not_for_use disagrees with the reviewer field")
    if side["not_for_use"]:
        assert "NOT FOR USE" in DOC.read_text(encoding="utf-8"), (
            "the sidecar says not_for_use and the document does not say so")


def test_it_says_which_run_it_came_from(side) -> None:
    for field in ("generated", "run", "trial"):
        assert side.get(field), f"the sidecar does not record {field}"
