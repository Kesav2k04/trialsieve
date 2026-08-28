"""Score the arms and write the evaluation report.

    python scripts/report.py --run runs/tierA

Reads every cell file in a run, restricts arms to the cells they share so the
comparison is paired, and writes both machine-readable results and the markdown
tables that appear in the README.

Nothing here chooses a metric. The metric was fixed in `docs/EVAL_PROTOCOL.md`
and committed before the first scored run.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from score import (  # noqa: E402
    Cell, agreement, operating_curve, paired_bootstrap, score_arm, score_panel, seed_spread,
)

ARMS = ("TS", "B0", "B1", "B2", "B3")


def load_cells(run: Path) -> dict[str, list[dict]]:
    """Group raw cell rows by the tag they were produced under."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in sorted((run / "cells").glob("cells_*.jsonl")):
        tag = p.stem.split("_", 2)[-1]
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    groups[tag].append(json.loads(line))
    return groups


def to_cells(rows: list[dict], arm: str) -> list[Cell]:
    out = []
    for r in rows:
        if arm not in r:
            continue
        out.append(Cell(r["patient_id"], r["criterion_id"], r["criterion_hash"],
                        r["gold"], r[arm], r.get("stratum", "synthea")))
    return out


def pair(a: list[Cell], b: list[Cell]) -> tuple[list[Cell], list[Cell]]:
    ka = {(c.patient_id, c.criterion_id): c for c in a}
    kb = {(c.patient_id, c.criterion_id): c for c in b}
    shared = sorted(set(ka) & set(kb))
    return [ka[k] for k in shared], [kb[k] for k in shared]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run = Path(a.run)
    groups = load_cells(run)
    if not groups:
        print(f"no cell files in {run/'cells'}", file=sys.stderr)
        return 2

    results: dict[str, dict] = {"run": str(run), "groups": {}}
    md: list[str] = []

    for tag, rows in sorted(groups.items()):
        merged: dict[tuple[str, str], dict] = {}
        for r in rows:
            merged.setdefault((r["patient_id"], r["criterion_id"]), {}).update(r)
        rows = list(merged.values())

        present = [x for x in ARMS if any(x in r for r in rows)]
        n_screens = len({(r["patient_id"], r["criterion_id"].split("-")[0]) for r in rows})
        block: dict = {"n_rows": len(rows), "arms": present, "n_screens": n_screens}

        md.append(f"\n## {tag}\n")
        md.append(f"{len(rows)} cells, {n_screens} screens, arms {', '.join(present)}.\n")
        md.append("| arm | coverage | SER | silent | false-FAILS | false-MEETS | "
                  "unnecessary abstention | errors | unique criteria |")
        md.append("|---|---|---|---|---|---|---|---|---|")

        scores = {}
        for arm in present:
            cells = to_cells(rows, arm)
            s = score_arm(arm, cells, n_screens)
            scores[arm] = s
            block.setdefault("cell_scores", {})[arm] = s.as_dict()
            md.append(f"| {arm} | {s.coverage:.1%} | {s.ser:.1%} | {s.n_silent} | "
                      f"{s.n_false_fails} | {s.n_false_meets} | "
                      f"{s.unnecessary_abstention} | {s.n_error} | {s.n_unique_criteria} |")

        md.append("\n### Panel reduction\n")
        md.append("| arm | screens | ruled out | reduction | false exclusions | "
                  "criteria used | 95% upper bound |")
        md.append("|---|---|---|---|---|---|---|")
        for arm in present:
            ps = score_panel(arm, to_cells(rows, arm))
            block.setdefault("panel_scores", {})[arm] = ps.as_dict()
            ub = (f"{ps.rule_of_three_upper:.3f} (rule of three, n_eff="
                  f"{ps.n_eff_excluding_criteria})") if ps.rule_of_three_upper is not None else "n/a"
            md.append(f"| {arm} | {ps.n_screens} | {ps.n_ineligible} | {ps.reduction:.1%} | "
                      f"**{ps.false_exclusions}** | {ps.n_eff_excluding_criteria} | {ub} |")

        if "TS" in present:
            curve = operating_curve(to_cells(rows, "TS"))
            block["operating_curve_TS"] = curve
            md.append("\n### TrialSieve operating curve\n")
            md.append("| false-exclusion budget | reduction | ruled out | actual false "
                      "exclusions | criteria used |")
            md.append("|---|---|---|---|---|")
            for r in curve:
                md.append(f"| {r['false_exclusion_budget']} | {r['reduction']:.1%} | "
                          f"{r['n_ineligible']} | {r['false_exclusions']} | "
                          f"{r['criteria_used']} |")

        comparisons = []
        for other in [x for x in present if x != "TS"]:
            if "TS" not in present:
                break
            ta, tb = pair(to_cells(rows, "TS"), to_cells(rows, other))
            if not ta:
                continue
            for metric in ("ser", "coverage", "false_fails"):
                r = paired_bootstrap(ta, tb, metric=metric, b=a.bootstrap)
                r["arms"] = f"TS - {other}"
                comparisons.append(r)
        if comparisons:
            block["paired_bootstrap"] = comparisons
            md.append("\n### Paired difference, two-way bootstrap "
                      f"(B={a.bootstrap}, resampling unique criteria and patients)\n")
            md.append("| comparison | metric | difference | 95% CI | crosses zero | n_eff |")
            md.append("|---|---|---|---|---|---|")
            for r in comparisons:
                md.append(f"| {r['arms']} | {r['metric']} | {r['observed_difference']:+.4f} | "
                          f"[{r['ci_low']:+.4f}, {r['ci_high']:+.4f}] | "
                          f"{'yes' if r['crosses_zero'] else 'no'} | "
                          f"{r['n_unique_criteria']} criteria |")

        results["groups"][tag] = block

    # noise floor across compilation seeds
    seed_groups: dict[int, list[float]] = defaultdict(list)
    for tag, block in results["groups"].items():
        ts = block.get("cell_scores", {}).get("TS")
        if ts and "_seed" in tag:
            try:
                seed = int(tag.split("_seed")[-1])
            except ValueError:
                continue
            seed_groups[seed].append(ts["ser"])
    sers = [v[0] for v in seed_groups.values() if v]
    if len(sers) >= 2:
        results["noise_floor_ser_across_seeds"] = seed_spread(sers)
        md.append("\n## Noise floor\n")
        md.append(f"TrialSieve SER across {len(sers)} compilation seeds: "
                  f"`{json.dumps(results['noise_floor_ser_across_seeds'])}`.")
        md.append("\nAn effect smaller than this spread is reported as not detected. The "
                  "execution engine is deterministic and would report a floor of exactly "
                  "zero, so the floor is measured where the randomness actually is, in "
                  "compilation.")

    out = Path(a.out or (run / "report"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=1) + "\n",
                                      encoding="utf-8", newline="\n")
    (out / "RESULTS.md").write_text(
        "# Evaluation results\n\nGenerated by `scripts/report.py`. The metric definitions "
        "are fixed in `docs/EVAL_PROTOCOL.md`, committed before the first scored run.\n"
        + "\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))
    print(f"\nwrote {out/'RESULTS.md'} and {out/'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
