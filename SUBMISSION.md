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
| Coding agents disclosed, and what pre-existed | [Tools used, and what existed before the competition](#tools-used-and-what-existed-before-the-competition) |

## Tools used, and what existed before the competition

The rules require both of these to be stated, so they are stated here rather than
left to be inferred from the code.

### What existed before

**Nothing in this repository.** The problem was released at 15:00 UTC on 28
August 2026. The first commit here is `Add evaluation protocol and engine` at
**20:03 UTC on 28 August**, five hours later, and every file was written after
that. `git log --reverse` shows it.

There are **zero runtime dependencies**. `pyproject.toml` declares
`dependencies = []`, the engine and the evaluation run on the Python standard
library alone, and `tests/test_dependencies.py` fails if any module outside an
allow-list is imported. So there is no pre-existing framework doing the work and
no library boundary where the interesting part could be hiding. The only
third-party code involved at all is `pytest` for the test run, and `edge_tts` and
`playwright` for building the video, which is not on the reproduction path.

What did exist before, and was not written here, is the input data:

| pre-existing input | source | licence |
|---|---|---|
| 385-patient synthetic panel | Synthea sample FHIR R4 | Apache-2.0, archive sha256 pinned in `data/vendor/panel_provenance.json` |
| three trial protocols | ClinicalTrials.gov API v2 | US Government, public domain |
| terminology catalog | codes observed in the panel itself | derived here from the above |

No patient in this repository is a person. No credential is in the tree or in its
history, which `tests/test_no_credentials.py` checks across every commit
reachable from every ref.

### Coding agents used to build it

Coding-agent use is required by the rules and is disclosed here in full.

| tool | model | what it did |
|---|---|---|
| Claude Code | Claude Opus 5 | the primary coding agent. Wrote the engine, the compiler, the evaluation harness, the tests and the documentation, and ran the recorded evaluations. |

Delegated subagents run inside Claude Code were used for fan-out work that
returns a digest: independent blind review seats scoring this submission against
the published rubric, and read-only searches across the tree. They wrote no code
that was kept without being verified here first.

### Models the system calls at runtime

A different question from the one above, and worth separating, because the models
below are the subject of the evaluation rather than the authors of it. Every call
is recorded, and these counts are the recorded cassettes rather than an
account of intent:

| model | recorded calls | used for |
|---|---|---|
| `gemini-3.7-flash-medium` | 1,167 | the scored run: segmenter, grounder, compiler, critic, and the per-cell B2 baseline |
| `gpt-oss-120b-medium` | 181 | Checker B, the independent second labeller |
| `granite3.1-dense:8b` | 42 | the weak-model probe in `docs/WEAK_MODEL.md` |

Checker B runs on a **different model family from the system it labels**, which
is what makes the label noise floor a measurement rather than a model agreeing
with itself. `python scripts/verify.py blind` reads that independence out of
Checker B's own recorded prompts.

Calls reach these models through `cli_openai_shim.py`, a local
OpenAI-compatible endpoint that forwards to a vendor CLI the author is
authenticated to. That is why `docs/COST.md` reports the marginal cost of this
run as zero and publishes a hosted-rate estimate beside it: reporting zero would
be true and useless to anyone deciding whether to run it themselves.

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

**One of those rows describes a mechanism with no instances in the scored run,
and saying which is part of the deliverable.** The counts below come from
`python scripts/trajectories.py`, which reads the JSONL rather than being told.

| event kind | instances in the scored run | where |
|---|---|---|
| `critic_finding` | 2 | the compile trajectories, one confirmed by execution and one dismissed by it |
| `revision` | 1 | the predicate the confirmed counterexample changed |
| `human_checkpoint` | **0** | nothing in this repository performs one |

Two findings across 18 compiled predicates is a thin sample, and a component that
fires twice is only marginally more checkable than one that never fires. So
`evaluation/critic_probe.py` breaks each predicate in a named way and reviews it
again: **9 planted defects, 9 caught, 5 unmutated controls, 0 false alarms**, in
`docs/CRITIC_PROBE.md`. Both numbers or neither, because a critic that answered
REVISE to everything would catch every defect and be worthless, and the control
column is the only thing that separates the two. Those 9 findings are recorded in
`runs/tierA/trajectories/critic_probe/` and counted separately from the 2 in the
scored run, rather than summed into one flattering total.

The `revision` column exists at all because changelog entry 5 split it away from
`normalisation`, so that a run with 24 harness repairs and 1 real revision could
not report 25 revisions. The two numbers are printed side by side in the index
rather than added.

**A note on what was removed.** The index reported 15 critic findings and 3
revisions until the trajectories behind them were checked. Two thirds of them came
from compilation seeds 8 and 9, which had replayed seed 7's cassettes rather than
calling the model, so they were three copies of one run. Deleting the compiled
output of a run that did not happen is not enough: its trajectories are evidence
too, and they were being counted. Entry 22 in the changelog has the detail.

`human_checkpoint` is the empty one, and it is not going to be fixed
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
| What existed before the competition, and what was added | Everything in this repository was written after the problem was released: first commit 20:03 UTC on 28 August, five hours after the 15:00 UTC kickoff. `dependencies = []`, so no pre-existing framework is doing the work. The pre-existing inputs are the synthetic panel and the public trial protocols, each named with its licence above. |
| Every tool and component used within its licence | Synthea sample data is Apache-2.0 and the archive sha256 is pinned; ClinicalTrials.gov API v2 output is US Government public domain. Runtime model calls go through a local shim to a vendor CLI the author is authenticated to, under that vendor's own terms, and no key is in the tree. `pytest`, `edge_tts` and `playwright` are the only third-party packages, all permissively licensed, and the last two are off the reproduction path. |
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
