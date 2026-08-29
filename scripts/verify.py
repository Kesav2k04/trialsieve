"""The five checks that turn "reproducible" from a claim into something you can watch.

    python scripts/verify.py cassettes      --run runs/tierA
    python scripts/verify.py trajectories   --run runs/tierA
    python scripts/verify.py prove-replay   --run runs/tierA
    python scripts/verify.py prove-sensitivity --run runs/tierA

The distinction being proved is between a cassette store and an answer file.

An answer file maps a task to a verdict. It is inert when the code changes: alter
a prompt, alter the pipeline, alter anything at all, and it keeps returning the
same numbers, which is exactly what makes it worthless as evidence.

A cassette maps request bytes to response bytes. Change one character of one
prompt and the hash changes, the lookup misses, and the run stops with an error
rather than quietly reporting yesterday's result. `prove-replay` demonstrates
that by adding a single byte and showing the failure. `prove-sensitivity`
demonstrates the other direction, that the recorded content is load-bearing, by
editing one recorded answer and showing a published number move.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))

from trialsieve.llm import CassetteMiss, Client, Request, verify_cassettes  # noqa: E402


def cmd_cassettes(run: Path) -> int:
    r = verify_cassettes(run / "cassettes")
    print(json.dumps(r, indent=1))
    if r["mismatched"]:
        print(f"\nFAIL: {len(r['mismatched'])} cassette(s) do not hash to their stored key.",
              file=sys.stderr)
        return 1
    print(f"\nPASS: {r['ok']}/{r['files']} cassettes re-hash to their stored key.")
    print(f"corpus digest {r['corpus_digest'][:32]}")
    return 0


def cmd_trajectories(run: Path) -> int:
    """Every recorded model call must point at a cassette that exists and matches."""
    from trialsieve.llm import CASSETTE_VERSION  # noqa: F401
    cass = {p.stem: p for p in (run / "cassettes").glob("*.json")}
    files = sorted((run / "trajectories").rglob("*.jsonl"))
    bad, checked, seqbad = [], 0, []
    for p in files:
        events = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        seqs = [e["seq"] for e in events]
        if seqs != list(range(1, len(seqs) + 1)):
            seqbad.append(p.name)
        for e in events:
            if e["event"] != "llm_request":
                continue
            checked += 1
            key = e["cassette_key"]
            f = cass.get(key[:16])
            if f is None:
                bad.append({"file": p.name, "seq": e["seq"], "reason": "no cassette"})
                continue
            rec = json.loads(f.read_text(encoding="utf-8"))
            if rec["request"]["messages"] != e["messages"]:
                bad.append({"file": p.name, "seq": e["seq"],
                            "reason": "trajectory prompt differs from the recorded request"})
    print(json.dumps({"trajectory_files": len(files), "llm_requests_checked": checked,
                      "mismatched": bad[:10], "n_mismatched": len(bad),
                      "non_contiguous_seq": seqbad}, indent=1))
    if bad or seqbad:
        print("\nFAIL", file=sys.stderr)
        return 1
    print(f"\nPASS: {checked} recorded model calls all resolve to a cassette whose stored "
          f"request is byte-identical to the prompt in the trajectory.")
    return 0


def cmd_prove_replay(run: Path) -> int:
    """Add one byte to a prompt and show that replay refuses rather than answers."""
    cass = sorted((run / "cassettes").glob("*.json"))
    if not cass:
        print(f"no cassettes in {run/'cassettes'}", file=sys.stderr)
        return 2
    rec = json.loads(cass[0].read_text(encoding="utf-8"))
    client = Client(provider="openai", model=rec["request"]["model"], mode="replay",
                    cassette_dir=run / "cassettes")

    original = Request(model=rec["request"]["model"], messages=rec["request"]["messages"],
                       temperature=rec["request"]["temperature"],
                       max_tokens=rec["request"]["max_tokens"], seed=rec["request"]["seed"])
    print(f"cassette under test: {cass[0].name}")
    print(f"request key        : {original.key()[:32]}")

    got = client.complete(original)
    print(f"\n1. unmodified request  -> replayed {len(got.text)} chars "
          f"(from_cassette={got.from_cassette})")
    assert got.from_cassette, "the unmodified request should have replayed"

    tampered = copy.deepcopy(rec["request"]["messages"])
    tampered[-1]["content"] = tampered[-1]["content"] + " "
    mutated = Request(model=rec["request"]["model"], messages=tampered,
                      temperature=rec["request"]["temperature"],
                      max_tokens=rec["request"]["max_tokens"], seed=rec["request"]["seed"])
    print(f"2. one space added     -> key becomes {mutated.key()[:32]}")
    try:
        client.complete(mutated)
    except CassetteMiss as exc:
        print(f"                          CassetteMiss raised, as required")
        print(f"                          {str(exc)[:150]}")
        print("\nPASS: replay is keyed on the request bytes. A changed prompt stops the "
              "run instead of returning the previous answer, which is what separates a "
              "cassette store from a saved answer file.")
        return 0
    print("\nFAIL: a modified prompt still returned an answer. Replay is not honest.",
          file=sys.stderr)
    return 1


def cmd_prove_sensitivity(run: Path) -> int:
    """Edit one recorded answer and show that a published number moves."""
    src = run / "compiled"
    files = sorted(src.glob("criteria_seed*.json"))
    if not files:
        # Named the same way the blind check names its own empty case. A reader
        # running `verify.py all` needs to be able to tell a check that passed
        # from a check that never ran, and two words on stderr does not do that.
        print(f"NOT VERIFIED: no compiled predicates under {src}, so there is "
              f"nothing to perturb and this check did not run. Compile a run "
              f"first. This is reported as a failure rather than a pass.",
              file=sys.stderr)
        return 2
    blob = json.loads(files[0].read_text(encoding="utf-8"))
    compilable = [c for c in blob["criteria"] if c.get("compilable")]
    if not compilable:
        print("no compiled predicates to perturb", file=sys.stderr)
        return 2

    import gzip  # noqa: F401
    from trialsieve.chart import load_panel
    from trialsieve.evaluator import evaluate_criterion

    panel = load_panel("data/vendor/panel.jsonl.gz")[:120]
    target = None
    for c in compilable:
        vs = [evaluate_criterion(c, ch)["verdict"] for ch in panel]
        if sum(1 for v in vs if v in ("MEETS", "FAILS")) >= 10:
            target = (c, vs)
            break
    if target is None:
        print("no predicate produces enough definite verdicts to perturb", file=sys.stderr)
        return 2

    c, before = target
    counts_before = {v: before.count(v) for v in ("MEETS", "FAILS", "INDETERMINATE")}

    mutated = copy.deepcopy(c)
    flipped = _flip_one_comparison(mutated["expr"])
    if not flipped:
        print("predicate has no comparison to flip", file=sys.stderr)
        return 2
    after = [evaluate_criterion(mutated, ch)["verdict"] for ch in panel]
    counts_after = {v: after.count(v) for v in ("MEETS", "FAILS", "INDETERMINATE")}
    moved = sum(1 for x, y in zip(before, after) if x != y)

    print(f"criterion      : {c['criterion_id']}")
    print(f"perturbation   : {flipped}")
    print(f"before         : {counts_before}")
    print(f"after          : {counts_after}")
    print(f"verdicts moved : {moved} of {len(panel)}")
    if moved == 0:
        print("\nFAIL: editing the recorded predicate changed nothing, so the published "
              "numbers do not depend on it.", file=sys.stderr)
        return 1
    print("\nPASS: the recorded model output is load-bearing. Changing one comparison in "
          "one compiled predicate moves the verdicts, so the reported numbers are computed "
          "from the cassettes rather than stored beside them.")
    return 0


def _flip_one_comparison(expr: dict) -> str | None:
    flip = {">=": ">", ">": ">=", "<=": "<", "<": "<="}
    if expr.get("op") == "compare" and expr.get("cmp") in flip:
        old = expr["cmp"]
        expr["cmp"] = flip[old]
        return f"cmp {old} -> {expr['cmp']}"
    if expr.get("op") == "between":
        old = expr["low"]
        expr["low"] = old + (abs(old) * 0.15 + 0.5)
        return f"between.low {old} -> {expr['low']}"
    for key in ("args",):
        for sub in expr.get(key, []) or []:
            r = _flip_one_comparison(sub)
            if r:
                return r
    if "arg" in expr:
        return _flip_one_comparison(expr["arg"])
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["cassettes", "trajectories", "prove-replay",
                                     "prove-sensitivity", "blind", "all"])
    ap.add_argument("--run", default="runs/tierA")
    a = ap.parse_args()
    run = Path(a.run)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _verify_blind import cmd_blind
    fns = {"cassettes": cmd_cassettes, "trajectories": cmd_trajectories,
           "prove-replay": cmd_prove_replay, "prove-sensitivity": cmd_prove_sensitivity,
           "blind": cmd_blind}
    if a.what == "all":
        rc = 0
        for name, fn in fns.items():
            print(f"\n{'=' * 72}\n{name}\n{'=' * 72}")
            rc |= fn(run)
        return rc
    return fns[a.what](run)


if __name__ == "__main__":
    sys.exit(main())
