"""Compile one criterion into a typed predicate over FHIR.

This is where the model does its only real work, and it does it once per
criterion for the life of the protocol. Everything after this point is
deterministic, which is why this step gets a grounding pass, a schema validator,
a repair loop, an adversarial critic and a human signature, and why paying for
all of that is affordable: it is amortised over the whole panel.

The compiler is told to refuse. A criterion it cannot express exactly is marked
not compilable with a reason a coordinator can read, and refusing correctly is
worth as much here as compiling correctly. An approximate predicate is worse than
no predicate, because it produces a verdict with evidence attached to it.
"""
from __future__ import annotations

import json
from typing import Any

from ..ir import IRError, validate_criterion
from ..llm import Client
from ..trace import Trajectory
from .common import ask_json, require
from .grounder import ground

PROMPT_VERSION = "compiler-v1"

GRAMMAR = """PREDICATE GRAMMAR

expr:
  {"op":"and","args":[expr,...]}
  {"op":"or","args":[expr,...]}
  {"op":"not","arg":expr}
  {"op":"at_least","n":INT,"args":[expr,...]}        for "at least N of the following"
  {"op":"compare","cmp":">|>=|<|<=|==|!=","left":value,"right":value}
  {"op":"between","value":value,"low":NUM,"high":NUM,"inclusive":[BOOL,BOOL]}
  {"op":"exists","query":query}
  {"op":"const","value":"TRUE|FALSE|UNKNOWN"}

value:
  {"val":"age"}                                       age in years at the screening date
  {"val":"sex"}
  {"val":"literal","number":NUM,"unit":"STR"}
  {"val":"observation","codes":["LOINC",...],"unit":"STR","agg":"latest|min|max|first",
   "within_days":INT|null}
  {"val":"derived","name":"egfr_ckdepi_2021|bmi|systolic_bp|diastolic_bp","within_days":INT|null}
  {"val":"count","query":query}

query:
  {"domain":"condition|medication|procedure|observation","codes":["CODE",...],
   "within_days":INT|null,"active_only":BOOL,"absent_means":"false|unknown"}

RULES

* `unit` on an observation is the unit the CRITERION is written in, not the unit
  the record stores. Conversion is handled for you. State the criterion's unit.
* `within_days` encodes a temporal window. "within the past 3 months" is 91.
  "within 6 months" is 183. "within 1 month" is 30. null means no window.
* `absent_means` decides what an empty result means, and it is the most
  consequential field here.
    "false"   - this record can be trusted to be complete for these codes, so
                nothing found means the patient does not have it. Reasonable for
                a reconciled medication list or a coded problem list.
    "unknown" - silence proves nothing. Correct for anything that may have
                happened at another site, for events like a hospitalisation, and
                for anything acute or recent.
  When in doubt choose "unknown". A wrong "false" rules a patient out of a trial
  on the strength of a gap in their record, and nobody ever audits that.
* Never invent a code. Use only codes from the GROUNDED CONCEPTS block.
* An exclusion criterion is expressed as the thing that would EXCLUDE the
  patient. `exists(current SGLT2 inhibitor)` is a correct exclusion predicate.
* Model the criterion as written. Do not add a clinical safety margin, do not
  widen a range, and do not add a condition the text does not state."""

PLAN_SYSTEM = """You prepare clinical trial eligibility criteria for automated checking against
structured medical records.

You are careful about what a medical record can and cannot settle. Most criteria
in a real protocol cannot be settled from a record at all, and saying so is the
correct answer rather than a failure."""

PLAN = """Decide whether this criterion can be checked from a structured medical record,
and list the clinical concepts it needs.

Criterion ({kind}, category {category}):
  {text}

A criterion is checkable ONLY if every part of it can be settled from coded
record data: demographics, coded diagnoses, coded medications, coded procedures,
or numeric laboratory and vital-sign values, with dates.

It is NOT checkable if it needs any of:
  - consent, willingness, capacity, ability to comply or to attend
  - the investigator's opinion, or a judgement about suitability
  - a measurement a record does not normally hold (waist circumference,
    performance status, imaging read-outs, questionnaire scores, elastography)
  - counting prior lines of therapy, or a washout expressed in half-lives
  - a bound relative to a laboratory's own reference range, such as "2.5x the
    upper limit of normal", since the limit is not a fixed number
  - contraception, pregnancy intention, or residence and travel plans
  - enrolment in another study

Return JSON only:

{{"checkable": true,
  "reason": "one sentence; if not checkable, name the specific blocker",
  "concepts": [{{"name":"SGLT2 inhibitor","domain":"medication",
                 "intent":"currently prescribed drug of this class"}}]}}

`concepts` lists every clinical thing that must be looked up by code. Leave it
empty when the criterion uses only age or sex. Use the exact domain the record
would store it in."""

