"""Resolve a clinical concept to codes in this site's vocabulary, or refuse.

Four outcomes, and the last two are the ones that matter.

  MAPPED        the concept resolves to codes that exist in these records
  PARTIAL       some members resolve, others are absent from the vocabulary
  BROADER_ONLY  nothing states the concept, but a code that contains it exists
  UNMAPPABLE    nothing in this vocabulary can represent the concept

BROADER_ONLY is the one the README calls this design's sharp edge, and this
docstring used to omit it while the function below returned it. A reader opening
the file to check the argument found three outcomes and no sign of the mechanism.

UNMAPPABLE exists because of a failure that is easy to build and almost
impossible to see. Asked to ground "SGLT2 inhibitors" against a corpus that
contains no gliflozin at all, a grounder that returns an empty code list produces
a query matching nothing, and a closed-world reading of "nothing matched" reports
that the patient is not taking one. Every patient then clears that exclusion,
confidently, with a citation-shaped hole where the evidence should be. The
concept has to stop the criterion instead.

The division of labour is deliberate. The model supplies world knowledge, which
drug names belong to a class, and it is good at that. The vocabulary lookup is
deterministic and local, because whether a code exists in these records is a fact
about the records and not a thing to be inferred.
"""
from __future__ import annotations

from typing import Any

from .. import terminology
from ..llm import Client
from ..trace import Trajectory
from .common import ask_json, require

PROMPT_VERSION = "grounder-v3"

EXPAND_SYSTEM = """You are a clinical terminologist. You expand a clinical concept into the
specific named things a medical record would actually store for it."""

EXPAND = """Expand this clinical concept into concrete searchable names.

Concept: {concept}
Record domain: {domain}

For a drug class, list the generic ingredient names that belong to the class.
For a diagnosis, list the specific condition names, including the common
sub-types a record might code instead of the general term.
For a laboratory test, list the names and common synonyms of the measurement.

List what belongs to the concept in general clinical practice. Do NOT try to
guess what this particular site happens to record; that is looked up separately.

Return JSON only:
{{"names": ["empagliflozin", "dapagliflozin"], "note": "one short line"}}

Give between 1 and 15 names."""

SELECT_SYSTEM = """You match a clinical concept against a specific site's coded vocabulary.

You choose only from the candidates given. You never invent a code. If none of
the candidates genuinely represents the concept, you say so plainly, because a
wrong match here is worse than no match."""

SELECT = """Concept: {concept}
Record domain: {domain}
Meaning required: {intent}

Candidate entries from this site's vocabulary:
{candidates}

Select every candidate that genuinely represents the concept. Judge by what the
entry means, not by whether the words look similar. A different measurement that
shares a word is not a match: "Respiratory rate" is not a glomerular filtration
rate, and "Chronic sinusitis" is not chronic kidney disease.

The display text beside each code is whatever the source system chose to store.
It is frequently abbreviated, locally worded, or vaguer than the code it labels,
and it is not the code's definition. Judge the concept the code denotes. Where you
recognise a code and its display disagree about how specific the concept is, the
code decides, and name the code you relied on in `why` for the ones you rejected.
This does not license guessing: a code you do not recognise is judged on its
display like any other candidate, and a display that is vaguer than the concept is
still a reason to reject a code you have no independent knowledge of.

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

A candidate can also be BROADER than the concept: it contains what the criterion
asks for and other things as well. A site that records every diabetes diagnosis
under one unspecified diabetes code has a code that is broader than "type 2
diabetes mellitus". A site whose only asthma code is "chronic lower respiratory
disease" has one that is broader than asthma.

Put those in `broader_codes`, not in `codes`. The difference decides what happens
to a patient. A code in `codes` proves the concept when it is present. A code in
`broader_codes` cannot prove it, and the criterion comes back undetermined for
that patient rather than satisfied. Its absence still counts: a patient with no
diabetes code of any kind does not have type 2 diabetes either.

Do not use `broader_codes` for a code that is merely related, or for a
complication of the concept, or for a different thing that shares a word. Only
for a code whose meaning genuinely contains the concept.

If no candidate represents the concept and none contains it, return both lists
empty. That is a normal and useful answer.

Return JSON only:
{{"codes": ["4548-4"], "broader_codes": [],
  "rejected": [{{"code": "718-7", "why": "different analyte"}}],
  "confidence": "high"}}"""


