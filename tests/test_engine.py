"""The engine gate.

A defect in the shared execution engine would cancel between the compared arms
and score as agreement, which would leave the headline metric blind to exactly
the failure modes this project claims to fix. So the engine is tested on its own
semantics, and the protocol makes this suite a precondition for any scored run.

Every test here is a property a clinical reviewer would recognise, not an
implementation detail.
"""
from __future__ import annotations

import pytest

from conftest import chart, cond, med, obs, proc  # noqa: F401
from trialsieve.evaluator import Evaluator, evaluate_criterion, screen
from trialsieve.ir import IRError, is_demographic_only, validate_criterion, validate_expr
from trialsieve.logic import F, T, U, k_and, k_at_least, k_not, k_or
from trialsieve.units import convert

HBA1C, CREAT, EGFR, BMI, UACR, LDL = "4548-4", "38483-4", "33914-3", "39156-5", "14959-1", "18262-6"


def ev(c, expr):
    return Evaluator(c).eval_expr(expr)


# --------------------------------------------------------------------------
# 1. Kleene truth tables
# --------------------------------------------------------------------------

def test_and_false_dominates_unknown():
    """One proven failure settles a conjunction however much else is missing."""
    assert k_and([F, U]) is F
    assert k_and([U, F, U]) is F


def test_and_unknown_survives_true():
    assert k_and([T, U]) is U
    assert k_and([T, T]) is T


def test_or_true_dominates_unknown():
    assert k_or([T, U]) is T
    assert k_or([U, F]) is U
    assert k_or([F, F]) is F


def test_not_preserves_unknown():
    assert k_not(U) is U and k_not(T) is F and k_not(F) is T


def test_at_least_counts_unknown_optimistically_and_pessimistically():
    assert k_at_least(1, [T, U, F]) is T          # already reached
    assert k_at_least(2, [T, U, F]) is U          # reachable only if the unknown is true
    assert k_at_least(3, [T, U, F]) is F          # unreachable even then


# --------------------------------------------------------------------------
# 2. Date windows, both boundaries
# --------------------------------------------------------------------------

def test_observation_inside_window_is_used():
    c = chart(observations=[obs(HBA1C, 7.5, "%", days_ago=180)])
    r = ev(c, {"op": "compare", "cmp": ">", "left":
              {"val": "observation", "codes": [HBA1C], "unit": "%", "within_days": 180},
              "right": {"val": "literal", "number": 7.0, "unit": "%"}})
    assert r.value is T


def test_observation_one_day_outside_window_is_unknown_not_false():
    """Stale is not the same as absent, and neither is the same as out of range."""
    c = chart(observations=[obs(HBA1C, 7.5, "%", days_ago=181)])
    r = ev(c, {"op": "compare", "cmp": ">", "left":
              {"val": "observation", "codes": [HBA1C], "unit": "%", "within_days": 180},
              "right": {"val": "literal", "number": 7.0, "unit": "%"}})
    assert r.value is U
    assert "outside the 180-day window" in r.reason


def test_condition_exactly_on_window_edge_counts():
    c = chart(conditions=[cond("22298006", days_ago=183)])
    r = ev(c, {"op": "exists", "query": {"domain": "condition", "codes": ["22298006"],
                                         "within_days": 183, "absent_means": "unknown"}})
    assert r.value is T


def test_condition_just_outside_window_does_not_count():
    c = chart(conditions=[cond("22298006", days_ago=184)])
    r = ev(c, {"op": "exists", "query": {"domain": "condition", "codes": ["22298006"],
                                         "within_days": 183, "absent_means": "false"}})
    assert r.value is F


def test_older_diagnosis_outside_window_is_not_a_recent_one():
    """A myocardial infarction seven months ago does not satisfy 'within 6 months'."""
    c = chart(conditions=[cond("22298006", days_ago=213)])
    r = ev(c, {"op": "exists", "query": {"domain": "condition", "codes": ["22298006"],
                                         "within_days": 183, "absent_means": "false"}})
    assert r.value is F


# --------------------------------------------------------------------------
# 3. Units
# --------------------------------------------------------------------------

def test_uacr_mg_per_g_converts_to_mg_per_mmol():
    c = convert(265.2, "mg/g", "mg/mmol", UACR)
    assert c.ok and 29.5 < c.value < 30.5


