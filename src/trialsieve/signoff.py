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
    #: Which compiled seed was rendered on screen. Seeds compile the same
    #: criteria, and an identical predicate has an identical digest, so a
    #: signature matches every seed that produced that predicate. The reviewer
    #: read one of them. Without this, restoring a decision into "every
    #: trajectory the digest matches" turned 19 decisions into 44 checkpoints.
    #: `None` on ledger lines written before the field; see `reviewed_seed`.
    seed: int | None = None
    #: What the reviewer is qualified to say. Recorded because the ground rule
    #: is that a qualified human reviews anything that could affect a person,
    #: and a signature that does not say who signed it cannot be audited
    #: against that rule. In this repository the value is not "clinician", and
    #: the report says so rather than leaving it to be assumed.
    reviewer_role: str = "unspecified"

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


def reviewed_seed(run: str | Path) -> int | None:
    """The seed `scripts/signoff.py` would have put in front of a reviewer.

    It renders `sorted(glob("criteria_seed*.json"))[0]`, so a decision recorded
    before the ledger carried a seed was taken against that file. Derived rather
    than defaulted to 7, because a run whose seeds start elsewhere would then have
    its checkpoints restored into a trajectory nobody read.
    """
    import re

    files = sorted(Path(run).glob("compiled/criteria_seed*.json"))
    if not files:
        return None
    m = re.search(r"seed(\d+)", files[0].name)
    return int(m.group(1)) if m else None


def replay_into_trajectories(ledger: str | Path, compiled: list[dict],
                             trajectories: str | Path, seed: int = 7) -> list[str]:
    """Put every recorded decision back into the trajectory it belongs to.

    A compile rewrites `trajectories/compiler/*.jsonl` from the cassettes, which
    deletes any `human_checkpoint` appended after the fact. That made the sign-off
    the one event in the whole log that a rebuild could destroy, and the only one
    that no replay could reconstruct, because a human made it.

    This is idempotent by digest: a checkpoint already carrying that
    `artifact_sha256` is left alone. So it can sit on the reproduce path and run
    every time without ever writing a duplicate.

    Returns the criterion ids it wrote, so a caller can say how many it restored
    rather than claiming it silently.
    """
    from . import trace

    signoffs = load(ledger)
    if not signoffs:
        return []
    root = Path(trajectories)
    fallback = reviewed_seed(Path(ledger).parent)
    written: list[str] = []
    for c in compiled:
        s = signoffs.get(c.get("predicate_sha256", ""))
        if s is None:
            continue
        # The decision belongs to the rendering the reviewer read, not to every
        # seed that happens to produce the same digest.
        if (s.seed if s.seed is not None else fallback) != seed:
            continue
        name = trace.safe_name(f"{c['criterion_id']}-seed{seed}")
        path = root / "compiler" / f"{name}.jsonl"
        if not path.exists():
            continue
        if f'"{s.predicate_sha256}"' in path.read_text(encoding="utf-8"):
            continue
        trace.append_human_checkpoint(
            root, "compiler", f"{c['criterion_id']}-seed{seed}",
            reviewer=s.reviewer, reviewer_role=s.reviewer_role,
            decision=s.decision, rationale=s.rationale,
            artifact_sha256=s.predicate_sha256, signed_at=s.signed_at)
        written.append(c["criterion_id"])
    return written


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
    if st["rejected"]:
        # A rejection blocks, and it blocks differently from an absence. The
        # tempting alternative is to drop the rejected predicate and screen on
        # the rest, which produces a worklist where a criterion the reviewer
        # said is wrong is simply not applied to anybody. Nobody reading that
        # document would know a criterion was missing from it. So the run stops
        # until the predicate is fixed and recompiled, which invalidates the
        # signature anyway because the signature is over the digest.
        raise NotSignedOff(
            f"{len(st['rejected'])} compiled criterion/criteria were reviewed and "
            f"REJECTED, so no worklist can be produced until they are recompiled. A "
            f"rejected predicate is not dropped and screened around: a criterion the "
            f"reviewer found wrong would then be applied to nobody, and the document "
            f"would not say so. Rejected: {', '.join(st['rejected'][:6])}"
            + (" ..." if len(st["rejected"]) > 6 else "")
            + (f". Also unsigned: {', '.join(st['missing'][:6])}"
               if st["missing"] else "")
            + ". Read them with `python scripts/signoff.py --run <run> --show <id>`.")
    if st["missing"]:
        raise NotSignedOff(
            f"{len(st['missing'])} compiled criterion/criteria have no human sign-off. "
            f"A worklist cannot be produced from unreviewed predicates. Run "
            f"`python scripts/signoff.py --run <run>` to review them. Unsigned: "
            f"{', '.join(st['missing'][:6])}"
            + (" ..." if len(st["missing"]) > 6 else ""))
    # Nothing is filtered here. Everything compilable is approved by the time we
    # reach this line, and everything non-compilable asserts nothing about a
    # patient. An earlier version dropped rejected predicates at this point,
    # which was unreachable code describing a policy the check above forbids.
    return list(compiled)
