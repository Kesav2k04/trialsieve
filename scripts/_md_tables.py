"""Pad markdown tables so their columns line up in a monospace reader.

    from _md_tables import align
    text = align(text)

These tables get read three ways. A repository page renders them into a grid and
does the aligning for the reader. A person opening the raw `.md` in an editor, and
a viewer watching a table go past on a video frame, both get the characters as
written, and ragged pipes make them work to find which number sits under which
heading. `| TS | 30 | 18 | 60.0% |` under `| arm | screens | ruled out |` is a
lookup, not a reading.

Applied once where a document is written rather than at the dozen places that
build a row, so a new table is aligned without anyone remembering to align it.
Padding is the only change: the cell text, the column count and the row order are
untouched, so the rendered output is identical to what it was before.

Lines inside a fenced code block are left exactly as they are. A fence can hold a
pipe table that is being shown as text rather than used as one, and reformatting
it would edit the thing the surrounding prose is pointing at.
"""
from __future__ import annotations

import re

#: A separator row: three or more dashes per cell, with optional alignment colons.
_SEP = re.compile(r"^:?-{3,}:?$")


def _cells(line: str) -> list[str]:
    """The cells of a pipe row, without the leading and trailing delimiters."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and len(s) > 1


def _is_sep(line: str) -> bool:
    cells = _cells(line)
    return bool(cells) and all(_SEP.match(c) for c in cells)


def _render(block: list[str]) -> list[str]:
    """Pad one table. Returns it unchanged if the rows disagree on column count."""
    rows = [_cells(l) for l in block]
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        # A ragged table is a table this cannot pad without inventing a cell, and
        # inventing one would move a number under the wrong heading. Left alone
        # and left visibly ragged, which is the honest rendering of a ragged table.
        return block

    widths = [max(len(r[i]) for j, r in enumerate(rows) if j != 1)
              for i in range(width)]
    out = []
    for n, r in enumerate(rows):
        if n == 1:
            # Keep whatever alignment colons the separator carried.
            cells = []
            for i, c in enumerate(r):
                left, right = c.startswith(":"), c.endswith(":")
                # +2 for the space each data cell carries either side of it, so
                # the rule under a heading is exactly as wide as the column.
                dashes = "-" * max(3, widths[i] + 2 - left - right)
                cells.append((":" if left else "") + dashes + (":" if right else ""))
            out.append("|" + "|".join(cells) + "|")
        else:
            out.append("| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(r))
                       + " |")
    return out


def align(text: str) -> str:
    """Every markdown table in `text`, padded. Everything else byte-identical."""
    lines = text.split("\n")
    out: list[str] = []
    block: list[str] = []
    fenced = False

    def flush() -> None:
        if len(block) >= 2 and _is_sep(block[1]):
            out.extend(_render(block))
        else:
            out.extend(block)
        block.clear()

    for line in lines:
        if line.lstrip().startswith("```"):
            flush()
            fenced = not fenced
            out.append(line)
            continue
        if not fenced and _is_row(line):
            block.append(line)
            continue
        flush()
        out.append(line)
    flush()
    return "\n".join(out)