def test_uacr_conversion_is_reversible():
    a = convert(30.0, "mg/mmol", "mg/g", UACR)
    b = convert(a.value, "mg/g", "mg/mmol", UACR)
    assert abs(b.value - 30.0) < 1e-9


def test_uacr_without_conversion_would_wrongly_exclude():
    """The stored number alone is about 8.8x the threshold number."""
    c = chart(observations=[obs(UACR, 100.0, "mg/g")])
    r = ev(c, {"op": "compare", "cmp": "<", "left":
              {"val": "observation", "codes": [UACR], "unit": "mg/mmol", "within_days": None},
              "right": {"val": "literal", "number": 30, "unit": "mg/mmol"}})
    assert r.value is T, "100 mg/g is 11.3 mg/mmol, comfortably under 30"


def test_creatinine_mass_to_molar():
    c = convert(1.0, "mg/dL", "mmol/L", CREAT)
    assert c.ok and 0.088 < c.value < 0.089


def test_cholesterol_uses_its_own_factor_not_glucose():
    chol = convert(100.0, "mg/dL", "mmol/L", LDL).value
    gluc = convert(100.0, "mg/dL", "mmol/L", "2339-0").value
    assert abs(chol - 2.586) < 0.01 and abs(gluc - 5.55) < 0.01
    assert chol != gluc


def test_egfr_bare_ml_per_min_accepted_because_the_loinc_code_pins_it():
    """33914-3 is defined as the 1.73 m2 normalised rate, so the bare unit is a label."""
    c = convert(72.0, "mL/min", "mL/min/1.73m2", EGFR)
    assert c.ok and c.value == 72.0 and c.reconciled_by_code


def test_unknown_conversion_refuses_rather_than_comparing_raw_numbers():
    c = convert(5.0, "mg/dL", "kg/m2", None)
    assert not c.ok and c.value is None


def test_refused_conversion_becomes_unknown_not_a_verdict():
    c = chart(observations=[obs(HBA1C, 7.5, "mmol/mol")])
    r = ev(c, {"op": "compare", "cmp": ">", "left":
              {"val": "observation", "codes": [HBA1C], "unit": "%", "within_days": None},
              "right": {"val": "literal", "number": 7.0, "unit": "%"}})
    assert r.value is U
    assert "mmol/mol" in r.reason


# --------------------------------------------------------------------------
# 4. Absence
# --------------------------------------------------------------------------

def test_missing_observation_is_unknown_never_false():
    c = chart()
    r = ev(c, {"op": "compare", "cmp": ">", "left":
              {"val": "observation", "codes": [HBA1C], "unit": "%", "within_days": None},
              "right": {"val": "literal", "number": 7.0, "unit": "%"}})
    assert r.value is U


def test_open_world_absence_is_unknown():
    r = ev(chart(), {"op": "exists", "query": {"domain": "medication", "codes": ["999"],
                                               "absent_means": "unknown"}})
    assert r.value is U


def test_closed_world_absence_is_false():
    r = ev(chart(), {"op": "exists", "query": {"domain": "medication", "codes": ["999"],
                                               "absent_means": "false"}})
    assert r.value is F


def test_default_absent_means_override_changes_the_answer():
    """The ablation switch has to actually move the result, or it measures nothing."""
    q = {"op": "exists", "query": {"domain": "medication", "codes": ["999"],
                                   "absent_means": "unknown"}}
    assert Evaluator(chart()).eval_expr(q).value is U
    assert Evaluator(chart(), default_absent_means="false").eval_expr(q).value is F


def test_zero_is_not_missing():
    """A recorded value of zero is data. Absent is not."""
    c = chart(observations=[obs(UACR, 0.0, "mg/g")])
    r = ev(c, {"op": "compare", "cmp": "<", "left":
              {"val": "observation", "codes": [UACR], "unit": "mg/mmol", "within_days": None},
              "right": {"val": "literal", "number": 30, "unit": "mg/mmol"}})
    assert r.value is T
    assert ev(chart(), {"op": "compare", "cmp": "<", "left":
                        {"val": "observation", "codes": [UACR], "unit": "mg/mmol",
                         "within_days": None},
                        "right": {"val": "literal", "number": 30, "unit": "mg/mmol"}}).value is U


def test_count_on_open_world_absence_is_unknown_not_zero():
    """The defect this test exists for: a count committed 0.0 on silence."""
    v, why, _ = Evaluator(chart())._value(
        {"val": "count", "query": {"domain": "condition", "codes": ["x"],
                                   "absent_means": "unknown"}})
    assert v is None and "undetermined rather than zero" in why


