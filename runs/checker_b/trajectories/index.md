# Agent trajectories

180 trajectories from `runs/checker_b`. Each markdown file below is a rendering of the JSONL beside it, and the JSONL is the source of truth. Every model call in every one of them is matched to a recorded cassette by `python scripts/verify.py trajectories`, so the prompt shown here is byte-identical to the prompt that was sent.

| | |
|---|---|
| model calls | 181 |
| tool calls | 0 |
| schema rejections fed back to the model | 1 |
| retries after a schema rejection | 1 |
| recompiles after a confirmed counterexample | 0 |
| requests resent after the endpoint failed | 73 |
| critic findings | 0 |
| predicates revised after a confirmed counterexample | 0 |
| malformed fields the harness repaired without a retry | 0 |
| human checkpoints | 0 |
| completion tokens | 4782 |

This is one arm of the evaluation rather than the scored pipeline. Its agent is `checker_b`, and the scored run's index, which explains where each of the six agents keeps its log, is at [runs/tierA/trajectories/index.md](../../tierA/trajectories/index.md). What the arms are and what each one is compared against is in [results/RESULTS.md](../../../results/RESULTS.md).

## Read this one first

1. **[the schema rejected the model, and it was told why](checker_b/NCT06983054-EXC-01--bf0ad07a.md)** (checker_b, `NCT06983054-EXC-01--bf0ad07a`). 1 of these. The model returned something the schema would not accept. The validator's message is fed back as the next turn's input, and the retry is the model reading it.

Sorted so the trajectories that went wrong come first. Those are the ones worth reading: they show what the agent was told about its own output and what it did next.

