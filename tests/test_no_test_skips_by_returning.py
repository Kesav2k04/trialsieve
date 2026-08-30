"""No test in this suite bails out with a bare `return`.

A test that hits a missing artifact and returns is reported as PASSED, having
checked nothing. Three files were converted to `pytest.skip` in one pass and two
were missed; the two that were missed guarded on `runs/tierA/cells/` and
`runs/tierA/compiled/`, both excluded by `.gitignore`, so they were vacuous on
every clone of this repository and green on every machine that had already run
the pipeline.

The fix is not to convert them again. It is to make the next one impossible to
add quietly, which is what this file is: one walk of the suite's own syntax tree.
The distinction it enforces is the only one that matters here, that a check which
could not run says so out loud rather than counting itself among the passes.
"""
from __future__ import annotations

import ast
from pathlib import Path

TESTS = Path(__file__).resolve().parent


def _bare_returns(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test_"):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is None:
                out.append(f"{path.name}:{node.lineno} in {fn.name}()")
    return out


def test_no_test_function_returns_early_instead_of_skipping() -> None:
    files = sorted(TESTS.glob("test_*.py"))
    assert len(files) > 20, (
        f"only {len(files)} test files were walked, so this checked almost "
        f"nothing; the glob is wrong or this is not the tests directory")
    found = [hit for f in files for hit in _bare_returns(f)]
    assert not found, (
        "these tests exit without checking anything and are counted as passes:\n  "
        + "\n  ".join(found)
        + "\n\nUse `pytest.skip(reason)` so a check that could not run says so.")


def test_this_walk_would_notice() -> None:
    """The positive control, because the whole file is one negative assertion."""
    src = "import pytest\ndef test_x():\n    if 1:\n        return\n    assert 1\n"
    tmp = TESTS / "_bare_return_probe.py"
    tmp.write_text(src, encoding="utf-8", newline="\n")
    try:
        assert _bare_returns(tmp) == ["_bare_return_probe.py:4 in test_x()"], (
            "the walk did not find a planted bare return, so its silence on the "
            "real suite means nothing")
    finally:
        tmp.unlink()
