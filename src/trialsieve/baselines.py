"""The arms TrialSieve is measured against.

B0  always-FAILS. A degenerate control that shows what the label marginals alone
    are worth, so nobody mistakes a majority-class score for a result.
B1  demographics only. Deterministic age and sex bounds, no model. Age and sex
    are recorded for every patient in this corpus, so a system can post a large
    panel reduction on them and tell a coordinator nothing they did not already
    know. B1 is the floor the headline has to clear.
B2  one model call per patient-criterion cell. The arm that matters.
B3  B2 sampled three times with disagreement routed to INDETERMINATE.

Fairness rules for B2, which decide whether the comparison means anything:

* B2 receives a **criterion-agnostic** digest of the record. It is built once per
  patient and never consults the compiled predicate, because selecting facts with
  TrialSieve's own code lists would make it structurally impossible for B2 to
  find something TrialSieve missed.
* The digest is complete over the structured record: every condition, every
  medication, and the recent history of every distinct measurement, with dates.
* B2 is told plainly that INDETERMINATE is available, is given a worked example
  of when to use it, and is scored on the same three-valued output space. The
  claim under test is that a per-cell prompt commits where the record is silent,
  and that claim is only interesting if abstaining was easy to do.
"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from typing import Any

from .chart import Chart
from .llm import Client, Request
from .trace import Trajectory
from .agents.common import extract_json, require

PROMPT_VERSION = "b2-v1"

B2_SYSTEM = """You are screening a patient against one clinical trial eligibility criterion.

You answer from the record you are shown and nothing else. When the record does
not contain what the criterion asks about, you say so rather than inferring it."""

B2_INSTRUCTIONS = """Decide whether this patient satisfies the criterion.

CRITERION ({kind}):
  {criterion}

PATIENT RECORD (screening date {index_date})
{record}

Answer with exactly one verdict:

  MEETS          the record shows the patient satisfies this criterion
  FAILS          the record shows the patient does not satisfy it
                 (for an EXCLUSION criterion, FAILS means the patient triggers
                  the exclusion and cannot be enrolled)
  INDETERMINATE  the record does not contain what is needed to decide

Use INDETERMINATE whenever the record is silent or stale on the thing being
asked about. For example, if the criterion sets a limit on HbA1c and this record
contains no HbA1c, the answer is INDETERMINATE, not FAILS: an absent test is not
an abnormal one. The same applies when the criterion asks about something that
happened within a time window and the only relevant entry is older than that
window.

Cite the record lines you relied on in `evidence`.

Return JSON only:

