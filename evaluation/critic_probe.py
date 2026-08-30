"""Does the critic catch a defect that is definitely there?

    python evaluation/critic_probe.py --run runs/tierA --provider shim

The critic returned OK on every predicate in the scored run. That reads two ways
and the difference matters: either the predicates are right, or the critic says OK
to anything. A component that never fires is indistinguishable from a component
that does nothing, and `docs/AGENT_DESIGN.md` calls this one "the falsifiable
agent", which is a claim that has to be paid for.

So each predicate is broken on purpose in a named way, the critic is asked to
review the broken version, and the catch rate is published per defect class.

**Both arms, or the number means nothing.** A critic that answered REVISE to
everything would score a perfect catch rate and be worthless. So every predicate
is also reviewed unmodified, and the false alarm rate on those is reported beside
the catch rate. The pair is the result; either alone is a number that can be won
by a broken component.

**The defect classes are the ones the critic's own prompt claims to look for**,
in its order: window errors, boundary errors, direction errors, absence errors.
Adding a class the prompt never mentions would be testing something else and
scoring it as a failure here.

**A caught defect has to be caught by execution, not by assertion.** The critic
returns a counterexample patient and a truth value; the harness builds that chart
and runs the predicate. A finding the engine does not confirm is recorded as
dismissed and does not count as a catch. That rule already lives in the critic and
this probe does not relax it.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.agents.critic import review  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402

# Importable as a module, not only runnable as a script: the tests import these.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _md_tables import align as align_tables

PROVIDERS = {
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}

FLIP_CMP = {">": ">=", ">=": ">", "<": "<=", "<=": "<", "==": "!=", "!=": "=="}


def _walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values():
            _walk(v, fn)
    elif isinstance(node, list):
        for v in node:
            _walk(v, fn)


def m_boundary(expr: dict) -> tuple[dict, str] | None:
    """`>` becomes `>=`. The patient exactly on the threshold changes side."""
    out = copy.deepcopy(expr)
    hit = []

    def fn(n):
        if not hit and n.get("op") == "compare" and n.get("cmp") in FLIP_CMP:
            hit.append((n["cmp"], FLIP_CMP[n["cmp"]]))
            n["cmp"] = FLIP_CMP[n["cmp"]]

    _walk(out, fn)
    return (out, f"comparison {hit[0][0]} became {hit[0][1]}") if hit else None


def m_threshold(expr: dict) -> tuple[dict, str] | None:
    """A threshold moves far enough that a different population qualifies."""
    out = copy.deepcopy(expr)
    hit = []

    def fn(n):
        if not hit and n.get("val") == "literal" and isinstance(n.get("number"), (int, float)):
            old = n["number"]
            new = round(old * 2.0, 3)
            if new != old:
                hit.append((old, new))
                n["number"] = new

    _walk(out, fn)
    return (out, f"threshold {hit[0][0]} became {hit[0][1]}") if hit else None


def m_window(expr: dict) -> tuple[dict, str] | None:
    """"Within 6 months" quietly becomes within 2 years."""
    out = copy.deepcopy(expr)
    hit = []

    def fn(n):
        if not hit and isinstance(n.get("within_days"), int) and n["within_days"] > 0:
            old = n["within_days"]
            hit.append((old, old * 4))
            n["within_days"] = old * 4

    _walk(out, fn)
    return (out, f"window {hit[0][0]} days became {hit[0][1]}") if hit else None


def m_direction(expr: dict) -> tuple[dict, str]:
    """The whole predicate is negated. An exclusion now fires for the wrong people."""
    return {"op": "not", "arg": copy.deepcopy(expr)}, "the whole predicate is negated"


def m_absence(expr: dict) -> tuple[dict, str] | None:
    """Silence in the record becomes proof of absence. The dangerous one."""
    out = copy.deepcopy(expr)
    hit = []

    def fn(n):
        if not hit and n.get("absent_means") == "unknown":
            hit.append(True)
            n["absent_means"] = "false"

    _walk(out, fn)
    return (out, "absent_means unknown became false") if hit else None


MUTATIONS = [
    ("boundary", m_boundary),
    ("threshold", m_threshold),
    ("window", m_window),
    ("direction", m_direction),
    ("absence", m_absence),
]


def cover(compiled: list[dict], limit: int) -> list[dict]:
    """Pick predicates so every defect class that can be planted anywhere is.

    The probe took the first `limit` compiled predicates in file order. Those six
    admit boundary, threshold and direction defects and admit neither a window
    defect nor an absence one, so two of the five classes were planted zero times
    and the summary still read "caught 9 of 9". Nothing was wrong with the
    arithmetic. The denominator simply never contained the cases.

    The class that went untested is the one this system's worst measured failure
    came from: `absent_means` deciding a verdict on a fact the record does not
    contain. One criterion produced 358 of 424 wrong exclusions that way, and
    entry 30 of the improvement changelog is the repair. Three predicates admit
    that mutation and none of them were in the first six.

    Greedy set cover over the classes, rarest first, then file order to fill the
    remainder. Deterministic, and it states why each predicate is in the set.
    """
    applies = {}
    for c in compiled:
        applies[c["criterion_id"]] = {
            name for name, fn in MUTATIONS
            if fn(copy.deepcopy(c["expr"])) is not None}

    # Rarest class first, so a predicate that is the only home of a mutation is
    # picked before the limit is spent on one that three others also cover.
    scarcity = Counter()
    for names in applies.values():
        for n in names:
            scarcity[n] += 1

    picked: list[dict] = []
    covered: set[str] = set()
    by_id = {c["criterion_id"]: c for c in compiled}
    for name, _ in sorted(MUTATIONS, key=lambda m: scarcity.get(m[0], 0)):
        if name in covered or not scarcity.get(name):
            continue
        if len(picked) >= limit:
            break
        best = max((c for c in compiled if name in applies[c["criterion_id"]]
                    and c not in picked),
                   key=lambda c: len(applies[c["criterion_id"]] - covered),
                   default=None)
        if best is None:
            continue
        picked.append(best)
        covered |= applies[best["criterion_id"]]

    # Whatever budget is left goes to the least-tested classes rather than to file
    # order. Covering absence once is the difference between a class that has been
    # tested and a class that has been tried, and absence is the one the system's
    # worst failure came from, so a spare slot is worth more there than on a fifth
    # predicate that admits the same three common mutations as the first four.
    tried = Counter()
    for c in picked:
        for n in applies[c["criterion_id"]]:
            tried[n] += 1
    while len(picked) < limit:
        chosen = {x["criterion_id"] for x in picked}
        rest = [c for c in compiled if c["criterion_id"] not in chosen]
        if not rest:
            break
        best = min(rest, key=lambda c: (
            min((tried[n] for n in applies[c["criterion_id"]]), default=10**6),
            -len(applies[c["criterion_id"]]),
            compiled.index(c)))
        picked.append(best)
        for n in applies[best["criterion_id"]]:
            tried[n] += 1
    return [by_id[c["criterion_id"]] for c in picked[:limit]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--provider", default="shim", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--limit", type=int, default=6,
                    help="predicates to mutate. Each costs one model call per "
                         "applicable defect class, plus one control.")
    ap.add_argument("--out", default="docs/CRITIC_PROBE.md")
    a = ap.parse_args()

    run = Path(a.run)
    src = run / "compiled" / f"criteria_seed{a.seed}.json"
    if not src.exists():
        print(f"no compiled predicates at {src}", file=sys.stderr)
        return 2
    compiled = cover([c for c in json.loads(src.read_text(encoding="utf-8"))["criteria"]
                      if c.get("compilable")], a.limit)
    if not compiled:
        print("nothing compiled to mutate", file=sys.stderr)
        return 2

    base_url, default_model = PROVIDERS[a.provider]
    client = Client(provider="openai", model=a.model or default_model, mode=a.mode,
                    cassette_dir=run / "cassettes_critic_probe", base_url=base_url)

    rows, t0 = [], time.time()

    def ask(rec: dict, tag: str) -> dict:
        traj = Trajectory("critic_probe", f"{rec['criterion_id']}--{tag}")
        try:
            out, traj = review(client, rec, traj)
        except Exception as exc:
            out = {"verdict": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
            traj.final(**out)
        traj.write(run / "trajectories")
        return out

    for rec in compiled:
        control = ask(rec, "control")
        rows.append({"criterion_id": rec["criterion_id"], "defect": "none (control)",
                     "detail": "the predicate as compiled",
                     "verdict": control.get("verdict"),
                     "confirmed": bool(control.get("executed", {}) or {}),
                     "correct": control.get("verdict") == "OK"})
        print(f"  {rec['criterion_id']:22s} control    {control.get('verdict')}", flush=True)

        for name, fn in MUTATIONS:
            got = fn(rec["expr"])
            if got is None:
                rows.append({"criterion_id": rec["criterion_id"], "defect": name,
                             "detail": "not applicable to this predicate",
                             "verdict": "n/a", "correct": None})
                continue
            broken_expr, detail = got
            broken = dict(rec, expr=broken_expr)
            out = ask(broken, name)
            caught = out.get("verdict") == "REVISE"
            rows.append({"criterion_id": rec["criterion_id"], "defect": name,
                         "detail": detail, "verdict": out.get("verdict"),
                         "correct": caught,
                         "engine_confirmed": bool(out.get("executed"))})
            print(f"  {rec['criterion_id']:22s} {name:10s} "
                  f"{out.get('verdict')}{'  CAUGHT' if caught else ''}", flush=True)

    tested = [r for r in rows if r["correct"] is not None]
    defects = [r for r in tested if r["defect"] != "none (control)"]
    controls = [r for r in tested if r["defect"] == "none (control)"]
    caught = sum(1 for r in defects if r["correct"])
    false_alarms = sum(1 for r in controls if not r["correct"])
    by_class = Counter()
    tot_class = Counter()
    for r in defects:
        tot_class[r["defect"]] += 1
        by_class[r["defect"]] += 1 if r["correct"] else 0

    L = ["# Does the critic catch a defect that is definitely there?", "",
         "Generated by `python evaluation/critic_probe.py`. Output, not illustration.", "",
         "The critic returned OK on every predicate in the scored run. That reads two",
         "ways, and a component that never fires is indistinguishable from one that does",
         "nothing. So each predicate was broken on purpose in a named way and reviewed",
         "again.", "",
         f"| | |", "|---|---|",
         f"| defects planted | {len(defects)} |",
         f"| caught | **{caught}** |",
         f"| controls, reviewed unmodified | {len(controls)} |",
         f"| false alarms on controls | **{false_alarms}** |", "",
         "Both numbers or neither. A critic that answered REVISE to everything would",
         "catch every defect and be worthless, and the control column is the only thing",
         "that separates the two.", "",]

    # Every probe trajectory in the tree, not only the run this table scores. An
    # earlier and wider probe left its logs here and its numbers were never
    # published, and one of them is an `absence` miss, so reporting the scored run
    # alone makes the critic look better in the one class it is weak in. Counted
    # from the files rather than described, so it cannot drift from them.
    traj = run / "trajectories" / "critic_probe"
    disk: dict[str, list[int]] = {}
    disk_ids = set()
    for f in sorted(traj.glob("*.jsonl")) if traj.is_dir() else []:
        crit, defect = f.stem.split("--")
        disk_ids.add(crit)
        finals = [e for e in (json.loads(x) for x in
                              f.read_text(encoding="utf-8").split(chr(10)) if x.strip())
                  if e.get("event") == "final"]
        if not finals:
            continue
        n = finals[-1].get("n_findings", 0)
        right = (n == 0) if defect == "control" else (n >= 1)
        row = disk.setdefault(defect, [0, 0])
        row[0] += 1
        row[1] += int(right)
    scored_ids = {r["criterion_id"] for r in rows}
    extra = sorted(disk_ids - scored_ids)
    if extra and disk:
        planted_d = sum(v[0] for k, v in disk.items() if k != "control")
        caught_d = sum(v[1] for k, v in disk.items() if k != "control")
        ctrl_d = disk.get("control", [0, 0])
        absence_d = disk.get("absence", [0, 0])
        L += [f"**Every probe in this tree, which is more than this table scores.** "
              f"The table above is one run: {len(scored_ids)} predicates, "
              f"{len(defects)} applicable mutations, {len(controls)} controls, "
              f"regenerated from the recorded cassettes. An earlier and wider probe "
              f"ran before it and its logs were kept when its numbers were not "
              f"published, so `{traj.as_posix()}/` holds "
              f"{sum(v[0] for v in disk.values())} trajectories across "
              f"{len(disk_ids)} predicates. Counting every one of them:", ""]
        L += ["| defect | planted, every probe | caught |", "|---|---|---|"]
        for name, _ in MUTATIONS:
            if name in disk:
                L.append(f"| {name} | {disk[name][0]} | {disk[name][1]} |")
        L += ["",
              f"That is **{caught_d} of {planted_d}** planted defects and "
              f"{ctrl_d[0] - ctrl_d[1]} false alarm on {ctrl_d[0]} controls. The "
              f"difference that matters is `absence`: {absence_d[1]} of "
              f"{absence_d[0]} across every probe against {by_class['absence']} of "
              f"{tot_class['absence']} in the scored run, because one of the "
              f"predicates outside that run is an absence miss. **The wider figure "
              f"is the one to hold this component to.** The scored run is kept "
              f"because it is the one that regenerates from cassettes, and the "
              f"extra predicates are "
              f"{', '.join('`' + e + '`' for e in extra)}.", ""]

    L += [
         "## By defect class", "",
         "These are the classes the critic's own prompt says it looks for, in its order.", "",
         "| defect | planted | caught |", "|---|---|---|"]
    # Every class gets a row, including the ones nothing was planted for. Omitting
    # them left a table of three rows under a headline of "9 of 9", and a reader
    # had no way to see that two of the five classes had never been tried. A ratio
    # cannot report a class that is missing from its denominator.
    never = [n for n, _ in MUTATIONS if not tot_class[n]]
    for name, _ in MUTATIONS:
        if tot_class[name]:
            L.append(f"| {name} | {tot_class[name]} | {by_class[name]} |")
        else:
            L.append(f"| {name} | **0, never planted** | n/a |")
    # A reader should not have to do the division. "16 of 18" reads as a clean
    # sweep, and it is one class at one in three sitting under fifteen of fifteen.
    scored = [(n, by_class[n], tot_class[n]) for n, _ in MUTATIONS if tot_class[n]]
    if len(scored) > 1:
        weakest = min(scored, key=lambda x: (x[1] / x[2], -x[2]))
        rest_c = sum(c for n, c, _ in scored if n != weakest[0])
        rest_t = sum(x for n, _, x in scored if n != weakest[0])
        if weakest[1] < weakest[2] and rest_c == rest_t:
            L += ["", f"**Every class but one is caught every time.** The critic "
                      f"catches {rest_c} of {rest_t} planted defects across "
                      f"{len(scored) - 1} classes and "
                      f"**{weakest[1]} of {weakest[2]}** in the `{weakest[0]}` class, which is "
                      f"{disk.get(weakest[0], [0, 0])[1]} of "
                      f"{disk.get(weakest[0], [0, 0])[0]} counting every probe in "
                      f"the tree. "
                      f"That is not a rounding difference and it is not the class it "
                      f"would be convenient to be weak in: `absence` is silence in the "
                      f"record becoming proof of absence, which is the defect that "
                      f"produced 358 of the 424 wrong exclusions in the run this probe "
                      f"was first written against, and entry 30 of the "
                      f"improvement changelog is the repair. "
                      f"The critic passed the real one, and planting it deliberately "
                      f"says the miss is a property of the reviewer rather than bad "
                      f"luck on one predicate."]
    if never:
        L += ["", f"**{len(never)} of {len(MUTATIONS)} classes were never planted**: "
                  f"{', '.join(never)}. No predicate in the selection admits the "
                  f"mutation, so the catch rate above says nothing about "
                  f"{'them' if len(never) > 1 else 'it'}. `cover()` picks the "
                  f"selection to exercise every class that is plantable anywhere in "
                  f"the compiled set, so a class still listed here is one no "
                  f"compiled predicate can carry."]
    L += ["", "## Every case", "",
          "| criterion | defect | what was changed | critic | right answer? |",
          "|---|---|---|---|---|"]
    for r in rows:
        mark = {True: "yes", False: "**no**", None: "not applicable"}[r["correct"]]
        L.append(f"| `{r['criterion_id']}` | {r['defect']} | {r['detail']} | "
                 f"{r['verdict']} | {mark} |")
    L.append("")

    out_p = Path(a.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(align_tables("\n".join(L)), encoding="utf-8", newline="\n")
    js = ROOT / "results" / "critic_probe.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(
        {"model": client.model, "n_defects": len(defects), "n_caught": caught,
         "n_controls": len(controls), "n_false_alarms": false_alarms,
         "by_class": {k: [by_class[k], tot_class[k]] for k, _ in MUTATIONS},
         "classes_never_planted": never,
         "usage": client.usage.as_dict(), "wall_s": round(time.time() - t0, 1),
         "rows": rows}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\ncaught {caught} of {len(defects)} planted defects, "
          f"{false_alarms} false alarms on {len(controls)} controls")
    if never:
        print(f"NOT MEASURED: {len(never)} of {len(MUTATIONS)} defect classes were "
              f"never planted ({', '.join(never)}), so the rate above does not "
              f"cover them")
    print(f"wrote {out_p} and {js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
