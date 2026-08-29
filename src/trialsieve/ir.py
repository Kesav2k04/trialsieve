"""The predicate IR: the artifact a compiled criterion actually becomes.

Design constraints that shaped this format:

* A human has to be able to read one of these and agree or disagree with it in
  under a minute, because sign-off happens per criterion and not per patient.
* Every leaf that touches the record must name the codes it will read and the
  window it will read them over, so the evidence trail is derivable from the IR
  alone before anything runs.
* Absence has to be modelled explicitly. `absent_means` is the whole ballgame:
  a missing SGLT2 inhibitor on a reconciled medication list is close to proof
  the patient is not taking one, while a missing HbA1c is proof of nothing.
  The compiler must choose, and the reviewer sees the choice.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

BOOL_OPS = {"and", "or", "not", "at_least"}
LEAF_OPS = {"compare", "between", "exists", "const"}
ALL_OPS = BOOL_OPS | LEAF_OPS

CMP = {">", ">=", "<", "<=", "==", "!="}

VALUE_KINDS = {"age", "sex", "observation", "literal", "derived", "count"}
DOMAINS = {"condition", "medication", "procedure", "observation"}
AGGS = {"latest", "min", "max", "any", "first"}

#: Codes that contain the concept without establishing it.
#:
#: A site can hold a code that is genuinely broader than the criterion asks for.
#: This corpus records every diabetes diagnosis under SNOMED 44054006, displayed
#: as the single word "Diabetes", and has no separate code for type 2. A trial
#: asking for type 2 diabetes therefore cannot be answered from the presence of
#: that code, and can be answered from its absence: a patient with no diabetes
#: code at all does not have type 2 diabetes either.
#:
#: That asymmetry is the whole reason this field exists. Treating a broader code
#: as an exact match manufactures MEETS verdicts for a criterion the record
#: cannot settle. Refusing the concept entirely throws away the half of the
#: information that is real. `broader_codes` keeps both: present is UNKNOWN,
#: absent is whatever `absent_means` says.

#: What an empty result set means for a given domain.
#: "false"   - closed world. The record is trusted to be complete for this query.
#: "unknown" - open world. Silence in the record is not an answer.
ABSENT_MEANS = {"false", "unknown"}

DERIVED = {"egfr_ckdepi_2021", "bmi", "systolic_bp", "diastolic_bp"}


class IRError(ValueError):
    """Raised when a compiled criterion is not a well-formed predicate."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_value(v: Any, path: str = "value") -> None:
    if not isinstance(v, dict):
        raise IRError(f"{path}: value must be an object, got {type(v).__name__}")
    kind = v.get("val")
    if kind not in VALUE_KINDS:
        raise IRError(f"{path}: unknown value kind {kind!r}; expected one of {sorted(VALUE_KINDS)}")
    if kind == "literal":
        if not isinstance(v.get("number"), (int, float)) and not isinstance(v.get("string"), str):
            raise IRError(f"{path}: literal needs a number or a string")
    elif kind == "observation":
        codes = v.get("codes")
        if not isinstance(codes, list) or not codes or not all(isinstance(c, str) for c in codes):
            raise IRError(f"{path}: observation needs a non-empty list of string codes")
        if v.get("agg", "latest") not in AGGS:
            raise IRError(f"{path}: unknown agg {v.get('agg')!r}")
        if not isinstance(v.get("unit"), str):
            raise IRError(f"{path}: observation must declare the unit it expects")
        _check_within(v, path)
    elif kind == "derived":
        if v.get("name") not in DERIVED:
            raise IRError(f"{path}: unknown derived value {v.get('name')!r}; expected one of {sorted(DERIVED)}")
        _check_within(v, path)
    elif kind == "count":
        validate_query(v.get("query"), f"{path}.query")


def _check_within(v: dict, path: str) -> None:
    w = v.get("within_days")
    if w is not None and (not isinstance(w, int) or w <= 0):
        raise IRError(f"{path}: within_days must be a positive integer or null, got {w!r}")


