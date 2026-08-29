"""Replay must never reach the network. That is the whole reproducibility claim.

`REPRODUCE.md` tells a reader that `python run.py reproduce` makes no model call
and that "replay never falls through to a live call". If that were ever false, a
judge on a different machine would silently re-record instead of reproducing, get
different numbers from a different model, and have no way to tell which happened.
The diff would report DIFFERENT and blame the arithmetic.

Nothing was testing it. These tests seal the two holes that matter: a request with
no cassette, and a cassette whose stored key does not match the request that found
it. Both must raise rather than call, and the test proves "rather than call" by
pointing the client at an endpoint that fails loudly if anything touches it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.llm import CassetteMiss, Client, Request  # noqa: E402


@pytest.fixture
def sealed(tmp_path, monkeypatch):
    """A replay client whose transport raises if it is ever entered."""
    calls = []

    def explode(*args, **kwargs):
        calls.append(1)
        raise AssertionError(
            "replay reached the transport. A reader on another machine would "
            "silently re-record here and call the result a reproduction.")

    import trialsieve.llm as llm
    monkeypatch.setattr(llm.Client, "_call_openai", explode, raising=True)
    monkeypatch.setattr(llm.Client, "_call_cli", explode, raising=True)
    c = Client(provider="openai", model="test-model", mode="replay",
               cassette_dir=tmp_path, base_url="http://127.0.0.1:9/v1")
    return c, calls


def ask(client):
    return client.complete(Request(
        model="test-model",
        messages=[{"role": "user", "content": "does the record say?"}],
        tag="sealed-probe"))


def test_a_missing_cassette_raises_instead_of_calling(sealed):
    client, calls = sealed
    with pytest.raises(CassetteMiss) as exc:
        ask(client)
    assert not calls, "the transport was entered"
    assert "never falls through" in str(exc.value), (
        "the error should say why it refused, because a reader who hits this "
        "needs to know it is a missing recording and not a broken endpoint")


def test_the_error_names_the_request(sealed):
    client, _ = sealed
    with pytest.raises(CassetteMiss) as exc:
        ask(client)
    msg = str(exc.value)
    assert "sealed-probe" in msg, "a miss that does not say which call missed is a dead end"
    assert "record mode" in msg, "the error should name the way out"


def test_an_edited_cassette_raises_rather_than_replaying_it(sealed, tmp_path):
    """A file whose contents no longer match its own key is not evidence.

    The cassette name is the first 16 characters of the request hash and the full
    hash is stored inside. Editing the stored prompt without renaming the file
    would otherwise replay an answer to a question nobody asked.
    """
    import json

    client, calls = sealed
    # Record what the client would look for, then plant a file under that name
    # carrying somebody else's key.
    with pytest.raises(CassetteMiss) as first:
        ask(client)
    key16 = str(first.value).split("key ")[1].split(")")[0].strip()
    (tmp_path / f"{key16}.json").write_text(json.dumps({
        "key": "0" * 64,
        "provider": "openai",
        "response": {"text": "an answer to a different question", "model": "test-model",
                     "prompt_tokens": 1, "completion_tokens": 1, "latency_s": 0.0},
    }), encoding="utf-8", newline="\n")

    with pytest.raises(CassetteMiss) as exc:
        ask(client)
    assert not calls
    assert "edited or the prompt changed" in str(exc.value)


def test_record_mode_is_the_only_mode_that_may_call(tmp_path, monkeypatch):
    """Stated as a test so that widening replay later fails here rather than quietly."""
    import inspect

    import trialsieve.llm as llm
    src = inspect.getsource(llm.Client.complete)
    assert 'if self.mode == "replay":' in src, (
        "the replay guard moved or changed shape. Whatever replaced it has to be "
        "read before this assertion is updated.")
    # The guard must sit before the dispatch, not after it.
    assert src.index('if self.mode == "replay":') < src.index("_call_cli"), (
        "the replay guard is after the transport dispatch, so a miss would call "
        "first and refuse afterwards")


def test_reproduce_replays_under_the_model_that_recorded():
    """A replay must name the model the recording named, or it matches nothing.

    The model is part of the request the cassette key hashes. `run_arms.py`
    defaults `--provider` to ollama, the B2 arm was recorded on the shim, and
    `run.py reproduce` passed neither flag, so it rebuilt all 400 prompts under
    `granite3.1-dense:8b` and missed every cassette on the first call. The
    reproduction stopped with a CassetteMiss that reads like corrupt recordings
    rather than a wrong flag, and this repository's central claim is that its
    numbers regenerate offline.

    So this asserts the resolved model equals the one inside the cassettes,
    rather than asserting a constant, which would drift the same way.
    """
    import json
    import sys

    sys.path.insert(0, str(ROOT))
    import run as runner

    cells = ROOT / "runs" / "tierA" / "cells"
    metas = sorted(cells.glob("meta_B2_*.json"))
    if not metas:
        return  # a checkout without the sampled arm reproduces everything else

    for meta_path in metas:
        tag = meta_path.stem.split("_", 2)[-1]
        resolved = runner._recorded_model("runs/tierA", "B2", tag)
        assert resolved, f"no model resolves for the recorded arm in {meta_path.name}"

        recorded = set()
        for traj in (ROOT / "runs" / "tierA" / "trajectories" / "baseline-b2").glob(f"*{tag}.jsonl"):
            for line in traj.read_text(encoding="utf-8").splitlines():
                key = json.loads(line).get("cassette_key")
                if not key:
                    continue
                cas = ROOT / "runs" / "tierA" / "cassettes" / f"{key[:16]}.json"
                if cas.exists():
                    recorded.add(json.loads(cas.read_text(encoding="utf-8"))["request"]["model"])

        assert recorded, f"no cassette backs the {tag} trajectories"
        assert recorded == {resolved}, (
            f"reproduce would replay {tag} as {resolved!r} but it was recorded "
            f"under {sorted(recorded)}. Every prompt would hash to a different "
            f"key and the reproduction would stop on the first cell.")
