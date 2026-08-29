"""Did a code the grounder called BROADER_ONLY end up settling a verdict?

    python scripts/grounding_audit.py --run runs/tierA

The design's sharpest promise, in `README.md`: a code the site uses more coarsely
than the criterion needs goes in a query's `broader_codes`, never in its `codes`.
Presence of such a code cannot settle the question. Absence still can.

`src/trialsieve/agents/compiler.py` builds the emit validator's allow-list by
pooling both fields:

    allowed = {c for g in grounded for c in g["codes"]}
    allowed |= {c for g in grounded for c in (g.get("broader_codes") or [])}

so a broader-only code emitted into `codes` is inside the allow-list and passes.
The prompt asks for the distinction, the contract states it, and nothing checked
it. This checks it.

It is a separate script rather than a rule inside the compiler on purpose.
Enforcing it at emit time would reject a recorded response, force a retry that
has no cassette, and stop `python run.py reproduce` on a criterion it has already
published numbers for. Fixing it properly means recompiling and rescoring, which
is choosing a new number after watching the old one fail. So the violation is
measured and published instead, and the count is pinned by a test.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def promotions(criterion: dict) -> list[str]:
    """Codes in a query's `codes` slot that the grounder returned as broader-only."""
    grounded = criterion.get("grounded") or []
    broader = {c for g in grounded for c in (g.get("broader_codes") or [])}
    exact = {c for g in grounded for c in (g.get("codes") or [])}
    if not broader:
        return []

    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            q = node.get("query")
            if isinstance(q, dict):
                for code in q.get("codes") or []:
                    if code in broader and code not in exact:
                        found.append(code)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(criterion.get("expr"))
    return sorted(set(found))


def audit(path: Path) -> dict:
    blob = json.loads(path.read_text(encoding="utf-8"))
    rows, n_at_risk = [], 0
    for c in blob["criteria"]:
        if not c.get("compilable"):
            continue
        if not any((g.get("broader_codes") or []) for g in c.get("grounded") or []):
            continue
        n_at_risk += 1
        bad = promotions(c)
        if bad:
            rows.append({"criterion_id": c["criterion_id"],
                         "promoted": bad,
                         "source_text": (c.get("source_text") or "")[:90],
                         "absent_means": sorted(
                             {n.get("absent_means") for n in _nodes(c["expr"])
                              if isinstance(n, dict) and n.get("absent_means")})})
    return {"n_criteria_with_broader_codes": n_at_risk,
            "n_violations": len(rows), "violations": rows}


def _nodes(node: object) -> list:
    out = []
    if isinstance(node, dict):
        out.append(node)
        for v in node.values():
            out += _nodes(v)
    elif isinstance(node, list):
        for v in node:
            out += _nodes(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    src = ROOT / a.run / "compiled" / f"criteria_seed{a.seed}.json"
    if not src.exists():
        print(f"no compiled predicates at {src}", file=sys.stderr)
        return 2

    res = audit(src)
    print(f"criteria whose grounding produced a broader-only code: "
          f"{res['n_criteria_with_broader_codes']}")
    print(f"of those, criteria that then used it as an exact code: "
          f"**{res['n_violations']}**")
    for r in res["violations"]:
        print(f"  {r['criterion_id']}  promoted {', '.join(r['promoted'])}"
              f"   absent_means={r['absent_means']}")
        print(f"    {r['source_text']}")

    if not res["n_violations"]:
        print("\nPASS: every broader-only code is in broader_codes, so presence "
              "cannot settle any of these criteria.")
        return 0

    print("\nFAIL: the codes above settle a verdict the site's vocabulary cannot "
          "support. Where such a criterion also carries absent_means=false, both "
          "branches commit and the criterion can never answer INDETERMINATE, "
          "which is how one criterion produced 358 of the 424 wrong exclusions.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