def validate_query(q: Any, path: str = "query") -> None:
    if not isinstance(q, dict):
        raise IRError(f"{path}: query must be an object")
    if q.get("domain") not in DOMAINS:
        raise IRError(f"{path}: unknown domain {q.get('domain')!r}")
    codes = q.get("codes")
    if not isinstance(codes, list) or not all(isinstance(c, str) for c in codes):
        raise IRError(f"{path}: query codes must be a list of string codes")
    broader = q.get("broader_codes")
    if broader is not None:
        if not isinstance(broader, list) or not all(isinstance(c, str) for c in broader):
            raise IRError(f"{path}: broader_codes must be a list of string codes")
        if set(broader) & set(codes):
            raise IRError(
                f"{path}: a code cannot be both exact and broader than the concept; "
                f"overlapping: {sorted(set(broader) & set(codes))}")
    # `codes` may be empty when `broader_codes` carries the concept. That is the
    # shape this vocabulary forces when a site records only a parent code: the
    # exact concept has no code here, so nothing can establish it, and presence of
    # the parent is UNKNOWN rather than MEETS. Requiring `codes` to be non-empty
    # left the model one legal move, putting the parent in `codes`, which is the
    # promotion that manufactured 358 of 424 wrong exclusions. A query with no
    # code in either slot is still meaningless and is still refused.
    if not codes and not (broader or []):
        raise IRError(
            f"{path}: a query needs at least one code, in codes or in broader_codes")
    if q.get("absent_means") not in ABSENT_MEANS:
        raise IRError(
            f"{path}: absent_means must be 'false' (the record is trusted to be complete "
            f"for this query) or 'unknown' (silence is not an answer); got {q.get('absent_means')!r}"
        )
    _check_within(q, path)


def validate_expr(e: Any, path: str = "expr") -> None:
    if not isinstance(e, dict):
        raise IRError(f"{path}: expression must be an object")
    op = e.get("op")
    if op not in ALL_OPS:
        raise IRError(f"{path}: unknown op {op!r}; expected one of {sorted(ALL_OPS)}")

    if op in {"and", "or"}:
        args = e.get("args")
        if not isinstance(args, list) or len(args) < 1:
            raise IRError(f"{path}: {op} needs a non-empty args list")
        for i, a in enumerate(args):
            validate_expr(a, f"{path}.args[{i}]")
    elif op == "not":
        validate_expr(e.get("arg"), f"{path}.arg")
    elif op == "at_least":
        n = e.get("n")
        args = e.get("args")
        if not isinstance(n, int) or n < 1:
            raise IRError(f"{path}: at_least needs a positive integer n")
        if not isinstance(args, list) or len(args) < n:
            raise IRError(f"{path}: at_least n={n} needs at least {n} args")
        for i, a in enumerate(args):
            validate_expr(a, f"{path}.args[{i}]")
    elif op == "compare":
        if e.get("cmp") not in CMP:
            raise IRError(f"{path}: unknown comparison {e.get('cmp')!r}")
        validate_value(e.get("left"), f"{path}.left")
        validate_value(e.get("right"), f"{path}.right")
    elif op == "between":
        validate_value(e.get("value"), f"{path}.value")
        for k in ("low", "high"):
            if not isinstance(e.get(k), (int, float)):
                raise IRError(f"{path}: between needs a numeric {k}")
        if e["low"] > e["high"]:
            raise IRError(f"{path}: between has low {e['low']} above high {e['high']}")
    elif op == "exists":
        validate_query(e.get("query"), f"{path}.query")
    elif op == "const":
        if e.get("value") not in {"TRUE", "FALSE", "UNKNOWN"}:
            raise IRError(f"{path}: const must be TRUE, FALSE or UNKNOWN")


