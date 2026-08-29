"""A broader-only code must never sit where presence can settle a verdict.

`README.md` promises it plainly: a code the site uses more coarsely than the
criterion needs goes in a query's `broader_codes`, and "presence cannot settle
it. Absence still can." `docs/AGENT_DESIGN.md` restates it as a hard contract on
the compiler, and the emit prompt spells it out to the model.

Nothing checked it. `compiler.py` builds the emit validator's allow-list by
unioning `codes` with `broader_codes`, so a broader-only code emitted into the
`codes` slot is inside the allow-list and validates. The one invariant the design
calls its sharp edge was enforced by asking politely.

Two of the eight grounded criteria that produced a broader-only code then used it
as an exact one, and both also carry `absent_means=false`. Presence settles them
as MEETS and absence settles them as FAILS, so neither can ever answer
INDETERMINATE. One of the two is `NCT06983054-INC-01`, which is 358 of the 424
wrong exclusions in the scored run.

These tests hold three things: that the detector detects, that it does not fire
on a clean predicate, and that the committed run's violation set is exactly the
two named below. The last one is a ledger, not an exemption. If a recompile adds
a third, or silently fixes one, this fails and someone has to say which.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from grounding_audit import audit, promotions  # noqa: E402

#: The violations in the committed scored run, named so a change is visible.
KNOWN = {"NCT06983054-INC-01": ["44054006"],
         "NCT06717698-INC-07": ["44054006"]}


def _criterion(codes, broader, used):
    return {"criterion_id": "X-1", "compilable": True,
            "grounded": [{"concept": "c", "domain": "condition",
                          "status": "BROADER_ONLY" if not codes else "EXACT",
                          "codes": codes, "broader_codes": broader}],
            "expr": {"op": "exists", "query": {"domain": "condition",
                                               "codes": used}}}


def test_it_catches_a_promoted_broader_code():
    got = promotions(_criterion(codes=[], broader=["44054006"], used=["44054006"]))
    assert got == ["44054006"], (
        "a code the grounder returned as broader-only was used as an exact code "
        f"and the detector returned {got}")


def test_it_does_not_fire_when_the_code_is_where_it_belongs():
    """The negative control. A detector that always fires measures nothing."""
    assert promotions(_criterion(codes=["44054006"], broader=[],
                                 used=["44054006"])) == []
    assert promotions(_criterion(codes=["11111"], broader=["44054006"],
                                 used=["11111"])) == []


def test_a_code_that_is_both_exact_and_broader_is_not_a_violation():
    """Grounding can return the same code both ways for different concepts."""
    c = _criterion(codes=["44054006"], broader=["44054006"], used=["44054006"])
    assert promotions(c) == []


def test_the_committed_run_carries_exactly_the_known_violations():
    src = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"
    if not src.exists():
        return  # a checkout without a compiled run has nothing to audit

    res = audit(src)
    got = {r["criterion_id"]: r["promoted"] for r in res["violations"]}
    assert got == KNOWN, (
        f"the broader-code promotions in the committed run are {got}, and this "
        f"test records {KNOWN}. A new one means the compiler emitted a coarse "
        f"code where presence now settles a verdict; a missing one means it was "
        f"fixed, which changes published numbers and needs saying out loud.")

    # The half that makes it dangerous rather than merely wrong.
    for r in res["violations"]:
        assert "false" in r["absent_means"], (
            f"{r['criterion_id']} was recorded as a both-branches-commit case "
            f"and its absent_means is now {r['absent_means']}")


def test_the_audit_is_reachable_as_a_command():
    """A check nobody can run is a check nobody runs."""
    import subprocess
    out = subprocess.run([sys.executable, "scripts/grounding_audit.py",
                          "--run", "runs/tierA"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 3, (
        f"the audit exited {out.returncode}; with known violations present it "
        f"must exit non-zero so a pipeline cannot walk past it")
    assert "NCT06983054-INC-01" in out.stdout
