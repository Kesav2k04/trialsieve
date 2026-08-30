"""Take the machine out of anything this repository generates and commits.

A generated file that quotes an absolute path is two problems wearing one coat.
It is machine-specific, so the same run on two computers writes two different
files and a byte comparison is worthless. And on most computers that path runs
through a home directory, so the file names a person.

Both of those arrived here the same way: a Python traceback. `contamination.py`
stores one when a counterfactual cannot compile, because "KeyError: 'text'" names
a key and not the line that wanted it. Every frame in that traceback carries the
absolute path of the file it is in. In the tree this was written in, the checkout
is `D:\\trialsieve` and nothing looked wrong. Cloned into a home directory, which
is where a judge will clone it, the same command wrote a home directory into a
tracked file seven times.

So the rewrite is not "hide the username". It is "a path inside this repository
is written relative to this repository", which happens to make the private case
impossible and happens to make the file reproducible. Anything still absolute
after that came from outside the checkout and only its home directory is
collapsed, because a system path is not private and deleting it would remove the
one clue that says the call left the repository.
"""

from __future__ import annotations

import re
from pathlib import Path

#: A path appears in more shapes than the one `str(Path)` produces. A traceback
#: on Windows writes backslashes; the same string inside JSON writes them
#: doubled; a URL or a git-bash line writes forward slashes. Redacting one shape
#: and missing the rest is the mistake this repository already made once, in the
#: agent-trace exporter, and `tests/test_agent_traces.py` is where it failed.
def _shapes(prefix: Path) -> list[str]:
    native = str(prefix)
    posix = prefix.as_posix()
    return sorted({native, native.replace("\\", "\\\\"), posix}, key=len, reverse=True)


def _home_shapes() -> list[str]:
    return _shapes(Path.home())


def paths(text: str, root: Path) -> str:
    """Rewrite paths inside `root` as relative, then collapse any home directory.

    Order matters. A checkout under a home directory matches both patterns, and
    the repository-relative form is the more useful of the two, so it wins.
    """
    for shape in _shapes(Path(root)):
        for sep in ("\\\\", "\\", "/"):
            text = text.replace(shape + sep, "")
        text = text.replace(shape, ".")
    for shape in _home_shapes():
        text = text.replace(shape, "~")
    return text


#: The shapes a scan should reject in a generated file. Kept beside the rewrite
#: so that a scanner and the thing it scans cannot drift apart.
ABSOLUTE = re.compile(
    # A drive letter is exactly one letter, so the lookbehind is load-bearing.
    # Without it, `including:` followed by an escaped newline inside JSON reads
    # as a drive letter, and twelve lines of registered trial text scored as a
    # leak on the first run of this scan.
    r"(?<![A-Za-z])[A-Za-z]:[\\/]"
    r"|/(?:home|Users)/[A-Za-z0-9]"
)


def has_absolute_path(text: str) -> bool:
    return ABSOLUTE.search(text) is not None
