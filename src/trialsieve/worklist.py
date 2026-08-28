"""The artifact a coordinator opens.

Written for someone who has a screening list and forty minutes, not for someone
evaluating a system. Three rules shaped it:

* Nothing is asserted without a dated line from the record behind it. A ruled-out
  patient names the criterion, the value, and the resource that carried it.
* The survivors are ranked by how little is left to do, because the coordinator
  works down the list and the top of it should be the cheapest wins.
* It recommends nobody. Every open question is addressed to a human, and the
  document says so in the first paragraph rather than the last.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter
from typing import Any

from .chart import Chart
from .evaluator import screen


def build(compiled: list[dict], panel: list[Chart], trial: dict,
          unit_policy: str = "code_authoritative") -> dict:
    """Screen a panel and assemble the worklist data."""
    screens = []
    for ch in panel:
        s = screen(compiled, ch, unit_policy=unit_policy)
        s["age"] = ch.age
        s["sex"] = ch.sex
        screens.append(s)

    ruled_out = [s for s in screens if s["decision"] == "INELIGIBLE"]
    review = [s for s in screens if s["decision"] == "NEEDS_REVIEW"]
    eligible = [s for s in screens if s["decision"] == "ELIGIBLE"]
    review.sort(key=lambda s: (s["n_indeterminate"], -s["n_meets"], s["patient_id"]))
    ruled_out.sort(key=lambda s: s["patient_id"])

    reasons = Counter()
    for s in ruled_out:
        for c in s["criteria"]:
            if c["verdict"] == "FAILS":
                reasons[c["criterion_id"]] += 1

    open_questions = Counter()
    for s in review:
        for c in s["criteria"]:
            if c["verdict"] == "INDETERMINATE":
                open_questions[c["criterion_id"]] += 1

    return {"trial": trial, "screens": screens, "ruled_out": ruled_out,
            "review": review, "eligible": eligible,
            "ruleout_reasons": reasons, "open_questions": open_questions,
            "compiled": {c["criterion_id"]: c for c in compiled}}


def _cite(c: dict, limit: int = 2) -> str:
    ev = [e for e in c.get("evidence", []) if e.get("kind") != "absent"][:limit]
    if not ev:
        return c["reason"][:140]
    return "; ".join(f"{e['display']} = {e['value']}"
                     + (f" ({e['date']})" if e.get("date") else "") for e in ev)


def render_markdown(wl: dict, generated: str = "", reviewer: str = "",
                    max_listed: int = 25) -> str:
    t = wl["trial"]
    n = len(wl["screens"])
    ro, rv, el = wl["ruled_out"], wl["review"], wl["eligible"]
    L: list[str] = []

    L.append(f"# Prescreening worklist: {t.get('nct_id', '')}")
    L.append("")
    L.append(f"**{t.get('title', '')}**")
    L.append("")
    L.append(f"Panel of {n} patients screened on {generated or dt.date.today()}. "
             f"Compiled criteria signed off by {reviewer or 'UNSIGNED'}.")
    L.append("")
    L.append("> This list does not decide anything. It removes patients who are "
             "provably ineligible on a dated fact in their record, and it ranks "
             "everyone else by how much is left to check. Every remaining patient "
             "needs a human. Nobody is enrolled by this document.")
    L.append("")
    L.append("| | count | share |")
    L.append("|---|---|---|")
    L.append(f"| Ruled out, with evidence | {len(ro)} | {len(ro)/n:.0%} |")
    L.append(f"| Needs review | {len(rv)} | {len(rv)/n:.0%} |")
    L.append(f"| All checkable criteria met | {len(el)} | {len(el)/n:.0%} |")
    L.append("")
    L.append(f"The coordinator's list is {len(rv) + len(el)} patients rather than {n}.")
    L.append("")

    if wl["ruleout_reasons"]:
        L.append("## What removed people")
        L.append("")
        L.append("| criterion | patients removed | text |")
        L.append("|---|---|---|")
        for cid, cnt in wl["ruleout_reasons"].most_common():
            src = wl["compiled"].get(cid, {}).get("source_text", "")
            L.append(f"| `{cid}` | {cnt} | {src[:88]} |")
        L.append("")

    L.append("## Ruled out")
    L.append("")
    if not ro:
        L.append("Nobody was ruled out.")
    else:
        L.append("Each line names the criterion that removed the patient and the record "
                 "entry it read. A blank here would be an assertion; there are none.")
        L.append("")
        L.append("| patient | age | sex | failed criterion | evidence from the record |")
        L.append("|---|---|---|---|---|")
        for s in ro[:max_listed]:
            first = next(c for c in s["criteria"] if c["verdict"] == "FAILS")
            L.append(f"| `{s['patient_id'][:8]}` | {s['age']} | {s['sex']} | "
                     f"`{first['criterion_id']}` | {_cite(first)} |")
        if len(ro) > max_listed:
            L.append(f"\n_{len(ro) - max_listed} further ruled-out patients in the "
                     f"machine-readable output._")
    L.append("")

    L.append("## Needs review, cheapest first")
    L.append("")
    if not rv:
        L.append("No patients require review.")
    else:
        L.append("Ranked by how few questions remain. The questions are the ones the "
                 "record could not settle, written out so they can be answered without "
                 "reopening the chart from the beginning.")
        L.append("")
        for s in rv[:max_listed]:
            L.append(f"### `{s['patient_id'][:8]}`  ({s['age']}, {s['sex']}) "
                     f"- {s['n_indeterminate']} open, {s['n_meets']} already met")
            L.append("")
            for c in s["criteria"]:
                if c["verdict"] != "INDETERMINATE":
                    continue
                why = (c.get("unknown_because") or [c["reason"]])[0]
                L.append(f"- **{c['source_text'][:96]}**  \n  {why[:150]}")
            L.append("")
        if len(rv) > max_listed:
            L.append(f"_{len(rv) - max_listed} further patients in the machine-readable "
                     f"output._")
    L.append("")

    if wl["open_questions"]:
        L.append("## Where the review time goes")
        L.append("")
        L.append("| criterion | patients needing a human | text |")
        L.append("|---|---|---|")
        for cid, cnt in wl["open_questions"].most_common(12):
            src = wl["compiled"].get(cid, {}).get("source_text", "")
            L.append(f"| `{cid}` | {cnt} | {src[:88]} |")
        L.append("")
        L.append("A criterion at the top of this table is where an extra data feed, or a "
                 "single clarification with the sponsor, would buy the most time.")
    L.append("")
    return "\n".join(L) + "\n"


def summary_row(wl: dict) -> dict[str, Any]:
    n = len(wl["screens"])
    return {"nct_id": wl["trial"].get("nct_id"), "panel": n,
            "ruled_out": len(wl["ruled_out"]), "needs_review": len(wl["review"]),
            "eligible": len(wl["eligible"]),
            "reduction": round(len(wl["ruled_out"]) / n, 4) if n else 0.0}
