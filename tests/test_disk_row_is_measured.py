"""The disk row in REPRODUCE.md, recomputed from what is tracked.

That row tells a reader to measure it themselves with `git ls-tree -r -l HEAD`,
and by its own admission it has already been wrong three times. A figure that
invites a recount has to survive one, so the recount is a test.

What is checked is the headline MB figure against the decimal reading of the
measured byte total, plus the fact that the two plausible readings of that total
still differ. The row names its unit because the raw command prints bytes and a
reader dividing by 1024 squared lands four lower, which reads as a fourth error
in a row that has already had three.

The exact byte total is deliberately not asserted here, and not printed in the
document either. It would be a fixed point: the figure lives inside REPRODUCE.md,
REPRODUCE.md is tracked, and writing the figure changes the total it reports. The
rounded MB figure has no such problem, because a few kilobytes of prose cannot
move it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPRODUCE = ROOT / "REPRODUCE.md"

#: `| Disk | **85 MB of tracked files, ...`
HEADLINE = re.compile(r"\*\*(\d+) MB of tracked files")


def _tracked_bytes() -> int:
    """Blob sizes from git, or the sizes on disk when there is no git.

    The two agree here because a separate gate requires every text file to be
    stored with LF, so nothing gains a byte on checkout.
    """
    from _shipped import has_git, shipped_paths
    if has_git():
        out = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        return sum(int(line.split()[3]) for line in out.splitlines() if line.strip())
    return sum(p.stat().st_size for p in shipped_paths() if p.is_file())


def test_the_disk_row_matches_what_is_tracked() -> None:
    text = REPRODUCE.read_text(encoding="utf-8")
    m = HEADLINE.search(text)
    assert m, ("REPRODUCE.md no longer opens the disk row with an MB figure, so "
               "this test is checking nothing. Find the row and re-anchor it.")
    quoted = int(m.group(1))
    measured = _tracked_bytes()
    decimal = round(measured / 1_000_000)
    binary = round(measured / 1_048_576)
    assert quoted == decimal, (
        f"the disk row says {quoted} MB and `git ls-tree -r -l HEAD` sums to "
        f"{measured:,} bytes, which is {decimal} MB decimal and {binary} MiB. "
        f"The row states it is decimal, so it should say {decimal}. Something was "
        f"added, removed or re-rendered since the row was written.")


def test_the_two_readings_still_differ() -> None:
    """The unit note exists because the readings disagree. Check they still do.

    If the repository ever shrank to where decimal MB and MiB round the same,
    the sentence warning a reader about the gap would be describing a gap that
    is not there, which is its own small lie.
    """
    measured = _tracked_bytes()
    decimal, binary = round(measured / 1_000_000), round(measured / 1_048_576)
    assert decimal != binary, (
        f"{measured:,} bytes reads as {decimal} either way, so the sentence in "
        f"REPRODUCE.md about the two readings differing is no longer true")
    assert "decimal MB" in REPRODUCE.read_text(encoding="utf-8"), (
        "the disk row no longer names its unit, so a reader measuring in MiB "
        "has nothing telling them why they got a different number")
