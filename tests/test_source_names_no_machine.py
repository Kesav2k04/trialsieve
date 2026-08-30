"""No shipped script hardcodes a path on the machine that wrote it.

`tests/test_generated_files_name_no_machine.py` covers files a script writes. It
does not cover the scripts. Four committed files in the video build opened with a
drive-rooted assignment of the repository root, so a clone anywhere else could not
run them, and two of them named a directory belonging to an entirely different
project, which published the author's disk layout alongside the code.

Scoped to shipped code. `tests/` is excluded on purpose: a test that checks how a
path is redacted has to contain a path to redact, and the version of this file that
scanned itself flagged its own fixture.

Read with `ast`, not with a regex over the text, so a path inside a comment or a
docstring explaining this rule is not itself a violation.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Directories whose Python is shipped and run by somebody else.
SHIPPED = ("scripts/", "src/", "evaluation/", "run.py")

#: A Windows drive-rooted path, or a POSIX home directory.
# Two backslashes in the pattern source, so the class holds one. A single
# one escapes the slash beside it and the class becomes "/" alone, which
# matched no Windows path and made the control the only thing that failed.
ABSOLUTE = re.compile("^(?:[A-Za-z]:[" + chr(92) * 2 + "/]|/(?:home|Users)/)")


def _tracked() -> list[Path]:
    # Via the shared helper, which falls back to MANIFEST.txt where there is no
    # object database. This used to skip instead, so in the source archive, the
    # only form most readers will hold, the gate reported a pass having read
    # nothing.
    from _shipped import shipped
    return [ROOT / n for n in shipped("*.py")
            if any(n.startswith(d) for d in SHIPPED)]


def _absolute_literals(path: Path) -> list[str]:
    try:
        where = path.relative_to(ROOT).as_posix()
    except ValueError:
        where = path.name
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if not ABSOLUTE.match(node.value):
            continue
        # An elided path is the redaction table's replacement, not a real
        # location. `scripts/capture.py` rewrites a home directory to one, which
        # is the sanitiser working rather than a machine name shipping.
        if "..." in node.value:
            continue
        out.append(f"{where}:{node.lineno} {node.value[:60]!r}")
    return out


def test_no_shipped_script_names_an_absolute_path() -> None:
    files = _tracked()
    assert len(files) > 15, (
        f"only {len(files)} shipped scripts were walked, so this checked almost "
        f"nothing; SHIPPED no longer matches the tree")
    found = [hit for f in files for hit in _absolute_literals(f)]
    assert not found, (
        "these run only on the machine that wrote them:\n  " + "\n  ".join(found)
        + "\n\nDerive the path from __file__, or read it from the environment.")


def test_the_walk_would_notice(tmp_path) -> None:
    """The control. Every assertion above is a negative."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        # Assembled rather than written out. tests/test_no_private_paths.py
        # greps every tracked file for a home directory, correctly, and the
        # first version of this control put one in the source to prove that a
        # comment is not a violation. Two gates, both right, one file.
        "# a comment naming " + chr(67) + ":/" + "Users" + "/someone/x is "
        "not a violation" + chr(10) +
        "P = " + repr("D:" + chr(92) + "somewhere" + chr(92) + "else") + "\n",
        encoding="utf-8", newline="\n")
    hits = _absolute_literals(probe)
    assert len(hits) == 1, (
        f"expected exactly the assignment and not the comment, got {hits}")
