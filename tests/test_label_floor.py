"""The label noise floor has to be absent loudly.

The report used to load `agreement.json` behind `if path.exists()`, so on any
checkout where the second labeller had not run the whole section disappeared and
the document read as though there were nothing to say about label noise. It also
read two keys, `cohens_kappa` and `gwets_ac1`, that nothing writes, so the first
run that did find the file would have died on a KeyError. Neither could be caught
by running the report, because the file was missing in every environment where
anyone ran it.
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


def _report_module():
    spec = importlib.util.spec_from_file_location("report_mod", ROOT / "scripts" / "report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_loader_returns_none_when_the_second_labeller_has_not_run(monkeypatch, tmp_path):
    mod = _report_module()
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    assert mod.load_label_floor() is None


def test_report_says_not_measured_rather_than_dropping_the_section(monkeypatch, tmp_path):
    """The section header is printed either way. A reader who scrolls past a
    missing heading and a reader who scrolls past an empty one are not the same
    reader, and only the second one has been told anything."""
    src = (ROOT / "scripts" / "report.py").read_text(encoding="utf-8")
    assert '"## Label noise floor"' in src
    body = src[src.index("# label noise floor"):src.index("# provenance:")]
    assert "NOT MEASURED" in body
    assert "if floor is None:" in body
    # and the header is emitted before the branch, so it cannot be skipped
    assert body.index('"## Label noise floor"') < body.index("if floor is None:")


def test_keys_match_what_checker_b_actually_writes():
    """The crash that never happened because the file was never there."""
    mod = _report_module()
    path = ROOT / "evaluation" / "checker_b" / "agreement.json"
    if not path.exists():
        pytest.skip("no agreement.json in this checkout")
    floor = mod.load_label_floor()
    assert floor is not None
    for key in ("percent_agreement", "cohen_kappa", "gwet_ac1"):
        assert floor[key] is not None, f"{key} came back None, so a key name has drifted"


def test_contradictions_and_confidence_splits_are_separated(monkeypatch, tmp_path):
    """A MEETS against a FAILS is one labeller being wrong. A MEETS against an
    INDETERMINATE is the two of them drawing the confidence line differently.
    Summing them would inflate the bar every measured difference has to clear."""
    mod = _report_module()
    d = tmp_path / "evaluation" / "checker_b"
    d.mkdir(parents=True)
    (d / "agreement.json").write_text(json.dumps({
        "n": 100,
        "agreement": {"percent_agreement": 0.8, "cohen_kappa": 0.7, "gwet_ac1": 0.71},
        "a_marginals": {"MEETS": 50, "FAILS": 30, "INDETERMINATE": 20},
        "b_marginals": {"MEETS": 40, "FAILS": 30, "INDETERMINATE": 30},
        "disagreement_pattern": {"MEETS->FAILS": 6, "FAILS->MEETS": 2,
                                 "MEETS->INDETERMINATE": 9, "INDETERMINATE->FAILS": 3},
    }), encoding="utf-8", newline=NL)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    floor = mod.load_label_floor()
    assert floor["n_contradictions"] == 8
    assert floor["n_confidence_splits"] == 12
    assert floor["hard"] == pytest.approx(0.08)
    assert floor["soft"] == pytest.approx(0.12)
    assert floor["hard"] < 1 - floor["percent_agreement"], (
        "the bar for interpreting a difference must be the contradiction rate, "
        "not the whole disagreement rate")


def test_every_comparison_row_carries_a_floor_verdict():
    results = ROOT / "results" / "results.json"
    if not results.exists():
        pytest.skip("no scored run in this checkout")
    blob = json.loads(results.read_text(encoding="utf-8"))
    rows = [r for g in blob.get("groups", {}).values()
            for r in g.get("paired_bootstrap", [])]
    if not rows:
        pytest.skip("no paired comparisons in this run")
    for r in rows:
        assert r.get("vs_label_floor"), (
            f"{r.get('arms')} {r.get('metric')} was published with no statement of "
            f"whether the labels can resolve a difference that size")
