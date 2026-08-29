"""Every path a document points at must exist.

    python scripts/linkcheck.py

A README that links to a file nobody generated is the cheapest possible way to
look careless, and it is invisible to the author, who has the file locally or
remembers meaning to make it. It is the first thing a reader hits.

This is a script rather than a test on purpose. Several of the paths are produced
by the run itself, so a test in the gate would fail on a clean checkout before the
run that creates them, and a gate that fails when nothing is wrong gets muted.
`python run.py reproduce` calls this after the generating steps, which is the
moment the answer means something.

Three kinds of reference are checked and one is deliberately not:

* markdown links, `[text](path)`
* inline code that looks like a path, `` `docs/THING.md` `` or `` `scripts/x.py` ``
* the command in a fenced block, when its first token is a script in this tree

External URLs are not fetched. A link checker that hits the network fails on an
aeroplane and passes when a site is merely slow, so it measures connectivity and
reports it as correctness.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOCS = ["README.md", "SUBMISSION.md", "REPRODUCE.md"]
DOC_GLOBS = ["docs/*.md"]

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_PATH = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|md|json|jsonl|yml|gz|toml|cfg))`")
CMD = re.compile(r"^\s*python3?\s+([A-Za-z0-9_./-]+\.py)", re.M)

#: Paths that name a directory of generated output rather than one file, or that
#: are illustrative. Listed here so the exemption is visible instead of being a
#: silent hole in the pattern.
EXEMPT = {
    "results/published/",
    "runs/tierA/trajectories/",
    "data/vendor/",
    "tests/",
    # The sign-off ledger. The README and SUBMISSION.md point at it to say where
    # the fact lives rather than to assert the fact, and the whole point of the
    # gate is that no automated step creates this file. It is absent in an
    # unsigned checkout by design, so a link checker that failed on it would be
    # reporting the safety property as a defect. If a reviewer signs, it appears
    # and this line stops doing anything.
    "runs/tierA/signoffs.jsonl",
}


def targets(text: str) -> set[str]:
    out: set[str] = set()
    for m in MD_LINK.finditer(text):
        out.add(m.group(1))
    for m in CODE_PATH.finditer(text):
        out.add(m.group(1))
    for m in CMD.finditer(text):
        out.add(m.group(1))
    return out


def main() -> int:
    files = [ROOT / d for d in DOCS]
    for g in DOC_GLOBS:
        files.extend(sorted(ROOT.glob(g)))

    import subprocess
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                             capture_output=True, text=True,
                             check=True).stdout.split(chr(0))
    by_name = {n.rsplit("/", 1)[-1] for n in tracked if n}

    missing: list[str] = []
    checked = 0
    for f in files:
        if not f.exists():
            missing.append(f"{f.relative_to(ROOT).as_posix()} (the document itself)")
            continue
        text = f.read_text(encoding="utf-8")
        for t in sorted(targets(text)):
            if t.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if t in EXEMPT:
                continue
            base = t.split("#", 1)[0]
            if not base:
                continue
            checked += 1
            if (f.parent / base).exists() or (ROOT / base).exists():
                continue
            # A reference with no directory in it is a filename mentioned in
            # passing, `units.py` or `environment.json`, not a link. Those resolve
            # by basename anywhere in the tree. A reference that does carry a
            # directory is a claim about where the file is, and is checked as one.
            if "/" not in base and base in by_name:
                continue
            missing.append(f"{f.relative_to(ROOT).as_posix()} -> {t}")

    print(f"checked {checked} path reference(s) across {len(files)} document(s)")
    if missing:
        print(f"\n{len(missing)} point at something that is not there:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        return 1
    print("every path a document points at exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
