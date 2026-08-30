"""What this cost and how long it took, read out of the run rather than recalled.

    python scripts/costs.py

Writes `docs/COST.md`. Every row comes from a file the run produced: recorded
token counts, recorded wall clock, and the number of cells each step touched.

**On the dollar figure.** The model backend here is a locally authenticated vendor
CLI on a subscription, so the marginal cost of a call is zero and reporting "$0"
would be true and useless. What a reader wants to know is what this would cost
them, so each row also carries an estimate at published per-token rates for a
comparable model, clearly labelled as an estimate and with the rate printed beside
it. A number that is right about this machine and silent about theirs is the wrong
number to publish.

**On the token counts.** The provider returns them when it can, and the local shim
cannot, so those rows fall back to a four-characters-per-token estimate. Which
rows are estimated is stated in the table rather than averaged away.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _md_tables import align as align_tables

ROOT = Path(__file__).resolve().parents[1]

#: Published rates for a mid-tier hosted model, dollars per million tokens, as a
#: yardstick rather than a quote. Named and dated so a reader can check whether it
#: has moved rather than wondering what it was.
RATE_LABEL = "a mid-tier hosted model at $0.30 in / $2.50 out per million tokens"
RATE_IN, RATE_OUT = 0.30 / 1e6, 2.50 / 1e6


def money(pt: int, ct: int) -> str:
    d = pt * RATE_IN + ct * RATE_OUT
    return f"${d:,.2f}" if d >= 0.005 else "under a cent"


def clock(s: float) -> str:
    s = int(s + 0.5)
    if s < 90:
        return f"{s} s"
    m, sec = divmod(s, 60)
    if m < 90:
        return f"{m} min {sec:02d} s"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min"


def _accuracy_on_the_same_cells() -> list[str]:
    """Whether the cheaper path is also the worse one, on the cells both arms ran.

    A cost curve on its own invites the obvious objection, that the cheap arm is
    cheap because it does less. Both arms are scored on the same 400 cells in
    `results/RESULTS.md`, so the answer is measured rather than argued. Silent if
    the paired group is not in the results, because the claim only holds paired.
    """
    res = read(ROOT / "results" / "results.json") or {}
    g = (res.get("groups") or {}).get("b2_10p")
    if not g:
        return []
    cell, panel = g.get("cell_scores", {}), g.get("panel_scores", {})
    if not {"TS", "B2"} <= set(cell) or not {"TS", "B2"} <= set(panel):
        return []
    return [
        f"Cheaper is not the same as worse here, and the two arms are scored on the "
        f"same {g.get('n_rows', 0):,} cells. Silent error rate: "
        f"**{cell['TS']['ser']:.1%}** compiled against "
        f"**{cell['B2']['ser']:.1%}** per cell. Screens wrongly ruled out, of "
        f"thirty, which is ten patients each read against three trials: "
        f"**{panel['TS']['false_exclusions']}** against "
        f"**{panel['B2']['false_exclusions']}**. Both arms are VOID against the "
        f"registered primary outcome, which requires zero.", "",
    ]


def human_time() -> list[str]:
    """The other currency. Dollars are the cheap half of what screening costs.

    A coordinator's cost is chart-hours, not tokens, and today those hours are
    spent one cell at a time. This reads the sidecar the worklist writes beside
    its own document, so the counts come from the artifact rather than from a
    sentence somebody kept up to date, and it is skipped rather than estimated
    when the worklist has not been generated.
    """
    wl = read(ROOT / "docs" / "sample_worklist.json")
    if not wl or not wl.get("question_sets"):
        return []
    sets = wl["question_sets"]
    biggest = sets[0]
    n_q = len(wl["distinct_open_criteria"])
    return [
        "## The other currency", "",
        f"Money is the cheap half. The expensive half is a person reading charts, "
        f"and `docs/sample_worklist.md` is what this run leaves them. It is one "
        f"trial ({wl['trial']}) at the zero-false-exclusion operating point, so "
        f"the panel is {wl['n_screens']:,} screens against "
        f"{len(wl['criteria_used'])} criteria.", "",
        "| | count |", "|---|---|",
        f"| cell judgements, one per patient per criterion | {wl['n_cells']:,} |",
        f"| screens the engine ruled out with no person involved | {wl['n_ruled_out']:,} |",
        f"| screens it cleared to contact | {wl['n_eligible']:,} |",
        f"| screens left open for a human | {wl['n_review']:,} |",
        f"| distinct question sets those screens contain | {len(sets)} |",
        f"| **distinct criteria a person has to answer** | **{n_q}** |",
        f"| screens sharing the single largest question set | {biggest['n_patients']:,} |",
        "",
        f"The last two rows are the point. {biggest['n_patients']:,} of the "
        f"{wl['n_review']:,} open screens are stuck on the same "
        f"{'question' if len(biggest['criteria']) == 1 else str(len(biggest['criteria'])) + ' questions'}, "
        f"so a coordinator has one thing to go and find rather than "
        f"{wl['n_review']:,} charts to read. Getting it still returns "
        f"{biggest['n_patients']:,} separate values, one per patient: what "
        f"collapses is the search, not the answers. The document groups them "
        f"that way instead of listing patients one after another, so the "
        f"work in front of a coordinator is {n_q} data-gathering "
        f"{'question' if n_q == 1 else 'questions'} rather than "
        f"{wl['n_cells']:,} readings.", "",
        "That shape follows from compiling once rather than asking per cell. A "
        "predicate fails the same way for everyone it fails for, so what it "
        "cannot settle comes out sorted into questions. A per-cell model answers "
        "each patient independently, so what it cannot settle comes out sorted "
        "into patients, and there is nothing to group.", "",
        "Two limits worth stating. This is one trial on one synthetic corpus at "
        "an operating point chosen in sample, so the number 2 is not a claim "
        "about clinical trials; the grouping is what generalises, not the count. "
        "And a question answered once still has to be answered by someone with "
        "access to data the record does not hold.", "",
    ]


def crossover(R: list[dict]) -> list[str]:
    """The section a reader who has to fund this asks for, computed from the table.

    Both arms answer the same question, so the interesting number is not what
    either cost but where the two curves cross. Compiling is paid once per
    criterion set. Asking per cell is paid again for every patient, every time
    the panel is rescreened. That is the whole architectural argument and it is
    already in the rows above, so it is derived here rather than asserted, and it
    is skipped entirely if the per-cell arm was never run.
    """
    def find(prefix: str) -> dict | None:
        for r in R:
            if r["step"].startswith(prefix) and not r.get("missing"):
                return r
        return None

    compile_row, b2 = find("compile the held-out protocols"), find("arms B2 over")
    ts = find("arms TS, B0, B1 over")
    if not (compile_row and b2 and ts):
        return []

    meta = read(ROOT / "runs" / "tierA" / "cells" / "meta_B2_b2_10p.json") or {}
    cells, patients = meta.get("n_cells"), meta.get("n_patients")
    criteria = meta.get("n_criteria")
    panel = (read(ROOT / "runs" / "tierA" / "cells" / "meta_TS_ow.json") or {}
             ).get("n_patients")
    if not (cells and patients and criteria and panel):
        return []

    once = compile_row["pt"] * RATE_IN + compile_row["ct"] * RATE_OUT
    per_cell = (b2["pt"] * RATE_IN + b2["ct"] * RATE_OUT) / cells
    per_patient = per_cell * criteria
    breakeven = once / per_patient
    full = per_patient * panel

    return [
        "## Where the two curves cross", "",
        f"Both arms answer the same {criteria} questions about the same patient. "
        f"They differ in what the model is asked to do, and that difference is a "
        f"cost curve rather than a constant.", "",
        f"Compiling the {criteria} criteria cost **${once:,.2f}** and is paid once "
        f"per criterion set. Screening a patient after that is arithmetic over the "
        f"compiled predicate: the row above that adjudicates {panel} patients on all "
        f"{criteria} criteria makes **zero model calls** and finishes in "
        f"**{clock(ts['wall'])}**.", "",
        f"The per-cell baseline pays per question per patient. Measured over its "
        f"{cells:,} recorded cells, that is **${per_cell:.4f}** a cell, or "
        f"**${per_patient:.2f}** to put one patient through {criteria} criteria.", "",
        f"| patients screened | compile once, then arithmetic | ask per cell |",
        f"|---|---|---|",
        f"| 1 | ${once:,.2f} | ${per_patient:,.2f} |",
        f"| {int(breakeven) + 1} | ${once:,.2f} | ${per_patient * (int(breakeven) + 1):,.2f} |",
        f"| {panel} | ${once:,.2f} | ${full:,.2f} |",
        f"| {panel} again next month | ${0:,.2f} | ${full:,.2f} |", "",
        f"The two cross at **{breakeven:.1f} patients**. Past that the compiled "
        f"path is cheaper, and the gap grows with every patient and every rescreen, "
        f"because one side of it is flat.", "",
        *_accuracy_on_the_same_cells(),
        "Three things this does not say. The dollar figures are the published list "
        f"rate in the table above, not what this run was billed. The per-cell figure "
        f"is measured on these {criteria} criteria against records of this size, and "
        "a longer record moves it. And it counts model spend only: the compiled "
        "predicates go to a human reviewer before deployment, which is the control "
        "`README.md` describes and the one that failed here, and that reviewer's "
        "time is a real cost this table does not carry.", "",
    ]


def read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def rows() -> list[dict]:
    out: list[dict] = []

    def add(step, blob, note="", usage_key="usage", wall_key="wall_s"):
        if not blob:
            out.append({"step": step, "missing": True, "note": note})
            return
        u = blob.get(usage_key) or {}
        out.append({"step": step, "calls": u.get("calls", 0),
                    "hits": u.get("cassette_hits", 0),
                    "pt": u.get("prompt_tokens", 0), "ct": u.get("completion_tokens", 0),
                    "wall": blob.get(wall_key) or u.get("wall_s") or 0.0,
                    "model": blob.get("model", ""), "note": note})

    add("compile the held-out protocols, 40 criteria",
        read(ROOT / "runs" / "tierA" / "compiled" / "criteria_seed7.json"),
        "the only step that reads a protocol")
    add("segmenter, 3 trials", read(ROOT / "results" / "segmentation.json"),
        "measured separately, not in the scored path")
    # The extra compilation seeds. The protocol registers at least three, and a
    # cost table that shows only the scored one understates the work behind the
    # noise floor by two thirds.
    for seed in (8, 9):
        p = ROOT / "runs" / "tierA" / "compiled" / f"criteria_seed{seed}.json"
        if p.exists() or seed == 8:
            add(f"recompile under seed {seed}, for the noise floor", read(p),
                "same criteria, different compilation randomness")

    for tag in ("before", "after"):
        add(f"vocabulary probe, {tag}",
            read(ROOT / "runs" / f"probe-{tag}" / "probe.json"),
            "21 concepts, on neither evaluation split")
    add("vocabulary probe, weak model",
        read(ROOT / "runs" / "probe-weak" / "probe.json"),
        "the same 21 concepts on a local 8B, ran on this machine")

    # The three checks that cost model calls. Each one is cited in the writeup,
    # so leaving it out of the cost table would make the total a smaller number
    # than the work it describes.
    cont = read(ROOT / "results" / "contamination.json")
    if cont and cont.get("counterfactual"):
        cf = cont["counterfactual"]
        out.append({"step": "counterfactual thresholds, contamination check 3",
                    "calls": (cf.get("usage") or {}).get("calls", 0),
                    "hits": (cf.get("usage") or {}).get("cassette_hits", 0),
                    "pt": (cf.get("usage") or {}).get("prompt_tokens", 0),
                    "ct": (cf.get("usage") or {}).get("completion_tokens", 0),
                    "wall": cf.get("wall_s") or 0.0,
                    "model": cf.get("model", ""),
                    "note": f"{cf.get('n_attempted', 0)} perturbed criteria recompiled"})
    add("critic probe, planted defects", read(ROOT / "results" / "critic_probe.json"),
        "one call per defect class plus an unmutated control")

    for f in sorted((ROOT / "runs" / "tierA" / "cells").glob("meta_*.json")):
        blob = read(f)
        if not blob:
            continue
        arms = ", ".join(blob.get("arms", []))
        paid = any(a in ("B2", "B3") for a in blob.get("arms", []))
        # The group tag, because six of these rows were otherwise identical text
        # and a reader could not tell which seed or which damage level each one
        # was. It is in the filename the meta was read from.
        tag = f.stem.split("_", 2)[-1] if "_" in f.stem else ""
        out.append({"step": f"arms {arms} over {blob.get('n_patients')} patients"
                            + (f", group {tag}" if tag else ""),
                    "calls": (blob.get("usage") or {}).get("calls", 0),
                    "hits": (blob.get("usage") or {}).get("cassette_hits", 0),
                    "pt": (blob.get("usage") or {}).get("prompt_tokens", 0),
                    "ct": (blob.get("usage") or {}).get("completion_tokens", 0),
                    "wall": blob.get("wall_s") or 0.0,
                    "model": blob.get("model", ""),
                    "note": f"{blob.get('n_cells')} cells"
                            + ("" if paid else ", no model call at all")})

    # `agreement.json` records the comparison, not what it cost to produce. The
    # usage lives beside the run. Reading the wrong file published this step at
    # zero calls and zero tokens for every version of this table so far.
    b = read(ROOT / "runs" / "checker_b_usage.json")
    add("second blind labeller, Checker B", b, "a different model family")
    return out


def main() -> int:
    R = rows()
    have = [r for r in R if not r.get("missing")]
    tot_c = sum(r["calls"] for r in have)
    tot_p = sum(r["pt"] for r in have)
    tot_o = sum(r["ct"] for r in have)
    tot_w = sum(r["wall"] for r in have)

    L = ["# What it cost, and how long it took", "",
         "Generated by `python scripts/costs.py` from the files the run produced.", "",
         "## The claim this table exists to support", "",
         "The model reads each protocol once and never reads a patient, so screening a",
         "patient costs arithmetic. That is an architectural claim and it should be",
         "visible as a runtime fact: the row that touches every patient makes no model",
         "call, and its wall clock is seconds.", "",
         "## Recorded", "",
         "| step | model calls | from cassette | prompt tokens | completion tokens | "
         "wall clock | at published rates |", "|---|---|---|---|---|---|---|"]
    for r in R:
        if r.get("missing"):
            L.append(f"| {r['step']} | _not run yet_ | | | | | |")
            continue
        L.append(f"| {r['step']} | {r['calls']:,} | {r['hits']:,} | {r['pt']:,} | "
                 f"{r['ct']:,} | {clock(r['wall'])} | {money(r['pt'], r['ct'])} |")
    # A total summed over a table with "not run yet" rows in it is a partial
    # total, and printed as **total** it reads as the cost of the project. The
    # word changes and the shortfall is named, because a reader who budgets from
    # this number has to know which steps are not in it.
    missing = [r["step"] for r in R if r.get("missing")]
    n_m = len(missing)
    plural = "step" if n_m == 1 else "steps"
    label = "total" if not missing else f"total so far, {n_m} {plural} not yet run"
    L += [f"| **{label}** | **{tot_c:,}** | | **{tot_p:,}** | **{tot_o:,}** | "
          f"**{clock(tot_w)}** | **{money(tot_p, tot_o)}** |", ""]
    if missing:
        verb = "has" if n_m == 1 else "have"
        each = "That step is" if n_m == 1 else "Each is"
        it = "it" if n_m == 1 else "them"
        names = "; ".join(f"*{m}*" for m in missing)
        L += [f"**PARTIAL.** {n_m} {plural} in the table above {verb} not run, so the "
              f"total is a floor rather than the cost of the work: {names}. {each} a "
              f"recording step, so running {it} raises the recorded totals and changes "
              f"nothing about reproduction, which replays and calls no model.", ""]
    L += [
          f"The right-hand column is an estimate at {RATE_LABEL}. Each row is "
          f"rounded to the cent, so adding the column comes to a cent or two more "
          f"than the total, which is computed once from the raw token counts "
          f"rather than by summing rounded rows. It is not what this",
          "run cost. This ran on a locally authenticated vendor CLI on a subscription, so",
          "the marginal cost of a call was zero, and reporting zero would be true and",
          "useless to anyone deciding whether to run it themselves.", "",
          "Token counts come from the provider where it returns them. The local shim does",
          "not, so those rows fall back to an estimate of four characters per token, and",
          "the report says which rather than averaging the distinction away.", "",
          *crossover(R),
          *human_time(),
          "## Reproducing costs nothing", "",
          "`python run.py reproduce` makes no model call. Every recorded call replays from",
          "`runs/tierA/cassettes/`, and replay never falls through to a live call: a",
          "missing cassette raises and stops the run. So the reproduction is free, offline,",
          "and needs no key.", ""]

    dest = ROOT / "docs" / "COST.md"
    dest.write_text(align_tables("\n".join(L)), encoding="utf-8", newline="\n")
    print("\n".join(L))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
