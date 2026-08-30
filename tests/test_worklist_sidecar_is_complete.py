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


CSV = ROOT / "docs" / "sample_worklist.csv"


@pytest.fixture(scope="module")
def sheet() -> list[dict]:
    """The third copy: the one a trial site can open without a programmer.

    Read with `csv.DictReader` rather than by index, because that is what an
    import does and because reading it by index is how the first version passed
    while binding `patient_id` to a column called `trial`. A metadata block above
    the header made every field name wrong and spilled the evidence into a `None`
    key, so the one artifact described as the form a screening log takes was the
    one artifact that could not be imported.
    """
    import csv as _csv
    if not CSV.is_file():
        pytest.skip("no sample worklist csv; run scripts/gate_demo.py")
    with CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    assert rows, "the sheet has a header and no rows"
    return rows


def test_a_stock_reader_binds_the_right_columns(sheet) -> None:
    first = sheet[0]
    assert None not in first, (
        "a row has more fields than the header names, so the reader put the "
        "overflow under None and every column after it is shifted")
    assert first["patient_id"] and "-" in first["patient_id"], (
        f"patient_id came back as {first['patient_id']!r}, which is not a "
        f"patient identifier, so the header row is not the first row")
    assert first["verdict"] in ("FAILS", "INDETERMINATE", "MEETS", ""), (
        f"verdict came back as {first['verdict']!r}")


def test_the_sheet_holds_every_cell_not_every_patient(side, sheet) -> None:
    expected = side["n_screens"] * len(side["criteria_used"])
    assert len(sheet) == expected, (
        f"the sheet has {len(sheet)} rows and the panel is {side['n_screens']} "
        f"patients against {len(side['criteria_used'])} criteria, which is "
        f"{expected} cells")


def test_the_sheet_agrees_with_the_document_on_who_was_ruled_out(side, sheet) -> None:
    by_decision: dict[str, set[str]] = {}
    for r in sheet:
        by_decision.setdefault(r["decision"], set()).add(r["patient_id"])
    for key, group in (("INELIGIBLE", "ruled_out"), ("NEEDS_REVIEW", "review"),
                       ("ELIGIBLE", "eligible")):
        theirs = {p["patient_id"] for p in side[group]}
        assert by_decision.get(key, set()) == theirs, (
            f"{key}: the sheet and the sidecar name different patients")


def test_every_row_carries_its_provenance_and_the_unsigned_mark(side, sheet) -> None:
    """A row pasted into a screening log arrives without the rows around it."""
    mark = "TRUE" if side["not_for_use"] else "FALSE"
    bad = [r["patient_id"] for r in sheet
           if r["trial"] != side["trial"] or r["generated"] != side["generated"]
           or r["run"] != side["run"] or r["not_for_use"] != mark]
    assert not bad, (
        f"{len(bad)} rows do not carry the trial, date, run and override mark "
        f"that the document and the JSON carry, first {bad[:3]}")
    assert int(sheet[0]["criteria_answered"]) == len(side["criteria_used"])
    assert int(sheet[0]["criteria_in_protocol"]) > int(sheet[0]["criteria_answered"]), (
        "the sheet claims the protocol is no larger than the part that was "
        "answered, which is the fact the document exists to be honest about")


def test_the_column_that_makes_this_a_phone_call_is_reserved(sheet) -> None:
    """`4b10c406` is a Synthea id, not somebody a coordinator can ring.

    Identity linkage is the site's own step and this project does not do it. The
    column exists and is empty so the mapping is obvious rather than invented per
    site, and so nobody mistakes the patient id for a record number.
    """
    assert "site_mrn" in sheet[0], "no column for the site's own record number"
    assert all(not r["site_mrn"] for r in sheet), (
        "site_mrn is populated; this repository has no identity linkage and a "
        "value here would be one it invented")


def test_the_readme_counts_the_protocol_the_way_the_document_does(side) -> None:
    """`README.md` types 15, 3 and 12. All three are in the run.

    A count of what a document does not do is exactly the kind of number that
    stops being true when a criterion recompiles, and it is the one a reader uses
    to decide whether the shrink is worth anything.
    """
    import json as _json
    import re as _re
    compiled = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"
    if not compiled.is_file():
        pytest.skip("no compiled run in this checkout")
    own = [c for c in _json.loads(compiled.read_text(encoding="utf-8"))["criteria"]
           if c.get("nct_id") == side["trial"]]
    total, answered = len(own), len(side["criteria_used"])
    doc = DOC.read_text(encoding="utf-8")
    assert "## What this document does not settle" in doc, (
        "the worklist no longer says what it left undone. That section is built "
        "from the trial's own criterion list, and it renders as nothing at all if "
        "the trial id stops matching, which is a silent way to lose the half a "
        "coordinator is accountable for.")
    assert f"This trial has **{total} criteria**" in doc, (
        f"the document does not state the protocol size as {total}")

    m = _re.search(
        r"this\s+trial has (\d+) criteria, the document answers (\d+), and the other\s+"
        r"(\d+)\b", ROOT.joinpath("README.md").read_text(encoding="utf-8"))
    assert m, "the README sentence about unsettled criteria was reworded; update this"
    assert (int(m.group(1)), int(m.group(2)), int(m.group(3))) == \
           (total, answered, total - answered), (
        f"README says {m.group(1)}/{m.group(2)}/{m.group(3)}, the run has "
        f"{total}/{answered}/{total - answered}")
    assert total > answered, (
        "the trial has no criteria beyond the ones answered, so this test is "
        "checking a subtraction that is always zero")