def test_count_on_closed_world_absence_is_zero():
    v, _, _ = Evaluator(chart())._value(
        {"val": "count", "query": {"domain": "condition", "codes": ["x"],
                                   "absent_means": "false"}})
    assert v == 0.0


def test_count_is_not_truncated_by_the_evidence_display_limit():
    c = chart(conditions=[cond("X", days_ago=i + 1) for i in range(9)])
    v, _, _ = Evaluator(c)._value({"val": "count", "query": {
        "domain": "condition", "codes": ["X"], "absent_means": "false"}})
    assert v == 9.0


# --------------------------------------------------------------------------
# 5. Codes and clinical status
# --------------------------------------------------------------------------

def test_parent_criterion_is_satisfied_by_a_child_code():
    """The compiler expands a concept into its descendants; any one of them counts."""
    c = chart(conditions=[cond("368581000119106")])  # neuropathy due to type 2 diabetes
    r = ev(c, {"op": "exists", "query": {
        "domain": "condition", "codes": ["44054006", "368581000119106", "422034002"],
        "absent_means": "false"}})
    assert r.value is T


def test_resolved_condition_is_excluded_when_active_only():
    c = chart(conditions=[cond("44054006", days_ago=400, abated=100)])
    assert ev(c, {"op": "exists", "query": {"domain": "condition", "codes": ["44054006"],
                                            "absent_means": "false", "active_only": True}}).value is F
    assert ev(c, {"op": "exists", "query": {"domain": "condition", "codes": ["44054006"],
                                            "absent_means": "false"}}).value is T


def test_stopped_medication_is_not_active():
    c = chart(medications=[med("860975", status="stopped")])
    assert ev(c, {"op": "exists", "query": {"domain": "medication", "codes": ["860975"],
                                            "absent_means": "false", "active_only": True}}).value is F


# --------------------------------------------------------------------------
# 6. Derived values
# --------------------------------------------------------------------------

def test_ckdepi_is_in_the_right_neighbourhood():
    c = chart(age=50, sex="male", observations=[obs(CREAT, 1.0, "mg/dL")])
    v, _, _ = Evaluator(c)._value({"val": "derived", "name": "egfr_ckdepi_2021"})
    assert 88 < v < 95


def test_ckdepi_falls_as_creatinine_rises():
    lo = Evaluator(chart(observations=[obs(CREAT, 1.0, "mg/dL")]))._value(
        {"val": "derived", "name": "egfr_ckdepi_2021"})[0]
    hi = Evaluator(chart(observations=[obs(CREAT, 2.0, "mg/dL")]))._value(
        {"val": "derived", "name": "egfr_ckdepi_2021"})[0]
    assert hi < lo


def test_ckdepi_without_creatinine_is_unknown():
    v, why, _ = Evaluator(chart())._value({"val": "derived", "name": "egfr_ckdepi_2021"})
    assert v is None and "cannot derive eGFR" in why


def test_age_is_computed_at_the_index_date_not_today():
    import datetime as dt
    c = chart(age=64, index=dt.date(2021, 11, 1))
    assert c.age == 64


def test_age_the_day_before_a_birthday_has_not_ticked_over():
    import datetime as dt
    c = chart(index=dt.date(2021, 11, 1))
    c.birth_date = dt.date(1961, 11, 2)
    assert c.age == 59


# --------------------------------------------------------------------------
# 7. Same-day conflict
# --------------------------------------------------------------------------

def test_two_different_values_on_the_same_latest_date_is_unknown():
    c = chart(observations=[obs(CREAT, 1.0, "mg/dL", days_ago=5, rid="a"),
                            obs(CREAT, 2.4, "mg/dL", days_ago=5, rid="b")])
    r = ev(c, {"op": "compare", "cmp": "<", "left":
              {"val": "observation", "codes": [CREAT], "unit": "mg/dL", "within_days": None},
              "right": {"val": "literal", "number": 2.0, "unit": "mg/dL"}})
    assert r.value is U and "same most recent" in r.reason


def test_identical_duplicate_values_on_one_date_are_not_a_conflict():
    c = chart(observations=[obs(CREAT, 1.0, "mg/dL", days_ago=5, rid="a"),
                            obs(CREAT, 1.0, "mg/dL", days_ago=5, rid="b")])
    assert not c.same_day_conflict([CREAT])


