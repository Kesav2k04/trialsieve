"""Can the grounder find a code the site does have, given the concept's real name?

    python evaluation/vocab_probe.py --run runs/probe-v0 --provider shim

This measures one thing and it is not on either evaluation split. Each probe is a
code that is definitely present in this corpus, paired with the name a protocol
would use for the concept. The grounder is given the name and has to return the
code. Nothing here comes from a trial's criterion text, so a prompt change
measured on it is not a prompt change fitted to the answer sheet.

Why it exists. Source systems label codes however they like. This corpus displays
SNOMED 44054006, which is `Diabetes mellitus type 2 (disorder)`, as the single
word `Diabetes`, and displays 59621000, `Essential hypertension`, as
`Hypertension`. A grounder that reads the display and ignores the code will reject
both as too vague, refuse the criterion, and look conservative while being wrong.
A grounder that trusts the code too readily will accept anything.

So the probe set contains both. `gap` entries are ones where the display is
narrower, broader, or differently worded than the concept. `control` entries are
ones where display and concept already agree, and a fix that starts failing those
has traded one error for another. `absent` entries are concepts this corpus really
does not code, where the correct answer is to return nothing.
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

# name the protocol would use, domain, acceptable codes, class, why it is here
#
# `acceptable` is a set, not an answer. A concept can have more than one defensible
# code in a vocabulary, and a probe that demanded one exact code would score a
# correct-but-different choice as a failure and then get "fixed" by a prompt change
# that made the grounder less careful. So a gap or control probe is right when it
# returns a non-empty subset of the acceptable codes, and an absent probe is right
# when it returns nothing.
PROBES = [
    # -- the display is not the concept's name -------------------------------
    ("Type 2 diabetes mellitus", "condition", ["44054006"], "gap",
     "SNOMED 44054006 is Diabetes mellitus type 2; this corpus displays it as 'Diabetes'"),
    ("Essential hypertension", "condition", ["59621000"], "gap",
     "SNOMED 59621000 is Essential hypertension; displayed here as 'Hypertension'"),
    ("Obesity", "condition", ["162864005", "408512008"], "gap",
     "displayed as 'Body mass index 30+ - obesity (finding)'; either obesity code is fine"),
    ("Diabetic nephropathy", "condition", ["127013003"], "gap",
     "displayed as 'Diabetic renal disease (disorder)'"),
    ("Glycated haemoglobin", "observation", ["4548-4"], "gap",
     "the corpus display uses the American spelling and the full LOINC long name"),
    ("Estimated glomerular filtration rate", "observation", ["33914-3"], "gap",
     "displayed as 'Glomerular filtration rate/1.73 sq M.predicted'"),
    ("Urine albumin to creatinine ratio", "observation", ["14959-1"], "gap",
     "displayed as 'Microalbumin Creatinine Ratio'; 1751-7 is serum albumin, not a ratio"),
    ("Haemodialysis", "procedure", ["265764009", "302497006"], "gap",
     "both are dialysis procedure codes in this vocabulary; either is acceptable"),
    ("Metformin", "medication", ["860975"], "gap",
     "the display is a full product string with strength and release profile"),

    # -- controls, where display and concept already agree -------------------
    ("Prediabetes", "condition", ["15777000"], "control", "display matches exactly"),
    ("Anaemia", "condition", ["271737000"], "control", "display matches but for spelling"),
    ("Hydrochlorothiazide", "medication", ["310798"], "control", "ingredient is in the display"),
    ("Simvastatin", "medication", ["314231", "312961"], "control",
     "two strengths of the same ingredient; both are the drug"),
    ("Systolic blood pressure", "observation", ["8480-6"], "control", "display matches"),

    # -- genuinely absent, where returning nothing is the right answer -------
    ("Acute pancreatitis", "condition", [], "absent",
     "no pancreatitis code appears anywhere in this corpus"),
    ("Gastroparesis", "condition", [], "absent", "no gastroparesis code in this corpus"),
    ("Metoprolol", "medication", [], "absent", "no metoprolol product in this corpus"),
    ("Oral glucose tolerance test", "observation", [], "absent",
     "no OGTT code; a plain serum glucose is a different measurement"),
]

PROVIDERS = {
    "shim": ("http://127.0.0.1:8100/v1", "gpt-5.6-terra"),
    "gemini": ("http://127.0.0.1:8101/v1", "gemini-2.5-flash"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}


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

    rows = []
    t0 = time.time()
    for i, (name, domain, expect, cls, why) in enumerate(PROBES, 1):
        traj = Trajectory("vocab_probe", f"{cls}-{name.replace(' ', '_')[:40]}")
        try:
            got = ground(client, name, domain,
                         intent="as a trial protocol would mean it", traj=traj)
            codes = sorted(got.get("codes", []))
        except Exception as exc:
            traj.final(error=f"{type(exc).__name__}: {exc}")
            codes = None
        traj.write(run / "trajectories")

        want = sorted(expect)
        if codes is None:
            correct = over = under = False
        elif cls == "absent":
            correct = codes == []
            over = bool(codes)
            under = False
        else:
            over = bool(set(codes) - set(want))
            under = not codes
            correct = bool(codes) and not over
        rows.append({"concept": name, "domain": domain, "class": cls, "why": why,
                     "expected": want, "got": codes, "correct": correct,
                     "over_accepted": over, "under_accepted": under})
        mark = ("ok  " if correct else "ERR " if codes is None
                else "OVER" if over else "MISS")
        print(f"  [{i:2d}/{len(PROBES)}] {mark} {cls:8s} {name[:38]:40s} "
              f"want {want} got {codes}", flush=True)

    out = run / "probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = score(rows)
    n_ok = sum(1 for r in rows if r["correct"])
    out.write_text(json.dumps({"model": client.model, "provider": a.provider,
                               "n": len(rows), "correct": n_ok,
                               "by_class": summary,
                               "usage": client.usage.as_dict(),
                               "wall_s": round(time.time() - t0, 1),
                               "rows": rows}, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"\n{n_ok}/{len(rows)} exactly right")
    print(json.dumps(summary, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
