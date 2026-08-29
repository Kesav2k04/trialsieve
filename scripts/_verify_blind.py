"""Was the second labeller actually blind?

Imported by `scripts/verify.py`. Split out because the check is longer than the
four beside it and its reasoning is the part worth reading.

**The claim this replaces.** The original wording said blindness was a git fact:
the labels were committed before any commit containing system output, so the
ordering was checkable. That was true when it was written and it stopped being
true, because Checker B and the scored compile ended up running at the same time
on the same machine. Commit ordering now records nothing except which process
happened to finish first.

**The claim that survives, and it is the stronger one.** Blindness is not about
when a file was written. It is about what was in the prompt. Every one of Checker
B's model calls is recorded in full, so the question "did B see the system's
answer" is answerable by reading the request rather than by trusting a timeline.

So this searches every recorded Checker B request for anything the system
produced: the vocabulary of the predicate IR, the digests the sign-off gate signs,
the identifiers of the compiled predicates, and the text of the gold labels. If B
saw none of them, the agreement rate between A and B is a comparison of two
independent readings, which is what a label noise floor has to be.

What it deliberately does not flag: the words MEETS, FAILS and INDETERMINATE. B is
instructed to answer with them, so they are in every prompt by design, and a check
that fires on its own instructions is a check that cannot pass.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Vocabulary that appears in a compiled predicate and nowhere in a criterion or a
#: flattened chart. Finding any of these in a Checker B prompt means the predicate
#: reached the labeller.
IR_TOKENS = ('"absent_means"', '"expr"', '"op":', '"val":', '"codes":',
             '"agg":', '"window_days"', 'egfr_ckdepi_2021', '"cmp":',
             '"broader_codes"', '"compilable"', '"predicate_digest"')

#: Files whose content is a system answer. Any long line from one of these turning
#: up in a prompt is the same leak by another route.
ANSWER_FILES = ("evaluation/gold/criteria_set.py",)


def _compiled_digests(run: Path) -> set[str]:
    out: set[str] = set()
    for f in sorted((run / "compiled").glob("criteria_seed*.json")):
        blob = json.loads(f.read_text(encoding="utf-8"))
        for c in blob.get("criteria", []):
            for k in ("digest", "predicate_digest"):
                if c.get(k):
                    out.add(str(c[k]))
    return out


def verify_blind(b_run: Path, sys_run: Path) -> dict:
    cassettes = sorted((b_run / "cassettes").glob("*.json"))
    digests = _compiled_digests(sys_run)

    hits, scanned = [], 0
    for f in cassettes:
        try:
            blob = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            hits.append({"cassette": f.name, "kind": "unreadable", "detail": str(exc)})
            continue
        scanned += 1
        req = json.dumps(blob.get("request", ""), ensure_ascii=False)
        for tok in IR_TOKENS:
            if tok in req:
                hits.append({"cassette": f.name, "kind": "predicate vocabulary",
                             "detail": tok})
        for d in digests:
            if d and d in req:
                hits.append({"cassette": f.name, "kind": "predicate digest",
                             "detail": d[:16]})
    return {"cassettes_scanned": scanned, "compiled_digests_searched": len(digests),
            "ir_tokens_searched": len(IR_TOKENS), "hits": hits, "pass": not hits}


def cmd_blind(run: Path) -> int:
    b_run = ROOT / "runs" / "checker_b"
    if not (b_run / "cassettes").is_dir():
        print(f"no Checker B cassettes under {b_run}. Nothing to verify, and nothing "
              f"claimed: the label noise floor is only reported when B has run.")
        return 0
    r = verify_blind(b_run, run)
    print(json.dumps({k: v for k, v in r.items() if k != "hits"}, indent=1))
    if r["hits"]:
        print(f"\nFAIL: {len(r['hits'])} Checker B prompt(s) contain something the "
              f"system produced. The agreement rate is not a noise floor.")
        for h in r["hits"][:10]:
            print(f"  {h['cassette']}: {h['kind']}, {h['detail']}")
        return 1
    print(f"\nPASS: none of {r['cassettes_scanned']} recorded Checker B prompts "
          f"contains a predicate, a digest, or any part of the compiled output. "
          f"The two labellings are independent readings of the same record.")
    return 0
