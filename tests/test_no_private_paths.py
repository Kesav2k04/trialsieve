"""No tracked file may carry a path through somebody's home directory.

A coding-agent transcript is obviously a shell session on a laptop, and the
exporter that wrote those redacted them. The other kind of artifact went
unchecked: the trajectories the system itself writes while running. Those record what a tool returned, and one of
the things a tool returned was an HTTP 502 whose message quoted the absolute path
of the CLI binary that had just died. Eighty-two copies of it, across fifty-seven
files, none of which anybody would have thought to read.

Rule 08 of the competition says to keep credentials and private information
outside the submission, and a home directory names a person. So this scans every
tracked text file rather than a directory somebody remembered to list, which is
the only version of this check that would have caught the case that happened.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: A path through a home directory, in any of the forms a JSON-escaped Windows
#: path can take: one backslash raw, two through one round of JSON escaping, four
#: through two. The literal user directory itself is the thing being looked for,
#: not the drive letter and not the tool that failed.
PATTERNS = [
    ("a Windows home directory", re.compile(r"[A-Za-z]:\\+Users\\+[A-Za-z0-9]", re.I)),
    ("a POSIX home directory", re.compile(r"/(?:home|Users)/[A-Za-z0-9][A-Za-z0-9._-]*")),
]

#: Files that name a home directory on purpose. Each one is here with a reason,
#: and the list is short so that adding to it is a decision rather than a habit.
ALLOWED = {
    # A test for how a path is redacted has to contain a path to redact.
    "tests/test_no_private_paths.py",
}


def _tracked_text_files() -> list[Path]:
    from _shipped import shipped
    files = []
    for name in shipped():
        name = name.strip()
        if not name or name in ALLOWED:
            continue
        p = ROOT / name
        if not p.is_file():
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".mp4", ".mp3", ".wav",
                                ".gz", ".zip", ".ico", ".woff", ".woff2"}:
            continue
        files.append(p)
    return files


def test_the_repository_has_tracked_files():
    """A positive control. Every assertion below passes on an empty list."""
    files = _tracked_text_files()
    assert len(files) > 100, f"only {len(files)} tracked text files found"


@pytest.mark.parametrize("name,pattern", PATTERNS, ids=[n for n, _ in PATTERNS])
def test_no_home_directory_in_any_tracked_file(name, pattern):
    hits = []
    for path in _tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = pattern.search(line)
            if m:
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{i}: {m.group(0)}")
    assert not hits, (
        f"{name} appears in {len(hits)} place(s), first few: {hits[:5]}. "
        f"Run the redaction rather than adding the file to ALLOWED.")


def test_the_scan_can_fail():
    """The control that matters.

    The scan above passes just as well against a pattern that matches nothing.
    This plants each shape in a string and requires the pattern to find it, so a
    regex broken by an editor is caught here rather than by a judge.
    """
    windows = "C:" + ("\\" * 4) + "Users" + ("\\" * 4) + "someone" + ("\\" * 4) + "x"
    posix = "/" + "home" + "/" + "someone" + "/x"
    assert PATTERNS[0][1].search(windows), "the Windows pattern no longer matches"
    assert PATTERNS[1][1].search(posix), "the POSIX pattern no longer matches"
    assert not PATTERNS[0][1].search("C:" + ("\\" * 4) + "Users" + ("\\" * 4) + "...")


def test_the_runner_does_not_echo_the_interpreters_absolute_path():
    """Where the last leak came from, closed at the source rather than the scan.

    `run.py` prints every sub-command before running it, and it invokes them with
    `sys.executable`, which is absolute. On this machine that path sits under a
    home directory, so a captured transcript carried a username on every command
    line. The scan above found it, which is the scan working; this requires the
    runner not to write it in the first place, because a transcript is what a
    reader is invited to paste into a bug report.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("_run_under_test", ROOT / "run.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    line = mod.shown([mod.PY, "scripts/report.py", "--run", "runs/tierA"])
    assert line.startswith("python "), (
        f"the interpreter is still shown as {line.split()[0]!r}; a reader cannot "
        f"retype that and it carries whatever directory it was installed into")
    assert "scripts/report.py --run runs/tierA" in line, (
        "everything after the interpreter has to stay verbatim, or the echo is "
        "no longer the command that ran")
    for _name, pattern in PATTERNS:
        assert not pattern.search(line), f"{_name} survived in the echoed command"
