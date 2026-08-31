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


def test_the_published_snapshot_names_its_own_interpreter() -> None:
    """The record has to say what produced the numbers, whoever is reading it."""
    published = _published()
    for field in ("python", "implementation", "platform"):
        value = published.get(field)
        assert isinstance(value, str) and value.strip(), (
            f"results/published/environment.json has no {field}, so it does not "
            f"say what the published numbers were produced on")


def test_a_different_interpreter_reproduced_the_same_numbers() -> None:
    """The claim is that the numbers come back, not that everyone runs 3.14.

    This used to require the current run's interpreter to equal the published
    one. On the machine that published, it passed. Everywhere else it could not:
    `results/environment.json` is rewritten by whoever runs `run.py reproduce`,
    so a judge on any other Python failed a test whose message told them the
    snapshot was stale when nothing was stale. CI found it, on 3.13, against a
    snapshot taken on 3.14.

    What is worth asserting is the opposite of what it asserted. A different
    interpreter is expected. What must not differ is the numbers, so that is what
    is checked, and it is a stronger claim than the one it replaces: the
    published figures are reproduced by an interpreter that did not produce them.
    """
    published = _published()
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    pub_results = ROOT / "results" / "published" / "results.json"
    cur_results = ROOT / "results" / "results.json"
    if not (pub_results.exists() and cur_results.exists()):
        pytest.skip("no results pair in this checkout to compare")
    same_interpreter = all(published.get(f) == current.get(f)
                           for f in ("python", "implementation"))
    # The comparison `run.py` itself makes, rather than a fresh one. A raw dict
    # equality here failed on CI over `wall_s`, which is how long the run took:
    # a test written to check that the numbers reproduce, failing on a clock.
    # `_canonical` is the project's own definition of which fields are numbers
    # and which are timestamps, so borrowing it keeps this test and the command
    # a judge runs from disagreeing about what reproduced.
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ts_run", ROOT / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    a = mod._canonical(pub_results, drop_provenance=True)
    b = mod._canonical(cur_results, drop_provenance=True)
    where = "the same interpreter" if same_interpreter else (
        f"{current.get('python')} against figures published on "
        f"{published.get('python')}")
    assert a == b, (
        f"results/results.json does not match results/published/results.json, "
        f"running on {where}. The published numbers did not reproduce here, "
        f"which is the one thing `python run.py reproduce` claims.")


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
