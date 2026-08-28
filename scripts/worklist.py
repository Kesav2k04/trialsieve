"""Produce the document a coordinator opens.

    python scripts/worklist.py --run runs/tierA --trial NCT06983054

This is the only output that is meant for a person rather than for a scorer, and
it is the only step gated on human sign-off. An unsigned predicate stops it, with
a message naming what to run. That refusal is the feature.

    python scripts/signoff.py --run runs/tierA --list

Everything upstream of this has been about being able to say "the record does not
say" without losing the thread. This is where that pays: the ruled-out list is
short and every line on it carries a dated resource, and the review list is
ordered so the coordinator's next forty minutes go where the fewest questions are
left.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve import worklist  # noqa: E402
from trialsieve.chart import load_panel  # noqa: E402
from trialsieve.signoff import NotSignedOff, enforce, load  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--trial", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--panel", default="data/vendor/panel.jsonl.gz")
    ap.add_argument("--out", default="")
    ap.add_argument("--unit-policy", default="code_authoritative")
    ap.add_argument("--max-listed", type=int, default=20)
    ap.add_argument("--allow-unsigned", action="store_true",
                    help="produce the document without human sign-off. Marks every "
                         "page as not for use and is refused for anything but a "
                         "demonstration of the gate.")
    a = ap.parse_args()

    run = Path(a.run)
    src = run / "compiled" / f"criteria_seed{a.seed}.json"
    if not src.exists():
        print(f"no compiled predicates at {src}", file=sys.stderr)
        return 2
    blob = json.loads(src.read_text(encoding="utf-8"))
    compiled = blob["criteria"]
    if a.trial:
        compiled = [c for c in compiled if c.get("nct_id") == a.trial]
        if not compiled:
            print(f"no criteria for {a.trial} in {src}", file=sys.stderr)
            return 2

    signoffs = load(run / "signoffs.jsonl")
    reviewer = ""
    try:
        compiled = enforce(compiled, signoffs)
        signers = {s.reviewer for s in signoffs.values()}
        roles = {s.reviewer_role for s in signoffs.values()}
        reviewer = ", ".join(sorted(signers)) + (f" ({', '.join(sorted(roles))})"
                                                 if roles else "")
    except NotSignedOff as exc:
        if not a.allow_unsigned:
            print(f"\nREFUSED.\n\n{exc}\n", file=sys.stderr)
            return 3
        print(f"WARNING, running unsigned: {exc}\n", file=sys.stderr)
        reviewer = ""

    trials = json.loads((ROOT / "data" / "vendor" / "trials_index.json")
                        .read_text(encoding="utf-8"))["trials"]
    nct = a.trial or (compiled[0].get("nct_id") if compiled else "")
    trial = next((t for t in trials if t["nct_id"] == nct), {"nct_id": nct, "title": ""})

    panel = load_panel(a.panel)
    wl = worklist.build(compiled, panel, trial, unit_policy=a.unit_policy)
    md = worklist.render_markdown(wl, generated=dt.date.today().isoformat(),
                                  reviewer=reviewer, max_listed=a.max_listed)

    out = Path(a.out) if a.out else run / f"worklist_{nct}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8", newline="\n")
    row = worklist.summary_row(wl)
    print(json.dumps(row, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
