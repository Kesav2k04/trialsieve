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

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Vocabulary that appears in a compiled predicate and nowhere in a criterion or a
#: flattened chart. Finding any of these in a Checker B prompt means the predicate
#: reached the labeller.
IR_TOKENS = ('"absent_means"', '"expr"', '"op":', '"val":', '"codes":',
             '"agg":', '"window_days"', 'egfr_ckdepi_2021', '"cmp":',
             '"broader_codes"', '"compilable"', '"predicate_sha256"')

#: Files whose content is a system answer. Any distinctive line from one of these
#: turning up in a prompt is the same leak by another route.
ANSWER_FILES = ("evaluation/gold/criteria_set.py",)

#: A line from an answer file only counts as a probe if it is unmistakably source
#: rather than clinical prose. The criterion text legitimately appears in a
#: Checker B prompt, so searching for every long line would report a leak on
#: every cassette and the check would be worse than useless.
SOURCE_MARKS = ("plain.", "def gold", "return ", "elif ", " and ", " or ")


def _compiled_digests(run: Path) -> set[str]:
    """Every predicate digest this run produced.

    The key is `predicate_sha256`. An earlier version of this function looked for
    `digest` and `predicate_digest`, neither of which anything in this system
    writes, so it searched an empty set on every run and reported PASS. That is
    the reason `verify_blind` now refuses to pass when a term set comes back
    empty: the bug was invisible because its only symptom was a zero.
    """
    out: set[str] = set()
    for f in sorted((run / "compiled").glob("criteria_seed*.json")):
        blob = json.loads(f.read_text(encoding="utf-8"))
        for c in blob.get("criteria", []):
            if c.get("predicate_sha256"):
                out.add(str(c["predicate_sha256"]))
    return out


def _answer_lines() -> set[str]:
    """Distinctive source lines from the files that hold the gold answers."""
    out: set[str] = set()
    for rel in ANSWER_FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if len(line) < 30 or line.startswith("#"):
                continue
            if any(m in line for m in SOURCE_MARKS):
                out.add(line)
    return out


def verify_blind(b_run: Path, sys_run: Path) -> dict:
    cassettes = sorted((b_run / "cassettes").glob("*.json"))
    digests = _compiled_digests(sys_run)
    answers = _answer_lines()

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
        for line in answers:
            if line in req:
                hits.append({"cassette": f.name, "kind": "gold answer text",
                             "detail": line[:60]})

    # A search over an empty term set finds nothing and looks exactly like a
    # search that found nothing. Three of the four term sets are built from the
    # tree at run time and any of them can silently come back empty, so an empty
    # one is reported as a distinct outcome rather than folded into the pass.
    empty = [name for name, n in (("compiled digests", len(digests)),
                                  ("gold answer lines", len(answers)),
                                  ("IR tokens", len(IR_TOKENS)),
                                  ("cassettes", scanned)) if not n]
    return {"cassettes_scanned": scanned, "compiled_digests_searched": len(digests),
            "ir_tokens_searched": len(IR_TOKENS),
            "answer_lines_searched": len(answers),
            "empty_term_sets": empty, "hits": hits,
            "pass": not hits and not empty}


