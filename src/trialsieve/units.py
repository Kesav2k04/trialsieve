"""Unit reconciliation between what a criterion states and what a chart stores.

Two hazards in this corpus motivated every line here, and both were found by
reading the data rather than by imagining what could go wrong:

* eGFR (LOINC 33914-3) is stored 695 times as `mL/min/{1.73_m2}` and 888 times
  as bare `mL/min`. The LOINC code is defined as the body-surface-normalised
  quantity, so the bare unit is a labelling inconsistency rather than a
  different measurement. The code is treated as authoritative and the
  discrepancy is surfaced, never silently dropped.
* UACR (LOINC 14959-1) is stored in `mg/g`, and trials state the threshold in
  `mg/mmol`. These differ by a factor of about 8.84. Comparing the bare numbers
  is off by almost an order of magnitude in the direction that wrongly excludes
  patients.

The default policy is therefore: convert when a conversion is defined, accept a
known alias when the LOINC code pins the quantity, and otherwise refuse to
compare. Refusing produces UNKNOWN, which routes to a human. It never produces a
number.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Units that mean the same thing written differently.
ALIASES: dict[str, str] = {
    "%": "%",
    "percent": "%",
    "mg/dl": "mg/dL",
    "mg/dL": "mg/dL",
    "mmol/l": "mmol/L",
    "mmol/L": "mmol/L",
    "kg/m2": "kg/m2",
    "kg/m^2": "kg/m2",
    "kg/m**2": "kg/m2",
    "mm[hg]": "mmHg",
    "mmhg": "mmHg",
    "mm hg": "mmHg",
    "mg/g": "mg/g",
    "mg/mmol": "mg/mmol",
    "ml/min": "mL/min",
    "ml/min/1.73m2": "mL/min/1.73m2",
    "ml/min/{1.73_m2}": "mL/min/1.73m2",
    "ml/min/1.73 m2": "mL/min/1.73m2",
    "ml/min/1.73m^2": "mL/min/1.73m2",
    "u/l": "U/L",
    "iu/l": "U/L",
    "g/dl": "g/dL",
    "years": "a",
    "year": "a",
    "a": "a",
}

#: (from, to) -> multiplier. Molar conversions are analyte specific, so they are
#: keyed by the LOINC code rather than applied globally.
GENERIC: dict[tuple[str, str], float] = {
    ("mg/g", "mg/mmol"): 1.0 / 8.8402,
    ("mg/mmol", "mg/g"): 8.8402,
    ("g/dL", "mg/dL"): 1000.0,
    ("mg/dL", "g/dL"): 0.001,
}

#: LOINC code -> {(from, to): multiplier} for mass/molar pairs.
PER_CODE: dict[str, dict[tuple[str, str], float]] = {
    "2339-0": {("mg/dL", "mmol/L"): 1 / 18.0182, ("mmol/L", "mg/dL"): 18.0182},   # glucose
    "2345-7": {("mg/dL", "mmol/L"): 1 / 18.0182, ("mmol/L", "mg/dL"): 18.0182},
    "38483-4": {("mg/dL", "mmol/L"): 88.42 / 1000, ("mmol/L", "mg/dL"): 1000 / 88.42},  # creatinine
    "2160-0": {("mg/dL", "mmol/L"): 88.42 / 1000, ("mmol/L", "mg/dL"): 1000 / 88.42},
    "2093-3": {("mg/dL", "mmol/L"): 1 / 38.67, ("mmol/L", "mg/dL"): 38.67},        # total cholesterol
    "18262-6": {("mg/dL", "mmol/L"): 1 / 38.67, ("mmol/L", "mg/dL"): 38.67},       # LDL
    "2085-9": {("mg/dL", "mmol/L"): 1 / 38.67, ("mmol/L", "mg/dL"): 38.67},        # HDL
    "2571-8": {("mg/dL", "mmol/L"): 1 / 88.57, ("mmol/L", "mg/dL"): 88.57},        # triglycerides
    "14959-1": {("mg/g", "mg/mmol"): 1 / 8.8402, ("mg/mmol", "mg/g"): 8.8402},     # UACR
}

#: LOINC codes whose definition pins the quantity, so a loosely written unit on
#: the observation can be accepted as the canonical one. The accepted aliases
#: are listed explicitly rather than inferred.
CODE_AUTHORITATIVE: dict[str, tuple[str, set[str]]] = {
    # 33914-3 is "Glomerular filtration rate/1.73 sq M.predicted": the /1.73m2
    # normalisation is part of the code, so a bare mL/min is the same quantity.
    "33914-3": ("mL/min/1.73m2", {"mL/min"}),
}


def canonical(unit: str | None) -> str | None:
    if unit is None:
        return None
    u = unit.strip()
    return ALIASES.get(u.lower(), ALIASES.get(u, u))


@dataclass
class Conversion:
    ok: bool
    value: float | None
    note: str
    #: True when the units differed and the LOINC code was used to reconcile them.
    reconciled_by_code: bool = False


def convert(value: float, from_unit: str | None, to_unit: str | None,
            loinc: str | None = None, policy: str = "code_authoritative") -> Conversion:
    """Convert `value` from one unit to another, or refuse.

    Refusing is a first-class outcome. A caller that receives ok=False must
    produce UNKNOWN; it must not fall back to comparing the raw numbers.
    """
    f, t = canonical(from_unit), canonical(to_unit)

    if t is None or f is None:
        return Conversion(False, None, f"missing unit (stored={from_unit!r}, wanted={to_unit!r})")
    if f == t:
        return Conversion(True, value, "units match")

    per = PER_CODE.get(loinc or "", {})
    if (f, t) in per:
        return Conversion(True, value * per[(f, t)], f"converted {f} to {t} using the factor for LOINC {loinc}")
    if (f, t) in GENERIC:
        return Conversion(True, value * GENERIC[(f, t)], f"converted {f} to {t}")

    if policy == "code_authoritative" and loinc in CODE_AUTHORITATIVE:
        canon, accepted = CODE_AUTHORITATIVE[loinc]
        if t == canon and f in accepted:
            return Conversion(
                True, value,
                f"stored unit {f} accepted as {canon}: LOINC {loinc} defines the normalisation",
                reconciled_by_code=True,
            )

    return Conversion(False, None, f"no defined conversion from {f} to {t}"
                                  + (f" for LOINC {loinc}" if loinc else ""))
