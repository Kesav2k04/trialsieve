"""Anywhere a document states how many changelog entries there are, recount it.

Three documents said three different things at once. `SUBMISSION.md` opened with
"the 38 entries behind it" and, seventy-nine lines later in the same file, "39
entries each tied to the command that shows it". The changelog's own introduction
said "Thirty-eight entries is more rows than that sketch has". There were 39.

The film said thirty-nine and was right, because that one is
`{{changelog_entries}}` resolved out of the file at build time rather than typed.
The derived figure was correct and all three typed ones had drifted, which is the
argument the changelog spends its whole length making, arriving uninvited.

So this recounts. Every "N entries" claim in a tracked markdown file, in digits or
spelled out, has to equal the number of `## <n>.` headings in
`docs/IMPROVEMENT_CHANGELOG.md`. It is cheap and it is the shape of drift that a
careful reader catches and a busy one does not.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "docs" / "IMPROVEMENT_CHANGELOG.md"

#: A numbered entry heading: `## 41. The one sentence ...`
ENTRY = re.compile(r"^## (\d+)\.", re.M)

#: `38 entries`, `Thirty-eight entries`, `forty-one entries`. Hyphenated tens are
#: one token, so `thirty-eight` matches without also matching a bare `eight`.
UNITS = ("one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
CLAIM = re.compile(
    r"\b(\d{1,3}|(?:twenty|thirty|forty|fifty)(?:-(?:" + "|".join(UNITS[:9]) + r"))?|"
    + "|".join(UNITS) + r")\s+entries\b", re.I)


#: What follows a count of entries that were added or removed, rather than a
#: statement of how many there are. Anchored at the start of what comes after
#: the word "entries", so it cannot match somewhere further along the line.
DELTA = re.compile(r"\s+(were|was|have been|has been|got|are)\s+"
                   r"(added|removed|written|appended|deleted)", re.I)


def _spelled(word: str) -> int | None:
    word = word.lower()
    if word.isdigit():
        return int(word)
    if "-" in word:
        tens, unit = word.split("-", 1)
        if tens in TENS and unit in UNITS:
            return TENS[tens] + UNITS.index(unit) + 1
        return None
    if word in TENS:
        return TENS[word]
    return UNITS.index(word) + 1 if word in UNITS else None


def _tracked_markdown() -> list[Path]:
    from _shipped import shipped_paths
    return [p for p in shipped_paths("*.md") if p.suffix == ".md"]


def _entries() -> int:
    return len(ENTRY.findall(CHANGELOG.read_text(encoding="utf-8")))


def test_the_entries_are_numbered_without_a_gap() -> None:
    """A count is only meaningful if the headings it counts are a clean run."""
    numbers = [int(n) for n in ENTRY.findall(CHANGELOG.read_text(encoding="utf-8"))]
    assert numbers, "no numbered entries found; the heading shape has changed"
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"the changelog headings are not 1..{len(numbers)}: they run {numbers}. "
        f"A duplicate or a skipped number makes every count below ambiguous.")


def test_no_document_states_a_stale_entry_count() -> None:
    paths = _tracked_markdown()
    expected = _entries()
    wrong: list[str] = []
    for path in paths:
        for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for match in CLAIM.finditer(line):
                value = _spelled(match.group(1))
                # Not every "N entries" is about this changelog. Only a claim that
                # sits next to the changelog, by name or by link, is one this test
                # can speak for.
                context = line.lower()
                if "changelog" not in context and "entries behind it" not in context:
                    continue
                # And not every claim about the changelog is a claim about its
                # size. "Two entries were added to this changelog" is a count of
                # a change, and entry 37 says exactly that about itself. A delta
                # is worded in the past tense; a total is not.
                if DELTA.match(line[match.end():]):
                    continue
                if value is not None and value != expected:
                    wrong.append(
                        f"{path.relative_to(ROOT).as_posix()}:{line_no} says "
                        f"{match.group(0)!r} and there are {expected}")
    assert not wrong, (
        "a document states a changelog size that the changelog does not have:\n  "
        + "\n  ".join(wrong)
        + "\n\nThese are typed by hand. The film's count is not: it resolves "
          "{{changelog_entries}} out of the file, which is why it stayed right "
          "while these drifted.")


def test_the_reader_can_parse_both_shapes() -> None:
    """The positive control. A parser that returned None everywhere would pass."""
    assert _spelled("38") == 38
    assert _spelled("thirty-eight") == 38
    assert _spelled("Forty-one".lower()) == 41
    assert _spelled("nine") == 9
    assert _spelled("banana") is None
    for shape in ("38 entries", "Thirty-eight entries", "forty-one entries"):
        assert CLAIM.search(shape), f"the claim pattern does not match {shape!r}"
    assert _entries() >= 40, (
        f"only {_entries()} entries parsed out of the changelog, which is fewer "
        f"than were there when this test was written; the heading shape probably "
        f"changed and the count above is being read from the wrong thing")
