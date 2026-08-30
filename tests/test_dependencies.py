"""The reproduction path imports nothing that is not in the standard library.

That claim appears in four files, and it is the kind of claim that is true when
written and false a week later, because adding an import is easy and re-reading
the README is not. So it is a test.

The exception is stated rather than hidden: the video build uses a speech
synthesiser and a browser to render frames, and neither is on the reproduction
path. `python run.py reproduce` never imports either. The allow-list below is the
whole exception, and any module added to it has to be added here deliberately.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Modules that are part of this project, resolved by path rather than installed.
LOCAL = {"trialsieve", "criteria_set", "plainview", "score", "dev_criteria",
         "vocab_probe", "contamination", "checker_b", "segmentation",
         "_verify_blind", "_md_tables", "_shipped"}

#: Third-party imports that are allowed, and only in these files.
#:
#: This used to carry `edge_tts` and `playwright`, for a video build that
#: synthesised a voice and screenshotted pages. That build is a Node project
#: now, and it is not part of this submission, so both went away with it and
#: the only third-party import left in the whole tree is the test runner.
ALLOWED = {
    "pytest": {"tests/"},
}

SCANNED = ("src", "scripts", "evaluation", "tools", "run.py")


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name.split(".")[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0], node.lineno


def _files():
    for entry in SCANNED:
        p = ROOT / entry
        yield from ([p] if p.is_file() else sorted(p.rglob("*.py")))


def test_nothing_outside_the_video_build_imports_a_third_party_module():
    stdlib = set(sys.stdlib_module_names)
    bad = []
    for f in _files():
        rel = f.relative_to(ROOT).as_posix()
        for name, line in _imports(f):
            if name in stdlib or name in LOCAL:
                continue
            where = ALLOWED.get(name, set())
            if any(rel == w or rel.startswith(w) for w in where):
                continue
            bad.append(f"{rel}:{line} imports {name}")
    assert not bad, ("third-party imports outside the allow-list, so the "
                     "'standard library only' claim in README.md, REPRODUCE.md, "
                     "SUBMISSION.md and run.py is no longer true: " + "; ".join(bad))


def test_the_allow_list_is_not_stale():
    """An entry nobody uses invites the next one. Each allowance must be live."""
    seen = set()
    for f in _files():
        for name, _ in _imports(f):
            seen.add(name)
    dead = [k for k in ALLOWED if k != "pytest" and k not in seen]
    assert not dead, f"allowed but never imported: {dead}"


def test_the_reproduction_path_reaches_no_allowed_exception():
    """A weaker check than it looks, and worth stating as such: it reads the
    commands `run.py reproduce` shells out to, rather than tracing imports at
    runtime. It catches the case that matters, which is somebody wiring the video
    build into the reproduce target."""
    src = (ROOT / "run.py").read_text(encoding="utf-8")
    body = src[src.index("def t_reproduce"):src.index("def t_diff")]
    assert "make_video" not in body, "the video build is on the reproduction path"
