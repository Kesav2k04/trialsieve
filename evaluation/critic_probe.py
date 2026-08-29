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
    compiled = [c for c in json.loads(src.read_text(encoding="utf-8"))["criteria"]
                if c.get("compilable")][:a.limit]
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
         "that separates the two.", "",
         "## By defect class", "",
         "These are the classes the critic's own prompt says it looks for, in its order.", "",
         "| defect | planted | caught |", "|---|---|---|"]
    for name, _ in MUTATIONS:
        if tot_class[name]:
            L.append(f"| {name} | {tot_class[name]} | {by_class[name]} |")
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
    out_p.write_text("\n".join(L), encoding="utf-8", newline="\n")
    js = ROOT / "results" / "critic_probe.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(
        {"model": client.model, "n_defects": len(defects), "n_caught": caught,
         "n_controls": len(controls), "n_false_alarms": false_alarms,
         "by_class": {k: [by_class[k], tot_class[k]] for k in tot_class},
         "usage": client.usage.as_dict(), "wall_s": round(time.time() - t0, 1),
         "rows": rows}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\ncaught {caught} of {len(defects)} planted defects, "
          f"{false_alarms} false alarms on {len(controls)} controls")
    print(f"wrote {out_p} and {js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
