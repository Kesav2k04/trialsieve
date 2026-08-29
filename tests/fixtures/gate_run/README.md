# A run directory kept as a test fixture

`tests/test_worklist_gate.py` runs `scripts/worklist.py` as a subprocess and reads
its exit status, because the claim in `SUBMISSION.md` is about the script and not
about the library function underneath it.

That test needs a run with compiled predicates and no signatures. Pointing it at
the scored run made it skip on a clean clone, before anything has been recorded,
which is exactly when a reader checking the claim would run it. A skipped test
backs no claim.

So one small compiled file is committed here: two criteria, one of them
compilable, recorded during a smoke run. It is a fixture and not a result. No
number in the writeup comes from it.
