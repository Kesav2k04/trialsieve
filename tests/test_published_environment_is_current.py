"""The published environment record has to describe the published numbers.

`results/published/` holds three files that are meant to be one snapshot:
`results.json`, `RESULTS.md` and `environment.json`. `run.py publish` writes all
three together and `SUBMISSION.md` points a judge at the third for versions.

They came apart. `environment.json` recorded a commit eighteen behind HEAD and
`locked_packages: 23` when the lockfile held 8, while the two beside it had been
rewritten four and a half hours later. `run.py diff` could not see it, because it
compares `RESULTS.md` and `results.json` and printed `IDENTICAL` over the top. A
reproduction guide whose environment record describes a different run is worse
than one with no record, because the mismatch is invisible unless someone opens
the third file.

So this checks the third file against things that cannot drift with it: the
lockfile it counts, the interpreter the current run recorded, and the commit
graph. It is deliberately not a byte comparison against a fresh snapshot, because
`utc` and `git_dirty` legitimately move between a publish and a check.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "results" / "published" / "environment.json"
CURRENT = ROOT / "results" / "environment.json"
LOCK = ROOT / "requirements-lock.txt"


def _published() -> dict:
    assert PUBLISHED.exists(), (
        "results/published/environment.json is gone, and SUBMISSION.md points a "
        "reader at it for versions")
    return json.loads(PUBLISHED.read_text(encoding="utf-8"))


def _locked() -> int:
    return sum(1 for line in LOCK.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.lstrip().startswith("#"))


def test_it_counts_the_lockfile_that_ships() -> None:
    published, real = _published().get("locked_packages"), _locked()
    assert published == real, (
        f"results/published/environment.json says {published} locked packages and "
        f"requirements-lock.txt has {real}. The snapshot was taken against a "
        f"different lockfile, so it is describing a different run. Re-run "
        f"`python run.py publish`.")


def test_it_names_the_same_interpreter_as_the_current_run() -> None:
    published, current = _published(), json.loads(CURRENT.read_text(encoding="utf-8"))
    for field in ("python", "implementation"):
        assert published.get(field) == current.get(field), (
            f"published environment says {field}={published.get(field)!r} and the "
            f"current run recorded {current.get(field)!r}. Either the published "
            f"numbers were produced on a different interpreter, in which case say "
            f"so, or the snapshot is stale.")


def test_it_names_a_commit_this_history_contains() -> None:
    from _shipped import has_git
    if not has_git():
        pytest.skip("no object database here, so a commit cannot be resolved. "
                    "An unpacked source archive carries the tree without it.")
    commit = _published().get("git_commit")
    assert commit, "the published environment records no commit"
    seen = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                          cwd=ROOT, capture_output=True)
    assert seen.returncode == 0, (
        f"results/published/environment.json names commit {commit}, which is not "
        f"in this repository. A judge cannot check out the state the published "
        f"numbers came from.")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT, capture_output=True)
    assert ancestor.returncode == 0, (
        f"commit {commit} is not an ancestor of HEAD, so the published numbers "
        f"claim to come from a state this branch never passed through")


def test_the_three_published_files_were_written_together() -> None:
    """A snapshot is one act. Two of three refreshed is the failure this had."""
    folder = PUBLISHED.parent
    names = ["results.json", "RESULTS.md", "environment.json"]
    missing = [n for n in names if not (folder / n).exists()]
    assert not missing, f"results/published/ is missing {missing}"
    stamps = {n: (folder / n).stat().st_mtime for n in names}
    spread = max(stamps.values()) - min(stamps.values())
    # An hour is generous for one `run.py publish`, and far tighter than the four
    # and a half hours that separated them when this was found.
    assert spread < 3600, (
        f"the three files in results/published/ were written {spread / 3600:.1f} "
        f"hours apart: {stamps}. `run.py publish` writes them together, so this "
        f"means two of them were copied by hand and the third was left behind. "
        f"Re-run `python run.py publish`.")
