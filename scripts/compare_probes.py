"""Compare two probe runs on the probes they have in common.

    python scripts/compare_probes.py runs/probe-before/probe.json runs/probe-after/probe.json

The probe set grew between the two runs: the `broader` class did not exist when
the first one was recorded, because the capability it tests did not exist either.
Comparing the totals would then credit the change with probes the earlier run was
never given. So the comparison is restricted to the concepts both runs saw, and
the new ones are listed separately as a capability rather than as an improvement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from vocab_probe import PROBES, judge, score  # noqa: E402

BY_NAME = {p["concept"]: p for p in PROBES}


def rescored(path: Path) -> dict[str, dict]:
    """Apply today's scoring rule to a recorded run, calling no model.

    The acceptance rule changed after the first run. Applying it to one run and
    not the other would make the difference an artefact of the definition.
    """
    blob = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for r in blob["rows"]:
        probe = BY_NAME.get(r["concept"])
        if probe is None:
            continue
        codes = r.get("got_codes", r.get("got"))
        broader = r.get("got_broader", [])
        v = judge(probe, codes, broader)
        out[r["concept"]] = {**probe, "got_codes": codes, "got_broader": broader,
                             "status": r.get("status", ""),
                             "correct": v["correct"], "over_accepted": v["over_accepted"],
                             "under_accepted": v["under_accepted"],
                             "demoted": v.get("demoted", []), "mark": v["mark"]}
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    before_p, after_p = Path(sys.argv[1]), Path(sys.argv[2])
    before, after = rescored(before_p), rescored(after_p)
    common = sorted(set(before) & set(after))
    only_after = sorted(set(after) - set(before))

    print(f"before : {before_p}  ({len(before)} probes)")
    print(f"after  : {after_p}  ({len(after)} probes)")
    print(f"compared on the {len(common)} probes both runs were given\n")

    b_ok = sum(1 for k in common if before[k]["correct"])
    a_ok = sum(1 for k in common if after[k]["correct"])
    print(f"{'concept':40s} {'before':>8s} {'after':>8s}")
    print("-" * 60)
    for k in common:
        bm, am = before[k]["mark"].strip(), after[k]["mark"].strip()
        flag = "" if bm == am else ("   <- fixed" if after[k]["correct"] else
                                    "   <- REGRESSED" if before[k]["correct"] else "   <- changed")
        print(f"{k[:38]:40s} {bm:>8s} {am:>8s}{flag}")
    print("-" * 60)
    print(f"{'':40s} {b_ok:>8d} {a_ok:>8d}   of {len(common)}")

    if only_after:
        print(f"\nprobes only the later run was given ({len(only_after)}). These are a "
              f"capability the earlier run could not have, not an improvement on it:")
        for k in only_after:
            r = after[k]
            print(f"  {r['mark'].strip():>6s}  {k[:36]:38s} class {r['class']:8s} "
                  f"status {r['status']:14s} codes {r['got_codes']} "
                  f"broader {r['got_broader']}")

    out = {"before": str(before_p), "after": str(after_p),
           "compared_on": common, "before_correct": b_ok, "after_correct": a_ok,
           "n_common": len(common),
           "by_class_before": score([before[k] for k in common]),
           "by_class_after": score([after[k] for k in common]),
           "new_probes": {k: {"class": after[k]["class"], "correct": after[k]["correct"],
                              "status": after[k]["status"],
                              "got_codes": after[k]["got_codes"],
                              "got_broader": after[k]["got_broader"]}
                          for k in only_after}}
    dest = ROOT / "results" / "probe_comparison.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
