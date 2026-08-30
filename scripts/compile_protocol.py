"""Compile the criterion set into predicates. This is the only step that costs money.

    python scripts/compile_protocol.py --run runs/tierB --provider ollama --seed 7

Once this has run, screening any number of patients costs nothing, so the whole
economic argument of the project lives in the fact that this script is run once
per protocol rather than once per patient.

The criterion set is the human-authored one in `evaluation/gold/criteria_set.py`,
shared by every arm, so that arms are compared on verdicts rather than on how
they happened to split the source text.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))

from criteria_set import CRITERIA  # noqa: E402
from trialsieve.agents.compiler import compile_criterion, predicate_sha256  # noqa: E402
from trialsieve.agents.critic import review  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402

PROVIDERS = {
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
}


def revise_with_finding(client, criterion, compiled, finding, traj):
    """Recompile once with the critic's executed counterexample attached.

    The feedback is a patient the predicate demonstrably gets wrong, not an
    opinion, so the compiler is being told a fact about its own output.
    """
    ce = finding["counterexample"]
    ex = finding["executed"]
    note = (
        "A review of your previous predicate found a patient where it disagrees "
        "with the criterion text.\n\n"
        f"Patient: {json.dumps(ce['patient'])}\n"
        f"Your predicate returned: {ex.get('actual')}\n"
        f"The criterion text requires: {ce['expected_truth']}\n"
        f"Reviewer note: {ce.get('why', '')}\n"
        f"Issues raised: {'; '.join(f['issue'] for f in finding['findings'])}\n\n"
        "Produce a corrected predicate for the same criterion."
    )
    # Not an attempt at the same reply: the critic found a real defect and the
    # compiler is asked for a different predicate. It is outside the schema
    # retry budget, so it carries no attempt number rather than a sentinel.
    traj.retry(None, note, cause="a confirmed counterexample")
    amended = dict(criterion)
    amended["text"] = criterion["text"] + "\n\n[REVIEW FEEDBACK]\n" + note
    return compile_criterion(client, amended, traj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/dev")
    ap.add_argument("--provider", default="ollama", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-critic", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="comma-separated criterion ids")
    ap.add_argument("--split", default="held-out", choices=["held-out", "dev"],
                    help="dev compiles the five unlabelled development trials "
                         "instead of the three scored ones; see docs/DEV_SPLIT.md")
    ap.add_argument("--dev-n", type=int, default=30)
    a = ap.parse_args()

    base_url, default_model = PROVIDERS[a.provider]
    model = a.model or default_model
    run = Path(a.run)
    (run / "compiled").mkdir(parents=True, exist_ok=True)

    client = Client(provider="openai", model=model, mode=a.mode,
                    cassette_dir=run / "cassettes",
                    base_url=a.base_url or base_url)
    # `--seed` has to reach the model. It names the output file and the
    # trajectory subject, and until this line it did nothing else: every request
    # went out carrying seed 7, so recompiling under seeds 8 and 9 replayed seed
    # 7's cassettes and produced identical predicates. The registered noise floor
    # would have been exactly zero and would have made every difference look
    # significant. The seed is part of the cassette key, so setting it here also
    # means each seed records its own cassettes rather than sharing one set.
    client.seed = a.seed

    if a.split == "dev":
        sys.path.insert(0, str(ROOT / "evaluation" / "dev"))
        import dev_criteria
        todo = dev_criteria.sample(a.dev_n)
    else:
        todo = list(CRITERIA)
    if a.only:
        want = {x.strip() for x in a.only.split(",")}
        todo = [c for c in todo if c["criterion_id"] in want]
    if a.limit:
        todo = todo[:a.limit]

    ground_cache: dict[str, dict] = {}
    out, stats = [], {"compiled": 0, "refused_plan": 0, "refused_grounding": 0,
                      "errors": 0, "critic_confirmed": 0, "critic_dismissed": 0,
                      "revised": 0, "revised_unchanged": 0}
    t0 = time.time()

    for i, c in enumerate(todo, 1):
        crit = {"criterion_id": c["criterion_id"], "nct_id": c["nct_id"], "kind": c["kind"],
                "category": c["category"], "source_text": c["source_text"],
                "text": c["source_text"], "content_hash": c["criterion_id"]}
        traj = Trajectory("compiler", f"{c['criterion_id']}-seed{a.seed}")
        try:
            rec, traj = compile_criterion(client, crit, traj, ground_cache)
        except Exception as exc:
            stats["errors"] += 1
            print(f"  [{i:2d}/{len(todo)}] {c['criterion_id']:20s} ERROR "
                  f"{type(exc).__name__}: {str(exc)[:90]}", flush=True)
            traj.final(error=f"{type(exc).__name__}: {exc}")
            traj.write(run / "trajectories")
            out.append({**crit, "compilable": False,
                        "reason_not_compilable": f"compiler failed: {type(exc).__name__}",
                        "compile_error": True})
            continue

        # adversarial review, and a single bounded revision if it finds something real
        if rec.get("compilable") and not a.no_critic:
            ctraj = Trajectory("critic", f"{c['criterion_id']}-seed{a.seed}")
            try:
                finding, ctraj = review(client, rec, ctraj)
                if finding.get("dismissed_findings"):
                    stats["critic_dismissed"] += 1
                if finding["verdict"] == "REVISE":
                    stats["critic_confirmed"] += 1
                    rec2, traj = revise_with_finding(client, crit, rec, finding, traj)
                    if rec2.get("compilable"):
                        # The critic proved a case and the model was given it.
                        # Whether it then changed anything is a separate
                        # question, and on this run the answer was no twice out
                        # of five. Counting those as revisions would publish a
                        # revision rate the artefacts do not support, so the
                        # unchanged ones are counted apart and the event itself
                        # carries `changed`.
                        changed = rec.get("expr") != rec2.get("expr")
                        traj.revision(
                            "predicate revised after a confirmed counterexample"
                            if changed else
                            "revision returned the predicate unchanged after a "
                            "confirmed counterexample",
                            rec.get("expr"), rec2.get("expr"))
                        rec = rec2
                        stats["revised" if changed else "revised_unchanged"] += 1
            except Exception as exc:
                ctraj.final(error=f"{type(exc).__name__}: {exc}")
            ctraj.write(run / "trajectories")

        rec["seed"] = a.seed
        rec["model"] = model
        rec["predicate_sha256"] = predicate_sha256(rec)
        out.append(rec)
        traj.write(run / "trajectories")

        if rec.get("compilable"):
            stats["compiled"] += 1
            tag = "COMPILED"
        elif rec.get("blocked_at") == "grounding":
            stats["refused_grounding"] += 1
            tag = "refused(vocab)"
        else:
            stats["refused_plan"] += 1
            tag = "refused(plan)"
        print(f"  [{i:2d}/{len(todo)}] {c['criterion_id']:20s} {tag}", flush=True)

    path = run / "compiled" / f"criteria_seed{a.seed}.json"
    path.write_text(json.dumps(
        {"model": model, "seed": a.seed, "provider": a.provider,
         "n_criteria": len(out), "stats": stats,
         "usage": client.usage.as_dict(),
         "wall_s": round(time.time() - t0, 1),
         "criteria": out}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")

    print(f"\n{json.dumps(stats)}")
    print(f"usage: {client.usage.as_dict()}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
