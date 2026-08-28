"""Adversarial review of a compiled predicate.

A schema validator proves a predicate is well formed. It cannot prove the
predicate means what the criterion says, and that gap is where the expensive
mistakes live: a window off by a month, a threshold read as inclusive, an
exclusion compiled as its own negation, a closed-world assumption on data that
routinely lives at another hospital.

So the critic does not give an opinion. It is required to produce a
counterexample: a specific patient, described in facts, together with the truth
value the criterion should take for that patient. That counterexample is then
built into a chart and the predicate is actually run against it. If the predicate
returns what the critic predicted, the critic was wrong and the finding is
dropped. If it does not, there is a real disagreement between prose and
predicate, and the exact patient that exposes it goes back to the compiler.

The critic is therefore falsifiable by the same engine it is auditing, which
means a talkative model cannot manufacture findings, and a lazy one cannot hide
behind a general remark.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from ..chart import Chart, Coding, ConditionRow, MedicationRow, ObservationRow, ProcedureRow
from ..evaluator import Evaluator
from ..llm import Client
from ..logic import TV
from ..trace import Trajectory
from .common import ask_json, require

PROMPT_VERSION = "critic-v1"

SYSTEM = """You review formal predicates written from clinical trial eligibility criteria.

Your job is to find a patient for whom the predicate and the criterion text
disagree. You are not asked whether the predicate looks reasonable. You are asked
to break it, and a specific patient who breaks it is the only thing that counts."""

INSTRUCTIONS = """Review this compiled criterion.

CRITERION ({kind}):
  {text}

COMPILED PREDICATE:
{expr}

CODES AVAILABLE (you may only use these):
{codes}

Look specifically for:
  1. Window errors. Is `within_days` right, and does an event just inside or just
     outside the window behave correctly? "within 6 months" is 183 days.
  2. Boundary errors. Should the comparison be > or >=? Does the criterion say
     "between 6.5 and 10" (inclusive) or "above 6.5"?
  3. Direction errors. For an EXCLUSION, the predicate must be TRUE for a patient
     who should be EXCLUDED. A predicate that is true for eligible patients is
     inverted.
  4. Absence errors. Is any `absent_means` set to "false" for something that
     could easily have happened at another hospital, or that is acute or recent?
     Ruling a patient out because their record is silent is the worst failure
     available here.
  5. Missing or added conditions. Does the predicate check everything the
     criterion states, and nothing it does not?

If you find a problem, construct a patient that demonstrates it and say what
truth value the CRITERION TEXT should take for that patient.

Truth values: TRUE means the patient satisfies the criterion text, FALSE means
they do not, UNKNOWN means the record shown cannot settle it.

Patient facts use days before the screening date. `days_ago: 30` is a month ago.
Include only facts you want the record to contain; anything you omit is absent
from the record.

Return JSON only:

{{"verdict": "OK" | "REVISE",
  "findings": [{{"issue": "one sentence", "kind": "window|boundary|direction|absence|scope",
                 "severity": "high|medium|low"}}],
  "counterexample": {{
     "patient": {{"age": 62, "sex": "female",
                  "observations": [{{"code":"4548-4","value":7.2,"unit":"%","days_ago":30}}],
                  "conditions": [{{"code":"22298006","days_ago":200}}],
                  "medications": [{{"code":"860975","days_ago":20,"status":"active"}}],
                  "procedures": []}},
     "expected_truth": "TRUE|FALSE|UNKNOWN",
     "why": "one sentence explaining what the criterion text says for this patient"}}}}

