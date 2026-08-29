"""Run each shot and keep what it printed.

Imported by `make_video.py`. Separate from the renderer because capture is the
step that can legitimately fail: a command may exit non-zero, a generated file may
not exist yet. Those are build failures rather than frames, and the distinction is
easier to keep when the two steps do not share a function.

The expected exit code is part of the spec. Two shots exist to show a refusal, so
a zero exit from those means the gate stopped working, and this reports it rather
than filming a broken gate looking fine.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def capture(spec: list[dict], shots_dir: Path) -> tuple[list[dict], list[str]]:
    shots_dir.mkdir(parents=True, exist_ok=True)
    out, problems = [], []

    for s in spec:
        text = ""
        if s["kind"] == "cmd":
            proc = subprocess.run(s["cmd"], cwd=ROOT, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            text = (proc.stdout or "") + (proc.stderr or "")
            want = s.get("expect_exit", 0)
            if proc.returncode != want:
                problems.append(
                    f"{s['id']}: exit {proc.returncode}, expected {want}. "
                    + (f"This shot exists to show a refusal, so a {proc.returncode} "
                       f"means the gate is not refusing." if want else
                       f"last line: {text.strip().splitlines()[-1][:120] if text.strip() else '(no output)'}"))
        else:
            src = ROOT / s["path"]
            if not src.exists():
                problems.append(f"{s['id']}: {s['path']} has not been generated yet")
                continue
            text = src.read_text(encoding="utf-8")

        lines = text.splitlines()
        if s.get("tail"):
            lines = lines[-s["tail"]:]
        elif s.get("lines"):
            a, b = s["lines"]
            lines = lines[a:b]
        text = "\n".join(lines)

        (shots_dir / f"{s['id']}.txt").write_text(text, encoding="utf-8",
                                                  newline=chr(10))
        out.append({**s, "text": text})
        print(f"  {s['id']:20s} {len(lines):4d} lines")

    junk = shots_dir / "_discard.md"
    if junk.exists():
        junk.unlink()
    return out, problems
