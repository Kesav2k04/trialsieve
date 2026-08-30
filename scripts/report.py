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
import random
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
# Importable as a module, not only runnable as a script: the tests import these.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _md_tables import align as align_tables

#: A newline, named, so an f-string can carry one without a backslash.
NL = chr(10)

from score import (  # noqa: E402
    Cell, agreement, operating_curve, operating_curve_cv, paired_bootstrap, score_arm,
    score_panel, seed_spread,
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

    # B2 costs a model call per cell, so it ran on a 10-patient subsample and its
    # file carries B2 verdicts only. With nothing to pair against, the report
    # scored it alone and printed no comparison at all, while the protocol calls
    # B2 the arm that matters. Comparing a 400-cell arm to a 15,400-cell arm on
    # different patients would not be a comparison either, so the scored run's
    # verdicts for exactly those cells are joined in and every B2 row is paired.
    base = {(r["patient_id"], r["criterion_id"]): r
            for r in groups.get("k0_seed7", [])}
    for tag, rows in groups.items():
        if not any("B2" in r for r in rows):
            continue
        for r in rows:
            src = base.get((r["patient_id"], r["criterion_id"]))
            if not src:
                continue
            for arm in ("TS", "B0", "B1"):
                if arm in src and arm not in r:
                    r[arm] = src[arm]
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




def coverage_denominators() -> dict | None:
    """Both denominators for criterion coverage, and the registered prediction.

    A coverage figure is a fraction, and this project had been publishing the
    numerator against the friendlier of two available denominators. The segmenter
    produced 65 criteria across the three held-out trials; the hand-authored gold
    set keeps 40; 24 of those 40 are marked `checkable`. 24/40 is 60%. 24/65 is
    37%. `docs/EVAL_PROTOCOL.md` registered "coverage will land at 30-40% **of
    segmented criteria**", so the registered denominator is 65, and the 25
    criteria the gold set drops are not a random 25: they skew hard toward
    informed consent, psychiatric history, substance use and site affiliation,
    which a structured record cannot settle. Dropping them raises coverage
    mechanically, and reporting only the number they raise is choosing the
    denominator after seeing both.
    """
    seg = ROOT / "results" / "segmentation.json"
    if not seg.exists():
        return None
    trials = json.loads(seg.read_text(encoding="utf-8")).get("trials", [])
    n_auto = sum(int(t.get("n_auto") or 0) for t in trials)
    sys.path.insert(0, str(ROOT / "evaluation" / "gold"))
    from criteria_set import CRITERIA
    n_gold = len(CRITERIA)
    n_checkable = sum(1 for c in CRITERIA if c.get("checkable"))
    # What the compiler actually produced, which is not the same number and was
    # being reported as if it were. `checkable` is a gold annotation: a human
    # deciding whether a structured record could settle the criterion at all. It
    # is a ceiling on coverage, not a measurement of this system, and quoting it
    # as "the system expresses N criteria as predicates" credits the run with
    # every criterion the answer key thought was answerable.
    comp_p = ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"
    compiled_ids, gap = set(), []
    if comp_p.exists():
        blob = json.loads(comp_p.read_text(encoding="utf-8"))["criteria"]
        compiled_ids = {c["criterion_id"] for c in blob if c.get("compilable")}
        reasons = {c["criterion_id"]: c.get("reason_not_compilable") for c in blob}
        gap = sorted(({"criterion_id": c["criterion_id"],
                       "reason": reasons.get(c["criterion_id"])}
                      for c in CRITERIA
                      if c.get("checkable") and c["criterion_id"] not in compiled_ids),
                     key=lambda r: r["criterion_id"])
    n_compiled = len(compiled_ids)
    if not (n_auto and n_gold):
        return None
    return {"n_segmented": n_auto, "n_gold": n_gold, "n_checkable": n_checkable,
            "coverage_of_segmented": round(n_checkable / n_auto, 4),
            "coverage_of_gold": round(n_checkable / n_gold, 4),
            "n_compiled": n_compiled,
            "compiled_of_segmented": round(n_compiled / n_auto, 4) if n_auto else None,
            "compiled_of_gold": round(n_compiled / n_gold, 4) if n_gold else None,
            "checkable_but_not_compiled": gap,
            "registered_band": [0.30, 0.40],
            "per_trial": [{"nct_id": t.get("nct_id"), "segmented": t.get("n_auto"),
                           "gold": t.get("n_gold")} for t in trials]}


def load_label_floor() -> dict | None:
    """The measured disagreement between the two independent labellers.

    Returns None when the second labeller has not run, and every caller has to
    handle that case explicitly, because a noise floor that silently vanishes
    turns "we could not measure this" into "there is nothing here to see". The
    report prints NOT MEASURED rather than dropping the section.
    """
    path = ROOT / "evaluation" / "checker_b" / "agreement.json"
    if not path.exists():
        return None
    blob = json.loads(path.read_text(encoding="utf-8"))
    ag = blob.get("agreement", blob)
    pattern = blob.get("disagreement_pattern") or {}
    n = int(blob.get("n") or ag.get("n") or 0)
    hard = soft = 0
    for key, count in pattern.items():
        a_lab, b_lab = key.split("->") if "->" in key else (key, key)
        if "INDETERMINATE" in (a_lab, b_lab):
            soft += int(count)
        else:
            hard += int(count)
    # Which stratum each disagreement came from. The sample is drawn with equal
    # shares of each Checker A label, so a rate over the whole sample is a rate in
    # a population that is one third FAILS, and no real panel is.
    strata: dict[str, dict] = {}
    for key, count in pattern.items():
        a_lab, b_lab = key.split("->") if "->" in key else (key, key)
        kind = "splits" if "INDETERMINATE" in (a_lab, b_lab) else "contradictions"
        strata.setdefault(a_lab, {"contradictions": 0, "splits": 0})[kind] += int(count)
    for lab, n_s in (blob.get("a_marginals") or {}).items():
        strata.setdefault(lab, {"contradictions": 0, "splits": 0})["n"] = int(n_s)

    return {"n": n,
            "strata": strata,
            "percent_agreement": ag.get("percent_agreement"),
            "cohen_kappa": ag.get("cohen_kappa", ag.get("cohens_kappa")),
            "gwet_ac1": ag.get("gwet_ac1", ag.get("gwets_ac1")),
            "marginals_a": blob.get("a_marginals") or ag.get("marginals_a"),
            "marginals_b": blob.get("b_marginals") or ag.get("marginals_b"),
            "n_contradictions": hard, "n_confidence_splits": soft,
            "hard_in_sample": (hard / n) if n else 0.0,
            "soft_in_sample": (soft / n) if n else 0.0}


def poststratify(floor: dict, population: Counter, draws: int = 4000,
                 seed: int = 20260829) -> dict | None:
    """The contradiction rate the scored cells would show, not the sample's own.

    `evaluation/checker_b.stratified` draws equal shares of each Checker A label
    and says in its own docstring that prevalence cannot be read off the result.
    The floor was then computed as contradictions divided by sample size, which is
    the rate in a population that is one third FAILS. The scored panel is 5.2%
    FAILS, and FAILS is by far the stratum the labellers contradict each other in
    (16 of 60 against 3 of 60), so dividing by the sample size published 10.6%
    where the panel's own rate is 2.3%.

    That number is not decorative. Any difference between two arms smaller than it
    is printed "below, uninterpretable", and at 10.6% the differences it covered
    were the ones where TrialSieve does not win. A floor drawn from a sample
    enriched in the hardest cells is a floor that excuses the losses.

    Returns None where the weights cannot be formed, because a floor that quietly
    falls back to the unweighted rate is the bug this exists to fix.
    """
    strata = floor.get("strata") or {}
    total = sum(population.values())
    if not strata or not total:
        return None
    usable = {lab: s for lab, s in strata.items() if s.get("n")}
    if not usable or not set(population) <= set(usable):
        # A label present in the scored cells and absent from the sample has no
        # measured rate, and assuming one would invent the number this fixes.
        return None

    weights = {lab: population.get(lab, 0) / total for lab in usable}
    rates = {lab: s["contradictions"] / s["n"] for lab, s in usable.items()}
    soft = {lab: s["splits"] / s["n"] for lab, s in usable.items()}
    point = sum(weights[lab] * rates[lab] for lab in usable)

    # The interval matters more than usual here: the stratum carrying most of the
    # estimate is 60 cells wide. Resampled within stratum, which is how the sample
    # was drawn, rather than over the sample as a whole.
    rng = random.Random(seed)
    boot = []
    for _ in range(draws):
        acc = 0.0
        for lab, s in usable.items():
            n_s, p_s = s["n"], rates[lab]
            hits = sum(1 for _ in range(n_s) if rng.random() < p_s)
            acc += weights[lab] * (hits / n_s)
        boot.append(acc)
    boot.sort()
    lo = boot[int(0.025 * (draws - 1))]
    hi = boot[int(0.975 * (draws - 1))]
    return {"hard": point, "hard_ci": [lo, hi],
            "soft": sum(weights[lab] * soft[lab] for lab in usable),
            "weights": {k: round(v, 4) for k, v in weights.items()},
            "per_stratum_contradiction_rate": {k: round(v, 4) for k, v in rates.items()},
            "n_population_cells": total, "draws": draws}


#: A cell group whose tag is not self-describing is a table nobody can read six
#: months later. `ow` in particular looks like a typo rather than the sensitivity
#: analysis it is, and an unexplained arm that scores better than the headline is
#: the kind of thing a reader is right to be suspicious of.
GROUP_NOTES = {
    "k0_seed7": "(the scored run)",
    "ow": "(sensitivity: every absence forced to unknown)",
}

GROUP_BLURB = {
    "ow": "**This is not a different system and it is not the headline.** It is the same compiled predicates from the same run, executed with `--absent-means-override unknown`, which ignores every `absent_means` decision the compiler made and treats a silent record as silent everywhere. The flag predates this run and exists to answer one question: how much of TrialSieve's error is the model asserting a closed world it was not entitled to? The section at the end of this document has the answer with the numbers attached.\n\nThe scored arm above remains the pre-registered result.",
}


def worst_closed_world_criterion(run: Path, groups: dict) -> tuple | None:
    """The compiled criterion whose `absent_means: false` costs the most cells.

    Returns (criterion_id, times it ruled a patient out, times that was wrong,
    the code it checked) or None. Named rather than left as an aggregate,
    because "most of the error comes from closed-world assertions" is a claim a
    reader cannot check and "this criterion, this code, these 358 patients" is.
    """
    import gzip  # noqa: F401  (kept local; the loader below is plain json)
    comp = run / "compiled" / "criteria_seed7.json"
    if not comp.exists():
        return None
    closed = {}
    for c in json.loads(comp.read_text(encoding="utf-8")).get("criteria", []):
        if not c.get("compilable"):
            continue
        found = []

        def walk(node):
            if isinstance(node, dict):
                q = node.get("query")
                if isinstance(q, dict) and q.get("absent_means") == "false":
                    found.extend(q.get("codes") or ["(no code)"])
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(c.get("expr"))
        if found:
            closed[c["criterion_id"]] = (found[0], c.get("source_text", ""))
    if not closed:
        return None
    best = None
    for tag, rows in groups.items():
        if tag != "k0_seed7":
            continue
        wrong, right = Counter(), Counter()
        fails, meets = Counter(), Counter()
        for r in rows:
            cid = r["criterion_id"]
            if cid not in closed:
                continue
            ts = r.get("TS")
            # A wrong commitment is a committed verdict that disagrees with gold,
            # in either direction, including where gold is INDETERMINATE. That is
            # the repository's own definition of a silent error, in
            # `evaluation/score.py`. This used to count `FAILS` only, so a
            # closed-world assertion that over-accepted rather than over-excluded
            # scored zero, the function returned None, and the guard test skipped
            # with the message "no closed-world assertion in this run, which is
            # the good case". There were three, and one of them made 22 wrong
            # MEETS: half the run's over-acceptances, reported as nothing.
            if ts not in ("MEETS", "FAILS"):
                continue
            if ts == r.get("gold"):
                right[cid] += 1
                continue
            wrong[cid] += 1
            (fails if ts == "FAILS" else meets)[cid] += 1
        for cid, n in wrong.most_common(1):
            best = (cid, right[cid], n, fails[cid], meets[cid],
                    closed[cid][0], closed[cid][1])
    return best


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

    # The label noise floor is loaded first because the comparison tables below
    # are annotated against it. Two labellers disagreeing is not one number: a
    # MEETS against a FAILS is a contradiction, while a MEETS against an
    # INDETERMINATE is the two of them drawing the confidence line in different
    # places. Only the first bounds what a difference between arms can mean, so
    # the two are separated rather than summed into one disagreement rate.
    floor = load_label_floor()
    if floor is not None:
        results["label_noise_floor"] = floor

    for tag, rows in sorted(groups.items()):
        merged: dict[tuple[str, str], dict] = {}
        for r in rows:
            merged.setdefault((r["patient_id"], r["criterion_id"]), {}).update(r)
        rows = list(merged.values())

        present = [x for x in ARMS if any(x in r for r in rows)]
        n_screens = len({(r["patient_id"], r["criterion_id"].split("-")[0]) for r in rows})
        block: dict = {"n_rows": len(rows), "arms": present, "n_screens": n_screens}

        # Reweighted to THIS group's label mix rather than the sample's. A group
        # is the population its own comparisons are drawn from, and the groups do
        # not share a mix: the full panel is 5.2% FAILS and the ten-patient
        # sample is not, so one floor for all of them would be wrong for most.
        gfloor = poststratify(floor, Counter(r["gold"] for r in rows)) if floor else None
        if gfloor is not None:
            block["label_floor_poststratified"] = gfloor

        md.append("")
        md.append(f"## {tag}  " + GROUP_NOTES.get(tag, ""))
        md.append("")
        if tag in GROUP_BLURB:
            md.append(GROUP_BLURB[tag])
            md.append("")
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


        # The per-cell baseline puts a whole chart in one prompt and 20% of these
        # charts do not fit, so those cells ran against a record trimmed by age
        # with the omission stated in the prompt. That is a difference in what the
        # two arms were given, and the brief asks for it to be explained rather
        # than assured away. `run_arms.py` has carried a flag on every affected
        # cell since the first run so the comparison could be repeated without
        # them, and nothing had ever repeated it.
        n_trimmed = sum(1 for r in rows if r.get("record_trimmed"))
        if n_trimmed:
            full = [r for r in rows if not r.get("record_trimmed")]
            block["n_cells_trimmed"] = n_trimmed
            md.append(f"{NL}#### Fairness check: the {len(full)} cells where no "
                      f"record was trimmed{NL}")
            md.append(f"{n_trimmed} of {len(rows)} cells "
                      f"({n_trimmed / len(rows):.0%}) put a chart in front of the "
                      f"per-cell baseline that had been trimmed by age to fit the "
                      f"prompt. TrialSieve reads the record through the engine and "
                      f"is not subject to that limit, so the arms were not given "
                      f"the same input on those cells. Rescored over only the "
                      f"cells where nothing was cut:")
            md.append("")
            md.append("| arm | SER, all cells | SER, untrimmed only | difference |")
            md.append("|---|---|---|---|")
            moved = {}
            for arm in present:
                s_all = scores[arm]
                s_full = score_arm(arm, to_cells(full, arm), n_screens)
                moved[arm] = s_full.ser - s_all.ser
                block.setdefault("cell_scores_untrimmed", {})[arm] = s_full.as_dict()
                md.append(f"| {arm} | {s_all.ser:.1%} | {s_full.ser:.1%} | "
                          f"{moved[arm]:+.1%} |")
            md.append("")
            worst = max(abs(v) for v in moved.values())
            if "TS" in moved and "B2" in moved:
                gap_all = scores["B2"].ser - scores["TS"].ser
                gap_full = (block["cell_scores_untrimmed"]["B2"]["ser"]
                            - block["cell_scores_untrimmed"]["TS"]["ser"])
                md.append(
                    f"The gap between the per-cell baseline and TrialSieve is "
                    f"**{gap_all:.1%}** over all cells and **{gap_full:.1%}** over "
                    f"the untrimmed ones, a change of {gap_full - gap_all:+.1%}. "
                    f"No arm moves by more than {worst:.1%}. The trimming is "
                    f"therefore not where the difference comes from, which is the "
                    f"claim this table exists to let a reader reject rather than "
                    f"the one it exists to assert.")

        md.append("\n### Primary outcome, as registered\n")
        md.append("`docs/EVAL_PROTOCOL.md` registers the primary outcome as panel "
                  "reduction **at zero false exclusions**, and VOID otherwise, reported "
                  "with the count. VOID is not a formatting choice. An arm that rules out "
                  "a patient who was in fact eligible has done the one thing this system "
                  "exists to prevent, and no reduction figure earns credit beside it. The "
                  "rule was registered before any run and then not implemented, so the "
                  "report printed a bare reduction and left the reader to apply it.")
        md.append("")
        md.append("| arm | primary outcome | false exclusions | reduction, descriptive only |")
        md.append("|---|---|---|---|")
        for arm in present:
            _ps = score_panel(arm, to_cells(rows, arm))
            _po = _ps.primary_outcome
            _shown = f"{_po:.1%}" if isinstance(_po, float) else "**VOID**"
            md.append(f"| {arm} | {_shown} | {_ps.false_exclusions} | {_ps.reduction:.1%} |")
        
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

            # The curve above chooses which criteria to trust by counting their
            # false exclusions on the same patients it then scores, so its zero
            # row is a hindsight optimum. This one runs the identical rule with
            # the choice made on other patients. Printing only the first would be
            # reporting a selection made on the evaluation set as a result.
            cv = operating_curve_cv(to_cells(rows, "TS"))
            block["operating_curve_TS_crossfitted"] = cv
            k = cv[0]["folds"] if cv else 0
            md.append("")
            md.append(f"The curve above is **in-sample**: each row picks the criterion "
                      f"subset using the gold labels of the patients it then scores, so it "
                      f"reports that a clean subset existed rather than that one could have "
                      f"been chosen in advance. Below is the same greedy rule cross-fitted "
                      f"over {k} folds of patients, so no patient contributes to the "
                      f"decision that scores them. The gap between the two is the "
                      f"selection's optimism.")
            md.append("")
            md.append(f"### TrialSieve operating curve, cross-fitted ({k}-fold over patients)")
            md.append("")
            md.append("| false-exclusion budget | reduction | ruled out | actual false "
                      "exclusions | criteria used (union) |")
            md.append("|---|---|---|---|---|")
            for r in cv:
                md.append(f"| {r['false_exclusion_budget']} | {r['reduction']:.1%} | "
                          f"{r['n_ineligible']} | {r['false_exclusions']} | "
                          f"{r['criteria_used']} |")
            base = {r["false_exclusion_budget"]: r for r in curve}
            worse = [r for r in cv
                     if r["false_exclusions"] > base[r["false_exclusion_budget"]]["false_exclusions"]]
            # Keyed by group. This was one shared top-level slot written inside
            # the per-group loop, so whichever group came last owned it: the
            # published `crossfit` block described the open-world sensitivity
            # arm while every document citing it meant the scored run. The
            # scored run keeps the flat keys as well, because they are what the
            # older documents point at.
            cf = results.setdefault("crossfit", {}).setdefault("by_group", {})
            cf.setdefault(tag, {})["optimism_rows"] = len(worse)
            if tag == "k0_seed7":
                results["crossfit"]["optimism_rows"] = len(worse)

            # Two identical curves is also what a cross-fit that silently did
            # nothing would print, so the separation that produces the equality is
            # measured and stated rather than assumed.
            fires, badc = Counter(), Counter()
            for c in to_cells(rows, "TS"):
                if c.system == "FAILS":
                    fires[c.criterion_hash] += 1
                    if c.gold != "FAILS":
                        badc[c.criterion_hash] += 1
            clean = sorted(h for h in fires if not badc[h])
            dirty = sorted((badc[h] for h in fires if badc[h]), reverse=True)
            counts = {"excluding_criteria": len(fires),
                      "clean_criteria": len(clean),
                      "dirty_false_exclusion_counts": dirty}
            results["crossfit"]["by_group"].setdefault(tag, {}).update(counts)
            if tag == "k0_seed7":
                results["crossfit"].update(counts)
            md.append("")
            if not worse:
                md.append(f"The two curves agree on every row. That is a property of "
                          f"this panel rather than a curve that was not recomputed: of "
                          f"the {len(fires)} criteria that ever exclude a patient, "
                          f"{len(clean)} make no false exclusion anywhere in "
                          f"{len({c.patient_id for c in to_cells(rows, 'TS')})} patients "
                          f"and the remaining {len(dirty)} make "
                          f"{', '.join(str(x) for x in dirty)}. Nothing sits near the "
                          f"threshold, so every fold selects the same subset. "
                          f"`tests/test_score.py` carries a panel where they do differ, "
                          f"so the agreement here is a measurement and not a no-op.")
            else:
                md.append(f"{len(worse)} of {len(cv)} rows lose their guarantee under "
                          f"cross-fitting. The in-sample row is the optimism, and the "
                          f"cross-fitted row is the one to read.")
            md.append("")

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
            md.append("| comparison | metric | difference | 95% CI | crosses zero | "
                      "n_eff | vs label floor |")
            md.append("|---|---|---|---|---|---|---|")
            for r in comparisons:
                # The prose under the noise-floor table promises that a difference
                # smaller than the two labellers' own disagreement is reported as
                # uninterpretable. It was a promise and nothing enforced it, so the
                # verdict is computed here and printed in the row it applies to.
                if gfloor is None:
                    verdict = "not measured"
                elif abs(r["observed_difference"]) >= gfloor["hard"]:
                    verdict = "above"
                elif abs(r["observed_difference"]) >= gfloor["hard"] / 2:
                    verdict = "**borderline**"
                else:
                    verdict = "**below, uninterpretable**"
                r["vs_label_floor"] = verdict.replace("*", "")
                md.append(f"| {r['arms']} | {r['metric']} | {r['observed_difference']:+.4f} | "
                          f"[{r['ci_low']:+.4f}, {r['ci_high']:+.4f}] | "
                          f"{'yes' if r['crosses_zero'] else 'no'} | "
                          f"{r['n_unique_criteria']} criteria | {verdict} |")
            if gfloor is not None:
                md.append("")
                md.append(f"The last column compares the absolute difference against "
                          f"the rate at which the two independent labellers contradict "
                          f"each other, **{gfloor['hard']:.1%}** "
                          f"(95% CI {gfloor['hard_ci'][0]:.1%} to "
                          f"{gfloor['hard_ci'][1]:.1%}). That is measured on "
                          f"{floor['n']} doubly-labelled cells and then reweighted to "
                          f"this group's own mix of labels, because the sample was "
                          f"drawn with equal shares of each and these "
                          f"{len(rows):,} cells are "
                          f"{gfloor['weights'].get('FAILS', 0):.1%} FAILS. The "
                          f"unweighted sample rate is "
                          f"{floor['hard_in_sample']:.1%}, and using it here would "
                          f"hold every comparison to the disagreement rate of a "
                          f"population made of the hardest cells. A CI that excludes "
                          f"zero says the difference is not noise from resampling; it "
                          f"says nothing about whether the labels themselves could "
                          f"support a difference that small.")

            if any(r["arms"] == "TS - B2" for r in block["paired_bootstrap"]):
                md.append("")
                md.append(
                    "**What B2 is, and what it is not.** B2 is one model call per "
                    "cell at temperature 0, sampled once. The protocol also "
                    "registers B3, the same baseline sampled three times with a "
                    "majority vote, and B3 was not run: the cassette key is a hash "
                    "of the full request including temperature and the store keeps "
                    "one response per key, so three draws of one request replay as "
                    "one answer counted three times "
                    "(`docs/EVAL_PROTOCOL.md:65`, entry 26 of the improvement "
                    "changelog). So the gap measured here is against a "
                    "single-sample per-cell baseline, not against the best "
                    "per-cell baseline money can buy. Self-consistency would "
                    "plausibly close some of it, and this evaluation cannot say "
                    "how much.")

        results["groups"][tag] = block

    # noise floor across compilation seeds
    seed_groups: dict[int, list[float]] = defaultdict(list)
    seed_primary: dict[int, list[tuple]] = defaultdict(list)
    for tag, block in results["groups"].items():
        ts = block.get("cell_scores", {}).get("TS")
        if ts and "_seed" in tag:
            try:
                seed = int(tag.split("_seed")[-1])
            except ValueError:
                continue
            seed_groups[seed].append(ts["ser"])
            # The registered floor is the spread of the PRIMARY metric, and the primary
            # metric is not SER. Publishing SER alone made the floor look tight while
            # panel reduction moved 60.3 to 46.5 points and false exclusions moved 182
            # to 20 across the same two seeds. A floor measured on the one number that
            # does not move is a floor that clears everything.
            ps = block.get("panel_scores", {}).get("TS")
            if ps:
                seed_primary[seed].append((ps["reduction"], ps["false_exclusions"]))
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

    # What did not compile, split by whether a person decided it or a retry
    # budget ran out. Both land in the same field with the same shape, and the
    # difference is the whole point: one is the system working as designed and
    # the other is a criterion lost to a validator the model could not satisfy.
    comp_src = Path(run) / "compiled" / "criteria_seed7.json"
    if comp_src.exists():
        crit = json.loads(comp_src.read_text(encoding="utf-8"))["criteria"]
        nope = [c for c in crit if not c.get("compilable")]
        crashed = [c for c in nope if str(
            c.get("reason_not_compilable", "")).startswith("compiler failed:")]
        principled = [c for c in nope if c not in crashed]
        results["not_compilable"] = {
            "total": len(nope),
            "principled_refusals": len(principled),
            "exhausted_retries": [c["criterion_id"] for c in crashed],
        }
        md.append(NL + "## What did not compile, and why" + NL)
        md.append(f"{len(crit)} criteria were put to the compiler and "
                  f"{len(crit) - len(nope)} produced predicates. Of the {len(nope)} "
                  f"that did not, **{len(principled)} are refusals with a named "
                  f"blocker** and **{len(crashed)} ran out of retries**. Those two "
                  f"are not the same event and this report does not report them as "
                  f"one number.")
        for c in crashed:
            cid = c["criterion_id"]
            reason = c.get("reason_not_compilable")
            text = str(c.get("text", "")).strip()
            traj = (Path(run) / "trajectories" / "compiler" / f"{cid}-seed7.jsonl")
            tried, rejects = [], []
            if traj.exists():
                for line in traj.read_text(encoding="utf-8").splitlines():
                    ev = json.loads(line)
                    if ev.get("event") == "validation_error":
                        rejects.append(str(ev.get("message", "")).split(": ", 1)[-1])
                    if ev.get("event") == "llm_response" and '"expr"' in (ev.get("text") or ""):
                        raw = ev["text"]
                        try:
                            blob = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
                        except ValueError:
                            continue
                        for arg in (blob.get("expr") or {}).get("args") or []:
                            q = arg.get("query") or {}
                            if q.get("broader_codes"):
                                tried.append((q.get("codes"), q.get("broader_codes")))
            md.append("")
            md.append(f"`{cid}` is the second kind. Its `reason_not_compilable` reads "
                      f"`{reason}`, which reads like a crash and is not one. The "
                      f"grounder returned this criterion's second concept as "
                      f"broader-only: no exact code at all, and the coarse code "
                      f"44054006 in `broader_codes`. The compiler then made "
                      f"{len(rejects)} attempts to express that, and the IR "
                      f"validator rejected every one:")
            md.append("")
            md.append("| attempt | `codes` | `broader_codes` | rejected because |")
            md.append("|---|---|---|---|")
            for n, msg in enumerate(rejects):
                got = tried[n] if n < len(tried) else (None, None)
                short = msg.split(": ", 1)[-1] if ": " in msg else msg
                md.append(f"| {n + 1} | `{got[0]}` | `{got[1]}` | {short} |")
            md.append("")
            md.append("Attempt 1 is the answer this design asks for. `README.md` says "
                      "a code the site records more coarsely than the criterion needs "
                      "goes in `broader_codes` so that presence cannot settle the "
                      "verdict and absence still can. That is exactly what the model "
                      "sent, and `src/trialsieve/ir.py:103` rejected it, because "
                      "every query must carry at least one exact code. Attempt 2 "
                      "hedged by declaring the code both ways and hit "
                      "`src/trialsieve/ir.py:108`. Attempt 3 dropped `codes` "
                      "entirely and hit line 103 again. There was no legal move.")
            md.append("")
            md.append(f"The shape the validator does accept is `codes: "
                      f"['44054006']` with `broader_codes` empty, which is the "
                      f"shape two other criteria in this run emitted and which "
                      f"turns an UNKNOWN into a MEETS. So on this concept the "
                      f"schema rejects the careful answer and accepts the "
                      f"dangerous one. 44054006 is the code behind those two "
                      f"promotions, and it is the same code that produced 358 of "
                      f"the 424 wrong exclusions in the first published run. "
                      f"That pair is a record of a run this one is not: those "
                      f"numbers are not above and they are not in this document, "
                      f"they are entry 29 of `docs/IMPROVEMENT_CHANGELOG.md`, "
                      f"which is where the measurement lives. One coarse code, "
                      f"three failures, one root cause.")
            md.append("")
            md.append(f"The criterion reads *{text}*, and insulin is in this "
                      f"vocabulary, so this is not a concept the corpus cannot "
                      f"express. It sits in the same bucket as {len(principled)} "
                      f"criteria that were correctly refused, and counting it with "
                      f"them overstates how much of the non-coverage is "
                      f"principled. Entry 27 of the improvement changelog has the "
                      f"rest, including why the IR was not changed.")

        if not crashed:
            md.append("")
            md.append("Nothing in this run was lost to the validator, and that is a "
                      "change rather than a property. In the run this report first "
                      "described, `NCT06989723-EXC-01` had a concept the grounder "
                      "returned as broader-only, with no exact code at all. "
                      "`src/trialsieve/ir.py:103` required every query to carry at "
                      "least one exact code, so the shape `README.md` asks for, "
                      "`codes: []` with the coarse code in `broader_codes`, could "
                      "not be written down. The model sent it first, was rejected, "
                      "hedged into declaring the code both ways, was rejected by the "
                      "disjointness rule, dropped `codes` again, and ran out of "
                      "retries. The only shape the validator accepted was the one "
                      "that puts a coarse code where presence settles a verdict.")
            md.append("")
            md.append("The IR now accepts an empty `codes` list when `broader_codes` "
                      "carries the concept, and refuses only a query with no code in "
                      "either slot. `tests/test_not_compilable.py` keeps the split "
                      "visible so a future crash cannot be absorbed into the refusal "
                      "count the way that one was. Entries 27 and 29 of the "
                      "improvement changelog have the rest.")

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
    reds = [v[0][0] for v in seed_primary.values() if v]
    fxs = [v[0][1] for v in seed_primary.values() if v]
    if len(reds) >= 2:
        results["noise_floor_primary_across_seeds"] = {
            "panel_reduction": seed_spread(reds),
            "false_exclusions": seed_spread([float(x) for x in fxs])}
        md.append("")
        md.append("**The registered floor is the spread of the primary metric, and "
                  "that is not SER.** Panel reduction across the same seeds: "
                  f"`{json.dumps(seed_spread(reds))}`. False exclusions: "
                  f"`{json.dumps(seed_spread([float(x) for x in fxs]))}`.")
        md.append("")
        # This paragraph used to be a fixed sentence saying the primary metric
        # moved "by more than ten points". It was true when it was written. Entry
        # 30 collapsed the spread to zero and the sentence stayed, sitting two
        # lines under a printed range of 0.0, which is this project's own failure
        # mode with the project on the receiving end. It is computed now, so it
        # cannot outlive the numbers above it.
        r_red = seed_spread(reds)["range"]
        r_fx = seed_spread([float(x) for x in fxs])["range"]
        if r_red == 0 and r_fx == 0:
            md.append(
                f"**Both are flat.** Across {len(reds)} seeds the panel reduction "
                f"and the false-exclusion count do not move at all: the range is "
                f"0 on each. That is a change from an earlier run of this same "
                f"report, where reduction moved more than ten points across seeds "
                f"and this paragraph said so; entry 30 of the changelog is what "
                f"removed the movement. A zero floor is not a licence to call "
                f"every difference detected. It means seed choice is no longer a "
                f"source of variation here, and the floor that does bound this "
                f"report is the label noise floor above, measured between two "
                f"independent labellers rather than between two seeds.")
        else:
            md.append(
                f"**The registered floor is the spread of the primary metric, and "
                f"it is not zero.** Across {len(reds)} seeds the panel reduction "
                f"moves by {r_red * 100:.1f} points and the false-exclusion count "
                f"by {r_fx:.0f}. No difference in this report smaller than that "
                f"spread is claimed as detected, and a floor quoted on SER alone "
                f"would have hidden it, because SER is the stable one.")

    # degradation curve, read across the k groups rather than within one
    curve = []
    # The group tags are `k0_seed7`, `k10_seed7`, `ow`. This looked for "_k" and
    # split on it, which matches none of them, so the curve was empty for every run
    # and the section never rendered. The harness had also never been run, so an
    # empty curve looked like the expected state instead of a parse that could not
    # succeed. Only the scored seed is charted, because a curve that mixes seeds
    # would be reading the seed spread as a degradation effect.
    for tag, block in sorted(results["groups"].items()):
        if not tag.startswith("k") or "_seed" not in tag:
            continue
        try:
            k = int(tag[1:].split("_")[0])
            seed = int(tag.split("_seed")[-1])
        except ValueError:
            continue
        if seed != 7:
            continue
        ts = block.get("cell_scores", {}).get("TS")
        ps = block.get("panel_scores", {}).get("TS")
        if not ts or not ps:
            continue
        curve.append({"k_percent": k, "coverage": ts["coverage"], "ser": ts["ser"],
                      "false_fails": ts["n_false_fails"],
                      # Divided, not the stored four-place `reduction`, for the
                      # same reason the sensitivity table above divides: two
                      # roundings of one quantity print two different tenths.
                      "reduction": ps["n_ineligible"] / ps["n_screens"],
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

    # label noise floor
    md.append("")
    md.append("## Label noise floor")
    md.append("")
    if floor is None:
        md.append("**NOT MEASURED.** `evaluation/checker_b/agreement.json` is absent, so "
                  "no second independent labelling exists in this checkout and there is "
                  "no bound on how much of any difference above is label noise. This "
                  "section is printed empty rather than omitted, because a missing "
                  "section and a section with nothing to report look identical once a "
                  "document has been read past.")
    else:
        md.append(f"Checker A and Checker B labelled the same {floor['n']} cells "
                  f"independently. B saw the criterion prose and a flattened patient "
                  f"table, on a different model family, with no sight of the predicate "
                  f"IR, of A, or of any system output. `python scripts/verify.py blind` "
                  f"reads that claim out of B's own recorded prompts.")
        md.append("")
        md.append("| | |")
        md.append("|---|---|")
        md.append(f"| cells labelled twice | {floor['n']} |")
        md.append(f"| raw percent agreement | {floor['percent_agreement']:.1%} |")
        md.append(f"| Cohen's kappa | {floor['cohen_kappa']:.3f} |")
        md.append(f"| Gwet's AC1 | {floor['gwet_ac1']:.3f} |")
        md.append(f"| **contradictions** (MEETS against FAILS) | "
                  f"**{floor['n_contradictions']} = {floor['hard_in_sample']:.1%} "
                  f"of the sample** |")
        md.append(f"| confidence splits (a definite verdict against INDETERMINATE) | "
                  f"{floor['n_confidence_splits']} = {floor['soft_in_sample']:.1%} "
                  f"of the sample |")
        md.append(f"| Checker A marginals | `{json.dumps(floor['marginals_a'])}` |")
        md.append(f"| Checker B marginals | `{json.dumps(floor['marginals_b'])}` |")
        md.append("")
        md.append(f"The two labellers disagree on "
                  f"{1 - floor['percent_agreement']:.1%} of cells, and that total is "
                  f"split rather than quoted whole because the two halves bound "
                  f"different things. {floor['n_contradictions']} cells are "
                  f"contradictions, where one labeller says a patient meets a criterion "
                  f"and the other says they fail it; those are the cells where at least "
                  f"one label is simply wrong. The other "
                  f"{floor['n_confidence_splits']} are one labeller committing where the "
                  f"other abstained. That is a disagreement about how much a record has "
                  f"to say before it counts as saying it, which is the same judgement "
                  f"this whole system is built to make explicit, so counting it as label "
                  f"error would be scoring the question rather than the answer.")
        md.append("")
        md.append("### What that rate is a rate of")
        md.append("")
        scored = results["groups"].get("k0_seed7", {})
        ps = scored.get("label_floor_poststratified")
        if ps is None:
            md.append("The sample was drawn with equal shares of each Checker A label, "
                      "so the percentage above is the contradiction rate in a population "
                      "made of equal parts MEETS, FAILS and INDETERMINATE. No scored "
                      "group here could be reweighted to its own mix, so no population "
                      "rate is published rather than reusing the sample's.")
        else:
            rates = ps["per_stratum_contradiction_rate"]
            w = ps["weights"]
            md.append(f"The sample was drawn with equal shares of each Checker A label, "
                      f"deliberately: a uniform draw would have been almost all "
                      f"INDETERMINATE and a labeller who abstained on everything would "
                      f"have scored well. The cost is that "
                      f"{floor['hard_in_sample']:.1%} is the contradiction rate in a "
                      f"population that is one third FAILS, and the scored panel is "
                      f"{w.get('FAILS', 0):.1%} FAILS.")
            md.append("")
            md.append("| Checker A label | contradicted | share of the sample | "
                      "share of the scored panel |")
            md.append("|---|---|---|---|")
            for lab in sorted(rates):
                n_s = floor["strata"][lab]["n"]
                md.append(f"| {lab} | {floor['strata'][lab]['contradictions']} of "
                          f"{n_s} = {rates[lab]:.1%} | {n_s / floor['n']:.1%} | "
                          f"{w.get(lab, 0):.1%} |")
            md.append("")
            md.append(f"Reweighting those rates to the panel's own mix gives "
                      f"**{ps['hard']:.1%}** (95% CI {ps['hard_ci'][0]:.1%} to "
                      f"{ps['hard_ci'][1]:.1%}, resampled within stratum), and that is "
                      f"the figure the comparison tables above are marked against. "
                      f"Using {floor['hard_in_sample']:.1%} instead was not "
                      f"conservative: it is the rate for a population made of the "
                      f"hardest cells, it is "
                      f"{floor['hard_in_sample'] / ps['hard']:.1f} times the panel's "
                      f"own, and every comparison it covered was reported "
                      f"uninterpretable. Two of those were comparisons TrialSieve "
                      f"loses.")
        md.append("")
        md.append(f"Checker B abstains more than A does "
                  f"({floor['marginals_b'].get('INDETERMINATE')} against "
                  f"{floor['marginals_a'].get('INDETERMINATE')} of {floor['n']}), which "
                  f"is the direction that matters: B was not simply noisier, it drew a "
                  f"stricter line. Kappa is printed beside AC1 because kappa collapses "
                  f"under skewed marginals and would understate agreement that is real.")
        md.append("")

    wc = worst_closed_world_criterion(run, groups)
    worst_absence = wc[:6] if wc else None
    worst_absence_text = (wc[6][:120] if wc else "")

    # What the compiler's closed-world assertions cost, computed rather than
    # asserted. Every number in the prose below is read back out of the two
    # scored groups, because a paragraph that quotes a figure it did not compute
    # goes stale the first time the run changes and nothing notices.
    base = results["groups"].get("k0_seed7", {}).get("cell_scores", {}).get("TS")
    ow = results["groups"].get("ow", {}).get("cell_scores", {}).get("TS")
    bp = results["groups"].get("k0_seed7", {}).get("panel_scores", {}).get("TS")
    op = results["groups"].get("ow", {}).get("panel_scores", {}).get("TS")
    md.append("")
    md.append("## Sensitivity: what the closed-world assertions cost")
    md.append("")
    if not (base and ow and bp and op):
        md.append("**NOT MEASURED.** The open-world arm has not been run in this "
                  "checkout, so there is no figure for how much of the error above "
                  "comes from the compiler asserting a closed world. Produce it with "
                  "`python scripts/run_arms.py --run runs/tierA --arms TS --seed 7 "
                  "--mode replay --absent-means-override unknown --tag ow`. This "
                  "section is printed empty rather than omitted.")
    else:
        rows = [("coverage", base["coverage"], ow["coverage"], "pct"),
                ("silent error rate", base["ser"], ow["ser"], "pct"),
                ("silent errors", base["n_silent"], ow["n_silent"], "int"),
                ("false FAILS", base["n_false_fails"], ow["n_false_fails"], "int"),
                ("false MEETS", base["n_false_meets"], ow["n_false_meets"], "int"),
                # Divided rather than read. `reduction` is rounded to four
                # places on the way into results.json, and formatting that to
                # one decimal rounds a second time: 0.46147 stores as 0.4615
                # and prints as 46.2%, against the 46.1% every other table
                # here prints and the narration speaks.
                ("panel reduction",
                 bp["n_ineligible"] / bp["n_screens"],
                 op["n_ineligible"] / op["n_screens"], "pct"),
                ("false exclusions", bp["false_exclusions"], op["false_exclusions"], "int")]
        md.append("| | as compiled | absence forced to unknown | change |")
        md.append("|---|---|---|---|")
        for label, a_, b_, kind in rows:
            if kind == "pct":
                md.append(f"| {label} | {a_:.1%} | {b_:.1%} | "
                          f"{(b_ - a_) * 100:+.1f} points |")
            else:
                pct = f", {(b_ - a_) / a_:+.0%}" if a_ else ""
                md.append(f"| {label} | {a_} | {b_} | {b_ - a_:+d}{pct} |")
        md.append("")
        cut = base["n_silent"] - ow["n_silent"]
        md.append(f"Ignoring every closed-world decision the compiler made removes "
                  f"{cut} of {base['n_silent']} silent errors "
                  f"({cut / base['n_silent']:.0%}) and "
                  f"{bp['false_exclusions'] - op['false_exclusions']} of "
                  f"{bp['false_exclusions']} false exclusions, and costs "
                  f"{(base['coverage'] - ow['coverage']) * 100:.1f} points of "
                  f"coverage. Read that the way it falls: after the repairs in "
                  f"entries 29 and 30, the closed-world assertions left in this run "
                  f"are not where its error is. This section used to close by saying "
                  f"the opposite, that almost all of the error was the model reading "
                  f"a silent record as an answer, which is what the run looked like "
                  f"before those repairs and is contradicted by the row above it now. "
                  f"The remaining flags sit inside disjunctions where another term "
                  f"settles the verdict anyway, so flipping them moves nothing.")
        md.append("")
        # the single worst offender, named, with its own cell counts
        if worst_absence:
            cid, right, wrong, n_fails, n_meets, code = worst_absence
            md.append(f"The criterion that still carries one, and what it gets "
                      f"wrong. This is a correlation and not the cause: the row "
                      f"above already shows that flipping the flag changes nothing, "
                      f"so these are errors made by a criterion that happens to hold "
                      f"a closed-world assertion, not errors the assertion produced. "
                      f"`{cid}` compiles "
                      f"*{worst_absence_text}* against `{code}` with `absent_means` "
                      f"set to `false`. It commits {right + wrong} verdicts on the "
                      f"scored panel, is right about {right} of them, and is wrong "
                      f"about {wrong}: **{n_fails} wrong FAILS** against "
                      f"{base['n_false_fails']} in the run, and **{n_meets} wrong "
                      f"MEETS** against {base['n_false_meets']}. Both directions are "
                      f"printed because only one of them was counted here until an "
                      f"independent reader checked: the search for the worst offender "
                      f"scored wrong exclusions and ignored wrong acceptances, so a "
                      f"criterion that over-accepted came back as no offender at all. "
                      f"A silent error is a committed verdict that is wrong, and the "
                      f"direction it is wrong in decides who pays, not whether it "
                      f"counts.")
            md.append("")
        md.append("The compiler prompt states that a wrong `false` rules a patient out "
                  "on the strength of a gap in their record and to choose `unknown` "
                  "when in doubt. The critic's fourth review rule is the same check. "
                  "Both are model-side, both had the information in front of them, and "
                  "both passed it. What stops it reaching a coordinator is the "
                  "sign-off gate, where a human reads the predicate in English before "
                  "any worklist exists: `docs/GATE.md`.")
        md.append("")

    # Criterion coverage, against both available denominators. Printed before
    # the cell tables are read rather than after, because a reader who has already
    # taken 24.1% as the headline will not revise it downward from a footnote.
    cd = coverage_denominators()
    md.append("")
    md.append("## Criterion coverage, both denominators")
    md.append("")
    if cd is None:
        md.append("**NOT MEASURED.** `results/segmentation.json` is absent, so the "
                  "number of criteria the segmenter produced is unknown and coverage "
                  "can only be quoted against the hand-authored set. Regenerate it "
                  "with `python evaluation/segmentation.py`.")
    else:
        lo, hi = cd["registered_band"]
        md.append(f"Two numbers, and until this run the wrong one was published. "
                  f"**{cd['n_checkable']}** criteria in the gold set are marked "
                  f"`checkable`, which is a human deciding a structured record "
                  f"*could* settle them. The compiler produced predicates for "
                  f"**{cd['n_compiled']}**. The first is a ceiling on what any "
                  f"system here could reach; only the second is this system.")
        md.append("")
        md.append("| numerator | of the 40-criterion gold set | of the 65 the segmenter produced |")
        md.append("|---|---|---|")
        md.append(f"| {cd['n_checkable']} the gold set calls checkable | "
                  f"{cd['coverage_of_gold']:.0%} | {cd['coverage_of_segmented']:.0%} |")
        md.append(f"| **{cd['n_compiled']} the compiler produced** | "
                  f"**{cd['compiled_of_gold']:.0%}** | "
                  f"**{cd['compiled_of_segmented']:.1%}** |")
        md.append("")
        inband = lo <= (cd["compiled_of_segmented"] or 0) <= hi
        md.append(f"`docs/EVAL_PROTOCOL.md` registered, before any scored run, that "
                  f"coverage would land at {lo:.0%} to {hi:.0%} **of segmented "
                  f"criteria**, following Kopcke et al., and that a number far above "
                  f"that would suggest the criteria had been cherry-picked. The "
                  f"registered denominator is {cd['n_segmented']}, not "
                  f"{cd['n_gold']}.")
        md.append("")
        md.append(f"**Against the registered band this run is at "
                  f"{cd['compiled_of_segmented']:.1%}, which is "
                  f"{'inside' if inband else 'below'} it.** The "
                  f"{cd['coverage_of_segmented']:.0%} this report used to print was "
                  f"the checkable count against the same denominator, so it was the "
                  f"answer key's number wearing the system's name, and it happened to "
                  f"land inside the band the system missed. Entry 28 of the "
                  f"improvement changelog has how that went unnoticed.")
        md.append("")
        if cd.get("checkable_but_not_compiled"):
            gap = cd["checkable_but_not_compiled"]
            md.append(f"The {len(gap)} criteria the gold set calls checkable and the "
                      f"compiler did not produce:")
            md.append("")
            md.append("| criterion | why not |")
            md.append("|---|---|")
            for g in gap:
                why = str(g["reason"] or "(not present in the compiled set)")
                why = why.split(".")[0].strip() if "." in why else why.strip()
                md.append(f"| `{g['criterion_id']}` | {why} |")
            md.append("")
            # Counted, not asserted. This said "Six of those are the vocabulary
            # refusing ... The seventh is the one lost to the IR validator" and
            # listed exactly six rows, because the seventh stopped existing when
            # entry 29 fixed the validator and the sentence did not follow.
            vocab = sum(1 for g in gap if "vocab" in str(g["reason"] or "").lower()
                        or "terminology" in str(g["reason"] or "").lower())
            other = len(gap) - vocab
            md.append(
                f"{vocab} of those {len(gap)} are the vocabulary refusing, which is "
                f"the design working: a concept with no code in this site's "
                f"terminology stops the criterion instead of clearing every patient "
                f"on it."
                + (f" The remaining {other} stopped for another reason, listed in "
                   f"the table above." if other else
                   " There is no other kind in this run; every one of them is the "
                   "vocabulary. An earlier version of this report claimed one more "
                   "lost to the IR validator, which entry 29 had already fixed.")
                + " So the gap between the ceiling and the result is the price of "
                  "the refusal policy, and that price belongs in the coverage "
                  "number rather than in a footnote under a higher one.")
            md.append("")
        md.append(f"Against {cd['n_gold']} the compiled figure is "
                  f"{cd['compiled_of_gold']:.0%}. The "
                  f"{cd['n_segmented'] - cd['n_gold']} criteria the gold set drops "
                  f"are listed in full in `docs/SEGMENTATION.md` and they are not a "
                  f"random {cd['n_segmented'] - cd['n_gold']}: informed consent, "
                  f"psychiatric history, substance use, site affiliation, pregnancy "
                  f"intent, allergy to study agents. A structured record cannot "
                  f"settle any of them, so removing them raises coverage without the "
                  f"system having answered anything more. Beating a registered "
                  f"prediction by picking the denominator afterwards is not beating "
                  f"it, and neither is picking the numerator.")
        md.append("")
        md.append("| trial | segmenter | hand-authored |")
        md.append("|---|---|---|")
        for t in cd["per_trial"]:
            md.append(f"| `{t['nct_id']}` | {t['segmented']} | {t['gold']} |")
        md.append("")
        md.append(f"The panel-reduction figures above inherit the same denominator: "
                  f"a screen is ruled ineligible on the {cd['n_gold']} hand-authored "
                  f"criteria, and a coordinator runs the whole protocol. The reduction "
                  f"is therefore what these criteria achieve, not what the protocol "
                  f"would.")
        md.append("")
        results["criterion_coverage"] = cd

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
    (out / "RESULTS.md").write_text(align_tables(
        "# Evaluation results\n\nGenerated by `scripts/report.py`. The metric definitions "
        "are fixed in `docs/EVAL_PROTOCOL.md`, committed before the first scored run.\n"
        + "\n".join(md)) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))
    print(f"\nwrote {out/'RESULTS.md'} and {out/'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