def _v_expand(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    names = p.get("names")
    require(isinstance(names, list) and names, "names must be a non-empty list")
    require(all(isinstance(n, str) and n.strip() for n in names), "names must be strings")
    require(len(names) <= 25, f"at most 25 names, got {len(names)}")


def _v_select(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    require(isinstance(p.get("codes"), list), "codes must be a list (possibly empty)")
    require(all(isinstance(c, str) for c in p["codes"]), "codes must be strings")
    b = p.get("broader_codes", [])
    require(isinstance(b, list) and all(isinstance(c, str) for c in b),
            "broader_codes must be a list of strings (possibly empty)")
    require(not (set(p["codes"]) & set(b)),
            "a code cannot be in both codes and broader_codes; decide whether it "
            "means the concept or merely contains it")
    require(p.get("confidence") in {"high", "medium", "low"},
            "confidence must be high, medium or low")


def ground(client: Client, concept: str, domain: str, intent: str = "",
           traj: Trajectory | None = None, search_limit: int = 12) -> dict:
    """Ground one concept. Returns a record with a status and the codes found."""
    traj = traj or Trajectory("grounder", f"{domain}-{concept}")
    traj.instructions(EXPAND_SYSTEM + "\n\n" + EXPAND + "\n\n---\n\n"
                      + SELECT_SYSTEM + "\n\n" + SELECT, PROMPT_VERSION)
    traj.input(concept=concept, domain=domain, intent=intent)

    # 1. world knowledge: what belongs to this concept
    exp = ask_json(client, traj,
                   [{"role": "system", "content": EXPAND_SYSTEM},
                    {"role": "user", "content": EXPAND.format(concept=concept, domain=domain)}],
                   _v_expand, tag=f"ground-expand:{domain}:{concept}",
                   prompt_version=PROMPT_VERSION)
    names = [n.strip() for n in exp["names"]]

    # 2. local fact: what this vocabulary can represent
    traj.tool_call("terminology.search_any", terms=names, domain=domain, limit=search_limit)
    cands = terminology.search_any(names, domain, limit=search_limit)
    traj.tool_result("terminology.search_any", [c.as_dict() for c in cands])

    if not cands:
        rec = {"concept": concept, "domain": domain, "status": "UNMAPPABLE", "codes": [],
               "broader_codes": [], "expanded_names": names,
               "reason": (f"no entry in this site's {domain} vocabulary matches any of "
                          f"{', '.join(names[:6])}"
                          + (" and others" if len(names) > 6 else "")),
               "confidence": "high"}
        traj.final(**rec)
        return rec

    # 3. judgement: which candidates actually mean the concept
    table = "\n".join(f"  {c.code:>16s}  {c.display[:70]}   (in {c.n_resources} resources)"
                      for c in cands)
    sel = ask_json(client, traj,
                   [{"role": "system", "content": SELECT_SYSTEM},
                    {"role": "user", "content": SELECT.format(
                        concept=concept, domain=domain, intent=intent or "(not specified)",
                        candidates=table)}],
                   _v_select, tag=f"ground-select:{domain}:{concept}",
                   prompt_version=PROMPT_VERSION)

    valid = {c.code for c in cands}
    chosen = [c for c in sel["codes"] if c in valid]
    broader = [c for c in (sel.get("broader_codes") or [])
               if c in valid and c not in chosen]
    hallucinated = [c for c in sel["codes"] if c not in valid]
    if hallucinated:
        # Codes not on the candidate list are dropped rather than trusted: the
        # point of the shortlist is that it is the set of codes that exist here.
        traj.validation_error(f"dropped {len(hallucinated)} code(s) not in the candidate "
                              f"list: {hallucinated}")

    if not chosen and broader:
        # The site has the concept, at a coarser grain than the criterion needs.
        # That is not the same as not having it, and treating it as UNMAPPABLE
        # throws away the half of the answer that is real: absence of the broader
        # code rules the patient out, presence leaves the question open.
        rec = {"concept": concept, "domain": domain, "status": "BROADER_ONLY",
               "codes": [], "broader_codes": sorted(broader),
               "expanded_names": names,
               "displays": [c.display for c in cands if c.code in broader],
               "reason": ("this vocabulary codes the concept only at a coarser grain; "
                          "presence cannot settle the criterion and absence can"),
               "rejected": sel.get("rejected", []), "confidence": sel["confidence"]}
        traj.final(**rec)
        return rec

    if not chosen:
        rec = {"concept": concept, "domain": domain, "status": "UNMAPPABLE", "codes": [],
               "broader_codes": [], "expanded_names": names,
               "reason": ("the vocabulary returned candidates but none of them represents "
                          "the concept"),
               "rejected": sel.get("rejected", []), "confidence": sel["confidence"]}
        traj.final(**rec)
        return rec

    covered = {n.lower() for n in names
               if any(n.lower() in c.display.lower() for c in cands if c.code in chosen)}
    status = "MAPPED" if len(covered) >= max(1, len(names) // 3) else "PARTIAL"
    rec = {"concept": concept, "domain": domain, "status": status, "codes": sorted(chosen),
           "broader_codes": sorted(broader),
           "expanded_names": names,
           "matched_names": sorted(covered),
           "unmatched_names": sorted(n for n in names if n.lower() not in covered),
           "displays": [c.display for c in cands if c.code in chosen],
           "confidence": sel["confidence"],
           "reason": f"{len(chosen)} of {len(cands)} candidates selected"}
    traj.final(**rec)
    return rec
