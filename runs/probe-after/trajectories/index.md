# Agent trajectories

21 trajectories from `runs/probe-after`. Each markdown file below is a rendering of the JSONL beside it, and the JSONL is the source of truth. Every model call in every one of them is matched to a recorded cassette by `python scripts/verify.py trajectories`, so the prompt shown here is byte-identical to the prompt that was sent.

| | |
|---|---|
| model calls | 42 |
| tool calls | 21 |
| schema rejections fed back to the model | 0 |
| retries after a schema rejection | 0 |
| recompiles after a confirmed counterexample | 0 |
| requests resent after the endpoint failed | 3 |
| critic findings | 0 |
| revisions asked for after a confirmed counterexample | 0 |
| of those, the predicate actually changed | 0 |
| malformed fields the harness repaired without a retry | 0 |
| human checkpoints | 0 |
| completion tokens | 8493 |

## The tools, and what calling one looks like in the log

| tool | calls | what it does, and why it is a tool rather than a prompt |
|---|---|---|
| `terminology.search_any` | 21 | lexical search over the codes this site's own records use. Deliberately not an embedding search: a near miss on a drug class is indistinguishable from a hit right up until it clears a patient. |

This is one arm of the evaluation rather than the scored pipeline. Its agent is `vocab_probe`, and the scored run's index, which explains where each of the six agents keeps its log, is at [runs/tierA/trajectories/index.md](../../tierA/trajectories/index.md). What the arms are and what each one is compared against is in [results/RESULTS.md](../../../results/RESULTS.md).

## Read this one first

1. **[the grounder could not map the concept, and stopped rather than guessing](vocab_probe/absent-Metoprolol.md)** (vocab_probe, `absent-Metoprolol`). 7 of these. A near miss on a drug class is indistinguishable from a hit right up until it clears a patient, so an unmappable concept ends the step instead of returning the closest code.

Sorted so the trajectories that went wrong come first. Those are the ones worth reading: they show what the agent was told about its own output and what it did next.

| agent | subject | calls | rejections | retries | critic | revised | outcome |
|---|---|---|---|---|---|---|---|
| vocab_probe | [absent-Metoprolol](vocab_probe/absent-Metoprolol.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [absent-Acute_pancreatitis](vocab_probe/absent-Acute_pancreatitis.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [absent-Gastroparesis](vocab_probe/absent-Gastroparesis.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [absent-Oral_glucose_tolerance_test](vocab_probe/absent-Oral_glucose_tolerance_test.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [absent-Type_1_diabetes_mellitus](vocab_probe/absent-Type_1_diabetes_mellitus.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [broader-Chronic_kidney_disease_stage_3_or_worse](vocab_probe/broader-Chronic_kidney_disease_stage_3_or_worse.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [broader-Iron_deficiency_anaemia](vocab_probe/broader-Iron_deficiency_anaemia.md) | 2 | 0 | 0 | 0 | 0 | unmappable |
| vocab_probe | [control-Anaemia](vocab_probe/control-Anaemia.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [control-Hydrochlorothiazide](vocab_probe/control-Hydrochlorothiazide.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [control-Prediabetes](vocab_probe/control-Prediabetes.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [control-Simvastatin](vocab_probe/control-Simvastatin.md) | 2 | 0 | 0 | 0 | 0 | grounded to 2 code(s) |
| vocab_probe | [control-Systolic_blood_pressure](vocab_probe/control-Systolic_blood_pressure.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Diabetic_nephropathy](vocab_probe/gap-Diabetic_nephropathy.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Essential_hypertension](vocab_probe/gap-Essential_hypertension.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Estimated_glomerular_filtration_rate](vocab_probe/gap-Estimated_glomerular_filtration_rate.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Glycated_haemoglobin](vocab_probe/gap-Glycated_haemoglobin.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Haemodialysis](vocab_probe/gap-Haemodialysis.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Metformin](vocab_probe/gap-Metformin.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |
| vocab_probe | [gap-Obesity](vocab_probe/gap-Obesity.md) | 2 | 0 | 0 | 0 | 0 | grounded to 2 code(s) |
| vocab_probe | [gap-Type_2_diabetes_mellitus](vocab_probe/gap-Type_2_diabetes_mellitus.md) | 2 | 0 | 0 | 0 | 0 | grounded to 7 code(s) |
| vocab_probe | [gap-Urine_albumin_to_creatinine_ratio](vocab_probe/gap-Urine_albumin_to_creatinine_ratio.md) | 2 | 0 | 0 | 0 | 0 | grounded to 1 code(s) |

