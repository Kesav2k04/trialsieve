"""Criteria from the five development trials, split mechanically.

No gold labels here and none coming. This set exists so prompts can be changed
while looking at something other than the answer sheet, per `docs/DEV_SPLIT.md`.

The split is deliberately crude: bullet lines, with a section tracker for the
inclusion and exclusion headings. Registry text runs a criterion across several
bullets often enough that a tidier splitter would be inventing structure the
sponsor did not write, and the compiler has to survive the messy version anyway.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEV_TRIALS = ["NCT06338553", "NCT07065383", "NCT07588256", "NCT06578078", "NCT06998862"]

_BULLET = re.compile(r"^\s*[*\-•]\s+(.*)$")
_INC = re.compile(r"inclusion", re.I)
_EXC = re.compile(r"exclusion", re.I)


def _clean(s: str) -> str:
    s = s.replace("\\<", "<").replace("\\>", ">").replace("≥", ">=").replace("≤", "<=")
    return re.sub(r"\s+", " ", s).strip(" .;")


def _guess_category(text: str) -> str:
    t = text.lower()
    if re.search(r"\bage\b|years old|\byears\b", t) and len(t) < 60:
        return "demographic"
    if re.search(r"hba1c|egfr|creatinin|bmi|glucose|alt\b|ast\b|ldl|albumin|mg/dl|mmol", t):
        return "lab"
    if re.search(r"metformin|insulin|inhibitor|agonist|therapy|treatment|medication|drug", t):
        return "medication"
    if re.search(r"pregnan|consent|willing|able to|participat|study", t):
        return "administrative"
    return "diagnosis"


def load(trial_dir: Path | None = None) -> list[dict]:
    d = trial_dir or (ROOT / "data" / "vendor" / "trials")
    out: list[dict] = []
    for nct in DEV_TRIALS:
        blob = json.loads((d / f"{nct}.json").read_text(encoding="utf-8"))
        text = blob["protocolSection"]["eligibilityModule"]["eligibilityCriteria"]
        kind = "inclusion"
        n = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            if _EXC.search(line) and len(line) < 60:
                kind = "exclusion"
                continue
            if _INC.search(line) and len(line) < 60:
                kind = "inclusion"
                continue
            m = _BULLET.match(line)
            if not m:
                continue
            body = _clean(m.group(1))
            if len(body) < 8:
                continue
            n += 1
            out.append({
                "criterion_id": f"{nct}-{'INC' if kind == 'inclusion' else 'EXC'}-{n:02d}",
                "nct_id": nct,
                "kind": kind,
                "category": _guess_category(body),
                "source_text": body,
            })
    return out


CRITERIA = load()


def sample(n: int = 30, seed: int = 11) -> list[dict]:
    """A fixed subset, because a full development pass costs an hour of inference.

    Seeded and sorted so the same n criteria come back every time. Changing n
    changes which criteria are in the set, so the changelog records n once and
    keeps it.
    """
    import random
    rng = random.Random(seed)
    picked = rng.sample(CRITERIA, min(n, len(CRITERIA)))
    return sorted(picked, key=lambda c: c["criterion_id"])


if __name__ == "__main__":
    from collections import Counter
    print(f"{len(CRITERIA)} development criteria")
    print(Counter(c["nct_id"] for c in CRITERIA))
    print(Counter(c["kind"] for c in CRITERIA))
    print(Counter(c["category"] for c in CRITERIA))
    for c in CRITERIA[:8]:
        print(f"  {c['criterion_id']:22s} {c['category']:14s} {c['source_text'][:80]}")