def validate_criterion(c: Any, path: str = "criterion") -> None:
    """Validate one compiled criterion record."""
    if not isinstance(c, dict):
        raise IRError(f"{path}: criterion must be an object")
    for k in ("criterion_id", "kind", "source_text"):
        if not isinstance(c.get(k), str) or not c[k].strip():
            raise IRError(f"{path}: missing required string field {k!r}")
    if c["kind"] not in {"inclusion", "exclusion"}:
        raise IRError(f"{path}: kind must be inclusion or exclusion, got {c['kind']!r}")
    if not isinstance(c.get("compilable"), bool):
        raise IRError(f"{path}: compilable must be a boolean")
    if c["compilable"]:
        validate_expr(c.get("expr"), f"{path}.expr")
    else:
        reason = c.get("reason_not_compilable")
        if not isinstance(reason, str) or not reason.strip():
            raise IRError(f"{path}: a criterion marked not compilable must say why")


# ---------------------------------------------------------------------------
# Introspection used by the reviewer UI and the evidence planner
# ---------------------------------------------------------------------------

def referenced_codes(e: dict) -> list[tuple[str, str]]:
    """Every (domain, code) the expression will read. Order is stable."""
    out: list[tuple[str, str]] = []

    def walk_value(v: dict) -> None:
        if v.get("val") == "observation":
            out.extend(("observation", c) for c in v["codes"])
        elif v.get("val") == "derived":
            for c in derived_inputs(v["name"]):
                out.append(("observation", c))
        elif v.get("val") == "count":
            walk_query(v["query"])

    def walk_query(q: dict) -> None:
        out.extend((q["domain"], c) for c in q["codes"])

    def walk(x: dict) -> None:
        op = x.get("op")
        if op in {"and", "or", "at_least"}:
            for a in x["args"]:
                walk(a)
        elif op == "not":
            walk(x["arg"])
        elif op == "compare":
            walk_value(x["left"])
            walk_value(x["right"])
        elif op == "between":
            walk_value(x["value"])
        elif op == "exists":
            walk_query(x["query"])

    walk(e)
    seen: set[tuple[str, str]] = set()
    uniq = []
    for item in out:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq


def derived_inputs(name: str) -> list[str]:
    return {
        "egfr_ckdepi_2021": ["38483-4", "2160-0"],
        "bmi": ["39156-5"],
        "systolic_bp": ["8480-6"],
        "diastolic_bp": ["8462-4"],
    }.get(name, [])


def is_demographic_only(e: dict) -> bool:
    """True when the predicate reads nothing but age, sex and constants.

    Age and sex bounds are present on essentially every Synthea patient, so a
    system that rules people out on those alone would post a large panel
    reduction while telling a coordinator nothing they did not already know.
    The headline is therefore reported as the reduction *beyond* what these
    predicates achieve on their own, and this is the test that separates them.
    """
    if referenced_codes(e):
        return False
    kinds: set[str] = set()

    def walk_value(v: dict) -> None:
        kinds.add(v.get("val", "?"))

    def walk(x: dict) -> None:
        op = x.get("op")
        if op in {"and", "or", "at_least"}:
            for a in x["args"]:
                walk(a)
        elif op == "not":
            walk(x["arg"])
        elif op == "compare":
            walk_value(x["left"])
            walk_value(x["right"])
        elif op == "between":
            walk_value(x["value"])
        elif op == "exists":
            kinds.add("exists")

    walk(e)
    return kinds.issubset({"age", "sex", "literal"})


def open_world_leaves(e: dict) -> int:
    """How many leaves treat silence as unknown. Used to summarise a criterion."""
    n = 0

    def walk(x: dict) -> None:
        nonlocal n
        op = x.get("op")
        if op in {"and", "or", "at_least"}:
            for a in x["args"]:
                walk(a)
        elif op == "not":
            walk(x["arg"])
        elif op == "exists" and x["query"].get("absent_means") == "unknown":
            n += 1

    walk(e)
    return n
