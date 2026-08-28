"""The search step is lexical on purpose, so its blind spots are spelling.

A concept that comes back with an empty candidate list becomes UNMAPPABLE, the
criterion becomes non-compilable, and the run looks conservative. That is the most
expensive way to be wrong here, because it costs coverage and leaves no trace that
anything went wrong: an empty shortlist and a genuinely absent concept produce the
same output.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialsieve import terminology as T  # noqa: E402


def codes(term, domain, n=6):
    return [c.code for c in T.search(term, domain, n)]


def test_british_spelling_finds_the_american_entry():
    """A protocol says anaemia. A US-built record system says Anemia."""
    assert "271737000" in codes("Anaemia", "condition")
    assert "271737000" in codes("Anemia", "condition")


def test_haemoglobin_and_hemoglobin_are_the_same_search():
    assert codes("Haemoglobin A1c", "observation") == codes("Hemoglobin A1c", "observation")


def test_haemodialysis_finds_a_dialysis_procedure():
    assert "302497006" in codes("Haemodialysis", "procedure")


def test_folding_is_symmetric_so_it_cannot_lose_a_match():
    """Both sides fold, so an over-eager rule costs a spare candidate, not a hit."""
    assert T._fold("aerobic") == T._fold("erobic")
    assert T._fold("tumour") == T._fold("tumor")
    assert T._fold("organisation") == T._fold("organization")


def test_a_concept_the_vocabulary_lacks_still_returns_nothing():
    """The fold must not invent a match. UNMAPPABLE has to stay reachable."""
    assert codes("Gastroparesis", "condition") == []
    assert codes("Metoprolol", "medication") == []


def test_a_word_collision_is_shortlisted_but_not_ranked_first():
    """Recall here, precision next.

    "Respiratory rate" shares a word with "glomerular filtration rate" and is
    returned as a candidate. That is correct: this step is not allowed to decide,
    and a shortlist that quietly dropped near misses would hide from the select
    step exactly the distinctions it exists to make. What this step owes is
    ranking, and the real code has to come first.
    """
    got = codes("Glomerular filtration rate", "observation", 8)
    assert got[0] == "33914-3"
    assert "9279-1" in got


def test_panel_count_is_zero_for_a_code_no_patient_carries():
    """The corpus has 1079 dialysis rows. This panel has none of them."""
    assert T.panel_count("265764009") is None
    assert (T.panel_count("44054006") or {}).get("patients") == 27
