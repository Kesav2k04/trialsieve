"""The human checkpoint, as a thing you actually sit down and do.

    python scripts/signoff.py --run runs/tierA --list
    python scripts/signoff.py --run runs/tierA --reviewer "Jane Doe" \
        --role "clinical research coordinator"

It shows one compiled predicate at a time, rendered into English with the codes
resolved to the display names this site's own records use, and takes a decision.
Nothing is approved in bulk and there is no `--approve-all`, because a gate you
can clear without reading is not a gate.

Decisions are appended to `<run>/signoffs.jsonl`, keyed on the predicate digest.
Recompiling changes the digest and invalidates the signature, which is the point:
approval cannot carry over to a predicate nobody read.

The worklist step refuses to run without this. Evaluation runs do not require it
and say so, since measuring your own error rate affects nobody.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve import explain, trace  # noqa: E402
from trialsieve.signoff import Signoff, append, check, load  # noqa: E402

MENU = """
  [a] approve            the predicate says what the criterion says
  [n] approve with note  usable, with a caveat worth recording
  [r] reject             it does not say what the criterion says
  [s] skip               decide later
  [q] save and quit
"""


def latest_compiled(run: Path) -> Path:
    files = sorted((run / "compiled").glob("criteria_seed*.json"))
    if not files:
        raise SystemExit(f"no compiled predicates in {run / 'compiled'}. Compile first.")
    return files[0]


def cmd_list(run: Path) -> int:
    blob = json.loads(latest_compiled(run).read_text(encoding="utf-8"))
    signoffs = load(run / "signoffs.jsonl")
    st = check(blob["criteria"], signoffs)
    n_comp = sum(1 for c in blob["criteria"] if c.get("compilable"))
    print(f"run            : {run}")
    print(f"criteria       : {len(blob['criteria'])} ({n_comp} compiled, "
          f"{len(blob['criteria']) - n_comp} refused and needing no signature)")
    print(f"approved       : {len(st['approved'])}")
    print(f"rejected       : {len(st['rejected'])}")
    print(f"awaiting review: {len(st['missing'])}")
    if st["missing"]:
        print("\nunsigned:")
        for cid in st["missing"]:
            print(f"  {cid}")
    print(f"\nworklist ready : {st['ready']}")
    return 0 if st["ready"] else 1


def cmd_review(run: Path, reviewer: str, role: str) -> int:
    path = latest_compiled(run)
    blob = json.loads(path.read_text(encoding="utf-8"))
    signoffs = load(run / "signoffs.jsonl")
    todo = [c for c in blob["criteria"]
            if c.get("compilable") and c.get("predicate_sha256") not in signoffs]

    if not todo:
        print("Every compiled predicate already carries a signature.")
        return cmd_list(run)

    print(f"{len(todo)} predicate(s) to review, from {path.name}")
    print(f"reviewer: {reviewer} ({role})")
    print("Read the criterion text first, then the predicate. They should say the "
          "same thing.\nIf they do not, reject it and say what is wrong; the "
          "rejection is data.")

    done = 0
    for i, c in enumerate(todo, 1):
        print("\n" + "=" * 74)
        print(f"[{i}/{len(todo)}]")
        print("=" * 74)
        print(explain.criterion(c))
        print(MENU)
        try:
            choice = input("  decision > ").strip().lower()
        except EOFError:
            print("\nno terminal to read from; nothing was signed", file=sys.stderr)
            return 2
        if choice == "q":
            break
        if choice == "s":
            continue
        decision = {"a": "APPROVED", "n": "APPROVED_WITH_NOTE", "r": "REJECTED"}.get(choice)
        if decision is None:
            print("  unrecognised, skipping")
            continue
        rationale = input("  in one line, why: ").strip()
        while not rationale:
            print("  a signature without a reason is not reviewable.")
            rationale = input("  in one line, why: ").strip()
        signed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        append(run / "signoffs.jsonl", Signoff(
            criterion_id=c["criterion_id"], predicate_sha256=c["predicate_sha256"],
            reviewer=reviewer, decision=decision, rationale=rationale,
            signed_at=signed_at, reviewer_role=role))
        # The ledger is what the gate reads. The trajectory is what a reader
        # follows, and a decision a human took about this criterion belongs in the
        # same ordered log as everything the agents did to it. Writing it in only
        # one of the two places is how "human checkpoints appear in the
        # trajectories" became a sentence with no call site behind it.
        seed = blob.get("seed", 7)
        written = trace.append_human_checkpoint(
            run / "trajectories", "compiler", f"{c['criterion_id']}-seed{seed}",
            reviewer=reviewer, reviewer_role=role, decision=decision,
            rationale=rationale, artifact_sha256=c["predicate_sha256"],
            signed_at=signed_at)
        if written is None:
            print(f"  note: no compiler trajectory for {c['criterion_id']}; the "
                  f"signature is in signoffs.jsonl only")
        done += 1
        print(f"  recorded {decision}")

    print(f"\n{done} decision(s) written to {run / 'signoffs.jsonl'}")
    return cmd_list(run)


def cmd_show(run: Path, cid: str) -> int:
    blob = json.loads(latest_compiled(run).read_text(encoding="utf-8"))
    hit = [c for c in blob["criteria"] if c["criterion_id"] == cid]
    if not hit:
        raise SystemExit(f"no criterion {cid} in {run}")
    print(explain.criterion(hit[0]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--list", action="store_true", help="status only, sign nothing")
    ap.add_argument("--show", default="", help="render one criterion and exit")
    ap.add_argument("--reviewer", default="")
    ap.add_argument("--role", default="",
                    help="what this reviewer is qualified to say, recorded with "
                         "the signature")
    a = ap.parse_args()
    run = Path(a.run)
    if a.show:
        return cmd_show(run, a.show)
    if a.list:
        return cmd_list(run)
    if not a.reviewer or not a.role:
        raise SystemExit("--reviewer and --role are both required to sign. An "
                         "unattributed signature cannot be audited.")
    return cmd_review(run, a.reviewer, a.role)


if __name__ == "__main__":
    sys.exit(main())
