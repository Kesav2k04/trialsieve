"""A broader-only code must never sit where presence can settle a verdict.

`README.md` promises it plainly: a code the site uses more coarsely than the
criterion needs goes in a query's `broader_codes`, and "presence cannot settle
it. Absence still can." `docs/AGENT_DESIGN.md` restates it as a hard contract on
the compiler, and the emit prompt spells it out to the model.

For one run nothing checked it. `compiler.py` built the emit validator's
allow-list by unioning `codes` with `broader_codes`, and a set cannot say which
slot a code arrived in, so a broader-only code emitted into `codes` was inside
the allow-list and validated. The one invariant the design calls its sharp edge
was enforced by asking the model politely.

Two of the eight grounded criteria that produced a broader-only code then used it
as an exact one, and both carried `absent_means=false`. Presence settled them as
MEETS and absence as FAILS, so neither could ever answer INDETERMINATE. One of
the two was `NCT06983054-INC-01`, which was 358 of the 424 wrong exclusions in
the scored run.

`compiler.py` now builds two allow-lists and rejects an emission that puts a
broader-only code in `codes`, naming the code and telling the model where it
belongs. The committed run carries no violations, and `KNOWN` below is empty
rather than deleted: it is a ledger, so a recompile that reintroduces one fails
here and someone has to say which.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from grounding_audit import audit, promotions  # noqa: E402

#: The violations in the committed scored run, named so a change is visible.
#: Empty since the allow-list became slot-aware. Kept as a ledger rather than
#: removed, because a test that only asserts "none" reads the same whether the
#: audit works or returns nothing at all.
KNOWN: dict[str, list[str]] = {}


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
        f"code where presence now settles a verdict, which changes published "
        f"numbers and needs saying out loud.")

    # The audit has to have looked at something. An empty violation list is the
    # same output whether the run is clean or the reader silently read nothing,
    # which is the failure shape this project has hit three times.
    assert res["n_criteria_with_broader_codes"] > 0, (
        "no criterion in the committed run grounded a broader-only code, so a "
        "clean result here proves nothing about the check")


def test_the_audit_is_reachable_as_a_command():
    """A check nobody can run is a check nobody runs."""
    import subprocess
    out = subprocess.run([sys.executable, "scripts/grounding_audit.py",
                          "--run", "runs/tierA"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, (
        f"the audit exited {out.returncode} on a run this test expects to be "
        f"clean. stdout: {out.stdout.strip()!r}")
    # The exit code is load-bearing in the other direction too: a pipeline must
    # not be able to walk past a violation. The detector itself is covered by
    # `test_it_catches_a_promoted_broader_code`; this covers the plumbing.
    assert "broader-only" in out.stdout
