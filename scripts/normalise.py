"""Strip carriage returns from tracked text files.

    python scripts/normalise.py

`.gitattributes` says `* text=auto eol=lf`, so git stores line feeds whatever the
working tree holds. That covers a fresh clone. It does not cover the tree on the
machine that recorded the run, where anything written by a Python process that did
not pin `newline=` on `write_text` lands as CRLF and then reads as modified
forever, which makes `results/environment.json` record "dirty" on a tree nobody
edited.

`tests/test_line_endings.py` is the gate. This is the fix, kept separate because a
test that repairs what it measures is a test that always passes.

Files modified in the last ninety seconds are skipped. A long recording run writes
cassettes continuously, and rewriting one mid-write would corrupt it. Run this
again after the run finishes; the gate will say whether anything is left.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".py", ".md", ".json", ".jsonl", ".yml", ".yaml", ".txt", ".cfg",
            ".toml", ".srt"}
QUIET_SECONDS = 90


def main() -> int:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    now = time.time()
    fixed, skipped = 0, []
    for name in out.split("\0"):
        if not name:
            continue
        p = ROOT / name
        if p.suffix.lower() not in SUFFIXES or not p.exists():
            continue
        raw = p.read_bytes()
        if b"\r" not in raw:
            continue
        if now - p.stat().st_mtime < QUIET_SECONDS:
            skipped.append(name)
            continue
        p.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        fixed += 1
    print(f"normalised {fixed} file(s)")
    if skipped:
        print(f"skipped {len(skipped)} being written right now: {skipped[:4]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
