"""Render a compiled predicate as something a person can disagree with.

The sign-off gate is only as good as what it shows the reviewer. A clinician
handed forty lines of JSON approves all forty in ninety seconds and the gate has
measured nothing. So the predicate is rendered back into a sentence, with the
codes resolved to the display names the site's own records use and the resource
counts attached, because a code that appears on eleven patients and a code that
appears on none are very different things to approve.

Two rules the rendering follows:

* `absent_means` is never hidden. It is the one decision in the IR that can
  quietly rule a person out, so it gets its own clause in plain words rather
  than a flag the eye skips.
* Nothing is smoothed. If the predicate compares a value in an odd unit, or
  reads a window of 99999 days, the sentence says so. A renderer that tidies its
  input is a renderer that hides its input.
"""
from __future__ import annotations

from typing import Any

from . import terminology

_DERIVED = {
    "egfr_ckdepi_2021": "eGFR (CKD-EPI 2021, no race coefficient)",
    "bmi": "BMI",
    "systolic_bp": "systolic blood pressure",
    "diastolic_bp": "diastolic blood pressure",
}

_DOMAIN = {"condition": "a diagnosis of", "medication": "a prescription for",
           "procedure": "a record of", "observation": "a measurement of"}


def code_label(code: str, domain: str = "") -> str:
    """The site's display for a code, and how many patients in this panel carry it.

    The panel count is the number a reviewer needs. A code that is in the site's
    vocabulary but on nobody's chart will make its criterion compile, run, and
    quietly return nothing for every patient, which under a closed-world query
    clears the entire panel on that criterion. Putting `0 patients` in front of
    the person signing it is the cheapest possible guard against that.
    """
    hit = terminology.lookup(code)
    disp = (hit or {}).get("display", "")
    pc = terminology.panel_count(code)
    if pc is None:
        tail = ", 0 patients in this panel"
    else:
        tail = f", {pc['patients']} patient(s) in this panel"
    return f"{code} ({disp}{tail})" if disp else f"{code}{tail}"


def _codes(codes: list[str], domain: str = "") -> str:
    if len(codes) == 1:
        return code_label(codes[0], domain)
    return " or ".join(code_label(c, domain) for c in codes)


def _window(within: Any) -> str:
    if within is None:
        return "at any time in the record"
    if within % 365 == 0:
        return f"within the last {within // 365} year(s)"
    return f"within the last {within} days"


def value(v: dict) -> str:
    kind = v.get("val")
    if kind == "age":
        return "age in years"
    if kind == "sex":
        return "recorded sex"
    if kind == "literal":
        if "number" in v:
            u = f" {v['unit']}" if v.get("unit") else ""
            return f"{v['number']}{u}"
        return repr(v.get("string"))
    if kind == "observation":
        agg = v.get("agg", "latest")
        word = {"latest": "the most recent", "min": "the lowest", "max": "the highest",
                "first": "the earliest", "any": "any"}.get(agg, agg)
        return (f"{word} value of {_codes(v['codes'], 'observation')} "
                f"in {v.get('unit')}, {_window(v.get('within_days'))}")
    if kind == "derived":
        return f"{_DERIVED.get(v.get('name'), v.get('name'))}, {_window(v.get('within_days'))}"
    if kind == "count":
        return f"the number of records matching [{query(v['query'])}]"
    return str(v)


def query(q: dict) -> str:
    dom = q.get("domain", "")
    absent = ("and if there is none, the record is trusted and this is false"
              if q.get("absent_means") == "false"
              else "and if there is none, this is undetermined rather than false")
    return (f"{_DOMAIN.get(dom, dom)} {_codes(q.get('codes', []), dom)}, "
            f"{_window(q.get('within_days'))}, {absent}")


