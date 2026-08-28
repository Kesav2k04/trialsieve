"""The human checkpoint, enforced rather than described.

A compiled predicate is a clinical judgement written by a model. Before it is
allowed to rule any real person out of a trial, a named human has to have read it
and said so. This module is what makes that a property of the code instead of a
sentence in a README.

The signature is over the predicate digest, not over the criterion id. Recompiling
changes the digest, which invalidates the signature, which stops the run. That is
the whole point: approval cannot silently carry over to a predicate nobody read.

Evaluation runs are exempt and say so. Measuring how often a system is wrong
affects nobody, and requiring a clinical signature before you are allowed to
measure your own error rate would be theatre. The gate guards the artifact that
reaches a coordinator.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DECISIONS = ("APPROVED", "REJECTED", "APPROVED_WITH_NOTE")


class NotSignedOff(RuntimeError):
    """Raised when a predicate would be used on a patient without human approval."""


@dataclass
class Signoff:
    criterion_id: str
    predicate_sha256: str
    reviewer: str
    decision: str
    rationale: str
    signed_at: str

    def as_dict(self) -> dict:
        return vars(self)


def load(path: str | Path) -> dict[str, Signoff]:
    p = Path(path)
    if not p.exists():
        return {}
    out: dict[str, Signoff] = {}
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            d = json.loads(line)
            out[d["predicate_sha256"]] = Signoff(**d)
    return out


def append(path: str | Path, s: Signoff) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(s.as_dict(), sort_keys=True, ensure_ascii=False) + "\n")


def check(compiled: list[dict], signoffs: dict[str, Signoff]) -> dict:
    """Report which compiled predicates are cleared for use on patients."""
    approved, missing, rejected = [], [], []
    for c in compiled:
        if not c.get("compilable"):
            continue                      # nothing will be asserted from it
        digest = c.get("predicate_sha256", "")
        s = signoffs.get(digest)
        if s is None:
            missing.append(c["criterion_id"])
        elif s.decision == "REJECTED":
            rejected.append(c["criterion_id"])
        else:
            approved.append(c["criterion_id"])
    return {"approved": approved, "missing": missing, "rejected": rejected,
            "ready": not missing and not rejected}


def enforce(compiled: list[dict], signoffs: dict[str, Signoff]) -> list[dict]:
    """Return the predicates cleared for patient-facing use, or refuse.

    Refusing is the correct behaviour and the failure message names what to do,
    because a gate that is annoying to satisfy gets bypassed and a gate that is
    bypassed is not a gate.
    """
    st = check(compiled, signoffs)
    if not st["ready"]:
        raise NotSignedOff(
            f"{len(st['missing'])} compiled criterion/criteria have no human sign-off and "
            f"{len(st['rejected'])} were rejected. A worklist cannot be produced from "
            f"unreviewed predicates. Run `python scripts/signoff.py --run <run>` to review "
            f"them. Unsigned: {', '.join(st['missing'][:6])}"
            + (" ..." if len(st["missing"]) > 6 else ""))
    ok = {c["criterion_id"] for c in compiled
          if not c.get("compilable")
          or signoffs[c["predicate_sha256"]].decision != "REJECTED"}
    return [c for c in compiled if c["criterion_id"] in ok]
