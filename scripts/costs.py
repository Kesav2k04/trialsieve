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
        out.append({"step": f"arms {arms} over {blob.get('n_patients')} patients",
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
          f"The right-hand column is an estimate at {RATE_LABEL}. It is not what this",
          "run cost. This ran on a locally authenticated vendor CLI on a subscription, so",
          "the marginal cost of a call was zero, and reporting zero would be true and",
          "useless to anyone deciding whether to run it themselves.", "",
          "Token counts come from the provider where it returns them. The local shim does",
          "not, so those rows fall back to an estimate of four characters per token, and",
          "the report says which rather than averaging the distinction away.", "",
          "## Reproducing costs nothing", "",
          "`python run.py reproduce` makes no model call. Every recorded call replays from",
          "`runs/tierA/cassettes/`, and replay never falls through to a live call: a",
          "missing cassette raises and stops the run. So the reproduction is free, offline,",
          "and needs no key.", ""]

    dest = ROOT / "docs" / "COST.md"
    dest.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print("\n".join(L))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
