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
    """Screen a panel against ONE trial's criteria and assemble the worklist.

    The predicate list was used exactly as handed in, while the document was
    titled with one trial's id, so a worklist headed NCT06983054 ruled patients
    out on criteria belonging to the other two trials in the run. That is not a
    labelling slip. A patient removed from a trial they were never screened
    against is a false exclusion, which is the one error this system exists to
    prevent, and it is what made the shipped sample rule out 385 of 385.
    """
    nct = trial.get("nct_id", "")
    if nct:
        own = [c for c in compiled if str(c.get("criterion_id", "")).startswith(nct)]
        if not own:
            raise ValueError(
                f"no compiled criterion belongs to {nct}. Rendering every trial's "
                f"predicates under one trial's heading is what this guard exists to "
                f"stop, so this refuses rather than screening against the wrong list.")
        compiled = own

    used_ids = sorted(str(c.get("criterion_id", "")) for c in compiled)
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

    # What was actually applied, after the per-trial filter above, so a caller
    # cannot describe the document with the list it handed in.
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

    return {"trial": trial, "criteria_used": used_ids, "screens": screens, "ruled_out": ruled_out,
            "review": review, "eligible": eligible,
            "ruleout_reasons": reasons, "open_questions": open_questions,
            "compiled": {c["criterion_id"]: c for c in compiled}}


def _short(text: str, limit: int = 34) -> str:
    """A column heading from criterion prose, cut on a word rather than mid-token.

    Cutting at a fixed width turned "BMI: >25 kg/m2" into "BMI: >25 kg/m", which
    is a different criterion.
    """
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return (cut or text[:limit]) + "..."


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
    L.append(f"Panel of {n} patients screened on {generated or dt.date.today()}.")
    L.append("")
    if reviewer:
        L.append(f"Compiled criteria reviewed and signed by {reviewer}.")
    else:
        L.append("**NOT FOR USE.** No human has reviewed the compiled criteria behind "
                 "this document. It was produced with the sign-off gate overridden, "
                 "which is a thing you can only do on purpose.")
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

    # The one group this document counted in its summary and never printed. A
    # coordinator's first question is who can be contacted today, and the answer
    # was computed on line 54 and dropped on the floor. Printed first, in full,
    # because it is the shortest path from this panel to an enrolled patient.
    L.append("## Ready to contact")
    L.append("")
    if not el:
        L.append("No patient in this panel meets every applied criterion outright. "
                 "That is an ordinary result rather than a failure: most records "
                 "leave at least one question open, and those patients are below.")
    else:
        L.append(f"{len(el)} of {n} patients meet **every** criterion applied here, "
                 f"each on a dated fact already in the record, with nothing left "
                 f"open. Start here.")
        L.append("")
        # One column per criterion rather than every citation crushed into one
        # cell. These patients meet all of them by definition, so the columns are
        # the same for every row and the value under each is what a coordinator
        # is actually checking. Truncating a shared list mid-date read as a draft.
        cols = [c for c in el[0]["criteria"] if c["verdict"] == "MEETS"]
        if 1 <= len(cols) <= 6:
            head = " | ".join(_short(c["source_text"]) for c in cols)
            L.append(f"| patient | age | sex | {head} |")
            L.append("|---|---|---|" + "---|" * len(cols))
            for s in el[:max_listed]:
                by_id = {c["criterion_id"]: c for c in s["criteria"]}
                cells = " | ".join(_cite(by_id[c["criterion_id"]], 1)
                                   if c["criterion_id"] in by_id else "n/a"
                                   for c in cols)
                L.append(f"| `{s['patient_id'][:8]}` | {s['age']} | {s['sex']} | "
                         f"{cells} |")
        else:
            L.append("| patient | age | sex |")
            L.append("|---|---|---|")
            for s in el[:max_listed]:
                L.append(f"| `{s['patient_id'][:8]}` | {s['age']} | {s['sex']} |")
        if len(el) > max_listed:
            L.append("")
            L.append(f"_{len(el) - max_listed} further eligible patients in the "
                     f"machine-readable output._")
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
        # Grouped by the questions left open, not listed patient by patient.
        # Ranking alone put 190 patients on one rung and broke the tie on patient
        # id, so the top of the page was twenty identical rows in hash order.
        # A queue ordered by a hash is the thing this document exists to replace,
        # and the coordinator's real unit of work is the question, not the row:
        # one HbA1c result settles all 190 of them at once.
        groups: dict[tuple, list[dict]] = {}
        for s in rv:
            key = tuple(sorted(c["criterion_id"] for c in s["criteria"]
                               if c["verdict"] == "INDETERMINATE"))
            groups.setdefault(key, []).append(s)
        for key, members in sorted(groups.items(),
                                   key=lambda kv: (len(kv[0]), -len(kv[1]))):
            q = [c for c in members[0]["criteria"]
                 if c["verdict"] == "INDETERMINATE"]
            L.append(f"### {len(members)} patients, {len(q)} open")
            L.append("")
            for c in q:
                why = (c.get("unknown_because") or [c["reason"]])[0]
                L.append(f"- **{c['source_text'][:96]}**  \n  {why[:150]}")
            L.append("")
            if len(members) > 8:
                asked = ("question" if len(q) == 1
                         else f"{len(q)} questions")
                L.append(f"The same {asked} for all {len(members)}. Answered once, "
                         f"they resolve together.")
                L.append("")
            ids = ", ".join(f"`{s['patient_id'][:8]}` ({s['age']}, {s['sex']})"
                            for s in members[:12])
            more = (f" and {len(members) - 12} more in the machine-readable output"
                    if len(members) > 12 else "")
            L.append(f"{ids}{more}.")
            L.append("")
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
