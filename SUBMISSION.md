# Submission map

Every required deliverable, and the file that satisfies it.

| required | where |
|---|---|
| Full working code | this repository. Zero runtime dependencies, standard library only. |
| Improvement changelog | [docs/IMPROVEMENT_CHANGELOG.md](docs/IMPROVEMENT_CHANGELOG.md) |
| Reproduction guide, clean environment | [REPRODUCE.md](REPRODUCE.md). One command: `python run.py reproduce`. |
| Exact commands | [REPRODUCE.md](REPRODUCE.md) and `python run.py help` |
| Data | `data/vendor/`, with source URL and archive sha256 in `data/vendor/panel_provenance.json` |
| Expected output | `results/published/`, byte-compared by `python run.py diff` |
| Versions | `results/environment.json`, written by every run |
| Runtime and cost | the cost table in [REPRODUCE.md](REPRODUCE.md); recorded token counts in `results/results.json` |
| Solution video, 5 minutes or less | `docs/VIDEO.md` for the link and the script |
| Agent trajectories, every agent | [runs/tierA/trajectories/index.md](runs/tierA/trajectories/index.md) |

## The trajectory requirement, point by point

The brief asks for instructions, tool responses, the feedback that shaped the next
step, retries, and human checkpoints. Each is a distinct event kind in the
recorded JSONL, not a reconstruction:

| asked for | event kind | where to look |
|---|---|---|
| instructions given to the agent | `instructions` | verbatim prompt text, with its version tag |
| tool call and what came back | `tool_call`, `tool_result` | the terminology search, its arguments and its full result |
| feedback that shaped the next step | `validation_error`, `retry` | the validator's error text, then the exact message returned to the model |
| retries | `retry` | numbered, with the budget that bounds them |
| adversarial review | `critic_finding` | the counterexample, and whether running it confirmed or dismissed the finding |
| human checkpoints | `human_checkpoint` | reviewer, role, decision, rationale, and the digest signed |

**Two of those rows describe a mechanism with no instances in the scored run, and
saying so is part of the deliverable.** A third event kind, `revision`, is empty
for the same reason and follows from it: a predicate is only revised after a
confirmed counterexample, so zero findings gives zero revisions necessarily. That
column exists because changelog entry 5 split it away from `normalisation`,
precisely so that a run with 6 harness repairs and 0 real revisions could not
report 6 revisions. It is doing its job by being empty, and the two numbers are
printed side by side in the index rather than summed.

The critic returned OK on every predicate
it reviewed, so there are no `critic_finding` events in the compile trajectories.
A component that never fires cannot be told apart from one that does nothing, so
`evaluation/critic_probe.py` breaks each predicate in a named way and reviews it
again, and those trajectories are where the findings and the revision path are
exercised. `docs/CRITIC_PROBE.md` reports the catch rate next to the false alarm
rate on unmutated controls, because either number alone can be won by a broken
component.

`human_checkpoint` has no instances either, and that one is not going to be fixed
by a harness. Signing is a human action, nothing in this repository performs it,
and no signature exists in this checkout. What is shipped is the mechanism and its
refusal: `docs/GATE.md` is the gate demonstrated by running into it, exit codes
captured rather than transcribed.

The mechanism is wired at both ends. A decision taken in `scripts/signoff.py` is
appended to `<run>/signoffs.jsonl`, which is what the gate reads, **and** appended
to the compiler trajectory of the predicate it approved, continuing that log's
sequence, which is what a reader follows. It used to go to the ledger only. The
event kind existed, the renderer knew how to draw it, the index counted a column
for it, and no line of code ever emitted one, so the column reported a zero that
was true for the wrong reason. `tests/test_human_checkpoint.py` drives the script
the way a reviewer does and asserts the decision lands in both places, that a
rejection is recorded the same way as an approval, and that a run whose
trajectories were not kept still records the signature rather than losing it.

The index is sorted so the trajectories that went wrong come first, because a run
of uniformly clean trajectories is either a trivial task or an edited log.

`python scripts/verify.py trajectories` matches every recorded model call in every
trajectory against a cassette whose stored request is byte-identical to the prompt
shown, so the trajectory is checkable rather than narrated.

## Ground rules

| rule | how this submission satisfies it |
|---|---|
| Public or synthetic data only | Synthea sample FHIR R4 (Apache-2.0, sha256 pinned) and ClinicalTrials.gov API v2 (US Government, public domain). No real patient data. |
| Legal and ethical use case | Trial prescreening that produces a document for a coordinator. It enrols nobody and contacts nobody. |
| Consequential actions sandboxed, with human approval before the action | There is no outward action at all. The only artifact that could affect a person is the worklist. From predicates nobody has signed, `scripts/worklist.py` exits 3 and writes no document. `tests/test_worklist_gate.py` runs the script and asserts the exit code, rather than testing the library call underneath it, because a library test passes even when the script ignores what the library returned. There is one way past: `--allow-unsigned` produces the document with NOT FOR USE stamped across it, so that the gate can be demonstrated and so that the override marks the artifact instead of only the shell history. `docs/GATE.md` is that demonstration, exit codes captured rather than transcribed. |
| A qualified human reviewer in the loop | The sign-off gate. It is a human action and it is left to a human, so whether it has been cleared in this checkout is a fact in `runs/tierA/signoffs.jsonl` rather than a claim here; `python scripts/signoff.py --run runs/tierA --list` prints it. Any signature here is the author's, who is not a clinician, and `reviewer_role` records that. A deployment puts a clinician in that slot. |
| No credentials or private information in the submission | No key, token or credential in the tree **or anywhere in its history**, which is the claim that matters for a repository handed to strangers: a secret committed once and deleted in the next commit is invisible to `git grep` and still in the object store. `tests/test_no_credentials.py` scans the working tree and then every commit reachable from every ref, for eight credential shapes. It carries a positive control that plants a key and requires the scan to catch it, and a negative control that requires it not to fire on code merely reading an environment variable. The model shim copies an auth token to a temporary directory outside the repository and deletes it at exit, and that is asserted too. |
| Every claim tied to submitted evidence | Numbers come from `results/results.json`, generated by `scripts/report.py` from recorded cells. The opening example in the README is generated by `scripts/counterexample.py` and says so if it fails to hold. Three registered trials with public identifiers is the setup where recall can masquerade as reading, so `scripts/contamination.py` checks it three ways and `docs/CONTAMINATION.md` is the output: no prompt template has a slot for an identifier, no recorded request contains one, and a perturbed threshold has to reach the predicate. On the last of those, 6 of 6 compiled criteria carry the changed number and none carries the original. |

## What is deliberately not here

- **No live clinical deployment.** The panel is synthetic and the trials are
  registry summaries rather than site protocols.
- **No claim that a coarse code can be read as a fine one.** Where the vocabulary
  cannot draw the distinction a criterion needs, the answer is undetermined and
  the reason says why.
- **No accuracy figure without a coverage figure beside it.** Abstaining
  everywhere is a way to score perfectly on accuracy alone, so the two are
  reported as a pair throughout.