EMIT_SYSTEM = """You translate one clinical trial eligibility criterion into a formal predicate.

You are precise and literal. You express exactly what the criterion says, and you
use only the codes you are given."""

EMIT = """Translate this criterion into a predicate.

Criterion ({kind}, category {category}):
  {text}

{grammar}

GROUNDED CONCEPTS
=================
{grounded}

Return JSON only:

{{"expr": <expr>,
  "unit_note": "which units the criterion is written in",
  "absence_note": "why each absent_means was chosen",
  "confidence": "high|medium|low"}}"""


#: Near-misses on the domain enum, mapped to the FHIR resource they mean.
#: Smaller models reliably get the clinical reasoning right and the enum wrong:
#: "laboratory_value" for an observation, "drug" for a medication. Rejecting
#: those outright spends the whole repair budget on vocabulary rather than on
#: substance, so a known synonym is normalised and the substitution is recorded.
DOMAIN_ALIASES = {
    "observation": "observation", "lab": "observation", "labs": "observation",
    "laboratory": "observation", "lab_value": "observation",
    "laboratory_value": "observation", "laboratory_test": "observation",
    "lab_test": "observation", "measurement": "observation", "vital": "observation",
    "vital_sign": "observation", "vitals": "observation", "test": "observation",
    "result": "observation", "lab_result": "observation",
    "medication": "medication", "drug": "medication", "med": "medication",
    "medicine": "medication", "prescription": "medication", "medications": "medication",
    "pharmacy": "medication", "therapy": "medication", "treatment": "medication",
    "condition": "condition", "diagnosis": "condition", "disease": "condition",
    "disorder": "condition", "problem": "condition", "comorbidity": "condition",
    "history": "condition", "conditions": "condition",
    "procedure": "procedure", "surgery": "procedure", "operation": "procedure",
    "intervention": "procedure", "procedures": "procedure",
}


def canon_domain(x: Any) -> str | None:
    if not isinstance(x, str):
        return None
    return DOMAIN_ALIASES.get(x.strip().lower().replace(" ", "_").replace("-", "_"))


