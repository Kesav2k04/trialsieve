"""Nothing this repository writes may carry a carriage return.

Why a whole test for a line ending. The reproduction claim rests on files being
byte-identical across machines, and the recording was made on Windows, where
`Path.write_text` turns every line feed into a carriage return plus line feed
unless told otherwise. That does not change a cassette's stored key, which hashes
the parsed request rather than the file. It changes three things that matter:

* the working tree is permanently dirty against the repository's `eol=lf` rule,
  so `results/environment.json` records "dirty" on a tree nobody edited, and a
  provenance field that is always set has stopped carrying information;
* a reader taking their own digest of a committed artifact gets a different
  number on Windows than on Linux, for a file whose content is identical;
* a byte comparison against `results/published/` fails for a reason that has
  nothing to do with the numbers, which is the worst kind of red.

Two tests, because either alone can pass while the problem is present. The first
catches the artifacts already written. The second catches the next call site
somebody adds.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = ("src", "scripts", "evaluation", "tests")

#: Extensions that are text and are generated or committed by this project.
#: Binary formats are excluded by extension rather than by sniffing, because a
#: gzip member legitimately contains 0x0d and a sniff would have to guess.
TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".yml", ".yaml", ".txt",
                 ".cfg", ".toml", ".srt"}


def _tracked() -> list[Path]:
    from _shipped import shipped_paths
    return shipped_paths()


def test_no_tracked_text_file_contains_a_carriage_return():
    offenders = []
    for p in _tracked():
        if p.suffix.lower() not in TEXT_SUFFIXES or not p.exists():
            continue
        if b"\r" in p.read_bytes():
            offenders.append(p.relative_to(ROOT).as_posix())
    assert not offenders, (
        f"{len(offenders)} tracked text file(s) contain a carriage return, so the "
        f"working tree disagrees with what git stores under eol=lf: "
        f"{offenders[:10]}")


def test_every_write_text_call_pins_its_newline():
    """The next call site, caught before it writes anything.

    A file scan alone would pass on a clean checkout and start failing only after
    someone ran a recording on Windows, which is the wrong moment to find out.
    """
    unpinned = []
    for d in CODE_DIRS:
        for f in sorted((ROOT / d).rglob("*.py")):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "write_text"
                        and "newline" not in {k.arg for k in node.keywords}):
                    unpinned.append(f"{f.relative_to(ROOT).as_posix()}:{node.lineno}")
    assert not unpinned, (
        "write_text without an explicit newline= writes CRLF on Windows: "
        + ", ".join(unpinned))


@pytest.mark.parametrize("name", ["*.gz", "*.png", "*.mp4", "*.zip"])
def test_binary_extensions_are_declared_binary(name):
    """A gzip member containing 0x0a would be corrupted by eol=lf normalisation."""
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert f"{name} binary" in attrs, f"{name} is not declared binary in .gitattributes"
