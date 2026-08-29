"""The gate is tested by running it, not by testing the function underneath it.

`tests/test_signoff.py` covers `signoff.enforce()`, the library call. That is not
the same claim. What SUBMISSION.md asserts is that `scripts/worklist.py` refuses
by exit code, and a reader checking that claim runs the script. A library test
passes even if the script forgets to call the library, or calls it and ignores
the result, or catches the exception and carries on.

So these tests invoke the script the way a person would and read the exit status.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: A committed run that carries compiled predicates and no signatures. Using a
#: fixture rather than the scored run keeps this test runnable on a clean clone,
#: before anything has been recorded, which is when a reader checking the claim
#: would run it. Pointing it at the scored run made all four tests skip, and a
#: skipped test backs no claim at all.
FIXTURE = ROOT / "tests" / "fixtures" / "gate_run"

pytestmark = pytest.mark.skipif(
    not (FIXTURE / "compiled" / "criteria_seed7.json").exists(),
    reason="the fixture run carries no compiled predicates")


@pytest.fixture
def unsigned_run(tmp_path):
    """A copy of the fixture run with any signature removed."""
    dest = tmp_path / "run"
    shutil.copytree(FIXTURE, dest)
    (dest / "signoffs.jsonl").unlink(missing_ok=True)
    return dest


def worklist(run: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/worklist.py", "--run", str(run), *extra],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace")


def test_unsigned_run_exits_three(unsigned_run, tmp_path):
    p = worklist(unsigned_run, "--out", str(tmp_path / "w.md"))
    assert p.returncode == 3, (
        f"expected exit 3 from an unsigned run, got {p.returncode}.\n"
        f"{p.stdout}\n{p.stderr}")
    assert not (tmp_path / "w.md").exists(), \
        "the gate refused but wrote the document anyway"


def test_refusal_names_the_command_that_clears_it(unsigned_run, tmp_path):
    out = worklist(unsigned_run, "--out", str(tmp_path / "w.md"))
    both = out.stdout + out.stderr
    assert "signoff.py" in both, \
        "a refusal that does not say how to clear it is a dead end"


def test_override_is_visible_in_the_document(unsigned_run, tmp_path):
    dest = tmp_path / "w.md"
    p = worklist(unsigned_run, "--allow-unsigned", "--out", str(dest))
    assert p.returncode == 0, f"{p.stdout}\n{p.stderr}"
    assert dest.exists(), "the override produced no document"
    head = dest.read_text(encoding="utf-8")[:2000]
    assert "NOT FOR USE" in head or "signed by" in head, (
        "the override left no mark in the artifact. A flag whose only trace is "
        "the shell history is a flag that reports approval nobody gave.")


def test_no_bulk_approval_exists():
    """The gate is only as strong as the absence of a way around it.

    The flags are parsed out of the `add_argument` calls rather than grepped for
    in the file. The first version of this test grepped, and failed on the
    docstring sentence that says there is no `--approve-all`: it flagged its own
    rule description as a violation of the rule.
    """
    import ast

    src = (ROOT / "scripts" / "signoff.py").read_text(encoding="utf-8")
    declared = set()
    for node in ast.walk(ast.parse(src)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    declared.add(arg.value)
    assert declared, "parsed no arguments; the parser, not the gate, is broken"
    for flag in ("--approve-all", "--yes", "--all", "--bulk", "--force"):
        assert flag not in declared, (
            f"{flag} is a declared option on signoff.py. A gate that can be "
            f"cleared without reading reports approval nobody gave.")