def expr(e: dict, indent: int = 0) -> str:
    pad = "  " * indent
    op = e.get("op")

    if op == "compare":
        return f"{pad}{value(e['left'])}  {e['cmp']}  {value(e['right'])}"
    if op == "between":
        inc = e.get("inclusive", [True, True])
        lo = "at least" if inc[0] else "above"
        hi = "at most" if inc[1] else "below"
        return f"{pad}{value(e['value'])} is {lo} {e['low']} and {hi} {e['high']}"
    if op == "exists":
        return f"{pad}there is {query(e['query'])}"
    if op == "const":
        return f"{pad}always {e.get('value')}"
    if op == "not":
        return f"{pad}NOT:\n{expr(e['arg'], indent + 1)}"
    if op in ("and", "or"):
        head = "ALL of:" if op == "and" else "ANY of:"
        body = "\n".join(expr(a, indent + 1) for a in e.get("args", []))
        return f"{pad}{head}\n{body}"
    if op == "at_least":
        body = "\n".join(expr(a, indent + 1) for a in e.get("args", []))
        return f"{pad}AT LEAST {e.get('n')} of:\n{body}"
    return f"{pad}{e}"


def criterion(rec: dict) -> str:
    """The whole review packet for one compiled criterion."""
    L = [f"criterion : {rec.get('criterion_id')}  ({rec.get('kind', '')})",
         f"text      : {rec.get('source_text', '')}"]
    if not rec.get("compilable"):
        L.append(f"REFUSED   : {rec.get('reason_not_compilable', '')}")
        if rec.get("blocked_at"):
            L.append(f"blocked at: {rec['blocked_at']}")
        return "\n".join(L)
    L.append(f"digest    : {rec.get('predicate_sha256', '')[:16]}")
    L.append("")
    L.append("This criterion is satisfied when:")
    L.append(expr(rec["expr"], 1))
    notes = rec.get("notes") or rec.get("compiler_note")
    if notes:
        L.append("")
        L.append(f"compiler note: {notes}")
    open_leaves = _open_world_leaves(rec["expr"])
    if open_leaves:
        L.append("")
        L.append(f"{len(open_leaves)} leaf/leaves treat an empty record as undetermined "
                 f"rather than false.")
    closed = _closed_world_leaves(rec["expr"])
    if closed:
        L.append("")
        L.append("READ THIS TWICE. The following treat an absent record as proof of "
                 "absence, which is how a patient gets ruled out on silence:")
        for q in closed:
            L.append(f"  - {query(q)}")

    empty = empty_closed_world_codes(rec["expr"])
    if empty:
        L.append("")
        L.append("STOP. These codes are in the site vocabulary but on no chart in this "
                 "panel, and the query treats their absence as proof. Every patient "
                 "will come back the same way, and it will look like a result:")
        for code in empty:
            L.append(f"  - {code_label(code)}")
    return "\n".join(L)


def empty_closed_world_codes(e: dict) -> list[str]:
    """Codes that no panel patient carries, used in a query that trusts absence.

    This is the SGLT2 inhibitor hazard one level deeper. The grounder guards
    against a concept with no code at all. It cannot guard against a concept whose
    code exists in the vocabulary and on nobody's chart, because from the
    grounder's side that looks like success: the criterion compiles, runs, returns
    nothing for everyone, and clears the panel.
    """
    out: list[str] = []
    for q in _closed_world_leaves(e):
        for code in q.get("codes", []):
            pc = terminology.panel_count(code)
            if (pc is None or pc.get("patients", 0) == 0) and code not in out:
                out.append(code)
    return out


def _walk(e: dict):
    yield e
    for a in e.get("args", []) or []:
        yield from _walk(a)
    if "arg" in e:
        yield from _walk(e["arg"])


def _closed_world_leaves(e: dict) -> list[dict]:
    out = []
    for n in _walk(e):
        q = n.get("query")
        if isinstance(q, dict) and q.get("absent_means") == "false":
            out.append(q)
        for side in ("left", "right", "value"):
            v = n.get(side)
            if isinstance(v, dict) and isinstance(v.get("query"), dict) \
                    and v["query"].get("absent_means") == "false":
                out.append(v["query"])
    return out


def _open_world_leaves(e: dict) -> list[dict]:
    out = []
    for n in _walk(e):
        q = n.get("query")
        if isinstance(q, dict) and q.get("absent_means") == "unknown":
            out.append(q)
    return out
