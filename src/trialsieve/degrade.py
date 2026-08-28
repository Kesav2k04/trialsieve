"""Make records incomplete on purpose, because this corpus is not.

Synthea charts are complete by construction. Every value the generator decided a
patient has is present, correctly coded, correctly dated and correctly united. A
silent-error rate measured on such records is a lower bound on what would happen
in a real clinic, and it is a lower bound on precisely the failure this project
is built around, so measuring only on clean charts would be measuring everywhere
except where the claim lives.

Four degradations, each a thing that happens in real records:

  drop_value      the result is simply not there. Care happened elsewhere.
  flip_unit       the value is stored under a different unit for the same code.
  strip_date      the entry has no usable date, so no window can be applied.
  decode_condition  a coded diagnosis becomes free text with no code.

Honest limits, stated here rather than in a footnote. Real missingness is not
random: it tracks fragmented care, deprivation and sicker patients, so absence
correlates with the answer. This harness removes data independently of the
answer, so it reproduces the mechanism and not the correlation. Results under it
should be read as "what happens when a record is silent", not as "what happens in
a real clinic".

Every arm sees byte-identical degraded charts, chosen by a seeded permutation
that is committed with the results.
"""
from __future__ import annotations

import copy
import hashlib
import random
from dataclasses import dataclass
from typing import Iterable

from .chart import Chart

#: Plausible wrong-unit substitutions for a code, drawn from units the same
#: analyte is genuinely reported in somewhere.
UNIT_FLIPS: dict[str, str] = {
    "4548-4": "mmol/mol",     # HbA1c IFCC rather than NGSP
    "38483-4": "umol/L",      # creatinine molar rather than mass
    "2160-0": "umol/L",
    "14959-1": "mg/mmol",     # UACR already differs from the criterion unit
    "18262-6": "mmol/L",
    "2093-3": "mmol/L",
    "2571-8": "mmol/L",
    "2085-9": "mmol/L",
    "2339-0": "mmol/L",
    "39156-5": "lb/in2",
    "33914-3": "mL/min",      # the corpus already carries both
}

MODES = ("drop_value", "flip_unit", "strip_date", "decode_condition")


@dataclass
class Change:
    patient_id: str
    mode: str
    domain: str
    code: str
    resource_id: str
    detail: str

    def as_dict(self) -> dict:
        return vars(self)


def _rng(seed: int, patient_id: str) -> random.Random:
    """Per-patient stream, so adding a patient does not reshuffle the others."""
    h = hashlib.sha256(f"{seed}:{patient_id}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def degrade_chart(chart: Chart, k: float, seed: int,
                  relevant_codes: Iterable[str] | None = None,
                  modes: Iterable[str] = MODES) -> tuple[Chart, list[Change]]:
    """Return a degraded copy of `chart` and the list of what was changed.

    `relevant_codes` restricts damage to codes the evaluation actually looks at.
    It must come from the GOLD predicates, never from the system under test:
    relevance derived from the system's own compiled code lists would damage
    exactly what the system reads and spare what the baseline reads.
    """
    if k <= 0:
        return chart, []

    modes = list(modes)
    rng = _rng(seed, chart.patient_id)
    out = copy.deepcopy(chart)
    changes: list[Change] = []
    want = set(relevant_codes) if relevant_codes is not None else None

    def touched(codings) -> str | None:
        for c in codings:
            if want is None or c.code in want:
                return c.code
        return None

    # Observations
    survivors = []
    for o in out.observations:
        code = touched(o.codings)
        if code is None or rng.random() >= k:
            survivors.append(o)
            continue
        choices = [m for m in modes if m != "decode_condition"]
        if code not in UNIT_FLIPS and "flip_unit" in choices:
            choices = [m for m in choices if m != "flip_unit"]
        if not choices:
            survivors.append(o)
            continue
        mode = rng.choice(choices)
        if mode == "drop_value":
            changes.append(Change(chart.patient_id, mode, "observation", code,
                                  o.resource_id, "observation removed from the record"))
            continue
        if mode == "flip_unit":
            before = o.unit
            o.unit = UNIT_FLIPS[code]
            changes.append(Change(chart.patient_id, mode, "observation", code, o.resource_id,
                                  f"unit {before!r} rewritten as {o.unit!r}"))
        elif mode == "strip_date":
            o.effective = None
            changes.append(Change(chart.patient_id, mode, "observation", code, o.resource_id,
                                  "effective date removed"))
        survivors.append(o)
    out.observations = survivors

    # Conditions
    for c in out.conditions:
        code = touched(c.codings)
        if code is None or rng.random() >= k:
            continue
        choices = [m for m in modes if m in ("decode_condition", "strip_date")]
        if not choices:
            continue
        mode = rng.choice(choices)
        if mode == "decode_condition":
            from .chart import Coding
            display = (c.codings[0].display if c.codings else "") or "unspecified"
            c.codings = [Coding(None, None, display)]
            changes.append(Change(chart.patient_id, mode, "condition", code, c.resource_id,
                                  f"coded diagnosis reduced to free text {display!r}"))
        else:
            c.onset = None
            changes.append(Change(chart.patient_id, mode, "condition", code, c.resource_id,
                                  "onset date removed"))

    # Medications
    for m in out.medications:
        code = touched(m.codings)
        if code is None or rng.random() >= k:
            continue
        if "strip_date" in modes:
            m.authored = None
            changes.append(Change(chart.patient_id, "strip_date", "medication", code,
                                  m.resource_id, "authored date removed"))

    return out, changes


def degrade_panel(panel: list[Chart], k: float, seed: int,
                  relevant_codes: Iterable[str] | None = None
                  ) -> tuple[list[Chart], list[Change]]:
    charts, all_changes = [], []
    for c in panel:
        d, ch = degrade_chart(c, k, seed, relevant_codes)
        charts.append(d)
        all_changes.extend(ch)
    return charts, all_changes


def manifest_digest(changes: list[Change]) -> str:
    """Digest of the damage, so both arms can be shown to have seen the same charts."""
    body = "\n".join(f"{c.patient_id}|{c.mode}|{c.domain}|{c.code}|{c.resource_id}"
                     for c in sorted(changes, key=lambda x: (x.patient_id, x.resource_id,
                                                             x.mode, x.code)))
    return hashlib.sha256(body.encode()).hexdigest()
