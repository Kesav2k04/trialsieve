"""Checker B: a second, blind labeller.

    python evaluation/checker_b.py --sample 180 --provider gemini --mode record
    python evaluation/checker_b.py --report

Gold labels authored by one route are gold labels with one route's blind spots in
them. Checker B exists so that the disagreement between two independent routes can
be published as a label noise floor, and any measured difference smaller than that
floor can be called uninterpretable instead of reported as a finding.

What B sees: the criterion prose, and the patient's record flattened into a table.
That is all. It does not see the compiled IR, Checker A's predicate, Checker A's
label, or any system output. It runs on a different model family from the one that
compiles predicates, so a shared failure of one model cannot manufacture agreement.

What B does not do: adjudicate. Where A and B disagree, the disagreement is
recorded and a human resolves it, with arm identity stripped and case order
shuffled. B is a second opinion, not a tiebreaker.

Blindness is a git fact. These labels are committed before any commit containing
system output, so the ordering is checkable rather than promised.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))

import plainview  # noqa: E402
from criteria_set import CRITERIA  # noqa: E402
from trialsieve.agents.common import ask_json  # noqa: E402
from trialsieve.chart import load_panel  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402

OUT = ROOT / "evaluation" / "checker_b"
LABELS = OUT / "labels.jsonl"
SAMPLE = OUT / "sample.json"

PROMPT_VERSION = "checker-b-v1"

INSTRUCTIONS = """\
You decide whether one patient meets one clinical trial eligibility criterion,
using only the record you are shown.

There are three answers and the third one matters most.

MEETS          the record shows the criterion is satisfied
FAILS          the record shows the criterion is not satisfied
INDETERMINATE  the record does not settle it

Choose INDETERMINATE whenever the deciding fact is absent, is older than a window
the criterion specifies, or is recorded in a form you cannot convert with
confidence. An absent test result is not a normal test result. A patient with no
HbA1c on file has not been shown to have an HbA1c below any threshold.

Do not reason about what is likely. A record that does not mention smoking is not
a record of a non-smoker. Judge only what is written down.

Some criteria cannot be answered from a record at all: willingness to consent,
ability to attend visits, contraception intentions, enrolment in another study.
Answer INDETERMINATE for those and say so in the reason.

Units in this record are as the source system stored them. Convert only when you
are certain of the factor. If you are not, that is INDETERMINATE.
"""

TASK = """\
Criterion ({kind}): {text}

Patient record, as of {index_date}:

{record}

Return JSON only:
{{"label": "MEETS" | "FAILS" | "INDETERMINATE",
  "reason": "one sentence naming the specific value or the specific absence"}}
