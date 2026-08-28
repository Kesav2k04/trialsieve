"""An engine-free view of a patient, for the gold labels only.

This module and everything that imports it must never import `trialsieve.evaluator`,
`trialsieve.ir`, `trialsieve.units` or `trialsieve.logic`. That is the whole point.

If gold and the system under test shared an execution path, then any defect in
that path would appear on both sides of the comparison and be scored as
agreement. A wrong window boundary, an inverted unit factor, a null that resolves
to False rather than to unknown: every one of those would cancel, and the metric
would be blind to exactly the failure modes this project claims to fix.

So gold is computed twice over, from a different data shape, by hand-written
per-criterion functions, with its own arithmetic. Where the two disagree on a
clean record, a human adjudicates and the disagreement is published.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

MEETS, FAILS, INDET = "MEETS", "FAILS", "INDETERMINATE"


def plain(chart: Any) -> dict:
    """Flatten a Chart into plain lists of dicts with ISO date strings."""
    def iso(d):
        return d.isoformat() if d else None

    return {
        "patient_id": chart.patient_id,
        "sex": chart.sex,
        "birth_date": iso(chart.birth_date),
        "index_date": iso(chart.index_date),
        "labs": [{"code": (o.codings[0].code if o.codings else None),
                  "name": (o.codings[0].display if o.codings else None),
                  "value": o.value, "unit": o.unit, "date": iso(o.effective),
                  "id": o.resource_id}
                 for o in chart.observations],
        "problems": [{"code": (c.codings[0].code if c.codings else None),
                      "name": (c.codings[0].display if c.codings else None),
                      "onset": iso(c.onset), "resolved": iso(c.abatement),
                      "status": c.clinical_status, "id": c.resource_id}
                     for c in chart.conditions],
        "orders": [{"code": (m.codings[0].code if m.codings else None),
                    "name": (m.codings[0].display if m.codings else None),
                    "date": iso(m.authored), "status": m.status, "id": m.resource_id}
                   for m in chart.medications],
        "procedures": [{"code": (p.codings[0].code if p.codings else None),
                        "name": (p.codings[0].display if p.codings else None),
                        "date": iso(p.performed), "id": p.resource_id}
                       for p in chart.procedures],
    }


# -- small helpers, written independently of the engine ---------------------

def _days(index_iso: str, when_iso: str | None) -> int | None:
    if not when_iso:
        return None
    a = dt.date.fromisoformat(index_iso)
    b = dt.date.fromisoformat(when_iso)
    return (a - b).days


def age_years(p: dict) -> int | None:
    if not p["birth_date"]:
        return None
    b = dt.date.fromisoformat(p["birth_date"])
    i = dt.date.fromisoformat(p["index_date"])
    years = i.year - b.year
    if (i.month, i.day) < (b.month, b.day):
        years -= 1
    return years


#: Conversions written out longhand, in the direction the gold needs them, so a
#: sign or factor error in the engine cannot be inherited here.
def to_percent_hba1c(value: float, unit: str | None) -> float | None:
    if unit in ("%", "percent"):
        return value
    if unit == "mmol/mol":
        return value / 10.929 + 2.15          # NGSP from IFCC
    return None


def to_mg_dl_creatinine(value: float, unit: str | None) -> float | None:
    if unit in ("mg/dL", "mg/dl"):
        return value
    if unit in ("umol/L", "µmol/L"):
        return value / 88.42
    if unit == "mmol/L":
        return value * 1000 / 88.42
    return None


def to_mg_per_mmol_uacr(value: float, unit: str | None) -> float | None:
    if unit == "mg/mmol":
        return value
    if unit in ("mg/g", "mg/gCr"):
        return value / 8.8402
    return None


def to_kg_m2(value: float, unit: str | None) -> float | None:
    return value if unit in ("kg/m2", "kg/m^2") else None


def to_ml_min_173(value: float, unit: str | None) -> float | None:
    # LOINC 33914-3 is defined as the 1.73 m2 normalised rate, so a bare mL/min
    # on that code is the same quantity under a looser label. Written out here
    # deliberately so the choice is visible in the gold as well as in the engine.
    if unit in ("mL/min/{1.73_m2}", "mL/min/1.73m2", "mL/min"):
        return value
    return None


def latest_lab(p: dict, codes: list[str], within_days: int | None = None) -> dict | None:
    """Most recent dated lab with a value, tie-broken by resource id."""
    rows = [r for r in p["labs"]
            if r["code"] in codes and r["value"] is not None and r["date"]]
    if within_days is not None:
        rows = [r for r in rows
                if (_days(p["index_date"], r["date"]) or 10 ** 9) <= within_days
                and (_days(p["index_date"], r["date"]) or -1) >= 0]
    if not rows:
        return None
    rows.sort(key=lambda r: (r["date"], r["id"]))
    newest = rows[-1]["date"]
    same = [r for r in rows if r["date"] == newest]
    if len({round(r["value"], 9) for r in same}) > 1:
        return {"conflict": True}
    return same[-1]


def has_lab_at_all(p: dict, codes: list[str]) -> bool:
    return any(r["code"] in codes and r["value"] is not None for r in p["labs"])


def problems_with(p: dict, codes: list[str], within_days: int | None = None,
                  active_only: bool = False) -> list[dict]:
    out = []
    for r in p["problems"]:
        if r["code"] not in codes:
            continue
        if active_only and r["resolved"]:
            continue
        if within_days is not None:
            n = _days(p["index_date"], r["onset"])
            if n is None or n < 0 or n > within_days:
                continue
        out.append(r)
    return out


def orders_with(p: dict, codes: list[str], within_days: int | None = None,
                active_only: bool = False) -> list[dict]:
    out = []
    for r in p["orders"]:
        if r["code"] not in codes:
            continue
        if active_only and r["status"] not in (None, "active"):
            continue
        if within_days is not None:
            n = _days(p["index_date"], r["date"])
            if n is None or n < 0 or n > within_days:
                continue
        out.append(r)
    return out


def band(value: float | None, low: float, high: float) -> str:
    """Inclusive band test in gold terms. None means the record could not say."""
    if value is None:
        return INDET
    return MEETS if low <= value <= high else FAILS


def at_least(n: int, results: list[str]) -> str:
    t = sum(1 for r in results if r == MEETS)
    u = sum(1 for r in results if r == INDET)
    if t >= n:
        return MEETS
    if t + u < n:
        return FAILS
    return INDET


def all_of(results: list[str]) -> str:
    if any(r == FAILS for r in results):
        return FAILS
    if any(r == INDET for r in results):
        return INDET
    return MEETS


def invert_for_exclusion(r: str) -> str:
    """An exclusion the patient triggers is a FAILS for that patient."""
    return {MEETS: FAILS, FAILS: MEETS, INDET: INDET}[r]
