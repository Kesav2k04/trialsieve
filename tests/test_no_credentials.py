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
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).name

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

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".yml", ".yaml", ".txt", ".cfg",
                 ".toml", ".srt", ".sh", ".ps1", ".env", ""}


def _tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return [ROOT / n for n in out.split("\0") if n]


def test_no_tracked_file_contains_a_credential():
    compiled = [(re.compile(p), why) for p, why in PATTERNS]
    findings = []
    for p in _tracked():
        if p.name == SELF or p.suffix.lower() not in TEXT_SUFFIXES or not p.exists():
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
