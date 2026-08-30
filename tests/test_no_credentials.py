"""No credential may be in this repository. A ground rule, so it gets a gate.

Two decisions that make this scan worth running rather than reassuring.

**It matches values, not words.** A scanner that greps for "api_key" fires on
every line of prose that says the words, on the code that reads an environment
variable by name, and on its own rule descriptions. That scanner reports findings
forever and gets muted, which is worse than not having it. So the patterns here
are shaped like the secrets themselves: a provider prefix followed by enough
entropy to be a real key, a private key armour line, a long opaque blob assigned
to something.

**It excludes itself by path, not by cleverness.** This file necessarily contains
strings that look like the things it hunts. Trying to write patterns that somehow
do not match their own definitions is how a scanner ends up with a hole in it. The
file is skipped by name and that is stated here rather than discovered later.

**It also has to show the claim holds at run time, not just in the source
tree.** A clean grep of every tracked file says no key was left lying around.
It says nothing about whether a key ever reaches the request body, the
written cassette, or the trajectory log while the transport is actually
running, because it never runs the transport. The tests below do: they set a
fake key, drive `trialsieve.llm.Client` through a live-style call and through
a replay, and check the artifacts that would ship to a judge rather than the
source.
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve import llm  # noqa: E402

SELF = Path(__file__).name
SELF_REL = "tests/" + SELF

#: Each pattern is a secret's shape. The comment is what it is, because a regex
#: with no explanation is a regex nobody dares delete.
PATTERNS = [
    (r"sk-[A-Za-z0-9_\-]{24,}", "OpenAI-style secret key"),
    (r"sk-ant-[A-Za-z0-9_\-]{24,}", "Anthropic-style secret key"),
    (r"gh[pousr]_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"AIza[A-Za-z0-9_\-]{30,}", "Google API key"),
    (r"AKIA[A-Z0-9]{16}", "AWS access key id"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key armour"),
    (r"eyJ[A-Za-z0-9_\-]{12,}\.eyJ[A-Za-z0-9_\-]{12,}\.", "JSON web token"),
    (r"(?i)\b(?:api[_-]?key|secret|password|passwd|auth[_-]?token)\b"
     r"\s*[:=]\s*[\"'][^\"'\s${}]{16,}[\"']", "a long literal assigned to a secret name"),
]

def _tracked() -> list[Path]:
    from _shipped import shipped_paths
    return shipped_paths()


def test_no_tracked_file_contains_a_credential():
    """Every tracked file is opened, not a suffix allow-list of them.

    This used to skip anything whose extension was not on a short list of
    known text types, which meant a key sitting in `.png`, `.mp3` or `.gz`
    was invisible to the scan. The repository is small enough (low tens of
    megabytes tracked) that reading every file costs nothing worth trading
    coverage for, and a genuinely binary file still gets skipped: the UTF-8
    decode fails on its first invalid byte and the except below moves on.
    """
    compiled = [(re.compile(p), why) for p, why in PATTERNS]
    findings = []
    for p in _tracked():
        if p.name == SELF or not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        for rx, why in compiled:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                findings.append(f"{p.relative_to(ROOT).as_posix()}:{line} {why}")
    assert not findings, "credential-shaped strings in tracked files: " + "; ".join(findings)


def test_the_scan_would_catch_a_planted_key(tmp_path):
    """Without this, a pattern that stopped matching would pass silently forever."""
    compiled = [(re.compile(p), why) for p, why in PATTERNS]
    planted = [
        "OPENAI_API_KEY = " + repr("sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"),
        "token: " + repr("ghp_" + "0123456789abcdefghijklmnopqrstuvwx"),
        "-----BEGIN RSA PRIVATE KEY-----",
        "password = " + repr("hunter2hunter2hunter2hunter2"),
    ]
    for line in planted:
        assert any(rx.search(line) for rx, _ in compiled), f"not caught: {line[:40]}"


def test_the_scan_does_not_fire_on_reading_an_environment_variable():
    """The code that looks a key up by name is not a key, and a scanner that says
    otherwise is one nobody keeps enabled."""
    compiled = [(re.compile(p), why) for p, why in PATTERNS]
    innocent = [
        'key = os.environ.get(self.api_key_env, "")',
        'ap.add_argument("--api-key-env", default="OPENAI_API_KEY")',
        'headers["Authorization"] = f"Bearer {key}"',
        "No key, token or credential in the tree.",
        'password_field = "password"',
    ]
    for line in innocent:
        hit = [why for rx, why in compiled if rx.search(line)]
        assert not hit, f"false positive on {line!r}: {hit}"


def test_the_shim_never_writes_an_auth_file_inside_the_repository():
    """The one place a credential could plausibly land: the shim copies an auth
    file so a headless CLI can read it. It must land outside this tree."""
    src = (ROOT / "tools" / "cli_openai_shim.py").read_text(encoding="utf-8")
    assert "tempfile.mkdtemp" in src, "the shim no longer uses a temporary directory"
    assert "atexit" in src or "_rm" in src, "nothing removes the copied auth file"
    for bad in ("./auth", "data/auth", 'ROOT / "auth'):
        assert bad not in src, f"the shim writes an auth file into the tree: {bad}"


class _FakeHTTPResponse(io.BytesIO):
    """A context-manager stand-in for what `urllib.request.urlopen` returns.

    `llm._urlopen_json` does `with urllib.request.urlopen(request, ...) as fh:
    json.load(fh)`, so the fake needs `__enter__`/`__exit__`, not just a
    readable stream.
    """

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_completion_body(text: str = "ok") -> _FakeHTTPResponse:
    return _FakeHTTPResponse(json.dumps({
        "choices": [{"message": {"content": text}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 5, "completion_tokens": 2},
    }).encode())


def test_the_api_key_never_reaches_the_body_the_cassette_or_the_trajectory(monkeypatch, tmp_path):
    """Drive a live-style call end to end and check where the key actually goes.

    An `Authorization: Bearer <key>` header is the one place a key is
    supposed to reach: that is how the call authenticates at all, and this
    test confirms it lands there. What it must not do is leak into the JSON
    body sent over the wire, into the cassette written to disk, or into the
    trajectory log, because those three are what a judge downloads and
    reads. A regression that put the key in the request body, or a stray
    `str(req)` that dumped headers into a log line, would show up here; the
    source-text scan above would not catch it, because none of those
    artifacts are committed to this repository.
    """
    fake_key = "sk-test-DO-NOT-LOG-" + "a1b2c3d4e5f6g7h8i9j0"
    monkeypatch.setenv("TRIALSIEVE_FAKE_KEY", fake_key)

    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["request"] = request
        return _fake_completion_body()

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm.time, "sleep", lambda _s: None)

    cassette_dir = tmp_path / "cassettes"
    trajectory_dir = tmp_path / "trajectory"
    client = llm.Client(provider="openai", mode="record", cassette_dir=cassette_dir,
                       api_key_env="TRIALSIEVE_FAKE_KEY", trajectory_dir=trajectory_dir)
    req = llm.Request(model="test-model", messages=[{"role": "user", "content": "hello"}],
                      tag="credential-check")
    client.complete(req)
    client.dump_trajectory("agent")

    sent = captured.get("request")
    assert sent is not None, "the fake transport was never called"
    assert sent.get_header("Authorization") == f"Bearer {fake_key}", (
        "the key should reach the Authorization header; if it does not, "
        "auth is broken in a different way than this test is about")
    assert fake_key not in sent.data.decode("utf-8"), (
        "the key leaked into the JSON body sent over the wire")

    cassette_files = list(cassette_dir.glob("*.json"))
    assert cassette_files, "record mode did not write a cassette"
    for f in cassette_files:
        assert fake_key not in f.read_text(encoding="utf-8"), (
            f"the key leaked into the recorded cassette {f.name}")

    trajectory_files = list(trajectory_dir.glob("*.json"))
    assert trajectory_files, "no trajectory was written"
    for f in trajectory_files:
        assert fake_key not in f.read_text(encoding="utf-8"), (
            f"the key leaked into the trajectory log {f.name}")


def test_replay_never_touches_the_network_or_needs_a_key(monkeypatch, tmp_path):
    """The other half of the claim: reproducing a recorded run needs no key.

    Replay must answer from the cassette without ever calling
    `urllib.request.urlopen`. This is proven by making that call raise if it
    is reached at all, then unsetting the fake key so there is nothing to
    leak even if the code took the live path by mistake. A judge who never
    had a key gets the same numbers this way; if replay ever fell through to
    a live call, this test fails loudly instead of quietly needing a key.
    """
    def _refuse(*_a, **_k):
        raise AssertionError("replay must never open a network connection")

    monkeypatch.setattr(llm.urllib.request, "urlopen", _refuse)
    monkeypatch.delenv("TRIALSIEVE_FAKE_KEY", raising=False)

    cassette_dir = tmp_path / "cassettes"
    cassette_dir.mkdir()
    req = llm.Request(model="test-model", messages=[{"role": "user", "content": "hello"}],
                      tag="replay-check")
    record = {
        "key": req.key(),
        "cassette_version": llm.CASSETTE_VERSION,
        "provider": "openai",
        "request": req.key_payload(),
        "response": {"text": "recorded answer", "model": "test-model",
                     "prompt_tokens": 5, "completion_tokens": 2, "latency_s": 0.1},
    }
    (cassette_dir / f"{req.key()[:16]}.json").write_text(json.dumps(record),
                                                       encoding="utf-8", newline="\n")

    client = llm.Client(provider="openai", mode="replay", cassette_dir=cassette_dir,
                       api_key_env="TRIALSIEVE_FAKE_KEY_NEVER_SET")
    resp = client.complete(req)
    assert resp.text == "recorded answer"
    assert resp.from_cassette


def test_no_credential_is_reachable_anywhere_in_the_history():
    """A deleted secret is still a published secret.

    The scan above reads the working tree. That is the weaker claim: a key
    committed once and removed in the next commit is gone from `git grep` and
    still sitting in the object store, reachable by anyone who clones. For a
    repository that is about to be handed to strangers, history is the surface
    that matters.

    Every commit is scanned rather than every blob, which is the same coverage
    for a linear history and is fast enough to keep in the gate.
    """
    import subprocess

    from _shipped import has_git
    if not has_git():
        pytest.skip("no object database here, so there is no history to scan. "
                    "An unpacked source archive carries the tree without it.")

    revs = subprocess.run(["git", "rev-list", "--all"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.split()
    assert revs, "no commits found; the scan would pass by having nothing to read"

    patterns = "|".join([
        r"sk-[A-Za-z0-9]{16,}",
        r"ghp_[A-Za-z0-9]{20,}",
        r"github_pat_[A-Za-z0-9_]{20,}",
        r"AIza[A-Za-z0-9_-]{30,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    ])
    # `:(exclude)` on this file, for the same reason the tree scan skips SELF.
    # The positive control a few tests up plants `-----BEGIN RSA PRIVATE KEY-----`
    # on purpose, and it is in every commit since it was written, so without this
    # the scan reports 35 hits and every one of them is its own fixture. A scanner
    # that flags its own test data fails on the day it is added and gets deleted.
    p = subprocess.run(["git", "grep", "-I", "-n", "-E", patterns, *revs, "--",
                        f":(exclude){SELF_REL}"],
                       cwd=ROOT, capture_output=True, text=True)
    # git grep exits 1 when it finds nothing, which is the outcome we want.
    hits = [line for line in p.stdout.splitlines() if line.strip()]
    assert not hits, (
        f"{len(hits)} credential-shaped string(s) in the history. The first: "
        f"{hits[0][:160]}")