| agent | subject | calls | rejections | retries | critic | revised | outcome |
|---|---|---|---|---|---|---|---|
| checker_b | [NCT06983054-EXC-01--bf0ad07a](checker_b/NCT06983054-EXC-01--bf0ad07a.md) | 2 | 1 | 1 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--396babc6](checker_b/NCT06983054-EXC-02--396babc6.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--38f38890](checker_b/NCT06983054-INC-04--38f38890.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-09--61a2fcc0](checker_b/NCT06983054-INC-09--61a2fcc0.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-04--50aac3ff](checker_b/NCT06989723-EXC-04--50aac3ff.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--09faca51](checker_b/NCT06989723-INC-01--09faca51.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--38f38890](checker_b/NCT06717698-INC-03--38f38890.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--74b7fc31](checker_b/NCT06717698-INC-03--74b7fc31.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--90053970](checker_b/NCT06983054-EXC-01--90053970.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--203e71e8](checker_b/NCT06983054-EXC-02--203e71e8.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-01--cb8c092a](checker_b/NCT06983054-INC-01--cb8c092a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--c98f8278](checker_b/NCT06983054-INC-03--c98f8278.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--f665d685](checker_b/NCT06983054-INC-04--f665d685.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--443e574b](checker_b/NCT06983054-INC-07--443e574b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-01--3a364909](checker_b/NCT06989723-EXC-01--3a364909.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--90053970](checker_b/NCT06989723-EXC-03--90053970.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-02--459f6a66](checker_b/NCT06717698-EXC-02--459f6a66.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-07--5ec53533](checker_b/NCT06717698-EXC-07--5ec53533.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--418c6a4c](checker_b/NCT06717698-INC-01--418c6a4c.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--81b2098d](checker_b/NCT06717698-INC-01--81b2098d.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--c6861ca8](checker_b/NCT06717698-INC-01--c6861ca8.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--055bcb42](checker_b/NCT06717698-INC-03--055bcb42.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--165a4435](checker_b/NCT06717698-INC-03--165a4435.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--454bbec4](checker_b/NCT06717698-INC-03--454bbec4.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--07a1f80c](checker_b/NCT06717698-INC-07--07a1f80c.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--563187cb](checker_b/NCT06717698-INC-07--563187cb.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--60e27639](checker_b/NCT06717698-INC-07--60e27639.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--6f4a8d14](checker_b/NCT06717698-INC-07--6f4a8d14.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--0f444cf3](checker_b/NCT06983054-EXC-01--0f444cf3.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--6b3a5686](checker_b/NCT06983054-EXC-02--6b3a5686.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-01--5e4a0309](checker_b/NCT06983054-INC-01--5e4a0309.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-01--b74d0752](checker_b/NCT06983054-INC-01--b74d0752.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--5b0609a7](checker_b/NCT06983054-INC-02--5b0609a7.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--be01726c](checker_b/NCT06983054-INC-02--be01726c.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--83c5cc27](checker_b/NCT06983054-INC-03--83c5cc27.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--a06bce31](checker_b/NCT06983054-INC-03--a06bce31.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--5b2f8ddd](checker_b/NCT06983054-INC-04--5b2f8ddd.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--d868e198](checker_b/NCT06983054-INC-04--d868e198.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--165a4435](checker_b/NCT06983054-INC-07--165a4435.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--67c6597f](checker_b/NCT06983054-INC-07--67c6597f.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--79823958](checker_b/NCT06983054-INC-07--79823958.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-09--80591a09](checker_b/NCT06983054-INC-09--80591a09.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-09--cf49b901](checker_b/NCT06983054-INC-09--cf49b901.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--246fb368](checker_b/NCT06989723-EXC-03--246fb368.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--3a364909](checker_b/NCT06989723-EXC-03--3a364909.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--63d20fbe](checker_b/NCT06989723-EXC-03--63d20fbe.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--72f91cc7](checker_b/NCT06989723-INC-01--72f91cc7.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--873049ed](checker_b/NCT06989723-INC-01--873049ed.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--d19face0](checker_b/NCT06989723-INC-02--d19face0.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--0b48bf9b](checker_b/NCT06989723-INC-05--0b48bf9b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--2a98d763](checker_b/NCT06989723-INC-05--2a98d763.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--b8c195d4](checker_b/NCT06989723-INC-05--b8c195d4.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-01--23d16ee3](checker_b/NCT06717698-EXC-01--23d16ee3.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-01--2af5741b](checker_b/NCT06717698-EXC-01--2af5741b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-01--7d1a0d44](checker_b/NCT06717698-EXC-01--7d1a0d44.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-02--d02b2ca5](checker_b/NCT06717698-EXC-02--d02b2ca5.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-07--22e14c09](checker_b/NCT06717698-EXC-07--22e14c09.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-07--28db1c55](checker_b/NCT06717698-EXC-07--28db1c55.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-07--2987fe83](checker_b/NCT06717698-EXC-07--2987fe83.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-EXC-07--39b9fc41](checker_b/NCT06717698-EXC-07--39b9fc41.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--297c1550](checker_b/NCT06717698-INC-01--297c1550.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--3dfce025](checker_b/NCT06717698-INC-01--3dfce025.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--407ef75b](checker_b/NCT06717698-INC-01--407ef75b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-01--d31bde96](checker_b/NCT06717698-INC-01--d31bde96.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--1376b3c5](checker_b/NCT06717698-INC-03--1376b3c5.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--177971b9](checker_b/NCT06717698-INC-03--177971b9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--303c8bd7](checker_b/NCT06717698-INC-03--303c8bd7.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--33c2ca32](checker_b/NCT06717698-INC-03--33c2ca32.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--3d5f91c2](checker_b/NCT06717698-INC-03--3d5f91c2.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--8151b558](checker_b/NCT06717698-INC-03--8151b558.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--86b4e80a](checker_b/NCT06717698-INC-03--86b4e80a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--9188198b](checker_b/NCT06717698-INC-03--9188198b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--9e84e569](checker_b/NCT06717698-INC-03--9e84e569.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--af7711e2](checker_b/NCT06717698-INC-03--af7711e2.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--ccfc4db2](checker_b/NCT06717698-INC-03--ccfc4db2.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--d29560ea](checker_b/NCT06717698-INC-03--d29560ea.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-03--e1a2f3c6](checker_b/NCT06717698-INC-03--e1a2f3c6.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-05--7fea6a12](checker_b/NCT06717698-INC-05--7fea6a12.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-05--915aacda](checker_b/NCT06717698-INC-05--915aacda.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-05--97a20cf9](checker_b/NCT06717698-INC-05--97a20cf9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--23d16ee3](checker_b/NCT06717698-INC-07--23d16ee3.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--303c8bd7](checker_b/NCT06717698-INC-07--303c8bd7.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--307b6419](checker_b/NCT06717698-INC-07--307b6419.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--3ce79121](checker_b/NCT06717698-INC-07--3ce79121.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--918e387f](checker_b/NCT06717698-INC-07--918e387f.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06717698-INC-07--d7c46304](checker_b/NCT06717698-INC-07--d7c46304.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--165a4435](checker_b/NCT06983054-EXC-01--165a4435.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--1d1af1df](checker_b/NCT06983054-EXC-01--1d1af1df.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--3beee40e](checker_b/NCT06983054-EXC-01--3beee40e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--5ec53533](checker_b/NCT06983054-EXC-01--5ec53533.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--82493462](checker_b/NCT06983054-EXC-01--82493462.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--8c39d1ea](checker_b/NCT06983054-EXC-01--8c39d1ea.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--8de0c26b](checker_b/NCT06983054-EXC-01--8de0c26b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--c0b0f482](checker_b/NCT06983054-EXC-01--c0b0f482.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--c628b9c2](checker_b/NCT06983054-EXC-01--c628b9c2.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--d362f4e5](checker_b/NCT06983054-EXC-01--d362f4e5.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--e4c2980e](checker_b/NCT06983054-EXC-01--e4c2980e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-01--fa311677](checker_b/NCT06983054-EXC-01--fa311677.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--1a4f3136](checker_b/NCT06983054-EXC-02--1a4f3136.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--1ab85caa](checker_b/NCT06983054-EXC-02--1ab85caa.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--3f8f669e](checker_b/NCT06983054-EXC-02--3f8f669e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--4727c1ea](checker_b/NCT06983054-EXC-02--4727c1ea.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--76b289fd](checker_b/NCT06983054-EXC-02--76b289fd.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--c63b5472](checker_b/NCT06983054-EXC-02--c63b5472.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--d8e3a701](checker_b/NCT06983054-EXC-02--d8e3a701.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-02--f6542a20](checker_b/NCT06983054-EXC-02--f6542a20.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-03--792a51c0](checker_b/NCT06983054-EXC-03--792a51c0.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-03--8bf6aa92](checker_b/NCT06983054-EXC-03--8bf6aa92.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-EXC-05--246fb368](checker_b/NCT06983054-EXC-05--246fb368.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-01--0d281c81](checker_b/NCT06983054-INC-01--0d281c81.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-01--aa2f41c3](checker_b/NCT06983054-INC-01--aa2f41c3.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--509f9a77](checker_b/NCT06983054-INC-02--509f9a77.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--659bd07d](checker_b/NCT06983054-INC-02--659bd07d.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--8c39d1ea](checker_b/NCT06983054-INC-02--8c39d1ea.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--a06bce31](checker_b/NCT06983054-INC-02--a06bce31.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--be82309d](checker_b/NCT06983054-INC-02--be82309d.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--c0219ca9](checker_b/NCT06983054-INC-02--c0219ca9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--f6542a20](checker_b/NCT06983054-INC-02--f6542a20.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--f992b5b4](checker_b/NCT06983054-INC-02--f992b5b4.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-02--ff9f14e4](checker_b/NCT06983054-INC-02--ff9f14e4.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--2987fe83](checker_b/NCT06983054-INC-03--2987fe83.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--3dfce025](checker_b/NCT06983054-INC-03--3dfce025.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--90053970](checker_b/NCT06983054-INC-03--90053970.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--d321aaa9](checker_b/NCT06983054-INC-03--d321aaa9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-03--d432ac90](checker_b/NCT06983054-INC-03--d432ac90.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--28db1c55](checker_b/NCT06983054-INC-04--28db1c55.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--303c8bd7](checker_b/NCT06983054-INC-04--303c8bd7.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--90a958eb](checker_b/NCT06983054-INC-04--90a958eb.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--94c64aed](checker_b/NCT06983054-INC-04--94c64aed.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--a25e9984](checker_b/NCT06983054-INC-04--a25e9984.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--e23c7a6e](checker_b/NCT06983054-INC-04--e23c7a6e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--f4e9db02](checker_b/NCT06983054-INC-04--f4e9db02.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-04--fbc55f1a](checker_b/NCT06983054-INC-04--fbc55f1a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--01d78eb5](checker_b/NCT06983054-INC-07--01d78eb5.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--05877654](checker_b/NCT06983054-INC-07--05877654.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--1cfa5a70](checker_b/NCT06983054-INC-07--1cfa5a70.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--2c098b38](checker_b/NCT06983054-INC-07--2c098b38.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--34f26c54](checker_b/NCT06983054-INC-07--34f26c54.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--42017485](checker_b/NCT06983054-INC-07--42017485.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--d57e867e](checker_b/NCT06983054-INC-07--d57e867e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--df9b9e5b](checker_b/NCT06983054-INC-07--df9b9e5b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-07--e841df97](checker_b/NCT06983054-INC-07--e841df97.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-09--b8c195d4](checker_b/NCT06983054-INC-09--b8c195d4.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06983054-INC-09--d7bb0340](checker_b/NCT06983054-INC-09--d7bb0340.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-01--055bcb42](checker_b/NCT06989723-EXC-01--055bcb42.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-01--23cec4fc](checker_b/NCT06989723-EXC-01--23cec4fc.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-01--c6861ca8](checker_b/NCT06989723-EXC-01--c6861ca8.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-01--e4c2980e](checker_b/NCT06989723-EXC-01--e4c2980e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--72b71d33](checker_b/NCT06989723-EXC-03--72b71d33.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--8bf6aa92](checker_b/NCT06989723-EXC-03--8bf6aa92.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--a06bce31](checker_b/NCT06989723-EXC-03--a06bce31.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-03--d66b5418](checker_b/NCT06989723-EXC-03--d66b5418.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-04--39e6bf34](checker_b/NCT06989723-EXC-04--39e6bf34.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-04--aa2f41c3](checker_b/NCT06989723-EXC-04--aa2f41c3.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-EXC-04--fcca54e8](checker_b/NCT06989723-EXC-04--fcca54e8.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--1a4f3136](checker_b/NCT06989723-INC-01--1a4f3136.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--2f031d4a](checker_b/NCT06989723-INC-01--2f031d4a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--4688bc6a](checker_b/NCT06989723-INC-01--4688bc6a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--51c7ff6a](checker_b/NCT06989723-INC-01--51c7ff6a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--5c15f3b9](checker_b/NCT06989723-INC-01--5c15f3b9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--7cfbccad](checker_b/NCT06989723-INC-01--7cfbccad.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-01--fc8dfe9b](checker_b/NCT06989723-INC-01--fc8dfe9b.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--0288c42c](checker_b/NCT06989723-INC-02--0288c42c.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--3f8f669e](checker_b/NCT06989723-INC-02--3f8f669e.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--418c6a4c](checker_b/NCT06989723-INC-02--418c6a4c.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--51b59c09](checker_b/NCT06989723-INC-02--51b59c09.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--57b53310](checker_b/NCT06989723-INC-02--57b53310.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--90053970](checker_b/NCT06989723-INC-02--90053970.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--9c3df38a](checker_b/NCT06989723-INC-02--9c3df38a.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--b91dc3fd](checker_b/NCT06989723-INC-02--b91dc3fd.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-02--d66b5418](checker_b/NCT06989723-INC-02--d66b5418.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-03--8151b558](checker_b/NCT06989723-INC-03--8151b558.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-03--83a86980](checker_b/NCT06989723-INC-03--83a86980.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--0ee91088](checker_b/NCT06989723-INC-05--0ee91088.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--7378ba81](checker_b/NCT06989723-INC-05--7378ba81.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--7683e3a1](checker_b/NCT06989723-INC-05--7683e3a1.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--915aacda](checker_b/NCT06989723-INC-05--915aacda.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--d3daf8c9](checker_b/NCT06989723-INC-05--d3daf8c9.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--f0aa92fa](checker_b/NCT06989723-INC-05--f0aa92fa.md) | 1 | 0 | 0 | 0 | 0 | done |
| checker_b | [NCT06989723-INC-05--fdc21ebe](checker_b/NCT06989723-INC-05--fdc21ebe.md) | 1 | 0 | 0 | 0 | 0 | done |

