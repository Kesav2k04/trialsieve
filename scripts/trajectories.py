"""Render every trajectory to markdown and build an index that points at the failures.

    python scripts/trajectories.py --run runs/tierA --out trajectories

A judge opening a folder of two hundred JSONL files reads none of them. The index
is sorted so the ones worth reading come first: a trajectory where the model was
rejected by the schema validator and told exactly why, where the critic built a
patient the predicate got wrong, or where a human refused to sign. A run of
uniformly clean trajectories is either a trivial task or an edited log, and this
table is where that shows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.trace import render_markdown  # noqa: E402

INTERESTING = ("validation_error", "retry", "critic_finding", "revision",
               "normalisation", "human_checkpoint")


def stats(events: list[dict]) -> dict:
    kinds: dict[str, int] = {}
    tokens = 0
    latency = 0.0
    for e in events:
        kinds[e["event"]] = kinds.get(e["event"], 0) + 1
        if e["event"] == "llm_response":
            tokens += int(e.get("completion_tokens") or 0)
            latency += float(e.get("latency_s") or 0.0)
    final = next((e for e in reversed(events) if e["event"] == "final"), {})
    return {
        "events": len(events),
        "llm_calls": kinds.get("llm_request", 0),
        "tool_calls": kinds.get("tool_call", 0),
        "validation_errors": kinds.get("validation_error", 0),
        "retries": kinds.get("retry", 0),
        "transport_retries": kinds.get("transport_retry", 0),
        "critic_findings": kinds.get("critic_finding", 0),
        "revisions": kinds.get("revision", 0),
        "normalisations": kinds.get("normalisation", 0),
        "human_checkpoints": kinds.get("human_checkpoint", 0),
        "completion_tokens": tokens,
        "latency_s": round(latency, 1),
        "outcome": _outcome(final),
    }


def _outcome(final: dict) -> str:
    if not final:
        return "no final event"
    if final.get("error"):
        return f"error: {str(final['error'])[:60]}"
    if final.get("compilable") is False:
        return f"refused: {str(final.get('reason_not_compilable', ''))[:60]}"
    if final.get("compilable") is True:
        return "compiled"
    if final.get("verdict"):
        return str(final["verdict"])
    if final.get("codes") is not None:
        n = len(final["codes"])
        return f"grounded to {n} code(s)" if n else "unmappable"
    return "done"


def excerpt(path: Path, context: int = 1) -> str:
    """The events that make a trajectory worth reading, and their neighbours.

    Not a tail. The end of a compiler trajectory is the predicate it settled on,
    which is the least interesting part: it is the same thing the compiled file
    already contains. What is worth seeing is the middle, where the validator
    rejected an answer and the exact error text went back to the model.

    So this selects the interesting events, keeps one event either side of each
    for context, and says in the header how many of the total it kept. A reader
    who suspects the selection is flattering can render the whole file, and the
    line that tells them how is printed with it.
    """
    events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()
              if x.strip()]
    keep: set[int] = set()
    for i, e in enumerate(events):
        if e["event"] in INTERESTING:
            for j in range(max(0, i - context), min(len(events), i + context + 1)):
                keep.add(j)
    if not keep:
        keep = set(range(min(len(events), 12)))

    L = [f"# {path.stem}", "",
         f"{len(keep)} of {len(events)} events. The ones where something went wrong, "
         f"plus one either side.",
         f"Whole log: `python -c \"from trialsieve.trace import render_markdown as r; "
         f"print(r(r'{path.as_posix()}'))\"`", ""]
    last = -2
    for i in sorted(keep):
        if i > last + 1:
            L.append(f"...  {i - last - 1} event(s) omitted  ...")
        last = i
        e = events[i]
        L.append(f"### {i + 1}. {e['event']}")
        for k, v in e.items():
            if k in ("event", "t"):
                continue
            text = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            if len(text) > 700:
                text = text[:700] + f"  ... [{len(text) - 700} more characters]"
            L.append(f"{k}: {text}")
        L.append("")
    return chr(10).join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--out", default="")
    ap.add_argument("--show-worst", action="store_true",
                    help="print the single most eventful trajectory to stdout and "
                         "write nothing. Used by the video build, so what a viewer "
                         "sees is a rendering of the log rather than a screenshot "
                         "somebody chose.")
    a = ap.parse_args()

    run = Path(a.run)
    src = run / "trajectories"
    if not src.exists():
        print(f"no trajectories under {src}", file=sys.stderr)
        return 2
    out = Path(a.out) if a.out else src
    rows = []

    for p in sorted(src.rglob("*.jsonl")):
        events = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        if not events:
            continue
        st = stats(events)
        rel = p.relative_to(src)
        md = out / rel.with_suffix(".md")
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(p), encoding="utf-8", newline="\n")
        st["agent"] = rel.parts[0] if len(rel.parts) > 1 else "?"
        st["subject"] = p.stem
        st["md"] = str(rel.with_suffix(".md")).replace("\\", "/")
        st["interest"] = (st["retries"] * 3 + st["validation_errors"] * 2
                          + st["critic_findings"] * 4 + st["revisions"] * 5
                          + st["human_checkpoints"] * 2)
        rows.append(st)

    if not rows:
        print("nothing to render", file=sys.stderr)
        return 2

    rows.sort(key=lambda r: (-r["interest"], r["agent"], r["subject"]))

    if a.show_worst:
        worst = rows[0]
        src_file = src / Path(worst["md"]).with_suffix(".jsonl")
        print(excerpt(src_file))
        return 0
    tot = {k: sum(r[k] for r in rows) for k in
           ("events", "llm_calls", "tool_calls", "validation_errors", "retries",
            "transport_retries", "critic_findings", "revisions", "normalisations",
            "human_checkpoints", "completion_tokens")}

    L: list[str] = []
    L.append("# Agent trajectories")
    L.append("")
    L.append(f"{len(rows)} trajectories from `{run}`. Each markdown file below is a "
             f"rendering of the JSONL beside it, and the JSONL is the source of truth. "
             f"Every model call in every one of them is matched to a recorded cassette "
             f"by `python scripts/verify.py trajectories`, so the prompt shown here is "
             f"byte-identical to the prompt that was sent.")
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append(f"| model calls | {tot['llm_calls']} |")
    L.append(f"| tool calls | {tot['tool_calls']} |")
    L.append(f"| schema rejections fed back to the model | {tot['validation_errors']} |")
    L.append(f"| retries after a schema rejection | {tot['retries']} |")
    L.append(f"| requests resent after the endpoint failed | "
             f"{tot['transport_retries']} |")
    L.append(f"| critic findings | {tot['critic_findings']} |")
    L.append(f"| predicates revised after a confirmed counterexample | {tot['revisions']} |")
    L.append(f"| malformed fields the harness repaired without a retry | "
             f"{tot['normalisations']} |")
    L.append(f"| human checkpoints | {tot['human_checkpoints']} |")
    L.append(f"| completion tokens | {tot['completion_tokens']} |")
    L.append("")
    L.append("Sorted so the trajectories that went wrong come first. Those are the ones "
             "worth reading: they show what the agent was told about its own output and "
             "what it did next.")
    L.append("")
    L.append("| agent | subject | calls | rejections | retries | critic | revised | outcome |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['agent']} | [{r['subject']}]({r['md']}) | {r['llm_calls']} | "
                 f"{r['validation_errors']} | {r['retries']} | {r['critic_findings']} | "
                 f"{r['revisions']} | {r['outcome']} |")
    L.append("")

    index = out / "index.md"
    index.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"rendered {len(rows)} trajectories, wrote {index}")
    print(json.dumps(tot, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
