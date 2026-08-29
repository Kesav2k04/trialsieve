"""A gateway failure must not be recorded as a model failure.

The distinction these tests protect: `retry` in a trajectory means the model
returned something the validator rejected and was handed the error back.
`transport_retry` means the request never reached a model. Summing them would
report a flaky evening on a local shim as a flaky model, and the improvement
table would move for a reason that has nothing to do with the system.
"""
from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve import llm  # noqa: E402
from trialsieve.trace import Trajectory  # noqa: E402


class _Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ok_body(text: str = '{"ok": true}') -> _Reply:
    return _Reply(json.dumps({
        "choices": [{"message": {"content": text}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 11, "completion_tokens": 3},
    }).encode())


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x/v1/chat/completions", code, "boom",
                                  {}, io.BytesIO(b'{"error":"gateway"}'))


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda _s: None)


def test_a_502_is_retried_and_the_call_succeeds(monkeypatch):
    calls = []

    def fake(req, timeout=None):
        calls.append(1)
        if len(calls) < 3:
            raise _http_error(502)
        return _ok_body()

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    out, retries = llm._urlopen_json(llm.urllib.request.Request("http://x/v1/chat/completions"))
    assert out["model"] == "test-model"
    assert len(retries) == 2
    assert all("502" in r for r in retries)


def test_a_400_is_not_retried(monkeypatch):
    """Retrying a rejected request sends the same rejected request again."""
    calls = []

    def fake(req, timeout=None):
        calls.append(1)
        raise _http_error(400)

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    with pytest.raises(llm.TransportError):
        llm._urlopen_json(llm.urllib.request.Request("http://x/v1/chat/completions"))
    assert len(calls) == 1


def test_the_budget_is_bounded(monkeypatch):
    calls = []

    def fake(req, timeout=None):
        calls.append(1)
        raise _http_error(503)

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    with pytest.raises(llm.TransportError):
        llm._urlopen_json(llm.urllib.request.Request("http://x/v1/chat/completions"))
    assert len(calls) == llm.TRANSPORT_ATTEMPTS


def test_transport_retries_are_a_distinct_trajectory_event():
    traj = Trajectory("test", "distinct")
    traj.llm_response("{}", "openai", 10, 2, 0.5,
                      transport_retries=["HTTP 502: gateway", "HTTP 502: gateway"])
    traj.retry(1, "the validator rejected that")
    kinds = [e["event"] for e in traj.events]
    assert kinds.count("transport_retry") == 2
    assert kinds.count("retry") == 1


def test_a_clean_call_records_no_transport_retry():
    traj = Trajectory("test", "clean")
    traj.llm_response("{}", "openai", 10, 2, 0.5)
    assert not [e for e in traj.events if e["event"] == "transport_retry"]
