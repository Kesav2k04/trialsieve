"""Shared plumbing for the model-facing agents.

Structured output is obtained with a fenced JSON convention plus a validator plus
a bounded repair loop, rather than with provider-specific tool calling. That
choice is about reach: the same agent code has to run against an OpenAI-style
endpoint, against a local model served by Ollama, and against a CLI behind the
shim, and tool-calling support differs across all three. A validator and one
repair turn work everywhere.

The repair message sent back to the model is the exact validator error. It is
recorded verbatim in the trajectory, because that text is what changed the next
step and a reader should be able to judge whether it was fair.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from ..llm import Client, Request
from ..trace import Trajectory

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


class AgentError(RuntimeError):
    pass


def extract_json(text: str) -> Any:
    """Pull one JSON document out of a model reply.

    Models wrap JSON in fences, prefix it with a sentence, or emit it bare. All
    three are accepted; anything else is a hard failure that goes back as a
    repair message rather than being guessed at.
    """
    for m in FENCE.finditer(text):
        body = m.group(1).strip()
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            continue
    t = text.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        i, j = t.find(opener), t.rfind(closer)
        if 0 <= i < j:
            try:
                return json.loads(t[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise AgentError(f"no JSON object found in reply of {len(text)} chars")


def ask_json(client: Client, traj: Trajectory, messages: list[dict[str, str]],
             validate: Callable[[Any], None], *, tag: str, model: str = "",
             prompt_version: str = "v1", max_repairs: int = 2,
             temperature: float = 0.0, seed: int | None = None) -> Any:
    """One model turn, validated, with a bounded repair loop.

    Returns the first payload that passes `validate`. Raises after the repair
    budget is spent, and never returns a partially-valid object: an agent that
    degrades quietly to something almost right is how a bad predicate reaches a
    patient.
    """
    # None means "whatever this run is seeded with", which is the right default
    # for every agent: none of them has a reason to pin a seed of its own, and
    # the one that hardcoded 7 silently disabled the multi-seed noise floor.
    if seed is None:
        seed = getattr(client, "seed", 7)
    convo = list(messages)
    last_err = ""
    for attempt in range(max_repairs + 1):
        req = Request(model=model or client.model, messages=convo,
                      temperature=temperature, seed=seed, tag=f"{tag}#a{attempt}")
        traj.llm_request(req.key(), convo, req.model)
        resp = client.complete(req)
        traj.llm_response(resp.text, "cassette" if resp.from_cassette else resp.provider,
                          resp.prompt_tokens, resp.completion_tokens, resp.latency_s,
                          resp.transport_retries)
        try:
            payload = extract_json(resp.text)
            validate(payload)
            return payload
        except Exception as exc:  # validation or parse failure
            last_err = f"{type(exc).__name__}: {exc}"
            traj.validation_error(last_err)
            if attempt == max_repairs:
                break
            feedback = (
                "That reply was rejected by the schema validator.\n\n"
                f"Error: {last_err}\n\n"
                "Return the corrected JSON only, with no commentary and no code fence. "
                "Do not restate the task. Fix exactly the error above and keep everything "
                "else identical."
            )
            traj.retry(attempt + 1, feedback)
            convo = convo + [{"role": "assistant", "content": resp.text},
                             {"role": "user", "content": feedback}]
    raise AgentError(f"{tag}: no valid reply after {max_repairs + 1} attempts. last: {last_err}")


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AgentError(msg)
