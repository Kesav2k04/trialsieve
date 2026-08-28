"""Resolve a clinical concept to codes in this site's vocabulary, or refuse.

Three outcomes, and the third is the one that matters.

  MAPPED       the concept resolves to codes that exist in these records
  PARTIAL      some members resolve, others are absent from the vocabulary
  UNMAPPABLE   nothing in this vocabulary can represent the concept

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

PROMPT_VERSION = "grounder-v1"

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

For a drug class, select the entries whose ingredient belongs to that class.
Different strengths or formulations of the same ingredient are all matches.

If no candidate represents the concept, return an empty list. That is a normal
and useful answer.

Return JSON only:
{{"codes": ["4548-4"], "rejected": [{{"code": "718-7", "why": "different analyte"}}],
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
               "expanded_names": names,
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
    hallucinated = [c for c in sel["codes"] if c not in valid]
    if hallucinated:
        # Codes not on the candidate list are dropped rather than trusted: the
        # point of the shortlist is that it is the set of codes that exist here.
        traj.validation_error(f"dropped {len(hallucinated)} code(s) not in the candidate "
                              f"list: {hallucinated}")

    if not chosen:
        rec = {"concept": concept, "domain": domain, "status": "UNMAPPABLE", "codes": [],
               "expanded_names": names,
               "reason": ("the vocabulary returned candidates but none of them represents "
                          "the concept"),
               "rejected": sel.get("rejected", []), "confidence": sel["confidence"]}
        traj.final(**rec)
        return rec

    covered = {n.lower() for n in names
               if any(n.lower() in c.display.lower() for c in cands if c.code in chosen)}
    status = "MAPPED" if len(covered) >= max(1, len(names) // 3) else "PARTIAL"
    rec = {"concept": concept, "domain": domain, "status": status, "codes": sorted(chosen),
           "expanded_names": names,
           "matched_names": sorted(covered),
           "unmatched_names": sorted(n for n in names if n.lower() not in covered),
           "displays": [c.display for c in cands if c.code in chosen],
           "confidence": sel["confidence"],
           "reason": f"{len(chosen)} of {len(cands)} candidates selected"}
    traj.final(**rec)
    return rec
