"""What goes on screen, and which narration section it belongs to.

Imported by `make_video.py`. Every entry is either a command whose real output is
captured or a file the repository generated. There is no third kind, and adding
one would be the moment this stops being a recording of the project and starts
being a presentation about it.

`section` binds a shot to a narration section, and the section's measured audio
length is divided among its shots. That is the direction the dependency has to
run: the voice is fixed and the pictures move to fit it.

`expect_exit` is not decoration. Two of these shots are supposed to fail, because
the refusal is the feature. A build where the sign-off gate exits 0 is a build
where the gate is broken, and the capture step fails rather than filming it.
"""
from __future__ import annotations

import sys

SPEC = [
    {"id": "01-scale", "section": 1, "kind": "cmd",
     "title": "what is actually in here", "source": "scripts/describe_corpus.py",
     "cmd": [sys.executable, "scripts/describe_corpus.py"]},

    {"id": "02-counterexample", "section": 2, "kind": "file",
     "title": "one criterion, one patient, two arms",
     "source": "docs/COUNTEREXAMPLE.md", "path": "docs/COUNTEREXAMPLE.md",
     "lines": (0, 62)},

    {"id": "03-agents", "section": 3, "kind": "file",
     "title": "where the model calls are, and where they stop",
     "source": "docs/AGENT_DESIGN.md", "path": "docs/AGENT_DESIGN.md",
     "lines": (12, 30)},

    {"id": "04-trajectory", "section": 3, "kind": "cmd",
     "title": "the trajectory that went wrong, unedited",
     "source": "runs/tierA/trajectories/", "tail": 60,
     "cmd": [sys.executable, "scripts/trajectories.py", "--run", "runs/tierA",
             "--show-worst"]},

    {"id": "05-refusal", "section": 3, "kind": "cmd",
     "title": "the sign-off gate, refusing",
     "source": "scripts/worklist.py", "expect_exit": 3,
     "cmd": [sys.executable, "scripts/worklist.py", "--run", "runs/tierA",
             "--out", "docs/video/shots/_discard.md"]},

    {"id": "06-results", "section": 4, "kind": "file",
     "title": "coverage and error, always as a pair",
     "source": "results/RESULTS.md", "path": "results/RESULTS.md", "lines": (0, 46)},

    {"id": "07-probe", "section": 4, "kind": "cmd",
     "title": "before and after, on probes neither split contains",
     "source": "scripts/compare_probes.py",
     # Without an explicit --json this writes results/probe_comparison.json, the
     # same path the weak-model comparison writes, so capturing this shot
     # silently replaced a committed artifact with a different pair of runs.
     "cmd": [sys.executable, "scripts/compare_probes.py",
             "runs/probe-before/probe.json", "runs/probe-after/probe.json",
             "--json", "results/probe_comparison_before_after.json"]},

    {"id": "08-reproduce", "section": 5, "kind": "cmd",
     "title": "one command, offline, no key",
     "source": "python run.py reproduce", "tail": 42,
     "cmd": [sys.executable, "run.py", "reproduce"]},

    {"id": "09-falsifiable", "section": 5, "kind": "cmd",
     "title": "replay, proved not to be a saved answer file",
     "source": "scripts/verify.py prove-replay",
     "cmd": [sys.executable, "scripts/verify.py", "prove-replay", "--run", "runs/tierA"]},

    {"id": "10-hottake", "section": 6, "kind": "file",
     "title": "the whole bet, in one table",
     "source": "docs/AGENT_DESIGN.md", "path": "docs/AGENT_DESIGN.md",
     "lines": (143, 165)},
]