"""


# ---------------------------------------------------------------- rendering ---

def render_record(p: dict, max_labs_per_code: int = 2, max_rows: int = 60) -> str:
    """The patient as a table, criterion-agnostic.

    Deliberately not filtered to what the criterion asks about. Filtering would
    hand the labeller the answer to the hardest part of the task, which is
    noticing that the deciding fact is not there.

    Length is capped, because one patient in this panel renders to 233,000
    characters and would cost more than the rest of the sample put together. The
    caps preserve the thing that decides a label: every distinct lab code is
    listed even when only its two most recent values are shown, so "this test was
    never done" stays distinguishable from "this test was done and the value is
    X". Whatever is cut is counted out loud, so a labeller can answer
    INDETERMINATE on the grounds that it was not shown everything, which is the
    correct answer when it is true.
    """
    L: list[str] = []
    age = plainview.age_years(p)
    L.append(f"Demographics: age {age}, sex {p.get('sex')}, index date {p.get('index_date')}")
    L.append("")

    by_code: dict[str, list[dict]] = {}
    for row in p.get("labs", []):
        by_code.setdefault(f"{row.get('code')}|{row.get('name')}", []).append(row)
    L.append(f"Laboratory and vital measurements ({len(p.get('labs', []))} rows, "
             f"{len(by_code)} distinct):")
    if not by_code:
        L.append("  (none recorded)")
    for key in sorted(by_code):
        code, name = key.split("|", 1)
        rows = sorted(by_code[key], key=lambda r: (r.get("date") or ""), reverse=True)
        shown = rows[:max_labs_per_code]
        vals = "; ".join(f"{r.get('value')} {r.get('unit') or ''} on {r.get('date')}".strip()
                         for r in shown)
        more = f" (+{len(rows) - len(shown)} earlier)" if len(rows) > len(shown) else ""
        L.append(f"  [{code}] {name}: {vals}{more}")
    L.append("")

    L.append(f"Problem list ({len(p.get('problems', []))}):")
    if not p.get("problems"):
        L.append("  (none recorded)")
    for c in _recent(p.get("problems", []), "onset", max_rows):
        res = f", resolved {c['resolved']}" if c.get("resolved") else ""
        L.append(f"  [{c.get('code')}] {c.get('name')}: onset {c.get('onset')}, "
                 f"status {c.get('status')}{res}")
    _omitted(L, p.get("problems", []), max_rows, "problems")
    L.append("")

    L.append(f"Medication orders ({len(p.get('orders', []))}):")
    if not p.get("orders"):
        L.append("  (none recorded)")
    for m in _recent(p.get("orders", []), "date", max_rows):
        L.append(f"  [{m.get('code')}] {m.get('name')}: {m.get('date')}, {m.get('status')}")
    _omitted(L, p.get("orders", []), max_rows, "orders")
    L.append("")

    L.append(f"Procedures ({len(p.get('procedures', []))}):")
    if not p.get("procedures"):
        L.append("  (none recorded)")
    for pr in _recent(p.get("procedures", []), "date", max_rows):
        L.append(f"  [{pr.get('code')}] {pr.get('name')}: {pr.get('date')}")
    _omitted(L, p.get("procedures", []), max_rows, "procedures")
    return "\n".join(L)


def _recent(rows: list[dict], date_key: str, n: int) -> list[dict]:
    return sorted(rows, key=lambda r: (r.get(date_key) or ""), reverse=True)[:n]


def _omitted(L: list[str], all_rows: list, shown_n: int, what: str) -> None:
    """Say what was cut. A labeller that is not shown everything should be told."""
    k = len(all_rows) - min(len(all_rows), shown_n)
    if k > 0:
        L.append(f"  ... {k} older {what} are not shown here. If one of them would "
                 f"decide this criterion, the answer is INDETERMINATE.")


# ------------------------------------------------------------------ sampling ---

def gold_cells(panel: list) -> list[dict]:
    """Every checkable criterion against every patient, with Checker A's label."""
    out = []
    for c in CRITERIA:
        if not c["checkable"]:
            continue
        for ch in panel:
            p = plainview.plain(ch)
            out.append({"criterion_id": c["criterion_id"], "patient_id": ch.patient_id,
                        "gold_a": c["gold"](p)})
    return out


