"""The wrapper must not offer fewer doors than the thing it wraps.

`REPRODUCE.md` says the Makefile "only forwards to run.py". A reader who prefers
`make` should be able to reach every target, and a target that exists in one place
and not the other is a small lie in a document about reproducibility.

This is a two-line test that would have caught four missing targets.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


#: `run.py` names its handler `t_live_smoke` and the CLI and the Makefile both
#: spell it `live-smoke`. Comparing the two sets without normalising reports a
#: difference that is only punctuation.
def norm(name: str) -> str:
    return name.replace("-", "_")


def run_py_targets() -> set[str]:
    src = (ROOT / "run.py").read_text(encoding="utf-8")
    return {norm(m.group(1)) for m in re.finditer(r"^def t_(\w+)\(", src, re.M)}


def makefile_targets() -> set[str]:
    src = (ROOT / "Makefile").read_text(encoding="utf-8")
    return {norm(m.group(1)) for m in re.finditer(r"^(\w[\w-]*):", src, re.M)} - {"help"}


def test_the_makefile_forwards_every_target():
    missing = run_py_targets() - makefile_targets()
    assert not missing, (
        f"run.py has target(s) {sorted(missing)} that `make` cannot reach. "
        f"REPRODUCE.md says the Makefile only forwards to run.py.")


def test_the_makefile_invents_nothing():
    extra = makefile_targets() - run_py_targets()
    assert not extra, (
        f"the Makefile offers {sorted(extra)}, which run.py does not implement")


def test_every_makefile_rule_calls_run_py():
    """A rule that does its own work is a second implementation to keep in step."""
    src = (ROOT / "Makefile").read_text(encoding="utf-8")
    for line in src.splitlines():
        if line.startswith("\t") and line.strip() and not line.strip().startswith("#"):
            assert "run.py" in line, f"rule body does not forward to run.py: {line.strip()}"


def test_reproduce_guide_quotes_the_real_test_count():
    """A count in prose drifts silently. `REPRODUCE.md` said 187 while the suite
    collected 203, which is the harmless version of a claim nobody rechecks and
    the same shape as the harmful ones. The number is asserted here so that
    adding a test either updates the document or fails the gate."""
    import re
    import subprocess
    import sys as _sys

    doc = (ROOT / "REPRODUCE.md").read_text(encoding="utf-8")
    m = re.search(r"The engine gate runs\.\*\* (\d+) tests, of which (\d+) are semantic", doc)
    assert m, "the sentence that quotes the counts has been reworded; update this test"
    claimed_total, claimed_engine = int(m.group(1)), int(m.group(2))

    out = subprocess.run([_sys.executable, "-m", "pytest", "--collect-only", "-q"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    ids = [l for l in out.splitlines() if "::" in l]
    total = len(ids)
    engine = sum(1 for l in ids if l.startswith("tests/test_engine.py")
                 or l.startswith("tests\test_engine.py"))
    assert claimed_total == total, (
        f"REPRODUCE.md says {claimed_total} tests, the suite collects {total}")
    assert claimed_engine == engine, (
        f"REPRODUCE.md says {claimed_engine} engine tests, test_engine.py has {engine}")
