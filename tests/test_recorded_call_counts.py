"""The per-model call counts in SUBMISSION.md, recounted from the cassettes.

That table invites a judge to recount it in a clone. It was wrong by 36 when an
independent reader took the invitation: the row for the compiling model said
1,167 and the tracked cassettes hold 1,131. A number that asks to be checked and
then fails the check is worse than one that never asked.

So the recount is a test rather than an invitation. It reads every tracked
cassette, groups by the model recorded inside the request, and compares against
the table. Untracked cassettes are excluded on purpose: the claim is about what
ships, and a clone has only what ships.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "SUBMISSION.md"

#: `| `model-name` | 1,234 | what it was used for |`
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([\d,]+)\s*\|", re.M)


def _tracked_cassettes() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [ROOT / rel for rel in out.split("\0")
            if "/cassettes/" in rel and rel.endswith(".json")]


def _counted() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in _tracked_cassettes():
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        model = (d.get("request") or {}).get("model") or d.get("model")
        if model:
            counts[model] = counts.get(model, 0) + 1
    return counts


def _stated() -> dict[str, int]:
    text = SUBMISSION.read_text(encoding="utf-8")
    block = text[text.index("| model | recorded calls | used for |"):]
    block = block[:block.index("\n\n")]
    return {m: int(n.replace(",", "")) for m, n in ROW.findall(block)}


def test_the_table_is_present_and_names_models() -> None:
    stated = _stated()
    assert len(stated) >= 3, (
        f"the recorded-call table in SUBMISSION.md parsed to {stated}; its shape "
        "has changed and this recount is no longer reading it"
    )


def test_there_are_cassettes_to_count() -> None:
    assert len(_tracked_cassettes()) > 1000, (
        "fewer than a thousand tracked cassettes; the recount would pass on an "
        "empty set, which is the wrong kind of green"
    )


@pytest.mark.parametrize("model", sorted(_stated()))
def test_stated_call_count_matches_the_tracked_cassettes(model: str) -> None:
    stated, counted = _stated()[model], _counted().get(model, 0)
    assert stated == counted, (
        f"SUBMISSION.md says {stated:,} recorded calls for {model} and the "
        f"tracked cassettes hold {counted:,}. Correct the table; the files are "
        "the evidence and the table is the claim."
    )


def test_every_model_with_tracked_cassettes_is_declared() -> None:
    """A model in the tree and not in the table is an undisclosed model."""
    missing = sorted(set(_counted()) - set(_stated()))
    assert not missing, (
        f"{missing} have tracked cassettes and no row in SUBMISSION.md, so the "
        "submission calls a model it does not declare"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