def stratified(cells: list[dict], n: int, seed: int = 4242) -> list[dict]:
    """Equal shares of each Checker A label, so agreement is not read off the marginals.

    A sample drawn uniformly would be almost entirely INDETERMINATE, and a
    labeller that answered INDETERMINATE to everything would score high agreement
    while knowing nothing. Stratifying costs the ability to read prevalence off
    the sample, which is fine: prevalence is measured on the full matrix.
    """
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = {}
    for c in cells:
        by_label.setdefault(c["gold_a"], []).append(c)
    per = max(1, n // max(1, len(by_label)))
    picked: list[dict] = []
    for label in sorted(by_label):
        pool = sorted(by_label[label], key=lambda c: (c["criterion_id"], c["patient_id"]))
        picked += rng.sample(pool, min(per, len(pool)))
    rng.shuffle(picked)          # order carries no information about the label
    return picked


# -------------------------------------------------------------------- labelling ---

PROVIDERS = {

    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}

VALID = {"MEETS", "FAILS", "INDETERMINATE"}


def _validate(d: object) -> None:
    if not isinstance(d, dict):
        raise ValueError("expected a JSON object")
    if d.get("label") not in VALID:
        raise ValueError(f"label must be one of {sorted(VALID)}, got {d.get('label')!r}")
    if not isinstance(d.get("reason"), str) or not d["reason"].strip():
        raise ValueError("reason must be a non-empty sentence naming the value or the absence")


def label_cells(cells: list[dict], panel: list, client: Client, run: Path) -> int:
    charts = {ch.patient_id: ch for ch in panel}
    crit = {c["criterion_id"]: c for c in CRITERIA}
    done = {(d["criterion_id"], d["patient_id"])
            for d in _read(LABELS)}
    written = 0
    OUT.mkdir(parents=True, exist_ok=True)

    for i, cell in enumerate(cells, 1):
        key = (cell["criterion_id"], cell["patient_id"])
        if key in done:
            continue
        c = crit[cell["criterion_id"]]
        p = plainview.plain(charts[cell["patient_id"]])
        traj = Trajectory("checker_b", f"{cell['criterion_id']}--{cell['patient_id'][:8]}")
        traj.instructions(INSTRUCTIONS, PROMPT_VERSION)
        traj.input(criterion_id=c["criterion_id"], patient_id=cell["patient_id"],
                   kind=c["kind"], source_text=c["source_text"])
        task = TASK.format(kind=c["kind"], text=c["source_text"],
                           index_date=p["index_date"], record=render_record(p))
        messages = [{"role": "system", "content": INSTRUCTIONS},
                    {"role": "user", "content": task}]
        try:
            raw = ask_json(client, traj, messages, _validate,
                           tag=f"checker-b:{c['criterion_id']}",
                           prompt_version=PROMPT_VERSION)
            got = {"label": raw["label"], "reason": raw["reason"].strip()}
        except Exception as exc:
            traj.final(error=f"{type(exc).__name__}: {exc}")
            traj.write(run / "trajectories")
            print(f"  [{i}/{len(cells)}] {c['criterion_id']:20s} ERROR {type(exc).__name__}",
                  flush=True)
            continue
        traj.final(**got)
        traj.write(run / "trajectories")
        rec = {"criterion_id": c["criterion_id"], "patient_id": cell["patient_id"],
               "label": got["label"], "reason": got["reason"],
               "model": client.model, "prompt_version": PROMPT_VERSION}
        with open(LABELS, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
        written += 1
        print(f"  [{i}/{len(cells)}] {c['criterion_id']:20s} {got['label']}", flush=True)
    return written


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


# ---------------------------------------------------------------------- report ---

def report() -> int:
    labels = _read(LABELS)
    if not labels:
        print("no labels yet", file=sys.stderr)
        return 2
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    a = {(c["criterion_id"], c["patient_id"]): c["gold_a"] for c in sample["cells"]}
    pairs = [(a[(d["criterion_id"], d["patient_id"])], d["label"])
             for d in labels if (d["criterion_id"], d["patient_id"]) in a]

    sys.path.insert(0, str(ROOT / "evaluation"))
    from score import agreement
    ag = agreement([x for x, _ in pairs], [y for _, y in pairs])

    print(f"cells labelled by both routes : {len(pairs)}")
    print(f"Checker A marginals           : {dict(Counter(x for x, _ in pairs))}")
    print(f"Checker B marginals           : {dict(Counter(y for _, y in pairs))}")
    print(json.dumps(ag, indent=1))
    dis = [(x, y) for x, y in pairs if x != y]
    print(f"\ndisagreements: {len(dis)} ({len(dis)/len(pairs):.1%})")
    print(f"pattern      : {dict(Counter(dis))}")
    out = OUT / "agreement.json"
    out.write_text(json.dumps({"n": len(pairs), "agreement": ag,
                               "a_marginals": dict(Counter(x for x, _ in pairs)),
                               "b_marginals": dict(Counter(y for _, y in pairs)),
                               "disagreement_pattern": {f"{x}->{y}": n
                                                        for (x, y), n in Counter(dis).items()}},
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\nwrote {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=180)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--provider", default="gemini", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--run", default="runs/checker_b")
    ap.add_argument("--panel", default="data/vendor/panel.jsonl.gz")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="draw the sample, call no model")
    a = ap.parse_args()

    if a.report:
        return report()

    panel = load_panel(a.panel)
    OUT.mkdir(parents=True, exist_ok=True)

    if SAMPLE.exists():
        blob = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cells = blob["cells"]
        print(f"reusing the committed sample of {len(cells)} cells (seed {blob['seed']})")
    else:
        cells = stratified(gold_cells(panel), a.sample, a.seed)
        SAMPLE.write_text(json.dumps(
            {"seed": a.seed, "n": len(cells), "panel": a.panel,
             "note": "Drawn once and committed. Redrawing after seeing agreement "
                     "would let the sample be chosen for its answer.",
             "cells": cells}, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"drew {len(cells)} cells, wrote {SAMPLE}")

    print(f"strata: {dict(Counter(c['gold_a'] for c in cells))}")
    if a.dry_run:
        p = plainview.plain(panel[0])
        print("\n--- one rendered record, for inspection ---")
        print(render_record(p)[:2000])
        return 0

    base_url, default_model = PROVIDERS[a.provider]
    client = Client(provider="openai", model=a.model or default_model, mode=a.mode,
                    cassette_dir=Path(a.run) / "cassettes", base_url=base_url)
    n = label_cells(cells, panel, client, Path(a.run))
    print(f"\nwrote {n} new label(s) to {LABELS}")
    print(f"usage: {client.usage.as_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