When the predicate is faithful, return verdict "OK", an empty findings list, and
counterexample null. Do not invent a problem to look useful."""


def _v(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    require(p.get("verdict") in {"OK", "REVISE"}, "verdict must be OK or REVISE")
    require(isinstance(p.get("findings", []), list), "findings must be a list")
    if p["verdict"] == "REVISE":
        require(isinstance(p.get("findings"), list) and p["findings"],
                "a REVISE verdict needs at least one finding")
        ce = p.get("counterexample")
        require(isinstance(ce, dict), "a REVISE verdict needs a counterexample object")
        require(isinstance(ce.get("patient"), dict), "counterexample.patient must be an object")
        require(ce.get("expected_truth") in {"TRUE", "FALSE", "UNKNOWN"},
                "counterexample.expected_truth must be TRUE, FALSE or UNKNOWN")


def build_chart(spec: dict, index: dt.date = dt.date(2021, 11, 1)) -> Chart:
    """Materialise a critic's patient description into a real chart."""
    def when(d: Any) -> dt.date | None:
        try:
            return index - dt.timedelta(days=int(d))
        except (TypeError, ValueError):
            return None

    age = spec.get("age")
    birth = dt.date(index.year - int(age), index.month, index.day) if age is not None else None
    obs, conds, meds, procs = [], [], [], []
    for i, o in enumerate(spec.get("observations") or []):
        obs.append(ObservationRow([Coding("http://loinc.org", str(o.get("code")), str(o.get("code")))],
                                  o.get("value"), o.get("unit"), None,
                                  when(o.get("days_ago", 1)), f"ce-obs-{i}"))
    for i, c in enumerate(spec.get("conditions") or []):
        conds.append(ConditionRow([Coding("http://snomed.info/sct", str(c.get("code")),
                                          str(c.get("code")))],
                                  when(c.get("days_ago", 30)),
                                  when(c["abated_days_ago"]) if c.get("abated_days_ago") else None,
                                  c.get("clinical_status", "active"), f"ce-cond-{i}"))
    for i, m in enumerate(spec.get("medications") or []):
        meds.append(MedicationRow([Coding("rxnorm", str(m.get("code")), str(m.get("code")))],
                                  when(m.get("days_ago", 30)), m.get("status", "active"),
                                  f"ce-med-{i}"))
    for i, p in enumerate(spec.get("procedures") or []):
        procs.append(ProcedureRow([Coding("http://snomed.info/sct", str(p.get("code")),
                                          str(p.get("code")))],
                                  when(p.get("days_ago", 30)), f"ce-proc-{i}"))
    return Chart(patient_id="counterexample", birth_date=birth, sex=spec.get("sex"),
                 deceased_date=None, index_date=index, conditions=conds, observations=obs,
                 medications=meds, procedures=procs)


def check_counterexample(expr: dict, ce: dict) -> dict:
    """Run the predicate on the critic's patient and compare with its prediction."""
    chart = build_chart(ce["patient"])
    res = Evaluator(chart).eval_expr(expr)
    expected = TV(ce["expected_truth"])
    return {
        "actual": res.value.value,
        "expected": expected.value,
        "confirmed": res.value is not expected,
        "engine_reason": res.reason,
    }


def review(client: Client, compiled: dict, traj: Trajectory | None = None
           ) -> tuple[dict, Trajectory]:
    """Review one compiled criterion. Findings survive only if executable."""
    import json

    traj = traj or Trajectory("critic", compiled["criterion_id"])
    traj.instructions(SYSTEM + "\n\n" + INSTRUCTIONS, PROMPT_VERSION)
    traj.input(criterion_id=compiled["criterion_id"], kind=compiled["kind"],
               source_text=compiled["source_text"])

    if not compiled.get("compilable"):
        out = {"verdict": "OK", "findings": [], "counterexample": None,
               "note": "not compilable, nothing to review"}
        traj.final(**out)
        return out, traj

    codes = sorted({c for g in compiled.get("grounded", []) for c in g["codes"]})
    payload = ask_json(
        client, traj,
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": INSTRUCTIONS.format(
             kind=compiled["kind"], text=compiled["source_text"],
             expr=json.dumps(compiled["expr"], indent=1),
             codes=", ".join(codes) or "(age and sex only)")}],
        _v, tag=f"critic:{compiled['criterion_id']}", prompt_version=PROMPT_VERSION)

    result = {"verdict": payload["verdict"], "findings": payload.get("findings", []),
              "counterexample": payload.get("counterexample"), "executed": None}

    if payload["verdict"] == "REVISE":
        ce = payload["counterexample"]
        traj.tool_call("execute_counterexample", patient=ce["patient"],
                       expected_truth=ce["expected_truth"])
        try:
            chk = check_counterexample(compiled["expr"], ce)
        except Exception as exc:
            chk = {"error": f"{type(exc).__name__}: {exc}", "confirmed": False}
        traj.tool_result("execute_counterexample", chk)
        result["executed"] = chk

        if chk.get("confirmed"):
            traj.critic_finding("CONFIRMED",
                                "; ".join(f["issue"] for f in result["findings"]), ce)
        else:
            # The predicate already behaves as the critic said it should, so the
            # objection does not survive execution and is not sent onward.
            result["verdict"] = "OK"
            result["dismissed_findings"] = result.pop("findings")
            result["findings"] = []
            traj.critic_finding(
                "DISMISSED",
                f"the predicate returned {chk.get('actual')} on the critic's own patient, "
                f"which is what the critic said the criterion requires", ce)

    traj.final(verdict=result["verdict"], n_findings=len(result["findings"]),
               executed=result["executed"])
    return result, traj
