"""Deterministic evaluation of a compiled criterion against one chart.

No model is called here. Once a criterion has been compiled and signed off, the
answer for any patient is a pure function of the IR and the record, which is
what makes a verdict reproducible, auditable and free.

Every result carries the resources it read. A verdict a coordinator cannot
trace back to a dated row in the chart is not worth showing them.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Any

from .chart import Chart, ObservationRow
from .logic import TV, T, F, U, k_and, k_at_least, k_not, k_or
from .units import convert


@dataclass
class Evidence:
    """One record fact that contributed to a verdict."""
    kind: str          # observation | condition | medication | procedure | demographic | absent | derived
    code: str
    display: str
    value: str
    date: str
    resource_id: str
    note: str = ""

    def cite(self) -> str:
        d = f" ({self.date})" if self.date else ""
        n = f" - {self.note}" if self.note else ""
        return f"{self.display} = {self.value}{d}{n}"


@dataclass
class Result:
    value: TV
    reason: str
    evidence: list[Evidence] = field(default_factory=list)
    children: list["Result"] = field(default_factory=list)
    op: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value.value,
            "op": self.op,
            "reason": self.reason,
            "evidence": [vars(e) for e in self.evidence],
            "children": [c.to_dict() for c in self.children],
        }

    def all_evidence(self) -> list[Evidence]:
        out = list(self.evidence)
        for c in self.children:
            out.extend(c.all_evidence())
        seen, uniq = set(), []
        for e in out:
            key = (e.resource_id, e.code, e.value, e.date)
            if key not in seen:
                seen.add(key)
                uniq.append(e)
        return uniq

    def unknown_reasons(self) -> list[str]:
        """Why this came out UNKNOWN, gathered from the leaves that caused it."""
        if self.value is not U:
            return []
        if not self.children:
            return [self.reason]
        out: list[str] = []
        for c in self.children:
            out.extend(c.unknown_reasons())
        return out or [self.reason]


class Evaluator:
    def __init__(self, chart: Chart, unit_policy: str = "code_authoritative",
                 default_absent_means: str | None = None) -> None:
        self.chart = chart
        self.unit_policy = unit_policy
        #: Set to force every query to one policy. Used only by the ablation that
        #: measures what the per-query closed-world flag is worth.
        self.default_absent_means = default_absent_means

    # -- expressions --------------------------------------------------------
    def eval_expr(self, e: dict) -> Result:
        op = e["op"]
        if op == "and":
            kids = [self.eval_expr(a) for a in e["args"]]
            v = k_and(k.value for k in kids)
            return Result(v, self._why_bool(v, kids, "and"), children=kids, op=op)
        if op == "or":
            kids = [self.eval_expr(a) for a in e["args"]]
            v = k_or(k.value for k in kids)
            return Result(v, self._why_bool(v, kids, "or"), children=kids, op=op)
        if op == "not":
            kid = self.eval_expr(e["arg"])
            v = k_not(kid.value)
            return Result(v, f"negation of a {kid.value.value} sub-result", children=[kid], op=op)
        if op == "at_least":
            kids = [self.eval_expr(a) for a in e["args"]]
            n = e["n"]
            v = k_at_least(n, [k.value for k in kids])
            t = sum(1 for k in kids if k.value is T)
            u = sum(1 for k in kids if k.value is U)
            return Result(v, f"at least {n} of {len(kids)}: {t} proven, {u} undetermined",
                          children=kids, op=op)
        if op == "const":
            return Result(TV(e["value"]), "constant", op=op)
        if op == "compare":
            return self._compare(e)
        if op == "between":
            return self._between(e)
        if op == "exists":
            return self._exists(e["query"])
        raise ValueError(f"unknown op {op!r}")

    @staticmethod
    def _why_bool(v: TV, kids: list[Result], op: str) -> str:
        if op == "and":
            if v is F:
                for k in kids:
                    if k.value is F:
                        return f"conjunction fails: {k.reason}"
            if v is U:
                return "conjunction undetermined: " + "; ".join(
                    r for k in kids if k.value is U for r in k.unknown_reasons()[:1])
            return "every conjunct holds"
        if v is T:
            for k in kids:
                if k.value is T:
                    return f"disjunction holds: {k.reason}"
        if v is U:
            return "disjunction undetermined: " + "; ".join(
                r for k in kids if k.value is U for r in k.unknown_reasons()[:1])
        return "no disjunct holds"

    # -- leaves -------------------------------------------------------------
    def _compare(self, e: dict) -> Result:
        # Both operands are brought to one target unit before anything is compared.
        # Passing the target to only one side left the other in whatever unit it
        # happened to carry, so a threshold written in mg/mmol could be compared
        # against a value stored in mg/g: the same 8.84x error units.py exists to
        # catch, in the direction that wrongly excludes a patient.
        target = self._unit_of(e["left"]) or self._unit_of(e["right"])
        left = self._value(e["left"], want_unit=target)
        right = self._value(e["right"], want_unit=target)
        ev = left[2] + right[2]
        if left[0] is None:
            return Result(U, left[1], evidence=ev, op="compare")
        if right[0] is None:
            return Result(U, right[1], evidence=ev, op="compare")
        a, b, cmp = left[0], right[0], e["cmp"]
        ok = {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b,
              "==": a == b, "!=": a != b}[cmp]
        # The unit belongs in the sentence. A converted operand is a number that
        # appears nowhere in the record, so a reviewer reading "30 <= 16.97" with
        # no unit cannot check it against the 150 mg/g cited beside it.
        unit = _unit_label(target)
        return Result(T if ok else F,
                      f"{_fmt(a)} {cmp} {_fmt(b)}{unit} is {ok}", evidence=ev, op="compare")

    def _between(self, e: dict) -> Result:
        val, why, ev = self._value(e["value"])
        if val is None:
            return Result(U, why, evidence=ev, op="between")
        lo, hi = e["low"], e["high"]
        inc = e.get("inclusive", [True, True])
        ok = (val >= lo if inc[0] else val > lo) and (val <= hi if inc[1] else val < hi)
        unit = _unit_label(self._unit_of(e["value"]))
        return Result(T if ok else F,
                      f"{_fmt(val)} in [{lo}, {hi}]{unit} is {ok}",
                      evidence=ev, op="between")

    def _exists(self, q: dict) -> Result:
        domain, codes = q["domain"], q["codes"]
        days = q.get("within_days")
        active = bool(q.get("active_only"))
        absent = self.default_absent_means or q["absent_means"]

        if domain == "condition":
            rows = self.chart.conditions_for(codes, days, active)
            ev = [Evidence("condition", _c(r), _d(r), "present",
                           str(r.onset or ""), r.resource_id) for r in rows]
        elif domain == "medication":
            rows = self.chart.medications_for(codes, days, active)
            ev = [Evidence("medication", _c(r), _d(r), r.status or "",
                           str(r.authored or ""), r.resource_id) for r in rows]
        elif domain == "procedure":
            rows = self.chart.procedures_for(codes, days)
            ev = [Evidence("procedure", _c(r), _d(r), "performed",
                           str(r.performed or ""), r.resource_id) for r in rows]
        else:
            rows = self.chart.observations_for(codes, days)
            ev = [Evidence("observation", _c(r), _d(r), _fmt(r.value), str(r.effective or ""),
                           r.resource_id) for r in rows]

        window = f" within {days} days of {self.chart.index_date}" if days else ""
        if rows:
            # Evidence is kept whole. Truncation belongs to the renderer, and doing
            # it here once meant a count leaf silently capped at the display limit.
            return Result(T, f"{len(rows)} matching {domain} record(s){window}",
                          evidence=ev, op="exists")

        note = ("the compiler declared this domain complete for these codes, so "
                "silence is read as absence" if absent == "false" else
                "silence in the record is not evidence of absence")
        marker = [Evidence("absent", ",".join(codes[:4]), f"no matching {domain}", "none", "", "",
                           note)]
        if absent == "false":
            return Result(F, f"no matching {domain} record{window}; closed-world",
                          evidence=marker, op="exists")
        return Result(U, f"no matching {domain} record{window}; open-world, so undetermined",
                      evidence=marker, op="exists")

    # -- values -------------------------------------------------------------
    @staticmethod
    def _unit_of(v: dict) -> str | None:
        if v.get("val") == "observation":
            return v.get("unit")
        if v.get("val") == "derived":
            return {"egfr_ckdepi_2021": "mL/min/1.73m2", "bmi": "kg/m2",
                    "systolic_bp": "mmHg", "diastolic_bp": "mmHg"}.get(v["name"])
        if v.get("val") == "age":
            return "a"
        if v.get("val") == "literal":
            # A literal threshold carries a unit too. Without this branch a
            # comparison with the threshold on the left had no target unit at all.
            return v.get("unit")
        return None

    def _value(self, v: dict, want_unit: str | None = None
               ) -> tuple[float | None, str, list[Evidence]]:
        kind = v["val"]

        if kind == "literal":
            if "number" in v:
                num, unit = float(v["number"]), canonical_or_none(v.get("unit"))
                if want_unit and unit and canonical_or_none(want_unit) != unit:
                    c = convert(num, unit, want_unit, v.get("loinc"), self.unit_policy)
                    if not c.ok:
                        return None, f"threshold unit cannot be reconciled: {c.note}", []
                    return c.value, f"threshold converted from {unit} to {want_unit}", []
                if want_unit and not unit:
                    return num, f"literal read as {want_unit} (no unit was declared on it)", []
                return num, "literal", []
            return None, "non-numeric literal cannot be compared", []

        if kind == "age":
            a = self.chart.age
            if a is None:
                return None, "no birth date in record", []
            return float(a), "age at index date", [
                Evidence("demographic", "age", "Age at index date", str(a),
                         str(self.chart.index_date), self.chart.patient_id)]

        if kind == "observation":
            return self._obs_value(v, want_unit or v["unit"])

        if kind == "derived":
            return self._derived(v)

        if kind == "count":
            return self._count(v["query"])

        return None, f"value kind {kind!r} is not numeric", []

    def _count(self, q: dict) -> tuple[float | None, str, list[Evidence]]:
        """How many matching records exist.

        Two traps live here, and both were found in review of this file.

        A count taken from `_exists` would inherit its evidence truncation and
        silently cap at the display limit. So the rows are counted directly.

        More seriously: when the query is open-world and nothing matches, the
        honest answer is "the record does not say how many", not zero. Returning
        0.0 there would commit a number on silence, which is the exact failure
        this project exists to prevent, committed by the engine that claims to
        prevent it.
        """
        domain, codes = q["domain"], q["codes"]
        days = q.get("within_days")
        active = bool(q.get("active_only"))
        absent = self.default_absent_means or q["absent_means"]

        if domain == "condition":
            rows: list[Any] = self.chart.conditions_for(codes, days, active)
            ev = [Evidence("condition", _c(r), _d(r), "present", str(r.onset or ""),
                           r.resource_id) for r in rows]
        elif domain == "medication":
            rows = self.chart.medications_for(codes, days, active)
            ev = [Evidence("medication", _c(r), _d(r), r.status or "", str(r.authored or ""),
                           r.resource_id) for r in rows]
        elif domain == "procedure":
            rows = self.chart.procedures_for(codes, days)
            ev = [Evidence("procedure", _c(r), _d(r), "performed", str(r.performed or ""),
                           r.resource_id) for r in rows]
        else:
            rows = self.chart.observations_for(codes, days)
            ev = [Evidence("observation", _c(r), _d(r), _fmt(r.value), str(r.effective or ""),
                           r.resource_id) for r in rows]

        if not rows and absent == "unknown":
            return None, (f"no matching {domain} record, and this query is open-world, "
                          f"so the count is undetermined rather than zero"), []
        return float(len(rows)), f"count of matching {domain} records", ev

    def _obs_value(self, v: dict, want_unit: str | None
                   ) -> tuple[float | None, str, list[Evidence]]:
        codes, days = v["codes"], v.get("within_days")
        agg = v.get("agg", "latest")
        rows = [o for o in self.chart.observations_for(codes, days) if o.value is not None]
        if not rows:
            any_ever = [o for o in self.chart.observations_for(codes, None) if o.value is not None]
            if any_ever and days:
                last = any_ever[-1]
                return None, (f"most recent {last.codings[0].display} is {last.effective}, "
                              f"outside the {days}-day window ending {self.chart.index_date}"), []
            return None, f"no observation with code {'/'.join(codes)} in the record", []

        if agg in ("latest", "any") and self.chart.same_day_conflict(codes, days):
            return None, (f"two different values for {'/'.join(codes)} on the same most recent "
                          f"date; choosing one would be arbitrary"), []

        row = _pick(rows, agg)
        loinc = next((c.code for c in row.codings if c.code in codes), codes[0])
        c = convert(float(row.value), row.unit, want_unit, loinc, self.unit_policy)
        ev = [Evidence("observation", loinc, _d(row), f"{_fmt(row.value)} {row.unit or ''}".strip(),
                       str(row.effective or ""), row.resource_id,
                       c.note if (c.reconciled_by_code or not c.ok) else "")]
        if not c.ok:
            return None, (f"{_d(row)} is stored in {row.unit!r} but the criterion is written in "
                          f"{want_unit!r}: {c.note}"), ev
        return c.value, f"{agg} {_d(row)}", ev

    def _derived(self, v: dict) -> tuple[float | None, str, list[Evidence]]:
        name = v["name"]
        days = v.get("within_days")
        if name == "bmi":
            return self._obs_value({"codes": ["39156-5"], "within_days": days, "agg": "latest"},
                                   "kg/m2")
        if name == "systolic_bp":
            return self._obs_value({"codes": ["8480-6"], "within_days": days, "agg": "latest"},
                                   "mmHg")
        if name == "diastolic_bp":
            return self._obs_value({"codes": ["8462-4"], "within_days": days, "agg": "latest"},
                                   "mmHg")
        if name == "egfr_ckdepi_2021":
            scr, why, ev = self._obs_value(
                {"codes": ["38483-4", "2160-0"], "within_days": days, "agg": "latest"}, "mg/dL")
            if scr is None:
                return None, f"cannot derive eGFR: {why}", ev
            age, sex = self.chart.age, (self.chart.sex or "").lower()
            if age is None:
                return None, "cannot derive eGFR: no birth date", ev
            if sex not in ("male", "female"):
                return None, f"cannot derive eGFR: sex is {self.chart.sex!r}", ev
            female = sex == "female"
            k = 0.7 if female else 0.9
            a = -0.241 if female else -0.302
            e = (142 * (min(scr / k, 1) ** a) * (max(scr / k, 1) ** -1.200)
                 * (0.9938 ** age) * (1.012 if female else 1.0))
            ev = ev + [Evidence("derived", "egfr_ckdepi_2021", "eGFR (CKD-EPI 2021)",
                                f"{e:.1f} mL/min/1.73m2", str(self.chart.index_date), "",
                                f"computed from creatinine {_fmt(scr)} mg/dL, age {age}, {sex}")]
            return e, "CKD-EPI 2021, race-free", ev
        return None, f"unknown derived value {name!r}", []


# -- helpers ----------------------------------------------------------------

def _pick(rows: list[ObservationRow], agg: str) -> ObservationRow:
    if agg in ("latest", "any"):
        return rows[-1]
    if agg == "first":
        return rows[0]
    if agg == "min":
        return min(rows, key=lambda r: r.value)
    if agg == "max":
        return max(rows, key=lambda r: r.value)
    return rows[-1]


def _unit_label(unit: str | None) -> str:
    """The unit as it belongs in a sentence a coordinator reads, or nothing.

    UCUM writes years as `a`, which is correct and unreadable. Everything else
    is already in the form a clinician expects.
    """
    if not unit:
        return ""
    return " years" if unit == "a" else f" {unit}"


def _fmt(x: Any) -> str:
    if isinstance(x, float):
        if math.isfinite(x) and abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f"{x:.4g}"
    return str(x)


def _c(row: Any) -> str:
    return row.codings[0].code if row.codings else ""


def _d(row: Any) -> str:
    return (row.codings[0].display or "") if row.codings else ""


def canonical_or_none(u: str | None) -> str | None:
    from .units import canonical
    return canonical(u) if u else None


# -- criterion level --------------------------------------------------------

VERDICT = {"MEETS": "MEETS", "FAILS": "FAILS", "INDETERMINATE": "INDETERMINATE"}


def evaluate_criterion(criterion: dict, chart: Chart, unit_policy: str = "code_authoritative",
                       default_absent_means: str | None = None) -> dict:
    """Run one compiled criterion and return a verdict record.

    An inclusion criterion the patient satisfies is MEETS. An exclusion criterion
    the patient triggers is FAILS. Anything the record cannot settle is
    INDETERMINATE, which is a routing outcome and not an error.
    """
    if not criterion.get("compilable", False):
        return {
            "criterion_id": criterion["criterion_id"],
            "kind": criterion["kind"],
            "source_text": criterion["source_text"],
            "verdict": "INDETERMINATE",
            "truth": "UNKNOWN",
            "reason": criterion.get("reason_not_compilable", "not compilable"),
            "needs_human": True,
            "not_compilable": True,
            "evidence": [],
            "trace": None,
        }

    ev = Evaluator(chart, unit_policy=unit_policy, default_absent_means=default_absent_means)
    res = ev.eval_expr(criterion["expr"])

    if res.value is U:
        verdict = "INDETERMINATE"
    elif criterion["kind"] == "inclusion":
        verdict = "MEETS" if res.value is T else "FAILS"
    else:
        verdict = "FAILS" if res.value is T else "MEETS"

    return {
        "criterion_id": criterion["criterion_id"],
        "kind": criterion["kind"],
        "source_text": criterion["source_text"],
        "verdict": verdict,
        "truth": res.value.value,
        "reason": res.reason,
        "needs_human": verdict == "INDETERMINATE",
        "not_compilable": False,
        "unknown_because": res.unknown_reasons() if res.value is U else [],
        "evidence": [vars(e) for e in res.all_evidence()],
        "trace": res.to_dict(),
    }


def screen(criteria: list[dict], chart: Chart, **kw) -> dict:
    """Screen one patient against a whole protocol."""
    rows = [evaluate_criterion(c, chart, **kw) for c in criteria]
    failed = [r for r in rows if r["verdict"] == "FAILS"]
    undet = [r for r in rows if r["verdict"] == "INDETERMINATE"]

    if failed:
        decision = "INELIGIBLE"
        because = f"{len(failed)} criterion/criteria definitively not met"
    elif undet:
        decision = "NEEDS_REVIEW"
        because = f"{len(undet)} criterion/criteria the record cannot settle"
    else:
        decision = "ELIGIBLE"
        because = "every criterion resolved in the patient's favour"

    return {
        "patient_id": chart.patient_id,
        "index_date": str(chart.index_date),
        "decision": decision,
        "because": because,
        "n_criteria": len(rows),
        "n_meets": sum(1 for r in rows if r["verdict"] == "MEETS"),
        "n_fails": len(failed),
        "n_indeterminate": len(undet),
        "criteria": rows,
    }
