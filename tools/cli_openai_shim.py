"""A local OpenAI-compatible endpoint backed by a locally authenticated vendor CLI.

Why this exists. Recording cassettes by shelling out to a CLI, while the judge
replays against `POST /v1/chat/completions`, would mean the HTTP path is the one
piece of the system that never runs during development and first executes on
someone else's machine. This shim removes that asymmetry: everything, including
recording, goes through the same client code and the same request shape. The
machine with no API key gets its inference from the CLI behind this server; the
machine with a key points at the real endpoint. Neither knows the difference.

    python tools/cli_openai_shim.py --port 8080 --cli gemini

Not a production server. Loopback only, no auth, no TLS, and it is never part of
the reproduction path: judges replay cassettes or bring their own endpoint.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Semaphore(4)
CLI = "gemini"
TIMEOUT = 600
_stats = {"calls": 0, "errors": 0, "wall": 0.0}


def resolve_cli(name: str) -> str:
    """Find the real executable.

    On Windows an npm-installed CLI is a `.cmd` wrapper, and CreateProcess will
    not run a bare name that has no extension, so `shutil.which` is asked for the
    wrapper explicitly before falling back to the plain name.
    """
    import os
    import shutil

    if os.path.isabs(name) and os.path.exists(name):
        return name
    for cand in ((name + ".cmd", name + ".exe", name + ".bat", name)
                 if os.name == "nt" else (name,)):
        found = shutil.which(cand)
        if found:
            return found
    raise SystemExit(f"cannot find {name!r} on PATH")


def render(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        role, content = m.get("role", "user"), m.get("content", "")
        parts.append(content if role == "user" else f"[{role}]\n{content}")
    return "\n\n".join(parts)


def strip_noise(s: str) -> str:
    """Drop the CLI banner that precedes the answer."""
    lines = s.splitlines()
    for i, ln in enumerate(lines):
        t = ln.strip()
        if t.startswith(("{", "[", "```")):
            return "\n".join(lines[i:]).strip()
    return s.strip()


def approx_tokens(s: str) -> int:
    return max(1, (len(s) + 3) // 4)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # keep the console readable
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") in ("/v1/models", "/models"):
            return self._json(200, {"object": "list", "data": [{"id": CLI, "object": "model"}]})
        if self.path.rstrip("/") == "/stats":
            return self._json(200, _stats)
        self._json(404, {"error": "not found"})

    def do_POST(self):
        try:
            return self._do_post()
        except Exception:
            import traceback
            traceback.print_exc()
            sys.stderr.flush()
            try:
                self._json(500, {"error": {"message": "shim internal error"}})
            except Exception:
                pass

    def _do_post(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self._json(404, {"error": {"message": f"no route {self.path}"}})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as exc:
            return self._json(400, {"error": {"message": f"bad request: {exc}"}})

        model = req.get("model") or "gemini-2.5-flash"
        prompt = render(req.get("messages") or [])
        t0 = time.time()
        with LOCK:
            try:
                proc = subprocess.run(
                    [CLI, "-m", model, "-p", prompt],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=TIMEOUT, stdin=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                _stats["errors"] += 1
                return self._json(504, {"error": {"message": f"{CLI} timed out after {TIMEOUT}s"}})
        dt = time.time() - t0
        _stats["calls"] += 1
        _stats["wall"] += dt

        if proc.returncode != 0:
            _stats["errors"] += 1
            return self._json(502, {"error": {
                "message": f"{CLI} exited {proc.returncode}",
                "detail": (proc.stderr or "")[-2000:]}})

        text = strip_noise(proc.stdout)
        self._json(200, {
            "id": f"chatcmpl-shim-{_stats['calls']}",
            "object": "chat.completion",
            "created": int(t0),
            "model": model,
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": approx_tokens(prompt),
                      "completion_tokens": approx_tokens(text),
                      "total_tokens": approx_tokens(prompt) + approx_tokens(text)},
        })


def main() -> int:
    global CLI
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--cli", default="gemini")
    ap.add_argument("--concurrency", type=int, default=4)
    a = ap.parse_args()
    CLI = resolve_cli(a.cli)
    globals()["LOCK"] = threading.Semaphore(a.concurrency)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.daemon_threads = True
    print(f"shim on http://127.0.0.1:{a.port}/v1 backed by {CLI}, concurrency {a.concurrency}",
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
