"""Test helpers: build small charts by hand instead of loading 2 MB bundles."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialsieve.chart import (  # noqa: E402
    Chart, Coding, ConditionRow, MedicationRow, ObservationRow, ProcedureRow,
)

INDEX = dt.date(2021, 11, 1)


def d(days_ago: int) -> dt.date:
    return INDEX - dt.timedelta(days=days_ago)


def obs(code: str, value: float | None, unit: str | None, days_ago: int = 1,
        display: str = "", rid: str = "") -> ObservationRow:
    return ObservationRow([Coding("http://loinc.org", code, display or code)], value, unit,
                          None, d(days_ago), rid or f"obs-{code}-{days_ago}")


def cond(code: str, days_ago: int = 30, display: str = "", status: str = "active",
         abated: int | None = None, rid: str = "") -> ConditionRow:
    return ConditionRow([Coding("http://snomed.info/sct", code, display or code)], d(days_ago),
                        d(abated) if abated is not None else None, status,
                        rid or f"cond-{code}-{days_ago}")


def med(code: str, days_ago: int = 30, display: str = "", status: str = "active",
        rid: str = "") -> MedicationRow:
    return MedicationRow([Coding("rxnorm", code, display or code)], d(days_ago), status,
                         rid or f"med-{code}-{days_ago}")


def proc(code: str, days_ago: int = 30, display: str = "", rid: str = "") -> ProcedureRow:
    return ProcedureRow([Coding("http://snomed.info/sct", code, display or code)], d(days_ago),
                        rid or f"proc-{code}")


def chart(age: int = 50, sex: str = "male", observations=(), conditions=(), medications=(),
          procedures=(), index: dt.date = INDEX) -> Chart:
    birth = dt.date(index.year - age, index.month, index.day)
    return Chart(patient_id="p1", birth_date=birth, sex=sex, deceased_date=None,
                 index_date=index, conditions=list(conditions), observations=list(observations),
                 medications=list(medications), procedures=list(procedures))
