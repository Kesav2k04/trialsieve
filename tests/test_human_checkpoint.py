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


def test_a_rebuild_cannot_lose_the_checkpoint(run_dir):
    """The one event in a trajectory that no replay can reconstruct.

    Everything else in these files records a model call, so a rebuild from the
    cassettes puts it back. A human's decision has no cassette. It was appended
    to the compiler trajectory after the compile, and `run.py reproduce` re-runs
    the compile, which rewrites that file. The first reproduce after a sign-off
    deleted all nineteen of them and the index went back to printing zero while
    the ledger still held every decision.

    So the ledger is the durable record and the trajectory is derived from it.
    This deletes the events the way a rebuild does, then requires them back.
    """
    import json as _json
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "src"))
    from trialsieve.signoff import replay_into_trajectories

    run, compiled = run_dir
    sign(run, "a\nfine\nq\n")
    traj = next((t for t in (run / "trajectories" / "compiler").glob("*.jsonl")
                 if '"human_checkpoint"' in t.read_text(encoding="utf-8")), None)
    assert traj is not None, "nothing was signed, so nothing is at risk"
    before = traj.read_text(encoding="utf-8")

    # What a rebuild does: rewrite the file without the appended event.
    kept = [l for l in before.splitlines()
            if l.strip() and _json.loads(l).get("event") != "human_checkpoint"]
    traj.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
    assert '"human_checkpoint"' not in traj.read_text(encoding="utf-8")

    restored = replay_into_trajectories(
        run / "signoffs.jsonl", compiled, run / "trajectories", seed=7)
    assert restored, "the ledger held a decision and nothing was put back"
    assert '"human_checkpoint"' in traj.read_text(encoding="utf-8"), (
        "a rebuild can still destroy the only event a human produced")

    # And running it twice must not duplicate, because it sits on a path that
    # runs on every reproduce.
    again = replay_into_trajectories(
        run / "signoffs.jsonl", compiled, run / "trajectories", seed=7)
    assert again == [], f"re-applying wrote {again} a second time"
    assert traj.read_text(encoding="utf-8").count('"human_checkpoint"') == 1


def test_one_decision_does_not_become_three_checkpoints(tmp_path):
    """Three seeds compile the same criterion, and a person read it once.

    The signature is over the predicate digest, and seeds 7, 8 and 9 produce the
    same digest wherever they compile the same thing. So a replay that restores a
    decision into every trajectory whose digest matches turned 19 decisions into
    44 human checkpoints, and the index published that. Defensible code, wrong
    number, and the number overstated human review, which is the direction that
    matters.
    """
    import json
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "src"))
    from trialsieve.signoff import replay_into_trajectories, reviewed_seed

    run = tmp_path / "run"
    (run / "compiled").mkdir(parents=True)
    crit = {"criterion_id": "NCT00000001-INC-01", "nct_id": "NCT00000001",
            "compilable": True, "predicate_sha256": "deadbeef"}
    for seed in (7, 8, 9):
        (run / "compiled" / f"criteria_seed{seed}.json").write_text(
            json.dumps({"seed": seed, "criteria": [crit]}), encoding="utf-8",
            newline=chr(10))
        d = run / "trajectories" / "compiler"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"NCT00000001-INC-01-seed{seed}.jsonl").write_text(
            json.dumps({"seq": 1, "event": "final", "compilable": True}) + "\n",
            encoding="utf-8", newline="\n")

    # A ledger line from before the seed was recorded. The seed it was taken
    # against is derivable: signoff.py renders whichever file sorts first.
    (run / "signoffs.jsonl").write_text(json.dumps({
        "criterion_id": "NCT00000001-INC-01", "predicate_sha256": "deadbeef",
        "reviewer": "A Reviewer", "reviewer_role": "author, not a clinician",
        "decision": "REJECTED", "rationale": "no exact code for the concept",
        "signed_at": "2026-08-31T00:00:00+00:00"}) + "\n",
        encoding="utf-8", newline="\n")
    assert reviewed_seed(run) == 7

    for seed in (7, 8, 9):
        replay_into_trajectories(run / "signoffs.jsonl", [crit],
                                 run / "trajectories", seed=seed)
    total = sum(t.read_text(encoding="utf-8").count('"human_checkpoint"')
                for t in (run / "trajectories" / "compiler").glob("*.jsonl"))
    assert total == 1, (
        f"one decision produced {total} checkpoints; a signature matching every "
        f"seed that shares a digest is not a person reviewing it that many times")
    signed = run / "trajectories" / "compiler" / "NCT00000001-INC-01-seed7.jsonl"
    assert '"human_checkpoint"' in signed.read_text(encoding="utf-8"), (
        "the one checkpoint landed in a seed the reviewer never saw")


def test_the_rendered_page_says_what_the_reviewer_is_qualified_to_say(run_dir):
    """The one question a reader of a human checkpoint should be able to answer.

    `reviewer_role` exists because the ground rule is that a qualified human
    reviews anything that could affect a person, and a signature that does not
    name the signer's qualification cannot be audited against it. It reached the
    ledger and `docs/GATE.md`, and the trajectory page read "APPROVED by Kesav".
    """
    run, compiled = run_dir
    sign(run, chr(10).join(["a", "fine", "q", ""]))
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "src"))
    from trialsieve.trace import render_markdown

    # Signing appends to the JSONL; `scripts/trajectories.py` renders the page,
    # and that is what the reproduce path runs. Render it here the same way.
    src = next((t for t in (run / "trajectories" / "compiler").glob("*.jsonl")
                if "human_checkpoint" in t.read_text(encoding="utf-8")), None)
    assert src is not None, "nothing was signed, so there is nothing to render"
    text = render_markdown(src)
    assert "human_checkpoint" in text, "the renderer dropped the event"
    assert "author, not a clinician" in text, (
        "the rendered checkpoint names the reviewer and not their role, so a "
        "reader cannot tell whether a clinician signed it")
