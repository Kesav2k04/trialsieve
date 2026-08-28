"""Lexical search over the vocabulary this site actually records.

The catalog is built from the corpus itself, which is the honest thing to search:
a criterion can only ever be checked against codes that appear in these records,
so a concept that has no match here cannot be evaluated no matter how well the
model understands it.

That is what makes the third outcome necessary. Asked for "SGLT2 inhibitors",
this vocabulary returns nothing, because the corpus contains metformin and
insulin and no gliflozin at all. A grounder that answers with an empty code list
hands the evaluator a query that matches nothing, and a closed-world reading of
"nothing matched" clears every patient on that exclusion. The empty result has to
be reported as UNMAPPABLE and stop the criterion, not flow through it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CATALOG = Path("data/vendor/terminology_catalog.json")

_STOP = {"of", "in", "the", "and", "or", "by", "with", "for", "a", "an", "to",
         "mg", "ml", "oral", "tablet", "injection", "hr", "act", "actuat",
         "disorder", "finding", "situation", "procedure", "blood", "serum",
         "plasma", "count", "automated", "entitic", "volume", "mass"}


def _tok(s: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t and t not in _STOP]


@dataclass
class Concept:
    domain: str
    system: str | None
    code: str
    display: str
    n_resources: int
    score: float = 0.0

    def as_dict(self) -> dict:
        return {"domain": self.domain, "code": self.code, "display": self.display,
                "n_resources": self.n_resources}


@lru_cache(maxsize=1)
def _load(path: str = str(CATALOG)) -> dict[str, list[Concept]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, list[Concept]] = {}
    for rt, rows in raw.items():
        domain = {"Observation": "observation", "Condition": "condition",
                  "Medication": "medication", "Procedure": "procedure"}.get(rt, rt.lower())
        seen: dict[str, Concept] = {}
        for r in rows:
            c = r["code"]
            if c in seen:
                seen[c].n_resources += r["n_resources"]
                continue
            seen[c] = Concept(domain, r.get("system"), c, r.get("display") or "",
                              r.get("n_resources", 0))
        out[domain] = list(seen.values())
    return out


def search(term: str, domain: str, limit: int = 8) -> list[Concept]:
    """Rank vocabulary entries against a free-text clinical term.

    Deliberately lexical. An embedding search would return a plausible neighbour
    for a term the vocabulary does not contain, which is the one behaviour that
    must not happen here: a near miss on a drug class is indistinguishable from a
    hit until it silently clears a patient.
    """
    q = _tok(term)
    if not q:
        return []
    qs = set(q)
    out = []
    for c in _load().get(domain, []):
        toks = set(_tok(c.display))
        if not toks:
            continue
        hit = qs & toks
        if not hit:
            # allow a prefix match so "gliflozin" finds "empagliflozin"
            hit = {t for t in qs if any(t in d and len(t) >= 5 for d in toks)}
            if not hit:
                continue
        score = len(hit) / len(qs) + 0.25 * (len(hit) / len(toks))
        out.append(Concept(c.domain, c.system, c.code, c.display, c.n_resources, round(score, 4)))
    out.sort(key=lambda c: (-c.score, -c.n_resources, c.code))
    return out[:limit]


def search_any(terms: list[str], domain: str, limit: int = 8) -> list[Concept]:
    """Union of searches over several candidate names, de-duplicated by code."""
    seen: dict[str, Concept] = {}
    for t in terms:
        for c in search(t, domain, limit):
            prev = seen.get(c.code)
            if prev is None or c.score > prev.score:
                seen[c.code] = c
    out = sorted(seen.values(), key=lambda c: (-c.score, -c.n_resources, c.code))
    return out[:limit]


def domains() -> list[str]:
    return sorted(_load().keys())


def summary() -> dict[str, int]:
    return {d: len(v) for d, v in sorted(_load().items())}


@lru_cache(maxsize=4096)
def lookup(code: str, domain: str | None = None) -> dict | None:
    """One code to its entry in this site's catalog, or nothing.

    Used to render a predicate for review. A code the site has never recorded
    returns None, and the reviewer sees the bare code, which is the correct and
    slightly alarming thing to show them.
    """
    for dom, rows in _load().items():
        if domain and dom != domain:
            continue
        for c in rows:
            if c.code == code:
                return c.as_dict()
    return None


PANEL_COUNTS = Path("data/vendor/panel_code_counts.json")


@lru_cache(maxsize=1)
def _panel_counts(path: str = str(PANEL_COUNTS)) -> dict[str, dict]:
    """How often each code appears in the panel being screened, not in the corpus.

    These are different numbers and the difference matters. The catalog is built
    from the whole Synthea corpus; the panel is 385 alive adults drawn from it.
    Seven percent of catalog codes appear in no panel patient at all, including
    the dialysis procedure code, which has over a thousand rows in the corpus and
    none here. A reviewer told "1079 in the panel" about a code no patient in the
    panel carries has been handed a false statement in the one document that
    exists to let them check.
    """
    f = Path(path)
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8")).get("counts", {})


def panel_count(code: str) -> dict | None:
    """Rows and distinct patients carrying this code in the screened panel."""
    return _panel_counts().get(code)
