"""The probe's published tally, recounted from the trajectories it shipped.

`docs/CRITIC_PROBE.md` scores one run of six predicates and reproduces exactly from
the recorded cassettes. The tree also carries the logs of an earlier, wider probe
whose numbers were never published, and one of those is a miss in `absence`, the
one class this critic is weak in. A reviewer counted the files, found five absence
probes under a table saying four, and read it as a denominator chosen to flatter.
It was not, and the document gave them no way to tell.

The document now prints both tallies, wider one first. This recounts the wider one
from the files, because a figure whose whole purpose is to be the less flattering
of two is the figure most likely to be quietly dropped when the generator is next
edited.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "docs" / "CRITIC_PROBE.md"
TRAJ = ROOT / "runs" / "tierA" / "trajectories" / "critic_probe"
SCORED = ROOT / "results" / "critic_probe.json"


def _recount() -> dict[str, list[int]]:
    """planted and right, per defect class, over every probe trajectory."""
    tally: dict[str, list[int]] = {}
    for f in sorted(TRAJ.glob("*.jsonl")):
        crit, _, defect = f.stem.partition("--")
        finals = [e for e in (json.loads(x) for x in
                              f.read_text(encoding="utf-8").split("\n") if x.strip())
                  if e.get("event") == "final"]
        if not finals:
            continue
        n = finals[-1].get("n_findings", 0)
        right = (n == 0) if defect == "control" else (n >= 1)
        row = tally.setdefault(defect, [0, 0])
        row[0] += 1
        row[1] += int(right)
    return tally


def test_the_wider_tally_matches_the_files() -> None:
    if not TRAJ.is_dir() or not PROBE.is_file():
        pytest.skip("no probe trajectories in this checkout")
    tally = _recount()
    text = PROBE.read_text(encoding="utf-8")
    # The generator aligns its tables, so the header arrives padded. Split on the
    # column names rather than on an exact string, which is the difference between
    # a check and a check that passes for the wrong reason.
    header = re.search(r"\|\s*defect\s*\|\s*planted, every probe\s*\|\s*caught\s*\|",
                       text)
    section = [text[:header.start()], text[header.end():]] if header else [text]
    assert len(section) == 2, (
        "docs/CRITIC_PROBE.md no longer prints the tally over every probe in the "
        "tree. That table is the less flattering of the two the document carries, "
        "so removing it needs to be a decision rather than a side effect.")
    body = section[1].split("\n\n")[0]
    printed = {m.group(1): [int(m.group(2)), int(m.group(3))]
               for m in re.finditer(r"\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", body)}
    for defect, counts in printed.items():
        assert tally.get(defect) == counts, (
            f"the document says {defect} is {counts[1]} of {counts[0]} over every "
            f"probe, and recounting the trajectories gives {tally.get(defect)}")
    assert printed, "the wider table parsed to nothing, so this checked nothing"


def test_the_scored_run_is_a_subset_of_what_shipped() -> None:
    """Every predicate the table scores has its log in the tree. The reverse does
    not hold, which is the whole point of printing both."""
    if not SCORED.is_file() or not TRAJ.is_dir():
        pytest.skip("no probe results in this checkout")
    scored = {r["criterion_id"] for r in json.loads(
        SCORED.read_text(encoding="utf-8"))["rows"]}
    on_disk = {f.stem.partition("--")[0] for f in TRAJ.glob("*.jsonl")}
    missing = sorted(scored - on_disk)
    assert not missing, (
        f"{len(missing)} predicate(s) are scored in results/critic_probe.json with "
        f"no trajectory in the tree: {missing[:5]}")


def test_the_weakest_class_is_reported_at_its_worse_rate() -> None:
    """The document quotes the scored run's absence rate in its headline sentence.
    It has to quote the wider one beside it, because that is the rate a reader
    counting files will compute."""
    if not TRAJ.is_dir() or not PROBE.is_file():
        pytest.skip("no probe trajectories in this checkout")
    absence = _recount().get("absence")
    if not absence:
        pytest.skip("no absence probes in this checkout")
    text = PROBE.read_text(encoding="utf-8")
    assert f"{absence[1]} of {absence[0]} counting every probe" in text, (
        f"the absence class is {absence[1]} of {absence[0]} across every probe in "
        f"the tree, and the document does not say so beside the scored run's rate")
