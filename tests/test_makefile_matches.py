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
    # Two counts, two homes, because entry 46 split the gate: the engine tests
    # gate the run at step 2 and the whole suite runs at step 8, once the
    # artifacts it reads exist. Both are asserted, so moving one and forgetting
    # the other fails here rather than in front of a reader.
    eng = re.search(r"The engine gate runs\.\*\* The (\d+) semantic tests", doc)
    assert eng, "the step 2 sentence quoting the engine count has been reworded"
    tot = re.search(r"The full suite runs\*\*, all (\d+) tests", doc)
    assert tot, "the step 8 sentence quoting the total has been reworded"
    claimed_total, claimed_engine = int(tot.group(1)), int(eng.group(1))

    out = subprocess.run([_sys.executable, "-m", "pytest", "--collect-only", "-q"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    ids = [l for l in out.splitlines() if "::" in l]
    total = len(ids)
    # The second branch here was written "tests\test_engine.py", which is a tab
    # followed by est_engine.py, so it never matched anything. Normalising the
    # separator says what was meant and cannot be mistyped the same way.
    engine = sum(1 for l in ids
                 if l.replace(chr(92), "/").startswith("tests/test_engine.py"))
    assert claimed_total == total, (
        f"REPRODUCE.md says {claimed_total} tests, the suite collects {total}")
    assert claimed_engine == engine, (
        f"REPRODUCE.md says {claimed_engine} engine tests, test_engine.py has {engine}")
