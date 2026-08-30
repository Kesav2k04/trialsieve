"""The independence claim at the top of `evaluation/gold/plainview.py`, parsed.

That docstring says the module and everything that imports it must never reach
`trialsieve.evaluator`, `ir`, `units` or `logic`, and gives the reason: if gold
and the system under test shared an execution path, a defect in that path would
land on both sides of the comparison and be scored as agreement. A wrong window
boundary or an inverted unit factor would cancel, and the metric would be blind to
the failure modes this project exists to measure.

It was true and it was ungated, which is the state a claim is in just before it
stops being true. This walks the import graph transitively rather than reading the
first line of each file, because the leak that matters is the one two hops away.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "evaluation" / "gold"

#: The engine's execution path. Importing any of these into gold would put the
#: same code on both sides of the comparison.
FORBIDDEN = {"trialsieve.evaluator", "trialsieve.ir", "trialsieve.units",
             "trialsieve.logic"}


def _imports(path: Path) -> set[str]:
    """Every module name this file imports, absolute and relative alike."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)
    return found


def _resolve(name: str) -> Path | None:
    """A module name to a file inside this repository, or None if it is not ours."""
    rel = name.replace(".", "/")
    for base in (ROOT / "src", ROOT, ROOT / "evaluation"):
        for candidate in (base / f"{rel}.py", base / rel / "__init__.py"):
            if candidate.is_file():
                return candidate
    return None


def _reachable(start: Path) -> set[str]:
    """Every repository module reachable from `start`, following imports."""
    seen: set[str] = set()
    queue = [start]
    walked: set[Path] = set()
    while queue:
        path = queue.pop()
        if path in walked:
            continue
        walked.add(path)
        for name in _imports(path):
            seen.add(name)
            nxt = _resolve(name)
            if nxt is not None:
                queue.append(nxt)
    return seen


def test_the_gold_modules_exist_to_be_checked() -> None:
    """Without this, every assertion below passes against an empty directory."""
    files = sorted(GOLD.glob("*.py"))
    assert files, "evaluation/gold/ has no modules, so nothing was checked"
    assert (GOLD / "plainview.py").is_file(), "plainview.py is the module that claims this"


@pytest.mark.parametrize("path", sorted(GOLD.glob("*.py")), ids=lambda p: p.name)
def test_gold_never_reaches_the_engine(path: Path) -> None:
    reached = _reachable(path)
    leaked = sorted(n for n in reached
                    if any(n == f or n.startswith(f + ".") for f in FORBIDDEN))
    assert not leaked, (
        f"{path.name} reaches the engine through {leaked}. Gold and the system "
        f"under test would then share an execution path, and any defect in it "
        f"would be scored as agreement rather than caught.")


def test_the_walk_would_notice_a_leak_two_hops_away() -> None:
    """The check, run against files that do the thing it forbids.

    A resolver that returns None for everything makes every assertion above pass
    against any graph at all, which is the silent-empty failure this repository
    keeps finding in its own gates. So the plant is deliberately indirect: the
    probe imports a second module and only that one touches the engine. Seeing it
    requires `_resolve` to have actually found a file and followed it, which a
    direct import would not have proved.
    """
    hop = GOLD / "_leak_hop_delete_me.py"
    probe = GOLD / "_leak_probe_delete_me.py"
    hop.write_text("from trialsieve import evaluator\n", encoding="utf-8",
                   newline="\n")
    probe.write_text("from evaluation.gold import _leak_hop_delete_me\n",
                     encoding="utf-8", newline="\n")
    try:
        reached = _reachable(probe)
        assert any(n == "trialsieve.evaluator" or n.startswith("trialsieve.evaluator.")
                   for n in reached), (
            "the walk did not follow an import into a second file, so it cannot "
            "see an indirect leak and the assertions above prove nothing")
    finally:
        probe.unlink()
        hop.unlink()
