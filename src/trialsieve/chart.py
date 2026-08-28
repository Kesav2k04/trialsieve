"""A normalized, queryable view of one patient FHIR bundle.

Synthea bundles run to about two megabytes each. Nothing downstream should walk
raw FHIR, so this module flattens a bundle once into typed rows with parsed
dates, and exposes the handful of queries an eligibility predicate needs.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def _parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


@dataclass(frozen=True)
class Coding:
    system: str | None
    code: str | None
    display: str | None


@dataclass
class ConditionRow:
    codings: list[Coding]
    onset: dt.date | None
    abatement: dt.date | None
    clinical_status: str | None
    resource_id: str

    @property
    def active(self) -> bool:
        if self.abatement is not None:
            return False
        return self.clinical_status in (None, "active", "relapse", "recurrence")


@dataclass
class ObservationRow:
    codings: list[Coding]
    value: float | None
    unit: str | None
    value_string: str | None
    effective: dt.date | None
    resource_id: str


@dataclass
class MedicationRow:
    codings: list[Coding]
    authored: dt.date | None
    status: str | None
    resource_id: str

    @property
    def active(self) -> bool:
        return self.status in (None, "active")


@dataclass
class ProcedureRow:
    codings: list[Coding]
    performed: dt.date | None
    resource_id: str


@dataclass
class Chart:
    """One patient, flattened. index_date is the simulated screening date."""

    patient_id: str
    birth_date: dt.date | None
    sex: str | None
    deceased_date: dt.date | None
    index_date: dt.date
    conditions: list[ConditionRow] = field(default_factory=list)
    observations: list[ObservationRow] = field(default_factory=list)
    medications: list[MedicationRow] = field(default_factory=list)
    procedures: list[ProcedureRow] = field(default_factory=list)
    source_file: str = ""

    @property
    def age(self) -> int | None:
        if self.birth_date is None:
            return None
        b, i = self.birth_date, self.index_date
        return i.year - b.year - ((i.month, i.day) < (b.month, b.day))

    def _within(self, when: dt.date | None, days: int | None) -> bool:
        if days is None:
            return True
        if when is None:
            return False
        return 0 <= (self.index_date - when).days <= days

    def observations_for(self, codes: Iterable[str], days: int | None = None) -> list[ObservationRow]:
        want = set(codes)
        out = [o for o in self.observations
               if any(c.code in want for c in o.codings) and self._within(o.effective, days)]
        # Tie-break explicitly on resource id. Relying on bundle order would make
        # "the latest value" depend on how the flattener happened to walk the file,
        # which is a silent nondeterminism that would propagate into gold labels.
        out.sort(key=lambda o: (o.effective or dt.date.min, o.resource_id))
        return out

    def latest_observation(self, codes: Iterable[str], days: int | None = None) -> ObservationRow | None:
        rows = [o for o in self.observations_for(codes, days) if o.value is not None]
        return rows[-1] if rows else None

    def same_day_conflict(self, codes: Iterable[str], days: int | None = None,
                          rel_tol: float = 1e-6) -> bool:
        """True when the most recent date carries two different values for one code.

        Picking one of them by sort order would be a coin flip dressed as a
        measurement, so the evaluator turns this into UNKNOWN instead.
        """
        rows = [o for o in self.observations_for(codes, days) if o.value is not None]
        if len(rows) < 2:
            return False
        last = rows[-1].effective
        same = [o for o in rows if o.effective == last]
        if len(same) < 2:
            return False
        lo, hi = min(o.value for o in same), max(o.value for o in same)
        return abs(hi - lo) > rel_tol * max(1.0, abs(hi))

    def conditions_for(self, codes: Iterable[str], days: int | None = None,
                       active_only: bool = False) -> list[ConditionRow]:
        want = set(codes)
        out = []
        for c in self.conditions:
            if not any(cd.code in want for cd in c.codings):
                continue
            if active_only and not c.active:
                continue
            if days is not None and not self._within(c.onset, days):
                continue
            out.append(c)
        return out

    def medications_for(self, codes: Iterable[str], days: int | None = None,
                        active_only: bool = False) -> list[MedicationRow]:
        want = set(codes)
        out = []
        for m in self.medications:
            if not any(cd.code in want for cd in m.codings):
                continue
            if active_only and not m.active:
                continue
            if days is not None and not self._within(m.authored, days):
                continue
            out.append(m)
        return out

    def procedures_for(self, codes: Iterable[str], days: int | None = None) -> list[ProcedureRow]:
        want = set(codes)
        return [p for p in self.procedures
                if any(cd.code in want for cd in p.codings) and self._within(p.performed, days)]


def _codings(cc: dict[str, Any] | None) -> list[Coding]:
    if not cc:
        return []
    return [Coding(c.get("system"), c.get("code"), c.get("display"))
            for c in cc.get("coding", [])]


def load_chart(path: str, index_date: dt.date | None = None) -> Chart:
    """Flatten one Synthea FHIR bundle.

    When index_date is not given it defaults to the latest dated resource in the
    bundle. A single global date would penalise patients whose record simply ends
    earlier, which is a property of the synthetic generator, not of the patient.
    """
    with open(path, encoding="utf-8") as fh:
        bundle = json.load(fh)

    patient_id = birth = sex = deceased = None
    conds: list[ConditionRow] = []
    obs: list[ObservationRow] = []
    meds: list[MedicationRow] = []
    procs: list[ProcedureRow] = []
    latest: dt.date | None = None

    def bump(d: dt.date | None) -> None:
        nonlocal latest
        if d and (latest is None or d > latest):
            latest = d

    for entry in bundle.get("entry", []):
        r = entry.get("resource", {})
        rt = r.get("resourceType")
        rid = r.get("id", "")
        if rt == "Patient":
            patient_id = rid
            birth = _parse_date(r.get("birthDate"))
            sex = r.get("gender")
            deceased = _parse_date(r.get("deceasedDateTime"))
        elif rt == "Condition":
            onset = _parse_date(r.get("onsetDateTime"))
            status = (r.get("clinicalStatus", {}).get("coding") or [{}])[0].get("code")
            conds.append(ConditionRow(_codings(r.get("code")), onset,
                                      _parse_date(r.get("abatementDateTime")), status, rid))
            bump(onset)
        elif rt == "Observation":
            eff = _parse_date(r.get("effectiveDateTime"))
            vq = r.get("valueQuantity") or {}
            obs.append(ObservationRow(_codings(r.get("code")), vq.get("value"), vq.get("unit"),
                                      r.get("valueString"), eff, rid))
            bump(eff)
            for comp in r.get("component", []) or []:
                cvq = comp.get("valueQuantity") or {}
                obs.append(ObservationRow(_codings(comp.get("code")), cvq.get("value"),
                                          cvq.get("unit"), None, eff, rid))
        elif rt == "MedicationRequest":
            auth = _parse_date(r.get("authoredOn"))
            meds.append(MedicationRow(_codings(r.get("medicationCodeableConcept")), auth,
                                      r.get("status"), rid))
            bump(auth)
        elif rt == "Procedure":
            perf = _parse_date((r.get("performedPeriod") or {}).get("start")
                               or r.get("performedDateTime"))
            procs.append(ProcedureRow(_codings(r.get("code")), perf, rid))
            bump(perf)
        elif rt == "Encounter":
            bump(_parse_date((r.get("period") or {}).get("start")))

    idx = index_date or latest or dt.date(2021, 11, 1)
    return Chart(patient_id=patient_id or "", birth_date=birth, sex=sex, deceased_date=deceased,
                 index_date=idx, conditions=conds, observations=obs, medications=meds,
                 procedures=procs, source_file=path)
