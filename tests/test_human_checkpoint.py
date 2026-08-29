"""Signing has to land in the trajectory, not only in the ledger.

The brief asks for human checkpoints in the agent trajectories. The event kind
existed, `render_markdown` knew how to draw it, the index counted a column for it,
and nothing in the repository ever called it. Every one of those pieces looked
correct on its own, and the number they produced was a truthful zero, so nothing
failed.

These tests drive `scripts/signoff.py` the way a reviewer does, over a temporary
copy of a committed fixture, and then read both places the decision is supposed to
land.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIXTURE = ROOT / "tests" / "fixtures" / "gate_run"

pytestmark = pytest.mark.skipif(
    not (FIXTURE / "compiled" / "criteria_seed7.json").exists(),
    reason="the fixture run carries no compiled predicates")


@pytest.fixture
def run_dir(tmp_path):
    """The fixture, plus the compiler trajectory a real run would have left."""
    dest = tmp_path / "run"
    shutil.copytree(FIXTURE, dest)
    (dest / "signoffs.jsonl").unlink(missing_ok=True)

    blob = json.loads((dest / "compiled" / "criteria_seed7.json").read_text("utf-8"))
    compiled = [c for c in blob["criteria"] if c.get("compilable")]
    traj = dest / "trajectories" / "compiler"
    traj.mkdir(parents=True)
    for c in compiled:
        p = traj / f"{c['criterion_id']}-seed7.jsonl"
        p.write_text(
            json.dumps({"seq": 1, "event": "instructions", "text": "compile it"}) + "\n"
            + json.dumps({"seq": 2, "event": "final", "compilable": True}) + "\n",
            encoding="utf-8", newline="\n")
    return dest, compiled


def sign(run: Path, answers: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/signoff.py", "--run", str(run),
         "--reviewer", "A Reviewer", "--role", "author, not a clinician"],
        cwd=ROOT, input=answers, capture_output=True, text=True,
        encoding="utf-8", errors="replace")


def events(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_a_decision_reaches_both_the_ledger_and_the_trajectory(run_dir):
    run, compiled = run_dir
    c = compiled[0]
    p = sign(run, "a\nthe predicate says what the criterion says\nq\n")
    assert p.returncode in (0, 1), f"{p.stdout}\n{p.stderr}"

    ledger = run / "signoffs.jsonl"
    assert ledger.exists(), "nothing was written to the ledger"
    rows = events(ledger)
    assert any(r["predicate_sha256"] == c["predicate_sha256"] for r in rows)

    traj = run / "trajectories" / "compiler" / f"{c['criterion_id']}-seed7.jsonl"
    evs = events(traj)
    checkpoints = [e for e in evs if e["event"] == "human_checkpoint"]
    assert len(checkpoints) == 1, (
        "the decision reached the ledger and not the trajectory. The trajectory "
        "is the deliverable the brief names.")
    e = checkpoints[0]
    assert e["decision"] == "APPROVED"
    assert e["reviewer"] == "A Reviewer"
    assert e["reviewer_role"] == "author, not a clinician", (
        "a signature that does not record what the signer is qualified to say "
        "cannot be audited")
    assert e["artifact_sha256"] == c["predicate_sha256"], (
        "the checkpoint must name the digest it approved, or it approves whatever "
        "the file says next")
    assert e["rationale"]


def test_the_appended_event_continues_the_sequence(run_dir):
    """The log stays one ordered record rather than two glued together."""
    run, compiled = run_dir
    c = compiled[0]
    sign(run, "a\nlooks right\nq\n")
    evs = events(run / "trajectories" / "compiler" / f"{c['criterion_id']}-seed7.jsonl")
    seqs = [e["seq"] for e in evs]
    assert seqs == sorted(seqs), "the appended event broke the ordering"
    assert seqs == list(range(1, len(seqs) + 1)), f"sequence has a gap: {seqs}"
    assert evs[-1]["event"] == "human_checkpoint", "the checkpoint is not last"


def test_a_rejection_is_recorded_the_same_way(run_dir):
    """A rejection is data. Recording only approvals would make the log evidence
    for one side of a decision the gate exists to allow either way."""
    run, compiled = run_dir
    c = compiled[0]
    sign(run, "r\nthe window is wrong\nq\n")
    evs = events(run / "trajectories" / "compiler" / f"{c['criterion_id']}-seed7.jsonl")
    hit = [e for e in evs if e["event"] == "human_checkpoint"]
    assert len(hit) == 1 and hit[0]["decision"] == "REJECTED"
    assert hit[0]["rationale"] == "the window is wrong"


def test_a_missing_trajectory_does_not_lose_the_signature(run_dir):
    """Signing a run whose trajectories were not kept still records the decision."""
    run, compiled = run_dir
    shutil.rmtree(run / "trajectories")
    p = sign(run, "a\nfine\nq\n")
    assert (run / "signoffs.jsonl").exists(), (
        "the signature was lost because the trajectory was missing. The ledger is "
        "what the gate reads and it must not depend on the log.")
    assert "signoffs.jsonl only" in p.stdout, \
        "the fallback happened silently; a reader should be told the log is short"


def test_the_index_counts_what_was_written(run_dir):
    """The column that reported a truthful zero must now report a truthful one."""
    run, compiled = run_dir
    sign(run, "a\nfine\nq\n")
    r = subprocess.run(
        [sys.executable, "scripts/trajectories.py", "--run", str(run)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    index = (run / "trajectories" / "index.md").read_text(encoding="utf-8")
    assert "| human checkpoints | 1 |" in index, (
        "the event was written and the index did not count it")