{{"verdict": "MEETS|FAILS|INDETERMINATE",
  "evidence": ["Hemoglobin A1c = 7.4 % (2021-06-02)"],
  "reasoning": "one sentence"}}"""


# ---------------------------------------------------------------------------
# Patient digest
# ---------------------------------------------------------------------------

def render_record(chart: Chart, max_history: int = 3) -> str:
    """A complete, criterion-agnostic rendering of the structured record.

    Built from the chart alone. Nothing here is chosen by looking at the
    criterion, at a compiled predicate, or at any code list, so this digest
    cannot be tuned to make one arm look good.
    """
    lines: list[str] = []
    age = chart.age
    lines.append(f"Demographics: age {age if age is not None else 'unknown'}, "
                 f"sex {chart.sex or 'unknown'}")

    by_code: dict[str, list] = defaultdict(list)
    for o in chart.observations:
        if o.value is None and not o.value_string:
            continue
        code = o.codings[0].code if o.codings else ""
        by_code[code].append(o)

    lines.append("")
    lines.append(f"Measurements ({len(by_code)} distinct tests; most recent "
                 f"{max_history} of each, newest first):")
    if not by_code:
        lines.append("  (none recorded)")
    for code in sorted(by_code):
        rows = sorted(by_code[code], key=lambda r: (r.effective or dt.date.min, r.resource_id))
        name = (rows[-1].codings[0].display or code) if rows[-1].codings else code
        vals = []
        for r in reversed(rows[-max_history:]):
            v = r.value if r.value is not None else r.value_string
            unit = f" {r.unit}" if r.unit else ""
            vals.append(f"{v}{unit} ({r.effective})")
        older = f", plus {len(rows) - max_history} earlier" if len(rows) > max_history else ""
        lines.append(f"  {name} [{code}]: " + "; ".join(vals) + older)

    lines.append("")
    act = [c for c in chart.conditions if c.active]
    res = [c for c in chart.conditions if not c.active]
    lines.append(f"Conditions on the problem list ({len(act)} active, {len(res)} resolved):")
    if not chart.conditions:
        lines.append("  (none recorded)")
    for c in sorted(chart.conditions, key=lambda x: (x.onset or dt.date.min), reverse=True):
        nm = (c.codings[0].display or "") if c.codings else ""
        cd = (c.codings[0].code or "") if c.codings else ""
        state = "active" if c.active else f"resolved {c.abatement}"
        lines.append(f"  {nm} [{cd}]: onset {c.onset}, {state}")

    lines.append("")
    lines.append(f"Medication orders ({len(chart.medications)}):")
    if not chart.medications:
        lines.append("  (none recorded)")
    for m in sorted(chart.medications, key=lambda x: (x.authored or dt.date.min), reverse=True):
        nm = (m.codings[0].display or "") if m.codings else ""
        cd = (m.codings[0].code or "") if m.codings else ""
        lines.append(f"  {nm} [{cd}]: ordered {m.authored}, status {m.status}")

    if chart.procedures:
        lines.append("")
        lines.append(f"Procedures ({len(chart.procedures)}):")
        for p in sorted(chart.procedures, key=lambda x: (x.performed or dt.date.min),
                        reverse=True)[:60]:
            nm = (p.codings[0].display or "") if p.codings else ""
            lines.append(f"  {nm}: {p.performed}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------

VERDICTS = {"MEETS", "FAILS", "INDETERMINATE"}


def b0_always_fails(criterion: dict, chart: Chart) -> dict:
    return {"criterion_id": criterion["criterion_id"], "verdict": "FAILS",
            "evidence": [], "reasoning": "degenerate control: always FAILS", "arm": "B0"}


def b1_demographics(criterion: dict, chart: Chart) -> dict:
    """Answer only from age and sex; abstain on everything else.

    Uses the compiled predicate when, and only when, that predicate reads nothing
    but age, sex and constants. That keeps B1 a genuine floor rather than a
    strawman: it gets full credit for every criterion demographics can settle.
    """
    from .evaluator import evaluate_criterion
    from .ir import is_demographic_only

    if criterion.get("compilable") and is_demographic_only(criterion["expr"]):
        r = evaluate_criterion(criterion, chart)
        return {"criterion_id": criterion["criterion_id"], "verdict": r["verdict"],
                "evidence": [e["display"] for e in r["evidence"]],
                "reasoning": r["reason"], "arm": "B1"}
    return {"criterion_id": criterion["criterion_id"], "verdict": "INDETERMINATE",
            "evidence": [], "reasoning": "not answerable from demographics alone", "arm": "B1"}


def _v_b2(p: Any) -> None:
    require(isinstance(p, dict), "top level must be an object")
    require(p.get("verdict") in VERDICTS,
            f"verdict must be one of MEETS, FAILS, INDETERMINATE; got {p.get('verdict')!r}")


def b2_prompt_messages(criterion: dict, chart: Chart, record: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": B2_SYSTEM},
            {"role": "user", "content": B2_INSTRUCTIONS.format(
                kind=criterion["kind"].upper(), criterion=criterion["source_text"],
                index_date=chart.index_date, record=record)}]


def b2_cell(client: Client, criterion: dict, chart: Chart, record: str,
            traj: Trajectory | None = None, temperature: float = 0.0,
            seed: int | None = 7) -> dict:
    """One model call for one patient-criterion cell."""
    messages = b2_prompt_messages(criterion, chart, record)
    tag = f"b2:{criterion['criterion_id']}:{chart.patient_id[:8]}"
    req = Request(model=client.model, messages=messages, temperature=temperature,
                  seed=seed, tag=tag)
    if traj:
        traj.llm_request(req.key(), messages, req.model)
    resp = client.complete(req)
    if traj:
        traj.llm_response(resp.text, "cassette" if resp.from_cassette else resp.provider,
                          resp.prompt_tokens, resp.completion_tokens, resp.latency_s)
    try:
        payload = extract_json(resp.text)
        _v_b2(payload)
    except Exception as exc:
        # A malformed reply is recorded as ERROR, which is distinct from an
        # abstention. Folding it into INDETERMINATE would reward a broken arm
        # with the abstention arm's clean silent-error rate.
        if traj:
            traj.validation_error(f"{type(exc).__name__}: {exc}")
        return {"criterion_id": criterion["criterion_id"], "verdict": "ERROR",
                "evidence": [], "reasoning": f"unparseable reply: {exc}", "arm": "B2",
                "raw": resp.text[:500]}
    return {"criterion_id": criterion["criterion_id"], "verdict": payload["verdict"],
            "evidence": payload.get("evidence", []),
            "reasoning": payload.get("reasoning", ""), "arm": "B2"}


def b3_cell(client: Client, criterion: dict, chart: Chart, record: str,
            traj: Trajectory | None = None, samples: int = 3,
            temperature: float = 0.7) -> dict:
    """B2 sampled several times; disagreement becomes INDETERMINATE."""
    votes = []
    for i in range(samples):
        r = b2_cell(client, criterion, chart, record, traj, temperature=temperature, seed=7 + i)
        votes.append(r["verdict"])
    uniq = set(votes)
    if len(uniq) == 1:
        verdict = votes[0]
        why = f"unanimous across {samples} samples"
    else:
        verdict = "INDETERMINATE"
        why = f"disagreement across samples: {votes}"
    return {"criterion_id": criterion["criterion_id"], "verdict": verdict, "evidence": [],
            "reasoning": why, "arm": "B3", "votes": votes}
