"""The closed-world sensitivity section must fail loudly, not quietly.

Two of this project's sections have already shipped as silent omissions: the
blindness check scanned a gitignored directory and printed PASS, and the label
noise floor sat behind `if exists()` and vanished from every report ever
produced. This section reports the single largest source of error in the scored
run, so the same guard is asserted rather than assumed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

NL = chr(10)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))


def _src() -> str:
    return (ROOT / "scripts" / "report.py").read_text(encoding="utf-8")


def test_section_prints_not_measured_when_the_arm_is_absent():
    src = _src()
    body = src[src.index("## Sensitivity: what the closed-world assertions cost"):
               src.index("# provenance:")]
    assert "NOT MEASURED" in body
    assert "run_arms.py" in body, "the empty case has to name the command that fills it"
    # the heading is emitted before the branch, so it cannot be skipped
    assert body.index("NOT MEASURED") > 0


def test_no_hand_typed_figures_survive_in_the_static_blurb():
    """The blurb used to quote 469, 111, 182 and 18 as prose. Every one of them
    now comes out of the scored groups, so a run that moves them cannot leave a
    paragraph behind asserting the old ones."""
    src = _src()
    blurb = src[src.index("GROUP_BLURB = {"):src.index("def load_label_floor")]
    for stale in ("469", "111", "182", "358", "424", "5.5"):
        assert stale not in blurb, (
            f"{stale} is typed into the static blurb; it will go stale silently")


def test_worst_offender_is_named_and_counted_from_the_cells():
    """An aggregate claim a reader cannot check, against one they can."""
    spec = importlib.util.spec_from_file_location("report_mod", ROOT / "scripts" / "report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    run = ROOT / "runs" / "tierA"
    if not (run / "compiled" / "criteria_seed7.json").exists():
        pytest.skip("no compiled run in this checkout")
    groups = mod.load_cells(run)
    got = mod.worst_closed_world_criterion(run, groups)
    if got is None:
        pytest.skip("no closed-world assertion in this run, which is the good case")
    cid, right, wrong, code, text = got
    assert wrong > 0
    assert right >= 0
    assert code and code != "(no code)"
    assert text, "the criterion text is quoted in the report and must be present"


def test_reported_sensitivity_matches_the_scored_groups():
    """The section's arithmetic, recomputed from results.json."""
    path = ROOT / "results" / "results.json"
    if not path.exists():
        pytest.skip("no scored run in this checkout")
    blob = json.loads(path.read_text(encoding="utf-8"))
    groups = blob.get("groups", {})
    if "ow" not in groups or "k0_seed7" not in groups:
        pytest.skip("the open-world arm has not been run")
    base = groups["k0_seed7"]["cell_scores"]["TS"]
    ow = groups["ow"]["cell_scores"]["TS"]
    assert ow["n_silent"] < base["n_silent"], (
        "forcing every absence to unknown must not increase silent errors; if it "
        "did, absence is not what the errors are made of")
    assert ow["coverage"] < base["coverage"], (
        "and it must cost coverage, or the closed-world assertions were doing "
        "nothing and the trade-off being reported is not real")
    assert ow["n_false_meets"] == base["n_false_meets"], (
        "an absence can only ever turn a definite verdict into an abstention, so "
        "false MEETS cannot move; if it did, the override is changing something "
        "other than what it claims to")
