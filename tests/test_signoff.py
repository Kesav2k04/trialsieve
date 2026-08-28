"""The gate must actually stop things. A checkpoint that cannot fail is decoration."""
from __future__ import annotations

import pytest

from trialsieve.signoff import NotSignedOff, Signoff, check, enforce

COMPILED = [
    {"criterion_id": "c1", "compilable": True, "predicate_sha256": "aaa"},
    {"criterion_id": "c2", "compilable": True, "predicate_sha256": "bbb"},
    {"criterion_id": "c3", "compilable": False, "reason_not_compilable": "consent"},
]


def sign(digest, decision="APPROVED"):
    return Signoff("c", digest, "Kesav2k04", decision, "checked against the source text",
                   "2026-08-29T00:00:00Z")


def test_unsigned_predicates_block_the_worklist():
    with pytest.raises(NotSignedOff, match="no human sign-off"):
        enforce(COMPILED, {"aaa": sign("aaa")})


def test_a_rejected_predicate_also_blocks():
    signoffs = {"aaa": sign("aaa"), "bbb": sign("bbb", "REJECTED")}
    with pytest.raises(NotSignedOff):
        enforce(COMPILED, signoffs)


def test_fully_signed_predicates_pass():
    signoffs = {"aaa": sign("aaa"), "bbb": sign("bbb", "APPROVED_WITH_NOTE")}
    out = enforce(COMPILED, signoffs)
    assert {c["criterion_id"] for c in out} == {"c1", "c2", "c3"}


def test_a_non_compilable_criterion_needs_no_signature():
    """It asserts nothing about a patient, so there is nothing to approve."""
    st = check([COMPILED[2]], {})
    assert st["ready"] and st["missing"] == []


def test_recompiling_invalidates_an_existing_signature():
    """The signature is over the predicate, not over the criterion name."""
    signoffs = {"aaa": sign("aaa"), "bbb": sign("bbb")}
    recompiled = [dict(COMPILED[0], predicate_sha256="ccc"), COMPILED[1], COMPILED[2]]
    with pytest.raises(NotSignedOff):
        enforce(recompiled, signoffs)
