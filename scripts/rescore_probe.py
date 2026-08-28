"""Re-score a recorded probe run under the current acceptance rule, calling nothing.

    python scripts/rescore_probe.py runs/probe-v0/probe.json

The acceptance rule changed after the first run: a probe is satisfied by any
non-empty subset of the acceptable codes rather than by one exact code. That
change has to be applied to every run or the comparison between them is
meaningless, and re-running the model to apply it would cost forty calls to
change an arithmetic definition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from vocab_probe import PROBES, score  # noqa: E402

ACCEPT = {name: sorted(codes) for name, _, codes, _, _ in PROBES}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    for path in sys.argv[1:]:
        p = Path(path)
        blob = json.loads(p.read_text(encoding="utf-8"))
        for r in blob["rows"]:
            want = ACCEPT.get(r["concept"], r["expected"])
            got = r["got"]
            r["expected"] = want
            if got is None:
                r["correct"] = r["over_accepted"] = r["under_accepted"] = False
            elif r["class"] == "absent":
                r["correct"], r["over_accepted"], r["under_accepted"] = (
                    got == [], bool(got), False)
            else:
                over = bool(set(got) - set(want))
                r["over_accepted"], r["under_accepted"] = over, not got
                r["correct"] = bool(got) and not over
        blob["correct"] = sum(1 for r in blob["rows"] if r["correct"])
        blob["by_class"] = score(blob["rows"])
        blob["scoring_rule"] = "non-empty subset of acceptable codes; absent means empty"
        p.write_text(json.dumps(blob, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"{p}: {blob['correct']}/{blob['n']}")
        print(json.dumps(blob["by_class"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
