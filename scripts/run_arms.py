"""Run every arm over the panel and write one row per patient-criterion cell.

    python scripts/run_arms.py --run runs/tierB --arms TS,B0,B1 --k 0
    python scripts/run_arms.py --run runs/tierB --arms B2 --patients 15 --k 0

TrialSieve and the deterministic controls run over the whole panel because they
cost nothing per patient. B2 and B3 run over a seeded uniform sample, because
they cost one model call per cell and the honest way to say so is to publish the
sample rule and the sample size rather than to quietly shrink the panel for
everyone.

Scoring later restricts every arm to the cells they share, so the comparison is
always paired.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))
sys.path.insert(0, str(ROOT / "evaluation"))

from criteria_set import CRITERIA, BY_ID  # noqa: E402
from plainview import plain  # noqa: E402
from trialsieve.baselines import (  # noqa: E402
    b0_always_fails, b1_demographics, b2_cell, b3_cell, render_record, trimmed,
)

#: The per-cell arms put the whole chart in a prompt, and a prompt has a length.
#: Fifteen percent of these charts do not fit. They are trimmed by age with the
#: omission stated in the text, and the flag is carried on every affected cell so
#: the comparison can be repeated without them.
B2_MAX_CHARS = 26000
from trialsieve.chart import load_panel  # noqa: E402
from trialsieve.degrade import degrade_panel, manifest_digest  # noqa: E402
from trialsieve.evaluator import evaluate_criterion  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402

PROVIDERS = {
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
}


def gold_relevant_codes() -> set[str]:
    """Codes the GOLD predicates read.

    Degradation targets these and never the codes the system under test compiled,
    because damaging what the system reads while sparing what the baseline reads
    would decide the result in advance.
    """
    import criteria_set as cs
    codes: set[str] = set()
    for name in dir(cs):
        v = getattr(cs, name)
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v) and name.isupper():
            if name != "ABSENT_FROM_VOCABULARY":
                codes.update(v)
    return codes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/dev")
    ap.add_argument("--arms", default="TS,B0,B1")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--k", type=float, default=0.0, help="degradation fraction")
    ap.add_argument("--degrade-seed", type=int, default=101)
    ap.add_argument("--patients", type=int, default=0, help="0 = whole panel")
    ap.add_argument("--patient-seed", type=int, default=23)
    ap.add_argument("--provider", default="ollama", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--panel", default="data/vendor/panel.jsonl.gz")
    ap.add_argument("--absent-means-override", default=None, choices=["false", "unknown"])
    ap.add_argument("--unit-policy", default="code_authoritative",
                    choices=["code_authoritative", "strict"])
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    run = Path(a.run)
    (run / "cells").mkdir(parents=True, exist_ok=True)
    arms = [x.strip().upper() for x in a.arms.split(",") if x.strip()]

    panel = load_panel(a.panel)
    changes = []
    if a.k > 0:
        panel, changes = degrade_panel(panel, a.k, a.degrade_seed, gold_relevant_codes())

    if a.patients:
        # Shuffle once, then take a prefix, rather than drawing a sample of size
        # n. Both are uniform, but only the prefix nests: the first ten patients
        # of the shuffle are the first ten of the fifteen. That matters because
        # the paid arms are recorded against cassettes, so extending the sample
        # later has to replay the earlier calls rather than draw a fresh set and
        # pay for all of them again. `random.sample(panel, 10)` and
        # `random.sample(panel, 15)` on one seed share no such guarantee.
        rng = random.Random(a.patient_seed)
        panel = sorted(panel, key=lambda c: c.patient_id)
        rng.shuffle(panel)
        panel = panel[:min(a.patients, len(panel))]
        panel.sort(key=lambda c: c.patient_id)

    compiled_path = run / "compiled" / f"criteria_seed{a.seed}.json"
    compiled = {}
    if compiled_path.exists():
        blob = json.loads(compiled_path.read_text(encoding="utf-8"))
        compiled = {c["criterion_id"]: c for c in blob["criteria"]}
    elif "TS" in arms or "B1" in arms:
        print(f"missing {compiled_path}; run compile_protocol.py first", file=sys.stderr)
        return 2

    client = None
    if {"B2", "B3"} & set(arms):
        base_url, default_model = PROVIDERS[a.provider]
        client = Client(provider="openai", model=a.model or default_model, mode=a.mode,
                        cassette_dir=run / "cassettes", base_url=base_url)

    suffix = a.tag or f"k{int(a.k * 100)}_seed{a.seed}"
    rows: list[dict] = []
    t0 = time.time()

    for pi, chart in enumerate(panel, 1):
        pv = plain(chart)
        record = render_record(chart, max_chars=B2_MAX_CHARS) if client else ""
        was_trimmed = trimmed(chart, B2_MAX_CHARS) if client else False
        traj = Trajectory("baseline-b2", f"{chart.patient_id[:8]}-{suffix}") if client else None
        for c in CRITERIA:
            cid = c["criterion_id"]
            try:
                gold = c["gold"](pv)
            except Exception:
                gold = "UNMEASURABLE"
            row = {"patient_id": chart.patient_id, "criterion_id": cid,
                   "criterion_hash": cid, "gold": gold, "k": a.k, "seed": a.seed}
            if client:
                row["record_trimmed"] = was_trimmed

            if "TS" in arms:
                comp = compiled.get(cid)
                if comp is None:
                    row["TS"] = "ERROR"
                else:
                    r = evaluate_criterion(comp, chart, unit_policy=a.unit_policy,
                                           default_absent_means=a.absent_means_override)
                    row["TS"] = r["verdict"]
                    row["TS_reason"] = r["reason"][:220]
                    row["TS_evidence"] = [e["resource_id"] for e in r["evidence"][:4]]
            if "B0" in arms:
                row["B0"] = b0_always_fails(c, chart)["verdict"]
            if "B1" in arms:
                comp = compiled.get(cid)
                row["B1"] = b1_demographics(comp or {**c, "compilable": False},
                                            chart)["verdict"]
            if "B2" in arms:
                r = b2_cell(client, c, chart, record, traj)
                row["B2"] = r["verdict"]
                row["B2_reason"] = (r.get("reasoning") or "")[:220]
            if "B3" in arms:
                r = b3_cell(client, c, chart, record, traj)
                row["B3"] = r["verdict"]
                row["B3_votes"] = r.get("votes")
            rows.append(row)
        if traj:
            traj.write(run / "trajectories")
        # Report often enough that a long paid run does not look hung. Every
        # patient when the sample is small, which is exactly when each one is
        # slow, and every tenth when the panel is the free arms' whole 385.
        every = 1 if len(panel) <= 40 else 10
        if pi % every == 0 or pi == len(panel):
            print(f"  {pi}/{len(panel)} patients, {len(rows)} cells, "
                  f"{time.time() - t0:.0f}s", flush=True)

    out = run / "cells" / f"cells_{'-'.join(arms)}_{suffix}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    meta = {"arms": arms, "seed": a.seed, "k": a.k, "degrade_seed": a.degrade_seed,
            "b2_max_chars": B2_MAX_CHARS if client else None,
            "cells_with_trimmed_record": sum(1 for r in rows if r.get("record_trimmed")),
            "n_patients": len(panel), "n_criteria": len(CRITERIA), "n_cells": len(rows),
            "patient_sample": a.patients or "full panel", "patient_seed": a.patient_seed,
            "unit_policy": a.unit_policy, "absent_means_override": a.absent_means_override,
            "degradation_changes": len(changes),
            "degradation_manifest_sha256": manifest_digest(changes) if changes else None,
            "wall_s": round(time.time() - t0, 1),
            "usage": client.usage.as_dict() if client else None,
            "panel_ids_sha256": __import__("hashlib").sha256(
                "".join(c.patient_id for c in panel).encode()).hexdigest()}
    (run / "cells" / f"meta_{'-'.join(arms)}_{suffix}.json").write_text(
        json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")

    if changes:
        with open(run / "cells" / f"degradation_{suffix}.jsonl", "w",
                  encoding="utf-8", newline="\n") as fh:
            for ch in changes:
                fh.write(json.dumps(ch.as_dict(), sort_keys=True) + "\n")

    print(f"\n{json.dumps(meta, indent=1)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
