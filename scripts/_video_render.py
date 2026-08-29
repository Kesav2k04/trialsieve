"""Turn captured output into frames, and frames plus narration into a video.

Imported by `make_video.py`. Split out so the build script stays readable.

The design rule everything here follows: **a frame is a rendering of a file the
repository produced.** There is no template with a headline in it, no diagram
drawn to illustrate an idea, no screenshot cropped to the good part. Each shot is
either a command's real output or a generated markdown file, paged into screens
and typeset. That constraint costs some polish and buys the only thing that
matters here, which is that a viewer is looking at the artifact rather than at a
description of it.

Two smaller decisions worth stating.

**Paging, not scrolling.** A long file becomes consecutive full screens rather
than a smooth scroll. Smooth scrolling reads better and is unreadable at any speed
that fits a five minute video, and a viewer who pauses on a scrolling frame gets
half a line of text at the top and half at the bottom.

**Monospace throughout, including the markdown.** These are terminal artifacts and
a proportional font would be dressing them up as something they are not.
"""
from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

W, H = 1920, 1080
FPS = 30
COLS = 104
LINES_PER_PAGE = 30

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
  width:1920px; height:1080px; background:#0b0f14; color:#c9d4df;
  font-family:"Cascadia Mono","Consolas","DejaVu Sans Mono",monospace;
  font-size:26px; line-height:1.42; overflow:hidden;
}
.frame { padding:54px 64px 40px 64px; height:1080px; display:flex; flex-direction:column; }
.bar { display:flex; align-items:center; gap:14px; margin-bottom:26px;
       border-bottom:1px solid #1e2a36; padding-bottom:18px; }
.dot { width:14px; height:14px; border-radius:50%; }
.d1 { background:#ff5f57; } .d2 { background:#febc2e; } .d3 { background:#28c840; }
.title { color:#7f95a8; font-size:23px; letter-spacing:.4px; margin-left:10px; }
.src { margin-left:auto; color:#4c6076; font-size:20px; }
pre { white-space:pre; flex:1; }
.pg { position:absolute; right:64px; bottom:34px; color:#3c4c5c; font-size:19px; }
.k  { color:#7fd1b9; }
.n  { color:#e2b56b; }
.hi { color:#ffffff; font-weight:600; }
.dim{ color:#5b6b7b; }
.bad{ color:#ff8f7a; }
.ok { color:#8fd694; }
"""

#: Words worth colouring. Deliberately short: a frame with every other token
#: highlighted is a frame with nothing highlighted.
MARK = [
    ("INDETERMINATE", "hi"), ("UNMAPPABLE", "hi"), ("BROADER_ONLY", "hi"),
    ("REFUSED", "bad"), ("NOT FOR USE", "bad"), ("FAIL", "bad"),
    ("IDENTICAL", "ok"), ("PASS", "ok"), ("CassetteMiss", "bad"),
    ("MEETS", "n"), ("FAILS", "n"),
]


def _typeset(line: str) -> str:
    out = html.escape(line.rstrip())
    for word, cls in MARK:
        out = out.replace(html.escape(word), f'<span class="{cls}">{html.escape(word)}</span>')
    return out


def _wrap(text: str, cols: int = COLS) -> list[str]:
    """Hard-wrap at the column count, because a terminal does."""
    out: list[str] = []
    for raw in text.splitlines():
        if len(raw) <= cols:
            out.append(raw)
            continue
        while len(raw) > cols:
            cut = raw.rfind(" ", 0, cols)
            cut = cut if cut > cols * 0.6 else cols
            out.append(raw[:cut])
            raw = "  " + raw[cut:].lstrip()
        out.append(raw)
    return out


def pages(text: str) -> list[list[str]]:
    lines = _wrap(text)
    while lines and not lines[-1].strip():
        lines.pop()
    return [lines[i:i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[""]]


def page_html(title: str, source: str, body: list[str], n: int, total: int) -> str:
    rows = "\n".join(_typeset(x) for x in body)
    counter = f'<div class="pg">{n} of {total}</div>' if total > 1 else ""
    return (f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
            f"<div class='frame'><div class='bar'>"
            f"<span class='dot d1'></span><span class='dot d2'></span>"
            f"<span class='dot d3'></span>"
            f"<span class='title'>{html.escape(title)}</span>"
            f"<span class='src'>{html.escape(source)}</span></div>"
            f"<pre>{rows}</pre>{counter}</div>")


def render_frames(shots: list[dict], out_dir: Path) -> list[dict]:
    """One PNG per page. Returns the manifest the timing step consumes."""
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    manifest: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H},
                                device_scale_factor=1)
        for shot in shots:
            body = pages(shot["text"])
            for i, chunk in enumerate(body, 1):
                dest = out_dir / f"{shot['id']}_{i:02d}.png"
                page.set_content(page_html(shot["title"], shot["source"], chunk,
                                           i, len(body)))
                page.screenshot(path=str(dest))
                manifest.append({"shot": shot["id"], "section": shot["section"],
                                 "page": i, "of": len(body),
                                 "file": dest.name})
            print(f"  {shot['id']:20s} {len(body)} page(s)")
        browser.close()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n",
                                           encoding="utf-8", newline=chr(10))
    return manifest


def build(manifest: list[dict], timings: dict, frames_dir: Path, audio_dir: Path,
          dest: Path) -> None:
    """Cut the frames to the narration and mux.

    Each section's frames share that section's measured narration length. The
    audio is the fixed quantity and the pictures move to fit it, which is the
    whole reason narration is synthesised first.
    """
    secs = {s["n"]: s for s in timings["sections"]}
    concat, srt_parts, t = [], [], 0.0

    for n in sorted(secs):
        mine = [m for m in manifest if m["section"] == n]
        if not mine:
            mine = [manifest[-1]]
        span = secs[n]["seconds"] / len(mine)
        for m in mine:
            concat.append((frames_dir / m["file"], span))
        srt_parts.append((n, t, t + secs[n]["seconds"]))
        t += secs[n]["seconds"]

    listing = frames_dir / "concat.txt"
    lines = []
    for path, span in concat:
        lines.append(f"file '{path.as_posix()}'")
        lines.append(f"duration {span:.3f}")
    lines.append(f"file '{concat[-1][0].as_posix()}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8", newline=chr(10))

    audio_list = frames_dir / "audio.txt"
    audio_list.write_text(
        "\n".join(f"file '{(audio_dir / s['file']).as_posix()}'"
                  for s in sorted(timings["sections"], key=lambda x: x["n"])) + "\n",
        encoding="utf-8", newline=chr(10))

    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(listing),
         "-f", "concat", "-safe", "0", "-i", str(audio_list),
         "-vf", f"fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-shortest", str(dest)],
        check=True)
