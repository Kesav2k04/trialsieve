"""The provenance rule has to move when the prompt moves and not before.

`results/RESULTS.md` says a run is invalid if the prompt changed after it. That
rule was written against the commit that last touched the file, which is a proxy,
and the proxy fired the first time a docstring in `grounder.py` was corrected: a
run that replays byte for byte from its cassettes was declared invalid because a
sentence about the code changed.

So the rule keys on a digest of the prompt text. These tests are the two halves of
that claim, and neither is worth much without the other: a digest that never moves
would pass the first and fail the second.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

AGENTS = ROOT / "src" / "trialsieve" / "agents"
PROMPT_FILES = sorted(p for p in AGENTS.glob("*.py")
                      if p.name not in ("__init__.py", "common.py"))


@pytest.fixture(scope="module")
def digest():
    from report import prompt_digest
    return prompt_digest


def test_there_are_prompt_files_to_check():
    """A control. Every assertion below passes over an empty list."""
    assert len(PROMPT_FILES) >= 4, (
        f"only {len(PROMPT_FILES)} prompt-carrying module(s) found in {AGENTS}")


@pytest.mark.parametrize("path", PROMPT_FILES, ids=[p.name for p in PROMPT_FILES])
def test_prose_does_not_move_the_digest(path, digest, tmp_path):
    """The defect this replaced.

    A comment, a docstring or a renamed local is not something the model reads.
    Rewriting all three has to leave the digest where it was, or the rule keeps
    voiding runs for prose.
    """
    src = path.read_text(encoding="utf-8")
    before = digest(path)

    edited = ('"""A completely different module docstring.\n\nWith a second '
              'paragraph that says nothing the model will ever see.\n"""\n'
              + re.sub(r"^\"\"\".*?\"\"\"\n", "", src, count=1, flags=re.S)
              + "\n# A trailing comment added after the run was scored.\n")
    assert edited != src, "the rewrite changed nothing, so this proves nothing"
    twin = tmp_path / path.name
    twin.write_text(edited, encoding="utf-8", newline="\n")

    assert digest(twin) == before, (
        f"editing prose in {path.name} moved the prompt digest, so the "
        f"provenance rule still invalidates a run for text no model reads")


@pytest.mark.parametrize("path", PROMPT_FILES, ids=[p.name for p in PROMPT_FILES])
def test_changing_a_prompt_moves_the_digest(path, digest, tmp_path):
    """The half that makes the other half mean something.

    Without it, a digest hard-coded to a constant satisfies the prose test above
    and notices nothing. This edits the first prompt constant in place, through
    the source segment `ast` reports for it, and requires the digest to move.
    """
    import ast

    src = path.read_text(encoding="utf-8")
    node = next((n for n in ast.parse(src).body
                 if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.Constant)
                 and isinstance(n.value.value, str)
                 and any(isinstance(t, ast.Name) and t.id.isupper()
                         for t in n.targets)), None)
    assert node is not None, f"{path.name} carries no prompt constant to hash"
    literal = ast.get_source_segment(src, node.value)
    assert literal, "could not read the constant back out of the source"

    edited = src.replace(literal, f"({literal} + ' one more instruction.')", 1)
    assert edited != src, "the edit changed nothing, so this proves nothing"
    twin = tmp_path / path.name
    twin.write_text(edited, encoding="utf-8", newline="\n")

    # A concatenation is no longer a bare Constant, so the digest must fall to
    # zero prompt constants for that name rather than silently keeping the old
    # value. Either way it has to differ from before.
    assert digest(twin) != digest(path), (
        f"changing a prompt constant in {path.name} left the digest unchanged, "
        f"so the provenance rule would not notice the edit it exists to catch")


def test_the_report_publishes_a_digest_per_prompt_file():
    """The digest is only a rule if it reaches the document that states the rule."""
    import json

    results = ROOT / "results" / "results.json"
    if not results.exists():
        pytest.skip("no scored run in this tree")
    blob = json.loads(results.read_text(encoding="utf-8"))
    digests = blob.get("prompt_text_sha256") or {}
    assert set(digests) == {p.name for p in PROMPT_FILES}, (
        f"the report publishes digests for {sorted(digests)}, the tree carries "
        f"{sorted(p.name for p in PROMPT_FILES)}")
    assert all(len(v) == 64 for v in digests.values()), (
        "a published digest is not a sha256")

    doc = (ROOT / "results" / "RESULTS.md").read_text(encoding="utf-8")
    for name, value in digests.items():
        assert value[:16] in doc, (
            f"the digest for {name} is in results.json and not in RESULTS.md, "
            f"which is the file that states the rule")
