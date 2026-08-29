"""Model access, and the record/replay layer that makes the numbers checkable.

A judge should be able to reproduce every figure in the report without an API
key, without a network, and without spending anything. That is only honest if
replay is genuinely replaying recorded model output rather than reading a saved
answer sheet, so the cassette key is a hash of the full request. Change one
character of a prompt and the key changes, the cassette misses, and replay stops
with an error instead of quietly returning the old answer.

Three providers:
  * `openai`  - any OpenAI-compatible endpoint (OpenAI, Ollama, vLLM, OpenRouter).
  * `cli`     - a locally authenticated vendor CLI, for machines with no key.
  * `replay`  - cassettes only. Any miss is a hard error.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CASSETTE_VERSION = 1


class TransportError(RuntimeError):
    """The endpoint could not be reached, after the retry budget was spent.

    Separate from every model-level error on purpose. This one says nothing at
    all about the model's answer, so a run that ends here has not measured the
    model and must not be reported as if it had.
    """


class CassetteMiss(RuntimeError):
    """Replay was asked for a request that was never recorded.

    Deliberately fatal. A cassette layer that falls through to a live call, or to
    a default, would let a changed prompt keep reporting the old numbers.
    """


@dataclass
class Request:
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.0
    max_tokens: int = 4096
    seed: int | None = 7
    #: Free-form label for the trajectory log. Never part of the cassette key,
    #: so renaming a call site does not invalidate recorded output.
    tag: str = ""

    def key_payload(self) -> dict[str, Any]:
        return {
            "v": CASSETTE_VERSION,
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
        }

    def key(self) -> str:
        blob = json.dumps(self.key_payload(), sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class Response:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    from_cassette: bool = False
    provider: str = ""
    #: Transport failures survived on the way to this response. Deliberately a
    #: separate field from anything the trajectory calls a retry: a gateway
    #: returning 502 is not the model producing an unusable answer, and summing
    #: the two would make an unreliable network look like an unreliable model.
    transport_retries: list[str] = field(default_factory=list)


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    wall_s: float = 0.0
    cassette_hits: int = 0

    def add(self, r: Response) -> None:
        self.calls += 1
        self.prompt_tokens += r.prompt_tokens
        self.completion_tokens += r.completion_tokens
        self.wall_s += r.latency_s
        if r.from_cassette:
            self.cassette_hits += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "wall_s": round(self.wall_s, 2),
            "cassette_hits": self.cassette_hits,
        }


# ---------------------------------------------------------------------------


#: Transport retry policy. Only these HTTP statuses are retried, and only these.
#: 502 and 503 are a gateway or a local CLI shim failing to produce a reply at
#: all; 429 and 529 are rate limiting. A 4xx that is not 429 is the request being
#: wrong, and retrying it sends the same wrong request again.
RETRY_STATUS = {429, 500, 502, 503, 504, 529}
TRANSPORT_ATTEMPTS = 4
TRANSPORT_BACKOFF = (2.0, 6.0, 15.0)


def _urlopen_json(request: urllib.request.Request) -> tuple[dict, list[str]]:
    """POST and parse, surviving a transient gateway failure.

    Why this exists. A long compile is a few hundred sequential calls through a
    local shim onto a vendor CLI, and a single 502 partway through used to abort
    one criterion and leave an ERROR row in a scored table. An ERROR row is worse
    than a slow run: it is indistinguishable, in the summary, from the model
    failing to answer, so a flaky evening would read as a worse system.

    The failure text is kept and returned rather than swallowed, because a run
    that needed nine retries is a run whose timings mean something different from
    one that needed none, and the report says which.
    """
    retries: list[str] = []
    for attempt in range(TRANSPORT_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=300) as fh:
                return json.load(fh), retries
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:400]
            except Exception:
                pass
            note = f"HTTP {exc.code}: {detail or exc.reason}"
            if exc.code not in RETRY_STATUS or attempt == TRANSPORT_ATTEMPTS - 1:
                raise TransportError(f"{note} after {len(retries)} retries") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            note = f"{type(exc).__name__}: {exc}"
            if attempt == TRANSPORT_ATTEMPTS - 1:
                raise TransportError(f"{note} after {len(retries)} retries") from exc
        retries.append(note)
        time.sleep(TRANSPORT_BACKOFF[min(attempt, len(TRANSPORT_BACKOFF) - 1)])
    raise TransportError("unreachable")


def _approx_tokens(s: str) -> int:
    """A stable, dependency-free token estimate.

    Deliberately not a real tokenizer: the cost table needs a number that is the
    same on every machine and in every replay, and a tokenizer download would be
    one more thing to fail on a judge's laptop. Reported as an estimate, and the
    provider's own count is preferred whenever it returns one.
    """
    return max(1, (len(s) + 3) // 4)


class Client:
    def __init__(self, provider: str = "replay", model: str = "gemini-2.5-flash",
                 cassette_dir: str | Path = "cassettes", mode: str = "replay",
                 base_url: str | None = None, api_key_env: str = "OPENAI_API_KEY",
                 cli_cmd: str | None = None, trajectory_dir: str | Path | None = None) -> None:
        self.provider = provider
        self.model = model
        self.cassette_dir = Path(cassette_dir)
        #: replay = cassettes only; record = live call, then persist; live = no cassettes.
        self.mode = mode
        self.base_url = base_url or os.environ.get("TRIALSIEVE_BASE_URL",
                                                   "https://api.openai.com/v1")
        self.api_key_env = api_key_env
        self.cli_cmd = cli_cmd
        self.usage = Usage()
        self.trajectory_dir = Path(trajectory_dir) if trajectory_dir else None
        self._steps: list[dict[str, Any]] = []
        if self.mode in ("record", "replay"):
            self.cassette_dir.mkdir(parents=True, exist_ok=True)

    # -- cassettes ----------------------------------------------------------
    def _path(self, key: str) -> Path:
        return self.cassette_dir / f"{key[:16]}.json"

    def _read_cassette(self, req: Request) -> Response | None:
        p = self._path(req.key())
        if not p.exists():
            return None
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("key") != req.key():
            raise CassetteMiss(
                f"cassette {p.name} stores key {rec.get('key','?')[:16]} but the request hashes "
                f"to {req.key()[:16]}. The file was edited or the prompt changed."
            )
        r = rec["response"]
        return Response(r["text"], r.get("model", self.model), r.get("prompt_tokens", 0),
                        r.get("completion_tokens", 0), r.get("latency_s", 0.0),
                        from_cassette=True, provider=rec.get("provider", ""))

    def _write_cassette(self, req: Request, resp: Response) -> None:
        rec = {
            "key": req.key(),
            "cassette_version": CASSETTE_VERSION,
            "provider": resp.provider,
            "request": req.key_payload(),
            "response": {
                "text": resp.text,
                "model": resp.model,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "latency_s": round(resp.latency_s, 3),
            },
        }
        self._path(req.key()).write_text(
            json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    # -- providers ----------------------------------------------------------
    def _call_openai(self, req: Request) -> Response:
        key = os.environ.get(self.api_key_env, "")
        body = {"model": req.model, "messages": req.messages,
                "temperature": req.temperature, "max_tokens": req.max_tokens}
        if req.seed is not None:
            body["seed"] = req.seed
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        r = urllib.request.Request(f"{self.base_url.rstrip('/')}/chat/completions",
                                   data=data, headers=headers)
        t0 = time.time()
        out, retries = _urlopen_json(r)
        dt = time.time() - t0
        text = out["choices"][0]["message"]["content"] or ""
        u = out.get("usage") or {}
        return Response(text, out.get("model", req.model),
                        u.get("prompt_tokens") or _approx_tokens(json.dumps(req.messages)),
                        u.get("completion_tokens") or _approx_tokens(text),
                        dt, provider="openai", transport_retries=retries)

    def _call_cli(self, req: Request) -> Response:
        prompt = "\n\n".join(
            (m["content"] if m["role"] == "user" else f"[{m['role']}]\n{m['content']}")
            for m in req.messages)
        cmd = self.cli_cmd or "gemini"
        t0 = time.time()
        proc = subprocess.run([cmd, "-m", req.model, "-p", prompt],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=600, stdin=subprocess.DEVNULL)
        dt = time.time() - t0
        if proc.returncode != 0:
            raise RuntimeError(f"{cmd} exited {proc.returncode}: {(proc.stderr or '')[-800:]}")
        return Response(_strip_cli_noise(proc.stdout), req.model,
                        _approx_tokens(prompt), _approx_tokens(proc.stdout), dt,
                        provider=f"cli:{cmd}")

    # -- entry point --------------------------------------------------------
    def complete(self, req: Request) -> Response:
        if req.model == "":
            req.model = self.model

        if self.mode in ("replay", "record"):
            hit = self._read_cassette(req)
            if hit is not None:
                self.usage.add(hit)
                self._log(req, hit)
                return hit
            if self.mode == "replay":
                raise CassetteMiss(
                    f"no cassette for {req.tag or 'request'} (key {req.key()[:16]}). "
                    f"Replay never falls through to a live call. Run in record mode to create it."
                )

        resp = self._call_cli(req) if self.provider == "cli" else self._call_openai(req)
        if self.mode == "record":
            self._write_cassette(req, resp)
        self.usage.add(resp)
        self._log(req, resp)
        return resp

    # -- trajectory ---------------------------------------------------------
    def _log(self, req: Request, resp: Response) -> None:
        self._steps.append({
            "tag": req.tag,
            "model": req.model,
            "cassette_key": req.key(),
            "from_cassette": resp.from_cassette,
            "messages": req.messages,
            "response": resp.text,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "latency_s": round(resp.latency_s, 3),
        })

    def dump_trajectory(self, name: str) -> Path | None:
        if not self.trajectory_dir:
            return None
        self.trajectory_dir.mkdir(parents=True, exist_ok=True)
        p = self.trajectory_dir / f"{name}.json"
        p.write_text(json.dumps({"agent": name, "steps": self._steps},
                                indent=1, ensure_ascii=False), encoding="utf-8")
        return p


def _strip_cli_noise(s: str) -> str:
    """Drop the banner some CLIs print before the answer."""
    lines = s.splitlines()
    for i, ln in enumerate(lines):
        t = ln.strip()
        if t.startswith("{") or t.startswith("[") or t.startswith("```"):
            return "\n".join(lines[i:]).strip()
    return s.strip()


def verify_cassettes(cassette_dir: str | Path) -> dict[str, Any]:
    """Re-hash every stored request and check it matches the filename and key.

    This is the check that separates record/replay from a saved answer table. If
    someone hand-edited a response to improve a result, the stored request still
    hashes to the stored key and the file still passes -- so this also reports
    the response digest, which the report pins.
    """
    d = Path(cassette_dir)
    files = sorted(d.glob("*.json"))
    bad, ok = [], 0
    digest = hashlib.sha256()
    for p in files:
        rec = json.loads(p.read_text(encoding="utf-8"))
        blob = json.dumps(rec["request"], sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"))
        recomputed = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        if recomputed != rec.get("key"):
            bad.append({"file": p.name, "stored": rec.get("key", "")[:16],
                        "recomputed": recomputed[:16]})
        elif not p.name.startswith(recomputed[:16]):
            bad.append({"file": p.name, "reason": "filename does not match key"})
        else:
            ok += 1
        digest.update(recomputed.encode())
        digest.update(hashlib.sha256(rec["response"]["text"].encode("utf-8")).hexdigest().encode())
    return {"files": len(files), "ok": ok, "mismatched": bad,
            "corpus_digest": digest.hexdigest()}
