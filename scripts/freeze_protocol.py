"""Write the pre-registration into a file an archive can check itself against.

    python scripts/freeze_protocol.py            # write docs/protocol_registration.json
    python scripts/freeze_protocol.py --check    # verify it against git, write nothing

`docs/EVAL_PROTOCOL.md` claims it was registered before any scored result, and
`tests/test_protocol_outcome_sections_are_frozen.py` checks that claim against
the object database: it reads the protocol out of the commit that introduced it
and compares the three sections a result could be made to pass by editing.

That check is the strongest one available and it is also unavailable to most of
the people who will look. A source archive has no `.git`, so every assertion in
that file skipped, and the freeze, which is the single load-bearing claim about
how this evaluation was conducted, was verifiable only by someone who cloned.

So the registration is written here as data: the registering commit, its
timestamp, and the sha256 of each frozen section as that commit had it. With git
present the test verifies this file against the object database, so a checkout
that has history cannot be fooled by an edited receipt. Without git the file is
the only record and the test says so in as many words rather than passing
quietly, because a reader offline is trusting the archive and should be told
that is what they are doing.

The file records the protocol's own registering commit, which is an earlier
commit than the one that will carry the file. It never records its own.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "docs/EVAL_PROTOCOL.md"
RESULTS = "results/results.json"
OUT = ROOT / "docs" / "protocol_registration.json"

#: The sections a result could be made to pass by editing. Kept in step with
#: `tests/test_protocol_outcome_sections_are_frozen.py`, which imports this
#: tuple rather than repeating it.
FROZEN = ("1. What is being claimed",
          "11. Decision rule, fixed in advance",
          "12. What would falsify the thesis")


def git(*args: str) -> str | None:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout if p.returncode == 0 else None


def section(text: str, head: str) -> str | None:
    m = re.search(r"^## " + re.escape(head) + r"$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else None


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def registration() -> dict:
    """Build the record from git. Raises rather than guessing at any step."""
    log = (git("log", "--format=%H %ct", "--", PROTOCOL) or "").split(chr(10))
    log = [x for x in log if x.strip()]
    if not log:
        raise SystemExit(f"no history for {PROTOCOL}; this must be run in a clone")
    commit, when = log[-1].split()
    text = git("show", f"{commit}:{PROTOCOL}")
    if text is None:
        raise SystemExit(f"cannot read {PROTOCOL} out of {commit}")

    first_result = (git("log", "--diff-filter=A", "--format=%H %ct", "--", RESULTS)
                    or "").split(chr(10))
    first_result = [x for x in first_result if x.strip()]

    sections = {}
    for head in FROZEN:
        body = section(text, head)
        if body is None:
            raise SystemExit(
                f"section {head!r} is not in the registering commit {commit[:12]}, "
                f"so there is nothing to freeze; the heading was renamed")
        sections[head] = {"sha256": digest(body), "characters": len(body)}

    out = {
        "what_this_is":
            "The pre-registration, as data, so that a reader without a git object "
            "database can check the three sections of docs/EVAL_PROTOCOL.md that "
            "a result could be made to pass by editing. Written by "
            "scripts/freeze_protocol.py, which reads them out of the commit that "
            "introduced the protocol.",
        "what_this_does_not_establish":
            "That the registration is honest. A reader holding only a source "
            "archive is trusting this file, and a clone is not: with git present "
            "the test verifies every digest here against the object database, so "
            "the archive's copy can be checked by anyone who clones the "
            "repository. That is the whole of what it offers.",
        "protocol": PROTOCOL,
        "registered_in_commit": commit,
        "registered_at_unix": int(when),
        "frozen_sections": sections,
    }
    if first_result:
        rc, rw = first_result[-1].split()
        out["first_scored_result"] = {
            "path": RESULTS,
            "added_in_commit": rc,
            "added_at_unix": int(rw),
            "seconds_after_registration": int(rw) - int(when),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="compare the written file against git and write nothing")
    a = ap.parse_args()
    fresh = registration()
    if a.check:
        if not OUT.exists():
            print(f"{OUT.relative_to(ROOT).as_posix()} does not exist", file=sys.stderr)
            return 1
        have = json.loads(OUT.read_text(encoding="utf-8"))
        if have != fresh:
            print(f"{OUT.relative_to(ROOT).as_posix()} disagrees with git; "
                  f"re-run without --check", file=sys.stderr)
            return 1
        print(f"{OUT.relative_to(ROOT).as_posix()} matches the object database")
        return 0
    OUT.write_text(json.dumps(fresh, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} from commit "
          f"{fresh['registered_in_commit'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
