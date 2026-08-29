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
import subprocess
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

    # A floor of exactly zero across seeds is far more likely to mean the seeds
    # were not independent than to mean compilation is deterministic. It happened:
    # `--seed` never reached the model, so three "seeds" replayed one set of
    # cassettes and produced identical predicates. The published floor would have
    # been 0.0 and every difference would have cleared it. So the predicate
    # digests are compared directly, and identical ones disqualify the floor
    # rather than producing a very impressive one.
    digests = {}
    for seed in sorted(seed_groups):
        src = Path(run) / "compiled" / f"criteria_seed{seed}.json"
        if src.exists():
            blob = json.loads(src.read_text(encoding="utf-8"))
            digests[seed] = tuple(c.get("predicate_sha256") for c in blob["criteria"])
    identical = len(digests) >= 2 and len(set(digests.values())) == 1
    results["seed_predicates_identical"] = identical

    if identical:
        md.append("\n## Noise floor\n")
        md.append(f"**NOT MEASURED.** The {len(digests)} compilation seeds produced "
                  f"byte-identical predicates, so the spread between them is zero for "
                  f"a reason that has nothing to do with compilation being stable: the "
                  f"seeds were not independent. A floor of zero would clear every "
                  f"difference in this report, so none is claimed against one. "
                  f"`docs/EVAL_PROTOCOL.md` registers this floor and it is outstanding.")
    elif len(sers) >= 2:
        results["noise_floor_ser_across_seeds"] = seed_spread(sers)
        md.append("\n## Noise floor\n")
        md.append(f"TrialSieve SER across {len(sers)} compilation seeds: "
                  f"`{json.dumps(results['noise_floor_ser_across_seeds'])}`.")
        md.append("\nAn effect smaller than this spread is reported as not detected. The "
                  "execution engine is deterministic and would report a floor of exactly "
                  "zero, so the floor is measured where the randomness actually is, in "
                  "compilation.")
        # `docs/EVAL_PROTOCOL.md` registers at least three seeds. Two is a range
        # between two points, not an estimate of spread, and the two numbers look
        # identical in the table either way. Which one this is has to be said in
        # the document rather than inferred from a count in a JSON field.
        if len(sers) < 3:
            md.append(f"\n**This is {len(sers)} seed(s), and the protocol registers at "
                      f"least 3.** What is printed above is the range between "
                      f"{len(sers)} points rather than an estimate of the spread, and it "
                      f"is almost certainly narrower than the real floor. Treat it as a "
                      f"lower bound on the noise and read every difference near it as "
                      f"undecided.")

    # degradation curve, read across the k groups rather than within one
    curve = []
    for tag, block in sorted(results["groups"].items()):
        if "_k" not in tag:
            continue
        try:
            k = int(tag.split("_k")[-1].split("_")[0])
        except ValueError:
            continue
        ts = block.get("cell_scores", {}).get("TS")
        ps = block.get("panel_scores", {}).get("TS")
        if not ts or not ps:
            continue
        curve.append({"k_percent": k, "coverage": ts["coverage"], "ser": ts["ser"],
                      "false_fails": ts["n_false_fails"], "reduction": ps["reduction"],
                      "false_exclusions": ps["false_exclusions"]})
    if len(curve) >= 2:
        curve.sort(key=lambda r: r["k_percent"])
        results["degradation_curve"] = curve
        md.append("\n## Degradation curve\n")
        md.append("Synthea records are complete by construction, so the failure mode this "
                  "design exists for barely occurs at k=0, and any silent error rate "
                  "measured there is a lower bound. Each row damages k percent of the "
                  "resources the *gold* predicates read, never the ones the system "
                  "compiled, so the harness cannot favour the arm under test.\n")
        md.append("| k | coverage | SER | false-FAILS | panel reduction | false exclusions |")
        md.append("|---|---|---|---|---|---|")
        for r in curve:
            md.append(f"| {r['k_percent']}% | {r['coverage']:.1%} | {r['ser']:.1%} | "
                      f"{r['false_fails']} | {r['reduction']:.1%} | "
                      f"**{r['false_exclusions']}** |")
        md.append("\nReal missingness is not random. It tracks fragmented care and sicker "
                  "patients, which is the one property this harness cannot reproduce, so "
                  "the curve is a floor on the effect rather than an estimate of it.")

    # label noise floor, if the second checker has run
    ag_path = ROOT / "evaluation" / "checker_b" / "agreement.json"
    if ag_path.exists():
        ag = json.loads(ag_path.read_text(encoding="utf-8"))
        results["label_noise_floor"] = ag
        a_pct = ag["agreement"]["percent_agreement"]
        md.append("\n## Label noise floor\n")
        md.append(f"Checker A and Checker B labelled the same {ag['n']} cells "
                  f"independently. B saw the criterion prose and a flattened patient "
                  f"table, on a different model family, with no sight of the predicate "
                  f"IR, of A, or of any system output.\n")
        md.append("| | |")
        md.append("|---|---|")
        md.append(f"| cells labelled twice | {ag['n']} |")
        md.append(f"| raw percent agreement | {a_pct:.1%} |")
        md.append(f"| Cohen's kappa | {ag['agreement']['cohens_kappa']:.3f} |")
        md.append(f"| Gwet's AC1 | {ag['agreement']['gwets_ac1']:.3f} |")
        md.append(f"| Checker A marginals | `{json.dumps(ag['a_marginals'])}` |")
        md.append(f"| Checker B marginals | `{json.dumps(ag['b_marginals'])}` |")
        md.append(f"\nPre-adjudication disagreement is {1 - a_pct:.1%}. Any difference "
                  f"between arms smaller than that is reported as uninterpretable rather "
                  f"than as a finding. Kappa is printed beside AC1 because kappa collapses "
                  f"under the skewed marginals expected here and would understate "
                  f"agreement that is real.")

    # provenance: which commit last touched each prompt file
    prompts = {}
    for f in sorted((ROOT / "src" / "trialsieve" / "agents").glob("*.py")):
        if f.name in ("__init__.py", "common.py"):
            continue
        try:
            prompts[f.name] = subprocess.run(
                ["git", "log", "-1", "--format=%H %cI", "--", str(f)],
                cwd=ROOT, capture_output=True, text=True).stdout.strip()
        except OSError:
            prompts[f.name] = ""
    results["prompt_files_last_commit"] = prompts
    md.append("\n## Provenance\n")
    md.append("The commit that last touched each prompt-carrying file. If any of these is "
              "later than the commit that produced these numbers, the run is invalid and "
              "is rerun. See `docs/DEV_SPLIT.md`.\n")
    md.append("| file | last touched by |")
    md.append("|---|---|")
    for k, v in prompts.items():
        md.append(f"| `{k}` | `{v[:16]}` {v[41:]} |")

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
