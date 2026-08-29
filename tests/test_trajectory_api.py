"""The recorder's own surface, tested by using it.

Every event in every trajectory this project ships goes through this class, and
nothing was exercising it. That was not a hypothetical gap. Adding a module-level
function in the middle of the class body silently ended the class early, so
`final`, `write` and `summary` stopped being methods, and the whole suite of 153
tests stayed green. The break surfaced when a running job died on
`AttributeError: 'Trajectory' object has no attribute 'final'`.

A test suite that cannot notice a core class losing three methods is not covering
that class. These tests record a trajectory the way the agents do, write it, read
it back, and render it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.trace import (  # noqa: E402
    Trajectory, append_human_checkpoint, render_markdown)

#: Every event kind the recorder is supposed to be able to emit. The list is here
#: rather than derived from the class so that deleting a method is a failure
#: instead of a smaller list.
EVENT_METHODS = [
    "instructions", "input", "tool_call", "tool_result", "llm_request",
    "llm_response", "transport_retry", "validation_error", "retry",
    "critic_finding", "normalisation", "revision", "human_checkpoint", "final",
]


@pytest.mark.parametrize("name", EVENT_METHODS + ["write", "summary"])
def test_the_class_still_has_its_methods(name):
    """Cheap, and it is the exact assertion that would have caught the break."""
    assert callable(getattr(Trajectory, name, None)), (
        f"Trajectory.{name} is missing or is not callable. A function defined at "
        f"module level inside the class body ends the class body, and nothing "
        f"else in this suite notices.")


def full_trajectory() -> Trajectory:
    t = Trajectory("compiler", "NCT00000000-INC-01-seed7")
    t.instructions("compile this criterion", version="v3")
    t.input(criterion_id="NCT00000000-INC-01", kind="inclusion")
    t.tool_call("terminology.search_any", terms=["metformin"], domain="medication")
    t.tool_result("terminology.search_any", [{"code": "860975"}])
    t.llm_request("a" * 64, [{"role": "user", "content": "hello"}], "test-model")
    t.llm_response("{}", "openai", 10, 5, 1.5, transport_retries=["502 once"])
    t.validation_error("expr is not an object")
    t.retry(1, "your reply was not valid JSON")
    t.critic_finding("REVISE", "the window is wrong", counterexample={"age": 40})
    t.normalisation("domain", "laboratory_value", "observation")
    t.revision("expr", {"op": "and"}, {"op": "or"})
    t.final(compilable=True, predicate_sha256="b" * 64)
    return t


def test_a_recorded_trajectory_round_trips(tmp_path):
    t = full_trajectory()
    p = t.write(tmp_path)
    assert p.exists()
    events = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

    # The transport retry is emitted by llm_response, so there is one more event
    # than there were calls. That is deliberate and worth pinning.
    assert [e["event"] for e in events].count("transport_retry") == 1
    assert events[-1]["event"] == "final"
    seqs = [e["seq"] for e in events]
    assert seqs == list(range(1, len(events) + 1)), f"sequence is not dense: {seqs}"


def test_the_written_file_is_lf_regardless_of_platform(tmp_path):
    """A CRLF trajectory makes the tree permanently dirty on Windows."""
    p = full_trajectory().write(tmp_path)
    assert b"\r\n" not in p.read_bytes()


def test_a_payload_field_called_kind_does_not_collide(tmp_path):
    """`_add` is positional-only for this reason. A criterion has a `kind`."""
    t = Trajectory("compiler", "x")
    t.input(kind="exclusion")
    assert t.events[0]["kind"] == "exclusion"
    assert t.events[0]["event"] == "input"


def test_summary_counts_every_kind():
    s = full_trajectory().summary()
    assert s["agent"] == "compiler"
    assert s["events"] == 13
    assert s["by_kind"]["retry"] == 1
    assert s["by_kind"]["critic_finding"] == 1
    assert s["by_kind"]["normalisation"] == 1


def test_render_covers_every_event_kind(tmp_path):
    """A renderer that silently drops an event kind hides it from every reader."""
    p = full_trajectory().write(tmp_path)
    md = render_markdown(p)
    for kind in ("instructions", "tool_call", "tool_result", "llm_request",
                 "llm_response", "validation_error", "retry", "critic_finding",
                 "normalisation", "revision", "final"):
        assert kind in md, f"{kind} does not appear in the rendered trajectory"


def test_render_survives_an_event_missing_an_optional_field(tmp_path):
    """One old event should degrade one heading, not stop the index building."""
    p = tmp_path / "compiler" / "old.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"seq": 1, "event": "instructions", "text": "do it"}) + "\n",
                 encoding="utf-8", newline="\n")
    md = render_markdown(p)
    assert "not recorded" in md


def test_an_empty_trajectory_renders_rather_than_raising(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8", newline="\n")
    assert "empty" in render_markdown(p)


def test_append_returns_none_for_a_trajectory_that_is_not_there(tmp_path):
    assert append_human_checkpoint(tmp_path, "compiler", "nope", reviewer="x") is None
