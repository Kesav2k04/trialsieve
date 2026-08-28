"""Three-valued (Kleene K3) truth values.

Eligibility screening has a third answer that binary logic cannot express: the
record does not say. Collapsing that to False silently converts "we have no
HbA1c on file" into "the patient's HbA1c is out of range", which is how a
confident wrong verdict reaches a coordinator. K3 keeps the distinction and
propagates it, so a verdict is only committed when it holds no matter what the
missing value turns out to be.
"""
from __future__ import annotations
from enum import Enum
from typing import Iterable


class TV(Enum):
    """A Kleene truth value."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - display only
        return self.value

    @property
    def known(self) -> bool:
        return self is not TV.UNKNOWN


T, F, U = TV.TRUE, TV.FALSE, TV.UNKNOWN


def tv(value: bool | None) -> TV:
    """Lift an optional bool into K3. None means the record is silent."""
    if value is None:
        return U
    return T if value else F


def k_not(a: TV) -> TV:
    if a is U:
        return U
    return F if a is T else T


def k_and(args: Iterable[TV]) -> TV:
    """False dominates: one proven failure settles a conjunction whatever else is unknown."""
    seen_unknown = False
    for a in args:
        if a is F:
            return F
        if a is U:
            seen_unknown = True
    return U if seen_unknown else T


def k_or(args: Iterable[TV]) -> TV:
    """True dominates: one proven success settles a disjunction."""
    seen_unknown = False
    for a in args:
        if a is T:
            return T
        if a is U:
            seen_unknown = True
    return U if seen_unknown else F


def k_at_least(n: int, args: Iterable[TV]) -> TV:
    """`at least n of the following` under K3.

    TRUE  when the proven-true count already reaches n.
    FALSE when even counting every unknown as true cannot reach n.
    UNKNOWN otherwise.
    """
    vals = list(args)
    t = sum(1 for a in vals if a is T)
    u = sum(1 for a in vals if a is U)
    if t >= n:
        return T
    if t + u < n:
        return F
    return U


def k_implies(a: TV, b: TV) -> TV:
    return k_or([k_not(a), b])
