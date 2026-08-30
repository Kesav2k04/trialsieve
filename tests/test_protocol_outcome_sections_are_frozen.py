"""The sections that decide the outcome are byte-identical to their registration.

`docs/EVAL_PROTOCOL.md` opens by saying it was registered before any scored run
and that the ordering is checkable with `git log`. It has been amended since,
each amendment logged with its reason, which is the honest way to do it and is
also exactly the shape a moved goalpost takes. A reviewer put it plainly: the
amendments are disclosed, and nothing checks that the parts that decide whether
this project succeeded are not among them.

So this checks the three that matter. What is being claimed, the decision rule
fixed in advance, and what would falsify the thesis are compared against the
commit that added the file. Everything else in the protocol may be amended and
the amendment list is where that is argued; these three may not be, because they
are the ones a result can be made to pass by editing.

**Two sources, and the weaker one is never alone silently.** Every assertion here
used to read the object database, so an unpacked source archive skipped the whole
file and the one load-bearing claim about how this evaluation was run was
checkable only by someone who cloned. `docs/protocol_registration.json` carries
the registering commit and the sha256 of each frozen section, written from git by
`scripts/freeze_protocol.py`. With git present that file is itself verified
against the object database, so a clone cannot be fooled by an edited receipt.
Without git it is the only record, and the test that says so is a passing test
with an explicit name rather than a skip.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_protocol import FROZEN, digest, section  # noqa: E402

PROTOCOL = "docs/EVAL_PROTOCOL.md"
RESULTS = "results/results.json"
RECEIPT = ROOT / "docs" / "protocol_registration.json"


def _git(*args: str) -> str | None:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout if p.returncode == 0 else None


def _has_git() -> bool:
    log = _git("log", "--format=%H", "-1", "--", PROTOCOL)
    return bool(log and log.strip())


@pytest.fixture(scope="module")
def receipt() -> dict:
    assert RECEIPT.exists(), (
        f"{RECEIPT.relative_to(ROOT).as_posix()} is missing, so an archive has no "
        f"way to check the freeze. Run: python scripts/freeze_protocol.py")
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registered() -> str:
    """The protocol as it was in the commit that introduced it."""
    log = (_git("log", "--format=%H", "--", PROTOCOL) or "").split()
    if not log:
        pytest.skip("no history for the protocol in this checkout")
    return _git("show", f"{log[-1]}:{PROTOCOL}") or ""


# -- what every reader can check, git or no git -----------------------------

@pytest.mark.parametrize("head", FROZEN)
def test_the_outcome_section_matches_its_registered_digest(head, receipt) -> None:
    """The freeze itself, from the receipt, so an archive checks it too."""
    now = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    here = section(now, head)
    assert here, f"section {head!r} is gone from the current protocol"
    frozen = receipt["frozen_sections"].get(head)
    assert frozen, (
        f"section {head!r} is not in {RECEIPT.name}, so this test is comparing "
        f"nothing; the heading was renamed and the freeze is void")
    assert digest(here) == frozen["sha256"], (
        f"section {head!r} differs from the version this protocol was registered "
        f"as, in commit {receipt['registered_in_commit'][:12]}. Amend anything "
        f"else and log it; not this one. In a clone, diff it against that commit.")
    assert len(here) == frozen["characters"], (
        f"section {head!r} is {len(here)} characters and was registered at "
        f"{frozen['characters']}")


def test_the_digest_would_notice_an_edit(receipt) -> None:
    """The control, because every assertion above is a comparison to equality."""
    now = (ROOT / PROTOCOL).read_text(encoding="utf-8")
    here = section(now, FROZEN[0])
    assert here, "nothing to control against"
    edited = here + "\n\nand also this."
    assert digest(edited) != receipt["frozen_sections"][FROZEN[0]]["sha256"], (
        "adding a sentence to the registered text did not change its digest, so "
        "the comparisons above are not reading the section they name")


def test_the_receipt_records_registration_before_the_first_result(receipt) -> None:
    """From recorded commit timestamps, not from the sentence that asserts it."""
    first = receipt.get("first_scored_result")
    assert first, f"{RECEIPT.name} does not record when the first result landed"
    assert first["seconds_after_registration"] > 0, (
        f"the protocol was committed at {receipt['registered_at_unix']} and the "
        f"first scored result at {first['added_at_unix']}, so the file's own "
        f"opening claim is false in this history")


def test_an_archive_without_git_still_checks_the_freeze() -> None:
    """Named so the absence of git is a reported condition, not a silent skip.

    A skip and a pass look the same in a summary line. This one states which of
    the two sources the run had, and it is the assertion that stops the receipt
    from being the thing that quietly disappears from an archive.
    """
    assert RECEIPT.exists(), "the registration receipt is not in this checkout"
    body = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert set(body["frozen_sections"]) == set(FROZEN), (
        f"the receipt freezes {sorted(body['frozen_sections'])}, which is not the "
        f"three sections this test names")
    assert re.fullmatch(r"[0-9a-f]{40}", body["registered_in_commit"]), (
        "the receipt does not name a commit")


# -- what only a clone can check --------------------------------------------

def test_the_receipt_agrees_with_the_object_database(receipt, registered) -> None:
    """A clone verifies the archive's copy, so an edited receipt cannot pass."""
    if not _has_git():
        pytest.skip("no object database in this checkout; the receipt is the record")
    for head in FROZEN:
        then = section(registered, head)
        assert then, (
            f"section {head!r} is not in the registering commit, so the receipt "
            f"was written against a different file")
        assert hashlib.sha256(then.encode("utf-8")).hexdigest() == \
            receipt["frozen_sections"][head]["sha256"], (
            f"{RECEIPT.name} records a digest for {head!r} that is not what the "
            f"registering commit holds. Re-run scripts/freeze_protocol.py.")


def test_the_receipt_names_the_registering_commit(receipt) -> None:
    if not _has_git():
        pytest.skip("no object database in this checkout; the receipt is the record")
    log = (_git("log", "--format=%H", "--", PROTOCOL) or "").split()
    assert log, "no history for the protocol"
    assert receipt["registered_in_commit"] == log[-1], (
        f"the receipt names {receipt['registered_in_commit'][:12]} and the first "
        f"commit touching the protocol is {log[-1][:12]}")


# -- the amendment list, which is prose about itself -------------------------

def test_the_amendment_list_states_its_own_length() -> None:
    """A phrase that states a count, so the count is checked."""
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
