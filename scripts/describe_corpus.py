"""What is actually in this repository's data, counted rather than described.

    python scripts/describe_corpus.py

Every figure the README and the video open with comes from here, and this reads
the vendored files rather than a note somebody wrote when the panel was built. A
corpus description that is prose goes stale the first time the panel is rebuilt,
and nothing catches it, because prose does not fail.

It is also the honest place to state the size of the thing. Three hundred and
eighty-five synthetic patients and forty criteria is a small corpus, and a reader
should learn that from the first screen rather than infer it later.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))

from trialsieve.chart import load_panel  # noqa: E402


def main() -> int:
    panel = load_panel(str(ROOT / "data" / "vendor" / "panel.jsonl.gz"))
    trials = json.loads((ROOT / "data" / "vendor" / "trials_index.json")
                        .read_text(encoding="utf-8"))
    prov = json.loads((ROOT / "data" / "vendor" / "panel_provenance.json")
                      .read_text(encoding="utf-8"))
    cat = json.loads((ROOT / "data" / "vendor" / "terminology_catalog.json")
                     .read_text(encoding="utf-8"))

    from criteria_set import CRITERIA

    obs = sum(len(c.observations) for c in panel)
    cond = sum(len(c.conditions) for c in panel)
    meds = sum(len(c.medications) for c in panel)
    procs = sum(len(c.procedures) for c in panel)
    codes = sum(len(v) for v in cat.values())

    uacr = sum(1 for c in panel
               if not any(o.codings and o.codings[0].code == "14959-1"
                          for o in c.observations))

    kinds = Counter(c["kind"] for c in CRITERIA)
    checkable = sum(1 for c in CRITERIA if c.get("checkable"))
    cats = Counter(c.get("category", "?") for c in CRITERIA)

    W = 46
    def row(label, value):
        print(f"{label:<{W}} {value}")

    print("THE PANEL")
    row("  patients", f"{len(panel)}")
    row("  laboratory and vital results", f"{obs:,}")
    row("  problem list entries", f"{cond:,}")
    row("  medication orders", f"{meds:,}")
    row("  procedures", f"{procs:,}")
    row("  distinct codes in the site vocabulary", f"{codes:,}")
    row("  licence", prov.get("licence", "?"))
    url = str(prov.get("source_url", "?"))
    row("  source archive", url.split("/")[2] + "/.../" + url.rsplit("/", 1)[-1])
    row("  archive sha256", str(prov.get("archive_sha256", "?"))[:40] + "...")
    row("  panel sha256", str(prov.get("panel_sha256", "?"))[:40] + "...")
    row("  selection rule", prov.get("selection_rule", "?"))
    print()

    print("THE TRIALS")
    row("  registered trials fetched", f"{len(trials['trials'])}")
    row("  held out for scoring", "3")
    row("  criteria with hand-authored gold labels", f"{len(CRITERIA)}")
    row("    inclusion / exclusion", f"{kinds['inclusion']} / {kinds['exclusion']}")
    row("    judged checkable from a record alone", f"{checkable}")
    row("  source", trials.get("source", "?"))
    print()

    print("THE JUDGEMENTS")
    row("  patient by criterion cells", f"{len(panel) * len(CRITERIA):,}")
    row("  patients with no UACR result at all",
        f"{uacr} of {len(panel)} ({uacr / len(panel):.0%})")
    print()

    print("CRITERIA BY CATEGORY")
    for k, n in cats.most_common():
        row(f"  {k}", n)
    print()
    print("Synthetic patients, public registry text. No real patient data, and no")
    print("credential anywhere in this tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
