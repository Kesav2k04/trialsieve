"""The sections that decide the outcome are byte-identical to their registration.

`docs/EVAL_PROTOCOL.md` opens by saying it was registered before any scored run and
that the ordering is checkable with `git log`. It has been amended nine times since,
each amendment logged with its reason, which is the honest way to do it and is also
exactly the shape a moved goalpost takes. A reviewer put it plainly: the amendments
are disclosed, and nothing checks that the parts that decide whether this project
succeeded are not among them.

So this checks the two that matter. What is being claimed, the decision rule fixed
in advance, and what would falsify the thesis are compared against the commit that
added the file. Everything else in the protocol may be amended and the amendment
list is where that is argued; these three may not be, because they are the ones a
result can be made to pass by editing.

The ordering claim is checked too, from the commit timestamps rather than from the
sentence that asserts it.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "docs/EVAL_PROTOCOL.md"
RESULTS = "results/results.json"

#: The sections a result could be made to pass by editing.
FROZEN = ("1. What is being claimed",
          "11. Decision rule, fixed in advance",
          "12. What would falsify the thesis")


def _git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        pytest.skip(f"git said no: {' '.join(args)}")
    return p.stdout


def _section(text: str, head: str) -> str | None:
    m = re.search(r"^## " + re.escape(head) + r"$(.*?)(?=^## |\Z)", text,
                  re.M | re.S)
    return m.group(1).strip() if m else None


@pytest.fixture(scope="module")
def registered() -> str:
    """The protocol as it was in the commit that introduced it."""
    log = _git("log", "--format=%H", "--", PROTOCOL).split()
    if not log:
        pytest.skip("no history for the protocol in this checkout")
    return _git("show", f"{log[-1]}:{PROTOCOL}")


@pytest.mark.parametrize("head", FROZEN)
def test_the_outcome_section_has_not_moved(head, registered) -> None:
    now = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    then, here = _section(registered, head), _section(now, head)
    assert then, (
        f"section {head!r} is not in the registering commit, so this test is "
        f"comparing nothing; the heading was renamed and the freeze is void")
    assert here, f"section {head!r} is gone from the current protocol"
    assert here == then, (
        f"section {head!r} differs from the version this protocol was registered "
        f"as. Amend anything else and log it; not this one. Diff it with "
        f"`git diff $(git log --format=%H -- {PROTOCOL} | tail -1) -- {PROTOCOL}`.")


def test_the_freeze_would_notice_an_edit(registered) -> None:
    """The control, because every assertion above is a comparison to equality."""
    then = _section(registered, FROZEN[0])
    assert then, "nothing to control against"
    assert _section(registered.replace(then, then + "\n\nand also this."),
                    FROZEN[0]) != then, (
        "editing the registered text did not change what the extractor returns, "
        "so the comparisons above are not reading the section they name")


def test_the_protocol_was_registered_before_the_first_result() -> None:
    """From the commit dates, not from the sentence in the file that says so."""
    reg = _git("log", "--format=%ct", "--", PROTOCOL).split()
    res = _git("log", "--diff-filter=A", "--format=%ct", "--", RESULTS).split()
    if not reg or not res:
        pytest.skip("no history for one of the two files in this checkout")
    assert int(reg[-1]) < int(res[-1]), (
        f"the protocol was committed at {reg[-1]} and the first scored result at "
        f"{res[-1]}, so the file's own opening claim is false in this history")


def test_the_amendment_list_states_its_own_length() -> None:
    """`these nine differences and no others` is a count, so it is counted."""
    text = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    entries = re.findall(r"^\*\*A(\d+),", text, re.M)
    assert entries, "no amendment entries found; the format changed"
    assert [int(n) for n in entries] == list(range(1, len(entries) + 1)), (
        f"the amendments are numbered {entries}, which is not a run from 1")
    words = {"nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
             "fourteen": 14, "fifteen": 15}
    m = re.search(r"these (\w+) differences and no others", text)
    assert m, "the amendment list no longer states how many there are"
    claimed = words.get(m.group(1).lower())
    assert claimed is not None, f"unhandled number word {m.group(1)!r}"
    assert claimed == len(entries), (
        f"the list says {m.group(1)} and carries {len(entries)}")