def probe_blind(b_run: Path, sys_run: Path) -> dict:
    """Plant a contaminated prompt in a scratch copy and require the scan to find it.

    The other four gates under `verify.py` each carry one of these. This one did
    not, so "none of 181 recorded Checker B prompts contains a predicate" rested
    on a search nothing had ever seen succeed. Three of its four term sets are
    built from the tree at run time; the `empty_term_sets` report catches a set
    that came back empty, and catches nothing about a scan that walks a full set
    and matches wrongly.

    So this copies one real cassette, splices a compiled predicate's digest and a
    line of IR vocabulary into its request, and asserts the scan reports both.
    The copy lives in a temporary directory and is never written beside the
    recordings, because a contaminated cassette left in `runs/checker_b/` would
    be indistinguishable from the thing the gate exists to detect.
    """
    import shutil
    import tempfile

    real = sorted((b_run / "cassettes").glob("*.json"))
    digests = sorted(d for d in _compiled_digests(sys_run) if d)
    if not real or not digests:
        return {"ran": False, "why": "no recordings or no compiled digests here"}

    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "cassettes"
        fake.mkdir(parents=True)
        shutil.copy2(real[0], fake / real[0].name)
        blob = json.loads((fake / real[0].name).read_text(encoding="utf-8"))
        # One term of each kind the scan looks for, so a scan that quietly
        # dropped a term set fails here rather than passing on the other one.
        #
        # The IR term goes in as a JSON key, not inside a string. `IR_TOKENS`
        # entries carry their own quotes, and putting `"absent_means"` inside a
        # value makes `json.dumps` escape them to `\"absent_means\"`, which the
        # scan correctly does not match. The first probe planted it that way and
        # reported that the gate had missed a leak the gate was right to miss.
        token = next(t for t in IR_TOKENS
                     if t.startswith('"') and t.endswith('"'))
        blob["request"] = {"planted_digest": digests[0],
                           token.strip('"'): True}
        (fake / "planted.json").write_text(json.dumps(blob), encoding="utf-8",
                                           newline=chr(10))
        r = verify_blind(Path(tmp), sys_run)

    kinds = {h["kind"] for h in r["hits"]}
    return {"ran": True, "cassettes_scanned": r["cassettes_scanned"],
            "kinds_found": sorted(kinds),
            "caught": {"predicate digest", "predicate vocabulary"} <= kinds}



def cmd_blind(run: Path) -> int:
    b_run = ROOT / "runs" / "checker_b"
    if not (b_run / "cassettes").is_dir():
        # This used to return 0 with a friendly note. `runs/checker_b/` was
        # gitignored, so on every machine except the one that recorded it the
        # check printed a success it had not earned, over a directory that was
        # not there. The cassettes are tracked now, and their absence is a
        # failure rather than a shrug: a reader who clones and sees PASS has to
        # be seeing a scan that happened.
        print(f"NOT VERIFIED: no Checker B cassettes under {b_run}. The blindness "
              f"claim is not an argument about commit order, it is these prompts, "
              f"so with the prompts missing there is nothing to read and nothing "
              f"to conclude. This is reported as a failure rather than a pass.",
              file=sys.stderr)
        return 1
    r = verify_blind(b_run, run)
    print(json.dumps({k: v for k, v in r.items() if k != "hits"}, indent=1))
    if r["hits"]:
        print(f"\nFAIL: {len(r['hits'])} Checker B prompt(s) contain something the "
              f"system produced. The agreement rate is not a noise floor.")
        for h in r["hits"][:10]:
            print(f"  {h['cassette']}: {h['kind']}, {h['detail']}")
        return 1
    if r["empty_term_sets"]:
        print(f"\nNOT VERIFIED: {', '.join(r['empty_term_sets'])} came back empty, so "
              f"the search for it could not have found anything. This is reported as "
              f"a failure rather than a pass because a check that searched nothing "
              f"and a check that found nothing print the same zero.", file=sys.stderr)
        return 1
    probe = probe_blind(b_run, run)
    if probe.get("ran") and not probe.get("caught"):
        print(chr(10) + "FAIL: the contamination probe planted a predicate "
              "digest and a line of IR vocabulary in a copied prompt, and this "
              "scan did not report both; it reported "
              f"{probe['kinds_found']}. A clean result "
              "from a scan that cannot find a planted hit is not evidence.",
              file=sys.stderr)
        return 1
    if probe.get("ran"):
        print(f"probe: planted one contaminated prompt, the scan reported "
              f"{probe['kinds_found']}")
    else:
        print(f"probe: not run, {probe.get('why')}")

    print(f"\nPASS: none of {r['cassettes_scanned']} recorded Checker B prompts "
          f"contains a predicate, a digest, or any part of the compiled output. "
          f"The two labellings are independent readings of the same record.")
    return 0
