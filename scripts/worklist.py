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
# Importable as a module, not only runnable as a script: the tests import these.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _md_tables import align as align_tables

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
    ap.add_argument("--operating-point", type=int, default=None,
                    help="render only the criteria the published operating curve"
                         " keeps at this false-exclusion budget")
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

    # Firing every compiled predicate is a measurement configuration, not a
    # product one. It includes the criterion whose closed-world `absent_means`
    # rules out 358 patients on a silent record, and the sample worklist that
    # shipped with this repository ruled out 385 of 385 and left a coordinator
    # nothing to work. A deployment picks an operating point. This one is the
    # zero-false-exclusion row of the published curve, and the document says
    # which criteria it kept and that the subset was chosen in sample.
    if a.operating_point is not None:
        rp = ROOT / "results" / "results.json"
        if not rp.exists():
            print(f"no {rp}. Run scripts/report.py first.", file=sys.stderr)
            return 2
        res = json.loads(rp.read_text(encoding="utf-8"))
        grp = res.get("groups", {}).get(f"k0_seed{a.seed}", {})
        rows = grp.get("operating_curve_TS") or []
        row = next((r for r in rows
                    if r["false_exclusion_budget"] == a.operating_point), None)
        if row is None or not row.get("criteria"):
            print(f"no operating-curve row at budget {a.operating_point} with a "
                  f"named criterion set in {rp}", file=sys.stderr)
            return 2
        keep = set(row["criteria"])
        compiled = [c for c in compiled if c.get("criterion_id") in keep]
        if not compiled:
            print(f"the operating point at budget {a.operating_point} keeps no "
                  f"criterion from seed {a.seed}", file=sys.stderr)
            return 2
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

    if a.operating_point is not None:
        mine = wl.get("criteria_used") or sorted(c["criterion_id"] for c in compiled)
        note = [
            "",
            f"## Operating point: {a.operating_point} tolerated false exclusions",
            "",
            f"This worklist runs {len(mine)} of the trial's compiled criteria, not all of "
            f"them: " + ", ".join(f"`{m}`" for m in mine) + ". They are the set the "
            f"published operating curve keeps at a budget of {a.operating_point} false "
            f"exclusions.",
            "",
            "Two things a reader should hold against this. The subset was chosen by "
            "counting each criterion's false exclusions on the same patients it is then "
            "applied to, so it reports that a clean subset existed rather than that it "
            "could have been picked in advance; `operating_curve_cv` in "
            "`results/RESULTS.md` is the cross-fitted answer to that. And running every "
            "compiled criterion instead removes almost the whole panel, because one of "
            "them treats a silent record as a negative. That configuration is measured "
            "in the report and is not what a deployment would run.",
            "",
        ]
        marker = "## What removed people"
        md = md.replace(marker, chr(10).join(note).lstrip(chr(10)) + chr(10) + marker, 1)

    out = Path(a.out) if a.out else run / f"worklist_{nct}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(align_tables(md), encoding="utf-8", newline="\n")

    # A machine-readable sidecar beside the document. `docs/COST.md` reports what
    # this worklist asks a person to do, and reading those counts back out of
    # rendered markdown would make a headline number depend on a heading string.
    groups: dict[tuple, int] = {}
    for s in wl["review"]:
        key = tuple(sorted(c["criterion_id"] for c in s["criteria"]
                           if c["verdict"] == "INDETERMINATE"))
        if key:
            groups[key] = groups.get(key, 0) + 1
    side = {
        "trial": (wl["trial"] or {}).get("nct_id"),
        "criteria_used": sorted(wl["criteria_used"]),
        "n_screens": len(wl["screens"]),
        "n_cells": len(wl["screens"]) * len(wl["criteria_used"]),
        "n_ruled_out": len(wl["ruled_out"]),
        "n_eligible": len(wl["eligible"]),
        "n_review": len(wl["review"]),
        "distinct_open_criteria": sorted(wl["open_questions"]),
        "question_sets": sorted(
            ({"criteria": list(k), "n_patients": v} for k, v in groups.items()),
            key=lambda g: (-g["n_patients"], g["criteria"])),
    }
    out.with_suffix(".json").write_text(
        json.dumps(side, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
    row = worklist.summary_row(wl)
    print(json.dumps(row, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