# --------------------------------------------------------------------------
# 8. Verdict mapping and the screen decision
# --------------------------------------------------------------------------

INC = {"criterion_id": "i", "kind": "inclusion", "source_text": "t", "compilable": True,
       "expr": {"op": "const", "value": "TRUE"}}
EXC = {"criterion_id": "e", "kind": "exclusion", "source_text": "t", "compilable": True,
       "expr": {"op": "const", "value": "TRUE"}}


def test_satisfied_inclusion_meets_satisfied_exclusion_fails():
    assert evaluate_criterion(INC, chart())["verdict"] == "MEETS"
    assert evaluate_criterion(EXC, chart())["verdict"] == "FAILS"


def test_unsatisfied_exclusion_is_a_pass():
    e = dict(EXC, expr={"op": "const", "value": "FALSE"})
    assert evaluate_criterion(e, chart())["verdict"] == "MEETS"


def test_unknown_becomes_indeterminate_for_both_kinds():
    for k in (INC, EXC):
        c = dict(k, expr={"op": "const", "value": "UNKNOWN"})
        r = evaluate_criterion(c, chart())
        assert r["verdict"] == "INDETERMINATE" and r["needs_human"]


def test_non_compilable_criterion_routes_to_a_human_and_says_why():
    c = {"criterion_id": "x", "kind": "inclusion", "source_text": "informed consent",
         "compilable": False, "reason_not_compilable": "established at the screening visit"}
    r = evaluate_criterion(c, chart())
    assert r["verdict"] == "INDETERMINATE" and r["not_compilable"] and r["reason"]


def test_one_definite_failure_settles_the_screen_despite_unknowns():
    """This is the property that makes panel reduction possible at all."""
    crit = [dict(INC, criterion_id="a", expr={"op": "const", "value": "FALSE"}),
            dict(INC, criterion_id="b", expr={"op": "const", "value": "UNKNOWN"}),
            dict(INC, criterion_id="c", expr={"op": "const", "value": "UNKNOWN"})]
    r = screen(crit, chart())
    assert r["decision"] == "INELIGIBLE" and r["n_indeterminate"] == 2


def test_any_unknown_without_a_failure_needs_review():
    crit = [dict(INC, criterion_id="a"),
            dict(INC, criterion_id="b", expr={"op": "const", "value": "UNKNOWN"})]
    assert screen(crit, chart())["decision"] == "NEEDS_REVIEW"


def test_all_satisfied_is_eligible():
    assert screen([dict(INC, criterion_id="a")], chart())["decision"] == "ELIGIBLE"


def test_every_ruling_out_carries_positive_evidence():
    """A patient is only excluded on a fact with a resource id behind it."""
    c = chart(conditions=[cond("22298006", days_ago=10, rid="cond-mi-1")])
    crit = dict(EXC, expr={"op": "exists", "query": {
        "domain": "condition", "codes": ["22298006"], "within_days": 183,
        "absent_means": "unknown"}})
    r = evaluate_criterion(crit, c)
    assert r["verdict"] == "FAILS"
    assert any(e["resource_id"] == "cond-mi-1" for e in r["evidence"])


# --------------------------------------------------------------------------
# 9. IR validation
# --------------------------------------------------------------------------

def test_absent_means_is_mandatory():
    with pytest.raises(IRError, match="absent_means"):
        validate_expr({"op": "exists", "query": {"domain": "medication", "codes": ["1"]}})


def test_observation_must_declare_its_unit():
    with pytest.raises(IRError, match="unit"):
        validate_expr({"op": "compare", "cmp": ">",
                       "left": {"val": "observation", "codes": ["x"]},
                       "right": {"val": "literal", "number": 1}})


def test_non_compilable_criterion_must_give_a_reason():
    with pytest.raises(IRError, match="say why"):
        validate_criterion({"criterion_id": "a", "kind": "inclusion", "source_text": "t",
                            "compilable": False})


def test_inverted_between_bounds_are_rejected():
    with pytest.raises(IRError, match="above high"):
        validate_expr({"op": "between", "value": {"val": "age"}, "low": 85, "high": 18})


def test_demographic_only_predicates_are_detected():
    assert is_demographic_only({"op": "between", "value": {"val": "age"},
                                "low": 18, "high": 85})
    assert not is_demographic_only({"op": "compare", "cmp": ">", "left": {
        "val": "observation", "codes": [HBA1C], "unit": "%"},
        "right": {"val": "literal", "number": 7}})
