"""Split a registry eligibility blob into atomic, typed criteria.

Segmentation is its own step because the downstream unit of everything (review,
compilation, scoring, the bootstrap) is one criterion, and a sponsor's summary
does not come pre-divided. One bullet routinely carries several independent
tests joined by "and", and a nested bullet list under "at least one of the
following" is a single criterion rather than five.

The classification made here is committed before compilation runs, so the
headline can be reported honestly as "k of n criteria are record-checkable"
rather than as a coverage figure computed after seeing which ones compiled.
"""
from __future__ import annotations

import hashlib
from typing import Any

from ..llm import Client
from ..trace import Trajectory
from .common import ask_json, require

PROMPT_VERSION = "segmenter-v1"

SYSTEM = """You prepare clinical trial eligibility text for review by a research coordinator.

You split the text into atomic criteria. An atomic criterion is one thing a
reviewer can answer on its own. You do not judge any patient, and you do not
decide whether a criterion is checkable from a medical record."""

INSTRUCTIONS = """Split the eligibility text below into atomic criteria.

Rules:
1. Every criterion is INCLUSION or EXCLUSION, taken from the heading it sits under.
2. One bullet containing several independent tests joined by "and" becomes several
   criteria. "Age 18-85 and BMI > 25" is two.
3. A bullet with a nested list governed by "at least one of the following", "any of",
   or "either" stays as ONE criterion. Keep the nested options inside its text.
4. Copy the source text verbatim into `text`. Do not paraphrase, expand abbreviations,
   normalise units, or fix typos. This text is what a human reviewer will read.
5. Assign `category` from exactly this list, describing what the criterion is about:
   demographic, lab_value, vital_sign, diagnosis, medication, procedure, temporal_event,
   consent_or_capacity, investigator_judgement, lifestyle_or_social, reproductive, other
6. Drop headings, section numbers, and sentences that state no requirement.

Return JSON only:

{"criteria": [{"index": 1, "kind": "inclusion", "category": "lab_value",
               "text": "HbA1c 6.5-10%"}]}

ELIGIBILITY TEXT
================
"""

CATEGORIES = {"demographic", "lab_value", "vital_sign", "diagnosis", "medication",
              "procedure", "temporal_event", "consent_or_capacity",
              "investigator_judgement", "lifestyle_or_social", "reproductive", "other"}


def _validate(payload: Any) -> None:
    require(isinstance(payload, dict), "top level must be an object")
    rows = payload.get("criteria")
    require(isinstance(rows, list) and rows, "criteria must be a non-empty list")
    for i, r in enumerate(rows):
        require(isinstance(r, dict), f"criteria[{i}] must be an object")
        require(r.get("kind") in {"inclusion", "exclusion"},
                f"criteria[{i}].kind must be 'inclusion' or 'exclusion', got {r.get('kind')!r}")
        require(isinstance(r.get("text"), str) and r["text"].strip(),
                f"criteria[{i}].text must be a non-empty string")
        require(r.get("category") in CATEGORIES,
                f"criteria[{i}].category must be one of {sorted(CATEGORIES)}, "
                f"got {r.get('category')!r}")


def criterion_hash(nct: str, text: str) -> str:
    """Stable id for a criterion. Content-addressed so identical criteria across
    trials collapse to one compilation and one review."""
    return hashlib.sha256(" ".join(text.split()).lower().encode("utf-8")).hexdigest()[:12]


def segment(client: Client, nct: str, criteria_text: str,
            traj: Trajectory | None = None) -> tuple[list[dict], Trajectory]:
    traj = traj or Trajectory("segmenter", nct)
    traj.instructions(SYSTEM + "\n\n" + INSTRUCTIONS, PROMPT_VERSION)
    traj.input(nct_id=nct, criteria_chars=len(criteria_text))

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": INSTRUCTIONS + criteria_text.strip()}]
    payload = ask_json(client, traj, messages, _validate, tag=f"segment:{nct}",
                       prompt_version=PROMPT_VERSION)

    out = []
    for i, r in enumerate(payload["criteria"], start=1):
        text = r["text"].strip()
        out.append({
            "criterion_id": f"{nct}-{'INC' if r['kind'] == 'inclusion' else 'EXC'}-{i:02d}",
            "nct_id": nct,
            "kind": r["kind"],
            "category": r["category"],
            "source_text": text,
            "content_hash": criterion_hash(nct, text),
        })
    traj.final(n_criteria=len(out),
               by_kind={k: sum(1 for c in out if c["kind"] == k)
                        for k in ("inclusion", "exclusion")})
    return out, traj
