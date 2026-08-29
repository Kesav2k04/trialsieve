"""Does the segmenter split a protocol the way a person did?

    python evaluation/segmentation.py --run runs/tierA --provider shim

The scored pipeline does not run the segmenter. Its criteria come from
`evaluation/gold/criteria_set.py`, hand-authored so that a gold label can attach
to a stable identifier and stay attached while prompts change. That is the right
call for the evaluation and it leaves one of the six agents unmeasured, which is
the wrong place to leave it.

So the segmenter is run on the same three held-out trials, its output is compared
against the hand-authored split, and both are published. Three model calls.

**What this can and cannot say.** It compares one automatic split against one
human split of the same text. A disagreement is not automatically the machine's
error: "male or female aged 18 to 75" is defensibly one criterion or two, and the
hand-authored set made a choice. So the report gives the counts first, the matched
pairs second, and every unmatched fragment in full, on both sides, because the
unmatched ones are the only rows anybody can actually adjudicate.

**The matching rule, and why it is strict.** Two criteria match when the Jaccard
overlap of their content words is at least 0.5. A looser threshold matches almost
any two sentences about diabetes and turns this into a test of the disease area
rather than of the split. The threshold is reported beside the score, and the
score at three thresholds is printed, so a reader can see how much the number
depends on it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "gold"))

from criteria_set import CRITERIA  # noqa: E402
from trialsieve.agents.segmenter import segment  # noqa: E402
from trialsieve.llm import Client  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402

PROVIDERS = {
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}

STOP = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
        "have", "in", "is", "must", "not", "of", "on", "or", "the", "to", "who",
        "will", "with", "within", "any", "all", "patient", "patients", "subject",
        "subjects", "participant", "participants"}


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def match(auto: list[dict], gold: list[dict], threshold: float) -> dict:
    """Greedy best-first pairing. Each criterion is used at most once."""
    pairs, used_g = [], set()
    scored = []
    for i, a in enumerate(auto):
        for j, g in enumerate(gold):
            scored.append((jaccard(words(a["source_text"]), words(g["source_text"])), i, j))
    scored.sort(reverse=True)
    used_a = set()
    for sc, i, j in scored:
        if sc < threshold or i in used_a or j in used_g:
            continue
        used_a.add(i)
        used_g.add(j)
        pairs.append({"score": round(sc, 3), "auto": auto[i]["source_text"],
                      "gold": gold[j]["source_text"],
                      "auto_kind": auto[i]["kind"], "gold_kind": gold[j]["kind"],
                      "kind_agrees": auto[i]["kind"] == gold[j]["kind"]})
    return {"threshold": threshold, "pairs": pairs,
            "auto_unmatched": [a["source_text"] for i, a in enumerate(auto) if i not in used_a],
            "gold_unmatched": [g["source_text"] for j, g in enumerate(gold) if j not in used_g]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--provider", default="shim", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--out", default="docs/SEGMENTATION.md")
    a = ap.parse_args()

    run = Path(a.run)
    base_url, default_model = PROVIDERS[a.provider]
    client = Client(provider="openai", model=a.model or default_model, mode=a.mode,
                    cassette_dir=run / "cassettes", base_url=base_url)

    ncts = sorted({c["nct_id"] for c in CRITERIA})
    rows, t0 = [], time.time()
    for nct in ncts:
        blob = json.loads((ROOT / "data" / "vendor" / "trials" / f"{nct}.json")
                          .read_text(encoding="utf-8"))
        text = blob["protocolSection"]["eligibilityModule"]["eligibilityCriteria"]
        traj = Trajectory("segmenter", nct)
        auto, traj = segment(client, nct, text, traj=traj)
        traj.write(run / "trajectories")
        gold = [c for c in CRITERIA if c["nct_id"] == nct]
        rows.append({"nct_id": nct, "chars": len(text), "n_auto": len(auto),
                     "n_gold": len(gold),
                     "at": {str(t): match(auto, gold, t) for t in (0.4, 0.5, 0.6)}})
        print(f"  {nct}  {len(text):5d} chars  auto {len(auto):2d}  gold {len(gold):2d}",
              flush=True)

    L = ["# The segmenter, measured against the hand-authored split", "",
         "Generated by `python evaluation/segmentation.py`. Output, not illustration.", "",
         "The scored pipeline does not run the segmenter: its criteria are hand-authored",
         "so a gold label can attach to a stable identifier and stay attached while",
         "prompts change. That leaves one of the six agents unmeasured, so it is run here",
         "on the same three held-out trials and both splits are published.", "",
         "A disagreement here is not automatically the machine's error. \"Male or female",
         "aged 18 to 75\" is defensibly one criterion or two, and the hand-authored set",
         "made a choice. The counts come first, and every unmatched fragment is printed",
         "in full on both sides, because those are the only rows a reader can adjudicate.", "",
         "| trial | eligibility text | segmenter | hand-authored |", "|---|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['nct_id']}` | {r['chars']:,} characters | {r['n_auto']} | {r['n_gold']} |")
    tot_a = sum(r["n_auto"] for r in rows)
    tot_g = sum(r["n_gold"] for r in rows)
    L += [f"| **total** | | **{tot_a}** | **{tot_g}** |", "",
          "## How much the score depends on the matching threshold", "",
          "Two criteria are called the same when the Jaccard overlap of their content",
          "words clears a threshold. A loose threshold matches almost any two sentences",
          "about diabetes and turns this into a test of the disease area. So the number is",
          "given at three thresholds rather than at the flattering one.", "",
          "| threshold | matched | kinds agree | segmenter fragments unmatched | "
          "hand-authored criteria unmatched |", "|---|---|---|---|---|"]
    for t in ("0.4", "0.5", "0.6"):
        m = sum(len(r["at"][t]["pairs"]) for r in rows)
        k = sum(1 for r in rows for p in r["at"][t]["pairs"] if p["kind_agrees"])
        ua = sum(len(r["at"][t]["auto_unmatched"]) for r in rows)
        ug = sum(len(r["at"][t]["gold_unmatched"]) for r in rows)
        L.append(f"| {t} | {m} of {tot_g} | {k} of {m} | {ua} | {ug} |")
    L += ["", "## What the segmenter produced that the hand-authored set does not have", "",
          "At threshold 0.5.", ""]
    for r in rows:
        for s in r["at"]["0.5"]["auto_unmatched"]:
            L.append(f"- `{r['nct_id']}` {s}")
    L += ["", "## What the hand-authored set has that the segmenter did not produce", ""]
    for r in rows:
        for s in r["at"]["0.5"]["gold_unmatched"]:
            L.append(f"- `{r['nct_id']}` {s}")
    L += ["", "## Where the two agree on the text but disagree on the kind", "",
          "An inclusion read as an exclusion inverts the predicate, so this is the one",
          "disagreement here that would change a verdict rather than a boundary.", ""]
    bad = [(r["nct_id"], p) for r in rows for p in r["at"]["0.5"]["pairs"]
           if not p["kind_agrees"]]
    if not bad:
        L.append("None.")
    for nct, p in bad:
        L.append(f"- `{nct}` segmenter said **{p['auto_kind']}**, hand-authored says "
                 f"**{p['gold_kind']}**: {p['gold']}")
    L.append("")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    js = ROOT / "results" / "segmentation.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps({"model": client.model, "trials": rows,
                              "usage": client.usage.as_dict(),
                              "wall_s": round(time.time() - t0, 1)}, indent=1) + "\n",
                  encoding="utf-8", newline="\n")
    print("\n".join(L[:20]))
    print(f"\nwrote {out} and {js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
