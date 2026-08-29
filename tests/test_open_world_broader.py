"""Closed-world absence is not available for a concept the vocabulary cannot express.

`absent_means: "false"` is a claim that the record is complete for this query, so
silence settles it. That claim needs the query to have a code for the concept.
When `codes` is empty the query is asking about something this site has no code
for, the record could never have stored it, and its silence says nothing.

The pairing was legal for one run and cost 358 wrong FAILS on one criterion and
246 on another. These tests pin the repair, and one of them reads the committed
predicates rather than a fixture, so the invariant is checked against what
actually ships.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialsieve.agents.compiler import open_world_broader_only  # noqa: E402
from trialsieve.evaluator import Evaluator  # noqa: E402
from trialsieve.ir import validate_query  # noqa: E402
from trialsieve.logic import U  # noqa: E402


def _q(codes, broader, absent="false", domain="condition"):
    return {"op": "exists", "query": {"domain": domain, "codes": list(codes),
                                      "broader_codes": list(broader),
                                      "within_days": None, "active_only": False,
                                      "absent_means": absent}}


def test_broader_only_is_forced_open_world():
    e = _q([], ["44054006"])
    changed = open_world_broader_only(e)
    assert len(changed) == 1
    assert changed[0]["before"] == "false" and changed[0]["after"] == "unknown"
    assert e["query"]["absent_means"] == "unknown"


def test_a_query_with_an_exact_code_is_left_alone():
    """The repair must not touch a query that can settle its own concept.

    A blanket open-world override is a different change with a different cost:
    it would abstain on every silent record in the corpus. `run_arms
    --absent-means-override unknown` exists to measure that, and it is a
    sensitivity arm rather than the engine's behaviour.
    """
    e = _q(["44054006"], [])
    assert open_world_broader_only(e) == []
    assert e["query"]["absent_means"] == "false"

    both = _q(["1501000119109"], ["44054006"])
    assert open_world_broader_only(both) == []
    assert both["query"]["absent_means"] == "false"


def test_an_already_open_world_query_is_not_reported_as_repaired():
    e = _q([], ["44054006"], absent="unknown")
    assert open_world_broader_only(e) == []


def test_the_walk_reaches_every_nesting_the_grammar_allows():
    """`not`, `and`/`or`, and a `count` under a `compare` each hold a query in a
    different place.

    This test used to assert that one query was repaired in the tree below, and
    the tree holds two: the `or` arm and the count on the `compare`'s left. The
    number it asserted was the number the walker produced rather than the number
    the tree contains, so it passed against a walker that never descended into
    `left` or `right`. `criteria_seed8.json` carried the shape it was missing.
    """
    tree = {"op": "not", "arg": {"op": "or", "args": [
        _q([], ["44054006"]),
        {"op": "compare", "cmp": ">=", "left": {
            "val": "count", "query": {"domain": "medication", "codes": [],
                                      "broader_codes": ["999"], "absent_means": "false"}},
         "right": {"val": "literal", "number": 1, "unit": ""}},
    ]}}
    changed = open_world_broader_only(tree)
    assert len(changed) == 2, ("the tree holds two broader-only closed-world "
                               "queries and the walk reported a different number")
    assert tree["arg"]["args"][0]["query"]["absent_means"] == "unknown"
    assert tree["arg"]["args"][1]["left"]["query"]["absent_means"] == "unknown", (
        "the count under the compare's left operand was not reached")


def test_the_repaired_query_still_validates():
    e = _q([], ["44054006"])
    open_world_broader_only(e)
    validate_query(e["query"])


def _closed_world_broader_only(node, found):
    """Find the forbidden pairing by reading the JSON, not by calling the engine.

    This audit used to run `open_world_broader_only` over a copy of each
    committed predicate and report what it repaired. That makes the audit a
    restatement of the function it is auditing: when the walker could not reach
    a `compare` operand, neither could the audit, and both agreed the shipped
    predicates were clean while `criteria_seed8.json` held two violations. So
    this walks the parsed JSON itself and knows nothing about the repair.
    """
    if isinstance(node, dict):
        if (not node.get("codes") and (node.get("broader_codes") or [])
                and node.get("absent_means") == "false"):
            found.append({"domain": node.get("domain"),
                          "broader_codes": list(node["broader_codes"])})
        for v in node.values():
            _closed_world_broader_only(v, found)
    elif isinstance(node, list):
        for v in node:
            _closed_world_broader_only(v, found)
    return found


def test_no_committed_predicate_pairs_an_empty_code_list_with_closed_world():
    """The invariant, over the predicates this submission actually ships."""
    offenders, scanned = [], 0
    for path in sorted((ROOT / "runs" / "tierA" / "compiled").glob("criteria_seed*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("criteria", data)
        for rec in items:
            expr = rec.get("expr")
            if not expr:
                continue
            scanned += 1
            for hit in _closed_world_broader_only(expr, []):
                offenders.append({"file": path.name, "criterion": rec["criterion_id"],
                                  **hit})
    assert scanned >= 3, (f"only {scanned} compiled predicate(s) were scanned, so a "
                          f"clean result here would mean nothing")
    assert offenders == [], (
        "a committed predicate reads silence as absence for a concept this "
        f"vocabulary has no code for: {offenders}")


def test_the_independent_audit_can_see_a_violation():
    """The positive control for the audit above, which otherwise passes just as
    well against a scan that looks at nothing."""
    planted = {"op": "compare", "cmp": ">", "left": {
        "val": "count", "query": {"domain": "condition", "codes": [],
                                  "broader_codes": ["44054006"],
                                  "absent_means": "false"}},
        "right": {"val": "literal", "number": 0, "unit": ""}}
    assert _closed_world_broader_only(planted, []), (
        "the audit cannot see a violation planted directly in a compare operand, "
        "which is the exact shape it failed to see in a shipped predicate")


def test_absence_of_the_parent_code_is_unknown_not_false():
    """The behaviour the repair buys, executed rather than argued.

    A chart with no diabetes coding at all must come back INDETERMINATE for a
    criterion whose only available code is the parent, because the site cannot
    record the distinction the criterion turns on.
    """
    from conftest import chart as make_chart
    empty = make_chart()
    e = _q([], ["44054006"])
    open_world_broader_only(e)
    out = Evaluator(empty).eval_expr(e)
    assert out.value is U, f"silence settled a concept it cannot settle: {out.reason}"


def test_the_parent_code_present_is_also_unknown():
    """Both branches abstain, which is the point.

    Present says the record is imprecise. Absent says the record is silent about
    something it could not have written down. Neither settles the criterion, and
    a criterion that can never answer INDETERMINATE is the defect this repair
    closes.
    """
    from conftest import chart as make_chart, cond
    out = Evaluator(make_chart(conditions=[cond("44054006")])).eval_expr(_q([], ["44054006"]))
    assert out.value is U, out.reason
