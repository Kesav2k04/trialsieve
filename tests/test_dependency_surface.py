"""The dependency lock, and the check that keeps `dependencies = []` honest.

`run.py reproduce` promises a judge can reach every published number from a
clean checkout with no install step. That promise rests on one property: nothing
the reproduction path imports comes from outside the standard library. The
property is easy to state and easy to break by accident, so it is parsed rather
than asserted in prose, and the parser itself is given something to find.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lockfile  # noqa: E402

#: Written out rather than escaped inline. `tests/test_line_endings.py` requires
#: every `write_text` in this repository to pin its newline, because the default
#: turns LF into CRLF on Windows and silently changes the digest of a file two
#: other checks compare byte for byte.
LF = chr(10)


def test_reproduction_path_is_standard_library_only():
    """The claim itself, over the real tree."""
    assert lockfile.offenders_in(lockfile._module_files()) == []


def test_the_check_can_fail(tmp_path):
    """A planted third-party import, which the check has to catch.

    Without this the previous test passes just as well when the walker is broken
    and returns nothing, which is the shape of every silent-empty failure in this
    project's changelog.
    """
    planted = tmp_path / "planted.py"
    planted.write_text("import numpy" + LF + "from requests import get" + LF,
                       encoding="utf-8", newline=LF)
    found = lockfile.offenders_in([planted])
    assert sorted(n for _, n in found) == ["numpy", "requests"]


def test_local_modules_are_not_reported_as_third_party(tmp_path):
    """The negative control.

    `scripts/report.py` imports `score` and `scripts/run_arms.py` imports
    `plainview`. Both are this project's own files, imported bare because their
    directory is placed on `sys.path` at runtime. The first version of this check
    reported all three as third-party dependencies.
    """
    local = lockfile.local_names()
    assert {"score", "plainview", "criteria_set"} <= local
    planted = tmp_path / "planted.py"
    planted.write_text("import score" + LF + "import json" + LF,
                       encoding="utf-8", newline=LF)
    assert lockfile.offenders_in([planted]) == []


def test_lock_covers_every_declared_optional_group():
    """Whatever pyproject declares has to appear in the lock, or be named absent."""
    lock = ROOT / "requirements-lock.txt"
    assert lock.exists(), "requirements-lock.txt is missing; run scripts/lockfile.py --write"
    text = lock.read_text(encoding="utf-8")
    for group in lockfile._roots():
        assert f"# --- {group}:" in text, f"group {group} is declared but not locked"


def test_lock_pins_exact_versions():
    """No ranges. A range is not a lock."""
    lock = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    pins = [ln for ln in lock.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]
    assert pins, "the lock has no pins in it"
    for line in pins:
        assert "==" in line, f"not an exact pin: {line!r}"
        for loose in (">=", "<=", "~=", ">", "<", "*"):
            assert loose not in line.replace("==", ""), f"not an exact pin: {line!r}"


def test_lock_records_the_interpreter():
    """A pinned package set on an unnamed interpreter is half a lock."""
    lock = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    assert lockfile._locked_python(), "the lock does not name the python it was written on"
    assert "cpython" in lock.lower()
