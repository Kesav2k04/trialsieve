"""Trajectory recording.

A trajectory is the evidence that the agent did what the write-up says it did, so
it records what actually happened rather than a tidied narrative: the verbatim
instructions, every tool call and what came back, every validation failure and
the exact text fed back to the model, every retry, and every point where a human
had to approve something before it could be used.

Failures stay in. A trajectory in which every step succeeded on the first attempt
is either a trivial task or an edited log, and a reader can tell.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Trajectory:
    agent: str
    subject: str
    events: list[dict[str, Any]] = field(default_factory=list)
    _seq: int = 0

    def _add(self, event_kind: str, /, **payload: Any) -> dict[str, Any]:
        # Positional-only: payloads legitimately carry a field called "kind"
        # (a criterion is an inclusion or an exclusion), and a keyword clash here
        # would make the recorder fail on exactly the events worth recording.
        self._seq += 1
        e = {"seq": self._seq, "event": event_kind, **payload}
        self.events.append(e)
        return e

    # The event vocabulary is closed on purpose: a reader can diff two
    # trajectories without first learning a bespoke schema.
    def instructions(self, text: str, version: str) -> None:
        self._add("instructions", prompt_version=version, text=text)

    def input(self, **payload: Any) -> None:
        self._add("input", **payload)

    def tool_call(self, tool: str, **args: Any) -> None:
        self._add("tool_call", tool=tool, args=args)

    def tool_result(self, tool: str, result: Any, error: str | None = None) -> None:
        self._add("tool_result", tool=tool, result=result, error=error)

    def llm_request(self, cassette_key: str, messages: list[dict], model: str) -> None:
        self._add("llm_request", cassette_key=cassette_key, model=model, messages=messages)

    def llm_response(self, text: str, source: str, prompt_tokens: int,
                     completion_tokens: int, latency_s: float,
                     transport_retries: list[str] | None = None) -> None:
        self._add("llm_response", source=source, text=text, prompt_tokens=prompt_tokens,
                  completion_tokens=completion_tokens, latency_s=latency_s)
        for i, why in enumerate(transport_retries or [], 1):
            self.transport_retry(i, why)

    def transport_retry(self, attempt: int, error: str) -> None:
        """The endpoint failed and the same request was sent again.

        A separate event kind from `retry`, which means the model returned
        something the validator rejected and was given the error text back. This
        one carries no information about the model at all. Counting them together
        would let a bad evening on a gateway be read as a bad model.
        """
        self._add("transport_retry", attempt=attempt, error=error)

    def validation_error(self, message: str) -> None:
        self._add("validation_error", message=message)

    def retry(self, attempt: int, feedback_to_model: str) -> None:
        """`feedback_to_model` is stored verbatim: it is the thing that changed the next step."""
        self._add("retry", attempt=attempt, feedback_to_model=feedback_to_model)

    def critic_finding(self, verdict: str, finding: str, counterexample: Any = None) -> None:
        self._add("critic_finding", verdict=verdict, finding=finding,
                  counterexample=counterexample)

    def normalisation(self, what: str, before: Any, after: Any) -> None:
        """A field the model got slightly wrong that the harness repaired itself.

        Kept separate from `revision`. Silently accepting `laboratory_value`
        where the grammar says `observation` is a real repair and belongs in the
        record, but counting it alongside a predicate rewritten after a failed
        counterexample would inflate the interesting number with housekeeping.
        """
        self._add("normalisation", what=what, before=before, after=after)

    def revision(self, what: str, before: Any, after: Any) -> None:
        self._add("revision", what=what, before=before, after=after)

    def human_checkpoint(self, reviewer: str, decision: str, rationale: str,
                         artifact_sha256: str, reviewer_role: str = "") -> None:
        self._add("human_checkpoint", reviewer=reviewer, decision=decision,
                  rationale=rationale, artifact_sha256=artifact_sha256,
                  reviewer_role=reviewer_role)


def append_human_checkpoint(root: str | Path, agent: str, subject: str,
                            **payload: Any) -> Path | None:
    """Add a checkpoint to a trajectory that was written and closed long ago.

    A sign-off happens hours or days after the compile that produced the
    predicate, in a different process, so there is no live `Trajectory` object to
    call `human_checkpoint` on. Without this the event kind existed, was rendered,
    was counted, and was never once emitted: the trajectory index described a
    mechanism with no call site, which is the same defect as a check that cannot
    fail.

    The event is appended to the existing file rather than rewritten, and the
    sequence number continues from the last line, so the log stays a single
    ordered record of everything that happened to that criterion including the
    part a human did.

    Returns the path written, or None if there is no such trajectory. A missing
    file is not an error here: signing a run whose trajectories were not kept is
    allowed, and losing the signature over it would be worse.
    """
    p = Path(root) / agent / f"{_safe(subject)}.jsonl"
    if not p.exists():
        return None
    lines = [x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    last = json.loads(lines[-1]) if lines else {}
    event = {"seq": int(last.get("seq", 0)) + 1, "event": "human_checkpoint", **payload}
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return p

    def final(self, **payload: Any) -> None:
        self._add("final", **payload)

    # -- persistence --------------------------------------------------------
    def write(self, root: str | Path) -> Path:
        d = Path(root) / self.agent
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{_safe(self.subject)}.jsonl"
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            for e in self.events:
                fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")
        return p

    def summary(self) -> dict[str, Any]:
        kinds: dict[str, int] = {}
        for e in self.events:
            kinds[e["event"]] = kinds.get(e["event"], 0) + 1
        return {"agent": self.agent, "subject": self.subject, "events": len(self.events),
                "by_kind": kinds}


def _safe(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in s)[:120]


def render_markdown(path: str | Path) -> str:
    """Render one trajectory for a human reader. The JSONL stays the source of truth."""
    lines: list[str] = []
    with open(path, encoding="utf-8") as fh:
        events = [json.loads(x) for x in fh if x.strip()]
    if not events:
        return "(empty trajectory)\n"
    for e in events:
        k = e["event"]
        head = f"### {e['seq']}. {k}"
        if k == "instructions":
            # `.get`, not `[]`. This renderer reads JSONL off disk, including logs
            # written by an earlier version of the recorder, and a missing
            # optional field used to raise KeyError and take the whole index build
            # down with it. One old event should degrade one heading, not stop
            # every trajectory in the run from rendering.
            ver = e.get("prompt_version")
            lines += [head + (f" (prompt {ver})" if ver else " (prompt version not recorded)"),
                      "", "```", e.get("text", ""), "```", ""]
        elif k == "llm_request":
            body = "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in e["messages"])
            lines += [head + f" -> {e['model']}  cassette `{e['cassette_key'][:16]}`", "",
                      "```", body, "```", ""]
        elif k == "llm_response":
            lines += [head + f" ({e['source']}, {e['completion_tokens']} tok, "
                             f"{e['latency_s']}s)", "", "```", e["text"], "```", ""]
        elif k == "tool_call":
            lines += [head + f" `{e['tool']}`", "", "```json",
                      json.dumps(e["args"], indent=1)[:1500], "```", ""]
        elif k == "tool_result":
            body = json.dumps(e["result"], indent=1)[:1500] if e["result"] is not None else ""
            lines += [head + f" `{e['tool']}`" + (f" ERROR: {e['error']}" if e.get("error") else ""),
                      "", "```json", body, "```", ""]
        elif k == "retry":
            lines += [head + f" (attempt {e['attempt']}), verbatim feedback returned to the model:",
                      "", "```", e["feedback_to_model"], "```", ""]
        elif k == "human_checkpoint":
            lines += [head + f": **{e['decision']}** by {e['reviewer']}", "",
                      f"> {e['rationale']}", "",
                      f"artifact sha256 `{e['artifact_sha256'][:16]}`", ""]
        else:
            payload = {kk: vv for kk, vv in e.items() if kk not in ("seq", "event")}
            lines += [head, "", "```json", json.dumps(payload, indent=1)[:1800], "```", ""]
    return "\n".join(lines) + "\n"
