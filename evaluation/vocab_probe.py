"""Can the grounder find a code the site does have, given the concept's real name?

    python evaluation/vocab_probe.py --run runs/probe-v1 --provider shim

This measures one thing and it is not on either evaluation split. Each probe is a
concept paired with the codes this corpus actually uses for it, if any. The
grounder is given the name a protocol would write and has to return the codes.
Nothing here comes from a trial's criterion text, so a prompt change measured on
it is not a prompt change fitted to the answer sheet.

Why it exists. Source systems label codes however they like, and they code at
whatever grain they were built for. This corpus displays SNOMED 44054006, which
is `Diabetes mellitus type 2 (disorder)`, as the single word `Diabetes`, and
displays 59621000, `Essential hypertension`, as `Hypertension`. A grounder that
reads the display and ignores the code rejects both as too vague, refuses the
criterion, and looks conservative while being wrong. A grounder that trusts every
code rejects nothing and clears patients on evidence it does not have.

Four classes, and the third is the interesting one.

`gap`      the display is worded differently from the concept, and the code is
           still an exact match. Expected in `codes`.
`control`  display and concept already agree. A change that starts failing these
           has traded one error for another.
`broader`  the site codes the concept only at a coarser grain. Expected in
           `broader_codes` and NOT in `codes`, because presence cannot settle the
           criterion and absence still can.
`absent`   the concept is not in this vocabulary at any grain. Both lists empty.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.agents.grounder import ground  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402


def P(name, domain, cls, codes=(), broader=(), why=""):
    return {"concept": name, "domain": domain, "class": cls,
            "codes": sorted(codes), "broader": sorted(broader), "why": why}


#: `codes` and `broader` hold sets of acceptable answers, not single answers. A
#: concept can have more than one defensible code in a vocabulary, and a probe
#: that demanded one exact code would score a correct-but-different choice as a
#: failure and then get "fixed" by a prompt change that made the grounder less
#: careful.
PROBES = [
    # -- the display is worded differently, the code is still exact -----------
    P("Essential hypertension", "condition", "gap", codes=["59621000"],
      why="SNOMED 59621000 is Essential hypertension; displayed here as 'Hypertension'"),
    P("Obesity", "condition", "gap", codes=["162864005", "408512008"],
      why="displayed as 'Body mass index 30+ - obesity (finding)'"),
    P("Diabetic nephropathy", "condition", "gap", codes=["127013003"],
      why="displayed as 'Diabetic renal disease (disorder)'"),
    P("Glycated haemoglobin", "observation", "gap", codes=["4548-4"],
      why="British spelling against an American display and the full LOINC long name"),
    P("Estimated glomerular filtration rate", "observation", "gap", codes=["33914-3"],
      why="displayed as 'Glomerular filtration rate/1.73 sq M.predicted'"),
    P("Urine albumin to creatinine ratio", "observation", "gap", codes=["14959-1"],
      why="displayed as 'Microalbumin Creatinine Ratio'"),
    P("Haemodialysis", "procedure", "gap", codes=["265764009", "302497006"],
      why="two dialysis procedure codes here; either is a defensible answer"),
    P("Metformin", "medication", "gap", codes=["860975"],
      why="the display is a full product string with strength and release profile"),

    # -- controls, where display and concept already agree -------------------
    P("Prediabetes", "condition", "control", codes=["15777000"], why="display matches"),
    P("Anaemia", "condition", "control", codes=["271737000"],
      why="display matches but for the spelling"),
    P("Hydrochlorothiazide", "medication", "control", codes=["310798"],
      why="the ingredient is in the display"),
    P("Simvastatin", "medication", "control", codes=["314231", "312961"],
      why="two strengths of one ingredient; both are the drug"),
    P("Systolic blood pressure", "observation", "control", codes=["8480-6"],
      why="display matches"),

    # -- the site codes it, at a coarser grain than the criterion needs ------
    P("Type 2 diabetes mellitus", "condition", "broader", broader=["44054006"],
      why="every diabetes diagnosis here is one unspecified code; presence cannot "
          "establish the type and absence still rules the patient out"),
    P("Type 1 diabetes mellitus", "condition", "broader", broader=["44054006"],
      why="the same single code, and the same argument, for the other type"),

    # -- genuinely absent at any grain ---------------------------------------
    P("Acute pancreatitis", "condition", "absent",
      why="no pancreatitis code appears anywhere in this corpus"),
    P("Gastroparesis", "condition", "absent", why="no gastroparesis code in this corpus"),
    P("Metoprolol", "medication", "absent", why="no metoprolol product in this corpus"),
    P("Oral glucose tolerance test", "observation", "absent",
      why="no OGTT code; a plain serum glucose is a different measurement"),
]

PROVIDERS = {
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}


def judge(probe: dict, codes: list[str] | None, broader: list[str] | None) -> dict:
    """Score one probe, and give the table a one-word label."""
    if codes is None:
        return {"correct": False, "over_accepted": False, "under_accepted": False,
                "mark": "ERR "}
    broader = broader or []
    cls = probe["class"]

    if cls == "absent":
        ok = not codes and not broader
        return {"correct": ok, "over_accepted": bool(codes or broader),
                "under_accepted": False, "mark": "ok  " if ok else "OVER"}

    if cls == "broader":
        # The right answer puts nothing in `codes` and the coarse code in
        # `broader_codes`. Putting it in `codes` is the dangerous failure: a
        # coarse code treated as exact manufactures MEETS verdicts for a
        # criterion the record cannot settle.
        if codes:
            return {"correct": False, "over_accepted": True, "under_accepted": False,
                    "mark": "EXACT"}
        ok = bool(broader) and not set(broader) - set(probe["broader"])
        return {"correct": ok,
                "over_accepted": bool(set(broader) - set(probe["broader"])),
                "under_accepted": not broader,
                "mark": "ok  " if ok else ("MISS" if not broader else "OVER")}

    over = bool(set(codes) - set(probe["codes"]))
    ok = bool(codes) and not over
    return {"correct": ok, "over_accepted": over, "under_accepted": not codes,
            "mark": "ok  " if ok else ("OVER" if over else "MISS")}


def score(rows: list[dict]) -> dict:
    by_class: dict[str, Counter] = {}
    for r in rows:
        c = by_class.setdefault(r["class"], Counter())
        c["n"] += 1
        c["correct"] += 1 if r["correct"] else 0
        c["over"] += 1 if r["over_accepted"] else 0
        c["under"] += 1 if r["under_accepted"] else 0
    return {k: dict(v) for k, v in sorted(by_class.items())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/probe")
    ap.add_argument("--provider", default="shim", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    a = ap.parse_args()

    base_url, default_model = PROVIDERS[a.provider]
    run = Path(a.run)
    client = Client(provider="openai", model=a.model or default_model, mode=a.mode,
                    cassette_dir=run / "cassettes", base_url=base_url)

    rows, t0 = [], time.time()
    for i, probe in enumerate(PROBES, 1):
        traj = Trajectory("vocab_probe",
                          f"{probe['class']}-{probe['concept'].replace(' ', '_')[:40]}")
        codes = broader = None
        status = "ERROR"
        try:
            got = ground(client, probe["concept"], probe["domain"],
                         intent="as a trial protocol would mean it", traj=traj)
            codes = sorted(got.get("codes", []))
            broader = sorted(got.get("broader_codes", []) or [])
            status = got.get("status", "")
        except Exception as exc:
            traj.final(error=f"{type(exc).__name__}: {exc}")
        traj.write(run / "trajectories")

        v = judge(probe, codes, broader)
        rows.append({**probe, "got_codes": codes, "got_broader": broader,
                     "status": status,
                     **{k: v[k] for k in ("correct", "over_accepted", "under_accepted")}})
        print(f"  [{i:2d}/{len(PROBES)}] {v['mark']} {probe['class']:8s} "
              f"{probe['concept'][:36]:38s} codes {codes} broader {broader}", flush=True)

    summary = score(rows)
    n_ok = sum(1 for r in rows if r["correct"])
    out = run / "probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"model": client.model, "provider": a.provider, "n": len(rows), "correct": n_ok,
         "scoring_rule": "gap and control: a non-empty subset of the acceptable codes. "
                         "broader: nothing in codes, a non-empty subset of the acceptable "
                         "broader codes. absent: both lists empty.",
         "by_class": summary, "usage": client.usage.as_dict(),
         "wall_s": round(time.time() - t0, 1), "rows": rows}, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    print(f"\n{n_ok}/{len(rows)} correct")
    print(json.dumps(summary, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
