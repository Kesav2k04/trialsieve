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
