"""The list of files this project ships.

    python scripts/manifest.py --write     regenerate MANIFEST.txt from git
    python scripts/manifest.py --check     fail if it has drifted

Several gates ask "what did the reader actually get" and answered it with `git
ls-files`. That is the right question and the wrong sole source, because a judge
who downloads the source archive has the files and no object database: the gates
raised, and `python run.py reproduce` failed with thirteen errors on a reader
doing exactly what the guide said.

Walking the directory instead is not the same question. A working tree carries
whatever the run just generated, and `.pytest_cache/` and the uncommitted cells
under `runs/` pushed one gate's byte total from 57 MB to 105 MB and made another
report a carriage return in a file that does not ship. So the answer is written
down once, from git, and travels inside the archive.

It lists itself, which is not a fixed point: the content is the set of names, and
adding a name changes the set exactly once.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.txt"


def from_git() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return sorted(n for n in out.split(chr(0)) if n)


def read() -> list[str]:
    if not MANIFEST.is_file():
        return []
    return [ln for ln in MANIFEST.read_text(encoding="utf-8").split("\n") if ln]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    names = from_git()
    if a.write:
        MANIFEST.write_text("\n".join(names) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote MANIFEST.txt, {len(names)} files")
        return 0

    have = read()
    if have == names:
        print(f"MANIFEST.txt matches git, {len(names)} files")
        return 0
    added = sorted(set(names) - set(have))
    gone = sorted(set(have) - set(names))
    print(f"MANIFEST.txt has drifted: {len(added)} not listed, {len(gone)} listed "
          f"and not shipped. Run `python scripts/manifest.py --write`.",
          file=sys.stderr)
    for n in (added + gone)[:10]:
        print(f"  {n}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
