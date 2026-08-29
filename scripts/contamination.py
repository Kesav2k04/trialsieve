"""Did the model recall these trials, or read them?

    python scripts/contamination.py --run runs/tierA                 # free, no model calls
    python scripts/contamination.py --run runs/tierA --counterfactual --provider shim

Three registered trials with public identifiers is exactly the setup where a
result can be produced by recall rather than by reading. A model that has seen
NCT06983054 during training can emit its thresholds without the criterion text
in front of it, and every number in the output would still be right. The
evaluation would then be measuring memorisation and reporting it as compilation.

Three checks, in increasing strength.

**1. No identifier reaches a prompt.** Structural. Every prompt in this system is
a `str.format` template, so the set of substitutions is enumerable without
running anything. If no template has a slot for the identifier or the title,
neither can appear. A future edit that adds one fails this check.

**2. No identifier is in any recorded request.** Empirical, and the one that
actually binds, because a template audit cannot see a string concatenated in by
hand. Every cassette holds the full canonical request that was sent. This
searches all of them for the identifiers, for the registered titles, and for the
distinctive word sequences in those titles.

**3. The numbers move when the criterion moves.** The strongest of the three. A
threshold in a criterion is perturbed to a value the real protocol does not
contain, the criterion is recompiled, and the emitted predicate has to carry the
perturbed number. A compiler that reproduces the original threshold is reciting.

Check 3 is the one worth arguing with, so its failures are reported per
criterion with both numbers, rather than as a rate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

NCT_RE = re.compile(r"NCT\d{8}")

#: Words too common to be evidence of anything. A title n-gram containing only
#: these would fire on any diabetes trial ever written, so it would report
#: contamination on a corpus the model has never seen.
STOP = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the",
        "to", "with", "study", "trial", "phase", "participants", "patients",
        "subjects", "efficacy", "safety", "evaluate", "assess", "versus", "vs"}


def ngrams(text: str, n: int = 3) -> list[str]:
    words = re.findall(r"[A-Za-z0-9-]+", text.lower())
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def title_ngrams(title: str, legitimate: set[str], n: int = 3) -> list[str]:
    """Word sequences that identify a registered title and nothing else.

    Two filters, and the second one is the one that makes this check mean
    anything.

    The first drops sequences that are mostly function words, so "safety and
    efficacy of" is not treated as a fingerprint.

    The second subtracts every sequence that also occurs in the text the system
    is legitimately given: the eligibility criteria themselves. "Chronic kidney
    disease" is in the title of one of these trials and also in the body of half
    the criteria, so finding it in a prompt says nothing about whether the title
    leaked. Without this subtraction the check fires on the disease name and
    reports contamination on every corpus that mentions the disease, which is a
    scan that can only ever return positive.

    What survives is title-specific wording: an acronym the sponsor coined, a
    design phrase, a sequence of drug and population that only the title puts in
    that order.
    """
    out = []
    for gram in ngrams(title, n):
        words = gram.split()
        if sum(1 for w in words if w not in STOP) < 2:
            continue
        if gram in legitimate:
            continue
        out.append(gram)
    return out


def legitimate_ngrams(n: int = 3) -> set[str]:
    """Every three-word sequence in text the system is entitled to see.

    The eligibility criteria of every vendored trial. These are the strings the
    segmenter is given by design, so their appearance in a prompt is the system
    working rather than the model recalling.
    """
    seen: set[str] = set()
    for f in sorted((ROOT / "data" / "vendor" / "trials").glob("NCT*.json")):
        try:
            blob = json.loads(f.read_text(encoding="utf-8"))
            text = blob["protocolSection"]["eligibilityModule"]["eligibilityCriteria"]
        except (OSError, ValueError, KeyError):
            continue
        seen.update(ngrams(text, n))
    return seen


# ---------------------------------------------------------------------------
# 1. template audit
# ---------------------------------------------------------------------------

def audit_templates() -> dict:
    from trialsieve import baselines
    from trialsieve.agents import compiler, critic, grounder, segmenter

    templates: list[tuple[str, str]] = []
    for mod in (segmenter, grounder, compiler, critic, baselines):
        name = mod.__name__.rsplit(".", 1)[-1]
        for attr in dir(mod):
            if attr.isupper() and isinstance(getattr(mod, attr), str):
                templates.append((f"{name}.{attr}", getattr(mod, attr)))

    rows = []
    for label, text in sorted(templates):
        slots = sorted(set(re.findall(r"\{(\w+)\}", text)))
        if slots:
            rows.append({"template": label, "slots": slots})

    banned = {"nct", "nct_id", "trial", "trial_id", "title", "trial_title",
              "nctid", "brief_title", "official_title"}
    offending = [r for r in rows if set(r["slots"]) & banned]
    return {"templates": rows, "offending": offending, "pass": not offending}


# ---------------------------------------------------------------------------
# 2. cassette scan
# ---------------------------------------------------------------------------

def scan_cassettes(run: Path, trials: list[dict]) -> dict:
    legit = legitimate_ngrams()
    grams: dict[str, str] = {}
    for t in trials:
        for g in title_ngrams(t.get("title", ""), legit):
            grams.setdefault(g, t["nct_id"])

    hits, n = [], 0
    for f in sorted((run / "cassettes").glob("*.json")):
        try:
            blob = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            hits.append({"cassette": f.name, "kind": "unreadable", "detail": str(exc)})
            continue
        n += 1
        req = str(blob.get("request", "")).lower()
        for nct in sorted({m for m in NCT_RE.findall(str(blob.get("request", "")))}):
            hits.append({"cassette": f.name, "kind": "nct_id", "detail": nct})
        for gram, nct in grams.items():
            if gram in req:
                hits.append({"cassette": f.name, "kind": "title_ngram",
                             "detail": f"{gram!r} from {nct}"})
    return {"cassettes_scanned": n, "distinct_title_ngrams": len(grams),
            "legitimate_ngrams_subtracted": len(legit),
            "example_ngrams": sorted(grams)[:8],
            "hits": hits, "pass": not hits}


# ---------------------------------------------------------------------------
# 3. counterfactual thresholds
# ---------------------------------------------------------------------------

NUM_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)(?![\d.])")


#: Every slot in the IR that can hold a number the criterion supplied. Taken from
#: the grammar in `src/trialsieve/agents/compiler.py`, not guessed.
#:
#: This list is the whole check. An earlier version read only
#: `{"val":"literal","number":N}`, which is the shape a `compare` uses, and missed
#: `between`, which keeps its bounds in `low` and `high`. So a predicate that
#: carried the perturbed value perfectly reported no literals at all, "follows"
#: came back false, and the strongest anti-contamination check in the project was
#: about to report maximum recitation on a compiler that had done exactly the
#: right thing. A gate blind to one syntax fails the cases written in it.
#:
#: `tests/test_perturb.py` parses the grammar and fails if it declares a
#: numeric slot this tuple does not name. That test found `n`, the count in
#: `at_least`, on its first run.
NUMERIC_SLOTS = ("number", "low", "high", "within_days", "n")


def literals(expr: dict) -> list[float]:
    """Every number the compiled predicate carries, in any slot that holds one."""
    out: list[float] = []

    def walk(node):
        if isinstance(node, dict):
            for slot in NUMERIC_SLOTS:
                v = node.get(slot)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append(float(v))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(expr)
    return out


def perturb(text: str) -> tuple[str, float, float] | None:
    """Change the largest number in the criterion to something the protocol never said.

    The largest, because a criterion often carries an incidental small number (a
    stage, a count of prior lines) alongside the threshold that matters, and a
    perturbation applied to the incidental one tests nothing. Multiplying by
    1.37 and rounding keeps the value plausible for its unit, which matters: a
    threshold of 900 for an HbA1c would be rejected on its face by a careful
    model and the check would pass for the wrong reason.

    A number is only a candidate if it stands alone. `NUM_RE` alone matched the
    `2` inside `T2DM` and the check duly rewrote the criterion to say `T2.7DM`,
    which is not a threshold moved to a new value, it is a word broken. The
    compiler refused it, correctly, and the refusal was counted as a row that
    failed to follow the perturbation. A check whose failures are its own
    malformed inputs measures nothing.
    """
    nums = []
    for m in NUM_RE.finditer(text):
        i, j = m.span(1)
        before = text[i - 1] if i else " "
        after = text[j] if j < len(text) else " "
        if before.isalpha() or after.isalpha():
            continue  # T2DM, HbA1c, CKD3, a1c
        nums.append((float(m.group(1)), (i, j)))
    if not nums:
        return None
    value, (i, j) = max(nums, key=lambda p: p[0])
    if value == 0:
        return None
    new = round(value * 1.37, 1)
    new = int(new) if float(new).is_integer() else new
    if float(new) == value:
        return None
    return text[:i] + str(new) + text[j:], value, float(new)


def counterfactual(run: Path, provider: str, model: str | None, mode: str,
                   limit: int) -> dict:
    from trialsieve.agents.compiler import compile_criterion
    from trialsieve.llm import Client
    from trialsieve.trace import Trajectory

    sys.path.insert(0, str(ROOT / "evaluation" / "gold"))
    from criteria_set import CRITERIA  # noqa

    base_url, default_model = PROVIDERS[provider]
    client = Client(provider="openai", model=model or default_model, mode=mode,
                    cassette_dir=run / "cassettes_counterfactual", base_url=base_url)

    picked = []
    for c in CRITERIA:
        p = perturb(c["source_text"])
        if p is None:
            continue
        picked.append((c, *p))
        if len(picked) >= limit:
            break

    rows = []
    for i, (crit, new_text, old, new) in enumerate(picked, 1):
        # `compile_criterion` reads `text`, and the gold criterion set stores the
        # wording under `source_text`. Setting only `source_text` left `text`
        # holding the ORIGINAL wording where it was present, and absent where it
        # was not, so every row came back `KeyError: 'text'` and the report
        # printed "0 of 0 follow the perturbation" as though that were a finding.
        # Both keys are set here, from the perturbed text, the way
        # `scripts/compile_protocol.py` builds the same record.
        shadow = dict(crit, source_text=new_text, text=new_text,
                      content_hash=crit["criterion_id"] + "-CF",
                      criterion_id=crit["criterion_id"] + "-CF")
        traj = Trajectory("contamination", shadow["criterion_id"])
        row = {"criterion_id": crit["criterion_id"], "original": old,
               "perturbed": new, "text": new_text}
        try:
            # `compile_criterion` returns (record, trajectory). Treating the pair
            # as the record raised `'tuple' object has no attribute 'get'` on
            # every row, which the loop swallowed into `status: error`, and the
            # report then printed "0 of 0 follow the perturbation" as a result.
            out, traj = compile_criterion(client, shadow, traj=traj)
            traj.write(run / "trajectories")
            if not out.get("compilable"):
                row.update(status="refused", reason=out.get("reason_not_compilable", ""))
            else:
                nums = literals(out["expr"])
                row.update(status="compiled", literals=nums,
                           follows=new in nums, recites=old in nums)
        except Exception as exc:
            # The traceback, not just the exception. "KeyError: 'text'" names a
            # key and not the line that wanted it, and this loop wraps a call
            # chain several modules deep.
            row.update(status="error", reason=f"{type(exc).__name__}: {exc}",
                       traceback=traceback.format_exc()[-1400:])
        rows.append(row)
        # The reason goes on the progress line, not only into the JSON written at
        # the end. A long run that prints `error` fifteen times and explains none
        # of them until it finishes is a run you cannot fix while it is going.
        tail = f" literals {row['literals']}" if row["status"] == "compiled" \
            else f"  {str(row.get('reason', ''))[:90]}"
        print(f"  [{i:2d}/{len(picked)}] {row['status']:9s} {row['criterion_id']:24s} "
              f"{old} -> {new}{tail}", flush=True)

    compiled = [r for r in rows if r["status"] == "compiled"]
    return {"n_attempted": len(rows), "n_compiled": len(compiled),
            "n_follows": sum(1 for r in compiled if r["follows"]),
            "n_recites": sum(1 for r in compiled if r["recites"]),
            "usage": client.usage.as_dict(), "rows": rows}


PROVIDERS = {
    "shim": ("http://127.0.0.1:8100/v1", "gemini-3.7-flash-medium"),
    "oss": ("http://127.0.0.1:8100/v1", "gpt-oss-120b-medium"),
    "ollama": ("http://127.0.0.1:11434/v1", "granite3.1-dense:8b"),
}


# ---------------------------------------------------------------------------

def render(res: dict) -> str:
    L = ["# Recall, or reading?", "",
         "Generated by `python scripts/contamination.py`. Everything below is output.", "",
         "Three registered trials with public identifiers is the setup where a good",
         "result can come from having memorised the protocol rather than from having",
         "read it. These are the checks that separate the two.", ""]

    t = res["templates"]
    L += ["## 1. No identifier reaches a prompt", "",
          f"Every prompt in this system is a `str.format` template, so the substitutions",
          f"are enumerable without running anything. {len(t['templates'])} templates carry a slot.",
          "None has a slot for a trial identifier or title.", "",
          "| template | substitutions |", "|---|---|"]
    for r in t["templates"]:
        L.append(f"| `{r['template']}` | {', '.join('`' + s + '`' for s in r['slots'])} |")
    L += ["", f"**{'PASS' if t['pass'] else 'FAIL'}.**"]
    if t["offending"]:
        L += ["", "Templates carrying an identifier slot:"] + \
             [f"- `{r['template']}`: {r['slots']}" for r in t["offending"]]
    L.append("")

    c = res.get("cassettes")
    if c:
        L += ["## 2. No identifier is in any recorded request", "",
              "A template audit cannot see a string joined on by hand, so this reads the",
              "requests that were actually sent. Every model call in this system is recorded",
              f"in full. {c['cassettes_scanned']} recorded requests were searched for the",
              f"identifiers and for {c['distinct_title_ngrams']} title-specific three-word sequences.", "",
              "Title-specific is doing work in that sentence. A registered title contains the",
              "disease name, and so does the criterion text the segmenter is given on purpose,",
              f"so the {c['legitimate_ngrams_subtracted']} sequences occurring anywhere in the",
              "vendored eligibility text are subtracted first. Without that subtraction the scan",
              "fires on 'chronic kidney disease' and returns positive on any corpus that mentions",
              "the disease, which is a check that cannot fail and therefore cannot pass.", "",
              f"What is left is wording only the title uses, for example: "
              f"{', '.join(repr(g) for g in c['example_ngrams'][:4])}.", "",
              f"**{'PASS' if c['pass'] else 'FAIL'}.** "
              f"{len(c['hits'])} hits.", ""]
        for h in c["hits"][:20]:
            L.append(f"- `{h['cassette']}`: {h['kind']}, {h['detail']}")
        L.append("")

    k = res.get("counterfactual")
    if k:
        L += ["## 3. The numbers move when the criterion moves", "",
              "The check worth arguing with. A threshold is changed to a value the real",
              "protocol does not contain, the criterion is recompiled, and the emitted",
              "predicate has to carry the changed number. A compiler that reproduces the",
              "original threshold is reciting rather than reading.", "",
              "The perturbation is the largest number in the criterion multiplied by 1.37",
              "and rounded. Largest, because criteria often carry an incidental small number",
              "beside the threshold that matters. Rounded rather than randomised, because a",
              "wildly implausible threshold would be rejected on its face and the check would",
              "pass for the wrong reason.", "",
              f"{k['n_attempted']} criteria carried a perturbable number. {k['n_compiled']} compiled.", "",
              "| criterion | protocol says | criterion was changed to | predicate carries | follows |",
              "|---|---|---|---|---|"]
        for r in k["rows"]:
            if r["status"] != "compiled":
                L.append(f"| `{r['criterion_id']}` | {r['original']} | {r['perturbed']} | "
                         f"{r['status']} | n/a |")
                continue
            L.append(f"| `{r['criterion_id']}` | {r['original']} | {r['perturbed']} | "
                     f"{r['literals']} | {'yes' if r['follows'] else '**no**'} |")
        n = k["n_compiled"]
        if not n:
            # "0 of 0 follow the perturbation" reads like a clean result and is
            # the output of a check that measured nothing. It was the only
            # symptom of a wrong dict key that made every row error.
            failed = [r for r in k["rows"] if r["status"] == "error"]
            L += ["", "**NOT MEASURED. Nothing compiled, so nothing was tested.** A ratio "
                      "over an empty denominator is not evidence of anything, and the "
                      "shape it prints is indistinguishable from a pass.", ""]
            if failed:
                L += [f"{len(failed)} of {len(k['rows'])} attempts raised. The first: "
                      f"`{failed[0].get('reason', '')[:120]}`", ""]
        else:
            L += ["", f"**{k['n_follows']} of {n} follow the perturbation. "
                      f"{k['n_recites']} of {n} reproduce the original number.**", ""]
        if k["n_recites"]:
            L += ["A predicate carrying the original threshold after the criterion was",
                  "changed is reciting the protocol. Those rows are listed above with both",
                  "numbers so the claim can be checked rather than taken.", ""]
    return "\n".join(L) + "\n"


def failures(res: dict) -> list[str]:
    """Which checks failed the run. Split out of main so the rule itself can be
    tested without running the checks, because two of these three branches were
    added after the exit code was found to be ignoring them.
    """
    failed = [k for k in ("templates", "cassettes") if k in res and not res[k]["pass"]]
    # The counterfactual was outside the exit code, so a run in which every
    # attempt raised still exited 0 and wrote a document. A check that could not
    # run is a failure here for the same reason it is in `scripts/verify.py`: it
    # prints the same zero as a check that ran and found nothing.
    cf = res.get("counterfactual")
    if cf is not None and not cf.get("n_compiled"):
        failed.append("counterfactual (nothing compiled, so nothing was measured)")
    # Reciting is the signal this check exists for: a predicate still carrying the
    # original threshold after the criterion was changed read the protocol from
    # memory rather than from the text in front of it. The report printed that in
    # bold and the exit code ignored it, so the strongest of the three
    # contamination checks could not fail the run.
    if cf is not None and cf.get("n_recites"):
        failed.append(f"counterfactual ({cf['n_recites']} of {cf.get('n_compiled')} "
                      "predicates reproduce the original number)")
    return failed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/tierA")
    ap.add_argument("--counterfactual", action="store_true")
    ap.add_argument("--provider", default="shim", choices=sorted(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--mode", default="record", choices=["record", "replay", "live"])
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--out", default="docs/CONTAMINATION.md")
    ap.add_argument("--json", default="results/contamination.json")
    a = ap.parse_args()

    run = Path(a.run)
    trials = json.loads((ROOT / "data" / "vendor" / "trials_index.json")
                        .read_text(encoding="utf-8"))["trials"]

    res = {"templates": audit_templates()}
    if (run / "cassettes").is_dir():
        res["cassettes"] = scan_cassettes(run, trials)
    if a.counterfactual:
        res["counterfactual"] = counterfactual(run, a.provider, a.model, a.mode, a.limit)

    md = render(res)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8", newline="\n")

    js = Path(a.json)
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")

    failed = failures(res)
    print(md)
    print(f"wrote {out} and {js}")
    if failed:
        print(f"\nFAIL: {', '.join(failed)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