def _v_plan(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    require(isinstance(p.get("checkable"), bool), "checkable must be true or false")
    require(isinstance(p.get("reason"), str) and p["reason"].strip(),
            "reason must be a non-empty string")
    cs = p.get("concepts", [])
    require(isinstance(cs, list), "concepts must be a list")
    for i, c in enumerate(cs):
        require(isinstance(c, dict), f"concepts[{i}] must be an object")
        require(isinstance(c.get("name"), str) and c["name"].strip(),
                f"concepts[{i}].name must be a non-empty string")
        require(canon_domain(c.get("domain")) is not None,
                f"concepts[{i}].domain is {c.get('domain')!r}; it must be exactly one of "
                f"condition, medication, procedure, observation")


def _v_emit(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    require(isinstance(p.get("expr"), dict), "expr must be an object")
    require(p.get("confidence") in {"high", "medium", "low"},
            "confidence must be high, medium or low")


def _render_grounded(g: list[dict]) -> str:
    if not g:
        return "(none needed: this criterion uses only age or sex)"
    out = []
    for rec in g:
        if rec["status"] == "UNMAPPABLE":
            out.append(f"* {rec['concept']} ({rec['domain']}): NOT AVAILABLE in this "
                       f"vocabulary. {rec['reason']}")
            continue
        pairs = ", ".join(f'"{c}"' for c in rec["codes"])
        names = "; ".join(d[:44] for d in rec.get("displays", [])[:6])
        out.append(f"* {rec['concept']} ({rec['domain']}) [{rec['status']}]\n"
                   f"    codes: [{pairs}]\n    meaning: {names}")
    return "\n".join(out)


def compile_criterion(client: Client, criterion: dict, traj: Trajectory | None = None,
                      ground_cache: dict[str, dict] | None = None) -> tuple[dict, Trajectory]:
    """Compile one segmented criterion into a validated IR record."""
    cid = criterion["criterion_id"]
    traj = traj or Trajectory("compiler", cid)
    traj.instructions(PLAN_SYSTEM + "\n\n" + PLAN + "\n\n---\n\n" + EMIT_SYSTEM + "\n\n"
                      + EMIT.replace("{grammar}", GRAMMAR), PROMPT_VERSION)
    traj.input(**{k: criterion[k] for k in ("criterion_id", "kind", "category", "source_text")})

    base = {"criterion_id": cid, "nct_id": criterion.get("nct_id", ""),
            "kind": criterion["kind"], "category": criterion["category"],
            "source_text": criterion["source_text"],
            "content_hash": criterion.get("content_hash", "")}

    # 1. can this be checked at all, and what does it need
    plan = ask_json(client, traj,
                    [{"role": "system", "content": PLAN_SYSTEM},
                     {"role": "user", "content": PLAN.format(**criterion)}],
                    _v_plan, tag=f"compile-plan:{cid}", prompt_version=PROMPT_VERSION)

    if not plan["checkable"]:
        rec = {**base, "compilable": False,
               "reason_not_compilable": plan["reason"], "blocked_at": "plan"}
        validate_criterion(rec)
        traj.final(**{k: rec[k] for k in ("compilable", "reason_not_compilable")})
        return rec, traj

    # 2. ground every concept it needs against this site's vocabulary
    cache = ground_cache if ground_cache is not None else {}
    grounded: list[dict] = []
    for c in plan.get("concepts", []):
        raw = c.get("domain")
        c["domain"] = canon_domain(raw)
        if c["domain"] != raw:
            traj.revision("normalised concept domain", raw, c["domain"])
        key = f"{c['domain']}::{c['name'].strip().lower()}"
        if key in cache:
            traj.tool_call("ground_cache.hit", key=key)
            traj.tool_result("ground_cache.hit", cache[key])
        else:
            cache[key] = ground(client, c["name"], c["domain"], c.get("intent", ""), traj)
        grounded.append(cache[key])

    unmappable = [g for g in grounded if g["status"] == "UNMAPPABLE"]
    if unmappable:
        # The concept has no representation in these records, so no predicate over
        # them can decide the criterion. Committing anyway is the failure this
        # branch exists to prevent.
        why = "; ".join(f"{g['concept']}: {g['reason']}" for g in unmappable)
        rec = {**base, "compilable": False,
               "reason_not_compilable": (
                   f"cannot be represented in this site's vocabulary. {why}"),
               "blocked_at": "grounding",
               "unmappable_concepts": [g["concept"] for g in unmappable]}
        validate_criterion(rec)
        traj.final(**{k: rec[k] for k in ("compilable", "reason_not_compilable")})
        return rec, traj

    # 3. emit the predicate, restricted to codes that exist
    allowed = {c for g in grounded for c in g["codes"]}

    def _v_emit_scoped(p: Any) -> None:
        _v_emit(p)
        probe = {**base, "compilable": True, "expr": p["expr"]}
        try:
            validate_criterion(probe)
        except IRError as exc:
            raise AssertionError(str(exc)) from None
        from ..ir import referenced_codes
        used = {code for _, code in referenced_codes(p["expr"])}
        from ..ir import derived_inputs
        derived_ok = {c for n in ("egfr_ckdepi_2021", "bmi", "systolic_bp", "diastolic_bp")
                      for c in derived_inputs(n)}
        stray = used - allowed - derived_ok
        require(not stray, f"expr uses code(s) {sorted(stray)} that are not in the "
                           f"GROUNDED CONCEPTS block; use only "
                           f"{sorted(allowed) if allowed else 'age/sex only'}")

    emit = ask_json(client, traj,
                    [{"role": "system", "content": EMIT_SYSTEM},
                     {"role": "user", "content": EMIT.format(
                         grammar=GRAMMAR, grounded=_render_grounded(grounded), **criterion)}],
                    _v_emit_scoped, tag=f"compile-emit:{cid}", prompt_version=PROMPT_VERSION)

    rec = {**base, "compilable": True, "expr": emit["expr"],
           "grounded": [{"concept": g["concept"], "domain": g["domain"],
                         "status": g["status"], "codes": g["codes"]} for g in grounded],
           "unit_note": emit.get("unit_note", ""),
           "absence_note": emit.get("absence_note", ""),
           "confidence": emit["confidence"],
           "compiler_prompt_version": PROMPT_VERSION}
    validate_criterion(rec)
    traj.final(compilable=True, expr=rec["expr"], confidence=rec["confidence"])
    return rec, traj


def predicate_sha256(rec: dict) -> str:
    import hashlib
    body = json.dumps({"criterion_id": rec["criterion_id"],
                       "compilable": rec["compilable"],
                       "expr": rec.get("expr"),
                       "reason_not_compilable": rec.get("reason_not_compilable")},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
