"""The frame must show every line the pager puts on it.

`_video_render` pages a file into fixed-size screens instead of scrolling it, and
the docstring gives the reason: a viewer who pauses a scroll "gets half a line of
text at the top and half at the bottom". The pager then emitted 30 lines onto a
frame that fits 25. The overflow was hidden, the next page began at line 31, and
six lines in every thirty appeared nowhere in the video. Nothing failed, because
nothing was checking that a line placed on a frame is a line a viewer can read.

So this measures the real layout in the real browser rather than restating the
arithmetic, which is what got the constant wrong in the first place. Skipped
where the video toolchain is not installed: it is an optional extra and
`REPRODUCE.md` promises the engine gate runs on the standard library alone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _measure():
    """Lines of the text box that fall fully inside the frame, per the browser."""
    playwright = pytest.importorskip("playwright.sync_api")
    import _video_render as render

    body = [f"{i:02d}" for i in range(1, 41)]
    html = render.page_html("geometry", "geometry", body, 1, 2)
    tmp = ROOT / "runs" / ".video_geometry.html"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(html, encoding="utf-8", newline=chr(10))
    try:
        with playwright.sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as exc:  # a driver present but no browser installed
                pytest.skip(f"no chromium for the geometry check: {exc}")
            page = browser.new_page(viewport={"width": render.W, "height": render.H},
                                    device_scale_factor=1)
            page.goto(tmp.as_uri())
            got = page.evaluate("""() => {
              const pre = document.querySelector('pre');
              const counter = document.querySelector('.pg');
              const lh = parseFloat(getComputedStyle(pre).lineHeight);
              const top = pre.getBoundingClientRect().top;
              const floor = counter ? counter.getBoundingClientRect().top
                                    : window.innerHeight;
              return {lineHeight: lh, top: top,
                      fits: Math.floor((window.innerHeight - top) / lh),
                      clearsCounter: Math.floor((floor - top) / lh)};
            }""")
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)
    return got


def test_every_paged_line_is_on_screen():
    import _video_render as render

    m = _measure()
    assert render.LINES_PER_PAGE <= m["fits"], (
        f"a frame fits {m['fits']} lines and the pager puts "
        f"{render.LINES_PER_PAGE} on it, so {render.LINES_PER_PAGE - m['fits']} "
        f"of every {render.LINES_PER_PAGE} are rendered off the bottom and appear "
        f"in no frame at all. Lower LINES_PER_PAGE or raise the frame.")


def test_the_last_line_clears_the_page_counter():
    """The counter sits over the text box, so the bottom line must stop above it."""
    import _video_render as render

    m = _measure()
    assert render.LINES_PER_PAGE <= m["clearsCounter"], (
        f"line {render.LINES_PER_PAGE} runs under the '1 of N' counter, which "
        f"clears only {m['clearsCounter']} lines")
