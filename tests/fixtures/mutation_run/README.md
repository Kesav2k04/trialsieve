# Compiled predicates kept as a mutation fixture

`tests/test_critic_probe.py` checks that every defect `evaluation/critic_probe.py`
plants is actually planted. That needs predicates carrying the features each
mutation targets: a comparison operator, a numeric threshold, a time window, and a
query whose `absent_means` is `unknown`.

The gate fixture next door has none of those, so four of the five mutation tests
skipped against it, and a skip is indistinguishable from a pass while leaving the
mutation unchecked.

This file is four compilable predicates recorded during an early development run.
It is a fixture and not a result. No number in the writeup comes from it, and the
predicates in it were never scored.
